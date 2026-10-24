# Linux 面试题 40 问

面向运维/后端面试的速查版：先给结论，再给定位命令与边界；默认以主流 systemd 发行版为例，不同发行版以文档为准。

## 一、命令与文件

### Q1 软链接和硬链接的区别？
**答**：
- 硬链接是同一 inode 的另一个目录项，链接数 +1，删掉任一名字数据仍在；不能跨文件系统，通常也不能指向目录。
- 软链接是独立 inode，内容是目标路径，可跨文件系统、可指向目录；目标删除后变成悬挂链接。
- 用 `ln` 建硬链接、`ln -s` 建软链接，`ls -li` 或 `stat` 可看 inode 与链接数。

```bash
ln data.txt hard.txt
ln -s /data/app/current current
ls -li data.txt hard.txt current
```

### Q2 grep 和 find 有什么区别？怎么找大文件？
**答**：
- `grep` 按文件内容/行过滤，`find` 按路径、名称、大小、时间等元数据遍历目录树，二者解决的不是一类问题。
- 找大文件用 `find` 的 `-size`，按字节排序；GNU find 可用 `-printf`，其他实现可改 `-exec ls -lh`。
- 搜内容用 `grep -r`，配合 `--include` 限定文件类型，比先 `find` 再 `xargs` 更少踩空格与转义坑。

```bash
find /var -xdev -type f -size +1G -printf '%s %p\n' 2>/dev/null | sort -nr | head
grep -rn --include='*.log' 'ERROR' /var/log
```

### Q3 如何统计日志里访问量 Top10 的 IP？
**答**：
- 思路是取第一列 IP → 排序 → 相邻去重计数 → 按次数倒序 → 取前 10。
- `uniq -c` 只合并相邻行，所以必须先 `sort`；大文件可加 `LC_ALL=C` 提速。
- 若日志带代理头或 JSON 格式，要先按实际字段取 IP，必要时再按时间段 `grep` 过滤。

```bash
awk '{print $1}' access.log | sort | uniq -c | sort -nr | head -10
```

### Q4 管道和重定向的区别？
**答**：
- 管道 `|` 连接两个进程：前一个的 stdout 作为后一个的 stdin，数据在内核缓冲区流动，不落盘。
- 重定向改变命令自身的 fd 指向，通常指向文件；`>` 覆盖、`>>` 追加、`<` 作为输入。
- 管道默认只传 stdout，stderr 仍在终端；需要一起传时用 `2>&1` 或 bash 的 `|&`。

```bash
ps aux | grep nginx
command > out.log 2>&1
```

### Q5 2>&1 是什么意思？顺序为什么重要？
**答**：
- fd 1 是 stdout，fd 2 是 stderr；`2>&1` 是让 fd 2 复制 fd 1 当前的指向，不是“把 2 变成 1”。
- `cmd > out 2>&1` 先让 1 指向文件，再让 2 跟到同一文件，二者都进文件。
- `cmd 2>&1 > out` 中 2 先复制了终端，随后 1 才转向文件，stderr 仍打在终端，顺序不能反。
- `&>` 是 bash 简写；写脚本若要兼容 POSIX sh，优先 `> out 2>&1`。

```bash
cmd > out.log 2>&1
cmd 2>&1 > out.log   # 错误顺序：stderr 仍在终端
```

### Q6 tar 打包时如何排除目录？
**答**：
- GNU tar 用 `--exclude=PATTERN`，匹配的是归档成员路径（如 `app/logs`），不是宿主机绝对路径，所以别写 `/var/log`。
- 可多次指定 `--exclude`，或用 `--exclude-from=file` 批量排除；`--exclude-vcs` 可排除 `.git`、`.svn`。
- 打包后先 `tar -tzf` 看清单，确认日志、缓存、`.git` 没有被打进去。

```bash
tar -czf app.tar.gz --exclude='app/logs' --exclude='app/.git' app
tar -tzf app.tar.gz | head
```

### Q7 怎么查内核版本和发行版版本？
**答**：
- 内核用 `uname -r`，全量信息 `uname -a`，架构 `uname -m`。
- 发行版用 `cat /etc/os-release` 最通用；`hostnamectl` 可同时给出 OS、内核和架构。
- 老系统可看 `/etc/redhat-release`、`/etc/debian_version`；容器里的 `os-release` 可能来自镜像而非宿主机。

```bash
uname -r
cat /etc/os-release
hostnamectl
```

## 二、权限与用户

### Q8 进入目录、读取文件分别需要什么权限？chmod 755 是什么含义？
**答**：
- 目录：`x` 进入/穿越，`r` 列出文件名，`w` 在目录内创建、删除、改名（且需 `x`）。
- 文件：`r` 读内容，`w` 改内容，`x` 执行；删除文件看父目录的 `w`，不看文件自身权限。
- `chmod 755` 即 `rwxr-xr-x`：属主读写执行，组和其他人读+执行，常用于目录和可执行脚本。
- 755 对普通数据文件偏大（其他人可执行），一般文件用 644；目录要进入就必须有 `x`。

```bash
chmod 755 /opt/app/bin/start.sh
ls -ld /opt/app /opt/app/bin/start.sh
```

### Q9 umask 022 新建文件和目录的权限是多少？
**答**：
- 文件基准 666、目录基准 777；实际权限 = 基准 & ~umask，022 屏蔽 group/other 的写位。
- 结果：文件 644（`rw-r--r--`），目录 755（`rwxr-xr-x`）。
- 常用 027 得 640/750；umask 只影响之后新建的对象，不改已有文件。
- 临时 `umask 027`，永久写 `~/.bashrc` 或 `/etc/profile`；root 的默认 umask 常见为 022。

```bash
umask 022
touch f; mkdir d; ls -ld f d
```

### Q10 SUID 有什么用，有什么风险？
**答**：
- SUID 让执行者临时以文件属主身份运行，典型是 `/usr/bin/passwd` 以 root 权限改 `/etc/shadow`。
- `chmod u+s` 或数字 `4755`；`ls -l` 中属主执行位显示 `s`，没有 `x` 时显示大写 `S`。
- 风险是提权面：程序若有命令注入、溢出或可劫持的配置，就可能被用来拿 root，也可能被留后门。
- 定期用 `find` 审计，去掉不必要的 SUID，敏感挂载加 `nosuid`。

```bash
find / -xdev -perm -4000 -type f 2>/dev/null
chmod u-s /path/to/bin
```

### Q11 普通用户如何执行 root 命令？
**答**：
- 首选 `sudo`：按 `/etc/sudoers` 授权，命令有审计日志；改配置用 `visudo`，避免语法错误锁死提权。
- 最小权限授权，例如只允许重启某个服务；不要为了方便写 `NOPASSWD: ALL`。
- 需要完整 root shell 用 `sudo -i` 或 `sudo -s`；`su -` 要共享 root 密码，不利于审计。
- 先把用户加入发行版对应的 `sudo` 或 `wheel` 组；用 `sudo -l` 查看当前能执行什么。

```bash
sudo systemctl restart nginx
sudo -l
```

## 三、进程与内存

### Q12 进程状态 D 是什么？
**答**：
- 不可中断睡眠：进程在内核态等 IO 或锁，信号要等系统调用返回才处理，所以 `kill -9` 也可能暂时不生效。
- 少量短暂的 D 正常；大量 D 会推高 load 但 CPU 空闲，常见于磁盘故障、NFS 失联、块设备卡住。
- 用 `ps` 的 `stat` 与 `wchan` 定位，再结合 `dmesg`、`iostat -x` 和挂载点排查。

```bash
ps -eo stat,pid,wchan:30,cmd | awk '$1 ~ /^D/'
dmesg -T | tail -50
```

### Q13 僵尸进程怎么产生、怎么处理？
**答**：
- 子进程退出后，内核保留 PID、退出码等父进程 `wait()`/`waitpid()`，其间状态为 Z；父进程不回收就会堆积，最终耗尽 PID 表。
- 僵尸已释放大部分内存，`kill -9` 对它无效；根因是父进程的回收逻辑，应该在信号处理或事件循环里 wait。
- 临时处理是找到并重启/杀掉父进程，让 PID 1 或 subreaper 收养并回收；容器里 PID 1 不回收同样会堆。

```bash
ps -eo stat,ppid,pid,cmd | awk '$1 ~ /^Z/'
kill -TERM 1234   # 1234 换成僵尸的父进程 PID
```

### Q14 孤儿进程和僵尸进程有什么区别？
**答**：
- 孤儿是父进程先退出、自己还在运行的进程，会被 PID 1（或 subreaper）收养，继续正常工作，通常无害。
- 僵尸是子进程已退出、父进程还在但不 `wait()`，只剩 PID 与退出码，占进程表项。
- 一句话：孤儿还活着、换了爹；僵尸已死、没注销。处理重点分别是“是否需要终止”和“让父进程回收”。

### Q15 kill -9 和 kill -15 有什么区别？为什么有的进程 -9 也杀不掉？
**答**：
- `-15` 是 SIGTERM，默认终止信号，可被捕获，程序能刷盘、关连接、优雅退出，应优先使用。
- `-9` 是 SIGKILL，不可捕获、不可忽略，由内核直接杀，可能丢数据或留下脏状态，是最后手段。
- 杀不掉常见原因：进程处于 D 状态等 IO 返回、已经是僵尸、被父进程或 supervisor 反复拉起、本身是内核线程。
- 先确认 PID 与权限，排除守护进程重启；`kill -9` 后仍显示 Z，说明要处理的是它的父进程。

```bash
kill -15 1234
sleep 2; kill -9 1234
ps -o stat,pid,ppid,cmd -p 1234
```

### Q16 nohup、&、disown 有什么区别？
**答**：
- `&` 只是把命令放后台，作业仍属于当前 shell，退出终端时可能收到 SIGHUP。
- `nohup` 让进程忽略 SIGHUP，通常和 `&` 搭配，输出默认进 `nohup.out`，也可显式重定向。
- `disown` 把作业移出 shell 的作业表，之后退出终端不再转发 SIGHUP；`disown -h` 只标记不转发。
- 长期服务应交给 systemd，能管重启、日志和开机自启；nohup 只适合临时任务。

```bash
nohup ./svc.sh >svc.log 2>&1 &
disown -h %1
```

### Q17 fork 和 exec 的区别？
**答**：
- `fork()` 复制当前进程（写时复制）产生子进程，返回值区分父子；子进程继承 fd、环境和地址空间。
- `exec()` 族用新程序替换当前进程的代码、数据、堆栈，PID 不变，成功后不返回。
- shell 执行外部命令的典型路径是 fork 子进程、子进程 exec、父进程 wait；fork 后马上 exec 要注意 `FD_CLOEXEC`。
- 只 fork 不 exec 会得到两个几乎相同的进程，适合并行处理；只 exec 不 fork 会替换掉当前 shell。

```bash
strace -f -e trace=process bash -c 'ls /tmp'
```

### Q18 如何看进程打开的文件？
**答**：
- `lsof -p PID` 列出 fd、类型、大小和路径；`lsof -p PID | wc -l` 可粗看句柄规模。
- `/proc/PID/fd/` 是 fd 到文件的映射，`ls -l` 可看；`/proc/PID/limits` 看 `Max open files`。
- 查端口占用用 `lsof -i:8080`；查已删除但仍占用的文件用 `lsof +L1`。
- fd 数持续上涨通常意味着句柄泄漏，要结合代码检查是否忘记 close。

```bash
lsof -p 1234
ls -l /proc/1234/fd | tail
lsof +L1
```

### Q19 free 里 available 和 free 的区别？
**答**：
- `free` 是完全未分配的内存；Linux 会用空闲内存做 `buff/cache`，所以这个值小很正常。
- `available` 是内核估算的“不换页即可给新进程用”的内存，包含大部分可回收缓存。
- 判断内存压力看 available 趋势和 `si/so`；available 很低且 swap in/out 持续非 0 才危险。
- `buff` 偏块设备元数据，`cache` 偏文件页；用 `free -h -s 1` 观察趋势比看单次快照可靠。

```bash
free -h
vmstat 1 5
```

### Q20 free 里 buff/cache 很大是否正常？swap 要不要开？
**答**：
- 正常，缓存是“把空闲内存用起来”，应用需要时内核会回收；只有 cache 不可回收且 available 很低才是问题。
- 不要在生产上习惯性 `drop_caches`，它会清掉热点缓存、拖慢系统，只适合排查或特殊测试。
- swap 建议开：能兜住突发内存、支持休眠、给回收留缓冲；低延迟服务可调小 `vm.swappiness`，而不是完全关掉。
- 完全禁用 swap 时，内存打满更容易直接触发 OOM；容器还要同时看节点内存和 cgroup 限额。

```bash
free -h
swapon --show
sysctl vm.swappiness
```

### Q21 OOM Killer 是什么？
**答**：
- 内存（含 cgroup 限额）耗尽时，内核按 `oom_score` 选择进程杀掉以保住系统，日志在 `dmesg` 或 `journalctl -k`。
- 常见触发：RSS 暴涨、内存泄漏、容器 limit 太小、page cache 不可回收、overcommit 配置不当。
- 排查 `dmesg -T | grep -i oom` 和进程的 `/proc/PID/oom_score`；调 `oom_score_adj` 只是权宜。
- 根治要限内存、修泄漏、扩容或加 swap，并用 cgroup `memory.max` 配告警。

```bash
dmesg -T | grep -i -E 'oom|killed process'
cat /proc/$(pgrep -f myapp | head -1)/oom_score
```

### Q22 内存持续上涨怎么排查？怎么判断是不是泄漏？
**答**：
- 先确认真涨：`free -h` 看 available 趋势，`ps -eo pid,rss,cmd --sort=-rss | head` 找大户；RSS 高不一定是泄漏，cache 可回收。
- 看进程内部：`/proc/PID/status` 的 VmRSS/VmData、`pmap -x PID` 的匿名段；`smem` 的 PSS 在多进程共享内存时更准。
- 语言层工具：Java 用 `jmap -histo:live` 或 heap dump，Go 用 pprof，C/C++ 用 valgrind/ASan。
- 对比多次采样的对象数量与堆大小：只涨不降更像泄漏；随流量涨落更像缓存或连接池。

```bash
ps -eo pid,rss,pmem,cmd --sort=-rss | head
pmap -x 1234 | tail -1
```

### Q23 用 cgroup 限制 CPU 怎么做？
**答**：
- cgroup v2 挂在 `/sys/fs/cgroup`；建子组后写 `cpu.max`，格式是「配额 周期」，单位微秒。
- `echo '50000 100000' > cpu.max` 表示每 100ms 最多跑 50ms，约 0.5 核；写 `max` 表示不限制。
- `cpu.weight` 是争抢时的相对权重，不是硬上限；容器可用 `docker run --cpus=1.5`。
- 生产上优先用 systemd slice 或容器运行时，别手改系统层级；手工示例要求父组已启用 cpu 控制器，可用 `cpu.stat` 的 `nr_throttled` 验证限流。

```bash
mkdir -p /sys/fs/cgroup/demo
echo '50000 100000' > /sys/fs/cgroup/demo/cpu.max
cat /sys/fs/cgroup/demo/cpu.stat
```

## 四、systemd 与服务

### Q24 systemd 和传统 init 的区别？
**答**：
- SysV init 按 `/etc/rc.d` 脚本串行启动、靠运行级别；systemd 用 unit 描述依赖，可并行启动、按需激活。
- systemd 用 cgroup 跟踪服务及其子进程，stop 能清理整个进程组；还统一了日志、定时器、挂载和 socket 激活。
- unit 通过 `After`、`Requires`、`Wants` 表达依赖；`systemctl enable` 只是建开机链接，不等于现在启动。
- systemd 也兼容部分 SysV 脚本，但排障思路要从“脚本顺序”转为“unit 依赖 + journal 日志”。

```bash
systemctl list-units --type=service
systemctl list-dependencies nginx
```

### Q25 开机自启动有哪些方式？systemctl enable 和 start 有什么区别？
**答**：
- `start` 只立即启动本次，重启不保留；`enable` 创建开机启动链接，重启才拉起；`enable --now` 两者都做。
- 自建 unit 放 `/etc/systemd/system/`，改完 `daemon-reload` 再 enable；用户级服务用 `systemctl --user`。
- 其他方式有 cron 的 `@reboot`、`/etc/rc.local`（需启用 rc-local 服务）、桌面 autostart；定时任务优先 systemd timer。
- `disable` 只取消开机自启，不停止当前进程；用 `is-enabled` 和 `is-active` 分别验证。

```bash
systemctl enable --now myapp
systemctl is-enabled myapp; systemctl is-active myapp
```

### Q26 怎么写一个 service 文件？journalctl 怎么查某个服务的日志？
**答**：
- 文件放 `/etc/systemd/system/myapp.service`；`[Unit]` 写描述和依赖，`[Service]` 写启动命令、用户、重启策略，`[Install]` 决定 enable 挂到哪个 target。
- 前台进程用 `Type=simple`，传统 daemon 用 `forking`；按需配 `WorkingDirectory`、`EnvironmentFile`、`Restart=on-failure`。
- 改完先 `systemctl daemon-reload`，再 restart；启动失败看 `systemctl status` 和 `journalctl -u myapp -b`。
- `journalctl -u myapp -f` 跟踪，`--since "1 hour ago" -p err` 过滤；`-b -1` 看上一次启动。

```ini
[Unit]
Description=My App
After=network-online.target
[Service]
Type=simple
User=appuser
ExecStart=/opt/myapp/start.sh
Restart=on-failure
[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload && systemctl restart myapp
journalctl -u myapp -b --since "1 hour ago"
```

## 五、磁盘与文件系统

### Q27 inode 是什么？inode 耗尽怎么办？
**答**：
- inode 存文件类型、权限、属主、大小、时间戳、数据块指针和链接数，不含文件名；文件名在目录项里映射到 inode 号。
- `df -h` 还有空间但创建文件报 `No space left on device` 时，用 `df -i` 确认是否 inode 耗尽。
- 海量小文件最容易耗尽 inode；先按目录统计数量，重点清缓存、邮件队列、session、临时文件。
- ext4 的 inode 数在 `mkfs` 时基本固定，XFS 动态分配；根治要重建文件系统并调 `-N`/`-i`，不能只靠删大文件。

```bash
df -i
find /var -xdev -type f | wc -l
```

### Q28 为什么 df 和 du 结果不一致？
**答**：
- `df` 统计文件系统已分配的块（含元数据、保留块），`du` 累加目录中可见文件占用，口径不同。
- 常见原因：文件已删除但仍被进程持有、挂载点覆盖了底层目录、稀疏文件、硬链接重复计数、权限不足漏算。
- 先 `df -h` 找分区，再 `du -x -h --max-depth=1` 从根逐层下钻；`-x` 保证不跨文件系统。
- ext4 默认保留 5% 块给 root，元数据和日志也占空间；差值异常时优先查 deleted open files。

```bash
df -h /var
du -x -h --max-depth=1 /var | sort -h
lsof +L1
```

### Q29 文件删除了但磁盘空间没释放，怎么处理？
**答**：
- 进程仍持有已删除文件的 fd，inode 和数据块就不会释放，`df` 仍计入，但 `du` 看不到这个名字。
- 用 `lsof +L1` 或 `lsof | grep deleted` 找 PID 与 fd；`ls -l /proc/PID/fd` 里会显示 `(deleted)`。
- 处理：重启或优雅 reload 进程释放 fd；不能重启时可用 `: > /proc/PID/fd/N` 截断，仅适用于可截断的普通文件。
- 不要直接删 `/proc/PID/fd/N`；数据库等文件被截断可能损坏，操作前先确认文件用途。

```bash
lsof +L1
: > /proc/1234/fd/5
```

### Q30 MBR 和 GPT 有什么区别？
**答**：
- MBR 用 32 位 LBA，单盘上限 2 TiB，最多 4 个主分区（可 3 主 + 扩展），没有校验和备份。
- GPT 用 64 位 LBA，默认 128 个分区，首尾各一份分区表并带 CRC32 校验，通常配 UEFI，也可用于 BIOS。
- 新盘优先 GPT + `parted`/`gdisk`；转换分区表会改动磁盘结构，先备份，再用 `lsblk` 或 `fdisk -l` 确认。

```bash
parted /dev/sdb print
gdisk -l /dev/sdb
```

## 六、网络

### Q31 如何查端口被谁占用？ss 和 netstat 有什么区别？
**答**：
- `ss -tulnp | grep ':8080'` 直接列出监听 socket 与进程，需 root 才看得到别人的 PID；备选 `lsof -i:8080`、`fuser -n tcp 8080`。
- `ss` 属于 iproute2，直接读内核，速度快、信息多；`netstat` 属于 net-tools，已停止维护，新系统可能没装。
- 只有 TIME_WAIT/ESTAB 而没有 LISTEN，说明端口不是被监听，而是连接残留或对端问题。
- `-l` 只看监听，`-p` 显示进程，`-n` 不做 DNS 反解；查所有连接时去掉 `-l`。

```bash
ss -tulnp | grep ':8080'
ss -tan state time-wait | wc -l
```

### Q32 TIME_WAIT 过多怎么办？
**答**：
- TIME_WAIT 是主动关闭方等待 2MSL 的正常状态，用来保证最后 ACK 可达、旧报文消散；短连接多时堆积是现象，不是 bug。
- 先看分布：`ss -tan state time-wait | awk '{print $4}' | sort | uniq -c | sort -nr | head`，区分本机主动关闭还是被动。
- 优化优先复用连接：HTTP keep-alive、连接池、长连接；减少频繁短连接比调内核参数更有效。
- 可评估 `net.ipv4.tcp_tw_reuse=1`（仅出站、依赖时间戳）和 `tcp_max_tw_buckets`；不要开启已被移除的 `tcp_tw_recycle`。

```bash
ss -s
sysctl net.ipv4.tcp_tw_reuse net.ipv4.tcp_max_tw_buckets
```

### Q33 ping 通但端口不通怎么排查？tcpdump 怎么用？
**答**：
- ping 通只说明 ICMP 到主机，不代表端口在听；先确认服务监听的是 `0.0.0.0` 还是 `127.0.0.1`。
- 本机用 `curl -v telnet://127.0.0.1:8080` 或 `nc -vz` 测，远端用 `nc -vz host 8080`，区分服务未起、防火墙 DROP、安全组/ACL。
- 防火墙看 `firewall-cmd --list-all`、`nft list ruleset`、`iptables -S`；云主机还要查安全组。
- 抓包用 `tcpdump -i any -nn port 8080`：有 SYN 无 SYN-ACK 多为过滤，回 RST 多为端口未监听。

```bash
ss -tulnp | grep ':8080'
tcpdump -i any -nn -c 20 'tcp port 8080'
```

## 七、性能排查

### Q34 load average 高但 CPU 不高，为什么？vmstat 看什么？
**答**：
- load 统计运行队列（R）加不可中断睡眠（D），不只看 CPU 忙不忙；D 多会推高 load 而 CPU 空闲。
- 常见原因是磁盘 IO 慢、NFS/网络存储失联、内存不足触发直接回收；先 `vmstat 1` 看 `r/b`、`wa`、`si/so`。
- `vmstat` 关键列：`r` 可运行进程数、`b` 阻塞进程数、`si/so` 换入换出、`us/sy/id/wa` 的 CPU 分布。
- `wa` 高时用 `iostat -x 1` 看 `%util`、`await`、`avgqu-sz/aqu-sz`，再用 `ps` 找 D 状态进程。

```bash
vmstat 1 5
iostat -x 1
```

### Q35 IO 高怎么排查？
**答**：
- `iostat -x 1` 先定位盘：`%util` 接近 100、`await` 或 `avgqu-sz/aqu-sz` 升高说明排队严重。
- `iotop -o` 或 `pidstat -d 1` 找读写大户；再看是否日志刷盘、备份/压缩任务、数据库 checkpoint、swap 抖动。
- 区分磁盘本身慢（云盘 IOPS 上限、坏盘）与访问模式（随机小 IO、超大文件）；`fio` 可做基线测试。
- 处理方向：限流/错峰、异步写、加缓存、拆分盘、升级 IOPS；`ionice` 只调优先级，不能解决容量瓶颈。

```bash
iostat -x 1
pidstat -d 1
iotop -o
```

### Q36 CPU 100% 怎么定位？
**答**：
- `top` 按 `P` 找进程并记下 PID；`top -H -p PID` 找线程，把线程 ID 转成 16 进制。
- Java 用 `jstack PID` 搜 `nid=0x...` 看栈；Go 用 pprof；C/C++ 用 `perf top` 或 `perf record -g`。
- 区分用户态忙（us 高，死循环/计算）和内核态忙（sy 高，系统调用/软中断）；`vmstat 1` 看 `us/sy/wa`。
- `pidstat -u 1`、`strace -c -p PID` 可看调用耗时；容器内还要排查 cgroup CPU 限额导致的限流。

```bash
top -H -p 1234
printf '%x\n' 1234
perf top -p 1234
```

## 八、场景题

### Q37 服务器起不来，怎么排查？
**答**：
- 先确认能否进单用户/救援模式，记录屏幕最后的报错；远程不通就用带外控制台（IPMI/iDRAC/云 VNC）。
- 按引导链排查：固件是否识别磁盘 → GRUB 是否出现 → 内核/initramfs 是否加载 → 是否卡在 fsck、mount 或服务。
- 常见原因：根分区只读或满、`/etc/fstab` 写错进 emergency mode、内核升级后 initramfs 缺失、GRUB 配置损坏。
- 救援模式下看 `journalctl -b -1`、`dmesg`，必要时 `mount -o remount,rw /`，改完 fstab 先用 `mount -a` 验证。

```bash
journalctl -b -1 -p err
mount -o remount,rw /
mount -a
```

### Q38 SSH 连不上，怎么排查？
**答**：
- 分层排查：网络是否通 → 22 端口是否监听 → 防火墙/安全组 → 认证与配置 → 资源与日志。
- 本机 `ss -tlnp | grep ':22'`、`systemctl status sshd`（Ubuntu 服务名常为 `ssh`）；远端 `nc -vz host 22`、`ssh -vvv user@host` 看卡在哪一步。
- 常见原因：sshd 没起、`PermitRootLogin`/`AllowUsers` 限制、密钥权限过宽、`/etc/hosts.deny`、磁盘满导致无法写 session。
- 有控制台时看 `/var/log/secure`（RHEL）或 `/var/log/auth.log`（Debian/Ubuntu），也可用 `journalctl -u sshd`；改配置先 `sshd -t` 校验，并保留一个已登录会话再 reload。

```bash
ss -tlnp | grep ':22'
sshd -t && systemctl reload sshd   # Ubuntu 服务名常为 ssh
journalctl -u sshd -n 50
```

### Q39 磁盘满了，怎么排查？
**答**：
- `df -h` 找满的分区，`df -i` 排除 inode 耗尽；不要只看根分区，`/var`、`/home`、容器 overlay 都可能满。
- `du -x -h --max-depth=1 /var | sort -h` 逐层下钻；重点看日志、缓存、镜像层、core dump、数据库 binlog。
- 文件删了没释放时用 `lsof +L1` 找 deleted open files，重启进程或 `: > /proc/PID/fd/N`。
- 临时清理正在写的日志用 `truncate -s 0` 或 logrotate，不要直接 `rm`；清理后确认 `df` 和业务都恢复。

```bash
df -h; df -i
du -x -h --max-depth=1 /var | sort -h
lsof +L1
```

### Q40 服务启动失败，怎么排查？
**答**：
- `systemctl status myapp -l` 看退出码和最近日志，`journalctl -u myapp -b -n 100 --no-pager` 看完整报错。
- 常见原因：`ExecStart` 路径或权限错、`User` 无权限、端口被占、环境变量缺失、依赖服务未起、配置语法错。
- 用相同用户手动执行 `ExecStart` 复现；`systemd-analyze verify myapp.service` 查 unit 语法。
- 资源类问题看 `dmesg` 的 OOM、`ulimit -n`、SELinux/AppArmor 拒绝；改 unit 后必须 `daemon-reload`。

```bash
systemctl status myapp -l
journalctl -u myapp -b -n 100 --no-pager
systemd-analyze verify /etc/systemd/system/myapp.service
```

## 面试表达建议

- 先给结论，再给两三条定位命令，最后补边界和风险，别一上来背命令。
- 场景题统一用「现象 → 定位 → 根因 → 处置 → 验证」组织，面试官更容易跟上。
- 命令要讲清关键参数，例如 `ss -tulnp` 的 `-p/-n`、`du -x` 的 `-x`、`find -xdev` 的 `-xdev`。
- 主动说明发行版和版本差异，别把 Ubuntu 或某个内核版本的经验说成所有 Linux 的定论。
- 不会的题先讲排查思路和验证方法，不硬编参数；涉及线上操作先说备份、保留会话和回滚方案。
