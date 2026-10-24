# Linux 基础

面向刚接触服务器的读者：讲清 Linux 是什么、怎么登录、目录怎么组织、权限怎么理解、用户怎么管，最后落到装软件、查文档和常见坑。默认值随发行版与版本变化，以发行版文档为准。

## 1 Linux 是什么

### 1.1 内核与发行版

- **内核（kernel）**：唯一直接管硬件的部分，负责进程调度、内存管理、文件系统、网络协议栈与设备驱动；它只提供系统调用，不提供 `ls`、`apt` 这类工具。
- **发行版（distribution）**：内核 + GNU 用户态工具（bash、coreutils）+ 包管理器 + init（现在多为 systemd）+ 默认配置与安全策略，打包成可安装的镜像。

日常说的「装个 Linux」指的是装发行版，严格意义上的 Linux 只是内核。主流发行版分两大类：Debian 系用 `apt` + `.deb`，RHEL 系用 `dnf` + `.rpm`。

| 发行版 | 包管理器 / 包格式 | 特点 |
| --- | --- | --- |
| Debian / Ubuntu | `apt` / `.deb` | 社区驱动、文档多；Ubuntu 每 6 个月一版，每两年一个 LTS，云主机与桌面最常见 |
| RHEL / CentOS / Fedora | `dnf`（旧 `yum`）/ `.rpm` | 企业向，RHEL 生命周期约 10 年；CentOS 已转向 Stream；Fedora 是新特性试验田 |
| Arch Linux | `pacman` / `.pkg.tar.zst` | 滚动更新、软件最新，装系统要自己配，适合学习不适合当稳定服务器 |
| Alpine | `apk` / `.apk` | musl libc + BusyBox，镜像只有几 MB，容器基础镜像常用；部分 glibc 程序要额外兼容层 |

选型建议：生产服务器优先 Ubuntu LTS、Debian stable 或 RHEL；容器镜像优先 Alpine；想追新、愿意自己修系统再用 Arch。

### 1.2 内核版本号怎么看

```bash
uname -r               # 5.15.0-91-generic：内核版本，脚本里最常用
uname -a               # 内核版本 + 主机名 + 架构 + 编译时间
uname -m               # x86_64 / aarch64，下载软件包时看它
cat /etc/os-release    # 发行版名称与版本，比 lsb_release 更通用
```

`5.15.0-91-generic` 逐段拆开：

| 片段 | 含义 |
| --- | --- |
| `5` | 主版本，大版本升级可能带来不兼容 |
| `15` | 次版本；3.0 之前偶数表示稳定版、奇数表示开发版，现在不再严格区分 |
| `0` | 修订号，同一版本内的 bug 与安全修复 |
| `-91-generic` | 发行版自己的补丁与 ABI 编号；`-generic` 是 Ubuntu 通用内核，还有 `-aws`、`-lowlatency` 等变体 |

### 1.3 LTS

- **LTS（Long Term Support）**：长期支持版本，只修 bug 与安全漏洞，不引入新特性。
- Ubuntu LTS（20.04、22.04、24.04）服务器版标准支持 5 年，可付费延长 ESM；Debian stable 约 2 年一版，再加约 5 年 LTS；RHEL 每个大版本约 10 年。
- 内核也有 LTS 分支：4.19、5.4、5.10、5.15、6.1、6.6 等，通常维护 2 年以上。
- 生产环境优先选 LTS：升级窗口可控、遇到问题搜得到答案；滚动发行版不适合要求稳定的服务器。

## 2 登录与第一个终端

### 2.1 本地登录与虚拟终端

服务器装好系统后，本机可用虚拟终端：`Ctrl+Alt+F1`~`F6` 切到 tty，`Ctrl+Alt+F7`（部分发行版是 F1/F2）回图形界面。输入用户名密码后得到 shell，看到提示符即登录成功。

```bash
tty             # 显示当前终端设备，如 /dev/pts/0
who             # 谁登录了、从哪个终端或地址、何时登录
w               # 比 who 多一列：当前在跑什么命令
exit            # 退出登录，Ctrl-D 等效
```

### 2.2 SSH 远程登录

```bash
ssh alice@192.168.1.10                    # 用密码登录远程主机
ssh -p 2222 alice@192.168.1.10            # 服务端改了端口时用 -p
ssh-keygen -t ed25519 -C "alice@web01"    # 生成密钥对，默认放 ~/.ssh
ssh-copy-id alice@192.168.1.10            # 把公钥追加到对方 ~/.ssh/authorized_keys
```

- 首次连接会显示主机指纹，确认后写入 `~/.ssh/known_hosts`；指纹突然变化，要么换了机器，要么是中间人，先别输密码。
- 私钥权限必须是 `600`，`~/.ssh` 目录是 `700`，权限过宽 ssh 会拒绝使用。
- 服务端配置在 `/etc/ssh/sshd_config`：`PermitRootLogin no`、`PasswordAuthentication no`；改端口后记得放行防火墙并 `systemctl reload sshd`。

### 2.3 提示符在说什么

`alice@web01:/var/log$` 由 `PS1` 决定：

| 片段 | 含义 |
| --- | --- |
| `alice` | 当前用户名，对应 `whoami` |
| `web01` | 主机名，`hostname` 可查可改 |
| `/var/log` | 当前工作目录，家目录会显示成 `~` |
| `$` | 普通用户；是 `#` 就说明当前是 root |

```bash
echo $PS1              # 默认大致是 \u@\h:\w\$
PS1='\u@\h:\w\$ '      # 临时改提示符，写进 ~/.bashrc 可长期生效
```

`\u` 用户名、`\h` 短主机名、`\w` 完整路径（`\W` 只显示最后一段）、`\$` 根据 UID 自动切 `$` 与 `#`。

### 2.4 root 与 sudo 的区别

| | 直接使用 root | 使用 sudo |
| --- | --- | --- |
| 权限 | UID 0，绕过所有权限检查 | 按 sudoers 授权，通常可执行任意命令 |
| 审计 | 操作全记在 root 名下，分不清是谁 | 记录「谁、在哪、执行了什么」 |
| 风险 | 一条手滑的 `rm -rf` 直接毁系统 | 仍会出事，但至少有一次显式提权动作 |
| 口令 | 需要知道 root 密码 | 用自己的密码，可免密，也可只放开几条命令 |

```bash
su -                            # 切到 root 并加载 root 的登录环境，需要 root 密码
sudo -i                         # 用 sudo 起一个 root 登录 shell
sudo -l                         # 看自己被允许执行哪些命令
sudo systemctl restart nginx    # 单条命令提权，日常最常用的姿势
```

- `su -` 与 `su` 的差别在是否加载目标用户环境：带 `-` 才读 `/etc/profile` 与目标用户 profile，`PATH` 才是对的。
- Ubuntu 默认锁住 root 密码（`/etc/shadow` 里是 `!`），只能走 sudo；Debian 安装时会让你设 root 密码。
- 生产建议：禁止 root 直接 SSH 登录，日常用普通用户 + sudo，需要连续多条命令时再 `sudo -i`。

## 3 目录结构 FHS

Linux 只有一个根 `/`，没有 C:、D: 盘符，所有分区都挂到根下某个目录。目录职责由 **FHS（Filesystem Hierarchy Standard）** 约定，各发行版大体一致。另一个要建立的概念是「一切皆文件」：设备、内核参数、进程状态都以文件暴露，`cat`、`echo` 就能读写。

![](../asset/linux目录结构.jpg)

### 3.1 各目录职责

| 目录 | 职责 | 备注与示例 |
| --- | --- | --- |
| `/etc` | 全系统配置文件 | `my.cnf`、`/etc/fstab`、`/etc/passwd`、`/etc/ssh/sshd_config` |
| `/var` | 经常变化的数据 | 日志 `/var/log`、包与状态 `/var/lib`、缓存 `/var/cache` |
| `/usr` | 用户态程序与只读数据 | 类似 Program Files；`/usr/bin`、`/usr/lib`、`/usr/share`，`/usr/local` 放源码编译软件 |
| `/home` | 普通用户主目录 | `/home/alice`，登录后的默认位置 |
| `/root` | root 的主目录 | 不在 `/home` 下，权限 `700` |
| `/tmp` | 临时文件 | 全局可写并带 Sticky 位，重启或定时任务可能清理 |
| `/proc` | 内核与进程状态的虚拟文件系统 | `/proc/cpuinfo`、`/proc/meminfo`、`/proc/<pid>/status`，不占磁盘 |
| `/sys` | 设备与内核对象的虚拟文件系统 | `/sys/class/net`、`/sys/fs/cgroup`，调内核参数用 |
| `/dev` | 设备文件 | `/dev/sda`、`/dev/nvme0n1`、`/dev/null` |
| `/mnt` | 手动临时挂载点 | `mount /dev/sdb1 /mnt` |
| `/opt` | 额外安装的第三方大型软件 | 如 Oracle，通常为空；整套产品放这里 |
| `/boot` | 内核与引导文件 | `vmlinuz`、`initramfs`、GRUB 配置，常单独分区 |
| `/srv` | 服务数据 | 网站、FTP 等对外服务的数据目录 |
| `/run` | 运行时状态 | 重启清空，`/run/nginx.pid`、`/run/systemd` |
| `/bin`、`/sbin` | 基础命令 / 系统管理命令 | `sbin` = system binaries；现代发行版多是指向 `/usr/bin`、`/usr/sbin` 的软链接 |
| `/lib`、`/lib64` | 基础命令与开机依赖的共享库 | 类似 Windows 的 DLL |
| `/media` | 可移动设备自动挂载 | 插 U 盘后出现在 `/media/alice/...` |
| `/lost+found` | ext 系 fsck 恢复的碎片文件 | 仅 ext2/3/4 有，XFS 没有 |
| `/selinux` | SELinux 伪文件系统 | 启用 SELinux 时才挂载，`getenforce` 看状态 |

### 3.2 易混点

- `/bin`、`/sbin`、`/lib` 在现代发行版多是与 `/usr/bin`、`/usr/sbin`、`/usr/lib` 合并的软链接（merged `/usr`），`ls -l /` 一看便知。
- `/opt` 放整套第三方产品，`/usr/local` 放源码编译软件，`/srv` 放服务数据，三者不要混用。
- `/proc`、`/sys`、`/dev`、`/run` 都是内存中的虚拟文件系统，重启不保留，别往里放需要持久化的数据。
- `/media` 是自动挂载，`/mnt` 是手动临时挂载；长期使用的数据盘建议在 `/etc/fstab` 里挂到 `/data` 这类明确目录。
- 根分区被日志撑满是常见故障，把 `/var` 或 `/var/log` 单独分区能避免整个系统写不进去。

## 4 文件类型与路径

### 4.1 七种文件类型

`ls -l` 输出的第一位就是类型：

| 字符 | 类型 | 例子 |
| --- | --- | --- |
| `-` | 普通文件 | `/etc/passwd`、脚本、ELF 二进制 |
| `d` | 目录 | `/etc`、`/var/log` |
| `l` | 符号链接 | `/usr/bin/awk -> /etc/alternatives/awk` |
| `c` | 字符设备 | `/dev/null`、`/dev/tty` |
| `b` | 块设备 | `/dev/sda`、`/dev/nvme0n1` |
| `s` | 套接字 | `/run/mysqld/mysqld.sock` |
| `p` | 命名管道 | `mkfifo /tmp/pipe` 创建 |

```bash
ls -l /dev/null         # crw-rw-rw- ...，第一位 c 说明是字符设备
file /bin/ls            # ELF 64-bit LSB executable，判断真实类型而不是看扩展名
stat /etc/passwd        # inode、权限、atime/mtime/ctime 三个时间戳
```

### 4.2 绝对路径与相对路径

- 绝对路径从 `/` 开始，与当前位置无关：`/var/log/nginx/error.log`。
- 相对路径从当前目录算起：`logs/error.log`、`../conf/nginx.conf`。

```bash
pwd                                  # 打印当前目录的绝对路径
cd /var/log                          # 绝对路径切换
cd ../..                             # 相对路径：上两级
cd ~                                 # 回家目录，cd 不带参数等价
cd -                                 # 回上一个目录，并把路径打印出来
basename /var/log/nginx/error.log    # error.log
dirname  /var/log/nginx/error.log    # /var/log/nginx
```

- `.` 当前目录、`..` 上级目录、`~` 当前用户家目录、`~alice` alice 的家目录。
- 脚本里用相对路径会随「从哪执行」而变，稳妥做法是先 `cd "$(dirname "$0")"`，或全部用绝对路径。

### 4.3 文件名规则

- 大小写敏感：`File.txt`、`file.txt`、`FILE.TXT` 是三个文件；从 Windows 或默认不敏感的 macOS 迁过来最容易踩。
- 以 `.` 开头是隐藏文件，`ls -a` 才看得到，`~/.bashrc`、`~/.ssh` 都是。
- 扩展名只是给人看的约定，内核不看；`file` 才是判断真实类型的工具，`chmod +x` 后没有扩展名的脚本一样能跑。
- 避免空格、中文、`$`、`&`、`;`、`*` 等字符；必须用时加引号 `"my file.txt"` 或转义 `my\ file.txt`。

## 5 权限基础

### 5.1 读一行 ls -l

`-rwxr-xr-- 1 alice dev 1024 app.sh`

| 字段 | 含义 |
| --- | --- |
| `-` | 文件类型，见 4.1 |
| `rwx` | 属主 alice 的权限 |
| `r-x` | 属组 dev 的权限 |
| `r--` | 其他人的权限 |
| `1` | 硬链接数；目录这里是 2 + 子目录数 |
| `alice` | 属主（owner） |
| `dev` | 属组（group） |
| `1024` | 大小（字节），`ls -lh` 显示为 1.0K |
| `app.sh` | 文件名 |

### 5.2 rwx 对文件与目录的不同含义

| 权限 | 对文件 | 对目录 |
| --- | --- | --- |
| `r` | 读取内容 | 列出目录内的文件名（`ls`） |
| `w` | 修改内容 | 在目录内创建、删除、改名文件 |
| `x` | 执行（程序/脚本） | 进入目录（`cd`） |

- 目录只有 `r` 没有 `x`：`ls` 能看到名字，但 `ls -l`、`stat` 取不到详情，会报 Permission denied。
- 删除文件看的是所在目录的 `w` 与 `x`，与文件自己是不是 `444` 无关；`/tmp` 靠 Sticky 位挡住「删别人的文件」。

### 5.3 chmod：数字法与符号法

```bash
chmod 755 run.sh            # 数字法：r=4 w=2 x=1，得到 rwxr-xr-x
chmod 644 notes.txt         # rw-r--r--，普通文件默认
chmod u+x run.sh            # 符号法：u/g/o/a + +/-/= + rwx
chmod u+x,g-w,o=r run.sh    # 逗号分隔多条规则
chmod -R 750 /data/app      # 递归修改目录及其内容
```

| 数字 | 权限 | 典型用途 |
| --- | --- | --- |
| 644 | rw-r--r-- | 普通文件、配置文件 |
| 600 | rw------- | 私钥、含密码的配置 |
| 755 | rwxr-xr-x | 目录、可执行程序 |
| 700 | rwx------ | 私有目录，如 `~/.ssh` |
| 775 | rwxrwxr-x | 组内协作目录 |
| 777 | rwxrwxrwx | 不要用，任何用户都能改 |

- `chmod +x` 不写 `who` 时默认对 `a` 生效，但会受 `umask` 影响；脚本里建议写全数字。
- 目录要能被「进入」必须有 `x`，所以给目录加权限时 `r` 和 `x` 一般成对出现。

### 5.4 chown 与 chgrp

```bash
chown alice:dev file                    # 同时改属主与属组
chown -R www-data:www-data /var/www     # 递归改，Web 目录最常见
chown alice file                        # 只改属主，属组不动
chgrp dev file                          # 只改属组
```

- 只有 root 能把文件「送」给别人；普通用户只能把自己的文件改到自己所属的组。
- `-R` 递归不要对 `/`、`/usr` 这类系统目录随手执行，会破坏 SUID 与系统文件属主。

### 5.5 umask

文件基准 `666`、目录基准 `777`，`umask` 是「要屏蔽掉的位」，实际权限 = 基准 & ~umask。

```bash
umask           # 查看当前值，常见 0022
umask 027       # 临时改成 027：新建文件 640、新建目录 750
umask -S        # 用 rwx 形式显示，0022 时输出 u=rwx,g=rx,o=rx
```

| umask | 新建文件 | 新建目录 | 场景 |
| --- | --- | --- | --- |
| 022 | 644 | 755 | 默认，同组可读 |
| 027 | 640 | 750 | 生产常用，其他人无权限 |
| 077 | 600 | 700 | 私有，只有自己能访问 |

- 长期生效写进 `/etc/profile`（全局）或 `~/.bashrc`（当前用户）。
- 目录还需要 `x` 才能进入，所以 `umask 027` 下目录是 `750` 而不是 `640`。

### 5.6 SUID / SGID / Sticky

| 特殊位 | 数字 | 作用 | 例子 |
| --- | --- | --- | --- |
| SUID | 4755 | 以文件属主身份运行 | `/usr/bin/passwd` |
| SGID | 2755 | 文件按属组运行；目录内新建文件继承目录的属组 | 组协作目录 |
| Sticky | 1775 | 目录内文件只有属主或 root 能删 | `/tmp` |

```bash
ls -l /usr/bin/passwd                     # -rwsr-xr-x，属主位的 s 就是 SUID
find / -perm -4000 -type f 2>/dev/null    # 审计全系统 SUID 程序
```

- 显示为 `s`/`S`（没有 `x` 时是大写 `S`）与 `t`/`T`；大写表示对应的 `x` 位没开，特殊位形同虚设。
- SUID 是最常见的提权面：SUID 程序一旦有命令注入或缓冲区溢出，攻击者就能拿到属主（常为 root）权限，定期用上面的 `find` 审计。

### 5.7 ACL（了解）

标准权限只能有一个属主、一个属组；ACL 可以给任意用户或组单独授权，`ls -l` 权限位末尾出现 `+` 就说明存在 ACL。

```bash
setfacl -m u:alice:rw file        # 给用户 alice 单独读写
setfacl -m g:dev:rx -R /data      # 递归给组 dev 读 + 进入
getfacl file                      # 查看 ACL 规则
```

ext4 现代内核默认启用 ACL，XFS 默认支持；很老的系统才需要在挂载参数里加 `acl`。

### 5.8 权限判定顺序

1. 当前用户 UID 等于文件属主 → 只适用属主那三位，不再看组和其他。
2. 否则用户属于文件属组（含附加组）→ 只适用属组那三位。
3. 否则适用其他人那三位。

- root 例外：读写不受权限位限制，但执行仍要求至少有一个 `x` 位，否则一样 Permission denied。
- 权限只匹配一次：属主位是 `---` 时，即使属组位给了 `rwx`，属主本人也没有权限。

## 6 用户与组

Linux 的权限围绕「用户 UID + 组 GID」展开，`id` 是查看这一切最快的方式。

### 6.1 /etc/passwd 的七个字段

示例 `alice:x:1000:1000:Alice:/home/alice:/bin/bash`，7 个冒号分隔字段：

| 字段 | 含义 |
| --- | --- |
| 用户名 | 登录名 |
| `x` | 密码占位符，真实哈希在 `/etc/shadow` |
| UID | `0` 为 root，普通用户通常 ≥ 1000 |
| GID | 主组 ID，对应 `/etc/group` |
| 描述 | 注释或全名（GECOS） |
| 主目录 | 登录后的家目录 |
| 登录 shell | `/sbin/nologin` 表示禁止登录 |

补充：UID `1`~`999` 通常留给系统用户；改 UID 用 `usermod -u`，别忘了同步改家目录属主。

### 6.2 /etc/shadow 与 /etc/group

`/etc/shadow` 只有 root 可读，每行 9 个字段，例如 `alice:$6$...:19800:0:99999:7:::`：

| 字段 | 含义 |
| --- | --- |
| 用户名 | 与 `/etc/passwd` 对应 |
| 密码哈希 | `$6$` 为 SHA-512，`$y$` 为 yescrypt；`!`、`*`、`!!` 表示锁定或未设密码 |
| 最后修改 | 距 1970-01-01 的天数 |
| 最小间隔 | 改密码后多少天内不能再改，`0` 表示不限 |
| 最大有效 | 多少天后必须改，`99999` 表示永不 |
| 警告 | 过期前几天开始提示 |
| 宽限 | 过期后还能登录几天 |
| 失效 | 账号作废日期（天数） |
| 保留 | 未使用 |

`/etc/group` 每行是 `dev:x:1001:alice,bob`，即「组名:密码占位:GID:成员列表」，成员列表只列附加组，主组不在这里体现。

- 主组（primary group）：`/etc/passwd` 第 4 字段，新建文件默认属于它。
- 附加组（supplementary group）：`/etc/group` 第 4 字段，用来获得额外权限，如 `sudo`、`docker`。
- 新用户的家目录从 `/etc/skel` 复制（`.bashrc`、`.profile` 就在里面）；默认 shell、UID 范围由 `/etc/login.defs`、`/etc/default/useradd` 决定。

### 6.3 用户与组管理命令

```bash
useradd -m -s /bin/bash -G dev,sudo alice  # 建用户：建家目录、指定 shell 与附加组
usermod -aG docker alice                   # 追加附加组；漏 -a 会用 -G 覆盖原有附加组
userdel -r alice                           # 删用户，并连带家目录与邮件
passwd alice                               # root 改他人密码；不带参数改自己
id alice                                   # UID、主组、附加组一次看全
groups alice                               # 只看组名列表
groupadd -g 1001 dev                       # 建组并指定 GID
chage -l alice                             # 看密码与账号有效期
```

- Debian/Ubuntu 上 `adduser alice` 是交互式封装，自动建家目录、问密码，比 `useradd` 友好；写脚本仍用 `useradd`。
- `usermod -aG` 之后要重新登录（或 `newgrp docker`）新组才在当前 shell 生效。
- 删用户前先确认没有进程占用（`pgrep -u alice`），否则会留下属主为旧 UID 的孤儿文件。

### 6.4 sudo 与 visudo

```bash
visudo          # 编辑 /etc/sudoers，保存时自动做语法检查
visudo -c       # 只检查语法，不改文件
sudo -l         # 当前用户被授予了哪些命令
```

`/etc/sudoers` 一行一条规则，格式是「谁 在哪台主机=(以谁的身份) 可执行的命令」：

```text
alice ALL=(ALL) NOPASSWD: ALL                        # 免密全权，方便但等于给了 root
%wheel ALL=(ALL) ALL                                 # 组授权，RHEL 系；Debian 系组名是 %sudo
alice ALL=(root) /usr/bin/systemctl restart nginx    # 只放开一条命令
```

- 永远用 `visudo` 改，写坏 `/etc/sudoers` 会导致所有人都无法提权，只能进单用户模式救。
- 推荐在 `/etc/sudoers.d/` 下按用户建文件（权限 `440`），不要动主文件。
- sudo 会记录命令，比直接分发 root 密码更可审计；`NOPASSWD` 只给确实需要的自动化账号。

## 7 环境变量与 PATH

### 7.1 变量与环境变量

```bash
NAME="app"              # 定义 shell 变量，等号两边不能有空格
export NAME             # 导出为环境变量，子进程可见
echo "$NAME"            # 取值，推荐加花括号：echo "${NAME}-1"
printenv NAME           # 只打印环境变量，不存在时退出码非 0
VAR=1 ./run.sh          # 只对这条命令生效，不污染当前 shell
unset NAME              # 删除变量
env                     # 列出所有环境变量
```

- 不加 `export` 的变量只存在于当前 shell，`bash -c 'echo $NAME'` 看不到。
- 变量名区分大小写，环境变量习惯全大写；值里有空格必须加引号。

### 7.2 PATH

`PATH` 是冒号分隔的目录列表，输入命令时 shell 从左到右找第一个同名可执行文件。

```bash
echo $PATH                       # /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:...
which nginx                      # 实际会执行哪个 nginx，找不到时返回非 0
type -a python3                  # 所有同名命令：别名、函数、多个路径
export PATH="$HOME/bin:$PATH"    # 临时把自己的脚本目录放到最前
```

- `which` 只看 `PATH`；`type` 还能识别别名、函数、内建命令，排查「为什么执行的不是我想的那个」用它。
- 不要把 `.` 或当前目录放进 `PATH`：在别人目录里敲 `ls` 可能跑到恶意同名程序。
- 长期生效写进 `~/.bashrc` 或 `/etc/profile.d/xxx.sh`，改完 `source` 一下。

### 7.3 配置文件加载顺序

| 场景 | 读取顺序（自上而下） |
| --- | --- |
| 登录 shell：tty 登录、`ssh host`、`su -` | `/etc/profile` → `/etc/profile.d/*.sh` → `~/.bash_profile` → `~/.bash_login` → `~/.profile`（后三个只读第一个存在的） |
| 交互式非登录：图形终端新开窗口、直接敲 `bash` | `/etc/bash.bashrc`（Debian/Ubuntu）或 `/etc/bashrc`（RHEL） → `~/.bashrc` |
| 非交互：执行脚本 | 不读上面这些，只读 `$BASH_ENV`（通常没设） |

- 环境变量（`PATH`、`JAVA_HOME`）放 `/etc/profile.d/*.sh` 或 `~/.profile`；别名、提示符、补全放 `~/.bashrc`。
- `su alice` 不读登录文件、保留原环境；`su - alice` 才是完整登录。sudo 执行命令默认也不读 `~/.bashrc`，脚本里别依赖它。
- 改完用 `source ~/.bashrc` 立即生效，不必退出重登。

## 8 软件安装入门

### 8.1 包管理器能做什么

- 从配置好的仓库（`/etc/apt/sources.list*`、`/etc/yum.repos.d/*.repo`）下载包，并用 GPG 校验签名。
- 自动解析并安装依赖，避免「缺一个 .so 就起不来」。
- 把文件装到标准位置（`/usr/bin`、`/usr/lib`、`/etc`），并登记进本地数据库（Debian 是 `/var/lib/dpkg`，RHEL 是 `/var/lib/rpm`）。
- 支持升级、卸载、按文件反查所属包、校验完整性。
- 不管源码包和语言级包（`pip`、`npm`、`gem`），那是各自生态的包管理器。

### 8.2 apt 与 dnf 对照

| 操作 | Debian/Ubuntu（apt/dpkg） | RHEL/CentOS/Fedora（dnf，旧为 yum） |
| --- | --- | --- |
| 更新索引 | `apt update` | `dnf makecache` |
| 升级已装软件 | `apt upgrade` | `dnf upgrade` |
| 安装 / 卸载 | `apt install nginx` / `apt remove nginx` | `dnf install nginx` / `dnf remove nginx` |
| 彻底卸载含配置 | `apt purge nginx` | 无直接对应，手动删配置 |
| 搜索 / 详情 | `apt search` / `apt show` | `dnf search` / `dnf info` |
| 已安装列表 | `dpkg -l` | `rpm -qa` |
| 文件属于哪个包 | `dpkg -S /usr/sbin/nginx` | `rpm -qf /usr/sbin/nginx` |

- `apt update` 只刷新索引、不升级软件，这点最常被混淆；升级要再执行 `apt upgrade`。
- 装本地包：`apt install ./pkg.deb`、`dnf install ./pkg.rpm`；`dnf history` 可以回滚某次事务。

### 8.3 源码编译三步

```bash
./configure --prefix=/usr/local/nginx    # 检查依赖与编译环境，生成 Makefile
make -j"$(nproc)"                        # 编译，-j 用满所有核
make install                             # 安装到 --prefix 指定的目录
```

- 前提是装好工具链与开发库：Debian `apt install build-essential`，RHEL `dnf install gcc make`，报缺头文件时按名字装对应的 `-dev`/`-devel` 包。
- `--prefix` 决定安装路径，默认 `/usr/local`；装完二进制在 `/usr/local/nginx/sbin`，不在 `PATH` 里就要写全路径或自己做软链。
- 源码装的软件不受包管理器管理：升级要重新编译，卸载基本是 `rm -rf /usr/local/nginx`，装过什么只有自己记得。
- 三条命令中任何一步失败都别硬往下走，`configure` 失败要读它最后几行，缺什么装什么。

### 8.4 装完怎么确认

```bash
which nginx                 # 命令是否在 PATH 里
nginx -v                    # 版本，确认装的是哪一个
dpkg -S /usr/sbin/nginx     # Debian：这个文件属于哪个包
rpm -qf /usr/sbin/nginx     # RHEL：同上
dpkg -L nginx | head        # 列出这个包装了哪些文件
```

## 9 帮助与文档

### 9.1 man

| 章节 | 内容 | 例子 |
| --- | --- | --- |
| 1 | 用户命令 | `man ls` |
| 2 | 系统调用 | `man 2 open` |
| 3 | 库函数 | `man 3 malloc` |
| 4 | 设备与特殊文件 | `man 4 null` |
| 5 | 文件格式与配置 | `man 5 passwd`、`man 5 fstab` |
| 7 | 杂项、协议、宏包 | `man 7 tcp` |
| 8 | 系统管理命令 | `man 8 mount` |

```bash
man ls              # 看 ls 的完整手册
man 5 passwd        # 指定章节：/etc/passwd 的格式，而不是 passwd 命令
man -k password     # 按关键字搜索手册，等价于 apropos
```

- 手册里 `/关键字` 搜索、`n` 跳下一个、`q` 退出；`man -k` 依赖索引，新系统可能要先跑一次 `mandb`。
- 同名条目可能有多章，`man 5 passwd` 与 `man 1 passwd` 内容完全不同，这是新手最容易困惑的点。

### 9.2 其他入口

```bash
ls --help           # 大多数命令都支持，比 man 短，先看这个最快
help cd             # bash 内建命令（cd、export）没有 man 页，用 help
info coreutils      # GNU 项目的 info 文档，比 man 更详细
tldr tar            # 社区示例集，需先安装（apt install tldr），只给常用例子
```

- `/usr/share/doc/<包名>/`：README、changelog、示例配置，排障时经常能翻到官方说明。
- 配置目录里的 `*.conf.example` 与 `man 5 xxx.conf` 往往比网上博客准。

## 10 新手最常踩的 10 个坑

1. **`rm` 没有回收站。** 删掉就没了，`rm -rf $DIR/` 在 `DIR` 为空时会变成 `rm -rf /`。执行前先 `ls` 同参数确认，关键目录用 `rm -i`，或用 `trash-cli` 代替。
2. **用 `chmod 777` 解决一切权限问题。** 目录需要 `x` 才能进、删除看目录的 `w`，777 经常既解决不了问题又留下安全隐患，按最小权限给。
3. **`sudo echo x > /etc/f` 仍报 Permission denied。** 重定向由当前 shell 打开，sudo 只提权了 `echo`。改用 `sudo tee /etc/f` 或 `sudo sh -c 'echo x > /etc/f'`。
4. **Windows 编辑过的脚本报 `bad interpreter: /bin/bash^M`。** 是 CRLF 换行，`file`、`cat -A` 能看到 `^M`；用 `dos2unix a.sh` 或 `sed -i 's/\r$//' a.sh` 修，Git 里配 `core.autocrlf` 预防。
5. **`usermod -G` 漏了 `-a`。** 附加组被整体覆盖，用户悄悄掉出 `sudo`、`docker` 组；追加组一律写 `usermod -aG`。
6. **改完 systemd unit 不 `daemon-reload`。** 服务还是旧配置，甚至 `start` 报错；改 unit 后 `systemctl daemon-reload && systemctl restart xxx`。
7. **把 `apt update` 当成升级。** 它只刷新索引；升级是 `apt upgrade`，而且装包前先 `update` 才能拿到新版本。
8. **服务本机通、外面不通。** 常见是只监听 `127.0.0.1`，或防火墙没放行；`ss -tulnp` 看监听地址，再查 `firewall-cmd` / `ufw`。
9. **磁盘还有空间却写不进文件。** 多半是 inode 用完（`df -i`）或文件已删但被进程占用（`lsof +L1`），`df -h` 看着有空间也没用。
10. **长期用 root、直接手改 `/etc/sudoers`。** 前者手滑代价最大，后者写坏就没人能提权；用 `visudo`、按用户放 `/etc/sudoers.d/`，日常普通用户 + sudo。

## 11 下一步

本篇解决「是什么、怎么登录、目录与权限、用户怎么管、软件怎么装」。往下按这个顺序走：

- [Linux常用命令](Linux常用命令.md)：文件、文本、查找、压缩、进程、网络、磁盘的命令速查，配合本篇第 4、5 章边看边敲。
- [Linux详解](Linux详解.md)：进程与信号、systemd、磁盘与文件系统、网络与防火墙、Shell 脚本、性能排查、容器基础。
- [Linux面试题](Linux面试题.md)：25 道高频问答，遮住答案自测，答不出的回到对应章节。

自测清单（能全部说清再往下走）：

1. `-rwxr-xr--` 是什么权限？`umask 022` 下新建文件和目录各是多少？
2. 目录的 `r` 和 `x` 分别管什么？为什么给文件 `777` 也可能执行失败？
3. 用户被加进 `docker` 组，为什么当前终端不生效？
4. 登录 shell 与交互式非登录 shell 分别读哪些配置文件？
5. 源码编译装的软件，怎么查它装到哪、又该怎么卸载？
