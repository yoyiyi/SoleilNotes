## 1 C 语言简介与特点

C 是一门通用、面向过程的编译型语言：关键字少、贴近硬件、效率接近汇编。本文面向第一次系统学 C 的人和基础语法复习，每个知识点配一个可编译的最小示例。指针与内存布局、预处理器细节、调试工具等底层内容放在 [C详解](C详解.md)，面试冲刺看 [C面试题](C面试题.md)。

### 1.1 从 UNIX 说起
- 1972 年，丹尼斯·里奇在贝尔电话实验室设计并实现 C，用于移植和开发 UNIX，它由 B 语言发展而来；1973 年 UNIX 内核大部分用 C 重写，C 由此成为系统软件的主流语言。
- 第一个标准由 ANSI 制定（C89），之后交给 ISO 维护（C90 及以后）。
- 今天 Linux 内核、MySQL、Redis、编译器、嵌入式固件都用 C 写成，C 还是 C++/Rust/Java 的 FFI 底座。

### 1.2 C 语言的特点
- 结构化、易学：关键字少，程序由函数、语句、表达式组成。
- 高效、贴近硬件：运行速度接近汇编，能操作内存地址、位与寄存器映射，适合驱动、协议栈、RTOS。
- 可移植：同一份源码换平台重新编译即可；代价是没有自动内存管理和边界检查，越界、野指针、泄漏都要自己负责（见第 13 节）。

### 1.3 C 标准演进
| 标准 | 发布 | 关键变化 | `__STDC_VERSION__` |
| --- | --- | --- | --- |
| C89/C90 | 1989/1990 | 首个标准：函数原型、`void *`、`const`/`volatile` | 不定义 |
| C95 | 1995 | 宽字符、双字符组 | `199409L` |
| C99 | 1999 | `//` 注释、`stdbool.h`、VLA、`inline`、指定初始化器 | `199901L` |
| C11 | 2011 | `_Generic`、`_Static_assert`、原子操作、线程库、删除 `gets` | `201112L` |
| C17/C18 | 2018 | 只做缺陷修复，无新特性 | `201710L` |
| C23 | 2024 | `bool`/`true`/`false`、`constexpr`、`nullptr`、`auto`、`typeof` | `202311L` |

- C99：`long long`、`<stdint.h>`、变长数组、`inline`、指定初始化器、复合字面量、`snprintf`。
- C11：`_Generic` 按类型选分支、`_Static_assert` 编译期断言、`<stdatomic.h>`、`<threads.h>`（可选）；`gets` 从标准中删除。
- C17 相当于「C11 的稳定修订版」；C23 把 `bool`/`true`/`false` 变成关键字，新增 `constexpr`、`nullptr`、`auto` 类型推断、`typeof`、`0b1010`。

GCC/Clang 对 C99~C17 支持完整，MSVC 用 `/std:c11`、`/std:c17`，嵌入式工具链升级较慢；标准细节与编译器支持现状见 [C详解](C详解.md)。实测用 `__STDC_VERSION__`；嵌入式常锁定 `-std=c99` 或 `-std=c11` 并开 `-Wpedantic`，MISRA 等规范通常禁用 VLA 和动态内存。

## 2 第一个程序：程序结构与编码风格

### 2.1 一个完整的程序
```c
#include <stdio.h>              /* 1. 预处理指令 */

#define MAX 100                 /* 2. 宏定义：无分号 */

int g_count;                    /* 3. 全局变量定义，未初始化默认为 0 */

static int helper(int x);       /* 4. 函数声明（原型） */

int main(void)                  /* 5. 程序入口，返回 int */
{
    int local = helper(1);      /* 6. 语句与表达式 */
    printf("%d %d\n", local, MAX);
    return 0;                   /* 7. 0 表示成功 */
}

static int helper(int x) { return x + 1; }   /* 函数定义 */
```

1. 源文件由预处理指令、函数、变量、语句与表达式、注释组成。
2. 编译运行：`gcc -std=c11 -Wall -Wextra hello.c -o hello`，再执行 `./hello`。

### 2.2 从源码到可执行文件
`gcc` 一步生成可执行文件，背后有四个阶段：预处理（`-E`，展开 `#include`/`#define`、删注释）→ 编译（`-S`，生成汇编）→ 汇编（`-c`，生成 `.o`）→ 链接（把 `.o` 与库合成可执行文件）。各阶段细节、静态库与共享库见 [C详解](C详解.md)。

常用选项：`-std=c11` 指定标准，`-Wall -Wextra` 开告警，`-g` 带调试信息，`-O0`/`-O2` 选优化级别，`-I`/`-L`/`-l` 指定头文件路径、库路径与库名。初学阶段至少固定带上 `-Wall -Wextra`。

### 2.3 头文件与头文件卫士
1. `#include <stdio.h>` 从系统目录和 `-I` 目录查找；`#include "my.h"` 先查当前源文件目录，再查系统目录。
2. 头文件只放声明：函数原型、`extern` 变量、类型定义、宏、`static inline` 函数。放变量或普通函数定义，多文件链接时会重复定义。
3. 同一个头文件被重复包含会重复展开，用头文件卫士按宏去重：

```c
/* sum.h：头文件不是独立编译单元，只被 #include */
#ifndef SUM_H
#define SUM_H

int sum(int a, int b);

#endif /* SUM_H */
```

4. `#pragma once` 更简单但不是标准，按「文件」去重；同一文件的不同路径副本会失效，卫士按宏去重更可靠。

### 2.4 main、注释与编码风格
1. 标准形式是 `int main(void)`；`int main()` 在 C 中表示参数未指定（K&R 风格），不要用；带参数写 `int main(int argc, char *argv[])`。`main` 返回进程退出状态，0 表示成功；C99 起末尾省略 `return` 等价于 `return 0`，但显式写出更清楚。
2. 注释有 `/* ... */`（C89）和 `//`（C99），预处理阶段被替换成一个空格；`/* */` 不能嵌套，不要用注释屏蔽含 `*/` 的代码（改用 `#if 0`）。
3. 风格：4 空格缩进、大括号位置全文件统一、一行只做一件事、标识符小写加下划线、宏全大写、函数短小。风格统一比选哪种风格更重要。

## 3 词法：标识符、关键字与分隔符

### 3.1 标识符与关键字
1. 标识符由字母、数字、下划线组成，不能以数字开头，区分大小写；`@`、`$`、`%` 不允许，也不能是关键字。
2. 以「下划线 + 大写字母」或双下划线开头的名字留给实现（如 `_Bool`、`__LINE__`）；C99 起外部标识符至少 31 个有效字符、内部至少 63 个。

| 标准 | 关键字 |
| --- | --- |
| C89（32 个） | `auto` `break` `case` `char` `const` `continue` `default` `do` `double` `else` `enum` `extern` `float` `for` `goto` `if` `int` `long` `register` `return` `short` `signed` `sizeof` `static` `struct` `switch` `typedef` `union` `unsigned` `void` `volatile` `while` |
| C99 新增 | `inline` `restrict` `_Bool` `_Complex` `_Imaginary` |
| C11 新增 | `_Alignas` `_Alignof` `_Atomic` `_Generic` `_Noreturn` `_Static_assert` `_Thread_local` |
| C23 新增 | `bool` `true` `false` `constexpr` `nullptr` `auto`（语义改变）`typeof` `typeof_unqual` |

### 3.2 分隔符与空白
1. 令牌（token）分五类：关键字、标识符、常量、字符串字面量、运算符与标点；常用标点有 `;`、`,`、`{}`、`()`、`[]`、`#`。
2. 空白用于分隔令牌：`int x` 不能写成 `intx`；`a+++b` 按最长匹配解析为 `a++ + b`，不要依赖这种写法。
3. 中文全角标点（`；`、`，`、`（）`）会导致编译错误，报错信息很怪时先检查标点。

## 4 数据类型

C 的类型分四类：基本类型（整型、浮点）、枚举类型、void、派生类型（指针/数组/结构/共用体/函数）。数组与结构体又称聚合类型；C 是静态类型语言，变量类型在编译期确定，混合运算时按规则隐式转换。

### 4.1 整数类型
| 类型 | 典型字节 | 典型范围 | 备注 |
| --- | --- | --- | --- |
| `char` | 1 | -128~127 或 0~255 | 有无符号由实现决定 |
| `signed char` | 1 | -128~127 | 明确有符号 |
| `unsigned char` | 1 | 0~255 | 存字节、做位运算 |
| `short` | 2 | -32768~32767 | 至少 16 位 |
| `unsigned short` | 2 | 0~65535 | |
| `int` | 2 或 4 | -32768~32767 或约 ±21 亿 | 现代桌面/服务器为 4 字节 |
| `unsigned int` | 2 或 4 | 0~65535 或 0~4294967295 | |
| `long` | 4 或 8 | 至少 32 位 | Win64 为 4，Linux64 为 8 |
| `unsigned long` | 4 或 8 | 至少 32 位 | |
| `long long` | 8 | 至少 64 位 | C99 引入 |

1. 标准只规定最小范围，准确大小用 `sizeof` 在目标平台确认，`<limits.h>` 给出 `INT_MAX`、`CHAR_BIT` 等宏；`char` 是否有符号由实现决定，处理字节时用 `unsigned char` 或 `uint8_t`，协议解析、序列化优先用 `<stdint.h>` 的定宽类型。整数字面量可写十进制 `221`、八进制 `0755`、十六进制 `0xFeeL`，后缀 `u`/`l` 表示无符号与长整型；浮点字面量默认 `double`，`2.0f` 是 `float`，`1.5e-3` 是科学计数法。

### 4.2 浮点类型
| 类型 | 典型字节 | 值范围 | 有效十进制位 |
| --- | --- | --- | --- |
| `float` | 4 | 1.2E-38 ~ 3.4E+38 | 6~7 |
| `double` | 8 | 2.3E-308 ~ 1.7E+308 | 15~16 |
| `long double` | 16（x86 为 80 位扩展精度） | 3.4E-4932 ~ 1.1E+4932 | 18~19 |

1. 浮点是二进制近似值，`0.1 + 0.2 != 0.3`，不要用 `==` 比较，判断相等用 `fabs(a - b) < 1e-9`（`<math.h>`，链接 `-lm`）。
2. 浮点常量默认 `double`，要 `float` 加后缀 `f`；`printf` 用 `%f` 输出 `double`、`%Lf` 输出 `long double`。

### 4.3 void 与 sizeof
1. `void` 有三种用法：函数无返回值、函数无参数（`int main(void)`）、通用指针 `void *`（可与其他对象指针隐式互转，但不能解引用、不能做指针算术）。
2. `sizeof` 是运算符不是函数，结果是 `size_t`，`printf` 用 `%zu`；它的操作数不求值，`sizeof(i++)` 不会让 `i` 自增；数组元素个数用 `sizeof(a) / sizeof(a[0])`，前提是数组还没退化为指针。

```c
#include <limits.h>
#include <stdint.h>
#include <stdio.h>

int main(void)
{
    printf("int %zu 字节 %d~%d\n", sizeof(int), INT_MIN, INT_MAX);
    printf("long %zu 指针 %zu int32_t %zu\n", sizeof(long), sizeof(void *), sizeof(int32_t));
    return 0;
}
```

### 4.4 类型转换
1. 隐式转换：`int` 与 `double` 运算转 `double`；`char`/`short` 先做整型提升到 `int`；`int` 与 `unsigned int` 运算统一转成 `unsigned int`。显式转换 `(type)expr` 只影响这一次表达式的解释，不改变变量本身的类型；`(int)3.99` 得 3、`(int)-3.99` 得 -3，向零截断。

```c
#include <stdio.h>

int main(void)
{
    int a = -1, sum = 7, count = 2;
    unsigned int b = 1;

    printf("%d %d\n", a < b, -1 < sizeof(int));             /* 0 0：都按无符号比较 */
    printf("%.2f %d\n", (double)sum / count, (int)-3.99);   /* 3.50 -3 */
    return 0;
}
```

2. 有符号与无符号混用是经典坑，打开 `-Wsign-compare`（含在 `-Wextra` 中），并尽量统一类型。

## 5 变量、常量与存储类

### 5.1 定义、声明与常量
1. 定义分配存储空间，只能有一次；声明只告诉编译器名字和类型，可以多次出现；函数原型是声明，带函数体的是定义。
2. 定义常量优先 `const` 或 `enum`：有类型、有作用域、参与编译期检查、调试可见；`#define` 是无类型、无作用域的文本替换，适合条件编译、字符串拼接和数组长度等需要编译期常量的场合。`#define MAX 100;` 多了分号，展开后 `int buf[MAX;];` 直接语法错误。
3. 跨文件时，头文件放 `extern` 声明和函数原型，在一个 `.c` 里定义，编译 `gcc main.c util.c -o app`。

```c
#include <stdio.h>

#define MAX 100                  /* 预处理替换：无类型、无作用域、无分号 */
const int LIMIT = 100;           /* 有类型、有作用域、可检查 */
int g_count = 1;                 /* 定义：分配存储，只能一次 */
extern int g_count;              /* 声明：可以重复，不分配空间 */
int add(int a, int b);           /* 函数原型 */

int main(void)
{
    int buf[MAX] = {0};
    printf("%d %d %zu\n", add(g_count, 2), LIMIT, sizeof buf / sizeof buf[0]);
    return 0;
}

int add(int a, int b) { return a + b; }   /* 函数定义 */
```

### 5.2 存储类
| 存储类 | 作用域 | 生命周期 | 说明 |
| --- | --- | --- | --- |
| `auto` | 块 | 自动 | 局部变量默认，C 中几乎不写 |
| `register` | 块 | 自动 | 建议放寄存器，不能取地址；现代编译器基本忽略 |
| `static` | 块或文件 | 静态 | 局部：只初始化一次、贯穿程序；全局/函数：内部链接 |
| `extern` | 全局 | 静态 | 声明外部符号，不分配空间 |

```c
#include <stdio.h>

static int g_counter;            /* 文件作用域 + 内部链接：其他 .c 看不到 */

static void bump(void)
{
    static int n = 0;            /* 静态局部变量：只初始化一次，值跨调用保留 */
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

1. `extern` 只声明外部符号、不给初值；`extern int count = 5;` 是定义而不是声明。
2. `static` 全局变量和函数只在本文档（翻译单元）内可见，是 C 里实现「私有」的主要手段。

### 5.3 作用域、存储期与左值
1. 局部变量：块作用域，函数返回即销毁（`static` 除外）；全局变量：文件作用域，程序启动时分配、结束时释放，未初始化默认为 0。存储期分三种：自动（栈）、静态（`.data`/`.bss`）、动态（堆，`malloc`）；局部 `static` 只初始化一次、跨调用保留值，全局变量未初始化默认为 0，都由存储期决定。
2. 左值表示可定位的存储位置，能放在赋值号左边（变量、数组元素、`*p`、结构体成员）；右值是临时值（`1`、`a + b`、返回值）。`const` 变量是不可修改的左值，`&` 只能作用于左值。

## 6 运算符与优先级

### 6.1 运算符分类
| 运算符 | 符号 |
| --- | --- |
| 算术 | `+`、`-`、`*`、`/`、`%`、`++`、`--` |
| 关系 | `==`、`!=`、`>`、`<`、`>=`、`<=` |
| 逻辑 | `&&`、`\|\|`、`!` |
| 位 | `&`、`\|`、`^`、`~`、`<<`、`>>` |
| 赋值 | `=`、`+=`、`-=`、`*=`、`/=`、`%=` 等 |
| 杂项 | `sizeof`、`&`、`*`、`?:`、`,`、`->`、`.` |

1. 整数除法向零截断，`%` 只能用于整数，结果符号与被除数一致：`-7 % 3 == -1`；关系运算的结果是 `int`（0 或 1），不是布尔类型。
2. `&&` 与 `||` 有短路求值，`&` 与 `|` 没有：`if (p != NULL && p->x)` 依赖短路才安全；位运算管理标志位用 `flags |= MASK;`、`flags &= ~MASK;`、`if (flags & MASK)`。

### 6.2 一个示例看清算术、逻辑与位运算
```c
#include <stdio.h>

int main(void)
{
    int a = 7, b = 3, i = 5;
    unsigned int flags = 0x1u;

    printf("%d %d %d %d\n", a + b, a - b, a * b, a / b);   /* 10 4 21 2 */
    printf("%d %d %d\n", a % b, -7 % 3, a > b);            /* 1 -1 1 */
    flags |= 0x4u;                                          /* 置位 */
    flags &= ~0x1u;                                         /* 清位 */
    printf("%u %u %d\n", flags, flags << 1, (flags & 0x4u) != 0);
    printf("%d ", i++);            /* 5：先取值，i 变成 6 */
    printf("%d\n", ++i);           /* 7：先自增再取值 */
    return 0;
}
```

### 6.3 优先级与结合性
| 优先级 | 运算符 | 结合性 |
| --- | --- | --- |
| 1（最高） | `()` `[]` `->` `.` | 左 |
| 2 | `!` `~` `++` `--` 正负号 `*` `&` `(type)` `sizeof` | 右 |
| 3 | `*` `/` `%` | 左 |
| 4 | `+` `-` | 左 |
| 5 | `<<` `>>` | 左 |
| 6 | `<` `<=` `>` `>=` | 左 |
| 7 | `==` `!=` | 左 |
| 8 | `&` `^` `\|`（同组内优先级 & > ^ > \|） | 左 |
| 9 | `&&` | 左 |
| 10 | `\|\|` | 左 |
| 11 | `?:` | 右 |
| 12 | `=` `+=` `-=` `*=` `/=` 等 | 右 |
| 13（最低） | `,` | 左 |

1. 记不住就加括号，可读性优先；`*p++` 等价于 `*(p++)`，先取指针再让指针自增，`(*p)++` 才是自增所指对象。
2. `a = b = c` 从右向左结合；逗号表达式返回最后一个值，少用。

## 7 控制流

### 7.1 if 与 switch
```c
#include <stdio.h>

int main(void)
{
    int score = 78;
    char grade = 'C';

    if (score >= 90) grade = 'A';
    else if (score >= 60) grade = 'B';

    switch (grade) {
    case 'A': printf("优秀\n"); break;
    case 'B': printf("及格\n"); break;      /* 78 走到这里 */
    default:  printf("不及格\n"); break;     /* 漏 break 会贯穿到下一个 case */
    }
    return 0;
}
```

1. `if (a = b)` 是赋值不是比较，`-Wparentheses` 会告警，要当错误处理；浮点数不要用 `==` 判等；简单二选一用三目运算符更紧凑：`int max = a > b ? a : b;`。
2. `switch` 的表达式必须是整型（含 `char`、枚举），`case` 必须是整型常量表达式且不能重复；多个 `case` 可以共用一段逻辑。

### 7.2 循环
```c
#include <stdio.h>

int main(void)
{
    int i;

    for (i = 0; i < 3; i++) printf("for %d\n", i);    /* 已知次数 */
    i = 0;
    while (i < 3) printf("while %d\n", i++);          /* 条件驱动 */
    i = 0;
    do printf("do %d\n", i++); while (i < 3);         /* 至少执行一次 */
    return 0;
}
```

1. `for` 适合已知次数，`while` 适合条件驱动，`do...while` 适合「至少执行一次」。
2. 循环边界用 `<` 而不是 `<=`，可减少越界；C99 起可写 `for (int i = 0; ...)`。

### 7.3 break、continue 与 goto
```c
#include <stdio.h>

int main(void)
{
    int i;

    for (i = 0; i < 6; i++) {
        if (i % 2 == 0) continue;    /* 跳过本次迭代 */
        if (i == 5) break;           /* 跳出整个循环 */
        printf("%d ", i);            /* 1 3 */
    }
    return 0;
}
```

1. `break` 跳出当前循环或 `switch`；`continue` 跳过本次迭代，进入下一次。
2. `goto` 只能跳到同一函数内的标号，合理用法是统一错误清理：申请资源失败就 `goto cleanup`，函数末尾集中 `free`/`fclose`；不要用它构造循环或跨函数跳转。

## 8 函数

### 8.1 定义、原型与返回值
```c
#include <stdio.h>

int max(int a, int b);              /* 原型：先声明后使用 */

int main(void)
{
    printf("%d\n", max(3, 7));      /* 7 */
    return 0;
}

int max(int a, int b) { return a > b ? a : b; }   /* 定义 */
```

1. 原型让编译器检查参数类型和个数；非 `void` 函数所有路径都应有 `return`，否则返回值未定义。
2. 需要返回多个值时用结构体打包，或通过指针参数输出。

### 8.2 参数传递：C 只有传值
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
    swap(&x, &y);                    /* 传地址，x 和 y 才真正交换 */
    printf("%d %d\n", x, y);         /* 2 1 */
    return 0;
}
```

1. 所谓「传址」是传指针，函数内通过 `*p` 修改实参；写成 `void swap(int a, int b)` 只交换副本，实参不变。
2. 数组作为参数会退化为指针，函数内 `sizeof(arr)` 得到指针大小，必须额外传长度（见 9.2）；较大的结构体传 `const struct S *`，避免整体拷贝。

### 8.3 递归
```c
#include <stdio.h>

long factorial(int n)
{
    if (n <= 1) return 1;            /* 终止条件，必须有 */
    return n * factorial(n - 1);
}

int main(void)
{
    printf("5! = %ld\n", factorial(5));   /* 120 */
    return 0;
}
```

1. 每层递归占一个栈帧，必须有终止条件，否则栈溢出；深度过大在嵌入式几 KB 的栈上必崩。
2. C 标准不保证尾递归优化，朴素斐波那契递归是 O(2^n)。

### 8.4 声明与定义分离、可变参数与命令行参数
1. 头文件放原型，`.c` 放定义，其他文件 `#include` 头文件后调用；只在文件内使用的函数加 `static`，得到内部链接。
2. 可变参数用 `<stdarg.h>` 的 `va_list`、`va_start`、`va_arg`、`va_end`；`va_arg(ap, int)` 必须按默认实参提升后的类型读取（`char`/`short` 提升为 `int`，`float` 提升为 `double`），所以 `va_arg(ap, char)` 是错的。
3. 命令行参数：`argc` 是参数个数（含程序名），`argv` 是字符串数组，`argv[argc]` 为 `NULL`；数字参数用 `strtol`/`sscanf` 转换并检查 `errno`、`endptr`。

## 9 数组

### 9.1 一维数组与二维数组
```c
#include <stdio.h>

int main(void)
{
    double balance[5] = {100.0, 2.0};        /* 其余元素自动补 0 */
    int a[] = {1, 2, 3};                     /* 长度由初始化列表决定 */
    int m[2][3] = {{1, 2, 3}, {4, 5, 6}};    /* 按行优先连续存放 */

    balance[4] = 9.9;                        /* 下标从 0 开始 */
    printf("%zu %d %d\n", sizeof(a) / sizeof(a[0]), a[2], m[1][2]);   /* 3 3 6 */
    return 0;
}
```

1. 局部数组不初始化时元素是随机值，`= {0}` 可全部清零；越界是未定义行为，编译器不检查。
2. `m[i][j]` 等价于 `*(*(m + i) + j)`；初始化可省略第一维长度，第二维不能省。

### 9.2 数组作为函数参数
```c
#include <stdio.h>

void print_array(const int arr[], int len)   /* 等价于 const int *arr */
{
    for (int i = 0; i < len; i++) printf("%d ", arr[i]);
    printf("\nsizeof(arr) = %zu\n", sizeof(arr));   /* 指针大小，不是数组大小 */
}

int main(void)
{
    int a[5] = {1, 2, 3, 4, 5};
    print_array(a, 5);
    return 0;
}
```

1. `int param[]`、`int param[10]`、`int *param` 在参数位置完全等价，长度信息全部丢失；数组大小要在还没「退化」的作用域里算好再传进去。

### 9.3 越界与变长数组
1. `int a[10]; a[10] = 0;` 是越界写，属于未定义行为，可能改坏栈上的其他变量。
2. C99 变长数组 `int a[n];` 在栈上分配，`n` 在运行时确定；C11 起是可选特性，`n` 过大会栈溢出，工程中更常用 `malloc`。

## 10 字符串

### 10.1 字符数组与字符串字面量
1. C 没有字符串类型，字符串是以 `'\0'` 结尾的字符数组：`char s[6] = {'H','e','l','l','o','\0'};` 与 `char s[] = "Hello";` 等价。
2. 字符串字面量的类型是 `char[N]`，存放在只读区，修改它是未定义行为，应写成 `const char *`；字符 `'A'` 是 `int`，字符串 `"A"` 是 2 字节数组；UTF-8 下中文按字节计，`strlen("中文")` 得到 6 而不是 2。

### 10.2 常用 string.h 函数
| 函数 | 简介 |
| --- | --- |
| `strcpy(s1, s2)` | 复制 s2 到 s1，不检查目标大小 |
| `strcat(s1, s2)` | 把 s2 连接到 s1 末尾 |
| `strlen(s1)` | 返回长度，不含 `'\0'`，类型为 `size_t` |
| `strcmp(s1, s2)` | 相等返回 0，小于返回负数，大于返回正数 |
| `strchr(s1, ch)` | 返回指向 s1 中字符 ch 首次出现位置的指针 |
| `strstr(s1, s2)` | 返回指向 s1 中子串 s2 首次出现位置的指针 |

```c
#include <stdio.h>
#include <string.h>

int main(void)
{
    char s1[40] = "Hello";
    const char *s2 = "World";
    char buf[16];

    strcat(s1, " ");
    strcat(s1, s2);
    printf("%zu %s\n", strlen(s1), strstr(s1, "lo"));
    snprintf(buf, sizeof buf, "%s", s1);                /* 安全：保证 '\0' */
    printf("%d %s\n", strcmp(s1, s1), buf);
    return 0;
}
```

1. `strcmp` 只看返回值的正负，不要依赖具体数值；`strcpy`、`strcat`、`strlen` 都以 `'\0'` 为界，源字符串没有终止符会越界读。

### 10.3 sizeof、strlen 与安全版本
| 表达式 | 计算时机 | 结果 |
| --- | --- | --- |
| `sizeof("hello")` | 编译期 | 6（含 `'\0'`） |
| `strlen("hello")` | 运行期 | 5（不含 `'\0'`） |
| `sizeof(char *)` | 编译期 | 指针大小（32 位 4，64 位 8） |
| `sizeof(arr) / sizeof(arr[0])` | 编译期 | 元素个数（`arr` 未退化时） |

1. `strncpy(dst, src, n)` 最多拷 n 字节，src 短时用 0 填充，但不保证 `'\0'`；`strncat` 总是补 `'\0'`。
2. 推荐 `snprintf(buf, sizeof buf, "%s", src)`：保证 `'\0'`，返回值是「想要写入的长度」，大于等于 size 说明被截断；`strlcpy`/`strlcat` 更安全但不是标准，跨平台慎用。

## 11 结构体与枚举入门

### 11.1 结构体的定义、初始化与访问
```c
#include <stdio.h>
#include <string.h>

struct Book { char title[50]; int id; };   /* 声明类型，不分配存储 */
typedef struct Book Book;                  /* 起别名，之后可写 Book b; */

int main(void)
{
    Book b1 = {"C", 1};                     /* 按成员顺序初始化 */
    Book b2 = {.id = 2, .title = "C++"};    /* C99 指定初始化器 */
    Book *pb = &b1;

    strcpy(b1.title, "C 语言");
    printf("%d %s %s\n", b1.id, pb->title, b2.title);   /* pb->title 即 (*pb).title */
    b2 = b1;                                /* 同类型可整体赋值，但不能用 == 比较 */
    printf("%s\n", b2.title);
    return 0;
}
```

1. 结构体把不同类型的数据聚在一起，这是它和数组的根本区别；初始化列表按成员顺序赋值，未列出的成员补 0。结构体可以嵌套其他结构体，也可以包含指向自身类型的指针（链表、树），但不能包含自身类型的成员，因为大小无法确定；匿名结构体 `struct { int a; } s1;` 可直接定义变量。
2. 结构体作参数是传值，会整体拷贝；大结构体传 `const struct Book *`。内存对齐、位域、共用体见 [C详解](C详解.md)。

### 11.2 typedef
1. `typedef struct Book Book;` 给类型起别名；也可以 `typedef struct { ... } Book;` 一次完成。
2. `typedef` 由编译器处理，有作用域和类型检查；`#define` 是纯文本替换，没有类型和作用域。`typedef int *P; P a, b;` 两个都是指针；而 `#define P int *` 后 `P a, b;` 只有 `a` 是指针——这是经典区别。

### 11.3 枚举
```c
#include <stdio.h>

enum DAY { MON = 1, TUE, WED, THU, FRI, SAT, SUN };   /* 第一个 1，后面依次 +1 */
enum COLOR { RED, GREEN = 5, BLUE };                  /* RED=0，GREEN=5，BLUE=6 */

int main(void)
{
    enum DAY day;

    for (day = MON; day <= WED; day++) printf("day = %d\n", day);   /* 1 2 3 */
    printf("%d %d %zu\n", GREEN, BLUE, sizeof(enum DAY));
    return 0;
}
```

1. 不写 `= 1` 时第一个枚举常量为 0，后面依次 +1；枚举常量本质是 `int`，`sizeof(enum DAY)` 通常为 4。枚举让一组相关的整数有名字，比裸写 `0`、`1`、`2` 可读；C 中枚举变量可以自增遍历，C++ 不允许；也可以写 `enum { A, B } x;` 省略标签直接定义变量。

## 12 输入输出基础

### 12.1 标准流与格式符
标准流有三个：`stdin`（键盘）、`stdout`（屏幕，通常行缓冲）、`stderr`（屏幕，不带缓冲，错误信息优先输出，用 `fprintf(stderr, ...)`）。

| 格式符 | printf 用于 | scanf 用于 | 说明 |
| --- | --- | --- | --- |
| `%d` | `int` | `int *` | 十进制有符号 |
| `%u` | `unsigned int` | `unsigned int *` | 十进制无符号 |
| `%f` | `double` | `float *` | printf 的 `%f` 就是 `double` |
| `%lf` | 同 `%f` | `double *` | scanf 读 `double` 必须用 `%lf` |
| `%c` | `char` | `char *` | scanf 不跳过空白 |
| `%s` | `char *` | `char *` | 读到空白为止，不检查长度 |
| `%x` / `%o` | 无符号十六/八进制 | 对应指针 | 常用于地址、权限 |
| `%p` | `void *` | `void **` | 打印指针地址 |
| `%zu` | `size_t` | `size_t *` | `sizeof` 的结果 |
| `%ld` / `%lld` | `long` / `long long` | 对应指针 | 长度修饰符 |
| `%%` | 输出一个 `%` | 不适用 | |

1. 格式串与参数类型必须匹配，否则是未定义行为：`printf("%d", 3.14)`、`printf("%d", sizeof(x))` 都是典型错误；`%Lf` 对应 `long double`。`scanf` 必须传地址（数组名本身是地址），并检查返回值：`if (scanf("%d", &n) != 1)`。

### 12.2 格式化输入输出示例
```c
#include <stdio.h>

int main(void)
{
    int n = 0;
    char name[32];

    printf("输入整数和名字：\n");
    if (scanf("%d %31s", &n, name) != 2) {   /* 传地址 + 检查返回值 */
        fprintf(stderr, "格式错误\n");
        return 1;
    }
    printf("n=%d name=%s\n", n, name);
    return 0;
}
```

### 12.3 getchar 与 putchar
```c
#include <stdio.h>

int main(void)
{
    int ch, lines = 0;

    while ((ch = getchar()) != EOF) {   /* 必须用 int 接收，才能与 EOF 区分 */
        if (ch == '\n') lines++;
        putchar(ch);                    /* 原样回显 */
    }
    printf("lines = %d\n", lines);
    return 0;
}
```

1. `getchar` 返回 `int`（为了能返回 `EOF`），不要用 `char` 接收，否则无法区分 `EOF`（-1）和合法字符。
2. `gets` 不检查缓冲区大小，C11 起已从标准删除；替代是 `fgets(buf, sizeof buf, stdin)`（保留换行符）或 `gets_s`（可选，很多实现不提供）。`puts` 输出字符串并追加换行。

### 12.4 常见坑
1. `scanf("%d", n)` 少 `&`：直接崩溃或写坏内存；`scanf("%c", &c)` 前有残留换行，读到的是 `'\n'`，改成 `" %c"`（格式串前加空格跳过空白）。
2. `scanf("%s", buf)` 不检查长度且遇空白停止；用 `%31s` 限定宽度，或改用 `fgets`。混用 `scanf` 与 `fgets` 时残留换行；`printf` 用 `%zu` 输出 `size_t`、`%f` 输出 `double`。
3. 文件：`fopen("a.txt", "r")` 失败返回 `NULL` 必须判断，用完 `fclose`；用 `feof` 判断结束会多读一次，应判断 `fgets`/`fread` 的返回值；失败原因用 `perror("msg")` 或 `strerror(errno)` 打印（`<errno.h>`），`errno` 成功时不会清零，应先手动置 0。详见 [C标准库速查](C标准库速查.md)。

## 13 初学常见错误清单

1. **忘写 `#include <stdio.h>`**：C99 起隐式声明是错误，`printf` 之前必须包含头文件。
2. **写 `void main()`**：标准只接受 `int main(void)`，返回值是进程退出状态。
3. **漏分号、`if (x);` 多分号**：后者让 `if` 变成空语句，后面的块无条件执行。
4. **`=` 写成 `==`**：`if (a = 1)` 永远为真，开 `-Wparentheses` 能抓到。
5. **`switch` 漏 `break`**：贯穿到下一个 `case`，逻辑悄悄出错。
6. **数组越界**：`for (i = 0; i <= n; i++)` 多走一步，`a[n]` 是未定义行为。
7. **在函数里用 `sizeof` 求数组长度**：数组已退化为指针，得到的是指针大小。
8. **字符串用 `==` 比较、用 `=` 赋值**：比较用 `strcmp`，复制用 `strcpy` 或 `snprintf`。
9. **`scanf` 少 `&`、`printf` 格式符不匹配**：前者崩溃，后者是未定义行为（`%d` 打 `double`、`%d` 打 `sizeof`）；`%c` 读到换行要写 `" %c"`。
10. **有符号与无符号混用**：`-1 < sizeof(int)` 为假，`-1 < 1u` 也为假。
11. **返回局部变量的地址**：函数返回后栈帧失效，得到悬垂指针。
12. **有符号溢出、`i++ + i++`**：都是未定义行为，编译器可以任意优化。
13. **忘记 `free` 或 `free` 后继续使用**：内存泄漏与 use-after-free，用 ASan/valgrind 排查。
14. **宏参数不加括号、`#define` 末尾带分号**：`SQUARE(1 + 2)` 会展开成 `1 + 2 * 1 + 2`。

## 14 下一步学什么

1. [C详解](C详解.md)：指针与内存、进程内存布局、`malloc`/`free`、结构体位域与对齐、预处理器、文件 IO、未定义行为、gdb/ASan 调试，以及完整版面试问答。
2. [C面试题](C面试题.md)：按「关键字 → 指针与内存 → 字符串与库函数 → 编译与调试」刷题，遮住答案自测。
3. [C标准库速查](C标准库速查.md)：`stdio.h`、`string.h`、`stdlib.h`、`stdint.h` 的常用函数与格式符，写代码时随手查。

练习建议：把第 13 节的清单当检查表，每写一个程序都用 `gcc -std=c11 -Wall -Wextra -Wpedantic -g` 编译一遍；再手写 `strlen`、`strcpy`、`memmove`，基础就稳了。返回 [C 与 Linux 学习路线](000.目录.md)。
