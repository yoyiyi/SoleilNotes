## 1 C 标准演进
C 语言由 ANSI 起头制定标准，之后交给 ISO 维护。面试常问「C99 加了什么」「`__STDC_VERSION__` 是多少」，以及某个特性在目标编译器上到底能不能用。
### 1.1 从 C89 到 C23：一张表
| 标准 | 发布 | 标准号 | 关键变化 | `__STDC_VERSION__` |
| --- | --- | --- | --- | --- |
| C89/C90 | 1989/1990 | ANSI X3.159-1989、ISO/IEC 9899:1990 | 首个标准：函数原型、`void *`、`const`/`volatile` | 未定义（只定义 `__STDC__`） |
| C95 | 1995 | ISO/IEC 9899:1990/Amd 1 | 宽字符、双字符组 | `199409L` |
| C99 | 1999 | ISO/IEC 9899:1999 | `//` 注释、`stdbool.h`、VLA、`inline`、指定初始化器 | `199901L` |
| C11 | 2011 | ISO/IEC 9899:2011 | `_Generic`、`_Static_assert`、原子操作、线程库、删除 `gets` | `201112L` |
| C17/C18 | 2018 | ISO/IEC 9899:2018 | 只做缺陷修复，无新特性 | `201710L` |
| C23 | 2024 | ISO/IEC 9899:2024 | `bool`/`true`/`false`、`constexpr`、`nullptr`、`auto`、`typeof` | `202311L` |

### 1.2 每个版本到底加了什么
- **C89/C90**：首个正式标准，把 K&R C 规范化。引入函数原型、`void *`、`const`/`volatile`、`signed`、宽字符串 `L"..."`；没有 `//` 注释，变量必须在块首声明，`int` 可省略。C89 共 32 个关键字。
- **C95**：只做补充，增加宽字符工具（`<wchar.h>`、`<wctype.h>`）和双字符组（digraph，如 `<%` 表示 `{`），语言核心没动。
- **C99**：`//` 行注释；`<stdbool.h>` 提供 `bool`/`true`/`false`（底层 `_Bool`）；变长数组 `int a[n];`（C11 起可选）；`inline`；指定初始化器 `{.x = 1}`、`[2] = 3`；另有 `long long`、`<stdint.h>`、`restrict`、复合字面量、变参宏、柔性数组、`snprintf`。
- **C11**：`_Generic` 按类型选分支（如 `_Generic((x), int: "int", double: "double", default: "other")`）；`_Static_assert(常量, "消息")`；`<stdatomic.h>` 原子操作；`<threads.h>` 线程库（可选）；匿名结构体/共用体、`aligned_alloc`；删除 `gets`；VLA/复数/原子/线程为可选特性，用 `__STDC_NO_VLA__` 等宏判断。
- **C17**：只修缺陷（DR），无新特性，常被当作「C11 的稳定修订版」。
- **C23**：`bool`/`true`/`false` 成为关键字；`constexpr` 常量对象（不同于 C++ 的 constexpr 函数）；`nullptr`（类型 `nullptr_t`，在 `<stddef.h>`）；`auto` 类型推断（与旧存储类 auto 不同）；`typeof`/`typeof_unqual`；另有 `_BitInt(N)`、`[[nodiscard]]`、`#embed`、`0b1010`、`1'000'000`、`#elifdef`。注意这些与 C++ 语义不完全相同。
### 1.3 用 `__STDC_VERSION__` 实测编译器
标准宏比 `gcc --version` 可靠：交叉工具链的版本号和它实际支持的标准未必同步。

```c
#include <stdio.h>

int main(void)
{
#if defined(__STDC_VERSION__)
    printf("__STDC_VERSION__ = %ldL\n", (long)__STDC_VERSION__);
#if __STDC_VERSION__ >= 202311L
    puts("C23 or later");
#elif __STDC_VERSION__ >= 201710L
    puts("C17");
#elif __STDC_VERSION__ >= 201112L
    puts("C11");
#else
    puts("C99 or earlier");
#endif
#else
    puts("C89/C90");
#endif
    return 0;
}
```

C99 为 `199901L`，C11 为 `201112L`，C17 为 `201710L`，C23 为 `202311L`，C89/C90 不定义该宏。C23 草案期有些编译器会报 `202000L` 一类的中间值，**不确定的以编译器文档为准**。
### 1.4 编译器与嵌入式支持现状
| 编译器 | C99 | C11 | C17 | C23 | 说明 |
| --- | --- | --- | --- | --- | --- |
| GCC | 完整 | 完整 | 完整 | GCC 14 起 `-std=c23` 逐步完善 | 桌面、服务器、交叉编译主力 |
| Clang | 完整 | 完整 | 完整 | Clang 18 起逐步支持 | macOS、iOS、Android NDK |
| MSVC | 部分 | `/std:c11` | `/std:c17` | 部分 | 不支持 VLA 等可选特性 |
| arm-none-eabi-gcc | 视版本 | 视版本 | 视版本 | 视版本 | 交叉工具链升级慢 |
| Keil MDK AC5/AC6 | AC5 部分、AC6 较完整 | AC6 | 视版本 | 视版本 | 以编译器文档为准 |
| IAR EWARM | 支持 | 支持 | 视版本 | 部分 | 以编译器文档为准 |

1. 支持情况用 `__STDC_VERSION__` 实测，不要只看 IDE 里选的「C99 模式」。
2. 嵌入式常锁定 `-std=c99` 或 `-std=c11` 并开 `-Wpedantic`；C11 的线程库和原子操作在无 OS 或 RTOS 上未必可用。
3. MISRA 等规范通常禁用 VLA 和动态内存；C23 新特性在旧工具链上不可用，落地前先确认编译器版本。
4. C11 的可选特性不提供时，实现会定义 `__STDC_NO_VLA__`、`__STDC_NO_ATOMICS__`、`__STDC_NO_THREADS__`、`__STDC_NO_COMPLEX__`；`__STDC_IEC_559__` 表示浮点符合 IEEE 754。

## 2 编译与链接
「一个 `.c` 文件怎么变成进程」是 C 面试的保留题。这一章把四个阶段、静态库/动态库、`static`/`extern` 的链接语义串起来。

```text
hello.c --预处理(-E)--> hello.i --编译(-S)--> hello.s --汇编(-c)--> hello.o --链接--> hello
        展开头文件/宏        生成汇编           生成机器码          符号解析/重定位
```
### 2.1 从源码到可执行文件：四个阶段
| 阶段 | gcc 选项 | 输入 → 输出 | 做什么 |
| --- | --- | --- | --- |
| 预处理 | `-E` | `.c` → `.i` | 展开 `#include`、`#define`，删注释，处理条件编译 |
| 编译 | `-S` | `.i` → `.s` | 词法、语法、语义分析，生成汇编 |
| 汇编 | `-c` | `.s` → `.o` | 汇编器翻译成机器指令，生成可重定位目标文件 |
| 链接 | 无（默认） | `.o` + 库 → 可执行文件 | 符号解析、重定位、合并段 |

```bash
gcc -E hello.c -o hello.i     # 预处理
gcc -S hello.i -o hello.s     # 编译
gcc -c hello.s -o hello.o     # 汇编
gcc hello.o -o hello          # 链接
gcc -std=c11 -Wall -Wextra -O2 -g hello.c -o hello   # 一步到位
```

`.i` 仍是 C 源码（只是没有宏和头文件），`.s` 是文本汇编，`.o` 是 ELF 可重定位文件；`-c` 隐含预处理和编译。链接阶段才解析 `printf` 这类外部符号，`-l` 库必须放在引用它的目标文件后面。
### 2.2 目标文件、静态库与共享库
| 文件 | 生成方式 | 链接时机 | 特点 |
| --- | --- | --- | --- |
| `.o` | `gcc -c` | — | 可重定位目标文件，含代码、数据、符号表、重定位表 |
| `.a` | `ar rcs libfoo.a foo.o` | 静态链接时复制进可执行文件 | 体积大、部署简单、无运行时依赖 |
| `.so` | `gcc -shared -fPIC foo.c -o libfoo.so` | 动态链接时只记录依赖 | 体积小、可共享、升级方便、运行时需查找 |

```bash
gcc -c foo.c -o foo.o && ar rcs libfoo.a foo.o
gcc main.o -L. -lfoo -o app          # 静态库
gcc -fPIC -shared foo.c -o libfoo.so
gcc main.c -L. -lfoo -o app          # 共享库
```

排查手段：`nm` 看符号（`T` 全局代码、`t` 局部 `static`、`U` 未定义），`ldd` 看动态依赖，`size` 看各段大小，`readelf -S` 看段表。静态库只复制被用到的 `.o`；动态库运行时由动态链接器加载，换库不用重新链接。`-fPIC` 是共享库前提，忘记加常报 `recompile with -fPIC`。
### 2.3 static 与 extern 在链接层面的区别
| 写法 | 链接属性 | 可见性 | 典型用途 |
| --- | --- | --- | --- |
| 文件作用域 `static` 变量/函数 | 内部链接 | 仅本翻译单元 | 隐藏实现细节，避免命名冲突 |
| `extern` 声明 | 外部链接 | 全程序 | 引用其他 `.c` 中定义的符号 |
| 普通全局定义 | 外部链接 | 全程序 | 提供符号 |
| 函数内 `static` 局部变量 | 无链接，静态存储期 | 仅函数内 | 计数器、单次初始化 |

链接器只认符号：只有声明没有定义报 `undefined reference to 'foo'`，同一强符号定义两次报 `multiple definition of 'foo'`（GCC 10 起默认 `-fno-common`，旧代码的「暂定定义」会暴露）。

```c
/* util.c */
static int counter;                          /* 内部链接 */
static void helper(void) { }                 /* 内部链接 */
int util_call(void) { counter++; helper(); return counter; }   /* 外部链接 */
```

`static` 函数在 `nm` 里是小写 `t`，外部函数是大写 `T`。`extern int x;` 是声明，`extern int x = 5;` 是**定义**，不要写进头文件。C11 之前文件作用域的 `int x;` 是「暂定定义」，多个 `.c` 都写会合并；GCC 10 改为 `-fno-common` 后直接报重复定义。
### 2.4 头文件与头文件卫士
1. `#include <file>` 从系统目录和 `-I` 目录查找；`#include "file"` 先查当前源文件目录，再查系统目录。
2. 头文件卫士防止重复包含：

```c
#ifndef MY_HEADER_H
#define MY_HEADER_H

/* 声明、宏、类型定义 */

#endif /* MY_HEADER_H */
```

3. `#pragma once` 非标准但主流编译器支持，按「文件」去重，遇到同一文件的不同路径副本会失效；卫士按宏去重更可靠。
4. 头文件只放声明：函数原型、`extern` 变量、类型定义、宏、`static inline` 函数；把变量或普通函数定义放进去，多文件链接时会重复定义。
5. 需要被 C++ 调用的 C 头文件，声明外层加 `#ifdef __cplusplus` / `extern "C" {` / `}` / `#endif`。
### 2.5 gcc 常用选项
| 选项 | 作用 |
| --- | --- |
| `-E` / `-S` / `-c` | 只做预处理 / 编译 / 汇编 |
| `-o file` | 指定输出文件名 |
| `-Wall -Wextra` | 打开常用和额外告警，建议必开 |
| `-Wpedantic` | 严格按标准检查，暴露扩展用法 |
| `-O0` / `-O2` / `-Os` | 优化级别，调试用 `-O0`，发布常用 `-O2` |
| `-g` | 生成调试信息（配合 gdb） |
| `-std=c11` / `c17` / `c23` | 指定语言标准 |
| `-I dir` / `-L dir` / `-lname` | 头文件路径 / 库路径 / 链接库 |
| `-DMACRO=VAL` | 命令行定义宏 |
| `-fPIC` / `-shared` | 生成位置无关代码 / 共享库 |
| `-fsanitize=address,undefined` | 运行时检查内存错误和未定义行为 |
| `-fstack-protector-strong` | 栈保护（canary）；`-static` 静态链接 |

推荐组合：`gcc -std=c11 -Wall -Wextra -Wpedantic -O2 -g main.c -o main`。
### 2.6 程序结构与词法要素
1. 组成：预处理器指令、函数、变量、语句与表达式、注释；标准骨架是「包含头文件 → 宏 → 全局变量 → 函数声明 → `main` → 其他函数定义」。
2. 令牌：关键字、标识符、常量、字符串字面量、运算符与标点；注释在预处理阶段被替换成一个空格，`/* */` 不能嵌套。
3. 标识符由字母、数字、下划线组成，不能以数字开头，不允许 `@`、`$`、`%`，区分大小写；C99 起外部标识符至少 31 个有效字符、内部至少 63 个。
4. 关键字不能作标识符：C89 有 32 个；C99 增加 `inline`、`restrict`、`_Bool`、`_Complex`、`_Imaginary`；C11 增加 `_Alignas`、`_Alignof`、`_Atomic`、`_Generic`、`_Noreturn`、`_Static_assert`、`_Thread_local`；C23 又把 `bool`、`true`、`false`、`constexpr`、`nullptr`、`auto`、`typeof` 等变成关键字。
5. 空白分隔令牌（`int x` 不能写成 `intx`）；`a+++b` 按最长匹配解析为 `a++ + b`，不要依赖这种写法。

## 3 预处理器
### 3.1 预处理器的作用与常用指令
1. 预处理器不是编译器的一部分，而是编译过程中的独立步骤，本质是文本替换工具：展开宏、插入头文件、处理条件编译、删除注释。
2. 预处理发生在词法分析之前，它不懂 C 语法，所以宏不检查类型，也不遵循作用域。

| 指令 | 描述 |
| --- | --- |
| `#define` | 定义宏 |
| `#include` | 包含源文件代码 |
| `#undef` | 取消宏 |
| `#ifdef` / `#ifndef` | 宏已定义 / 未定义时为真 |
| `#if` / `#elif` / `#else` | 条件编译 |
| `#endif` | 结束条件编译块 |
| `#error` | 输出错误消息并终止编译 |
| `#pragma` | 向编译器发布特殊命令 |
| `#line` | 修改当前行号和文件名 |

### 3.2 宏定义与展开
对象宏替换文本，函数宏替换参数。展开顺序是：先替换参数（除非参数紧邻 `#` 或 `##`），再替换宏体，然后重新扫描结果继续展开；宏不能递归展开自身。`#` 把参数转成字符串，`##` 拼接两个记号，二者都不会预先展开参数；宏体跨行用反斜杠 `\` 续行，行尾不能有空格。

```c
#include <stdio.h>

#define PI 3.14159
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define SWAP(type, a, b) do { type t = (a); (a) = (b); (b) = t; } while (0)
#define STR(x) #x
#define XSTR(x) STR(x)
#define CAT(a, b) a##b
#define XCAT(a, b) CAT(a, b)
#define VERSION 34

int main(void)
{
    int x = 3, y = 8, token34 = 40;

    SWAP(int, x, y);
    printf("%.5f %d %d\n", PI, MAX(x, y), y);       /* 3.14159 8 3 */
    printf("%s %s\n", STR(hello), XSTR(VERSION));    /* hello 34 */
    printf("%d %d\n", CAT(token, 34), XCAT(token, VERSION));   /* 40 40 */
    return 0;
}
```

宏体里每个参数和整个表达式都要加括号；多语句宏用 `do { ... } while (0)` 包住。`#`/`##` 需要「先展开再拼接」时套一层中转宏（`XSTR`、`XCAT`），这是写调试宏的常用手法。
### 3.3 条件编译
1. `#if` / `#elif` / `#else` / `#endif` 按常量表达式选择代码块；`defined(X)` 与 `#ifdef X` 等价，复杂表达式里只能写 `defined(X)`，如 `#if defined(X) && X > 2`。
2. 典型用法是按平台选实现：`#if defined(_WIN32) ... #elif defined(__linux__) ... #else ... #endif`；`#ifndef NDEBUG` 区分 debug/release。
3. `#if 0 ... #endif` 是屏蔽大段代码的常用方式，比 `/* */` 安全；`#error "message"` 主动终止编译，适合检查平台/标准。
4. `-DNDEBUG` 关闭 `assert`；`assert` 是宏，定义 `NDEBUG` 后整个表达式被替换掉，不要在里面写有副作用的代码。
### 3.4 预定义宏
| 宏 | 含义 |
| --- | --- |
| `__DATE__` / `__TIME__` | 编译日期 / 时间，字符串字面量 |
| `__FILE__` / `__LINE__` | 当前文件名 / 行号，常用于日志 |
| `__STDC__` | 符合标准 C 时为 1 |
| `__STDC_VERSION__` | 标准版本，C89 不定义 |
| `__STDC_HOSTED__` | 有完整标准库的宿主环境为 1，裸机为 0 |
| `__func__` | C99 的当前函数名，是预定义标识符，**不是宏** |
| `__GNUC__` / `__clang__` | 编译器扩展宏，非标准 |
| `_WIN32` / `__linux__` / `__x86_64__` | 平台/架构宏，非标准 |

`__DATE__`、`__TIME__` 会让构建结果不可复现，需要 reproducible build 时应避免写进二进制；不要自己定义 `__` 开头的名字，那是实现保留的。
### 3.5 宏的副作用与括号陷阱
```c
#include <stdio.h>

#define SQUARE_BAD(x) x * x
#define SQUARE(x) ((x) * (x))
#define MAX_BAD(a, b) a > b ? a : b

int main(void)
{
    int i = 1, r;

    printf("%d %d\n", SQUARE_BAD(1 + 2), SQUARE(1 + 2));   /* 5 9 */
    r = MAX_BAD(i++, 0);                                   /* i 自增两次 */
    printf("%d %d\n", r, i);                               /* 2 3 */
    return 0;
}
```

1. 参数和整体都要加括号，否则运算符优先级会改变语义。
2. 参数可能被求值多次，`MAX(i++, j++)` 会让其中一个自增两次，改用 `static inline` 函数。
3. `#define MAX 100;` 多了分号，`int buf[MAX];` 展开成 `int buf[100;];`，直接语法错误。
4. 宏没有类型、没有作用域、调试时看不到符号；宏展开的错误信息指向调用点，排查时看 `gcc -E` 最快。能用 `const`、`enum`、`static inline` 就不要用宏。
5. 宏参数里的逗号会被当成参数分隔符，传 `f(x, y)` 会错位，需要额外加括号或改用函数。
### 3.6 `do { } while (0)` 惯用法
多语句宏直接写成 `{ ... }`，放在 `if (cond) MACRO(); else ...` 里会多出一个分号，导致 `else` 悬空；`do { ... } while (0)` 展开后是一条语句，末尾分号刚好结束 `do-while`。

```c
#include <stdio.h>

#define CHECK(cond) do { \
    if (!(cond)) { \
        fprintf(stderr, "%s:%d: %s failed\n", __FILE__, __LINE__, #cond); \
        return -1; \
    } \
} while (0)

static int positive(int x)
{
    CHECK(x > 0);
    return x;
}

int main(void)
{
    printf("%d\n", positive(3));
    return positive(-1) == 0;
}
```

`while (0)` 保证循环体只执行一次，编译器通常会把循环优化掉；宏内部的 `break` 只跳出这个假循环，不会破坏外层的 `switch`/`for`。能用 `static inline` 替代时优先替代：有类型检查、能调试、只在本编译单元展开。

## 4 指针全解
指针语法只有 `&`、`*` 两个运算符，难的是「指向哪里、能走多远、谁能改」。
### 4.1 指针基础
```c
#include <stdio.h>

int main(void)
{
    int var = 20, arr[3] = {100, 200, 300};
    int *ip = &var;                 /* 必须初始化，否则是野指针 */
    int *p = arr;                   /* 数组名退化为首元素地址 */

    *ip = 21;
    for (int i = 0; i < 3; i++) printf("%d ", *(p + i));
    p = &arr[2];
    printf("\n%d %d %d\n", var, p[0], p[-2]);   /* 21 300 100 */
    return 0;
}
```

1. 指针的大小与所指类型无关：32 位平台 4 字节，64 位平台 8 字节。
2. 指针算术只能在同一数组（或同一对象）内部进行：指向「最后一个元素的下一个位置」合法，可以比较、可以计算，但不能解引用。
3. 两个指针相减得到 `ptrdiff_t`，表示相隔的元素个数，不是字节数。
4. `NULL` 是空指针常量（`<stddef.h>`），空指针解引用是未定义行为；函数返回指针时调用方必须判空。
### 4.2 指针运算
```text
int a[4] = {10, 20, 30, 40};
a+0      a+1      a+2      a+3      a+4（one-past-end，可比较不可解引用）
 |        |        |        |        |
 v        v        v        v        v
 10       20       30       40       （越界，不可解引用）
0x1000   0x1004   0x1008   0x100c   0x1010
```

`p + n` 的地址增量是 `n * sizeof(*p)`，所以 `int *` 加 1 走 4 字节，`char *` 加 1 走 1 字节。`p[n]` 等价于 `*(p + n)`，`n` 可以为负，只要结果仍落在同一数组内。不同数组的指针相减、比较都是未定义行为。
### 4.3 指针与数组的区别
| 对比项 | 数组 `int a[5]` | 指针 `int *p` |
| --- | --- | --- |
| 类型 | `int[5]` | `int *` |
| `sizeof` | 20（整个数组） | 8（64 位指针） |
| 赋值 | `a = ...` 非法 | 可以重新指向 |
| `&` 运算 | `&a` 类型是 `int (*)[5]` | `&p` 类型是 `int **` |
| 作为参数 | 退化为指针 | 本身就是指针 |

```c
#include <stdio.h>

int main(void)
{
    int a[5] = {1, 2, 3, 4, 5};
    int *p = a;

    printf("%zu %zu\n", sizeof(a), sizeof(p));                /* 20 8 */
    printf("%td\n", (char *)(&a + 1) - (char *)(a + 1));      /* 16 */
    return 0;
}
```

数组名退化的例外：`sizeof`、`&`、`_Alignof`、用于初始化字符数组的字符串字面量。`&a` 的类型是「指向 `int[5]` 的指针」，`&a + 1` 直接跨过 20 字节，所以与 `a + 1` 相差 16 字节；这也是「数组指针」的来源。
### 4.4 多级指针
`int **pp` 是二级指针：`*pp` 是一级指针，`**pp` 才是指向的值。它让函数能修改「调用方的指针本身」。

```c
#include <stdlib.h>

static int alloc(int **out, size_t n)
{
    int *p = malloc(n * sizeof *p);
    if (p == NULL) return -1;
    for (size_t i = 0; i < n; i++) p[i] = (int)i;
    *out = p;                       /* 修改调用方的指针 */
    return 0;
}

int main(void)
{
    int *data = NULL;
    if (alloc(&data, 4) != 0) return 1;
    free(data);
    return 0;
}
```

`const char *argv[]` 与 `char **argv` 是同一个意思：数组参数退化成指针。三级指针以上通常意味着设计有问题，优先用结构体封装。
### 4.5 const 与指针、void *
| 写法 | 含义 | 能否改 `*p` | 能否改 `p` |
| --- | --- | --- | --- |
| `const int *p` | 指向 const int 的指针 | 否 | 是 |
| `int const *p` | 同上（const 在 `*` 左边） | 否 | 是 |
| `int * const p` | const 指针，必须初始化 | 是 | 否 |
| `const int * const p` | 两者都 const | 否 | 否 |

记忆口诀：**const 在 `*` 左边锁数据，在 `*` 右边锁指针**；从变量名往右读，遇到 `*` 念「指针」，遇到 `const` 念「只读」。

```c
#include <stdio.h>

int main(void)
{
    int a = 1, b = 2;
    const int *p1 = &a;         /* 不能 *p1 = 3，但可以 p1 = &b */
    int * const p2 = &a;        /* 可以 *p2 = 3，但 p2 不能再指向 b */
    const int * const p3 = &a;  /* 两者都不行 */

    p1 = &b;
    *p2 = 3;
    printf("%d %d %d\n", *p1, *p2, *p3);   /* 2 3 3 */
    return 0;
}
```

1. `char *` 不能直接指向字符串字面量，应写 `const char *`；字面量在只读区，写入是未定义行为。`void *` 可与任意对象指针隐式互转，但不能解引用、不能做指针算术（GCC 扩展按 1 字节处理）；`malloc` 返回 `void *`，C 中不需要强制转换。
2. `typedef` 会把「指针」整体变成一个类型名，`const P` 锁的是指针而不是数据：

```c
typedef int *int_ptr;

void set_one(int *a)
{
    const int_ptr p = a;    /* 等价于 int * const p，不是 const int *p */
    *p = 1;
}
```
### 4.6 指针与字符串
`char s1[] = "hello";` 是可修改的数组（6 字节，含 `'\0'`）；`const char *s2 = "hello";` 指向只读区，`s2[0] = 'H'` 是未定义行为。`sizeof(s1)` 是 6，`sizeof(s2)` 是指针大小。函数参数写 `const char *` 表示「只读、不复制」。
### 4.7 函数指针与回调
函数指针保存函数入口地址，用来实现回调、状态机、跳转表。`typedef int (*binop_t)(int, int);` 定义函数指针类型，`binop_t table[] = {add, sub};` 就是跳转表；`(*fp)()` 与 `fp()` 等价。

```c
#include <stdio.h>
#include <stdlib.h>

static int cmp_int(const void *a, const void *b)
{
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);           /* 避免 x - y 溢出 */
}

int main(void)
{
    int v[] = {3, 1, 2};
    qsort(v, 3, sizeof v[0], cmp_int);
    printf("%d %d %d\n", v[0], v[1], v[2]);   /* 1 2 3 */
    return 0;
}
```

`qsort` 的比较函数返回负数/0/正数表示小于/等于/大于。函数指针不能和 `void *` 互转（标准不允许，POSIX 的 `dlsym` 是平台扩展），在部分架构上转回来会崩。
### 4.8 指针数组 vs 数组指针
```c
int *ptr[3];        /* 指针数组：3 个 int * */
int (*parr)[3];     /* 数组指针：指向 int[3] 的指针 */
```

`int *ptr[3]` 的 `ptr[i]` 是 `int *`，常用来存一组字符串：`const char *names[] = {"zz", "aa"};`。`int (*parr)[3]` 的 `(*parr)[i]` 取到元素，`parr + 1` 跨越整个 `int[3]`，常用于二维数组传参：

```c
#include <stdio.h>

static void print2d(int (*a)[3], int rows)
{
    for (int i = 0; i < rows; i++)
        printf("%d %d %d\n", a[i][0], a[i][1], a[i][2]);
}

int main(void)
{
    int m[2][3] = {{1, 2, 3}, {4, 5, 6}};
    print2d(m, 2);
    return 0;
}
```

二维数组传参时第二维长度不能省：编译器要靠 `int (*)[3]` 计算 `a[i]` 的步长。写成 `int **` 是错的——二维数组不是「指针的指针」，它的内存是连续的行优先布局。

## 5 内存管理
### 5.1 进程内存布局
```text
高地址
+---------------------+  栈：局部变量、调用帧，向低地址增长
|        stack        |
|          ↓          |
|          ↑          |
|        heap         |  堆：malloc/calloc/realloc，向高地址增长
+---------------------+
|   .bss              |  未初始化/零初始化的全局、static 变量
+---------------------+
|   .data             |  已初始化的全局、static 变量
+---------------------+
|   .rodata           |  字符串字面量、const 全局
+---------------------+
|   .text             |  机器指令，只读
+---------------------+
低地址
```

1. `.text` 只读可共享；`.rodata` 存字符串字面量和 `const` 全局；`.data` 存已初始化的全局/`static`；`.bss` 存未初始化/零初始化的全局/`static`，不占可执行文件空间，运行时由内核清零。
2. 栈由编译器与操作系统管理，大小固定（Linux 默认 8 MB 左右），递归过深或超大局部数组会栈溢出。
3. 堆由分配器管理；栈和堆之间是尚未映射的空闲区域，由 ASLR 随机化。
4. 用 `size a.out` 看 text/data/bss 大小，`nm` 看符号，`readelf -S` 看段表；函数内的 `static` 局部变量不在栈上，而在 `.data`/`.bss`。
### 5.2 malloc / free 的正确写法
```c
#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    size_t n = 10;
    int *p = malloc(n * sizeof *p);     /* 不要写死 sizeof(int) */

    if (p == NULL) {
        perror("malloc");
        return EXIT_FAILURE;
    }
    for (size_t i = 0; i < n; i++) p[i] = (int)i;
    printf("p[9] = %d\n", p[9]);

    free(p);
    p = NULL;                           /* 防止悬垂指针 */
    return 0;
}
```

1. `malloc` 返回 `void *`，C 中不需要强制转换；参数用 `n * sizeof *p`，改类型时不用改表达式。
2. 失败返回 `NULL`，必须检查；`free(NULL)` 是空操作，重复 `free` 是未定义行为。
3. `free` 后原指针值不变，但内存已归还，继续解引用是 use-after-free；置 `NULL` 能让二次释放立刻崩在明确位置。
4. `malloc(0)` 可能返回 `NULL` 或一个可 `free` 的唯一指针，不要依赖具体行为。
### 5.3 calloc 与 realloc
| 对比 | `malloc` | `calloc` |
| --- | --- | --- |
| 参数 | 总字节数 | 元素个数 + 单个元素大小 |
| 初始化 | 不清零，内容是随机值 | 全部置 0 |
| 溢出检查 | 调用方自己算 | 内部检查 `nmemb * size` |
| 典型用途 | 结构体、缓冲区 | 数组、需要零值的结构 |

```c
#include <stdlib.h>

static int grow(size_t n)
{
    int *a = calloc(n, sizeof *a);                  /* 分配并清零 */
    int *tmp = realloc(a, 2 * n * sizeof *a);       /* 扩容到 2 倍 */
    if (tmp == NULL) {
        free(a);                                    /* 失败时 a 仍有效 */
        return -1;
    }
    a = tmp;
    free(a);
    return 0;
}

int main(void) { return grow(5) == 0 ? 0 : 1; }
```

1. `realloc` 成功时返回新地址（可能等于原地址），失败时返回 `NULL` 且原块不变，所以必须用临时指针接收；直接 `a = realloc(a, ...)` 在失败时会丢失原指针。
2. `realloc` 可能搬移数据，扩容后原指针失效；新增部分**不会**清零。
3. `realloc(p, 0)` 在 C17 及以前由实现定义，C23 起是未定义行为，不要依赖。
### 5.4 brk / mmap 与分配器
1. glibc 的 `malloc` 使用 ptmalloc2：小块内存通过 `brk`/`sbrk` 抬高堆顶，大块内存（默认 ≥ 128 KiB，`M_MMAP_THRESHOLD` 可调）直接用 `mmap` 映射。
2. `free` 只把块还给分配器（arena），不保证立刻还给操作系统，所以进程 RSS 可能不下降。
3. 每个线程有独立的 arena（受 `M_ARENA_MAX` 限制），多线程频繁分配会有锁竞争和内存膨胀。
4. 碎片化的根源是「分配大小不一 + 释放顺序随机」，长期运行的服务要考虑对象池或固定大小分配。
### 5.5 内存泄漏、野指针与悬垂指针
1. 内存泄漏：`malloc` 后丢失指针、函数提前 `return` 没走到 `free`、循环里反复分配不释放。
2. 野指针：未初始化的指针、`free` 后没置 `NULL` 的指针、指向已销毁栈帧的指针；悬垂指针是其中一种，返回局部数组就是典型（见 10.4）。
3. 排查手段：编译期 `-Wall -Wextra`，运行期 ASan、valgrind，见第 11 章。
### 5.6 常见分配错误
| 错误 | 后果 | 正确做法 |
| --- | --- | --- |
| `malloc(sizeof(p))` | 只分配了指针大小 | `malloc(n * sizeof *p)` |
| 不检查 `NULL` | 空指针解引用 | 失败走错误分支 |
| `free` 后继续用 | use-after-free | 释放后置 `NULL` |
| 重复 `free` | 堆破坏/崩溃 | 只释放一次 |
| `free(p + 1)` / `free(&local)` | 非法释放 | 只能释放 `malloc` 返回的原地址 |
| 整数溢出 `n * size` | 分配过小后越界 | 先检查 `n > SIZE_MAX / size` |
| 跨模块分配/释放 | CRT 不同导致崩溃 | 谁分配谁释放，或提供统一 API |

## 6 结构体进阶
### 6.1 声明、自引用与初始化
```c
struct B;                                       /* 不完整声明 */

struct A { struct B *partner; };                /* 互相引用只能用指针 */
struct B { struct A *partner; };

struct Node { int value; struct Node *next; };  /* 自引用：链表/树 */

struct { int a; } s1;                           /* 匿名结构体 + 变量 */
typedef struct { int a; } Simple2;              /* typedef 起别名 */
```

1. `struct` 的标签、成员列表、变量列表至少要出现两个；只声明类型不分配存储，定义变量才分配。
2. 结构体可以嵌套其他结构体（需要完整类型），也可以包含指向自身类型的指针；不能包含自身类型的成员，因为大小无法确定。
3. 初始化列表按成员顺序赋值，未列出的成员补 0；C99 指定初始化器 `{.id = 2, .title = "C++"}` 按名字赋值。同类型结构体可以整体赋值 `b2 = b1`，但不能用 `==` 比较（填充字节内容不确定）。
4. 成员访问用 `.`，指针用 `->`，`p->x` 等价于 `(*p).x`；结构体传参是传值，会整体拷贝，较大的结构体应传 `const struct Book *`。
### 6.2 内存对齐规则
1. 每个成员的偏移量必须是其对齐数的整数倍，结构体总大小必须是最大对齐数的整数倍。
2. 基本类型的对齐数通常等于其大小（`char` 1、`short` 2、`int` 4、`double` 8），受平台和 ABI 影响；编译器在成员之间和末尾插入填充字节。
3. 对齐让 CPU 一次总线周期就能取到数据，部分架构未对齐访问会异常。

```text
struct A { char c; int i; short s; };   struct B { char c; short s; int i; };
A: [c 0][pad 1-3][i 4-7][s 8-9][pad 10-11]   大小 12
B: [c 0][pad 1][s 2-3][i 4-7]                 大小 8
```

调整成员顺序（大的放前面）能减少填充：`struct A` 是 12 字节，`struct B` 只要 8 字节。协议结构体不要依赖默认布局，跨平台要用序列化或 `pack`。
### 6.3 `#pragma pack(n)`
```c
#include <stdint.h>

#pragma pack(push, 1)
struct wire { uint8_t type; uint32_t len; uint16_t crc; };
#pragma pack(pop)

_Static_assert(sizeof(struct wire) == 7, "wire must be packed");

int main(void) { return 0; }
```

`#pragma pack(push, 1)` 取消填充，`#pragma pack(pop)` 恢复默认；常用于协议和寄存器结构，风险是未对齐访问变慢甚至崩溃（ARM 某些配置、SPARC 会异常）。`pack` 是编译器扩展，网络协议更稳妥的做法是按字节读写。
### 6.4 `offsetof` 与容器宏
```c
#include <stddef.h>
#include <stdio.h>

struct S { char c; int i; double d; };

int main(void)
{
    printf("%zu %zu %zu\n", offsetof(struct S, c),
           offsetof(struct S, i), offsetof(struct S, d));   /* 0 4 8 */
    return 0;
}
```

`offsetof(type, member)` 在 `<stddef.h>` 中，返回成员相对结构体起始的字节偏移，类型是 `size_t`。它常用于序列化、内核的 `container_of`（由成员地址反推结构体地址）：

```c
#include <stddef.h>

#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))
```

这个宏依赖「结构体起始地址 + 偏移」的线性布局，对 `pack` 结构同样成立；GCC 的 `typeof` 版本还会做类型检查。
### 6.5 三道 sizeof 例题
1. `struct C { double d; char c; };` → 16：`d` 占 0~7，`c` 在 8，总 9 补齐到 8 的倍数。
2. `struct BF { unsigned a:3; unsigned b:5; unsigned c:8; unsigned d:17; };` → 8：前三个共 16 位在同一 32 位单元，`d` 需要 17 位、剩余 16 位不够且位域不能跨单元，所以另起一个单元。
3. 6.2 的 `struct A` 在 `#pragma pack(1)` 下 → 7（1 + 4 + 2）。

以上按「`int` 4 字节、`double` 8 字节、位域按 `unsigned int` 分配单元」的常见 ABI 计算；换平台或换编译器要用 `sizeof` 实测，标准只规定下限，位域布局由实现定义。
### 6.6 柔性数组
```c
#include <stdlib.h>

struct packet {
    size_t len;
    char data[];            /* 必须是最后一个成员 */
};

int main(void)
{
    size_t n = 16;
    struct packet *p = malloc(sizeof *p + n);   /* 一次分配：头部 + 数据 */
    if (p == NULL) return 1;
    p->len = n;
    free(p);
    return 0;
}
```

1. C99 允许结构体最后一个成员是柔性数组成员 `char data[];`，长度在运行时决定；`sizeof(struct packet)` 不包含 `data`。
2. 结构体至少要有一个其他成员；`malloc` 时要加上数据区大小，并检查乘法/加法溢出。
3. 对比 `char *data`：需要两次分配、内存不连续；对比 `char data[0]`：GCC 扩展，C99 之前常见，现在应写 `[]`。
### 6.7 共用体与大小端
```c
#include <stdint.h>
#include <stdio.h>

union Data {
    int i;
    float f;
    char str[20];           /* 占 20 字节，决定整个共用体的大小 */
};

static int is_little_endian(void)
{
    union { uint32_t i; uint8_t c[4]; } u = {.i = 1};
    return u.c[0] == 1;
}

int main(void)
{
    printf("%zu %d\n", sizeof(union Data), is_little_endian());   /* 20 1 */
    return 0;
}
```

1. 所有成员共享同一块内存，同一时刻只有一个成员有效；大小等于最大成员并按最大对齐取整。
2. 类型双关的结果依赖字节序和实现，常用于节省内存、协议字段多视角解释、判断大小端。先写 `data.str` 再打印 `data.i` 得到 1917853763 之类的值，是同一块内存被重新解释，不是三个值共存。
3. 严格别名规则下，通过共用体读另一个成员在 C 中是允许的（C++ 不允许），但跨平台协议仍建议用 `memcpy` 或移位。
### 6.8 位域
```c
struct bs {
    unsigned int a : 8;     /* 占 8 位 */
    unsigned int b : 2;     /* 占 2 位 */
    unsigned int c : 6;     /* 占 6 位 */
};
```

1. 用途：用 1 位表示开关量；解析非标准文件格式（如 9 位整数）或硬件寄存器。
2. 剩余空间不够时从下一单元开始；`unsigned int : 0` 强制从下一单元开始；无名位域只用于填充，不能使用。
3. 位域不能取地址（`&s.a` 非法）、不能定义数组、宽度不能超过类型位宽；布局与位序由实现定义，跨平台协议要用移位和掩码。
4. 位域的类型应是 `int`/`unsigned int`/`_Bool` 或实现支持的类型；有符号位域的符号性也由实现决定。

## 7 枚举与 typedef
### 7.1 枚举
```c
enum DAY { MON = 1, TUE, WED, THU, FRI, SAT, SUN };   /* 第一个 1，后面 +1 */
enum DAY2 { MON2 = 1, TUE2 } day2;    /* 定义类型的同时定义变量 */
enum { MON3 = 1, TUE3 } day3;         /* 省略标签，直接定义变量 */

int main(void) { return MON + MON2 + MON3; }
```

1. 不写 `= 1` 时第一个默认为 0，后面的值依次 +1；枚举常量本质是 `int`，`sizeof(enum DAY)` 通常为 4，由实现决定，C23 起可以指定底层类型（以编译器文档为准）。
2. C 中枚举变量可以自增遍历：`for (day = MON; day <= SUN; day++)`；C++ 不允许这样自增。
3. 枚举常量有作用域，不同枚举里的同名常量会冲突。
### 7.2 枚举与 `#define` 的区别
| 对比 | `enum` | `#define` |
| --- | --- | --- |
| 处理阶段 | 编译器 | 预处理器，纯文本替换 |
| 类型 | 有整型类型 | 无类型 |
| 作用域 | 遵循块/文件作用域 | 从定义点到 `#undef`，无作用域 |
| 调试 | 符号可见 | 调试器看不到名字 |
| 自增 | 支持 | 不支持 |

定义一组相关常量优先用 `enum`；只有条件编译、字符串拼接才必须用宏。
### 7.3 typedef 的用法与坑
```c
typedef unsigned char BYTE;
typedef struct Node { int v; struct Node *next; } Node;
typedef int (*cmp_fn)(const void *, const void *); /* 函数指针类型 */
typedef int IntArray[4];                           /* 数组类型 */

int main(void)
{
    Node n = {1, 0};
    IntArray a = {1, 2, 3, 4};
    return n.v + a[0];
}
```

1. `typedef` 由编译器处理，有作用域和类型检查；`#define` 是预处理文本替换，无作用域、无类型检查。
2. `typedef int *P; P a, b;` 两个都是指针；`#define P int *` 后 `P a, b;` 只有 a 是指针，b 是 `int`。
3. `typedef` 不创建新类型，只是别名，和原类型完全兼容；不能用 `typedef` 加存储类（`typedef static int` 非法）。
4. `const P` 锁的是指针本身（见 4.5）；想定义「指向 const 的指针别名」要写 `typedef const int *PC;`。

## 8 文件 IO
### 8.1 标准输入输出
| 标准文件 | 文件指针 | 设备 |
| --- | --- | --- |
| 标准输入 | `stdin` | 键盘 |
| 标准输出 | `stdout` | 屏幕 |
| 标准错误 | `stderr` | 屏幕（不带缓冲，优先输出） |

1. `printf` 输出到 stdout，`puts` 输出字符串并追加换行；`scanf` 从 stdin 读取，必须传地址并检查返回值，如 `if (scanf("%d", &n) != 1)`。
2. 格式符：`%d`、`%u`、`%ld`、`%lld`、`%f`、`%lf`（scanf 读 double）、`%c`、`%s`、`%p`、`%zu`、`%%`；格式串与参数类型不匹配是未定义行为。
3. `getchar()` 返回 `int` 以便区分 `EOF`（-1），不要用 `char` 接收；`gets()` 不检查长度，C11 起已删除，改用 `fgets(buf, sizeof buf, stdin)`，或用 Annex K 的 `gets_s`（可选，很多实现不提供）。
### 8.2 fopen 模式表
`fopen` 失败返回 `NULL`，使用前必须判断；`fclose` 成功返回 0，失败返回 `EOF`，不关闭会丢缓冲区数据、泄漏句柄。

| 模式 | 描述 |
| --- | --- |
| `r` | 打开已有文本文件读 |
| `w` | 打开文本文件写，不存在则创建，存在则截断为零长度 |
| `a` | 追加写，不存在则创建 |
| `r+` / `w+` / `a+` | 读写模式，`w+` 会截断，`a+` 写只能追加 |
| `rb`/`wb`/`ab` | 二进制模式，Windows 上不做 CRLF 转换 |
| `wx`/`w+x` | C11 独占创建，文件已存在则失败 |

`+` 表示同时可读可写，但读写切换之间要 `fseek`/`fflush`；`a` 模式下所有写都追加到末尾，`fseek` 也改不了写位置。
### 8.3 文本模式与二进制模式
Windows 文本模式会把 `\n` 写成 `\r\n`，读时再转回来；二进制模式不做转换，`ftell` 才是真实字节偏移。POSIX 系统两者没有区别，但跨平台代码应显式写 `"rb"`/`"wb"`。结构体直接 `fwrite` 会写入填充字节，且受字节序/对齐影响，只适合本机临时文件。
### 8.4 读写、定位与错误处理
```c
#include <errno.h>
#include <stdio.h>

int main(void)
{
    char buf[32];
    FILE *fp = fopen("demo.txt", "w+");     /* 读写模式，存在则截断 */

    if (fp == NULL) { perror("fopen"); return 1; }
    fputs("hello\n", fp);
    rewind(fp);                             /* 等价于 fseek(fp, 0, SEEK_SET) */
    while (fgets(buf, (int)sizeof buf, fp) != NULL) fputs(buf, stdout);
    fseek(fp, 0, SEEK_END);
    printf("size = %ld\n", ftell(fp));
    fclose(fp);
    return 0;
}
```

1. `fputc`/`fgetc` 读写一个字符，`fputs`/`fgets` 读写字符串，`fread`/`fwrite` 读写二进制块并返回实际元素个数，`fprintf`/`fscanf` 格式化读写。
2. 用 `feof` 判断文件结束是错误写法（会多读一次），应判断 `fgets`/`fread` 的返回值；`fseek` 偏移是 `long`，大文件在 32 位平台要用 `fseeko`/`ftello`（POSIX）。
3. 缓冲区：标准流默认全缓冲（文件）或行缓冲（终端），`fflush(fp)` 把用户态缓冲区写回内核；`fflush(NULL)` 刷新所有输出流。`fflush` 只对输出流有定义，且不等于 `fsync`（前者只到页缓存，后者才落盘）。
4. `exit`/`return` 会刷新所有流、执行 `atexit` 注册的函数；`_Exit`/`_exit` 不刷新。`errno` 成功时不会清零，应先 `errno = 0`；`perror("msg")` 输出 `msg: 错误描述`，`strerror(errno)` 返回描述指针。`errno` 是线程局部的，失败后要立刻保存。

## 9 可变参数与命令行参数
### 9.1 va_list 原理
`<stdarg.h>` 提供 `va_list`、`va_start`、`va_arg`、`va_end`。`va_list` 是 ABI 相关的游标：x86-64 System V 把可变参数放在寄存器保存区和栈上，`va_start` 初始化游标，`va_arg` 按类型对齐后取值并前进。可变参数没有类型检查，个数和类型靠调用方与格式串约定。
### 9.2 可变参数函数
```c
#include <stdarg.h>
#include <stdio.h>

double average(int num, ...)
{
    va_list ap;
    double sum = 0.0;

    va_start(ap, num);                  /* 绑定最后一个固定参数 */
    for (int i = 0; i < num; i++) sum += va_arg(ap, int);
    va_end(ap);
    return num > 0 ? sum / num : 0.0;
}

int main(void) { printf("%.2f\n", average(3, 10, 20, 30)); return 0; }
```

1. 默认实参提升：`char`/`short` 传成 `int`，`float` 传成 `double`，所以 `va_arg(ap, char)` 是错的。
2. C23 起 `va_start` 允许省略第二个参数（以编译器文档为准）；需要把可变参数继续传给 `printf` 家族时用 `vsnprintf`，不要自己拆。
3. `va_end` 必须调用；不要把 `va_list` 传给另一个函数后继续用（除非用 `va_copy`）。
### 9.3 argc / argv 与 getopt
`argc` 是参数个数（含程序名），`argv` 是字符串数组，`argv[argc]` 为 `NULL`，`argv[0]` 是程序名（可能带路径）；第三个参数 `envp` 不是标准，但多数平台支持。数字参数用 `strtol` 转换并检查 `errno`/`endptr`，不要直接把字符串指针强转成整数指针：

```c
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    char *end = NULL;
    long v;

    if (argc != 2) { fprintf(stderr, "usage: %s <number>\n", argv[0]); return 1; }
    errno = 0;
    v = strtol(argv[1], &end, 10);
    if (errno != 0 || end == argv[1] || *end != '\0') return 1;
    printf("%ld\n", v * 2);
    return 0;
}
```

参数解析复杂时用 `getopt`（POSIX，不是 ISO C）：`getopt(argc, argv, "n:v")` 返回选项字符，`-n` 后的冒号表示需要参数，参数在 `optarg`；`optind` 是下一个待处理下标，`optopt` 是出错的选项字符。Windows 的 MSVC 没有 `unistd.h`。

## 10 未定义行为与陷阱
### 10.1 三种「不确定」
| 类别 | 含义 | 例子 |
| --- | --- | --- |
| 实现定义 | 标准允许实现自选，且要写进文档 | `char` 是否有符号、`int` 位宽、位域布局 |
| 未指定 | 标准不规定选哪个，但必须是合法值 | 函数实参求值顺序 |
| 未定义行为（UB） | 标准不做任何保证，编译器可以任意优化 | 数组越界、有符号溢出、空指针解引用 |

UB 的可怕之处在于「编译器假设它不会发生」：一旦违反，优化可能把整段逻辑改掉，甚至删除后面的检查。
### 10.2 数组越界与不安全函数
数组越界不报错，可能改坏栈上的其他变量，甚至被利用执行任意代码。`strcpy`、`strcat`、`sprintf` 不检查目标大小，例如 `char buf[8]; strcpy(buf, "0123456789");` 会溢出 3 字节；`gets` 从 C11 起被删除就是因为无法防溢出。

| 不安全 | 风险 | 替代 |
| --- | --- | --- |
| `strcpy` / `strcat` | 目标缓冲区溢出 | `snprintf`、先算长度 |
| `sprintf` | 无长度限制 | `snprintf`，检查返回值 |
| `gets` | 完全不检查长度 | `fgets` |
| `scanf("%s")` | 无宽度限制 | `scanf("%31s", buf)` 或 `fgets` |
| `strncpy` | 可能不补 `'\0'` | 手动补 `'\0'` 或 `snprintf` |

```c
#include <stdio.h>

int main(void)
{
    char buf[8];
    int n = snprintf(buf, sizeof buf, "%s", "0123456789");

    return n >= (int)sizeof buf;   /* 返回 1 表示被截断 */
}
```

`snprintf` 返回「想要写入的长度」（不含 `'\0'`），大于等于 `size` 说明被截断；拼接前先算总长度。
### 10.3 有符号溢出与求值顺序
有符号整数溢出是 UB，编译器可以假设它不发生并做激进优化；无符号溢出是回绕，行为有定义。

```c
#include <limits.h>

int main(void)
{
    int x = INT_MAX;
    unsigned u = UINT_MAX;

    x = x + 1;      /* 未定义行为 */
    u = u + 1;      /* 0，合法回绕 */
    return x + (int)u;
}
```

判断加法溢出用 `if (a > INT_MAX - b)`，或用 `__builtin_add_overflow`。`i++ + i++` 两个自增之间没有序列点（C11 称「无顺序」），是 UB；`i = i++ + 1` 同理。
### 10.4 动态内存与返回局部变量
`free` 后继续使用、重复释放、`free(&local)`、`free(p + 1)` 都是 UB；泄漏常见于丢失指针、提前 `return`、错误分支忘了 `free`。返回局部数组地址会得到悬垂指针：

```c
char *f(void)
{
    char buf[16] = "hi";
    return buf;             /* 函数返回后栈帧失效 */
}
```

修复：改成 `static char buf[16];`（不可重入）、`malloc`（调用方负责 free），或由调用方传入缓冲区。
### 10.5 sizeof 与 strlen
| 表达式 | 计算时机 | 结果 |
| --- | --- | --- |
| `sizeof("hello")` | 编译期 | 6（含 `'\0'`） |
| `strlen("hello")` | 运行期 | 5（不含 `'\0'`） |
| `sizeof(char *)` | 编译期 | 指针大小（32 位 4，64 位 8） |
| `sizeof(arr) / sizeof(arr[0])` | 编译期 | 元素个数（`arr` 未退化时） |

`sizeof` 是运算符，操作数不求值（`sizeof(i++)` 不会自增）；数组传参退化后，函数内不能再用 `sizeof` 求长度。
### 10.6 严格别名
编译器假设不同类型的指针不会指向同一块内存（`char *` 例外），否则优化会出错。`*(uint32_t *)&f` 是违反严格别名的 UB，`-O2` 下可能得到错误结果；正确写法是 `memcpy(&u, &f, sizeof u);`，它会被优化成一条 `mov`，没有性能损失。老代码可以用 `-fno-strict-aliasing` 兜底，但新代码应写对。其它高频陷阱：`if (a = 1)`、`switch` 漏 `break`、`scanf("%d", n)` 少 `&`、`printf("%d", sizeof(x))`、移位负数或超过位宽、除数为 0、修改字符串字面量、函数指针与 `void *` 互转。
### 10.7 少写 UB 的习惯
1. 打开 `-Wall -Wextra -Wpedantic -Wconversion -Wshadow`，CI 里加 `-Werror`。
2. 数组长度和缓冲区大小用 `sizeof`/宏统一，拼接用 `snprintf`。
3. 有符号数做溢出检查，或用无符号做位运算；不在一个表达式里对同一对象多次修改。
4. 动态内存遵循「谁分配谁释放」，释放后置 `NULL`。

## 11 调试与工具
### 11.1 编译告警与 Sanitizer
`-Wall -Wextra -Wpedantic -Wconversion -Wshadow` 能提前发现大部分类型不匹配、未使用变量、隐式截断；CI 里加 `-Werror` 把告警变错误。定位阶段用 `-O0 -g`，发布用 `-O2`。

| 选项 | 检查内容 | 开销 |
| --- | --- | --- |
| `-fsanitize=address` | 越界、use-after-free、double free、栈溢出 | 约 2 倍 |
| `-fsanitize=undefined` | 有符号溢出、空指针、移位越界、对齐错误 | 较小 |
| `-fsanitize=thread` | 数据竞争 | 较大 |
| `-fsanitize=leak` | 内存泄漏（常包含在 ASan 中） | 较小 |

ASan 需要编译器插桩，不能用于已发布的无插桩二进制；它和 valgrind 二选一，不要同时开。
### 11.2 ASan 报错示例
```c
#include <stdio.h>

int main(void)
{
    int a[3] = {0};

    for (int i = 0; i <= 3; i++) {      /* i == 3 时越界写 */
        a[i] = i;
    }
    printf("%d\n", a[0]);
    return 0;
}
```

```bash
gcc -std=c11 -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer demo.c -o demo
./demo
```

典型输出（地址和行号每次不同）：

```text
==12345==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7ffd...
WRITE of size 4 at 0x7ffd... thread T0
    #0 0x... in main /tmp/demo.c:8
SUMMARY: AddressSanitizer: stack-buffer-overflow /tmp/demo.c:8 in main
```

ASan 直接给出越界类型、地址、行号和调用栈，比 gdb 单步快得多。
### 11.3 gdb 常用命令
| 命令 | 作用 |
| --- | --- |
| `gcc -g -O0 demo.c -o demo` | 带调试信息编译 |
| `gdb ./demo` | 启动调试 |
| `run` / `r` | 运行程序 |
| `break main` / `b file.c:10` | 设置断点 |
| `next` / `n`；`step` / `s` | 单步不进入 / 进入函数 |
| `continue` / `c` | 继续到下一个断点 |
| `print x` / `p *p` | 打印变量或表达式 |
| `backtrace` / `bt` | 查看调用栈 |
| `x/16xb p` | 按十六进制查看内存 |
| `watch x` | 变量变化时中断 |
| `finish` / `quit` | 返回上一层 / 退出 |

段错误时先 `bt` 看栈，再 `frame N` 切到出错帧，`p` 看变量、`x` 看内存；`watch` 适合抓「谁改了它」。
### 11.4 valgrind 与加固
1. `valgrind --leak-check=full --show-leak-kinds=all ./demo` 检测内存泄漏和非法访问，无需重新编译，但慢 10~50 倍，主要用于 Linux。
2. `-fstack-protector-strong` 在栈帧里放 canary，检测返回地址被覆盖；加固还可加 `-Wl,-z,relro,-z,now` 和操作系统层面的 ASLR。
3. `strace` 看系统调用，`perf` 看性能热点，`objdump -d` 反汇编，`nm`/`readelf` 看符号和段。

## 12 面试延伸
以下是「详解里最容易被追问」的 8 个点，答案尽量能落到代码或命令上；完整题库见 [C面试题](C面试题.md)，库函数细节见 [C标准库速查](C标准库速查.md)。
### 12.1 八个追问
1. **结构体大小怎么算？位域呢？** 按成员对齐数算偏移并补齐，总大小取最大对齐数的倍数；位域按分配单元打包，不能跨单元，布局由实现定义。
2. **`const int *p`、`int * const p` 怎么区分？** const 在 `*` 左边锁数据、右边锁指针；`typedef` 会把指针整体变成类型名，`const P` 锁的是指针。
3. **`realloc` 为什么要用临时指针？** 失败返回 `NULL` 且原块不变，直接 `p = realloc(p, n)` 会丢掉原指针造成泄漏；成功可能搬移，旧指针失效。
4. **`i++ + i++` 为什么是 UB？** 两次修改之间没有序列点，编译器可以任意安排；拆成两条语句就没事。
5. **什么是严格别名？** 编译器假设不同类型的指针不重叠，`*(uint32_t *)&f` 违反规则，`-O2` 下可能算错；用 `memcpy` 或 `-fno-strict-aliasing`。
6. **有符号溢出为什么危险？** 它是 UB，编译器可以假设不发生，从而删掉 `if (x + 1 < x)` 这类检查；无符号溢出才是回绕。
7. **静态库和动态库链接有什么差别？** `.a` 链接时把用到的 `.o` 复制进可执行文件，`.so` 只记录依赖、运行时加载；共享库要 `-fPIC`。
8. **`malloc` 一定走 `brk` 吗？`free` 后 RSS 为什么不降？** 小块走 `brk`、大块走 `mmap`，`free` 只还给 arena，不保证还给 OS。

### 12.2 自测与延伸
自测建议：合上文档，手写 `struct` 对齐计算、`realloc` 正确用法、一个 ASan 能抓到的越界例子，再对照 [C面试题](C面试题.md) 的题库查漏。
