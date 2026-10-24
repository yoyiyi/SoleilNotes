## 1 前言与 C 语言概述

### 1.1 前言
关于 C/C++ 这两个玩意，自从大学毕业之后，接触到的地方也比较少了，抽空把以前零散笔记整理下，不过以前也是整理菜鸟教程。虽然业务中涉及到的 C/C++ 部分，有专门 C 大佬搞。但是 Android 底层涉及到 C/C++，看一些源码 C/C++ 还是非常重要的。
本次整理按「基础语法 → 指针与内存 → 结构体与联合 → 预处理器 → 文件与 IO → 进阶与陷阱 → 面试」重排，代码尽量给成可编译片段，缩进统一 4 空格，主函数统一 `int main(void)`。

### 1.2 C 语言简介
1. 通用、面向过程的语言，1972 年为移植与开发 UNIX，丹尼斯·里奇在贝尔电话实验室设计开发。
2. 最新标准是 C23（ISO/IEC 9899:2024），工程中最常见的编译选项仍是 C99/C11。
3. 第一个程序：

```c
#include <stdio.h>      /* 头文件：声明 printf */

int main(void)          /* 主函数，程序入口 */
{
    printf("Hello World\n");
    return 0;           /* 0 表示成功 */
}
```

编译运行：`gcc -std=c11 -Wall -Wextra hello.c -o hello`。

### 1.3 C 语言特点
1. 易于学习、结构化。
2. 产生高效率的程序，运行速度接近汇编。
3. 可以处理底层活动：内存、位、寄存器映射。
4. 可在多种计算机平台上编译。
5. 生态成熟，是操作系统、数据库、嵌入式以及 C++/Rust FFI 的基础。

### 1.4 关于 C
1. 为编写 UNIX 操作系统而发明，以 B 语言为基础。
2. 第一个标准由 ANSI 制定（C89），之后交给 ISO 维护（C90 及以后）。
3. 截止 1973 年，UNIX 操作系统完全使用 C 编写。
4. 大多数系统软件由 C 编写：Linux 内核、MySQL、编译器、嵌入式固件。
5. C 语言是最广泛使用的语言之一。

### 1.5 为什么要使用 C
1. 代码运行速度与汇编语言几乎一样。
2. 可移植性好：同一份源码换平台重新编译即可。
3. 贴近硬件，适合驱动、协议栈、RTOS。
4. 几乎所有平台都有 C 编译器，也是其他语言 FFI 的基础。

### 1.6 C 标准演进

| 标准 | 发布 | 标准号 | 关键变化 | `__STDC_VERSION__` |
| --- | --- | --- | --- | --- |
| C89/C90 | 1989/1990 | ANSI X3.159-1989、ISO/IEC 9899:1990 | 首个标准：函数原型、`void *`、`const`/`volatile` | 未定义（只定义 `__STDC__`） |
| C95 | 1995 | ISO/IEC 9899:1990/Amd 1 | 宽字符、双字符组 | `199409L` |
| C99 | 1999 | ISO/IEC 9899:1999 | `//` 注释、`stdbool.h`、VLA、`inline`、指定初始化器 | `199901L` |
| C11 | 2011 | ISO/IEC 9899:2011 | `_Generic`、`_Static_assert`、原子操作、线程库、删除 `gets` | `201112L` |
| C17/C18 | 2018 | ISO/IEC 9899:2018 | 只做缺陷修复，无新特性 | `201710L` |
| C23 | 2024 | ISO/IEC 9899:2024 | `bool`/`true`/`false`、`constexpr`、`nullptr`、`auto`、`typeof` | `202311L` |

**C99**：`//` 行注释；`<stdbool.h>` 提供 `bool`/`true`/`false`（底层 `_Bool`）；变长数组 `int a[n];`（C11 起为可选特性）；`inline`；指定初始化器 `{.x = 1}`、`[2] = 3`；另有 `long long`、`stdint.h`、`restrict`、复合字面量、变参宏、柔性数组、`snprintf`。
**C11**：`_Generic` 按类型选择分支，如 `#define TYPE_NAME(x) _Generic((x), int: "int", double: "double", default: "other")`；`_Static_assert(常量, "消息")` 编译期断言；`<stdatomic.h>` 原子操作；`<threads.h>` 线程库（可选，很多嵌入式工具链不提供）；匿名结构体/共用体、`aligned_alloc`；`gets` 从标准删除；VLA/复数/原子/线程为可选特性，可用 `__STDC_NO_VLA__` 等宏判断。
**C17**：只修缺陷（DR），不引入新特性，常被当作「C11 的稳定修订版」。
**C23**：`bool`/`true`/`false` 成为关键字；`constexpr` 编译期常量对象（与 C++ 的 constexpr 函数不同）；`nullptr`（类型 `nullptr_t`，定义在 `<stddef.h>`）；`auto x = 1;` 类型推断（与早期存储类 auto 含义不同）；`typeof`/`typeof_unqual`；另有 `_BitInt(N)`、`[[nodiscard]]` 等属性、`#embed`、`0b1010`、`1'000'000`、`#elifdef`。注意 `constexpr`/`auto`/`typeof` 与 C++ 语义不完全相同。

### 1.7 编译器与嵌入式支持现状

| 编译器 | C99 | C11 | C17 | C23 | 说明 |
| --- | --- | --- | --- | --- | --- |
| GCC | 完整 | 完整 | 完整 | GCC 14 起 `-std=c23` 逐步完善 | 桌面、服务器、交叉编译主力 |
| Clang | 完整 | 完整 | 完整 | Clang 18 起逐步支持 | macOS、iOS、Android NDK |
| MSVC | 部分 | `/std:c11` | `/std:c17` | 部分 | 不支持 VLA 等可选特性 |
| arm-none-eabi-gcc | 视版本 | 视版本 | 视版本 | 视版本 | 交叉工具链升级慢 |
| Keil MDK AC5/AC6 | AC5 部分、AC6 较完整 | AC6 | 视版本 | 视版本 | 以编译器文档为准 |
| IAR EWARM | 支持 | 支持 | 视版本 | 部分 | 以编译器文档为准 |

1. 支持情况用 `__STDC_VERSION__` 实测：C99 为 `199901L`，C11 为 `201112L`，C17 为 `201710L`，C23 为 `202311L`，C89/C90 不定义该宏；不确定的以编译器文档为准。
2. 嵌入式常锁定 `-std=c99` 或 `-std=c11` 并开 `-Wpedantic`；C11 的线程库和原子操作在无 OS 或 RTOS 上未必可用。
3. MISRA 等规范通常禁用 VLA 和动态内存；C23 新特性在旧工具链上不可用，落地前先确认编译器版本。

## 2 编译、链接与程序结构

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

排查手段：`nm` 看符号，`ldd` 看动态依赖，`size` 看各段大小，`readelf -S` 看段表。

### 2.3 static 与 extern 在链接层面的区别

| 写法 | 链接属性 | 可见性 | 典型用途 |
| --- | --- | --- | --- |
| 文件作用域 `static` 变量/函数 | 内部链接 | 仅本翻译单元 | 隐藏实现细节，避免命名冲突 |
| `extern` 声明 | 外部链接 | 全程序 | 引用其他 `.c` 中定义的符号 |
| 普通全局定义 | 外部链接 | 全程序 | 提供符号 |
| 函数内 `static` 局部变量 | 无链接，静态存储期 | 仅函数内 | 计数器、单次初始化 |

链接器只认符号：只有声明没有定义会报 `undefined reference to 'foo'`，同一个强符号定义两次会报 `multiple definition of 'foo'`（GCC 10 起默认 `-fno-common`，旧代码的「暂定定义」会暴露）。

```c
/* util.c */
static int counter;                          /* 内部链接，其他文件看不到 */
static void helper(void) { }                 /* 内部链接 */
int util_call(void) { counter++; helper(); return counter; }   /* 外部链接 */
```

`static` 函数在 `nm` 输出里是小写 `t`，外部函数是大写 `T`。

### 2.4 头文件与头文件卫士
1. `#include <file>` 从系统目录和 `-I` 指定目录查找；`#include "file"` 先查当前源文件目录，再查系统目录。
2. 头文件卫士防止同一个头文件被重复包含：

```c
#ifndef MY_HEADER_H
#define MY_HEADER_H

/* 声明、宏、类型定义 */

#endif /* MY_HEADER_H */
```

3. `#pragma once` 非标准但主流编译器都支持，它按「文件」去重，遇到同一文件的不同路径副本会失效，卫士按宏去重更可靠。
4. 头文件只放声明：函数原型、`extern` 变量、类型定义、宏、`static inline` 函数；把变量或普通函数定义放进头文件，多文件链接时会重复定义。

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
1. 组成：预处理器指令、函数、变量、语句与表达式、注释。
2. 一个源文件的标准骨架：

```c
#include <stdio.h>              /* 1. 预处理指令 */
#define MAX 100                 /* 2. 宏定义 */
int g_count;                    /* 3. 全局变量（定义） */
static int helper(int x);       /* 4. 函数声明 */
int main(void)                  /* 5. 主函数：程序入口 */
{
    int local = helper(1);      /* 6. 语句、表达式 */
    printf("%d %d\n", local, MAX);
    return 0;
}

static int helper(int x)        /* 7. 函数定义 */
{
    return x + 1;
}
```

3. 令牌（Tokens）：C 程序由关键字、标识符、常量、字符串字面量、运算符与标点组成，编译器先切分成令牌再做语法分析。
4. 注释：`/* ... */`（C89）与 `//`（C99）。注释在预处理阶段被替换成一个空格，`/* */` 不能嵌套，不要用注释屏蔽含 `*/` 的代码。
5. 标识符：由字母、数字、下划线组成，不能以数字开头，不允许 `@`、`$`、`%`，区分大小写；C99 起外部标识符至少 31 个有效字符、内部至少 63 个。
6. 关键字不能作为标识符：C89 有 32 个（`auto`、`break`、`case`、`char`、`const`、`continue`、`default`、`do`、`double`、`else`、`enum`、`extern`、`float`、`for`、`goto`、`if`、`int`、`long`、`register`、`return`、`short`、`signed`、`sizeof`、`static`、`struct`、`switch`、`typedef`、`union`、`unsigned`、`void`、`volatile`、`while`）；C99 增加 `inline`、`restrict`、`_Bool`、`_Complex`、`_Imaginary`；C11 增加 `_Alignas`、`_Alignof`、`_Atomic`、`_Generic`、`_Noreturn`、`_Static_assert`、`_Thread_local`；C23 又把 `bool`、`true`、`false`、`constexpr`、`nullptr`、`auto`、`typeof` 等变成关键字。
7. 空白：只含空格的行是空白行，编译器忽略；空白用于分隔令牌（`int x` 不能写成 `intx`），`a+++b` 按最长匹配解析为 `a++ + b`，不要依赖这种写法。

## 3 数据类型、变量与常量

### 3.1 数据类型总览

| 类型 | 说明 |
| --- | --- |
| 基本类型 | 整数类型、浮点类型 |
| 枚举类型 | 也是算术类型，用来定义只能赋予一定离散整数值的变量 |
| void 类型 | 类型说明符，没有可用值 |
| 派生类型 | 指针、数组、结构、共用体、函数类型 |

1. 数组类型和结构类型称为聚合类型。
2. C 是静态类型语言：变量类型在编译期确定，运算前会做隐式类型转换。

### 3.2 整数类型

| 类型 | 典型字节 | 典型范围 | 说明 |
| --- | --- | --- | --- |
| `char` | 1 | -128~127 或 0~255 | 是否有符号由实现决定 |
| `signed char` | 1 | -128~127 | 明确有符号 |
| `unsigned char` | 1 | 0~255 | 明确无符号，常存字节 |
| `short` | 2 | -32768~32767 | 至少 16 位 |
| `unsigned short` | 2 | 0~65535 | |
| `int` | 2 或 4 | -32768~32767 或 -2147483648~2147483647 | 现代桌面/服务器为 4 字节 |
| `unsigned int` | 2 或 4 | 0~65535 或 0~4294967295 | |
| `long` | 4 或 8 | 至少 32 位 | Windows 64 位 4 字节，Linux 64 位 8 字节 |
| `unsigned long` | 4 或 8 | 至少 32 位 | |
| `long long` | 8 | 至少 64 位 | C99 引入 |

1. 标准只规定最小范围（见 `<limits.h>`），准确大小用 `sizeof` 在目标平台确认。
2. `sizeof` 的结果类型是 `size_t`，`printf` 用 `%zu` 输出；用 `sizeof(char)`、`sizeof(int)`、`sizeof(void *)` 可在目标平台上实测。
3. 嵌入式、协议解析、跨平台序列化优先用 `<stdint.h>` 的 `int8_t`、`uint16_t` 等定宽类型。

### 3.3 浮点类型

| 类型 | 存储大小（字节） | 值范围 | 精度（十进制位） |
| --- | --- | --- | --- |
| `float` | 4 | 1.2E-38 ~ 3.4E+38 | 6~7 |
| `double` | 8 | 2.3E-308 ~ 1.7E+308 | 15~16 |
| `long double` | 16（x86 为 80 位扩展精度，占 16 字节） | 3.4E-4932 ~ 1.1E+4932 | 18~19 |

1. 浮点数在内存中是二进制近似值，`0.1 + 0.2 != 0.3`，不要用 `==` 比较，判断相等用 `fabs(a - b) < 1e-9`（`<math.h>`，链接 `-lm`）。
2. 浮点常量默认是 `double`，要 `float` 加后缀 `f`；`printf` 用 `%f`（double）和 `%Lf`（long double）。

### 3.4 void 类型
1. 函数返回为空：`void log_msg(const char *msg);`
2. 函数参数为空：`int main(void)`，表示不接收参数。
3. 指针指向 void：`void *` 代表对象的地址，可与对象指针隐式互转，但不能解引用，也不能做指针算术。

### 3.5 变量定义与声明
1. 定义：分配存储空间，如 `int a;`、`int a = 1;`，只能有一次。
2. 声明：告诉编译器名字和类型，不一定分配空间，如 `extern int i;`，可以有多次。

```c
/* main.c */
#include <stdio.h>

int x = 1;                  /* 定义，分配存储 */
int y = 2;
int addtwonum(void);        /* 声明 */

int main(void) { printf("%d\n", addtwonum()); return 0; }
```

```c
/* addtwonum.c */
extern int x;               /* 声明，定义在 main.c 中 */
extern int y;

int addtwonum(void) { return x + y; }
```

编译：`gcc main.c addtwonum.c -o demo`。

### 3.6 左值与右值
1. 左值：可以出现在赋值号左边，表示一个可定位的存储位置，如变量、数组元素、`*p`、结构体成员。
2. 右值：只能出现在右边，是临时值，如 `1`、`a + b`、函数返回值。
3. 左值可以转换成右值使用；`const` 变量是「不可修改的左值」。
4. `&` 只能作用于左值，`&(a + b)` 编译错误。

### 3.7 常量
1. 常量是固定值，执行期间不会改变，又叫字面量。

| 常量类型 | 例子 | 说明 |
| --- | --- | --- |
| 整数常量 | `221`、`215u`、`0xFeeL`、`0755` | `0` 开头八进制，`0x` 十六进制，`u`/`l` 后缀 |
| 浮点常量 | `3.142`、`1.5e-3`、`2.0f` | 默认 `double`，`f` 后缀为 `float` |
| 字符常量 | `'x'`、`'\t'`、`'\0'` | C 中类型是 `int`，不是 `char` |
| 字符串常量 | `"hello"` | 以 `'\0'` 结尾，存放在只读区 |

2. 定义常量的两种方式：

```c
#define MAX 100          /* 预处理替换：无类型、无作用域、无分号 */
const int LIMIT = 100;   /* 有类型、编译期检查、有作用域，推荐 */
```

3. 常见错误：`#define MAX 100;` 多了分号，展开后 `int buf[MAX;];` 直接语法错误。

### 3.8 存储类
1. 存储类定义变量/函数的范围（可见性）和生命周期，说明符放在类型之前。

| 存储类 | 作用域 | 生命周期 | 说明 |
| --- | --- | --- | --- |
| `auto` | 块 | 自动 | 局部变量默认，C 中几乎不写 |
| `register` | 块 | 自动 | 建议放寄存器，不能取地址；现代编译器会忽略 |
| `static` | 块或文件 | 静态 | 局部：只初始化一次、生命周期贯穿程序；全局/函数：内部链接 |
| `extern` | 全局 | 静态 | 声明外部符号，不分配空间 |

```c
void f(void)
{
    auto int month = 1;     /* 显式写法，C 中无实际意义（C23 起 auto 语义改变） */
    register int i = 0;     /* 不能取地址：&i 编译错误 */
    int mount = month + i;  /* 局部变量默认就是 auto */

    (void)mount;
}
```

```c
#include <stdio.h>

static int g_counter;           /* 文件作用域：内部链接 */

static void bump(void)          /* 函数：内部链接，其他文件不可见 */
{
    static int n = 0;           /* 静态局部变量：只初始化一次 */
    n++;
    g_counter++;
    printf("n = %d, g = %d\n", n, g_counter);
}

int main(void)
{
    bump();
    bump();
    return 0;
}
```

1. `extern` 声明外部符号，不给初值：`extern int count = 5;` 是定义而不是声明；跨文件示例见 3.5。
2. `static` 全局变量和函数只在本文档内可见，是 C 里实现「私有」的主要手段。

### 3.9 作用域与生命周期
1. 局部变量：块作用域，函数返回即销毁（`static` 除外）。
2. 全局变量：文件作用域，程序启动时分配、结束时释放，未初始化默认为 0。
3. 形式参数：函数作用域，等价于局部变量。
4. 存储期分三种：自动存储期（栈）、静态存储期（`.data`/`.bss`）、动态存储期（堆，`malloc`）。
5. 局部 `static` 变量只初始化一次，函数多次调用会保留上次的值；全局变量未初始化时默认为 0，这两个现象都由存储期决定。

### 3.10 强制类型转换与整型提升
1. 语法：`(type)expression`，只影响这一次表达式的解释，不改变变量本身的类型。例：`mean = (double)sum / count;`、`(int)3.99 == 3`、`(int)-3.99 == -3`（向零截断）。
2. 整数提升：小于 `int` 的整数类型（`char`、`short`、位域、枚举）先提升为 `int` 或 `unsigned int` 再运算。
3. 寻常算术转换：`int` 与 `double` 运算时转 `double`；`int` 与 `unsigned int` 运算时转 `unsigned int`。
4. 经典坑：

```c
#include <stdio.h>

int main(void)
{
    int a = -1;
    unsigned int b = 1;

    printf("%d\n", a < b);              /* 0：a 被转成无符号大数 */
    printf("%d\n", -1 < sizeof(int));   /* 0 */
    return 0;
}
```

5. 指针转换：`void *` 与对象指针互转可隐式；函数指针与 `void *` 互转不可移植；`(void *)0` 是空指针常量。建议有符号与无符号不要混用，打开 `-Wsign-compare`。

## 4 运算符与控制流

### 4.1 运算符总览

| 运算符 | 符号 |
| --- | --- |
| 算术 | `+`、`-`、`*`、`/`、`%`、`++`、`--` |
| 关系 | `==`、`!=`、`>`、`<`、`>=`、`<=` |
| 逻辑 | `&&`、`!`、`\|\|` |
| 位 | `&`、`\|`、`^`、`~`、`<<`、`>>` |
| 赋值 | `=`、`+=`、`-=`、`*=`、`/=`、`%=` 等 |
| 杂项 | `sizeof()`、`&`、`*`、`?:`、`,`、`->`、`.` |

1. 整数除法向零截断，`%` 只能用于整数，结果符号与被除数一致（`-7 % 3 == -1`）。
2. `&&` 和 `||` 有短路求值，`&` 和 `|` 没有；`if (p != NULL && p->x)` 依赖短路才安全。
3. 位运算管理标志位：`flags |= MASK;`、`flags &= ~MASK;`、`if (flags & MASK)`；`sizeof` 是运算符，操作数不求值（`sizeof(i++)` 不会自增）。

### 4.2 优先级与结合性
优先级从高到低：`()`/`[]`/`->`/`.` → 单目（`!`、`~`、`++`、`--`、正负号、`*`、`&`、`(type)`、`sizeof`，右结合）→ `*`/`/`/`%` → `+`/`-` → `<<`/`>>` → 关系运算 → `==`/`!=` → `&` → `^` → `|` → `&&` → `||` → `?:`（右结合）→ 赋值（右结合）→ `,`。
记不住就加括号：`*p++` 等价于 `*(p++)`，`(*p)++` 才是自增所指对象。

### 4.3 判断语句
1. `if` / `if...else` / `else if` 链按条件从上到下匹配；简单二选一用三元运算符更紧凑：`int max = a > b ? a : b;`。
2. `switch` 适合多分支等值判断：

```c
#include <stdio.h>

int main(void)
{
    char ch = 'A';

    switch (ch) {
    case 'a':
    case 'A':                   /* 多个 case 共用一段逻辑 */
        printf("A\n");
        break;                  /* 忘了 break 会贯穿到下一个 case */
    case 'b':
        printf("B\n");
        break;
    default:
        printf("other\n");
        break;
    }
    return 0;
}
```

3. `switch` 的表达式必须是整型（含 `char`、枚举），`case` 必须是整型常量表达式且不能重复；浮点数不要用 `==` 比较。
4. `if (a = b)` 是赋值不是比较，`-Wparentheses` 会告警，要当错误看。

### 4.4 循环语句
1. `while`、`for`、`do...while` 与嵌套循环：

```c
#include <stdio.h>

int main(void)
{
    int i;

    for (i = 0; i < 3; i++) {           /* C99 起可写 for (int i = 0; ...) */
        printf("for: %d\n", i);
    }

    i = 0;
    while (i < 3) {
        printf("while: %d\n", i);
        i++;
    }

    i = 0;
    do {
        printf("do-while: %d\n", i);    /* 至少执行一次 */
        i++;
    } while (i < 3);

    return 0;
}
```

2. `for` 适合已知次数，`while` 适合条件驱动，`do...while` 适合「至少执行一次」；循环边界用 `<` 而不是 `<=` 可减少越界。

### 4.5 循环控制

| 关键字 | 简介 |
| --- | --- |
| `break` | 跳出当前循环或 `switch` |
| `continue` | 跳过本次迭代，进入下一次 |
| `goto` | 跳转到同函数内的标号，不建议滥用，常用于统一错误清理 |

```c
void loop_demo(void)
{
    int a = 10;

LOOP:
    a++;
    if (a < 20) {
        goto LOOP;              /* 跳回同函数的标号 */
    }
}
```

1. `goto` 的合理用法是集中清理：申请资源后失败就 `goto cleanup`，在函数末尾统一 `free`/`fclose`，避免每层重复写清理代码。
2. 不要用 `goto` 向后跳转构造循环，也不要跨函数跳转（C 不支持）。

## 5 函数

### 5.1 函数的定义与声明
1. 每个 C 程序都有入口 `main`，返回 `int`；函数先声明后使用，原型让编译器检查参数类型。

```c
#include <stdio.h>

int max(int num1, int num2);        /* 函数声明（原型） */

int main(void)
{
    printf("max = %d\n", max(1, 6));
    return 0;
}

int max(int num1, int num2)         /* 函数定义 */
{
    return num1 > num2 ? num1 : num2;
}
```

2. `int main()` 在 C 中表示参数未指定（K&R 风格），应写 `int main(void)`；带参数用 `int main(int argc, char *argv[])`。
3. 非 `void` 函数所有路径都应有 `return`；`main` 末尾省略 `return` 等价于 `return 0`（C99 起）。

### 5.2 函数参数：传值调用与传址调用
1. C 只有传值调用，所谓「引用调用」是传指针，函数内通过 `*p` 修改实参。

```c
#include <stdio.h>

void swap(int *a, int *b)
{
    int t = *a;
    *a = *b;
    *b = t;
}

int main(void)
{
    int x = 1, y = 2;

    swap(&x, &y);                       /* 传地址，x 和 y 才真正交换 */
    printf("x = %d, y = %d\n", x, y);   /* 2 1 */
    return 0;
}
```

2. 如果写成 `void swap(int a, int b)`，函数内只交换副本，实参不变。
3. 数组作为参数会退化为指针，函数内 `sizeof(arr)` 得到指针大小，因此必须额外传长度；较大的结构体建议传 `const struct S *`。

### 5.3 递归
1. 函数自己调用自己，必须有终止条件，否则栈溢出。

```c
#include <stdio.h>

long factorial(int n)
{
    if (n <= 1) {
        return 1;                   /* 终止条件 */
    }
    return n * factorial(n - 1);
}

int main(void)
{
    printf("5! = %ld\n", factorial(5));
    return 0;
}
```

2. 每层递归都占一个栈帧，深度过大（如十万层）会栈溢出，嵌入式栈通常只有几 KB；C 标准不保证尾递归优化，朴素斐波那契递归是 O(2^n)。

### 5.4 可变参数
1. `<stdarg.h>` 提供 `va_list`、`va_start`、`va_arg`、`va_end` 四个要素。

```c
#include <stdarg.h>
#include <stdio.h>

double average(int num, ...)
{
    va_list ap;
    double sum = 0.0;
    int i;

    va_start(ap, num);                  /* 绑定最后一个固定参数 */
    for (i = 0; i < num; i++) {
        sum += va_arg(ap, int);         /* 必须按 int 读取 */
    }
    va_end(ap);

    return num > 0 ? sum / num : 0.0;
}
```

2. 可变参数没有类型检查，个数和类型靠调用方与格式串约定；默认实参提升：`char`/`short` 传成 `int`，`float` 传成 `double`，所以 `va_arg(ap, char)` 是错的。
3. C23 起 `va_start` 允许省略第二个参数（以编译器文档为准）。

### 5.5 命令行参数
1. `int main(int argc, char *argv[])`：`argc` 是参数个数（含程序名），`argv` 是字符串数组，`argv[argc]` 为 `NULL`。

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    for (int i = 0; i < argc; i++) {
        printf("argv[%d] = %s\n", i, argv[i]);   /* argv[0] 是程序名 */
    }
    if (argc > 1) {
        printf("n * 2 = %ld\n", strtol(argv[1], NULL, 10) * 2);
    }
    return 0;
}
```

2. `argv[0]` 是程序名（可能带路径）；第三个参数 `envp` 不是标准，但多数平台支持。
3. 数字参数用 `strtol` 或 `sscanf` 转换并检查 `errno`/`endptr`，不要直接把字符串指针强转成整数指针。

## 6 数组与字符串

### 6.1 数组的声明、初始化与访问

```c
#include <stdio.h>

int main(void)
{
    double balance[5] = {100.0, 2.0};       /* 其余元素自动补 0 */
    int a[] = {1, 2, 3};                    /* 长度由初始化列表决定：3 */
    int matrix[2][3] = {{1, 2, 3}, {4, 5, 6}};

    printf("%zu %zu\n", sizeof(balance), sizeof(balance[0]));
    printf("%.1f %d %d\n", balance[1], a[2], matrix[1][2]);
    balance[4] = 9.9;                       /* 访问与修改 */
    return 0;
}
```

1. 数组下标从 0 开始，越界是未定义行为，编译器不检查。
2. 局部数组不初始化时元素是随机值，`= {0}` 可全部清零。
3. 二维数组按行优先连续存放，`matrix[i][j]` 等价于 `*(*(matrix + i) + j)`。
4. C99 变长数组 `int a[n];` 在栈上分配，C11 起为可选特性，`n` 过大会栈溢出。

### 6.2 数组作为函数参数

```c
#include <stdio.h>

void print_array(const int arr[], int len)   /* 等价于 const int *arr */
{
    int i;

    for (i = 0; i < len; i++) {
        printf("%d ", arr[i]);
    }
    printf("\nsizeof(arr) = %zu\n", sizeof(arr));   /* 指针大小，不是数组大小 */
}

int main(void)
{
    int a[5] = {1, 2, 3, 4, 5};

    print_array(a, 5);
    return 0;
}
```

1. `int param[]`、`int param[10]`、`int *param` 在参数位置完全等价，长度信息全部丢失。
2. 数组大小要在数组还没「退化」的作用域里算：`sizeof(a) / sizeof(a[0])`。

### 6.3 字符串与 '\0'
1. 字符串实际上是使用 null 字符 `'\0'` 终止的一维字符数组：`char s[6] = {'H','e','l','l','o','\0'};` 与 `char s[] = "Hello";` 等价。
2. 字符串字面量的类型是 `char[6]`，存放在只读区，修改它（`s[0] = 'h'`）是未定义行为，应写 `const char *`。
3. 字符 `'A'` 与字符串 `"A"` 不同：前者是 `int`，后者是 2 字节数组。
4. UTF-8 下中文按字节计长度，`strlen("中文")` 得到 6 而不是 2。

### 6.4 常用字符串函数
1. 使用前 `#include <string.h>`。

| 函数 | 简介 |
| --- | --- |
| `strcpy(s1, s2)` | 复制字符串 s2 到 s1，不检查目标大小 |
| `strcat(s1, s2)` | 把 s2 连接到 s1 末尾 |
| `strlen(s1)` | 返回长度，不含 `'\0'`，类型为 `size_t` |
| `strcmp(s1, s2)` | 相等返回 0；s1 < s2 返回负数；s1 > s2 返回正数 |
| `strchr(s1, ch)` | 返回指向 s1 中字符 ch 首次出现位置的指针 |
| `strstr(s1, s2)` | 返回指向 s1 中子串 s2 首次出现位置的指针 |

```c
#include <stdio.h>
#include <string.h>

int main(void)
{
    char s1[40] = "Hello";
    char s2[20] = "World";

    strcat(s1, " ");
    strcat(s1, s2);                                 /* s1 = "Hello World" */
    printf("%zu %s %s\n", strlen(s1), strstr(s1, "lo"), strchr(s1, 'W'));
    strcpy(s2, "C");                                /* 目标必须足够大 */
    printf("%s\n", s2);
    return 0;
}
```

2. `strcmp` 只看返回值的正负，具体数值不要依赖；`strcpy`、`strcat`、`strlen` 都以 `'\0'` 为界，源字符串没有终止符会越界读。

### 6.5 sizeof、strlen 与安全版本

| 表达式 | 计算时机 | 结果 |
| --- | --- | --- |
| `sizeof("hello")` | 编译期 | 6（含 `'\0'`） |
| `strlen("hello")` | 运行期 | 5（不含 `'\0'`） |
| `sizeof(char *)` | 编译期 | 指针大小（32 位 4，64 位 8） |
| `sizeof(arr) / sizeof(arr[0])` | 编译期 | 元素个数（`arr` 未退化时） |

1. `strncpy(dst, src, n)` 最多拷 n 字节，src 短时用 0 填充，但不保证 `'\0'`；`strncat` 总是补 `'\0'`。
2. 推荐 `snprintf(buf, sizeof buf, "%s", src)`：保证 `'\0'`，返回「想要写入的长度」，大于等于 size 说明被截断。
3. `strlcpy`/`strlcat` 语义更安全，但不是标准（BSD、glibc 2.38+ 提供），跨平台慎用。

## 7 指针与内存

### 7.1 指针基础与指针运算
1. `&` 取地址，`*` 解引用；指针必须先声明再赋值，未初始化的指针就是野指针。

```c
#include <stdio.h>

int main(void)
{
    int var = 20;
    int arr[3] = {100, 200, 300};
    int *ip = &var;                 /* 必须初始化，否则是野指针 */
    int *p = arr;                   /* 数组名退化为首元素地址 */
    int i;

    *ip = 21;                       /* 通过指针修改 var */
    printf("var = %d, %p\n", var, (void *)ip);

    for (i = 0; i < 3; i++) {
        printf("%d ", *(p + i));    /* +1 前进一个 int，不是一个字节 */
    }

    p = &arr[2];
    printf("\n%d %d\n", p[0], p[-2]);   /* 等价于 *(p-2)，下标可以是负数 */
    return 0;
}
```

2. 指针的大小与所指类型无关：32 位平台 4 字节，64 位平台 8 字节。
3. 指针算术只能在同一数组（或同一对象）内部进行：指向「最后一个元素的下一个位置」合法，可以比较、可以计算，但不能解引用。
4. 两个指针相减得到 `ptrdiff_t`，表示相隔的元素个数，不是字节数。

### 7.2 指针与数组的区别

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

    printf("sizeof(a) = %zu, sizeof(p) = %zu\n", sizeof(a), sizeof(p));   /* 20 8 */
    printf("%td\n", (char *)(&a + 1) - (char *)(a + 1));                  /* 16：&a 跨越整个数组 */
    return 0;
}
```

数组名退化的例外：`sizeof`、`&`、`_Alignof`、用于初始化字符数组的字符串字面量。

### 7.3 指针数组、数组指针与多级指针

```c
int *ptr[3];        /* 指针数组：3 个 int * */
int (*parr)[3];     /* 数组指针：指向 int[3] 的指针 */
```

1. `int *ptr[3]` 是「指针数组」，`ptr[i]` 是 `int *`，常用来存一组字符串：`const char *names[] = {"zz", "aa"};`。
2. `int (*parr)[3]` 是「数组指针」，`(*parr)[i]` 取到元素，`parr + 1` 跨越整个 `int[3]`，常用于二维数组传参。
3. `int **pptr` 是二级指针，`*pptr` 取回一级指针，`**pptr` 取到值；常用于在函数内修改「指针本身」：`void alloc(int **out)`。
4. `const char *argv[]` 与 `char **argv` 是同一个意思。

### 7.4 const 与指针、void *

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
    int a = 1;
    int b = 2;
    const int *p1 = &a;         /* 不能 *p1 = 3，但可以 p1 = &b */
    int * const p2 = &a;        /* 可以 *p2 = 3，但 p2 不能再指向 b */
    const int * const p3 = &a;  /* 两者都不行 */

    p1 = &b;
    *p2 = 3;
    printf("%d %d %d\n", *p1, *p2, *p3);   /* 2 3 3 */
    return 0;
}
```

1. `char *` 不能直接指向字符串字面量，应写 `const char *`；字面量在只读区，写入是未定义行为。
2. `void *` 是通用对象指针，可与任意对象指针隐式互转，但不能解引用、不能做指针算术（标准不允许，GCC 扩展按 1 字节处理）；`malloc` 的返回值就是 `void *`，C 中不需要强制转换。

### 7.5 函数指针与回调
1. 函数指针保存函数入口地址，用来实现回调、状态机、跳转表。

```c
#include <stdio.h>

int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }

typedef int (*binop_t)(int, int);       /* 函数指针类型 */

int apply(binop_t op, int a, int b)     /* 回调：行为由调用方决定 */
{
    return op(a, b);
}

int main(void)
{
    int (*fp)(int, int) = add;          /* 取地址的 & 可以省略 */
    binop_t table[] = {add, sub};       /* 函数指针数组 */

    printf("%d %d %d\n", fp(2, 3), apply(sub, 5, 2), table[1](5, 2));   /* 5 3 3 */
    return 0;
}
```

2. 典型回调是 `qsort` 的比较函数：`int cmp(const void *a, const void *b)`，返回负数/0/正数表示小于/等于/大于。
3. 函数指针的解引用 `(*fp)()` 与直接调用 `fp()` 等价；`*fp` 不改变语义。

### 7.6 内存布局

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

1. 用 `size a.out` 看 text/data/bss 大小，`nm` 看符号，`readelf -S` 看段表。
2. 栈由编译器与操作系统管理，大小固定（Linux 默认 8 MB 左右），递归过深或超大局部数组会栈溢出。
3. 堆由分配器管理；栈和堆之间是尚未映射的空闲区域，由 ASLR 随机化；`.bss` 不占可执行文件空间，运行时由内核清零，所以「未初始化全局变量为 0」有保证。

### 7.7 malloc / free 与 brk / mmap
1. `malloc` 在堆上分配指定字节数，返回 `void *`，失败返回 `NULL`；`free` 归还内存。

```c
#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    int n = 10;
    int *p = malloc((size_t)n * sizeof *p);   /* 不要写死 sizeof(int) */

    if (p == NULL) {                          /* 必须检查失败 */
        perror("malloc");
        return EXIT_FAILURE;
    }
    for (int i = 0; i < n; i++) {             /* C99 起可在 for 内声明 */
        p[i] = i;
    }
    printf("p[9] = %d\n", p[9]);

    free(p);
    p = NULL;                                 /* 防止悬垂指针 */
    return 0;
}
```

2. glibc 的 `malloc` 使用 ptmalloc2：小块内存通过 `brk`/`sbrk` 抬高堆顶，大块内存（默认 ≥ 128 KiB，`M_MMAP_THRESHOLD` 可调）直接用 `mmap` 映射。
3. `free` 只把块还给分配器（arena），不保证立刻还给操作系统，所以进程 RSS 可能不下降。
4. `malloc(0)` 可能返回 `NULL` 或一个可 `free` 的唯一指针；`free(NULL)` 是空操作；重复 `free` 是未定义行为。

### 7.8 calloc 与 realloc 的正确用法

| 对比 | `malloc` | `calloc` |
| --- | --- | --- |
| 参数 | 总字节数 | 元素个数 + 单个元素大小 |
| 初始化 | 不清零，内容是随机值 | 全部置 0 |
| 溢出检查 | 调用方自己算 | 内部检查 `nmemb * size` |
| 典型用途 | 结构体、缓冲区 | 数组、需要零值的结构 |

```c
#include <stdlib.h>

int main(void)
{
    int n = 5;
    int *arr = calloc((size_t)n, sizeof *arr);          /* 分配并清零 */
    int *tmp = realloc(arr, (size_t)n * 2 * sizeof *arr);   /* 扩容到 2 倍 */
    if (tmp == NULL) {
        free(arr);                                      /* 失败时 arr 仍有效 */
        return 1;
    }
    arr = tmp;

    arr[n] = 42;                                        /* 新增部分未清零 */
    free(arr);
    return 0;
}
```

1. `realloc` 成功时返回新地址（可能等于原地址），失败时返回 `NULL` 且原块不变，所以必须用临时指针接收。
2. `realloc(p, 0)` 在 C17 及以前由实现定义，C23 起是未定义行为，不要依赖；`realloc` 可能搬移数据，扩容后原指针失效。

### 7.9 内存泄漏、野指针与悬垂指针
1. 内存泄漏：`malloc` 后丢失指针、函数提前 `return` 没走到 `free`、循环里反复分配不释放。
2. 野指针：未初始化的指针、`free` 后没置 `NULL` 的指针、指向已销毁栈帧的指针；悬垂指针是其中一种，返回局部数组就是典型（见 11.3）。
3. 排查手段：编译期 `-Wall -Wextra`，运行期 ASan、valgrind，见第 12 章。

## 8 结构体、位域、共用体与枚举

### 8.1 结构体基础与三种声明形式
1. 数组只能存相同类型的数据，结构体把不同类型的数据聚在一起，是用户自定义类型。

```c
struct Books {
    char title[50];
    char author[50];
    char subject[100];
    int book_id;
};                          /* 声明类型，此时不分配存储 */
struct Books book;          /* 定义变量，分配存储 */
```

2. tag、member-list、variable-list 至少要出现两个：

```c
struct { int a; } s1;                           /* 1. 匿名结构体 + 变量 */
struct SIMPLE { int a; char b; };               /* 2. 有标签，无变量 */
struct SIMPLE t1, t2[20], *t3;
typedef struct { int a; } Simple2;              /* 3. typedef 起别名 */
Simple2 u1, u2[20], *u3;
```

### 8.2 嵌套、自引用与不完整声明

```c
struct B;                           /* 不完整声明：告诉编译器有这个名字 */

struct A { struct B *partner; };    /* 此时只能使用指针 */
struct B { struct A *partner; };    /* 两个结构体互相引用 */

struct NODE { int value; struct NODE *next; };   /* 自引用：链表/树 */
```

1. 结构体可以嵌套其他结构体（需要完整类型），也可以包含指向自身类型的指针。
2. 结构体不能包含自身类型的成员，因为大小无法确定。

### 8.3 初始化、成员访问与函数传参

```c
#include <stdio.h>
#include <string.h>

struct Book { char title[50]; int id; };

int main(void)
{
    struct Book b1 = {"C", 1};
    struct Book b2 = {.id = 2, .title = "C++"};   /* C99 指定初始化器 */
    struct Book *pb = &b1;

    strcpy(b1.title, "C 语言");
    printf("%d: %s\n", b1.id, b1.title);
    printf("%d: %s\n", b2.id, b2.title);          /* 指定初始化器按名字赋值 */
    printf("%s\n", pb->title);                   /* 等价于 (*pb).title */
    return 0;
}
```

1. 初始化列表按成员顺序赋值，未列出的成员补 0；`b2 = b1` 可以整体赋值，但不能用 `==` 比较。
2. 访问成员：变量用 `.`，指针用 `->`，即 `p->x` 等价于 `(*p).x`。
3. 结构体作为函数参数是传值，会整体拷贝；较大的结构体应传 `const struct Book *`，需要修改时传非 const 指针。

### 8.4 内存对齐与 #pragma pack
1. 每个成员的偏移量必须是其对齐数的整数倍，结构体总大小必须是最大对齐数的整数倍。
2. 基本类型的对齐数通常等于其大小（`char` 1、`short` 2、`int` 4、`double` 8），受平台和 ABI 影响；编译器在成员之间和末尾插入填充字节。
3. 对齐让 CPU 一次总线周期就能取到数据，部分架构未对齐访问会异常。

```c
struct A { char c; int i; short s; };   /* 1 + 3填充 + 4 + 2 + 2尾部 = 12 */
struct B { char c; short s; int i; };   /* 1 + 1填充 + 2 + 4 = 8 */
```

4. `#pragma pack(push, 1)` 取消填充，`#pragma pack(pop)` 恢复默认；常用于协议和寄存器结构，风险是未对齐访问变慢甚至崩溃。

### 8.5 sizeof 计算例题
1. `struct C { double d; char c; };` → 16：`d` 占 0~7，`c` 在 8，总 9 补齐到 8 的倍数。
2. `struct BF { unsigned a:3; unsigned b:5; unsigned c:8; unsigned d:17; };` → 8：前三个共 16 位在同一 32 位单元，`d` 需要 17 位、剩余 16 位不够且位域不能跨单元，所以另起一个单元。
3. 上节的 `struct A` 在 `#pragma pack(1)` 下 → 7（1 + 4 + 2）。

### 8.6 位域
1. 位域把一个字节中的二进制位划分为若干区域，每个域有域名和位数。

```c
struct bs {
    unsigned int a : 8;     /* 占 8 位 */
    unsigned int b : 2;     /* 占 2 位 */
    unsigned int c : 6;     /* 占 6 位 */
};
```

2. 用途：用 1 位表示开关量；解析非标准文件格式（如 9 位整数）或硬件寄存器。
3. 剩余空间不够时从下一单元开始；`unsigned int : 0` 强制从下一单元开始；无名位域只用于填充，不能使用。
4. 位域不能取地址（`&s.a` 非法）、不能定义数组、宽度不能超过类型位宽；布局由实现定义，跨平台协议要用移位和掩码。

### 8.7 柔性数组
1. C99 允许结构体最后一个成员是柔性数组成员 `char data[];`，长度在运行时决定。

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
    if (p == NULL) {
        return 1;
    }
    p->len = n;
    free(p);
    return 0;
}
```

2. `sizeof(struct packet)` 不包含 `data`；结构体至少要有一个其他成员。
3. 对比 `char *data`：需要两次分配、内存不连续；对比 `char data[0]`：GCC 扩展，C99 之前常见。

### 8.8 共用体

```c
union Data {
    int i;
    float f;
    char str[20];           /* 占 20 字节，决定整个共用体的大小 */
};
```

1. 所有成员共享同一块内存，同一时刻只有一个成员有效；大小等于最大成员并按最大对齐取整。
2. 类型双关的结果依赖字节序和实现，常用于节省内存、协议字段多视角解释、判断大小端。
3. 先写 `data.str` 再打印 `data.i` 得到 1917853763 之类的值，是同一块内存被重新解释，不是三个值共存。

### 8.9 枚举与 typedef
1. 枚举把一组具名整型常量组织成一个类型。

```c
enum DAY { MON = 1, TUE, WED, THU, FRI, SAT, SUN };   /* 第一个 1，后面 +1 */
enum DAY day;                         /* 1. 先定义类型，再定义变量 */
enum DAY2 { MON2 = 1, TUE2 } day2;    /* 2. 定义类型的同时定义变量 */
enum { MON3 = 1, TUE3 } day3;         /* 3. 省略标签，直接定义变量 */
```

2. 不写 `= 1` 时第一个默认为 0；枚举常量本质是 `int`，`sizeof(enum DAY)` 通常为 4，由实现决定。
3. C 中枚举变量可以自增遍历：`for (day = MON; day <= SUN; day++)`；C++ 不允许这样自增。
4. `typedef unsigned char BYTE;` 由编译器处理；`#define` 是预处理文本替换，无作用域、无类型检查。
5. `typedef int *P; P a, b;` 两个都是指针；`#define P int *` 后 `P a, b;` 只有 a 是指针。

## 9 预处理器

### 9.1 预处理器的作用与常用指令
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

### 9.2 预定义宏与运算符
1. 常用预定义宏：`__DATE__`、`__TIME__`、`__FILE__`、`__LINE__`、`__STDC__`、`__STDC_VERSION__`；`__func__` 是 C99 的当前函数名，不是宏。
2. 反斜杠 `\` 续行；`#` 把参数转成字符串；`##` 拼接两个记号；`defined()` 判断宏是否已定义。

```c
#include <stdio.h>

#define STR(x) #x                                    /* 字符串化 */
#define CAT(a, b) a##b                               /* 记号拼接 */
#define SHOW(expr) printf(#expr " = %d\n", (expr))   /* 反斜杠续行的典型写法 */

int main(void)
{
    int token34 = 40;

    printf("%s\n", STR(hello));        /* 输出 hello */
    printf("%d\n", CAT(token, 34));    /* 展开成 token34，输出 40 */
    SHOW(token34 + 2);                 /* 输出 token34 + 2 = 42 */
    return 0;
}
```

```c
#if !defined(MESSAGE)
#define MESSAGE "You wish!"
#endif
```

### 9.3 带参宏的陷阱与头文件
1. 参数和整体都要加括号，否则运算符优先级会改变语义：

```c
#define SQUARE(x) x * x            /* 错误：SQUARE(1 + 2) 展开为 1 + 2 * 1 + 2 */
#define SQUARE_OK(x) ((x) * (x))   /* 正确 */
```

2. 参数可能被求值多次：`MAX(i++, j++)` 会让其中一个自增两次，改用 `static inline` 函数；多语句宏用 `do { ... } while (0)` 包起来。
3. `#define MAX 100;` 多了分号，是经典错误；宏没有类型、没有作用域、调试时看不到符号，能用 `const`、`enum`、`static inline` 就不要用宏。
4. 头文件：`#include <stdio.h>` 从系统目录查找，`#include "my.h"` 先查当前目录；头文件卫士见 2.4。

## 10 输入输出、文件与错误处理

### 10.1 标准输入输出

| 标准文件 | 文件指针 | 设备 |
| --- | --- | --- |
| 标准输入 | `stdin` | 键盘 |
| 标准输出 | `stdout` | 屏幕 |
| 标准错误 | `stderr` | 屏幕（不带缓冲，优先输出） |

1. `printf()` 格式化输出到 stdout；`scanf()` 从 stdin 读取并格式化，必须传地址并检查返回值，如 `if (scanf("%d", &n) != 1)`。
2. 常用格式符：`%d`、`%u`、`%ld`、`%lld`、`%f`、`%lf`（scanf 读 double）、`%c`、`%s`、`%p`、`%zu`、`%%`。
3. 格式串与参数类型必须匹配，否则是未定义行为；`printf("%d", 3.14)`、`printf("%d", sizeof(x))` 都是典型错误。

### 10.2 字符、行输入输出与 gets 的移除
1. `getchar()` 读取下一个字符并返回为 `int`（为了能返回 `EOF`）；`putchar()` 输出字符并返回它。
2. `gets()` 从 stdin 读一行直到终止符或 EOF；`puts()` 把字符串和尾随换行符写入 stdout。
3. `gets()` 不检查缓冲区大小，C11 起已从标准中删除；替代方案是 `fgets(buf, sizeof buf, stdin)`（保留换行符）或 Annex K 的 `gets_s`（可选，很多实现不提供）。
4. `getchar` 返回 `int`，不要用 `char` 接收，否则无法区分 `EOF`（-1）和合法字符。

### 10.3 文件的打开与关闭
1. `FILE *fopen(const char *filename, const char *mode);` 失败返回 `NULL`，使用前必须判断。
2. `fclose(FILE *fp)` 成功返回 0，失败返回 `EOF`；不关闭会丢缓冲区数据、泄漏句柄。

| 模式 | 描述 |
| --- | --- |
| `r` | 打开已有文本文件读 |
| `w` | 打开文本文件写，不存在则创建，存在则截断为零长度 |
| `a` | 追加写，不存在则创建 |
| `r+` / `w+` / `a+` | 读写模式，`w+` 会截断，`a+` 写只能追加 |
| `rb`/`wb`/`ab` | 二进制模式，Windows 上不做 CRLF 转换 |

### 10.4 文件读写
1. 字符与字符串：`fputc` 写一个字符，`fputs` 写字符串，`fgetc` 读一个字符，`fgets(buf, n, fp)` 最多读 n-1 个字符并补 `'\0'`。
2. 二进制块：`fread(void *ptr, size_t size, size_t nmemb, FILE *fp)` 与 `fwrite(...)`，返回实际读写的元素个数。

```c
#include <stdio.h>

int main(void)
{
    char buf[64];
    FILE *fp = fopen("demo.txt", "w+");   /* 读写模式，文件存在则先截断 */

    if (fp == NULL) {
        perror("fopen");
        return 1;
    }
    fputs("hello\n", fp);
    fputc('C', fp);
    rewind(fp);                           /* 回到文件开头再读 */

    while (fgets(buf, (int)sizeof buf, fp) != NULL) {
        fputs(buf, stdout);
    }
    fclose(fp);
    return 0;
}
```

3. 用 `feof` 判断文件结束是错误写法（会多读一次），应判断 `fgets`/`fread` 的返回值；定位用 `fseek`、`ftell`、`rewind`。

### 10.5 错误处理：errno、perror、strerror
1. 很多库函数失败时设置全局变量 `errno`（`<errno.h>`），成功时不会清零，所以应先 `errno = 0`。
2. `perror("msg")` 输出 `msg: 错误描述`；`strerror(errno)` 返回错误描述的字符串指针。

```c
#include <errno.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    FILE *fp = fopen("not_exist.txt", "r");

    if (fp == NULL) {
        fprintf(stderr, "fopen failed: %s\n", strerror(errno));
        perror("fopen");
    }
    return 0;
}
```

3. 程序退出状态：`return 0` / `exit(EXIT_SUCCESS)` 表示成功，`return 1` / `exit(EXIT_FAILURE)` 表示失败。
4. `exit` 会刷新并关闭所有流、执行 `atexit` 注册的函数；`_Exit`/`_exit` 不刷新缓冲区。

## 11 常见陷阱与未定义行为

### 11.1 数组越界与缓冲区溢出
1. 数组越界不报错，可能改坏栈上的其他变量，甚至被利用执行任意代码：`int a[10]; a[10] = 0;` 就是未定义行为。
2. `strcpy`、`strcat`、`sprintf` 不检查目标大小：`char buf[8]; strcpy(buf, "0123456789");` 溢出 3 字节。
3. 安全写法：`snprintf(buf, sizeof buf, "%s", input)`；`fgets` 代替 `gets`；拼接前先算总长度。
4. `gets` 从 C11 起被删除，根本原因就是无法防溢出。

### 11.2 有符号溢出与求值顺序
1. 有符号整数溢出是未定义行为，编译器可以假设它不发生并做激进优化；无符号溢出是回绕，行为有定义。

```c
void overflow_demo(void)        /* #include <limits.h> */
{
    int x = INT_MAX;
    unsigned u = UINT_MAX;
    x = x + 1;                  /* 未定义行为 */
    u = u + 1;                  /* 0，合法回绕 */
}
```

2. 判断加法溢出用 `if (a > INT_MAX - b)`，或使用 `__builtin_add_overflow`。
3. `i++ + i++` 两个自增之间没有序列点（C11 称「无顺序」），是未定义行为；`i = i++ + 1` 同理。
4. 常见未定义行为：

| 类别 | 例子 |
| --- | --- |
| 越界访问 | `a[10]`、`p[-1]` |
| 空指针解引用 | `int *p = NULL; *p = 1;` |
| 释放后使用 / 重复释放 | `free(p); *p = 1;`、`free(p); free(p);` |
| 有符号溢出 | `INT_MAX + 1` |
| 读未初始化变量 | `int x; printf("%d", x);` |
| 格式串不匹配 | `printf("%d", 3.14)` |
| 修改字符串字面量 | `char *s = "abc"; s[0] = 'A';` |

### 11.3 动态内存与返回局部变量
1. `free` 后继续使用、重复释放、`free(&local)`、`free(p + 1)` 都是未定义行为；泄漏常见于丢失指针、提前 `return`、错误分支忘了 `free`。
2. 返回局部数组地址会得到悬垂指针：

```c
char *f(void)
{
    char buf[16] = "hi";
    return buf;             /* 函数返回后栈帧失效 */
}
```

修复：改成 `static char buf[16];`（不可重入）、`malloc`（调用方负责 free），或由调用方传入缓冲区。

### 11.4 sizeof 与 strlen 等高频错误
1. `sizeof` 是编译期运算符，`strlen` 是运行期函数；`sizeof("abc")` 为 4，`strlen("abc")` 为 3。
2. `sizeof` 作用于指针得到指针大小，作用于数组得到数组总大小；数组传参退化后，函数内不能再用 `sizeof` 求长度。
3. 其他高频错误：`if (a = 1)`、`switch` 漏 `break`、`scanf("%d", n)` 少 `&`、`printf("%d", sizeof(x))` 格式符错误。

## 12 调试与工具

### 12.1 编译告警与 Sanitizer
1. 先让编译器说话：`-Wall -Wextra -Wpedantic -Wconversion -Wshadow`，CI 里可以加 `-Werror`。
2. ASan 检查越界、use-after-free、double free、栈溢出；UBSan 检查未定义行为；`-fstack-protector-strong` 在栈帧里放 canary，检测返回地址被覆盖。

```bash
gcc -std=c11 -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer demo.c -o demo
./demo
```

### 12.2 ASan 报错示例

```c
#include <stdio.h>

int main(void)
{
    int a[3] = {0};
    int i;

    for (i = 0; i <= 3; i++) {      /* i == 3 时越界写 */
        a[i] = i;
    }
    printf("%d\n", a[0]);
    return 0;
}
```

典型输出（地址和行号每次不同）：

```text
==12345==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7ffd...
WRITE of size 4 at 0x7ffd... thread T0
    #0 0x... in main /tmp/demo.c:8
Address 0x... is located in stack of thread T0 at offset 48 in frame
SUMMARY: AddressSanitizer: stack-buffer-overflow /tmp/demo.c:8 in main
```

### 12.3 gdb 常用命令

| 命令 | 作用 |
| --- | --- |
| `gcc -g -O0 demo.c -o demo` | 带调试信息编译 |
| `gdb ./demo` | 启动调试 |
| `run` / `r` | 运行程序 |
| `break main` / `b file.c:10` | 设置断点 |
| `next` / `n` | 单步，不进入函数 |
| `step` / `s` | 单步，进入函数 |
| `continue` / `c` | 继续到下一个断点 |
| `print x` / `p *p` | 打印变量或表达式 |
| `backtrace` / `bt` | 查看调用栈 |
| `x/16xb p` | 按十六进制查看内存 |
| `watch x` | 变量变化时中断 |
| `finish` / `quit` | 返回上一层 / 退出 |

### 12.4 valgrind 与其它工具
1. `valgrind --leak-check=full --show-leak-kinds=all ./demo` 检测内存泄漏和非法访问，无需重新编译，但慢 10~50 倍，主要用于 Linux；`strace`/`perf`/`objdump -d` 分别用来看系统调用、性能和反汇编。
2. 加固选项：`-fstack-protector-strong`、`-Wl,-z,relro,-z,now`，加上操作系统层面的 ASLR。

## 13 面试问答
以下 30 题按「关键字 → 指针与内存 → 字符串与库函数 → 编译与调试」排列，每题给出 2~4 行要点。

1. **static 的三种作用？**
   修饰局部变量：生命周期变为整个程序、只初始化一次；修饰全局变量或函数：内部链接，仅本文件可见；第三种是 C++ 的静态成员，C 中没有。
2. **volatile 的作用？**
   告诉编译器该对象可能被外部改变，禁止缓存到寄存器、禁止优化掉读写。用于硬件寄存器、中断里修改的变量、多线程共享标志；它不保证原子性，也不提供内存屏障。
3. **const 与 #define 的区别？**
   `const` 有类型、有作用域、参与编译期检查、调试可见；`#define` 是预处理文本替换，无类型无作用域。定义常量优先 `const`/`enum`，只有条件编译或字符串拼接才用宏。
4. **const 修饰指针的四种写法？**
   `const int *p` 和 `int const *p` 都不能改 `*p`；`int * const p` 不能改 `p`；`const int * const p` 两者都不能改。口诀：const 在 `*` 左边锁数据，右边锁指针。
5. **指针和引用有什么区别？**
   C 没有引用，只有 C++ 有。C 里用指针实现引用语义：指针可以为 `NULL`、可以重新赋值、有独立地址、需要显式解引用；C++ 引用必须初始化、不能为 null、不能改绑，语法上像别名。
6. **sizeof 和 strlen 的区别？**
   `sizeof` 是编译期运算符，算类型或对象占的字节数，含 `'\0'`；`strlen` 是运行期函数，从指针走到第一个 `'\0'`，不含 `'\0'`。`sizeof(char *)` 永远是指针大小，不能用来求字符串长度。
7. **数组名和指针的区别？**
   数组名代表整块数组，`sizeof` 得到数组总大小，不可赋值；指针是变量，存首地址，`sizeof` 得到指针大小。数组名在大多数表达式里退化为首元素指针，但在 `sizeof`、`&`、`_Alignof` 和字符串初始化时不退化。
8. **结构体内存对齐规则？为什么对齐？**
   每个成员的偏移是其对齐数的整数倍，结构体总大小是最大对齐数的整数倍。对齐让 CPU 一次总线周期就能取到数据，部分架构未对齐访问会异常；代价是填充字节，调整成员顺序可以减小 `sizeof`。
9. **#pragma pack 的作用和风险？**
   改变对齐方式（如 `pack(1)`）取消填充，常用于网络协议、文件格式、硬件寄存器。风险是未对齐访问在部分平台性能下降甚至崩溃，且不同编译器行为可能不同，跨平台数据不要直接按内存布局解析。
10. **位域的用途和限制？**
   用少量二进制位表示开关量、协议字段或硬件寄存器，节省内存。限制：不能取地址、不能是数组、宽度不能超过类型位宽、布局和位序由实现定义，所以跨平台协议要用移位和掩码。
11. **共用体有什么用？sizeof 怎么算？**
   所有成员共享同一块内存，同一时刻只有一个成员有效，用于节省内存、协议字段多视角解释、判断大小端。`sizeof` 等于最大成员的大小，再按最大对齐数取整。
12. **typedef 和 #define 的区别？**
   `typedef` 由编译器处理，有作用域和类型检查；`#define` 由预处理器做纯文本替换。`typedef int *P; P a, b;` 两个都是指针，而 `#define P int *` 后 `P a, b;` 只有 a 是指针。
13. **宏的副作用？如何避免？**
   参数和整体不加括号会改变优先级；参数可能被求值多次（`MAX(i++, j++)`）；没有类型检查、调试困难。避免方式：全部加括号、用 `do { } while (0)` 包多语句、能用 `static inline` 函数就不用宏。
14. **extern "C" 有什么用？**
   C++ 编译器会对函数名做名字修饰（name mangling），`extern "C"` 让 C++ 按 C 的规则生成符号，从而能链接 C 编译出的目标文件。C 代码本身不需要它，通常写在 C++ 侧头文件里并用 `#ifdef __cplusplus` 包住。
15. **malloc 失败怎么处理？**
   `malloc` 返回 `NULL`，必须检查并处理：打印错误、返回错误码、或走降级路径。不要直接解引用；嵌入式里还要考虑内存碎片和 `malloc` 本身是否可用，很多安全规范禁止动态分配。
16. **malloc、calloc、realloc 的区别？**
   `malloc(n)` 分配 n 字节、内容随机；`calloc(n, size)` 分配并清零、内部检查乘法溢出；`realloc(p, n)` 调整已分配块的大小，可能搬移数据。三者失败都返回 `NULL`，`free(NULL)` 安全。
17. **realloc 的正确用法？**
   必须用临时指针接收：`tmp = realloc(p, n); if (tmp == NULL) { /* p 仍有效 */ } else { p = tmp; }`。直接 `p = realloc(p, n)` 在失败时会丢失原指针，造成泄漏。
18. **内存泄漏和野指针怎么排查？**
   泄漏：分配后丢失指针、提前 return、循环里只分配不释放；用 valgrind 或 ASan 的 LeakSanitizer 定位。野指针：未初始化、free 后没置 NULL、指向已销毁的栈帧；开启 `-Wall -Wextra` 和 ASan 基本能抓到大部分。
19. **栈和堆的区别？**
   栈由编译器和 OS 管理，自动分配释放，速度快、空间小（默认几 MB），存放局部变量和调用帧；堆由 `malloc/free` 管理，手动释放，空间大但慢、易碎片化。栈向低地址增长，堆向高地址增长。
20. **怎么判断大小端？写代码。**
   取 `int` 的地址转成 `unsigned char *`，看最低地址字节：`int x = 1; if (*(unsigned char *)&x == 1) 小端;`。也可以用共用体：`union { int i; char c; } u = {1};` 判断 `u.c`。
21. **指针运算的边界在哪？**
   只能在同一数组或同一对象内部运算：指向「最后一个元素的下一个位置」合法，可以比较和计算，但不能解引用；再往前或往后都是未定义行为。两个指针相减要求指向同一数组，结果类型是 `ptrdiff_t`。
22. **函数指针和回调有什么关系？**
   函数指针保存函数入口地址，把函数指针作为参数传给另一个函数，被调用方在合适的时机通过它调用你的函数，这就是回调。`qsort` 的比较函数、事件处理、状态机跳转表都是典型用法。
23. **void * 有什么用？**
   通用对象指针，`malloc` 返回它，`qsort`/`memcpy` 用它接收任意类型；C 中可与对象指针隐式互转，不需要强制转换。不能解引用、不能做指针算术，转回具体类型后才能使用。
24. **memcpy 和 memmove 的区别？**
   `memcpy` 不处理内存重叠，重叠时行为未定义；`memmove` 会判断方向（从前向后或从后向前）保证重叠也正确。实现 `memmove` 的关键就是比较 `dst` 和 `src` 的地址高低决定拷贝方向。
25. **手写 strlen 的实现？**
   `size_t strlen(const char *s) { const char *p = s; while (*p) p++; return (size_t)(p - s); }`。要点：返回 `size_t`、不包含 `'\0'`、指针相减得到长度、不要用 `int` 接收返回值。
26. **手写 strcpy 有哪些坑？**
   要返回 `dst` 以支持链式调用；要处理 `src == dst`；不能处理重叠（重叠要用 `memmove`）；调用方必须保证 `dst` 足够大，标准版不检查长度；末尾必须拷贝 `'\0'`。
27. **C 里常见的未定义行为有哪些？**
   数组越界、空指针解引用、释放后使用、重复释放、有符号溢出、读未初始化变量、格式串与参数不匹配、修改字符串字面量、`i++ + i++`、返回局部变量地址。
28. **编译链接的四个阶段？static 和 extern 在链接层面有什么区别？**
   预处理（`-E`）→ 编译（`-S`）→ 汇编（`-c`）→ 链接。`static` 修饰文件作用域的变量/函数时是内部链接，符号不导出；`extern` 是声明外部链接的符号，链接器负责解析，找不到就报 `undefined reference`。
29. **头文件卫士为什么需要？#pragma once 呢？**
   防止同一个头文件被重复包含导致类型重定义。卫士用 `#ifndef/#define/#endif` 按宏去重，可移植；`#pragma once` 按文件去重，写法简单但不是标准，遇到同一文件的不同路径副本会失效。
30. **怎么调试一个内存越界？**
   先用 `-Wall -Wextra` 看告警，再用 `-fsanitize=address,undefined -g` 编译运行，ASan 会直接给出越界类型、地址和行号；没有 ASan 的平台用 gdb 看 `bt`、`x` 和 `watch`，或用 valgrind 的 memcheck。
