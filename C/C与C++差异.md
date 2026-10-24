## 1 定位差异
C 是过程式语言：以函数和数据结构为中心，接近机器模型，运行时极小，常被当作「可移植的汇编」。C++ 是多范式语言：在过程式基础上加入面向对象、泛型、函数式设施，并坚持「零开销抽象」——不用的特性不付代价，用了也不比手写差。

| 维度 | C | C++ |
| --- | --- | --- |
| 范式与抽象 | 过程式；结构体、函数指针、宏 | 过程式/面向对象/泛型；类、模板、Lambda |
| 资源管理 | malloc/free、goto cleanup | 构造/析构、RAII、智能指针 |
| 运行时 | 可 freestanding，几乎无运行时 | 可有异常/RTTI，也可关闭 |
| 典型场景 | 内核、驱动、RTOS、底层 ABI | 应用、基础设施、游戏、高性能服务 |

C 的「可移植汇编」定位意味着语言小、ABI 稳定、编译器易移植，程序员对内存布局和指令有较强控制。C++ 的零开销抽象意味着 `vector`、`unique_ptr`、模板和内联可以生成接近手写 C 的代码，但语言规则、编译时间和二进制体积明显增加。
C++ 不是 C 的严格超集：`void*` 隐式转对象指针、VLA、`restrict`、`_Generic`、复合字面量、K&R 函数定义、`char *p = "abc";` 在标准 C++ 中都不合法；`f()` 在 C 中表示参数未指定，在 C++ 中表示无参数。C23 借用了 `bool`、`constexpr`、`nullptr`、`auto`、`typeof`，但语义并不完全相同。
同一个 `.h` 给两种语言使用时，只能写共有语法，并用 `__cplusplus` 包住 C++ 专属的链接声明：

```c
/* acme_math.h：C 与 C++ 都能包含 */
#ifndef ACME_MATH_H
#define ACME_MATH_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct acme_ctx acme_ctx;      /* 不透明类型 */
acme_ctx *acme_ctx_new(void);
int acme_add(acme_ctx *ctx, int a, int b);
void acme_ctx_free(acme_ctx *ctx);
#ifdef __cplusplus
}
#endif
#endif /* ACME_MATH_H */
```

头文件里不要出现 `class`、`template`、重载、默认参数、引用等 C 不认识的语法；C++ 调用方看到 `extern "C"` 后按 C 符号链接，C 调用方完全看不到这个关键字。

## 2 编译与链接
两种语言都经历「预处理 → 编译 → 汇编 → 链接」，但 C++ 的符号命名、链接约定和头文件处理更复杂，跨语言链接错误十有八九出在名字修饰上。
### 2.1 名称修饰
C 函数符号基本就是函数名（部分平台加前导下划线）；C++ 把命名空间、类、参数类型、cv/ref 限定、模板实参编码进符号，称为 name mangling。不同编译器/ABI 规则不同，下表是 Itanium ABI（GCC/Clang 常见）的示意：

| 源码 | 典型符号 | 编码含义 |
| --- | --- | --- |
| C 的 `int add(int, int)` | `add` 或 `_add` | 只有名字 |
| `namespace math { int add(int, int); }` | `_ZN4math3addEii` | `N...E` 嵌套名，`i` 是 int |
| `void Foo::bar(double) const` | `_ZNK3Foo3barEd` | `K` 表示 const 成员函数 |
| `template<class T> T twice(T)` | `_Z5twiceIiET_S0_` | 模板实参进入符号 |

MSVC 使用另一套编码（如 `?add@@YAHHH@Z`），所以不要把修饰后的名字写死。排查时用 `nm` 看符号、`nm -C` 还原可读名，或 `c++filt` 解码。
如果 C++ 调用 C 函数时没有声明 C 链接，编译器会去找 `_Z3addii` 一类符号，链接器报 `undefined reference to 'add(int, int)'`。
### 2.2 extern "C"
`extern "C"` 指定 C 语言链接（language linkage），关闭 C++ 名字修饰，按 C ABI 生成和查找符号。它只影响链接名和调用约定，不改变函数体的 C++ 语义。
- 可以修饰单个函数/变量，也可以包住一段声明；同一名字只能有一个 C 链接函数，因此 `extern "C"` 函数不能重载。
- 类成员函数、模板不能整体获得 C 链接；带虚函数或非平凡构造的 C++ 对象不能直接跨 C 边界，通常用不透明指针封装。
- 声明和定义都要让编译器看到 C 链接；通常把 `extern "C"` 写进头文件，而不是只在调用处写一次。

```cpp
extern "C" int c_add(int, int);     // 单个声明
extern "C" {
#include "legacy.h"                  // C 头没有 extern "C" 守卫时
}
```

只有头文件确实是 C 头时才这样包；如果它包含 C++ 类、模板或异常规格，放进 `extern "C"` 会编译失败。
### 2.3 为什么要 #ifdef __cplusplus
C 编译器不认识 `extern "C"`，直接写会语法错误；C++ 编译器定义 `__cplusplus`（C++17 为 `201703L`，C++20 为 `202002L`）。用条件编译把 C++ 专属声明包起来，同一份头文件就能被两边包含。
`#ifdef __cplusplus` 应放在头文件内部、紧挨声明；不要用 `#if __cplusplus >= 201103L` 判断 C 标准版本（C 下该宏未定义），头文件还应有 include guard 或 `#pragma once`。
### 2.4 C++ 调 C 库与 C 调 C++
C++ 调 C 库：
1. C 源码用 C 编译器编成 `.o`、`.a` 或 `.so`，不要为了「统一」强行用 C++ 编译器重编。
2. C++ 侧包含声明并确保 C 链接；头文件没有 `extern "C"` 就自己包一层，或重新声明所需函数。
3. 链接时用 `-L` 指定库路径、`-l` 指定库名；静态库顺序是使用者在左、库在右。
4. 向 C 注册回调时，回调必须是 C 链接函数；无捕获 Lambda 可转函数指针，有捕获的不行。

C 调 C++：
1. 在 C++ 源文件中用 `extern "C"` 定义导出函数，头文件只暴露 C 兼容类型。
2. 参数/返回值只用 POD、指针、整数、`const char *`；C++ 对象用不透明指针或前向声明隐藏。
3. 异常绝不能穿越 C 栈帧：导出函数内 `try/catch(...)`，把异常转成错误码。
4. C++ 库可能依赖 libstdc++，用 `gcc` 链接时补 `-lstdc++`，或直接用 `c++` 驱动链接；ABI 必须匹配。

## 3 类型系统
C 的类型系统围绕对象表示和隐式转换；C++ 增加了引用、类类型、模板推导和更细的转换分类。C++ 更严格，但并不自动等于更安全。
### 3.1 bool
C99 用关键字 `_Bool` 表示布尔类型，`<stdbool.h>` 把 `bool`、`true`、`false` 定义为宏；C23 起它们成为关键字。`_Bool` 会把任何标量的「是否为 0」归一化为 0/1，`sizeof(_Bool)` 常见为 1 但标准未固定。
C++ 的 `bool` 是内建独立类型，`true`/`false` 是关键字；整数和指针可隐式转 `bool`（非零为真），`bool` 也参与重载决议。跨语言 ABI 不要直接传 `bool`，用 `int` 或 `uint8_t` 更稳。
### 3.2 nullptr vs NULL vs 0
| 写法 | C | C++ |
| --- | --- | --- |
| `0` | 空指针常量，也是 int | 空指针常量，但重载时按 int 处理 |
| `NULL` | 实现定义，常见 `((void*)0)` 或 `0` | 常见 `0` 或编译器内建，可能误选 int 重载 |
| `nullptr` | C23 才有 `nullptr_t` | C++11 关键字，类型 `std::nullptr_t` |
| 建议 | 指针用 `NULL`，整数用 `0` | 一律用 `nullptr` |

- 同时有 `f(int)` 和 `f(char*)` 时，`f(NULL)` 可能调用 `f(int)` 或产生歧义；`f(nullptr)` 明确选择指针重载。
- `template<class T> void g(T)` 遇到 `NULL` 可能推导出整数类型，遇到 `nullptr` 推导出 `std::nullptr_t`；`auto p = NULL;` 也未必得到指针。
- C 允许 `void*` 隐式转任意对象指针，所以 `char *p = NULL;` 没问题；C++ 不允许 `void*` 隐式转 `T*`，必须显式转换。`nullptr` 可转成员指针，且不会像 `0`/`NULL` 那样在重载中被当成整数。
### 3.3 enum class
C 的枚举常量注入外围作用域，底层类型由实现选择（通常 int），枚举变量可隐式转 int，不同枚举之间也能经整型转换混用。
C++11 的 `enum class` 是作用域枚举：必须写 `Color::Red`，不隐式转 int，不能和另一个枚举类型随意比较；可以指定底层类型并前向声明，需要整数时用 `static_cast`。非限定枚举仍保留隐式转 int 的兼容行为。
C23 支持 `enum E : type` 固定底层类型，但没有 `enum class` 那样的作用域隔离。

```cpp
enum class Color : std::uint8_t { Red, Green, Blue };
Color c = Color::Red;
auto v = static_cast<std::uint8_t>(c);   // 必须显式
```
### 3.4 引用 vs 指针
| 维度 | 指针 | 引用 |
| --- | --- | --- |
| 能否为空 | 可以 | 语言层面不可以，必须绑定对象 |
| 能否重新绑定 | 可以 | 不可以，始终是同一对象 |
| 是否占存储 | 是 | 通常按指针实现，但语言层面不是独立对象 |
| `sizeof` | 指针本身大小 | 被引用类型的大小 |
| 算术/多级 | 支持 | 不支持 |

引用必须初始化，没有合法的空引用，但可以悬空：返回局部变量的引用、绑定已销毁对象都是 UB。`const T&` 能绑定临时量并延长其生命周期到引用作用域结束；`T&&` 是右值引用，用于移动和完美转发。
传参选择：小对象按值，大对象 `const T&`，需要修改用 `T&`，需要可空或可重绑用 `T*`。C 没有引用，统一用指针并靠文档约定非空。
### 3.5 auto 与 decltype
C 的 `auto` 是存储类说明符（自动存储期，几乎不用）；C23 的 `auto` 才是类型推导，只能用于带初始化器的对象定义，语义比 C++ 窄。
C++11 的 `auto` 按初始化表达式推导，默认按值，丢掉顶层 const 和引用；保留引用写 `auto&`，只读且避免拷贝写 `const auto&`，要精确类型用 `decltype(auto)`。`decltype(x)` 得到变量声明类型，`decltype((x))` 对带括号的左值得到 `T&`，这是转发和引用折叠的基础。
C++14 支持函数返回类型 `auto` 推导，C++20 支持 `auto` 参数（缩写模板）；C 没有 `decltype`，C23 提供 `typeof`/`typeof_unqual`。

```cpp
int x = 0;
const int &r = x;
auto a = r;            // int：去掉 const 和引用
auto &b = r;           // const int&
decltype(r) c = x;     // const int&
decltype((x)) d = x;   // int&
```
### 3.6 四种 cast 与 C 风格强转
C 只有 `(T)expr` 一种写法，编译器会按上下文尝试 `const_cast`、`static_cast`、`reinterpret_cast` 的组合，可能悄悄去掉 const 或做无关指针转换，而且难以检索。
- `static_cast`：相关类型间的显式转换，数值转换、`void*` 转对象指针、基类与派生类互转（不做运行时检查，向下转型错误是 UB）、显式构造函数。
- `const_cast`：只增删 `const`/`volatile`，用于适配旧接口；修改真正 const 的对象是 UB。
- `reinterpret_cast`：指针与整数、无关指针类型之间按位解释，结果实现定义，除底层字节处理外少用。
- `dynamic_cast`：多态类型的运行时安全向下/交叉转换，失败时指针返回 `nullptr`、引用抛 `std::bad_cast`，需要 RTTI。

| cast | 典型用途 | 运行时检查 |
| --- | --- | --- |
| `static_cast` | 数值、void*、上行/下行转换 | 无 |
| `const_cast` | 去掉/加上 const | 无 |
| `reinterpret_cast` | 指针/整数/无关指针 | 无 |
| `dynamic_cast` | 多态类型安全向下转换 | 有，需 RTTI |

```cpp
double d = 3.7;
int i = static_cast<int>(d);            // 明确是数值转换
const char *s = "x";
char *p = const_cast<char *>(s);        // 只去 const，不要改原对象
void *raw = p;
auto *q = static_cast<char *>(raw);     // void* 必须显式转
```

C++20 还有 `std::bit_cast`，按位复制要求 trivially copyable，和传统 cast 不是一类。

## 4 函数与重载
### 4.1 函数重载
C 不允许同名函数共存，只能靠 `add_int`/`add_double` 这类命名区分。C++ 允许重载，条件是参数列表不同：类型、个数、顺序不同，成员函数还可以用 cv/ref 限定区分；返回类型不参与重载。
重载在编译期解析，优先精确匹配，其次整型提升、标准转换、用户定义转换；出现多个同等匹配就报歧义。底层依靠 name mangling 把参数类型编进符号，所以 `extern "C"` 函数不能重载；C 代码可用不同函数名或 `_Generic` 模拟。

```cpp
int max(int, int);
double max(double, double);        // 合法重载
// int max(int, int, int = 0);     // 与第一行冲突：默认参数不改变签名
```
### 4.2 默认参数
C 没有默认参数。C++ 在声明处给尾部参数默认值，调用点补全，默认值在编译期确定；只能从右往左连续默认，同一作用域内默认值只能指定一次，通常放在头文件。
虚函数的默认参数是静态绑定：按指针/引用的静态类型选默认值，而函数体按动态类型绑定，二者可能不一致。
### 4.3 inline
C99 的 `inline` 链接语义较复杂（一个 inline 定义配一个外部定义），头文件里常用 `static inline`。C++ 的 `inline` 允许同一函数在多个翻译单元中重复定义（ODR 例外），由链接器合并，适合放头文件。
`inline` 只是「允许定义在头文件、建议内联」，不保证展开；`-O0` 下通常不展开。类内定义的成员函数隐式 inline。C++17 还有 inline 变量，C 没有对应物。
### 4.4 constexpr
C++11 的 `constexpr` 要求变量/函数能在编译期求值，C++14 放宽函数体限制，C++20 增加 `consteval`（强制编译期）和 `constinit`（保证静态初始化）。`constexpr` 函数也可以在运行时调用。
`const` 只表示只读，不保证编译期；`constexpr` 变量隐含 const，可用于数组大小、模板实参和 `static_assert`。C 没有 constexpr 函数，C23 只有 constexpr 对象；C 里常用 `#define`、枚举、`static const int` 代替。

```cpp
constexpr int square(int x) { return x * x; }
static_assert(square(5) == 25);
int a[square(3)];       // 编译期常量
```
### 4.5 模板
函数模板是一组参数类型不同的函数，编译期实例化，类型安全；类模板把类型作为参数生成类，容器和智能指针都是例子；可变参数模板 `template<class... Ts>` 接受任意个类型/值，配合折叠表达式和完美转发。
C 没有模板，只能用 `void*` 泛型加函数指针（如 `qsort`）、宏、`_Generic` 或复制代码，代价是类型信息丢失、回调开销和调试困难。模板在编译期展开，可能代码膨胀、编译变慢；C++20 concepts 改善约束和报错。

```cpp
template <class T> T max(T a, T b) { return a > b ? a : b; }
template <class... Ts> void print(const Ts &...xs) { ((std::cout << xs), ...); }
```
### 4.6 命名空间
C 没有 namespace，靠前缀 `acme_`、文件级 `static`、头文件里不定义对象来避免冲突。C++ 的 namespace 可嵌套、可多次打开、可起别名；匿名 namespace 提供内部链接，可替代文件级 static；inline namespace 常用于版本化。
头文件里不要写 `using namespace std;`，它会污染所有包含者；`using std::string;` 比 using-directive 可控。

## 5 内存与对象生命周期
C 只提供「分配/释放字节」，C++ 把对象作为一等公民：分配、构造、析构、拷贝、移动分开描述。这是两者最大的思维差异。
### 5.1 new/delete vs malloc/free
| 维度 | `new/delete` | `malloc/free` |
| --- | --- | --- |
| 单位 | 类型/对象，自动计算大小 | 字节数 |
| 构造/析构 | 调用构造函数/析构函数 | 不调用 |
| 返回类型 | 正确的 `T*` | `void*`，C++ 中需转换 |
| 失败 | 默认抛 `std::bad_alloc`，`nothrow` 返回 nullptr | 返回 NULL |
| 配对 | `delete` / `delete[]` | `free` |
| 扩容 | 无 | `realloc` |
| 重载 | 可重载 `operator new/delete` | 不可 |

```cpp
int *p = new int(42);       // 分配 + 初始化
delete p;
int *q = new int[10]();     // 10 个 0
delete[] q;
```

`new T` 等价于调用 `operator new(sizeof(T))` 分配内存，再在该内存上构造对象；`delete p` 先析构，再调用 `operator delete`。`malloc` 只做第一步，所以对非平凡类型用 `malloc` 是 UB。
`new[]` 可能保存数组长度 cookie（尤其元素有非平凡析构时），`delete[]` 靠它逐个析构；`delete` 与 `delete[]` 混用是 UB，即使元素是 int 也不要赌。placement new 在已有内存上构造，必须显式析构：`::new (buf) T(args); p->~T();`。
### 5.2 构造函数与析构函数
C 用 `foo_init`/`foo_destroy` 约定，忘记调用、重复调用、错误路径漏调用全靠人；C++ 构造函数建立不变式，析构函数在作用域退出、异常展开、delete 时自动调用。
构造顺序是基类 → 成员（按声明顺序）→ 构造函数体；析构顺序相反。析构函数应 `noexcept`（C++11 起默认），异常逃出析构会 `std::terminate`。
多态基类的析构函数必须 `virtual`，否则 `delete base_ptr` 只析构基类部分，是 UB；构造函数/析构函数中调用虚函数只会 dispatch 到当前类。
### 5.3 拷贝构造与赋值
C 的 struct 赋值、传参、返回都按值复制（浅拷贝），指针成员共享同一块内存；C++ 默认拷贝构造/赋值逐成员拷贝，同样是浅拷贝。拥有资源的类必须自定义拷贝行为，否则会 double free。
Rule of 3：需要自定义析构、拷贝构造、拷贝赋值中的任何一个，通常三个都需要；C++11 再加移动构造和移动赋值，成为 Rule of 5。能默认就 `= default`，不能拷贝就 `= delete`，最好 Rule of 0：用 RAII 成员，让编译器生成。
拷贝赋值要处理自赋值、先释放旧资源、返回 `T&`，常用 copy-and-swap。移动后源对象必须可析构、可赋值，内容处于「有效但未指定」状态。
### 5.4 RAII
RAII 是「资源获取即初始化」：构造函数获取资源，析构函数释放资源，资源包括内存、文件、锁、socket、事务。对象生命周期由作用域决定，所以提前 return 或抛异常都不会漏掉清理。
C 的 `goto cleanup` 是手动 RAII；C++ 用 `std::lock_guard`、`std::unique_ptr`、`std::fstream` 把清理绑定到析构。RAII 通常零额外开销：析构调用静态确定，常被内联；代价是可能增加异常展开表和对象尺寸。
### 5.5 unique_ptr、shared_ptr、weak_ptr
| 类型 | 所有权 | 拷贝 | 开销 | 典型用途 |
| --- | --- | --- | --- | --- |
| `unique_ptr` | 独占 | 禁止，可 move | 通常与裸指针同大 | 工厂返回值、pimpl、容器元素 |
| `shared_ptr` | 共享 | 可拷贝，引用计数 | 两个指针 + 控制块 | 共享生命周期、异步回调 |
| `weak_ptr` | 不拥有 | 可拷贝 | 通常与 `shared_ptr` 同大 | 打破循环、观察者 |

`unique_ptr<T>` 默认用 `delete`，`unique_ptr<T[]>` 用 `delete[]`；`make_unique`（C++14）避免显式 new，自定义删除器可管理 `FILE*`、socket 等。
`shared_ptr` 的引用计数是原子操作，计数线程安全，但对象访问不线程安全；`make_shared` 通常一次分配控制块和对象，但 `weak_ptr` 存活会延迟整块内存释放。循环引用用 `weak_ptr` 打破，`lock()` 原子地提升为 `shared_ptr`，失败返回空；`expired()`/`use_count()` 只适合调试，不能作为同步依据。
### 5.6 移动语义
C++11 的右值引用 `T&&` 让「即将销毁的临时对象」的资源可以被窃取；移动构造/移动赋值把指针、缓冲区转走，源对象置空，避免深拷贝。
`std::move(x)` 只是一个到 `T&&` 的 `static_cast`，本身不移动任何东西；真正的移动发生在被调用的移动构造/赋值里。`std::forward<T>` 用于完美转发，保持实参的值类别。
移动构造应尽量 `noexcept`，否则 `std::vector` 扩容时可能退回拷贝（`move_if_noexcept`）；C++17 对纯右值返回有强制拷贝消除。C 没有移动语义，`memcpy` 或指针交换是手动「移动」，浅拷贝后源对象仍需正确清理，容易 double free。

```cpp
class Vec {
    int *p_ = nullptr;
    std::size_t n_ = 0;
public:
    Vec(Vec &&o) noexcept : p_(o.p_), n_(o.n_) { o.p_ = nullptr; o.n_ = 0; }
    Vec &operator=(Vec &&o) noexcept;   // 释放自身，接管 o 的资源
};
std::vector<Vec> v;
v.push_back(Vec{});                     // 移动而非深拷贝
```
### 5.7 对象布局与虚函数表
C 的 struct 成员按声明顺序排列（中间可能有 padding），`offsetof` 可测偏移；没有隐藏成员，标准布局且 trivially copyable 的对象可以 `memcpy`。
C++ 的多态对象通常含一个隐藏的 vptr（常见在对象开头），指向该类的 vtable；vtable 是函数指针数组，按槽位保存虚函数地址，通常还带 RTTI 信息。每个对象多一个指针，每次虚调用多一次间接跳转。
多重继承可能产生多个 vptr 和 this 指针调整，虚继承更复杂；空基类优化、`final` 去虚化、LTO 都可能改变布局和调用方式。对象布局不是标准 ABI，不要跨编译器/语言直接读写对象内存。
非虚类不一定有 vptr；标准布局类型可以 `memcpy`，含虚函数或非平凡成员的类型不能。C 可以手动模拟：结构体第一个成员放函数指针表，析构和类型识别全部手写。

```cpp
struct Shape {
    virtual ~Shape() = default;
    virtual double area() const = 0;
};
struct Circle : Shape {
    double r;
    double area() const override { return 3.14159 * r * r; }
};
// 对象通常含 vptr；vptr[slot] -> Circle::area
```

## 6 结构体与类
### 6.1 从 struct 到 class
| 维度 | C struct | C++ class/struct |
| --- | --- | --- |
| 成员函数 | 无 | 有 |
| 访问控制 | 无，全部公开 | public/private/protected |
| 默认访问 | — | class 默认 private，struct 默认 public |
| 默认继承 | — | class 默认 private，struct 默认 public |
| 构造/析构 | 手动 init/destroy | 自动调用 |
| 继承/多态 | 无，可手动函数指针表 | 支持 |
| 类型名 | `struct Foo`，常配合 typedef | `Foo` 直接可用 |

C++ 里 `struct` 和 `class` 只差默认访问和默认继承；两者都可以有虚函数、构造、模板成员。习惯上纯数据聚合用 struct，有不变式或接口的用 class。
C 的 struct 是「内存布局 + 标签」，C++ 的 class 是「布局 + 行为 + 访问约束」；`sizeof`、标准布局、trivially copyable 仍会影响能否安全 memcpy 或跨语言传递。
### 6.2 访问控制与封装
`private` 是编译期检查，不是安全边界；`friend` 可访问私有成员，`protected` 对派生类开放。C 用不透明指针隐藏实现：头文件只给 `typedef struct Foo Foo;`，实现在 .c 中定义，调用方只能拿指针；C++ 用 pimpl 或 private 成员达到类似效果。
### 6.3 继承与多态
`virtual` 成员函数动态绑定；纯虚函数 `= 0` 使类成为抽象类；`override` 让签名写错时编译失败；`final` 禁止继续重写或继承。基类指针/引用可指向派生类，虚调用按动态类型；按值传递/赋值基类会发生对象切片，必须用引用或指针。
多继承、虚继承、菱形问题会引入指针调整和布局复杂度；`dynamic_cast`/`typeid` 需要 RTTI；多态基类必须有虚析构。C 没有继承，只能用「基类作为第一个成员 + 函数指针表」模拟，并手动维护类型标签。

```cpp
class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const = 0;   // 纯虚：抽象类
};
class Circle final : public Shape {
public:
    explicit Circle(double r) : r_(r) {}
    double area() const override { return 3.14159 * r_ * r_; }
private:
    double r_;
};
```

## 7 错误处理
### 7.1 C 的返回码与 errno
C 通常用返回值表示错误（0、NULL、-1），输出参数带回结果；`errno` 是线程局部的错误码，成功调用不会自动清零，必须在失败后立刻保存/检查。`perror`、`strerror(errno)` 可转成文本；`ferror` 检查流；系统调用常返回 -1 并设置 errno，但后续库调用可能覆盖它。
错误码可被忽略，深层调用需要层层转发，容易丢上下文；优点是零异常、ABI 简单，适合内核、嵌入式、跨语言接口。

```c
int rc = read(fd, buf, n);
if (rc < 0) {
    int err = errno;
    fprintf(stderr, "read: %s\n", strerror(err));
    return -1;
}
```

### 7.2 C++ 异常
`throw` 可抛出任意类型，建议继承 `std::exception`；栈展开会自动调用局部对象析构，这是 RAII 能保证异常安全的关键。`catch` 按类型匹配，建议 `catch (const std::exception &e)` 避免切片，`catch (...)` 兜底后常需 rethrow。异常安全通常分基本保证、强保证和不抛保证，RAII 是共同基础。
构造函数抛异常时，已构造的基类和成员会析构，对象本身不析构；析构函数默认 noexcept，异常逃出析构会 terminate。异常不适合无异常支持的环境（`-fno-exceptions`）、跨 C ABI、硬实时/高可靠场景以及频繁的「预期失败」；适合构造函数失败、运算符重载、深调用链等无法返回错误码的场合。

| 维度 | 错误码/errno | 异常 |
| --- | --- | --- |
| happy path 开销 | 小 | 常见实现零开销（表驱动），代码尺寸增大 |
| 错误传播 | 每层手动检查 | 自动沿栈传播 |
| 忽略风险 | 容易 | 未捕获会终止，不易静默 |
| 资源清理 | goto cleanup/手动 | 栈展开 + RAII 自动 |
| 构造函数 | 只能 init 后检查 | 构造函数可直接抛 |
| 跨 C ABI | 天然兼容 | 不能穿越 C 边界 |
| 实时/嵌入式 | 更可控 | 延迟/空间不确定，常禁用 |
### 7.3 noexcept
`noexcept` 承诺函数不抛异常，违反则 `std::terminate`，编译器不保证逐路径检查；`noexcept(expr)` 可按条件声明，C++17 起它是函数类型的一部分。
移动构造/移动赋值、`swap`、析构函数通常应 noexcept；标准容器扩容依赖它决定 move 还是 copy。C 没有异常规格，`noexcept` 是 C++ 特有的契约；旧的 `throw()` 已废弃/移除。C++23 的 `std::expected<T, E>` 把错误码风格带回类型系统，`[[nodiscard]]` 可提醒调用方检查返回值。

## 8 标准库与惯用法
### 8.1 C 标准库在 C++ 中的对应
| C 头 | C++ 头 | 说明 |
| --- | --- | --- |
| `<stdio.h>` | `<cstdio>` | `std::printf`，通常也保留全局 `printf` |
| `<stdlib.h>` | `<cstdlib>` | `std::malloc/free`、`std::exit` |
| `<string.h>` | `<cstring>` | `std::strlen/memcpy` |
| `<math.h>` | `<cmath>` | `std::sqrt`，对浮点类型有重载 |
| `<stdint.h>` | `<cstdint>` | `std::int32_t` 等 |
| `<stddef.h>` | `<cstddef>` | `std::size_t`、`std::nullptr_t` |

C++ 标准库头把名字放进 `std`，C 头保留全局名字；新代码优先 `<c*>`，但 C 兼容代码和第三方库常用 `<*.h>`。`<stdbool.h>` 在 C++ 中基本无意义，因为 `bool` 是关键字；跨标准时以编译器文档为准。
### 8.2 std::string vs char[]
`std::string` 自管理内存（RAII），记录 size/capacity，可动态增长；`c_str()` 返回以 `\0` 结尾的只读视图，`at()` 越界检查，`[]` 不检查。C 的 `char[]` 长度固定，需要手动保证 `\0`，`strcpy/strcat` 容易溢出；`char*` 不携带长度，函数签名常丢 size。
`std::string_view`（C++17）是非拥有只读视图，可切片，适合只读参数；但它不保证 `data()` 以 `\0` 结尾（从指针+长度构造时），也不能返回指向局部 string 的 view。
### 8.3 std::vector vs 数组
`std::vector<T>` 连续存储、自动扩容（常见 1.5 或 2 倍）、RAII、有 size；扩容会使指针、迭代器、引用失效，提前 `reserve` 可避免。C 数组 `T a[N]` 长度编译期固定（VLA 是 C99 可选，C++ 不支持），传参退化为指针并丢失长度；`malloc` 数组要手动 free。
固定长度优先 `std::array<T, N>`（栈上、不退化、有 begin/end），只读视图用 `std::span`（C++20）；`vector<bool>` 是位压缩特化，不要当普通 `vector` 用。
### 8.4 迭代器与范围 for
迭代器是容器和算法之间的泛型接口，分输入、前向、双向、随机访问、连续等类别；`begin()/end()` 是半开区间，`end()` 不指向元素。
范围 for 展开为 `auto &&__r = range; for (auto it = begin(__r); it != end(__r); ++it)`；`auto x` 拷贝，`auto &x` 可修改，`const auto &x` 只读且避免拷贝。遍历时修改容器可能使迭代器失效，删除元素用 `it = v.erase(it)`，C++20 有 `std::erase_if`。

```cpp
std::vector<int> v{1, 2, 3};
for (const auto &x : v) std::cout << x << ' ';
for (auto it = v.begin(); it != v.end(); ) {
    if (*it % 2 == 0) it = v.erase(it);
    else ++it;
}
```
### 8.5 C 风格代码在 C++ 中的坑
- `void*` 不能隐式转 `T*`：`int *p = malloc(sizeof(int));` 在 C++ 编译失败，需要显式转换或改用 `new`/容器。
- `malloc/free` 不调用构造/析构：对 `std::string` 等非平凡类型用 `malloc` 是 UB；需要裸内存时用 `operator new` + placement new。
- C 的 `restrict`、VLA、复合字面量、`_Generic`、K&R 函数定义在标准 C++ 中不存在；GNU 扩展可编译但不便携。
- C 的 `f()` 表示参数未指定，C++ 的 `f()` 表示无参数，跨语言头文件统一写 `f(void)`；C 的文件作用域 `const` 默认外部链接，C++ 默认内部链接。

## 9 常见坑与面试追问
### 9.1 char* 字面量到 const char*
C 的字符串字面量类型是 `char[N]`，可写属于历史遗留，修改内容仍是 UB；C++ 中类型是 `const char[N]`，`char *p = "abc";` 从 C++11 起 ill-formed。统一写 `const char*`；需要修改就拷贝到数组或 `std::string`；`string_view` 不拥有数据，注意生命周期。
### 9.2 数组退化
数组在大多数表达式和函数参数中退化为首元素指针；`sizeof(arr)` 是数组字节数，`sizeof(p)` 是指针大小；函数参数 `int a[10]` 的实际类型是 `int*`。C++ 可用 `std::array`、`std::span`、模板 `template<size_t N> void f(int (&a)[N])` 保留长度；C 用额外的 size 参数或结构体封装。

```cpp
void f(int a[10]) { /* a 的类型是 int*，不是 int[10] */ }
template <std::size_t N>
void g(int (&a)[N]) { /* N 已知 */ }
```
### 9.3 隐式转换风险
C 的隐式转换更宽：`void*` 与对象指针互转、整数与指针互转（通常只是警告）、枚举与 int 互转、double 转 int；C++ 收紧了部分规则，但仍保留数值转换、派生类到基类（切片）、`const char*` 到 `std::string`、`operator bool` 等。用 `explicit` 阻止单参构造和转换运算符的隐式转换；`-Wconversion -Wsign-conversion` 暴露窄化；C++11 列表初始化禁止窄化。常见 bug：`int` 与 `size_t` 比较、`-1` 转 `unsigned`、浮点超出目标整数范围（UB）、指针直接转 `bool`。
### 9.4 delete 与 delete[]
`new[]` 必须配 `delete[]`，`new` 必须配 `delete`；混用是 UB，可能只析构第一个元素或破坏堆。`delete[]` 通常逆序析构数组元素，再释放内存；内置类型可能不调用析构，但仍必须匹配。用 `std::vector` 或 `std::unique_ptr<T[]>` 避免手写；`delete nullptr` 安全，重复 delete 不安全。
### 9.5 sizeof 差异
字符常量：C 中 `sizeof('a') == sizeof(int)`，C++ 中 `sizeof('a') == sizeof(char)`，这是常考差异。空 struct 在 C 中不是标准写法（GCC 扩展常给 0/1），C++ 空类 `sizeof` 至少为 1；含虚函数会多 vptr，多重继承和空基类优化会改变布局。`sizeof(bool)`、`sizeof(long)`、指针大小由实现决定；`sizeof` 数组得到总字节数，`sizeof` 指针得到指针大小，`sizeof` 引用得到被引用类型大小；C 的 VLA 在运行时求值。不要用 `sizeof(struct)` 做序列化或网络协议，使用固定宽度类型和显式序列化。
### 9.6 C 的 restrict vs C++
C 的 `restrict` 是程序员承诺：在指针生命周期内，对象只通过该指针及其派生指针访问，编译器可据此优化，违反是 UB。C++ 标准没有 `restrict`，可用编译器扩展 `__restrict`/`__restrict__`；引用不提供非别名保证，`const` 也不保证。严格别名规则、`std::launder`、`memcpy` 是相关但不同的话题，不要以为 `T&` 就没有别名。

## 10 面试问答 15 题
### Q1 C++ 为什么兼容 C？兼容的边界在哪？
- 兼容 C 是为了复用庞大的 C 代码、库和 ABI，降低迁移成本，也让 C++ 能直接做系统编程。
- 但 C++ 不是严格超集：`void*` 隐式转换、VLA、`restrict`、`_Generic`、复合字面量、`char*` 字符串字面量等都不合法。
- 交叉部分应写成两种语言都能编译的头文件，跨边界用 `extern "C"` 和 C 兼容类型。
### Q2 extern "C" 的作用是什么？为什么头文件要 #ifdef __cplusplus？
- 它指定 C 语言链接，关闭 C++ 名字修饰，让 C++ 按 C 符号名查找/生成函数。
- C 编译器不认识 `extern "C"`，所以用 `__cplusplus` 只在 C++ 编译时包住这段声明。
- 同一份头文件因此既能给 C 编译器，也能给 C++ 编译器；C++ 侧看到的是 C ABI。
### Q3 C++ 如何调用 C 库？C 代码如何调用 C++？
- C++ 调 C：C 代码用 C 编译器编库，C++ 侧包含声明并保证 C 链接，链接时加 `-l`。
- C 调 C++：C++ 侧写 `extern "C"` 导出函数，只暴露 C 兼容类型，异常在边界内捕获并转错误码。
- C++ 对象用不透明指针隐藏；链接 C++ 库时注意 libstdc++ 和编译器 ABI。
### Q4 new/delete 和 malloc/free 的区别？
- `new` 分配内存并调用构造函数，返回 `T*`，失败默认抛 `bad_alloc`；`delete` 先析构再释放。
- `malloc` 只分配字节，返回 `void*`，失败返回 NULL；`free` 只释放，不调用构造/析构。
- 两者不能混用，`new[]` 必须配 `delete[]`；C++ 中优先 `new`/容器/智能指针。
### Q5 RAII 解决什么问题？
- 把资源生命周期绑定到对象生命周期：构造获取，析构释放，提前 return 和异常展开都能自动清理。
- 解决 C 中手动 free/close/unlock 容易漏掉、错误路径难覆盖的问题。
- `unique_ptr`、`lock_guard`、`fstream` 都是典型例子，通常没有额外运行时开销。
### Q6 虚函数怎么实现？基类析构为什么要是 virtual？
- 多态对象通常含 vptr，指向类的 vtable；虚表按槽位存函数地址，虚调用通过 vptr 间接跳转。
- 每个类一张虚表，每个对象一个 vptr；多重继承还涉及 this 指针调整。
- 基类析构非 virtual 时，`delete base_ptr` 只析构基类部分，派生类资源泄漏，行为未定义。
### Q7 什么时候用 C 不用 C++？
- 工具链受限、无 C++ 运行时、需要 freestanding、内核/驱动/RTOS 等环境。
- 需要稳定 C ABI、极小程序体积、确定性延迟，或团队/历史代码只接受 C。
- C 的简单性便于审计和移植；但「性能够不够」通常不是选 C 的理由，C++ 也能做到零开销。
### Q8 C 的 struct 和 C++ 的 class/struct 有什么区别？
- C struct 只有数据，没有成员函数、访问控制、继承、构造/析构，类型名常需 `struct` 或 typedef。
- C++ 的 class/struct 只差默认访问和默认继承：class 默认 private，struct 默认 public。
- C++ struct 也能有方法、虚函数、构造；纯数据仍常用 struct，有不变式的接口常用 class。
### Q9 nullptr、NULL、0 有什么区别？
- C 中 `NULL` 是实现定义的 null 指针常量，常为 `0` 或 `((void*)0)`；C23 才有 `nullptr`。
- C++11 的 `nullptr` 类型是 `std::nullptr_t`，可转任意指针/成员指针，不会像 `NULL` 那样被当作整数，重载和模板推导更明确。
- `f(NULL)` 可能误选 int 重载，`f(nullptr)` 选指针；C++ 一律优先 `nullptr`。
### Q10 四种 cast 和 C 风格强转有什么区别？
- C 风格 `(T)x` 会尝试 const_cast、static_cast、reinterpret_cast 的组合，可能悄悄去 const 或做危险转换。
- `static_cast` 用于相关类型，`const_cast` 只改 cv，`reinterpret_cast` 按位重解释，`dynamic_cast` 做带 RTTI 的安全向下转换。
- C++ cast 意图明确、可 grep、编译期更容易发现问题；新代码避免 C 风格强转。
### Q11 移动语义解决什么？std::move 做了什么？
- 解决临时对象/即将销毁对象的深拷贝浪费，把堆资源「偷」过来，降低分配和复制成本。
- `std::move` 只是把表达式转成右值引用的 cast，本身不移动；移动发生在移动构造/赋值中。
- 移动后源对象有效但未指定；移动构造应尽量 `noexcept`，否则容器扩容可能退回拷贝。
### Q12 函数重载底层怎么实现？为什么 extern "C" 不能重载？
- C++ 用 name mangling 把命名空间、类、参数类型编码进符号，链接器才能区分同名函数。
- 重载解析在编译期完成，返回类型不参与；默认参数不改变函数签名。
- `extern "C"` 关闭修饰，同名函数会产生同一个 C 符号，无法共存，所以不能重载。
### Q13 异常和错误码怎么选？noexcept 有什么用？
- 错误码适合预期内的频繁失败、跨 C ABI、嵌入式和硬实时；异常适合构造失败、深调用链和无法返回错误码的场合。
- 异常自动栈展开并配合 RAII 清理，但有代码尺寸/延迟不确定性，且不能穿越 C 边界。
- `noexcept` 承诺不抛，违反会 terminate；移动构造、swap、析构常标 noexcept，便于容器优化。
### Q14 C 的字符串和数组在 C++ 中有哪些坑？
- 字符串字面量在 C++ 是 `const char[N]`，不能赋给 `char*`；修改字面量是 UB。
- 数组传参退化为指针，`sizeof` 得到指针大小；用 `std::array`、`std::span` 或数组引用保留长度。
- `malloc` 不调用构造，`void*` 不能隐式转 `T*`；C 的 VLA、`restrict`、`_Generic` 在标准 C++ 中不可用。
### Q15 C++ 对象布局和 C 结构体布局有什么差异？
- C struct 只按成员顺序和 alignment 排布；C++ 多态类通常多一个 vptr，多重继承还可能有多个 vptr 和指针调整。
- C++ 有访问控制、空基类优化、`final` 去虚化等，布局不是标准 ABI，不能假定和 C 结构体一致。
- 只有标准布局且 trivially copyable 的类型才适合 `memcpy`；跨语言传递用不透明指针和显式序列化。
