# Linux Shell 脚本

面向面试与真实运维：语法压成表格，末尾 6 个可直接上线的脚本 + 15 道问答。与《Linux 基础》《Linux 常用命令》互补——那两篇讲系统和命令，这篇只解决「脚本怎么写才不出事」。

约定：bash 4.2+ 与 GNU coreutils，Ubuntu 22.04 / CentOS Stream 9 可跑；`$` 是普通用户，`#` 是 root；`file`、`dir` 是占位符。bash 4 特性（关联数组、`mapfile`、`${var,,}`）老 macOS 不支持。

15 节：[1 为什么学 Shell](#1-为什么学-shell) · [2 第一个脚本](#2-第一个脚本) · [3 变量与引号](#3-变量与引号) · [4 参数处理](#4-参数处理) · [5 条件判断](#5-条件判断) · [6 循环](#6-循环) · [7 函数](#7-函数) · [8 数组与字符串](#8-数组与字符串) · [9 重定向与管道](#9-重定向与管道) · [10 文本处理配合](#10-文本处理配合) · [11 退出码与错误处理](#11-退出码与错误处理) · [12 调试](#12-调试) · [13 定时任务](#13-定时任务) · [14 实战脚本](#14-实战脚本) · [15 面试问答](#15-面试问答)

## 1 为什么学 Shell
Shell 是 Linux 的胶水层：登录、CI、容器 entrypoint、cron 都在调它；它擅长串联命令，不擅长业务逻辑。
### 1.1 适用场景
| 场景 | 典型写法 | 为什么合适 |
| --- | --- | --- |
| 一次性运维 | 日志清理、备份、巡检、批量改名 | 十几行搞定，无编译与运行时依赖 |
| 串联系统命令 | `find \| xargs tar`、`df \| awk` | 管道就是它的 DSL |
| 容器入口 | `entrypoint.sh` 等依赖、改配置、`exec` 降权 | 任何镜像都有 sh/bash |
| CI 胶水 | 发布、健康检查、构建前后处理 | 与 runner 同环境，改完即生效 |

### 1.2 不适用场景与判断
| 场景 | 问题 | 替代 |
| --- | --- | --- |
| 超过约 150~200 行、有状态 | 无模块无类型，错误处理只有退出码 | Python |
| 复杂数据结构 | 只有索引/关联数组，嵌套要拼字符串 | Python dict |
| 需要单元测试 | bats 生态弱，mock 外部命令别扭 | pytest |
| 解析 JSON/YAML、并发 | 只能外挂 jq/yq；`&`+`wait` 没有超时原语 | Python / Go |

判断标准：只调现成命令且短 → shell；要解析结构化数据、重试、状态机、测试 → Python；容器 entrypoint 只做 `exec` → shell。反例：用 bash 写 HTTP 服务、解析 HTML。经验：一屏拆函数，150 行换语言，评审先看 `set -euo pipefail`、引号、`trap`。

## 2 第一个脚本
### 2.1 shebang 与最小脚本
```bash
#!/usr/bin/env bash
set -euo pipefail
echo "hello, ${1:-world}"
```
`#!/usr/bin/env bash` 走 PATH 找 bash（macOS、Nix 友好），`#!/bin/bash` 写死路径（容器更可控）；shebang 必须第一行第一列，前面有空行或 BOM 即失效。存成 CRLF 会报 `bad interpreter`，用 `dos2unix` 修。
### 2.2 三种运行方式
| 写法 | 需要 x 权限 | 解释器 | 影响当前 shell | 用途 |
| --- | --- | --- | --- | --- |
| `bash script.sh` | 否 | 显式 bash，忽略 shebang | 否，子进程 | 调试、CI、cron |
| `./script.sh` | 是 | 由 shebang 决定 | 否，子进程 | 正式部署 |
| `source script.sh` | 否 | 当前 shell | **是**，变量/函数/`cd` 保留 | 加载配置与函数库 |
| `sh script.sh` | 否 | `/bin/sh`（Ubuntu 是 dash） | 否，子进程 | 只写 POSIX 时 |

`chmod +x` 后才能 `./`；`sh script.sh` 忽略 shebang，dash 不支持 `[[ ]]`、数组、`$'…'`，所以「`bash x.sh` 行、`sh x.sh` 报错」多半是写了 bash 扩展。
### 2.3 set -euo pipefail
| 选项 | 作用 | 坑 |
| --- | --- | --- |
| `set -e` | 命令失败立即退出 | `if`/`&&`/`\|\|`/`!` 里的失败不算；`((i++))` 返回 1 会误退 |
| `set -u` | 引用未定义变量报错 | `${1}` 无参即退出，用 `${1:-}` 兜底 |
| `set -o pipefail` | 管道任一环失败即失败 | 默认只看最后一环 |

组合写成 `set -euo pipefail`，放在 shebang 之后；POSIX sh 没有 pipefail，`set -e` 的失效场景见 11.2。

## 3 变量与引号
### 3.1 定义与使用
```bash
name="app"                       # 等号两边不能有空格
export PATH="/opt/bin:${PATH}"   # 导出给子进程
echo "${name}.log"               # $name.log 会被当成变量 name.log
```
### 3.2 参数展开
| 写法 | 含义 | 示例 |
| --- | --- | --- |
| `${var}` | 明确变量边界 | `${name}.log` |
| `${var:-default}` | 未设置**或为空**时用默认值 | `${PORT:-8080}` |
| `${var:=default}` | 同上并回写 var | `${DIR:=/tmp}` |
| `${var:?msg}` | 未设置或为空则报错退出 | `${1:?usage: $0 file}` |
| `${var:+alt}` | 已设置且非空时用 alt | `${DEBUG:+--verbose}` |
| `${#var}` | 字符串长度 | `${#name}` → 3 |

`${var:-}` 是最高频的兜底写法；变量默认都是字符串，算术用 `$(( ))`。
### 3.3 引号对比
| 写法 | 变量展开 | 命令替换 | 通配符 | 用途 |
| --- | --- | --- | --- | --- |
| `"..."` | 是 | 是 | 否 | 默认选择，几乎总是加它 |
| `'...'` | 否 | 否 | 否 | 正则、awk/sed、JSON、含 `$` 的模板 |
| 不加引号 | 是 | 是 | 是 | 只在你明确要分词或通配时 |
| `` `...` `` | 是 | 是 | 否 | 旧写法，不能嵌套，统一换 `$()` |
| `$'...'` | 否 | 否 | 否 | 解释 `\n` `\t` `\x41` |

### 3.4 命令替换、算术与头号 bug
```bash
now=$(date +%F)
n=$(( $(wc -l < access.log) + 1 ))
(( n > 10 )) && echo big          # (( )) 有退出码，可以当条件
echo "scale=2; 1/3" | bc          # bash 只做整数运算
f="a b.txt"; touch $f             # 错误：拆成两个参数，建了两个文件
touch "$f"                        # 正确
```
`$(( ))` 里变量不加 `$`；除零报错并返回非 0，`set -e` 下会终止。规则：变量、命令替换、位置参数一律加双引号。

## 4 参数处理
### 4.1 特殊参数
| 变量 | 含义 | 注意 |
| --- | --- | --- |
| `$0` | 脚本名（含调用路径） | `basename "$0"` 取纯名字 |
| `$1`…`$9`、`${10}` | 位置参数 | 第 10 个起必须花括号 |
| `$#` | 参数个数 | 不含 `$0` |
| `$@` | 参数列表 | **`"$@"` 保留每个参数的边界** |
| `$*` | 参数列表 | `"$*"` 用 IFS 首字符拼成一个串 |
| `$?` | 上一条命令的退出码 | 0 成功，会被下一条命令覆盖 |

转发只写 `"$@"`：`cp "$@"` 遇到 `a b` 仍是一个参数；`$@` 或 `"$*"` 都会被拆开或拼接。
### 4.2 shift 与手写长选项
`while [[ $# -gt 0 ]]` 配 `shift`（`$2` 变成 `$1`，`$#` 减一）是遍历参数的标准写法，`shift 2` 一次移两位；移多了返回非 0，`set -e` 下会退出，所以循环条件先判 `$#`。长选项用 `case` 配合 `shift`：

```bash
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--file)     file="${2:?--file 需要值}"; shift 2 ;;
    -f=*|--file=*) file="${1#*=}"; shift ;;
    -n|--dry-run)  dry=1; shift ;;
    --)            shift; break ;;
    -*)            echo "未知选项：$1" >&2; exit 2 ;;
    *)             break ;;      # 第一个非选项即位置参数
  esac
done
```
`${1#*=}` 取等号右边的值；`--` 之后全部当位置参数，是处理「文件名以 `-` 开头」的标准解法；校验集中放开头：`[[ $# -ge 1 ]] || usage`。
### 4.3 getopts：短选项
```bash
while getopts ":vo:h" opt; do
  case "$opt" in
    v) verbose=1 ;;
    o) out="$OPTARG" ;;
    h) usage ;;
    :)  echo "缺参数：-$OPTARG" >&2; exit 2 ;;
    \?) echo "未知选项：-$OPTARG" >&2; exit 2 ;;
  esac
done
shift $((OPTIND - 1))   # 剩下的是非选项参数
```
选项串开头的 `:` 让缺参进入 `:` 分支而不自动报错；`getopts` 只支持短选项，`OPTIND` 要重置才能再次解析。

## 5 条件判断
### 5.1 [[ ]] 与 [ ]
| 对比项 | `[ ]`（test 命令） | `[[ ]]`（bash 关键字） |
| --- | --- | --- |
| 标准 | POSIX，sh 可用 | bash/ksh/zsh，sh 不可用 |
| 空变量 | 不加引号会报 `unary operator expected` | 不需要引号，空串安全 |
| 逻辑 | `-a` `-o`（已废弃） | `&&` `\|\|` `!` |
| 模式 | 不支持 | `==` 右侧通配符，`=~` 正则 |

bash 脚本一律用 `[[ ]]`；写 POSIX 兼容脚本或极简判断才用 `[ ]`。`[` 是命令，`[ -f x]` 少空格必错。
### 5.2 字符串与数值
| 测试 | 含义 | 示例 |
| --- | --- | --- |
| `-z` / `-n` | 长度为 0 / 非 0 | `[[ -z "${x}" ]]` |
| `=`, `==`, `!=` | 相等 / 模式匹配 / 不等 | `[[ $f == *.log ]]` |
| `=~` | 正则匹配，捕获在 `BASH_REMATCH` | 校验数字输入 |
| `-eq -ne -lt -le -gt -ge` | 整数比较 | `[ "$n" -gt 0 ]` |
| `(( n > 0 ))` | 算术比较，推荐 | 支持 `+=`、`++`、位运算 |

`-eq` 遇到非数字会按变量名求值（`[ abc -eq 0 ]` 可能为真），先用正则校验；`<` `>` 在 `[ ]` 里是重定向，要写 `\<` 或改用 `[[ ]]`。
### 5.3 文件测试
| 测试 | 含义 |
| --- | --- |
| `-e` | 存在（文件、目录或断链的符号链接） |
| `-f` / `-d` | 普通文件 / 目录 |
| `-r` / `-w` / `-x` | 当前用户可读 / 可写 / 可执行（root 下几乎恒真） |
| `-s` | 存在且大小大于 0（判断日志空不空） |
| `-p` / `-S` / `-b` / `-c` | 管道 / socket / 块设备 / 字符设备 |
| `a -nt b` / `a -ot b` | a 比 b 新 / 旧（增量备份） |

`-r/-w/-x` 对 root 几乎恒真，判断权限不能只看它们；组合写 `[[ -f $f && -r $f ]]`，别用废弃的 `-a`。
### 5.4 && || 与短路
```bash
[[ -f "$conf" ]] && source "$conf"
command -v nginx >/dev/null || { echo "未安装 nginx" >&2; exit 1; }
```
`A && B || C` **不是** if-else：B 失败也会走 C，要分支就写 `if`。`[[ ... ]] && cmd` 作为函数最后一条命令时条件为假会让函数返回 1，末尾显式 `return 0`。

## 6 循环
### 6.1 for
```bash
for i in 1 2 3; do echo "$i"; done
for f in /var/log/*.log; do          # 通配符由 shell 展开
  [[ -e "$f" ]] || continue          # 无匹配时 f 是字面量
  wc -l "$f"
done
for ((i = 0; i < 10; i++)); do echo "$i"; done     # C 风格
```
别写 `for f in $(ls)`：按空白拆分，文件名带空格就断。遍历目录树用 `find -print0`，或 `shopt -s globstar` 后 `for f in **/*.log`。
### 6.2 while read 按行读
```bash
while IFS= read -r line; do
  printf '%s\n' "$line"
done < access.log
```
`IFS=` 防止吃空白，`-r` 防止反斜杠被转义，两条都必须加。用 `done < file` 而不是 `cat file |`：管道会开子 shell，循环里的赋值外面看不到。最后一行没换行符会漏读，用 `|| [[ -n $line ]]` 兜底；文件名可能含空格或换行时，改用 `find -print0` 配 `read -r -d ''`（或 `xargs -0`）。
### 6.3 until 与 break/continue
```bash
n=0
until (( n >= 3 )); do       # 条件为假时循环，与 while 相反
  n=$((n + 1)); echo "retry $n"   # 别写 ((n++))，n=0 时返回 1 触发 set -e
done
for f in *.txt; do
  [[ $f == skip* ]] && continue
  [[ $f == stop* ]] && break 2   # 跳出两层
done
```

## 7 函数
### 7.1 定义与调用
```bash
log() { echo "[$(date '+%F %T')] $*" >&2; }
say_hi() {
  local name="${1:-guest}"      # local 只在本函数有效
  echo "hi, ${name}"
}
say_hi "tom"                    # 先定义后调用
```
`function name {` 与 `name() {` 等价，后者 POSIX。`local` 要写在赋值同一行或之前，`local x=$(false)` 会把失败退出码吞成 0。
### 7.2 参数与返回值
函数内 `$1` 是函数参数，`$0` 仍是脚本名，`"$@"` 原样转发。`return N` 只返回 0–255 的状态码给 `$?` 用，不能返回字符串；要返回数据用 `echo` + 命令替换 `out=$(say_hi tom)`，此时 `$?` 是替换里最后一条命令的退出码。既要数据又要状态，用全局变量、`local -n`（nameref）或输出多行后 `read`。`!` 反转退出码；调用函数不带括号，写 `say_hi tom`。
### 7.3 local 与作用域
```bash
x=global
f() { local x=local; echo "$x"; }   # 输出 local
g() { x=changed; }                  # 不声明就是全局
```
Bash 是**动态作用域**：函数里能读到调用者的 `local` 变量，别依赖这一点，函数内变量一律显式 `local`。`local -r x=1` 只读，`declare -g` 改全局。
### 7.4 递归
```bash
fact() {
  local n="$1"
  (( n <= 1 )) && { echo 1; return 0; }
  local sub
  sub=$(fact $((n - 1)))        # 必须用命令替换接住结果
  echo $(( n * sub ))
}
fact 5                          # 120
```
每次 `$( )` 都 fork 子 shell，深递归又慢又可能栈溢出；遍历目录优先 `find`/`globstar`。

## 8 数组与字符串
### 8.1 索引数组
```bash
arr=(a "b c" d)
arr+=(e)                          # 追加
echo "${arr[0]} ${arr[-1]}"       # a e（负下标要 bash 4.3+）
echo "${#arr[@]}"                 # 元素个数 4
for x in "${arr[@]}"; do echo "$x"; done              # 必须加引号
for i in "${!arr[@]}"; do echo "$i=${arr[$i]}"; done  # 遍历下标
unset 'arr[1]'                    # 留空洞，下标不重排
```
`${arr[@]}` 不加引号会被分词；`${#arr}` 是首元素长度而不是个数。`mapfile -t lines < file` 一次读成数组（bash 4）。
### 8.2 关联数组
```bash
declare -A conf
conf[host]="127.0.0.1"
conf[port]=8080
for k in "${!conf[@]}"; do echo "$k=${conf[$k]}"; done
[[ -v conf[host] ]] && echo "已设置"
```
必须先 `declare -A`，bash 3（老 macOS 自带）不支持；键无序，遍历顺序不保证。
### 8.3 字符串操作
以 `s=/data/app.tar.gz` 为例：
| 写法 | 作用 | 结果 |
| --- | --- | --- |
| `${#s}` | 长度 | 16 |
| `${s#*/}` / `${s##*/}` | 删最短 / 最长前缀 | `data/app.tar.gz` / `app.tar.gz` |
| `${s%.*}` / `${s%%.*}` | 删最短 / 最长后缀 | `/data/app.tar` / `/data/app` |
| `${s/app/APP}` | 替换第一个 | `/data/APP.tar.gz` |
| `${s//a/A}` | 替换全部 | `/dAtA/App.tAr.gz` |
| `${s/#\/data/\/opt}` | 只替换开头 | `/opt/app.tar.gz` |
| `${s/%gz/bz2}` | 只替换结尾 | `/data/app.tar.bz2` |
| `${s:6}` / `${s:0:5}` | 子串 | `app.tar.gz` / `/data` |

记忆法：`#` 从左删、`%` 从右删，键盘上 `#` 在 `%` 左边，`##`/`%%` 是贪婪版本；POSIX 兼容就用 `basename`、`dirname`。`IFS=, read -ra parts <<< "a,b,c"` 可把一行拆成数组。

## 9 重定向与管道
### 9.1 常用写法
| 写法 | 含义 |
| --- | --- |
| `> f` / `>> f` | stdout 覆盖 / 追加 |
| `2> f` | stderr 写入文件 |
| `&> f` / `&>> f` | stdout+stderr 一起覆盖 / 追加（bash 专属） |
| `> f 2>&1` | 先重定向 stdout，再让 stderr 复制 fd 1 |
| `2>&1 > f` | stderr 仍指向原 stdout（终端），只有 stdout 进文件 |
| `>&2` | 把输出临时指向 stderr（打印错误） |
| `< f` / `<> f` | 只读 / 读写打开 |

### 9.2 顺序为什么重要
```bash
cmd > out.log 2>&1      # 正确：fd1 指向文件，fd2 复制 fd1，两者都进文件
cmd 2>&1 > out.log      # 错误：fd2 先复制终端，之后 fd1 才改，错误仍在屏幕
```
`2>&1` 不是「合并」，而是复制「当前」fd 1 的指向；shell 从左到右处理重定向，时机决定结果。
### 9.3 heredoc
```bash
cat > app.conf <<EOF
host=${HOST}
port=${PORT}
EOF
cat <<'EOF'             # 引号包住分隔符：不展开变量、不执行 $()
literal $HOME and $(date)
EOF
```
`<<EOF` 会展开变量与命令替换；写配置模板或含 `$` 的脚本用 `<<'EOF'`。分隔符必须单独一行，`<<-EOF` 允许 Tab 缩进。
### 9.4 管道、tee 与进程替换
```bash
set -o pipefail
grep -q error app.log | tee -a scan.log
echo "${PIPESTATUS[0]} ${PIPESTATUS[1]}"    # 每一环各自的退出码
diff <(sort a.txt) <(sort b.txt)            # 把命令输出当文件
```
默认管道退出码只看最后一环，`set -e` 会被前面的失败骗过；`PIPESTATUS` 必须在下一条命令前读。`<(...)` 生成 `/dev/fd/63`，不落盘，也避免子 shell。

## 10 文本处理配合
### 10.1 grep / awk / sed / xargs
```bash
grep -q 'ERROR' app.log && echo "有错误"       # -q 静默，只看退出码
grep -c 'ERROR' app.log                         # 计数；为 0 时退出码 1
awk -F: '$3 >= 1000 {print $1}' /etc/passwd     # 取列并过滤
awk '{sum += $10} END {print sum}' access.log   # 求和
awk -v limit=80 '$5 + 0 > limit' df.txt         # -v 传外部变量
sed -i.bak 's/old/new/g' file                   # 留 .bak；macOS 必须给后缀
sed -i 's#/usr/local#/opt#g' file               # 内容有 / 就换分隔符
find . -name '*.log' -print0 | xargs -0 -n 1 -P 4 gzip
echo app | xargs -I{} cp {}/conf.yml /backup/{}/
```
`grep -c` 为 0 时退出码是 1，`set -e` 下要 `|| true` 或放进 `if`。`&` 在 sed 里代表整个匹配，要字面量写 `\&`；改系统文件前先 `sed 's/old/new/g' file | diff - file` 看效果。xargs 默认按空白切分，不加 `-0` 就是文件名带空格的经典事故。
### 10.2 文件名带空格的批量处理
```bash
find /data/logs -type f -name '*.log' -print0 |
  while IFS= read -r -d '' f; do
    printf '%s -> %s\n' "$f" "${f%.log}.gz"
    gzip -f -- "$f"
  done
```
四件事一起做：`-print0` + `read -d ''`、`"$f"` 加引号、命令加 `--`、别解析 `ls`。`find … -exec cmd {} +` 也能避免分词，但循环里做复杂逻辑还得用上面这套。

## 11 退出码与错误处理
### 11.1 退出码
| 码 | 含义 |
| --- | --- |
| 0 | 成功 |
| 1 | 一般错误（`false`、grep 无匹配） |
| 2 | 用法错误（参数校验、getopts） |
| 126 / 127 | 找到了但不可执行 / 命令未找到（PATH 不对） |
| 128+n | 被信号 n 杀死：130 Ctrl-C、137 SIGKILL、143 SIGTERM |
| 255 | `exit -1` 或超出范围 |

`$?` 只保留最后一条命令的结果，`echo $?` 读一次就重置，要立刻 `rc=$?` 存下来。
### 11.2 set -e 的坑
- `if cmd`、`cmd || true`、`cmd && x`、`! cmd` 里的失败**不**触发退出。
- 管道默认只看最后一环，必须 `set -o pipefail`。
- `((i++))`、`let i++` 在结果为 0 时返回 1，会误退，写 `i=$((i + 1))`。
- `local x=$(cmd)`、`export x=$(cmd)` 的退出码来自 `local`/`export`（通常 0），失败被吞。
- 函数失败是否退出取决于调用点上下文；别在交互式 shell 里 `set -e`，CI 里要配 `trap` 打日志。
### 11.3 trap、日志与 || exit
```bash
log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*" >&2; }
die() { log "ERROR: $*"; exit 1; }
tmp=$(mktemp -d)
cleanup() { local rc=$?; rm -rf -- "$tmp"; exit "$rc"; }
trap cleanup EXIT
mkdir -p "$dst" || die "创建目录失败：$dst"
cp -a src/. "$dst"/ || exit 1
```
`EXIT` 覆盖正常退出、`set -e` 退出和信号退出，是最可靠的清理点；清理里先保存 `$?`，最后 `exit "$rc"` 保住原退出码。日志写 stderr，避免污染 stdout 的管道数据；`trap 'echo "ERR at $LINENO"' ERR` 可定位失败行。
### 11.4 幂等与并发
```bash
tmp=$(mktemp -d)
exec 9>/var/lock/backup.lock
flock -n 9 || { echo "已有实例在跑" >&2; exit 0; }
mkdir -p "$dst"                            # 已存在不报错
[[ -f "$dst/app.tar.gz" ]] && exit 0       # 已完成就跳过
mv -- "$tmp/app.tar.gz" "$dst/app.tar.gz"  # 原子替换
```
幂等三件事：创建用 `mkdir -p`、删除用 `rm -f`、写入用临时文件 + `mv` 原子替换；`flock -n` 拿不到锁立即退出，防 cron 重叠。

## 12 调试
### 12.1 常用开关
| 命令 / 选项 | 作用 |
| --- | --- |
| `bash -n script.sh` | 只做语法检查，不执行 |
| `bash -x script.sh` | 打印每条命令展开后的样子 |
| `set -x` / `set +x` / `set -v` | 追踪展开后的命令 / 关闭 / 回显原始行（含注释） |
| `shellcheck script.sh` | 静态检查，CI 必装 |

`-x` 输出以 `+` 开头，打印的是展开后的命令，密码、token 会明文出现，生产别常开。
### 12.2 PS4 带行号
```bash
PS4='+ ${BASH_SOURCE##*/}:${LINENO}:${FUNCNAME[0]:-main}: '
set -x
do_something
set +x
```
`BASH_SOURCE` 是当前文件，`LINENO` 行号，`FUNCNAME[0]` 函数名。要写进单独文件：`exec 5>trace.log; BASH_XTRACEFD=5; set -x`。
### 12.3 shellcheck 常见告警
| 编号 | 含义 | 修法 |
| --- | --- | --- |
| SC2086 | 变量未加引号，可能分词 | `"$var"` |
| SC2046 | 命令替换未加引号 | `"$(cmd)"` |
| SC2181 | 用 `$?` 判断而不是直接 if | `if cmd; then` |
| SC2015 | `A && B \|\| C` 不是 if-else | 改写成 if |

本地 `shellcheck -S warning script.sh`，CI 加一步；确需忽略要写原因：`# shellcheck disable=SC2086  # 这里就是要分词`。

## 13 定时任务
### 13.1 cron 五个字段
| 字段 | 范围 | 说明 |
| --- | --- | --- |
| 分 | 0-59 | `*/5` 每 5 分钟 |
| 时 | 0-23 | `9-18` 工作时间 |
| 日 | 1-31 | 与「周」是**或**关系，别同时限制 |
| 月 | 1-12 | `1,7` 一月和七月 |
| 周 | 0-7 | 0 和 7 都是周日 |

`0 3 * * *` 每天 3:00；`*/10 9-18 * * 1-5` 工作日 9-18 点每 10 分钟；`@daily`、`@reboot` 是简写。
### 13.2 crontab 与文件位置
`crontab -e` 编辑当前用户任务，`crontab -l` 列出，`crontab -r` 删除全部（慎用）。`/etc/crontab` 与 `/etc/cron.d/*` 多一个「用户」字段：`0 3 * * * root /opt/backup.sh`；`/etc/cron.{hourly,daily}` 由 run-parts 执行，文件名不能带点。cron 不读 `~/.bashrc`。
### 13.3 环境变量与日志
- `PATH` 通常只有 `/usr/bin:/bin`，调 `/usr/local/bin` 下的命令会 127；脚本开头 `export PATH=...` 或全用绝对路径。
- `HOME`、`LANG` 可能与登录 shell 不同，日期格式、中文排序都会变。
- 命令里的 `%` 要转义成 `\%`，cron 把未转义的 `%` 当换行。
- 日志用 `>> /var/log/x.log 2>&1` 兜底，配 logrotate；脚本内部再 `log()` 带时间戳，例如 `0 3 * * * /opt/backup.sh >> /var/log/backup.log 2>&1`。

排查顺序：手动 `bash -x` 复现 → `crontab -l` 检查行 → `/var/log/syslog` 或 `journalctl -u cron`。
### 13.4 cron vs systemd timer
| 对比 | cron | systemd timer |
| --- | --- | --- |
| 精度 | 分钟级 | 秒级，`OnCalendar`、`OnBootSec` |
| 日志 | 自己重定向 | journald，`journalctl -u x.service` |
| 错过补跑 | 不补 | `Persistent=true` 补一次 |
| 依赖与资源 | 无 | `After=`、`Requires=`、cgroup 限制 |
| 用户级 | `crontab -e` | `systemctl --user`（需 linger） |

`backup.timer` 里写 `OnCalendar=*-*-* 03:00:00`、`Persistent=true`、`RandomizedDelaySec=300`，配一个 `Type=oneshot`、`ExecStart=/opt/backup.sh` 的 `backup.service`；`systemctl enable --now backup.timer` 后用 `systemctl list-timers` 确认下次触发。

## 14 实战脚本
以下脚本都完整可运行，统一 `set -euo pipefail`，路径可用参数或环境变量覆盖后再上线。
### 14.1 日志清理（保留 7 天）
```bash
#!/usr/bin/env bash
set -euo pipefail
dir="${1:-/var/log/app}" days="${2:-7}"
[[ -d "$dir" ]] || { echo "目录不存在：$dir" >&2; exit 1; }
find "$dir" -type f -name '*.log' -mtime "+${days}" -print -delete
find "$dir" -mindepth 1 -type d -empty -delete
```
`-mtime +7` 是「超过 7×24 小时」，与「保留 7 个自然日」略有差异；按日期命名的日志用文件名比较更准。`-delete` 隐含 `-depth`，不能和 `-prune` 混用；上线前先把 `-delete` 换成 `-print` 做 dry-run。
### 14.2 目录备份 + 压缩 + 校验
```bash
#!/usr/bin/env bash
set -euo pipefail
src="${1:?用法: $0 <源目录> [目标目录]}"
dst="${2:-/backup}" keep=7
name="$(basename "$src")-$(date +%Y%m%d-%H%M%S).tar.gz"
mkdir -p "$dst"
tar -czf "$dst/$name.part" -C "$(dirname "$src")" "$(basename "$src")"
mv -- "$dst/$name.part" "$dst/$name"           # 原子替换，断电不留半包
sha256sum "$dst/$name" > "$dst/$name.sha256"
( cd "$dst" && sha256sum -c "$name.sha256" )   # 校验文件里是相对路径
ls -1t "$dst"/*.tar.gz | tail -n +$((keep + 1)) | xargs -r rm -f --
```
先写 `.part` 再 `mv`，避免 cron 重叠或断电留下坏包；校验必须在 `$dst` 里执行；`tail -n +8` 保留最新 7 个，`xargs -r` 在没有旧包时不执行 `rm`。
### 14.3 服务健康检查（curl + 重试 + 告警）
```bash
#!/usr/bin/env bash
set -euo pipefail
url="${1:-http://127.0.0.1:8080/health}"
state=/tmp/health.state webhook="${WEBHOOK:-}"
for i in 1 2 3; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$url" || true)
  [[ "$code" == 200 ]] && { rm -f "$state"; exit 0; }
  echo "第 $i 次失败：HTTP $code" >&2
  sleep 5
done
if [[ -n "$webhook" && ! -f "$state" ]]; then     # 状态文件去重，恢复前不再告警
  curl -sS -m 5 -X POST -d "health check failed: $url" "$webhook" || true
  : > "$state"
fi
exit 1
```
`-w '%{http_code}'` 只取状态码，`|| true` 防 curl 非 0 在 `set -e` 下中断；`--max-time` 必须设，否则服务假死时脚本一起卡住。告警去重靠状态文件，恢复时删掉它。
### 14.4 批量重命名 / 批量替换
```bash
#!/usr/bin/env bash
set -euo pipefail
dir="${1:?目录}" prefix="${2:?前缀}"
n=0
while IFS= read -r -d '' f; do
  mv -- "$f" "$dir/${prefix}-$((++n)).${f##*.}"
done < <(find "$dir" -maxdepth 1 -type f -print0 | sort -z)
```
```bash
#!/usr/bin/env bash
set -euo pipefail
dir="${1:?目录}" old="${2:?旧串}" new="${3:?新串}"
find "$dir" -type f -print0 | while IFS= read -r -d '' f; do
  sed -i.bak "s/${old//\//\\/}/${new//\//\\/}/g" "$f"
  cmp -s "$f" "$f.bak" && rm -f -- "$f.bak" || echo "已改：$f"
done
```
`mv --` 防 `-` 开头；`$((++n))` 先自增再取号；`${old//\//\\/}` 把 `/` 转义为 `\/`，更稳的做法是换分隔符 `s#old#new#g`。`cmp` 判断是否真的替换过，没变就删备份。
### 14.5 磁盘使用率巡检（超过 80% 告警）
```bash
#!/usr/bin/env bash
set -euo pipefail
th="${1:-80}" warn=0
while IFS= read -r line; do
  use="${line%%%*}" mp="${line#* }"
  (( use >= th )) || continue
  warn=1; echo "告警：${mp} 使用率 ${use}%（阈值 ${th}%）" >&2
done < <(df -P -x tmpfs -x devtmpfs -x overlay | awk 'NR > 1 {print $5, $6}')
if (( warn == 0 )); then echo "all below ${th}%"; exit 0; fi
[[ -n "${WEBHOOK:-}" ]] && curl -sS -m 5 -X POST -d "disk usage high" "$WEBHOOK" || true
exit 1
```
`df -P` 保证每个文件系统一行，`-x` 排除内存盘，`awk` 取 Capacity 与挂载点。挂载点含空格时 `$6` 会被截断，这种环境改用 `awk '{print $5, substr($0, index($0,$6))}'` 或直接读 `/proc/mounts`。

## 15 面试问答
### 15.1 `"$@"` 和 `"$*"` 有什么区别？
`"$@"` 展开成多个独立参数，保持每个参数的边界；`"$*"` 用 IFS 首字符把参数拼成一个字符串。转发参数永远用 `"$@"`，判断个数用 `$#`。
### 15.2 `set -e` 有哪些坑？
`if`/`&&`/`||`/`!` 里的失败不退出，管道只看最后一环，`((i++))` 返回 1 会误退，`local x=$(cmd)` 会吞掉失败。所以配 `set -o pipefail` + `trap`，关键命令显式 `|| exit 1`。
### 15.3 `source` 与 `sh script.sh` 有什么区别？
`source` 在当前 shell 执行，变量、函数、`cd`、`umask` 都留在当前会话；`sh`/`bash` 起子进程，只继承 `export` 的变量。`./x.sh` 由 shebang 决定解释器，`sh x.sh` 强制用 dash，bash 扩展会报错。
### 15.4 heredoc 是什么？`<<'EOF'` 与 `<<EOF` 的区别？
heredoc 把一段文本作为 stdin 喂给命令。`<<EOF` 展开变量和 `$()`；`<<'EOF'` 完全原样，适合配置模板或含 `$` 的脚本。分隔符必须单独一行顶格，`<<-` 允许 Tab 缩进。
### 15.5 `[[ ]]` 和 `[ ]` 有什么区别？
`[[ ]]` 是 bash 关键字：不分词、空变量安全、支持 `&&`/`||`/`=~` 和通配符；`[ ]` 是 POSIX 命令，变量要加引号，逻辑用 `-a`/`-o`，`<` 要转义。写 bash 用 `[[ ]]`，兼容 sh 才退回 `[ ]`。
### 15.6 如何用脚本清理僵尸进程？
僵尸已经死了，`kill -9` 无效，它占的是父进程的进程表项。先 `ps -o ppid= -p <pid>` 找父进程，让父进程 `wait`；父进程不处理就重启它，或杀掉它让 init 收养。脚本只做「扫 `ps -eo stat,ppid,pid` 里的 Z → 告警 / 重启父进程」，别直接杀僵尸。
### 15.7 如何写幂等的脚本？
创建用 `mkdir -p`，删除用 `rm -f`，写入用临时文件 + `mv` 原子替换；操作前先检查目标状态（`[[ -f … ]] && exit 0`）；用 `flock` 防并发；不依赖当前目录和「跑了几次」。重复执行结果一致才算幂等。
### 15.8 `2>&1` 为什么顺序很重要？
重定向从左到右处理，`2>&1` 是复制「当前」fd 1 的指向。`> f 2>&1` 两者都进文件；`2>&1 > f` 里 stderr 先绑到终端，之后 stdout 才改，错误仍留在屏幕。
### 15.9 管道里的 `while read` 为什么改不了变量？
管道每一段都在子 shell 执行，循环里的赋值随子 shell 退出而丢失。改成 `while …; done < file` 或用进程替换 `done < <(cmd)`，两者都在当前 shell，变量可见。
### 15.10 如何安全处理带空格或换行的文件名？
全程加引号 `"$f"`；用 `find -print0` + `read -r -d ''` 或 `xargs -0`；`mv`/`rm` 加 `--`。不要 `for f in $(ls)`，也不要把 `ls` 输出当数据源。
### 15.11 `$$`、`$!`、`$?`、`$_` 分别是什么？
`$$` 当前 shell 的 PID（子 shell 里可能不变，真 PID 用 `$BASHPID`）；`$!` 最近一个后台进程的 PID；`$?` 上一条命令的退出码；`$_` 上一条命令的最后一个参数。`$?` 会被下一条命令覆盖，要立即保存。
### 15.12 如何防止脚本并发重复执行？
`exec 9>lockfile; flock -n 9 || exit 0`，拿不到锁立即退出，`flock -w 10` 可以等 10 秒；也可以用 `mkdir` 的原子性做锁。锁文件别放会被清理的 `/tmp`，`flock` 随 fd 关闭自动释放，比手写 PID 文件可靠。
### 15.13 cron 里脚本不执行，怎么排查？
先手动 `bash -x /path/script.sh` 复现；`crontab -l` 确认任务，`/etc/cron.d` 下要检查是否漏了用户字段；重点看 `PATH`、`HOME`、编码、`%` 转义、执行权限与 shebang；最后查 `/var/log/syslog` 或 `journalctl -u cron`。
### 15.14 如何保证脚本失败时清理临时文件？
`tmp=$(mktemp -d)` 后立刻 `trap 'rm -rf -- "$tmp"' EXIT`，`EXIT` 覆盖正常退出、`set -e` 退出和信号退出；再补 `trap … INT TERM`。清理函数先保存 `$?`，最后 `exit "$rc"`，别覆盖原退出码。
### 15.15 shellcheck 报 SC2086 是什么意思？
变量展开没加引号，会分词和做通配，`$var` 含空格就被拆成多个参数。修法是 `"$var"`；确实要分词才保留，并写 `# shellcheck disable=SC2086` 加理由。把 shellcheck 当 CI lint 跑，能提前拦掉大部分引号 bug。
