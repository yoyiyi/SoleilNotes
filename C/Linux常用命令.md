# Linux 常用命令速查

按用途分类的命令手册，与《Linux 基础》互补：那篇讲原理与面试，这篇解决「命令怎么写」。默认 bash + GNU coreutils / util-linux / iproute2 环境，Debian/Ubuntu 与 RHEL 系通用，个别发行版差异会标注。

约定：`$` 是普通用户，`#` 是 root；示例中的 `file`、`dir`、`8080` 是占位符，照抄前先替换；选项随版本演进，拿不准就 `man 命令`。

15 节：[1 命令基础](#1-命令基础) · [2 文件与目录](#2-文件与目录) · [3 查看与编辑](#3-查看与编辑) · [4 文本处理](#4-文本处理) · [5 查找](#5-查找) · [6 压缩与打包](#6-压缩与打包) · [7 权限与属主](#7-权限与属主) · [8 进程](#8-进程) · [9 磁盘](#9-磁盘) · [10 网络](#10-网络) · [11 系统信息](#11-系统信息) · [12 服务与日志](#12-服务与日志) · [13 包管理](#13-包管理) · [14 高频组合拳](#14-高频组合拳) · [15 危险命令清单](#15-危险命令清单)

## 1 命令基础

命令是「可执行文件 + 参数」，shell 先做通配符展开、变量替换、去引号，再交给程序；很多「命令没生效」的问题其实卡在 shell 这一层。

### 1.1 命令格式与求助
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `命令 [选项] [参数]` | 通用格式，短选项可合并 | `-l -h` 合并为 `-lh`；长选项用 `=` 赋值 | `tar -czvf log.tar.gz /var/log` |
| `man` | 查手册页，最权威 | `-k` 搜关键词；`-f` 简介；章节 `1` 命令、`5` 配置文件、`8` 管理命令 | `man 5 passwd` |
| `命令 --help` | 选项速查，比 man 短 | 多数 GNU 命令支持；`--version` 看版本 | `grep --help \| head -20` |
| `type` | 判断别名、内建还是外部程序 | `-a` 列出全部同名项 | `type -a ls` |
| `command -v` | 打印命令路径，脚本里比 `which` 可靠 | 无输出且退出码 1 即不存在 | `command -v nginx` |
| `whatis` / `apropos` | 一句话说明 / 按描述搜命令 | 索引由 `mandb` 维护，新系统先 `sudo mandb` | `apropos "copy files"` |

### 1.2 通配符（glob）
| 写法 | 匹配 | 示例 | 注意 |
| --- | --- | --- | --- |
| `*` | 任意长度字符，不含 `/` | `ls *.log` | `rm *` 前先 `echo *` 看范围 |
| `?` | 恰好一个字符 | `ls file?.txt` | 匹配 `file1.txt`，不匹配 `file10.txt` |
| `[abc]` | 集合内任一字符 | `ls [ab]*.md` | 支持 `[0-9]`、`[a-z]` |
| `[!abc]` | 不在集合内 | `ls [!a]*` | bash 也认 `[^abc]`，POSIX 写 `!` |
| `{a,b}` | 花括号展开成多个词 | `cp app.conf{,.bak}` | 不是通配符，`sh` 不支持；目标不存在也照传 |
| `{1..5}` | 序列展开 | `touch log{01..05}.txt` | 支持 `{a..e}`、`{1..10..2}` |
| `\*` / 引号 | 阻止展开，原样传给命令 | `grep '\*' file` | 正则里的 `*` 必须防 shell 展开 |

`mkdir -p /data/{log,cache,tmp}` 可一次建三个目录；通配符由 shell 展开，`ls *.log` 里没有 `ls` 的事。

### 1.3 补全与快捷键
| 按键 | 作用 | 示例 / 说明 |
| --- | --- | --- |
| `Tab` | 补全命令、路径、选项 | `cd /usr/lo` + Tab → `/usr/local/` |
| `Tab` `Tab` | 列出全部候选 | 候选多时会问是否全部显示 |
| `Ctrl+R` | 反向搜索历史，再按继续往前 | 输入 `ssh` 后连按找旧命令 |
| `Ctrl+A` / `Ctrl+E` | 光标跳到行首 / 行尾 | 改长命令开头很省事 |
| `Ctrl+U` / `Ctrl+K` | 删到行首 / 删到行尾 | 清掉半条命令重写 |
| `Ctrl+C` | 中断前台进程（SIGINT） | 跑飞的命令用这个 |
| `Ctrl+Z` | 挂起到后台并暂停 | 随后 `bg` 继续或 `fg` 调回 |
| `Alt+.` | 插入上一条命令的最后一个参数 | 连按可取更早命令的参数 |

### 1.4 历史命令
| 写法 | 作用 | 示例 |
| --- | --- | --- |
| `history` | 列出历史（带编号） | `history 20` 只看最近 20 条 |
| `!!` | 重复上一条命令 | `sudo !!` 用 root 重跑上一条 |
| `!$` | 上一条命令的最后一个参数 | `mkdir /data/app` 后 `cd !$` |
| `!123` / `!ssh` | 执行指定编号 / 最近一条以 ssh 开头的命令 | `!ssh` |
| `!?str?` | 执行最近一条包含 str 的命令 | `!?nginx?` |
| `^old^new^` | 把上一条命令里的 old 换成 new 再执行 | `^8080^9090^` |
| `history -w` / `-c` | 立即写入文件 / 清空内存历史 | `history -w`，落盘到 `~/.bash_history` |

`export HISTTIMEFORMAT='%F %T '` 让 `history` 带时间；`HISTCONTROL=ignorespace` 时命令前加空格不进历史，但密码仍可能被 `ps` 抓到。

### 1.5 别名与配置生效
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `alias` | 查看 / 定义别名 | 只在当前 shell 生效 | `alias ll='ls -alh'` |
| `unalias` | 删除别名 | `-a` 全部删除 | `unalias ll` |
| `alias ..='cd ..'` | 高频别名 | 还有 `alias ...='cd ../..'` | `alias grep='grep --color=auto'` |
| `source` / `.` | 重载配置让别名立即生效 | 交互式非登录 shell 读 `~/.bashrc` | `source ~/.bashrc` |
| `\ls` / `command ls` | 绕过别名 | 临时不用别名 | `\rm -i file` |
| `type ls` | 确认是否被别名覆盖 | 输出 `ls is aliased to ...` | `type -a rm` |

持久化写 `~/.bashrc`（当前用户）或 `/etc/profile.d/*.sh`（全局）。脚本默认不加载别名，别在脚本里依赖它。

### 1.6 引号、变量与命令替换
| 写法 | 含义 | 示例 |
| --- | --- | --- |
| `'...'` | 单引号内全部字面，不展开 | `echo '$HOME'` → `$HOME` |
| `"..."` | 双引号内展开变量与 `$()`，保留空格 | `echo "hi $USER"` |
| `$(命令)` | 命令替换，可嵌套，推荐写法 | `cd $(dirname $(readlink -f app))` |
| `$(( ))` / `;` `&&` `\|\|` | 算术展开 / 顺序、成功才、失败才执行 | `make && make install` |

`"$var"` 加引号几乎总是对的：不加引号时变量里的空格会被拆成多个参数，是脚本最常见的 bug。

## 2 文件与目录

### 2.1 浏览目录
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `ls` | 列目录 | `-l` 详情、`-a` 含隐藏、`-h` 人类可读 | `ls -lh` |
| `ls -l` | 权限、链接数、属主、属组、大小、时间、名字 | 首位 `-` 文件、`d` 目录、`l` 链接 | `ls -l /etc/passwd` |
| `ls -a` | 含 `.` 开头的隐藏项 | `-A` 不含 `.` 与 `..` | `ls -la /root` |
| `ls -h` | 大小显示 K/M/G | 必须配合 `-l` 或 `-s` | `ls -lhS` |
| `ls -t` | 按修改时间倒序 | `-r` 反序，`-tr` 最旧在前 | `ls -lt \| head` |
| `ls -S` | 按大小倒序 | 常配 `-lh` 看谁最占地方 | `ls -lhS \| head` |
| `ls -R` | 递归列出子目录 | 目录大时配 `less` | `ls -R /etc \| less` |

### 2.2 切换目录与路径处理
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `cd` | 切换目录 | 无参数回家目录；`-` 回上一个 | `cd /var/log`、`cd -` |
| `pwd` | 显示当前目录 | `-P` 解析软链接后的物理路径 | `pwd -P` |
| `realpath` | 绝对路径，解析 `..` 与链接 | `--relative-to=.` 输出相对路径 | `realpath ./a/../b` |
| `basename` | 取路径最后一段 | 第二个参数可去掉后缀 | `basename /data/app.tar.gz .tar.gz` |
| `dirname` | 取路径的目录部分 | 常与 `cd $(dirname $0)` 连用 | `dirname /data/app/run.sh` |

### 2.3 创建与删除
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `mkdir` | 建目录 | `-p` 递归创建、已存在不报错；`-m` 直接给权限 | `mkdir -p /data/app/{log,conf}` |
| `rmdir` | 删空目录 | `-p` 连同空父目录一起删 | `rmdir /data/empty` |
| `rm` | 删文件 | `-i` 逐个确认、`-f` 忽略不存在、`-r` 递归 | `rm -i old.log` |
| `rm -rf` | 递归强制删除，**不进回收站、无法撤销** | `--` 分隔以 `-` 开头的文件名 | `rm -rf -- ./cache` |

> **风险提示**：`rm -rf` 没有回收站也没有确认。执行前用 `pwd` + `ls` 确认位置，变量路径写 `rm -rf -- "${dir:?}"`（变量为空直接报错退出），详见 [15 危险命令清单](#15-危险命令清单)。

### 2.4 复制、移动与链接
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `cp` | 复制文件 | `-i` 覆盖前询问、`-n` 不覆盖、`-u` 只复制更新的 | `cp -i app.conf app.conf.bak` |
| `cp -r` | 递归复制目录 | 目标目录不存在则创建 | `cp -r conf/ /backup/conf/` |
| `cp -p` | 保留权限、属主、时间戳 | 备份配置常用 | `cp -p nginx.conf nginx.conf.$(date +%F)` |
| `cp -a` | 归档复制，等于 `-dR --preserve=all` | 迁目录、保留软链接与 ACL | `cp -a /data/app /backup/` |
| `mv` | 移动或重命名 | `-i` 覆盖前问、`-n` 不覆盖 | `mv -n old.txt new.txt` |
| `mv -t` | 目标目录前置，配合 `xargs` 批量移动 | 避免最后一个参数是目录 | `find . -name '*.log' -print0 \| xargs -0 mv -t /tmp/logs` |
| `ln -s` | 建软链接 | `-f` 覆盖、`-n` 不进入目录链接、`-r` 相对链接 | `ln -sfn /opt/app/releases/v2 /opt/app/current` |
| `ln` | 建硬链接，同一 inode 的另一个名字 | 不能跨文件系统、一般不能链目录 | `ln data.db data.db.bak` |

> 软链接的相对路径按「链接所在目录」解析，用 `ln -sr` 生成相对链接更抗迁移；删软链接用 `rm link`，写成 `rm link/` 会删目标目录内容。

### 2.5 元数据与文件类型
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `touch` | 建空文件或更新时间戳 | `-c` 不存在则不建、`-t` 指定时间 | `touch -t 202610240900 app.log` |
| `stat` | 看 inode、大小、三种时间 | `-c` 自定义格式：`%n` 名、`%s` 字节、`%i` inode、`%a` 权限 | `stat -c '%n %s %y %U:%G' app.log` |
| `file` | 按魔数判断真实类型，不看后缀 | `-i` 输出 MIME、`-b` 只输出结果 | `file -i backup.tar.gz` |
| `tree` | 树形展示目录 | `-L` 层数、`-d` 只看目录、`-I` 排除 | `tree -L 2 -d -I 'node_modules\|.git'` |

## 3 查看与编辑

### 3.1 cat / tac / nl
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `cat` | 输出内容、拼接文件 | `-n` 所有行编号、`-b` 非空行编号、`-A` 显示 `$` 与制表符、`-s` 压缩空行 | `cat -n app.conf` |
| `cat >` | heredoc 直接写文件 | 引号包裹 `EOF` 阻止变量展开 | `cat > /tmp/a.txt <<'EOF'` |
| `tac` | 按行逆序输出 | 查最新日志在前的文件 | `tac app.log \| head` |
| `nl` | 加行号输出 | `-ba` 所有行、`-w` 宽度、`-s` 分隔符 | `nl -ba -w4 -s': ' app.c` |

```bash
cat header.html body.html > page.html
cat > /tmp/hosts.bak <<'EOF'
127.0.0.1 localhost
EOF
```

### 3.2 more 与 less
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `more` | 最基础分页，只能往下翻 | 空格翻页、`q` 退出 | `more /etc/services` |
| `less` | 分页查看，可前后翻、搜索，首选 | `-N` 行号、`-S` 不折行、`+F` 进入后跟 tail | `less -N /var/log/syslog` |
| `/word`、`n` | less 内向下搜索、下一个匹配 | `?word` 向上、`N` 反向、`&word` 只显示匹配行 | `less app.log` 后输 `/ERROR` |
| `G` / `g` | 跳到文件尾 / 文件头 | `q` 退出、`F` 进入跟踪模式 | `less app.log` 后按 `G` |

### 3.3 head 与 tail
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `head` | 看开头，默认 10 行 | `-n 20` 前 20 行、`-c 100` 前 100 字节 | `head -n 5 /etc/passwd` |
| `tail` | 看结尾，默认 10 行 | `-n 100` 最后 100 行、`-n +100` 从第 100 行到结尾 | `tail -n 50 app.log` |
| `tail -f` | 跟踪追加（按 inode，轮转后失效） | 常配 `grep` | `tail -f app.log` |
| `tail -F` | 跟踪文件名，轮转后自动重开 | 生产看日志首选 | `tail -F /var/log/nginx/error.log` |

```bash
tail -F app.log | grep --line-buffered -iE 'error|exception'   # 实时筛错误
head -c 512 disk.img | xxd                                     # 看文件头魔数
```

### 3.4 vim 最小可用操作
| 操作 | 按键 | 说明 |
| --- | --- | --- |
| 进入编辑 | `i` / `a` / `o` / `O` | 光标前插入 / 后插入 / 下方新行 / 上方新行 |
| 回到普通模式 | `Esc` | 不确定在哪就按两下 |
| 保存 / 退出 | `:w` / `:q` | `:w!` 强制写（需权限）、`:q!` 放弃修改退出 |
| 保存并退出 | `:wq` / `:x` / `ZZ` | `:x` 未改动时不写盘 |
| 撤销 / 重做 | `u` / `Ctrl+r` | 撤销一整次插入或命令 |
| 删行 / 复制行 / 粘贴 | `dd` / `yy` / `p` | `3dd` 删 3 行，`P` 粘到光标前 |
| 行首 / 行尾 | `0` / `$` | `^` 到第一个非空字符 |
| 文件头 / 尾 | `gg` / `G` | `:100` 跳到第 100 行 |
| 向下 / 向上搜索 | `/word` / `?word` | `n` 下一个，`N` 上一个 |
| 全局替换 | `:%s/old/new/g` | 加 `c` 逐个确认：`:%s/old/new/gc` |
| 删除匹配行 / 行号 | `:g/pat/d` / `:set nu` | `:v/pat/d` 删不匹配的；`:set nonu` 关闭行号 |

> 只用三件事也能干活：`i` 进入编辑 → `Esc` → `:wq` 保存退出；改错了 `u` 撤销，不要了 `:q!`。只读查看用 `vim -R file`。

## 4 文本处理

### 4.1 grep 过滤行
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `grep` | 按行匹配文本 | `-i` 忽略大小写、`-v` 反选、`-n` 行号、`-c` 计数 | `grep -in error app.log` |
| `grep -r` | 递归搜目录 | `--include` 限定后缀、`-l` 只列文件名 | `grep -rn --include='*.conf' timeout /etc` |
| `grep -E` | 扩展正则，等同 `egrep` | `-o` 只输出匹配部分、`-w` 整词匹配 | `grep -Eo '[0-9]{1,3}(\.[0-9]{1,3}){3}' app.log` |
| `grep -A/-B/-C` | 匹配行后 / 前 / 前后若干行 | `-A3`、`-B2`、`-C2` | `grep -C2 -n 'Traceback' app.log` |
| `grep -F` | 按字面串匹配，不当正则 | 搜含 `.` `[` 的串更安全 | `grep -F '1.2.3' versions.txt` |

### 4.2 sed 流式编辑
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `sed 's/old/new/'` | 每行替换第一个 | 加 `g` 替换全部 | `sed 's/http:/https:/' urls.txt` |
| `sed -i` | 直接改文件 | `-i.bak` 先备份再改 | `sed -i.bak 's/8080/9090/g' app.conf` |
| `sed -n '2,5p'` | 只打印第 2~5 行 | `-n` 抑制默认输出 | `sed -n '1,10p' /etc/passwd` |
| `sed '5d'` / `2,4d` | 删除指定行 | 原文件不变，只影响输出 | `sed '1d' data.csv` |
| `sed '/pattern/d'` | 删除匹配行 | 常用来删注释与空行 | `sed '/^#/d;/^$/d' app.conf` |
| `sed -E 's/(a+)(b+)/\2\1/'` | 扩展正则与反向引用 | `&` 代表整个匹配 | `sed -E 's/[0-9]+/N&/g' f` |

```bash
sed -i '/^$/d' hosts.txt                              # 删空行
sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config   # 改配置项
```

### 4.3 awk 按列处理
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `awk '{print $1}'` | 按空白分列输出第 1 列 | `$0` 整行、`$NF` 最后一列 | `awk '{print $1, $NF}' app.log` |
| `awk -F:` | 指定分隔符 | `-F'\t'` 制表符、`-F'\|'` 竖线 | `awk -F: '{print $1}' /etc/passwd` |
| `awk 'NR==5'` | 按行号筛选 | `NR` 行号、`NF` 每行列数 | `awk 'NR>=2 && NR<=5' data.txt` |
| `awk '$3>100'` | 按列值条件过滤 | 支持 `==`、`!=`、`~` 正则 | `awk -F: '$3>=1000 {print $1}' /etc/passwd` |
| `awk '{s+=$1} END{print s}'` | 求和，`END` 在处理完所有行后执行 | 百分比用 `printf "%.2f"` | `awk '{s+=$5} END{printf "%.2f\n", s}' sales.txt` |
| `awk '!seen[$0]++'` | 去重且保持原顺序 | 比 `sort \| uniq` 保序 | `awk '!seen[$0]++' urls.txt` |

### 4.4 cut / sort / uniq / wc
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `cut -d: -f1,3` | 按分隔符取列 | `-f2-` 第 2 列到末尾 | `cut -d: -f1,3 /etc/passwd` |
| `sort` | 排序，默认字典序 | `-n` 数值、`-r` 逆序、`-u` 去重、`-h` 按大小 | `sort -n sizes.txt` |
| `sort -k2` | 按第 2 列排序 | `-t:` 指定分隔符、`-k2,2nr` 第 2 列数值逆序 | `sort -t: -k3,3n /etc/passwd` |
| `uniq -c` | 相邻去重并计数，**必须先 sort** | `-d` 只看重复、`-u` 只看唯一 | `sort ips.txt \| uniq -c` |
| `wc -l` | 统计行数 | `-w` 词数、`-c` 字节 | `wc -l app.log` |
| `wc -l < file` | 只要数字，不带文件名 | 脚本取值常用 | `n=$(wc -l < app.log)` |

### 4.5 tr 与 xargs
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `tr 'a-z' 'A-Z'` | 字符替换（只读 stdin） | 不能直接跟文件名 | `tr 'a-z' 'A-Z' < names.txt` |
| `tr -d '\r'` | 删除字符，去 Windows 换行 | 修 `bad interpreter: ^M` | `tr -d '\r' < win.sh > unix.sh` |
| `xargs` | 把 stdin 变成后续命令的参数 | `-n1` 每次一个、`-I{}` 占位、`-P4` 并发 | `cat list.txt \| xargs -n1 rm -v` |
| `xargs -0` | 以 NUL 分隔，配合 `find -print0` | 文件名含空格必备 | `find . -name '*.log' -print0 \| xargs -0 gzip` |
| `xargs -r` | 输入为空时不执行命令 | 防 `rm` 无参数报错 | `grep -l old *.conf \| xargs -r sed -i 's/old/new/g'` |

### 4.6 组合示例

```bash
# 访问日志 Top10 IP：取列 → 排序 → 相邻去重计数 → 数值倒序
awk '{print $1}' access.log | sort | uniq -c | sort -nr | head -10

# 状态码分布、按小时 PV（时间字段形如 [24/Oct/2026:10:31:02）
awk '{print $9}' access.log | sort | uniq -c | sort -nr
awk -F'[][]' '{split($2,t,":"); print t[1]":"t[2]}' access.log | sort | uniq -c

# 某接口平均耗时（第 10 列，单位 ms）
awk '$7=="/api/user" {s+=$10; n++} END{printf "%.1f ms (%d 次)\n", s/n, n}' access.log

# 统计代码行数；去重保序
find . -name '*.c' -print0 | xargs -0 wc -l | tail -1
awk '!seen[$0]++' urls.txt > urls.uniq.txt
```

## 5 查找

### 5.1 find
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `find . -name` | 按文件名（区分大小写） | `-iname` 忽略大小写；通配符加引号 | `find /var/log -name '*.log'` |
| `find . -type` | 按类型：`f` 文件、`d` 目录、`l` 链接 | `-o` 表示或 | `find . -type d -name cache` |
| `find . -size +100M` | 按大小，`+` 大于、`-` 小于 | `c` 字节、`k`、`M`、`G` | `find / -xdev -type f -size +500M` |
| `find . -mtime -7` | 按修改天数，`-7` 七天内 | `-mmin -60` 按分钟、`+30` 三十天前 | `find /var/log -name '*.log' -mtime +7` |
| `find . -newermt` | 按时间点筛选 | `-newer ref.txt` 参照文件 | `find . -type f -newermt '2026-10-01'` |
| `find . -perm -4000` | 按权限筛选，查 SUID | `-user alice` 按属主 | `find / -perm -4000 -type f 2>/dev/null` |
| `find . -exec ... {} +` | 对结果执行命令，`+` 批量传参 | `\;` 逐个执行，慢但兼容 | `find . -name '*.sh' -exec chmod +x {} +` |
| `find . -print0` | NUL 分隔输出，防空格文件名 | 配 `xargs -0` | `find . -name '*.log' -print0 \| xargs -0 gzip` |

```bash
find . -path ./.git -prune -o -name '*.py' -print     # 跳过 .git
find /data -type f -name '*.tmp' -mtime +7 -print      # 先预览再删
find . -type f -mmin -60 -printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort -r | head
```

### 5.2 locate / which / whereis
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `locate` | 查预建数据库，极快但可能过期 | `-i` 忽略大小写、`-c` 只计数、`-r` 正则 | `locate -i nginx.conf` |
| `which` | 在 `PATH` 里找可执行文件 | `-a` 列出全部同名 | `which -a python3` |
| `whereis` | 找二进制、源码、man 页 | `-b` 只找二进制、`-m` 只找手册 | `whereis nginx` |
| `command -v` | 脚本里判断命令是否存在 | 不存在返回非 0 | `command -v docker >/dev/null \|\| echo 未安装` |

### 5.3 find 与 grep -r 怎么选
| 需求 | 用哪个 | 示例 |
| --- | --- | --- |
| 按名字、大小、时间、权限找文件 | `find` | `find . -name '*.conf' -mtime -1` |
| 在文件内容里搜字符串 | `grep -r` | `grep -rn 'timeout' ./conf/` |
| 先筛文件再搜内容 | `find` + `xargs grep` | `find . -name '*.py' -print0 \| xargs -0 grep -n 'TODO'` |
| 限定后缀、排除目录 | `grep -r --include/--exclude-dir` | `grep -rn --include='*.go' --exclude-dir=vendor 'panic' .` |

内容搜索量大时用 `rg`（ripgrep）：默认递归、尊重 `.gitignore`，`rg -n 'TODO'`；没装就用上面的 `grep -r`。

## 6 压缩与打包

### 6.1 tar
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `tar -czvf` | 打包并 gzip 压缩，显示过程 | `c` 创建、`z` gzip、`v` 详细、`f` 文件名 | `tar -czvf etc-$(date +%F).tar.gz /etc` |
| `tar -xzvf` | 解压 gzip 包 | `-C` 指定解压目录 | `tar -xzvf etc.tar.gz -C /tmp` |
| `tar -tzvf` | 只列内容不解压 | 解压前先看结构，防 tar 炸弹 | `tar -tzvf app.tar.gz \| head -20` |
| `tar -cjf` / `-cJf` | bzip2 / xz 压缩 | xz 压缩比最高、最慢 | `tar -cJf src.tar.xz src/` |
| `tar --exclude` | 排除文件或目录，可写多次 | 模式相对打包根 | `tar -czf app.tar.gz --exclude='*.log' --exclude=node_modules app/` |
| `tar --strip-components=1` | 解压时去掉一层目录 | 包内是 `app-1.0/...` 时很有用 | `tar -xzf app.tar.gz --strip-components=1 -C /opt/app` |
| `tar -rf` / `-uvf` | 向未压缩包追加 / 更新文件 | 压缩包不能直接追加 | `tar -rf backup.tar new.conf` |

### 6.2 gzip / xz / zip
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `gzip` | 压缩单文件，**默认删除原文件** | `-k` 保留原文件、`-9` 最高压缩 | `gzip -k9 app.log` |
| `gunzip` / `zcat` | 解压 / 不解压直接看 | `zgrep -i error app.log.gz` 直接搜 | `zcat app.log.1.gz \| tail -50` |
| `xz` | 压缩比高、耗 CPU，常见于镜像与源码包 | `-9` 最高、`-T0` 用满核、`-k` 保留、`-d` 解压 | `xz -9 -T0 -k bigfile.img` |
| `xzcat` / `unxz` | 直接看 / 解压 `.xz` | `unxz` 等同 `xz -d` | `xzcat src.tar.xz \| tar -x` |
| `zip -r` | 递归压缩目录 | `-q` 安静、`-9` 最高压缩 | `zip -rq site.zip site/` |
| `unzip -l` / `-d` | 列出内容 / 解压到指定目录 | `-o` 覆盖、`-n` 不覆盖 | `unzip -q site.zip -d /var/www` |
| `unzip -O cp936` | 解决 Windows 中文文件名乱码 | 新版 unzip 支持，旧版用 `7z x` | `unzip -O cp936 data.zip` |

## 7 权限与属主

### 7.1 权限位与 chmod
`ls -l` 的 `-rwxr-xr--`：首位是类型，后 9 位按「属主 / 属组 / 其他人」各 3 位，`r=4`、`w=2`、`x=1`。

| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `chmod 755` | 数字法设权限 | 755=`rwxr-xr-x`、644=`rw-r--r--`、600=`rw-------` | `chmod 755 run.sh` |
| `chmod u+x` | 符号法：`u/g/o/a` + `+/-/=` + `rwx` | 逗号分隔多项 | `chmod u+x,g-w,o=r app.sh` |
| `chmod -R` | 递归修改 | 目录要有 `x` 才能进入 | `chmod -R u=rwX,g=rX,o= /data` |
| `chmod 4755` | 加 SUID，执行时以文件属主身份 | `g+s` 为 SGID、`+t` 为 Sticky | `chmod 4755 /usr/local/bin/tool` |
| `chmod g+s dir` | 目录内新建文件继承目录属组 | 团队协作目录常用 | `chmod 2775 /srv/share` |
| `chmod +t dir` | 只有属主或 root 能删目录内文件 | `/tmp` 就是 `1777` | `chmod 1777 /srv/upload` |

> `chmod -R 777` 是坏习惯：任何用户可改可执行，Web 目录被写 shell 的经典入口。目录用 `755`、文件用 `644`，需要写的目录单独授权给服务账号。

### 7.2 chown / chgrp
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `chown user:group` | 同时改属主与属组 | 只写 `user` 则属组不变 | `chown alice:dev app.conf` |
| `chown :group` | 只改属组 | 等同 `chgrp group file` | `chown :www-data /var/www` |
| `chown -R` | 递归修改 | 大目录耗时长，先确认路径 | `chown -R www-data:www-data /var/www` |
| `chgrp -R` / `chown --reference` | 递归改属组 / 参照另一文件对齐属主 | `-R` 递归、`--reference` 参照文件 | `chgrp -R dev /srv/share` |

### 7.3 umask
| umask | 新建文件 | 新建目录 | 场景 |
| --- | --- | --- | --- |
| `022` | `644` | `755` | 默认，最常用 |
| `027` | `640` | `750` | 同组可读、其他人无权限 |
| `077` | `600` | `700` | 私有目录、密钥文件 |
| `002` | `664` | `775` | 团队共享目录（配 SGID） |

文件基准 `666`、目录基准 `777`，实际权限 = 基准 & ~umask；`umask` 查看、`umask -S` 符号形式、`umask 027` 当前 shell 生效（持久化写 `~/.bashrc`）。

### 7.4 ACL 细粒度授权
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `setfacl -m` | 修改 ACL | `u:用户:权限`、`g:组:权限` | `setfacl -m u:alice:rw- report.txt` |
| `setfacl -R -m` | 递归授权，只影响已存在文件 | 新建文件需配默认 ACL | `setfacl -R -m g:dev:rx /srv/share` |
| `setfacl -d -m` | 设默认 ACL，新建文件自动继承 | 只对目录有意义 | `setfacl -d -m u:alice:rwx /srv/share` |
| `setfacl -x` / `-b` | 删除某条 ACL / 清空全部 | `-m m::r-x` 收紧 mask | `setfacl -x u:alice report.txt` |
| `getfacl` | 查看 ACL | `-R` 递归、`-p` 显示绝对路径 | `getfacl /srv/share` |

`ls -l` 权限位末尾的 `+` 表示存在 ACL；ext4 现代内核默认启用，XFS 默认支持。

## 8 进程

### 8.1 ps
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `ps aux` | BSD 风格全量快照 | 含 `%CPU`、`%MEM`、`STAT`、`COMMAND` | `ps aux \| grep nginx` |
| `ps -ef` | System V 风格，含 PPID | `-e` 全部、`-f` 全格式 | `ps -ef --forest` |
| `ps -eo` | 自定义列 | `--sort=-%cpu` 排序 | `ps -eo pid,ppid,stat,%cpu,%mem,cmd --sort=-%cpu \| head` |
| `ps -p` | 看指定 PID | `-p 1234,5678` | `ps -p 1234 -o pid,etime,cmd` |
| `ps -eo stat,pid,cmd` | 按状态筛选 | `D` 不可中断、`Z` 僵尸、`R` 运行、`S` 睡眠 | `ps -eo stat,pid,cmd \| grep '^D'` |

### 8.2 top 与 htop
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `top` | 实时资源视图 | `-b -n1` 批处理输出一次、`-p` 指定 PID | `top -b -n1 \| head -20` |
| `top -H -p` | 看指定进程的线程 | 定位是哪个线程吃 CPU | `top -H -p 1234` |
| `htop` | 彩色交互版，支持鼠标与树形 | `F3` 搜索、`F5` 树形、`F6` 排序、`F9` 杀进程 | `htop -u www-data` |

top 交互键：`P` 按 CPU、`M` 按内存、`T` 按累计时间、`1` 展开各核、`c` 完整命令行、`H` 线程视图、`u` 按用户、`k` 发信号、`r` renice、`q` 退出。

### 8.3 pgrep / pkill / killall
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `pgrep` | 按名字找 PID | `-a` 显示命令行、`-f` 匹配完整命令行、`-u` 按用户 | `pgrep -af 'python worker'` |
| `pkill` | 按名字发信号 | `-f` 完整命令行、`-u` 按用户、`-9` 强杀 | `pkill -f 'python worker.py'` |
| `killall` | 按进程名杀全部 | 比 `pkill` 更粗暴，先 `pgrep` 确认 | `killall -15 nginx` |

### 8.4 kill 与信号
| 信号 | 编号 | 含义 | 用法 |
| --- | --- | --- | --- |
| SIGHUP | 1 | 挂断；守护进程常用来重载配置 | `kill -1 $(cat /run/nginx.pid)` |
| SIGINT | 2 | 中断，等同 `Ctrl+C` | `kill -2 1234` |
| SIGQUIT | 3 | 退出并生成 core | `kill -3 1234`（调试用） |
| SIGKILL | 9 | 强制杀死，不可捕获、不可忽略 | `kill -9 1234`，最后手段 |
| SIGTERM | 15 | 默认终止信号，可捕获做优雅退出 | `kill 1234` 即 `-15` |
| SIGCONT | 18 | 继续被暂停的进程 | `kill -18 1234` |
| SIGSTOP | 19 | 暂停，不可捕获 | `kill -19 1234` |
| SIGTSTP | 20 | 终端暂停，等同 `Ctrl+Z` | `kill -20 1234` |

```bash
kill -l                  # 列出全部信号名与编号
kill -0 1234             # 只检查进程是否存在，不发信号
kill -TERM 1234; sleep 5; kill -9 1234   # 先优雅，5 秒后仍在再强杀
```

### 8.5 nice / renice
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `nice -n 10` | 以低优先级启动 | 范围 `-20`（最高）~`19`（最低） | `nice -n 10 tar -czf bak.tar.gz /data` |
| `renice -n 5 -p` | 调整运行中进程的优先级 | 普通用户只能调大（降优先级） | `renice -n 5 -p 1234` |
| `renice -n 10 -u` | 调整某用户所有进程 | 需 root | `sudo renice -n 10 -u alice` |

### 8.6 前后台作业与 nohup
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `&` | 放后台运行 | 终端关闭仍可能收到 SIGHUP | `./batch.sh &` |
| `jobs` | 查看当前 shell 的作业 | `-l` 带 PID | `jobs -l` |
| `fg` / `bg` | 调回前台 / 让暂停的作业后台继续 | `%1` 指定作业号 | `fg %1`、`bg %1` |
| `Ctrl+Z` | 暂停前台作业并放入后台 | 随后 `bg` 继续 | 编译卡住时常用 |
| `nohup` | 忽略 SIGHUP，退出终端不终止 | 常配 `> out 2>&1 &` | `nohup ./svc.sh > svc.log 2>&1 &` |
| `disown` | 把作业移出作业表 | `-h` 忽略 SIGHUP | `disown -h %1` |

> 长期服务别用 `nohup` 硬扛，交给 systemd：`systemctl enable --now myapp`，有日志、有重启策略、能杀干净整个 cgroup。

### 8.7 lsof
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `lsof -i:8080` | 查端口被谁占用 | `-nP` 不解析域名与端口名 | `lsof -nP -i:8080` |
| `lsof -p` | 查进程打开的所有文件 | 排查句柄泄漏 | `lsof -p 1234 \| wc -l` |
| `lsof -u` | 查某用户打开的文件 | 排查是谁占着文件 | `lsof -u www-data` |
| `lsof +L1` | 已删除但仍被占用的文件 | 磁盘满的经典原因 | `lsof +L1` |

## 9 磁盘

### 9.1 df 与 du
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `df -h` | 各文件系统容量与使用率 | `-T` 显示类型、`-a` 含伪文件系统 | `df -hT` |
| `df -i` | inode 使用率 | 有空间却写不进文件时先看它 | `df -i /` |
| `df -h /path` | 看某路径所在分区 | 比全量输出直观 | `df -h /var/lib/docker` |
| `du -sh` | 汇总目录总占用 | `-s` 只出总和、`-h` 人类可读 | `du -sh /var/log` |
| `du -sh *` | 当前目录各子项占用 | 隐藏项要 `du -sh .[!.]*` | `du -sh /var/*` |
| `du -h --max-depth=1` | 只看一层，逐层下钻 | 与 `sort -h` 组合找大头 | `du -h --max-depth=1 / \| sort -h \| tail` |

### 9.2 挂载与卸载
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `mount` | 查看已挂载 / 挂载设备 | `-t` 指定类型、`-o` 选项 | `mount \| column -t` |
| `findmnt` | 树形看挂载关系 | `-T /path` 反查所在挂载点 | `findmnt -T /var/log` |
| `mount -o remount,rw` | 只读根分区改回读写 | 救援模式常用 | `mount -o remount,rw /` |
| `mount -o loop` | 挂载 ISO 镜像 | 需 loop 设备支持 | `mount -o loop ubuntu.iso /mnt` |
| `mount --bind` | 把目录挂到另一处 | 容器与 chroot 常用 | `mount --bind /data /srv/data` |
| `mount -a` | 按 `/etc/fstab` 全部挂载 | 改完 fstab 先验证，避免开不了机 | `mount -a` |
| `umount` / `fuser -vm` | 卸载 / 查谁占用挂载点 | `-l` 延迟卸载、`-f` 强制；占用时 `fuser -vm /mnt` | `umount -l /mnt` |

### 9.3 块设备与分区
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `lsblk` | 块设备树 | `-f` 显示文件系统与 UUID、`-o` 自定义列 | `lsblk -f` |
| `blkid` | 查设备 UUID 与类型 | `-s UUID -o value` 只取值，写 fstab 用 | `blkid -s UUID -o value /dev/sdb1` |
| `fdisk -l` | 列出分区表 | `-l /dev/sdb` 只看一块盘 | `sudo fdisk -l` |
| `parted -l` | 查看分区，支持 GPT | 交互式分区用 `parted /dev/sdb` | `sudo parted -l` |
| `ncdu` | 交互式磁盘占用分析（需安装） | 方向键浏览、`d` 删除、`q` 退出 | `ncdu /var` |

> 分区、格式化、改 UUID 属于高风险操作：先 `lsblk -f` 确认盘符，别把数据盘当 U 盘写，参见 [15 危险命令清单](#15-危险命令清单)。

## 10 网络

### 10.1 ip
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `ip addr` | 查 IP 与网卡 | `-br` 简洁、`-4`/`-6` 限定协议 | `ip -br a` |
| `ip addr show` | 看指定网卡 | 输出含 MAC、MTU、状态 | `ip a show eth0` |
| `ip route` | 查路由表 | `get` 查某地址走哪条路由 | `ip route get 8.8.8.8` |
| `ip link set` | 启停网卡、改 MTU | `up`/`down`、`mtu 1400` | `ip link set eth0 up` |
| `ip -s link` | 网卡收发统计与错误计数 | 看丢包、error、drop | `ip -s link show eth0` |

### 10.2 ss
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `ss -lntp` | 监听中的 TCP 端口与进程 | `-l` 监听、`-n` 不解析、`-p` 进程 | `ss -lntp` |
| `ss -tulnp` | 同时看 TCP 与 UDP | `-u` UDP | `ss -tulnp \| grep :53` |
| `ss -tanp` | 所有 TCP 连接 | `state established` 只看已建立 | `ss -tanp state established` |
| `ss -s` | 连接数汇总 | 快速看 TIME_WAIT 是否异常 | `ss -s` |

### 10.3 ping / traceroute / mtr
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `ping` | ICMP 连通性与 RTT | `-c4` 发 4 个、`-i` 间隔、`-W` 超时秒 | `ping -c4 -W2 8.8.8.8` |
| `ping -s 1472 -M do` | 测 MTU（1472+28=1500） | `-M do` 禁止分片 | `ping -c2 -s1472 -M do example.com` |
| `traceroute` | 逐跳路径 | `-n` 不解析、`-T` TCP、`-p` 端口 | `traceroute -nT -p 443 example.com` |
| `mtr` | 持续逐跳统计，看丢包在哪一跳 | `-rw` 报告模式、`-c` 次数 | `mtr -rwc 20 example.com` |

### 10.4 curl 与 wget
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `curl -I` | 只取响应头 | 看状态码、`Content-Type`、跳转 | `curl -I https://example.com` |
| `curl -X` | 指定方法 | `-X POST/PUT/DELETE` | `curl -X DELETE http://127.0.0.1:8080/api/1` |
| `curl -d` | 发请求体（默认表单） | `--data-urlencode` 自动转义 | `curl -d 'user=alice&pwd=123' http://127.0.0.1/login` |
| `curl -H` | 加请求头，可多次 | JSON 必须显式声明 | `curl -H 'Content-Type: application/json' -d '{"a":1}' http://127.0.0.1/api` |
| `curl -o` / `-O` | 存到指定文件 / 用远端文件名 | `-o /dev/null` 丢弃响应体 | `curl -o app.tar.gz https://example.com/app.tar.gz` |
| `curl -L` / `-sS` | 跟随 3xx / 静默但保留错误 | 脚本里常用 | `curl -sS -L http://127.0.0.1:8080/health` |
| `curl -w` | 自定义输出状态码与耗时 | `%{http_code}`、`%{time_total}` | `curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' http://127.0.0.1` |
| `curl --resolve` | 绕过 DNS 直连指定 IP | 测试后端 / 未切流量 | `curl --resolve example.com:443:10.0.0.5 https://example.com` |
| `wget` | 下载文件 | `-c` 断点续传、`-O` 指定名、`-P` 目录 | `wget -c https://example.com/app.tar.gz` |

### 10.5 DNS：dig / nslookup / host
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `dig +short` | 查 A 记录，只输出结果 | 简洁适合脚本 | `dig +short example.com` |
| `dig @8.8.8.8` | 指定 DNS 服务器 | 对比本地与公共解析 | `dig @8.8.8.8 example.com MX` |
| `dig -x` | 反查 PTR | 由 IP 查域名 | `dig -x 8.8.8.8 +short` |
| `nslookup` / `host` | 交互式查询 / 简洁查询 | 指定记录类型 | `nslookup -type=MX example.com` |
| `cat /etc/resolv.conf` | 看本机 DNS 配置 | systemd-resolved 下可能是 `127.0.0.53` | `resolvectl status` |

### 10.6 nc 与 tcpdump
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `nc -zv` | 探测端口通不通 | `-z` 只扫不传数据、`-v` 输出、`-w` 超时 | `nc -zv 127.0.0.1 8080` |
| `nc -l` | 监听端口，做临时服务端 | 新版写 `nc -l 9000`，老版 `nc -l -p 9000` | `nc -l 9000` |
| `nc` 传文件 | 两端对拷 | 接收端 `nc -l 9000 > f`，发送端 `nc host 9000 < f` | `nc -w3 10.0.0.5 9000 < app.tar.gz` |
| `tcpdump -i any` | 抓包，指定网卡 | `-nn` 不解析域名与端口名、`-c` 包数 | `tcpdump -i any -nn -c 20` |
| `tcpdump port 80` | 按端口 / 主机过滤 | 支持 `host`、`src`、`dst`、`and/or/not` | `tcpdump -i eth0 -nn port 8080` |
| `tcpdump -w` / `-r` | 存 pcap / 读 pcap | 可再叠加过滤条件 | `tcpdump -i any -w /tmp/a.pcap -c 500` |

## 11 系统信息

### 11.1 系统与内核
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `uname -a` | 内核、主机名、架构全量 | `-r` 内核版本、`-m` 架构 | `uname -a` |
| `cat /etc/os-release` | 发行版与版本，最通用 | 老系统看 `/etc/issue` | `cat /etc/os-release` |
| `hostnamectl` | 主机名、系统、内核、虚拟化 | `set-hostname` 永久改主机名 | `hostnamectl set-hostname web01` |
| `lscpu` | CPU 型号、核数、缓存、NUMA | 比 `/proc/cpuinfo` 可读 | `lscpu` |
| `nproc` | 可用 CPU 核数 | 编译时 `make -j$(nproc)` | `nproc` |

### 11.2 资源与负载
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `uptime` | 运行时长、登录数、load | 输出与 `w` 首行相同 | `uptime` |
| `free -h` | 内存与 swap | `-s 1` 每秒刷新、`-m` 以 MB 显示 | `free -h` |
| `cat /proc/loadavg` | 负载原始值 | 第四字段是运行中/总进程数 | `cat /proc/loadavg` |
| `vmstat 1` | `r` 运行队列、`b` 阻塞、`si/so` 换页、`wa` IO 等待 | `vmstat 1 5` 采 5 次 | `vmstat 1 5` |
| `iostat -x 1` | 每块盘 `%util`、`await` | 需 `sysstat` | `iostat -x 1 3` |

### 11.3 时间与登录
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `date` | 显示/设置时间 | `+%F` 日期、`+%T` 时间、`+%s` 时间戳 | `date '+%F %T'` |
| `date -d` | 解析自然语言时间 | 常用于算前一天 | `date -d '1 day ago' +%F` |
| `timedatectl` | 时区、NTP 同步状态 | `set-timezone` 改时区 | `timedatectl set-timezone Asia/Shanghai` |
| `cal` | 日历 | `-3` 显示三个月、`-y` 全年 | `cal -3` |
| `who` / `w` | 当前登录用户 / 及其正在执行的命令 | `who -b` 看上次启动时间 | `w` |
| `last` / `lastb` | 登录历史 / 失败登录 | `-n 10` 最近 10 条、`-x` 含关机记录 | `last -n 10` |
| `dmesg` | 内核环形缓冲 | `-T` 可读时间、`-w` 跟踪、`-l err` 只看错误 | `dmesg -T -l err,warn` |

> `free` 的 `buff/cache` 可回收，判断内存是否紧张看 `available`；`available` 很低且 `si/so` 持续非 0 才说明在换页。

## 12 服务与日志

### 12.1 systemctl
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `systemctl start` | 启动服务 | 立即生效，不设开机自启 | `systemctl start nginx` |
| `systemctl stop` | 停止服务，杀整个 cgroup | 比 `kill` 干净 | `systemctl stop nginx` |
| `systemctl restart` | 重启（先停再起） | 改配置后用 | `systemctl restart nginx` |
| `systemctl reload` | 只重载配置，不断连接 | 服务需支持 `ExecReload` | `systemctl reload nginx` |
| `systemctl status` | 状态、最近日志、PID | `-l` 不截断、`--no-pager` | `systemctl status nginx -l --no-pager` |
| `systemctl enable` | 设开机自启 | `--now` 同时启动 | `systemctl enable --now nginx` |
| `systemctl disable` | 取消开机自启 | 不会停止当前进程 | `systemctl disable nginx` |
| `systemctl list-units` | 列出已加载 unit | `--type=service --state=running` | `systemctl list-units --type=service --state=running` |
| `systemctl list-unit-files` | 所有 unit 及启用状态 | `--state=enabled` 只看自启 | `systemctl list-unit-files --state=enabled` |
| `systemctl is-enabled` / `is-active` | 脚本里判断状态 | 返回 `enabled`/`active` 或非 0 | `systemctl is-active --quiet nginx && echo up` |
| `systemctl daemon-reload` | 重载 unit 文件 | 改完 `.service` 必须执行 | `systemctl daemon-reload` |
| `systemctl --failed` | 列出失败 unit | 开机排查第一站 | `systemctl --failed` |

### 12.2 journalctl
| 命令 | 作用 | 常用参数 | 示例 |
| --- | --- | --- | --- |
| `journalctl -u` | 看某服务日志 | `-f` 跟踪、`--no-pager` 不分页 | `journalctl -u nginx --no-pager -n 100` |
| `journalctl -f` | 实时跟踪全部日志 | 常配 `-u` | `journalctl -u nginx -f` |
| `journalctl --since` | 按时间范围 | 支持 `"1 hour ago"`、`"2026-10-24 10:00"`；配 `--until` | `journalctl -u nginx --since '1 hour ago'` |
| `journalctl -p` | 按优先级过滤 | `err`、`warning`、`info` | `journalctl -p err -b --no-pager` |
| `journalctl -n` / `--grep` | 最后 N 行 / 按内容搜索 | `--grep` 比管道 grep 省内存 | `journalctl -u nginx --grep 'upstream'` |
| `journalctl --disk-usage` | 日志占用 | 清理用 `--vacuum-time=7d` | `journalctl --vacuum-time=7d` |

### 12.3 /var/log 与轮转
| 路径 | 内容 | 查看示例 |
| --- | --- | --- |
| `/var/log/syslog`、`/var/log/messages` | 系统综合日志（Debian / RHEL） | `tail -f /var/log/syslog` |
| `/var/log/auth.log`、`/var/log/secure` | 认证与 sudo 记录 | `grep -i failed /var/log/auth.log` |
| `/var/log/kern.log`、`/var/log/dmesg` | 内核日志 | `tail -50 /var/log/kern.log` |
| `/var/log/nginx/`、`/var/log/httpd/` | Web 访问与错误日志 | `tail -F /var/log/nginx/access.log` |
| `/var/log/journal/` | 二进制日志，用 `journalctl` 读 | `journalctl --disk-usage` |

`logrotate` 负责切割与清理，配置在 `/etc/logrotate.conf` 与 `/etc/logrotate.d/`；`copytruncate` 适合不支持重开文件的程序，`postrotate` 里通常 `systemctl reload nginx`。

## 13 包管理

### 13.1 apt 与 dnf 对照
| 操作 | Debian/Ubuntu（apt） | RHEL/Fedora（dnf） | 备注 |
| --- | --- | --- | --- |
| 更新索引 | `apt update` | `dnf makecache` | `apt update` 不升级软件 |
| 升级已装软件 | `apt upgrade` | `dnf upgrade` | `apt full-upgrade` 可处理依赖变更 |
| 安装 | `apt install nginx` | `dnf install nginx` | 可一次装多个 |
| 卸载 | `apt remove nginx` | `dnf remove nginx` | 配置残留需另清 |
| 彻底卸载（含配置） | `apt purge nginx` | 无直接对应 | `dnf` 需手动删 `/etc` 下配置 |
| 搜索 / 详情 | `apt search nginx` / `apt show nginx` | `dnf search nginx` / `dnf info nginx` | 搜不到先更新索引 |
| 已安装列表 | `apt list --installed` | `dnf list installed` | 过滤：`\| grep nginx` |
| 可升级列表 | `apt list --upgradable` | `dnf check-update` | 变更窗口前先看 |
| 清理无用依赖 / 缓存 | `apt autoremove` / `apt clean` | `dnf autoremove` / `dnf clean all` | 磁盘紧张时用 |
| 仓库列表 | `/etc/apt/sources.list.d/` | `dnf repolist` | 加源：`add-apt-repository` / `dnf config-manager --add-repo` |

`yum` 在 RHEL 8+ 是 `dnf` 的软链接，命令基本通用。

### 13.2 底层包查询
| 操作 | Debian（dpkg） | RHEL（rpm） | 示例 |
| --- | --- | --- | --- |
| 装本地包 | `dpkg -i pkg.deb` | `rpm -ivh pkg.rpm` | 缺依赖时 `apt -f install` / `dnf install ./pkg.rpm` |
| 包内文件列表 | `dpkg -L nginx` | `rpm -ql nginx` | `dpkg -L nginx \| grep conf` |
| 文件属于哪个包 | `dpkg -S /usr/sbin/nginx` | `rpm -qf /usr/sbin/nginx` | 排查命令来源 |
| 包版本 / 信息 | `dpkg -l nginx` / `dpkg -s nginx` | `rpm -q nginx` / `rpm -qi nginx` | `dpkg -l \| grep ^ii` 列已装 |

### 13.3 版本锁定与仓库
| 命令 | 作用 | 示例 |
| --- | --- | --- |
| `apt-mark hold` | 锁定版本，禁止升级 | `apt-mark hold nginx`、`apt-mark unhold nginx` |
| `apt-cache policy` | 看可用版本与来源 | `apt-cache policy nginx` |
| `dnf history` | 事务历史，可回滚 | `dnf history`、`dnf history undo 12` |
| `add-apt-repository` | 添加 PPA 或第三方源 | `add-apt-repository ppa:ondrej/php` |
| `dnf config-manager` | 启用/禁用仓库 | `dnf config-manager --set-enabled powertools` |

> 生产升级前先看变更：`apt list --upgradable`、`dnf check-update`，在测试机验证；安全更新可用 `unattended-upgrades` / `dnf-automatic` 单独控制。

## 14 高频组合拳

| # | 任务 | 一行命令 | 说明 |
| --- | --- | --- | --- |
| 1 | 查端口被谁占用 | `ss -lntp \| grep :8080` | 无结果再试 `lsof -nP -i:8080`、`fuser -n tcp 8080` |
| 2 | 找最大的文件 | `find / -xdev -type f -size +500M -printf '%s %p\n' 2>/dev/null \| sort -nr \| head -20` | `-xdev` 不跨文件系统；字节数可配 `numfmt --to=iec` |
| 3 | 批量改后缀名 | `for f in *.jpeg; do mv -n -- "$f" "${f%.jpeg}.jpg"; done` | `-n` 不覆盖；`${f%.jpeg}` 去后缀；也可 `rename 's/\.jpeg$/.jpg/' *.jpeg` |
| 4 | 统计代码总行数 | `find . -type f \( -name '*.c' -o -name '*.h' \) -print0 \| xargs -0 wc -l \| tail -1` | 多文件时 `wc` 输出 `total` 行 |
| 5 | 清理 7 天前日志 | `find /var/log -type f -name '*.log' -mtime +7 -print` | 确认无误后把 `-print` 换成 `-delete`；更规范的是 logrotate |
| 6 | 查最近 1 小时改动的文件 | `find . -type f -mmin -60 -printf '%TY-%Tm-%Td %TH:%TM %p\n' \| sort -r \| head` | `-printf` 比 `ls -l` 好排序；也可 `-newermt '-1 hour'` |
| 7 | 磁盘满快速定位 | `du -h --max-depth=1 / \| sort -h \| tail -5` | 逐层下钻；仍对不上就 `lsof +L1` 与 `df -i` |
| 8 | 日志 Top10 IP | `awk '{print $1}' access.log \| sort \| uniq -c \| sort -nr \| head -10` | `uniq` 必须先 `sort`；字段位置按日志格式调整 |
| 9 | 实时盯错误日志 | `tail -F app.log \| grep --line-buffered -iE 'error\|exception'` | `--line-buffered` 保证及时输出；`-F` 支持轮转 |
| 10 | 批量替换文本 | `grep -rlZ 'old' --include='*.conf' . \| xargs -0 sed -i.bak 's/old/new/g'` | `-Z`/`-0` 处理空格文件名；`-i.bak` 留退路 |

> 一行命令先在测试目录跑一遍；涉及删除、覆盖的，把动作命令换成 `echo` 或 `-print` 预览，确认输出范围再执行。

## 15 危险命令清单

### 15.1 高风险命令与安全写法
| 命令/写法 | 后果 | 安全写法 | 说明 |
| --- | --- | --- | --- |
| `rm -rf /` | 删光根文件系统，系统当场报废 | `rm -rf -- "${dir:?}"` | 现代 `rm` 默认拒绝 `/`，但加 `--no-preserve-root` 或变量为空时照样执行 |
| `rm -rf $DIR/`（变量未设） | 展开成 `rm -rf /` | `set -u` + `${DIR:?}`，先 `echo "$DIR"` | 脚本里变量拼路径必须加保护 |
| `rm -rf *` 在错误目录 | 删掉整个项目或家目录 | `pwd && ls` 确认后再执行；用 `rm -ri` | 通配符展开前先 `echo *` 看范围 |
| `dd if=xx of=/dev/sdX` | 覆盖分区表或整盘数据，不可恢复 | 先 `lsblk -f` 确认盘符；写盘加 `status=progress conv=fsync` | `of=` 写错一个字母就是灾难 |
| `mkfs.ext4 /dev/sdb` | 格式化整块盘 | `lsblk -f`、`blkid` 双确认；`wipefs -n` 预览 | 别把数据盘当新盘 |
| `chmod -R 777 /` | 所有用户可改可执行，权限模型全失效 | 按需 `chmod -R u=rwX,g=rX,o= /data` | Web 目录 777 是被写 shell 的头号原因 |
| `chown -R root:root /` | 普通用户服务无法读写自己的文件 | 只对目标目录 `chown -R user:group /path` | 家目录权限改坏后要逐个修回 |
| `> file` 覆盖 | 原内容瞬间清空，无备份 | 先 `cp file file.bak`；清空用 `truncate -s 0 file` | `set -o noclobber` 可防误覆盖，`>\|` 强制覆盖 |
| `kill -9` 滥用 | 进程来不及清理临时文件、刷盘、释放锁，数据库可能损坏 | 先 `kill -15`，等 5~10 秒；服务用 `systemctl stop` | `-9` 对 `D` 状态与僵尸进程也无效 |
| `find / -delete` / `-exec rm -rf` | 按错误条件批量删除 | 先用 `-print` 预览，再换 `-delete` | `-delete` 自带深度优先，别与 `-prune` 混用 |
| `crontab -r` | 无确认清空当前用户全部定时任务 | 先 `crontab -l > /root/cron.bak`，再 `crontab -e` | `-r` 与 `-e` 只差一个字母 |
| `iptables -F` / `nft flush ruleset` | 清空防火墙规则，远程主机可能直接失联 | 先 `iptables-save > /root/ipt.rules` | 远程操作前确认有带外通道 |
| `:(){ :\|:& };:` | fork 炸弹，耗尽 PID 与内存，机器卡死 | `ulimit -u 200`、cgroup `pids.max` 限制 | 只能重启或从其他终端杀进程 |

### 15.2 执行前的六条习惯
1. **先打印再执行**：把 `rm`/`mv`/`-delete` 换成 `echo`、`-print`，确认输出范围。
2. **变量必加保护**：`set -euo pipefail`，路径用 `"${var:?}"`，文件名统一加引号。
3. **用绝对路径与 `--`**：`rm -rf -- /data/tmp`，避免文件名被当成选项。
4. **先备份再动手**：配置文件 `cp -a` 带时间戳，重要操作前打快照。
5. **远程操作进 tmux**：`tmux new -s work`，断线不中断；改网络/防火墙时留一条已登录会话。
6. **最小权限**：日常不用 root，`sudo` 只给必要命令；`rm -i` 别名只防手滑，不防 `-rf`。

### 15.3 误删或误覆盖后的补救
- **立即停止写入**：卸载或只读挂载分区（`mount -o remount,ro /data`），避免数据块被覆盖。
- **查仍被占用的文件**：`lsof +L1` 找到已删除但进程还开着的 fd，可从 `/proc/<pid>/fd/<n>` 复制回来。
- **从备份/快照恢复**：优先 LVM 快照、云盘快照、`rsync` 备份；确认恢复点后再覆盖。
- **ext 系可尝试**：`extundelete`、`testdisk`、`photorec`，务必对镜像或只读副本操作。
- **复盘**：把事故写进 runbook，补上「预览 + 备份 + 二次确认」步骤，比记住命令更重要。
