## 1 C++ 简介与环境
C++ 是多范式、静态类型、编译型语言：既能像 C 一样贴近硬件写系统程序，也能用面向对象、泛型（模板）和函数式（Lambda）表达抽象，核心承诺是「零开销抽象」。它由 C 发展而来，但不是严格超集，差异见 [C与C++差异](../C/C与C++差异.md)。本文面向「第一次系统学 C++」与语法速查，底层原理留给 [C++详解](C++详解.md)。
```cpp
#include <iostream>              // 预处理：把标准库头文件内容展开到这里
using std::cout;                 // 只引入需要的名字，比 using namespace std 更安全
using std::endl;
int main(int argc, char* argv[]) // 入口：argc 是参数个数、argv[0] 是程序名，返回 0 表示成功
{
    cout << "Hello, C++" << endl;
    return 0;
}
```
1. `#include <xxx>` 行尾不加分号；`std` 是标准库命名空间，写全 `std::cout` 最稳妥，`using namespace std;` 最省事但容易撞名。可移植的入口只有 `int main()` 和 `int main(int argc, char* argv[])`，标准里没有 `void main()`。
2. `main` 省略 `return` 等价于 `return 0;`，返回值即进程退出码（Linux 下 `echo $?` 查看），`'\n'` 比 `std::endl` 少一次刷新。
3. 编译：`g++ -std=c++20 -Wall -Wextra -g -O2 hello.cpp -o hello`，再执行 `./hello`（Windows PowerShell 写 `.\hello.exe`）。预处理 → 编译 → 汇编 → 链接一步完成；排错时用 `-E` 看预处理结果、`-S` 出汇编、`-c` 出 `.o`，便于分清编译错误与链接错误。初学固定带 `-Wall -Wextra`。
4. 标准演进：C++11 带来 `auto`、Lambda、范围 `for`、`nullptr`、`enum class`、智能指针；C++17 加入 `if` 初始化、结构化绑定、`inline` 变量、`string_view`；C++20 有 concepts、ranges、`span`、三路比较 `<=>`。新标准向下兼容，用新语法却按旧标准编译才会报错，查 `__cplusplus`。
## 2 基本语法
一个 `.cpp` 通常由五部分组成：预处理指令（`#include`、`#define`，行尾不加分号）→ 命名空间引入（`using namespace std;`）→ 全局声明与定义（全局变量、函数原型、类型）→ 函数定义 → 入口函数 `main`（有且只有一个）。
| 写法 | 形式 | 说明 |
| --- | --- | --- |
| 单行注释 | `// 说明` | 从 `//` 到行尾，最常用 |
| 块注释 | `/* 多行说明 */` | 可跨行，但**不能嵌套** |
| 条件编译注释 | `#if 0 ... #endif` | 注释掉含 `/* */` 的大段代码，可嵌套 |
1. 标识符由字母、数字、下划线组成，以字母或下划线开头，区分大小写；不能是关键字。常见关键字：`int` `char` `bool` `double` `auto` `const` `constexpr` `static` `extern` `class` `struct` `enum` `namespace` `template` `virtual` `override` `final` `new` `delete` `nullptr` `this` `sizeof` `if` `switch` `for` `while` `return` `try` `catch`，完整列表见 [C++详解](C++详解.md)；命名习惯定 `maxValue`、类型 `PascalCase`、成员加后缀 `_` 即可。
## 3 数据类型
### 3.1 内置类型
| 类型 | 说明 | 64 位 Linux/GCC 典型大小与范围 |
| --- | --- | --- |
| `bool` / `char` | 布尔 / 单字符（本质是小整数） | 1 字节；`char` 范围 -128~127 或 0~255（取决于平台是否有符号） |
| `int` / `unsigned int` | 最常用的整数 | 4 字节，±2.1e9 / 0~4.3e9 |
| `short` / `long long` | 更窄 / 更宽的整数 | 2 字节 / 8 字节（`long` 在 Windows 上是 4 字节） |
| `float` / `double` | 单/双精度浮点，字面量默认 `double` | 4 / 8 字节，约 7 位 / 15 位有效数字 |
| `void` | 无类型：函数无返回值、`void*` 通用指针 | — |
1. 宽度随平台变化，需要精确位数时用 `<cstdint>` 的 `int32_t`、`uint64_t`；`signed`/`unsigned` 可用于整型和字符型，`short`/`long` 只修饰整型，`int` 可省略。有符号与无符号混算时有符号数会转成无符号：`-1 < 0u` 为 `false`，`size()` 返回无符号的 `size_t`。类型限定符：`const` 值不可改；`volatile` 禁用优化、每次重新读内存；`restrict` 是 C99 关键字，C++ 只有扩展 `__restrict`。
### 3.2 sizeof、typedef 与 using
`sizeof` 是运算符不是函数，结果是 `size_t`、编译期求值：`sizeof(int)` 得类型大小，`sizeof(arr)` 得整个数组字节数，而 `sizeof(p)` 只是指针大小（数组传给函数后就退化成指针，只能拿指针大小）。类型别名有两种等价写法，C++11 的 `using` 别名在左、可读性更好，还能定义模板别名：
```cpp
#include <iostream>
#include <map>
#include <string>
using MyInt = int;                                 // C++11 风格别名，推荐
using Dict = std::map<std::string, int>;           // 复杂类型别名：可读性更好
template <typename T>
using Vec = std::vector<T>;                        // typedef 做不了模板别名
typedef unsigned int uint;                         // C 风格别名（来自 C 的 typedef）
int main()
{
    int arr[10];
    std::cout << sizeof(int) << ' ' << sizeof arr << ' ' << sizeof arr[0] << '\n';   // 4 40 4
    return 0;
}
```
### 3.3 枚举
传统枚举的名字会泄漏到外层作用域、并且能隐式转成整数；`enum class`（C++11）把名字放进枚举作用域、不隐式转换、还可指定底层类型与前向声明，所以新代码优先用它：
```cpp
#include <iostream>
enum Color { red, green, blue };            // 传统枚举：默认从 0 开始 +1，red=0 green=1 blue=2
enum class Status : unsigned char { Ok, Failed };   // 作用域枚举：必须写 Status::，不隐式转 int
int main()
{
    std::cout << blue << '\n';                     // 2：传统枚举可隐式转 int
    int n = static_cast<int>(Status::Failed);      // 需要整数时显式转换
    std::cout << n << ' ' << sizeof(Status) << '\n';   // 1 1
    return 0;
}
```
1. 可手动指定值：`enum State { ok = 0, warn = 10, error };` 则 `error` 是 11；`switch` 漏分支时 `-Wswitch` 还会告警。
### 3.4 类型转换
| 转换 | 用途 |
| --- | --- |
| `static_cast<T>(x)` | 相关类型之间：数值互转、`void*` 转回 `T*`、有继承关系的指针互转；不检查 |
| `dynamic_cast<T>(x)` | 多态类型的向下转换，失败返回 `nullptr` 或抛 `std::bad_cast`；运行时检查 |
| `const_cast<T>(x)` / `reinterpret_cast<T>(x)` | 去掉或加上 `const`（别改真正只读的对象）/ 按位重新解释，如指针与整数互转，最危险 |
1. 例：`double d = 3.99;` 时 `static_cast<int>(d)` 得 3（向零截断）；`static_cast<double>(7) / 2` 得 3.5，而 `7 / 2` 是 3。隐式转换要当心窄化：`double` 转 `int` 丢小数，超出范围的浮点转整数是未定义行为，负数转 `unsigned` 会绕成很大的数；新代码优先 `static_cast`，别用能掩盖问题的 C 风格强转 `(int)x`，细节见 [C++详解](C++详解.md)。
### 3.5 数组与字符串
数组存放固定数量、同一类型的元素，下标从 0 开始；大小必须在编译期确定（C++ 标准不支持变长数组），越界访问是未定义行为、编译器不检查。数组名在大多数表达式里退化成指向首元素的指针：`sizeof(arr)` 只在直接用数组名时得到整个数组大小，一旦当参数传给函数就退化成指针；`void f(int* p)`、`void f(int p[10])`、`void f(int p[])` 三种写法等价且都丢长度，需要长度就额外传 `size_t n`，或改用 `std::array`、`std::vector`、`std::span`。
```cpp
#include <iostream>
#include <string>
int main()
{
    int a[10]{};                     // 全部置 0
    for (int i = 0; i < 5; ++i) {
        a[i] = i * i;                // 0 1 4 9 16，其余仍是 0；a[i] 等价于 *(a + i)
    }
    int b[] = {1, 2, 3};             // 自动推导长度为 3
    std::cout << sizeof a / sizeof a[0] << ' ' << b[0] << a[4] << '\n';   // 10 116
    std::string s = "Hello";        // 自动管理内存、可增长，自己记录长度
    s += ", C++";
    std::cout << s.substr(7, 3) << s.find("C++") << s.size() << '\n';   // C++710
    return 0;
}
```
1. C 风格字符串是「以 `'\0'` 结尾的字符数组」，长度靠 `std::strlen` 现算；char[] 转 string 直接赋值或构造即可，string 转 char[] 要先用 `c_str()` 再拷贝到自己的缓冲区（`std::strcpy(out, s.c_str())`），转 `const char*` 则 `c_str()`/`data()` 不拷贝、要注意生命周期——`std::string` 修改或销毁后指针可能失效。
2. `std::string_view`（C++17）是「非拥有」的只读字符串视图，只保存指针和长度、不拷贝数据，传参时字面量、`char*`、`std::string` 都能直接传；但它不拥有数据，**绝不能返回指向已销毁对象的 view**，从「指针 + 长度」构造的也不保证以 `'\0'` 结尾，需要长期保存就转成 `std::string`。
| API | 说明 |
| --- | --- |
| `size()` / `length()` / `empty()` | 长度、是否为空（返回 `size_t`，别和 `int` 直接比） |
| `operator+` / `+=` / `append()` / `push_back()` | 拼接、追加 |
| `operator[]` / `at()` | 取字符；`at` 越界抛 `std::out_of_range`，`[]` 越界是未定义行为 |
| `c_str()` / `data()` | 取 C 风格 `const char*`，保证以 `'\0'` 结尾 |
| `find()` / `rfind()`、`substr(pos, len)` | 查找（失败返回 `npos`）、取子串 |
| `replace()` / `insert()` / `erase()` / `clear()` | 替换、插入、删除、清空 |
| `stoi` / `stod` / `to_string` | 字符串与数字互转 |
## 4 变量与常量
### 4.1 定义、声明与初始化
定义分配存储空间，全程序只能一次；声明只说明「有这么个名字和类型」，可以多次。`extern` 声明常放头文件，定义放某个 `.cpp`。初始化方式有 `int b = 0;`（拷贝）、`int c(10);`（直接，允许窄化）、`int d{20};`（列表，C++11 推荐）、`int e{};`（值初始化为 0）几种；列表初始化**禁止窄化**（`double g{3.14}` 编译失败），还能避免 `Foo f();`（其实是函数声明）的解析歧义。全局变量和 `static` 变量未显式初始化时置 0（`char` 为 `'\0'`、指针为 `nullptr`）；**局部变量不会**，读未初始化的局部变量是未定义行为。
### 4.2 auto
`auto` 从初始化表达式推导类型、必须初始化；规则与模板一致——默认按值、丢掉引用和顶层 `const`，要引用写 `auto&`，只读且避免拷贝写 `const auto&`。例：`int& rx = x;` 时 `auto a = rx;` 得到新的 `int`（改 `a` 不影响 `x`），`auto& b = rx;` 让 `b` 成为 `x` 的别名。它适合迭代器、Lambda、长模板类型等类型名很啰嗦的地方；类型含义重要时（整数宽度、是否有符号）直接写清楚。C++14 起函数返回类型也能写 `auto`。
### 4.3 const
`const` 表示「通过这个名字不能修改」、编译器检查，把只读意图写进类型比注释可靠。从右往左读：`const int* p1` 是「指向 const int 的指针」（不能改 `*p1`，可以改指向），`int* const p2` 是「指向 int 的 const 指针」（不能改指向，可以改 `*p2`）；参数写成 `const int& value` 或 `const std::string& s` 表示函数内只读，也是大对象最常用的传参方式。文件作用域的 `const` 对象默认内部链接（每个 `.cpp` 各一份），放头文件安全，要共享一份就用 `inline const`（C++17）或 `extern`；成员函数末尾的 `const` 属类的知识，见 [C++详解](C++详解.md)。
### 4.4 constexpr
`constexpr`（C++11）比 `const` 更进一步：要求**编译期就能求值**，可用作数组长度、模板实参、`case` 标签等编译期常量。例：`constexpr int kArea = square(3);` 可当数组长度 `int arr[kArea];`，而 `const int c = runtime;` 只是运行期只读值。
| 对比项 | `const` | `constexpr` |
| --- | --- | --- |
| 核心含义 | 运行期只读 | 编译期可求值（隐式也满足只读） |
| 初始化时机 | 可运行期初始化 | 必须用常量表达式初始化 |
| 当数组长度、模板实参 | 不能（除非初始化式本身是常量表达式） | 能 |
| 修饰函数 | 无此用法 | 可以，C++14 起函数体允许局部变量和循环 |
1. 优先 `constexpr`：任何 `constexpr` 变量都能当 `const` 用，反过来不成立，需要编译期常量的场合它才可用；C++20 还有 `consteval`（强制编译期）和 `constinit`。
## 5 作用域与存储类
### 5.1 局部、全局与遮蔽
作用域决定名字在哪可见，存储期决定变量活多久：局部变量作用域在块内、随块结束销毁；全局变量整个程序都活着，加 `static` 后仅本文件可见。内层同名变量会遮蔽（shadowing）外层变量，`-Wshadow` 可告警，被遮蔽的全局变量写 `::value` 访问；全局变量可被任何函数修改、难以追踪，能用参数或返回值传递的就不要用。例：全局 `int value = 100;`，在 `main` 里再定义 `int value = 10;` 后，打印 `value` 得 10、打印 `::value` 得 100。
### 5.2 static 的三种用法
| 用法 | 位置 | 含义 |
| --- | --- | --- |
| 修饰局部变量 | 函数体内 `static int cnt;` | 存储期变成整个程序，只初始化一次（C++11 起线程安全），函数返回后值保留 |
| 修饰全局变量/函数 | 文件作用域 `static int g;` | 内部链接：其他 `.cpp` 看不到，避免符号冲突 |
| 修饰类的成员 | `class A { static int s; };` | 属于类而不属于某个对象，所有对象共享一份 |
1. 局部 `static` 的典型用法是让函数记住调用次数：`int nextId() { static int n = 0; return ++n; }`，每次调用返回 1、2、3……。匿名命名空间 `namespace { ... }` 是比文件级 `static` 更推荐的文件私有写法。
### 5.3 extern 声明与跨文件共享
`extern` 声明一个定义在别处的变量或函数：头文件 `counter.h` 里写 `#pragma once` 和 `extern int gCount;`，某个 `counter.cpp` 里 `int gCount = 0;` 定义（全程序只有这一处），`main.cpp` 包含头文件即可读写；链接时一起编译 `g++ -std=c++20 main.cpp counter.cpp -o app`。函数在头文件写原型、在 `.cpp` 写定义同样属于声明与定义分离，函数默认跨文件可见、不需要 `extern`；头文件用 `#pragma once` 防止重复包含。
### 5.4 thread_local
`thread_local`（C++11）让每个线程拥有自己的一份变量副本：线程开始时创建、结束时销毁，可与 `static`/`extern` 组合，适合放「每线程一份」的缓存、随机数引擎、错误码；类的 `static` 成员也能声明为 `thread_local`（类外定义）。例：`thread_local int tlsCount = 0;` 在多个线程里各自 `+1`，每个线程看到的都是 1。线程库细节见 [C++详解](C++详解.md)。
1. `register` 自 C++17 起弃用，`auto` 也不再是存储类，两者都不要当存储类用。
## 6 运算符
### 6.1 算术、关系、逻辑与位运算
| 类别 | 运算符 | 说明 |
| --- | --- | --- |
| 算术 / 关系 | `+` `-` `*` `/` `%` `++` `--` / `==` `!=` `>` `<` `>=` `<=` | 整数相除向零截断，`%` 只用于整数；关系运算结果是 `bool` |
| 逻辑 / 位 | `&&` `\|\|` `!` / `&` `\|` `^` `~` `<<` `>>` | 逻辑运算短路求值；位运算按二进制位操作，适用于整型 |
| 赋值 / 三元 / 杂项 | `=` `+=` `-=` `*=` `/=` `%=` 等 / `? :` / `sizeof` `,` `.` `->` `::` `new` `delete` | 复合赋值先算再写回；`? :` 是唯一的三目运算符 |
1. 例：`7 / 2` 得 3、`7 % 2` 得 1、`7 * 1.0 / 2` 得 3.5；`-7 / 2` 得 -3、`-7 % 2` 得 -1（C++11 起向零取整）。位运算常用于一组开关标志、掩码、乘除 2 的幂：`flags |= 0b0101` 置位、`flags &= ~0b0010` 清位、`(flags & 0b1000) != 0` 查位；移位量必须小于位宽，对负数左移是未定义行为。
### 6.2 自增、赋值、三元与逗号
| 写法 | 含义 | 返回值 | 性能 |
| --- | --- | --- | --- |
| `++i`（前置） | 先自增，返回自增后的值 | 变量本身（C++ 中是左值） | 直接返回引用，无临时对象 |
| `i++`（后置） | 返回自增前的值，再自增 | 旧值的临时副本（右值） | 类类型要构造临时对象 |
1. `int j = 5;` 时 `int a = ++j;` 使 `a = j = 6`，而 `int b = j++;` 使 `b = 6`、`j = 7`。对迭代器和自定义类型优先前置 `++it`，后置要多一次对象拷贝；对 `int` 两者无差异。不要在一个表达式里对同一变量多次自增自减（`n = n++ + ++n` 是未定义行为）。
2. `a = b = 0` 合法，因为赋值表达式返回被赋值的对象；别和 `==` 混淆，`if (a = 1)` 恒为真，开 `-Wparentheses` 可告警。三元 `max = (a > b) ? a : b;` 两个分支类型会统一，分支里有副作用时不如用 `if`；逗号表达式 `(i++, j++, j)` 取最后一个值；`.` 访问对象成员，`->` 通过指针访问（等价 `(*p).first_name`）。
### 6.3 优先级与结合性
| 优先级 | 运算符 | 结合性 |
| --- | --- | --- |
| 1（最高）~3 | `::`；`()` `[]` `.` `->` 后置 `++` `--`；`!` `~` 前置 `++` `--` 一元 `-` `+` `*` `&` `sizeof` `new` `delete` | 1~2 从左到右，3 从右到左 |
| 4~10 | `.*` `->*`；`*` `/` `%`；`+` `-`；`<<` `>>`；`<=>`；`<` `<=` `>` `>=`；`==` `!=` | 从左到右 |
| 11~15 | `&`；`^`；`\|`；`&&`；`\|\|` | 从左到右 |
| 16~17 | `? :`、`=` 及复合赋值、`throw`；`,` | 16 从右到左，17 从左到右 |
1. 只记一条主线：**后缀 > 前缀 > 乘除 > 加减 > 移位 > 关系 > 相等 > 位与/异或/或 > 逻辑与 > 逻辑或 > 三元 > 赋值 > 逗号**。常见坑：`a & b == c` 实际是 `a & (b == c)`，因为 `==` 优先级高于 `&`；不确定就加括号。
## 7 控制流
### 7.1 if 与 switch
```cpp
#include <iostream>
#include <map>
#include <string>
int main()
{
    int score = 85;
    if (score >= 90) {
        std::cout << "A\n";
    } else if (score >= 80) {
        std::cout << "B\n";              // 命中
    } else {
        std::cout << "C\n";
    }
    switch (score / 10) {
        case 9:
            std::cout << "one\n";
            break;                       // 忘了 break 会「贯穿」到下一个分支
        case 8:
        case 7:                          // 多个 case 共用一段处理
            std::cout << "two or three\n";
            break;
        default:
            break;
    }
    std::map<std::string, int> ages{{"Tom", 20}};
    if (auto it = ages.find("Tom"); it != ages.end()) {   // C++17：if 初始化 + 条件
        std::cout << it->first << " 的年龄是 " << it->second << '\n';
    }
    return 0;
}
```
1. C++17 起 `if`/`switch` 支持「初始化语句; 条件」的写法（`switch (int n = 3; n)` 同理），变量作用域限制在该语句内。`switch` 的表达式只能是整型、枚举或字符型，**不能是 `std::string`**；按字符串分支用 `if-else` 链或 `std::map<std::string, 枚举/函数>` 查表，`case` 标签必须是编译期常量。忘写 `break` 导致分支贯穿是高频 bug，确实要贯穿时加注释或 `[[fallthrough]];`（C++17）。
### 7.2 三种循环与跳转
```cpp
#include <iostream>
#include <vector>
int main()
{
    int a = 10;
    while (a < 13) {
        std::cout << a++ << ' ';         // while：条件先行，可能一次都不执行
    }
    int b = 0;
    do {
        std::cout << "do" << b;          // do-while：先执行一次再判断
    } while (++b < 2);
    std::vector<std::string> names{"A", "B"};
    std::string joined;
    for (int x : {1, 2, 3}) {            // 可遍历初始化列表；names 也可写 for (const auto& n : names)
        if (x == 2) {
            continue;                    // 跳过本次
        }
        joined += std::to_string(x);     // for (auto& n : names) n += "!"; 可修改原元素
    }
    std::cout << '\n' << joined << names[0] << '\n';   // AB1A!
    return 0;
}
```
1. 范围 `for` 写成 `for (int x : arr)` 时 `x` 是副本，改它不影响数组；要修改用 `for (int& x : arr)`，只读且元素较大用 `for (const auto& x : arr)`。已知次数用 `for`，条件驱动用 `while`，至少执行一次用 `do-while`。
2. `break` 只跳一层循环或一层 `switch`，`continue` 跳过本次循环剩余部分；跳出嵌套循环用标志变量或把循环封成函数后 `return`。`goto` 写作 `retry: ...; if (count < 2) goto retry;`，只能跳到同一函数内的标签、不能跳过变量初始化，也不建议在业务代码里用（C++ 的统一清理交给 RAII，见 11.4）。
## 8 函数
### 8.1 声明与定义
每个 C++ 程序至少有一个 `main`。函数声明（原型）给出名字和参数类型，让编译器在调用点检查参数；函数定义给出函数体。函数可以定义在调用之后，但调用点之前必须见过声明。
```cpp
#include <iostream>
int max(int a, int b);              // 声明（原型），也可写成 int max(int, int);
int main()
{
    std::cout << max(4, 78) << '\n';   // 78
    return 0;
}
int max(int a, int b)               // 定义
{
    return a > b ? a : b;
}
```
1. 声明里参数名可省略，只有类型是必需的；函数只能定义一次、可以声明多次，跨文件时原型放头文件、定义放某个 `.cpp`。C++ 中没有「不写返回类型默认为 int」的规矩，必须显式写，无返回值写 `void`。
### 8.2 参数传递
| 方式 | 写法 | 能否修改实参 | 何时用 |
| --- | --- | --- | --- |
| 传值 | `void f(int x)` | 不能，函数内改的是副本 | 内置小类型 |
| 引用 / `const` 引用 | `void f(int& x)` / `void f(const std::string& s)` | 引用段能改；`const` 引用不能改、也不拷贝 | 修改实参 / 传递只读大对象（最常用） |
| 指针 | `void f(int* p)` | 能（通过 `*p`），指针本身可判空 | 参数可以为空、C 接口 |
```cpp
#include <iostream>
#include <string>
void swapByValue(int x, int y)       { int t = x; x = y; y = t; }    // 不影响实参
void swapByPointer(int* x, int* y)   { int t = *x; *x = *y; *y = t; }
void swapByReference(int& x, int& y) { int t = x; x = y; y = t; }
void print(const std::string& s)     { std::cout << s << '\n'; }     // 只读引用
int main()
{
    int a = 100, b = 200;
    swapByValue(a, b);
    swapByPointer(&a, &b);
    std::cout << a << ' ' << b << '\n';   // 200 100
    swapByReference(a, b);
    print("const 引用");
    return 0;
}
```
1. 内置小类型传值即可；类类型和 `std::string`、`std::vector` 这类大对象，只读用 `const T&`、要修改用 `T&`。
2. 引用参数不能传字面量（`f(3)` 对 `int&` 不成立），`const` 引用可以；标准库已有 `std::swap`，上面只为演示三种传参方式。
### 8.3 默认参数与重载
```cpp
#include <iostream>
int sum(int x, int y = 300) { return x + y; }          // 只能给最右边的参数默认值
void play(int i)    { std::cout << "整数: " << i << '\n'; }
void play(double f) { std::cout << "浮点: " << f << '\n'; }
int main()
{
    std::cout << sum(5) << ' ' << sum(5, 899) << '\n';   // 305 904
    play(1);            // 整数: 1
    play(2.5);          // 浮点: 2.5
    play('a');          // 整数: 97（char 是整型，提升为 int）
    return 0;
}
```
1. 默认值只能从右往左连续给，同一作用域内一个参数只能有一个默认值，通常写在头文件声明里；它在编译期填入调用点、运行时不判断，因此虚函数的默认参数取静态类型的值，容易误导。
2. 同一作用域内可以有多组同名函数，只要参数列表（个数、类型、顺序）不同就是**重载**，**返回类型不同不能构成重载**。重载决议优先级大致是：精确匹配 > 整数提升 > 标准转换 > 用户自定义转换；多个重载一样「好」时编译器报二义性错误，只有默认参数不同（`f(int)` 与 `f(int, int = 0)`）时调用 `f(1)` 也会二义。
### 8.4 inline
`inline` 建议编译器把函数体展开到调用点、省去调用开销（用空间换时间），但只是建议：函数太大、含递归、被取地址或 `-O0` 编译时都可能被拒绝。现代 C++ 里它更重要的作用是**允许多个翻译单元重复定义**，所以 `inline int maxOf(int x, int y) { return x > y ? x : y; }` 这样的定义可以直接放头文件；类内定义的成员函数隐式就是 `inline`。
## 9 Lambda 表达式
Lambda（C++11）是匿名的、可就地定义并立即使用的函数对象，尤其适合传给算法的回调与短小的谓词。语法：`[capture](parameters) mutable -> return-type { body }`。
| 部分 | 说明 |
| --- | --- |
| `[capture]` | 捕获列表，也是 Lambda 的引出符，编译器靠它识别 Lambda；为空也不能省略 |
| `(parameters)` | 参数列表，与普通函数一致；无参时可连同括号一起省略 |
| `mutable` | 默认 Lambda 的 `operator()` 是 `const`，加 `mutable` 才能修改按值捕获的副本；加了它参数括号不可省略 |
| `-> return-type` | 尾置返回类型，可省略、由 `return` 推导；要返回引用时必须写 |
| `{ body }` | 函数体，除参数外还能使用捕获进来的变量 |
| 捕获 | 含义 |
| --- | --- |
| `[]` | 不捕获任何外部变量，使用外部变量会编译错误 |
| `[x]` / `[&x]` | 按值捕获副本 / 按引用捕获，后者修改会影响外面，要小心 `x` 的生命周期 |
| `[=]` / `[&]` | 隐式按值 / 按引用捕获所有用到的外部变量 |
| `[&, x]` / `[=, &x]` | 默认按引用、`x` 例外按值 / 默认按值、`x` 例外按引用 |
| `[this]` | 捕获当前对象指针（成员函数中常用），C++17 起可写 `[*this]` 按值捕获整个对象 |
### 9.1 捕获、mutable 与立即调用
```cpp
#include <algorithm>
#include <iostream>
#include <vector>
int main()
{
    int a = 1, b = 2;
    auto byValue  = [a]() mutable { a += 10; return a; };   // mutable 才能改副本
    auto byRef    = [&b]() { b += 10; };
    int sum = [] {                                          // 立即调用：[]{...}()
        int s = 0;
        for (int i = 1; i <= 10; ++i) {
            s += i;
        }
        return s;
    }();
    std::vector<int> v{5, 2, 8, 1, 9};
    std::sort(v.begin(), v.end(), [](int x, int y) { return x > y; });   // 降序
    int threshold = 4;
    auto found = std::find_if(v.begin(), v.end(),
                              [threshold](int x) { return x < threshold; });
    if (found != v.end()) {
        std::cout << byValue() << a << ' ' << b << ' ' << sum << ' ' << *found << '\n';
    }
    return 0;
}
```
1. 每次调用 `byValue()` 改的都是它自己保存的副本，所以得到 11，而外层 `a` 仍是 1；按引用捕获的 Lambda 不能比被捕获的变量活得久，否则就是悬垂引用（见 10.4），`[this]` 捕获对象指针时同理。`[=]`/`[&]` 方便但看不出依赖了哪些变量，很多团队禁用。
2. 「立即调用」尾部的 `()` 就是调用运算符，适合需要多行逻辑的复杂初始化。无捕获的 Lambda 可以隐式转成函数指针，能直接传给 C 接口；用到外部变量才写捕获列表。泛型 Lambda（C++14）可写 `[](auto x) { ... }`，容器与算法完整速查见 [STL标准库](C++STL标准库.md)。
## 10 引用与指针
### 10.1 引用必须初始化
引用是已存在变量的**别名**，不新分配对象；必须在定义时绑定，之后不能改绑，因此 `int& r;` 是编译错误。它不占独立对象，但底层通常以指针实现，`sizeof(r)` 得到的是被引用类型的大小、不是指针大小。例：`int i = 42; int& r = i;` 之后 `r = 100;` 等于改 `i`；再写 `r = j;` 是**赋值**，把 `j` 的值赋给 `i`，而不是让 `r` 改绑到 `j`。
### 10.2 引用 vs 指针
| 对比项 | 引用 `T&` | 指针 `T*` |
| --- | --- | --- |
| 是否必须初始化 | 必须，且之后不能改绑 | 可以后赋值、可以改指向 |
| 能否为空 | 不能 | 可以，`nullptr` 表示无效 |
| 语法 | 直接当变量用，不需解引用 | 要 `*p` 解引用、`p->` 访问成员 |
| 是否占内存 | 不单独分配 | 本身是一个对象 |
| 常见用途 | 函数参数/返回值、别名 | 可选参数、动态对象、链表节点、指针运算 |
```cpp
#include <iostream>
void addByPointer(int* x)   { if (x) { *x += 1; } }   // 可以为空，必须判空
void addByReference(int& x) { x += 1; }               // 不能为空，无需判空
int main()
{
    int a = 1;
    addByPointer(&a);           // 传地址
    addByReference(a);          // 直接传对象
    int* p = nullptr;
    addByPointer(p);            // 空指针安全
    // addByReference(*p);      // 解引用空指针 → 未定义行为
    std::cout << a << '\n';     // 3
    return 0;
}
```
### 10.3 nullptr 与常量引用
```cpp
#include <iostream>
#include <string>
void print(const std::string& s)      // 只读常量引用：不拷贝、可接字面量
{
    std::cout << s << '\n';
}
int main()
{
    int* p = nullptr;                 // C++11 的空指针常量，类型为 std::nullptr_t
    print(p ? "非空" : "空指针");      // 判空：也可写 if (!p) 或 p == nullptr
    std::cout << [](const int& r) { return r; }(42) << '\n';   // 普通 int& 不能绑定字面量
    return 0;
}
```
1. C++11 的 `nullptr` 是真正的空指针常量，能隐式转成任意指针类型，又不会像 `NULL`（通常是 `0`）那样被当成整数（`f(NULL)` 可能误选 `f(int)` 重载）。新代码一律用 `nullptr`，尤其在有重载或模板推导的场合。
2. `const T&` 是「万能只读参数」，`int`、`double`、`std::string`、临时结果都能直接传；它能绑定临时对象与字面量并把生命周期延长到引用作用域结束。非 const 引用 `T&` 不能绑定字面量或临时对象（`int& r = 1;` 编译错误），返回 `const T&` 时必须保证被引用对象活得比返回值长。
### 10.4 悬垂引用与野指针
```cpp
#include <iostream>
int& goodRef()
{
    static int x = 1;         // static 生命周期是整个程序，可以安全返回
    return x;
}
// int& badRef() { int x = 1; return x; }     // 错误示范：返回局部变量的引用
int main()
{
    int& r = goodRef();
    r = 42;
    static int local = 7;
    std::cout << r << ' ' << *&local << '\n';   // 42 7
    return 0;
}
```
1. 指向已销毁对象的引用或指针叫悬垂（dangling），未初始化的指针叫野指针；它们都能编译通过，运行时才崩溃或读到脏数据，是最难查的一类 bug。
2. 安全规则：**不要返回局部变量的引用或指针**，非 static 局部变量的地址只在它的作用域内有效；指针定义时初始化为 `nullptr`，`delete` 后立即置空，容器扩容会让指向元素的指针和迭代器失效。现代 C++ 主要靠智能指针和容器解决生命周期问题（见 14.2）。
## 11 结构体与类入门
### 11.1 struct 与 class 的区别
| 对比 | `struct` | `class` |
| --- | --- | --- |
| 默认成员访问 | `public` | `private` |
| 默认继承方式 | `public` | `private` |
| 常用场合 | 纯数据聚合、要与 C 互通的结构 | 有不变式、需要封装行为的类型 |
1. C++ 中二者只有默认访问和默认继承两点区别，都能有成员函数、构造/析构、虚函数、模板成员。习惯上只放数据的「记录」用 `struct`，有不变式和对外接口的用 `class`；C 与 C++ 的 struct 差异见 [C与C++差异](../C/C与C++差异.md)。
### 11.2 一个完整的类
```cpp
#include <iostream>
#include <string>
#include <utility>
class Person {
public:
    static int count;                             // 静态成员：所有对象共享一份
    Person();                                     // 默认构造函数
    Person(std::string name);                     // 带参构造函数
    Person(std::string name, int age);            // 委托构造函数
    void setName(const std::string& n) { name_ = n; }
    std::string getName() const { return name_; } // 末尾 const：不修改成员
    int getAge() const { return age_; }
private:                                          // 只能在类内访问
    std::string name_;
    int age_ = 0;                                 // 类内初始化，默认值
};
int Person::count = 0;                            // 静态成员必须在类外定义（分配存储）
Person::Person() : name_("匿名"), age_(0) { ++count; }   // 初始化列表在函数体之前初始化
Person::Person(std::string n) : name_(std::move(n)), age_(0) { ++count; }
Person::Person(std::string n, int a) : Person(std::move(n)) { age_ = a; }   // 委托构造
int main()
{
    Person p1;                                    // 默认构造
    p1.setName("Jack");
    Person p2("Maria");                           // 带参构造
    Person p3("Tom", 18);                         // 委托构造
    std::cout << p1.getName() << ' ' << p2.getAge() << ' ' << p3.getAge()
              << ' ' << Person::count << '\n';   // Jack 0 18 3
    return 0;
}
```
1. 委托构造让多个构造函数复用同一段初始化：被委托者执行完再进入委托者的函数体，`name_` 只初始化一次。
### 11.3 构造函数与初始化列表
| 构造函数 | 写法 | 何时调用 |
| --- | --- | --- |
| 默认构造函数 | `Person();` 或不写让编译器生成 | 定义对象不传参时 |
| 带参 / 委托构造函数 | `Person(std::string name);` / `A() : A(1, 2) {}` | 传参创建对象 / 转调同类另一个构造函数复用初始化逻辑 |
| 拷贝构造函数 | `Person(const Person& other);` | 用同类型对象初始化新对象时 |
| `= default` / `= delete` | `Person() = default;` `Person(const Person&) = delete;` | 要求编译器生成 / 禁止使用 |
1. 初始化列表在构造时**直接初始化**成员；函数体内赋值是「先默认构造再赋值」，对类成员多一次开销，对 `const` 成员和引用成员则根本不允许。成员按**声明顺序**初始化（与列表书写顺序无关），写法最好一致，`-Wreorder` 可告警。
2. 不写构造函数时编译器会生成默认构造函数；一旦自己写了带参构造函数，默认构造函数就不再自动生成，需要时写 `Person() = default;`。单参数构造函数若不希望允许隐式转换，加 `explicit`，防止 `Person p = 1;` 这种意外转换。拷贝构造与 Rule of 3/5 见 [C++详解](C++详解.md)。
### 11.4 析构函数与 RAII
析构函数名是 `~类名()`，对象生命周期结束时自动调用，用来释放资源；不能重载、不能带参数、不能有返回值。只在拥有裸资源时才需要自己写，成员是 `std::string`、`std::vector` 时会自动管理。「构造函数申请资源、析构函数释放资源」叫 RAII，是 C++ 管理资源的核心思想：资源生命周期绑定对象生命周期，异常路径也不会漏；析构函数默认 `noexcept`，析构中抛异常且没人捕获会直接 `std::terminate`。例：
```cpp
#include <cstdio>
#include <iostream>
class FileGuard {
public:
    explicit FileGuard(const char* path) : fp_(std::fopen(path, "w"))
    {
        std::cout << "打开文件\n";
    }
    ~FileGuard()                       // 作用域结束、delete、异常展开时都会调用
    {
        if (fp_) std::fclose(fp_);
        std::cout << "关闭文件\n";
    }
private:
    std::FILE* fp_;
};
int main() {
    FileGuard f("demo.txt");           // 出 main 作用域自动析构
    return 0;
}
```
### 11.5 this、static 成员与访问控制
1. 成员函数内部的 `this` 是指向当前对象的指针，用于区分成员与同名参数、返回自身实现链式调用：`Counter& add(int v) { value_ += v; return *this; }` 就能写 `c.add(1).add(2)`；`*this` 就是当前对象本身，静态成员函数里没有 `this`。
2. 静态成员属于类本身而不是某个对象、所有对象共享一份：数据成员要在类外**定义一次**（C++17 起可用 `inline static int alive_ = 0;` 在类内定义），静态成员函数只能访问静态成员、通过 `Counter::alive()` 调用。线程安全的计数要改用 `std::atomic`。
| 修饰符 | 类内 | 派生类 | 类外 |
| --- | --- | --- | --- |
| `public` | 可访问 | 可访问 | 可访问 |
| `protected` | 可访问 | 可访问 | 不可访问 |
| `private` | 可访问 | 不可访问 | 不可访问 |
3. `private` 是编译期的可见性检查，不是安全边界。数据成员通常 `private`，通过 `public` 成员函数读写，把不变式（如年龄不能为负）集中到 setter 里检查——这就是数据封装。友元 `friend` 可以授权某个函数或类访问私有成员，会破坏封装，除运算符重载（见 13.1）和紧密协作的类外少用，详见 [C++详解](C++详解.md)。
## 12 继承入门
### 12.1 继承的基本写法
派生类通过 `: 继承方式 基类名` 复用基类成员，被继承的类叫基类（父类），新类叫派生类（子类）。与 Java 不同，C++ 支持多继承（`class Dog : public Animal, public Pet {};`），但容易带来二义性和菱形继承问题，初学先掌握单继承。
```cpp
#include <iostream>
#include <string>
class Animal {                        // 基类
public:
    void eat() const { std::cout << name_ << " 吃东西\n"; }
    std::string name() const { return name_; }
protected:
    std::string name_ = "动物";
};
class Dog : public Animal {           // 派生类，public 继承
public:
    void bark() const { std::cout << name_ << " 汪汪\n"; }   // 基类 protected 成员可用
};
int main() {
    Dog d;
    d.eat();                          // 继承自基类
    d.bark();                         // 自己的成员
    return 0;
}
```
### 12.2 public、protected、private 继承
| 基类成员的访问级别 | `public` 继承后 | `protected` 继承后 | `private` 继承后 |
| --- | --- | --- | --- |
| `public` | `public` | `protected` | `private` |
| `protected` | `protected` | `protected` | `private` |
| `private` | 不可访问 | 不可访问 | 不可访问 |
1. 规律：**继承方式会把基类成员的级别压到不高于它的水平**。`public` 继承保持 is-a 语义，最常用；另外两种表示实现复用，现代 C++ 更推荐改用组合（把基类作为成员）。
2. `private` 继承后，类外和派生类的派生类都看不到基类的 `public`/`protected` 成员；基类的 `private` 成员无论如何都不能被派生类直接访问，只能通过基类的 `public`/`protected` 成员函数间接使用。
### 12.3 构造与析构顺序
```cpp
#include <iostream>
class Base {
public:
    Base()  { std::cout << "Base 构造\n"; }
    ~Base() { std::cout << "Base 析构\n"; }
};
class Member {
public:
    Member()  { std::cout << "Member 构造\n"; }
    ~Member() { std::cout << "Member 析构\n"; }
};
class Derived : public Base {
public:
    Derived() : Base(), m_() { std::cout << "Derived 构造\n"; }   // 先基类、再成员、最后自己
    ~Derived() { std::cout << "Derived 析构\n"; }
private:
    Member m_;
};
int main() {
    Derived d;   // Base → Member → Derived → Derived 析构 → Member 析构 → Base 析构
    return 0;
}
```
1. 构造顺序：基类构造函数 → 成员按声明顺序构造 → 自身构造函数体；析构顺序完全相反。派生类构造函数必须能调到基类的某个构造函数：不写时调基类默认构造函数，基类没有默认构造函数就必须在初始化列表里显式写。
### 12.4 override 与 final
| 关键字 | 位置 | 作用 |
| --- | --- | --- |
| `override`（C++11） | 虚函数声明末尾 | 断言「我确实覆盖了基类的虚函数」，签名写错直接编译报错 |
| `final`（C++11） | 虚函数末尾或类名之后 | 禁止继续覆盖该虚函数 / 禁止该类被继承 |
```cpp
#include <iostream>
class Shape {
public:
    virtual double area() const { return 0.0; }
    virtual ~Shape() = default;
};
class Circle : public Shape {
public:
    explicit Circle(double r) : r_(r) {}
    double area() const override { return 3.14159 * r_ * r_; }   // 签名写错会报错
private:
    double r_;
};
class Square final : public Shape {     // final 类：不能再被继承
public:
    explicit Square(double side) : side_(side) {}
    double area() const override { return side_ * side_; }
private:
    double side_;
};
// class Bad : public Square {};        // 错误：Square 是 final
int main()
{
    Circle c(1.0);
    Square s(2.0);
    std::cout << c.area() << ' ' << s.area() << '\n';   // 3.14159 4
    return 0;
}
```
1. 覆盖虚函数时一律写 `override`，它能防住「基类参数是 `int`、派生类写成 `long`」这类看起来像覆盖、实际是新函数的隐蔽错误。类标记 `final` 后编译器还能做去虚化优化，不想被继承的类型用 `final` 表达意图比写注释可靠。
## 13 重载与多态入门
### 13.1 运算符重载
运算符重载让自定义类型也能用 `+`、`<<`、`==` 等符号，本质是名为 `operator+`、`operator<<` 的函数。原则是只在语义直观时重载，不改变运算符原有含义。`+` 通常写成成员函数（左操作数是 `*this`），`<<` 必须写成非成员函数（左操作数是 `std::ostream`）并声明为友元：
```cpp
#include <iostream>
class Point {
public:
    Point(int x = 0, int y = 0) : x_(x), y_(y) {}
    Point operator+(const Point& rhs) const          // 成员：左操作数是 *this
    {
        return Point(x_ + rhs.x_, y_ + rhs.y_);
    }
    friend std::ostream& operator<<(std::ostream& os, const Point& p);   // 友元声明
private:
    int x_;
    int y_;
};
std::ostream& operator<<(std::ostream& os, const Point& p)   // 非成员：左操作数是 ostream {
    return os << '(' << p.x_ << ", " << p.y_ << ')';
}
int main()
{
    Point a(1, 2), b(3, 4);
    Point c = a + b;                    // 调 operator+
    std::cout << c << '\n';             // (4, 6)
    return 0;
}
```
1. 不能重载的运算符：`.`、`.*`、`::`、`?:`、`sizeof`；`=`、`[]`、`()`、`->` 只能作为成员函数重载。返回自定义类型按值（如 `+`）、返回引用（如 `<<`）要分清，返回局部对象的引用一定是错的；C++20 的 `operator<=>` 能一次生成全部比较运算符，见 [C++详解](C++详解.md)。
### 13.2 虚函数
在基类函数前加 `virtual`，通过基类指针或引用调用时，实际执行**运行时对象真实类型**对应的版本，这叫动态绑定（后期绑定）；不加 `virtual` 就按指针的静态类型静态绑定。
```cpp
#include <iostream>
class Animal {
public:
    virtual void eat() const { std::cout << "动物吃饭\n"; }   // 虚函数
    virtual ~Animal() = default;                              // 有虚函数就要有虚析构
};
class Dog : public Animal {
public:
    void eat() const override { std::cout << "狗吃狗粮\n"; }
};
class Cat : public Animal {
public:
    void eat() const override { std::cout << "猫吃猫粮\n"; }
};
int main() {
    Animal* animal = nullptr;
    Dog dog;
    animal = &dog;
    animal->eat();              // 狗吃狗粮：运行时看真实类型
    animal = new Cat();
    animal->eat();              // 猫吃猫粮
    delete animal;
    Dog d2;
    Animal copy = d2;           // 按值拷贝发生对象切片，只剩 Animal 部分
    copy.eat();                 // 动物吃饭：调不到 Dog 的版本
    return 0;
}
```
1. **必须通过基类指针或引用调用虚函数**才会多态；直接用基类对象（按值传递、按值返回、赋值）会发生对象切片，派生类部分被砍掉。多态调用有查虚表 + 间接跳转的开销，但远小于业务逻辑本身的成本。
### 13.3 纯虚函数与抽象类
把虚函数写成 `= 0` 就是纯虚函数，表示「接口在这里声明、实现留给派生类」；含纯虚函数的类叫抽象类，不能实例化、只能被继承。C++ 没有专门的 `interface` 关键字，抽象类就是表达接口的标准做法；只暴露必要接口、隐藏实现细节，也就是数据抽象。典型用法是用 `std::vector<std::unique_ptr<Shape>>` 装不同派生类对象，循环里调 `s->area()` 统一处理：
```cpp
#include <iostream>
#include <memory>
#include <vector>
class Shape {                                  // 抽象类：接口
public:
    virtual double area() const = 0;           // 纯虚函数
    virtual ~Shape() = default;
};
class Circle : public Shape {
public:
    explicit Circle(double r) : r_(r) {}
    double area() const override { return 3.14159 * r_ * r_; }
private:
    double r_;
};
class Rect : public Shape {
public:
    Rect(double w, double h) : w_(w), h_(h) {}
    double area() const override { return w_ * h_; }
private:
    double w_;
    double h_;
};
int main() {
    // Shape s;                                // 错误：抽象类不能实例化
    std::vector<std::unique_ptr<Shape>> shapes;
    shapes.push_back(std::make_unique<Circle>(1.0));
    shapes.push_back(std::make_unique<Rect>(2.0, 3.0));
    double total = 0.0;
    for (const auto& s : shapes) {
        total += s->area();
    }
    std::cout << "总面积 " << total << '\n';   // 9.14159
    return 0;
}
```
1. 派生类必须实现**全部**纯虚函数才能实例化，否则它自己也是抽象类；抽象类可以有数据成员和普通成员函数，纯虚函数也可以有定义，但仍必须被派生类覆盖。对象模型细节见 [C++详解](C++详解.md)。
## 14 动态内存入门
### 14.1 new 与 delete
```cpp
#include <iostream>
int main()
{
    int* parr = new int[10]();          // 分配 10 个 int，值初始化为 0（new int 则未初始化）
    int* pzero = new int(42);           // 分配并初始化为 42
    delete pzero;                       // 释放单个对象
    delete[] parr;                      // 释放数组，必须用 delete[]
    parr = pzero = nullptr;             // 释放后置空，避免悬垂
    return 0;
}
```
1. `new` 在堆上分配内存并调用构造函数、返回对应类型的指针，`delete` 调用析构函数并释放内存；与 `malloc`/`free` 不同，它们会调用构造/析构函数，返回的指针也不需要强制转换。`new` 失败时抛 `std::bad_alloc`，不需要再判断是否为 `nullptr`。
2. `new` 出来的对象必须手动 `delete`，忘掉就内存泄漏，同一块内存 `delete` 两次是未定义行为。
| 分配 | 释放 | 说明 |
| --- | --- | --- |
| `Box* p = new Box[4];` | `delete[] p;` | 调用 4 次构造、4 次析构；`new[]` 必须配 `delete[]` |
| `new[]` 却写 `delete` | — | 未定义行为：只析构第一个元素，其余既不析构也不释放 |
### 14.2 为什么优先用智能指针
裸 `new`/`delete` 要手动配对，遇到异常、提前 `return`、多分支时极易漏掉，造成泄漏或重复释放。智能指针把「释放」绑定到对象析构（RAII），出作用域自动释放：`std::unique_ptr<T>` 独占所有权、不可拷贝可移动（用 `std::move` 转移所有权），是默认选择；`std::shared_ptr<T>` 共享所有权、引用计数为 0 才释放；`std::weak_ptr<T>` 打破 `shared_ptr` 的循环引用。`std::make_unique<int>(42)`、`std::make_shared<int>(7)` 分别创建前两者，`w.use_count()` 查看计数。
1. 新代码原则上不出现裸 `new`/`delete`，需要动态对象就 `make_unique`/`make_shared`，需要数组就 `std::vector`。对 `int` 这类没有析构函数的类型，`delete` 与 `delete[]` 混用可能「看起来没事」，但它是 UB，换平台或换优化级别就可能崩。所有权语义、循环引用、自定义删除器见 [C++详解](C++详解.md)，堆与 `malloc` 的关系见 [C详解](../C/C详解.md)。
## 15 输入输出
### 15.1 iostream 与 cin/cout
| 头文件 | 内容 |
| --- | --- |
| `<iostream>` | `cin`（标准输入）、`cout`（标准输出，带缓冲）、`cerr`（标准错误，无缓冲）、`clog`（标准错误，带缓冲） |
| `<iomanip>` | 格式化操纵符：`setw`、`setprecision`、`setfill` 等 |
| `<fstream>` | 文件流：`ifstream`、`ofstream`、`fstream` |
```cpp
#include <iostream>
#include <limits>
#include <string>
int main()
{
    std::string name;
    int age = 0;
    std::cin >> name >> age;                    // 按空白分割读取，跳过空格和换行
    std::cout << "姓名：" << name << "，年龄：" << age << '\n';
    std::cerr << "这是错误流，无缓冲，写到 stderr\n";
    std::clog << "这是日志流，带缓冲，写到 stderr\n";
    // 读取一整行（含空格）：与 >> 混用前先清掉残留的换行
    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    std::string line;
    std::getline(std::cin, line);
    std::cout << "整行：" << line << '\n';
    return 0;
}
```
1. `cin >> x` 成功时返回 `cin`，失败（类型不匹配、到达文件尾）时进入失败状态，`while (std::cin >> x)` 就是常用的循环读取写法。
2. `cin >>` 与 `std::getline` 混用是新手第一大坑：`>>` 读完数字把换行留在缓冲区，`getline` 立刻读到空行。`std::endl` 除换行还会刷新缓冲区，频繁输出时比 `'\n'` 慢。
### 15.2 格式化输出与 iomanip
| 操纵符 | 作用 |
| --- | --- |
| `std::fixed` / `std::scientific` | 定点 / 科学计数法输出浮点 |
| `std::setprecision(n)` | 精度：配合 `fixed` 表示小数点后位数 |
| `std::setw(n)` | 下一次输出占 `n` 个字符宽，**只对下一次生效** |
| `std::setfill(c)` / `std::left` / `std::right` | 填充字符、左 / 右对齐 |
| `std::hex` / `std::oct` / `std::dec` | 十六进制、八进制、十进制输出 |
| `std::boolalpha` / `std::showpos` | `bool` 输出 `true`/`false`、正数显示 `+` |
```cpp
#include <iomanip>
#include <iostream>
int main()
{
    std::cout << std::fixed << std::setprecision(2) << 3.14159265358979 << '\n';   // 3.14
    std::cout << std::setfill('0') << std::setw(5) << 42 << '\n';                  // 00042
    std::cout << std::hex << std::showbase << 255 << '\n';                         // 0xff
    std::cout << std::dec << std::boolalpha << true << '\n';                       // true
    return 0;
}
```
1. `setw` 是一次性的，每次输出前都要重新设置；`setfill`、`setprecision`、`fixed`、`hex`、`boolalpha` 会一直生效，直到被改回。`printf` 风格（`<cstdio>`）仍可用，但更推荐流操纵符或 `std::format`（C++20），类型安全，不会因为格式符写错而崩溃。
### 15.3 文件读写
| 模式 | 含义 |
| --- | --- |
| `std::ios::in` / `std::ios::out` | 打开用于读取 / 写入（`out` 默认会截断已有文件） |
| `std::ios::app` | 追加模式，所有写入都追加到文件末尾 |
| `std::ios::ate` | 打开后立刻定位到文件末尾 |
| `std::ios::trunc` | 打开前把文件长度截断为 0（`out` 默认带） |
| `std::ios::binary` | 二进制模式，按字节读写，不做换行转换 |
```cpp
#include <fstream>
#include <iostream>
#include <string>
int main()
{
    std::ofstream out("demo.txt");          // 默认 out | trunc，不存在会自动创建
    std::ofstream app("demo.txt", std::ios::app);   // 追加，保留原有内容
    if (!out || !app) {
        std::cerr << "打开失败\n";
        return 1;
    }
    out << "第一行" << '\n';
    app << "追加的一行" << '\n';
    std::ifstream in("demo.txt");           // ifstream 只读
    std::string line;
    while (std::getline(in, line)) {        // 逐行读取
        std::cout << line << '\n';
    }
    return 0;
}
```
1. 打开后一定要检查 `if (!file)`：路径错误、权限不足、文件被占用都不会抛异常，只设置失败状态。
2. `ofstream` 只写、`ifstream` 只读、`fstream` 可同时读写（`in | out` 组合）；文件流析构会自动关闭文件，显式 `close()` 主要用于需要立刻落盘或复用对象。二进制读写的 `read()`/`write()` 用法见 [C++详解](C++详解.md)。
## 16 初学常见错误
1. **`delete` 与 `delete[]` 混用**：`new[]` 分配的一定要 `delete[]`，反过来也一样，混用是未定义行为（只析构第一个元素，其余既不析构也不释放）。用 `std::vector`、`std::string`、智能指针就能从根上避免。
2. **悬垂引用/指针**：返回局部变量的引用或指针、容器扩容后继续用旧指针或迭代器、Lambda 按引用捕获了已销毁的变量——都在运行时崩溃。规则：引用的生命周期不能超过被引用对象。
3. **隐式转换的陷阱**：`double` 转 `int` 静默丢精度；`-1 < 0u` 恒为假；指针与整数之间隐式往来。开 `-Wconversion -Wsign-conversion`，大对象构造函数加 `explicit`，初始化用 `{}` 禁止窄化。
4. **对象切片**：把派生类对象按值赋给基类对象、按值传参或按值返回，只拷走基类部分，多态失效。多态对象要用基类指针、引用或 `unique_ptr` 传递。
5. **忘记 `virtual` 析构**：用基类指针 `delete` 派生类对象时，基类析构函数不是虚的，派生类的析构不会执行，资源泄漏。规则：有虚函数的类，析构函数就必须是 `virtual`。
6. **覆盖虚函数签名写错**：参数类型差一点就成了「新函数」而不是覆盖。所有覆盖都加 `override`，让编译器替你检查。
7. **未初始化变量**：局部变量不像全局变量那样自动置 0，读到的是垃圾值。定义时就初始化，列表初始化 `{}` 至少保证为 0。
8. **数组越界与 `sizeof` 误用**：C 风格数组不检查越界；数组传给函数后退化成指针，`sizeof` 只得到指针大小。改用 `std::array`/`std::vector` 和 `.size()`，或显式传长度。
9. **`cin >>` 与 `getline` 混用**：读完数字残留的 `'\n'` 让下一次 `getline` 读到空行，混用前先 `std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');`。
10. **`switch` 忘了 `break`**：分支贯穿到下一段代码，悄悄执行了不该执行的逻辑。每个 `case` 结尾都写 `break` 或 `return`，有意贯穿时加 `[[fallthrough]];` 并注释。
11. **字符串字面量当 `char*` 用**：C++ 中字面量是 `const char[N]`，`char* p = "abc";` 自 C++11 起不合法，强行修改字面量内容是未定义行为。用 `std::string` 或 `const char*`。
12. **在头文件里定义非 `inline` 函数或全局变量**：被多个 `.cpp` 包含后在链接期报 `multiple definition`。头文件只放声明（`extern`、函数原型、`inline` 函数、类型定义），定义放 `.cpp`。
以上每一条大多能编译通过，只在运行时表现异常。两个习惯能消灭大半问题：编译固定开 `-Wall -Wextra`，优先用标准库容器和智能指针代替裸数组与裸指针。
## 17 下一步
本文只覆盖「把语法用对」的最小集，下面几篇按需深入：[C++详解](C++详解.md) 讲对象模型与虚表、模板与泛型、移动语义与完美转发、智能指针细节、异常安全、并发与 C++17/20 新特性；[C++面试题](C++面试题.md) 是高频面试题的问答式整理，覆盖本文每节的进阶追问；[STL标准库](C++STL标准库.md) 是容器、迭代器、算法与函数对象速查。从 C 过来的读者先看 [C与C++差异](../C/C与C++差异.md) 能少踩一半坑，C 基础本身见 [C基础](../C/C基础.md)。
学习路线：第 1~10 节过一遍并敲完示例 → 用 11~15 节写一个小项目（学生成绩管理、日志分析之类）→ 用第 16 节对照自查 → 再进入 [C++详解](C++详解.md) 与 [STL标准库](C++STL标准库.md)。
