## 1 Dalvik 虚拟机

简称 Dalvik VM 或 DVM，并不是一个 JVM 没有遵循 DVM 规范来实现。

与 JVM 区别：

|                  | JVM            | DVM                                                       |
| ---------------- | -------------- | --------------------------------------------------------- |
| 基于的架构不同   | 栈             | 寄存器                                                    |
| 执行的字节码不同 | .class -> .jar | .class -> .dex                                            |
| 运行的按进程     |                | 经过优化，有限的内存而当中运行多个进程                    |
|                  |                | DVM 由Zygote 创建和初始化                                 |
|                  |                | DVM 有共享机制，不同应用可以共享相同的类，JVM没有这种机制 |
|                  |                | DVM 早期没有使用 JIT 编译器                               |

## 2 DVM 的运行时堆

* 运行时堆使用标记-清除 算法进行 GC，由两个 Space 以及多个辅助数据结构组成
* 两个 Space
  * Zygote Space（Zygote Heap）：管理Zygote进程启动过程中预加载和创建的各种对象，不会触发 GC，进程共享
  * Allocation Space（Active Heap）：不是进程共享，以后的对象都在此分配和释放

## 3 DVM的GC日志

在 DVM 中，每次垃圾收集都会将GC日志打印到 logcat 中，具体的格式为：

```java
D/dalvikvm: <GC_Reason> <Amount_freed>, <Heap_stats>, <External_memory_stats>，<Pause_time>
```

引起GC原因：

- GC_CONCURRENT：当堆开始填充时，并发GC可以释放内存。
- GC_FOR_MALLOC：当堆内存已满时，app尝试分配内存而引起的GC，系统必须停止app并回收内存。
- GC_HPROF_DUMP_HEAP：当你请求创建 HPROF 文件来分析堆内存时出现的GC。
- GC_EXPLICIT：显示的GC，例如调用System.gc()（应该避免调用显示的GC，信任GC会在需要时运行）。
- GC_EXTERNAL_ALLOC：仅适用于 API 级别小于等于10 ，用于外部分配内存的GC。

其他信息：

除了引起GC原因，其他的信息为：

- Amount_freed：本次GC释放内存的大小。
- Heap_stats：堆的空闲内存百分比 （已用内存）/（堆的总内存）。
- External_memory_stats：API 级别 10 及更低级别的内存分配 （已分配的内存）/（引起GC的阀值）。
- Pause time：暂停时间，更大的堆会有更长的暂停时间。并发暂停时间显示了两个暂停：一个出现在垃圾收集开始时，另一个出现在垃圾收集快要完成时。

## 4 ART 虚拟机

ART 与 DVM 区别：

* DVM -> JIT（即时编译）、ART -> AOT（预编译） 但是 Android 7.0 加入  JIT
* DVM 是为 32 位 CPU 设计的，ART 支持 64 位并且兼容 32 位 CPU
* ART 对垃圾回收机制进行了改进，例如更加频繁的执行并行垃圾收集，将 GC 暂停 由 2 次变为 1 次
* ART 的运行时堆空间划分和 DVM 不同

## 5 ART 的运行时堆

四个 Space 和其他辅助的数据结构。

* Zygote Space（Zygote Heap）：管理 Zygote 进程启动过程中预加载和创建的各种对象，不会触发 GC，进程共享
* Allocation Space（Active Heap）：不是进程共享，以后的对象都在此分配和释放
* Image Space：存放一些预加载的类
* Large Object Space：分配一些大对象（默认大小为 12KB）

## 6 ART 的 GC 日志

引起GC原因：

- Concurrent： 并发GC，不会使App的线程暂停，该GC是在后台线程运行的，并不会阻止内存分配。
- Alloc：当堆内存已满时，App尝试分配内存而引起的GC，这个GC会发生在正在分配内存的线程。
- Explicit：App显示的请求垃圾收集，例如调用System.gc()。与DVM一样，最佳做法是应该信任GC并避免显示的请求GC，显示的请求GC会阻止分配线程并不必要的浪费 CPU 周期。如果显式的请求GC导致其他线程被抢占，那么有可能会导致 jank（App同一帧画了多次)。
- NativeAlloc：Native内存分配时，比如为Bitmaps或者RenderScript分配对象， 这会导致Native内存压力，从而触发GC。
- CollectorTransition：由堆转换引起的回收，这是运行时切换GC而引起的。收集器转换包括将所有对象从空闲列表空间复制到碰撞指针空间（反之亦然）。当前，收集器转换仅在以下情况下出现：在内存较小的设备上，App将进程状态从可察觉的暂停状态变更为可察觉的非暂停状态（反之亦然）。
- HomogeneousSpaceCompact：齐性空间压缩是指空闲列表到压缩的空闲列表空间，通常发生在当App已经移动到可察觉的暂停进程状态。这样做的主要原因是减少了内存使用并对堆内存进行碎片整理。
- DisableMovingGc：不是真正的触发GC原因，发生并发堆压缩时，由于使用了 GetPrimitiveArrayCritical，收集会被阻塞。一般情况下，强烈建议不要使用 GetPrimitiveArrayCritical，因为它在移动收集器方面具有限制。
- HeapTrim：不是触发GC原因，但是请注意，收集会一直被阻塞，直到堆内存整理完毕。

垃圾收集器名称：

GC_Name指的是垃圾收集器名称，有以下几种：

- Concurrent mark sweep (CMS)：CMS收集器是一种以获取最短收集暂停时间为目标收集器，采用了**标记-清除算法（Mark-Sweep）实现**。 它是完整的堆垃圾收集器，能释放除了Image Space之外的所有的空间。
- Concurrent partial mark sweep：部分完整的堆垃圾收集器，能释放除了Image Space和Zygote Spaces之外的所有空间。
- Concurrent sticky mark sweep：分代收集器，它只能释放自上次GC以来分配的对象。这个垃圾收集器比一个完整的或部分完整的垃圾收集器扫描的更频繁，因为它更快并且有更短的暂停时间。
- Marksweep + semispace：非并发的GC，复制GC用于堆转换以及齐性空间压缩（堆碎片整理）。

其他信息：

- Objects freed：本次GC从非Large Object Space中回收的对象的数量。
- Size_freed：本次GC从非Large Object Space中回收的字节数。
- Large objects freed： 本次GC从Large Object Space中回收的对象的数量。
- Large object size freed：本次GC从Large Object Space中回收的字节数。
- Heap stats：堆的空闲内存百分比 （已用内存）/（堆的总内存）。
- Pause times：暂停时间，暂停时间与在GC运行时修改的对象引用的数量成比例。目前，ART的CMS收集器仅有一次暂停，它出现GC的结尾附近。移动的垃圾收集器暂停时间会很长，会在大部分垃圾回收期间持续出现。