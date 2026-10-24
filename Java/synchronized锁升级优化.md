## 1 结论先行

`synchronized` 是 JVM 内置互斥锁，一条主线：

**monitorenter/monitorexit → 对象头 Mark Word → 锁升级（无锁 → 偏向 → 轻量 → 重量）→ ObjectMonitor → JIT 锁消除/锁粗化**。

三个高频误区：

* 「synchronized 一定是重量级锁」：JDK 6 后低竞争走偏向/轻量，不会进内核。
* 「偏向锁默认开启」：JDK 15（JEP 374）起默认关闭，JDK 18 移除实现，旧资料已过时。
* 「锁可以降级」：正常执行期只升不降；空闲 monitor 可能被 VM 回收，但不会退回偏向锁。

## 2 字节码：monitorenter / monitorexit

```java
public void inc() {
    synchronized (lock) { count++; }
}
```

`javap -c` 的关键指令（常量池编号因编译环境而异）：

```text
6: monitorenter
...
18: monitorexit
19: goto 27
22: monitorexit          // 异常路径
24: athrow
27: return
Exception table: from 7 to 19 target 22 type any
```

* `monitorenter`：monitor 计数为 0 则获取；已归当前线程则重入计数 +1；被其他线程持有则阻塞。
* `monitorexit`：计数 -1，减到 0 才真正释放；正常路径和异常路径各有一条，保证异常也能释放。
* `synchronized` 方法没有这两条指令，而是在方法访问标志里加 `ACC_SYNCHRONIZED`（0x0020），由 JVM 隐式加解锁。
* 字节码层面无法「只加不解」；但手写字节码/插桩漏掉 monitorexit 会导致 monitor 泄漏。

## 3 对象头与 Mark Word

64 位 HotSpot 对象头：Mark Word 8B + Klass Pointer 4B（开启压缩指针）/8B；数组对象再加 4B 长度。Mark Word 按锁状态复用同一块内存：

| 状态 | 64 位结构（高位 → 低位） | lock |
| --- | --- | --- |
| 无锁 | unused 25 + identity_hash 31 + unused 1 + age 4 + biased 0 | 01 |
| 偏向 | thread 54 + epoch 2 + unused 1 + age 4 + biased 1 | 01 |
| 轻量 | ptr_to_lock_record 62 | 00 |
| 重量 | ptr_to_heavyweight_monitor 62 | 10 |
| GC | forwarding 62 | 11 |

* identity hash 是延迟计算的；对象一旦算出 hash，Mark Word 被占用，偏向锁会被撤销且不能再偏向。
* age 是 GC 分代年龄（4 bit，最大 15），不是业务字段。
* 32 位 JVM 字段宽度不同，但「锁标志位 + 状态复用」的思路一致。
* Klass Pointer 指向 InstanceKlass，类的原型头里还保存偏向 epoch 等信息。

## 4 锁升级路径

```text
无锁 --首次 synchronized--> 偏向锁 --另一线程竞争--> 轻量级锁 --CAS 失败/竞争--> 重量级锁
```

| 状态 | 触发条件 | 主要开销 |
| --- | --- | --- |
| 无锁 | 未进入同步 | — |
| 偏向 | 第一次加锁，CAS 记录线程 ID | 一次 CAS，之后仅比较 |
| 轻量 | 另一线程竞争，撤销偏向 | 栈上 Lock Record + CAS |
| 重量 | 轻量 CAS 失败或自旋失败 | ObjectMonitor + park/unpark |

* 偏向锁不是所有对象都能进入：类未禁用偏向、对象没算过 hash、JVM 开启偏向（JDK 15 前默认）。
* 撤销偏向要在 safepoint 进行，这是偏向锁最贵的操作。
* 轻量级锁的获取是一次 CAS；失败后进入膨胀流程，自适应自旋发生在重量级 monitor 入口。
* 运行期一般只升不降；空闲 monitor 可能被 VM deflate，但不会回到偏向锁。

## 5 偏向锁

目的：单线程反复进入同一把锁时，省掉每次的 CAS。

流程：

1. 对象初始为可偏向状态（biased=1、lock=01、thread=0）。
2. 第一次加锁用 CAS 把当前线程 ID（和 epoch）写进 Mark Word。
3. 后续进入只比较线程 ID，不再 CAS；偏向会一直保留到撤销，不是每次退出都释放。
4. 另一线程尝试获取时，在 safepoint 撤销：原线程不活跃则恢复无锁/重偏向；仍活跃则升级为轻量级锁。

批量优化（HotSpot）：

| 参数 | 默认 | 作用 |
| --- | --- | --- |
| `BiasedLockingStartupDelay` | 4000ms | 启动 4s 后才启用，避开启动期竞争 |
| `BiasedLockingBulkRebiasThreshold` | 20 | 同类撤销 20 次后批量重偏向（epoch++） |
| `BiasedLockingBulkRevokeThreshold` | 40 | 同类撤销 40 次后该类禁用偏向 |
| `BiasedLockingDecayTime` | 25000ms | 一段时间无撤销则计数衰减，可重新偏向 |

**版本重点**：JDK 15 的 JEP 374 把偏向锁默认关闭并废弃相关参数（仍可用 `-XX:+UseBiasedLocking` 手动打开，但会告警）；JDK 18（JDK-8256425）移除实现，`-XX:+UseBiasedLocking` 变成 obsolete。很多旧资料仍写「默认开启、延迟 4s」，那只适用于 JDK 14 及以前。

为什么废弃：维护成本高、现代 CPU 的 CAS 已经足够便宜、收益集中在 Hashtable/Vector 等老集合、撤销要 STW，整体性价比下降。

## 6 轻量级锁

* 线程在栈帧里分配 Lock Record，把对象 Mark Word 复制进去（displaced header）。
* 用 CAS 把对象 Mark Word 改成指向该 Lock Record 的指针，成功即持有。
* 重入时再压一个 Lock Record，displaced header 为 null，用来计数。
* 解锁用 CAS 把 Mark Word 还原；失败说明有竞争，走膨胀/唤醒逻辑。
* 竞争失败且 owner 不是自己时，膨胀为重量级锁；轻量级锁适合「交替执行、临界区短」，不阻塞、不切内核。
* 注意：HotSpot 中轻量级锁阶段本身不自旋；自旋发生在膨胀后的 ObjectMonitor 入口（自适应自旋）。

## 7 重量级锁与 ObjectMonitor

HotSpot 的重量级锁是一个 C++ `ObjectMonitor`：

| 字段 | 作用 |
| --- | --- |
| `_header` | 保存 displaced Mark Word |
| `_owner` | 当前持有线程 |
| `_recursions` | 重入次数 |
| `_cxq` | 竞争队列，CAS 入队，后进先出 |
| `_EntryList` | 候选队列，等待被唤醒竞争锁 |
| `_WaitSet` | 调用 `wait()` 的线程 |
| `_count` | 等待/持有线程的估算计数 |
| `_succ` | 假定后继，减少不必要的 unpark |

获取流程：

1. CAS 把 `_owner` 从 null 改为当前线程，成功即持有。
2. 失败先自适应自旋；仍失败则把 `ObjectWaiter` CAS 进 `_cxq`，然后 `park`。
3. 释放时按 QMode 把 `_cxq` 批量移到 `_EntryList`，`unpark` 一个后继。

`wait/notify`：

* `wait()` 必须持有 monitor：保存重入计数 → 释放锁 → 进 `_WaitSet` → park；被唤醒后重新竞争锁，恢复计数再返回。
* `notify()` 从 `_WaitSet` 移一个到 `_EntryList`/`_cxq`，不立即释放锁；`notifyAll()` 移全部。
* 不在同步块里调用会抛 `IllegalMonitorStateException`。

代价是 park/unpark 和上下文切换，适合临界区长、竞争激烈的场景。字段名和 QMode 是 HotSpot 实现细节，其他 JVM 可能不同。

## 8 锁消除与锁粗化

两者都是 JIT 优化，不是源码改写。

**锁消除**：逃逸分析证明锁对象不会逃逸，JIT 直接删掉同步。

```java
public String concat(String a, String b) {
    StringBuffer sb = new StringBuffer();   // 局部变量，不逃逸
    sb.append(a).append(b);                 // append 上的锁可被消除
    return sb.toString();
}
```

**锁粗化**：相邻或循环内对同一对象反复加解锁，JIT 合并成一次大锁。

```java
for (int i = 0; i < n; i++) {
    synchronized (lock) { count++; }        // 可能被粗化成循环外一次加锁
}
```

相关参数：`-XX:+DoEscapeAnalysis`、`-XX:+EliminateLocks`（默认开启）。对象被发布到堆、静态字段或其他线程后，逃逸分析失效，锁消除不会发生。

## 9 与 ReentrantLock / CAS / AQS 对比

| 维度 | `synchronized` | `ReentrantLock` |
| --- | --- | --- |
| 实现层 | JVM（monitor） | JDK（AQS） |
| 释放 | 自动，异常也释放 | 必须 `finally unlock()` |
| 公平性 | 非公平 | 可选公平/非公平 |
| 可中断 | 不支持 | `lockInterruptibly()` |
| 超时 | 不支持 | `tryLock(timeout)` |
| 条件队列 | 一个 wait/notify | 多个 `Condition` |
| 尝试获取 | 不支持 | `tryLock()` |
| 低竞争优化 | 偏向/轻量（JDK 15 前） | 无 |
| 虚拟线程 | JDK 24 前会 pin 载体线程 | 不 pin |
| 适用 | 简单互斥、代码简洁 | 需要公平/超时/中断/多条件 |

CAS 与 AQS：

* CAS 是 CPU 原子指令（`Unsafe.compareAndSwapInt` / `VarHandle`），乐观重试；有 ABA、自旋开销、只能保证单个变量。
* AQS 用 `volatile state` + CLH 双向队列 + CAS 入队 + `LockSupport.park/unpark`，支持独占/共享模式；`ReentrantLock`、`Semaphore`、`CountDownLatch` 都基于它。
* JDK 6 后低竞争下 synchronized 与 ReentrantLock 性能接近，选型优先看语义需求，而不是「谁更快」。

```java
private final ReentrantLock lock = new ReentrantLock();
public void inc() {
    lock.lock();
    try { count++; } finally { lock.unlock(); }
}
```

## 10 Android ART 的差异

* DEX 字节码是 `monitor-enter` / `monitor-exit`；`synchronized` 方法同样用 `ACC_SYNCHRONIZED`。
* ART 对象头是 `klass_` + `monitor_`（LockWord，32 位），没有 HotSpot 的偏向锁。
* LockWord 状态：

| 状态 | 含义 |
| --- | --- |
| `kUnlocked` | 无锁 |
| `kThinLocked` | 轻量锁：线程 id（16 位）+ 递归计数（其余位，含 GC 状态位） |
| `kFatLocked` | 膨胀后的 `art::Monitor` id |
| `kHashCode` | identity hash |
| `kForwardingAddress` | GC 移动对象时的转发地址 |

* 无竞争时 CAS 改 LockWord 进入 thin lock；竞争后膨胀为 fat lock，`art::Monitor` 用 futex 等待。
* ART 没有偏向锁、批量重偏向，锁消除也不如 HotSpot 激进；不要把 HotSpot 的 Mark Word/偏向锁结论直接套到 ART。
* 实现参考：`art/runtime/lock_word.h`、`art/runtime/monitor.cc`；具体行为随 ART 版本变化，以 AOSP 为准。

## 11 版本变化

| 版本 | 变化 |
| --- | --- |
| JDK 6 | 偏向锁、轻量级锁、自适应自旋默认开启 |
| JDK 15 | JEP 374：偏向锁默认关闭，相关参数 deprecated |
| JDK 18 | JDK-8256425：移除偏向锁实现，参数 obsolete |
| JDK 21 | 虚拟线程正式；`synchronized` 会 pin 载体线程 |
| JDK 24 | JEP 491：`synchronized` 不再 pin 载体线程（native 等场景仍可能 pin） |

面试时如果被问「偏向锁默认开吗」，先确认 JDK 版本：≤14 默认开（延迟 4s），≥15 默认关，≥18 实现已移除。

## 12 面试问答

### Q1：synchronized 的底层原理？
字节码 `monitorenter`/`monitorexit` + 对象头 Mark Word + monitor。无竞争走偏向/轻量，竞争时膨胀为 ObjectMonitor，用 park/unpark 阻塞；方法级用 `ACC_SYNCHRONIZED`。

### Q2：锁升级的过程和触发条件？
无锁 → 偏向（首次 CAS 记线程）→ 轻量（另一线程竞争，撤销偏向）→ 重量（CAS/自旋失败）。偏向撤销要 safepoint；轻量是栈上 Lock Record + CAS；重量是 ObjectMonitor。

### Q3：偏向锁为什么被废弃？
JEP 374（JDK 15）默认关闭，JDK 18 移除。维护复杂、CAS 变便宜、收益集中在老集合、撤销要 STW。

### Q4：偏向锁撤销为什么要 safepoint？批量重偏向是什么？
撤销要改持有线程的栈和 Mark Word，必须在 safepoint 停下来做。同类撤销 20 次后批量重偏向（epoch++），40 次后该类禁用偏向，25s 无撤销则计数衰减。

### Q5：轻量级锁一定比重量级锁快吗？
不一定。轻量适合交替执行、临界区短；真实竞争时 CAS 失败会膨胀，重量级反而减少自旋浪费。低竞争下轻量通常更快，但要看临界区长度和竞争度。

### Q6：ObjectMonitor 的 cxq、EntryList、WaitSet 有什么区别？
`cxq` 是 CAS 入队的竞争队列（LIFO），`EntryList` 是候选队列，释放时按 QMode 从 `cxq` 迁移；`WaitSet` 是 `wait()` 的线程，`notify` 后移到 `EntryList`/`cxq` 重新竞争。

### Q7：wait/notify 为什么必须在 synchronized 块里？
`wait` 会释放 monitor 并进入 `WaitSet`，前提是当前线程持有 monitor；否则无法保证「检查条件 + 等待」的原子性，JVM 直接抛 `IllegalMonitorStateException`。

### Q8：锁消除和锁粗化是什么？
锁消除靠逃逸分析删掉不逃逸对象的同步（局部 `StringBuffer`）；锁粗化把相邻/循环内同一把锁合并成一次。两者都是 JIT 优化，不是源码改写。

### Q9：synchronized 和 ReentrantLock 怎么选？
简单互斥用 `synchronized`（自动释放、代码短）；需要公平、超时、可中断、多 `Condition` 或 `tryLock` 用 `ReentrantLock`；虚拟线程场景优先 `ReentrantLock`（JDK 24 前避免 pin）。

### Q10：Android ART 上的 synchronized 和 HotSpot 有什么不同？
ART 用 DEX `monitor-enter`/`monitor-exit` + LockWord（thin/fat），没有偏向锁和批量重偏向，竞争后 `Monitor` 用 futex；不能把 HotSpot 的 Mark Word 结论直接套过去。

## 13 一句话记忆

`synchronized` = 对象头状态机 + monitor；低竞争靠偏向/轻量省 CAS，高竞争靠 ObjectMonitor 排队；JDK 15 起别再答「偏向锁默认开启」。

参考：JEP 374、JDK-8256425、JEP 491、HotSpot `objectMonitor.hpp`/`synchronizer.cpp`；ART 见 `lock_word.h`/`monitor.cc`。
