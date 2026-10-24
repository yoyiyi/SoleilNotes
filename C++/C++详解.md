## 1 C++ 标准演进
「这条特性是哪个标准进来的」「项目用 14 还是 17」是面试常见开场。本章捋清 C++98 到 C++20 主线，给特性对照表与工具链支持现状（拿不准的一律「以编译器文档为准」）。
### 1.1 主线与四代特性
C++98 是第一个 ISO 标准，C++03 只修缺陷；C++11 让 C++ 变成现代语言，之后三年一版：14 修补、17 工程化、20 范式级变化。**C++11 八件套**：`auto`（按模板规则推导，丢顶层 `const`/引用）、`nullptr`、右值引用与移动语义、`std::function`/lambda、`constexpr`（11 限制极严）、`enum class`、`std::thread`、智能指针（有 `make_shared`，无 `make_unique`）。C++14：泛型 lambda、`std::make_unique`、放宽的 `constexpr`（可循环分支）、返回类型推导、变量模板。C++17：`if constexpr`（未命中分支不实例化）、结构化绑定、`optional`/`variant`/`any`、`filesystem`、inline 变量、CTAD，另有折叠表达式、`string_view`、并行算法。C++20：Concepts、Ranges（惰性视图管道）、Coroutines（`co_await`/`co_yield`，需 promise_type 或库）、Modules（`import std;` 取代文本包含）、`<=>`、`constinit`/`consteval`、`std::format`，另有 `span`、`bit_cast`、`jthread`。

```cpp
#include <functional>
#include <map>
#include <memory>
#include <ranges>
#include <variant>
template <std::integral T>                       // C++20 Concepts
T sum(const std::vector<T>& v) { T r{}; for (T x : v) r += x; return r; }
enum class Color { Red, Green };                  // C++11 强类型枚举
constexpr int square(int x) { return x * x; }     // C++11：只能一条 return
struct P { int x = 0; auto operator<=>(const P&) const = default; };   // C++20 自动比较
int main() {
    auto f = [](auto a) { return a + a; };        // C++14 泛型 lambda
    auto [x] = std::make_tuple(1);                // C++17 结构化绑定
    std::variant<int, std::string> v = 42;         // C++17 类型安全 union
    auto up = std::make_unique<Color>(Color::Red);
    auto evens = std::views::iota(1, 5) | std::views::filter([](int n) { return n % 2 == 0; });
    int n = 0;
    for (int i : evens) n += i;                   // 2 + 4
    return square(5) + f(1) + x + std::get<int>(v) + static_cast<int>(*up) + n;
}
```

Ranges 视图惰性且不拥有元素：容器销毁后视图即悬垂，别跨作用域保存。
### 1.2 特性对照表
| 特性 | 版本 | 头文件/关键字 | 一句话 | 常见坑 |
| --- | --- | --- | --- | --- |
| `auto` | 11 | 关键字 | 按初始化器推导 | 丢 `const`/引用，是拷贝 |
| `nullptr` | 11 | 关键字 | 类型安全的空指针 | 老代码仍用 `NULL` |
| 移动语义 | 11 | `T&&`、`<utility>` | 转移资源不深拷贝 | 移动后源状态未指定 |
| `std::function` | 11 | `<functional>` | 类型擦除存可调用对象 | 堆分配 + 间接调用开销 |
| `constexpr` | 11/14 | 关键字 | 编译期可求值 | 11 限制极严，14 才放宽 |
| `enum class` / `std::thread` | 11 | `<cstdint>` / `<thread>` | 强类型枚举 / 标准线程库 | 不转 `int`；忘 join 会 `terminate` |
| 智能指针 | 11 | `<memory>` | RAII 内存管理 | `shared_ptr` 循环引用泄漏 |
| 泛型 lambda / `make_unique` | 14 | `auto` 参数 / `<memory>` | 模板化 `operator()` / 安全构造 | 不同实例不同类型；11 需手写 |
| `if constexpr` | 17 | 关键字 | 编译期分支 | 未命中分支语法仍需合法 |
| 结构化绑定 | 17 | 关键字 | 解包 tuple/pair | `auto` 是拷贝，改值用 `auto&` |
| `optional`/`variant`/`any` | 17 | 对应头文件 | 可能无值/多选一/任意 | `any` 有堆分配 |
| `filesystem` | 17 | `<filesystem>` | 路径与目录操作 | 老 GCC 要 `-lstdc++fs` |
| inline 变量 / CTAD | 17 | `inline` / 无 | 头文件定义变量 / 类模板推导 | 仍需注意 ODR；括号推导不同 |
| Concepts | 20 | `<concepts>` | 模板约束 | 老工具链实现滞后 |
| Ranges | 20 | `<ranges>` | 范围与视图 | 视图不拥有数据 |
| Coroutines / Modules | 20 | `co_await` / `import` | 协程 / 模块化编译 | 需 promise_type；构建支持不齐 |
| `<=>` | 20 | `<compare>` | 三路比较 | 默认实现要求成员可比较 |
| `constinit`/`consteval` | 20 | 关键字 | 静态初始化/强制编译期 | `constinit` 不等于 `const` |
| `std::format` | 20 | `<format>` | 类型安全格式化 | 旧标准可用 `fmt` 替代 |
### 1.3 工具链支持现状
| 工具链 | C++11 | C++14 | C++17 | C++20 | 说明 |
| --- | --- | --- | --- | --- | --- |
| GCC | 4.8+ 基本可用 | 5+ | 7+ 大部分 | 10~13 逐步补齐 | 模块支持较晚 |
| Clang | 3.3+ | 3.4+ | 5+ 大部分 | 12+ 逐步推进 | libc++ 与 libstdc++ 进度不同 |
| MSVC | VS2015 起 | VS2015/2017 | VS2017 15.7 起较完整 | VS2019 16.10+ 逐步 | `/std:c++17`、`/std:c++20` |
| Apple Clang | 完整 | 完整 | Xcode 11+ 可用 | 较新 Xcode 可用 | 跟随系统版本，注意默认 `-std` |

编译器版本与标准库版本要一起看：`-std=c++20` 下 `std::format` 能否使用取决于 libstdc++/libc++，**以编译器文档为准**；MSVC 的 `__cplusplus` 默认是 `199711L`（除非加 `/Zc:__cplusplus`），判断标准版本用 `<version>` 的 `__cpp_lib_*` 特性宏更可靠。服务端一般 17 起步、20 用于新模块（Concepts、`span`、`format`）；嵌入式/老项目锁 11/14 时用 `boost` 补 `make_unique`、`optional`，别混用「17 写法 + 11 标准」。探测写法：`#if defined(__cpp_lib_format)` 判断库特性，`#ifdef _MSC_VER` / `__clang__` / `__GNUC__` 判断编译器，再打印 `__cplusplus` 佐证。

## 2 编译与链接
「一个 `.cpp` 怎么变成进程」是第一道底层题。本章串四个阶段、前置声明、`inline` 与 ODR、链接错误排查、`extern "C"`。
### 2.1 四个阶段
| 阶段 | 选项 | 输入 → 输出 | 做什么 |
| --- | --- | --- | --- |
| 预处理 | `-E` | `.cpp` → `.ii` | 展开 `#include`/`#define`、条件编译 |
| 编译 | `-S` | `.ii` → `.s` | 语义分析、模板实例化、名称修饰，生成汇编 |
| 汇编 | `-c` | `.s` → `.o` | 可重定位目标文件（符号表 + 重定位表） |
| 链接 | 默认 | `.o` + 库 → 可执行文件 | 符号解析、重定位、合并段 |

```bash
g++ -std=c++17 -E main.cpp -o main.ii    # 预处理
g++ -std=c++17 -S main.ii -o main.s      # 编译
g++ -std=c++17 -c main.s -o main.o       # 汇编
g++ -std=c++17 main.o -o app             # 链接
g++ -std=c++17 -Wall -Wextra -O2 -g main.cpp -o app     # 一步到位
```

C++ 比 C 多了**名称修饰**、重载决议和模板实例化，这解释了「模板代码为什么写在头文件」：实例化发生在编译期，编译器必须看到完整定义；另一种解法是显式实例化（`template class Stack<int>;`）放进 `.cpp`。
### 2.2 前置声明与 inline/ODR
ODR 要求同一个类、内联函数、模板在程序中只有一份有效定义；`inline` 的**现代含义不是「内联展开」，而是「允许多个 TU 各有一份定义，链接器合并成一份」**。前置声明能在只需指针/引用时减少依赖，但 `sizeof`、基类、值成员、模板实参都需要完整类型。

| 写法 | 定义位置 | 多 TU 重复定义 | 是否一定展开 |
| --- | --- | --- | --- |
| 普通函数 | `.cpp` | 不允许，恰好一份 | 由编译器决定 |
| `inline` 函数 | 头文件 | 允许，链接器合并 | 不一定 |
| 类内定义的成员函数 | 头文件 | 隐式 inline | 由编译器决定 |
| `static` 全局函数 | `.cpp` | 每 TU 各一份（内部链接） | 否 |
| 模板 | 头文件 | 允许 | 否 |

```cpp
// node.h
#pragma once
struct Node;                       // 前置声明：只需指针时够用
class List {
public:
    ~List();                       // 声明，定义放 .cpp
    void push(int v);
private:
    Node* head_ = nullptr;         // 值成员才需要完整定义
};
// node.cpp
#include "node.h"
struct Node { int v; Node* next; };
List::~List() = default;
void List::push(int v) { head_ = new Node{v, head_}; }
// math_util.h：头文件里定义，必须 inline，否则多 TU 重定义
inline int twice(int x) { return x * 2; }
inline constexpr int kMax = 100;               // C++17：inline 变量
```

递归函数、取地址的函数、经 vptr 的虚调用通常无法内联。
### 2.3 undefined reference 排查
本质是**有声明、被调用，但链接器找不到定义**（MSVC 是 `LNK2019`）。

| 原因 | 排查 | 解决 |
| --- | --- | --- |
| 只声明未定义 | `nm -C x.o` 中该符号为 `U` | 补实现 |
| 模板定义写在 `.cpp` | 链接时报模板函数未定义 | 定义移入头文件或显式实例化 |
| 忘链接库 | 看链接命令行 | 加 `-lfoo` |
| 静态库顺序错 | 被依赖库放在前面 | 被依赖的放后面，或 `--start-group` |
| 名字修饰不匹配 | `nm` 看不到修饰名 | 用 `extern "C"` 或包含正确头文件 |
| ABI 不一致 | 同一符号两份实现 | 统一 `-D_GLIBCXX_USE_CXX11_ABI` |
| 纯虚/虚函数未实现 | vtable 中有未定义符号 | 补实现或改纯虚 |

```bash
g++ -c a.cpp b.cpp
nm -C a.o | grep my_func          # U=未定义，T=已定义代码，-C 反修饰
g++ a.o b.o -L. -lfoo -o app      # 顺序：先 .o，再依赖库
```

排查口诀：先看符号是否存在（`nm`），再看签名是否一致（名字修饰），最后看链接顺序与库路径（`-L`/`-l`）。
### 2.4 extern "C" 与编译期/运行期
C++ 会对函数名做修饰（`void f(int)` → `_Z1fi`），C 不做；跨语言调用必须 `extern "C"`。它只影响链接名、不改调用约定，不能用于重载函数、模板、成员函数；声明与实现的修饰方式必须一致。

```cpp
// c_api.h：可被 C 和 C++ 同时包含
#pragma once
#ifdef __cplusplus
extern "C" {
#endif
int c_add(int a, int b);
#ifdef __cplusplus
}
#endif
```

| 阶段 | 时机 | 典型例子 |
| --- | --- | --- |
| 编译期 | 编译时 | 模板实例化、`constexpr`/`consteval`、`static_assert` |
| 链接期 | 链接时 | 符号解析、弱符号合并 |
| 装载期 | 启动前 | 全局/静态对象初始化、动态库重定位 |
| 运行期 | 执行时 | 虚函数派发、`new/delete`、异常 |

`constexpr` 函数「可以」编译期求值（取决于实参），`consteval`「必须」编译期求值，`constinit` 只保证静态初始化。

```cpp
#include <cstdio>
constexpr int fib(int n) { return n < 2 ? n : fib(n - 1) + fib(n - 2); }
static_assert(fib(10) == 55, "compile-time check");   // 编译期
constexpr int kTable[3] = {fib(1), fib(2), fib(3)};   // 进入只读段
int main() { std::printf("%d\n", kTable[2]); }
```

## 3 对象模型与内存布局
「空类多大」「虚函数怎么实现」「多继承指针为何不同」是底层面试必考区，本章内容都能用 `sizeof` 与 gdb 验证。
### 3.1 类的大小、对齐与 static 成员
空类 `sizeof` 为 1 是为了**每个对象有唯一地址**；成员函数在代码段、不占对象空间，对象里只有数据成员和 vptr；`static` 成员变量本质是全局变量，放 `.data`/`.bss`，所有对象共享（C++17 可用 `inline static` 类内定义）。类大小 = 数据成员按对齐规则排布 + 可能的 vptr，再补齐到最大对齐数的倍数：成员偏移是自身对齐的倍数（`char` 后接 `int` 有 3 字节填充），总大小是最大对齐数的倍数（保证数组元素对齐），虚基类另有虚基表开销。

```cpp
#include <iostream>
struct A { char c; int i; };                  // 1 + 3 填充 + 4 = 8
struct B { char c; double d; };               // 16
struct Empty {};                              // 1
struct D : Empty { int i; };                  // 空基类优化：4
struct V { virtual void f() {} int x; };      // vptr + int + 填充 = 16
struct Counter {
    void inc() { ++counter; }                  // 普通成员函数不占对象空间
    static int s_total;                        // 存放于数据段，所有对象共享
    int counter = 0;                           // 唯一的数据成员
};
int Counter::s_total = 0;
int main() {
    std::cout << sizeof(A) << sizeof(B) << sizeof(Empty) << sizeof(D) << sizeof(V)
              << sizeof(Counter) << sizeof(Counter::s_total);   // 8 16 1 4 16 4 4
}
```

调整成员顺序（小类型聚拢、`double`/指针聚拢）常能把 24 缩到 16；`#pragma pack(1)` 可去填充，但非对齐访问在 ARM 上可能 fault，只用于协议解析且应显式序列化。
### 3.2 vtable 与 vptr
有虚函数的类各有一张**虚函数表 vtable**（只读数据段，存函数指针），每个对象有一个隐藏 **vptr** 指向它；虚调用 = 经 vptr 找表、按槽位间接调用。Itanium ABI（GCC/Clang）中对象首地址是 vptr，vtable 前两槽是 `offset-to-top` 与 `typeinfo`，之后才是用户虚函数。

```cpp
#include <iostream>
struct Base {
    virtual void foo() { std::cout << "Base::foo\n"; }
    virtual ~Base() = default;
};
struct Derived : Base {
    void foo() override { std::cout << "Derived::foo\n"; }   // 覆盖槽位 0
};
int main() {
    std::cout << sizeof(Base) << '\n';   // 8（64 位），只有 vptr
    Derived d;
    Base* p = &d;
    p->foo();                            // 经 vptr 调到 Derived::foo
}
```

1. 虚调用多一次间接寻址且难内联，只在热路径上才成为瓶颈。
2. **析构必须是虚的**：`delete Base*` 指向派生对象时，非虚析构只调基类析构（UB + 泄漏）。
3. 构造/析构期间调用虚函数不会多态——vptr 仍指向当前构造阶段的类。
4. 调试时用 `g++ -g -O0 -fno-omit-frame-pointer demo.cpp -o demo && gdb ./demo`，再执行 `set print object on`（按动态类型显示）、`info vtbl *p`（虚表槽位）、`x/4gx &d`（对象首部 vptr + 成员），详见 12.2 节。
### 3.3 多继承、虚继承与 this
多继承按声明顺序嵌入基类子对象，**只有第一个基类与派生对象首地址相同**，后续偏移非 0，派生 → 非首基类指针会自动加减偏移。菱形继承用 `virtual` 继承让公共基类只存一份，代价是访问要经间接寻址，且虚基类偏移不固定、只能 `dynamic_cast` 回派生类。`this` 是隐式传入的非静态成员函数参数，`const` 成员函数里类型是 `const 类名*`；多继承时它的值可能被调整。

```cpp
struct A { virtual ~A() = default; int a = 1; };
struct B { virtual ~B() = default; int b = 2; };
struct C : A, B { int c = 3; };
struct X { virtual ~X() = default; int x = 0; };
struct Y : virtual X { int y = 1; };
struct Z : virtual X { int z = 2; };
struct Diamond : Y, Z { int d = 3; };
#include <cstddef>
ptrdiff_t offset_of(void* base, void* sub) {
    return static_cast<char*>(sub) - static_cast<char*>(base);   // 先转字节指针再相减
}
int main() {
    C obj;
    B* pb = &obj;
    Diamond dia;
    dia.x = 100;                                                // 只有一份 X，不二义
    X* px = static_cast<Y*>(&dia);
    return static_cast<int>(offset_of(&obj, pb) + sizeof(C) + dia.x + dia.Y::x
                            + (dynamic_cast<Diamond*>(px) == &dia));
}
```

多继承下派生类可能有多张 vtable（每个多态基类一张），this 指针由「调整块」（thunk）修正；构造顺序是虚基类 → 普通基类（按声明序）→ 成员 → 构造体，且**最派生类负责构造虚基类**。`(S*)nullptr->set(1)` 是 UB；`delete this` 允许（自删除对象），前提是之后不再访问成员。`this` 也可用于「成员与参数同名」的区分（`this->v = v;`）和链式调用（`S& chain(int x) { v += x; return *this; }`，之后可写 `s.chain(1).chain(2)`）。

## 4 构造与析构
对象生命周期是 C++ 与 C 最大的不同：出生就构造、死亡就析构。本章讲特殊成员函数、三/五/零法则、`explicit`、初始化顺序陷阱与 RAII。
### 4.1 特殊成员函数与三/五/零法则
| 成员函数 | 默认行为 | 何时不再自动生成 |
| --- | --- | --- |
| 默认构造 | 不初始化内置类型成员 | 声明了其他构造函数 |
| 拷贝构造 / 拷贝赋值 | 逐成员拷贝/赋值 | 声明了移动构造/移动赋值 |
| 移动构造 / 移动赋值 | 逐成员移动 | 声明了拷贝构造/拷贝赋值/析构 |
| 析构 | 空体 | 总会被生成（除非 `= delete`） |

| 法则 | 内容 | 适用 |
| --- | --- | --- |
| 三法则 | 析构、拷贝构造、拷贝赋值要么都写要么都不写 | C++98 管裸资源 |
| 五法则 | 再加上移动构造、移动赋值 | 手写资源管理 |
| **零法则** | 不手写任何特殊成员，全用 RAII 成员 | **现代 C++ 首选** |

```cpp
#include <algorithm>
#include <utility>
class Buffer {
public:
    explicit Buffer(std::size_t n) : data_(new int[n]()), size_(n) {}
    ~Buffer() { delete[] data_; }
    Buffer(const Buffer& o) : data_(new int[o.size_]), size_(o.size_) {   // 深拷贝
        std::copy(o.data_, o.data_ + size_, data_);
    }
    Buffer& operator=(const Buffer& o) {
        if (this != &o) { Buffer tmp(o); swap(tmp); }     // 拷贝-交换：强异常安全
        return *this;
    }
    Buffer(Buffer&& o) noexcept : data_(std::exchange(o.data_, nullptr)),
                                  size_(std::exchange(o.size_, 0)) {}
    Buffer& operator=(Buffer&& o) noexcept {             // 移动赋值：先释放再接管
        if (this != &o) { delete[] data_; data_ = o.data_; size_ = o.size_; o.data_ = nullptr; o.size_ = 0; }
        return *this;
    }
    void swap(Buffer& o) noexcept { std::swap(data_, o.data_); std::swap(size_, o.size_); }
    std::size_t size() const { return size_; }
private:
    int* data_ = nullptr;
    std::size_t size_ = 0;
};
int main() {
    Buffer a(4), b = a, c = std::move(a);   // 拷贝构造、移动构造
    b = c;                                   // 拷贝赋值
    (void)a;
    return static_cast<int>(a.size() + b.size() + c.size());   // 0 + 4 + 4
}
```

成员 `swap(tmp)` 交换的是成员，`std::swap` 交换整个对象，别混用。
### 4.2 explicit、委托/继承构造与初始化顺序
单参数构造函数、`initializer_list` 构造函数、转换运算符都该考虑加 `explicit`：函数实参被静默转换是最常见的坑。成员按**声明顺序**初始化，与初始化列表书写顺序无关；基类先于成员；`static` 成员不参与。顺序写错编译器只给警告不报错（`-Wreorder-ctor`）。委托构造不能成环，且初始化列表只能出现在被委托的那个构造函数里。

```cpp
struct Meter {
    explicit Meter(double v) : v_(v) {}        // 禁止隐式转换
    double v_;
};
struct Point {
    Point() : Point(0, 0) {}                   // 委托构造
    Point(int x) : Point(x, 0) {}
    Point(int x, int y) : x_(x), y_(y) {}
    int x_, y_;
};
struct Derived : Meter {
    using Meter::Meter;                        // 继承构造（C++11）
};
struct Bug {
    int a;
    int b;
    Bug(int v) : b(v), a(b * 2) {}             // a 先初始化，读未初始化的 b 即 UB
};
int main() {
    // Meter m = 3.0;                          // 编译错误：explicit
    Point p(1);
    Derived d(2.0);
    Bug bad(5);
    return p.x_ + static_cast<int>(d.v_) + bad.b;
}
```

另需区分：`T x;` 对内置类型不初始化，`T x{};` 零初始化；基类没有默认构造时必须在初始化列表里显式构造。
### 4.3 RAII 与 = default/= delete
RAII（Resource Acquisition Is Initialization）：构造获取、析构释放，靠栈展开保证异常路径也释放。文件、锁、智能指针、socket、事务——凡是「成对出现的获取/释放」都该封装成 RAII 类型。`= default` 让编译器生成默认实现（可能保留平凡属性），`= delete` 显式禁用某个函数；手写空析构会让类型不再是平凡类型，可能阻止优化。

```cpp
#include <cstdio>
#include <stdexcept>
class FileHandle {
public:
    explicit FileHandle(const char* p) : fp_(std::fopen(p, "w")) {
        if (!fp_) throw std::runtime_error("open failed");
    }
    ~FileHandle() { if (fp_) std::fclose(fp_); }
    FileHandle(const FileHandle&) = delete;                // 不可拷贝
    std::FILE* get() const { return fp_; }
private:
    std::FILE* fp_;
};
struct OnlyInt {
    void f(int) {}
    void f(double) = delete;              // 防止 f(1.5) 静默转 int
};
int main() {
    FileHandle f("out.txt");              // 作用域结束自动 fclose，异常路径也一样
    OnlyInt o;
    o.f(1);
    // o.f(1.5);                          // 编译错误：选中被 delete 的版本
    return f.get() ? 0 : 1;
}
```

## 5 移动语义与完美转发
移动语义是 C++11 最重要的特性，也是「背得出、写不对」的重灾区。本章讲值类别、`std::move` 真身、RVO、`std::forward` 与万能引用陷阱。
### 5.1 值类别与 std::move
| 值类别 | 特征 | 例子 |
| --- | --- | --- |
| 左值 lvalue | 有名字、可取址 | 变量 `x`、`*p`、`a[i]`、`s.m` |
| 纯右值 prvalue | 临时值、没名字 | `42`、`x + 1`、`T{}`、`f()` 返回值 |
| 将亡值 xvalue | 有地址但可被搬走 | `std::move(x)`、`static_cast<T&&>(x)` |

`std::move` 只是 `static_cast<std::remove_reference_t<T>&&>(t)`，**不搬任何字节**，只把表达式类型换成右值；真正搬运发生在移动构造/移动赋值里。移动后对象仍可析构、可赋新值，但内容未指定；对 `const T` 用 `std::move` 得到 `const T&&`，退化成拷贝。「按值传参 + `std::move`」是推荐写法：左实参拷一次、右实参移一次。`noexcept` 很关键——`vector` 扩容时只有移动构造 `noexcept` 才用移动，否则为强异常安全退化为拷贝。

```cpp
#include <string>
#include <utility>
#include <vector>
class Message {
public:
    Message(std::string text, std::vector<int> ids)
        : text_(std::move(text)), ids_(std::move(ids)) {}          // 按值传参 + move
    Message(const Message&) = default;
    Message(Message&& o) noexcept : text_(std::move(o.text_)), ids_(std::move(o.ids_)) {}
    std::size_t ids() const { return ids_.size(); }
private:
    std::string text_;
    std::vector<int> ids_;
};
int tag(const std::string&) { return 0; }      // 左值版本
int tag(std::string&&) { return 1; }           // 右值版本
int main() {
    std::vector<Message> v;
    v.reserve(2);
    v.emplace_back("hello", std::vector<int>{1, 2, 3});
    Message m("world", {4, 5});
    v.push_back(std::move(m));           // 移动进容器，m 之后不应再读
    std::string s = "abc";
    const std::string cs = "x";
    return tag(s) * 10 + tag(std::move(s)) * 10 + tag(std::move(cs))   // const 右值退化为左值
         + static_cast<int>(v[0].ids() + v[1].ids());
}
```
### 5.2 返回值优化 RVO/NRVO
编译器在调用者存储区直接构造返回值。C++17 起返回纯右值的省略是**强制的**；返回具名局部变量（NRVO）是可选优化，主流编译器 `-O1` 以上都会做。**不要写 `return std::move(local);`**——它阻止 NRVO 反而多一次移动（`-Wpessimizing-move`）。验证方法：给类型加计数用的拷贝构造和移动构造（`Tracked(const Tracked&) { ++copies; }` / `Tracked(Tracked&&) noexcept { ++moves; }`），令 `Tracked make_prvalue() { return Tracked{}; }`、`Tracked make_named() { Tracked t; return t; }`，`Tracked a = make_prvalue(); Tracked b = make_named();` 通常 `copies == moves == 0`，只有显式 `Tracked c = std::move(b);` 才让 `moves == 1`。
### 5.3 引用折叠与 std::forward
| 展开前 | 折叠后 |
| --- | --- |
| `T& &`、`T& &&`、`T&& &` | `T&` |
| `T&& &&` | `T&&` |

万能引用只有一种形式：`T&&` 且 `T` 需要推导（模板参数、`auto&&`）。传左值时 `T` 推导为 `T&`，折叠后仍是 `T&`；传右值时是 `T&&`。`std::forward<T>(v)` 同为 `static_cast`：`T` 是左值引用类型转 `T&`，否则转 `T&&`。转发函数里若只写 `sink(v)`，`v` 本身是左值，永远选中左值版本——这就是必须配 `std::forward` 的原因。

```cpp
#include <utility>
int sink(int&) { return 0; }                   // 左值
int sink(int&&) { return 1; }                  // 右值
template <typename T>
int forward_to_sink(T&& v) {                   // T&& 是万能引用
    return sink(std::forward<T>(v));           // 保持原值类别
}
int main() {
    int x = 1;
    return forward_to_sink(x) * 10 + forward_to_sink(2);   // 0*10 + 1
}
```
### 5.4 万能引用与重载冲突
万能引用几乎匹配一切，会**劫持**类的拷贝构造：写了 `template <typename T> Wrapper(T&&)` 后，拷贝非 `const` 的 `Wrapper` 时 `T` 推导为 `Wrapper&`，模板实例比 `Wrapper(const Wrapper&)` 更精确。

```cpp
#include <string>
#include <type_traits>
#include <utility>
struct Safe {                                  // 正确写法：限制实参不是自身
    std::string s;
    Safe() = default;
    Safe(const Safe&) = default;
    Safe(Safe&&) = default;
    template <typename T,
              typename = std::enable_if_t<!std::is_same_v<std::decay_t<T>, Safe>>>
    explicit Safe(T&& v) : s(std::forward<T>(v)) {}
};
int main() {
    Safe s1(std::string("hi"));       // 走模板
    Safe s2(s1);                      // 拷贝构造，不再被抢
    // 反过来：若把模板写成 template <typename T> Safe(T&&)，s2(s1) 会被
    // 实例化成 Safe(Safe&) 并优先于拷贝构造——这就是「万能引用劫持」。
    return static_cast<int>(s1.s.size() + s2.s.size());
}
```

C++20 可写 `requires (!std::same_as<std::remove_cvref_t<T>, Safe>)`，比 `enable_if` 直白得多。
### 5.5 移动语义的适用边界
| 场景 | 是否真移动 | 说明 |
| --- | --- | --- |
| `string`/`vector`（非 SSO） | 是 | 只搬指针和大小，O(1) |
| 小字符串（SSO）/ `std::array<int,10>` | 否 | 数据在对象内部，逐元素拷贝 |
| 自定义类型无移动构造 / `const` 对象 | 否 | 退化为拷贝 |
| 按值传参后 `std::move` 进成员 | 是 | 推荐写法 |

## 6 智能指针
裸 `new`/`delete` 是内存泄漏与悬垂指针的主要来源；智能指针用 RAII 把释放绑定到析构上。
### 6.1 unique_ptr 与自定义删除器
`unique_ptr` 独占所有权，不可拷贝只能移动；大小是「指针 + 删除器」，无状态删除器经空基类优化后通常就是 8 字节。有状态 lambda 删除器会让它变大，且类型是唯一匿名类型，不能与其他 `unique_ptr` 混放。

```cpp
#include <cstdio>
#include <memory>
struct FcloseDeleter { void operator()(std::FILE* f) const noexcept { std::fclose(f); } };
int main() {
    auto p = std::make_unique<int>(42);
    auto r = std::move(p);                                // 转移所有权，p 变 nullptr
    p.reset();                                            // 空指针上 reset 无副作用
    std::unique_ptr<std::FILE, FcloseDeleter> f(std::fopen("a.txt", "w"));   // 自定义删除器
    if (f) std::fputs("hi", f.get());                     // get() 把裸指针交给 C 接口
    return (r == nullptr) + static_cast<int>(sizeof(f));  // 0 + 8
}
```
### 6.2 shared_ptr：控制块、循环引用与线程安全
| 构件 | 位置 | 内容 |
| --- | --- | --- |
| 对象 | 堆（`make_shared` 时与控制块同块） | 真正的 `T` |
| 控制块 | 堆 | strong/weak count、deleter、allocator |
| `shared_ptr` 本体 | 栈/成员 | 对象指针 + 控制块指针（16 字节） |

强计数归零销毁对象，强弱计数都归零才释放控制块。互持 `shared_ptr` 时计数永不归零，把一侧改成 `weak_ptr`（只观察不拥有）即可打破；访问 `weak_ptr` 必须先 `lock()`，先 `expired()` 再访问有竞态。`make_shared` 只分配一次、更快且异常安全，但只要还有 `weak_ptr` 存活整块内存都不能释放。`shared_ptr` **只保证引用计数增减原子，不保证所指对象线程安全**：不同实例（副本）并发拷贝/析构安全；同一实例并发赋值不安全，需加锁或用 `std::atomic_load/atomic_store`（C++20 起可考虑 `std::atomic<std::shared_ptr<T>>`，**以标准库文档为准**）。

```cpp
#include <atomic>
#include <memory>
#include <string>
#include <thread>
struct Node {
    std::string name;
    std::shared_ptr<Node> next;        // 强引用
    std::weak_ptr<Node> prev;          // 弱引用，打破环
    explicit Node(std::string n) : name(std::move(n)) {}
};
std::shared_ptr<int> g_config = std::make_shared<int>(0);
int main() {
    auto a = std::make_shared<Node>("A");
    auto b = std::make_shared<Node>("B");
    a->next = b;
    b->prev = a;                       // weak：不影响 a 的计数
    std::thread writer([] {
        std::atomic_store(&g_config, std::make_shared<int>(42));   // 「不可变对象 + 原子替换指针」
    });
    writer.join();
    return static_cast<int>(a.use_count()) + (b->prev.lock() ? 1 : 0);
}
```
### 6.3 所有权对比与常见误用
| 类型 | 所有权 | 可拷贝 | 大小（64 位） | 适用 |
| --- | --- | --- | --- | --- |
| `T*` / `T&` | 无 | 是 | 8 | 函数参数、观察型引用 |
| `unique_ptr<T>` | 独占 | 否（可移动） | 8 | **默认首选**，工厂、pImpl |
| `shared_ptr<T>` | 共享 | 是 | 16 | 确实共享所有权、异步回调 |
| `weak_ptr<T>` | 无（观察） | 是 | 16 | 打破环、缓存、观察者 |
| `reference_wrapper<T>` | 无 | 是 | 8 | 容器里存引用 |

选择顺序：**栈/值 → `unique_ptr` → 确实共享才 `shared_ptr` → 防环用 `weak_ptr`**；函数参数优先 `const T&` 或 `T*`，别为方便传 `shared_ptr`。常见误用：循环引用；`shared_ptr<T>(this)` 新建控制块导致 double free（应用 `enable_shared_from_this`）；基类无虚析构；用同一个裸指针构造两个 `shared_ptr`。

## 7 模板进阶
模板是泛型的地基。本章从函数/类模板讲到可变参数、SFINAE 与 Concepts，最后落在代码膨胀上。
### 7.1 函数模板、类模板与特化
模板不是代码而是「图纸」，用具体实参实例化才生成代码。**全特化**给一组具体实参单独实现，**偏特化**给部分实参做特殊处理（函数模板不支持偏特化，只能重载）。定义必须对实例化点可见（所以写在头文件），特化必须出现在第一次使用之前。

```cpp
#include <string>
#include <vector>
template <typename T>
T max_of(const T& a, const T& b) { return a < b ? b : a; }      // 函数模板
template <typename T>
class Stack {                                                   // 类模板
public:
    void push(const T& v) { data_.push_back(v); }
    T pop() { T v = data_.back(); data_.pop_back(); return v; }
private:
    std::vector<T> data_;
};
template <typename T>
struct Printer { static int show(const T&) { return 0; } };                       // 主模板
template <>
struct Printer<bool> { static int show(const bool&) { return 1; } };             // 全特化
template <typename T>
struct Printer<T*> { static int show(T* const& v) { return v ? 2 : 3; } };       // 偏特化：所有指针
int main() {
    Stack<int> s;
    s.push(2);
    int x = 7;
    return max_of(3, 7) + s.pop() + Printer<bool>::show(true) + Printer<int*>::show(&x);   // 7+2+1+2
}
```
### 7.2 可变参数模板与折叠表达式
`typename... Ts` 是模板参数包，`sizeof...(Ts)` 求个数；消费参数包靠 C++17 **折叠表达式**，四种形式：`(args + ...)`、`(... + args)`、`(init + ... + args)`、`(args + ... + init)`。注意空包：`(... + args)` 对空包是编译错误，`(0 + ... + args)` 才有默认值。

```cpp
#include <cstddef>
template <typename... Ts>
auto sum_all(Ts... args) { return (0 + ... + args); }   // 二元左折叠，空包也有初值
template <typename... Ts>
std::size_t count_args(Ts&&...) { return sizeof...(Ts); }
int main() {
    return sum_all(1, 2, 3, 4, 5) + static_cast<int>(count_args(1, "a", 2.0)) + sum_all();   // 15+3+0
}
```
### 7.3 SFINAE / enable_if 与 Concepts
SFINAE（Substitution Failure Is Not An Error）：模板实参替换失败时该候选只是不参与重载决议，而不是编译错误；`enable_if`、`void_t` 就借这一点删候选。旧式痛点：报错动辄几百行，多个约束叠加难读，`enable_if` 要在每个重载里重复。

```cpp
#include <string>
#include <type_traits>
template <typename T, typename std::enable_if<std::is_integral_v<T>, int>::type = 0>
int label(T) { return 0; }                                   // 只对整型启用
template <typename T, typename std::enable_if<std::is_floating_point_v<T>, int>::type = 0>
int label(T) { return 1; }
template <typename T>
using HasSize = decltype(std::declval<T>().size());          // void_t 检测成员是否存在
template <typename T, typename = void>
struct has_size : std::false_type {};
template <typename T>
struct has_size<T, std::void_t<HasSize<T>>> : std::true_type {};
int main() {
    return label(1) * 10 + label(1.5) + has_size<std::string>::value + has_size<int>::value;   // 0*10+1+1+0
}
```

```cpp
#include <concepts>
#include <string>
template <typename T>
concept Addable = requires(T a, T b) { { a + b } -> std::convertible_to<T>; };
template <Addable T>
T add(const T& a, const T& b) { return a + b; }        // 简写约束
template <typename T>
    requires requires(const T& t) { t.size(); }         // requires 子句 + 内联需求
std::size_t len(const T& t) { return t.size(); }
int main() {
    return static_cast<int>(add(1, 2) + len(std::string("xyz")));   // 3 + 3
    // add(1, std::string("x"));   // 编译错误：T 不满足 Addable，报错直接点名
}
```

| 维度 | SFINAE / `enable_if` | Concepts |
| --- | --- | --- |
| 可读性 | 声明里嵌 `enable_if` | `concept` 名字自解释 |
| 报错 | 「替换失败」，几百行模板 | 「T does not satisfy Addable」 |
| 约束组合 | 逻辑运算符堆叠 | `concept X = A && B`、`requires` 子句 |
| 重载决议 | 依赖 SFINAE 退让 | 约束更特殊的版本优先 |
| 标准 | C++11/14/17 | C++20 |

C++20 还能写 `void f(std::integral auto x);`；C++17 项目继续用 `enable_if` + `void_t`，但把约束封装成命名 trait 能缩小可读性差距。
### 7.4 CRTP 与代码膨胀
CRTP（奇异递归模板模式）= 派生类把自身作为模板实参传给基类（`struct Point : Comparable<Point>`），基类里用 `static_cast<Derived*>(this)` 调派生类函数，从而在**编译期**实现多态，零虚表开销；典型用法是给 `Point` 自动获得 `operator!=`、`Clone()`、计数器。每个实参都生成一份独立代码，二进制和编译时间都会膨胀：类型参数多（`vector<int>`/`<double>` 各一份）时内部抽非模板实现；非类型参数多（`template <int N> FixedArray`）时改为运行时构造参数；多 TU 重复实例化时，在头文件写正常定义 + `extern template`，再在 `.cpp` 里显式实例化一次（`template void sort_impl<int>(int*, int);`）。

模板实例化能占掉大型项目一半以上编译时间，`-ftime-trace`（clang）、`-ftime-report`（gcc）可定位热点。

## 8 异常与错误处理
异常是 C++ 里唯一能跨函数、跨层传递错误、同时保证栈对象被正确析构的机制。
### 8.1 try/catch/throw 与栈展开
抛出的是对象**副本**，按引用捕获、从具体到一般、最后 `catch (...)` 兜底；`catch (Base)` 写在 `catch (Derived)` 前会让后者永远进不去。标准异常以 `std::exception` 为根，分 `logic_error`（编码可避免）与 `runtime_error`（运行时才发现）两支。沿栈向上寻找 `catch` 时会逐层退出作用域并调用局部对象析构，这叫**栈展开**——也是 RAII 在异常路径上正确释放资源的原因。

```cpp
#include <iostream>
#include <stdexcept>
#include <vector>
struct Guard {
    const char* name;
    explicit Guard(const char* n) : name(n) { std::cout << "enter " << name << '\n'; }
    ~Guard() { std::cout << "leave " << name << '\n'; }   // 异常路径也会执行
};
void level2() { Guard g("level2"); throw std::runtime_error("boom"); }
int main() {
    try {
        Guard g("level1");
        level2();
    } catch (const std::exception& e) {                    // 兜底
        std::cout << "std: " << e.what() << '\n';
    }
}
```

输出 `enter level1` → `enter level2` → `leave level2` → `leave level1` → `std: boom`。这解释了为何「裸 `new`」在异常下必然泄漏，而 `unique_ptr`/`vector` 不会。
### 8.2 noexcept 与异常安全三等级
`noexcept` 承诺不抛异常，会直接影响标准库行为：`vector` 扩容时只有移动构造 `noexcept` 才会用移动，否则为强异常安全退化为拷贝。移动构造、移动赋值、`swap`、析构都应 `noexcept`；一旦声明，内部抛出就 `std::terminate`，所以只给确实不会失败的函数加。

```cpp
#include <type_traits>
#include <utility>
#include <vector>
struct NoThrow { NoThrow() = default; NoThrow(NoThrow&&) noexcept {} NoThrow(const NoThrow&) {} };
struct Throw { Throw() = default; Throw(Throw&&) {} Throw(const Throw&) {} };
int main() {
    std::vector<NoThrow> v1;
    v1.reserve(1);                 // 扩容时用移动构造（noexcept）
    v1.push_back(NoThrow{});
    std::vector<Throw> v2;
    v2.reserve(1);                 // 扩容时退化为拷贝构造（移动可能抛）
    v2.push_back(Throw{});
    return std::is_nothrow_move_constructible_v<NoThrow> * 10
         + std::is_nothrow_move_constructible_v<Throw>;     // 10，即 1 和 0
}
```

| 等级 | 保证 | 例子 |
| --- | --- | --- |
| 基本保证 | 不泄漏、不破坏不变量，对象仍可析构 | 大多数 `push_back` 内存不足时 |
| 强保证 | 失败时回滚到调用前状态 | 拷贝交换赋值、`vector::reserve` |
| 不抛保证 | 承诺不抛（`noexcept`） | 移动构造、`swap`、`int` 运算 |

强保证的标准手法是 copy-and-swap：在临时对象上完成所有可能失败的操作，最后用不抛的 `swap` 提交。
### 8.3 异常 vs 错误码 vs optional/expected
| 方案 | 传播成本 | 错误可否忽略 | 适用 | 头文件 |
| --- | --- | --- | --- | --- |
| 异常 | 不抛时零成本，抛出时慢 | 不能 | 罕见、真正异常的错误 | `<stdexcept>` |
| 错误码 | 无 | 容易忽略 | C 接口、热路径、嵌入式 | 自定义 |
| `std::optional<T>` | 无 | 表示「可能没有值」，无原因 | 查找/解析的成败 | `<optional>` |
| `std::expected<T,E>`（23） | 无 | 可携带错误原因 | 不想用异常 | `<expected>` |

真正的编程错误（越界、空指针解引用）不要用异常掩盖；`-fno-exceptions` 环境（嵌入式/部分游戏）只能用错误码/`optional`；`std::expected` 是 C++23，C++17 可用 `tl::expected` 一类实现，**可用性以标准库为准**。用法：`std::optional<int> to_int(const std::string& s)` 内部 `try { return std::stoi(s); } catch (...) { return std::nullopt; }`，调用侧写 `to_int("abc").value_or(1)`。
### 8.4 析构不能抛异常、自定义异常
析构发生在栈展开途中，此时再抛异常会 `std::terminate`（不允许两个异常同时传播）。所以析构里不要抛；必须失败的操作（`fclose`、`commit`）提供显式 `close()`/`flush()`，析构只做「尽力而为 + 吞掉或记录」。自定义异常继承 `std::runtime_error` 以保留 `what()`，成员用 `std::string` 保证拷贝不抛，类型应能区分类别而非一个 `Error` 加字符串。

```cpp
#include <stdexcept>
#include <string>
class DbError : public std::runtime_error {                 // 自定义异常
public:
    enum class Code { Timeout, ConnectionLost };
    DbError(Code c, const std::string& msg) : std::runtime_error(msg), code_(c) {}
    Code code() const noexcept { return code_; }
private:
    Code code_;
};
struct SafeDtor {
    ~SafeDtor() noexcept {
        try { throw std::runtime_error("ignored"); }        // 被内部 catch，不逃出析构
        catch (const std::exception&) { /* 记录日志 */ }
    }
};
int main() {
    try {
        SafeDtor s;
        throw DbError(DbError::Code::Timeout, "db timeout");
    } catch (const DbError& e) {
        return static_cast<int>(e.code()) + static_cast<int>(std::string(e.what()).size());
    } catch (const std::exception&) {
        return -1;
    }
}
```

## 9 并发
C++11 起有了标准线程库。面试常问 `lock_guard` 与 `unique_lock` 的区别、`atomic` 与内存序、条件变量为何配锁、线程池怎么写、与 pthread 的差别。
### 9.1 thread、锁与 condition_variable
每个 `std::thread` 析构前必须 `join()` 或 `detach()`，否则 `std::terminate`；线程函数未捕获的异常也会 `terminate`；`detach` 后访问已销毁对象是 UB。多把锁用 `std::scoped_lock` 原子地同时获取，避免 AB-BA 死锁。

| 类型 | 自动加解锁 | 可手动解锁/移动 | 适用 |
| --- | --- | --- | --- |
| `lock_guard` | 构造加、析构解 | 否 | 最简单的作用域锁 |
| `unique_lock` / `scoped_lock` | 可延迟加锁 / 一次锁多个 | 是 / 否 | 配条件变量 / 防 AB-BA 死锁 |

条件变量用来「线程等待某条件成立」。规范写法：`unique_lock` + 谓词版 `wait`（防虚假唤醒）+ 改条件时持锁 + 先改条件后 `notify`；无谓词的 `cv.wait(lk)` 可能虚假唤醒，必须配 `while` 判断；条件变量必须与**同一把** mutex 配合，否则丢失唤醒（lost wakeup）。

```cpp
#include <condition_variable>
#include <mutex>
#include <queue>
#include <thread>
std::mutex m;
std::condition_variable cv;
std::queue<int> q;
bool finished = false;
void worker() {
    for (;;) {
        std::unique_lock<std::mutex> lk(m);
        cv.wait(lk, [] { return !q.empty() || finished; });   // 谓词版防虚假唤醒
        if (q.empty() && finished) return;
        q.pop();
        lk.unlock();                                          // 处理时不必持锁
    }
}
int main() {
    std::thread t(worker), t2(worker);                        // 不 join 就析构 → terminate
    for (int i = 1; i <= 3; ++i) {
        { std::lock_guard<std::mutex> lk(m); q.push(i); }     // 作用域锁
        cv.notify_one();                                      // 先改条件、后通知
    }
    { std::lock_guard<std::mutex> lk(m); finished = true; }
    cv.notify_all();                                          // 两个 worker 都要能退出
    t.join();
    t2.join();
    return 0;
}
```
### 9.2 atomic 与内存序
`std::atomic<T>` 保证对该对象的读写原子且不撕裂，但不代表整体线程安全。默认 `seq_cst` 最严格；`release`/`acquire` 用于发布-订阅。`atomic` 只保护自身读写，**多步复合操作**要用 `compare_exchange_weak` 循环或加锁；`atomic<bool>` 只能做「就绪标志」。拿不准时用默认 `seq_cst`。

| 内存序 | 语义 | 典型用途 |
| --- | --- | --- |
| `seq_cst` | 全局单一全序，最严格 | 默认，简单正确 |
| `acquire` | 之后的读写不能重排到它之前 | 读方加载 |
| `release` | 之前的读写不能重排到它之后 | 写方存储 |
| `acq_rel` | 同时具备两种约束 | 读改写操作 |
| `relaxed` | 只保证原子性与修改顺序一致 | 计数器 |

```cpp
#include <atomic>
#include <thread>
int main() {
    std::atomic<int> count{0};
    int payload = 0;
    std::atomic<bool> ready{false};
    std::thread producer([&] {
        for (int k = 0; k < 1000; ++k) count.fetch_add(1);   // relaxed 计数器
        payload = 42;
        ready.store(true, std::memory_order_release);        // 之前的写对 consumer 可见
    });
    std::thread consumer([&] {
        while (!ready.load(std::memory_order_acquire)) { }    // 之后的读不能提到前面
        if (payload != 42) count.store(-1);                   // 一定读到 42
    });
    producer.join();
    consumer.join();
    return count.load();                                     // 1000
}
```
### 9.3 async / future / promise
| 设施 | 作用 | 特点 |
| --- | --- | --- |
| `std::async` | 异步执行可调用对象，返回 future | 默认策略可能是 deferred |
| `std::future` | 等待/获取结果 | 只能 `get` 一次 |
| `std::promise` | 手动设置结果 | 线程间传值 |
| `std::packaged_task` | 包装可调用对象为任务 | 可放进线程池队列 |

`std::async` 的坑：不指定 `std::launch::async` 时实现可能选 `deferred`，任务直到 `get()`/`wait()` 才在当前线程执行；返回的 future 析构时会阻塞等待任务完成；任务抛异常时 `get()` 会重新抛出。典型用法：`auto f = std::async(std::launch::async, [] { return compute(); });` 再用 `f.get()` 取结果；`std::promise<int> p` 配 `p.get_future()`，在别的线程里 `p.set_value(1)` 即可跨线程传值。
### 9.4 线程池思路
线程池 = 固定 worker + 任务队列 + 条件变量；任务用 `std::function<void()>` 类型擦除，结果用 `packaged_task` + `future` 取回。面试点：任务为何在锁外执行（避免任务里再加锁导致死锁/串行化）、析构如何不丢任务（`stop_` + `notify_all` + `join`，或先排空队列）、任务抛异常怎么办（`packaged_task` 把异常存进 future，`get()` 时重抛）。

```cpp
#include <condition_variable>
#include <functional>
#include <future>
#include <mutex>
#include <queue>
#include <thread>
#include <vector>
class ThreadPool {
public:
    explicit ThreadPool(std::size_t n) {
        for (std::size_t i = 0; i < n; ++i) workers_.emplace_back([this] { loop(); });
    }
    ~ThreadPool() {
        { std::lock_guard<std::mutex> lk(m_); stop_ = true; }
        cv_.notify_all();
        for (auto& t : workers_) t.join();      // 唤醒全部后再 join，不丢任务
    }
    auto submit(std::function<int()> f) -> std::future<int> {
        auto task = std::make_shared<std::packaged_task<int()>>(std::move(f));
        auto fut = task->get_future();
        { std::lock_guard<std::mutex> lk(m_); tasks_.emplace([task] { (*task)(); }); }
        cv_.notify_one();
        return fut;
    }
private:
    void loop() {
        for (;;) {
            std::function<void()> job;
            {
                std::unique_lock<std::mutex> lk(m_);
                cv_.wait(lk, [this] { return stop_ || !tasks_.empty(); });   // 谓词防虚假唤醒
                if (stop_ && tasks_.empty()) return;   // 退出前保证队列已排空
                job = std::move(tasks_.front());
                tasks_.pop();
            }
            job();                                  // 锁外执行：任务里再加锁也不死锁
        }
    }
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;
    std::mutex m_;
    std::condition_variable cv_;
    bool stop_ = false;
};
int main() {
    ThreadPool pool(4);
    return pool.submit([] { return 1 + 2; }).get();   // 3
}
```
### 9.5 jthread 与 pthread 对比
`std::jthread`（C++20）析构时先 `request_stop()` 再 `join()`，自带 `std::stop_token` 协作式取消——线程函数写成 `[](std::stop_token st) { while (!st.stop_requested()) { /* 干活 */ } }`，不检查 `stop_token` 就不会停；普通 `std::thread` 用 `std::this_thread::sleep_for(...)` 做节拍、`join()` 收尾。

| 维度 | `std::thread`（C++11） | `pthread` |
| --- | --- | --- |
| 可移植性 | 跨平台 | 类 Unix，Windows 需兼容层 |
| 线程函数 | 任意可调用对象 | `void* (*)(void*)` |
| 返回值 | `future`/`promise` | `void*` 返回值或共享变量 |
| 加锁 | `mutex` + RAII | `pthread_mutex_lock/unlock` 手动配对 |
| 条件变量 | `condition_variable` | `pthread_cond_wait/signal` |
| 线程局部 | `thread_local` | `__thread` / `pthread_key_create` |
| 生命周期 | 必须 join/detach（`jthread` 自动） | `pthread_join`/`pthread_detach` |

Linux 上 `std::thread` 底层就是 pthread，性能基本一致；跨平台优先用标准库，需要设置栈大小、调度策略、亲和性时用 `native_handle()` 下探平台 API。

## 10 常用标准库设施
「不重复造轮子」的清单：IO、时间、随机数、正则、文件系统与算法。
### 10.1 iostream / fstream / sstream
| 头文件 | 类 | 用途 |
| --- | --- | --- |
| `<iostream>` | `cin`/`cout`/`cerr`/`clog` | 标准输入输出 |
| `<fstream>` / `<sstream>` | `ifstream`/`ofstream`；`istringstream`/`ostringstream` | 文件读写 / 字符串与流互转 |

性能敏感时关同步（`sync_with_stdio(false)`、`cin.tie(nullptr)`）；`>>` 失败要检查流状态（`if (in >> x)`）；`getline` 与 `>>` 混用注意残留换行；大文件按块 `read` 比逐行快，二进制加 `std::ios::binary`。

```cpp
#include <fstream>
#include <sstream>
#include <string>
int main() {
    std::istringstream iss("10 20 hello");   // 字符串拆分
    int a = 0, b = 0;
    std::string word;
    iss >> a >> b >> word;
    std::ostringstream oss;                  // 格式化拼接
    oss << "id=" << a << ", name=" << word;
    { std::ofstream out("demo.txt"); out << "line1\nline2\n"; }   // RAII：自动关闭
    std::ifstream in("demo.txt");
    std::string line;
    int lines = 0;
    while (std::getline(in, line)) ++lines;
    return a + b + static_cast<int>(word.size()) + lines;
}
```
### 10.2 chrono 与 random
| 时钟 | 特性 | 用途 |
| --- | --- | --- |
| `system_clock` | 墙上时钟，可被 NTP 调整 | 日志时间戳、显示时间 |
| `steady_clock` | 单调递增，不可调整 | **测量耗时** |
| `high_resolution_clock` | 通常是前两者之一 | 测耗时用 `steady_clock` 更稳 |

别用 `rand() % n`：低位分布差，`n` 非 2 的幂时还有模偏差；引擎对象别每次调用都重建。`duration` 类型安全：`1000ms == 1s` 为真，跨单位要 `duration_cast` 截断。

```cpp
#include <chrono>
#include <random>
#include <thread>
using namespace std::chrono_literals;
int main() {
    auto start = std::chrono::steady_clock::now();
    std::this_thread::sleep_for(10ms);                  // C++14 字面量
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                  std::chrono::steady_clock::now() - start).count();
    std::mt19937 gen(12345);                            // 固定种子：可复现
    std::uniform_int_distribution<int> dice(1, 6);      // 闭区间 [1, 6]
    return static_cast<int>(ms) + dice(gen);
}
```
### 10.3 regex、filesystem 与 algorithm
正则在部分实现上性能一般，密集场景可换 RE2/PCRE2；写正则用原始字符串 `R"(...)"` 免转义。`filesystem` 的错误处理两条路：抛 `filesystem_error` 或传 `error_code`（库代码倾向后者），路径拼接用 `operator/`。`accumulate` 的初值 `0` 是 `int`，对 `double` 求和会截断，应写 `0.0`。

| 算法 | 作用 | 注意 |
| --- | --- | --- |
| `sort`/`stable_sort` | 排序 | `stable_sort` 保序更贵 |
| `find`/`find_if` | 线性查找 | 已排序用 `binary_search` |
| `count`/`count_if` | 计数 | 常配 lambda |
| `transform` | 映射 | 可原地或写新容器 |
| `accumulate` | 折叠 | `<numeric>`，初值类型决定结果 |
| `remove_if` + `erase` | erase-remove | 单独 `remove_if` 不删元素 |
| `any_of`/`all_of` | 存在/全部 | 短路求值 |
| `unique` | 相邻去重 | 必须先排序 |

```cpp
#include <algorithm>
#include <filesystem>
#include <numeric>
#include <regex>
#include <string>
#include <vector>
namespace fs = std::filesystem;
int main() {
    std::regex email(R"(([\w.+-]+)@([\w-]+\.[\w.-]+))");   // 原始字符串免转义
    std::string s = "contact: alice@example.com";
    std::smatch m;
    std::regex_search(s, m, email);                   // 在 s 中查找，结果在 m[1]/m[2]
    fs::path dir = "fs_demo";
    fs::create_directories(dir / "sub");             // 自动创建中间目录
    std::error_code ec;
    fs::remove_all(dir, ec);                          // 不抛异常的版本
    std::vector<int> v{5, 1, 4, 2, 3, 2, 6};
    std::sort(v.begin(), v.end());
    int n = std::accumulate(v.begin(), v.end(), 0) + *std::max_element(v.begin(), v.end());
    v.erase(std::remove_if(v.begin(), v.end(), [](int x) { return x % 2 == 0; }), v.end());
    return static_cast<int>(m[2].length()) + n + static_cast<int>(v.size()) + (ec ? 1 : 0);
}
```

## 11 性能与优化
「这段代码为什么慢」比「语法怎么用」更能区分水平。下面是收益最高的几条规则与 `std::move` 反模式。
### 11.1 传参选择
| 参数类型 | 拷贝 | 适用 |
| --- | --- | --- |
| `const T&` | 无 | 只读大对象，**默认选择** |
| `T` | 一次（可被省略） | 函数内要存副本，配 `std::move` |
| `T&` / `T*` | 无 | 要修改实参 / 可为空、C 接口 |
| `T&&`（模板） | 无 | 完美转发，仅泛型代码 |

经验规则：`sizeof(T) <= 2 * sizeof(void*)` 且可平凡拷贝的小类型按值传更快（省掉解引用），其余用 `const&`。

```cpp
#include <string>
#include <utility>
#include <vector>
class User {
public:
    explicit User(std::string name) : name_(std::move(name)) {}   // 按值 + move
    const std::string& name() const { return name_; }
private:
    std::string name_;
};
int main() {
    std::vector<User> v;
    std::string n = "alice";
    v.emplace_back(n);              // 左值：拷贝一次
    v.emplace_back("bob");          // 右值：移动
    int len = 0;
    for (const auto& u : v) len += static_cast<int>(u.name().size());   // const auto&
    return len;
}
```
### 11.2 reserve、内联与优化选项
`vector` 扩容按倍数增长并搬动全部元素，`reserve` 一次分配到位；返回局部对象直接 `return t;`，不要 `return std::move(t);`。`resize` 会构造元素而 `reserve` 不会，别混用；`string` 多次拼接用 `+=` 而非反复 `+`；`shrink_to_fit()` 只是请求释放多余容量，不保证生效。`inline` 只是「允许合并定义」，是否内联由优化阶段决定；强制内联用 `__attribute__((always_inline))`/`__forceinline`，但会加大指令缓存压力。优化前先用 `perf`/火焰图定位热点。

| 选项 | 作用 | 注意 |
| --- | --- | --- |
| `-O0` | 不优化，便于调试 | 性能测试别用 |
| `-O2` | 常规优化，含内联 | 发布常用 |
| `-O3` | 更激进（循环展开、向量化） | 代码膨胀，未必更快 |
| `-Os` | 优化体积 | 嵌入式和移动端 |
| `-flto` | 链接时优化，跨 TU 内联 | 编译慢、调试信息变差 |
| `-march=native` | 针对本机 CPU | 产物不能分发 |
### 11.3 不必要的拷贝与 std::move 反模式
常见隐性拷贝：`for (auto x : bigVector)`、返回 `const T`（阻止移动）、`std::function` 包装大对象、lambda 按值捕获大对象、`map::operator[]` 的默认构造。开启 `-Wpessimizing-move`、`-Wredundant-move` 与 clang-tidy 的 `performance-*` 能抓出一批。

| 反模式 | 问题 | 正确做法 |
| --- | --- | --- |
| `return std::move(local);` | 阻止 NRVO，多一次移动 | `return local;` |
| move 之后还读原对象 | 状态未指定 | 移走后不再使用 |
| 移动 `const` 对象 | 变 `const T&&`，退化拷贝 | 去掉 `const` 或不必 move |
| 对小类型 `std::move` | 无收益 | 直接传值 |
| 循环里 move 容器元素 | 可能提前掏空数据 | 确认所有权再移 |

```cpp
#include <string>
#include <unordered_map>
#include <vector>
int main() {
    std::unordered_map<std::string, std::vector<int>> m;
    m["a"].push_back(1);                       // 不要 find 两次
    m.emplace("b", std::vector<int>{2, 3});    // 原地构造，省一次临时对象
    std::vector<int> v;
    v.reserve(1000);                           // 预分配：容量一次到位，避免多次扩容搬移
    for (int i = 0; i < 1000; ++i) v.push_back(i);
    std::string s = "abc";
    std::string t = s + "def";                 // 一次拼接，而不是反复 s = s + ...
    return static_cast<int>(t.size() + m.size() + v.size());
}
```
### 11.4 缓存友好
1. **数据局部性**：连续内存（`vector`）远胜链表，遍历链表每次跳转都可能缓存未命中。
2. **结构体布局**：热字段聚拢（AoS → SoA），顺序访问的结构体把常用字段放前面。
3. **避免伪共享**：多线程写同一缓存行内的不同变量会让缓存行反复失效，用 `alignas(64)` 隔离（`std::hardware_destructive_interference_size` 的**可用性以平台为准**）。
4. **循环顺序**：二维数组按行遍历比按列快数倍（`for (i) for (j) sum += flat[i * M + j];` 符合内存连续方向）；热循环里尽量避免虚调用和间接跳转。

## 12 调试与工具
会写代码也要会找 bug。本章把编译告警、gdb 看虚表、内存/线程检查器和静态分析工具串起来。
### 12.1 编译告警
| 选项 | 作用 |
| --- | --- |
| `-Wall` / `-Wextra` | 常用告警 + 更严格检查（未使用变量/参数、未初始化、可疑比较） |
| `-Wpedantic` / `-Wshadow` | 拒绝非标准扩展 / 变量遮蔽 |
| `-Werror` | 告警当错误，CI 常用 |
| `-Wreorder` / `-Wreorder-ctor` | 初始化顺序与声明顺序不一致 |
| `-Wpessimizing-move` | 抓 `return std::move(local)` |
| `/W4` + `/permissive-` | MSVC 的等价开关 |

```bash
g++ -std=c++17 -Wall -Wextra -Wpedantic -Wshadow -Wreorder -g -O1 main.cpp -o app
clang++ -std=c++17 -Wall -Wextra -Wpessimizing-move -Wredundant-move -g main.cpp -o app
cl /std:c++17 /W4 /permissive- /EHsc main.cpp
```

`-Wall -Wextra` 别和 `-Werror` 一起挂在第三方代码上，升级编译器会导致整个项目编译失败；自己的代码应做到零告警。
### 12.2 gdb 看 vtable 与 valgrind/sanitizer
| 命令 | 作用 |
| --- | --- |
| `bt` / `frame N` | 查看调用栈 / 切换帧 |
| `p obj` / `p /a obj` | 打印对象 / 按动态类型打印 |
| `info vtbl *p` | 打印虚表（现代 gdb） |
| `x/8gx &obj` | 按 8 字节查看对象首部（vptr） |
| `ptype obj` / `catch throw` | 打印类型布局 / 在异常抛出点中断 |

```bash
g++ -std=c++17 -g -O0 -fno-omit-frame-pointer vtbl.cpp -o vtbl && gdb ./vtbl
(gdb) set print object on     # 按动态类型显示
(gdb) p p                     # 显示 *p 的实际类型
(gdb) info vtbl *p            # 虚表槽位
(gdb) x/4gx &d                # 对象首部：vptr + 成员
```

`-O0` 下变量才可靠可见，`-fno-omit-frame-pointer` 让栈回溯更准；崩溃用 `gdb ./app core` 分析。

| 检查器 | 选项 | 抓什么 |
| --- | --- | --- |
| valgrind memcheck | `--leak-check=full` | 泄漏、非法读写（无需重编，慢 10~50 倍） |
| AddressSanitizer | `-fsanitize=address` | 越界、use-after-free、double free |
| LeakSanitizer | `-fsanitize=leak` | 内存泄漏（Linux 随 ASan 默认开） |
| UBSan | `-fsanitize=undefined` | 有符号溢出、空指针、对齐、类型双关 |
| ThreadSanitizer | `-fsanitize=thread` | 数据竞争 |
| MemorySanitizer | `-fsanitize=memory` | 未初始化读（依赖需全部用 MSan 编译） |

```bash
valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all ./app
valgrind --tool=helgrind ./app                          # 数据竞争
g++ -std=c++17 -g -O1 -fsanitize=address -fno-omit-frame-pointer app.cpp -o app_asan
./app_asan
# ==1234==ERROR: AddressSanitizer: heap-use-after-free on address 0x...
#     #0 0x... in main app.cpp:12
g++ -std=c++17 -g -O1 -fsanitize=undefined -fno-sanitize-recover=all app.cpp -o app_ubsan
g++ -std=c++17 -g -O1 -fsanitize=thread app.cpp -o app_tsan && ./app_tsan
```
ASan 与 TSan **不能同时开**，一般分别跑两套 CI 构建；ASan 内存开销约 2~3 倍，不适合长期开在生产；`-fno-sanitize-recover=all` 让 UBSan 在第一个错误处 abort，CI 更容易失败退出。
### 12.3 clang-tidy 与 cppcheck
| 检查组 / 工具 | 抓什么 | 典型提示 |
| --- | --- | --- |
| `modernize-*` | 用 C++11/14/17 写法替换旧写法 | `modernize-use-nullptr`、`modernize-use-auto` |
| `bugprone-*` | 易错结构 | `bugprone-use-after-move` |
| `performance-*` | 不必要拷贝 | `performance-unnecessary-copy-initialization` |
| `cppcheck` | 空指针、未初始化、越界、无用代码 | 不依赖编译器前端，可整目录扫描 |

```bash
clang-tidy main.cpp -checks='-*,modernize-*,bugprone-*,performance-*,readability-*' -- -std=c++17
clang-tidy main.cpp -p build/ -header-filter='.*'      # 用 compile_commands.json
clang-tidy -fix main.cpp -p build/                     # 自动修复
cppcheck --enable=all --std=c++17 --inconclusive --suppress=missingIncludeSystem src/
```

CMake 用 `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` 生成 `compile_commands.json`，规则固定进 `.clang-tidy`。推荐组合：**开发时 clang-tidy + 编译告警，CI 再跑 cppcheck + ASan/UBSan**。

## 13 常见陷阱 15 条
可以直接背下来在面试里朗读的清单，每条都是「为什么错 + 怎么对」。
### 13.1 对象切片 / 悬垂引用 / 迭代器失效
把派生类对象按值赋给基类会切掉派生部分，虚函数行为退化为基类——多态对象一律用 `Base&`/`Base*`/`unique_ptr<Base>`。返回局部变量的引用、指针或 `c_str()` 都是悬垂；正确做法是返回对象本身（靠 RVO）、写进调用方传入的对象、或返回智能指针。`string_view` 同理——视图不拥有数据。容器修改后旧迭代器会失效，遍历时别增删，`erase` 要用返回值继续。

```cpp
#include <string>
#include <vector>
struct Base { virtual int f() const { return 0; } };
struct Derived : Base { int f() const override { return 1; } };
int by_value(Base b) { return b.f(); }        // 切片：返回 0
int by_ref(const Base& b) { return b.f(); }   // 正确：返回 1
const std::string& bad() { std::string local = "temp"; return local; }   // 悬垂引用
int main() {
    Derived d;
    std::vector<int> v{1, 2, 3, 4};
    for (auto it = v.begin(); it != v.end();) {
        if (*it % 2 == 0) it = v.erase(it);   // 用返回值继续，别 ++it
        else ++it;
    }
    // const std::string& r = bad();          // UB
    return by_value(d) * 10 + by_ref(d) + static_cast<int>(v.size());
}
```

| 容器 | 操作 | 失效范围 |
| --- | --- | --- |
| `vector`/`string` | 触发扩容 | 全部迭代器/指针/引用 |
| `vector` | `insert`/`erase` | 插入或删除点之后 |
| `deque` | 中间插入/删除 | 全部迭代器 |
| `list`/`map`/`set` | 插入 | 不影响其他迭代器 |
| `list`/`map`/`set` | 删除 | 仅被删元素的迭代器 |

### 13.2 shared_ptr 循环引用 / memset / 隐式转换 / vector<bool> / 静态初始化
互持 `shared_ptr` 计数永不归零，一侧改 `weak_ptr` 或手动 `reset()` 打破环，`weak_ptr` 提升用 `lock()`。`memset` 只适合平凡类型，对 `std::string` 用会破坏内部指针、析构崩溃（可用 `std::is_trivially_copyable_v<T>` 做静态断言）。单参数构造函数不加 `explicit` 会让实参被静默转换。`vector<bool>` 按位压缩，元素不是真正的 `bool`，不能取地址、`v[0]` 是代理对象，替代是 `vector<char>`/`bitset`。不同 TU 的全局对象初始化顺序未定义，用函数内 `static`（Meyers Singleton）规避。

```cpp
#include <cstring>
#include <memory>
#include <string>
#include <vector>
struct A { std::shared_ptr<A> other; };   // 强引用自环：a 永不析构，内存泄漏
struct B { std::weak_ptr<B> other; };     // weak 打破环：b 正常析构
struct Size {
    Size(int n) : n_(n) {}                // 没有 explicit → check(3) 静默转换
    int n_;
};
const std::string& config() {             // Meyers Singleton：首次调用时才初始化
    static std::string s = "default";
    return s;
}
int main() {
    auto a = std::make_shared<A>();
    a->other = a;                         // use_count == 2
    a->other.reset();                     // 手动打破环
    auto b = std::make_shared<B>();
    b->other = b;                         // weak 不增加计数，正常析构
    std::vector<bool> flags{true, false};
    auto proxy = flags[0];                // 代理对象；&flags[0] 编译错误
    int raw = 0;
    std::memset(&raw, 0, sizeof(raw));    // 平凡类型才安全
    return Size(3).n_ + static_cast<int>(proxy) + raw + static_cast<int>(config().size());
}
```
### 13.3 向量切片 / 有符号溢出 / 构造中调虚函数 / 忘记 join
只要类可能被多态删除，析构就必须 `virtual`。有符号溢出是 UB，编译器可以假定它不发生从而把检查优化掉：先提升到更宽类型再运算，容器访问用 `at()` 换取可捕获的异常。构造阶段 vptr 指向当前正在构造的类，调用虚函数不会多态，调用纯虚函数是 UB——用「构造 + 显式 `init()`」两段式。`std::thread` 析构时仍 `joinable()` 会 `terminate`，用 RAII 包装或 C++20 `std::jthread`。

```cpp
#include <limits>
#include <thread>
struct Base {
    Base() { f(); }                      // 调用 Base::f，不是 Derived::f
    virtual void f() {}
    virtual ~Base() = default;           // 虚析构：delete Base* 才安全
};
struct Derived : Base { void f() override {} };
int main() {
    Base* p = new Derived;
    delete p;                            // 有虚析构，安全
    std::thread t([] {});
    t.join();                            // 未 join 也未 detach → terminate
    int x = std::numeric_limits<int>::max();
    long long safe = static_cast<long long>(x) + 1;   // 先提升类型，避免 UB
    return static_cast<int>(safe - x);
}
```
### 13.4 lambda 悬垂捕获 / map key / uint8_t
`[&]` 捕获局部变量后把 lambda 存起来（异步、放进容器），局部变量销毁后引用悬垂——异步/长期存活的 lambda 用按值捕获，例如 `for (int i = 0; i < 3; ++i) fns.push_back([i] { return i * i; });` 放进 `std::vector<std::function<int()>>` 是安全的。`map` 要求严格弱序，`unordered_map` 要求 `hash` + `==`；`operator<` 写错（例如总是 `false`）会静默丢元素，正确写法是 `bool operator<(const Key& o) const { return std::tie(a, b) < std::tie(o.a, o.b); }`（C++20 可直接 `auto operator<=>(const Key&) const = default;`）。`std::uint8_t` 是 `unsigned char` 的别名，`cout << x` 打印字符而非数字（`c = 65` 打印 `'A'`），调试日志常出现「空字符」，要输出数字得 `static_cast<int>(c)`。
### 13.5 15 条速查表
| # | 陷阱 | 一句话对策 |
| --- | --- | --- |
| 1 | 对象切片 | 多态对象用引用/指针/`unique_ptr` |
| 2 | 返回局部引用/指针/`c_str()` | 返回对象本身靠 RVO |
| 3 | `string_view` 悬垂 | 视图不拥有数据，注意生命周期 |
| 4 | 迭代器失效 | `erase` 用返回值；增删后重建 |
| 5 | `shared_ptr` 循环引用 | 一侧改 `weak_ptr` |
| 6 | `memset` 非平凡类型 | 只用于 trivially copyable |
| 7 | 隐式转换 | 构造函数/转换运算符加 `explicit` |
| 8 | `vector<bool>` 特化 | 用 `vector<char>`/`bitset` |
| 9 | 静态初始化顺序 | 函数内 `static` / `constinit` |
| 10 | 基类无虚析构 | 析构一律 `virtual` |
| 11 | 有符号溢出 | 先提升宽类型；用 `at()` |
| 12 | 构造中调虚函数 | 两段式 `init()` |
| 13 | thread 忘记 join | RAII 包装或 `jthread` |
| 14 | lambda 按引用捕获悬垂 | 按值捕获 / `shared_ptr` |
| 15 | map key 不是严格弱序 | `std::tie` 或 `<=>` 默认 |

## 14 延伸
以上覆盖了标准演进、编译链接、对象模型、构造析构、移动语义、智能指针、模板、异常、并发、标准库、性能与工具。按方向继续深入：
1. [C++基础](C++基础.md)——语法、关键字、类与对象、STL 使用层面的入门与查漏补缺。
2. [STL标准库](C++STL标准库.md)——容器、迭代器、算法的复杂度与实现细节（`vector`/`map`/`unordered_map` 内部结构）。
3. [C++面试题](C++面试题.md)——按主题整理的题库与参考答案，面试前集中刷。
4. [C++项目实战](C++项目实战.md)——把语言特性落到工程：构建系统、日志、网络、线程池、测试与性能剖析。

建议顺序：先用「C++基础」确认语法无死角，再用本文补齐「为什么」（对象模型、移动语义、异常安全、并发），然后对照「STL标准库」记复杂度，最后用「C++面试题」查漏、用「C++项目实战」做一两个能讲清楚的项目。
