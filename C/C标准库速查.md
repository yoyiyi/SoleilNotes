# C 标准库速查

> 面向 C11（兼容 C99/C17）：查函数看表格，记用法看代码，面试前刷第 11 章。原型省略 `restrict` 等限定符，示例默认已包含对应头文件；编译用 `gcc -std=c11 -Wall -Wextra -g demo.c -o demo`，用到 `<math.h>` 时在末尾加 `-lm`。

## 1 概览
下表 13 个头文件覆盖日常 90% 的代码。通用规则：成败看返回值（`NULL`/`EOF`/`-1`/非 0），细节看 `errno`，缓冲区大小永远由调用方负责。

| 头文件 | 主要提供 | 一句话用途 |
| --- | --- | --- |
| `stdio.h` | `printf`、`scanf`、`FILE`、`fopen` | 格式化输入输出与文件流 |
| `stdlib.h` | `malloc`、`qsort`、`strtol`、`exit` | 内存、转换、排序、进程与环境的杂货铺 |
| `string.h` | `strlen`、`strcpy`、`memcpy` | 以 `'\0'` 结尾的字符串与裸内存块操作 |
| `ctype.h` | `isalpha`、`toupper` | 单字节字符分类与大小写转换（受 locale 影响） |
| `math.h` | `sqrt`、`pow`、`fabs` | 浮点数学函数，链接时通常要加 `-lm` |
| `time.h` | `time`、`localtime`、`strftime` | 日历时间、CPU 时间与格式化 |
| `stdint.h` | `int32_t`、`uint64_t`、`INT64_MAX` | 定长与指针宽度整数，跨平台首选 |
| `stdbool.h` | `bool`、`true`、`false` | 布尔类型（C23 起成为关键字） |
| `stddef.h` | `size_t`、`ptrdiff_t`、`NULL`、`offsetof` | 大小、指针差、空指针与成员偏移 |
| `limits.h` | `INT_MAX`、`CHAR_BIT` | 各整数类型的实现相关极值 |
| `assert.h` | `assert` | 调试期断言，`NDEBUG` 下消失 |
| `errno.h` | `errno`、`EDOM`、`ERANGE` | 库函数失败的详细错误码 |
| `stdarg.h` | `va_list`、`va_start`、`va_arg` | 可变参数函数的取参工具 |

## 2 stdio.h
`stdin`/`stdout`/`stderr` 在启动时自动打开，`stderr` 不带缓冲。**返回 `EOF` 或负值表示失败，读写项数要和请求数比较**。

### 2.1 格式化输出
| 原型 | 说明 | 常见坑 |
| --- | --- | --- |
| `int printf(const char *fmt, ...)` | 输出到 `stdout`，返回输出字符数 | 格式符与参数类型不匹配是 UB，`printf("%d", 3.14)` 不报错但结果荒谬 |
| `int fprintf(FILE *fp, const char *fmt, ...)` | 输出到指定流，日志写 `stderr` | 忘记 `\n` 又不 `fflush`，重定向到文件时可能长时间看不到输出 |
| `int snprintf(char *s, size_t n, const char *fmt, ...)` | 最多写 `n-1` 字节并补 `'\0'`，返回**想要写**的长度 | 返回值 `>= n` 表示截断，不是实际写入长度；`n == 0` 可用来预算长度 |
| `int sprintf(char *s, const char *fmt, ...)` | 不检查目标大小，返回写入长度 | **禁止**用于外部输入，风险等同 `strcpy` 溢出；C11 的 `sprintf_s` 不是标准 |

### 2.2 格式化输入
| 原型 | 说明 | 常见坑 |
| --- | --- | --- |
| `int scanf(const char *fmt, ...)` | 从 `stdin` 解析，返回成功赋值的项数 | 必须传地址；`%s` 不限宽会溢出，写 `%31s`；返回 `0` 是匹配失败，`EOF` 是输入结束 |
| `int sscanf(const char *s, const char *fmt, ...)` | 从字符串解析，常用于拆 `key=value` | 同样要检查返回值；`%d` 遇到非数字立即停止，不报错 |

判断写法是 `if (scanf("%d %31s", &n, name) != 2) { /* 输入不合法 */ }`，不要只写 `if (scanf(...))`，因为 `EOF` 也是非 0。

### 2.3 文件流
| 原型 | 说明 | 常见坑 |
| --- | --- | --- |
| `FILE *fopen(const char *path, const char *mode)` | 打开文件，模式 `r/w/a` 可加 `b`、`+` | 失败返回 `NULL`，必须判断；`"w"` 会截断已有文件 |
| `int fclose(FILE *fp)` | 关闭流，成功返回 0 | 不关闭会丢缓冲区数据、泄漏句柄；`fclose(NULL)` 是 UB |
| `size_t fread(void *ptr, size_t size, size_t nmemb, FILE *fp)` | 读元素，返回实际读到的元素个数 | 短读要用 `feof`/`ferror` 区分「读完」还是「出错」 |
| `size_t fwrite(const void *ptr, size_t size, size_t nmemb, FILE *fp)` | 写元素，返回实际写入的元素个数 | 返回值小于 `nmemb` 说明出错，磁盘满时最常见 |
| `int fseek(FILE *fp, long offset, int whence)` | 定位，`whence` 取 `SEEK_SET/CUR/END` | 文本流只应使用 `offset == 0` 或 `ftell` 的返回值 |
| `long ftell(FILE *fp)` | 返回当前位置（字节），失败返回 `-1L` | 大文件可能超出 `long`，用 `fseeko/ftello`（POSIX） |
| `void rewind(FILE *fp)` | 回到开头并清除错误标志 | 无返回值，无法报告失败 |
| `int fflush(FILE *fp)` | 把输出缓冲区刷到文件 | `fflush(stdin)` 是 UB（MSVC 扩展）；传 `NULL` 刷所有输出流 |

`FILE *fp = fopen("a.txt", "r"); if (fp == NULL) { perror("fopen"); return 1; }` 是最小打开模板；`fgets` 循环见 2.4。用 `fseek(fp, 0, SEEK_END); size = ftell(fp); rewind(fp);` 可以取文件长度后回到开头；`fread`/`fwrite` 用「元素个数 × 元素大小」读写结构体数组最方便。

### 2.4 行/字符输入输出与文件操作
| 原型 | 说明 | 常见坑 |
| --- | --- | --- |
| `char *fgets(char *s, int n, FILE *fp)` | 最多读 `n-1` 个字符，保留 `'\n'`，总是补 `'\0'` | 行太长会分多次返回；EOF 或出错返回 `NULL` |
| `int fputs(const char *s, FILE *fp)` | 写字符串，不追加换行（区别于 `puts`） | 返回非负值即成功，具体值不要依赖 |
| `int getchar(void)` | 从 `stdin` 读一个字符，返回 `unsigned char` 值或 `EOF` | 必须用 `int` 接收，用 `char` 无法区分 `EOF` |
| `int putchar(int c)` | 向 `stdout` 写一个字符 | 成功返回写入的字符，失败返回 `EOF` |
| `void perror(const char *s)` | 把 `errno` 描述打印到 `stderr`，格式 `s: 描述` | 只应在失败后立刻调用，中间调用可能改写 `errno` |
| `int remove(const char *path)` | 删除文件，成功返回 0 | POSIX 下不能删非空目录；失败返回非 0 |
| `int rename(const char *old, const char *new)` | 改名/移动，成功返回 0 | 跨文件系统失败（`EXDEV`）；目标存在时行为由实现定义 |

`fgets` 保留换行，去掉它用 `line[strcspn(line, "\n")] = '\0';`（需要 `<string.h>`）；读二进制只能用 `fread`，`fgets` 遇 `0x00` 或 `0x1A` 会提前结束。

### 2.5 printf 格式符与修饰
| 格式符 | 对应类型 | 示例输出 |
| --- | --- | --- |
| `%d` | `int` | `-42` |
| `%u` | `unsigned int` | `4294967295` |
| `%ld` / `%lld` | `long` / `long long` | `1234567890123` |
| `%zu` | `size_t` | `8` |
| `%x` / `%X` | 无符号十六进制（小/大写） | `ff` / `FF` |
| `%o` | 无符号八进制 | `377` |
| `%f` | `double`，定点 6 位小数；`%lf` 等价 | `3.140000` |
| `%e` / `%E` | 科学计数法 | `3.140000e+00` |
| `%g` / `%G` | 自动选 `%f`/`%e` 中较短者，去掉尾随 0 | `3.14` |
| `%c` | `int`，按字符输出 | `A` |
| `%s` | `char *`，到 `'\0'` 为止 | `hello` |
| `%p` | `void *`，实现相关（glibc 为 `0x...`） | `0x7ffd...` |
| `%%` | 输出一个 `%` | `%` |

修饰顺序 `%[标志][宽度][.精度][长度]转换符`：`-` 左对齐、`+` 强制符号、`0` 补零、`#` 加 `0x`/`0` 前缀、空格补正号；宽度与精度可写 `*` 从参数取；长度修饰 `hh`、`h`、`l`、`ll`、`z`（`size_t`）、`t`（`ptrdiff_t`）、`j`（`intmax_t`）。

`printf("%5d|%-5d|%05d\n", 42, 42, 42)` 输出 `"   42|42   |00042"`；`printf("%8.3f|%-8.2f|\n", 3.14159, 2.5)` 输出 `"   3.142|2.50    |"`；`%*d`/`%.*s` 的宽度和精度从参数取。

1. `scanf` 的浮点规则与 `printf` 不同：读 `double` 必须 `%lf`，读 `float` 写 `%f`。
2. `%d` 打印 `long long`、`%zu` 写成 `%u` 在 64 位上是典型翻车点，`-Wall` 里的 `-Wformat` 能抓到。

## 3 stdlib.h
### 3.1 动态内存
| 原型 | 说明 | 常见坑 |
| --- | --- | --- |
| `void *malloc(size_t size)` | 分配 `size` 字节，内容未初始化 | 失败返回 `NULL` 必须判断；`malloc(0)` 的返回值由实现定义 |
| `void *calloc(size_t nmemb, size_t size)` | 分配并清零，内部检查乘法溢出 | 清零有成本；大块内存可能直接拿到零页 |
| `void *realloc(void *ptr, size_t size)` | 调整块大小，保留 `min(旧, 新)` 字节，可能搬移 | 失败返回 `NULL` 且原块仍有效，必须 `tmp = realloc(p, n); if (tmp) p = tmp;` |
| `void free(void *ptr)` | 释放 `malloc/calloc/realloc` 返回的块 | `free(NULL)` 安全；重复释放、释放栈地址、释放块中间指针都是 UB |

`malloc` 的经典写法是 `int *p = malloc(10 * sizeof *p); if (p == NULL) { perror("malloc"); return 1; }`；释放后 `p = NULL` 防悬垂指针；`realloc(p, 0)` 的行为由实现定义，可移植写法是 `free(p)`。

### 3.2 字符串转数字
| 原型 | 说明 | 常见坑 |
| --- | --- | --- |
| `int atoi(const char *s)` | 转 `int`，跳过前导空白 | 无法区分 `"abc"` 和 `"0"`（都返回 0）；溢出是 UB |
| `long atol(const char *s)` | 转 `long` | 同样没有错误检测，不要用于不可信输入 |
| `double atof(const char *s)` | 转 `double` | 失败返回 0.0，无法与真正的 0 区分 |
| `long strtol(const char *s, char **endptr, int base)` | 转 `long`，`base` 取 2~36，0 表示自动识别 `0x`/`0` 前缀 | 溢出返回 `LONG_MAX/LONG_MIN` 并置 `errno = ERANGE`；`endptr == s` 表示没解析出数字 |
| `unsigned long strtoul(const char *s, char **endptr, int base)` | 转 `unsigned long` | 负号被静默回绕成巨大正数（`"-1"` → `ULONG_MAX`） |
| `double strtod(const char *s, char **endptr)` | 转 `double`，支持 `inf`/`nan`/十六进制浮点 | 上溢 `ERANGE` 返回 `HUGE_VAL`，下溢返回接近 0 的值 |

`strtol` 的完整检查：`errno = 0; v = strtol(s, &end, 10); if (end == s) 没数字; else if (errno == ERANGE) 溢出; else 成功;`，`end` 还能继续解析剩余部分。

### 3.3 排序与查找
| 原型 | 说明 | 常见坑 |
| --- | --- | --- |
| `void qsort(void *base, size_t nmemb, size_t size, int (*cmp)(const void *, const void *))` | 快速排序，原地排序 | **不稳定**，相等元素顺序不定；比较函数必须满足全序 |
| `void *bsearch(const void *key, const void *base, size_t nmemb, size_t size, int (*cmp)(const void *, const void *))` | 二分查找，命中返回元素指针，否则 `NULL` | 必须先按**同一个**比较函数排序；`key` 类型要和比较函数约定一致 |

```c
#include <stdio.h>
#include <stdlib.h>
typedef struct { int id; char name[16]; double score; } Student;
/* 升序：不要写 return a - b，差值可能溢出 int */
static int cmp_int(const void *a, const void *b)
{
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);              /* 只返回 -1 / 0 / 1 */
}

/* 先按分数降序，分数相同再按 id 升序 */
static int cmp_student(const void *a, const void *b)
{
    const Student *x = a, *y = b;
    if (x->score != y->score) {
        return (x->score < y->score) - (x->score > y->score);
    }
    return (x->id > y->id) - (x->id < y->id);
}

int main(void)
{
    int a[] = {5, -2, 9, 0};
    Student s[] = {{3, "tom", 90.0}, {1, "amy", 95.5}, {2, "bob", 90.0}};
    size_t n = sizeof s / sizeof s[0];
    qsort(a, sizeof a / sizeof a[0], sizeof a[0], cmp_int);
    qsort(s, n, sizeof s[0], cmp_student);
    for (size_t i = 0; i < n; i++) {
        printf("%d %-4s %.1f\n", s[i].id, s[i].name, s[i].score);
    }
    int key = 9;
    int *hit = bsearch(&key, a, 4, sizeof a[0], cmp_int);   /* 数组必须已排序 */
    printf("%s\n", hit != NULL ? "found" : "missing");
    return 0;
}
```

字符串比较可直接 `return strcmp(x->name, y->name);`，`strcmp` 的返回值符号正是 `qsort` 需要的；比较结构体不要用 `memcmp`，填充字节的内容未定义。

### 3.4 随机数、绝对值与进程控制
| 原型 | 说明 | 常见坑 |
| --- | --- | --- |
| `int rand(void)` | 返回 `0 ~ RAND_MAX` 的伪随机数 | 质量差、周期短，不能用于加密；`rand() % n` 有轻微偏差 |
| `void srand(unsigned int seed)` | 设置随机种子 | 不播种等价 `srand(1)`，每次运行序列相同；调试时反而应固定种子 |
| `int abs(int n)` / `long labs(long)` | 取绝对值 | `abs(INT_MIN)` 溢出是 UB，先判边界 |
| `void exit(int status)` | 正常终止：刷新并关闭流、执行 `atexit`、返回状态码 | POSIX 上 `status` 只保留低 8 位 |
| `void abort(void)` | 异常终止：不刷新流、不执行 `atexit`，产生 `SIGABRT` | 用于不可恢复错误，缓冲区里的日志会丢 |
| `int atexit(void (*func)(void))` | 注册退出处理函数，成功返回 0 | 执行顺序与注册顺序相反（LIFO）；标准保证至少 32 个 |
| `int system(const char *cmd)` | 交给 shell 执行，`cmd` 为 `NULL` 时查询是否有 shell | 返回 `wait` 状态不是退出码，POSIX 要用 `WEXITSTATUS`；有命令注入风险 |
| `char *getenv(const char *name)` | 取环境变量，不存在返回 `NULL` | 返回内部指针，不能 `free` 也不能改；修改用 `setenv`（POSIX） |

`exit` 会刷新流、执行 `atexit`；`abort` 两者都不做，所以崩溃前想留日志必须先 `fflush`。

## 4 string.h
### 4.1 长度与复制
| 原型 | 返回 | 常见坑 |
| --- | --- | --- |
| `size_t strlen(const char *s)` | 长度，不含 `'\0'` | O(n)，循环里别反复调用；返回值无符号，`strlen(s) - 1 >= 0` 恒真 |
| `char *strcpy(char *dst, const char *src)` | `dst` | 不检查目标大小；`dst` 与 `src` 重叠是 UB；必须自己保证空间够 |
| `char *strncpy(char *dst, const char *src, size_t n)` | `dst` | 恰好写 `n` 字节：`src` 短则补 0，`src` 不短于 `n` 时**没有 `'\0'`** |
| `char *strcat(char *dst, const char *src)` | `dst` | 每次重找 `dst` 末尾，循环拼接是 O(n²)；不检查容量 |
| `char *strncat(char *dst, const char *src, size_t n)` | `dst` | 最多追加 `n` 个字符且**总是补 `'\0'`**，需要 `strlen(dst) + n + 1` 空间 |

`strncpy(dst, "abcdefgh", 8)` 写满 8 字节但没有 `'\0'`，此时 `dst` 只是字符数组；安全复制写 `snprintf(dst, sizeof dst, "%s", src)`。`strncpy` 的设计目标是定长字段（如早期 UNIX 目录项），不是「安全版 `strcpy`」。

### 4.2 比较、查找与分词
| 原型 | 返回 | 常见坑 |
| --- | --- | --- |
| `int strcmp(const char *a, const char *b)` | 小于/等于/大于分别返回负/0/正 | 按 `unsigned char` 比较，与 locale 无关；只判断正负，不要依赖具体差值 |
| `int strncmp(const char *a, const char *b, size_t n)` | 同上，最多比 `n` 字节 | 比较到 `'\0'` 即停止；判断前缀相等用 `== 0` |
| `char *strchr(const char *s, int c)` | 首次出现位置，找不到 `NULL` | 查 `'\0'` 合法，返回指向结尾的指针；`c` 按 `char` 截断 |
| `char *strrchr(const char *s, int c)` | 最后一次出现位置 | 常用于取文件名：`strrchr(path, '/')` |
| `char *strstr(const char *haystack, const char *needle)` | 子串首次出现位置 | `needle` 为空返回 `haystack`；找不到返回 `NULL`，直接 `%s` 打印会崩 |
| `char *strtok(char *s, const char *delim)` | 下一个记号，没有则 `NULL` | 就地写 `'\0'` 破坏原串；内部静态状态**不可重入**、不能嵌套分词 |
| `char *strerror(int errnum)` | 错误码描述 | 可能返回静态缓冲区，多线程用 `strerror_r`（POSIX）；未知码返回 `"Unknown error n"` |

`strtok` 的循环是 `for (tok = strtok(text, ";"); tok != NULL; tok = strtok(NULL, ";"))`：第一次传原串，之后传 `NULL`；连续分隔符被跳过，末尾分隔符不产生空记号。可重入版本是 POSIX 的 `strtok_r(text, ";", &save)`。

### 4.3 内存块操作
| 原型 | 返回 | 常见坑 |
| --- | --- | --- |
| `void *memcpy(void *dst, const void *src, size_t n)` | `dst` | 不处理重叠，重叠时 UB；编译器可能内联展开，出错更难查 |
| `void *memmove(void *dst, const void *src, size_t n)` | `dst` | 处理重叠（必要时反向拷），比 `memcpy` 略慢 |
| `void *memset(void *s, int c, size_t n)` | `s` | 按**字节**填充，`memset(a, 1, sizeof a)` 得到 `0x01010101` 而不是 1 |
| `int memcmp(const void *a, const void *b, size_t n)` | 同 `strcmp` 的正负 | 按 `unsigned char` 比较，不因 `'\0'` 停止；结构体填充字节未定义，不能用来判等 |

`memmove(buf + 2, buf, 5)` 可以把 `"hello"` 变成 `"hehello"`；`memset(a, 0, sizeof a)` 只对 0 可靠，要初始化成别的值只能循环赋值。

## 5 ctype.h
| 原型 | 说明 | 坑/示例 |
| --- | --- | --- |
| `int isalpha(int c)` | 是否为字母（`A-Z`/`a-z`，locale 下可能更多） | 写 `isalpha((unsigned char)c)`，直接传 `char` 遇负值是 UB |
| `int isdigit(int c)` | 是否为十进制数字 `0-9` | 只认 ASCII 数字，全角 `５` 返回 0 |
| `int isalnum(int c)` | 是否为字母或数字 | 等价于 `isalpha` 或 `isdigit` 为真，只求值一次参数 |
| `int isspace(int c)` | 是否为空白：空格、`\t`、`\n`、`\v`、`\f`、`\r` | 不含全角空格；`scanf("%s")` 跳过空白，读行要用 `fgets` |
| `int isupper(int c)` / `int islower(int c)` | 是否为大写/小写字母 | 返回非 0 即真，不要和 1 比较 |
| `int toupper(int c)` / `int tolower(int c)` | 转换大小写，不可转换时原样返回 | 参数同样要能表示为 `unsigned char`；返回值是 `int` |

1. 参数类型是 `int`，值必须是 `unsigned char` 能表示的值或 `EOF`；`char` 在 x86 上有符号，`isalpha((char)0xE4)` 传入负值会越界查表，是 UB。标准写法 `isalpha((unsigned char)c)`。
2. 返回值只保证「非 0 为真、0 为假」，不要和 1 比较。

## 6 math.h
| 原型 | 说明 | 常见坑 |
| --- | --- | --- |
| `double sqrt(double x)` | 平方根 | `x < 0` 返回 `NaN` 并置 `errno = EDOM`，不报错 |
| `double pow(double x, double y)` | 幂运算 | 负数底数配非整数指数返回 `NaN`；比循环慢 |
| `double fabs(double x)` | 浮点绝对值 | 整数取绝对值用 `abs/labs`，`fabs` 返回 `double` |
| `double ceil(double x)` / `double floor(double x)` | 向上/向下取整 | 返回仍是浮点；转 `int` 前确认范围 |
| `double round(double x)` | 四舍五入，半数远离 0 | 与 `rint`（默认银行家舍入）不同：`round(2.5)=3`，`rint(2.5)=2` |
| `double fmod(double x, double y)` | 浮点取余 | 结果符号跟随 `x`；`y == 0` 返回 `NaN` |

1. **链接坑**：gcc 下必须 `gcc calc.c -lm`，`-lm` 放在源文件/目标文件**之后**，否则静态链接报 `undefined reference to 'sqrt'`；C++ 的 `<cmath>` 通常自动处理。
2. `M_PI` 不是标准宏（POSIX 扩展），可移植写法是自己定义 `PI`；浮点判等写 `fabs(a - b) < 1e-9`，`float` 用 `1e-6f`。

## 7 time.h
| 原型 | 说明 | 常见坑 |
| --- | --- | --- |
| `time_t time(time_t *tloc)` | 当前日历时间（epoch 起的秒），失败返回 `(time_t)-1` | 精度只到秒；`time_t` 宽度由实现决定，打印先转 `long long` |
| `struct tm *localtime(const time_t *t)` | 转为本地时间 | 返回**静态缓冲区**，不可重入；多线程用 `localtime_r`（POSIX） |
| `struct tm *gmtime(const time_t *t)` | 转为 UTC 时间 | 同样的静态缓冲区问题，不要把返回指针存起来跨调用使用 |
| `size_t strftime(char *s, size_t max, const char *fmt, const struct tm *tm)` | 按格式写时间字符串 | 返回写入字节数（不含 `'\0'`）；返回 0 表示结果为空或缓冲区不够 |
| `clock_t clock(void)` | 进程消耗的 CPU 时间，单位 `CLOCKS_PER_SEC` | 不是墙钟时间；测耗时优先 `clock_gettime(CLOCK_MONOTONIC)`（POSIX） |
| `double difftime(time_t end, time_t begin)` | 两个时间的秒差 | 返回 `double`；不要直接对 `time_t` 做减法（可能是无符号） |

`struct tm` 字段最容易记错：`tm_year` 是「年份 - 1900」，`tm_mon` 是 0~11，`tm_mday` 是 1~31，`tm_wday` 0 表示周日，`tm_yday` 0~365，`tm_isdst` 表示夏令时。

```c
#include <stdio.h>
#include <time.h>
int main(void)
{
    time_t now = time(NULL);
    struct tm *lt = localtime(&now);       /* 非线程安全，多线程用 localtime_r */
    char buf[64];
    if (now == (time_t)-1 || lt == NULL) {
        perror("time");
        return 1;
    }
    strftime(buf, sizeof buf, "%Y-%m-%d %H:%M:%S", lt);
    printf("%s (wday=%d)\n", buf, lt->tm_wday);
    struct tm utc = *gmtime(&now);         /* 先复制，别改库的静态缓冲区 */
    printf("UTC: %04d-%02d-%02d\n", utc.tm_year + 1900, utc.tm_mon + 1, utc.tm_mday);
    printf("elapsed=%.0fs\n", difftime(time(NULL), now));
    return 0;
}
```

常用格式：`%Y` 四位年、`%m` 月、`%d` 日、`%H:%M:%S`、`%F`=`%Y-%m-%d`、`%T`=`%H:%M:%S`、`%a/%A` 星期缩写/全称、`%j` 年内第几天、`%p` AM/PM、`%z` 时区偏移、`%Z` 时区名、`%%` 百分号。

## 8 stdint.h / stdbool.h / stddef.h / limits.h
### 8.1 stdint.h：定长整型
| 类型 | 含义 |
| --- | --- |
| `int8_t` / `uint8_t` … `int64_t` / `uint64_t` | 恰好 8/16/32/64 位，没有对应宽度时该类型不存在 |
| `intptr_t` / `uintptr_t` | 能装下指针的整数，用于指针与整数互转 |
| `intmax_t` / `uintmax_t` | 编译器支持的最大宽度整数 |
| `INT32_MAX`、`UINT64_MAX`、`INT64_C(123)` | 极值宏与常量构造宏 |
| `PRId64`、`PRIu32`（在 `inttypes.h`） | 配合 `printf` 打印定长整型 |

`long` 在 64 位 Windows（LLP64）上仍是 32 位，所以 `int64_t` 一定用 `printf("%" PRId64 "\n", v)` 打印，而不是 `%ld`。

### 8.2 stdbool.h：布尔类型
`bool` 展开为 `_Bool`，`true`/`false` 展开为 1/0，任何非 0 值赋给 `bool` 都会归一化为 1。C23 起三者是关键字，头文件保留以兼容旧代码；`sizeof(bool)` 通常为 1，`bool ok = 42;` 得到 `1`。

### 8.3 stddef.h：大小、偏移与空指针
| 名字 | 说明 |
| --- | --- |
| `size_t` | `sizeof` 的结果类型，无符号；`printf` 用 `%zu` |
| `ptrdiff_t` | 两个指针相减的结果类型，有符号 |
| `NULL` | 空指针常量，可能是 `0` 或 `(void *)0`，不要当整数用 |
| `offsetof(type, member)` | 成员在结构体中的字节偏移，返回 `size_t` |
| `wchar_t` / `max_align_t` | 宽字符类型 / 最大对齐类型 |

`offsetof(struct packet, len)` 常用于序列化时定位字段：`struct { uint16_t type; uint32_t len; }` 中 `len` 的偏移通常是 4（对齐填充）。

### 8.4 limits.h：整数极值
| 宏 | 典型值 | 说明 |
| --- | --- | --- |
| `CHAR_BIT` | 8 | 一个字节的位数 |
| `SCHAR_MIN` / `SCHAR_MAX` | -128 / 127 | 有符号 `char` |
| `UCHAR_MAX` | 255 | 无符号 `char` |
| `SHRT_MIN` / `SHRT_MAX` | -32768 / 32767 | `short` |
| `INT_MIN` / `INT_MAX` | -2147483648 / 2147483647 | `int`（至少 16 位） |
| `UINT_MAX` | 4294967295 | `unsigned int` |
| `LONG_MIN` / `LONG_MAX` | 32 位：±21 亿；64 位 Linux：±9.2e18 | Windows 64 位仍是 32 位 |
| `LLONG_MIN` / `LLONG_MAX` | ±9.2e18 | 至少 64 位 |
| `SIZE_MAX`（`stdint.h`） | 2⁶⁴-1 | `size_t` 最大值 |

## 9 assert.h 与 errno.h
### 9.1 assert：抓不该发生的错误
`void assert(scalar expression)` 是宏：表达式为假时向 `stderr` 打印文件、行号、函数和表达式，然后调用 `abort()`。它用来抓**编程错误**（不变量被破坏），不要用来校验用户输入；典型用法是函数入口 `assert(b != 0);`。

1. 定义 `NDEBUG`（编译加 `-DNDEBUG`）后 `assert` 展开为空，release 版本失效。
2. 所以不要在 `assert` 里写有副作用的表达式：`assert(fp = fopen(...))` 在 release 下连赋值都不执行。
3. 编译期断言用 `_Static_assert`（C11）或 C23 的 `static_assert`，适合检查类型大小。

### 9.2 errno：失败的细节
`errno` 是宏，展开为可修改的左值（通常是线程局部变量）。**成功时不会清零**，所以要先 `errno = 0`，失败后再读；只有文档声明会设置 `errno` 的函数才有意义。

| 错误码 | 含义 | 典型来源 |
| --- | --- | --- |
| `EDOM` | 数学域错误 | `sqrt(-1)`、`log(0)` |
| `ERANGE` | 结果超出范围 | `strtol` 溢出、`strtod` 上溢 |
| `ENOMEM` | 内存不足 | `malloc`、`realloc` |
| `EINVAL` | 参数非法 | `fseek` 非法 `whence` |
| `ENOENT` | 文件不存在 | `fopen` 读不存在的文件 |
| `EACCES` | 权限不足 | `fopen` 无读权限 |

```c
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void)
{
    errno = 0;
    long v = strtol("99999999999999999999", NULL, 10);
    if (errno == ERANGE) {
        fprintf(stderr, "overflow: %s\n", strerror(errno));
        perror("strtol");
    }
    printf("v=%ld\n", v);
    return 0;
}
```

`perror("msg")` 输出 `msg: 描述`，`strerror(errno)` 返回描述字符串，两者都依赖「失败后立刻读取 `errno`」，中间插入的库调用可能把它改掉。

## 10 stdarg.h
四个要素：`va_list` 保存取参状态，`va_start` 绑定最后一个固定参数，`va_arg` 按类型取下一个参数，`va_end` 清理；需要复制状态时用 `va_copy`（C99），复制后两个 `va_list` 都要 `va_end`。

```c
#include <stdarg.h>
#include <stdio.h>
int sum(int count, ...)          /* 调用方必须保证个数和类型正确 */
{
    va_list ap;
    int total = 0;

    va_start(ap, count);
    for (int i = 0; i < count; i++) {
        total += va_arg(ap, int);   /* 不能写 char/short/float：默认提升后是 int/double */
    }
    va_end(ap);
    return total;
}

int main(void)
{
    printf("%d\n", sum(3, 1, 2, 3));
    return 0;
}
```

1. 默认实参提升：`char`/`short` 提升为 `int`，`float` 提升为 `double`，所以 `va_arg(ap, char)`、`va_arg(ap, float)` 都是错的。
2. 可变参数没有类型检查，个数和类型完全靠格式串或约定，格式串与参数不匹配是经典崩溃来源。
3. 不要对同一个 `va_list` 重复 `va_start` 而不 `va_end`；想把可变参数转给 `vprintf`/`vsnprintf` 时直接传当前 `va_list`，用完照样 `va_end`。

## 11 常见笔试题
### 11.1 手写五个标准库函数
```c
#include <stddef.h>
size_t my_strlen(const char *s)
{
    const char *p = s;
    while (*p != '\0') {
        p++;
    }
    return (size_t)(p - s);
}

char *my_strcpy(char *dst, const char *src)
{
    char *ret = dst;                /* 返回 dst 以支持链式调用 */
    while ((*dst++ = *src++) != '\0') {
        ;                            /* 连 '\0' 一起拷 */
    }
    return ret;
}

void *my_memcpy(void *dst, const void *src, size_t n)
{
    unsigned char *d = dst;
    const unsigned char *s = src;
    while (n-- > 0) {
        *d++ = *s++;                 /* 按字节，不处理重叠 */
    }
    return dst;
}
```

要点：`my_strlen` 返回 `size_t`、不计 `'\0'`；`my_strcpy` 必须拷 `'\0'` 并返回 `dst`，重叠场景用 `memmove`；`my_memcpy` 按 `unsigned char` 逐字节拷，`n == 0` 时不碰指针。

```c
#include <limits.h>
int my_atoi(const char *s)
{
    int sign = 1;
    long v = 0, limit;
    while (*s == ' ' || (*s >= '\t' && *s <= '\r')) {
        s++;                                  /* 跳过前导空白 */
    }
    if (*s == '+' || *s == '-') {
        sign = (*s++ == '-') ? -1 : 1;
    }
    if (*s < '0' || *s > '9') {
        return 0;                             /* 无数字可转 */
    }
    limit = (sign > 0) ? INT_MAX : (long)INT_MAX + 1;
    while (*s >= '0' && *s <= '9') {
        int d = *s++ - '0';
        if (v > (limit - d) / 10) {           /* 先判断再乘，避免溢出 */
            return sign > 0 ? INT_MAX : INT_MIN;
        }
        v = v * 10 + d;
    }
    return (int)(sign * v);
}

/* 支持 INT_MIN；返回指向末尾 '\0' 的指针 */
char *my_itoa(int value, char *buf)
{
    char tmp[12];                             /* 32 位 int 最多 10 位 + 符号 */
    int i = 0;
    unsigned int u = (value < 0) ? 0u - (unsigned int)value : (unsigned int)value;
    char *p = buf;
    do {
        tmp[i++] = (char)('0' + u % 10);
        u /= 10;
    } while (u != 0);
    if (value < 0) {
        *p++ = '-';
    }
    while (i > 0) {
        *p++ = tmp[--i];                      /* 逆序输出 */
    }
    *p = '\0';
    return p;
}
```

`atoi` 的三个考点：跳过空白、处理正负号、溢出保护；`itoa` 不是标准函数（标准只有 `sprintf`/`snprintf`），手写时用 `unsigned` 规避 `INT_MIN` 取负溢出。

### 11.2 五个标准库陷阱
1. **`snprintf` 的返回值是什么？**
   返回「格式化结果应有的长度」，**不含** `'\0'`，不是实际写入长度。返回值 `>= n` 表示被截断，此时缓冲区仍是合法字符串。循环拼接的正确写法：

```c
size_t off = 0;
int n = snprintf(buf + off, sizeof buf - off, "%s", s);
if (n < 0 || (size_t)n >= sizeof buf - off) {
    /* 出错或被截断，不要再前移 off */
} else {
    off += (size_t)n;
}
```

2. **`memcpy` 源和目标重叠会怎样？**
   未定义行为。glibc 按块拷贝，可能得到「部分正确」的结果，看起来像能用；要支持重叠必须用 `memmove`，或自己比较地址决定拷贝方向。另外 `memcpy(dst, src, 0)` 传 `NULL` 也是 UB（标准要求指针有效），虽然实践上不崩。

3. **`qsort` 比较函数写 `return a - b;` 有什么问题？**
   两个 `int` 相减可能溢出（如 `INT_MIN - INT_MAX`），有符号溢出是 UB，比较结果可能反号导致排序错乱；若先算 `long` 差值再隐式转 `int` 还会截断。安全写法是 `(a > b) - (a < b)`，只产生 -1/0/1。

4. **`strncpy` 能当安全版 `strcpy` 用吗？**
   不能。`src` 长度 ≥ `n` 时它不补 `'\0'`，得到的是「字符数组」不是字符串；`src` 较短时又把剩余字节全部补 0，代价高。安全复制用 `snprintf(dst, sizeof dst, "%s", src)`，或非标准的 `strlcpy`。

5. **`for (char c = getchar(); c != EOF; ...)` 错在哪？**
   `getchar` 返回 `int`（0~255 或 `EOF = -1`）。`char` 若为有符号 8 位，读到字节 `0xFF` 会变成 -1，与 `EOF` 相等而提前结束；若为无符号，`EOF` 永远比较不到，变成死循环。正确写法 `int c; while ((c = getchar()) != EOF)`。同理 `strlen(s) < 0` 恒为假，因为 `size_t` 是无符号的。

## 参考
- ISO/IEC 9899:2018（C17）标准草案 N2176，第 7 章「Library」。
- cppreference：<https://en.cppreference.com/w/c>。
- 本仓库 [C 与 Linux 学习路线](000.目录.md) 及 `_source_C.md` 第 6、7、10 章有字符串、内存与文件 IO 的展开讲解。
