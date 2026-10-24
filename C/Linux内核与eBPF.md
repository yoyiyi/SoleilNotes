# Linux 内核与 eBPF
面向面试的内核视角笔记：从「系统调用是用户态进入内核的唯一入口」出发，把内核职责、模块、子系统串起来，再用 ftrace / perf / eBPF 回答同一个问题——**内核到底在干什么**。命令以 x86-64、5.10+/6.1 LTS 为准，`#` 表示需 root；`bpftrace` 以 0.19+ 为例，字段名随内核版本变化，以 `bpftrace -lv` 的输出为准。

- 定位：[Linux详解](Linux详解.md) 讲原理与系统管理、[Linux性能排查](Linux性能排查.md) 讲工具矩阵与故障案例，本篇补「内核内部机制 + 动态追踪」这一层。
- 主线：内核是什么 → 怎么扩展（模块）→ 怎么进入（syscall）→ 里面有什么（子系统）→ 怎么看见（ftrace/perf/eBPF）→ 怎么安全地用。

## 1 内核是什么
内核是**唯一直接操作硬件的那段代码**，同时是资源仲裁者：所有进程共享一份 CPU、一份内存、一套设备，必须有代码决定「谁先用、用多少、用不到怎么办」。它跑在最高特权级（x86 的 ring 0），拥有全部物理内存映射与全部指令权限。

| 职责 | 内核里由谁做 | 一个具体问题 |
| --- | --- | --- |
| 进程调度 | 调度类 + 每核运行队列（CFS/EEVDF、RT、DL） | 8 核上 200 个线程，下一个谁跑、跑多久 |
| 内存管理 | 页表、伙伴系统、slab、页缓存与回收 | `malloc` 要一块内存，物理页从哪来、换不换出 |
| 虚拟文件系统 VFS | `super_block`/`inode`/`dentry`/`file` + 具体 fs | 同一个 `read()` 怎么同时支持 ext4、XFS、NFS |
| 网络栈 | socket 层、TCP/IP、`sk_buff`、NAPI、网卡驱动 | 一个包从网线到 `recv()` 缓冲区走了哪些层 |
| 设备驱动 | 字符/块/网络设备模型 + 总线 | 一块 NVMe 盘怎么变成 `/dev/nvme0n1` |
| 安全与隔离 | capability、namespace、cgroup、LSM | 容器里的 root 为什么杀不掉宿主机进程 |

**用户态与内核态**是 CPU 四种特权级里实际用到的两个：用户态不能执行特权指令（改页表、关中断、直接读写端口），访问内核地址会触发缺页并收到 `SIGSEGV`。x86-64 把虚拟地址空间劈成两半，低半区给用户、高半区给内核；开了 KPTI 后用户态页表里只留极少量内核入口代码，代价是每次进出内核多切一次 CR3。切换要保存/恢复寄存器、换内核栈、可能刷 TLB——**一次 syscall 的纯开销在几百纳秒量级**，比函数调用贵两个数量级，这就是「批量读写」「`io_uring`」「vDSO」存在的理由。

版本号是 `主.次.补丁`，次版本号为偶数的是稳定分支，带 `.y` 的是 stable 小版本（5.10/5.15/6.1/6.6 是常见 LTS）；`/lib/modules/$(uname -r)` 是模块的「家」，`kernel/` 放 `.ko`、`modules.dep` 记依赖、`modules.alias` 供 udev 按设备 ID 自动加载，它必须与运行内核严格对应，否则加载报 `Invalid module format`（vermagic 不匹配）。

```bash
uname -r                     # 6.1.0-18-amd64：模块、headers、CVE 都按它对齐
uname -m                     # x86_64 / aarch64：装错架构会 Exec format error
ls /lib/modules/$(uname -r)/kernel/    # 模块按子系统分：fs/ net/ drivers/
```

## 2 内核模块
模块（LKM）是能在运行时插进内核的 `.ko`，本质是**未链接完毕的 ELF 目标文件**：加载时由内核做符号重定位，把对 `printk`、`kmalloc` 的调用接到内核符号表上。它跑在内核态、与内核同一地址空间，写错一个空指针就是整机 panic，没有「进程崩了」这种缓冲。

| 命令 | 作用 | 备注 |
| --- | --- | --- |
| `lsmod` | 列出已加载模块与引用计数 | 内容来自 `/proc/modules` |
| `modinfo x.ko` | 看协议、参数、依赖、vermagic | 加载前先看，确认版本匹配 |
| `insmod x.ko` | 加载指定路径的模块 | **不解决依赖**，缺依赖直接失败 |
| `modprobe x` | 按名字加载并自动带上依赖 | 走 `modules.dep`，生产用这个 |
| `rmmod x` / `modprobe -r x` | 卸载（后者连带清理依赖） | 引用计数非 0 会 `Module is in use` |

最小可加载模块要有 `module_init`/`module_exit` 两个入口，且**必须声明 license**——不声明会被标记为 tainted，之后所有 oops 报告都不再可信。

```c
// hello.c：make 后 sudo insmod hello.ko
#include <linux/init.h>
#include <linux/module.h>

MODULE_LICENSE("GPL");          // 不写会 tainted；GPL 才能用部分导出符号

static int __init hello_init(void)
{
    printk(KERN_INFO "hello: loaded, jiffies=%lu\n", jiffies);
    return 0;                   // 返回非 0 表示加载失败，内核会回滚
}

static void __exit hello_exit(void)
{
    printk(KERN_INFO "hello: unloaded\n");
}

module_init(hello_init);
module_exit(hello_exit);
```

`__init` 把函数放进 `.init.text`，加载完成后这段内存被释放；`__exit` 在模块被编译进内核（而非做成模块）时直接丢弃。Makefile 走的是**内核构建系统**而不是普通 `gcc`，因为需要内核头文件、内核编译参数与符号版本：

```makefile
obj-m += hello.o                 # 告诉 kbuild：这个目标编成模块

KDIR ?= /lib/modules/$(shell uname -r)/build
PWD  := $(shell pwd)

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
```

`KDIR` 指向 `linux-headers-$(uname -r)` 提供的符号链接，容器里编译常因缺它报 `No such file or directory`；`-C` 是先切到内核源码树读顶层 Makefile，`M=` 表示只编当前目录这个外部模块。

```bash
make && sudo insmod hello.ko   # 成功无输出，失败看 dmesg
dmesg -T | tail -3             # 看到 "hello: loaded"
```

**为什么生产环境慎用第三方模块**：① 内核态没有内存保护，越界写静默破坏数据结构，几小时后才在别处 panic，栈已不可信；② 内核内部 ABI 不稳定，`vermagic` 校验逼着每个内核版本重编；③ 非 GPL 模块置 tainted 标志，厂商支持与 `crash` 分析都会先质疑你；④ 几万行 C 跑在 ring 0，安全边界为零，历史上大量 rootkit 就是模块；⑤ 多数「想 hook 一下」的需求，eBPF 不写内核代码就能做完。

**DKMS** 解决「内核一升级模块就失效」：把源码与 `dkms.conf`（含 `PACKAGE_NAME`、`BUILT_MODULE_NAME`、`MAKE` 等）装到 `/usr/src/<pkg>-<ver>/`，每次内核更新自动为新内核重编安装。NVIDIA 驱动、VirtualBox 增强包、ZFS 都走这条路，但它只是**自动重编**，不能让模块跨版本兼容。

```bash
dkms status                        # 各模块在各内核下的编译状态
sudo dkms add -m hello -v 1.0      # 注册源码（需 /usr/src/hello-1.0/dkms.conf）
sudo dkms install -m hello -v 1.0  # 装进 /lib/modules/$(uname -r)/updates/
sudo dkms autoinstall              # 内核升级后自动重编所有注册模块
```

## 3 系统调用
系统调用是用户态**主动**进入内核的唯一正规入口（另两个入口是中断与异常，都是被动的）。以 `write(fd, buf, len)` 为例：

1. glibc 的 `write` 是极薄的包装：调用号放 `rax`，参数放 `rdi/rsi/rdx`，执行 `syscall` 指令。
2. CPU 切到 ring 0，跳到 `entry_SYSCALL_64`：换内核栈、保存用户寄存器、按 `MSR_LSTAR` 进入。
3. `do_syscall_64()` 拿 `rax` 索引 `sys_call_table[]`，调到 `__x64_sys_write` → `ksys_write` → `vfs_write` → `file->f_op->write_iter`（`new_sync_write`）→ 具体文件系统 → 页缓存；要落盘再进块层 `submit_bio` → 调度器 → 驱动。
4. 返回值写回 `rax`，`sysretq` 回到用户态；内核用负的 `-Exxx` 表示错误，glibc 转成 `-1` 并置 `errno`。

```c
// 不用包装函数，直观看到「编号 + 寄存器」就是全部
#include <unistd.h>
#include <sys/syscall.h>

long n = syscall(SYS_write, 1, "hi\n", 3);   // x86-64 上 SYS_write == 1
```

编号表**和架构绑定**：x86-64 与 arm64 完全不同，arm64 根本没有 `open`/`stat`，只有 `openat`/`statx`。本机权威表在 `/usr/include/x86_64-linux-gnu/asm/unistd_64.h`，或 `ausyscall --dump`。

| 编号 | 名称 | 编号 | 名称 | 编号 | 名称 |
| --- | --- | --- | --- | --- | --- |
| 0 | `read` | 16 | `ioctl` | 202 | `futex` |
| 1 | `write` | 39 | `getpid` | 232/233 | `epoll_wait`/`epoll_ctl` |
| 2 | `open` | 41 | `socket` | 257 | `openat` |
| 3 | `close` | 42 | `connect` | 262 | `newfstatat` |
| 9 | `mmap` | 56 | `clone` | 288 | `accept4` |
| 12 | `brk` | 59 | `execve` | 318 | `getrandom` |
| 44 | `sendto` | 62 | `kill` | 332 | `statx` |
| 46 | `sendmsg` | 78/217 | `getdents`/`getdents64` | 435/437 | `clone3`/`openat2` |

`strace` 是理解系统调用最快的工具，但它基于 `ptrace`：被跟踪进程每次调用**停两次**（进入、返回），高并发服务上能把 P99 从 5 ms 拖到 50 ms。

```bash
strace -f -T -tt -y -p 1234            # 所有线程，带耗时/时间戳/fd 路径
strace -c -f -p 1234                   # 按调用汇总次数与总耗时，看谁最费
strace -e trace=openat,stat ./app      # 只看启动时的文件查找（-s 可放大字符串截断）
```

输出里 `openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY) = 3` 的 `= 3` 是返回 fd，`= -1 ENOENT` 才是失败；`-T` 的 `<0.000021>` 要和**同一次调用的其他次**比，跨调用比没有意义。`/proc/<pid>/syscall` 则直接给出进程此刻停在内核哪个调用、参数是什么，比 `strace` 更轻：

```bash
cat /proc/1234/syscall        # 首列是调用号（0=read），后面是寄存器参数，末列是用户栈指针
cat /proc/1234/wchan; echo    # 睡在内核哪个函数，看 D 状态进程必用
```

**vDSO** 是内核映射进每个进程的一段只读代码（`[vdso]`，见 `/proc/self/maps`），专给「高频、结果只依赖内核共享数据」的调用用。`gettimeofday`/`clock_gettime(REALTIME|MONOTONIC)`/`time`/`getcpu` 走它：内核把当前时间与时钟频率放在一页共享内存里，用户态代码直接读，**完全不陷入内核**，约 20 ns，而真 syscall 要 300~500 ns。例外：`CLOCK_BOOTTIME` 仍需 syscall；`getpid` 不走 vDSO，但 glibc 缓存了 PID 所以也很快。

```bash
cat /proc/self/maps | grep vdso         # 看到 [vdso] 段，没有文件路径
strace -c date | grep clock_gettime     # 没有输出：date 取时间走 vDSO
```

## 4 内核关键子系统速览
不求读源码，但要能说清「谁负责什么、数据结构叫什么、出问题看哪里」。

### 4.1 调度器
调度器是**一组按优先级排好的调度类**：`stop` → `deadline` → `realtime` → `fair` → `idle`，高优先级类有活干时低优先级类完全拿不到 CPU。

| 调度类 | 策略 | 一句话 |
| --- | --- | --- |
| fair | `SCHED_NORMAL` | **CFS** 按权重用 `vruntime` 红黑树取最小（≤5.15）；**EEVDF** 改按虚拟截止时间排序（6.6+），延迟更可控、`nice` 更符合直觉 |
| realtime | `SCHED_FIFO`/`RR` | 永远压过普通进程，配错会把机器饿死 |
| deadline | `SCHED_DEADLINE` | 按 `runtime/period` 预留带宽 |

`chrt -p 1234` 看某进程的策略与优先级，`ps -eo pid,cls,rtprio,ni,comm` 里的 `cls` 列 `TS` 是 CFS/EEVDF、`FF`/`RR` 是实时。

### 4.2 内存管理
| 层 | 单位 | 组件 | 关键问题 |
| --- | --- | --- | --- |
| 地址转换 | 4 KiB 页 | 多级页表（x86-64 四级、可选五级） | 虚拟到物理，TLB 命中率，大页减少遍历 |
| 物理页 | 2^order 个连续页 | 伙伴系统 | 大块连续内存够不够、外部碎片 |
| 小对象 | 字节级 | slab/slub（`kmalloc`、`kmem_cache`） | 复用内核对象，不为一小块找整页 |

`PGD→PUD→PMD→PTE` 每级 9 位索引，覆盖 48 位地址；页表项不存在或权限不符时 CPU 触发缺页、内核补页，所以 `malloc` 拿到的内存**第一次访问一定 fault**。伙伴系统按 2 的幂挂空闲链表，分配拆大块、释放与伙伴合并，能防外部碎片但给不出不连续的大块，`/proc/buddyinfo` 就是各 order 的空闲数。slab 把页切成等大小槽位缓存 `task_struct`、`dentry`、`sk_buff` 这类小对象，`slabtop` 里的 `kmalloc-*` 就是它。

```bash
cat /proc/buddyinfo                          # 某 order 长期为 0 = 碎片化
slabtop -s c | head -15                      # 按对象数排 slab 缓存
grep -E 'pgfault|pgmajfault' /proc/vmstat    # major fault 才是真读盘
```

### 4.3 VFS
| 对象 | 代表什么 | 生命周期 | 关键字段 |
| --- | --- | --- | --- |
| `super_block` | 一个已挂载的文件系统实例 | 挂载到卸载 | `s_op`、`s_root`、`s_dev` |
| `inode` | 文件**本身**（元数据 + 数据块位置） | 被引用期间常驻缓存 | `i_ino`、`i_size`、`i_op`、`i_mapping` |
| `dentry` | 名字到 inode 的**映射** | 引用计数 + LRU（dcache） | `d_name`、`d_inode`、`d_parent` |
| `file` | 一个**被打开的**文件（含偏移与标志） | `open` 到 `close` | `f_pos`、`f_flags`、`f_op` |

一次 `open("/data/a.txt")`：路径逐段解析（dcache 命中就不碰盘）→ 未命中让具体 fs `lookup` 读目录 → `iget` 拿 inode（已在缓存则复用）→ `f_op->open` → 分配 `file` 与 fd。所以「删了文件空间不释放」是 `unlink` 只减链接数、删 dentry，而 `file` 还被进程持有，inode 与数据块都不回收。

### 4.4 网络栈
`sk_buff`（skb）是网络栈的通货：一个包从驱动进来就是一块 skb，穿过各层时**只移动头部指针**（`data/head/tail/end`）尽量不拷贝，里面记着协议头偏移、目标 socket、路由、校验和状态。

收包（NAPI）：网卡 DMA 写环形缓冲区 → **硬中断**只记录并触发 NAPI → 软中断 `NET_RX_SOFTIRQ` 里 `net_rx_action` 按预算（`netdev_budget`，默认 300）轮询收包 → GRO 合并 → `ip_rcv` → `tcp_v4_rcv` 找 socket、入接收队列、回 ACK、唤醒等待者 → 用户态 `read`/`recvmsg` 拷进用户缓冲区。发包反向：`tcp_sendmsg` 切段算校验和 → `ip_queue_xmit` → 邻居子系统取 MAC → `dev_queue_xmit` → qdisc → 驱动 `ndo_start_xmit` → DMA；中间任何队列满都表现为「丢包或延迟」。

```bash
ss -ti                                   # 单连接 rtt/retrans/cwnd/发送队列
grep -E '^Tcp:' /proc/net/snmp           # TCP 全局计数：重传、队列溢出、校验和错
head -3 /proc/net/softnet_stat           # 每核收包统计，第 2 列是 backlog 丢弃
```

### 4.5 中断与软中断
中断处理劈成两半：**上半部**关中断、不能睡眠，只做「应答设备 + 记录 + 触发下半部」；耗时的部分延后。

| 机制 | 上下文 | 能否睡眠 | 典型用途 |
| --- | --- | --- | --- |
| 硬中断 | 中断上下文 | 否 | 收包第一跳、时钟、设备应答 |
| `softirq` | 中断返回或 `ksoftirqd` 线程 | 否 | `NET_RX/TX`、块层、定时器、RCU |
| `tasklet` | 基于 softirq | 否 | 老驱动的延后处理（同一 tasklet 不并行） |
| `workqueue` | 内核线程 | **能** | 需要阻塞、可能睡眠的工作 |

软中断有固定向量（`HI`/`TIMER`/`NET_TX`/`NET_RX`/`BLOCK`/`RCU`…），由 `do_softirq` 执行，**不能拿 mutex、不能 `copy_from_user`**；处理不完就挂到 `ksoftirqd/N` 慢慢做，这就是 `si` 高时 `ksoftirqd` 吃 CPU 的原因。

```bash
cat /proc/softirqs                  # 每核各软中断累计次数，看是否集中在一核
mpstat -I SUM -P ALL 1 3            # 硬中断速率；-I SCPU 看软中断
```

## 5 可观测性三件套
三种手段回答三个不同问题，混着用才完整：

| 维度 | 回答什么 | 数据形态 | 开销 | 代表 |
| --- | --- | --- | --- | --- |
| metrics 指标 | **整体**状态与趋势 | 预聚合的计数器 | 极低，可常开 | `/proc`、`/sys`、cgroup、node_exporter |
| tracing 追踪 | **每一次**事件的上下文：谁、什么参数、多久 | 逐事件记录 | 中到高 | ftrace、perf trace、bpftrace、BCC |
| sampling 采样 | 时间花在**哪里**（热点分布） | 定频快照的栈/PC | 低且可控 | `perf record`、`perf top`、火焰图 |

顺序固定：**先 metrics 判断是什么资源 → 再 tracing 定位到具体调用与参数 → 最后 sampling 深挖代码路径**。反过来（一上来 `strace -f`）通常既慢又抓不到重点。`/proc` 是进程与内核状态的文本快照（读取时用 `seq_file` 即时生成），`/sys` 是设备与驱动的结构化属性（`echo` 进去能改行为），cgroup 是按层级限流与统计。

```bash
head -2 /proc/stat                        # CPU 累计 jiffies，差分算使用率
grep -E 'VmRSS|Threads' /proc/1234/status
cat /sys/fs/cgroup/demo/memory.current    # cgroup v2 用量；cpu.stat 看 throttled
```

## 6 ftrace
ftrace 是内核**自带**的追踪框架（不用装东西、不用编译），靠编译期在函数入口插桩（`mcount`/`fentry`）记录调用与耗时。挂上 debugfs 后所有控制都在 `/sys/kernel/debug/tracing`：`current_tracer` 选 tracer，`set_ftrace_filter`/`set_graph_function` 限定函数，`trace` 一次性读全缓冲、`trace_pipe` 流式读走即消费，`buffer_size_kb` 调每核缓冲区（事件多会丢）。

```bash
mount -t debugfs none /sys/kernel/debug       # 多数发行版已自动挂载
cd /sys/kernel/debug/tracing
cat available_tracers                         # 支持哪些 tracer
wc -l < available_filter_functions            # 可插桩的函数数（几万）
```

| tracer | 作用 | 典型场景 |
| --- | --- | --- |
| `function` | 记录每次函数调用（只有名字，无参数） | 谁在被高频调用 |
| `function_graph` | 记录调用链与每层耗时（缩进） | 一次 IO 慢在哪一层 |
| `irqsoff`/`preemptoff` | 关中断/关抢占的最长延迟与原因 | 抖动、实时性 |
| `wakeup`/`wakeup_rt` | 唤醒到真正上 CPU 的延迟 | 「偶发卡顿几十毫秒」 |

**例 1：一次 open 走了哪些层**

```bash
cd /sys/kernel/debug/tracing
echo function_graph > current_tracer
echo do_sys_openat2 > set_graph_function
echo 1 > tracing_on; cat /etc/hostname > /dev/null; sleep 0.2; echo 0 > tracing_on
cat trace | head -40        # 每行「耗时 | 函数名」，DURATION 列是微秒
```

只看两件事：**哪一层的 `DURATION` 异常大**，以及**路径里有没有意外的函数**（本该命中 dcache 却又进了 `ext4_lookup` 读盘）。

**例 2：某函数被调多频繁（`function` + 过滤器）**

```bash
echo function > current_tracer
echo 'vfs_*' > set_ftrace_filter     # 只留 vfs_ 开头，支持通配
echo 1 > tracing_on; sleep 1; echo 0 > tracing_on
grep -c vfs_read trace              # 一秒内的调用次数
```

`set_ftrace_filter` 是性能关键：不设过滤器时**所有**函数都插桩，开销能到几十个百分点。直接 `> set_ftrace_filter` 是把它当命令来清空，不是重定向到普通文件。

**例 3：流式观察与调度延迟（`trace_pipe`）**

```bash
echo 'tcp_*' > set_ftrace_filter
timeout 5 cat trace_pipe | head -20       # 读走即消费，适合长时间 grep

echo wakeup_rt > current_tracer
echo 1 > tracing_on; sleep 3; echo 0 > tracing_on
grep delay trace | sort -t: -k2 -n | tail -5   # 微秒；几十以内正常，毫秒级说明抢不到 CPU
```

`wakeup`/`wakeup_rt` 的 `delay` 是唤醒到上 CPU 的微秒数；到毫秒级就是「该跑的时候没抢到 CPU」——CPU 饱和、中断风暴或实时任务压住了它，比看 `load` 直观得多。

## 7 perf
`perf` 是 `perf_events` 子系统的用户态前端，能力比 ftrace 宽：既能读**硬件性能计数器**（PMU），也能采**软件事件与 tracepoint**，还带调用栈。

| 子命令 | 回答什么 | 关键点 |
| --- | --- | --- |
| `perf stat` | 周期、指令、cache miss、分支预测失败 | 效率类问题，`-e` 指定事件 |
| `perf top` | 现在最热的函数 | 实时，`-p` 限进程，`-g` 带调用链 |
| `perf record -g` | 采一段时间落盘 `perf.data` | 采样，`-F 99` 定频 |
| `perf report` | 打开 `perf.data` 看热点与调用链 | `--stdio` 可脚本化 |
| `perf trace` | 类 `strace` 的系统调用时间线 | 基于 raw_syscalls tracepoint，开销低得多 |

| 事件类别 | 例子 | 说明 |
| --- | --- | --- |
| 硬件 PMU | `cycles`、`instructions`、`cache-misses`、`branch-misses` | 需 CPU 支持，`-e x:u`/`:k` 限定用户/内核 |
| 软件 | `task-clock`、`page-faults`、`context-switches`、`cpu-migrations` | 内核计数，任何机器都有 |
| tracepoint | `sched:sched_switch`、`syscalls:sys_enter_openat`、`block:block_rq_issue` | 静态埋点，字段稳定 |
| kprobe/uprobe | `probe:tcp_retransmit_skb` | 动态插桩，随内核版本失效 |

```bash
perf stat -p 1234 sleep 5                        # 默认事件组：cycles/instructions/cache/branch
perf stat -e 'syscalls:sys_enter_write' -a sleep 3
perf top -p 1234 -g                              # 实时热点，TUI 里回车展开调用链
perf record -F 99 -g -p 1234 -- sleep 30         # 99 Hz 采 30 秒
perf trace -e openat -p 1234                     # 低开销系统调用追踪
```

`perf stat` 两个比值最有用：**IPC**（`instructions/cycles`）低说明在等内存或分支预测失败，**cache-misses 占比**高说明局部性差。采完接 FlameGraph 就是火焰图：

```bash
perf record -F 99 -g -p 1234 -- sleep 30 && perf script > out.perf
./FlameGraph/stackcollapse-perf.pl out.perf > out.folded
./FlameGraph/flamegraph.pl out.folded > flame.svg
```

**权限**是 perf 最常见的坑，几乎所有「什么都采不到」都因为它。`kernel.perf_event_paranoid`：`-1` 不限制；`0` 允许 CPU 级事件但禁 raw tracepoint 采样；`1` 禁 CPU 级事件（不能 `-a`）；`2` 禁内核态采样（**多数发行版默认**，内核栈残缺）；`3` 完全禁止非特权 perf（较新内核）。

```bash
cat /proc/sys/kernel/perf_event_paranoid
sysctl -w kernel.perf_event_paranoid=1        # 临时放开；持久化写 /etc/sysctl.d/
perf record -g --call-graph dwarf -p 1234 -- sleep 10   # 栈不全时改用 dwarf 展开
```

## 8 eBPF 是什么
eBPF 是内核里一个**带验证器的虚拟机**：用户态把一段受限字节码交给内核，验证器静态证明它安全后 JIT 成本机指令，挂到指定事件上运行。它把「在内核里跑自定义逻辑」从「写模块、编译、重启、可能 panic」变成「一条命令、可随时卸载、崩了只丢事件」。

| 阶段 | 时间 | 关键变化 |
| --- | --- | --- |
| eBPF | 3.18 | 从 cBPF 包过滤演进而来：10 个 64 位寄存器、map、JIT、可挂 kprobe |
| 生态 | 4.x | tracepoint 4.7、XDP 4.8、bpftrace/BCC 起来 |
| 可移植 | 5.2+ | BTF + CO-RE，一次编译跨版本运行 |
| 更安全 | 5.3/5.8 | 有界循环、百万指令、`CAP_BPF` 拆分、ring buffer |

虚拟机形态：11 个 64 位寄存器（`r0` 返回值、`r1~r5` 传参、`r6~r9` 跨调用保存、`r10` 只读栈帧指针）、512 字节栈、定长 64 位指令；内存只能经 map、helper 或 `bpf_probe_read_*` 访问。

**验证器**是安全性的全部来源，加载时做静态分析（不执行程序）：

- **控制流无环**：必须是 DAG；5.3 起允许有界循环，但要能证明上界。
- **内存访问合法**：指针带类型与范围（`PTR_TO_CTX`/`PTR_TO_MAP_VALUE`/`PTR_TO_STACK`），越界、未初始化读、栈越界一律拒绝，读 map 前必须先判空。
- **不越权、规模有上限**：helper 按程序类型白名单发放；指令数（5.2 起 100 万）与复杂度都有上限，避免加载时把内核卡死。

所以「eBPF 为什么不会把内核搞崩」的答案是：**它不能执行任意指令，只能调白名单 helper、只能访问被证明合法的内存、必须终止；验证器不过就不加载。** 代价是「验证器认为不安全的一律拒绝」，写代码时常要跟它搏斗。

| 附着点 | 触发时机 | 典型用途 |
| --- | --- | --- |
| `kprobe`/`kretprobe` | 任意内核函数入口/返回 | 追踪内部函数参数与返回值 |
| `uprobe`/`uretprobe` | 用户态函数 | 无侵入观测业务代码、运行时 |
| `tracepoint` | 内核静态埋点 | 系统调用、调度、TCP、块层（字段稳定） |
| `perf_event` | 硬件/软件事件溢出 | CPU 采样、周期计数 |
| `XDP` | 驱动收包最早处 | DDoS 清洗、负载均衡（可 `XDP_DROP`） |
| `cgroup` | 按 cgroup 生效 | 容器级网络策略与限流 |
| `fentry`/`fexit` | 函数入口/出口（BTF，5.5+） | 比 kprobe 快得多，生产首选 |

## 9 bpftrace 实战
`bpftrace` 是 eBPF 的高级语言：一行脚本 = 一个 eBPF 程序 + 一个 map + 一段输出逻辑，适合临时排查。

```bash
sudo apt install bpftrace        # Debian/Ubuntu；RHEL 系用 dnf install bpftrace
bpftrace -l 'tracepoint:syscalls:sys_enter_*' | head   # 列可用探针
bpftrace -lv 'tracepoint:tcp:tcp_retransmit_skb'       # 看该探针的 args 字段
```

语法骨架是 `探针 / 过滤 / { 动作 }`，可写多个探针：

| 探针 | 写法 | 触发 |
| --- | --- | --- |
| 程序级 | `BEGIN` / `END` | 启动时 / Ctrl-C 退出时 |
| 内核函数 | `kprobe:vfs_read` / `kretprobe:vfs_read` | 函数入口 / 返回 |
| 用户函数 | `uprobe:/bin/bash:readline` | 二进制里的符号 |
| 静态埋点 | `tracepoint:syscalls:sys_enter_openat` | 内核埋点 |
| 定时 | `interval:s:5` | 每 5 秒（也可 `ms:100`） |

内置量与聚合：`pid`/`tid`、`comm`（进程名，15 字符）、`nsecs`（单调纳秒时间戳）、`arg0..argN`（kprobe 参数，寄存器值，要按类型转）、`args->xxx`（tracepoint 字段）、`retval`、`probe`；`count()/sum()/avg()/hist()/lquantize()` 聚合，`@name[key]` 声明 map。

**六个可直接用的脚本**（都是单条命令，Ctrl-C 结束）：

```bash
# 1. 统计各类系统调用次数：按探针名聚合，一眼看出谁最频繁
bpftrace -e 'tracepoint:syscalls:sys_enter_* { @[probe] = count(); }'

# 2. 按进程统计 read 字节数（只算成功的）
bpftrace -e 'tracepoint:syscalls:sys_exit_read /args->ret > 0/ { @bytes[comm] = sum(args->ret); }'

# 3. 追踪 openat 打开的文件路径
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%-16s %s\n", comm, str(args->filename)); }'

# 4. 统计 TCP 重传，按「源端口→目的端口」聚合，定位是哪条连接
bpftrace -e 'tracepoint:tcp:tcp_retransmit_skb { @[args->sport, args->dport] = count(); }'

# 5. 慢 IO：issue 到 complete 的延迟直方图（微秒），等价于 biolatency
bpftrace -e 'tracepoint:block:block_rq_issue { @start[args->dev, args->sector] = nsecs; }
             tracepoint:block:block_rq_complete /@start[args->dev, args->sector]/ {
               @us = hist((nsecs - @start[args->dev, args->sector]) / 1000);
               delete(@start[args->dev, args->sector]);
             }'

# 6. 函数耗时直方图：kprobe 记起点、kretprobe 算差值，按线程号区分
bpftrace -e 'kprobe:vfs_read { @start[tid] = nsecs; }
             kretprobe:vfs_read /@start[tid]/ {
               @ns = hist(nsecs - @start[tid]);
               delete(@start[tid]);
             }'
```

`hist()` 打 2 的幂次桶加 `|@@@@` 柱状，`[64, 128)` 表示落在该区间的事件数。`@start[tid]` 用线程号做键是并发下的正确做法：用 `pid` 会让同进程多线程互相覆盖，用全局变量则完全错。几个坑：`args->filename` 是 `const char *`，必须 `str()` 才是字符串；`@start[tid]` 必须配 `delete()`，否则 map 无限增长吃满内存；`arg0..` 只是寄存器值，要转成 `struct xxx *` 才有字段且字段名随版本变，所以**优先用 tracepoint**；通配探针会挂几十上百个点，热路径上开销可观。

## 10 BCC 与 libbpf 简介
`bpftrace` 适合一次性脚本，**BCC** 适合天天用、要打包分发的工具集：Python/Lua 前端 + C 写的 eBPF 程序，运行时用 `clang` 现场编译（依赖内核头文件，启动慢）。装 `bcc-tools` 后 `/usr/share/bcc/tools/` 有上百个开箱脚本：

| 工具 | 作用 | 典型用法 |
| --- | --- | --- |
| `execsnoop` | 追踪 `exec`，抓短命进程 | 查谁在疯狂 fork/exec |
| `opensnoop` | 追踪 `open`，含失败 | `-e` 只看失败，查配置找不到 |
| `biolatency` | 块设备 IO 延迟直方图 | `-m -D` 按盘分开看 |
| `biosnoop` | 每次 IO 一行：进程、盘、扇区、延迟 | 定位谁在慢 IO |
| `tcplife` | 每条 TCP 连接的起止、字节数、时长 | 长连接/短连接分布 |
| `runqlat` | 运行队列等待直方图 | 调度延迟，比 load 精确 |

**自写程序的编译链路**（libbpf + CO-RE）：写 `<name>.bpf.c`（`SEC("kprobe/xxx")` 标注程序、`__uint(type, BPF_MAP_TYPE_HASH)` 定义 map）→ `bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h` → `clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -c x.bpf.c -o x.bpf.o`（**必须 `-g`**，BTF 在调试段）→ `bpftool gen skeleton x.bpf.o > x.skel.h` → 用户态 `x_bpf__open_and_load()` + `x_bpf__attach()`，链接 `-lbpf -lelf -lz`。

**CO-RE 一句话**：编译时把「结构体字段偏移」记成重定位信息，加载时由 libbpf 用目标机 BTF 改写成实际偏移，所以同一个 `.o` 能跨内核版本跑；前提是 `/sys/kernel/btf/vmlinux` 存在（`CONFIG_DEBUG_INFO_BTF`）。BCC 的「每次现场编译」正是 CO-RE 之前的老办法。

## 11 安全与限制
eBPF 的能力等于「在内核里执行代码」，所以权限模型一直在收紧（5.8 起拆分）：

| 动作 | 5.8 之前 | 5.8+ |
| --- | --- | --- |
| 加载/查询 BPF 程序与 map | `CAP_SYS_ADMIN` | `CAP_BPF` |
| 打开 perf 事件、读内核采样 | `CAP_SYS_ADMIN` | `CAP_PERFMON` |
| 挂 XDP/tc、改网络配置 | `CAP_NET_ADMIN` | `CAP_NET_ADMIN`（不变） |

`kernel.unprivileged_bpf_disabled` 控制普通用户能否调 `bpf()`：`0` 允许但仅限 socket filter 等极少数类型；`1` 已禁用且**不可逆**（只能重启）；`2` 开机即禁用且运行时不可改（5.13+，主流发行版默认）。

| 能力 | 最低内核 |
| --- | --- |
| eBPF 基础 + `bpf()` | 3.18 |
| kprobe 程序 / tracepoint 程序 | 4.1 / 4.7 |
| XDP / BTF | 4.8 / 4.18 |
| CO-RE（libbpf 重定位） | 5.2 |
| `fentry`/`fexit` / `CAP_BPF` 拆分 | 5.5 / 5.8 |

容器里最容易翻车：容器与宿主机**共用内核**，所以内核版本看宿主机、权限看 capability 与 seccomp。

```bash
# 排查时给足能力（生产别这么干）
docker run --rm -it --privileged --pid=host \
  -v /sys/kernel/debug:/sys/kernel/debug nicolaka/netshoot bpftrace -l 'kprobe:*'
# 最小集合：只给 bpf + perfmon（挂 XDP/tc 再加 net_admin）
docker run --rm -it --cap-add=BPF --cap-add=PERFMON --security-opt seccomp=unconfined mytool
```

常见报错：`Operation not permitted` 多为缺 `CAP_BPF`/`CAP_PERFMON` 或被 seccomp 拦了 `bpf()`；RHEL 8/9 上还可能是内核 lockdown；读不到 `/sys/kernel/debug/tracing` 是没挂 debugfs 或缺 `CAP_SYS_ADMIN`；没有 `/sys/kernel/btf/vmlinux` 则 CO-RE 退化成现场编译。

**生产使用风险**：① kprobe 挂在热路径（`tcp_sendmsg`、`vfs_read`）上，每秒百万次就是百万次额外开销，要用 tracepoint/`fentry` 并加过滤与限时；② perf/ring buffer 有大小，高频事件会丢，要看 lost events；③ 验证器本身出过多个提权 CVE（如 `CVE-2021-3490`），内核得跟着打补丁；④ 脚本必须带 `timeout` 且能干净退出；⑤ XDP 写错会把包全 drop，变更必须灰度。

## 12 面试问答
### 12.1 用户态怎么进入内核？有几种方式？
- **系统调用**（主动）：`syscall` 指令 → `entry_SYSCALL_64` → `do_syscall_64` 查表分发，唯一正规入口。
- **中断/异常**（被动）：外设或时钟触发中断、缺页或除零触发异常，内核先处理再决定是否给进程发信号；32 位老接口是 `int 0x80`/`sysenter`。

### 12.2 什么是软中断？和硬中断、tasklet、workqueue 什么关系？
- 硬中断关中断执行、只做最少的活；软中断是延后执行的「下半部」，**不能睡眠**，有固定向量，同一向量可在多核并行。
- tasklet 建在 softirq 之上但同一 tasklet 不并行；workqueue 跑在内核线程、**可以睡眠**。`si` 高说明软中断吃 CPU：网卡小包多、队列没做多队列/RPS、或块层 IO 太碎。

### 12.3 ftrace 和 perf 有什么区别？
- ftrace 是内核内置的**函数级追踪**，编译期插桩，给精确调用链与每层耗时，不带参数与调用栈。
- perf 是**采样 + 事件**框架，能读 PMU/tracepoint/kprobe，给调用栈与火焰图、开销低，但不擅长逐次调用链。精确路径用 ftrace，热点分布用 perf，要参数与自定义聚合用 eBPF。

### 12.4 eBPF 为什么不会把内核搞崩？
- 程序不是任意机器码，只能调白名单 helper、只能访问被验证合法的内存、必须有界终止。
- 加载前验证器做静态分析（无环、指针类型、栈边界、map 判空、指令上限），不过就拒绝；JIT 后受同一套约束，最坏结果是返回错误或丢事件，还能随时 detach。

### 12.5 如何定位一个系统调用慢？
- 先确认慢在哪层：`strace -T -tt -p PID`（短时、限定 `-e`）看单次耗时，或 `perf trace` 低开销看时间线。
- 看内部在等什么：`/proc/PID/wchan`、`/proc/PID/stack` 看睡在哪；块层 `biolatency`/`iostat -x` 看 `await`，网络 `ss -ti` 看 `rtt/retrans`；再用 `bpftrace` 对该调用做 `hist()` 区分「一直慢」还是「只有 P99 慢」。

### 12.6 kprobe 和 tracepoint 有什么区别？怎么选？
- kprobe 是**动态**插桩：任意内核函数都能挂，灵活但依赖函数名与参数、内核改版失效、开销更高。
- tracepoint 是**静态**埋点：`TRACE_EVENT` 定义好的位置，字段稳定有 ABI 保证、开销低，但只能追「作者埋了的地方」。优先 tracepoint，没有对应埋点才用 kprobe，性能敏感用 `fentry`/`fexit`。

### 12.7 内核模块和 eBPF 都能扩展内核，怎么选？
- 模块是**任意内核代码**，能改数据结构、注册回调、实现驱动，能力与风险都无上限，需编译签名、与内核版本绑定。
- eBPF 是**受限沙箱**，不能改内核逻辑、多数类型不能睡眠，但可热加载、可验证、可移植。要**改变内核行为**用模块，只是**观测或轻量干预**用 eBPF。

### 12.8 gettimeofday 为什么不需要陷入内核？
- 内核把当前时间与时钟频率放在一页只读共享内存里，vDSO 是映射进用户空间的代码段，直接读并计算，全程不陷入内核，约 20 ns 对 300 ns。
- 用 `seqcount` 做无锁重试：读前读后序号一致才采信，因为内核可能正在更新。`CLOCK_BOOTTIME` 仍需 syscall。

### 12.9 容器里跑 bpftrace 报 `Operation not permitted`，怎么排查？
- 看能力：`capsh --print`，5.8+ 需要 `CAP_BPF` + `CAP_PERFMON`，老内核一律 `CAP_SYS_ADMIN`；挂 XDP/tc 还要 `CAP_NET_ADMIN`。
- 再看 seccomp/AppArmor 是否拦了 `bpf()`、`unprivileged_bpf_disabled` 是否为 2、`/sys/kernel/debug` 有没有挂上、有没有 BTF。

### 12.10 一个包从网卡到应用 read 到，中间经过什么？
- 网卡 DMA 写环形缓冲区 → 硬中断记录并触发 NAPI → 软中断 `NET_RX_SOFTIRQ` 按预算轮询收包 → GRO 合并 → `ip_rcv` → `tcp_v4_rcv` 找 socket、按序入接收队列、回 ACK、唤醒等待者 → 用户态 `read`/`recvmsg` 拷走。
- 任一环节队列满（`softnet_stat` 的 dropped、`ss` 的 `Recv-Q`、`netdev_max_backlog`）都表现为丢包或延迟高，要按这条链路逐段看计数。
