# Linux 基础

面试复习向笔记，按「目录 → 权限 → 命令 → 用户 → 进程 → 启动 → 存储 → 网络 → 包管理 → 脚本 → 排查 → 容器」组织；默认值随发行版与版本变化，以发行版文档为准。

## 1 目录结构与 FHS

Linux 只有一个根目录 `/`，各目录职责由 FHS 规划；「一切皆文件」，设备与内核状态也以文件形式暴露。

![](../asset/linux目录结构.jpg)

### 1.1 常见目录职责
| 目录 | 职责 | 备注 |
| --- | --- | --- |
| `/bin`、`/sbin` | 基础命令 / 系统管理命令 | `sbin` = system binaries；现代发行版多是指向 `/usr/bin`、`/usr/sbin` 的软链接 |
| `/lib`、`/lib64` | 基础命令与开机依赖的共享库 | 类似 Windows 的 DLL |
| `/etc` | 全系统配置文件 | 如 `my.cnf`、`/etc/fstab`、`/etc/passwd` |
| `/usr` | 用户态程序与只读数据 | 类似 Program Files；`/usr/local` 放源码编译软件 |
| `/opt` | 额外安装的第三方大型软件 | 如 Oracle，通常为空 |
| `/home`、`/root` | 普通用户主目录 / root 主目录 | root 不在 `/home` 下 |
| `/boot` | 内核与引导文件 | `vmlinuz`、`initramfs`、GRUB 配置 |
| `/dev` | 设备文件 | 类似设备管理器，如 `sda`、`nvme0n1` |
| `/proc` | 虚拟文件系统，暴露内核与进程状态 | 不占磁盘，见 5.5 |
| `/var` | 经常变化的数据 | 日志 `/var/log`、`/var/lib` |
| `/tmp` | 临时文件 | 全局可写并带 Sticky 位，可能被清理 |
| `/media`、`/mnt` | 可移动设备自动挂载 / 手动临时挂载 | `mount /dev/sdb1 /mnt` |
| `/lost+found` | ext 系 fsck 恢复的碎片文件 | 仅 ext2/3/4 有，XFS 没有 |
| `/selinux` | SELinux 相关 | 强制访问控制，限制进程只能访问特定文件 |

### 1.2 易混点
- `/bin`、`/sbin`、`/lib` 与 `/usr/bin`、`/usr/sbin`、`/usr/lib` 在现代发行版多为软链接合并（merged `/usr`），`ls -l /` 可看出。
- `/opt` 放整套第三方产品，`/usr/local` 放源码编译软件，`/srv` 放服务数据。
- 文件类型看 `ls -l` 首位：`-` 普通文件、`d` 目录、`l` 软链接、`c` 字符设备、`b` 块设备、`s` 套接字、`p` 命名管道。
- `/proc`、`/sys`、`/dev`、`/run` 都是内存中的虚拟文件系统，重启不保留。

## 2 文件与权限

### 2.1 rwx 的含义
`ls -l` 输出 `-rwxr-xr-- 1 alice dev 1024 app.sh`：首位是文件类型，其后 9 位按「属主 / 属组 / 其他人」各 3 位。

| 权限 | 对文件 | 对目录 |
| --- | --- | --- |
| `r` | 读取内容 | 列出目录内文件名（`ls`） |
| `w` | 修改内容 | 在目录内创建、删除、改名文件 |
| `x` | 执行（程序/脚本） | 进入目录（`cd`） |

### 2.2 chmod 与 chown
```bash
chmod 755 run.sh         # 数字法 r=4 w=2 x=1，rwxr-xr-x
chmod u+x run.sh         # 符号法 u/g/o/a + +/-/= + rwx
chown alice:dev file     # 同时改属主和属组
chown -R www-data:www-data /var/www
```

### 2.3 umask
文件基准 `666`、目录基准 `777`，`umask` 是「被屏蔽的位」，实际权限 = 基准 & ~umask；`umask 022` → 文件 `644`、目录 `755`，`027` → `640`、`750`。长期生效写入 `/etc/profile` 或 `~/.bashrc`。

### 2.4 SUID / SGID / Sticky
| 特殊位 | 数字 | 作用 | 例子 |
| --- | --- | --- | --- |
| SUID | 4755 | 以文件属主身份运行 | `/usr/bin/passwd` |
| SGID | 2755 | 文件按属组运行；目录内新建文件继承目录属组 | 协作目录 |
| Sticky | 1775 | 目录内文件只有属主或 root 能删 | `/tmp` |

`ls -l` 中显示为 `s`/`S`（无 `x` 时大写）与 `t`/`T`；SUID 是最常见提权面，审计用 `find / -perm -4000 -type f 2>/dev/null`。

### 2.5 ACL
标准权限只能一个属主、一个属组，ACL 可给任意用户或组单独授权，`ls -l` 权限位末尾的 `+` 表示存在 ACL。

```bash
setfacl -m u:alice:rw file     # 给用户授权
setfacl -m g:dev:rx -R /data   # 递归给组
getfacl file                   # 查看 ACL
```

ext4 现代内核默认启用 ACL，XFS 默认支持；老系统要在挂载参数里加 `acl`。

## 3 常用命令

### 3.1 文件与目录
| 命令 | 作用 | 常用参数 |
| --- | --- | --- |
| `ls` | 列目录 | `-l` 详情、`-a` 含隐藏、`-h` 人类可读、`-d` 看目录本身、`-t` 按时间 |
| `cd` / `pwd` | 切换 / 显示当前目录 | `cd -` 回上一个目录 |
| `mkdir` / `rmdir` | 建目录 / 删空目录 | `-p` 递归创建 |
| `cp` / `mv` | 复制 / 移动重命名 | `-r` 目录、`-p` 保留属性、`-a` 归档；同分区 `mv` 只改目录项 |
| `rm` | 删除 | `-r` 递归、`-f` 强制；**没有回收站** |
| `less` / `tail` | 分页查看 / 看末尾 | `less` 内 `/` 搜索、`q` 退出；`tail -f` 跟踪追加 |
| `stat` / `file` | 看 inode 与时间戳 / 判断真实类型 | atime 访问、mtime 内容修改、ctime 元数据修改 |

### 3.2 文本处理
| 命令 | 作用 | 要点 |
| --- | --- | --- |
| `grep` | 按行过滤 | `grep -in error app.log`；`-v` 反选、`-r` 递归、`-E` 扩展正则、`-A/-B/-C` 上下文 |
| `sed` | 流式编辑 | `sed -i 's/old/new/g' f`、`sed -n '10,20p' f`、`sed '/debug/d' f` |
| `awk` | 按列处理 | `awk -F: '{print $1}' /etc/passwd`；`$NF` 最后一列、`NR` 行号 |
| `cut` | 截取列或字符 | `cut -d: -f1,3 /etc/passwd`、`cut -c1-8 f` |
| `sort` | 排序 | `-n` 数值、`-r` 逆序、`-k2` 指定列、`-t:` 分隔符、`-u` 去重 |
| `uniq` | 相邻去重（须先 sort） | `-c` 计数、`-d` 只看重复行 |

### 3.3 查找
| 命令 | 范围 | 示例 |
| --- | --- | --- |
| `find` | 实时遍历目录树 | `find /var/log -name "*.log" -mtime -7 -size +100M` |
| `locate` | 预建数据库 | 快但可能过期，需 `updatedb` |
| `which` / `whereis` | `PATH` / 标准目录 | 确认实际调用的是哪个命令 |

### 3.4 压缩与打包
| 命令 | 说明 |
| --- | --- |
| `tar` | 打包并可压缩：`-z` gzip、`-j` bzip2、`-J` xz；`tar -czf a.tar.gz dir`、`tar -xzf a.tar.gz -C /opt`、`tar -tzf a.tar.gz` 只看内容 |
| `gzip` / `gunzip` | 单文件压缩，`-k` 保留原文件、`-9` 最高压缩比，`zcat` 直接看内容 |
| `xz` | 压缩比高、更耗 CPU，常用于镜像与源码包 |
| `zip` / `unzip` | 与 Windows 交换方便：`zip -r a.zip dir`、`unzip -d /opt a.zip` |

### 3.5 进程
| 命令 | 作用 |
| --- | --- |
| `ps aux` / `ps -ef` | 快照查看（BSD / System V 两种风格） |
| `top` / `htop` | 实时查看，`htop` 支持鼠标与树形 |
| `kill` / `pkill` / `jobs` | 发信号、按名字杀、作业控制（见第 5 章） |

### 3.6 网络
| 命令 | 作用 |
| --- | --- |
| `ip addr` / `ip route` | 查地址与路由，取代 `ifconfig`、`route` |
| `ss -tulnp` | 查监听端口与进程，取代 `netstat` |
| `ping` / `traceroute` / `mtr` / `dig` | 连通性、路径、逐跳质量、DNS |

### 3.7 磁盘
| 命令 | 作用 |
| --- | --- |
| `df -h` / `df -i` | 容量与 inode 使用率 |
| `du -sh *` | 当前目录各子项占用 |
| `lsblk -f` / `blkid` | 块设备树、文件系统、UUID |

## 4 用户与组

### 4.1 /etc/passwd 字段
示例 `alice:x:1000:1000:Alice:/home/alice:/bin/bash`，7 个冒号分隔字段。

| 字段 | 含义 |
| --- | --- |
| 用户名 | 登录名 |
| `x` | 密码占位符，真实哈希在 `/etc/shadow` |
| UID | `0` 为 root，普通用户通常 ≥ 1000 |
| GID | 主组 ID，对应 `/etc/group` |
| 描述 | 注释或全名（GECOS） |
| 主目录 | 登录后的家目录 |
| 登录 shell | `/sbin/nologin` 表示禁止登录 |

`/etc/group` 存组与成员，`/etc/skel` 是新用户家目录模板。

### 4.2 用户与组管理
```bash
useradd -m -s /bin/bash -G dev,sudo alice   # -m 建家目录，-G 附加组
usermod -aG docker alice                    # 追加组；漏 -a 会覆盖原有附加组
passwd alice                                # root 改他人密码；passwd 改自己
```

### 4.3 sudo
用 `visudo` 编辑 `/etc/sudoers`（带语法检查，避免改坏后无法提权）。`alice ALL=(ALL) NOPASSWD: ALL` 是免密全权，`%wheel`、`%sudo` 是组授权写法。sudo 会记录命令，比直接分发 root 密码更可审计。

## 5 进程管理

进程 = 程序 + 运行上下文，有 PID、PPID、状态、优先级与地址空间；PID 1 是 init/systemd，是所有用户态进程的祖先。

### 5.1 ps、top 与 htop
```bash
ps aux                                   # BSD 风格，含 %CPU、%MEM
ps -ef                                   # System V 风格，含 PPID
```

状态位：`R` 运行、`S` 可中断睡眠、`D` 不可中断睡眠（多在等 IO）、`T` 停止、`Z` 僵尸、`I` 空闲内核线程。`top` 交互键：`P` 按 CPU、`M` 按内存、`1` 展开各核、`c` 完整命令行、`H` 线程视图、`k` 发信号。

### 5.2 信号与 kill
| 信号 | 编号 | 含义 |
| --- | --- | --- |
| SIGHUP | 1 | 挂断，守护进程常用来触发重载配置 |
| SIGKILL | 9 | 强制杀死，不可捕获、不可忽略 |
| SIGTERM | 15 | 默认终止信号，可捕获以优雅退出 |
| SIGSTOP / SIGCONT | 19 / 18 | 暂停 / 继续，不可捕获 |

```bash
kill -15 1234           # 先请求优雅退出
kill -9 1234            # 再强制杀死，可能丢数据
```

### 5.3 nice 与前后台作业
`nice` 范围 `-20`（最高）到 `19`（最低），普通用户只能增大 nice 值（降优先级）。

```bash
nice -n 10 ./batch.sh    # 低优先级启动；renice -n 5 -p 1234 调整运行中的进程
nohup ./svc.sh > svc.log 2>&1 &   # & 放后台，nohup 忽略 SIGHUP，退出终端仍存活
jobs -l && fg %1         # 查看作业、调回前台；bg %1 让暂停的作业继续
```

### 5.4 僵尸进程与孤儿进程
| | 僵尸进程 | 孤儿进程 |
| --- | --- | --- |
| 成因 | 子进程已退出，父进程未 `wait()` 回收 | 父进程先退出 |
| 状态 | `Z`，内存已释放，仅剩 PID 与退出码 | 仍在运行，被 PID 1（或 subreaper）收养 |
| 处理 | 让父进程回收，或杀掉父进程使其被收养 | 通常无需处理 |

### 5.5 /proc 常用文件
| 路径 | 内容 |
| --- | --- |
| `/proc/cpuinfo` / `/proc/meminfo` | CPU 型号核数 / 内存明细（MemTotal、MemAvailable） |
| `/proc/loadavg` | 1/5/15 分钟负载与运行队列 |
| `/proc/<pid>/status` | 进程状态、VmRSS、Threads |
| `/proc/<pid>/fd/` | 打开的文件描述符，排查句柄泄漏 |

## 6 systemd

systemd 是现代发行版主流的 init 与服务管理器，核心概念是 unit：服务、挂载点、定时器统一抽象。

### 6.1 unit 类型
| 类型 | 用途 |
| --- | --- |
| `.service` | 守护进程或一次性任务 |
| `.target` | unit 集合，替代运行级别（`multi-user.target` ≈ runlevel 3） |
| `.timer` | 定时触发，替代 cron |
| `.socket` | 套接字激活，有连接才拉起服务 |

### 6.2 systemctl 常用命令
```bash
systemctl start|stop|restart|reload nginx
systemctl status nginx
systemctl enable --now nginx          # 开机自启并立即启动
systemctl daemon-reload               # 改 unit 文件后必须执行
```

### 6.3 写一个 service 文件
放到 `/etc/systemd/system/myapp.service`（自建 unit 用此目录，别改 `/usr/lib/systemd/system` 下的发行版文件）：

```ini
[Unit]
Description=My Demo Service
After=network-online.target

[Service]
Type=simple
User=appuser
ExecStart=/opt/myapp/bin/start.sh
Restart=on-failure
[Install]
WantedBy=multi-user.target
```

`Type=simple` 适合前台进程，传统守护进程用 `forking`；改完执行 `systemctl daemon-reload && systemctl enable --now myapp`。

### 6.4 journalctl
```bash
journalctl -u nginx -f                  # 跟踪某服务
journalctl -b                           # 本次启动全部日志；-b -1 上次启动
journalctl -u nginx --since "1 hour ago" -p err
```

## 7 磁盘与文件系统

### 7.1 分区表：MBR 与 GPT
| | MBR | GPT |
| --- | --- | --- |
| 最大磁盘 | 2 TB（32 位 LBA） | 约 9.4 ZB（64 位 LBA） |
| 分区数 | 4 个主分区，或 3 主 + 1 扩展（扩展内再分逻辑分区） | 默认 128 个，Linux 可更多 |
| 校验与备份 | 无，分区表损坏难恢复 | CRC32 校验，首尾各一份 |
| 启动方式 | 传统 BIOS | UEFI（也可配 BIOS 使用） |

早期「IDE 硬盘最多 59 个逻辑分区、SCSI 最多 11 个」源自老内核按设备号分配的限制，**现代内核已不再受此约束**，实际上限由分区表类型和工具决定。新盘直接用 GPT + `parted`/`gdisk`。

### 7.2 常见文件系统
| 文件系统 | 特点 | 现状 |
| --- | --- | --- |
| ext2 | 1993 年发布，无日志，断电易损坏 | 多用于 U 盘等小场景 |
| ext3 | ext2 加日志，崩溃恢复更快 | 已被 ext4 取代 |
| ext4 | 兼容 ext3，Extents、延迟分配、多块分配、快速 fsck、日志校验，支持 1 EiB 卷与 16 TiB 单文件 | Debian/Ubuntu 长期默认 |
| XFS | 64 位、大文件与大并发友好、在线扩容；**不支持缩容** | RHEL/CentOS 7+ 默认 |
| Btrfs | CoW、快照、子卷、内置 RAID 与压缩、数据校验 | SUSE 系默认，Fedora 工作站常用 |

### 7.3 设备命名与 NVMe
- SATA/SAS：`/dev/sda`，分区 `sda1`、`sda2`；NVMe：`/dev/nvme0n1`，分区是 `nvme0n1p1`（注意 `p`），高队列深度、低延迟，没有 IDE/SCSI 那套历史包袱。虚拟化磁盘为 `/dev/vda`、`/dev/xvda`。

### 7.4 df / du / mount 与 fstab
```bash
df -h                  # 各文件系统容量；df -i 看 inode 使用率
du -sh /var/log/*      # 各子项占用；du -h --max-depth=1 / | sort -h
mount -o remount,rw /  # 只读根分区改回读写
```

`/etc/fstab` 每行六个字段：设备（建议写 UUID）→ 挂载点 → 文件系统类型 → 挂载选项 → dump 备份标志 → fsck 检查顺序（根 `/` 为 1，其他为 2，0 表示不检查），例：`UUID=xxxx / ext4 defaults 0 1`。改完先 `mount -a` 验证，改 unit 后 `systemctl daemon-reload`。

### 7.5 inode
inode 存文件元数据：类型、权限、属主、大小、时间戳、数据块指针、链接数，**不含文件名**；文件名在目录项里，目录项建立「名字 → inode 号」的映射。`stat file` 看 inode 号与链接数，`df -i` 看 inode 余量。

ext4 的 inode 数在 `mkfs` 时固定（`-N`、`-i` 可调），XFS 动态分配。海量小文件会把 inode 用完，表现为「还有空间却建不了文件」，处理办法是清理小文件或重建文件系统。

### 7.6 硬链接与软链接
| 对比项 | 硬链接 | 软链接（符号链接） |
| --- | --- | --- |
| inode | 与原文件同一个 | 独立 inode，内容为目标路径 |
| 跨文件系统 | 不可以 | 可以 |
| 指向目录 | 一般不允许 | 可以 |
| 原文件删除后 | 仍可访问，链接数减 1 | 变成悬挂链接（dangling） |

## 8 网络

### 8.1 ip 与 ss
`netstat` 属于已停止维护的 net-tools，现代系统用 iproute2 的 `ip` 与 `ss` 取代。

```bash
ip -br a                         # 简洁查看所有网卡与地址
ss -tulnp                        # 监听中的 TCP/UDP 端口与进程
ss -tanp state established       # 已建立的连接；ss -s 看连接数汇总
```

### 8.2 连通性与 DNS
| 命令 | 用途 |
| --- | --- |
| `ping -c4 host` | ICMP 连通性、丢包与 RTT |
| `traceroute` / `mtr host` | 逐跳路径，`mtr` 持续统计更直观 |
| `dig +short example.com` | 看 A 记录；`dig @8.8.8.8 example.com MX` 指定服务器与记录类型 |

`curl -X POST -H 'Content-Type: application/json' -d '{"a":1}' http://127.0.0.1:8080/api`；`--resolve example.com:443:10.0.0.5` 可绕过 DNS 直连后端。

### 8.3 防火墙
`firewalld` 是 RHEL 系的动态防火墙前端，新版后端为 `nftables`（旧版为 `iptables`）。

```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --reload        # 永久规则需 reload 才生效
```

直接用 nftables：`nft list ruleset`、`nft add rule inet filter input tcp dport 8080 accept`，规则写入 `/etc/nftables.conf`。Debian/Ubuntu 上更常见 `ufw allow 22/tcp`；默认策略以发行版文档为准。

## 9 软件包管理

### 9.1 apt 与 dnf/yum 对照
| 操作 | Debian/Ubuntu（apt/dpkg） | RHEL/CentOS/Fedora（dnf，旧为 yum） |
| --- | --- | --- |
| 更新索引 | `apt update` | `dnf makecache` |
| 升级已装软件 | `apt upgrade` | `dnf upgrade` |
| 安装 / 卸载 | `apt install nginx` / `apt remove nginx` | `dnf install nginx` / `dnf remove nginx` |
| 彻底卸载含配置 | `apt purge nginx` | 无直接对应，手动删配置 |
| 搜索 / 详情 | `apt search` / `apt show` | `dnf search` / `dnf info` |
| 已安装列表 | `dpkg -l` | `rpm -qa` |
| 文件属于哪个包 | `dpkg -S /usr/sbin/nginx` | `rpm -qf /usr/sbin/nginx` |

`apt update` 只刷新索引、不升级软件，这点常被混淆。

### 9.2 源码编译三步
```bash
./configure --prefix=/usr/local/nginx   # 检查依赖、生成 Makefile
make -j$(nproc)                         # 编译
make install                            # 安装到 prefix
```

前提是装好工具链与开发库（Debian：`build-essential`；RHEL：`gcc`、`make`、`*-devel`）。`--prefix` 决定安装路径，默认 `/usr/local`；源码装的软件不受包管理器管理，升级卸载都要自己做。

## 10 Shell 与脚本

### 10.1 管道与重定向
| 写法 | 含义 |
| --- | --- |
| `cmd > file` | 标准输出覆盖写入 |
| `cmd >> file` | 标准输出追加 |
| `cmd 2> err.log` | 标准错误写入文件 |
| `cmd &> all.log` | stdout 与 stderr 一起写入（bash 专属） |
| `cmd > out 2>&1` | 先重定向 stdout，再让 stderr 指向同一处 |
| `cmd1 \| cmd2` | 管道：前者 stdout 作为后者 stdin |

### 10.2 变量与流程控制
```bash
NAME="app"              # 等号两边不能有空格
export NAME             # 导出为环境变量，子进程可见
echo "${NAME}-1"        # 推荐加花括号
```

```bash
if [ -f /etc/passwd ]; then
  echo exists
else
  echo missing
fi

for f in /var/log/*.log; do
  wc -l "$f"
done
```

判断用 `[ ]`（POSIX）或 `[[ ]]`（bash，支持 `&&` 与正则）；脚本首行建议 `#!/usr/bin/env bash` 并加 `set -euo pipefail`。

### 10.3 cron 与 systemd timer
cron 五个字段 `分 时 日 月 周`：`0 3 * * *` 表示每天 3:00。

```bash
crontab -e     # 编辑当前用户任务；crontab -l 列出
```

`/etc/cron.d/` 下的文件需多一个用户字段，`/etc/cron.{hourly,daily}` 由 run-parts 执行。cron 环境变量少、`PATH` 短，脚本里要用绝对路径。systemd timer 更可控，日志进 journal 且支持错过后补跑：

```ini
[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### 10.4 特殊变量与退出码
| 变量 | 含义 |
| --- | --- |
| `$?` | 上一条命令退出码，`0` 为成功 |
| `$$` | 当前 shell 的 PID |
| `$!` | 最近一个后台进程的 PID |
| `$0` / `$#` | 脚本名 / 参数个数 |
| `$@` / `$*` | 参数列表，`"$@"` 保留参数边界，优先用它 |

常见退出码：`1` 一般错误、`126` 无执行权限、`127` 命令未找到、`130` 被 Ctrl-C 中断、`137` 被 SIGKILL 杀死（128+9）。

## 11 性能与排查

| 工具 | 关注点 |
| --- | --- |
| `top` / `htop` | 整体 CPU、内存、负载与单进程占用 |
| `vmstat 1` | `r` 运行队列、`b` 阻塞、`si/so` 换页、`us/sy/id/wa` |
| `iostat -x 1` | 每块盘 `r/s`、`w/s`、`await`、`%util` |
| `sar -u 1 5` | 历史与实时趋势，需 sysstat 采集 |
| `free -h` | `available` 才是可用内存，`buff/cache` 可回收 |
| `lsof -p PID` / `lsof -i:80` | 打开的文件、网络连接 |
| `strace -f -p PID` / `strace -c cmd` | 系统调用跟踪与耗时统计 |
| `perf top` / `perf record -g` | 采样剖析 CPU 热点，定位到函数 |

- **CPU 高**：`top` 找进程 → `top -H -p PID` 找线程 → 线程 ID 转 16 进制去 `jstack` 查栈，或 `perf top` 看热点函数；`vmstat` 区分用户态忙还是 `wa` 高。
- **内存涨**：`free -h` 看 available 是否真降，`ps -eo pid,rss,cmd --sort=-rss` 找大户，`/proc/PID/status`、`pmap -x PID` 看明细；`dmesg` 有 OOM killer 说明已触顶。
- **IO 高**：`iostat -x 1` 看哪块盘 `%util` 接近 100、`await` 变大 → `iotop -o` 或 `pidstat -d` 找进程 → 再看是否日志刷盘、备份任务或 swap 抖动。
- **端口占用**：`ss -tulnp | grep :8080`、`lsof -i:8080`、`fuser 8080/tcp`；TIME_WAIT 过多要看连接复用与内核参数。
- **负载高但 CPU 不高**：load 包含 `D` 状态进程，多为 IO 或 NFS 卡住，用 `ps -eo stat,pid,cmd | grep '^D'` 定位。
- **磁盘满**：`df -h` 找分区 → `du -h --max-depth=1` 逐层下钻 → 注意已删除仍被占用的文件（`lsof +L1`）与 inode（`df -i`）。

## 12 容器基础

容器不是「轻量虚拟机」，而是**被隔离并限制资源的一组普通进程**：namespace 管「看得见什么」，cgroup 管「能用多少」。

### 12.1 namespace 与 cgroup
| 机制 | 作用 | 内容 |
| --- | --- | --- |
| namespace | 隔离视图 | `pid` 进程号、`net` 网络栈、`mnt` 挂载点、`uts` 主机名、`ipc` 进程间通信、`user` UID 映射、`cgroup` 视图 |
| cgroup | 限制资源 | CPU、内存、IO 带宽、进程数；v2 中为 `cpu.max`、`memory.max`、`pids.max` |

```bash
docker run --cpus=1.5 --memory=512m nginx
```

### 12.2 常用 docker 命令
```bash
docker ps -a                       # 容器列表
docker run -d --name web -p 8080:80 -v /data/html:/usr/share/nginx/html nginx
docker exec -it web bash           # 进入运行中的容器
docker logs -f --tail 100 web      # 看日志
docker build -t myapp:1.0 .        # 构建镜像
```

`-p 8080:80` 是「宿主机端口:容器端口」，`-v` 挂数据卷，`--restart=always` 控制重启策略。

### 12.3 容器与虚拟机
| 对比项 | 容器 | 虚拟机 |
| --- | --- | --- |
| 隔离级别 | 进程级，共享宿主机内核 | 硬件级，各自独立内核 |
| 启动速度 | 毫秒到秒级 | 数十秒起 |
| 隔离强度 | 较弱，内核漏洞可能逃逸 | 较强 |
| 典型技术 | Docker、containerd、Kubernetes | KVM、VMware、Xen |

## 13 面试问答
### 13.1 软链接和硬链接的区别？
- 硬链接是同一 inode 的另一个名字，链接数 +1，删任一名字数据仍在；软链接是独立文件，内容是目标路径。
- 硬链接不能跨文件系统、一般不能指向目录；软链接都可以，但目标删除后变成悬挂链接。
### 13.2 inode 是什么？inode 耗尽怎么办？
- inode 存元数据（权限、属主、大小、时间戳、数据块指针、链接数），不含文件名，文件名在目录项里。
- `df -h` 有空间却写不进文件时用 `df -i` 确认；清理海量小文件，或重建文件系统用 `-N`/`-i` 加大 inode（XFS 动态分配）。
### 13.3 进程状态 D 是什么？
- 不可中断睡眠，进程在内核里等 IO 或锁，连 `kill -9` 也要等系统调用返回才生效。
- 大量 `D` 会让 load 飙升而 CPU 空闲，多为磁盘故障或 NFS 失联，用 `ps -eo stat,pid,wchan,cmd | grep '^D'` 定位。
### 13.4 如何查端口被谁占用？
- `ss -tulnp | grep :8080` 直接列出监听进程与 PID（需 root 才看得到他人进程）。
- 备选 `lsof -i:8080`、`fuser -n tcp 8080`；若是 TIME_WAIT 而非 LISTEN，说明是连接残留。
### 13.5 systemd 和传统 init 的区别？
- SysV init 按 `/etc/rc.d` 脚本串行启动、靠运行级别；systemd 用 unit 描述依赖，并行启动、按需激活。
- systemd 用 cgroup 跟踪服务及子进程，`stop` 能杀干净整个进程组，并统一日志、定时任务与挂载管理。
### 13.6 用 cgroup 限制 CPU 怎么做？
- cgroup v2 写 `cpu.max`：`echo "50000 100000" > /sys/fs/cgroup/demo/cpu.max` 表示每 100ms 最多用 50ms，即 0.5 核。
- 容器用 `docker run --cpus=1.5`，K8s 用 `resources.limits.cpu`；这是上限不是保底，保底用 `cpu.weight`。
### 13.7 进入目录、读取文件分别需要什么权限？
- 进目录要 `x`，列目录要 `r`，在目录内建删文件要 `w`（且需 `x` 才能进入）。
- 读文件要文件 `r`，执行要 `x`；删除文件只看所在目录的 `w`。
### 13.8 umask 022 新建文件和目录的权限是多少？
- 文件基准 666 去掉 group/other 的写位 → `644`；目录基准 777 → `755`。
- umask 是屏蔽位，实际权限 = 基准 & ~umask；生产常设 `027`，得 640 与 750。
### 13.9 SUID 有什么用，有什么风险？
- 让普通用户执行时临时获得文件属主（常为 root）权限，典型是 `/usr/bin/passwd` 改 `/etc/shadow`。
- 风险是提权：SUID 程序若有命令注入或溢出即可拿 root，用 `find / -perm -4000 -type f` 定期审计。
### 13.10 僵尸进程怎么产生、怎么处理？
- 子进程退出后内核保留退出码等父进程 `wait()`，其间为 `Z`；父进程不回收就堆积，占 PID 表项。
- 僵尸已释放内存，`kill -9` 无效；修父进程回收逻辑，或杀掉父进程让 PID 1 收养回收。
### 13.11 孤儿进程和僵尸进程有什么区别？
- 孤儿是父进程先退出、自己还在跑的进程，被 PID 1 收养后继续运行，无害。
- 僵尸是子进程已退出但父进程不回收，只剩 PID 与退出码：孤儿还活着，僵尸死了没注销。
### 13.12 为什么 df 和 du 结果不一致？
- `df` 看文件系统块使用，`du` 按目录累加，口径不同。
- 常见原因：文件已删除但被进程占用（`lsof +L1`）、挂载点被覆盖、稀疏文件、权限不足漏算。
### 13.13 load average 高但 CPU 不高，为什么？
- load 统计运行队列加不可中断睡眠进程，不只看 CPU 忙不忙。
- 多见于磁盘 IO 慢、NFS 失联；`vmstat 1` 看 `b` 与 `wa`，`iostat -x` 看盘。
### 13.14 free 里 available 和 free 的区别？
- `free` 是完全未使用的内存，数值小很正常，Linux 会主动用空闲内存做 `buff/cache`。
- `available` 是可估算的可用内存（含可回收缓存）；它很低且 `si/so` 非 0 才危险。
### 13.15 内存持续上涨怎么排查？
- 先确认真涨：`free -h` 看 available 趋势，`ps -eo pid,rss,cmd --sort=-rss` 找大户。
- 再看进程内部：`/proc/PID/status` 的 VmRSS、`pmap -x PID`；Java 用 `jmap`，C/C++ 用 valgrind/ASan。
### 13.16 IO 高怎么排查？
- `iostat -x 1` 看哪块盘 `%util` 接近 100、`await` 升高、排队变长。
- `iotop -o` 或 `pidstat -d` 定位进程；再确认是否日志刷盘、备份任务、swap 抖动。
### 13.17 文件删除了但磁盘空间没释放，怎么处理？
- 进程仍持有该文件 fd，inode 未释放，`df` 仍计入占用。
- `lsof +L1` 找到进程与 fd；重启进程，或 `: > /proc/PID/fd/N` 截断为 0 立即回收。
### 13.18 管道和重定向的区别？
- 管道 `|` 把前一命令的 stdout 接到后一命令的 stdin，数据在内存流动、不落盘。
- 重定向改变命令自身的输入输出指向，通常指向文件；管道默认只传 stdout。
### 13.19 2>&1 是什么意思？顺序为什么重要？
- 把 fd 2（stderr）指向当前 fd 1 所在位置。
- `cmd > out 2>&1` 两者都进文件；`cmd 2>&1 > out` 中 stderr 仍指向终端，顺序不能反。
### 13.20 nohup、&、disown 有什么区别？
- `&` 只是放后台，shell 退出时仍可能收到 SIGHUP 而终止。
- `nohup` 让进程忽略 SIGHUP，需配合 `&`；`disown` 把后台任务移出作业表。长期服务更推荐 systemd。
### 13.21 为什么有的进程 kill -9 也杀不掉？
- 处于 `D` 状态时信号要等系统调用返回才处理。
- 僵尸进程已退出，`kill` 无效；或被父进程反复拉起，或本身是内核线程。
### 13.22 怎么查内核版本和发行版版本？
- 内核：`uname -r`，全量信息 `uname -a`。
- 发行版：`cat /etc/os-release` 最通用，`hostnamectl` 也可；架构用 `uname -m`。
### 13.23 开机自启动有哪些方式？
- systemd：`systemctl enable xxx.service`，定时任务用 `xxx.timer`。
- cron 的 `@reboot`、`/etc/rc.local`（需启用服务）、桌面环境的自启动项。
### 13.24 MBR 和 GPT 有什么区别？
- MBR 是 32 位 LBA，单盘上限 2 TB，最多 4 个主分区（可换逻辑分区），无校验备份。
- GPT 是 64 位 LBA，默认 128 个分区，首尾各一份分区表带 CRC32 校验，配 UEFI 使用。
### 13.25 如何统计日志里访问量 Top10 的 IP？
- `awk '{print $1}' access.log | sort | uniq -c | sort -nr | head -10`。
- 思路是取列 → 排序 → 相邻去重计数 → 倒序取前 10；`uniq` 必须先 `sort` 才准。
