## 1 简介

Binder 中文译为粘合剂，它把系统中各个组件粘合到了一起，是各个组件的桥梁。Binder 是Android 系统中进程间通讯（IPC）的一种非常重要的方式，区别于传统的 Linux IPC 机制。

> 2025 更新：`startActivity`、`bindService`、`ContentResolver.query`、`Messenger` 背后都是 Binder。面试一般问三层：**为什么不用 Linux 现成的 IPC**、**一次调用在用户态/内核态发生了什么**（mmap 与「一次拷贝」）、**AIDL 生成的类各管什么**。本文按这条主线补全，原有的 Linux IPC 整理全部保留。

一句话概括：Binder 是**基于 mmap 的、带调用方身份校验的、C/S 架构**的 IPC。Client 通过 Proxy 把参数写进 `Parcel`，用 `ioctl` 交给 `/dev/binder` 驱动；驱动把数据拷进**目标进程**的接收缓冲区并唤醒它的 Binder 线程；Server 的 `Stub` 解析 `Parcel` 调真实方法，结果沿原路返回。

## 2 Linux 的 IPC 机制

Linux 内核本身提供多种 IPC，理解它们是理解「为什么需要 Binder」的前提。2.1~2.8 为原有整理，2.9 补一张对比表。

### 2.1 管道（PIPE）

用于进程间通信的一段共享内存，创建管道的进程称为管道服务器，连接到一个管道的进程为管道客户机。一个进程在向管道写入数据后，另一进程就可以从管道的另一端将其读取出来。用于父子进程或者兄弟进程之间，具有亲缘关系的进程之间的通信。

### 2.2 命名管道（FIFO）

是一种特殊类型的文件，它在系统中以文件形式存在。克服了管道的弊端允许没有亲缘关系的进程间通信。

### 2.3 信号（signal）

信号机制是unix系统中最为古老的进程之间的通信机制，用于一个或几个进程之间传递异步信号。信号可以有各种异步事件产生，比如键盘中断等。shell 也可以使用信号将作业控制命令传递给它的子进程。

### 2.4 消息队列（Message queues）

是内核地址空间中的内部链表，通过 linux 内核在各个进程直接传递内容，消息顺序地发送到消息队列中，并以几种不同的方式从队列中获得，每个消息队列可以用 IPC 标识 唯一地进行识别。内核中的消息队列是通过 IPC 的标识符来区别，不同的消息队列直接是相互独立的，每个消息队列中的消息，又构成一个 独立的链表。
消息队列克服了信号承载信息量少，管道只能承载无格式字符流。

### 2.5 信号量（Semaphore）

是一种计数器，用于控制对多个进程共享的资源进行的访问。常常被用作一个锁机制，在某个进程正在对特定的资源进行操作时，信号量可以防止另一个进程去访问它。
信号量是特殊的变量，它只取正整数值并且只允许对这个值进行两种操作：等待（wait）和信号（signal），简单来说就是PV操作，P用于等待，V用于信号 ，P 相当于申请资源，V 相当于释放资源 。

* P(sv)：sv > 0，就减 1；sv == 0，就挂起该进程的执行
* V(sv)：如果有其他进程因等待 sv 而被挂起，就让它恢复运行；如果没有其他进程因等待 sv而挂起，则给它加1 。

### 2.6 共享内存（Share Memory）

多个进程之间共享内存区域的一种进程间的通信方式，由 IPC 为进程创建一个特殊地址范围，它将出现在该进程的地址空间中。其他进程可以将同一段共享内存连接到自己的地址空间中。所有进程都可以访问共享内存中的地址，就好像它们是 malloc 分配的一样。如果一个进程向共享内存中写入了数据，所做的改动将立刻被其他进程看到。

### 2.7 内存映射（Memory Map）

**内存映射文件**，是由一个文件到一块内存的映射。内存映射文件与 虚拟内存有些类似，通过内存映射文件可以保留一个地址的区域，
同时将物理存储器提交给此区域，内存文件映射的物理存储器来自一个已经存在于磁盘上的文件，而且在对该文件进行操作之前必须首先对文件进行映射。使用内存映射文件处理存储于磁盘上的文件时，将不必再对文件执行I/O操作。 每一个使用该机制的进程通过把同一个共享的文件映射到自己的进程地址空间来实现多个进程间的通信（这里类似于共享内存，只要有一个进程对这块映射文件的内存进行操作，其他进程也能够马上看到）。
使用内存映射文件不仅可以实现多个进程间的通信，还可以用于处理大文件提高效率。因为我们普通的做法是把磁盘上的文件先拷贝到内核空间的一个缓冲区再拷贝到用户空间（内存），用户修改后再将这些数据拷贝到缓冲区再拷贝到磁盘文件，一共四次拷贝。如果文件数据量很大，拷贝的开销是非常大的。那么问题来了，系统在在进行内存映射文件就不需要数据拷贝？mmap()确实没有进行数据拷贝，真正的拷贝是在在缺页中断处理时进行的，由于mmap()将文件直接映射到用户空间，所以中断处理函数根据这个映射关系，直接将文件从硬盘拷贝到用户空间，所以只进行一次数据拷贝。效率高于read/write。

### 2.8 套接字（socket）

套接字机制不但可以单机的不同进程通信，而且使得跨网机器间进程可以通信。它明确地将客户端与服务器 区分开来，可以实现多个客户端连到同一服务器。

### 2.9 横向对比

| 机制 | 数据拷贝 | 是否 C/S | 能拿到调用方身份 | 主要短板 |
| --- | --- | --- | --- | --- |
| 管道 / FIFO | 2 次 | 否（单向流） | 不能 | 只能传字节流，管道限亲缘进程 |
| 消息队列 / mmap 文件 | 2 次 / 缺页时 1 次 | 否 | 不能 | 无对象语义，进程间「约定」成本高 |
| 共享内存 | 0 次（映射后直写） | 否 | 不能 | 同步自己做，越界风险高 |
| Socket | 2 次以上 | 是 | 弱（需 `SO_PEERCRED`） | 通用但重，协议/拆包自己写 |
| **Binder** | **1 次** | **是** | **能（内核填 uid/pid）** | 单次数据量小，同步调用阻塞调用线程 |

## 3 为什么需要 Binder

### 3.1 性能：少一次拷贝，AIDL 少写样板

管道、消息队列、socket 都要「发送方用户空间 → 内核缓冲区 → 接收方用户空间」两次拷贝；Binder 用 mmap 把接收缓冲区同时映射进接收方用户空间，只剩第一次。另外 AIDL 直接生成 Stub/Proxy，协议、序列化、分发都不用自己写——socket 方案要自己定协议、处理粘包。

### 3.2 安全：身份由内核填写，不可伪造

驱动在 `binder_transaction` 时记录发送方 uid/pid，接收方 `Binder.getCallingUid()` 拿到的就是驱动填的值。传统 IPC 只有 root/非 root 的粗粒度，管道、共享内存甚至没有「谁在调用」的概念；socket 要 `SO_PEERCRED`，拿到的是连接建立时的身份。有了可靠身份，才有 `checkCallingPermission`、`clearCallingIdentity` 这些上层能力（AMS 大量使用）。

### 3.3 面向对象：传的是「对象引用」而不是数据副本

Binder 实体在驱动里有 `binder_node`，跨进程传的是 **handle（引用）**，接收方拿到代理，调代理转发回原进程执行。这才让 `bindService` 返回的接口能像本地对象一样被调用，也是 `RemoteCallbackList` 能管理远端回调的前提。共享内存和管道做不到「把对象传过去再调它的方法」。

## 4 一次拷贝原理

### 4.1 传统 IPC 的两次拷贝

数据必须先进入内核（内核不能直接读写对方用户空间），再从内核复制到接收方：`发送方用户空间 --(1) copy_from_user--> 内核缓冲区 --(2) copy_to_user--> 接收方用户空间`。数据量大时这两次拷贝就是主要开销。

### 4.2 Binder 的 mmap：把接收缓冲区「共享」出去

进程启动时（`ProcessState` 初始化）`open("/dev/binder")` 并 `mmap` 一段内核分配的物理页到自己用户空间，这就是该进程的 **Binder 接收缓冲区**：这段物理页既被驱动访问，也被该进程用户空间访问。驱动写进去的数据，接收方直接读同一块物理页，省掉第二次 `copy_to_user`。

### 4.3 为什么叫「一次拷贝」

1. 发送方在用户空间组好 `Parcel`（普通用户内存）；
2. `ioctl(BINDER_WRITE_READ)` 进内核，驱动在**目标进程**的缓冲区里分配 `binder_buffer`，`copy_from_user` 把数据拷进去 —— **唯一一次拷贝**；
3. 驱动把事务挂到目标进程待办队列，唤醒一个 Binder 线程；
4. 目标线程收到 `BR_TRANSACTION`，在**同一块物理页**上构造只读 `Parcel` 解析（零拷贝）；
5. 处理完发 `BC_FREE_BUFFER` 释放。

注意方向：mmap 是**接收方**映射自己的接收缓冲区，发送方并不直接写对方内存（否则等于允许任意写别人的地址空间）。所以准确表述是：**发送方用户空间 → 目标进程的内核缓冲区（同时映射在目标进程用户空间）**。

### 4.4 缓冲区多大：1MB - 8KB

```cpp
// frameworks/native/libs/binder/ProcessState.cpp
#define BINDER_VM_SIZE ((1 * 1024 * 1024) - sysconf(_SC_PAGE_SIZE) * 2)
#define DEFAULT_MAX_BINDER_THREADS 15
```

* 1MB 减两个页：4KB 页时是 `1MB - 8KB`，16KB 页时是 `1MB - 32KB`（Android 15 起有 16KB 页设备，具体以源码为准）。
* 这是**每个进程的接收缓冲区总量**，不是「每笔事务 1MB」：同一进程所有并发事务共享这 1MB。
* 内核侧 `binder_alloc_mmap_handler` 把可映射上限限制在 4MB（`SZ_4M`），AOSP 的 libbinder 只申请约 1MB。
* `oneway` 另有配额：`free_async_space = buffer_size / 2`，最多占一半。

## 5 Binder 驱动与 `/dev/binder`

驱动（`drivers/android/binder.c`、`binder_alloc.c`）是「中转站 + 记账员」：管理每个进程的 `binder_proc`、接收缓冲区、待办队列；把实体和引用翻译成 handle；拷贝数据、唤醒目标线程、回传结果；记录 uid/pid；处理死亡通知和 `BINDER_FREEZE`。Android 11 起还支持 binderfs，可动态创建 `/dev/binderfs/binder` 等节点。

### 5.1 关键数据结构

| 结构 | 含义 | 一句话理解 |
| --- | --- | --- |
| `binder_proc` | 一个打开 `/dev/binder` 的进程 | 驱动眼里的进程上下文 |
| `binder_node` | 一个 Binder 实体（服务端对象） | 被引用的目标 |
| `binder_ref` | 某进程对某 node 的引用 | 「谁在用我」 |
| `binder_buffer` | 接收缓冲区里的一块 | 一次事务的数据载体 |
| `binder_transaction` / `binder_thread` | 一次事务 / 一个 Binder 线程 | 待办队列里的工作项、执行者 |

用户态拿到的 `IBinder` 背后就是 `(handle, 进程)`；handle 只在**本进程内**有效，同一实体在不同进程的 handle 可以不同（ServiceManager 固定 handle 0 例外）。

### 5.2 一次 ioctl 的协议

用户态与驱动之间是命令协议：`BC_*`（用户 → 驱动）、`BR_*`（驱动 → 用户），通过 `BINDER_WRITE_READ` 一次收发：

```cpp
struct binder_write_read bwr;
bwr.write_size   = mOut.dataSize();      // 要发的 BC_* 命令
bwr.write_buffer = (binder_uintptr_t)mOut.data();
bwr.read_size    = mIn.dataCapacity();   // 接收 BR_* 命令
bwr.read_buffer  = (binder_uintptr_t)mIn.data();
ioctl(mProcess->mDriverFD, BINDER_WRITE_READ, &bwr);
```

| 命令 | 方向 | 作用 |
| --- | --- | --- |
| `BC_TRANSACTION` / `BC_REPLY` | 用户 → 驱动 | 发起调用 / 回复 |
| `BC_ENTER_LOOPER` / `BC_REGISTER_LOOPER` | 用户 → 驱动 | 主动 / 被请求后加入线程池 |
| `BC_FREE_BUFFER` | 用户 → 驱动 | 用完缓冲区，交还 |
| `BR_TRANSACTION` / `BR_REPLY` | 驱动 → 用户 | 收到调用 / 收到回复 |
| `BR_SPAWN_LOOPER` | 驱动 → 用户 | 再开一个 Binder 线程 |
| `BR_DEAD_BINDER` / `BR_FROZEN_REPLY` | 驱动 → 用户 | 对端死亡 / 对端被冻结 |

## 6 ServiceManager

### 6.1 作用：Binder 的「电话簿」

ServiceManager 是一个**特殊的 Binder 服务**（init 启动的 native 进程 `servicemanager`），维护「服务名 → Binder 引用」：服务端 `ServiceManager.addService("activity", binder)` 注册，客户端 `getService("activity")` 按名字拿 `IBinder`，再 `Stub.asInterface()`。它是唯一不需要先查表就能找到的 Binder 引用：`ProcessState::getContextObject()` 对 **handle 0** 特殊处理，代表「上下文管理者」，所以 `getService` 就是「向 handle 0 发一次 `TRANSACTION_getService`」。

### 6.2 启动时机：必须早于所有 Binder 服务

`init.rc` 里声明 `service servicemanager /system/bin/servicemanager`，`class core`（`critical`），由 init 在 `on boot` 的 `class_start core` 拉起 —— **早于 Zygote（`class main`）、早于 SystemServer**。原因很直白：别的 Binder 服务要注册，得先有电话簿。

### 6.3 注册与查询流程

1. 服务端初始化完，调 `addService(name, binder, allowIsolated, dumpPriority)`；
2. ServiceManager 进程把 binder 转成自己的引用存进 `svc` 列表（`do_add_service`），并按 selinux 策略校验调用方是否有权注册该名字；
3. 客户端 `getService(name)` 向 handle 0 发一次 `do_find_service`，拿到 handle；
4. 驱动在客户端进程建 `binder_ref`，返回本进程内有效的 handle；
5. 客户端用它发 `BC_TRANSACTION`，驱动找到 node 对应的服务端线程投递。

## 7 Binder 通信模型

### 7.1 四个角色

| 角色 | 职责 | 典型代码 |
| --- | --- | --- |
| Client | 发起调用，持有 Proxy | `IMyService.Stub.asInterface(binder)` |
| Server | 提供实现，持有 Stub | `extends IMyService.Stub` |
| ServiceManager | 名字 → 引用的注册表 | `ServiceManager.getService("activity")` |
| Binder 驱动 | 拷贝、寻址、唤醒、身份、死亡通知 | `/dev/binder` |

Client 和 Server 之间没有直接连接，数据都经过驱动；ServiceManager 只是「第一次找服务」的中介，拿到 handle 后 Client 直接与 Server 通信。

### 7.2 一次跨进程调用的完整路径

1. Client 调 `proxy.getName()`；
2. Proxy 把参数写进 `_data`，调 `mRemote.transact(code, _data, _reply, 0)`；
3. `BinderProxy.transactNative` → JNI → `BpBinder::transact` → `IPCThreadState::transact`；
4. `IPCThreadState` 把 `BC_TRANSACTION` 写入 `mOut`，`ioctl(BINDER_WRITE_READ)` 进驱动；
5. 驱动按 handle 找到目标 node 与进程，分配 buffer、拷贝、唤醒目标线程，**同步调用在此阻塞**；
6. 目标收到 `BR_TRANSACTION` → `BBinder::transact` → `Binder.execTransact` → `Stub.onTransact`；
7. `onTransact` 里 `enforceInterface` 校验接口、读参数、调真实方法、`writeNoException` + 写结果；
8. 驱动把 reply 拷回 Client 接收缓冲区，唤醒 Client 线程，`transact` 返回；
9. Proxy 先 `readException()` 再读结果，返回调用方。

### 7.3 线程归属：谁阻塞、谁执行

* **Client 的调用线程阻塞**（同步调用），它可能是主线程 —— 这是「Binder 调用导致卡顿/ANR」的根源；
* **Server 的执行线程是 Binder 线程**（`binder:xxx` / `Binder:xxx`），不是 Server 主线程，所以 Stub 方法里默认没有「主线程」，更新 UI 必须自己 post；而 `oneway` 只保证「提交完成」，不保证「执行完成」。

## 8 AIDL 生成代码的结构

### 8.1 生成物与职责

AIDL 编译后得到一个 `IInterface` 接口，内部固定包含：`Stub`（服务端基类）、`Proxy`（客户端代理）、`TRANSACTION_xxx` 方法编号常量、`DESCRIPTOR` 接口全名。

| 类 | 运行位置 | 职责 |
| --- | --- | --- |
| `Stub` | 服务端进程 | 继承 `Binder`（本身是 `IBinder`），在 `onTransact` 里按 `code` 分发、解析参数、调实现、写回复 |
| `Proxy` | 客户端进程 | 持有 `IBinder mRemote`，写 `Parcel` → `transact` → 读回复，**看起来像本地方法** |
| `asInterface` | 客户端 | 同进程直接返回 Stub 本身，跨进程才包一层 Proxy |

### 8.2 典型生成代码

```java
public interface IMyService extends android.os.IInterface {
    String getName() throws android.os.RemoteException;

    abstract class Stub extends android.os.Binder implements IMyService {
        private static final String DESCRIPTOR = "com.example.IMyService";
        static final int TRANSACTION_getName = android.os.IBinder.FIRST_CALL_TRANSACTION + 0;
        public Stub() { this.attachInterface(this, DESCRIPTOR); }

        public static IMyService asInterface(android.os.IBinder obj) {
            if (obj == null) return null;
            android.os.IInterface iin = obj.queryLocalInterface(DESCRIPTOR);
            if (iin instanceof IMyService) return (IMyService) iin;  // 同进程：直接返回 Stub
            return new Proxy(obj);                                    // 跨进程：包一层代理
        }

        @Override
        public boolean onTransact(int code, android.os.Parcel data,
                                  android.os.Parcel reply, int flags) throws android.os.RemoteException {
            switch (code) {
                case TRANSACTION_getName: {
                    data.enforceInterface(DESCRIPTOR);   // 校验接口，防止调错方法
                    String _result = this.getName();     // 调真实实现，跑在 Binder 线程
                    reply.writeNoException();            // 先写异常标记，再写结果
                    reply.writeString(_result);
                    return true;
                }
            }
            return super.onTransact(code, data, reply, flags);
        }

        private static class Proxy implements IMyService {
            private final android.os.IBinder mRemote;
            Proxy(android.os.IBinder remote) { mRemote = remote; }
            @Override public String getName() throws android.os.RemoteException {
                android.os.Parcel _data = android.os.Parcel.obtain();
                android.os.Parcel _reply = android.os.Parcel.obtain();
                try {
                    _data.writeInterfaceToken(DESCRIPTOR);
                    mRemote.transact(TRANSACTION_getName, _data, _reply, 0); // 0 = 同步
                    _reply.readException();                                  // 服务端异常在此重抛
                    return _reply.readString();
                } finally { _reply.recycle(); _data.recycle(); }
            }
        }
    }
}
```

### 8.3 `transact` 的四个参数

| 参数 | 含义 | 注意 |
| --- | --- | --- |
| `code` | 方法编号 | 从 `FIRST_CALL_TRANSACTION` 起；手写 Binder 时自己约定 |
| `data` | 入参 `Parcel` | Proxy 写、`onTransact` 读 |
| `reply` | 出参 `Parcel` | `oneway` 时为 null |
| `flags` | `0` 同步 / `FLAG_ONEWAY` 单向 | 决定是否等 `BR_REPLY` |

### 8.4 `oneway` 的真实语义与参数方向

调用方把事务交给驱动就返回（等到 `BR_TRANSACTION_COMPLETE`），**不等服务端执行**；但服务端仍要占一个 Binder 线程，同一 node 上的 `oneway` 由驱动串行投递，不同对象之间可并行。服务端异常不会回传（没有 reply），大量 `oneway` 会占满异步配额，提交失败或触发 spam 检测。另外 AIDL 参数默认 `in`，`out`/`inout` 需要额外读写、开销更大；自定义 `Parcelable` 要提供 `CREATOR`，能传基本类型和 `Parcelable` 就别塞大 `Bundle`。

## 9 线程池与缓冲区

### 9.1 默认几个线程、什么时候创建

* `DEFAULT_MAX_BINDER_THREADS = 15`，这是**驱动可按需请求的 lazy 线程上限**；`startThreadPool()` 还会主动创建 1 个（`BC_ENTER_LOOPER`）。所以常说的「16 个 Binder 线程」= 1 个主动线程 + 最多 15 个按需线程，手动 `joinThreadPool()` 的另算。`system_server` 在 `SystemServer.java` 里用 `BinderInternal.setMaxThreads(31)` 调大上限（版本/厂商可能不同，以源码为准）。
* 线程不是启动就创建 16 个，而是按需增长：驱动发现没有空闲线程且未达上限时返回 `BR_SPAWN_LOOPER`，用户态 `ProcessState::spawnPooledThread` 创建并 `BC_REGISTER_LOOPER` 注册。

### 9.2 线程池耗尽（饥饿）

常见成因：`onTransact` 里做 I/O/数据库/大计算；持锁跨进程调用形成 A→B→C 嵌套同步链；大量慢 `oneway` 占满工作线程；服务端主线程也在等 Binder 回复。表象是 `binder thread pool (15 threads) starved for xxx ms` 加客户端 ANR。治理顺序：缩短临界区 → 加超时 → 异步化 → 最后才考虑加线程。

## 10 Parcel 与序列化

* `Parcel` 是**连续内存**的读写封装，不是通用序列化框架：只支持基本类型、`String`、数组、`Parcelable`、`IBinder`、`FileDescriptor`、`Bundle` 等。
* 写的是**二进制布局**，读写顺序必须严格一致（写 `int` 后读 `String` 就错位）；`obtain()` 从池里取，用完必须 `recycle()`，否则内存抖动。`Parcelable` 手写读写、无反射，比 `Serializable` 快且体积小。
* `writeStrongBinder` / `readStrongBinder` 传的是 **handle** 不是对象本身 —— 「跨进程传对象」的实现基础。
* 传大对象触发 `TransactionTooLargeException`：1MB 是进程级且并发共享，所以「一次传 900KB」也可能失败。

## 11 Binder 死亡通知

```java
private final IBinder.DeathRecipient mDeath = () -> mHandler.post(this::onRemoteDied);

try {
    binder.linkToDeath(mDeath, 0);          // 0：对端已死时立刻回调并抛 RemoteException
    mRemote = IMyService.Stub.asInterface(binder);
} catch (RemoteException e) {
    // 注册时对端已经死了
}
binder.unlinkToDeath(mDeath, 0);            // 不再使用时必须解注册，否则 DeathRecipient 泄漏
```

* 回调在 **Binder 线程**执行，更新 UI 要切主线程；驱动通过 `BR_DEAD_BINDER` 通知，且通知是**一次性**的，对端重启后是新实体，要重新 `bindService` 再注册；
* 心跳只能发现「慢」，发现不了「死」；`linkToDeath` 负责失效，心跳负责超时，二者配合。

## 12 Binder 与 AIDL / Messenger / ContentProvider 的关系

| 封装 | 底层 | 适用 | 限制 |
| --- | --- | --- | --- |
| AIDL | 直接生成 Stub/Proxy | 高频、多方法、要返回值 | 要写 .aidl，两端接口同步 |
| Messenger | `IMessenger.aidl` + `Handler` | 只发消息、串行处理 | 全走一个 `Handler`，天然串行 |
| ContentProvider | `IContentProvider.aidl` + AMS 调度 | 跨进程数据共享、CRUD | 面向数据，启动有成本 |

一句话：**AIDL 是「怎么写」，Binder 是「怎么传」，Messenger 和 ContentProvider 是 Binder 的两种现成用法**。

## 13 Java Binder 与 native Binder 的分层

| 层 | Java | Native | 说明 |
| --- | --- | --- | --- |
| 接口 | `IBinder` / `IInterface` | `IBinder` / `IInterface` | 两套同名接口，JNI 桥接 |
| 本地实体 | `Binder` | `BBinder` | 服务端对象 |
| 远端代理 | `BinderProxy` | `BpBinder` | 持有 handle，转发事务 |
| 每线程状态 | — | `IPCThreadState` | 每线程一份 `mOut`/`mIn` |
| 每进程状态 | — | `ProcessState` | `mDriverFD`、接收缓冲区、线程池 |
| 驱动 | `/dev/binder` | 同 | 唯一内核入口 |

一次 Java 调用的下沉路径：`BinderProxy.transact` → `transactNative` → `android_os_BinderProxy_transact`（`android_util_Binder.cpp`）→ `BpBinder::transact` → `IPCThreadState::transact` → `talkWithDriver` → `ioctl(fd, BINDER_WRITE_READ, &bwr)`，回到用户态由 `executeCommand` 处理 `BR_REPLY` 写回 `Parcel`。反向是驱动 → `executeCommand` 收 `BR_TRANSACTION` → `BBinder::transact` → JNI → `Binder.execTransact` → `Stub.onTransact`。`Parcel` 在 Java 层是 `android.os.Parcel`、native 层是 `android::Parcel`，JNI 互相持有指针，**不复制数据**。

## 14 Android 12—16 的变化

> 这部分跨内核与框架两层，行为还受设备配置和厂商实现影响，具体以官方文档和实机为准。

### 14.1 冻结（freeze）与后台限制

* 系统把退到后台的缓存进程「冻结」：线程拿不到 CPU，但进程、地址空间、Binder 引用都还在（**冻结 ≠ 释放内存**）。
* 冻结时驱动分流：**同步事务被拒**（`BR_FROZEN_REPLY`，框架侧是 `RemoteException`/`FAILED_TRANSACTION`，并可能以「冻结期间收到同步调用」终止被冻结进程）；**`oneway` 允许入队**（`BR_TRANSACTION_PENDING_FROZEN`），解冻后集中处理，可能积压并造成 CPU 尖峰。
* Cached Apps Freezer 从 Android 11 起在 AOSP 提供，Android 12 周期内核补齐 Binder freeze（`BINDER_FREEZE`），Android 14 起默认 10 秒防抖、生命周期事件立刻解冻；是否启用取决于设备配置。
* 实践启示：**`unbindService` 后立刻丢弃代理**，别长期持有旧 `IBinder`；给后台服务发同步调用必须有失败分支。

### 14.2 12—13：可观测性

* 框架增加 Binder 调用统计（`dumpsys binder_calls_stats` 一类入口），可按 UID/接口/方法看次数、耗时、Parcel 大小，定位「谁在频繁跨进程」；字段随版本变化，以实机为准。
* Android 13 公开 `ApplicationExitInfo.REASON_FREEZER`，可把「被冻结器杀掉」和 LMK、ANR 区分开。
* 内核侧加入 `oneway` 洪泛检测（spam suspect）：同一发送方大量占用目标异步缓冲区时打印告警，但**不会自动限流**，治理仍靠应用层合并/限频。

### 14.3 Android 14—15：后台继续收紧

* Android 14：前台服务类型必填、后台启动 Activity 更严；动态注册的广播可先排队、解冻后投递 —— 「靠 Binder 回调驱动 UI」的架构要接受回调延迟到解冻后。
* Android 15：`dataSync`/`mediaProcessing` 类型前台服务有运行时长上限；后台启动 Activity 的旧例外（如 `SYSTEM_ALERT_WINDOW`）被移除，`PendingIntent` 拉起界面要显式 opt-in。结果是从后台通过 Binder 调 AMS 弹页面基本走不通。
* Android 15 起出现 16KB 页设备：`BINDER_VM_SIZE` 变成 `1MB - 32KB`，native 库要按 16KB 对齐重编，硬编码 4096 的缓冲区计算会算错。

### 14.4 Android 16（API 36）

* 公开 `IBinder#addFrozenStateChangeCallback` / `removeFrozenStateChangeCallback`，可观察**远端**是否被冻结；内核不支持时抛 `UnsupportedOperationException`，必须写降级分支（以官方文档为准）。
* `RemoteCallbackList` 增加「被调用方冻结时」的策略：丢弃、只保留最新、全部排队（有队列上限），用来替代无限堆积 `oneway` 回调 —— 官方推荐做法，比自维护队列稳。
* 16KB 页大小成为正式兼容目标，Binder 缓冲区大小和 native 内存假设都要复查。
* 进程内 `BinderProxy` 数量可用 `Debug.getBinderProxyObjectCount()` 一类接口观察（较新版本提供，API level 以官方文档为准），用于排查「代理只增不减」；`BinderProxy` 会按 handle 缓存复用，重复 `asInterface` 不一定新建 native 代理，具体以源码为准。

## 15 面试问答

### Q1：Android 为什么不用 Linux 现成的 IPC，非要自己做 Binder？

三个理由：**性能**（mmap 只拷一次，管道/socket 要两次）、**安全**（驱动记录 uid/pid，身份不可伪造，能支撑权限校验）、**面向对象**（传的是对象引用，能像本地方法调用，还带死亡通知）。共享内存虽然零拷贝，但要自己做同步、没有身份和对象语义，适合传大数据而不是组件间调用。

### Q2：「一次拷贝」省的是哪一次？为什么接收方不用再拷一次？

省的是「内核缓冲区 → 接收方用户空间」这次 `copy_to_user`。接收进程启动时把自己的 Binder 接收缓冲区 `mmap` 到用户空间，这块物理页同时被内核和接收方映射，驱动写进去的数据接收方直接读同一块内存。发送方那一侧仍要 `copy_from_user` 进内核，否则就等于允许进程直接写别人的地址空间。

### Q3：Binder 是不是每笔事务能传 1MB？为什么还会 `TransactionTooLargeException`？

不是。1MB-8KB 是**每个进程接收缓冲区的总量**，同一进程所有并发事务共享；内核最多允许映射 4MB，但 AOSP 只申请约 1MB。所以「一次传 900KB」在并发下也可能失败。大数据应该传 fd / `SharedMemory` / 文件，而不是塞 `Bundle`。

### Q4：Binder 线程池默认几个线程？什么时候会耗尽？

源码是 `DEFAULT_MAX_BINDER_THREADS = 15`（驱动按需请求的上限）+ `startThreadPool()` 主动创建的 1 个，所以常说 16 个；`system_server` 会调到 31。耗尽通常不是线程太少，而是 `onTransact` 里有慢 I/O、持锁跨进程调用、或大量慢 `oneway` 占着工作线程。加线程一般不是第一选择，先缩短临界区和加超时。

### Q5：Stub、Proxy、`asInterface` 各做什么？同进程调用会走 Binder 吗？

`Stub` 是服务端基类，继承 `Binder`，在 `onTransact` 里按 `code` 分发并解析 `Parcel`；`Proxy` 是客户端代理，写 `Parcel` 后 `transact`。`asInterface` 先 `queryLocalInterface`，同进程直接返回 Stub 本身 —— 此时是**普通 Java 调用，不经过驱动、不序列化**；只有跨进程才 `new Proxy(obj)`。

### Q6：`oneway` 和同步调用的区别？为什么 `oneway` 也可能失败？

同步调用阻塞到收到 `BR_REPLY`；`oneway` 只等到「提交完成」（`BR_TRANSACTION_COMPLETE`）就返回。但服务端仍占 Binder 线程，同一 node 的 `oneway` 仍串行，异步缓冲区只有一半配额，塞满就提交失败；服务端异常也不会回传。所以 `oneway` 适合「可丢、可合并、不需要返回值」的事件，不是可靠消息通道。

### Q7：`linkToDeath` 有什么用？回调在哪个线程？能用心跳替代吗？

用来在服务端进程死亡时收到 `binderDied()`，及时清理代理、重连或降级。回调在 **Binder 线程**，更新 UI 要切主线程；通知是一次性的，对端重启后要重新绑定注册。心跳只能发现「慢/无响应」，发现不了「已死」，两者配合才完整。别忘了 `unlinkToDeath`，否则 `DeathRecipient` 泄漏。

### Q8：Java Binder 和 native Binder 是什么关系？

同一套机制的两层封装：Java 的 `Binder`/`BinderProxy` 通过 JNI 对应 native 的 `BBinder`/`BpBinder`，最终都落到 `IPCThreadState::transact` → `ioctl(BINDER_WRITE_READ)`。Java 层多出来的主要是 `Parcel` 封装、`IInterface` 描述符校验和线程池管理，驱动行为完全一致。理解这条链路才能解释「`onTransact` 为什么跑在 Binder 线程」「主线程调用为什么卡」。

## 参考阅读

* [linux基础——linux进程间通信（IPC）机制总结](https://blog.csdn.net/a987073381/article/details/52006729)
* [一篇文章了解相见恨晚的 Android Binder 进程间通讯机制](https://jeanboy.blog.csdn.net/article/details/70082302?utm_medium=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-3.control&dist_request_id=&depth_1-utm_source=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-3.control)
* [Binder学习指南](http://weishu.me/2016/01/12/binder-index-for-newer/)
* [AOSP：Binder 线程模型](https://source.android.com/docs/core/architecture/ipc/binder-threading)
* [AOSP：Binder 与缓存进程冻结](https://source.android.com/docs/core/architecture/ipc/binder-freezer)
