## 1 为什么需要共享内存

Binder 是 Android 最常用的 IPC，但它并不适合搬大块数据：

* **缓冲区小**：Binder 驱动为每个进程映射的事务缓冲区默认只有 1MB - 8KB（`BINDER_VM_SIZE`），且被该进程所有 Binder 事务共享。
* **拷贝多**：一次事务至少经历「用户空间 → 内核缓冲区 → 目标进程」两次拷贝，Parcel 还要做序列化。
* **失败代价高**：数据接近上限时很容易抛 `TransactionTooLargeException`，日志里常能看到 "data parcel size ... bytes"。

一张 4000×3000 的 ARGB_8888 图片约 48MB，走 Binder 必然失败；即使只有几百 KB，频繁拷贝也会带来卡顿和 GC 压力。

| 方式 | 数据拷贝 | 大小限制 | 典型用途 |
| --- | --- | --- | --- |
| Binder `byte[]` / Bundle | 2 次 | 约 1MB/进程 | 小对象、控制指令 |
| 文件 / ContentProvider | 磁盘 IO + 用户态拷贝 | 受存储限制 | 持久化、媒体文件 |
| Socket / Pipe | 2 次 | 流式，无单条上限 | 顺序流、跨机通信 |
| **共享内存 + fd** | 映射后 0 次 | 受物理内存/地址空间限制 | 大图、音视频帧、大缓冲区 |

共享内存的做法是：内核创建一块匿名文件（tmpfs/shmem），两个进程各自 `mmap` 同一个文件，得到指向同一批物理页的虚拟地址；Binder 只负责传一个文件描述符。所谓「零拷贝」指映射建立后读写不再经过内核缓冲区，首次缺页仍要分配和清零物理页。

## 2 Binder 的 1MB 限制

`BINDER_VM_SIZE` 在 Binder 驱动里定义为 `1MB - 8KB`，是**每个进程**的 mmap 大小，不是每次事务独享：

* 一个进程里所有 Binder 线程、所有并发事务共用这 1MB。
* 事务缓冲区里放的是 Parcel 数据、对象偏移表和少量控制信息；对象越大，越容易提前耗尽。
* 触发限制时，服务端可能返回 `BR_FAILED_REPLY`，客户端收到 `TransactionTooLargeException`；系统进程出问题还可能拖垮整机。

传 fd 之所以能绕开：`ParcelFileDescriptor` 写进 Parcel 的只是一个整数形式的 fd，Binder 驱动在目标进程里重新安装一个 fd，指向内核中同一个 `struct file`。数据本身没有进事务缓冲区，成本与文件大小无关。

> 经验值：Bundle 超过 500KB 就要警惕；图片、音频、大 JSON 不要走 Binder。

## 3 Ashmem 是什么

Ashmem（Anonymous Shared Memory）是 Android 早期引入的匿名共享内存驱动，设备节点是 `/dev/ashmem`，通过 ioctl 管理：

* `ASHMEM_SET_NAME`：设置名字，方便在 `/proc/<pid>/maps`、`dumpsys meminfo` 里排查。
* `ASHMEM_SET_SIZE`：设置大小，内核按页向上取整。
* `ASHMEM_PIN_UNPIN`：pin 住一段区间，禁止回收；unpin 后内存紧张时可被 shrinker 回收。
* `ASHMEM_SET_PROT_MASK`：设置保护位，例如写完后降为只读。

它并不是一块「凭空出现」的内存：ashmem 驱动内部通过 `shmem_file_setup()` 在 tmpfs 上创建一个匿名文件，再把文件映射到用户空间。所以物理页由 shmem/tmpfs 管理，ashmem 额外提供的是**命名、按区间 pin/unpin、保护位**这些 Android 语义。

```c
int fd = ashmem_create_region("demo", size);           // open /dev/ashmem + SET_NAME + SET_SIZE
void *p = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
// ... 写入数据 ...
ashmem_set_prot_region(fd, PROT_READ);                 // 降为只读，防止对端篡改
```

几个容易忽略的点：

* `mmap` 必须用 `MAP_SHARED`，用 `MAP_PRIVATE` 会得到写时复制，对端看不到修改。
* `close(fd)` 之后已建立的映射仍然有效（映射持有 file 引用），但要在关闭前把 fd 传给对端。
* ashmem 从未进入 Linux mainline 的稳定 ABI，长期位于 Android 内核树（staging），这是后来被 memfd 取代的原因之一。

## 4 与 Linux shmem、memfd 的关系

三者是「机制」与「封装」的关系：

| 维度 | shmem / tmpfs | ashmem | memfd |
| --- | --- | --- | --- |
| 是什么 | 内核的共享内存文件系统机制 | Android 驱动，基于 shmem 文件 | 系统调用，返回匿名 shmem 文件的 fd |
| 创建方式 | 挂载 tmpfs 后 open 文件 | `open("/dev/ashmem")` + ioctl | `memfd_create(name, flags)` |
| 大小 | `ftruncate` / 文件系统 | `ASHMEM_SET_SIZE` | `ftruncate` |
| 回收粒度 | 文件/页缓存 | 可按区间 unpin 后回收 | 整个文件，无区间 pin |
| 封印 | 无 | 无 | 可用 `F_ADD_SEALS` 加封（禁止扩容/缩容/写入） |
| 跨进程 | 传 fd 或路径 | 传 fd | 传 fd |
| 上游 Linux | 是 | 否（Android 树） | 是（Linux 3.17+） |

memfd 的优势是上游通用、适配 GKI、支持 sealing（`F_SEAL_GROW`/`F_SEAL_SHRINK`/`F_SEAL_WRITE` 可固定大小和内容）、攻击面更小；代价是没有 ashmem 的按区间 pin/unpin，内存压力下不能只回收某一段，只能拆多个 memfd 或由业务自己控制。

## 5 Android 版本演进：ashmem → memfd

| 版本 | 变化 | 对开发者的影响 |
| --- | --- | --- |
| Android 8.0（API 26） | NDK 提供 `ASharedMemory_*`（`android/sharedmem.h`） | native 代码有了稳定接口 |
| Android 8.1（API 27） | Java 层新增 `android.os.SharedMemory` | 新代码优先用它，而不是反射 `MemoryFile` |
| Android 10 | libcutils 增加 memfd 后端，按内核能力和 `sys.use_memfd` 开关选择 | 不要假设 fd 一定是 ashmem，不要直接对 fd 做 ashmem ioctl |
| Android 11 | memfd 成为主路径，ashmem 被标记为废弃；新设备可能没有 `/dev/ashmem` | 迁移到 `SharedMemory` / `ASharedMemory` |
| Android 12 | GKI 内核不再包含 ashmem 驱动，旧接口由 libcutils/兼容层兜底 | 只使用公开 API；旧 ioctl 会返回 `ENOTTY` |

Android 12 前后需要特别注意的 API 行为：

* `SharedMemory` / `MemoryFile` 在 Android 12 的新内核上由 memfd 支撑，创建后大小固定，没有扩容 API。
* `SharedMemory.setProtect()` 只能移除权限、不能新增，而且**只影响之后创建的映射**；已有 mmap 保持创建时的权限。
* 通过 Binder 传 `SharedMemory` 或 `ParcelFileDescriptor` 时，接收方拿到的是新 fd，但映射的是同一份文件；不要假设 fd 数字相同。
* `MemoryFile.getFileDescriptor()` 仍可取到 fd，但不要再对它调用 `ASHMEM_*` ioctl；不同厂商内核的兼容层行为可能不同，以官方文档和 AOSP 源码为准。

> 结论：Android 10 开始过渡，Android 11 起 ashmem 逐步退场，Android 12 的新内核上应把共享内存当成「memfd + fd 传递」来用。

## 6 Java/Kotlin：MemoryFile

`MemoryFile` 是 API 1 的老接口，新版本内部是 `SharedMemory` 的包装，适合按字节读写。

```kotlin
val size = 4 * 1024 * 1024
val file = MemoryFile("share-bytes", size)
val bytes = ByteArray(size) { it.toByte() }
file.writeBytes(bytes, 0, 0, bytes.size)
val input = file.getInputStream()
```

`MemoryFile` 没有公开的 mmap API；`getFileDescriptor()` 在 API 27 之后被标记为 `@hide`，普通 App 不应依赖（老代码常见，但会受 hidden API 限制）。要跨进程共享，直接用 `SharedMemory` 的 `Parcelable`，或在 native 用 `ASharedMemory_dupFromJava` 拿 dup 的 fd。

| 维度 | `MemoryFile` | `SharedMemory` |
| --- | --- | --- |
| 引入版本 | API 1 | API 27 |
| 访问方式 | `readBytes` / `writeBytes` / 流 | `mapReadOnly` / `mapReadWrite` 返回 `ByteBuffer` |
| 传 fd | `getFileDescriptor()`（API 27 起 hide） | 本身是 `Parcelable`；fd 由 native dup |
| 权限控制 | 能力有限 | `setProtect()` 单向移除权限 |
| 适用 | 老代码兼容、简单字节读写 | 新代码、需要直接映射 |

两者都基于 fd + mmap；新代码用 `SharedMemory`，不要为了拿 fd 反射隐藏方法。

## 7 Java/Kotlin：SharedMemory

`SharedMemory` 用 `ByteBuffer` 直接映射，读写不经过 `readBytes` 的数组拷贝；它本身实现 `Parcelable`，跨进程直接传对象即可：

```kotlin
val shm = SharedMemory.create("share-image", size)
val buffer = shm.mapReadWrite()
buffer.put(bytes)                              // 写满后 position = size

shm.setProtect(OsConstants.PROT_READ)          // 只影响之后的映射，先写完再降权
bundle.putParcelable("shm", shm)               // Binder/AIDL 传给对端
```

接收端：

```kotlin
val shm = bundle.getParcelable<SharedMemory>("shm")!!
val buffer = shm.mapReadOnly()
val out = ByteArray(buffer.remaining())
buffer.get(out)
shm.close()
```

`SharedMemory` 的 `getFd()`/`getFileDescriptor()` 从 API 27 起就是 `@hide`（生命周期容易 double close），Java 层不要调用。需要 fd 时走 native：`ASharedMemory_dupFromJava(env, javaShm)` 返回一个 dup 的 fd（NDK API 27+），再包成 `ParcelFileDescriptor` 或直接 `mmap`。

服务端要校验 `size` 与 `Os.fstat(fd).st_size`，不要信任对端传来的长度；这里 `fd` 指 native 侧拿到的描述符。

## 8 Native：ashmem_create_region、mmap 与 fd

`ashmem_create_region` 属于 `libcutils`，是 platform 内部接口；普通 App 的 NDK 代码用 `ASharedMemory`（API 26+）：

```c
#include <android/sharedmem.h>
#include <sys/mman.h>
int fd = ASharedMemory_create("note-demo", size);
void *addr = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
ASharedMemory_setProt(fd, PROT_READ);   // 之后的映射只读
```

* `ashmem_create_region` / `ashmem_set_prot_region` 的写法和上面一致，只是头文件换成 `<cutils/ashmem.h>`。
* `size` 按页向上取整，`mmap` 的 offset 必须是页大小整数倍，通常传 0；必须用 `MAP_SHARED`。
* 映射建立后可 `close(fd)`，映射仍有效；但要在关闭前把 fd 传给对端。
* 接收方至少 `PROT_READ`；写完用 Binder 调用/futex/原子变量通知对端，共享内存本身不提供同步。
* Java ↔ native：`ASharedMemory_dupFromJava` 从 Java 的 `SharedMemory` 复制 fd，避免 double close。

## 9 文件描述符跨进程传递：ParcelFileDescriptor

AIDL/ContentProvider 传 fd 的载体是 `ParcelFileDescriptor`，底层走 `Parcel.writeFileDescriptor()` / `readFileDescriptor()`。

```kotlin
// 接收端：AIDL 参数中的共享内存 PFD
val shm = SharedMemory.fromFileDescriptor(pfd)   // 接管 pfd 的 fd，不要再 close(pfd)
val buffer = shm.mapReadOnly()
// ... 读取 ...
shm.close()
```

```kotlin
// 发送端：如果手里是 PFD，直接写 Parcel
parcel.writeParcelable(pfd, 0)
pfd.close()                                      // Parcel 内部已 dup
```

所有权规则（面试常问）：

| 操作 | 是否新建 fd | 谁负责关闭 |
| --- | --- | --- |
| `ParcelFileDescriptor.dup(FileDescriptor)` | 是 | 调用方（原 fd 也归调用方） |
| `ParcelFileDescriptor.fromFd(int)` | 是，内部 dup | 调用方仍持有原 fd |
| `ParcelFileDescriptor.adoptFd(int)` | 否，接管传入 fd | PFD 的持有方 |
| `Parcel.writeFileDescriptor(fd)` | 是，Parcel 内部 dup | Parcel 发送/回收时 |
| `ParcelFileDescriptor.detachFd()` | 否，交出 fd | 调用方 |
| `SharedMemory.fromFileDescriptor(pfd)` | 否，detach pfd 的 fd | `SharedMemory` |

常见坑：

* Java 的 `SharedMemory` 没有公开 `getFd()`，不要反射；要 PFD 就在 native 用 `ASharedMemory_dupFromJava`。
* fd 泄漏会耗尽进程 fd 配额，用 `use {}` 或 `try/finally`；对端传来的 `size` 先用 `fstat` 校验。
* `ParcelFileDescriptor` 传的是「打开文件描述」，接收方拿到独立 fd，但共享同一个 file offset 和文件状态标志。

## 10 Bitmap 共享内存与 HardwareBuffer

Bitmap 的像素内存在 Android 8.0 后主要分配在 native 堆（由 `NativeAllocationRegistry` 回收），不是 Java 堆；`Bitmap.Config.HARDWARE`（API 26）则把像素放进图形内存（gralloc），CPU 不能直接 `getPixels()`。

跨进程传大图通常有三条路：

1. **直接 Parcel Bitmap**：`Bitmap` 实现了 `Parcelable`，系统对大图的 Parcel 有特殊处理（不同版本实现不同），但业务侧不应依赖细节，超大图仍不推荐。
2. **共享内存 + 元数据**：把像素写进 `SharedMemory`/`MemoryFile`，通过 fd 传宽高、格式、stride、颜色空间，接收方自己建 Bitmap 并拷贝。
3. **HardwareBuffer**：API 26 引入，底层是 gralloc 图形缓冲区，可被 GPU、MediaCodec、显示合成、`ImageReader` 直接使用；API 29 起可用 `Bitmap.wrapHardwareBuffer(buffer, colorSpace)` 包成 `Bitmap`，跨进程可把 `HardwareBuffer` 作为 `Parcelable` 传递。

| 维度 | ashmem / memfd | HardwareBuffer |
| --- | --- | --- |
| 分配者 | 应用/系统，CPU 可 mmap | gralloc/图形驱动 |
| 访问方式 | CPU 读写 | GPU 采样/渲染、MediaCodec、CPU lock |
| 跨进程 | fd | `Parcelable`（底层也是 handle/fd） |
| 典型用途 | 大 byte[]、图片像素、序列化数据 | 相机预览、视频解码、渲染纹理、截图 |

```kotlin
val buffer = HardwareBuffer.create(
    width, height, HardwareBuffer.RGBA_8888, 1,
    HardwareBuffer.USAGE_GPU_SAMPLED_IMAGE or HardwareBuffer.USAGE_GPU_COLOR_OUTPUT
)
val bitmap = Bitmap.wrapHardwareBuffer(buffer, ColorSpace.get(ColorSpace.Named.SRGB))
// 交给 Canvas/GPU 使用；确保没有使用者后再 buffer.close()
```

注意：`HardwareBuffer` 和包装出的 `Bitmap` 生命周期要分开管理；`Bitmap.Config.HARDWARE` 的图不能直接读像素，需要 `copy(Bitmap.Config.ARGB_8888, false)` 落到 CPU 可读内存。

## 11 典型场景

### 11.1 系统截图

`MediaProjection` 返回虚拟屏幕，应用通过 `ImageReader` 拿到 `Image`，按 `rowStride` 读 plane（行间可能有 padding），或经 `HardwareBuffer` 交给 GPU。1440×3200 的截图约 18MB，不可能塞进 Binder；系统内部用图形缓冲区 + handle 传递，应用侧要及时 `image.close()`。

### 11.2 跨进程大图

相册选图、图片编辑、壁纸设置常见：Provider 进程解码 → 写入共享内存 → 把 fd + 宽高/格式/stride 传给编辑进程。接收方直接 `mmap` 或拷贝到 Bitmap，避免 Base64，也避免 `byte[]` 走 Binder。

### 11.3 MediaCodec 与其他

`MediaCodec` 的输入/输出缓冲区来自图形/媒体缓冲区（`ByteBuffer`、`Image` 或 `HardwareBuffer`），不是普通 ashmem；`createInputSurface()` 让相机/渲染直接写编码器，实现零拷贝。其他常见点：`ContentProvider.openFile()` 返回 `ParcelFileDescriptor`；`SurfaceControl`/`SurfaceTexture` 跨进程传图形缓冲区 handle；大 JSON/日志先落盘或写共享内存，再传 fd + 长度。

## 12 面试问答

### Q1：Binder 的 1MB 是单次限制还是每进程限制？
每进程。Binder 驱动为每个进程 mmap 一块 `1MB - 8KB` 的事务缓冲区，该进程所有 Binder 线程和并发事务共享；单个事务接近上限就会失败。大图/大数组应改用共享内存 + fd，Binder 只传描述符。

### Q2：ashmem 和 memfd 有什么区别，为什么 Android 要换？
两者底层都是 tmpfs/shmem 文件，差别在封装：ashmem 是 Android 私有驱动，提供命名、按区间 pin/unpin、保护位 ioctl；memfd 是 Linux 通用系统调用，返回匿名文件 fd，支持 `F_ADD_SEALS` 封印。换 memfd 是为了去掉树外驱动、适配 GKI、减小攻击面，代价是失去按区间回收能力。

### Q3：MemoryFile 和 SharedMemory 怎么选？
新代码优先 `SharedMemory`（API 27）：直接 `ByteBuffer` 映射、可 `setProtect` 降权、本身可 Parcel。`MemoryFile` 是 API 1 的老接口，适合兼容旧代码和简单字节读写；两者最终都是 fd + mmap，但 `MemoryFile` 的 `readBytes`/`writeBytes` 多一层字节数组拷贝。

### Q4：传 fd 为什么不算拷贝？两个进程 mmap 为什么看到同一份数据？
Binder 只把 fd 翻译成目标进程的一个新描述符，指向内核同一个 `struct file`，没有搬数据。两个进程各自 `mmap(MAP_SHARED)` 同一文件时，页表映射到同一批物理页，所以一边写完另一边能看见；但「能看见」不等于「同步好」，仍需 barrier/锁/futex 保证顺序。

### Q5：Bitmap 大图跨进程怎么做？HardwareBuffer 和 ashmem 有什么区别？
大图把像素放共享内存，传 fd + 宽高/格式/stride，接收方 mmap 后建 Bitmap；要走 GPU/相机/解码链路就用 `HardwareBuffer`，它是 gralloc 图形缓冲区，能直接被 GPU、MediaCodec、显示合成消费。ashmem/memfd 是 CPU 可映射的普通内存，HardwareBuffer 是图形内存，二者生命周期和访问方式都不同。

### Q6：使用共享内存要注意什么？
生命周期上分清 fd、映射、`SharedMemory`/`ParcelFileDescriptor` 的所有权，避免 double close 和泄漏；对端传来的 size/offset/stride 一律先用 `fstat` 校验；共享内存不提供同步，写完用 Binder 调用、futex 或原子变量通知；写完后 `setProtect(PROT_READ)` 降为只读；ashmem 可 unpin 回收，memfd 只能整体管理，大块共享内存要评估 OOM 风险。

参考：Android `SharedMemory` 源码、`system/core/libcutils/ashmem-dev.cpp`、Linux `memfd_create(2)` 手册；版本行为以官方文档与 AOSP 源码为准。
