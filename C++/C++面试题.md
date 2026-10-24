# C++ 面试题（60 道）

> 配套《C++ 笔记》（`_source_Cpp.md`）的自测题库，覆盖存储类、类与对象、继承、重载、多态、模板、异常、动态内存、命名空间、STL、线程，并补到 C++11—20 的现代特性。
> 按主题分八节、编号连续；每题只给面试现场能说出口的 3~6 条要点：先结论、再说原理、最后补一句「面试官想听的追问点」。

## 目录

- 一、语言基础（8 题，Q1–Q8）
- 二、类与对象（12 题，Q9–Q20）
- 三、继承与多态（8 题，Q21–Q28）
- 四、内存与资源管理（10 题，Q29–Q38）
- 五、模板与泛型（7 题，Q39–Q45）
- 六、现代 C++（C++11—20，10 题，Q46–Q55）
- 七、STL 与算法（8 题，Q56–Q63）
- 八、并发编程（7 题，Q64–Q70）

建议遮住答案自测：能一句话给出结论且说清边界，就算过关。

## 一、语言基础

### Q1 值传递、引用传递、指针传递怎么选？
**答**：
- 结论先行：**只读的小类型按值传，只读的大对象传 `const T&`，需要改调用方就传 `T&`；只有「可能为空」「要记录地址」「要兼容 C 接口」时才用指针**。
- 值传递拷一份副本，改不到外面，好处是天然线程安全、不用担心别名；代价是拷贝开销，`std::string`、`std::vector` 这类大对象尽量别按值传。
- 引用说到底是「不能为空、不能换绑的指针」，语法干净，但它在类型层面就没了空值信息；指针可以写 `nullptr`、可以 `++`、可以放进容器。
- 边界：引用形参对调用方是透明的（调用点看不出会被改），所以写 `void f(T& out)` 时函数名最好暗示「会改」，头文件里也可以加 `[[maybe_unused]]` 之类注释约束。
- 追问点：const 引用能绑临时对象可延长生命周期，指针没这个能力；C++17 起大对象返回值直接走返回值优化或移动，别再写「用指针输出参数避免拷贝」这种老套路。

### Q2 `struct` 和 `class` 的区别？
**答**：
- 标准原文只有一条区别：**默认访问权限和默认继承方式**，`struct` 默认 `public`、`class` 默认 `private`；其余能力完全一样（构造、析构、虚函数、继承、模板都支持）。
- 用法上形成惯例：纯数据聚合用 `struct`（可以配聚合初始化 `Point p{1, 2};`），有封装和不变量要做维护用 `class`。
- 边界：一旦给 `struct` 写了自定义构造函数，它就不再是聚合类型，`{...}` 初始化会走构造函数；反过来 `class` 加 `public:` 也能当聚合体。
- 追问点：`struct` 也可以有虚函数（有 vptr 大小就变了）；名字查找、内存布局跟 `class` 没有任何差别。

### Q3 构造函数和析构函数的调用顺序？
**答**：
- 构造顺序：**基类 → 成员变量（按声明顺序，不是初始化列表顺序）→ 构造函数体**；析构顺序正好相反：**函数体 → 成员逆序 → 基类**。
- 所以「先声明后初始化」这句口诀是对的：初始化列表里的书写顺序不影响实际顺序，成员互相依赖时顺序错了会读到未初始化值。
- 例子：`struct A { int a; int b; A() : b(1), a(b) {} };` 里 `a` 先被初始化，读到的 `b` 还是未初始化的，这是 UB，编译器会报 `-Wreorder`。
- 边界：全局和静态对象的构造在 `main` 之前、析构在 `main` 之后，跨编译单元的顺序未定义（静态初始化顺序问题，用函数内局部 static 才能顺序确定）。
- 追问点：数组按元素顺序构造、逆序析构；构造抛异常时已构造完成的成员和基类仍会被正确析构，但该对象的析构函数不会调用。

### Q4 拷贝构造函数和赋值运算符有什么区别？什么时候必须自己写？
**答**：
- 拷贝构造是**创建新对象**时用已有对象初始化（`T b(a);`、`f(a)` 按值传参、`return a;`），赋值运算符是**两个已存在对象**之间覆盖（`b = a;`）。
- 自己写这两个时的固定套路：拷贝构造要分配自己的资源再拷贝内容；拷贝赋值要先处理**自赋值**、再释放旧资源、再拷贝，最省心的写法是 copy-and-swap。
- 必须自己写的典型信号：类里持有裸指针、`FILE*`、句柄、锁这类资源；否则会双重释放。
- 参数为什么传 `const T&`：按值传会递归调用拷贝构造；返回为什么是 `T&`：支持 `a = b = c` 连续赋值。
- 追问点：拷贝赋值要检查 `this == &other`；返回 `*this` 而不是值；`= delete` 可以显式禁止拷贝（C++11 起）。

```cpp
class Buffer {
public:
    Buffer(size_t n) : data_(new char[n]), size_(n) {}
    Buffer(const Buffer& o) : data_(new char[o.size_]), size_(o.size_) {
        std::memcpy(data_, o.data_, size_);
    }
    Buffer& operator=(const Buffer& o) {
        if (this != &o) {
            Buffer tmp(o);          // 先做一份副本，异常安全
            std::swap(data_, tmp.data_);
            std::swap(size_, tmp.size_);
        }
        return *this;
    }
    ~Buffer() { delete[] data_; }
private:
    char* data_;
    size_t size_;
};
```

### Q5 深拷贝和浅拷贝的区别？
**答**：
- 浅拷贝只复制指针值（两个对象指向同一块堆内存），编译器默认生成的拷贝构造/赋值就是逐成员的浅拷贝；深拷贝会重新分配一块内存再复制内容。
- 后果：持有裸指针的类做浅拷贝，两个对象析构时 `delete` 同一块内存就是 double free；改一个对象另一个也跟着变，违反值语义。
- 判断标准：**类型有没有「所有权」**。有所有权就必须深拷贝（或干脆用 `unique_ptr`/`shared_ptr`/规则三，让所有权自己说清楚）。
- 选择建议：拷贝廉价用值语义（如 `std::string`、`std::vector`），共享访问可以故意用 `shared_ptr` 做浅拷贝，但要在文档里写清是「共享」而不是「复制」。
- 追问点：移动语义是把资源**转移**过去而不是复制，源对象要置为有效但可析构的状态，这是浅拷贝之后不再 double free 的关键。

### Q6 `static` 关键字有哪几种用法？
**答**：
- 修饰局部变量：存储期变静态，只初始化一次、值跨调用保留，但作用域仍在块内；C++11 起局部 static 初始化是线程安全的。
- 修饰全局变量或函数：内部链接，只在本翻译单元可见，用来隐藏符号、避免多文件重名。
- 修饰类的成员变量：属于类不属于对象，所有对象共享一份，**必须在类外定义**（C++17 起可以 `inline static` 就地定义）。
- 修饰类的成员函数：没有 `this`、不能访问非静态成员、不能是 `const` 也不能是 `virtual`。
- 追问点：静态成员的生命周期是「首次使用到程序结束」，析构发生在 `main` 之后；单例最经典实现就是函数内 `static` 局部对象；`thread_local static` 每个线程一份。

```cpp
struct Counter {
    static int total;                  // 类内声明
    static Counter& instance();        // 单例：C++11 起初始化线程安全
    int id;
    static int nextId() { return ++total; }   // 不能访问 id
};
int Counter::total = 0;                // 类外定义
```

### Q7 `const` 成员函数有什么意义？
**答**：
- `T f() const` 承诺不修改对象：函数体内 `this` 是 `const T*`，成员变量变成只读，编译器逐字段检查。
- 它能被 **const 对象和 const 引用调用**，所以「传 `const T&`」的 API 能不能用好，取决于成员函数是不是 `const`——这是 const 正确性最实际的价值。
- 重载：可以同时提供 `T& get()` 与 `const T& get() const`，编译器按对象本身的 const 性质选版本（`std::vector::operator[]` 就是这样）。
- 例外：`mutable` 成员在 const 函数里可以改，典型用途是缓存、引用计数、互斥锁；`std::atomic` 的 `load` 也是 const 的。
- 追问点：const 成员函数里返回内部成员指针/引用会「泄露 const」，要返回 `const T*`；`const` 是接口的一部分，`const T f()` 顶层 const 会被忽略，别乱加。

```cpp
class Cache {
public:
    int value() const {                 // 可被 const Cache& 调用
        if (!cached_) { v_ = compute(); cached_ = true; }
        return v_;
    }
private:
    int compute() const { return 42; }
    mutable int v_ = 0;                 // 缓存是「逻辑不变」的
    mutable bool cached_ = false;
};
```

### Q8 友元和命名空间：`friend` 该不该用？匿名命名空间为什么比 `static` 好？
**答**：
- `friend` 让外部函数/类/成员函数访问本类私有成员，**是单向的、不继承、不可传递**；典型场景是运算符重载（`operator<<`）、两个类强耦合的工厂函数、单元测试访问内部状态。
- 为什么不直接写 `public`：友元只放行「某一个」函数，暴露面比全公开小得多，而且不需要 `getter/setter` 污染接口。
- 代价：友元声明写在被访问类的头文件里，会加大头文件耦合；友元声明本身也是接口的一部分，是「测试私有实现」被滥用的重灾区。
- 命名空间层面：匿名命名空间等价于内部链接（C++11 起 `static` 只能用在这），但匿名命名空间能包住整个类模板，还能做 ADL 相关限制，所以现代代码用它代替 `static` 隐藏 TU 内符号。
- 追问点：`using namespace std;` 不要写在头文件里；`inline namespace` 用来做库版本化；ADL（参数相关查找）会让 `operator<<` 被自动找到。

```cpp
namespace {
int helper(int x) { return x * 2; }    // 只对本翻译单元可见
}

class Vec {
    friend std::ostream& operator<<(std::ostream& os, const Vec& v);
public:
    Vec(int x, int y) : x_(x), y_(y) {}
private:
    int x_, y_;
};
std::ostream& operator<<(std::ostream& os, const Vec& v) {
    return os << '(' << v.x_ << ',' << v.y_ << ')';
}
```

## 二、类与对象

### Q9 构造函数有哪些种类？什么是「初始化列表」，为什么优先用它？
**答**：
- 种类：默认构造、带参构造、拷贝构造、移动构造、委托构造（`A() : A(0) {}`）、`explicit` 转换构造；`= default` / `= delete` 可以显式要或不要。
- 初始化列表是**真正的初始化**，函数体里的赋值是「先默认构造再赋值」，对 `const` 成员、引用成员、无默认构造的成员只能在列表里初始化。
- 顺序坑：实际初始化顺序按**声明顺序**，列表顺序写反会读到未初始化值，编译器的 `-Wreorder` 能抓。
- `explicit` 是为了禁止隐式转换：`explicit A(int)` 之后 `void f(A); f(1);` 不再编译，`std::vector<int> v(10)` 和 `v = 10` 这类重载歧义也能避开。
- 追问点：`A a = A(1);` 在 C++17 起见不到临时对象（guaranteed copy elision）；委托构造只能有一个委托目标且不能形成环。

```cpp
class Widget {
public:
    explicit Widget(int id) : id_(id), name_("w"), ref_(id_) {}
    // 声明顺序 id_ → name_ → ref_，列表顺序也必须一致
private:
    int id_;
    std::string name_;
    int& ref_;
};
```

### Q10 拷贝构造在哪些场景会被调用？编译器什么时候自动生成、什么时候不生成？
**答**：
- 触发场景：`T b(a);`、`f(a)` 按值传参、`return a;`（未触发优化时）、`v.push_back(a)` 扩容搬移、`T b = a;` 这句是拷贝构造而不是赋值。
- 编译器自动生成的拷贝构造做逐成员拷贝（基类、成员、数组成员逐个走各自的拷贝构造），它不负责深拷贝。
- C++11 起只要写了移动构造/移动赋值/拷贝赋值/析构，拷贝构造就不再自动生成（老规则是写了析构也不生成拷贝构造，会退化成逐成员拷贝——这是个陷阱）。
- 规则三/五/零：要么全都自己写，要么一个不写，靠智能指针和 RAII 成员把所有权管起来。
- 追问点：`std::vector` 扩容时优先用移动构造（前提是 `noexcept`），否则为了强异常安全会退化成拷贝，所以移动构造一定加 `noexcept`。

### Q11 什么是移动构造与移动赋值？它只是「提升性能」吗？
**答**：
- 移动构造 `T(T&&)` 和移动赋值 `T& operator=(T&&)` 接管源对象的资源（指针、缓冲区），把源置成空壳；它不是性能优化，而是**所有权转移**的语义。
- 典型实现：成员申请的资源直接 `std::move` 过去，块内的临时对象不再被复制，`std::vector<std::string>` 的扩容成本从 O(n) 次深拷贝变成 O(n) 次指针搬运。
- 编译器只在你**没有**声明拷贝操作和析构的情况下自动生成移动操作；自己写了拷贝构造就会失去隐式移动。
- 移动后的对象必须是「有效但未指定状态」，只能析构或重新赋值，不能假设它还是原值。
- 追问点：move 构造要标 `noexcept`；`std::string` 短则 SSO 复制、长则指针转移，所以大字符串才明显加速；C++11 之后返回值多用移动+NRVO，`ctor` 次数别作为性能指标。

```cpp
class Buffer {
public:
    Buffer(Buffer&& o) noexcept
        : data_(o.data_), size_(o.size_) {
        o.data_ = nullptr;
        o.size_ = 0;
    }
    Buffer& operator=(Buffer&& o) noexcept {
        if (this != &o) {
            delete[] data_;
            data_ = o.data_; size_ = o.size_;
            o.data_ = nullptr; o.size_ = 0;
        }
        return *this;
    }
    ~Buffer() { delete[] data_; }
private:
    char* data_ = nullptr;
    size_t size_ = 0;
};
```

### Q12 什么是运算符重载？哪些运算符不能重载？为什么 `operator=` 要返回引用？
**答**：
- 允许把绝大多数运算符定义成成员函数或非成员（全局）函数，签名为 `operator` 加运算符号；目的是让自定义类型用起来像内置类型。
- 不能重载：`.`、`::`、`?:`、`sizeof`、`typeid`、`alignof`、`.*`、`#`、`##`；不能改优先级、结合性、操作数个数，也不能发明新运算符。
- 必须做成员的：`=`、`[]`、`()`、`->`、`->*`；二元运算符通常做成友元非成员，这样左右操作数都能走隐式转换（`cout << x` 而不是 `x << cout`）。
- `operator=` 返回 `*this` 的引用，是为了支持 `a = b = c` 链式赋值，也和内置类型的语义一致。
- 追问点：`operator+` 常写成非成员的 `operator+(T, const T&)`，配合移动能少一次拷贝；`operator<<` 一定返回 `ostream&` 才能连写。

```cpp
struct Money {
    long long cents = 0;
    explicit Money(long long c) : cents(c) {}
    Money& operator+=(const Money& o) { cents += o.cents; return *this; }
    friend Money operator+(Money a, const Money& b) { return a += b; }
    bool operator==(const Money& o) const = default;   // C++20
    friend std::ostream& operator<<(std::ostream& os, const Money& m) {
        return os << m.cents / 100.0;
    }
};
```

### Q13 为什么要禁止编译器自动生成的函数？`= delete` 和 `= default` 怎么用？
**答**：
- 自动生成的拷贝构造/赋值做浅拷贝，对有资源的类就是 bug 源头；显式 `= delete` 能在编译期把它变成硬错误，比运行期崩掉好查。
- `= delete` 还可以用在任何函数上：删掉某个重载（如 `void f(int) = delete;`）、禁止将某类型隐式转换（`explicit` 不够时）。
- `= default` 表示「让编译器按默认规则生成」，好处是保留 `trivial` 属性（可 `memcpy`、可当 `union` 成员、可传 POD 接口），又让意图清晰。
- 典型：模板参数被派生类继承时用 `using Base::operator=`；在公有接口里 `= delete` 掉隐式转换构造函数。
- 追问点：`= delete` 的删除函数仍**参与重载决议**，删除后报错更精确；`= default` 若不可用会被隐式删除（比如有引用成员和 `const` 成员时拷贝赋值就没了）。

```cpp
class File {
public:
    explicit File(const char* path);
    File(const File&) = delete;             // 句柄不可拷贝
    File& operator=(const File&) = delete;
    File(File&&) noexcept = default;        // 但可以移动
    File& operator=(File&&) noexcept = default;
    ~File() = default;
private:
    FILE* fp_ = nullptr;
};
```

### Q14 构造函数能是虚函数吗？为什么不能？析构函数为什么必须是虚的？
**答**：
- 不能是虚函数：虚函数要靠对象里的 vptr 找到，而构造之前对象的 vptr 还没建立完，「刚出生就要靠状态查表」是鸡生蛋问题；构造过程中 `this` 的动态类型只到当前正在构造的类。
- 那怎么做到「多态创建」？答案是虚工厂/工厂函数：`static std::unique_ptr<Base> create(int type)`，内部 `switch` 返回派生类。
- 基类析构函数应当是虚的：`Base* p = new Derived; delete p;` 只有虚析构才能先调 `~Derived()` 再调 `~Base()`，否则派生类成员泄漏。
- 规则细化：只要类打算被继承并且可能通过基类指针删除，就必须 `virtual ~Base() = default;`；反之 final 类不加，省掉 vptr 和开销。
- 追问点：构造函数里调用虚函数只会调到当前类版本，不会多态；`Base` 析构开始后 vptr 已被改回 `Base`，此时再调虚函数也退化。

### Q15 什么是委托构造和继承构造？C++11 之后类构造有什么新写法？
**答**：
- 委托构造：`A() : A(0, 0) {}`，一个构造函数把初始化工作交给另一个，避免重复写初始化逻辑，配合默认实参更省事。
- 继承构造：`using Base::Base;` 把基类构造函数「搬」进派生类，派生类不额外加成员时就不用挨个转发参数。
- 类内成员默认值（`int x_ = 0;`）也是 C++11 起的写法，相当于给所有构造函数兜底默认初始化，优先写这个而不是在初始化列表里重复。
- 注意继承构造不会继承默认构造、拷贝构造、移动构造，派生类自己还是要有默认构造。
- 追问点：委托构造的执行顺序仍是先构造委托目标再回到原先函数体；`using Base::Base` 遇上派生类新增成员需要初始化时，得再写一个自己的构造函数。

```cpp
struct Base {
    int x, y;
    Base(int x, int y = 0) : x(x), y(y) {}
};

struct Derived : Base {
    using Base::Base;          // 继承 Base(int, int)
    int z = 0;                 // 新增成员用默认值
    Derived() : Derived(1, 2) {}   // 委托构造
};
```

### Q16 `this` 指针是什么？什么时候会用到它？
**答**：
- `this` 是成员函数里隐含的指针，指向当前对象，类型是 `T*`（const 函数里是 `const T*`），由编译器作为隐含参数传入，存在寄存器里而通常不占额外存储。
- 主要用途：解决形参和成员同名（`this->name = name;`）、链式调用返回 `*this`、在成员函数里传自身给外部（`self_ = this;`）、`delete this;`（慎用）。
- 不能对 `this` 取地址、赋值，它是 const 指针；在 `this` 上调用虚函数会正常多态。
- `delete this;` 的边界：必须是 `new` 出来的对象、之后不能再访问任何成员，典型用于自引用计数或 `Release()` 模式，极容易出事。
- 追问点：`this` 在构造函数里可用但对象还不完整，别把 `this` 交给别的线程；`std::enable_shared_from_this::shared_from_this()` 比 `new shared_ptr(this)` 安全，因为后者会二次析构。

### Q17 什么是友元类、友元成员函数？友元会破坏封装吗？
**答**：
- `friend class X;` 让整个类 X 访问本类私有成员；`friend void X::f();` 只放行某个成员函数，粒度更细。
- 友元关系**单向、不传递、不被继承**：A 是 B 的友元，不等于 B 是 A 的友元，也不等于 A 的派生类能访问 B。
- 观点题答法：友元不破坏封装，它只是把「实现细节共享」这件事**显式化**——写在类定义里、代码评审就能看见，比暴露 `getRaw()` 出一堆内部状态健康得多。
- 典型合理用法：`operator<<` / `operator==` 非成员实现、两个协同类（如 `Graph` 与 `Node`）、单元测试需要检查内部状态时开一个 `friend class XxxTest;`。
- 追问点：友元声明会引入对另一个类的名字查找，模板里要小心前置声明与 `typename`；friend 函数只做声明不会实例化。

### Q18 什么是聚合初始化、`std::initializer_list`、列表初始化的坑？
**答**：
- `T t{...}` 统一初始化语法对所有类型有效，还额外禁止了「窄化转换」（`int x{3.5}` 直接编译错误），C++11 之后首选花括号。
- 聚合类型（无用户构造函数、无私有成员、无虚函数...）可以直接按成员顺序 `Point p{1, 2};`，C++20 起还支持指定初始化 `Point p{.x = 1, .y = 2};`。
- `std::initializer_list<T>` 是编译器生成的一段 const 数组的轻量视图，`f({1, 2, 3})` 能把它作为参数；容器构造优先选它。
- 坑：类既有 `C(int,int)` 又有 `C(std::initializer_list<int>)` 时，`C c{1, 2}` 优先选 initializer_list，`C c(1, 2)` 才走普通构造；`std::vector<int> v{10}` 是一个元素而不是 10 个元素。
- 追问点：initializer_list 底层是 `const T[N]`，`std::move(*it)` 搬不走内容；`return {1, 2}` 能初始化任何可接受的花括号类型。

### Q19 什么是「空基类优化」和空类的大小？为什么空类大小不是 0？
**答**：
- C++ 要求同类型对象必须有不同地址，所以 `sizeof(Empty) == 1`，编译器给空类塞一个字节占位，保证数组里相邻元素地址不同。
- 空基类优化（EBO）：作为**基类**的空类可以大小为 0，不占派生类空间；成员对象则不能，因为要保证 `&obj.member` 唯一。
- 这是 `std::allocator`、`std::hash`、`[[no_unique_address]]`（C++20，用在成员上也能省空间）的底层原因。
- 空类还会自动得到默认构造、拷贝构造、析构、拷贝赋值，以及 `operator&`（可以 `= delete` 避免被取地址）。
- 追问点：有虚函数的类至少加一个 vptr（64 位下通常 8 字节）；空类数组元素大小仍是 1；`[[no_unique_address]]` 让两个同类型空成员可以共用地址（C++20 起）。

### Q20 什么是 POD 和标准布局类型？为什么 C++ 里还要关心「能不能 memcpy」？
**答**：
- `trivial`（平凡）判据：默认构造、拷贝、析构都平凡（编译器合成且非虚）；`standard-layout`（标准布局）判据：无虚函数、所有非静态成员同一访问级别、无多重继承带成员...
- `POD` = trivial + standard-layout，能安全 `memcpy`/`memset`，能跟 C 结构体互相传、能写二进制文件。
- 不是 POD 却去 `memcpy` 就是 UB：虚表指针、`std::string` 这种内部指针会被原样复制过去，释放时 double free。
- 现代建议：对外接口（跨语言、序列化、硬件寄存器）用 POD；内部逻辑别为了 POD 牺牲 RAII 和封装。
- 追问点：`std::is_trivially_copyable<T>`、`std::is_standard_layout<T>` 可以在模板里做编译期判定；C++20 的 `std::bit_cast` 要求 trivially copyable。

## 三、继承与多态

### Q21 三种继承方式（public/protected/private）有什么区别？
**答**：
- `public` 继承是 is-a：基类 `public` 仍是 `public`、`protected` 仍是 `protected`；`protected` 继承把公有成员降为 protected（能派生不能外部用）；`private` 继承把全部成员降为 private（「用实现而不是 is-a」，等价于组合）。
- 口诀：继承方式越私有，对外暴露越少；派生类内部访问基类的规则则和继承方式共同作用。
- 工程建议：**默认写 `public`，剩下的全用组合**；`private` 继承只用在需要覆盖虚函数或 EBO 的场景，而且尽量用 `final`/`private` 锁死进一步继承。
- 边界：继承方式可以出现在基类说明符里（`class D : protected B, private V {}`），多继承时每个基类各自指定。
- 追问点：`protected` 在多继承和组合结构里容易形成「受保护成员的授权链」，实际项目里基本被组合替代。

### Q22 多态是怎么实现的？vtable 和 vptr 各是什么？
**答**：
- 结论：**虚函数靠「每个类一张虚函数表（vtable）+ 每个对象一个虚表指针（vptr）」实现动态绑定**；调用 `p->f()` 时先通过 vptr 找到 vtable，再按函数槽位索引拿到真正地址。
- vtable 是编译器在编译期为「有虚函数的类」生成的函数指针数组，每项对应一个虚函数槽位；vptr 通常放在对象起始位置，构造函数里由编译器插入赋值代码建立。
- 派生类覆盖虚函数时就改写对应槽位的地址，所以同一个 `Base*` 指向不同派生对象时，走的是不同的函数体。
- 代价：每个对象多一个指针（8 字节），每个带虚函数的类多一张表（在只读段），调用有「两次间接跳转」，而且内联很难做。
- 追问点：vtable 布局没有标准保证，别写代码依赖槽位顺序；`dynamic_cast` 和 `typeid` 都依赖 vtable 里的类型信息（RTTI）；`final` 能让编译器去做去虚化（多态内联）。

```cpp
class Base { public: virtual void f(); };
class D : public Base { public: void f() override; };

Base* p = new D;
p->f();   // p->vptr->f_slot(p)  →  真正调用 D::f

// 常见误解：vptr 属于类？不，它属于每个对象（所以 sizeof 变大会影响容器内存）
```

### Q23 什么是虚函数？构造/析构函数里调虚函数会怎样？
**答**：
- `virtual` 成员函数允许派生类覆盖，通过基类指针/引用调用时按**对象的动态类型**分派；派生类重写时建议加 `override`，让编译器检查签名。
- 构造函数里调用虚函数**不会多态**：对象构造到哪个类，调用的就是那个类版本，因为 vptr 还没更新到派生类。
- 析构函数里调用虚函数同理，析构从派生类向基类进行，vptr 已被改回当前类。
- 所以别在构造/析构里调虚函数，尤其别指望派生类的重写生效——这是「两阶段构造」模式的动机之一（`init()` 在构造完成后调用）。
- 追问点：`virtual` 函数不能是 `static`；`override` 和 `final` 都是上下文关键字，可以同名当变量用；协变返回类型允许派生类返回更具体的指针/引用。

### Q24 什么是纯虚函数和抽象类？
**答**：
- `virtual void f() = 0;` 是纯虚函数，含纯虚函数的类（或没覆盖纯虚函数的派生类）是**抽象类**，不能实例化，只能当接口用。
- 纯虚函数也可以有定义（`void Base::f() {}`），派生类通过 `Base::f()` 显式调用，这常见于「默认实现 + 强制覆盖」的场景。
- 抽象类用来定义契约（接口），`std::vector<std::unique_ptr<Shape>>` 这种多态容器就是典型用法。
- 析构函数不能是纯虚的未定义版本：`virtual ~Base() = 0;` 必须在类外写定义，否则析构时链接报错，所以一般写 `virtual ~Base() = default;` 更省事。
- 追问点：接口类（纯虚类）还应显式删除拷贝、保留虚析构；不打算被继承的类用 `final` 而不是靠「文档约定」。

```cpp
class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const = 0;     // 纯虚：接口
    virtual void draw(std::ostream& os) const { os << "shape"; }  // 可选默认实现
};
```

### Q25 什么是对象切片（object slicing）？怎么避免？
**答**：
- 把派生类对象**按值**赋给基类对象（或按值传参）时，派生类部分被「切掉」，只剩基类子对象，虚函数也随之退化为基类版本。
- 原因：按值传递/赋值要求拷贝构造，而 `Base` 的拷贝构造只知道 `Base` 那部分，vptr 被重新指向 `Base`。
- 避免：多态对象一律用 `Base&` 或 `Base*`（现代写法 `std::unique_ptr<Base>`），不要写成 `void f(Base b)`。
- 容器尤其危险：`std::vector<Base> v; v.push_back(Derived());` 静默切片、不报错，这是最难查的坑之一；应改为 `std::vector<std::unique_ptr<Base>>`。
- 追问点：就算把「基类拷贝构造」声明为 `protected` 也拦不住切片（派生类可以调用），真正有效的办法是禁止按值传递 + 用 `deleted` 拷贝配合指针容器。

```cpp
struct Base { virtual ~Base() = default; virtual void speak() { puts("base"); } };
struct Dog : Base { void speak() override { puts("dog"); } };

void byValue(Base b) { b.speak(); }    // 切片：打印 base
void byRef(Base& b)  { b.speak(); }    // 不切片：打印 dog
```

### Q26 多重继承有什么问题？菱形继承是怎么产生的？
**答**：
- 多重继承让一个类有多个基类子对象，编译器按声明顺序依次构造基类，带来地址偏移问题（`static_cast<D*>` 到各基类指针需要调整偏移）。
- 菱形继承：`B1 : A`、`B2 : A`、`D : B1, B2`，此时 D 里有两份 A 子对象，通过 `D` 访问 `A` 的成员产生歧义，也会有重复构造/状态。
- 解决：虚继承 `class B1 : virtual public A`，让最终派生类只保留一份 A，由最底层派生类负责构造 A。
- 代价：虚继承对象里多一个指向虚基类的指针/表，访问虚基类成员多一次间接，布局变复杂、C ABI 不友好。
- 追问点：C++ 里接口用「纯虚类 + 公有继承」，实现复用用「组合」，多重继承主要用于多个接口（`class D : public ISerializable, public ICloneable`）；慎用 `reinterpret_cast` 在多重继承对象上硬转指针，必须用 `static_cast` 才会做偏移调整。

```cpp
struct A { int v = 0; };
struct B1 : virtual A {};
struct B2 : virtual A {};
struct D  : B1, B2 {};      // D 里只有一份 A
// D d; d.v = 1;  无歧义
```

### Q27 虚继承的构造顺序和对象布局是什么样？
**答**：
- 虚继承下，**虚基类由最底层派生类负责构造**（不是由直接派生类构造），所以 `D : B1, B2` 时 `A` 只构造一次，参数由 `D` 的构造函数传给 `A`。
- 构造顺序：先构造虚基类 `A`（按深度优先、从左到右），再按声明顺序构造非虚基类 `B1`、`B2`，最后构造 `D` 自身成员；析构逆序；不在最底层的中间类**忽略**自己给虚基类的初始化参数。
- 布局：`D` 开头是 B1、B2 的子对象，虚基类 A 放在末尾，B1/B2 各自持有指向 A 的偏移；访问 A 的成员要经过偏移计算。
- 为什么容易忘：`B1::B1() : A(1)` 里的 `1` 在 `D` 实例化时会被忽略，实际来自 `D` 的构造函数列表——这就是「虚基类参数由最终类提供」的实战含义。
- 追问点：`sizeof(D)` 通常比直觉大（多了虚基类指针）；`static_cast` 到虚基类指针需要运行时查表，比普通继承慢；虚继承并不解决 A 状态合并后的「谁赋值算数」问题，那是设计问题。

```cpp
struct A { A(int x) { std::cout << "A" << x << '\n'; } };
struct B1 : virtual A { B1() : A(1) {} };   // 参数被忽略
struct B2 : virtual A { B2() : A(2) {} };   // 参数被忽略
struct D : B1, B2 { D() : A(3) {} };        // 实际打印 A3，然后 B1 B2
```

### Q28 什么是 RTTI？`typeid` 和 `dynamic_cast` 有什么区别？
**答**：
- RTTI 是运行期类型信息，主要提供 `typeid` 和 `dynamic_cast`，依赖多态类型的 vtable 里保存的类型信息，需要开启 RTTI（`-frtti`，嵌入式常用 `-fno-rtti` 关掉）。
- `typeid(x)` 返回 `std::type_info`，能 `.name()`（实现相关，可用 `abi::__cxa_demangle` 解码）和 `operator==`；对多态类型作用于**动态类型**（基类引用能拿到派生类），对非多态类型且是 glvalue 时作用于静态类型。
- `dynamic_cast<T*>(p)` 在运行期检查能否安全转换：失败返回 `nullptr`（指针）或抛 `std::bad_cast`（引用）；`dynamic_cast<void*>(p)` 返回最派生对象地址，常用来判同一对象。
- 相比 `static_cast`：`dynamic_cast` 会做运行期检查、有开销，但跨虚继承/向下转型才安全；`static_cast` 只做编译期调整，转错了就是 UB。
- 追问点：`typeid` 对空指针解引用是 `bad_typeid`（多态类型时）；跨 DLL 的 `typeid` 比较可能失败，工程里更稳的做法是加类型枚举/虚函数 `type()`；C++20 起还能用 `dynamic_cast` 做 `requires` 约束。

```cpp
struct Base { virtual ~Base() = default; };
struct D : Base { void onlyD() {} };

void f(Base* p) {
    if (auto* d = dynamic_cast<D*>(p)) {   // 失败得到 nullptr
        d->onlyD();
    }
    std::cout << typeid(*p).name() << '\n';   // 动态类型
}
```

## 四、内存与资源管理

### Q29 `new`/`delete` 和 `malloc`/`free` 有什么区别？
**答**：
- `new` 是运算符：先调 `operator new` 分配**原始字节**，再在字节上调用构造函数，失败抛 `std::bad_alloc`；`delete` 先调析构再释放内存。`malloc` 只是 C 函数，只分配不构造，失败返回 `nullptr`。
- `malloc` 参数是字节数（`malloc(n * sizeof(T))`），`new` 按类型或按数组（`new T[n]`），后者要多存元素个数并在 `delete[]` 时逐个析构。
- 不能混用：`new` 出来的必须 `delete`，`malloc` 出来的必须 `free`，混用是 UB（分配器记账方式不同）。
- `new` 可以配 placement new（在已有内存上构造）、可以重载 `operator new` 做内存池；`malloc` 只能被替换为 `malloc` 钩子。
- 追问点：`new T[n]` 里元素的构造顺序是从低到高、析构逆序；`delete[]` 必须和 `new[]` 配对；C++17 有 `aligned new`，可以申请 cache line 对齐内存。

```cpp
// new：分配 + 构造，失败抛异常
Widget* w = new Widget(1);
delete w;

// 等价于：
void* raw = ::operator new(sizeof(Widget));   // 只分配
Widget* w2 = new (raw) Widget(1);              // placement new：只构造
w2->~Widget();                                 // 手动析构
::operator delete(raw);                        // 只释放

// nothrow 版本不抛异常，失败返回 nullptr
Widget* w3 = new (std::nothrow) Widget(1);
```

### Q30 什么是内存泄漏、野指针、悬空指针、重复释放？
**答**：
- 内存泄漏：`new` 了没 `delete`，或容器里持有裸指针而析构没清；长期运行的服务会 OOM，排查用 Valgrind、ASan（`-fsanitize=address,leak`）、heaptrack。
- 野指针：未初始化的指针（值随机），解引用是 UB，C++11 起用 `nullptr` 初始化、`-Weffc++`/静态分析能抓。
- 悬空指针：指向已被释放或已离开作用域的对象，典型是 `return &local;`、`v.push_back` 后的旧指针、`unique_ptr.get()` 后 owner 被销毁。
- 重复释放（double free）：两个指针指向同一块、析构两次；RAII 化（`unique_ptr`）是根治手段。
- 追问点：`delete` 后置 `nullptr` 只是降低「再 delete」风险，改不了其他副本；`shared_ptr` 的循环引用是「逻辑上永不释放」的泄漏，要用 `weak_ptr` 破环。

### Q31 什么是 RAII？C++ 里怎么用它管理资源？
**答**：
- RAII（资源获取即初始化）：在构造函数里获取资源、在析构函数里释放资源，把「配对操作」绑到对象生命周期上，异常、提前 return、忘记清理都不会漏。
- 资源不止内存：文件 `FILE*`、`fstream`、锁 `lock_guard`、socket、`mmap`、GDI 句柄、连接池借出的连接，全可以用 RAII 封装。
- 标准库里的现成 RAII：`std::string`、`std::vector`、`std::unique_ptr`、`std::lock_guard`、`std::fstream`，写了它们就基本不用手写 `delete`。
- 实现要点：析构函数不抛异常（`noexcept`）、禁止拷贝或实现正确拷贝、用 `noexcept` 的移动支持容器的重排。
- 追问点：`std::lock_guard`/`std::unique_lock` 靠作用域解锁，比手写 `unlock()` 更能应对中途抛异常；`std::scope_exit`（C++23）可以包住任意「收尾动作」。

```cpp
struct FileGuard {
    explicit FileGuard(const char* path) : fp_(std::fopen(path, "r")) {
        if (!fp_) throw std::runtime_error("open failed");
    }
    ~FileGuard() { if (fp_) std::fclose(fp_); }      // 异常也会执行
    FileGuard(const FileGuard&) = delete;
    FileGuard& operator=(const FileGuard&) = delete;
    FILE* get() const { return fp_; }
private:
    FILE* fp_;
};

void read(const char* p) {
    FileGuard f(p);      // 中途 throw，fclose 照样发生
    // ... 使用 f.get()
}
```

### Q32 三法则、五法则、零法则分别是什么？
**答**：
- 三法则（C++98）：需要自定义**析构、拷贝构造、拷贝赋值**中的任何一个，通常三个都得写，否则另外两个的默认版本会以浅拷贝的方式出错。
- 五法则（C++11）：再加上**移动构造、移动赋值**，尤其是移动构造要 `noexcept`，否则 `std::vector` 扩容会放弃移动。
- 零法则（现代首选）：**一个都不写**，把资源交给 `std::string`/`std::vector`/智能指针，编译器默认生成的五个函数就是正确的。
- 判断标准：类里有「自己需要手动释放」的东西（裸指针、句柄）就违反了零法则，先想办法换成 RAII 成员。
- 追问点：写了移动操作就没法再用默认拷贝操作；五法则全部 `= default`/`= delete` 可以显式表达意图；EBO 与 `[[no_unique_address]]` 让空 RAII 成员不占空间。

```cpp
class Widget {
public:
    Widget() = default;
    Widget(const Widget&) = default;             // 五法则全显式
    Widget& operator=(const Widget&) = default;
    Widget(Widget&&) noexcept = default;
    Widget& operator=(Widget&&) noexcept = default;
    ~Widget() = default;
private:
    std::string name_;                           // 零法则：资源交给成员
    std::unique_ptr<Big> big_;
};
```

### Q33 三种智能指针分别解决什么问题？
**答**：
- `std::unique_ptr<T>`：独占所有权，零额外开销（默认删除器下大小等于裸指针），不可拷贝只能 `std::move`，是「有明确唯一 owner」的默认选择。
- `std::shared_ptr<T>`：共享所有权，引用计数归零才释放，有原子计数开销（约 2~3 个指针大小），拷贝是加减原子计数。
- `std::weak_ptr<T>`：不参与引用计数的弱观察者，用 `lock()` 升成 `shared_ptr`，用来破循环引用、做缓存/观察者。
- 选择顺序：栈对象优先，其次 `unique_ptr`，确实需要共享才 `shared_ptr`；能用 `unique_ptr` 的地方别用 `shared_ptr`。
- 追问点：`make_unique`/`make_shared` 异常安全（C++14/11）；`make_shared` 把控制块和对象一次分配，但会推迟对象内存释放直到弱引用也为空；`shared_ptr` 计数是原子的但对象访问不是线程安全的。

### Q34 `shared_ptr` 的循环引用是什么？`weak_ptr` 怎么解决？
**答**：
- 两个对象互相持有 `shared_ptr`（典型父子节点、观察者与被观察者），引用计数互相不为零，谁都不析构，内存永不释放——是「逻辑泄漏」，LeakSanitizer 可能都查不出来（对象仍有 root）。
- 解决：**让「从属方向」持有 `weak_ptr`**。比如父节点持有子节点的 `shared_ptr`，子节点回指父节点用 `weak_ptr`；观察者列表用 `weak_ptr` 避免观察者被反向保活。
- 使用时必须 `lock()` 判断是否还活着：`if (auto sp = wp.lock()) { sp->use(); }`，不能直接解引用（`weak_ptr` 没有 `operator*`）。
- 诊断：`use_count()` 该归零不归零、或者用 `valgrind --leak-check=full --show-reachable=yes` 看到大量 reachable 块，就该怀疑环。
- 追问点：`enable_shared_from_this` 让你在对象内部拿到自己的 `shared_ptr`；`weak_ptr` 还有「缓存」用途：数据被回收就自然失效；`expired()` 只适合单线程诊断。

```cpp
struct Node {
    std::shared_ptr<Node> next;
    std::weak_ptr<Node>   prev;     // 回指用 weak，破环
};

void visit(const std::weak_ptr<Node>& w) {
    if (auto p = w.lock()) {        // 对象还活着才访问
        // ...
    }
}
```

### Q35 智能指针有哪些易错用法？
**答**：
- 不要 `shared_ptr<T> p(new T);` 之后再 `shared_ptr<T> q(p.get());`：两个控制块管同一块内存，二次析构；也不要用裸指针构造多个 `shared_ptr`。
- 不要 `delete p.get();` 或在 `unique_ptr` 管理期间手动释放；`release()` 会放弃所有权但不释放，泄漏风险自负。
- 删除器：`shared_ptr` 类型里带删除器（默认 `delete` 就要保证 `new` 出来的）；`unique_ptr` 删除器是模板参数，对 `FILE*` 这种要写 `unique_ptr<FILE, decltype(&fclose)>`。
- `shared_ptr` 不是线程安全的「对象」：计数安全、对象内容不安全；跨线程共享对象仍要自己加锁或做成不可变。
- 追问点：`p.get()` 返回的指针不要跨 owner 生命周期保存；`shared_ptr<void>` 也能正确调用自定义删除器；`unique_ptr` 可以被 `return` 出去，天然适合工厂。

```cpp
// 正确：一次分配，异常安全
auto p = std::make_shared<Widget>(1);
auto u = std::make_unique<Widget>(2);

// 自定义删除器
std::unique_ptr<FILE, int(*)(FILE*)> fp(std::fopen("a.txt", "r"), &std::fclose);
std::shared_ptr<FILE>       sp(std::fopen("b.txt", "r"), &std::fclose);
```

### Q36 内存对齐是什么？`struct` 的大小怎么算？
**答**：
- 对齐要求每个成员地址是它自身对齐值的整数倍，`struct` 的大小被补齐到**最大成员对齐值**的整数倍，所以 `struct { char c; int i; }` 是 8 字节而不是 5。
- 规则：成员按声明顺序依次放，每个成员前补齐到它的对齐值；末尾补齐到整体对齐值；`#pragma pack(1)` 可以关掉填充但牺牲性能、甚至触发 ARM 上的非对齐访问故障。
- 为什么要对齐：CPU 访存按字进行，非对齐可能要多周期甚至硬件异常；`std::atomic<int>` 在非对齐时也可能不是原子。
- 实践：调整成员顺序（大的先放、把 char 凑一起）能明显省内存；`alignas(64)` 让成员落到 cache line 边界，避免伪共享。
- 追问点：`sizeof(std::atomic<int>)` 通常等于 4，但 `sizeof(std::mutex)` 远大于直觉；`offsetof` 只能用于标准布局类型；`alignof(T)` 可以用在模板约束里。

```cpp
struct A { char c; int i; };            // sizeof = 8
struct B { int i; char c; };            // sizeof = 8
struct C { char a; char b; int i; };    // sizeof = 8（两个 char 挤在一起）
struct D { char c; int i; } __attribute__((packed));   // sizeof = 5，但访问有代价

struct alignas(64) CacheLine { std::atomic<int> v; };  // 独占一条 cache line
```

### Q37 栈和堆的区别？函数里的对象什么时候被销毁？
**答**：
- 栈：由编译器自动分配释放，空间小（默认 1~8 MB）、分配即移动栈指针（纳秒级）、有缓存局部性优势；但递归深了会栈溢出。
- 堆：`new`/`malloc` 分配，生命周期由程序员控制、容量大，但分配器有锁和碎片开销，跨线程释放还有性能问题。
- 局部对象在作用域结束时按**逆序**析构；`static`/全局对象到程序结束才析构；堆对象靠 `delete` 或智能指针。
- 大对象不要放栈上：`char buf[1 << 20];` 容易直接爆栈；需要大缓冲区用 `std::vector<char>`。
- 追问点：`std::array` 是栈上的固定数组；`alloca`/VLA 不可移植；临时对象在完整表达式结束时销毁——`const char* p = std::string("x").c_str();` 就是悬空指针。

### Q38 C++ 里应该多用异常还是错误码？`noexcept` 有什么作用？
**答**：
- 异常适合「无法就地处理、必须向上传导」的错误，不会污染正常路径的返回值签名；错误码适合性能敏感/嵌入式/ABI 稳定的场合，也可用 `std::error_code`/`std::optional` 表达。
- 异常有代价（表驱动实现下不抛异常时几乎零成本，抛出时走栈展开），但会让代码更线性；工程里统一风格比纠结哪个快更重要。
- `noexcept` 表示函数不抛异常：调用方可以放心优化（移动构造必须 `noexcept` 才能被容器用来重排），不满足时直接 `std::terminate`。
- 析构函数、`swap`、移动操作原则上都该 `noexcept`；`lock_guard` 靠析构解锁，析构抛异常会 double terminate。
- 追问点：`throw()` 动态异常规格已被 C++17 移除，换成 `noexcept`；`noexcept(expr)` 可以做编译期条件标注；C++23 的 `std::expected` 提供了一个「错误码式」的现代选项。

## 五、模板与泛型

### Q39 函数模板和类模板有什么区别？模板的实例化机制是什么？
**答**：
- 函数模板可以根据实参推导 `T`（`max(1, 2)` 自动得到 `int`）；类模板到 C++17 才有 CTAD（`std::pair p{1, 2.0}`），C++17 之前必须显式写 `std::pair<int, double>`。
- 模板是「代码生成器」：编译器在实例化点按实参替换 `T` 生成具体函数/类，模板本身不产生代码，所以模板定义通常要放在头文件里。
- 类模板的成员函数按需实例化（你用到哪个就生成哪个），这也是头文件-only 库常见的原因。
- 模板不能有虚函数（vtable 需要编译期确定类集合），但可以写 CRTP 做静态多态。
- 追问点：模板的 `<>` 嵌套（`vector<vector<int>>`）C++11 起不必再写 `> >`；`template<typename T>` 和 `template<class T>` 等价；模板实例化失败是编译期错误，报错往往很长。

### Q40 模板特化和偏特化有什么区别？
**答**：
- 全特化：把**所有**模板参数都写死成具体类型，`template<> struct Hash<int> {...}`；偏特化：只固定**部分**参数或结构的形状，比如 `template<typename T> struct Hash<T*>`、`std::function<void(int)>` 对 `void(int)` 的偏特化。
- **函数模板只允许全特化，不支持偏特化**；想对一类参数特化要借助类模板（经典的 `std::is_pointer` 就是偏特化的例子）或 `if constexpr`（C++17）。
- 偏特化常用于类型萃取：`template<typename T> struct IsPtr { static constexpr bool value = false; };` 配 `template<typename T> struct IsPtr<T*> { ... true ... };`。
- 特化优先级：全特化 > 偏特化 > 主模板；模板匹配是精确匹配，不做隐式转换（除了 `T&` 绑定时的 const/引用调整）。
- 追问点：特化必须在实例化点之前可见；`std::hash` 的特化要放在 `namespace std` 里；C++20 可以用 `requires` 直接约束参数，减少偏特化的写法。

```cpp
template <typename T> struct TypeName { static const char* get() { return "unknown"; } };

template <> struct TypeName<int> { static const char* get() { return "int"; } };   // 全特化
template <typename T> struct TypeName<T*> { static const char* get() { return "pointer"; } };  // 偏特化

std::cout << TypeName<int>::get()     // int
          << TypeName<double*>::get();// pointer
```

### Q41 什么是可变参数模板？怎么用它们写一个 `print`？
**答**：
- `template<typename... Ts> void f(Ts... args)` 里的 `Ts` 是模板参数包，`args` 是函数参数包；展开用递归（C++11）或折叠表达式（C++17）。
- 递归展开：处理第一个参数，再 `f(rest...)`；折叠表达式 `(std::cout << ... << args)` 一句话搞定，可读性好得多。
- `sizeof...(Ts)` 拿参数个数；`std::forward_as_tuple`、`std::apply`、`std::make_unique` 都依赖参数包做完美转发。
- 常见坑：参数包必须是最后一组参数（否则推导不出边界）；递归展开需要终止重载（空参数版本）。
- 追问点：折叠表达式四种形式 `(... op args)`、`(args op ...)`、`(init op ... op args)`，遇到空包要小心短路的运算符优先级；`std::tuple` 的 `get<T>` 靠类型技巧实现，是「可变参数模板 + 偏特化」的综合题。

```cpp
template <typename... Ts>
void print(const Ts&... args) {
    ((std::cout << args << ' '), ...);   // C++17 折叠表达式
    std::cout << '\n';
}

template <typename T, typename... Rest>
T sum(T first, Rest... rest) {
    if constexpr (sizeof...(rest) == 0) return first;
    else return first + sum(rest...);
}

print(1, "two", 3.0);   // 1 two 3
```

### Q42 什么是 SFINAE？为什么需要它？
**答**：
- SFINAE = Substitution Failure Is Not An Error：模板推导时，把 `T` 代入签名若失败（比如 `T::value_type` 不存在），**只是从候选集中剔除，不报编译错误**。
- 用途：让重载/特化只在类型满足某条件时才参与——`std::enable_if_t<std::is_integral_v<T>, int> = 0` 是经典写法。
- 现代替代：C++17 的 `if constexpr`（函数体内分支）、C++20 的 `concepts`（`requires std::integral<T>`）可读性和报错都好得多，新代码首选 concepts。
- SFINAE 仍活跃的地方：C++11/14 代码库、检测某成员/运算符是否存在（`std::void_t` + 偏特化），以及需要在不改动函数体的情况下排除重载。
- 追问点：SFINAE 只在**替换阶段**生效，函数体里的错误是硬错误；`std::void_t<Ts...>` 是「只要参数合法就得到 void」的工具，用来做 `has_member` 探测器。

```cpp
// C++11/14：仅当 T 有 size() 成员时参与重载
template <typename T, typename = std::void_t<decltype(std::declval<T>().size())>>
std::size_t len(const T& t) { return t.size(); }

// C++20：等价但报错友好
template <typename T>
requires requires (const T& t) { t.size(); }
std::size_t len2(const T& t) { return t.size(); }
```

### Q43 什么是 CRTP？它和虚函数多态怎么选？
**答**：
- CRTP（奇异递归模板模式）：`template<typename D> struct Base { void f() { static_cast<D*>(this)->impl(); } };`，基类模板在**编译期**就知道派生类的具体类型。
- 好处：静态多态，没有 vtable/vptr 开销、调用可以内联；坏处是每个派生类生成一份基类代码，模板膨胀、编译慢，也无法在运行期做容器里的多态。
- 用途：`std::enable_shared_from_this`、静态接口注入、mixin 风格的 `operator==`/`operator<` 批量化、计数器 Counted\<T\>。
- 选型：类型集合编译期确定、追求极致性能 → CRTP；需要在运行期持有 `Base*` 集合 → 虚函数（或 `std::variant`）。
- 追问点：CRTP 里 `static_cast<D*>(this)` 在构造/析构阶段是 UB 的（对象还没完整），别在基类构造里调 CRTP 接口；C++20 的 concepts 能约束 `D` 必须有 `impl`。

```cpp
template <typename D>
struct Shape {
    double area() const { return static_cast<const D*>(this)->areaImpl(); }
};

struct Circle : Shape<Circle> {
    double r = 1;
    double areaImpl() const { return 3.14159 * r * r; }
};

template <typename T> void printArea(const T& s) { std::cout << s.area(); }
```

### Q44 模板的编译期计算：`constexpr` 模板、`if constexpr`、`static_assert` 各解决什么？
**答**：
- `constexpr` 函数在 C++11 只能单条 return，C++14 起可以是普通函数体，在常量表达式中求值就是**编译期计算**，否则退化为运行期普通函数。
- `if constexpr`（C++17）在模板里做**编译期分支**，不成立的分支不参与实例化，避免了以前用 `enable_if` 断掉整条路径的麻烦。
- `static_assert(cond, "msg")` 在编译期断言条件，常用来检查模板参数满足要求（`static_assert(std::is_integral_v<T>)`），比 SFINAE 长报错好读。
- 配合递归做编译期计算：`template<size_t N> struct Fact { static constexpr size_t v = N * Fact<N-1>::v; };`，C++17 以后直接写 `consteval` 或 constexpr 函数更顺。
- 追问点：`consteval`（C++20）强制必须在编译期求值，`constinit` 保证静态初始化不拖到运行期；`constexpr` 函数运行期调用时行为与普通函数一致，可以放心两用。

```cpp
template <typename T>
T clamp(T v, T lo, T hi) {
    if constexpr (std::is_pointer_v<T>) static_assert(!std::is_pointer_v<T>, "no ptr");
    return v < lo ? lo : (v > hi ? hi : v);
}

template <int N> struct Fact { static constexpr int v = N * Fact<N - 1>::v; };
template <> struct Fact<0> { static constexpr int v = 1; };
static_assert(Fact<5>::v == 120);
```

### Q45 模板库为什么经常用 `std::enable_if`、`std::void_t`、`if constexpr` 三件套？模板怎么调试？
**答**：
- 三件套解决的是同一件事：**只对合法类型实例化**。`enable_if` 管签名、`if constexpr` 管函数体、`void_t` 管「存在性探测」，C++20 后统一换成 concepts 更清楚。
- 模板报错的常见长尾原因：const/引用没去掉（`std::decay_t`）、忘记 `typename`（依赖名默认是值）、写成 `T::member` 而 `T` 是模板参数、`>>` 被当成右移。
- 调试手段：`static_assert(std::is_same_v<decltype(x), int>)` 打印类型、`template<typename> struct Debug;` 调用一次看错误消息、`-ftemplate-depth` 调深递归、clang 的报错比 GCC 可读。
- 思路：先把错误定位到「哪个实例化」，报错栈里第一个 `note: in instantiation of` 往往就是根因，后面都是级联。
- 追问点：模板元编程的编译成本很高，大型项目用预编译头、显式实例化（`extern template`/`template class`）缓解；C++20 的 concepts 能把报错缩短一大截。

## 六、现代 C++（C++11—20）

### Q46 `auto` 和 `decltype` 有什么区别？什么时候用哪一个？
**答**：
- `auto` 按值推导会**丢掉引用和顶层 const**（推导规则同函数模板的按值传参），`decltype(expr)` 精确保留引用、const 和完整类型。
- 常见陷阱：`for (auto x : v)` 会复制每个元素，应写 `const auto&`；`auto p = v.begin()` 在 `erase` 后同样会失效。
- `decltype(auto)`（C++14）让返回值用 decltype 规则推导，写完美转发/包装函数必备：`decltype(auto) f() { return v[0]; }` 返回 `int&`。
- `decltype(expr)` 与 `decltype((expr))` 不同：前者对未加括号的变量名特例返回其声明类型，加括号后按值类别——左值返回 `T&`。
- 追问点：`auto` 的推导会退化数组和函数为指针，`auto&` 才能保留数组；`auto` 不能用在函数参数（C++20 的简写模板才算 `auto` 参数）。

```cpp
int x = 0;
auto        a = x;            // int
decltype(x) b = x;            // int
decltype((x)) c = x;          // int&（加括号 → 左值）
auto&       d = x;            // int&

std::map<int, int> m{{1, 2}};
decltype(auto) r = m[1];      // int&，可写回 m
auto           v = m[1];      // int，副本
```

### Q47 `nullptr` 和 `NULL` 有什么区别？
**答**：
- `NULL` 是宏，通常是 `0` 或 `(void*)0`，本质是整型常量；`nullptr`（C++11）是 `std::nullptr_t` 类型的**空指针字面量**，能隐式转成任意指针类型，但不能当整数用。
- 经典坑：`void f(int)` 与 `void f(char*)` 重载时 `f(NULL)` 会选 `int` 版本（因为 `NULL` 是 0），`f(nullptr)` 才正确选指针版本。
- 模板推导：`template<class T> void g(T)` 传 `NULL` 得到 `T = int`，传 `nullptr` 得到 `std::nullptr_t`，所以模板场景必须用 `nullptr`。
- 取地址/比较：`nullptr` 跟任何指针类型比较都安全，`NULL` 在 `(void*)0` 定义下和 `char*` 比较就编不过。
- 追问点：C++11 起 `nullptr` 可以 `delete nullptr;` 安全无副作用；`NULL` 不要在 C++ 新代码里出现；`std::nullptr_t` 大小等于一个指针。

### Q48 什么是右值引用？移动语义和引用折叠是怎么回事？
**答**：
- `T&&` 是右值引用，只能绑定右值（临时对象、`std::move(x)` 的结果）；`T&` 是左值引用。C++11 借此区分「可被搬空」的资源。
- 移动语义的实质：把资源「偷」过来（改指针），不复制内容；源对象置为有效但未指定状态。
- 引用折叠规则：`& & → &`、`& && → &`、`&& & → &`、`&& && → &&`，这是模板里 `T&&`（转发引用）能同时接收左值和右值的原因。
- 转发引用（万能引用）：只有**形如 `T&&` 且 T 是模板参数且推导**时才是；`const T&&`、`std::vector<T>&&` 都不是，都是普通右值引用。
- 追问点：右值引用是右值，但一个具名的 `T&&` 变量本身是**左值**（这就是 `std::move` 存在的理由）；`std::is_same_v<T&, T>` 的折叠判定常出现在面试题里。

### Q49 `std::move` 和 `std::forward` 有什么区别？什么是完美转发？
**答**：
- `std::move(x)` **不做任何移动**，只是把左值 `static_cast<T&&>` 成右值引用，让后面的移动构造/移动赋值有机会被选中；对 `const` 对象移动无效，会退化成拷贝。
- `std::forward<T>(x)` 用于**转发引用**，在模板里按 `T` 的推导结果保持原始值类别——左值进来还是左值，右值进来还是右值。
- 完美转发 = 引用折叠 + `std::forward`，让包装函数（工厂、`std::make_unique`、`emplace_back`）原样传递值类别，不产生多余拷贝。
- 常见错误：函数里对具名的 `T&&` 参数直接当右值用（其实是左值）、`std::move` 之后再使用源对象、对 `const` 对象 `move`。
- 追问点：返回局部变量时**别**写 `return std::move(local);`，会破坏 NRVO；`std::move` 后的对象只能析构或重新赋值；`move` 也是名字遮蔽的好目标（`std::move_if_noexcept`）。

```cpp
template <typename T>
void relay(T&& v) {
    use(std::forward<T>(v));   // 左值仍是左值，右值仍是右值
}

std::string s = "hi";
relay(s);               // T = std::string&     → 左值
relay(std::string("x"));// T = std::string      → 右值

// str() 返回右值引用，用来明确表达「取走内部数据」
std::string str() && { return std::move(buf_); }
```

### Q50 lambda 的捕获方式有哪些？`[=]` 和 `[&]` 各有什么坑？
**答**：
- 值捕获 `[x]`：拷贝一份，lambda 里默认是 `const`，要改得加 `mutable`；引用捕获 `[&x]` 不拷贝，能看到外部修改。
- `[=]`/`[&]` 隐式捕获所有用到的变量，方便但危险：`[&]` 在异步回调里捕获局部变量，函数返回后就是悬空引用；`[=]` 在成员函数里捕获 `this` 是指针（C++20 已废弃隐式 `this`）。
- C++14 广义捕获：`[p = std::move(ptr)]` 可以把 `unique_ptr` 移进 lambda，也能做「初始化捕获」算出新变量。
- 存储：lambda 是编译器生成的类，捕获项是成员；无捕获 lambda 可转成函数指针（`+[]{}` 或 `[](int){}` 传给 C API）。
- 追问点：`auto` 参数让 lambda 成为泛型 lambda（C++14）；C++20 的模板 lambda 可以显式写 `[]<typename T>(T x)`；`std::function` 存 lambda 要注意拷贝成本与生命周期。

```cpp
int base = 10;
auto add = [base](int x) { return x + base; };     // 值捕获，拷贝一份
auto inc = [&base]() { ++base; };                  // 引用捕获

auto task = [p = std::make_unique<int>(1)]() {     // 初始化捕获（C++14）
    return *p;
};

std::thread t([&] { /* 千万别引用捕获局部变量后在别处 join */ });
```

### Q51 `std::function` 和 lambda / 函数指针怎么选？
**答**：
- `std::function<R(Args...)>` 是**类型擦除**的通用可调用对象容器，能存函数、lambda、`std::bind` 结果、成员函数指针；代价是一次堆分配（大对象时）和间接调用，性能不如模板直接展开。
- 函数指针最轻（一个指针大小），但只能指向普通函数/无捕获 lambda（无捕获 lambda 可隐式转）。
- 模板参数 `F&&` 最通用、最快（可以内联），但会让每个 lambda 类型生成一份代码，也可能导致接口膨胀/编译变慢；库接口里常用「模板 + `std::function` 兜底」。
- 空 `std::function` 调用会抛 `std::bad_function_call`，用前判 `if (f)`；`std::function` 拷贝时拷贝的是可调用对象，捕获大对象要小心。
- 追问点：`std::function` 的 `target<T>()` 能取回原始对象；开源实现常用 SBO（小对象优化）把小于两个指针的对象放在栈上；C++23 的 `std::move_only_function` 可以存 `unique_ptr` 这类只能移动的可调用对象。

```cpp
using Callback = std::function<void(int)>;

void on(Callback cb) { if (cb) cb(42); }        // 判空再调

on([](int v) { std::cout << v; });               // lambda
on(&oneshot);                                    // 函数指针

struct Handler { void operator()(int) const {} };
on(Handler{});                                   // 仿函数
```

### Q52 `constexpr` 和 `consteval` 有什么不同？编译期能做什么？
**答**：
- `constexpr` 函数：参数是常量表达式时在编译期求值，否则在运行期求值；`constexpr` 变量要求初始化必须是常量表达式。
- `consteval`（C++20）：强制在编译期求值，不满足就编译错误；`constinit` 保证静态变量在编译期初始化（避免静态初始化顺序问题）。
- 编译期能做的事：数组大小、模板参数、`switch` 的 `case` 标签、`static_assert`、以及用 `constexpr` 容器在编译期算查找表（C++20 起 `std::vector` 可以在 constexpr 里用，更早只能用 `std::array`）。
- 限制：编译期不能捕获异常、不能动态申请永不释放的内存、不能调非 constexpr 函数；C++20 放宽到允许 `new/delete` 配对使用。
- 追问点：`if consteval`（C++23）可以区分当前是否在常量求值里；编译期计算能省运行期开销但会增加编译时间，查找表建议用脚本生成/`constexpr` 二选一。

```cpp
constexpr int fib(int n) { return n < 2 ? n : fib(n - 1) + fib(n - 2); }
constexpr int f10 = fib(10);          // 编译期算好

consteval int square(int x) { return x * x; }   // C++20：必须编译期
// int r = square(std::rand());       // 编译错误

constexpr std::array<int, 4> makeTable() {
    std::array<int, 4> a{};
    for (int i = 0; i < 4; ++i) a[i] = i * i;
    return a;
}
```

### Q53 `override` 和 `final` 有什么用？为什么建议每个重写都加 `override`？
**答**：
- `override` 让编译器检查「确实覆盖了基类虚函数」，签名写错（漏 `const`、参数类型不一致、基类函数不是虚的）会直接编译失败，而不是悄悄变成新函数。
- 典型事故：基类 `virtual void f() const`，派生类写了 `void f()` 没写 const，不加 `override` 就是「新函数」，多态调用走的还是基类版本。
- `final` 用在类上禁止再继承，用在函数上禁止再覆盖；还能让编译器做去虚化、把间接调用变直接调用（多态内联）。
- 组合用法：`class Impl final : public Base` 明确表达设计意图，也告诉优化器「这个类不会再有派生类」。
- 追问点：`override`/`final` 是上下文关键字，可以当普通标识符用（老代码兼容）；`delete`/`default` 也属于同类 C++11 关键字。

```cpp
struct Base { virtual void f() const; virtual ~Base() = default; };

struct Mid : Base {
    void f() const override;   // 少了 const 或 override 都会报错
};

struct Leaf final : Mid {      // 不允许再被继承
    void f() const override final;
};
```

### Q54 C++17 的 `if constexpr`、结构化绑定、`std::optional`、`std::variant`、`std::string_view` 各自解决什么？
**答**：
- 结构化绑定 `auto [a, b] = pair;`：解构 `pair`/`tuple`/数组/聚合体，遍历 map 时首选 `for (const auto& [k, v] : m)`。
- `std::optional<T>`：表达「可能没有值」，替代「魔法返回值 -1」或指针输出参数；`v.has_value()` / `v.value_or(d)`。
- `std::variant<A, B>`：类型安全的 union，配合 `std::visit` 做静态分发，可以当「闭集合多态」用，避免 vtable。
- `std::string_view`：非拥有的字符串视图，避免 `std::string` 的临时构造和拷贝；但它不保证末尾有 `'\0'`，也不能跨生命周期持有。
- 追问点：`if constexpr` 能让不成立的分支不实例化，替代旧式 `if` 里的 tag dispatch；`std::any` 是彻底的运行时类型擦除，一般用 `variant` 更多。

```cpp
std::map<std::string, int> m{{"a", 1}};
for (const auto& [k, v] : m) std::cout << k << '=' << v << '\n';

std::optional<int> findId(const std::string& k) {
    auto it = m.find(k);
    if (it == m.end()) return std::nullopt;
    return it->second;
}

void handle(std::string_view sv) { std::cout << sv.size(); }   // 零拷贝入参
```

### Q55 C++20 有哪些最重要的新特性？
**答**：
- Concepts：`template<std::integral T> void f(T);`，编译期约束模板参数，报错从几十行缩到一行，也替代了大部分 SFINAE 写法。
- Ranges：`std::ranges::sort(v)`、`v | std::views::filter(...) | std::views::transform(...)`，管道式惰性算法，写起来接近函数式。
- 其他：协程（`co_await`/`co_yield`，C++20 先给机制）、模块（替代头文件，需编译器支持）、`std::span`（连续内存视图）、`<=>` 三路比较、指定初始化 `.x = 1`、`std::format`。
- 四个 `const` 家族补齐：`constinit`、`consteval`、`constexpr` 宽松化、`std::bit_cast`。
- 追问点：C++20 编译支持不均衡，面试被问「用过哪些」时要具体（ranges 视图性能、concepts 报错体验）；C++23 带来 `std::expected`、`std::print`、`import std;`，可以顺带提一句。

```cpp
#include <concepts>
#include <ranges>

template <std::integral T>            // concept 约束
T twice(T v) { return v * 2; }

std::vector<int> v = {1, 2, 3, 4};
auto evens = v | std::views::filter([](int x) { return x % 2 == 0; });
for (int x : evens) std::cout << x << ' ';    // 2 4
```

## 七、STL 与算法

### Q56 `std::vector` 的扩容机制是什么？`reserve` 和 `resize` 有什么区别？
**答**：
- `vector` 连续存储，`size()` 是元素个数、`capacity()` 是已申请容量；`push_back` 遇到容量不足时按**几何增长**重新分配（libstdc++ 通常是 2 倍，MSVC 1.5 倍），把元素移动/拷贝到新内存再析构旧的。
- 均摊 O(1)，但某次 `push_back` 可能是 O(n)；扩容时优先走 `noexcept` 的移动构造，否则为强异常安全会复制。
- `reserve(n)` 只改容量，不构造元素；`resize(n)` 改元素个数，变多会值初始化新元素、变少会析构尾部元素。
- 实践：已知规模先 `reserve`；`clear()` 只销毁元素不释放容量，要释放用 `shrink_to_fit()` 或 `swap` 空 vector。
- 追问点：`vector<bool>` 是位压缩的特化，`&v[0]` 取不到地址，别当普通容器用；C++11 起 `data()` 可以传给 C 接口。

```cpp
std::vector<int> v;
v.reserve(1000);          // 只改容量，不构造
std::cout << v.size() << ' ' << v.capacity() << '\n';   // 0 1000
v.resize(10);             // size 变 10，元素值为 0
v.push_back(1);           // 在容量范围内，不会重新分配
```

### Q57 迭代器失效是什么？各容器的失效规则？
**答**：
- 迭代器失效：容器结构变了，旧迭代器指向的位置被释放或挪走，继续用就是 UB；这是「迭代中删除元素」出事的主因。
- `vector`/`string`：发生扩容时**所有**迭代器、指针、引用失效；不扩容时，被删/被插位置之后的迭代器失效。
- `deque`：头尾插入只让**迭代器**失效（引用仍然有效），中间插入删除全失效；`list`/`forward_list`/`map` 的插入不影响其他迭代器，删除只让被删节点的迭代器失效。
- 正确删除法：`it = v.erase(it);`（erase 返回下一个合法迭代器），或者用 `std::remove_if` + `erase` 的 erase-remove 惯用法。
- 追问点：`unordered_map` 的 rehash 会让除被删元素外的迭代器全部失效（但指针/引用仍有效）；`map` 的迭代器失效时，指向元素的指针和引用仍有效；`reserve` 能避免 rehash。

```cpp
// 错误：erase 后 it 失效，再 ++ 是 UB
for (auto it = v.begin(); it != v.end(); ++it)
    if (*it % 2 == 0) v.erase(it);

// 正确 1：用 erase 的返回值
for (auto it = v.begin(); it != v.end(); )
    if (*it % 2 == 0) it = v.erase(it); else ++it;

// 正确 2：erase-remove 惯用法
v.erase(std::remove_if(v.begin(), v.end(), [](int x) { return x % 2 == 0; }), v.end());
```

### Q58 `map` 和 `unordered_map` 有什么区别？怎么选？
**答**：
- `map` 是红黑树（平衡 BST），有序、查找/插入/删除 O(log n)；`unordered_map` 是哈希表，平均 O(1)、最坏 O(n)，无序但迭代快。
- 哈希表的哈希函数要稳：自定义类型做 key 时必须提供 `std::hash` 特化或自定义 Hash，还要写 `operator==`（判定相等）。
- 选择：需要按 key 有序遍历、区间查询（`lower_bound`）、稳定性要求 → `map`；纯按 key 查、量大 → `unordered_map`。
- 性能坑：`unordered_map` 有 rehash（桶数不够会重建，迭代器失效），可先 `reserve(n)`；负载因子默认 1.0，可以 `max_load_factor` 调整。
- 追问点：`map` 的 `operator[]` 会**默认构造**不存在的元素（所以 const map 不能用 `[]`，要用 `find`/`at`）；`unordered_map` 的 `[]` 同理；`std::set`/`unordered_set` 的迭代器都是 const，别想着改 key。

### Q59 `emplace_back` 和 `push_back` 有什么区别？
**答**：
- `push_back` 接收一个已经构造好的对象（值或引用），需要时再移动/拷贝进容器；`emplace_back` 接收**构造参数**，直接在容器内存上原地构造，省掉一次临时对象。
- 效果上：`v.emplace_back(1, 2)` 等价于 `v.push_back(Widget(1, 2))` 但少一次移动；对 `int`、指针这类平凡类型没差别。
- 不是永远更快：如果已经有现成对象，`emplace_back(obj)` 和 `push_back(obj)` 一样要构造；而且 `emplace` 的隐式构造可能绕过 `explicit`，带来意外的重载。
- `emplace` 系列还有 `emplace`/`insert`（map 用 `emplace(k, v)` 或 `try_emplace(k, v)`）；`try_emplace` 在 key 已存在时不构造 value，比 `emplace` 更省。
- 追问点：容器元素要支持移动或拷贝（或原地构造）；`emplace_back` 可以返回引用（C++17 起），方便链式继续操作。

```cpp
struct Widget {
    Widget(int a, int b) { std::cout << "ctor\n"; }
    Widget(const Widget&) { std::cout << "copy\n"; }
};

std::vector<Widget> v;
v.reserve(10);
v.push_back(Widget(1, 2));   // ctor + copy
v.emplace_back(1, 2);        // 只有 ctor

std::map<int, std::string> m;
m.try_emplace(1, "a");       // key 已存在时不构造 "a"
```

### Q60 迭代器和指针有什么关系？五类迭代器有什么不同？
**答**：
- 迭代器是「泛化的指针」，提供 `*`、`->`、`++`、`==` 等操作；指针本身是合法的随机访问迭代器。
- 五个类别：Input（只读单遍，如 `istream_iterator`）、Forward（可多遍，`forward_list`）、Bidirectional（可 `--`，`list`/`map`）、RandomAccess（可 `+n`、比较大小，`vector`/`deque`）、Contiguous（C++20，内存连续，`data()` 可取，`vector`/`string`）。
- 算法按迭代器类别限定能力：`std::sort` 要随机访问，所以不能用在 `list` 上（`list` 有自己的 `sort`）；`std::find` 只要 Input。
- `iterator_traits` 把迭代器映射到 `value_type`/`difference_type`，泛型算法靠它写与容器无关的代码；C++20 的 `std::ranges` 用 concepts 表达这层约束。
- 追问点：C++20 引入 `std::contiguous_iterator` 和 `std::to_address`，可以安全地把迭代器传给 C API；`reverse_iterator` 的 `base()` 指向的位置比它「右一格」这个细节常被考。

```cpp
std::list<int> l{1, 2, 3};
// std::sort(l.begin(), l.end());    // 编译错误：需要随机访问迭代器
l.sort();                            // 用 list 自己的成员

std::vector<int> v{3, 1, 2};
std::ranges::sort(v);                // C++20：直接传容器

auto it = v.begin();
std::cout << std::distance(it, v.end());
```

### Q61 `std::sort` 是什么算法？为什么要求严格弱序？
**答**：
- 标准库实现通常是**内省排序**：快排 + 堆排 + 插入排序的混合（introsort），`std::stable_sort` 是归并排序，`std::partial_sort` 是堆。
- `std::sort` 要求比较器满足**严格弱序**：`comp(a,a)` 必须为假、反对称、可传递；用 `<=` 当比较器就是典型的错误（`a <= a` 为真），可能越界崩溃。
- 常见错误比较器：`return a.x <= b.x;` 应改为 `<`；浮点 NaN 会让比较器不满足严格弱序；比较器里带有状态修改更危险。
- 复杂度：`std::sort` 平均与最坏都是 O(n log n)（introsort 保证最坏情况），不保证稳定；需要稳定用 `std::stable_sort`（可能额外内存）。
- 追问点：`std::sort` 不能用于 `list`；`std::nth_element` 求第 k 大是 O(n)；自定义比较器要 `noexcept` 友好（抛异常会导致容器状态未定义）。

```cpp
std::vector<std::pair<int, std::string>> v{{2, "b"}, {1, "a"}, {2, "a"}};

std::sort(v.begin(), v.end(), [](const auto& x, const auto& y) {
    if (x.first != y.first) return x.first < y.first;  // 严格 <
    return x.second < y.second;
});

// std::stable_sort 保证相等元素保持原相对顺序
```

### Q62 `std::list` 真的比 `std::vector` 差吗？什么时候该用哪些容器？
**答**：
- `vector`：默认选择，连续内存、缓存友好、尾部增删快；中间插入删除 O(n) 但常数小，实践中常常比链表还快。
- `list`：双向链表，插入删除 O(1)（有迭代器时），但每次分配一个节点、内存分散、遍历缓存不友好，实际用到的机会不多。
- `deque`：阻塞式分段连续，头尾插入都快，中间慢；做队列/双端队列首选。
- 其他：`map`/`set` 有序关联，`unordered_*` 哈希，`stack`/`queue`/`priority_queue` 是适配器（底层默认 `deque`/`vector`）。
- 追问点：`vector<unique_ptr<T>>` 比 `list<T*>` 更省、更快；`std::array` 定长栈上数组；`std::flat_map`（C++23）在数据量小、只读场景比 `map` 更快。

### Q63 `std::remove` 为什么不能真正删除元素？erase-remove 惯用法怎么用？
**答**：
- `std::remove` 只做**算法**，它没有拿到容器，只能把不满足条件的元素往前挪，返回新的逻辑结尾；容器大小不变，尾部留着「移过来的重复值」。它属于「移除并重排」，真正的删除要靠容器的 `erase`。
- erase-remove 惯用法：`v.erase(std::remove(v.begin(), v.end(), 3), v.end());`，把逻辑结尾到物理结尾的一段删掉。
- C++20 起有 `std::erase(v, 3)` 和 `std::erase_if(v, pred)`，一行搞定，推荐使用。
- 同原理的还有 `std::unique` + `erase`（去重，前面要先 `sort`）、`std::partition` + erase 做条件删除。
- 追问点：`remove_if` 要求谓词无副作用；`list`/`forward_list` 有成员 `remove`/`remove_if` 才是真删除（O(n) 且不用搬元素）；`std::remove` 对有序容器同样不是删除。

```cpp
std::vector<int> v{1, 2, 3, 2, 4};

auto it = std::remove(v.begin(), v.end(), 2);   // 前移：{1,3,4,?,?}
std::cout << v.size();                          // 仍是 5
v.erase(it, v.end());                           // {1,3,4}

// C++20 一行版
std::erase_if(v, [](int x) { return x != 3; }); // {3}
```

## 八、并发编程

### Q64 `std::thread` 的基本用法和生命周期约定？
**答**：
- C++11 起有标准线程库：`std::thread t(func, args...)`，线程在构造时就启动；参数默认**按值拷贝**，要传引用必须 `std::ref(x)`。
- 每个 `std::thread` 对象在析构前必须 `join()`（等它结束）或 `detach()`（分离），否则析构时 `std::terminate`。
- `detach` 的线程访问了已经销毁的局部变量就是悬空引用，必须保证被引用的东西活到线程结束；主线程退出时 detached 线程也会被强杀。
- 线程对象只能移动不能拷贝；`hardware_concurrency()` 返回建议并发数（可能为 0，不能当权威值）。
- 追问点：`std::jthread`（C++20）析构时自动 join，还能配合 `stop_token` 取消；线程里抛异常没捕获会直接 terminate，要么在线程函数里捕获，要么 `std::packaged_task`/`std::async` 把异常传出去。

```cpp
void work(int id) {
    std::cout << "thread " << id << '\n';
}

int main() {
    int x = 1;
    std::thread t(work, 1);              // 参数按值传
    std::thread t2([&x] { x = 2; });     // 引用捕获
    std::thread t3([xp = &x] { *xp = 3; });   // 等价于传指针
    t.join(); t2.join(); t3.join();      // 必须 join 或 detach
}
```

### Q65 互斥量有哪几种？`lock_guard` 和 `unique_lock` 怎么选？
**答**：
- `std::mutex` 是最基础的互斥量；`std::timed_mutex` 支持 `try_lock_for`；`std::recursive_mutex` 允许同一线程重复加锁（设计上通常说明递归过深，能用别的办法就别用）；`std::shared_mutex`（C++17）读写锁。
- `lock_guard` 最轻量：构造加锁、析构解锁，不能手动解锁、不能条件变量用；`unique_lock` 更大但灵活，可以延迟加锁、提前解锁、转移所有权、配合 `condition_variable`。
- 锁的粒度：只保护共享数据访问，别把耗时操作、IO 放在锁里；多把锁要 `std::lock`/`std::scoped_lock` 一次性加，避免交叉死锁。
- 常见坑：用 `lock_guard` 作用域过大导致性能下降；在锁内调用外部回调（可能重入）；
- 追问点：`std::scoped_lock`（C++17）可以同时锁多个互斥量并用死锁避免算法；`shared_mutex` 读多写少才划算（读锁也是原子操作）。

```cpp
std::mutex m;
int balance = 0;

void deposit(int amt) {
    std::lock_guard<std::mutex> lk(m);      // 作用域结束自动解锁
    balance += amt;
}

// 同时加两把锁，避免死锁
std::mutex m1, m2;
std::scoped_lock lk(m1, m2);
```

### Q66 死锁是怎么产生的？怎么避免？
**答**：
- 死锁四个必要条件：**互斥、占有并等待（请求与保持）、不可剥夺、循环等待**，四个同时满足才可能发生；破坏任意一个就能避免。
- 典型场景：线程 A 持有锁 1 等锁 2、线程 B 持有锁 2 等锁 1（交叉加锁）；条件变量等待没配超时；库里回调时又拿了上层锁（重入）。
- 避免：固定加锁顺序、一次性加全部锁（`std::lock`/`std::scoped_lock`）、用 `try_lock` 失败就放弃并重试、缩小锁作用域、避免在锁内调用外部代码。
- 调试：gdb 里看各线程栈（`thread apply all bt`）、用 TSan（`-fsanitize=thread`）发现锁顺序反转、valgrind 的 Helgrind。
- 追问点：活锁/饥饿和死锁区别；`std::lock` 内部用「先加一个再尝试加另一个，失败则回退」避免循环等待；C++20 的 `std::disable_lock` 用地址排序约束顺序。

### Q67 条件变量怎么正确使用？为什么要用 `while` 而不是 `if`？
**答**：
- `condition_variable` 用于线程间「等某个条件成立」，必须配 `unique_lock<mutex>`（不是 `lock_guard`）和共享的标志位，固定套路是「加锁 → while 判断条件 → wait → 处理」。
- `wait` 会自动释放锁并挂起，被唤醒后重新加锁；用 `while` 而不是 `if` 是因为存在**虚假唤醒**（spurious wakeup），也可能被其他线程先抢走条件。
- `notify_one` 唤醒一个等待者、`notify_all` 唤醒全部；如果条件只满足一个等待者的需求，用 `notify_one`。
- 必须只改共享状态时持锁，然后解锁再 notify 或者持锁 notify 都行，但**改了标志却不 notify** 就是经典的挂死。
- 追问点：C++20 有 `condition_variable_any` 支持任意锁、`std::stop_token` 配合取消；`std::future`/`std::async` 可以免于手写条件变量；谓词版 `wait(lock, pred)` 内部就是 while。

```cpp
std::mutex m;
std::condition_variable cv;
std::queue<int> q;
bool done = false;

// 生产者
void produce() {
    { std::lock_guard<std::mutex> lk(m); q.push(1); }
    cv.notify_one();
}

// 消费者
void consume() {
    std::unique_lock<std::mutex> lk(m);
    cv.wait(lk, [] { return !q.empty() || done; });   // 谓词，抗虚假唤醒
    if (q.empty()) return;                            // done 且空
    int v = q.front(); q.pop();
}
```

### Q68 `std::atomic` 和 `volatile` 有什么区别？什么是内存序？
**答**：
- `std::atomic<T>` 保证操作的**原子性**并提供内存序，是线程间同步的正确工具；`volatile` 只保证不被编译器优化掉，**不保证原子性和可见性**，跨线程同步用它是错的。
- `atomic` 的默认内存序是 `memory_order_seq_cst`（顺序一致性，最安全也最慢）；`relaxed` 只保证原子性、`acquire/release` 保证配对同步（一个线程 release 写，另一个 acquire 读就能看到它之前的写）。
- 经典误区：`x++` 不是原子操作（读-改-写三步），多线程共享计数器要用 `std::atomic<int>` 或加锁。
- `atomic_flag` 是最轻的原子布尔（C++20 起 `atomic_flag::test`）；`atomic<T>.is_lock_free()` 判断是否真的无锁，64 位原子在 32 位平台上可能要加锁。
- 追问点：`fetch_add` 返回旧值，`operator++` 返回新值；`compare_exchange_weak` 会虚假失败，通常放在循环里；`volatile` 的正确用途是硬件寄存器、信号处理里的 `sig_atomic_t`。

### Q69 `std::async` 和手动 `std::thread` 怎么选？`std::future` 是怎么工作的？
**答**：
- `std::async(policy, f, args...)` 返回 `std::future`，把线程管理和结果传递交给库；`f` 抛的异常会保存在 future 里，`get()` 时重新抛出，这一点比裸 `std::thread` 省心。
- 策略：`std::launch::async` 强制新线程、`deferred` 延迟到 `get()`/`wait()` 时才在当前线程执行、默认 `async | deferred` 由实现决定（可能根本不并发）。
- `future.get()` 只能调用一次（之后 `valid()==false`），`std::shared_future` 可以多次读取、可拷贝；`wait_for` 返回 `future_status`。
- 坑：`future` 析构时会**阻塞**等待 async 任务完成（这是标准行为，容易让「忘了 get」变成性能问题）；`deferred` 加析构不会执行。
- 追问点：`std::promise` + `future` 可以手动设置值/异常，做异步回调；`std::packaged_task` 把可调用对象包成任务塞进线程池；C++20 协程是更高层的异步模型。

```cpp
auto f = std::async(std::launch::async, [] {
    throw std::runtime_error("boom");
});
try {
    f.get();                     // 异常在这里重新抛出
} catch (const std::exception& e) {
    std::cout << e.what();
}

std::promise<int> p;
std::future<int> r = p.get_future();
std::thread([&p] { p.set_value(42); }).detach();
std::cout << r.get();
```

### Q70 线程间共享数据的常见坑有哪些？怎么排查数据竞争？
**答**：
- 数据竞争（data race）是 UB：两个线程访问同一内存、至少一个是写、且没有同步，后果可能只是「结果偶尔不对」，也可能整个程序崩掉。
- 常见坑：`shared_ptr` 计数安全但对象不安全；`vector` 在另一个线程扩容时读取；静态局部变量以外的全局状态；`std::cout` 从多线程交错输出。
- 排查：`-fsanitize=thread`（ThreadSanitizer）能直接报竞争位置；`-fsanitize=address` 查内存错误；Valgrind 的 Helgrind/DRD；压力测试 + 随机 sleep 插桩。
- 设计上减少共享：消息队列、线程私有数据（`thread_local`）、不可变数据、每个线程处理独立分区（map-reduce 风格）。
- 追问点：无锁不等于高性能，`compare_exchange_weak` 循环在竞争激烈时可能比 mutex 慢；`std::atomic<int>` 计数器配合伪共享问题需要 `alignas(64)`；面试被问「线程池怎么设计」时要能说出任务队列 + 条件变量 + 优雅退出。

## 面试节奏建议

1. **结论先行**：每题第一句就把判断说出来（「切片是按值传递导致的」「循环引用要用 weak_ptr 破」），再补原因和边界；面试官考的是判断力，不是背原文。
2. **主动说代价**：每个方案都配一句成本——虚函数多一个 vptr、`shared_ptr` 有原子计数、`std::function` 可能堆分配、`list` 缓存不友好；能说出代价，说明真用过。
3. **用小型代码块自证**：答到指针/生命周期类问题时，嘴上给一个 3~5 行的最小例子（切片、悬空引用、erase 失效），比长篇描述有说服力。
4. **追问时给「为什么」而不是「标准这样规定」**：被追问 vtable 布局、内存序、严格弱序时，能说出设计动机（性能/安全/可移植性）才算深入；不确定的部分明确说「这块我按 A 的理解，B 的情况没深究」。
5. **留钩子收尾并反客为主**：答完补一句延伸（「再往下就是无锁队列和内存序模型」），把话题引到自己熟的方向；最后一定要问清团队的技术栈和 C++ 标准版本（C++11/17/20 的答案差别很大）。

> 全部 60 题建议分三次过：第一遍只答结论，第二遍补边界与追问点，第三遍限时手写 Q23（vtable 示意图）、Q31（RAII 封装）、Q49（完美转发）三类的示例代码。
