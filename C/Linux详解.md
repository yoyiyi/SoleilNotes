# Linux 详解
面向面试的 Linux 进阶笔记：进程 / 内存 / 文件系统 / systemd / 网络 / 容器，按「原理 + 可操作命令」组织；默认值随发行版与内核版本变化，以 `man` 和发行版文档为准。

- 定位：进阶原理与系统管理，命令清单与专项排查拆在姊妹篇（见第 12 章）。
- 约定：`#` 表示需 root；示例网卡 `eth0`、磁盘 `sda`、服务 `nginx`；基准内核 5.10+、systemd 249+、Docker 24+。

## 1 内核与启动流程
开机是一条串行链：固件 → GRUB → 内核 → initramfs → 真根 → systemd → 用户态；每环失败的表现都不同，先定位卡在哪一段。

### 1.1 固件：BIOS 与 UEFI
| 对比项 | Legacy BIOS | UEFI |
| --- | --- | --- |
| 运行模式 | 16 位实模式，1 MB 寻址 | 32/64 位，可访问全部内存 |
| 分区表 | MBR（单盘 2 TB 上限） | GPT（64 位 LBA） |
| 引导文件 | 读 MBR 前 446 字节的引导代码 | 从 ESP（FAT32，通常 `/boot/efi`）加载 `.efi` |
| 启动项 | 固定在磁盘 MBR | 存在主板 NVRAM，`efibootmgr` 管理 |
| 安全启动 | 无 | Secure Boot：只运行有签名的引导器（shim） |

```bash
[ -d /sys/firmware/efi ] && echo UEFI || echo BIOS   # 判断当前启动方式
efibootmgr -v                                        # 看/改 UEFI 启动项
```

### 1.2 引导加载器 GRUB2
BIOS 下是 MBR 的 `boot.img` + 嵌在扇区间隙的 `core.img`，UEFI 下是 ESP 上的 `grubx64.efi`（开了 Secure Boot 先跑签名的 `shimx64.efi`）。`grub.cfg`（RHEL 为 `/boot/grub2/grub.cfg`）是生成物，**不要手改**：改 `/etc/default/grub` 与 `/etc/grub.d/` 后重新生成，临时改参数在启动菜单按 `e`。

```bash
cat /proc/cmdline                         # 本次实际生效的参数
grub2-mkconfig -o /boot/grub2/grub.cfg    # RHEL；Debian 用 update-grub
grubby --update-kernel=ALL --args="transparent_hugepage=never"   # RHEL 持久化
```

高频参数：`root=UUID=...`、`ro`/`rw`、`console=ttyS0,115200`、`systemd.unit=rescue.target`、`init=/bin/bash`、`rd.break`（重置密码）、`nomodeset`、`ip=`（网络根）、`crashkernel=`。

### 1.3 内核初始化
`vmlinuz` 自解压后进 `start_kernel()`：解析 cmdline 与设备树 → 建页表、初始化内存管理 → 初始化调度/中断/时钟 → 按 initcall 顺序 probe 驱动 → 创建 PID 1（`kernel_init`，最终 exec 成 systemd）与 PID 2（`kthreadd`）。根设备驱动不在内核里时必须靠 initramfs；内核日志只在 ring buffer（`log_buf_len=1M` 可调）里，`kernel.dmesg_restrict=1` 时普通用户读不到 `dmesg`。

### 1.4 initramfs：为什么要两阶段挂根
initramfs 是 cpio 归档（gzip/zstd 压缩），内核解到内存 tmpfs 后执行 `/init`；它存在的唯一理由，是**挂真根所需的驱动可能在模块里**——LVM、LUKS、软 RAID、iSCSI/NFS 根、非主流存储控制器。

```bash
lsinitrd /boot/initramfs-$(uname -r).img | head   # 看内容（dracut 系）
dracut -f                                         # 重建；Debian 用 update-initramfs -u -k all
```

换存储控制器、加 LUKS、内核升级后漏重建，就会 `Unable to mount root fs` 并落进救援 shell；在 GRUB 补 `rd.lvm.lv=`、`rd.luks.uuid=`，或进救援重建。`switch_root` 到真根后执行 `/sbin/init`，内核退居幕后。

### 1.5 systemd 接管
systemd 并行拉起 unit，按 target 汇聚：`sysinit.target`（挂载、udev、tmpfiles）→ `basic.target` → `multi-user.target`（≈runlevel 3）→ `graphical.target`（≈5）；`rescue.target` 与 `emergency.target` 用于救援。随后 journald 收日志、udevd 管设备、getty/sshd 提供登录，经 PAM 进 shell。

### 1.6 用 dmesg 看启动日志
```bash
dmesg -T | head -50                    # 带时间戳，看固件与内核早期
dmesg -T -l err,crit,alert,emerg       # 只看错误级别
journalctl -k -b                       # 本次启动的内核日志（持久化，不会被覆盖）
```

高频报错：`ACPI Error`（多为固件 bug，常可忽略）、`Timed out waiting for device`（fstab 里的设备不存在，修 UUID 或加 `nofail`）、`Failed to start xxx`（再 `journalctl -u xxx -b`）、开机即 `Out of memory`；RHEL 另有 `/var/log/boot.log`。

## 2 文件系统
VFS 把 ext4、XFS、Btrfs、NFS、proc 统一成同一套接口，所以 `cp`/`ls` 不关心底层。

### 2.1 inode 与数据块
inode 存类型、权限、属主/属组、大小、atime/mtime/ctime、数据块指针、链接数、xattr 位置；**文件名在目录项里**，目录本身也是文件，内容是「文件名 → inode 号」的表。所以同一 inode 可有多个名字（硬链接），inode 号只在单个文件系统内唯一。

```bash
stat file          # inode 号、链接数、块数、三个时间戳
df -i              # 各文件系统 inode 使用率
```

- 寻址：ext2/3 用「12 直接 + 一/二/三级间接块」，ext4 改用 extent（连续块区间），元数据更少、碎片更少；块大小默认 4 KiB。
- inode 数量：ext4 在 `mkfs` 时**固定**（`-N` 个数，`-i` 每多少字节一个，默认 16384）之后不能扩；XFS **动态分配**，不会因 inode 用尽而建不了文件。
- 增删目录项就是改父目录的数据块，所以**删除文件看的是目录的 `w`+`x`**，与文件自身权限无关；dcache 缓存「名字 → inode」，`ls` 大目录第一次慢、后面快就是它。
- inode 耗尽的表现是「`df -h` 还有空间却报 `No space left on device`」，清海量小文件或重建文件系统加大 inode 密度。

### 2.2 硬链接与软链接
```bash
ln a.txt b.txt                  # 硬链接：同一 inode，链接数 +1
ln -s /opt/app/current c.txt    # 软链接：新 inode，内容是路径
readlink -f c.txt               # 展开为最终绝对路径
```

| 对比项 | 硬链接 | 软链接（符号链接） |
| --- | --- | --- |
| inode | 与原文件**同一个** | 独立 inode，内容是目标路径字符串 |
| 链接数 | 每加一个名字 `links +1`，删到 0 才释放数据 | 不影响目标的链接数 |
| 跨文件系统 | 不可以（inode 号只在单 fs 内唯一） | 可以 |
| 指向目录 | 一般不允许（防环，仅 `.`/`..` 内核特批） | 可以 |
| 原文件删除后 | 仍可访问，链接数减 1 | 变悬挂链接（dangling） |
| 大小 / 权限 | 与目标相同、共用权限 | 大小为路径长度，自身 `777` 无意义 |

发布用 `ln -sfn /opt/app/v2 /opt/app/current` 原子切换（`-n` 防止把链接建进目录）；**相对路径软链**在 bind mount、chroot、容器里易断，跨环境用绝对路径；硬链接可做备份去重（`cp -al`、`rsync --link-dest`）。

### 2.3 ext4 / XFS / Btrfs
| 特性 | ext4 | XFS | Btrfs |
| --- | --- | --- | --- |
| 日志 | 有，默认 `data=ordered` | 有，只记元数据 | CoW，无传统日志 |
| 分配 | extent + 延迟分配 + 多块分配 | B+ 树 + 延迟分配 | extent 树 + CoW |
| 最大卷 / 单文件 | 1 EiB / 16 TiB | 8 EiB / 8 EiB | 16 EiB / 16 EiB |
| 在线扩容 | 支持（`resize2fs`），缩容需卸载 | 支持（`xfs_growfs`），**不支持缩容** | 支持，可在线增删设备 |
| 快照 / 压缩 | 无（靠 LVM） | 无（靠 LVM） | 原生快照、子卷、zstd 压缩 |
| 数据校验 | 仅元数据 | 仅元数据 | 数据 + 元数据校验和 |
| fsck | `e2fsck`，海量文件慢 | `xfs_repair`，快 | `btrfs check`，慎用 |
| 默认发行版 | Debian/Ubuntu | RHEL/CentOS 7+ | SUSE、Fedora 工作站 |

ext4 兼容 ext3 并可原地挂载升级；ext2 无日志、断电易损；XFS 删大文件后 `df` 不立刻变小是延迟回收，属正常。

### 2.4 /etc/fstab 六字段
| # | 字段 | 说明 | 示例 |
| --- | --- | --- | --- |
| 1 | 设备 | 用 `UUID=`/`LABEL=`（`blkid` 查），别写 `/dev/sda1` | `UUID=3f2a...` |
| 2 | 挂载点 | 目录；路径含空格写 `\040` | `/data` |
| 3 | 类型 | `ext4`、`xfs`、`btrfs`、`swap`、`nfs`、`auto` | `xfs` |
| 4 | 选项 | 逗号分隔，见下 | `defaults,noatime` |
| 5 | dump | 备份标志，几乎总是 `0` | `0` |
| 6 | pass | fsck 顺序：根为 `1`，其他 `2`，`0` 不检查 | `2` |

```conf
# <device>          <mount point>  <type>  <options>                <dump> <pass>
UUID=3f2a1b7c-...    /              xfs     defaults                     0      1
UUID=8c11e0d2-...    /data          ext4    defaults,noatime,nofail      0      2
/swapfile            none           swap    sw                           0      0
```

常用选项：`defaults`（= `rw,suid,dev,exec,auto,nouser,async`）、`noatime`、`ro`、`noexec`/`nosuid`/`nodev`（`/tmp` 加固三件套）、`nofail`（设备缺失不阻塞开机）、`x-systemd.automount`（按需挂载）、`_netdev`（等网络就绪）。改完先验证再重启：

```bash
mount -a                 # 按 fstab 挂载所有未挂项，报错即语法/设备问题
findmnt --verify         # 校验语法与选项
systemctl daemon-reload  # fstab 会转成 .mount unit，改完需重载
```

### 2.5 挂载与 mount --bind
挂载的本质是把文件系统的根接到目录树某点，被盖住的旧内容不删除（`umount` 后重现）；`--bind` 把**已有目录**再挂到另一处，是 chroot、容器卷、把 `/data/www` 暴露成 `/var/www/html` 的标准手法。

```bash
mount /dev/sdb1 /mnt                     # 普通挂载
mount -o remount,rw /                    # 只读根改回读写（救援常用）
mount --bind /data/www /var/www/html     # 绑定挂载
mount --rbind /dev /mnt/chroot/dev       # 递归绑定（含子挂载）
findmnt -T /var/www/html                 # 查某路径最终来自哪个挂载
```

绑定挂载默认 `shared` 传播，宿主机新挂载会「漏」进 chroot/容器，隔离前先 `mount --make-rslave /mnt/chroot`；`/proc/mounts` 是内核视角的权威列表。

### 2.6 df 与 du 为什么不一致
`df` 读 superblock 的块统计（整个文件系统），`du` 遍历目录按路径累加，口径不同，差异是常态。

| 原因 | 现象 | 验证 |
| --- | --- | --- |
| 文件已删除但被进程持有 | `df` 显示占用，`du` 找不到文件 | `lsof +L1` 看 `deleted` |
| 挂载点被覆盖 | `du` 统计的是被遮住的下层 | `findmnt` + 卸载后重查 |
| 稀疏文件 | `du` 按实际块算，小于表观大小 | `du --apparent-size`、`ls -ls` |
| 硬链接被重复统计 | 分别 `du` 各子目录再相加偏大 | 对父目录一次 `du` |
| 权限不足 / 保留块 | `du` 跳过目录偏小；ext4 给 root 留 5% | `sudo du -sh`、`tune2fs -l` |
| 元数据与容器层 | `df` 的 used 含 inode 表与日志；容器内看 overlay 聚合 | `du -x --apparent-size`、`docker system df` |

## 3 权限与安全
Linux 权限分两层：`rwx` 与 ACL 属 **DAC**（自主访问控制），SELinux/AppArmor 属 **MAC**（强制访问控制）；MAC 在 DAC 放行之后**再判一次**，所以「权限明明对却读不了」多半是 MAC 拦的。

### 3.1 权限模型与身份
| 权限 | 对文件 | 对目录 |
| --- | --- | --- |
| `r` | 读内容 | 列出文件名（`ls`） |
| `w` | 改内容 | 在目录内创建/删除/改名文件 |
| `x` | 执行 | 进入目录（`cd`）、访问其中文件的 inode |

推论：**删除文件只看父目录的 `w`+`x`**；目录有 `r` 无 `x` 时只看得到名字、看不到属性。

```bash
chmod 755 run.sh              # 数字法 r=4 w=2 x=1
chmod u+x,g-w,o=r run.sh      # 符号法 u/g/o/a + +/-/= + rwx
chown -R www-data:www-data /var/www   # 改属主与属组，-R 递归
```

### 3.2 umask 计算
`umask` 是「被屏蔽的位」，只能减不能加：`实际权限 = 基准 & ~umask`，文件基准 `666`、目录基准 `777`。

| umask | 新建文件 | 新建目录 | 场景 |
| --- | --- | --- | --- |
| `022` | `644` | `755` | 默认，同组可读 |
| `027` | `640` | `750` | 生产常用，其他人无权限 |

手算：`022` 取反 `755`，`666 & 755 = 644`，`777 & 755 = 755`；`027` 取反 `750` → `640`/`750`。设置在 `/etc/profile`、`~/.bashrc`、`/etc/login.defs` 的 `UMASK`、PAM 的 `pam_umask`；root 也受 umask 约束，只是能绕过 `r/w` 检查。

### 3.3 SUID / SGID / Sticky
| 特殊位 | 数字 | 作用 | 典型 |
| --- | --- | --- | --- |
| SUID | `4755` | 执行时**有效 UID** 变成文件属主 | `/usr/bin/passwd` |
| SGID | `2755` | 文件：有效 GID 变成属组；目录：新建文件继承目录属组 | 协作目录、`/var/log/journal` |
| Sticky | `1775` | 目录内文件只有属主、目录属主或 root 能删 | `/tmp` |

原理在 `execve`：内核看到 `S_ISUID` 就把 `euid` 设为文件属主，原 `uid` 存进 `saved setuid`（提权后能降回）。`passwd` 正是靠它：普通用户运行时 `ruid=alice`、`euid=root`，才有权写 `/etc/shadow`；`ls -l` 里显示为 `s`/`S`（无 `x` 时大写）与 `t`/`T`。

```bash
find / -perm -4000 -type f 2>/dev/null   # SUID 文件（至少含该位）
find / -perm /6000 -type f 2>/dev/null   # SUID 或 SGID
```

SUID 是最常见的本地提权面：程序里有命令注入、`system()`、溢出，或本身能执行任意命令（`find -exec`、`vi` 的 `:!sh`）就等于送 root；**shell 脚本上的 SUID 会被内核忽略**。更细粒度用 capabilities：`setcap cap_net_bind_service=+ep /usr/local/bin/app` 让非 root 绑 80 端口。

### 3.4 ACL
标准权限只有「一个属主 + 一个属组」，ACL 可给任意用户/组单独授权，`ls -l` 权限位末尾的 `+` 表示存在 ACL。

```bash
setfacl -m u:alice:rw report.txt      # 给单用户授权
setfacl -m g:dev:rx -R /data          # 递归给组
setfacl -d -m u:alice:rw /data        # 目录默认 ACL，新建文件自动继承
getfacl -R /data > acl.bak            # 备份；恢复 setfacl --restore=acl.bak
```

ACL 存在扩展属性 `system.posix_acl_access` 里，ext4 默认开、XFS 默认支持；`getfacl` 输出里的 `mask` 是权限上限，`chmod g-w` 改的其实是 mask，会把组 ACL 一并压掉。

### 3.5 SELinux 与 AppArmor
| 对比项 | SELinux | AppArmor |
| --- | --- | --- |
| 判据 | **标签**（安全上下文），类型强制 | **路径**，profile 里写文件路径 |
| 粒度 | 细，进程类型 × 文件类型 × 布尔开关 | 中，按程序绑定路径规则 |
| 默认发行版 | RHEL/CentOS/Fedora | Ubuntu/Debian/SUSE |
| 模式 | `enforcing`/`permissive`/`disabled` | `enforce`/`complain` |
| 查看 | `getenforce`、`sestatus` | `aa-status` |
| 拒绝日志 | `ausearch -m avc -ts recent`、`/var/log/audit/audit.log` | `journalctl -k` 的 `apparmor="DENIED"` |
| 放行 | `semanage fcontext` + `restorecon`、布尔、`audit2allow` | 改 profile、`aa-complain` 观察 |

SELinux 上下文形如 `system_u:object_r:httpd_sys_content_t:s0`（用户、角色、类型、级别），**策略实际只看类型**；排障顺序是 `ls -Z`/`ps -Z` 看标签 → `ausearch` 确认被拒 → 标签错就 `restorecon -Rv`，确需新规则则 `audit2allow -a -M mypol` 后 `semodule -i` → 最后才 `setenforce 0` 临时关。

### 3.6 sudo 与提权审计
```bash
visudo                            # 带语法检查地编辑 /etc/sudoers
visudo -f /etc/sudoers.d/deploy   # 更推荐：drop-in，升级不冲突
sudo -l                           # 当前用户能执行什么
```

语法 `用户 主机=(可切换用户:组) 命令`，如 `alice ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx`；`%wheel`、`%sudo` 是组授权，常用 `Defaults` 有 `env_reset`、`secure_path`、`timestamp_timeout=5`。

安全要点：给**具体命令**而不是 `ALL`；`NOPASSWD` 只给自动化账号；通配符规则可能被参数绕过（`tar --checkpoint-action=exec`、编辑器 `:!sh`）；被 sudo 调用的脚本必须 root 属主且他人不可写。日志在 Debian 的 `/var/log/auth.log`、RHEL 的 `/var/log/secure`，或 `journalctl _COMM=sudo -b`，每条带 `SUDO_COMMAND`。

## 4 进程与线程
内核用 `task_struct` 描述进程、`mm_struct` 描述地址空间、`files_struct` 描述文件表；线程是**共享 `mm_struct` 的 `task_struct`**（`clone()` 带 `CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|CLONE_THREAD`）。线程共享地址空间、fd、信号处理表、cwd，各有独立栈、寄存器、`errno`、`tid`；TGID 等于主线程 PID，`ps -eLf`、`top -H` 看线程。

### 4.1 进程状态
| 状态 | 含义 | 说明 |
| --- | --- | --- |
| `R` | running / runnable | 在跑或在运行队列等 CPU |
| `S` | interruptible sleep | 等事件（IO、锁、`sleep`），可被信号唤醒，最常见 |
| `D` | uninterruptible sleep | 等内核态 IO/锁，**信号也要等系统调用返回** |
| `T` | stopped | `SIGSTOP` 或调试器暂停（`t` 为被追踪） |
| `Z` | zombie | 已退出，等父进程 `wait()` 收尸 |
| `I` | idle | 空闲内核线程，不计入负载 |

`D` 最需警惕：进程卡在磁盘、NFS、驱动里，`kill -9` 也杀不掉，而且**计入 load average**——于是出现「负载 20、CPU 95% idle」；用 `ps -eo stat,pid,wchan:32,cmd | awk '$1 ~ /^D/'` 定位。

```bash
ps aux                       # BSD 风格，含 %CPU、%MEM、STAT
ps -ef                       # System V 风格，含 PPID
ps -eo pid,ppid,stat,pcpu,pmem,rss,cmd --sort=-pcpu | head
top                          # P 按 CPU、M 按内存、1 展开各核、c 完整命令行、H 线程、k 发信号
```

### 4.2 fork / exec / wait
```c
pid_t pid = fork();              // 父进程得到子 PID，子进程得到 0，失败 -1
if (pid == 0) {
    execve("/bin/ls", argv, envp);   // 成功则永不返回
    _exit(127);
}
waitpid(pid, &status, 0);        // 回收；WIFEXITED(status) 判断是否正常退出
```

- `fork`：复制 `task_struct`，**地址空间用写时复制共享**，fd 表复制（指向同一 `file` 对象，共享偏移），信号处理函数继承、未决信号清空。
- `execve`：替换 `mm_struct`，**PID 不变**，除 `FD_CLOEXEC` 外 fd 保留，cwd、umask、信号掩码保留，被捕获的处理函数重置为默认。
- `wait`/`waitpid`：回收并取退出状态（`WIFEXITED`/`WEXITSTATUS`、`WIFSIGNALED`/`WTERMSIG`），`WNOHANG` 非阻塞轮询，`SIGCHLD` 通知状态变化；`vfork`/`posix_spawn` 可省掉页表复制。

### 4.3 写时复制（CoW）
`fork` 不复制物理页，而是把父子页表项都标**只读**并给 page 加引用计数；任一方写入触发缺页，内核才分配新页、复制内容、恢复可写。于是 `fork` 极快，`fork` + 立即 `exec` 几乎零拷贝，子进程写多少才复制多少。风险在 overcommit：几十 GB 的进程 `fork` 后大量写可能瞬间 OOM，`redis BGSAVE`、`nginx` 平滑重启都依赖 CoW，写压力大时内存会翻倍。

### 4.4 僵尸与孤儿
| 对比 | 僵尸进程 | 孤儿进程 |
| --- | --- | --- |
| 成因 | 子进程已退出，父进程没 `wait()` | 父进程先退出，自己还在跑 |
| 状态 | `Z`，内存已释放，只剩 PID 与退出码 | 仍在运行 |
| 归属 | 父进程（`ps` 的 PPID 指向它） | 被 PID 1 或最近的 subreaper 收养 |
| 危害 | 占 PID 表项与 `task_struct`，多了耗尽 `pid_max` | 通常无害，但会脱管 |
| 处理 | 修父进程回收逻辑；或杀父进程使其被收养；`kill -9` 对僵尸无效 | 一般无需处理，服务用 systemd 托管 |

容器里 PID namespace 的 PID 1 必须收尸，否则僵尸堆积——`docker run --init`（注入 tini）或应用自己 `waitpid(-1, ..., WNOHANG)`。

### 4.5 信号机制
信号是内核递送的异步通知，只在**从内核态返回用户态**时处理，所以 `D` 状态收不到、`kill -9` 也要等。

| 信号 | 编号 | 默认动作 | 用途 |
| --- | --- | --- | --- |
| `SIGHUP` | 1 | 终止 | 终端挂断；守护进程常用来重载配置 |
| `SIGINT` | 2 | 终止 | `Ctrl-C` |
| `SIGKILL` | 9 | 终止 | 强制杀死，不可捕获/忽略/阻塞 |
| `SIGUSR1` | 10 | 终止 | 自定义（如 nginx 重开日志） |
| `SIGSEGV` | 11 | 终止 + core | 非法内存访问 |
| `SIGPIPE` | 13 | 终止 | 写已关闭的管道/套接字 |
| `SIGTERM` | 15 | 终止 | 默认终止信号，可捕获以优雅退出 |
| `SIGCHLD` | 17 | 忽略 | 子进程状态变化 |
| `SIGCONT` | 18 | 继续 | 恢复暂停的进程 |
| `SIGSTOP` | 19 | 暂停 | 不可捕获 |
| `SIGTSTP` | 20 | 暂停 | `Ctrl-Z` |

```bash
kill -l                    # 列出所有信号
kill -15 1234              # 先请求优雅退出
kill -9 1234               # 再强制杀死，可能丢数据
pkill -f 'python worker'   # 按完整命令行匹配
kill -- -1234              # 给整个进程组发（注意负号）
```

`SIGTERM` vs `SIGKILL`：前者能被捕获，程序可关连接、刷盘、删临时文件，是**唯一应作为第一选择**的信号；后者由内核直接抹掉进程、不做任何清理，只在进程无响应或用户态死循环时用。`systemctl stop` 先发 `SIGTERM`，等 `TimeoutStopSec`（默认 90s）再 `SIGKILL`，与 `docker stop` 的 10s 超时同一逻辑。

两个易错点：标准信号用位图实现、**不排队**，连发多次可能只递送一次（实时信号会排队）；进程处于 `D`、是僵尸、或被父进程反复拉起时，「`kill -9` 杀不掉」是正常现象。

### 4.6 /proc/<pid> 关键文件
| 路径 | 内容 |
| --- | --- |
| `status` | 状态、`PPid`、`VmRSS`/`VmSize`、`Threads`、`SigQ`、`CapEff` |
| `cmdline` / `environ` | 启动参数（`\0` 分隔）/ 环境变量，查密钥泄漏 |
| `cwd` / `exe` / `root` | 工作目录、可执行文件、根目录的软链 |
| `fd/`、`fdinfo/` | 打开的描述符与偏移/标志，查句柄泄漏 |
| `maps` / `smaps_rollup` | 地址空间映射 / 汇总的 RSS/PSS/USS（比 `smaps` 快） |
| `wchan` / `stack` | 卡在哪个内核函数 / 内核栈（需 root） |
| `oom_score` / `oom_score_adj` | OOM 评分与可调偏移（见 5.5） |
| `cgroup` / `ns/` | 所属 cgroup 层级 / 8 种 namespace 的软链 |

### 4.7 cgroup 与进程隔离
cgroup 回答「能用多少资源」，namespace 回答「能看见什么」；v2 是单层树，控制器挂在 `/sys/fs/cgroup`，`cat /sys/fs/cgroup/cgroup.controllers` 看可用控制器。

systemd 给每个 service 自动建 `system.slice/<name>.service`，所以 `systemctl stop` 能连它 fork 出的进程一起干掉——这是相对 SysV init 的核心优势，也是容器资源限制的底层（见第 10 章）。

## 5 内存管理
每个进程都以为自己独占地址空间，这是虚拟内存的假象：MMU 用页表把虚拟地址翻译成物理地址，内核负责建表、换页、回收。

### 5.1 虚拟内存与页表
- 64 位下用户态通常 128 TiB（47 位），内核在高半区；32 位经典划分 3G/1G。
- 页 4 KiB，四级页表 `PGD → PUD → PMD → PTE`；大页 2 MiB/1 GiB 减少 TLB miss。
- 按需分页：`malloc` 只建 VMA，首次访问才缺页分配；**minor fault** 不读盘（零页、CoW、缓存命中），**major fault** 要读盘，是性能杀手。
- 匿名页（堆、栈，只能换到 swap）与文件页（page cache，可丢弃重读）的区分，决定内存紧张时先回收谁。

```bash
grep -E 'VmRSS|VmSize|VmSwap' /proc/<pid>/status
pmap -x <pid> | tail -1                      # 汇总 RSS/Dirty/Swap
```

### 5.2 内存指标别混用
| 指标 | 含义 | 来源 |
| --- | --- | --- |
| VIRT / VSZ | 虚拟地址空间总量，含未分配页与映射，**偏大很正常** | `top` VIRT、`ps` VSZ |
| RES / RSS | 常驻物理内存，**共享页被重复计算** | `top` RES、`ps` RSS |
| PSS | 共享页按共享者数量摊分，最能反映真实占用 | `smaps_rollup`、`smem` |
| USS | 独占内存，共享页完全不计 | `smaps` |

粗筛用 `ps -eo pid,rss,cmd --sort=-rss`，精查用 `smaps_rollup`；容器里 `docker stats` 的 `MEM USAGE` 是 cgroup 口径（`memory.current` 减可回收的 `inactive_file`），与进程 RSS 相加不是一回事。

### 5.3 free 的 buff/cache
```bash
free -h
#               total        used        free      shared  buff/cache   available
# Mem:           15Gi        4.2Gi       1.1Gi       210Mi        10Gi        10Gi
```

- `free` 是**完全未使用**的内存，数值小是健康的——Linux 主动拿空闲内存做 page cache。
- `buff/cache` = 块设备缓冲 + 文件页缓存，**绝大部分可回收**（脏页需先回写）；老式 `-/+ buffers/cache` 两行是 `available` 的前身。
- `available` 是内核估算的「新程序能用多少」，含可回收缓存，**只有它才是可用内存**；它低且 `si/so` 持续非 0 才是真不足。

### 5.4 swap 与 swappiness
```bash
fallocate -l 2G /swapfile && chmod 600 /swapfile
mkswap /swapfile && swapon /swapfile            # fstab 写 /swapfile none swap sw 0 0
swapon --show
```

`vm.swappiness` 范围 0~200（5.8 前 0~100），默认 60，值越大越愿意换出匿名页；数据库常设 `1`，桌面 `10~60`。`si/so` 持续非 0 说明已在颠簸（thrashing），性能断崖式下降；`zram`、`zswap` 能显著减少实际 IO。

### 5.5 OOM Killer
内存彻底不够时，内核按坏度评分挑一个进程杀掉；评分主要看 `oom_score_adj`（-1000~1000，越小越不易被杀）与内存占用，`oom_score` 是最终分值。

```bash
dmesg -T | grep -i -E 'out of memory|killed process'
# Out of memory: Killed process 12345 (java) total-vm:8123456kB,
#   anon-rss:2048000kB, file-rss:1024kB, shmem-rss:0kB, UID:1000
echo -1000 > /proc/<pid>/oom_score_adj    # 保护关键进程（-1000 永不被杀）
systemctl set-property app.service MemoryMax=1G MemoryMin=256M
```

看 `anon-rss`（通常就是元凶）与触发时的水位，`total-vm` 大不代表吃内存；cgroup v2 的 OOM 是组内杀，`memory.events` 的 `oom`/`oom_kill` 计数增长，`memory.oom.group=1` 让整组一起被杀。想提前干预而不是等内核杀，用 `systemd-oomd` 或 `earlyoom`。

### 5.6 vmstat 关键列
```bash
vmstat 1 5        # 每秒一行共 5 行；第一行是自启动以来的平均值，忽略
vmstat -w         # 宽格式，列名更清楚
```

| 列 | 含义 | 判读 |
| --- | --- | --- |
| `r` | 运行队列长度（在跑 + 等 CPU） | 持续 > CPU 核数说明 CPU 不足 |
| `b` | 不可中断睡眠进程数 | 持续 > 0 多为 IO/锁瓶颈 |
| `swpd` | 已用 swap | 大不一定坏，配合 si/so 看 |
| `free` / `buff` / `cache` | 空闲 / 块缓冲 / 页缓存 | `free` 小是常态，后两者可回收 |
| `si` / `so` | 换入/换出 KB/s | 持续非 0 = 内存不足 |
| `in` / `cs` | 每秒中断数 / 上下文切换 | `cs` 远高于 `in` 且 CPU 高，查线程争抢 |
| `us`/`sy`/`id`/`wa`/`st` | 用户/系统/空闲/IO 等待/被虚拟化偷走 | `wa` 高看磁盘，`st` 高找宿主机 |

## 6 systemd
systemd 是 PID 1，用 unit 统一描述服务、挂载、定时器、套接字、设备，并按依赖图**并行**启动；抓住「unit + 依赖 + cgroup」三件事，多数服务问题都能定位。

### 6.1 unit 类型
| 后缀 | 用途 | 例子 |
| --- | --- | --- |
| `.service` | 守护进程或一次性任务 | `nginx.service` |
| `.target` | unit 集合，替代运行级别 | `multi-user.target`（≈3） |
| `.timer` | 定时触发，替代 cron，`Persistent=true` 可补跑错过的任务 | `logrotate.timer` |
| `.socket` | 套接字激活，有连接才拉起服务 | `docker.socket` |
| `.mount` / `.automount` | 挂载点（fstab 自动生成）/ 按需挂载 | `data.mount` |
| `.slice` / `.scope` | 资源分组 / 外部创建的进程组 | `system.slice` |

运行级别对照：`poweroff`=0、`rescue`=1、`multi-user`=3、`graphical`=5、`reboot`=6；timer 比 cron 强在可依赖、可补跑、日志进 journal、能限资源。

### 6.2 依赖与顺序
**依赖**决定「要不要一起启停」，**顺序**决定「谁先谁后」，两者正交。

- `Requires=` 强依赖，被依赖者失败则本 unit 失败；`Wants=` 弱依赖，失败不影响；`Requisite=` 启动前必须已 active；`BindsTo=` 对方停本 unit 也停；`PartOf=` 连带重启/停止；`Conflicts=` 互斥。
- `After=`/`Before=` 只调顺序，不建立依赖；**只写 `After=` 忘了 `Wants=`，就是「启动时网络还没好」的经典原因**。
- 默认依赖：service 自动 `After=basic.target`、`Before=shutdown.target` 并 `Conflicts=shutdown.target`；`list-dependencies` 看依赖树，`show -p After -p Wants` 看实际生效值。

### 6.3 systemctl 命令表
| 操作 | 命令 |
| --- | --- |
| 启 / 停 / 重启 / 重载配置 | `systemctl start|stop|restart|reload nginx`（失败则重启用 `try-restart`） |
| 状态（含最近日志与 cgroup） | `systemctl status nginx` |
| 是否运行 / 是否自启 | `systemctl is-active nginx`、`is-enabled nginx` |
| 开机自启并立即启动 | `systemctl enable --now nginx` |
| 取消自启 / 彻底屏蔽 | `systemctl disable nginx`、`systemctl mask nginx`、`unmask` |
| 运行中的 unit / 已安装 unit | `systemctl list-units --type=service`、`list-unit-files` |
| 启动失败 / 定时器 / 套接字 | `systemctl --failed`、`list-timers`、`list-sockets` |
| 看 / 改 unit 文件 | `systemctl cat nginx`、`systemctl edit --full nginx` |
| 加 drop-in 覆盖 / 改单属性 | `systemctl edit nginx`、`set-property` |
| 看所有生效属性 | `systemctl show nginx` |
| 改 unit 后重载 / 重载 systemd 自身 | `systemctl daemon-reload`、`daemon-reexec` |
| 切 / 查 / 设默认 target | `systemctl isolate rescue.target`、`get-default`、`set-default` |
| 发信号 / 定位 unit 路径 | `systemctl kill -s HUP nginx`、`show -p FragmentPath nginx` |

unit 查找顺序：`/etc/systemd/system` > `/run/systemd/system` > `/usr/lib/systemd/system`（发行版自带，**不要直接改**）；自建 unit 放 `/etc/systemd/system`，改完必须 `daemon-reload`。

### 6.4 写一个生产可用的 service
```ini
[Unit]
Description=My App API
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=60
StartLimitBurst=5

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/myapp
Environment=TZ=Asia/Shanghai
EnvironmentFile=-/etc/myapp/env
ExecStart=/opt/myapp/bin/start.sh
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
KillMode=mixed
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/var/lib/myapp /var/log/myapp

[Install]
WantedBy=multi-user.target
```

要点：`Type=simple` 适合前台进程（传统自守护用 `forking`，一次性任务 `oneshot`，就绪通知 `notify`）；`Restart=` 取 `no`/`on-failure`/`always`，配 `StartLimitBurst` 防疯狂重启；`EnvironmentFile=-` 的 `-` 表示文件可缺失，别在 `ExecStart` 里内联密钥；`KillMode=mixed` 先给主进程 `SIGTERM`、超时再给整个 cgroup `SIGKILL`；`ProtectSystem=strict` 让文件系统只读，需 `ReadWritePaths` 放行，`PrivateTmp` 隔离 `/tmp`；`$MAINPID` 供 `ExecReload` 用。

```bash
systemctl daemon-reload && systemctl enable --now myapp
journalctl -u myapp -n 50 --no-pager
```

### 6.5 journalctl 常用组合
```bash
journalctl -u nginx -f                                  # 跟踪某服务
journalctl -b                                           # 本次启动；-b -1 上次，-b -2 上上次
journalctl -u nginx --since "1 hour ago" -p err
journalctl -k -p warning                                # 内核日志，警告以上
journalctl -o json-pretty -u nginx | head -40
journalctl _PID=1234                                    # 按字段过滤：_COMM、_UID、SYSLOG_IDENTIFIER
journalctl --disk-usage && journalctl --vacuum-size=500M
```

默认日志在 `/run/log/journal`（内存，重启即失）；持久化要 `mkdir -p /var/log/journal`，`journald.conf` 设 `Storage=persistent` 后重启 journald。`SystemMaxUse=`、`RateLimitBurst=` 控制容量与限速（日志刷屏被丢就是这个原因）。

### 6.6 systemd-analyze 分析启动
```bash
systemd-analyze time                        # 固件/引导器/内核/用户态耗时
systemd-analyze blame                       # 按耗时排 service
systemd-analyze critical-chain nginx.service # 关键路径，真正决定启动时间
systemd-analyze plot > boot.svg             # 可视化时间线
systemd-analyze verify /etc/systemd/system/myapp.service   # 校验语法
```

`blame` 排第一的不一定是瓶颈：并行启动下只有 `critical-chain` 上的耗时才拖慢开机；常见优化是 `NetworkManager-wait-online` 太长、`plymouth` 图形启动、不必要的 `dnf-makecache.timer`。

## 7 网络
Linux 网络栈是「socket 接口 + 协议实现 + netfilter + 驱动」的组合；排查先分层定位，再深入某一层。

### 7.1 分层与 Linux 实现
| 层 | 协议/概念 | Linux 实现 |
| --- | --- | --- |
| 应用 | HTTP、DNS、SSH | 用户态进程，通过 fd 读写 socket |
| 传输 | TCP、UDP | `struct sock`、拥塞控制（cubic/bbr）、`tcp_*` 参数 |
| 网络 | IP、ICMP、路由 | 路由表（FIB）、netfilter 钩子、`sk_buff` |
| 链路 | Ethernet、ARP | 网卡驱动、NAPI 轮询、qdisc 队列、`ip neigh` |
| 物理 | 光/电信号 | 硬件、`ethtool` 看协商速率与错误计数 |

一个包从网卡到应用：DMA 收包 → 硬中断 → 软中断（NAPI）→ 协议栈 → netfilter → socket 接收队列 → 应用 `read`；`ip -s link` 的 `dropped`、`ethtool -S` 的 ring buffer 丢包、`ss -i` 的 `retrans` 分别对应这条链的不同位置。

### 7.2 socket 与 ss 状态机
一个 TCP 连接由四元组唯一确定：`(源 IP, 源端口, 目的 IP, 目的端口)`；`ss` 直接读内核 socket 表，比 `netstat` 快得多。

| 状态 | 含义 | 谁处于此状态 |
| --- | --- | --- |
| `LISTEN` | 监听，等握手 | 服务端 |
| `SYN-SENT` | 已发 SYN | 客户端（连不上时堆积） |
| `SYN-RECV` | 收到 SYN 并回 SYN-ACK | 服务端（SYN flood 时堆积） |
| `ESTABLISHED` | 连接已建立 | 双方 |
| `FIN-WAIT-1` / `FIN-WAIT-2` | 已发 FIN / 等对方 FIN | 主动关闭方 |
| `TIME-WAIT` | 等 2MSL（约 60s）后释放 | 主动关闭方 |
| `CLOSE-WAIT` | 收到对方 FIN，本端还没关 | **被动关闭方，应用没调 `close()`** |

**大量 `TIME-WAIT`** 出现在主动关闭方（如反向代理），是正常回收过程，量级过大说明短连接太多，应做连接复用或调 `net.ipv4.tcp_tw_reuse=1`（只对客户端出向连接生效）；**大量 `CLOSE-WAIT`** 一定是应用 bug——对端已关而本端没 `close()`，fd 会持续泄漏。

```bash
ss -tulnp                                  # 监听中的 TCP/UDP 与进程（需 root 看他人进程）
ss -tanp state established                 # 已建立连接
ss -tan state time-wait | wc -l            # TIME-WAIT 数量；ss -s 看汇总
ss -tni                                    # 含 rtt、cwnd、retrans 等 TCP 内部信息
```

### 7.3 DNS 解析
glibc 的顺序由 `/etc/nsswitch.conf` 的 `hosts:` 决定，通常 `files dns`——**先查 `/etc/hosts` 再问 DNS**，所以「改了解析不生效」先看 hosts 有没有硬编码。

```conf
# /etc/resolv.conf
nameserver 10.0.0.2
nameserver 223.5.5.5
search corp.example.com
options ndots:5 timeout:2 attempts:2
```

`ndots:5` 表示域名中点少于 5 个时先拼 `search` 域，容器里常因此产生额外查询甚至解析失败，可调小；`timeout`/`attempts` 决定故障时的总延迟。现代发行版上该文件常是软链，由 `systemd-resolved`（`/run/systemd/resolve/stub-resolv.conf`）或 NetworkManager 生成，**手改会被覆盖**。

```bash
resolvectl status                 # 每个网卡的 DNS、search 域
getent hosts example.com          # 走完整 nsswitch 链路，最接近应用行为
dig +short example.com            # A 记录
dig @8.8.8.8 example.com MX       # 指定服务器与记录类型
dig +trace example.com            # 从根逐级查，定位哪一级出错
```

常用记录：`A`/`AAAA`、`CNAME`、`MX`、`NS`、`TXT`、`PTR`；`NXDOMAIN` 是域名不存在，`SERVFAIL` 多为上游故障或 DNSSEC 校验失败，`TTL` 决定缓存时长。

### 7.4 路由
```bash
ip route                                    # 主路由表
ip route get 8.8.8.8                        # 内核实际选哪条路由与源地址
ip route add 10.20.0.0/16 via 192.168.1.1 dev eth0 metric 100
ip rule list                                # 策略路由（0 local、32766 main、32767 default）
```

路由选择是**最长前缀匹配**，前缀相同比 `metric`（小者优先）；`scope link` 表示直连、`via` 是下一跳、`src` 指定源地址。多出口用策略路由：`ip rule add from 10.0.0.0/24 table 100` 加该表默认路由，按源地址分流；转发要开 `net.ipv4.ip_forward=1`（写 `/etc/sysctl.d/` 持久化），NAT 由 nftables 的 `masquerade` 完成。

### 7.5 防火墙
**firewalld**（RHEL 系）是动态前端，核心是 zone：每个网卡/网段归属一个 zone，zone 内定义放行的服务与端口。

| zone | 默认行为 |
| --- | --- |
| `drop` / `block` | 丢弃 / 拒绝所有入站（后者回 ICMP 拒绝） |
| `public` | 默认 zone，只放行显式允许的服务 |
| `internal` / `work` / `home` | 逐级更宽松 |

```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --permanent --add-masquerade          # NAT 出口
firewall-cmd --permanent --add-rich-rule='rule family=ipv4 source address=10.0.0.5 port port=3306 protocol=tcp accept'
firewall-cmd --reload                              # 永久规则必须 reload 才生效
```

**nftables** 是新一代内核框架（替代 `iptables`），概念是 table → chain → rule，chain 挂在 netfilter 钩子（`prerouting`/`input`/`forward`/`output`/`postrouting`）并带优先级。

```bash
nft add table inet filter
nft add chain inet filter input '{ type filter hook input priority 0 ; policy drop ; }'
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input tcp dport 8080 accept
nft -f /etc/nftables.conf                  # 从文件加载，开机生效
```

Debian/Ubuntu 更常用 `ufw`（`ufw allow 22/tcp`、`ufw status verbose`），它也是 nftables/iptables 的前端；`iptables-nft` 与 `iptables-legacy` 混用会导致「规则加了不生效」，用 `iptables -V` 确认后端。改远程机器的防火墙前，先确认放行了 SSH。

### 7.6 tcpdump 抓包
```bash
tcpdump -i eth0 -nn -c 100                 # 抓 100 个包，不解析主机名/端口名
tcpdump -i eth0 -nn port 80 -A             # 按端口过滤，ASCII 显示内容
tcpdump -i eth0 -nn 'tcp[tcpflags] & tcp-syn != 0'   # 只抓 SYN
tcpdump -i eth0 -nn -s 0 -w /tmp/a.pcap    # 全量包存文件（-s 0 不截断）
```

过滤器是 BPF 语法，支持 `and`/`or`/`not` 与括号，如 `'(port 80 or port 443) and host 10.0.0.5'`；输出里 `[S]` 是 SYN、`[S.]` 是 SYN-ACK、`[.]` 是 ACK、`[P.]` 是 PSH-ACK、`[F.]` 是 FIN。抓包需 `CAP_NET_RAW`（root 或 `setcap`），长期抓用 `-C`/`-G` 轮转，或用 `tshark -i eth0 -Y http` 按协议过滤；生产注意限速限大小。

## 8 包管理与仓库
包管理器做四件事：拉元数据、解依赖、下载并校验签名、按文件清单安装并执行脚本；理解这四步，装不上、卸不干净、依赖冲突都能定位。

### 8.1 apt 仓库与依赖
```conf
# /etc/apt/sources.list（传统格式）
deb http://deb.debian.org/debian bookworm main contrib non-free

# /etc/apt/sources.list.d/vendor.sources（deb822 新格式，Ubuntu 24.04+ 默认）
Types: deb
URIs: https://repo.example.com/ubuntu
Suites: noble
Components: main
Signed-By: /usr/share/keyrings/vendor.gpg
```

- `apt update` 只刷新索引到 `/var/lib/apt/lists`，**不升级任何软件**（最常见的误解）；`apt upgrade` 才升级且不删包，`apt full-upgrade` 允许为解依赖增删包。
- 签名失败先查 keyring 与系统时间，`Signed-By` 缺失会报 `NO_PUBKEY`；版本锁定用 `apt-mark hold`，`/etc/apt/preferences.d/` 的 `Pin-Priority` 决定用哪个源。
- 依赖破损：`apt -f install`、`dpkg --configure -a`；`dpkg -i` 只装不解决依赖，报错后再 `apt -f install` 补。

### 8.2 apt 与 dnf 对照
| 操作 | Debian/Ubuntu（apt/dpkg） | RHEL/CentOS/Fedora（dnf，旧为 yum） |
| --- | --- | --- |
| 更新索引 | `apt update` | `dnf makecache` |
| 升级已装软件 | `apt upgrade` | `dnf upgrade` |
| 安装 / 卸载 | `apt install nginx` / `apt remove nginx` | `dnf install nginx` / `dnf remove nginx` |
| 彻底卸载含配置 | `apt purge nginx` | 无直接对应，手动删 `/etc` 残留 |
| 搜索 / 详情 | `apt search` / `apt show` | `dnf search` / `dnf info` |
| 已安装列表 | `dpkg -l` | `rpm -qa` |
| 文件属于哪个包 | `dpkg -S /usr/sbin/nginx` | `rpm -qf /usr/sbin/nginx` |
| 包装了哪些文件 | `dpkg -L nginx` | `rpm -ql nginx` |
| 历史与回滚 | `/var/log/apt/history.log` | `dnf history`、`dnf history undo N` |

### 8.3 dnf 仓库配置
```ini
# /etc/yum.repos.d/example.repo
[example]
name=Example Repo
baseurl=https://repo.example.com/el9/$basearch/
enabled=1
gpgcheck=1
gpgkey=https://repo.example.com/RPM-GPG-KEY-example
```

`baseurl` 也可换成 `metalink` 由镜像列表自动选源；`gpgcheck=1` 必须开，否则等于信任任意中间人。常用：`dnf repolist --all`、`dnf config-manager --add-repo URL`、`dnf --downloadonly install`、`dnf module list`（AppStream 多版本）、`dnf groupinstall "Development Tools"`；第三方包通常先装 EPEL。

### 8.4 依赖解析
依赖粒度是**能力**：ELF 的 `DT_NEEDED` 里的 soname（如 `libssl.so.3`）、包的 `Provides`、版本约束（`>= 1.2`）；apt 用自己的求解器，dnf 用 libsolv（SAT 求解），冲突时给出「不安装/降级/替换」选项。混装第三方源、`--nogpgcheck`、`rpm --nodeps` 是依赖地狱的主要来源，`dnf distro-sync` 可把系统拉回仓库版本。

### 8.5 源码编译与 ldconfig
```bash
./configure --prefix=/usr/local/nginx --with-http_ssl_module   # 检查依赖、生成 Makefile
make -j$(nproc)                                                # 并行编译
make install                                                   # 安装到 prefix（默认 /usr/local）
```

前提是工具链与开发库：Debian 装 `build-essential`，RHEL 装 `gcc`、`make`、`*-devel`；`--prefix` 决定安装路径，源码装的软件**不受包管理器管理**，升级卸载都要自己做，想留退路用 `make DESTDIR=/tmp/stage install` 或 `checkinstall` 生成包。

| 机制 | 说明 | 命令 |
| --- | --- | --- |
| `/etc/ld.so.conf` + `ld.so.conf.d/*.conf` | 声明额外库目录 | 加完执行 `ldconfig` |
| 缓存 `/etc/ld.so.cache` | 二进制索引，`ldconfig` 生成 | `ldconfig -p | grep xxx` |
| `LD_LIBRARY_PATH` | 环境变量，优先于缓存；**setuid 程序会忽略** | 只用于临时调试 |
| RPATH / RUNPATH | 编译期写进 ELF 的搜索路径 | `readelf -d app | grep -E 'RPATH|RUNPATH'` |

搜索顺序大致是 `DT_RPATH` → `LD_LIBRARY_PATH` → `DT_RUNPATH` → `/etc/ld.so.cache` → `/lib`、`/usr/lib`；`ldd app` 会**执行**目标程序的部分逻辑，不要对不可信二进制用。

## 9 性能分析
性能问题的通用套路：先确定**哪类资源**（CPU/内存/磁盘/网络），再定位**哪个进程线程**，最后定位**代码哪一行**。

### 9.1 load average 到底在算什么
`/proc/loadavg` 前三个数是 1/5/15 分钟指数滑动平均，统计的是**运行队列长度 + 不可中断睡眠（`D`）进程数**，不是 CPU 使用率。

- 单核 load=1 表示刚好跑满，4 核 load=4 才 100%，所以先除以核数（`nproc`）再判断。
- 因为含 `D` 状态，磁盘/NFS 卡住会让 load 飙升而 CPU 空闲——这是「负载高但 CPU 不高」的标准答案。
- 容器里 load 是**宿主机**的，不反映 cgroup 限额，容器内看到 load 高不代表自己被限流。

```bash
uptime; cat /proc/loadavg                        # 负载，后两字段是 running/total 与最后 PID
ps -eo stat,pid,wchan:24,cmd | awk '$1 ~ /^D/'   # 找 D 状态
```

### 9.2 CPU 指标
| 指标 | 含义 | 高了说明 |
| --- | --- | --- |
| `us` | 用户态 | 计算密集，看 `perf` 热点 |
| `sy` | 内核态 | 系统调用/上下文切换/网络栈太忙 |
| `wa` | 等 IO | 磁盘或网络存储慢 |
| `hi` / `si` | 硬/软中断 | 网卡小包多、中断未做亲和 |
| `st` | 被虚拟化偷走 | 宿主机超卖，找云厂商 |

```bash
mpstat -P ALL 1 5        # 每核明细，看单核打满/核间不均
pidstat -w 1 5           # 上下文切换：cswch/s 自愿、nvcswch/s 非自愿
top -H -p <pid>          # 线程级热点
```

上下文切换的**自愿**（等锁、等 IO）与**非自愿**（时间片用完被抢占）要分清：`cs` 远高于 `in` 且 `sy` 高，通常是锁竞争或线程过多。

### 9.3 内存指标
看趋势不看瞬时：`free -h -s 5` 观察 `available` 是否单调下降；`ps -eo pid,rss,cmd --sort=-rss` 找大户；`smaps_rollup` 的 `Pss` 看真实占用；`slabtop -s c` 看内核 slab 是否泄漏；`vmstat 1` 的 `si/so` 判断是否换页。Java 进程 RSS 含堆外与 JIT 代码，需配合 `jcmd VM.native_memory`。

### 9.4 IO 指标
```bash
iostat -x 1 5        # 扩展统计，1 秒一次共 5 次
iotop -oPa           # 按进程的实时 IO（-o 只显示有 IO 的）
```

| 列 | 含义 | 判读 |
| --- | --- | --- |
| `r/s` `w/s` | 每秒读/写次数（IOPS） | HDD 约 100~200，SATA SSD 数万 |
| `rkB/s` `wkB/s` | 吞吐 | 顺序大文件看这里 |
| `await` | 平均等待（ms，含排队） | 机械盘 < 20ms、SSD < 1ms 较健康 |
| `r_await` `w_await` | 分开的读/写等待 | 定位读多还是写多 |
| `aqu-sz`（旧 `avgqu-sz`） | 平均队列深度 | 持续 > 1 说明在排队 |
| `%util` | 忙碌时间占比 | 接近 100% 是瓶颈；**SSD/RAID 下可能失真** |

`%util` 是历史遗留指标，对现代 SSD 与多队列设备参考价值有限，优先看 `await` 与 `aqu-sz`；做基线用 `fio` 压测（`fio -name=rw -rw=randwrite -bs=4k -iodepth=32 -numjobs=4 -size=1G -runtime=60 -time_based -filename=/data/test`），拿真实设备数据对照。

### 9.5 跟踪与剖析工具怎么选
| 工具 | 原理 | 开销 | 适用 |
| --- | --- | --- | --- |
| `perf` | 硬件/软件事件采样 | 低 | CPU 热点、调用栈、火焰图、调度 |
| `strace` | 系统调用跟踪（ptrace） | 很高，可能慢 10 倍 | 卡在哪个系统调用、文件/网络失败原因 |
| `ltrace` | 库函数跟踪 | 高 | 定位调用了哪个库函数 |
| `bpftrace` / `bcc` | eBPF 动态追踪（kprobe/uprobe/tracepoint） | 低 | 延迟分布、按进程/文件/调用链统计 |
| `gdb` | 断点调试 | 停止进程 | 崩溃现场、死锁栈 |

```bash
perf top -p <pid>                            # 实时热点函数
perf record -F 99 -g -p <pid> -- sleep 30    # 采样 30s，-g 记录调用栈
strace -c -f -p <pid>                        # 按系统调用汇总耗时
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { @[comm] = count(); }'
```

`perf record -F 99 -g` 得到 `perf.data` 后接 FlameGraph 脚本（`stackcollapse-perf.pl` + `flamegraph.pl`）就是火焰图：横轴是栈占比，纵轴是调用深度，最宽的塔顶就是热点；`strace` 只适合短时定性，别在生产长挂。

## 10 容器基础
容器不是「轻量虚拟机」，而是**被隔离并限制资源的一组普通进程**：namespace 管「看得见什么」，cgroup 管「能用多少」，镜像只是打包好的根文件系统；宿主机 `ps` 能看到所有容器进程，这是理解容器的最佳视角。

### 10.1 namespace 的八种隔离
| namespace | 隔离内容 | `unshare` 参数 | 效果 |
| --- | --- | --- | --- |
| `mnt` | 挂载点与文件系统树 | `--mount` | 看不到宿主机挂载，可有独立根 |
| `pid` | 进程号空间 | `--pid --fork` | 容器内 PID 1 是应用 |
| `net` | 网络栈 | `--net` | 独立 IP、端口空间、iptables |
| `ipc` | System V IPC、POSIX 消息队列 | `--ipc` | 隔离共享内存/信号量 |
| `uts` | 主机名与域名 | `--uts` | 独立 hostname |
| `user` | UID/GID 映射 | `--user` | 容器 root 映射为宿主机普通用户 |
| `cgroup` | cgroup 视图 | `--cgroup` | 隐藏宿主机层级 |
| `time` | 时钟偏移（5.6+） | `--time` | 独立 boottime |

```bash
unshare --pid --fork --mount-proc --uts --net bash   # 手工造一个「容器」
lsns                                                  # 所有 namespace 与成员进程
nsenter -t <pid> -n -p ss -tulnp                      # 进入某进程的 net/pid ns 排查
```

### 10.2 cgroup v1 与 v2
| 对比项 | v1 | v2 |
| --- | --- | --- |
| 层级 | 每控制器一棵树，可任意组合 | 单棵统一树，控制器同层 |
| 挂载点 | `/sys/fs/cgroup/<controller>/` | `/sys/fs/cgroup/` + `cgroup.controllers` |
| 进程归属 | 一个进程可在不同控制器的不同组 | 一个进程只能在一个组 |
| 内存 | `memory.usage_in_bytes` | `memory.current`、`memory.stat`、`memory.pressure` |
| CPU | `cpu.cfs_quota_us` + `cpu.cfs_period_us` | `cpu.max`（"quota period"） |
| 权重 | `cpu.shares` | `cpu.weight`（1~10000） |
| IO | `blkio.throttle.*` | `io.max`（`rbps`/`wbps`/`riops`/`wiops`） |
| PSI 压力 | 无 | `cpu.pressure`、`memory.pressure`、`io.pressure` |

```bash
cat /sys/fs/cgroup/cgroup.controllers              # v2 可用控制器
echo "50000 100000" > /sys/fs/cgroup/demo/cpu.max      # 每 100ms 最多跑 50ms = 0.5 核
echo 536870912     > /sys/fs/cgroup/demo/memory.max    # 512 MiB 硬上限
cat /sys/fs/cgroup/demo/memory.events                  # oom / oom_kill 计数
```

`memory.high` 是软限（超过则限速回收），`memory.max` 是硬限（超过就 OOM）；`cpu.max` 是**上限不是保底**，份额保底用 `cpu.weight`。systemd 包成 `MemoryMax=`/`CPUQuota=`，Docker 包成 `--memory`/`--cpus`，K8s 包成 `resources.limits`——底层是同一套文件。

### 10.3 docker 常用命令
| 操作 | 命令 |
| --- | --- |
| 容器列表 | `docker ps -a`（`-a` 含已退出） |
| 运行 | `docker run -d --name web -p 8080:80 -v /data/html:/usr/share/nginx/html nginx` |
| 资源限制 | `docker run --cpus=1.5 --memory=512m --memory-swap=1g nginx` |
| 进入运行中容器 | `docker exec -it web bash` |
| 看日志 / 详情 | `docker logs -f --tail 100 web`、`docker inspect web` |
| 实时资源 | `docker stats`（`--no-stream` 取一次） |
| 构建 / 分层 | `docker build -t myapp:1.0 .`、`docker history myapp:1.0` |
| 清理 / 网络 / 卷 | `docker system df`、`docker system prune -a`、`docker network ls` |

`-p 8080:80` 是「宿主机端口:容器端口」；`-v /host:/container:ro` 挂数据卷并可只读；`--restart=always`（或 `unless-stopped`）控制重启策略，`--rm` 退出即删。容器内 PID 1 是应用本身，**默认不处理信号、不回收僵尸**，需要 `--init` 注入 tini 或应用自己 `waitpid`；`docker stop` 先 `SIGTERM`，默认 10 秒后 `SIGKILL`（`-t` 可调）。

### 10.4 镜像分层
镜像是一组只读层的叠加，每层是相对上一层的文件差异；`RUN`/`COPY`/`ADD` 各产生一层，容器启动时在只读层之上加一个**可写层**（overlay2 的 `upperdir`），写时复制——改文件先把文件从下层拷上来。

```dockerfile
FROM golang:1.22 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download                 # 依赖层单独放，改代码不失效
COPY . .
RUN CGO_ENABLED=0 go build -o /out/app ./cmd/app

FROM gcr.io/distroless/static
COPY --from=build /out/app /app     # 多阶段构建，最终镜像不含工具链
ENTRYPOINT ["/app"]
```

要点：变化少的层放前面（依赖先于源码），命中缓存才快；`.dockerignore` 排除 `.git`、`node_modules`；多阶段构建只把产物拷进最终镜像，体积从 GB 降到几十 MB；`RUN` 里 `apt install` 后要在同一层清缓存，否则删不掉上层体积。

### 10.5 容器与虚拟机
| 对比项 | 容器 | 虚拟机 |
| --- | --- | --- |
| 隔离级别 | 进程级，**共享宿主机内核** | 硬件级，各自独立内核 |
| 启动速度 | 毫秒到秒级 | 数十秒起 |
| 资源开销 | 几乎无额外开销，密度高 | 每台要预留内存与 CPU |
| 隔离强度 | 较弱，内核漏洞可能逃逸 | 较强，需虚拟化层漏洞 |
| 典型技术 | Docker、containerd、Kubernetes | KVM、VMware、Xen |

「共享内核」带来两个后果：容器内不能加载内核模块、多数 `sysctl` 只读；内核版本由宿主机决定，宿主机的内核漏洞就是所有容器的漏洞。

### 10.6 docker stats 与容器排障
```bash
docker stats --no-stream
# CONTAINER   CPU %   MEM USAGE / LIMIT   MEM %   NET I/O       BLOCK I/O   PIDS
# web         0.35%   48.2MiB / 512MiB    9.41%   1.2MB / 3KB   0B / 0B     12
```

`CPU %` 是相对**单核**的占比（200% 表示两核跑满），`MEM USAGE` 来自 cgroup 且已扣除可回收的 page cache，`PIDS` 对应 `pids.max`。容器异常排查顺序：`docker inspect -f '{{.State.ExitCode}} {{.State.OOMKilled}}'` → 137 多为 `SIGKILL`（含 OOM）、143 是 `SIGTERM` → `dmesg` 找 cgroup OOM → `docker logs` 看应用是否自己 `exit`；进不去容器用 `nsenter -t $(docker inspect -f '{{.State.Pid}}' web) -n -m -p bash`。

## 11 故障排查方法论
排查的元原则比命令更重要：

1. **先止损再根因**：重启/摘流量/扩容先恢复业务，同时保留现场（`sar`、`dmesg`、`journalctl`、线程栈、`/proc` 快照）。
2. **界定范围**：单机还是全集群？什么时候开始？对着监控时间线找变更点（发布、配置、扩缩容、证书到期）。
3. **一次只改一个变量**，改完立刻验证；用 `pidstat`/`iostat`/`ss` 的绝对值对照基线，别信 `top` 的直觉。

### 11.1 CPU 线
1. `uptime` 看 load 与核数比值，判断是 CPU 型还是 IO 型。
2. `top` 按 `P` 排序，确认单进程打满还是整体高；`1` 看是否单核偏载。
3. `top -H -p <pid>` 或 `pidstat -t -p <pid> 1` 找热点线程，线程 ID 转 16 进制。
4. 用户态热点：`perf top -p <pid>` / `perf record -F 99 -g` 出火焰图；Java 用 `jstack` 对 nid 查栈。
5. 内核态高（`sy`）：`vmstat 1` 看 `cs`/`in`，`strace -c -p` 找高频系统调用，`mpstat -P ALL` 看中断是否集中。

### 11.2 内存线
1. `free -h` 看 `available` 趋势，`vmstat 1` 看 `si/so` 是否非 0。
2. `ps -eo pid,rss,cmd --sort=-rss | head` 找大户，注意 RSS 重复计共享页。
3. `/proc/<pid>/smaps_rollup` 看 `Pss`/`Anonymous`/`Swap`，判断是堆、映射还是换出。
4. `dmesg -T | grep -i oom` 确认是否已被 OOM 杀过，看被杀进程的 `anon-rss`。
5. 持续上涨：`pmap -x` 看段增长、`slabtop` 排内核泄漏、应用侧 heap dump / `valgrind` / ASan。

### 11.3 磁盘线
1. `df -h` 找满的分区，`df -i` 排 inode 耗尽。
2. `du -h --max-depth=1 <dir> | sort -h` 逐层下钻，`find /path -size +1G` 抓大文件。
3. 空间没释放：`lsof +L1` 找已删除仍被占用的文件，重启进程或 `: > /proc/<pid>/fd/N` 截断。
4. IO 慢：`iostat -x 1` 看 `await`/`aqu-sz`/`%util`，`iotop -oPa` 或 `pidstat -d` 找进程。
5. 判断是否换页抖动（`vmstat` 的 `si/so`）、日志刷盘或备份任务，必要时 `ionice` 降级。

### 11.4 网络线
1. `ip -br a` / `ip route`：网卡 UP、地址、默认路由是否正常。
2. `ping 网关` → `ping 公网 IP` → `dig`：分段确认是二层、三层还是 DNS。
3. `ss -tulnp`：服务是否监听、绑的是 `0.0.0.0` 还是 `127.0.0.1`、端口对不对。
4. `curl -v --max-time 5` 看是连接超时、TLS 失败还是 HTTP 5xx；`ss -s` 看连接数是否打满。
5. `tcpdump -i any -nn port <port>` 看包到没到、有没有回包；`ss -i` 看 `retrans`/`rtt` 判断链路质量。

### 11.5 进程线
1. `ps -eo stat,pid,ppid,cmd | grep -E '^[ZD]'`：僵尸与 D 状态先摘出来。
2. 进程莫名消失：`dmesg` 查 OOM、`journalctl -u` 查服务退出、`/var/log/messages` 查段错误。
3. 杀不掉：确认是否 `D` 状态、是否僵尸、是否被父进程或 systemd 反复拉起（`systemctl status` 看 `Restart`）。
4. 句柄/端口泄漏：`lsof -p <pid> | wc -l`、`ls /proc/<pid>/fd | wc -l`、`cat /proc/<pid>/limits`。
5. 起不来：`strace -f -o /tmp/trace ./app` 看第一个失败的系统调用；`ldd` 查动态库缺失；`journalctl -u` 看退出码。

## 12 延伸
本篇讲原理与系统管理，命令速查、专项排查与面试自测拆在另外三篇：

| 文档 | 内容 | 什么时候看 |
| --- | --- | --- |
| [Linux 常用命令](Linux常用命令.md) | 文件、文本、查找、打包、用户、Shell、cron 的完整命令表 | 需要「这个命令怎么写」时 |
| [Linux 性能排查](Linux性能排查.md) | top/vmstat/iostat/sar/perf/strace 逐项拆解与实战案例 | 线上出问题、按工具深入时 |
| [Linux 面试题](Linux面试题.md) | 高频问答与追问链，覆盖本篇全部章节 | 面试前自测、查漏补缺 |

配套阅读：[操作系统](../操作系统/001.计算机系统概述.md)（进程/内存/文件系统的理论侧）、[计算机网络](../计算机网络/计算机网络.md)（TCP/IP 与握手挥手）、[C 语言基础](C基础.md)（进程内存布局与系统调用）。
