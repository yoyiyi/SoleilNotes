# C++ STL 标准库

> 面向 C++17：查接口看表格，记用法看代码，避坑看每节末尾，面试前刷第 12、13 章。示例均可单文件编译：`g++ -std=c++17 -Wall -Wextra -g demo.cpp -o demo`。复杂度与失效规则以标准为准，扩容倍数、桶数、`what()` 文案等属实现细节，示例输出按 libstdc++（GCC + Linux）标注。

## 1 STL 六大组件概览

STL 不是「一堆容器」，而是六个互相解耦的组件拼出来的体系：容器负责存，迭代器负责走，算法负责算，仿函数负责「怎么比/怎么算」，适配器负责换接口，分配器负责要内存。

| 组件 | 代表 | 定位 | 与谁配合 |
| --- | --- | --- | --- |
| 容器 | `vector`、`map`、`list` | 管理一段元素集合的存储与生命周期 | 用迭代器暴露元素，用分配器申请内存 |
| 迭代器 | `vector<int>::iterator` | 统一「访问元素」的抽象，是容器与算法之间的桥 | 算法只认**迭代器类别**，不认容器类型 |
| 算法 | `sort`、`find_if`、`copy` | 对区间 `[first, last)` 操作，不关心底层容器 | 用仿函数定制比较，按迭代器类别挑实现 |
| 仿函数 | `less<int>`、`std::hash`、lambda | 把「行为」当对象传参，编译期可内联 | 作为算法的谓词、容器的比较器/哈希器 |
| 适配器 | `stack`、`priority_queue`、`reverse_iterator`、`bind` | 不新建数据结构，只改已有组件的接口形态 | 容器适配器包序列容器，迭代器/函数适配器包迭代器与可调用对象 |
| 分配器 | `std::allocator<T>` | 把「内存从哪来」与「对象怎么构造」解耦 | 每个容器都有 `allocator_type`，默认 `std::allocator` |

一句话记忆：**容器提供区间，迭代器描述区间，算法消费区间，仿函数定制比较，适配器转换接口，分配器供应内存。**

```cpp
#include <algorithm>
#include <functional>
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{5, 3, 9, 1, 7};                                       // 容器
    std::sort(v.begin(), v.end(), std::greater<int>());                      // 算法 + 仿函数
    auto it = std::find_if(v.begin(), v.end(), [](int x) { return x < 5; });  // 算法 + lambda
    std::cout << "降序: ";
    for (auto r = v.rbegin(); r != v.rend(); ++r) std::cout << *r << ' ';     // 反向迭代器适配器
    if (it != v.end()) std::cout << "| 首个小于 5 的元素: " << *it;           // 两端迭代器描述区间
    std::cout << '\n';
    return 0;
}
```

输出：`降序: 9 7 5 3 1 | 首个小于 5 的元素: 3`。

坑：`v.end()` 是尾后位置，不能解引用；所有标准算法都是左闭右开区间。

## 2 容器分类总表

按「元素怎么排」分四类：序列式（保持插入顺序）、关联式（按 key 有序）、无序关联式（哈希桶）、容器适配器（不自己存数据，包一个序列容器）。

| 容器 | 类别 | 底层结构 | 增删查复杂度 | 迭代器失效规则 | 适用场景 |
| --- | --- | --- | --- | --- | --- |
| `vector` | 序列 | 连续动态数组 | 尾部均摊 O(1)、中间 O(n)；随机访问 O(1) | 扩容时全部失效；插入点之后失效 | 默认首选：随机访问 + 尾部增删 + 频繁遍历 |
| `deque` | 序列 | 分段连续（定长块 + 中控数组） | 两端 O(1)、中间 O(n)；随机访问 O(1) | 首尾增删使全部迭代器失效 | 两端进出且要随机访问：滑动窗口、缓冲队列 |
| `list` | 序列 | 双向链表 | 已知位置插删 O(1)、查找 O(n) | 只有被删元素的失效，其余有效 | 频繁中间插删、`splice` 拼链、元素大不想搬 |
| `forward_list` | 序列 | 单向链表 | `insert_after`/`erase_after` O(1)、查找 O(n) | 只有被删元素的失效 | 内存极紧、只需单向遍历 |
| `array` | 序列 | 栈上定长数组，不管内存 | 不能增删；访问 O(1) | 无（长度固定） | 编译期已知大小、与 C 数组互通 |
| `set`/`multiset` | 关联 | 红黑树 | 插删查 O(log n)，有序遍历 O(n) | 只有被删元素的失效 | 有序唯一键集合、范围查询 |
| `map`/`multimap` | 关联 | 红黑树 | 插删查 O(log n) | 只有被删元素的失效 | 有序键值对、按 key 区间遍历 |
| `unordered_set`/`_multiset` | 无序关联 | 哈希表（链地址法） | 平均 O(1)、最坏 O(n) | rehash 时全部失效 | 只判「在不在」、去重 |
| `unordered_map`/`_multimap` | 无序关联 | 哈希表 | 平均 O(1)、最坏 O(n) | rehash 时全部失效 | 计数、缓存、索引映射 |
| `stack` | 适配器 | 默认包 `deque` | `push`/`pop`/`top` 均 O(1) | 同底层容器 | LIFO：括号匹配、DFS |
| `queue` | 适配器 | 默认包 `deque` | `push`/`pop` O(1) | 同底层容器 | FIFO：BFS、任务缓冲 |
| `priority_queue` | 适配器 | 默认包 `vector` + 二叉堆 | `push`/`pop` O(log n)，`top` O(1) | 同底层容器 | 第 K 大、Dijkstra、调度 |

选型速记：不知道选什么就 `vector`；要顺序 → `map`/`set`，只要快 → `unordered_*`；两头进出 → `deque`；已知位置频繁中间插删 → `list`。

```cpp
#include <iostream>
#include <stack>
#include <vector>

int main() {
    std::stack<int> s;                    // 适配器：默认包 deque
    std::stack<int, std::vector<int>> sv; // 显式换底层容器，同样是栈语义
    for (int x : {1, 2, 3}) { s.push(x); sv.push(x); }
    std::cout << "栈顶 " << s.top() << " / " << sv.top() << "，s.size=" << s.size() << '\n';
    return 0;
}
```

输出：`栈顶 3 / 3，s.size=3`。

坑：适配器**没有迭代器**，不能 `for (auto x : s)`；`list` 的「插入 O(1)」前提是**已持有迭代器**，按值找位置仍是 O(n)；`deque` 随机访问虽是 O(1) 但有计算块偏移的常数。

## 3 vector

一段连续内存 + `size`/`capacity` 两个长度。连续意味着随机访问快、遍历缓存友好、能直接喂 C 接口；代价是扩容要搬家。

| API | 说明 | 注意 |
| --- | --- | --- |
| `push_back` / `emplace_back` | 尾部追加，均摊 O(1) | `emplace_back` 原地构造，省一次移动 |
| `pop_back()` | 删除末尾 | 空容器调用是 UB |
| `size()` / `empty()` | 元素个数 / 是否为空 | `size()` 返回 `size_t`，`size()-1` 在 0 时会回绕 |
| `capacity()` | 不重新分配时最多能放多少 | 与 `size()` 无关 |
| `reserve(n)` | 预分配空间，**不改 size** | 仅当 `n > capacity()` 才重分配 |
| `resize(n)` / `resize(n, v)` | 改变 size：变长值初始化或填 v，变短销毁 | 可能扩容；不是「预留」 |
| `at(i)` / `operator[](i)` | 带检查访问（越界抛 `std::out_of_range`）/ 无检查访问（越界 UB） | 调试期优先 `at` |
| `front()` / `back()` | 首/尾元素引用 | 空容器是 UB，`back()` 不是尾后 |
| `data()` | 内部数组裸指针 | 扩容后失效 |
| `clear()` | 清空元素 | **不释放容量** |
| `shrink_to_fit()` | 请求把 capacity 缩到 size | 非强制，实现可忽略 |
| `insert(pos, v)` / `erase(pos)` | 插入/删除 | 插入删除点及之后迭代器失效 |

```cpp
#include <iostream>
#include <stdexcept>
#include <vector>

int main() {
    std::vector<int> v;
    v.reserve(2);                                        // size 仍为 0，只是把容量要到 2
    std::cout << "reserve 后 size=" << v.size() << " cap=" << v.capacity() << '\n';
    v.push_back(10);
    v.push_back(20);
    v.emplace_back(30);                                  // 容量不足，触发扩容
    for (int &x : v) x *= 10;                            // 引用遍历：就地修改
    std::cout << "修改后: ";
    for (const int &x : v) std::cout << x << ' ';
    std::cout << "\nfront=" << v.front() << " back=" << v.back() << " data[1]=" << v.data()[1] << '\n';
    try {
        std::cout << v.at(99) << '\n';                   // 越界，抛 out_of_range
    } catch (const std::out_of_range &) {
        std::cout << "at(99) 抛 out_of_range\n";
    }

    std::vector<std::vector<int>> grid(3, std::vector<int>(4, 0));   // 二维：vector of vector
    grid[1][2] = 7;
    std::cout << "二维 grid[1][2]=" << grid[1][2] << " 行列=" << grid.size() << 'x' << grid[0].size() << '\n';
    return 0;
}
```

输出：`reserve 后 size=0 cap=2`、`修改后: 100 200 300`、`front=100 back=300 data[1]=200`、`at(99) 抛 out_of_range`、`二维 grid[1][2]=7 行列=3x4`。

坑：① `for (int x : v)` 是拷贝，改 `x` 不影响容器，要 `for (int &x : v)`；元素是大对象时一律 `const auto &`；② 二维 `vector` 每行独立分配，行优先访问比列优先快得多。

### 3.1 扩容机制

`size == capacity` 时再插入：申请更大的连续块 → 把旧元素移动/拷贝过去 → 释放旧块。常见策略是 **libstdc++/libc++ 约 2 倍，MSVC 约 1.5 倍**，标准只要求均摊 O(1)，不规定倍数。为什么必须**成倍**：若每次只加 1，插入 n 个元素要拷贝 1+2+…+n ≈ n²/2 次；按 k 倍增长，累计拷贝约为 n/(k−1) 的几何级数，均摊到每次插入是常数。k 太小则摊还常数变大，实践取 1.5~2。

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v;
    std::size_t oldCap = v.capacity();
    for (int i = 0; i < 10; ++i) {
        v.push_back(i);
        if (v.capacity() != oldCap) {
            std::cout << "追加第 " << i << " 个时扩容: " << oldCap << " -> " << v.capacity() << '\n';
            oldCap = v.capacity();
        }
    }
    std::cout << "最终 size=" << v.size() << " cap=" << v.capacity() << '\n';
    return 0;
}
```

libstdc++ 输出（2 倍序列）：`0 -> 1`、`1 -> 2`、`2 -> 4`、`4 -> 8`、`8 -> 16`，最终 `size=10 cap=16`。MSVC 则是 `0->1, 1->2, 2->3, 3->4, 4->6, 6->9` 的 1.5 倍序列——**所以不要把 capacity 数值写进业务逻辑或断言。**

坑：扩容时若元素的移动构造未声明 `noexcept`，`vector` 为保证强异常安全会**退化成拷贝**，大对象上代价翻倍；解决方式是给移动构造加 `noexcept`。

### 3.2 迭代器失效与 shrink_to_fit

| 操作 | 是否可能扩容 | 失效范围 |
| --- | --- | --- |
| `push_back`/`emplace_back` | 可能 | 扩容：全部；不扩容：仅 `end()` |
| `insert`/`emplace`/`erase` | `insert` 可能 | 插入/删除点及**其后**全部 |
| `reserve(n > cap)` / `resize` 变大 | 会/可能 | 全部（元素值不变） |
| `clear()` / `pop_back()` | 否 | 被删元素及其后（`clear` 后全部） |
| `[]`/`at`/`front`/`back` | 否 | 不失效 |

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v;
    v.reserve(1000);                                     // 预留 1000 → 不会扩容
    int *p = v.data();
    auto it = v.begin();
    v.push_back(1);
    std::cout << "*it=" << *it << " *p=" << *p << '\n';  // 两者仍有效

    v.clear();                                           // 只析构元素
    std::cout << "clear 后 size=" << v.size() << " cap=" << v.capacity() << '\n';   // 0 / 1000
    v.shrink_to_fit();                                   // 非强制请求
    std::cout << "shrink_to_fit 后 cap=" << v.capacity() << '\n';   // libstdc++: 0
    std::vector<int>(v).swap(v);                         // swap 技巧：强制归还内存
    std::cout << "swap 技巧后 cap=" << v.capacity() << '\n';
    return 0;
}
```

输出：`*it=1 *p=1`、`clear 后 size=0 cap=1000`、`shrink_to_fit 后 cap=0`、`swap 技巧后 cap=0`。

坑：① 反面教材 `auto it = v.begin(); v.push_back(x); std::cout << *it;`——一旦触发扩容 `it` 就悬空，解引用是 UB，先 `reserve` 或用下标；② 长驻对象曾装过百万条数据，`clear()` 后内存仍在进程里，但对「还要继续复用」的容器别做 `shrink_to_fit`，下次插入又得扩容。

## 4 deque 与 list

`deque` 是「多块定长连续缓冲 + 指向这些块的中控数组」，所以两端插入不用搬动其他元素，随机访问仍是 O(1)（代价是多算一次块偏移）。它**没有 `data()`**，元素不连续，不能把 `&dq[0]` 当 C 数组传出去；`list` 则是双向链表，每元素多两个指针、缓存命中差，迭代器是**双向**的（不能 `it + 3`，只能 `++`），优势在「已持有位置」的插删和 `splice`。

```cpp
#include <deque>
#include <iostream>
#include <list>

int main() {
    std::deque<int> dq{2, 3};
    dq.push_front(1);                                  // 头插 O(1)
    dq.push_back(4);
    std::cout << "deque: front=" << dq.front() << " back=" << dq.back() << " dq[2]=" << dq[2] << '\n';

    std::list<int> a{1, 2, 3}, b{10, 20};
    auto it = a.begin();
    std::advance(it, 2);                               // 双向迭代器，advance 是 O(n)
    a.splice(it, b);                                   // 整链拼到 3 之前，不拷贝元素，O(1)
    a.push_front(99);
    for (int x : a) std::cout << x << ' ';
    std::cout << "\nb.size=" << b.size() << '\n';
    return 0;
}
```

输出：`deque: front=1 back=4 dq[2]=3`、`99 20 10 3 2 1`、`b.size=0`。

何时选 `list`：① 频繁在已定位位置插删，且插删次数与遍历同量级；② 元素大、移动昂贵，而 `vector` 中间插入要搬后半段；③ 需要 `splice`/`merge` 在 O(1) 内拼链；④ 需要「插删不影响其他元素迭代器」的强稳定保证。

坑：`std::sort(l.begin(), l.end())` **编译不过**（要随机访问迭代器），用 `l.sort()`；`deque` 的 `push_front` 会使全部迭代器失效。

`forward_list` 一句话：单向链表，比 `list` 省一个指针，只能 `insert_after`/`erase_after` 单向操作，也没有 `size()`。

## 5 map 与 set

底层是**红黑树**：自平衡 BST，插删查最坏都是 O(log n)，元素按 key 有序存放。所以遍历天然有序、支持 `lower_bound`/`upper_bound` 范围查询，但每次操作有 O(log n) 开销。

| 操作 | `set` | `map` |
| --- | --- | --- |
| 插入 | `insert(v)` / `emplace(args)` | `insert({k,v})` / `emplace(k,v)`；key 已存在则**不覆盖** |
| 查找 | `find(v)` / `count(v)` / C++20 `contains` | `find(k)` / `count(k)` |
| 删除 | `erase(v)` | `erase(k)`；`erase(it)` 返回下一个迭代器 |
| 范围 | `lower_bound(v)`：首个 ≥；`upper_bound`：首个 > | 同左 |
| 访问 | `*it` | `it->second`（key 是 `const`，改不了） |

```cpp
#include <iostream>
#include <map>
#include <set>
#include <string>

int main() {
    std::set<int> s{3, 1, 2, 3, 2};                    // 重复值自动去掉
    std::map<std::string, int> score{{"Bob", 60}, {"Alice", 95}};
    score["Carol"] = 70;                               // 插入
    score["Bob"] = 66;                                 // 已存在 → 修改
    auto [it, ok] = score.insert({"Alice", 0});        // 已存在 → 插入失败，不覆盖

    std::cout << "set size=" << s.size() << " 遍历: ";
    for (int x : s) std::cout << x << ' ';
    std::cout << "\nlower_bound(2)=" << *s.lower_bound(2) << " upper_bound(2)=" << *s.upper_bound(2);
    std::cout << "\n重复插入 ok=" << ok << " Alice=" << it->second << '\n';
    for (const auto &kv : score) std::cout << kv.first << ':' << kv.second << ' ';
    return 0;
}
```

输出：`set size=3 遍历: 1 2 3`、`lower_bound(2)=2 upper_bound(2)=3`、`重复插入 ok=0 Alice=95`、`Alice:95 Bob:66 Carol:70`。

### 5.1 operator[] 的坑：会插入默认值

`m["k"]` 的语义是「返回引用，不存在就默认构造一个插进去」——**读也会写**。于是 `if (m["k"])`、`int v = m["k"];` 都会悄悄增加元素；`map` 的 value 还必须有默认构造函数，否则 `operator[]` 编不过。

```cpp
#include <iostream>
#include <map>
#include <string>

int main() {
    std::map<std::string, int> m{{"a", 1}};
    int v = m["b"];                                    // 坑：读操作却插入了 b
    std::cout << "m[\"b\"]=" << v << " size=" << m.size() << '\n';   // 0 / 2
    if (m.find("c") == m.end()) {
        std::cout << "find 不插入，size 仍为 " << m.size() << '\n';
    }
    try {
        (void)m.at("c");                               // 查不到 → 抛 out_of_range
    } catch (const std::out_of_range &) {
        std::cout << "at 抛 out_of_range\n";
    }
    return 0;
}
```

输出：`m["b"]=0 size=2`、`find 不插入，size 仍为 2`、`at 抛 out_of_range`。只读用 `find`/`count`/`at`（C++20 用 `contains`）；「不存在才插入」用 `insert`/`emplace`/`try_emplace`（C++17）。

### 5.2 emplace、insert 与自定义比较器

- `insert` 接收**已构造好的对象**（或 `pair`），外面构造一次、容器里再移动一次。
- `emplace` 接收**构造参数**，在容器内部原地构造，省掉临时对象。
- `emplace` 不总是更快：传入的就是同类型对象时一样要移动；它还能绕过 `explicit` 的隐式转换检查。比较器则是**模板参数里的类型**，默认 `std::less<Key>`。

```cpp
#include <cctype>
#include <functional>
#include <iostream>
#include <set>
#include <string>
#include <vector>

struct Item {
    std::string name;
    int qty;
    Item(std::string n, int q) : name(std::move(n)), qty(q) {}
};

struct CaseInsensitiveLess {
    static std::string lower(std::string x) {
        for (char &c : x) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        return x;
    }
    bool operator()(const std::string &a, const std::string &b) const {
        return lower(a) < lower(b);                    // 严格弱序，不能用 <=
    }
};

int main() {
    std::vector<Item> v;
    v.emplace_back("apple", 3);                        // 原地构造，无临时对象
    v.push_back(Item("pear", 5));                      // 先构造临时再移动
    for (const auto &it : v) std::cout << it.name << 'x' << it.qty << ' ';

    std::set<std::string, CaseInsensitiveLess> s{"Apple", "apple", "Banana"};
    std::cout << "\n忽略大小写去重: ";
    for (const auto &x : s) std::cout << x << ' ';
    auto cmp = [](int a, int b) { return a > b; };     // 降序
    std::set<int, decltype(cmp)> desc(cmp);            // lambda 要传类型 + 实例（C++17）
    desc.insert({3, 1, 2});
    for (int x : desc) std::cout << x << ' ';
    std::cout << '\n';
    return 0;
}
```

输出：`applex3 pearx5`，第二行 `忽略大小写去重: Apple Banana 3 2 1`。

比较器的三个要求：类型要写进模板参数（lambda 需 `decltype` + 传实例）、**严格弱序**（`comp(a,a)` 必须为 false，用 `<=` 会丢元素）、纯函数无副作用。带比较器的 `set`/`map` 与默认的是**不同类型**，不能互相赋值或 `swap`；只想要倒序遍历，`map` 用 `rbegin()` 更省事。

## 6 unordered_map 与哈希容器

底层是**哈希表**（链地址法）：哈希函数把 key 映射到桶，桶里挂链表。平均 O(1)，但常数比 `map` 大；遍历顺序由哈希值决定，**不保证任何顺序**。

- `bucket_count()`：桶数；`load_factor() = size() / bucket_count()`；`max_load_factor()` 默认 1.0。
- `load_factor() > max_load_factor()` 时插入会触发 **rehash**：桶变多、全部元素重挂。
- `rehash(n)` 强制桶数 ≥ n；`reserve(n)` 按 n 个元素预估，提前把桶开够。

```cpp
#include <cstddef>
#include <functional>
#include <iostream>
#include <string>
#include <unordered_map>
#include <unordered_set>

struct Point {
    int x, y;
    bool operator==(const Point &o) const { return x == o.x && y == o.y; }
};

struct PointHash {
    std::size_t operator()(const Point &p) const noexcept {
        std::size_t hx = std::hash<int>{}(p.x), hy = std::hash<int>{}(p.y);
        return hx ^ (hy + 0x9e3779b9u + (hx << 6) + (hx >> 2));   // 组合，避免 (x,y) 与 (y,x) 同哈希
    }
};

int main() {
    std::unordered_map<int, int> um;
    std::cout << "max_load_factor=" << um.max_load_factor() << '\n';
    um.reserve(100);                                   // 避免反复 rehash
    for (int i = 0; i < 100; ++i) um[i] = i * i;
    std::cout << "size=" << um.size() << " bucket_count=" << um.bucket_count()
              << " load_factor=" << um.load_factor() << '\n';
    um.rehash(256);
    std::cout << "rehash(256) 后 bucket_count=" << um.bucket_count() << '\n';

    std::unordered_map<Point, std::string, PointHash> mp;
    mp[{1, 2}] = "a";                                  // 自定义 key；也可用 emplace/try_emplace
    mp[{2, 1}] = "b";
    std::cout << "Point: size=" << mp.size() << ' ' << mp.at({1, 2}) << mp.at({2, 1}) << '\n';

    // 最坏情况：所有 key 落进同一个桶，查找退化成链表遍历 O(n)
    struct BadHash {
        std::size_t operator()(const std::string &) const { return 0; }
    };
    std::unordered_set<std::string, BadHash> us{"a", "b", "c"};
    std::cout << "BadHash: bucket_count=" << us.bucket_count()
              << " bucket(\"a\") 内元素数=" << us.bucket_size(us.bucket("a")) << '\n';
    return 0;
}
```

libstdc++ 输出示例：`max_load_factor=1`、`size=100 bucket_count=127 load_factor≈0.787`、`rehash(256) 后 bucket_count=257`、`Point: size=2 ab`、`BadHash: bucket_count=13 bucket("a") 内元素数=3`（桶数依实现，勿写死）。

坑：① `std::hash<std::string>` 的**值不保证跨版本/跨平台一致**（libstdc++ 还加了随机种子），把哈希值持久化或用于协议是错的；② 恶意构造 key 可触发哈希退化 DoS，libstdc++ 对 `std::string` 有随机化种子兜底，自己的哈希器没有。

`map` 与 `unordered_map` 选型：

| 维度 | `map` | `unordered_map` |
| --- | --- | --- |
| 复杂度 | O(log n) 稳定 | 平均 O(1)，最坏 O(n) |
| 遍历顺序 | 按 key 有序 | 不确定，rehash 后还会变 |
| 迭代器失效 | 只有被删的失效 | rehash 时全部失效 |
| key 要求 | `<`（严格弱序） | `==` + hash |
| 范围查询 | 支持 `lower_bound` | **不支持** |
| 小数据量 | 常数小，常更快 | 有哈希开销 |
| 典型场景 | 顺序输出、区间统计、配置表 | 计数、缓存、去重、索引 |

一句话：**要顺序或范围 → `map`；只要「按 key 快速找」→ `unordered_map`（记得 `reserve`）；小数据量两者差别不大，实测为准。**

## 7 迭代器

迭代器是容器与算法之间的合同：**算法只声明需要哪一类迭代器能力**，容器提供对应类别的迭代器，两者就能组合。

| 类别 | 能力 | 典型来源 |
| --- | --- | --- |
| 输入迭代器（Input） | 只读、单遍、可 `++` | `istream_iterator` |
| 输出迭代器（Output） | 只写、单遍 | `back_inserter`、`ostream_iterator` |
| 前向迭代器（Forward） | 可读写、多遍、可保存位置 | `forward_list`、`unordered_*` |
| 双向迭代器（Bidirectional） | 可 `--` | `list`、`set`、`map` |
| 随机访问迭代器（RandomAccess） | `it + n`、`it[n]`、比较大小、相减 | `vector`、`deque`、`array`、`array 指针` |

常用取法：`begin()`/`end()` 普通迭代器，`cbegin()`/`cend()` 只读，`rbegin()`/`rend()` 反向，`std::size(v)`/`std::empty(v)`（C++17 统一接口）。`iterator` 可转 `const_iterator`，反过来不行。

```cpp
#include <algorithm>
#include <iostream>
#include <iterator>
#include <list>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3};
    for (auto it = v.cbegin(); it != v.cend(); ++it) std::cout << *it << ' ';   // 只读
    std::cout << '|';
    for (auto it = v.rbegin(); it != v.rend(); ++it) std::cout << *it << ' ';   // 反向
    std::cout << '|';
    std::list<int> l{4, 5, 6};
    auto it = l.begin();
    std::advance(it, 2);                                                      // 双向只能 ++/--
    std::cout << '*advance(list,2)=' << *it << '|';
    std::vector<int> out;
    std::copy(v.begin(), v.end(), std::back_inserter(out));                   // 输出迭代器
    std::cout << "out.size=" << out.size() << '\n';
    return 0;
}
```

输出：`1 2 3 |3 2 1 |*advance(list,2)=6|out.size=3`。

迭代器失效总表：

| 容器 | 插入 | 删除 | 备注 |
| --- | --- | --- | --- |
| `vector` | 扩容时全失效，否则插入点后失效 | 删除点及之后失效 | 指针/引用同理 |
| `deque` | 首尾插入：全失效 | 首尾删除：被删的失效 | 中间插删：全部失效 |
| `list`/`forward_list` | 不失效 | 被删元素失效 | 最稳定 |
| `set`/`map`/`multiset`/`multimap` | 不失效 | 被删元素失效 | 其余元素引用保持有效 |
| `unordered_*` | rehash 时全失效 | 被删元素失效 | 先 `reserve` 可避免 rehash |

坑：**在循环里 `erase` 必须用返回值接住迭代器**——`for (auto it = v.begin(); it != v.end(); ++it) if (bad(*it)) v.erase(it);` 在 `erase` 后就 `++it` 是 UB。正确写法 `it = v.erase(it);`（`erase` 返回下一个位置，循环里不要再 `++`）。

## 8 algorithm 常用算法

全部在 `[first, last)` 上工作。区分三组容易混的：**拷贝版**（`copy`/`remove`/`unique` 只重排、不动容器大小）、**原地版**（`sort`/`reverse`/`shuffle`）、**查询版**（`find`/`count`/`all_of`）。

| 算法 | 一行说明 | 复杂度 |
| --- | --- | --- |
| `sort` / `stable_sort` | 不稳定排序 / 保持相等元素相对顺序的排序 | O(n log n) |
| `partial_sort` / `nth_element` | 只排前 k 个 / 只要第 n 个就位（左边都不大于它） | O(n log k) / 平均 O(n) |
| `find` / `find_if` / `count` | 找值 / 找第一个满足谓词的元素 / 计数 | O(n) |
| `lower_bound` / `upper_bound` / `binary_search` | **已排序**区间中首个 ≥ / 首个 > / 是否存在 | O(log n) |
| `accumulate`（`<numeric>`） | 累加/折叠，初值类型决定结果类型 | O(n) |
| `transform` / `copy` / `copy_if` | 逐元素变换 / 拷贝 / 条件拷贝到输出区间 | O(n) |
| `remove` + `erase` | erase-remove 惯用法：`remove` 只搬不删 | O(n) |
| `unique` | 去掉**相邻**重复，要先排序才能去全局重复 | O(n) |
| `reverse` / `max_element` | 原地反转 / 返回最大元素迭代器 | O(n) |
| `for_each` / `all_of` / `any_of` | 逐元素施加函数 / 全满足 / 存在满足 | O(n) |

```cpp
#include <algorithm>
#include <iostream>
#include <iterator>
#include <numeric>
#include <vector>

int main() {
    std::vector<int> v{5, 3, 9, 1, 7, 3};
    std::sort(v.begin(), v.end());                       // 1 3 3 5 7 9
    std::cout << "sort: "; for (int x : v) std::cout << x << ' ';

    std::cout << "\nfind(7) 距离=" << (std::find(v.begin(), v.end(), 7) - v.begin());
    std::cout << " find_if(>6)=" << *std::find_if(v.begin(), v.end(), [](int x) { return x > 6; });
    std::cout << " count(3)=" << std::count(v.begin(), v.end(), 3);

    std::cout << "\nlower_bound(3)=" << *std::lower_bound(v.begin(), v.end(), 3);
    std::cout << " upper_bound(3)=" << *std::upper_bound(v.begin(), v.end(), 3);
    std::cout << " binary_search(5)=" << std::binary_search(v.begin(), v.end(), 5);
    std::cout << " accumulate=" << std::accumulate(v.begin(), v.end(), 0) << '\n';

    std::vector<int> sq{1, 9, 9, 25, 49, 81};
    std::partial_sort(sq.begin(), sq.begin() + 3, sq.end());       // 只保证前 3 小
    std::cout << "partial_sort 前 3: "; for (int i = 0; i < 3; ++i) std::cout << sq[i] << ' ';
    std::vector<int> top{9, 1, 7, 3, 5};
    std::nth_element(top.begin(), top.begin() + 2, top.end());     // 第 3 小 = 5
    std::cout << " nth_element(2)=" << top[2] << '\n';

    std::vector<int> dup{1, 2, 2, 3, 3, 3};
    dup.erase(std::unique(dup.begin(), dup.end()), dup.end());     // unique 只去相邻重复
    std::cout << "unique 后: "; for (int x : dup) std::cout << x << ' ';
    std::vector<int> raw{2, 4, 5, 6, 9};
    raw.erase(std::remove_if(raw.begin(), raw.end(), [](int x) { return x % 2 == 0; }), raw.end());
    std::cout << " erase-remove 去偶数: "; for (int x : raw) std::cout << x << ' ';
    std::vector<int> src{1, 2, 3}, dst;
    std::copy(src.begin(), src.end(), std::back_inserter(dst));    // copy 写到输出迭代器
    std::transform(src.begin(), src.end(), src.begin(), [](int x) { return x * 10; });
    std::cout << " copy 后 dst.size=" << dst.size() << " transform 后: ";
    for (int x : src) std::cout << x << ' ';
    std::reverse(v.begin(), v.end());                              // 9 7 5 3 3 1
    int sum = 0;
    std::for_each(v.begin(), v.end(), [&sum](int x) { sum += x; });
    std::cout << "\nreverse 后 max_element=" << *std::max_element(v.begin(), v.end())
              << " for_each 求和=" << sum;
    std::cout << " all_of(>0)=" << std::all_of(v.begin(), v.end(), [](int x) { return x > 0; })
              << " any_of(>8)=" << std::any_of(v.begin(), v.end(), [](int x) { return x > 8; }) << '\n';
    return 0;
}
```

输出：

```text
sort: 1 3 3 5 7 9
find(7) 距离=4 find_if(>6)=7 count(3)=2
lower_bound(3)=3 upper_bound(3)=5 binary_search(5)=1 accumulate=28
partial_sort 前 3: 1 9 9 nth_element(2)=5
unique 后: 1 2 3 erase-remove 去偶数: 5 9 copy 后 dst.size=3 transform 后: 10 20 30
reverse 后 max_element=9 for_each 求和=28 all_of(>0)=1 any_of(>8)=1
```

坑：① `lower_bound`/`binary_search` **必须**作用在已排序区间，否则结果是错的但不报错；② `remove`/`unique` **不会删除元素**，只是把保留的元素往前搬并返回新逻辑尾，必须配合 `erase`，这个惯用法叫 erase-remove；③ `list` 不能用 `std::sort`，用成员 `sort()`；④ `accumulate` 的初值若写 `0` 而元素是 `long long`，会按 `int` 累加截断；⑤ `stable_sort` 和 `sort` 的语义差别只在「相等元素是否保序」，需要多关键字稳定排序时先用 `stable_sort`。

## 9 函数对象与 lambda

函数对象（仿函数）是「重载了 `operator()` 的类」；lambda 是它的语法糖——编译器为每个 lambda 生成一个匿名闭包类型。两者都能当算法的谓词、容器的比较器。

| 工具 | 用途 | 建议 |
| --- | --- | --- |
| lambda | 就地写谓词，可捕获上下文 | **首选**；捕获只拷需要的，长生命周期捕获注意生命周期 |
| `std::function<R(Args)>` | 类型擦除的可调用对象容器 | 有堆分配/间接调用开销，热路径少用，必须用时传 `const&` |
| `std::bind` | 参数绑定/占位符 | **已过时**，用带捕获的 lambda 代替（可读性、内联性都更好） |
| `std::hash<T>` | 标准哈希仿函数 | `unordered_*` 的默认哈希 |
| `std::greater`/`less`/`plus` | 标准算术/比较仿函数 | 排序、`priority_queue`、`accumulate` 的定制点 |

```cpp
#include <algorithm>
#include <functional>
#include <iostream>
#include <vector>

int add(int a, int b) { return a + b; }

int main() {
    std::vector<int> v{3, 1, 2};
    std::sort(v.begin(), v.end(), [](int a, int b) { return a > b; });   // 无捕获 → 可转函数指针
    for (int x : v) std::cout << x << ' ';

    int base = 10;
    std::function<int(int)> f = [base](int x) { return x + base; };      // 按值捕获 + 类型擦除
    std::cout << "\nfunction(5)=" << f(5);
    std::cout << " bind=" << std::bind(add, 100, std::placeholders::_1)(1)      // 旧写法
              << " lambda=" << [](int x) { return add(100, x); }(1) << '\n';    // 推荐写法
    return 0;
}
```

输出：`3 2 1` / `function(5)=15 bind=101 lambda=101`。

坑：① `std::function` 为空时调用抛 `std::bad_function_call`；② 按引用捕获的变量在 lambda 被保存到容器或异步执行后可能悬空；③ 有捕获的 lambda 不能转成函数指针（C 回调 API 里常见需求，要用无捕获 lambda 或 static 函数）。

## 10 string 与流

| 成员 | 说明 | 坑 |
| --- | --- | --- |
| `size()`/`length()` | 字节数（不含 `\0`） | UTF-8 下不等于「字符数」 |
| `substr(pos, len)` | 取子串，`len` 省略取到末尾 | `pos > size()` 抛 `out_of_range` |
| `find`/`rfind` | 查找，失败返回 `npos` | 与 `size_t` 比较，别和 -1 比 |
| `append`/`operator+=` | 追加 | 循环里逐字符 `+=` 可能多次扩容 |
| `operator+` | 拼接（产生新串） | 链式 `a + b + c` 会产生临时串 |
| `compare` | 三路比较，返回负/0/正 | 不要用 `strcmp(s.c_str(), ...)` |
| `c_str()` / `data()` | 取 C 字符串 | 指针在修改/扩容后失效 |

**`std::string_view`（C++17）**：一个「指针 + 长度」的非拥有视图，构造零拷贝，函数形参用 `std::string_view` 可以同时接收 `const char*`、`std::string`、子串。它**不拥有**数据，绝不能让 view 活过被看的字符串（尤其是临时 `std::string`）。

```cpp
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

int main() {
    std::string s = "hello,world,stl";
    std::cout << "find(',')=" << s.find(',') << " substr=" << s.substr(0, 5)
              << " npos 判断: " << (s.find("xyz") == std::string::npos ? "没找到" : "找到") << '\n';

    std::string_view sv{s};                            // 零拷贝视图
    sv.remove_prefix(6);                               // "world,stl"
    std::cout << "view=" << sv << " size=" << sv.size() << '\n';

    std::cout << "to_string=" << std::to_string(42) << " stoi=" << std::stoi("  123abc") << '\n';
    try {
        std::stoi("abc");                              // 没有数字 → 抛 invalid_argument
    } catch (const std::invalid_argument &) {
        std::cout << "stoi(\"abc\") 抛 invalid_argument\n";
    }

    std::istringstream csv{"10,20,30"};                // stringstream：分割
    std::ostringstream oss;                            // stringstream：格式化
    std::string tok;
    std::vector<int> nums;
    while (std::getline(csv, tok, ',')) { oss << tok << '|'; nums.push_back(std::stoi(tok)); }
    std::cout << "分割后: "; for (int n : nums) std::cout << n << ' ';
    std::cout << "拼回: " << oss.str() << '\n';
    return 0;
}
```

输出：`find(',')=5 substr=hello npos 判断: 没找到` / `view=world,stl size=9` / `to_string=42 stoi=123` / `stoi("abc") 抛 invalid_argument` / `分割后: 10 20 30 拼回: 10|20|30|`。

坑：① `stoi` 的第二个参数能拿到「解析到哪里停」，用来判断是否整个字符串合法；② `std::stoi` 越界抛 `std::out_of_range`，而 `atoi` 静默 UB；③ 不要把 `string_view` 指向临时 `std::string`（`std::string_view sv = std::string("x") + "y";` 直接悬空）；④ `std::getline(std::cin, s)` 与 `std::cin >> x` 混用时，会残留换行符。

## 11 容器适配器与工具类型

适配器只暴露「该用的一部分接口」：`stack` 只有栈顶，`queue` 只有队首队尾，`priority_queue` 只有最大（默认）元素。

| 类型 | 关键接口 | 语义 |
| --- | --- | --- |
| `stack<T, Container=deque<T>>` | `push`/`emplace`/`pop`/`top`/`size`/`empty` | LIFO，`pop()` 无返回值，要先 `top()` |
| `queue<T, Container=deque<T>>` | `push`/`front`/`back`/`pop`/`size`/`empty` | FIFO |
| `priority_queue<T, Container=vector<T>, Compare=less<T>>` | `push`/`top`/`pop` | 大顶堆；小顶堆写 `greater<T>`，或自定义比较器 |

注意三者都**没有**迭代器，不能遍历；`stack<T, vector<T>>` 显式换底层容器是合法写法。

```cpp
#include <functional>
#include <iostream>
#include <queue>
#include <stack>
#include <tuple>
#include <vector>

int main() {
    std::stack<int> st;
    std::queue<int> q;
    std::priority_queue<int> maxHeap;                                        // 大顶堆
    std::priority_queue<int, std::vector<int>, std::greater<int>> minHeap;   // 小顶堆
    for (int x : {1, 2, 3}) { st.push(x); q.push(x); maxHeap.push(x); minHeap.push(x); }
    std::cout << "stack top=" << st.top();
    st.pop();                                                                // pop 无返回值
    std::cout << " pop 后 top=" << st.top() << "\nqueue front=" << q.front() << " back=" << q.back();
    std::cout << "\n大顶堆 top=" << maxHeap.top() << " 小顶堆 top=" << minHeap.top() << '\n';

    auto [name, age, score] = std::make_tuple(std::string("Tom"), 20, 88.5);  // C++17 结构化绑定
    std::cout << "tuple 解包: " << name << ' ' << age << ' ' << score << '\n';
    return 0;
}
```

输出：`stack top=3 pop 后 top=2` / `queue front=1 back=3` / `大顶堆 top=3 小顶堆 top=1` / `tuple 解包: Tom 20 88.5`。

`std::pair` 是两元素特化（`first`/`second`），`std::tuple` 是 N 元组（`std::get<i>`/`std::tie`/结构化绑定），`std::tie` 可做「多返回值 + 比较」。C++17 的三种「可能没有/可能是多个/什么都能装」类型：

| 类型 | 语义 | 取值的正确方式 | 典型用法 |
| --- | --- | --- | --- |
| `std::optional<T>` | 有值或没有值 | `if (o) use(*o);` 或 `o.value_or(d)` | 可能失败的查询，替代「返回 bool + 出参」 |
| `std::variant<A,B,...>` | 类型安全的 union，同一时刻只有一个类型 | `std::get<T>` / `std::get<idx>` / `std::visit` | 状态机、异构结果、解析器 AST 节点 |
| `std::any` | 可装任意类型（类型擦除） | `std::any_cast<T>` | 插件/脚本桥接、弱类型配置，尽量避免 |

```cpp
#include <any>
#include <iostream>
#include <optional>
#include <string>
#include <variant>

int main() {
    std::optional<int> maybe = 42;                     // optional：有值/无值
    std::cout << "optional=" << maybe.value_or(-1) << " 空则=" << std::optional<int>{}.value_or(-1) << '\n';

    std::variant<int, double, std::string> v = 3.14;   // variant：类型安全的 union
    v = std::string("hello");                          // 换类型
    std::cout << "variant 第 " << v.index() << " 个: " << std::get<std::string>(v) << '\n';
    std::visit([](const auto &x) { std::cout << "visit: " << x << '\n'; }, v);
    // std::get<int>(v) 类型不符会抛 bad_variant_access

    std::any a = 42;                                   // any：任意类型（类型擦除）
    a = std::string("now a string");
    std::cout << "any_cast<string>=" << std::any_cast<std::string>(a) << '\n';
    try {
        (void)std::any_cast<int>(a);                   // 类型不对 → 抛 bad_any_cast
    } catch (const std::bad_any_cast &) {
        std::cout << "any_cast<int> 抛 bad_any_cast\n";
    }
    return 0;
}
```

输出：`optional=42 空则=-1` / `variant 第 2 个: hello` / `visit: hello` / `any_cast<string>=now a string` / `any_cast<int> 抛 bad_any_cast`。

坑：`optional<T&>` 不合法（要引用用 `T*` 或 `reference_wrapper`）；`value()` 在空 optional 上抛 `bad_optional_access`；`any` 的拷贝会深拷贝内部对象，热路径慎用；`priority_queue` 的 `pop()` 返回值是 `void`，且 `top()` 是只读引用，改堆内元素会破坏堆性质。

## 12 性能陷阱 15 条

1. **`vector` 不 `reserve`**：循环 `push_back` 几十万次，扩容是 O(n) 级别的搬家，日志里出现大小一涨就卡顿。已知规模先 `reserve`。
2. **`map::operator[]` 访问不存在的键**：读也会插入默认值，容器越来越大、日志/计数里多了 0。只读用 `find`/`at`/`contains`。
3. **`list` 遍历缓存不友好**：节点随机分布，每次 `++` 都可能 cache miss；10 万以内 `int`，遍历通常比 `vector` 慢一个数量级。选 `list` 前先测。
4. **`unordered_map` 频繁 rehash**：不 `reserve` 时随着增长反复重挂元素，插入耗时呈台阶式抖动。已知规模就 `reserve`。
5. **`string` 用 `+` 拼接**：`s = s + a + b` 每步产生临时串，复杂度可能 O(n²)。改 `s += a; s += b;` 或先 `reserve`，多段拼接用 `stringstream`/`append`。
6. **拷贝传参**：`void f(std::vector<int> v)` 会整份拷贝；只读用 `const std::vector<int>&`，要拿所有权用 `std::move` 或按值 + `std::move` 语义。
7. **循环里 `erase` 用法错误**：`for (auto it = v.begin(); it != v.end(); ++it) if (p(*it)) v.erase(it);` 中 `it` 已失效仍 `++`。写 `it = v.erase(it);` 或 erase-remove。
8. **`vector<bool>` 当普通容器用**：它是位压缩特化，没有真正的 `bool&`，`auto& b = v[0]` 编不过，`cbegin()` 返回的也不是指针。要引用语义用 `vector<char>`/`bitset`。
9. **在 `unordered_map` 里存大对象并频繁 `operator[]`**：每次 `[]` 都可能默认构造 + 插入；改用 `try_emplace`/`emplace` 避免临时大对象。
10. **`std::endl` 代替 `'\n'`**：`std::endl` 每次 flush，IO 密集输出时比重排到期末快几倍到几十倍。只在需要立即刷盘时用 `std::endl`。
11. **`std::function` 放在热路径里**：类型擦除有间接调用和可能的堆分配；能用 lambda 模板参数或 `auto` 就不要擦除。
12. **`insert` 位置越靠前越贵**：`vector` 头部 `insert` 每次搬整个数组，循环 n 次插入就是 O(n²)。改成尾部追加再反转，或用 `deque`。
13. **`sort` 的比较函数有副作用或代价高**：比较函数每次 `O(n log n)` 次被调用，里面做字符串构造/查表会直接让排序变慢；lambda 里也别临时 `new`。
14. **用 `set` 去重后忘记 `map` 的 key 是 `const`**：试图排序 `map`/`set` 或用 `std::sort` 作用于它们会编译失败（迭代器不是随机访问，元素也不可变）；它们本来就有序。
15. **`reserve` 过大 / `shrink_to_fit` 乱用**：一次 `reserve(1'000'000)` 再只放 10 个元素，白占内存；`shrink_to_fit` 后下次插入又要扩容，反复 shrink/expand 是最差的组合。

## 13 面试问答 15 题

**1. `vector` 扩容为什么是 2 倍（或 1.5 倍），而不是固定增加？**
按倍数增长时扩容总代价是几何级数，均摊到每次插入是 O(1)；固定 +1 是 O(n) 每次、总代价 O(n²)。倍数也不能太小，否则摊还常数大；2 倍浪费内存稍多，1.5 倍有多版本复用旧内存的可能。

**2. `map` 和 `unordered_map` 怎么选？**
要按 key 有序遍历、范围查询（`lower_bound`）、需要稳定可预测的行为 → `map`；只关心快速查找/计数/去重、不在乎顺序 → `unordered_map` 并 `reserve`。数据量很小时 `map` 常数更小，最好实测。

**3. 迭代器失效的场景有哪些？**
`vector` 扩容全部失效、插入点之后失效；`deque` 首尾插删全失效、中间插删全失效；`list`/关联容器只有被删元素的失效；`unordered_*` 在 rehash 后全部失效。循环里删除要接 `erase` 的返回值。

**4. `size()` 和 `capacity()` 的区别？**
`size` 是真正存活的对象数，`capacity` 是不重新分配时最多能容纳的元素数。访问 `[0, size)` 合法；`reserve` 只改 `capacity`，`resize` 改 `size`；`clear` 改 `size` 不改 `capacity`。

**5. `deque` 为什么两端插入快？为什么 `vector` 头部插入慢？**
`deque` 是分块存储 + 中控数组，头插只在首块前面放，块满就新开一块，不用搬动已有元素；`vector` 头部插入要把整个数组向后挪一格，O(n)。

**6. 为什么 `std::vector<bool>` 特殊？**
它是标准为 `bool` 做的位压缩特化：每个元素占 1 bit，`operator[]` 返回代理对象而非 `bool&`，所以 `&v[0]`、`auto&`、指针互转都不成立，`data()` 也没有。它不是容器概念要求的普通容器，标准委员会也承认这是历史遗留的设计失误。

**7. `map::operator[]` 和 `find` 有什么区别？**
`operator[]` 找不到时会插入一个值初始化的元素并返回引用（读即写），且要求 value 可默认构造；`find` 只查不改，返回迭代器。C++17 起可用 `at`（抛异常）和 C++20 的 `contains`。

**8. 红黑树和哈希表的复杂度、最坏情况对比？**
红黑树插删查稳定 O(log n)，最坏也是 O(log n)；哈希表平均 O(1)，但哈希冲突严重或哈希函数被恶意构造时最坏 O(n)。哈希表还多出 rehash 抖动和不确定的遍历顺序。

**9. `reserve` 和 `resize` 的区别？**
`reserve(n)` 只保证容量不小于 n、不创建元素、不改 `size`；`resize(n)` 改变元素个数，变长时新元素被值初始化。前者用于性能预估，后者用于真正改变大小。

**10. `reserve` 之后 `push_back` 还会失效迭代器吗？**
不会因扩容失效——只要总插入数不超过预留容量。但 `insert`/`erase` 仍会使插入点之后（删除点及其后）的迭代器失效，这是元素移动导致的，与扩容无关。

**11. STL 算法为什么用迭代器而不是容器？**
解耦：算法只依赖迭代器类别（随机访问/双向/前向），因此同一份 `sort` 实现可以服务 `vector`、`deque`、原生数组；容器也不必为每个算法写成员函数，组合数从 M×N 降为 M+N。

**12. `unique` 和 `remove` 为什么不会改变容器大小？**
它们只接收迭代器，不知道容器是否存在、更不知道如何销毁尾部元素，所以只做「把要保留的元素依次搬到前面」，返回新的逻辑尾，再由调用方 `erase(new_end, end())` 才是 erase-remove 惯用法。

**13. `list` 和 `vector` 的插入删除谁快？**
「已持有位置」时 `list` 真 O(1)，`vector` 要搬后半段 O(n)；但 `list` 每次插入都要一次内存分配，且遍历缓存不友好。现实中多数场景 `vector` 反而更快，要用数据说话。

**14. `emplace_back` 一定比 `push_back` 快吗？**
不一定。它省掉临时对象的构造+移动，所以对「需要多个参数构造的贵对象」更快；若传入的已是同类型右值，两者代价相同。它还可能意外通过 `explicit` 构造，语义上更宽松，要看清。

**15. `unordered_map` 的负载因子和 rehash 有什么关系？**
`load_factor = size / bucket_count`，当它超过 `max_load_factor()`（默认 1.0）时，下一次插入会触发 rehash：增加桶数并重新分配所有元素，此时所有迭代器失效。用 `reserve(n)` 提前把桶开够，就能把 rehash 次数降到 0 或 1。

## 参考

- cppreference 容器与算法总览：<https://en.cppreference.com/w/cpp/container>。
- ISO/IEC 14882:2017（C++17）第 21~26 章（容器、迭代器、算法、数值）。
- 《Effective STL》（Scott Meyers）条款 1~7 讲容器选型、`vector` 扩容与 `reserve`。
- 本仓库 `_source_Cpp.md` 第 34 章 STL 原始笔记；[C 标准库速查](../C/C标准库速查.md) 可对照理解 C 头文件对应关系。
