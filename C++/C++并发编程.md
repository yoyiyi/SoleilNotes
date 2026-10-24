# C++ 并发编程
> C++11 起标准线程库的主干笔记，代码默认 **C++17**（仅 `std::jthread` 一节是 C++20），可单文件编译：`g++ -std=c++17 -pthread x.cpp -o x`。
## 1 并发基础
**进程**是资源分配单位，有独立地址空间、文件描述符表；**线程**是 CPU 调度单位，同进程的线程共享地址空间、堆、全局变量，各自独享栈、寄存器、TLS。共享内存让线程通信零成本，也让数据竞争成为常态。
| 对比项 | 进程 | 线程 |
| :--- | :--- | :--- |
| 地址空间 | 独立，隔离性好 | 共享，一个线程崩溃拖垮全进程 |
| 创建/切换 | 大（换页表、TLB 失效） | 小（只分配栈） |
| 通信 | 管道、共享内存、socket | 直接读写共享变量（需同步） |

`std::thread` 是对 pthread / Win32 线程的薄封装：**进程管隔离，线程管并发**。
### 1.1 四种创建方式
构造函数接收可调用对象加参数，**参数默认按值拷贝**到线程内部。

```cpp
void hello(int x) { std::cout << "[函数] " << x << "\n"; }
struct Functor {
    void operator()(int x) const { std::cout << "[对象] " << x << "\n"; }
};
struct Worker {
    void work(int x) const { std::cout << "[成员] " << x << "\n"; }
};
int main() {
    std::thread t1(hello, 1);                                             // 普通函数
    Functor f;
    std::thread t2(f, 2);                                                 // 函数对象（f 被拷贝）
    std::thread t3([n = 3] { std::cout << "[lambda] " << n << "\n"; });    // lambda
    std::thread t4(&Worker::work, Worker{}, 9);                            // 成员函数：对象 + 参数
    for (auto *t : {&t1, &t2, &t3, &t4}) t->join();
}
```
- **对象是拷贝的**：线程里改的是副本；要共享必须显式 `std::ref(f)` / `std::cref(f)`，否则形参写成引用也会退化成拷贝。
- **参数在创建时求值**：`char*` 指向局部数组要当场转成 `std::string`，否则线程启动时可能读到失效内存。
- 成员函数第二个参数是对象：传 `w` 是拷贝、`&w` 是引用，被调对象要活到 join 之后；`thread` 是 move-only，可 `move` 或放进 `vector`。
### 1.2 join 与 detach
`thread` 析构时若仍 `joinable()` 会直接 `std::terminate`——标准强制你交代所有权。
| 对比项 | `join()` | `detach()` |
| :--- | :--- | :--- |
| 含义 | 阻塞直到目标线程结束 | 与目标线程分手，不再干预 |
| 能否拿结果 | 能（配合 `promise`/原子量） | 不能，也没法等 |
| 主要风险 | 主线程被卡住（UI 线程会卡死界面） | 访问已销毁对象；主线程退出时被强杀 |

`detach` 的三个坑：① 线程还在读主线程局部变量，`main` 一返回就悬空；② `main` 结束即进程退出，不保证 detach 线程跑完；③ 静态对象（如 `std::cout`）析构后线程仍在写它。用 detach 时共享数据必须放 `shared_ptr` 或静态存储。经验法则：默认 `join`，只有后台常驻、不关心结束、不碰调用者栈数据的场景（日志刷盘、心跳）才 `detach`，更好的选择是 `jthread` 或线程池。

```cpp
std::vector<std::thread> threads;
for (int i = 0; i < 4; ++i) threads.emplace_back([i] { std::cout << i << " done\n"; });
for (auto &t : threads) t.detach();   // 之后 main 若先返回，这些线程可能读不到 cout
```
### 1.3 std::jthread（C++20）
两个改进：**析构自动 join**；析构时自动 `request_stop()`，线程查 `std::stop_token` 即可优雅退出。

```cpp
// g++ -std=c++20
void worker(std::stop_token st) {            // jthread 自动把 stop_token 注入首参
    while (!st.stop_requested()) std::this_thread::sleep_for(std::chrono::milliseconds(10));
}
int main() {
    std::vector<std::jthread> pool;
    for (int i = 0; i < 3; ++i) pool.emplace_back(worker);
    pool[0].request_stop();   // 主动请求；离开作用域时自动 request_stop + join
}
```
"自动 join"只是把 `join` 挪进析构，**照样阻塞**——线程 `while(true)` 不查 `stop_token`，析构就卡住；取消是**协作式**的，不会强杀线程。C++20 之前可自己写 `thread_guard` 这类 RAII 类替代。
### 1.4 线程数怎么选
- **CPU 密集型**：`硬件线程数 + 1`，多的 1 个填补缺页、缓存未命中的空档；`hardware_concurrency()` 可能返回 0，要兜底成 1。
- **IO 密集型**：`核数 × (1 + 阻塞时间/计算时间)`；工程上更常用固定上限（2 倍核数）加队列削峰。
- 线程不是越多越快：默认栈 8MB（虚拟内存），加上上下文切换、缓存局部性变差、锁竞争加剧；"每请求一线程"在上万并发时会被调度拖垮，容器里 `hardware_concurrency()` 还可能读到宿主机核数而非 cgroup 限额。
## 2 线程同步
`i++` 是"读-改-写"三步，两线程交错就丢更新，互斥量保证同一时刻只有一个线程进临界区。手写 `lock/unlock` 必然某天泄漏一次锁，所以**一律用 RAII 包装器**。

```cpp
int counter = 0;
std::mutex mtx;
for (int k = 0; k < 1000; ++k) {
    mtx.lock();
    ++counter;
    mtx.unlock();   // 中途 return 或抛异常这行就到不了；10 线程各加 1000 次应得 10000
}
```
### 2.1 lock_guard / unique_lock / scoped_lock
```cpp
void guard_style() {
    std::lock_guard<std::mutex> lk(mtx);   // 构造加锁、析构解锁，异常安全
    value = 1;
}
void unique_style() {
    std::unique_lock<std::mutex> lk(mtx, std::defer_lock);   // 先创建，此时未加锁
    value = 2;                                               // 准备数据时不持锁
    lk.lock();
    lk.unlock();                                             // 可提前释放
}
void two_locks(std::mutex &m1, std::mutex &m2) {
    std::scoped_lock lk(m1, m2);   // C++17：一次锁多个，死锁免疫，参数顺序无关
}
```
`unique_lock` 比 `lock_guard` 多出：延迟加锁（`defer_lock`）、只接管已锁的锁（`adopt_lock`）、尝试加锁（`try_to_lock` + `owns_lock()`）、提前 `unlock`/`lock`、`move` 转移所有权，代价是多一个状态位。**条件变量必须配 `unique_lock`**，因为 `wait` 要在等待期间解锁、醒来重新加锁。
### 2.2 其余互斥量与取舍
```cpp
std::recursive_mutex rmtx;
int recur(int n) {                                    // 同一线程可重复加锁
    std::lock_guard<std::recursive_mutex> lk(rmtx);
    return n == 0 ? 0 : n + recur(n - 1);             // recur(5) == 15
}
class Config {
public:
    void set(int v) { std::unique_lock<std::shared_mutex> lk(rw_); value_ = v; }    // 写：独占
    int get() const { std::shared_lock<std::shared_mutex> lk(rw_); return value_; }  // 读：共享
private:
    mutable std::shared_mutex rw_;
    int value_ = 0;
};
std::timed_mutex tmtx;
std::unique_lock<std::timed_mutex> lk(tmtx, std::chrono::milliseconds(100));
if (!lk.owns_lock()) { /* 100ms 没拿到，走降级逻辑 */ }
```
- **`recursive_mutex`**：内部存"持有者 + 计数"，锁几次就要解几次。链式调用、回调重入的权宜之计；能不用就别用，它会掩盖"临界区边界不清"的设计问题。
- **`shared_mutex`（C++17）**：读者用 `shared_lock` 并发进入，写者独占。读者持锁期间不能再申请写锁（自锁）；写者饥饿策略由实现决定；读写差异不明显时普通 `mutex` 往往更快。
- **`timed_mutex`**：`try_lock_for`/`try_lock_until` 超时返回 false，把"卡住"变成"失败"；它**不解决死锁**，只是让故障可见。
| 类型 | 特点 | 典型用途 |
| :--- | :--- | :--- |
| `mutex` | 最基础，不可递归 | 默认选择 |
| `recursive_mutex` | 同线程可重入 | 回调 / 链式调用 |
| `timed_mutex` | 带超时的 `try_lock_for` | 避免无限等待 |
| `shared_mutex` | 读写锁（C++17） | 读多写少 |
| `lock_guard` | 最简 RAII，零额外开销 | 简单临界区 |
| `unique_lock` | 可延迟、可释放、可移动 | 条件变量、需提前解锁 |
| `scoped_lock` | 一次锁多个，死锁免疫 | 多锁场景 |
| `shared_lock` | 读锁 RAII | 配 `shared_mutex` |
## 3 死锁
四个条件必须**同时**成立才会死锁，破坏任一条即可避免：
| 条件 | 含义 | 破坏方式 |
| :--- | :--- | :--- |
| 互斥 | 资源一次只能被一个线程占用 | 尽量用共享 / 无锁结构 |
| 占有并等待 | 持着资源又申请新资源 | 一次性申请所有锁 |
| 不可剥夺 | 资源不能被强行抢走 | `try_lock` 失败就释放已持有的 |
| 循环等待 | 存在环形等待链 | **统一加锁顺序**（最实用） |
工程上 90% 的死锁是"循环等待"。三个常见场景：**① 两把锁顺序不一致**——A 先锁 `m1` 再 `m2`，B 反向，只要各拿到第一把就永远等下去；它是**概率性**的，可能跑一百次才卡一次，这正是死锁难查的原因。**② 递归加锁**——同一线程对 `std::mutex` 重复 `lock()` 是未定义行为，实际多半直接死锁。**③ 条件变量误用**——`wait` 前没拿锁或没配 `unique_lock`（UB 且丢通知）；**持锁时 `join`** 一个要同一把锁的线程；通知发出时没人等待、又没用谓词检查，等待者再也醒不来。

```cpp
// ① 顺序不一致
std::thread a([] { for (;;) { std::lock_guard<std::mutex> x(m1); std::lock_guard<std::mutex> y(m2); } });
std::thread b([] { for (;;) { std::lock_guard<std::mutex> x(m2); std::lock_guard<std::mutex> y(m1); } });
// A 持 m1 等 m2，B 持 m2 等 m1 → 死锁
// ② 递归加锁：拆出不加锁的 _locked 内层版 → 只在最外层加锁 → 最后才考虑 recursive_mutex
void inner() { std::lock_guard<std::mutex> lk(mtx); }
void outer() { std::lock_guard<std::mutex> lk(mtx); inner(); }   // 同线程第二次加锁 → 死锁（UB）
// ③ 持锁时 join：工作线程要 mtx，主线程持锁等它 → 死锁
std::thread t([] { std::lock_guard<std::mutex> lk(mtx); });
std::lock_guard<std::mutex> lk(mtx);
t.join();
```
### 3.1 解决：scoped_lock 与固定顺序
`std::lock` 用"试锁 + 失败就把已拿到的全放开再重来"的算法，即使顺序相反也不会形成循环等待：

```cpp
std::scoped_lock lk(m1, m2);                           // 推荐（C++17）
std::lock(m1, m2);                                     // std::lock 等价写法
std::lock_guard<std::mutex> g1(m1, std::adopt_lock);   // 只接管，不再加锁
std::lock_guard<std::mutex> g2(m2, std::adopt_lock);
```
两个线程都写 `lock(m1, m2)` 或都写 `lock(m2, m1)` 都不会死锁；代价是可能活锁（不断重试）。**固定加锁顺序**则零运行时开销，从源头破坏循环等待——给每把锁一个全局唯一编号，永远按编号从小到大加：

```cpp
struct OrderedLock { int id; std::mutex mtx; };   // id 全局唯一，来自枚举或原子计数
void lock_pair(OrderedLock &a, OrderedLock &b) {
    if (a.id > b.id) std::swap(a, b);             // 保证先 a 后 b
    std::scoped_lock lk(a.mtx, b.mtx);
}
// 更简单的团队约定：任何时刻最多持有一把锁，需要多把时一律 scoped_lock
```
### 3.2 死锁检测思路
- **静态检查**：clang-tidy 的锁相关检查，或 Abseil 加锁注解（`ABSL_GUARDED_BY`、`ABSL_EXCLUSIVE_LOCKS_REQUIRED`），在编译期或评审期暴露加锁契约。
- **TSan**：报 `lock-order-inversion (potential deadlock)`，并给出两把锁各自的加锁点调用栈——最有效的手段。
- **gdb 现场**：`thread apply all bt` 若多条线程都卡在 `pthread_mutex_lock` 且互等，就是死锁。
- **兜底**：长持锁处用 `timed_mutex` 超时告警 + watchdog 定时喂狗，让卡死能被外部发现。
## 4 条件变量
`while(!ready){}` 忙等会跑满 CPU，编译器还可能把 `ready` 缓存进寄存器导致永不退出。条件变量让线程睡眠，由通知方唤醒。

```cpp
std::mutex mtx;
std::condition_variable cv;
bool ready = false;
void notifier() {
    { std::lock_guard<std::mutex> lk(mtx); ready = true; }   // 先改共享状态
    cv.notify_one();                                         // 再通知，且通知时不持锁
}
```
| 接口 | 作用 | 备注 |
| :--- | :--- | :--- |
| `wait(lk)` | 解锁并睡眠，唤醒后重新加锁返回 | 有虚假唤醒，几乎不该直接用 |
| `wait(lk, pred)` | 等价于 `while(!pred()) wait(lk);` | **推荐**，天然抵御虚假唤醒 |
| `wait_for` / `wait_until` | 超时版本 | 返回 `cv_status::timeout` / `no_timeout` |
| `notify_one()` | 唤醒一个等待线程 | 一个消费者时用 |
| `notify_all()` | 唤醒全部 | 状态影响所有等待者（关闭、退出）时用 |
**必须配 `unique_lock`**：`wait` 要在睡眠前解锁、醒来后重新加锁，需要"持有状态可变"的包装器，`lock_guard` 构造后状态就固定了。
### 4.1 虚假唤醒：必须用谓词
**虚假唤醒**指没有任何 `notify` 时 `wait` 也可能返回——POSIX 与 C++ 标准刻意允许（实现更高效）。所以醒来必须重新检查条件，`wait(lk, pred)` 内部就是 `while(!pred()) wait(lk)`：

```cpp
cv.wait(lk);                          // 错：醒来就往下走，ready 可能仍为 false
cv.wait(lk, [] { return ready; });    // 对：条件不满足就继续睡
```
谓词检查的是"**共享状态是否真的满足条件**"，不是"是否被通知过"；读写共享状态必须持锁，`wait(lk, pred)` 已保证这一点。
### 4.2 完整示例：生产者-消费者（带停止标志）
```cpp
template <typename T>
class BlockingQueue {
public:
    bool push(T value) {
        { std::lock_guard<std::mutex> lk(m_); if (closed_) return false; q_.push(std::move(value)); }
        cv_.notify_one();                      // 先改状态，解锁后再通知
        return true;
    }
    bool pop(T &out) {
        std::unique_lock<std::mutex> lk(m_);
        cv_.wait(lk, [this] { return closed_ || !q_.empty(); });   // 谓词同时查停止与数据
        if (q_.empty()) return false;          // 已关闭且排空 → 消费者收工
        out = std::move(q_.front());
        q_.pop();
        return true;
    }
    void close() {
        { std::lock_guard<std::mutex> lk(m_); closed_ = true; }
        cv_.notify_all();                      // 多个消费者都在等，必须全叫醒
    }
private:
    mutable std::mutex m_;
    std::condition_variable cv_;
    std::queue<T> q_;
    bool closed_ = false;
};
// 用法：生产者 push 完调 close()；消费者 while (q.pop(v)) 处理，全部返回后 join
```
细节：谓词同时查 `closed_` 和 `!q_.empty()`，避免关闭时丢掉剩余元素；`push` 解锁后才 `notify_one`（持锁通知等于"唤醒一个等锁的"，白白多一次调度）；`closed_`、返回值都由同一把锁保护。
## 5 原子操作与内存序
`std::atomic<T>` 保证对 `T` 的读写不可分割：要么看到旧值要么看到新值。常用类型：`atomic<bool>`、`atomic<int>`、`atomic<long>`、`atomic<size_t>`、`atomic<T*>`、`atomic<shared_ptr<T>>`（C++20 特化）、`atomic_flag`（保证无锁）。
| 操作 | 说明 |
| :--- | :--- |
| `load(mo)` / `store(v, mo)` | 读 / 写，默认 `seq_cst` |
| `exchange(v, mo)` | 写入并返回旧值 |
| `fetch_add/sub/or/xor` | 读-改-写，返回**旧值**（`operator++` 返回新值） |
| `compare_exchange_weak(e, d)` | CAS，允许伪失败，适合循环 |
| `compare_exchange_strong(e, d)` | CAS，不伪失败，可能多一条指令 |
| `is_lock_free()` | 运行时判断是否单条指令实现 |
| `atomic_flag::test_and_set/clear` | 最简 CAS，标准保证无锁 |
CAS 语义：**当前值 == `expected` 就写入 `desired` 返回 true；否则把当前值写回 `expected` 返回 false**。这个"失败回写"是写循环的关键：

```cpp
std::atomic<int> cnt{0};
int expected = 0, old = 0;
bool ok = cnt.compare_exchange_weak(expected, 10);   // 1 10
expected = 5;
ok = cnt.compare_exchange_weak(expected, 20);        // 0 10（失败把当前值写回 expected）
while (!cnt.compare_exchange_weak(old, old + 1)) { } // 无锁自增：失败时 old 已是新值，直接重试
```
`is_lock_free()`：并非所有 `atomic<T>` 都能用单条 CPU 指令实现，宽于机器字或自定义结构体可能退化成内部加锁——`std::atomic<long long> a{}; if (!a.is_lock_free()) { /* 未必比 mutex 快 */ }`。编译期判断用宏 `ATOMIC_INT_LOCK_FREE`、`ATOMIC_LLONG_LOCK_FREE`、`ATOMIC_POINTER_LOCK_FREE`（0/1/2，2 表示总是无锁）。标准只保证 `atomic_flag` 绝对无锁；有锁实现的原子类型不能跨进程共享，也不能用于信号处理函数。
### 5.1 六种内存序
| 内存序 | 读 | 写 | 读-改-写 | 语义 | 典型用途 |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `relaxed` | ✓ | ✓ | ✓ | 只保证原子性，不建立顺序 | 计数器、统计量 |
| `consume` | ✓ | ✗ | ✗ | 数据依赖有序（多数实现当作 acquire） | **别用**，C++17 起不推荐 |
| `acquire` | ✓ | ✗ | ✓ | 之后的读写不能排到本操作之前 | 读标志、同步消费 |
| `release` | ✗ | ✓ | ✓ | 之前的读写不能排到本操作之后 | 写标志、发布数据 |
| `acq_rel` | ✓ | ✓ | ✓ | 同时具备 acquire 与 release | CAS、引用计数递减 |
| `seq_cst` | ✓ | ✓ | ✓ | acquire + release + 全局唯一总顺序 | **默认值**，最省心 |
**默认就是 `seq_cst`**：所有不指定内存序的 `load`/`store`/`fetch_add`/`operator++` 都是它。没有实测证明有必要，就不要手动写更弱的序。
### 5.2 happens-before 直觉
编译器会重排指令、CPU 会乱序执行、缓存会延迟可见，所以"我写完了别人一定看得到"并不成立。三个关系：**sequenced-before**（单线程内按书写顺序）；**synchronizes-with**（A 对原子变量 `release` 写，B 对同一变量 `acquire` 读并读到该值，二者建立同步）；**happens-before**（同步关系 + 程序顺序传递，A 中 `release` 之前的所有写——含普通变量——对 B 中 `acquire` 之后的读**可见**）。

```cpp
std::atomic<bool> ready{false};
int data = 0;
void thread_a() {
    data = 42;                                    // ① 普通写
    ready.store(true, std::memory_order_release); // ② 发布
}
void thread_b() {
    while (!ready.load(std::memory_order_acquire)) { }   // ③ 等发布
    assert(data == 42);                           // ④ 一定成立
}
```
去掉 ②③ 的 release/acquire，① 与 ④ 之间没有任何保证，`assert` 可能失败——形式上就是数据竞争（UB）。
### 5.3 无锁计数器与自旋锁
```cpp
std::atomic<int> counter{0};
// 8 个线程各 fetch_add(1, relaxed) 1000 次 → 8000；只需原子，不需顺序
counter.fetch_add(1, std::memory_order_relaxed);
class SpinLock {                                   // 提供 lock/unlock 即可配 lock_guard
public:
    void lock() {
        for (;;) {
            if (!flag_.test_and_set(std::memory_order_acquire)) return;
            while (flag_.test(std::memory_order_relaxed)) std::this_thread::yield();
        }
    }
    void unlock() { flag_.clear(std::memory_order_release); }
private:
    std::atomic_flag flag_ = ATOMIC_FLAG_INIT;     // C++20 可写 std::atomic_flag flag_{};
};
```
自旋锁**自旋期间烧 CPU**：只适合临界区极短的场景，单核机器上自旋等于自杀，必须 `yield`。**ABA 问题一句话**：用 CAS 实现的栈/队列里，值从 A 改成 B 又改回 A，CAS 只比值就误以为没变过，于是把已删除的节点又挂回链表——解决思路是给指针配版本号（tagged pointer 或 `atomic<pair<ptr, counter>>`），让"改回去"也改变版本。
## 6 future 与任务
```cpp
int compute(int x) {
    if (x < 0) throw std::runtime_error("bad input");
    return x * x;
}
auto f1 = std::async(std::launch::async, compute, 9);      // 立刻在新线程跑
auto f2 = std::async(std::launch::deferred, compute, 5);   // 推迟到 get() 才跑
std::cout << f2.get() << "\n";                             // 此刻才在调用线程执行
try { std::async(std::launch::async, compute, -1).get(); } // 异常在 get() 处重抛
catch (const std::exception &e) { std::cout << e.what(); }
std::cout << f1.get() << "\n";                             // 81
```
`std::async` 的坑：**`deferred`** 是惰性的——`get()`/`wait()` 时才在**调用者线程**同步执行，不调 `get()` 就永不执行，异常也发现不了；**默认策略是 `async | deferred`**，由实现选择，所以 `std::async(f)` **不保证异步**；`launch::async` 返回的 `future` 若被丢弃（不接返回值），析构函数会阻塞等任务完成，看似"发射后不管"，实为同步执行；每次调用可能新建线程，高频调用应改用线程池。
### 6.1 future / promise / packaged_task 的关系
三者都是"一次性值传递通道"：**promise 是写端，future 是读端，packaged_task 把可调用对象包装成"执行完自动塞值给 promise"的适配器**。`future::get()` 只能调一次（之后 `valid()` 为 false），要多次读就用 `shared_future`；`promise` 析构前没设值，关联的 `future` 会抛 `std::future_error`（`broken_promise`）。
| 组件 | 角色 | 谁写 | 谁读 | 典型用法 |
| :--- | :--- | :--- | :--- | :--- |
| `future<T>` | 读端 | 由 promise / task / async 产生 | 调用者 `get()`/`wait()` | 取结果、取异常 |
| `promise<T>` | 写端 | 任意线程 `set_value`/`set_exception` | — | 跨线程传值、控制完成时机 |
| `packaged_task<R(Args...)>` | 可调用对象包装 | 调用它时自动写回 promise | `get_future()` 拿读端 | 塞进线程池 / 队列调度 |
| `shared_future<T>` | 可多次读取 | 由 `future::share()` 得到 | 多个线程 | 一个结果多个消费者 |

```cpp
std::promise<int> p;                       // promise 手动传值
std::future<int> f = p.get_future();
std::thread t([&p] { p.set_value(7); });
std::cout << f.get() << "\n";              // 7
t.join();
std::packaged_task<int(int, int)> task([](int a, int b) { return a + b; });
std::future<int> r = task.get_future();
std::thread t2(std::move(task), 3, 4);     // packaged_task 不可拷贝，必须 move
std::cout << r.get() << "\n";              // 7
t2.join();
```
### 6.2 wait_for / wait_until
```cpp
if (f.wait_for(std::chrono::milliseconds(50)) == std::future_status::timeout) { /* 先干别的 */ }
auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(1);
if (f.wait_until(deadline) == std::future_status::ready) std::cout << f.get();
```
三种返回值：`ready`（结果就绪，`get()` 不阻塞）、`timeout`（超时，可稍后重试）、`deferred`（惰性任务，`get()` 会当场执行）。计时用 `steady_clock`，别用会被系统时间调整影响的 `system_clock`。
## 7 线程池与并发模式
设计要点——四件套：**任务队列**（`queue<function<void()>>` + `mutex`）、**工作线程组**（`vector<thread>`）、**条件变量**（队列空时睡、有任务或停止时醒，谓词同时查两个条件）、**停止信号**（`bool stopping`，析构置位并 `notify_all` 后 join）。三个实践要点：**任务封装**——`std::function<void()>` 抹平所有可调用对象，需要返回值就包 `std::packaged_task`；**异常不能逃逸**——工作线程内必须 try/catch，否则异常穿过线程入口直接 `std::terminate`；**析构顺序**——先 `stopping = true` + `notify_all()`，再 join，最后才销毁队列和锁（成员逆序析构自动保证）。
### 7.1 完整最小实现（C++17）
```cpp
class ThreadPool {
public:
    explicit ThreadPool(size_t n = std::thread::hardware_concurrency()) {
        if (n == 0) n = 1;
        for (size_t i = 0; i < n; ++i) workers_.emplace_back([this] { worker_loop(); });
    }
    template <typename F, typename... Args>
    auto submit(F &&f, Args &&...args) -> std::future<std::invoke_result_t<F, Args...>> {
        using R = std::invoke_result_t<F, Args...>;
        // packaged_task 不可拷贝，用 shared_ptr 装箱后才能放进 std::function
        auto task = std::make_shared<std::packaged_task<R()>>(
            [f = std::forward<F>(f), args = std::make_tuple(std::forward<Args>(args)...)]() mutable {
                return std::apply(std::move(f), std::move(args));
            });
        std::future<R> result = task->get_future();
        {
            std::lock_guard<std::mutex> lk(mutex_);
            if (stopping_) throw std::runtime_error("submit on stopped ThreadPool");
            tasks_.emplace([task] { (*task)(); });
        }
        cv_.notify_one();
        return result;
    }
    ~ThreadPool() {
        { std::lock_guard<std::mutex> lk(mutex_); stopping_ = true; }
        cv_.notify_all();                            // 叫醒线程去检查 stopping_
        for (auto &t : workers_) if (t.joinable()) t.join();
    }
    ThreadPool(const ThreadPool &) = delete;
    ThreadPool &operator=(const ThreadPool &) = delete;
private:
    void worker_loop() {
        for (;;) {
            std::function<void()> task;
            {
                std::unique_lock<std::mutex> lk(mutex_);
                cv_.wait(lk, [this] { return stopping_ || !tasks_.empty(); });
                if (tasks_.empty()) { if (stopping_) return; continue; }  // 停止且已排空
                task = std::move(tasks_.front());
                tasks_.pop();
            }
            try { task(); }   // 锁外执行，避免所有线程被串行化
            catch (...) { }   // 必须吞掉：异常已通过 packaged_task 传给 future，逃逸会 terminate
        }
    }
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;
    std::mutex mutex_;
    std::condition_variable cv_;
    bool stopping_ = false;
};
// 用法：ThreadPool pool(4); auto fut = pool.submit([](int x) { return x * x; }, 7);
```
容易写错的地方：`packaged_task` 要装箱才可拷贝；**必须在锁外执行 `task()`**，否则所有线程被强制串行；`if (tasks_.empty()) { if (stopping_) return; continue; }` 保证队列里剩余任务做完（优雅关闭），想立即关闭就直接 return。

`std::function<void()>` 是线程池的"通用插槽"，代价是类型擦除（一次间接调用 + 可能堆分配）；捕获大对象时会堆分配，C++14 起可用移动捕获 `[p = std::move(p)]` 避免拷贝，要求可拷贝正是 `packaged_task` 必须装箱的原因。**任务窃取**一句话：每个工作线程有自己的双端队列，任务从本队一端取（快），本队空了就去别的队列另一端"偷"（慢但均衡），可扩展性优于单一全局队列——Intel TBB、Go runtime、Java ForkJoinPool 都是这个思路。
## 8 线程安全设计
**data race** 定义：两个线程并发访问同一内存位置，至少一个是写，且二者之间没有 happens-before 关系。一旦发生就是**未定义行为**，不是"结果不对"——编译器可以合法地死循环或删掉代码。`int bad = 0;` 被多个线程 `++` 就属于这种。三个误解：① 只有 `int` 才竞争——`std::string`、`std::vector` 一样；② 两个线程都 `push_back` 也算写-写竞争；③ 加 `volatile` 没用——它只禁止优化掉读写，不提供原子性和内存屏障。
| 概念 | 含义 | 例子 |
| :--- | :--- | :--- |
| **线程安全** | 多线程同时调用同一函数/对象无需额外同步也不出错 | `shared_ptr` 的引用计数操作 |
| **可重入** | 同一线程未返回时再次进入该函数也安全 | 纯函数、只用栈上数据 |
线程安全 ≠ 可重入：加了 `mutex` 的函数是线程安全的，但递归调用会自锁。可重入 ≠ 线程安全：只依赖栈的函数重入安全，但若共享全局可变数据仍是竞争。可重入的主战场是信号处理函数（内部只能调 async-signal-safe 函数）。
### 8.1 thread_local
每个线程独立一份、天然无竞争，适合每线程缓存、随机数种子、错误码：

```cpp
thread_local int tls_counter = 0;   // 每个线程各一份
// 三个线程各调两次 bump()：各自输出 1 2，互不影响
void bump() { std::cout << ++tls_counter << " "; }
```
首次使用时在该线程上初始化，线程退出时析构。不要用它传递参数，会让依赖关系变得隐形。
### 8.2 copy-on-write：读多写少
比读写锁更彻底：读者直接读不可变快照，写者构造新副本再原子替换指针，**读者零锁**。

```cpp
class ConfigStore {
public:
    using Snapshot = std::shared_ptr<const std::vector<std::string>>;
    ConfigStore() : data_(std::make_shared<const std::vector<std::string>>()) {}
    Snapshot get() const {                        // 读者：一次原子加载，无锁
        return std::atomic_load_explicit(&data_, std::memory_order_acquire);
    }
    void add(const std::string &item) {           // 写者：复制 → 修改 → 原子替换
        auto old = get();
        auto copy = std::make_shared<std::vector<std::string>>(*old);
        copy->push_back(item);
        Snapshot fresh = copy, expected = old;
        while (!std::atomic_compare_exchange_weak_explicit(
            &data_, &expected, fresh, std::memory_order_acq_rel, std::memory_order_acquire)) {
            copy = std::make_shared<std::vector<std::string>>(*expected);   // 别人抢先改了
            copy->push_back(item);
            fresh = copy;
        }
    }
private:
    mutable std::shared_ptr<const std::vector<std::string>> data_;
};
```
读者不阻塞，适合配置、路由表、白名单这类读远多于写的场景；缺点是每次写都复制整份数据。C++20 起可直接用 `std::atomic<std::shared_ptr<T>>` 代替那组自由函数。
### 8.3 单例的正确写法
**C++11 起局部 static 变量初始化是线程安全的**，所以懒汉式单例直接写：

```cpp
static Singleton &instance() {
    static Singleton inst;   // C++11 起线程安全，无需手动加锁
    return inst;
}
```
**为什么双重检查锁（DCL）以前是错的**：`instance = new Singleton()` 被拆成"分配内存 → 构造 → 赋指针"，编译器/CPU 可能把赋值提前，另一个线程看到非空指针但对象还没构造完。C++11 引入内存模型后，用 `std::atomic` + acquire/release 写 DCL 才安全，但已无必要。**需要初始化"一段逻辑"（不只一个变量）**时用 `std::call_once`：

```cpp
std::once_flag flag;
int *resource = nullptr;
void init() { resource = new int[1024]; }
void use() { std::call_once(flag, init); }   // init 只执行一次，其余线程等它完成
```
两者都异常安全：初始化抛异常时，局部 static 会放弃并允许下次重试，`call_once` 会把 flag 重置。Meyers 单例的两个边界：① 静态析构顺序——程序退出时若有别的静态对象还在用它，可能访问到已析构对象；② 同一头文件被静态链接进多个 `.so`，每个库会各有一份实例。
### 8.4 什么时候该用无锁
| 判断维度 | 适合无锁 | 应该用锁 |
| :--- | :--- | :--- |
| 临界区长度 | 极短（几十条指令，如计数器） | 有 IO、分配内存、调外部代码 |
| 竞争程度 | 低到中等 | 高竞争（CAS 频繁失败的代价更高） |
| 数据结构 | 单个原子变量、简单队列 | 树、哈希表、多字段一致性更新 |
| 成本 | 有并发测试 + TSan 覆盖 | 赶工期、正确性优先 |
无锁不等于更快：高竞争下 CAS 空转照样烧 CPU，**伪共享**（两个线程写同一缓存行里的不同变量）会让性能骤降——计数器可用"每线程局部计数 + 定期汇总"规避。无锁也不等于免等（lock-free 与 wait-free 是两回事）。工程上：**先用 `mutex` 写对**，profile 证明锁是瓶颈后再优化，需要高性能并发结构时优先用成熟库（folly、boost.lockfree、moodycamel）。
## 9 调试与工具
### 9.1 ThreadSanitizer（TSan）
编译期插桩检测数据竞争，不需要错误真的触发——它记录每次内存访问的线程与 happens-before 关系。

```bash
g++ -std=c++17 -g -O1 -fsanitize=thread -o app app.cpp -pthread
./app
# WARNING: ThreadSanitizer: data race
#   Write of size 4 at 0x7b0400000000 by thread T1:   #0 buggy() main.cpp:12
#   Previous read of size 4 at 0x7b0400000000 by main thread:   #0 main main.cpp:20
# SUMMARY: ThreadSanitizer: data race main.cpp:12
```
解读四步：① 两条栈分别是"本次访问"和"没有 happens-before 的另一次访问"，看是否指向同一变量；② `Location` 配合 `-g` 定位是全局还是堆上变量；③ 没有 happens-before 就是真问题（跨进程共享内存、手写汇编原语可用 `__tsan_acquire`/`__tsan_release` 注解消除误报）；④ 死锁也会报 `lock-order-inversion`。注意 TSan 不能与 ASan 同开（`-fsanitize=address,thread` 直接报错），运行时慢 5~15 倍。
### 9.2 gdb 看线程
```bash
gdb -p <pid>                     # 附加到运行中的进程
(gdb) info threads               # 所有线程：编号、id、栈顶函数、执行位置
(gdb) thread 3                   # 切到 3 号线程
(gdb) thread apply all bt        # 所有线程的调用栈——排查死锁首选
```
判读：多条线程都停在 `pthread_mutex_lock` / `__lll_lock_wait`，且各自想拿的锁正是别人持有的锁，就形成环。离线分析用 `gdb ./app core`（先 `ulimit -c unlimited`）；线上进程可用 `gcore <pid>` 抓现场，或 `pstack <pid>` 快速看栈。
### 9.3 valgrind --tool=helgrind
```bash
valgrind --tool=helgrind ./app
valgrind --tool=helgrind --history-level=full ./app   # 栈更精确，更慢
```
不用重编译，能查数据竞争、锁顺序反转、锁使用错误（重复加锁、未初始化）。与 TSan 对比：
| 对比项 | TSan | Helgrind |
| :--- | :--- | :--- |
| 使用方式 | 需 `-fsanitize=thread` 重编译 | 直接跑原程序 |
| 速度 | 慢 5~15 倍 | 慢 20~100 倍 |
| 误报率 | 较低 | 较高（对 atomics 识别有限） |
| 优势 | 贴近代码、CI 友好 | 无需重编译，可分析第三方二进制 |
### 9.4 strace -f 与 perf
```bash
strace -f -o trace.txt ./app                  # -f 跟随所有线程
strace -f -e trace=futex,clone ./app          # 只看线程相关系统调用
grep 'FUTEX_WAIT' trace.txt | head            # 卡在等锁/等条件变量
perf stat -e context-switches,cpu-migrations ./app   # 上下文切换、跨核迁移次数
perf sched record ./app && perf sched latency        # 调度延迟：谁被耽误了
perf c2c record ./app && perf c2c report             # 伪共享 / 缓存行争用
```
`strace` 用来确认线程卡在哪个系统调用（`futex(FUTEX_WAIT)` 表示等锁或条件变量）、数 `clone` 次数确认线程是否被反复创建、区分"死锁"（futex 等待）与"死循环"（无系统调用）；它会让程序慢几十倍且需权限，轻量替代是看 `/proc/<pid>/stack`。`perf` 里 `context-switches` 过高说明线程太多或在抢锁，`cpu-migrations` 高说明线程频繁换核、缓存失效，`perf sched latency` 找"偶发慢"的真凶。
## 10 面试问答
### Q1 `join` 和 `detach` 的区别？
- `join` 阻塞到目标线程结束，之后可确定资源已回收、结果可取；`detach` 让线程独立运行，无法等待也拿不到结果。
- 两者都只能调用一次，调用后 `joinable()` 为 false；`thread` 析构时仍 joinable 会 `std::terminate`。
- `detach` 的风险是生命周期：线程访问主线程栈变量或已析构的全局对象属于 UB。
### Q2 为什么会死锁？怎么避免？
- 需要四个条件同时成立：互斥、占有并等待、不可剥夺、循环等待，破坏任一条即可避免。
- 最常见原因是两把锁加锁顺序不一致；还有同线程重复加锁、持锁时 `join` 线程。
- 最实用手段：统一加锁顺序，或一律用 `scoped_lock`/`std::lock` 一次锁多个。
### Q3 条件变量为什么要用 while 而不是 if？
- `wait` 存在虚假唤醒，`if` 只判断一次就往下走，会读到不满足条件的状态。
- `notify_all` 唤醒多个线程时它们竞争同一把锁，先抢到的可能已消费数据，其余醒来条件已不成立。
- `wait(lk, pred)` 内部就是 `while (!pred()) wait(lk)`。
### Q4 只用 atomic 够用吗？
- 单个计数器 `atomic` 足够；多个变量要一起保持一致时，原子只保证各自原子，不保证组合不变式。
- "先查后改"（`if (x == 0) x = 1;`）用两个原子操作也救不了，必须 CAS 循环或加锁。
- 复合操作（如向 map 插入）无法用 `atomic<T>` 表达：`atomic` 只消除数据竞争，不负责业务原子性。
### Q5 内存序默认是什么？什么时候改？
- 默认 `memory_order_seq_cst`：原子操作之间有全局唯一的执行顺序。
- 只有经过验证有性能收益才改用弱序，如计数器用 `relaxed`、发布标志用 `release` + 消费端 `acquire`。
- 弱序正确性依赖 happens-before 推理，写错是偶发难复现；`memory_order_consume` 自 C++17 起不推荐。
### Q6 `std::async` 有哪些坑？
- 不写策略时默认 `async | deferred`，实现可选推迟执行，所以 `std::async(f)` 不保证异步。
- `launch::deferred` 的任务在 `get()/wait()` 时才在调用者线程执行，不调用就永不执行，异常也发现不了。
- 丢弃返回的 `future` 时其析构会阻塞到任务完成，看似异步实为同步。
### Q7 怎么实现一个简单的线程池？
- 四件套：任务队列（`queue<function<void()>>` + `mutex`）、工作线程组、条件变量、`bool stopping` 标志。
- 工作线程循环 `wait(lk, []{ return stopping || !tasks.empty(); })`，取到任务后在**锁外**执行，并用 try/catch 兜住异常。
- 析构时置 `stopping = true` 并 `notify_all()` 再 join，队列剩余任务会被做完。
### Q8 什么是虚假唤醒？
- 指没有对应 `notify` 时 `wait` 也可能返回，C++ 与 POSIX 标准刻意允许。
- 应对是用谓词 `wait(lk, pred)`，醒来重新检查条件，不满足就继续睡。
- 它还会叠加"多个消费者被同时唤醒"的情况，所以即便没有虚假唤醒，用 `if` 也是错的。
### Q9 `lock_guard` 和 `unique_lock` 的区别？
- `lock_guard` 构造即加锁、析构即解锁，无其他接口，体积小开销低。
- `unique_lock` 支持延迟加锁、`try_lock`、提前 `unlock`、拿底层锁、`move` 转移，代价是多一个状态位。
- 条件变量必须用 `unique_lock`，因为 `wait` 需要在等待期间解锁、醒来重新加锁。
### Q10 `shared_mutex` 什么时候有用？
- 读多写少且读占比很高时有用：多个读者并发持锁，写者独占。
- 读者用 `shared_lock`，写者用 `unique_lock`；读者持锁期间不能再申请写锁。
- 读写比例不明显时普通 `mutex` 往往更快；更强的是"不可变快照 + 原子替换指针"。
### Q11 `volatile` 能解决多线程问题吗？
- 不能：它只告诉编译器"变量可能被外部改变，不要优化掉读写"，不提供原子性也不提供内存屏障。
- `volatile int` 的 `++` 仍不是原子操作，两个线程自增照样丢更新。
- 多线程同步必须用 `std::atomic`（配内存序）或互斥量。
### Q12 如何保证多线程下单例的线程安全？
- C++11 起局部 `static` 最简单：标准保证初始化的线程安全，且只在首次调用时构造。
- 双重检查锁在 C++11 之前因"指针赋值早于构造完成"而错误；C++11 后要用 `atomic<Singleton*>` + acquire/release，但已无必要。
- 需要初始化任意逻辑时用 `std::call_once` + `std::once_flag`。
### Q13 TSan 怎么用？报错怎么看？
- 编译加 `-fsanitize=thread -g -O1`（不能与 ASan 同开），链接加 `-pthread`，然后正常跑。
- 报错给出两条栈（本次访问 + 竞争的另一次访问）、变量位置和 `SUMMARY` 行。
- 关键判断是两处访问之间有没有 happens-before，没有就是真问题；`__tsan_acquire/__tsan_release` 可消除误报。
### Q14 线程数怎么定？线程越多越快吗？
- CPU 密集型取 `hardware_concurrency() + 1`；IO 密集型按"核数 × (1 + 阻塞/计算)"估算，工程上常设固定上限。
- 不是越多越快：上下文切换、栈内存、缓存失效、锁竞争都会随线程数恶化。
- 线程池的作用就是固定线程数、用队列削峰，避免"每请求一线程"。
### Q15 无锁编程什么时候值得用？
- 临界区极短、只涉及单个原子变量、竞争中等时（计数器、标志位）有意义。
- 多字段要一致、临界区里有分配或 IO 时，锁更简单也更快；高竞争下 CAS 重试反而更糟。
- 无锁不代表 wait-free，也不自动更快；伪共享是常见性能陷阱，应先 profile 再优化。
## 参考
- 《C++ Concurrency in Action（Second Edition）》—— Anthony Williams
- cppreference：[Thread support library](https://en.cppreference.com/w/cpp/thread)、[Memory model](https://en.cppreference.com/w/cpp/language/memory_model)
