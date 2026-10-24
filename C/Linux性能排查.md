# Linux 性能排查
线上不会按教科书出事：多数时候你只拿到「接口变慢了」「机器报警了」，要在几分钟内把现象收缩到根因。这篇笔记按「方法论 → 工具矩阵 → 分资源定位 → 内核视角 → 火焰图 → 故障案例 → 压测基线 → 面试」组织，命令以 5.x 内核 + systemd 发行版为准，参数细节随版本变化。排查的难点从来不是不会敲命令，而是**知道该敲哪一条、输出里哪个数字算异常**，所以每节都写清「看什么指标」与「大概多大算坏」；具体阈值必须用自己的基线校准，别照抄网上的绝对值。

## 1 方法论
### 1.1 USE 方法
USE 是 Brendan Gregg 提出的资源检查法：对**每一类资源**依次问三个问题，能在不看业务代码的前提下快速排除大半故障。

| 维度 | 问什么 | 典型指标 |
| --- | --- | --- |
| Utilization（使用率） | 资源有多少时间在忙 | CPU 的 `100-idle`、磁盘 `%util`、网卡带宽占比、内存已用比例 |
| Saturation（饱和度） | 有多少活儿在排队 | CPU 运行队列 `r`、磁盘 `aqu-sz` 与 `await`、内存 `si/so` 与直接回收、网卡 `txqueuelen` 溢出 |
| Errors（错误） | 有没有报错 | `dmesg` 的 IO error、`netstat -s` 的 checksum/重传、`ListenOverflows`、文件系统只读重挂 |

使用率是「忙不忙」，饱和度是「排不排队」。**使用率高不一定慢，饱和了一定慢**：一块 NVMe 的 `%util` 到 100% 仍可能 0.1 ms 返回，而一块老 SATA 盘 `%util` 到 60% 就已经排队到几十毫秒。所以优先看饱和度，再看使用率。

### 1.2 四类资源
| 资源 | Utilization | Saturation | Errors |
| --- | --- | --- | --- |
| CPU | `mpstat -P ALL` 的 `%usr/%sys`，整体 `100-idle` | `vmstat` 的 `r`（可运行队列）、`/proc/loadavg`、`pidstat -w` 的 `nvcswch/s`、`%st`（被宿主机抢走） | `dmesg` 的 MCE、`soft lockup`、`hung task` |
| 内存 | `free` 的 used/total、`/proc/meminfo` 的 `MemAvailable` | `vmstat` 的 `si/so`、`pgscan_direct`、OOM 事件 | `dmesg` 的 `Out of memory`、`page allocation failure` |
| 磁盘 | `iostat -x` 的 `%util`、`r/s`+`w/s` 与基线比 | `aqu-sz`（平均排队长度）、`await`（含排队）、`vmstat` 的 `wa` | `dmesg` 的 `I/O error`、`EXT4-fs error`、`remounting filesystem read-only` |
| 网络 | `sar -n DEV` / `iftop` 的带宽、`ss -s` 的连接数 | `ss -ti` 的 `Send-Q`、`netstat -s` 的 `ListenOverflows`、`tc` 队列 | `netstat -s` 的 `retrans`、`checksum`、`dropped`、`RST` |

### 1.3 排查顺序：先看现象，再定位
不要一上来就 `strace`。固定六步，每步都产出「缩小后的范围」：

1. **定性**：是单机还是全站、单接口还是全部接口、从几点开始、有没有发布/扩容/配置变更。这一步经常直接给出答案。
2. **看整体**：一屏拿全 `top`、`vmstat 1 5`、`free -h`、`df -h`、`iostat -x 1 3`，判断是 CPU、内存、IO 还是网络。
3. **定位资源**：用 USE 三问确认是使用率高还是饱和，是否伴随错误。
4. **定位到进程/线程/连接**：`pidstat`、`top -H`、`ss`、`lsof`，把资源消耗挂到具体 PID。
5. **定位到代码或系统调用**：`perf top -p`、`strace -p`、`bpftrace`、语言层工具（`jstack`、`pprof`）。
6. **验证与记录**：改一个变量、复测、对比基线，把时间线和结论写进工单。

### 1.4 四条纪律
- **先取证，后重启**。重启会抹掉现场（`/proc`、连接状态、堆栈），动手前先 `top -b -n1`、`ss -s`、`dmesg -T | tail -100` 存一份。
- **一次只改一个变量**。同时改三个参数，复测好了也不知道是哪个起的作用。
- **观测本身有开销**。`strace`、`tcpdump -s 0`、`perf record` 全量采样都会显著改变被测系统，先用低开销工具收窄范围。
- **对比基线**。没有基线的「CPU 80%」没有意义，同样的 80% 在压测环境和生产是两回事。

## 2 观测工具矩阵
### 2.1 一览表
| 工具 | 看什么指标 | 典型用法 |
| --- | --- | --- |
| `top` / `htop` | 整体 load、CPU 分解（`us/sy/wa/st`）、内存、单进程 `%CPU/%MEM` | `top -b -n1 -o %CPU \| head -20` 存快照；交互键 `P` 按 CPU、`M` 按内存、`1` 展开各核、`H` 切线程、`c` 看完整命令行 |
| `vmstat` | `r`/`b` 队列、`si/so` 换页、`us/sy/id/wa`、`cs` 上下文切换、`in` 中断 | `vmstat 1 5`；`vmstat -s` 看累计值，`vmstat -d` 看块设备 |
| `iostat` | 每块盘的 `r/s`、`w/s`、`await`、`aqu-sz`、`%util` | `iostat -x -d 1 5`；`-m` 以 MB 显示，`-p` 分设备显示 |
| `mpstat` | 每核 CPU 与软中断分布，判断是否单核打满 | `mpstat -P ALL 1`；`mpstat -I SUM 1` 看中断 |
| `pidstat` | 单进程的 CPU、内存、IO、上下文切换 | `pidstat -u -w -d -p PID 1`；`pidstat -d 1` 按进程看谁在读写在盘 |
| `free` | 内存总量、`available`、`buff/cache`、swap | `free -h`；`free -h -s 3` 连续观察趋势 |
| `sar` | 历史与实时趋势：CPU、内存、IO、网络、队列 | `sar -u 1 5`、`sar -r 1 5`、`sar -n DEV 1 5`、`sar -q`（load 与队列）、`sar -f /var/log/sa/sa15` 回看某天 |
| `ss` | 连接状态分布、监听队列、socket 内存、单连接 RTT 与重传 | `ss -s` 汇总、`ss -tlnp` 监听、`ss -tanp state established`、`ss -ti` 看 `retrans`/`rtt`/`cwnd` |
| `iftop` / `nload` | 实时带宽、按对端排序的流量 | `iftop -i eth0 -nNP`（`-P` 显示端口）、`nload -u M eth0`；长期看用 `sar -n DEV` |
| `lsof` | 打开的文件、fd、被占用的目录、已删除未释放的文件 | `lsof -p PID`、`lsof -i:8080`、`lsof +D /data`、`lsof +L1` |
| `strace` | 系统调用的参数、返回值与**每次耗时**，卡在哪个调用 | `strace -f -T -tt -y -p PID`；`strace -c cmd` 做调用耗时统计 |
| `perf` | CPU 采样热点、调用栈、硬件计数、调度事件 | `perf top -p PID`、`perf record -F 99 -g -p PID -- sleep 30`、`perf stat -p PID` |
| `bpftrace` | 内核与用户态的动态追踪，可按进程/延迟/参数过滤，开销低 | `bpftrace -e '<probe> { ... }'`，见 9.3 |

### 2.2 几个容易踩的点
- `sar` 依赖 `sysstat` 采集，没开采集时只有实时数据、没有历史。开启：`systemctl enable --now sysstat`，数据在 `/var/log/sa/`，默认保留 7 天。
- `perf` 受 `kernel.perf_event_paranoid` 限制，值大于 2 时普通用户无法采样；临时放开 `sysctl -w kernel.perf_event_paranoid=1`。
- `bpftrace` 需要 4.9+ 内核（4.18+ 有 BTF 更好用），容器里要 `--privileged` 或 `CAP_BPF`+`CAP_PERFMON`。
- `strace` 基于 `ptrace`，被跟踪进程每次系统调用要停两次，高并发服务上可能把 P99 从 5 ms 拖到 50 ms。线上优先 `perf`/`bpftrace`，必须用 `strace` 时只跟目标调用（`-e trace=network`）并控制时长。

## 3 CPU 排查
### 3.1 load average 三个值
`/proc/loadavg` 前三列是 1、5、15 分钟负载，内核每 5 秒采样一次，做指数衰减平均（1 分钟衰减最快，15 分钟最慢），所以三个值反映的是**不同时间尺度的记忆**。

关键点：load 统计的是 `TASK_RUNNING`（正在跑 + 在运行队列里等 CPU）**加上** `TASK_UNINTERRUPTIBLE`（`D` 状态，多在等 IO）的进程数。它是「想干活但没立刻干上的任务数」，不是 CPU 使用率。

| 三值形态 | 含义 |
| --- | --- |
| 1 分钟高、15 分钟低 | 突发流量或瞬时任务，看是否已恢复 |
| 三个都高且持续 | 长期容量不足，或慢 IO 把进程压在 `D` 状态 |
| 15 分钟高、1 分钟低 | 刚过去的高峰，确认是否留下后遗症（连接堆积、队列积压） |

判断要除以核数：`nproc` 为 8 时 load 8 是满载，load 2 只是 25%。经验阈值 `load/nproc > 1` 需关注、`> 2` 已明显排队。另外**容器里的 load 是宿主机的**，`/proc/loadavg` 没有做命名空间隔离，容器看到的高 load 可能完全与自己无关（lxcfs 可修正）。

### 3.2 us/sy/wa/st 怎么读
| 指标 | 含义 | 高了通常说明 |
| --- | --- | --- |
| `us` | 用户态 CPU（含 `nice` 为负的进程） | 业务代码在算：死循环、正则回溯、序列化、加解密、GC（JVM 的 GC 线程算用户态） |
| `sy` | 内核态 CPU | 系统调用太频繁、上下文切换多、锁竞争、内存分配、软中断处理 |
| `ni` | 被 `nice` 调低优先级的用户态时间 | 批处理任务在抢 CPU |
| `id` | 空闲 | 与 load 对照：`id` 高而 load 高，几乎一定是 `D` 状态或 IO |
| `wa` | 空闲且有未完成 IO 的时间 | 磁盘慢或 IO 密集，但**不等于** IO 是瓶颈，见 3.4 与面试题 4 |
| `hi` / `si` | 硬中断 / 软中断 | 网卡小包多、中断没做多队列或 RPS 不均 |
| `st` | steal，被 hypervisor 抢走的时间 | 虚拟机被超卖，或宿主机邻居在抢 CPU |

`sy` 高而 `us` 低是典型的「syscall 或调度开销」特征：先 `vmstat 1` 看 `cs`（上下文切换）和 `in`（中断），再 `pidstat -w -p PID 1` 看 `cswch/s`（主动让出，多在等锁/IO）与 `nvcswch/s`（被动被抢，说明 CPU 竞争）。

### 3.3 从进程定位到线程
```bash
top -H -p 1234                       # 线程视图，记下高占用的 TID
ps -L -p 1234 -o pid,tid,pcpu,stat,comm --sort=-pcpu | head
printf '%x\n' 12567                  # TID 转十六进制，nid=0x3117
jstack 1234 | grep -A 30 'nid=0x3117'   # Java 线程栈
perf top -p 1234 -g                  # C/C++ 直接看热点函数与调用栈
```

`top -H` 的 `S` 列同时给线程状态，`R` 是真正在跑，`S` 在等，`D` 卡在内核。多个线程同时 `R` 且都在同一函数，才是 CPU 型热点。

### 3.4 CPU 100% 的 5 种常见原因
| 原因 | 特征 | 定位命令 |
| --- | --- | --- |
| 业务计算密集（死循环、大 JSON、正则回溯） | `us` 高、单线程接近 100% | `perf top -p PID` 看热点函数；`jstack` 抓栈看是否同一行 |
| 系统调用 / 上下文切换过多 | `sy` 高、`cs` 大 | `vmstat 1`、`strace -c -p PID`、`pidstat -w` |
| 锁竞争与自旋 | `sy` 高、多核不均衡、吞吐上不去 | `perf top` 看到 `futex`/`mutex`/`spin_lock`；`pidstat -t` 看线程分布 |
| 中断与软中断（网卡小包、`ksoftirqd`） | `si` 高、某核特别忙 | `mpstat -P ALL 1`、`cat /proc/softirqs`、`ethtool -l eth0` 看队列数 |
| GC 或内核回收（`kswapd`、`kcompactd`） | 周期性尖峰、伴随内存压力 | `jstat -gcutil PID 1000`、`pidstat -u -p PID`、`vmstat` 的 `si/so` |

排查顺序固定：`top` 找到进程 → `top -H` 找到线程 → `perf top -p` 或 `jstack` 找到代码 → 确认是业务逻辑、锁还是内核态开销。不要跳过第二步直接 `strace`，多线程进程里 `strace` 的输出会混在一起。

## 4 内存排查
### 4.1 free 各列
```bash
free -h
#                total        used        free      shared  buff/cache   available
# Mem:            15Gi       9.2Gi       310Mi       412Mi       6.1Gi       5.4Gi
# Swap:          2.0Gi       1.1Gi       924Mi
```

| 列 | 含义 | 备注 |
| --- | --- | --- |
| `total` | 物理内存总量 | 不含 swap |
| `used` | 已用内存 | 口径是 `total - free - buff/cache`，所以 `buff/cache` 大时 `used` 会显得小 |
| `free` | 完全未使用的内存 | 数值小是正常的，空闲内存会被主动拿去做缓存 |
| `shared` | `tmpfs` 与共享内存 | 计入 `buff/cache`，**且不可回收**，容易制造「缓存能回收」的误判 |
| `buff/cache` | 块设备缓存 + 页缓存 | 大部分可回收，见 4.2 |
| `available` | 估算的可用内存 | 含可回收缓存，**判断内存是否够用只看这一列** |

`available` 的估算来自 `/proc/meminfo` 的 `MemAvailable`（3.14+ 内核提供），它扣掉了不可回收的 `Shmem`、预留与低水位。`available` 持续下降才是真问题，`free` 小完全不用管。

### 4.2 buff/cache 能不能回收
能，但要分清三类：

- **干净的 page cache**：随时丢弃，零成本。
- **脏页（`Dirty`、`Writeback`）**：必须先回写磁盘才能释放，所以内存压力和慢盘叠加时会突然变慢。
- **不可回收部分**：`Shmem`（`tmpfs`、`/dev/shm`）、`mlock` 锁定的页、HugePages、内核 slab 中不可回收的对象。这部分算在 `buff/cache` 里，却永远不会让出来，所以「手动 `echo 3 > /proc/sys/vm/drop_caches`」在生产上基本是错误操作：缓存被清空、下一次读全部落到磁盘，指标好看几秒、随后更慢。

### 4.3 swap 与 si/so
`vmstat` 的 `si`（swap in）、`so`（swap out）单位是 KB/s。判断标准是**趋势**而不是绝对值：

- `si/so` 长期非 0：内存真的不够，匿名页在盘上换进换出，任何依赖这些页的请求都会变成随机 IO，延迟从微秒级跳到毫秒级。
- `Swap used` 高但 `si/so` 为 0：历史遗留。早高峰换出去后就没再访问，不影响当前性能，别急着 `swapoff`（`swapoff` 需要把 swap 全部读回内存，本身就可能触发 OOM）。

`vm.swappiness` 控制换出匿名页的倾向，默认 60；数据库类服务常设 1~10 以减少换出。注意 **`swappiness=0` 不等于禁用 swap**，内存紧张时仍会换出（只是尽量少），彻底禁用要 `swapoff -a`。

### 4.4 OOM Killer 日志
```bash
dmesg -T | grep -iE 'out of memory|killed process|oom'
journalctl -k -b | grep -i oom
cat /proc/PID/oom_score           # 当前 OOM 分数
cat /proc/PID/oom_score_adj       # -1000 ~ 1000，越小越不容易被杀
```

典型一条：`Out of memory: Killed process 1234 (java) total-vm:8257536kB, anon-rss:7340032kB, file-rss:0kB`。这里的 `anon-rss` 才是关键，`total-vm` 大不代表真占内存（虚拟地址空间可以很大）。

要区分两种 OOM：

- **全局 OOM**：整机内存耗尽，内核挑 `oom_score` 最高的进程杀。
- **cgroup OOM**：容器/`systemd` 的 `memory.max` 触顶，日志里是 `Memory cgroup out of memory`，此时**宿主机内存可能还很充裕**。cgroup v2 下看 `memory.events` 的 `oom` 与 `oom_kill` 计数，`memory.current` 与 `memory.max` 的比值。

### 4.5 进程 RSS 与 smaps
```bash
ps -eo pid,rss,vsz,pmem,comm --sort=-rss | head
cat /proc/1234/status | grep -E 'VmRSS|VmSwap|Threads'
cat /proc/1234/smaps_rollup          # 汇总版 smaps，比逐段读快得多
pmap -x 1234 | sort -k3 -n | tail    # 按段看谁大
```

| 口径 | 含义 | 用途 |
| --- | --- | --- |
| `VSZ` / `VmSize` | 虚拟地址空间，含未分配物理页的映射 | 只能看是否有异常大的映射，不能当内存占用 |
| `RSS` / `VmRSS` | 常驻物理内存，**含共享库与共享内存** | 多个进程会重复统计，加总远大于实际占用 |
| `PSS` | 共享页按引用数平均分摊 | 判断真实占用，`smaps_rollup` 直接给 `Pss` |
| `USS` | 独占内存 = `Private_Clean + Private_Dirty` | 进程私有开销，泄漏排查看这个 |

### 4.6 内存泄漏怎么判断
先分清两个概念：**内存增长**可能是缓存、连接池、预热、分配器碎片，会收敛到平台期；**泄漏**是单调上涨不回落，重启归零后继续涨。

1. 定时采样 `grep VmRSS /proc/PID/status` 或 `smaps_rollup`，画一条 30 分钟到几小时的曲线，看是否呈阶梯或线性上升。
2. 看 `smaps_rollup` 里哪一段在涨：`[heap]`/匿名映射涨是业务分配，线程栈涨是线程泄漏（线程数也涨），`/dev/shm` 涨是共享内存。
3. 语言层确认：Java 用 `jmap -histo:live PID` 隔一段时间对比两次对象数，或 `jcmd GC.heap_info`；Go 用 `pprof` 的 `heap`；C/C++ 用 `valgrind --leak-check=full`（慢，需能复现）、ASan/LSan，或 jemalloc/tcmalloc 的 heap profile。
4. 排除假泄漏：glibc `malloc` 的多 arena 与不归还（`MALLOC_ARENA_MAX=2`、`malloc_trim(0)` 立即归还）、JVM 堆外内存（DirectByteBuffer、Netty）导致的 RSS 涨而不见堆涨、`tmpfs` 写入。

## 5 磁盘与 IO
### 5.1 iostat -x 关键列
```bash
iostat -x -d 1 5
# Device  r/s     w/s   rkB/s   wkB/s  r_await  w_await  aqu-sz  %util
# nvme0n1 1200.0  800.0 48000.0 32000.0   0.35     0.52    1.20   62.4
```

| 列 | 含义 | 怎么读 |
| --- | --- | --- |
| `r/s`、`w/s` | 每秒读/写次数（IOPS） | 与基线比；小文件随机写会把 IOPS 打满而吞吐很低 |
| `rkB/s`、`wkB/s` | 每秒读写字节数（吞吐） | 顺序大 IO 先看吞吐，随机小 IO 先看 IOPS |
| `r_await`、`w_await` | 平均每次 IO 的耗时（ms），**含排队时间** | 机械盘 > 20 ms、SSD > 5 ms 就要怀疑；它涨而 `%util` 不涨，多半是单次服务慢（坏盘、远端存储） |
| `aqu-sz` | 平均排队长度（旧版 `avgqu-sz`） | 持续 > 1~2 说明在排队，这是比 `%util` 更可靠的饱和信号 |
| `%util` | 设备有 IO 在跑的时间占比 | 单队列 SATA 上接近 100% 基本等于饱和；NVMe/RAID 因并行度高会虚高，100% 仍可能正常 |

`await` 是核心：它等于「排队时间 + 服务时间」。要靠 `iostat -x` 里另一组列（`rareq-sz`、`wareq-sz`）和硬件标称值来推服务时间，`await` 远大于服务时间就是在排队。

### 5.2 找到是谁在读写
```bash
iotop -oPa                 # 只显示真正有 IO 的进程，累计模式更稳
pidstat -d 1               # 按进程看 kB_rd/s、kB_wr/s
cat /proc/1234/io          # read_bytes/write_bytes 累计值，隔 10 秒取两次做差最准
```

容器或未开 `CONFIG_TASK_IO_ACCOUNTING` 的内核上 `iotop` 只能看到自己，此时用 `pidstat -d` 与 `/proc/PID/io` 交叉验证。

### 5.3 空间与 inode
```bash
df -h                      # 容量
df -i                      # inode 使用率，海量小文件会先耗尽这个
du -x -h --max-depth=1 /var | sort -h        # -x 不跨文件系统，避免统计到挂载点
find / -xdev -type f -size +1G -printf '%s %p\n' 2>/dev/null | sort -rn | head
lsof +L1                   # 已被删除但仍被进程持有的文件
lsof | grep -i deleted
```

`df` 与 `du` 对不上，常见四种原因：已删除但仍被占用（`lsof +L1`）、有进程往未 `unlink` 的文件里继续写、目录被另一个文件系统挂载覆盖、稀疏文件（`du` 按块算、`ls` 按大小算）。inode 用尽的表现是 `df -h` 还有空间但 `touch` 报 `No space left on device`。

### 5.4 IO 高的常见原因
- **日志同步刷盘**：每条日志都 `fsync`，或 `logback`/`log4j` 的 `immediateFlush` 加同步 appender。`strace -f -e trace=fsync,fdatasync -T -p PID` 能直接看到单次 `fsync` 的耗时。
- **数据库 checkpoint / 大事务 / 慢查询全表扫**：`iostat` 上表现为周期性 `wkB/s` 尖峰，配合慢日志定位。
- **备份、压缩、解压、打包**：`tar`/`gzip`/`rsync` 抢 IO，用 `ionice -c2 -n7` 降级或错峰。
- **swap 抖动**：`si/so` 非 0 且盘上有大量随机读，本质是内存不足，去查内存而不是查盘。
- **硬件与文件系统问题**：`dmesg` 里的 `I/O error`、`ata` 重试、RAID 卡电池失效导致写策略变成 write-through（性能骤降数倍）。

## 6 网络
### 6.1 ss 与连接状态
```bash
ss -s                                            # 汇总：TCP/UDP 连接数、各状态计数、内存
ss -tan | awk '{print $1}' | sort | uniq -c      # 按状态统计
ss -tan state time-wait | wc -l
ss -tlnp                                         # 监听端口与进程
ss -ti                                           # 单连接的 rtt、retrans、cwnd、send/recv 队列
```

`Recv-Q`/`Send-Q` 的含义随状态变化：在 `LISTEN` 上是当前 accept 队列长度与 backlog 上限，`Recv-Q` 接近 `Send-Q` 说明应用 `accept` 太慢；在 `ESTAB` 上是接收但未被应用读走、发送但未被确认的字节数，持续堆积说明对端慢或本端处理不过来。

### 6.2 TIME_WAIT 与 CLOSE_WAIT
| 状态 | 出现在哪一侧 | 成因 | 处理 |
| --- | --- | --- | --- |
| `TIME_WAIT` | **主动关闭方** | 等 2MSL（约 60 秒）确保最后的 ACK 到达、旧连接报文不污染新连接 | 短连接太多时用连接池/keep-alive；`net.ipv4.tcp_tw_reuse=1`（仅对**出向**连接生效）；扩大 `net.ipv4.ip_local_port_range`；`tcp_max_tw_buckets` 只治标 |
| `CLOSE_WAIT` | **被动关闭方** | 对端已 `FIN`，本端应用没调 `close()` | 这是**应用 bug**：连接池泄漏、异常分支没关、`finally` 缺失。数量持续上涨必须改代码，调内核参数无效 |

千万不要开 `net.ipv4.tcp_tw_recycle`：它在 4.12 已被移除，且在 NAT 环境下会因时间戳判断错误大量丢连接。`TIME_WAIT` 数量上万本身不是故障，只要端口够用、没有 `cannot assign requested address` 就无需处理。

### 6.3 丢包与重传
```bash
netstat -s | grep -iE 'retrans|timeout|overflow|drop|prune'
nstat -az | grep -iE 'TcpRetransSegs|TcpExtListenOverflows|TcpExtListenDrops'
ss -ti | grep -E 'retrans|rtt'
```

看三个数：`retrans` 占比超 1% 说明链路丢包或拥塞；`ListenOverflows`/`ListenDrops` 增长说明 accept 队列满（应用处理慢或 `somaxconn` 太小）；`prune`/`collapsed` 增长说明 socket 内存不足。单连接层面，`ss -ti` 的 `retrans:x/y` 与 `rtt` 能区分是「一直慢」（RTT 高）还是「偶尔抖」（重传多）。

### 6.4 tcpdump 抓包定位
```bash
tcpdump -i any -nn -s 96 -c 200 port 8080          # 只抓头部，开销小
tcpdump -i eth0 -nn 'tcp[tcpflags] & tcp-syn != 0'  # 只看 SYN
tcpdump -i eth0 -nn -w /tmp/a.pcap host 10.0.0.5 and port 3306
tcpdump -r /tmp/a.pcap -nn -A | head -50            # 回放
```

看四件事：三次握手是否完成（只有 SYN 没有 SYN-ACK = 对端没回或中间被拦）、有没有 `RST`（应用没监听、连接被拒、超时被中间设备重置）、同序号报文是否重复出现（重传）、窗口是否缩到 0（接收方处理不过来）。生产上务必加 `-s` 限长、`-c` 限包数，并按需用 `-w` 落盘后再分析。

### 6.5 DNS 慢与带宽打满
DNS 慢的典型表现是「首次请求慢、之后正常」或「所有下游调用都慢一点」：

```bash
dig +stats example.com | grep -E 'Query time|SERVER'
getent hosts example.com            # 走完整 NSS 链路，比 dig 更接近应用行为
cat /etc/resolv.conf               # options timeout:1 attempts:2 可缩短失败等待
```

`getent hosts` 慢而 `dig` 快，说明卡在 `/etc/nsswitch.conf` 里 `dns` 之前的解析源（`myhostname`、`mdns`、LDAP）。带宽打满用 `iftop -i eth0 -nNP` 看是谁，用 `sar -n DEV 1` 看长期趋势与是否接近网卡上限；云主机还要确认是否被厂商限速（表现为丢包而非排队）。

## 7 进程与文件
### 7.1 lsof 的几种用法
```bash
lsof -p 1234                 # 该进程打开的所有文件、fd 号、类型、大小、偏移
lsof -i :8080                # 谁在占用端口
lsof +D /data/logs           # 递归扫描某目录下被打开的文件（慢，慎用于大目录）
lsof /var/log/app.log        # 谁在写这个文件
lsof +L1                     # link count < 1：已删除但仍被持有
```

### 7.2 fd 耗尽
```bash
ulimit -n                    # 当前 shell 软限
ulimit -Hn                   # 硬限
cat /proc/1234/limits | grep 'open files'   # 运行中进程的真实限制
cat /proc/sys/fs/file-nr     # 已分配 / 未用 / 全局上限 fs.file-max
lsof -p 1234 | wc -l
ls /proc/1234/fd | wc -l
```

报错特征是 `Too many open files`（`EMFILE`）、`accept` 失败、服务开始拒绝新连接。`ulimit -n` 只影响当前 shell 及其子进程，持久化要改 `/etc/security/limits.conf`（或 `limits.d/`），systemd 服务则改 unit 的 `LimitNOFILE=` 并 `daemon-reload`。另外注意单进程上限还受 `fs.nr_open` 约束，`fs.file-max` 是全局的。

### 7.3 strace 看卡在哪
```bash
strace -f -T -tt -y -p 1234                 # -T 每次耗时、-y 显示 fd 对应路径
strace -f -e trace=network -p 1234          # 只看网络相关
strace -f -e trace=file -p 1234             # 只看文件相关
strace -c -p 1234                           # 统计各调用的次数与总耗时
```

进程卡住时，`strace` 输出的最后一行就是现场：停在 `read()` 说明在等数据，停在 `futex()` 说明在等锁，停在 `connect()` 说明在等 TCP 握手（可能被防火墙丢包），停在 `fsync()` 说明在等盘。用 `-T` 看单次耗时，「哪个调用慢」比「调用了什么」更有价值。

### 7.4 D 状态进程
```bash
ps -eo stat,pid,ppid,wchan:32,cmd | awk '$1 ~ /^D/'
cat /proc/1234/stack          # 内核栈，需 root 且内核开了 CONFIG_STACKTRACE
cat /proc/1234/wchan          # 卡在哪个内核函数
```

`D` 是不可中断睡眠，进程在内核里等 IO 或内核锁，**信号要等系统调用返回才处理**，所以 `kill -9` 也没用。大量 `D` 进程会让 load 飙升而 CPU 空闲，最常见原因是磁盘故障/慢盘、NFS 服务端失联、`dm`/`md` 阵列降级、网络块设备（iSCSI）超时。处理方向永远是修 IO 链路，不是杀进程。

## 8 内核与系统
### 8.1 日志入口
```bash
dmesg -T | tail -100              # -T 转成可读时间（注意时区与 uptime 基准）
dmesg -T -l err,crit -w           # 只看错误级别并持续跟踪
journalctl -k -b -p err           # 本次启动的内核日志（-b -1 看上次启动）
journalctl --since '10 min ago' -p warning
```

内核 ring buffer 有上限，刷得快时早期记录会被覆盖；重要机器把 `rsyslog`/`journald` 落盘打开，否则 OOM 现场可能只剩一行。

### 8.2 /proc 关键文件
```bash
cat /proc/loadavg      # 1/5/15 分钟负载 + 运行中/总进程数 + 最近分配的 PID
cat /proc/meminfo      # 内存明细，MemAvailable 才是可用内存
cat /proc/interrupts   # 每个 CPU 上每个中断的计数
cat /proc/softirqs     # 软中断分布，看软中断是否集中在单核
```

| 字段 | 含义 |
| --- | --- |
| `MemTotal` / `MemFree` | 物理内存总量 / 完全空闲 |
| `MemAvailable` | 估算可用（含可回收缓存），判断内存够不够看它 |
| `Buffers` / `Cached` | 块设备元数据缓存 / 页缓存 |
| `Dirty` / `Writeback` | 待回写 / 正在回写的脏页，持续偏高说明盘写不过来 |
| `Shmem` | `tmpfs` 与共享内存，计入缓存但不可回收 |
| `Committed_AS` | 已承诺的虚拟内存总量，远超 `MemTotal` 时有 OOM 风险（配合 `overcommit_memory`） |

`/proc/interrupts` 的看点是**分布**：网卡多队列时各核计数应大致均匀，若全部集中在 CPU0，说明中断亲和性或 RPS 没配好，此时 `si` 高且单核打满。对应调整 `/proc/irq/<N>/smp_affinity` 或 `ethtool -L eth0 combined N`。

### 8.3 sysctl 常用调优与风险
| 参数 | 常见默认 | 调整作用 | 风险 |
| --- | --- | --- | --- |
| `vm.swappiness` | 60 | 降到 1~10 减少匿名页换出，适合数据库 | 内存紧张时更容易直接触发 OOM 而非换页；设 0 也不等于禁用 swap |
| `net.core.somaxconn` | 4096（老内核 128） | 放大 accept 队列上限，抗突发连接 | 必须同时调大应用的 `backlog`（`nginx` 的 `listen ... backlog=`、`Tomcat` 的 `acceptCount`），实际取 `min(backlog, somaxconn)`；队列太长会让客户端等更久才被拒 |
| `net.ipv4.tcp_max_syn_backlog` | 1024~4096 | 抗 SYN 洪峰 | 需配合 `tcp_syncookies`，过大只是延后失败 |
| `fs.file-max` | 随内存推算 | 全局 fd 上限 | 只改全局，单进程还受 `fs.nr_open` 与 `ulimit -n` 限制 |
| `net.ipv4.ip_local_port_range` | `32768 60999` | 扩大出向端口范围，缓解 `TIME_WAIT` 占端口 | 与目标端口冲突时可能连不上；范围过大会占用保留端口 |
| `vm.overcommit_memory` | 0（启发式） | 设为 1 允许超卖，Redis 等 fork 场景常用 | 超卖过度会在真正分配时 OOM，而不是 `malloc` 失败 |

调参纪律：改前 `sysctl -a > /tmp/sysctl.before` 留底；写 `/etc/sysctl.d/99-tune.conf` 而不是直接改 `/etc/sysctl.conf`；`sysctl -p` 生效后立即压测验证；一次只改一项。容器共享宿主机内核，容器内改 `sysctl` 大多不生效或影响全局，网络参数要在宿主机或 `Pod` 的 `securityContext.sysctls` 里设。

## 9 火焰图与采样
### 9.1 perf 采样
```bash
perf top -p 1234 -g                                  # 实时看热点与调用栈
perf record -F 99 -g -p 1234 -- sleep 30             # 99 Hz 采样 30 秒，低开销
perf report --stdio --sort comm,dso,symbol | head -40
perf stat -p 1234 -- sleep 5                         # 周期、指令数、cache miss、上下文切换
```

栈不全是常态：默认 frame pointer 在很多发行版编译时被省略。可靠做法是用 `--call-graph dwarf`（开销更大），或让程序用 `-fno-omit-frame-pointer` 编译。`perf record` 不加 `-p` 就是全系统采样，容器里要确认 `perf_event_paranoid` 与权限。

### 9.2 火焰图流程
```bash
perf record -F 99 -g -p 1234 -- sleep 30
perf script > out.perf
stackcollapse-perf.pl out.perf > out.folded
flamegraph.pl out.folded > cpu.svg
# 一行版：perf script | stackcollapse-perf.pl | flamegraph.pl > cpu.svg
```

读图三条规则：**宽度 = 占采样比例**（宽条才是重点）、**上下是调用关系**（上面是叶子/自身耗时，下面是调用者）、**颜色无语义**，只区分栈帧。要找的是「又宽又平」的塔：某一层特别宽说明它自身在耗 CPU；「上面宽下面窄」说明是这一层的直接开销。

on-CPU 火焰图看「忙什么」，off-CPU 火焰图看「等什么」（等锁、等 IO、等网络），后者用 `bpftrace` 的 `offcputime` 或 `perf sched` 生成。线上慢但 CPU 不高的问题，off-CPU 图往往才是答案。

### 9.3 bpftrace 一行示例
```bash
# 统计各进程 read 的总字节数
bpftrace -e 'tracepoint:syscalls:sys_exit_read /args->ret > 0/ { @[comm] = sum(args->ret); }'
# 谁在打开哪些文件
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args->filename)); }'
# 对指定进程做 99Hz 用户态栈采样，直接出折叠栈
bpftrace -e 'profile:hz:99 /pid == 1234/ { @[ustack] = count(); }'
```

`bpftrace` 的价值是「按条件过滤 + 聚合在内核里完成」，开销远低于 `strace`，适合线上长时间挂着。生产上先用 `-l` 确认探针存在，再小范围试跑。

### 9.4 ftrace 简介
ftrace 是内核自带的追踪框架，不需要额外装东西，适合看**内核函数级的调用链与延迟**：

```bash
cd /sys/kernel/debug/tracing
echo function_graph > current_tracer
echo 'vfs_read' > set_graph_function
echo 1 > tracing_on; sleep 2; echo 0 > tracing_on
cat trace | head -60
```

更方便的是 `trace-cmd record -p function_graph -l ext4_file_write_iter`，或 `perf trace`（`strace` 的低开销替代）。ftrace 的 `wakeup`/`wakeup_rt` tracer 能直接量出调度延迟，排查「偶发卡顿几十毫秒」很有效。

## 10 典型故障案例
### 10.1 load 高但 CPU 不高
- **现象**：load 15 分钟从 2 涨到 40，`top` 里 `id` 仍有 60%，业务 RT 抖动，`kill -9` 杀不掉某些进程。
- **排查命令**：`uptime` → `ps -eo stat,pid,wchan:32,cmd | awk '$1 ~ /^D/'` → `vmstat 1 5` 看 `b` 列与 `wa` → `iostat -x 1` 看是否有盘 `await` 暴涨或直接无响应 → `dmesg -T | tail -50` 看 `nfs`/`I/O error`/`hung_task`。
- **根因**：`D` 状态进程堆积。常见是 NFS 服务端失联（`wchan` 显示 `rpc_wait_bit_killable`）、磁盘坏道导致重试、RAID 降级、iSCSI 超时。
- **修复**：先恢复 IO 链路（重启 NFS、摘掉坏盘、切存储），临时 `umount -f -l` 不可用的 NFS 或降低其挂载超时；长期给关键路径加超时与熔断，避免整个线程池被 `D` 状态占死。

### 10.2 内存持续上涨导致 OOM
- **现象**：`available` 从 8 GiB 缓慢降到几百 MiB，凌晨被 OOM Kill，重启后重复。
- **排查命令**：`free -h -s 60` 看趋势 → `ps -eo pid,rss,pmem,cmd --sort=-rss | head` → `cat /proc/PID/smaps_rollup` 看 `Rss/AnonHugePages` → `dmesg -T | grep -i 'killed process'` 拿到被杀进程与 `anon-rss` → Java 用 `jmap -histo:live` 两次对比，Go 用 `pprof heap`。
- **根因**：本地缓存无上限（`Map<String, Object>` 只 put 不 evict）、线程池无界队列堆积任务、堆外内存（Netty `DirectByteBuffer`）未释放、连接对象持有大 buffer。
- **修复**：给缓存加容量与 TTL（Caffeine/Guava 的 `maximumSize`）、给队列设界并拒绝、`-XX:MaxDirectMemorySize` 显式限制；短期用 `oom_score_adj` 保护关键进程、加 swap 只作缓冲不是解法；上线前用 `memory.max` 或容器 limit 兜底，避免拖垮整机。

### 10.3 磁盘满
- **现象**：写日志报 `No space left on device`，`df -h` 显示某分区 100%。
- **排查命令**：`df -h` 定位分区 → `du -x -h --max-depth=1 /var | sort -h` 逐层下钻 → 若 `du` 加起来远小于 `df`，用 `lsof +L1 | sort -k7 -n | tail` 找已删除未释放的文件 → `df -i` 排除 inode 耗尽（海量小文件时 `du -x --inodes --max-depth=1`）。
- **根因**：日志未切割/未清理、`logrotate` 配置错误、核心转储（`core.*`）堆积、已删除但被进程持有的文件（`deleted` 状态）、inode 被小文件占满。
- **修复**：`logrotate` 加 `size`/`rotate`/`compress` 并 `copytruncate` 或 `postrotate` 重开文件；已删除文件用 `: > /proc/PID/fd/N` 立即回收（进程支持的话）或重启进程；不要用 `rm` 删正在写的日志（空间不释放）；给 `/var` 单独分区并加容量告警。

### 10.4 服务响应慢
- **现象**：接口 P99 从 50 ms 涨到 2 s，QPS 下降，偶发超时。
- **排查命令**：`ss -s` 与 `ss -lnt` 的 `Recv-Q/Send-Q` 看 accept 堆积 → `ss -tan state established | wc -l` 看连接数是否触顶 → `top -H -p PID` + `jstack PID` 看线程池是否全部 `WAITING` 在 socket read → `jstat -gcutil PID 1000` 看 Full GC 频率与耗时 → `ss -ti` 看与下游连接的 `rtt/retrans`，或直接看下游监控。
- **根因**：四类最常见——连接数/端口打满（`accept` 队列溢出）、线程池被慢下游占满（无超时，雪崩）、GC 停顿（老年代满或元空间泄漏）、下游超时（DNS、数据库慢查询、第三方限流）。
- **修复**：按根因分别处理——调 `backlog` 与连接池上限、给所有外部调用设连接/读超时并加熔断降级、修 GC 参数或对象生命周期、给下游加重试退避与隔离舱；同时确认是「所有请求都慢」还是「只有某类请求慢」，后者通常是特定下游或特定数据。

### 10.5 网络抖动
- **现象**：跨机房调用间歇性超时，重试后成功，`ping` 正常但大包偶发失败。
- **排查命令**：`netstat -s | grep -iE 'retrans|timeout'` → `ss -ti` 看单连接 `retrans` 与 `rtt` → `mtr -n --tcp -P 端口 目标` 看逐跳丢包 → `ping -M do -s 1472 目标` 测 MTU（1472+28=1500）→ `tcpdump -i eth0 -nn 'tcp and host 目标' -w a.pcap` 回放看重传与 RST → `dig +stats` 排除 DNS。
- **根因**：MTU 不一致（隧道/VPN/overlay 网络实际 MTU 1400，大包被丢且 `ICMP fragmentation needed` 被防火墙拦掉，表现为「小包通、大包卡」）、链路拥塞丢包、中间设备会话超时重置、DNS 解析慢或轮询到不可用 IP。
- **修复**：统一 MTU 或在网关上做 MSS clamp（`iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu`）；对丢包链路调整重传参数或换线路；DNS 加本地缓存与多 `nameserver`；应用层必须有超时、重试与幂等。

## 11 压测与基线
### 11.1 常用压测工具
```bash
wrk -t4 -c200 -d60s --latency http://127.0.0.1:8080/api    # 多线程高并发，输出延迟分布
ab -n 20000 -c 200 -k http://127.0.0.1:8080/api             # 简单，单线程模型，高并发下自身会成瓶颈
sysbench cpu --threads=4 --time=30 run                      # CPU 计算基准
sysbench fileio --file-test-mode=rndrw --file-total-size=4G prepare
sysbench fileio --file-test-mode=rndrw --file-total-size=4G run
```

选型：`wrk` 用 epoll + 多线程，能压出高 QPS 且给 P50/P99；`ab` 简单但单线程、不支持 keep-alive 以外的复杂场景，只适合快速验证；`sysbench` 用于 CPU/内存/磁盘/数据库的**基准能力**测量，不是业务压测。业务压测更常用 `JMeter`、`k6`、`locust`（能写业务脚本、做链路压测）。

### 11.2 建立性能基线
基线是「同一环境、同一数据量、同一压测脚本」下的可复现结果，没有基线的性能数字没有意义。要素：

- **环境固定**：同机型、同核数、同磁盘、同内核参数、同中间件配置；压测机与被压机分离，避免互相干扰。
- **数据量固定**：表行数、缓存命中率、日志量一致，否则「快」可能只是数据少。
- **梯度而非单点**：至少压 1/10/50/100/200 并发，找到**拐点**——QPS 不再随并发增长、RT 开始线性上升的那个点，它就是容量上限。
- **同时记录两侧**：客户端 P50/P90/P99、QPS、错误率；服务端 CPU、内存、连接数、GC 次数与停顿、磁盘 `await`、网络重传。
- **先预热**：JIT 编译、连接池建立、页缓存填充都会让前 30 秒数据失真，至少丢弃前 30~60 秒。

### 11.3 上线前后对比
对比只看三样：**同一接口的 P99**、**饱和点（拐点）位置**、**同等 QPS 下的资源消耗**。P99 涨 20% 以上、或拐点左移，就要在发布单里写清原因。发布前跑一遍基线、发布后跑同样脚本，把两份数据放在一起；如果只有均值好看而 P99 变差，说明是长尾问题（锁竞争、GC、慢下游），不要用平均值掩盖。

## 12 面试问答
### 12.1 load average 怎么算的？为什么包含 D 状态？
- 内核每 5 秒采样一次「运行队列长度 + 不可中断睡眠进程数」，再做指数衰减平均得到 1/5/15 分钟三个值。
- 包含 `D` 状态是因为它是「想干活但被 IO 卡住」的任务，同样代表系统处理能力不足，只统计 `R` 会漏掉 IO 瓶颈。

### 12.2 CPU 使用率怎么算？
- 两次读 `/proc/stat` 的 `cpu` 行，各字段做差后除以总 jiffies 增量，`1 - idle/total` 即使用率；`top`/`mpstat` 都是这个口径。
- `%CPU` 在 `top` 里是单核的百分比，多线程进程可以超过 100%；容器的 CPU 使用率要按 cgroup 的 `cpu.stat` 算，宿主机的 `%CPU` 不代表容器。

### 12.3 内存泄漏和内存增长的区别？
- 增长可能是缓存、连接池、预热、分配器碎片，最终收敛到平台期；泄漏是单调上涨不回落，重启归零后继续涨。
- 判断靠长期采样 `VmRSS`/`smaps_rollup` 看趋势与段落，再用 `valgrind`/ASan/`pprof`/`jmap` 定位到分配点。

### 12.4 iowait 高说明什么？iowait 低就没有 IO 瓶颈吗？
- `wa` 是 CPU 空闲且存在未完成 IO 的时间占比，高说明有 IO 在等，但**不说明 IO 是瓶颈**（也可能只是慢盘拖着一个无关请求）。
- 反过来 `wa` 低也不能排除 IO 问题：IO 完全打满时 CPU 可能没有空闲时间去计 `wa`。判断要看 `iostat -x` 的 `await` 与 `aqu-sz`。

### 12.5 如何定位一个接口变慢？
- 先分层：客户端耗时、网关、应用、下游（DB/缓存/第三方），用链路追踪或日志时间戳定位是哪一段变慢。
- 应用内看线程栈（`jstack`/`pprof`）判断卡在等锁、等 IO 还是 GC；再看 `ss -ti` 与下游 RTT、`jstat` 的 GC 停顿，最后对照发布与流量变化。

### 12.6 perf 和 strace 的区别？
- `strace` 基于 `ptrace`，逐个系统调用拦截，能看到参数、返回值与单次耗时，但开销极大，会把被测进程拖慢几倍到几十倍。
- `perf` 是采样，开销低，能看到 CPU 热点与调用栈，但不给单个调用的参数。定位「慢在哪个系统调用」用 `strace`（短时、限定 `-e`），定位「CPU 花在哪个函数」用 `perf`。

### 12.7 磁盘满了但 du 找不到大文件，为什么？
- 文件已被删除但进程仍持有 fd，inode 和数据块没释放，`df` 仍计入，`du` 遍历目录看不到。用 `lsof +L1` 找，`> /proc/PID/fd/N` 截断或重启进程释放。
- 其他可能：目录被另一文件系统挂载覆盖、稀疏文件（`ls` 大小远大于实际块）、`du` 因权限漏算、inode 耗尽（`df -i`）。

### 12.8 TIME_WAIT 过多怎么办？CLOSE_WAIT 过多呢？
- `TIME_WAIT` 在主动关闭方，等 2MSL，属正常状态。用连接池/keep-alive 减少短连接，或开 `tcp_tw_reuse`、扩大本地端口范围；不要用已移除的 `tcp_tw_recycle`。
- `CLOSE_WAIT` 在被动关闭方，是对端已关闭而本端没 `close()`，属于应用 bug（连接泄漏、异常分支未关闭），只能改代码，调内核参数无效。

### 12.9 服务「假死」、请求无响应但 CPU 不高，怎么查？
- 看进程状态与线程栈：`ps -eo stat` 是否大量 `D`，`jstack`/`gdb` 看线程是否全卡在等锁、等连接或 `socketRead`。
- 再看资源上限：`ss -lnt` 的 accept 队列是否满、`lsof -p | wc -l` 是否到 `ulimit -n`、`iostat -x` 的 `await` 是否异常、`dmesg` 是否有 OOM 或 IO error。

### 12.10 buff/cache 占满内存需要清理吗？
- 不需要。页缓存是可回收的，内存压力下内核会自动回收，`free` 小是正常现象；只有 `available` 低且 `si/so` 非 0 才是问题。
- `drop_caches` 只是让缓存失效、后续读全部落盘，指标短暂好看但整体更慢；`Shmem`、`mlock`、HugePages 那部分根本回收不了，要查具体使用者。

### 12.11 容器里 load 高但容器 CPU 不高，可能是什么？
- `/proc/loadavg` 没有命名空间隔离，读到的是**宿主机**负载；同宿主机的其他容器或系统任务在忙，跟你无关（lxcfs 可修正）。
- 也可能是本容器内有 `D` 状态进程在等 IO（磁盘、网络存储），或受 cgroup 的 `cpu.max` 限流导致排队——此时看 `cpu.stat` 的 `throttled` 计数。

### 12.12 线上服务 CPU 100%，你的排查步骤？
- `top` 定位进程 → `top -H -p PID` 定位线程 → 线程 ID 转十六进制，`jstack`（Java）或 `perf top -p`（C/C++）定位到函数。
- 同时区分类型：`us` 高是业务计算，`sy` 高是系统调用/锁竞争，`si` 高是中断，周期性尖峰看 GC 或 `kswapd`；确认后决定是改代码、调参数还是扩容。
