# Android 面试题精选（2025）

> 一份可以直接拿来自测和背诵的现代 Android 面试题库。每题只给"能说出口"的要点，不追求教科书式完整；需要展开的细节，回到本仓库对应的专题笔记。
>
> 现状以 **2025 年底** 为准：IntentService、AsyncTask 已废弃，ButterKnife、GreenDAO、Tinker 已停止维护，Dagger2 官方推荐迁移到 Hilt。

## 目录

- 一、Java 与 Kotlin（13 题）
- 二、语言与运行时（11 题）
- 三、四大组件与 Framework（17 题）
- 四、现代 UI（10 题）
- 五、协程与异步（10 题）
- 六、Jetpack（11 题）
- 七、性能优化（11 题）
- 八、架构与工程（9 题）
- 九、系统与适配（10 题）
- 十、开放题（7 题）

合计 109 题，建议按主题滚动自测，答不上来的再回专题笔记补。

## 一、Java 与 Kotlin

### Q: Java 17 和 Java 21 有哪些值得关注的新特性？
**答**：
- Java 17 是 LTS：record 转正、sealed 类转正、instanceof 模式匹配转正、文本块转正，switch 模式匹配还是预览。
- Java 21 是下一个 LTS：switch 的模式匹配 + 记录模式转正（JEP 441）、虚拟线程转正（JEP 444）、SequencedCollection、分代 ZGC。
- Android 侧：AGP 8.x 起 `compileOptions` 可以写 17，D8 负责脱糖成 dex；`java.time`、`Stream` 这类**库 API** 要开 `coreLibraryDesugaring`。
- 面试可以补一句：Android 上没有 HotSpot，字节码最终跑在 ART 上，所以"Java 版本"更多是**语法和库**的事。

### Q: record 和普通类有什么区别？在 Android 上能用吗？
**答**：
- record 是"不可变数据载体"：字段全 final，编译器生成全参构造、访问器、`equals/hashCode/toString`。
- 它隐式继承 `java.lang.Record`，所以**不能再继承别的类**，也不能声明额外的实例字段；可以 implements 接口、可以写紧凑构造器做参数校验。
- 和 Kotlin `data class` 比：record 没有 `copy()`、没有 `componentN()` 解构，但天然不可变；`data class` 属性可以是 var，也能继承。
- Android 上 D8 能脱糖 record，但需要较新的 AGP；如果项目还在老 AGP，用 `data class` 更省事。反射/序列化框架对 record 的兼容性也要先验证。

### Q: sealed class / interface 解决什么问题？
**答**：
- 它把"子类型集合"封闭起来：`permits` 列出的（或同文件/同包的）子类之外，不允许别人再继承。
- 最大价值是配合 switch 做**穷尽性检查**：少写一个分支编译期就报错，不用再写"兜底 default"。
- 子类只能是 `final`、`sealed` 或 `non-sealed` 三种之一，`non-sealed` 表示这个分支重新开放继承。
- 和枚举比：枚举的常量是单例，sealed 的子类可以带不同字段、可以有多个实例，表达力更强。
- 典型用法：UI State（Loading/Success/Error）、结果类型、AST 节点。Kotlin 里早就有 `sealed class`，Java 17 才跟上。

### Q: Java 21 的 switch 模式匹配怎么写？
**答**：
- 支持类型模式、记录模式（解构）、`null` 分支和 `when` 守卫条件，匹配按书写顺序进行，编译器会检查支配关系。

```java
sealed interface Shape permits Circle, Square {}
record Circle(double r) implements Shape {}
record Square(double side) implements Shape {}

static double area(Shape s) {
    return switch (s) {
        case Circle c when c.r() > 0 -> Math.PI * c.r() * c.r();
        case Circle c -> 0;
        case Square q -> q.side() * q.side();
    }; // sealed 类型不用写 default
}
```

- 记录模式还能直接解构：`case Circle(double r) -> ...`，省掉访问器调用。
- 普通类做 switch 时仍然需要 `default`，因为编译器证明不了穷尽。
- 这类语法在 Android 上由 D8 脱糖，用之前确认 AGP 版本。

### Q: 虚拟线程是什么？Android 上能用吗？
**答**：
- 虚拟线程是 JDK 21 正式的特性：由 JVM 调度到少量"载体线程"上，遇到阻塞 IO 会自动卸载（unmount），所以能开几十万个而不炸。
- 它解决的是**吞吐**不是**延迟**：单次请求不会变快，但同样的线程数能扛更多并发。
- 两个坑：CPU 密集任务没收益；在 `synchronized` 块里长时间阻塞会 pin 住载体线程，退化成平台线程。
- Android 上**没有**虚拟线程：ART 不是 HotSpot，`Thread.ofVirtual()` 拿不到。等价物就是 Kotlin 协程。
- 面试对比：虚拟线程由运行时调度、对代码透明；协程是编译期 CPS + 库调度，可取消、有结构化并发、能切 Dispatcher。

### Q: Kotlin 的空安全是怎么实现的？平台类型是什么？
**答**：
- 类型系统层面区分 `T` 和 `T?`，编译器在**调用边界插入空检查**（`Intrinsics.checkNotNullParameter`），不是运行时靠类型标记。
- 平台类型 `T!` 来自 Java：编译器不做校验，你把它赋给非空类型时它才插断言，所以 NPE 可能在你没写 `!!` 的地方出现。
- 常见漏网之鱼：Java 回调传 null、反射、JSON 反序列化、`lateinit` 未初始化就访问（抛 `UninitializedPropertyAccessException`）。
- 工程建议：对外 API 一律显式可空；Java 互操作的方法加 `@Nullable/@NonNull`，Kotlin 会把它们当真实类型处理。

### Q: 扩展函数是成员函数吗？它有哪些坑？
**答**：
- 不是。它编译成一个静态方法，接收者变成第一个参数，所以**不能被子类 override**，也不参与多态。
- 解析是静态的：用父类引用调扩展，执行的是父类那个扩展，跟实际对象类型无关。
- 同名成员函数优先于扩展函数；扩展函数也访问不到 private 成员。
- 从 Java 调用不方便（要写 `FooKt.xxx(foo)`），跨模块暴露的扩展要考虑这一点。
- 好处是给不可改的类（比如 `String`、`View`）加能力，不用继承、不用工具类。

### Q: inline 有什么用？什么时候不该用？
**答**：
- 把函数体内联到调用点，消掉 lambda 对象和高阶函数的调用开销；同时支持**非局部 return**和 `reified` 具体化泛型。
- `reified` 只能在 inline 函数里用，典型：`inline fun <reified T : Activity> Context.startActivity()`。
- `noinline` 表示这个 lambda 参数不内联（要当对象传出去）；`crossinline` 禁止非局部返回（给嵌套 lambda 用）。
- 不该用：函数体很大、调用点很多（代码膨胀）、需要被 Java 调用、需要拿函数引用。
- 一句话：inline 是用**体积换调用开销**，只对"小而热的高阶函数"划算。

### Q: Kotlin 的委托（by）有哪些典型用法？
**答**：
- 类委托：`class LoggingList<T>(private val inner: MutableList<T>) : MutableList<T> by inner`，只覆写关心的几个方法。
- 属性委托：`by lazy`、`by observable`、`by vetoable`、`by map`（适合解析配置/JSON）。
- 自定义委托实现 `ReadWriteProperty`（或 `operator getValue/setValue`），封装 SharedPreferences、MMKV、ViewBinding 很常见。
- `lazy` 默认 `SYNCHRONIZED`，可以显式指定 `PUBLICATION`（多线程重复计算但只用一个）或 `NONE`。
- 注意 lazy 只在首次访问时初始化，异常会导致下次重新初始化。

### Q: Kotlin 的 lambda 和 Java 的 lambda 有什么区别？SAM 转换是什么？
**答**：
- Kotlin 的函数类型是 `FunctionN` 对象（inline 时会消除）；Java 的 lambda 是 `@FunctionalInterface` + `invokedynamic`。
- SAM 转换：Kotlin 调 **Java 方法**时可以传 lambda，编译器自动包成接口实现；反过来 Java 调 Kotlin 的高阶函数不行，得传 `Function1` 实例。
- Kotlin 自己定义的接口默认不做 SAM 转换，想支持就声明 `fun interface`。
- 坑：Kotlin 函数类型参数默认非空；`Unit` 返回值和 `void` 的桥接；Java 接口方法多一个参数就转换失败。

### Q: Kotlin 与 Java 互操作有哪些坑？
**答**：
- Kotlin 类默认 `final`、`public`，Java 想继承要显式 `open`；大项目用 allopen/noarg 插件。
- 默认参数 Java 看不到，要加 `@JvmOverloads` 生成重载；否则 Java 必须把所有参数传满。
- `companion object` 的成员 Java 要写 `Foo.Companion.bar()`，加 `@JvmStatic` 才是真静态方法。
- 属性在 Java 侧是 getter/setter；`isXxx` 类型的 Boolean 生成 `isXxx()`，命名容易踩坑。
- Kotlin 不强制检查异常，Java 侧 catch 时可能"编译器说不会抛"，需要 `@Throws` 标注。
- 平台类型、集合的只读视图（`List` 在 Java 侧仍可变）都别当契约用。

### Q: data class 有哪些坑？
**答**：
- 只有**主构造参数**参与 `equals/hashCode/toString/copy/componentN`，写在类体里的属性不参与，很容易误判相等。
- 用它当 HashMap 的 key 时，别把 var 属性算进去——放进去之后改字段，hashCode 变了就再也查不到。
- `copy()` 是浅拷贝，里面的 List/对象还是同一个引用；要深拷贝得自己写。
- 它不能被继承（final），也不能是 `inner`/`abstract`/`open`；主构造至少要有一个参数。
- Room Entity、Parcelable、JSON 模型都用 data class 时，字段增删要考虑兼容（尤其配合混淆和 `@Keep`）。

### Q: companion object 和 @JvmStatic 有什么区别？
**答**：
- `companion object` 是类内部的一个单例对象，编译产物是 `Outer$Companion` 加上外部类里的一个静态字段，调用写 `Outer.foo()`。
- 加 `@JvmStatic` 后，编译器在**外部类上再生成一个真正的静态方法**，Java 才能 `Outer.foo()` 直接调；不加就得 `Outer.Companion.foo()`。
- `const val` 才是编译期内联常量；companion 里的普通 `val` 是运行时常量，还会有类初始化开销。
- 别在 companion 里长期持有 Activity/Context 引用——它是静态的，等于泄漏。
- 现在的倾向：工具方法用顶层函数或 `object`，companion 只放工厂方法和常量。

## 二、语言与运行时

### Q: ART 和 Dalvik 有什么区别？
**答**：
- Dalvik 是 Android 4.4 之前的虚拟机：纯 JIT + 解释执行，32 位，每个进程一个 VM 实例，方法调用靠寄存器式指令集，GC 停顿明显。
- ART 在 4.4 引入、5.0 成为默认：安装时用 dex2oat 把 dex **AOT 编译**成本地机器码，启动和运行都更快，支持 64 位和更紧凑的堆。
- 产物变化：`.dex` → `.oat`（机器码）+ `.vdex`（dex 与校验信息）+ `.art`（堆镜像/GC 根）。
- ART 的 GC 是并发、可移动、可压缩的，比 Dalvik 的 stop-the-world 友好很多。
- 代价：纯 AOT 会让安装慢、占空间，所以 7.0 之后又混合回了 JIT。

### Q: JIT、AOT 和混合编译是怎么演进的？
**答**：
- 5.0~6.0 纯 AOT：安装时全量编译，安装慢、ROM 占用大，但运行快。
- 7.0 起混合：先解释执行，热点方法由 JIT 编译，同时把热点记录进 **profile 文件**；设备空闲/充电时 dex2oat 按 profile 做 AOT。
- 10 起支持 **Cloud Profiles**（Play 下发别人跑出来的热点），12 起支持 **Baseline Profile**（随 APK/AAB 打包，安装时就能预编译热点）。
- 结论：启动路径上的类如果不在 profile 里，就要吃 JIT 的 warmup 成本，这就是做 Baseline Profile 的意义。

### Q: ART 的 GC 是怎样的？分代和并发标记指什么？
**答**：
- ART 用的是**并发复制（Concurrent Copying）**回收器，10 起引入分代：新生代频繁小回收，老年代少而慢。
- 并发标记：标记阶段和应用线程并发跑，靠读屏障/写屏障维持三色不变式，只有很短的 pause 用于最终标记和引用处理。
- 堆按 region 划分，另有 **LOS（Large Object Space）** 专门放大对象（比如大 Bitmap），避免复制成本。
- 13 起使用 userfaultfd 处理并发阶段的对象访问，进一步压短停顿。
- 优化启示：少产生临时对象、别在 `onDraw` 里 new、大图走采样或硬解复用。

### Q: 什么是 Java 内存模型？happens-before 有哪些规则？
**答**：
- JMM 是一套规范，定义多线程下**可见性**和**有序性**：抽象出主内存和每个线程的工作内存，允许编译器/CPU 重排但不能破坏语义。
- `volatile`：保证可见性 + 禁止指令重排，**不保证原子性**；`synchronized`：原子性 + 可见性 + 有序性。
- happens-before 规则：程序顺序、监视器解锁先于加锁、volatile 写先于读、`Thread.start()` 先于子线程动作、`join()` 返回前子线程的动作可见、以及传递性。
- 经典坑：DCL 单例不加 volatile 可能拿到"构造未完成"的对象；32 位机上 long/double 的读写不保证原子。
- Android 的 ART 实现的是同一套 JMM，Kotlin 的 `@Volatile` 就是 `java volatile`。

### Q: 类加载的过程是怎样的？
**答**：
- 五个阶段：加载 → 验证 → 准备 → 解析 → 初始化，之后才能使用和卸载。
- 加载：按全限定名拿到二进制流，生成 `Class` 对象放进方法区。
- 准备：给静态变量分配内存并赋**零值**；初始化：执行 `<clinit>`，真正跑静态赋值和 static 块。
- 触发初始化的时机：new、访问静态字段/方法、反射、初始化子类时先初始化父类。
- 双亲委派：先让父加载器加载，父加载不到才自己加载——保证核心类不被篡改、避免重复加载。

### Q: 双亲委派被"破坏"有哪些场景？
**答**：
- SPI 机制：JDBC 这类接口在核心库、实现在三方 jar，只能用**线程上下文类加载器**反向加载。
- 容器/OSGi：Tomcat 每个 webapp 独立 ClassLoader，要隔离同名类；OSGi 是网状委派。
- Android 的热修复/插件化：把补丁 dex 插到 `dexElements` 数组**前面**，让类先被补丁加载，本质是"抢先"而不是委派。
- 面试点：双亲委派不是语法强制，是 `loadClass` 的默认实现；重写 `loadClass` 就能改规则。

### Q: Android 的 ClassLoader 体系是怎样的？
**答**：
- 三层：`BootClassLoader`（加载 framework，父加载器为 null）→ `PathClassLoader`（加载已安装 APK 的 dex）→ `DexClassLoader`（加载任意路径的 dex/jar/zip，插件化用）。
- 两者都继承 `BaseDexClassLoader`，核心在 `DexPathList` 和 `Element[] dexElements`。
- 8.0 之后 `DexClassLoader` 的 `optimizedDirectory` 参数已废弃，oat 统一放系统目录。
- Android 没有 Java 的 Ext/App ClassLoader；`PathClassLoader` 的父加载器是 BootClassLoader。
- 面试延伸：热修复就是反射拿到 `dexElements`，把补丁 Element 插到最前面。

### Q: 一个 APK 是怎么安装到手机上的？
**答**：
- 触发方：应用商店/`PackageInstaller`/adb；APK 先被拷贝到 `/data/app/~~随机串/包名-随机串/base.apk`。
- `PackageManagerService` 解析 Manifest，做签名校验、ABI 校验、权限与 `sharedUserId` 检查。
- 分配 uid/gid，把包信息写进 `/data/system/packages.xml`；`installd` 创建应用数据目录。
- 对 dex 做 dexopt（dex2oat）生成 oat/vdex；Android 10+ 还有 fs-verity 完整性保护。
- 最后发 `PACKAGE_ADDED` 广播，Launcher 刷新图标。系统应用预置在 `/system/priv-app`，不需要走安装流程。

### Q: APK 签名 v1/v2/v3/v4 有什么区别？
**答**：
- v1：JAR 签名，逐文件摘要放 `META-INF/`，只保护解压后的内容，改 zip 中央目录就能绕过（Janus 漏洞）。
- v2：对整个 APK 文件签名，签名块放在 zip 尾部的 APK Signing Block，**校验全文件**，防篡改。
- v3：增加密钥轮换（key rotation），带 proof-of-rotation，换签名密钥后老版本还能升级。
- v4：基于 fs-verity 的增量安装校验（Android 11+），配合 `adb install --incremental` 边下边装。
- 现状：Android 11 起 targetSdk 30+ 必须 v2 以上；发布产物一般 v2 + v3 同时签，`apksigner` 一条命令搞定。

### Q: 什么是 dex？64K 问题和 multidex 怎么解决？
**答**：
- dex 是 Dalvik Executable，Android 的字节码格式；一个 dex 的**方法引用上限是 65536**（method_ids 索引是 16 位）。
- 超限编译就报 "Too many field references / method references"；字段和类型也有同样数量级限制。
- minSdk ≥ 21 时 AGP 自动开 multidex，系统原生支持多 dex；5.0 以下要 `MultiDexApplication`，启动时解压 dex，很慢。
- 缓解手段：R8 裁剪无用代码、去掉重复依赖（尤其老版 `support` 和 `androidx` 混用）、拆分 dex、少用巨型 SDK。
- 现在基本只在老项目或大厂巨型 App 里还会遇到。

### Q: 非 SDK 接口（hidden API）限制是怎么回事？
**答**：
- Android 9 开始给非公开 API 分级：light greylist / dark greylist / blacklist，后续版本收窄成"可访问/不可访问"。
- 效果：反射或 JNI 访问被限制的接口会打日志 `Accessing hidden method ...`，严重时直接抛异常。
- 影响面：热修复、插件化、Hook 框架、以及各种"黑科技"SDK，都大量依赖 hidden API，需要逐个适配。
- 官方给的替代：用公开 API、用 `Shizuku`/无障碍做系统能力、或走厂商合作。
- 面试态度：能说清"限制存在 + 绕过有风险 + 有官方替代"就够，别吹怎么绕。

## 三、四大组件与 Framework

### Q: 完整说一下 Activity 的生命周期？
**答**：
- 创建到可见：`onCreate`（setContentView、初始化）→ `onStart`（可见但不可交互）→ `onResume`（前台可交互）。
- 失去焦点到销毁：`onPause`（可见但不可交互，**不能做耗时操作**，否则挡住下一个页面）→ `onStop`（不可见，可做较重回收）→ `onDestroy`。
- 回到前台：`onRestart` → `onStart` → `onResume`。
- 记忆锚点：`onStart/onStop` 管**可见**，`onResume/onPause` 管**前台**；`onPause` 必须快速返回。
- A 跳 B（都不透明）：`A.onPause → B.onCreate/onStart/onResume → A.onStop`；返回时 `B.onPause → A.onRestart/onStart/onResume → B.onStop/onDestroy`。B 透明主题时 A 不会走 `onStop`。

### Q: onSaveInstanceState 和 onRestoreInstanceState 什么时候调用？
**答**：
- 触发时机：配置变更（旋转、深色模式切换）、系统因内存不足杀掉后台 Activity、进程被杀后重建。
- `onSaveInstanceState` 在 `onStop` 之前调用，和 `onPause` **没有固定先后**；数据写进 Bundle，View 层级会自动保存有 id 的控件状态。
- `onRestoreInstanceState` 在 `onStart` 之后调用，Bundle 同时也传给 `onCreate`，所以两处都能判断是否重建（`savedInstanceState != null`）。
- 只能存轻量、可序列化的数据；大数据用 ViewModel + SavedStateHandle 或本地持久化。
- 用户主动按返回键退出不会走这套流程。

### Q: Activity 的四种启动模式和常用 Flag？
**答**：
- `standard`：默认，每次都新建实例，进启动它的任务栈。
- `singleTop`：栈顶已有该实例就复用，回调 `onNewIntent`（注意再 `setIntent`），适合通知、搜索页。
- `singleTask`：全栈唯一，已存在就**清掉它上面的所有 Activity** 并回调 `onNewIntent`，适合首页、扫一扫。
- `singleInstance`：独占一个任务栈，其他 Activity 进不来，适合来电界面、地图这类独立页。
- 常用 Flag：`FLAG_ACTIVITY_NEW_TASK`、`CLEAR_TOP`、`SINGLE_TOP`、`CLEAR_TASK`、`NO_HISTORY`；`taskAffinity` 决定任务栈归属。

### Q: Activity 的启动流程，说个大概就行了？
**答**：
- 调用方 `startActivity` 经 `Instrumentation` → `ActivityTaskManager`（老版本是 `ActivityManagerService`）→ Binder 到 system_server。
- `ActivityTaskManagerService` 让 `ActivityTaskSupervisor` 解析 Intent、找到目标 Activity、做栈管理（`Task`/`ActivityRecord`），检查进程是否存在。
- 进程不存在就先 `startProcess`（Zygote fork），再走 `ApplicationThread` 的 Binder 回调到应用进程。
- 应用侧 `ActivityThread` 收到 `LAUNCH_ACTIVITY`，用 `ClassLoader` 加载类、反射创建实例、`attach` 绑定、依次 `onCreate/onStart/onResume`。
- 关键角色：`AMS/ATMS` 管调度、`ActivityThread` 是应用主线程的"操作系统入口"、`ClientTransaction` 把生命周期封装成事务。

### Q: Service 有哪些类型？生命周期怎么走？
**答**：
- 按启动方式分 `startService` 和 `bindService`；按用途分后台服务、前台服务、`JobIntentService`（已不推荐）。
- `startService`：`onCreate → onStartCommand → (运行) → onDestroy`，多次启动只回调 `onStartCommand`；返回值决定被杀后是否重启（`START_STICKY`/`START_NOT_STICKY`/`START_REDELIVER_INTENT`）。
- `bindService`：`onCreate → onBind → onUnbind → onDestroy`，最后一个客户端解绑就销毁。
- 混用：先 `startService` 再 `bind`，要 `stopService` 和 `unbind` 都调用才会销毁。
- 现状：后台 Service 在 8.0 之后基本活不下来，长任务用 `WorkManager` 或前台服务。

### Q: Android 14 之后前台服务的类型有什么新要求？
**答**：
- 必须在 Manifest 里声明 `android:foregroundServiceType`，运行时 `startForeground()` 传入的类型必须和声明一致。
- 类型有 `camera`、`microphone`、`location`、`mediaPlayback`、`dataSync`、`connectedDevice`、`health`、`shortService` 等，每个都有对应的权限和使用场景限制。
- 不声明或类型不符会抛 `MissingForegroundServiceTypeException` / `SecurityException`；Android 14 起还要求先申请对应运行时权限。
- Android 15 进一步限制：`BOOT_COMPLETED` 之后不能启动某些类型的前台服务（如 dataSync、camera）。
- 建议：能不用就不用；必须用就选对类型、写清通知文案，审核和上架都会被查。

### Q: 广播的两种注册方式有什么区别？导出要注意什么？
**答**：
- 静态注册（Manifest）：常驻，**7.0 之后部分隐式广播收不到**，8.0 之后大部分隐式广播静态注册失效；应用未启动也能收到（受限于豁免列表）。
- 动态注册（代码）：跟随组件生命周期，必须成对 `registerReceiver/unregisterReceiver`，否则泄漏或崩溃。
- 安全问题：`android:exported` 必须显式声明（Android 12 起带 intent-filter 的组件不写就编译失败）；敏感广播加 `android:permission`，发送时用 `sendBroadcast(intent, receiverPermission)`。
- 本地通信优先用 `LocalBroadcastManager`（已废弃）或 `Flow`/`LiveData`/`EventBus`，不必走系统广播。
- 8.0 起大部分隐式广播不能静态注册，只能动态注册，这是省电策略的一部分。

### Q: 隐式广播的限制具体是什么？
**答**：
- Android 8.0（API 26）起，**大多数隐式广播**不允许在 Manifest 里静态注册，只能动态注册。
- 豁免的包括：`BOOT_COMPLETED`、`LOCALE_CHANGED`、`ACTION_MY_PACKAGE_REPLACED`、`ACTION_PACKAGE_FULLY_REMOVED` 等和系统状态强相关的。
- 影响：以前靠静态广播做保活、监听网络/亮屏的方案全部失效，改用 `WorkManager`、`ConnectivityManager.NetworkCallback`、`ProcessLifecycleOwner`。
- 显式广播（指定包名/组件）不受限制，跨应用通信优先用显式 Intent。
- Android 14 起，动态注册的广播也必须声明 `RECEIVER_EXPORTED` 或 `RECEIVER_NOT_EXPORTED`。

### Q: ContentProvider 的原理和启动时机？
**答**：
- 它是**跨进程数据访问**的标准入口：`ContentResolver` 通过 Binder 找到 `ContentProvider.Transport`，再调用 `query/insert/update/delete`。
- 启动时机很早：应用进程创建时 `ActivityThread.handleBindApplication` 里会 `installContentProviders`，**在 Application.onCreate 之前**，所以别在 provider 里做重活。
- 关键类：`ContentProvider`、`ContentResolver`、`ContentObserver`（配合 `notifyChange` 做数据变更通知）、`Cursor`。
- 权限：`readPermission/writePermission`、`grantUriPermissions` 临时授权、`<path-permission>` 细粒度控制。
- 现状：应用内数据用 Room/DataStore 就够；跨应用共享用 `FileProvider` 或 `MediaStore`，自建 Provider 越来越少。

### Q: Binder 为什么说"一次拷贝"？mmap 起什么作用？
**答**：
- 传统 IPC（socket、管道）要把数据从发送方用户态拷到内核，再从内核拷到接收方用户态，共两次。
- Binder 在接收进程创建时，把内核里的一块缓冲区 **mmap** 到接收进程的用户空间；发送方只需 `copy_from_user` 一次把数据写进这块内核缓冲区，接收方直接读自己映射的内存。
- 所以总拷贝次数从 2 降到 1；同时 Binder 天然带**进程身份（uid/pid）**，安全性比 socket 好。
- 附加优势：支持对象引用跨进程传递（`Binder` 实体/引用）、支持同步调用（等待回复）。
- 面试补充：`/dev/binder` 每个进程映射缓冲区约 1MB，是**每进程共享**的，不是每次传输新开。

### Q: Binder 传输有大小限制吗？线程池是怎样的？
**答**：
- 有。普通 Binder 事务的缓冲区是**每进程 1MB 减去两页**（约 1MB - 8KB），所有并发事务共享；超了抛 `TransactionTooLargeException`。
- 所以 `Intent` 传大数据（大 Bitmap、长列表）会崩，应该写文件/用 `FileProvider`/用 `ashmem` 共享内存。
- Binder 线程池：每个进程默认最多 **16 个** Binder 线程（`ProcessState` 里 `maxThreads = 15 + 1`），由 `IPCThreadState` 驱动。
- 服务端回调客户端时是**同步**的，如果双方互相调用需要注意死锁；oneway 调用不占等待。
- 面试延伸：`AIDL` 生成 `Stub/Proxy`，`asInterface` 判断是否同进程，同进程直接返回本地对象不走 Binder。

### Q: Handler/Looper/MessageQueue 的原理？
**答**：
- `Looper.prepare()` 创建 `MessageQueue` 并存进 `ThreadLocal`；`Looper.loop()` 死循环 `queue.next()` 取消息，再 `msg.target.dispatchMessage()` 分发。
- `MessageQueue` 内部是**单链表按时间排序**，靠 native 的 `epoll` + `eventfd` 实现无消息时阻塞、有消息时唤醒，不占 CPU。
- `Handler` 发送消息时把 `this` 赋给 `msg.target`；`Message.obtain()` 从**消息池**复用，避免频繁创建。
- 主线程的 Looper 在 `ActivityThread.main()` 里 prepare，所以主线程默认有 Looper；子线程用 Handler 必须先 `prepare`。
- 内存泄漏：非静态 Handler 持有 Activity，延时消息未消费就泄漏；用静态内部类 + WeakReference，或在 `onDestroy` 里 `removeCallbacksAndMessages(null)`。

### Q: 什么是同步屏障？IdleHandler 有什么用？
**答**：
- 同步屏障是给 `MessageQueue` 插一个 `target == null` 的屏障消息，之后**异步消息**（`setAsynchronous(true)`）可以插队优先执行，同步消息被挡住。
- 典型用途：`ViewRootImpl.scheduleTraversals()` 发屏障 + 异步消息，保证 VSYNC 到来时绘制任务优先于普通消息，减少掉帧。
- 用完要 `removeSyncBarrier(token)`，否则同步消息永远卡住（ANR 的经典原因之一）。
- `IdleHandler` 在消息队列**空闲时**回调，返回 false 只执行一次，true 可以反复执行。
- 典型用途：延迟初始化、启动阶段把非关键任务挪到 idle、`LeakCanary` 也用它做延迟检测。注意 idle 回调里别再发耗时消息。

### Q: View 的绘制流程是怎样的？
**答**：
- 入口是 `ViewRootImpl.performTraversals()`，由 VSYNC 信号触发（`Choreographer`），依次执行 `measure → layout → draw`。
- measure：父容器把 `MeasureSpec`（mode + size）传给子 View，`onMeasure` 里算出宽高；`MeasureSpec` 的三种模式是 EXACTLY、AT_MOST、UNSPECIFIED。
- layout：`onLayout` 确定子 View 的四个顶点；draw：`onDraw` → `dispatchDraw`（画子 View）→ 前景/滚动条。
- 硬件加速下 draw 只是把绘制命令记到 `RenderNode`/DisplayList，真正的光栅化在 **RenderThread** 做，不占主线程。
- 触发方式区别：`requestLayout` 会重新 measure/layout（异步走 traversal），`invalidate` 只重绘且必须在主线程，`postInvalidate` 可在子线程。

### Q: View 的事件分发机制？
**答**：
- 三个核心方法：`dispatchTouchEvent`（分发）、`onInterceptTouchEvent`（ViewGroup 才有，拦截）、`onTouchEvent`（消费）。
- 流程：从 DecorView 往下 `dispatchTouchEvent`，ViewGroup 先问自己 `onInterceptTouchEvent`，不拦截就交给子 View；子 View 都不消费，最后回到自己的 `onTouchEvent`。
- 优先级：`OnTouchListener.onTouch` 先于 `onTouchEvent`；`onClick` 在 `onTouchEvent` 的 UP 里触发。
- `ACTION_DOWN` 决定这条事件流的归属：某个 View 消费了 DOWN，后续 MOVE/UP 都给它；中途拦截会给子 View 发 `ACTION_CANCEL`。
- 冲突解决：外部拦截法（父容器 `onInterceptTouchEvent` 按条件拦）、内部拦截法（子 View `requestDisallowInterceptTouchEvent`）。

### Q: Window、WindowManager 和 WMS 是什么关系？
**答**：
- `Window` 是抽象概念（一个"窗口"），实现是 `PhoneWindow`，根 View 是 `DecorView`；`WindowManager` 是应用侧的管理接口，实现是 `WindowManagerImpl`。
- `setContentView` 实际是把布局 inflate 进 `DecorView` 的 `content` 容器。
- `addView` 调用链：`WindowManagerImpl → WindowManagerGlobal → ViewRootImpl.setView → Session → WindowManagerService`。
- WMS 负责窗口的层级（Z-order）、位置、大小、输入事件分发、动画和令牌（token）管理；应用进程通过 `Surface` 拿到画布。
- 常见面试点：`Window` 不占内存只有 View 占；`Dialog` 本质也是一个 Window；`Toast` 在 11 之后不能用自定义 View（远程 View 限制）。

### Q: AMS 和 WMS 的面试要点有哪些？
**答**：
- AMS（现在拆分出 `ActivityTaskManagerService`）管**组件调度**：Activity 栈、Service 启动、广播分发、进程优先级与 `oom_adj`、进程回收。
- WMS 管**窗口与显示**：窗口添加/删除、层级、焦点窗口、输入事件派发、转屏、动画（`SurfaceAnimator`）。
- 两者都在 system_server 进程，通过 Binder 和应用进程通信，应用侧对应 `ApplicationThread` 和 `IWindowSession`。
- 进程管理：AMS 用 `ProcessList` 维护 `oom_adj`（前台 0、可见 100、服务 200、后台 700+），内存紧张时按 adj 杀。
- 面试别背源码细节，讲清"谁管什么 + 怎么通信 + oom_adj 分级"就够，再补一个你排查过的具体问题（比如启动白屏、ANR）。

## 四、现代 UI

### Q: Compose 和 View 体系的本质区别是什么？
**答**：
- View 是**命令式**：拿到控件引用，主动调 `setText`、改属性，状态散落在 View 树里。
- Compose 是**声明式**：描述"给定状态 UI 长什么样"，状态变了框架重新执行 `@Composable` 函数，自己算差异。
- 渲染模型不同：View 走 measure/layout/draw 三棵树；Compose 只有组合（Composition）→ 布局（Layout）→ 绘制（Draw）三个阶段，且布局是**单次测量**（不允许像 View 那样测两次）。
- Compose 的 UI 树是"slot table"记录的组合树，重组只重跑受影响的函数，不重建整棵树。
- 成本对比：Compose 首次组合有开销、包体积变大；但少写 findViewById/XML、状态驱动代码更短、动画和列表更省心。

### Q: 什么是重组（recomposition）？什么时候会触发？
**答**：
- 重组 = 用新状态重新执行受影响的 `@Composable` 函数，更新组合树。
- 触发条件：读取的 `State` 值发生变化；读取发生在**组合阶段**才会被记录依赖。
- 只有**读取了该状态的 Composable** 会被重启（restartable），所以状态的读取位置决定了重组范围——这就是"把状态读晚一点"的优化来源。
- 重组是并发的、可能多次执行、顺序不保证，所以 Composable 必须是**幂等且无副作用**的。
- 重组不是"重绘"：布局和绘制阶段只在尺寸/位置变化时才跑。

### Q: remember、rememberSaveable 和状态提升怎么用？
**答**：
- `remember { }` 在重组之间保留值，但**配置变更/进程死亡会丢**；`rememberSaveable` 存进 `SavedStateRegistry`，能扛旋转和进程重建。
- `remember(key)` 里 key 变了就重新计算，用来做"参数变化时的派生状态"。
- 状态提升（state hoisting）：把状态提到共同父级，子 Composable 只收 value + onValueChange 回调，变成无状态组件——可复用、可测试、单一数据源。
- `derivedStateOf` 用于"由其他状态派生、且希望减少重组"的场景（比如列表是否滚到顶部），比每次重组都算一遍划算。
- 反模式：在 Composable 里创建 ViewModel、在组合中直接改状态（会触发无限重组）。

### Q: Compose 性能优化有哪些手段？
**答**：
- 让 Composable **可跳过（skippable）**：参数用稳定类型（`@Immutable`/`@Stable`），避免传不稳定类型（如 `List`、未标注的普通类）导致每次都重组。新版本 Compose 编译器默认开启强跳过模式，弱化了这个问题，但仍建议标注。
- 状态**晚读**：不要在顶层读 `state.value` 再往下传，把读取下移到真正用到它的叶子节点。
- 列表用 `LazyColumn` 并给 `items(key = ...)`，避免用下标做 key 导致状态错位。
- 用 `derivedStateOf` 减少高频变化的派生计算；动画/滚动这类高频值用 lambda 形式传参。
- 别在组合里做重活（IO、排序、`SimpleDateFormat` 创建），挪到 `LaunchedEffect`/`remember`；`Modifier` 复用，避免在重组里 new。

### Q: LaunchedEffect、DisposableEffect、SideEffect 有什么区别？
**答**：
- `LaunchedEffect(key)`：进入组合时启动一个协程，key 变化时取消重启，离开组合时自动取消——最常用，做网络请求、Toast、埋点。
- `DisposableEffect(key)`：需要**清理**的副作用，`onDispose` 里注销监听、解绑、关资源，等价于 `onStart/onStop` 的配对。
- `SideEffect`：每次成功重组后都执行，不涉及协程，适合把 Compose 状态同步给非 Compose 代码（比如设置系统栏颜色）。
- `rememberCoroutineScope`：拿到与当前组合生命周期绑定的 scope，用于点击事件里手动 `launch`。
- 记住原则：Composable 里不能直接调 suspend 函数，也不能在组合中直接改外部状态。

### Q: ViewBinding、DataBinding 和 findViewById 怎么选？
**答**：
- `findViewById`：运行时查找 + 强转，类型不安全，View 不存在就 NPE，新项目不要用了。
- `ViewBinding`：编译期生成绑定类，**空安全、类型安全、无反射**，Fragment/Dialog 里要注意在 `onDestroyView` 置 null 避免泄漏。
- `DataBinding`：在 ViewBinding 基础上加表达式和双向绑定，代价是编译变慢、错误信息难读、布局里塞逻辑难维护。
- 现状：官方推荐 ViewBinding；DataBinding 在 Compose 项目里基本不用了；Kotlin 也可以直接用 `by viewBinding()` 委托减少模板代码。
- 顺带一句：ButterKnife 早已停止维护（AndroidX 之后注解处理收益很低），不要再提。

### Q: RecyclerView 的四级缓存是什么？
**答**：
- 一级 `mAttachedScrap` / `mChangedScrap`：屏幕内、未与 RecyclerView 分离的 ViewHolder，直接复用，不走 bind。
- 二级 `mCachedViews`：**默认容量 2**（按 position 命中），刚滑出屏幕的 ViewHolder 原样缓存，回来时不需要重新 bind。
- 三级 `ViewCacheExtension`：留给开发者自定义，一般用不到。
- 四级 `RecycledViewPool`：按 `viewType` 分池，每种默认 5 个，命中后需要重新 `onBindViewHolder`。
- 回收顺序是从一级到四级逐层找；优化点：按 type 调大 pool size、避免 viewType 过多、复杂 item 用 `setHasFixedSize`。

### Q: RecyclerView 的预取（prefetch）和局部刷新是怎么做的？
**答**：
- 预取由 `GapWorker` 负责：滑动时利用下一帧之前的空闲时间，提前创建/绑定即将进入屏幕的 item（默认预取 2 个）。
- 预取任务通过 `Choreographer` 的 `postCallback` 挂在帧回调上，避免和主线程的绘制抢时间。
- 局部刷新：`notifyItemChanged/Inserted/Removed/Moved`，配合 `DiffUtil`（或 `ListAdapter` + `AsyncListDiffer`）算最小更新集。
- `notifyDataSetChanged` 会让所有缓存失效、触发全量重绑，是卡顿常见原因。
- 局部刷新时如果用 `notifyItemChanged(position)` 引起图片闪烁，可以用 payload 只更新变化的部分（`onBindViewHolder(holder, position, payloads)`）。
- Compose 里对应的是 `LazyColumn` + 稳定 key，框架自己处理复用与动画。

### Q: RecyclerView 卡顿一般怎么优化？
**答**：
- 减少 `onBindViewHolder` 里的工作：不 new 对象、不做字符串拼接/格式化、不加载大图、不嵌套 `wrap_content` 的横向列表。
- 布局层级：item 用 `ConstraintLayout` 或 `LinearLayout` 扁平化，避免深层嵌套和 `RelativeLayout` 双重测量。
- 图片：按 item 尺寸采样、复用 Bitmap、滑动时暂停加载（`Glide.with(...).pauseRequests()`）。
- 减少 `requestLayout`：固定高度用 `setHasFixedSize(true)`，避免在 bind 里改 LayoutParams。
- 用 Macrobenchmark + JankStats/Perfetto 量化，别凭感觉；开启 `setItemViewCacheSize` 和共享 `RecycledViewPool`（多列表同 type 时）。

### Q: Compose 和 View 怎么互操作？
**答**：
- View 里嵌 Compose：用 `ComposeView`（`setContent {}`），注意它有独立生命周期，在 `onDestroyView` 里 `dispose`。
- Compose 里嵌 View：用 `AndroidView(factory, update)`，`factory` 只执行一次，`update` 每次重组都会调；`AndroidViewBinding` 可以直接绑定 XML。
- 传统 View 的 `ViewBinding` 在 Compose 页面里仍可用，但要注意别在重组中反复 inflate。
- 混合项目建议按页面灰度迁移：新页面用 Compose，老页面保持 View，公共组件抽成独立模块。
- 注意主题：`ComposeView` 要用 `MdcTheme`/`MaterialTheme` 包一层，否则样式对不上。

## 五、协程与异步

### Q: suspend 函数的实现原理是什么？
**答**：
- 编译器把 suspend 函数改造成**状态机**：每个挂起点是一个 `case`，用 `label` 记录执行到哪，局部变量存进 `Continuation` 对象。
- 返回值变成 `Any?`：要么是直接结果，要么是 `COROUTINE_SUSPENDED` 表示真的挂起了。
- 本质是 **CPS 变换**：函数多一个 `Continuation` 参数，挂起时把"后续代码"作为回调传出去，恢复时调用 `resumeWith`。
- 所以挂起**不阻塞线程**，线程可以去跑别的协程；恢复时由 `Dispatcher` 决定回到哪个线程。
- 面试常问：suspend 函数不指定 Dispatcher 就在调用者线程执行；挂起函数只能在协程或另一个 suspend 函数里调用。

### Q: 什么是结构化并发？
**答**：
- 协程有父子关系：父协程要等所有子协程结束才结束，父取消会级联取消所有子协程，子协程异常会向上传播并取消父。
- 好处：不会"泄漏"后台任务，作用域结束资源一定被清理，异常不会被静默吞掉。
- 用 `coroutineScope { }` 创建子作用域（异常向上抛），用 `supervisorScope { }` 让子协程之间互不影响。
- Android 上 `viewModelScope`/`lifecycleScope` 就是结构化并发的落地：ViewModel 清空、页面销毁时自动取消。
- 反例：`GlobalScope.launch` 没有父作用域，不会被自动取消，属于"结构化并发之外的野协程"，禁止使用。

### Q: Job、CoroutineScope、SupervisorJob 怎么配合？
**答**：
- `CoroutineScope` = `CoroutineContext`，里面最关键的三个元素是 `Job`、`Dispatcher`、`CoroutineExceptionHandler`。
- `Job` 是协程句柄：`cancel()` 取消、`join()` 等待，有 `isActive/isCancelled/isCompleted` 状态。
- `SupervisorJob` 让**子协程失败不影响兄弟和父**，适合"多个独立任务并发"的场景，比如一个页面同时拉多个接口。
- `viewModelScope` 内部用的是 `SupervisorJob + Dispatchers.Main.immediate`，所以一个接口挂了不会连累其他。
- 注意 `cancel()` 是协作式的：协程必须在挂起点或检查 `isActive` 才会响应，死循环里的计算要手动 `ensureActive()`。

### Q: 协程的取消和异常处理要注意什么？
**答**：
- 取消是抛 `CancellationException` 实现的，`try/catch` 里**不能吞掉它**，否则协程无法取消；要重抛或者用 `ensureActive()`。
- `catch (e: Exception)` 会把 `CancellationException` 一起抓住，正确写法是先判断 `if (e is CancellationException) throw e`。
- 未捕获异常走 `CoroutineExceptionHandler`；`async` 的异常在 `await()` 时抛出，`launch` 的异常直接走 handler。
- `withTimeout` 抛 `TimeoutCancellationException`，也是取消的一种；`withTimeoutOrNull` 返回 null 不抛。
- 兜底建议：`runCatching` 只包业务代码，别把整个 `launch` 包起来；`NonCancellable` 用于 `finally` 里必须执行的清理。

### Q: Flow、StateFlow、SharedFlow 有什么区别？
**答**：
- `Flow` 是**冷流**：每个收集者都会触发一次完整的数据生产，天然支持背压（`suspend` 生产），适合"一次请求返回多条数据"。
- `StateFlow` 是**热流**，必须有初始值、只保留最新值、`==` 相同的值会去重，新订阅者立刻拿到当前值——适合 UI State。
- `SharedFlow` 也是热流，可以配置 `replay`、`extraBufferCapacity`、`onBufferOverflow`，适合事件总线；`replay=0` 时新订阅者收不到旧事件。
- 常见坑：用 `StateFlow` 发"一次性事件"（Toast、跳转）会因去重或粘性导致重复消费，应该用 `Channel(Channel.BUFFERED)` + `receiveAsFlow()`。
- `flowOn` 改变上游的 Dispatcher，`collect` 所在线程不变；`launchIn(scope)` 是 `scope.launch { collect() }` 的简写。

### Q: Flow 的背压和切换线程怎么处理？
**答**：
- `buffer(capacity)`：给上下游之间加缓冲，生产者和消费者并行，减少互相等待。
- `conflate()`：只保留最新值，消费慢时丢弃中间值，适合 UI 进度刷新。
- `collectLatest`：新值到来时**取消上一次的收集体**，适合搜索联想、点击防抖。
- `flowOn(Dispatchers.IO)` 只影响它**上游**的 operator；多个 `flowOn` 会形成多层调度。
- 默认 `Flow` 是顺序执行的，`flatMapMerge`/`flatMapLatest` 才能并发；`map` 里做耗时操作不会自动切线程。

### Q: Android 上协程的最佳实践是什么？
**答**：
- 生命周期绑定：`viewModelScope` 做业务、`lifecycleScope` 做 UI、`repeatOnLifecycle(STARTED)` 收集 Flow，避免后台空跑。
- 只在**需要结果**的地方用 `suspend`，事件流用 `Flow`；不要在 Repository 里 `launch` 后不管。
- 注入 Dispatcher（`@IoDispatcher`），单测里换成 `TestDispatcher`，别到处写死 `Dispatchers.IO`。
- `Dispatchers.Main.immediate` 用于"已经在主线程就直接执行"的场景，减少一次 post。
- 禁止 `GlobalScope`、禁止 `runBlocking`（除了 main 函数和测试），禁止在 `suspend` 里做阻塞 IO 而不切线程。

### Q: 线程池的核心参数和拒绝策略？
**答**：
- `ThreadPoolExecutor(corePoolSize, maximumPoolSize, keepAliveTime, workQueue, threadFactory, handler)`。
- 执行顺序：核心线程未满 → 建核心线程；核心满了 → 进队列；队列满了 → 建非核心线程到 max；还满 → 拒绝策略。
- 拒绝策略：`AbortPolicy`（默认抛异常）、`CallerRunsPolicy`（调用者自己跑，起到反压作用）、`DiscardPolicy`、`DiscardOldestPolicy`。
- 常见坑：用 `Executors.newFixedThreadPool` 时队列无界（`LinkedBlockingQueue`），`maximumPoolSize` 永远不生效，任务堆积会 OOM。
- Android 建议：按任务类型分池（IO 密集线程多、CPU 密集 = CPU 核数 + 1），并起有意义的线程名方便抓 trace。

### Q: HandlerThread 是什么？什么时候用？
**答**：
- 它是一个**带 Looper 的 Thread**：`start()` 后 `getLooper()` 拿到该线程的 Looper，可以往它上面 post 任务，串行执行。
- 适合"串行 + 不需要并发"的后台任务：数据库写入、日志落盘、图片解码、传感器数据处理。
- 用完要 `quitSafely()`，否则线程一直活着；`HandlerThread` 不能被重复 start。
- 和线程池比：它只有一个线程、任务串行，没有锁竞争，但吞吐低；和 `Handler` 比：它跑在子线程，主线程 Handler 跑在 UI 线程。
- 现状：新代码更推荐 `Dispatchers.IO.limitedParallelism(1)` 或 `CoroutineScope` + 单线程 Dispatcher，语义一样还更好取消。

### Q: IntentService 为什么废弃了？替代方案是什么？
**答**：
- 它内部是 `HandlerThread + Handler`，`onHandleIntent` 串行处理 Intent，处理完自动 stop——设计上适合"一次性后台任务"。
- 废弃原因（API 30 标记 deprecated）：后台启动 Service 在 8.0 之后受限、无法应对 Doze、不能保证执行完成，而且和协程/WorkManager 的能力重叠。
- 替代：需要**保证执行**（即使进程被杀/重启）用 `WorkManager`；只是异步处理用协程；需要长时间运行且用户可感知用**前台服务**。
- 顺带：`AsyncTask` 也在 API 30 废弃，原因是生命周期不感知、易泄漏、串行/并行的行为在不同版本不一致。
- 面试点：能说清"为什么废弃 + 新方案的选择依据"比背源码重要。

## 六、Jetpack

### Q: ViewModel 的原理是什么？为什么配置变更不丢数据？
**答**：
- `ViewModelStoreOwner`（Activity/Fragment）内部持有一个 `ViewModelStore`，本质是 `HashMap<String, ViewModel>`。
- 配置变更时 Activity 走了 `onRetainNonConfigurationInstance()`，`ViewModelStore` 被交给新的 Activity 实例，所以 ViewModel 存活。
- 创建走 `ViewModelProvider` + `ViewModelProvider.Factory`；同一个 key 只会创建一次。
- 真正的销毁是 `onDestroy` 且非配置变更（`isChangingConfigurations == false`）时调 `clear()`，回调 `onCleared()`。
- 注意：ViewModel 不持有 View/Activity 引用，否则一样泄漏；进程死亡后 ViewModel 也会丢，要配 `SavedStateHandle`。

### Q: Lifecycle 是怎么感知生命周期的？
**答**：
- 核心是 `LifecycleRegistry` + `LifecycleObserver`，Activity/Fragment 在 `ReportFragment` 或基类里把生命周期事件转发进来。
- 状态机五态：`INITIALIZED/DESTROYED/CREATED/STARTED/RESUMED`，事件是 `ON_CREATE/ON_START/ON_RESUME/ON_PAUSE/ON_STOP/ON_DESTROY`。
- 添加观察者时如果当前状态已经超过要观察的状态，会**补发**事件（比如在 onResume 之后注册，立刻收到 ON_CREATE/ON_START/ON_RESUME）。
- `LifecycleOwner` 提供 `lifecycle`，`repeatOnLifecycle`/`flowWithLifecycle` 就是基于它做的。
- 好处：把"注册/注销"从生命周期的散落代码里解耦，避免忘了解绑。

### Q: LiveData 的原理和坑？
**答**：
- 它是"可观察的数据容器"：`observe(owner, observer)` 时把 observer 包成 `LifecycleBoundObserver`，在 `STARTED/RESUMED` 才回调，`DESTROYED` 自动移除。
- `setValue` 必须主线程，`postValue` 可以子线程（多次 post 会合并，只保留最后一个值）。
- **粘性**：新观察者会立刻收到最后一个值；页面重建、Fragment 切换时容易重复处理，常见于"一次性的跳转/Toast"。
- 数据倒灌问题一般用 `SingleLiveEvent`、`Event` 包装类或 `Channel` 解决，官方现在更推荐 `Flow`/`StateFlow`。
- 现状：新项目用 `StateFlow` + `repeatOnLifecycle`，LiveData 主要出现在老代码和 Java 项目里。

### Q: Room 的原理是什么？有哪些优化点？
**答**：
- 编译期用注解处理器（现在推荐 **KSP**，kapt 已不推荐）生成 `Xxx_Impl` 实现类，SQL 在编译期就校验，写错表名/字段直接编译失败。
- 底层还是 SQLite，`RoomDatabase` 持有 `SupportSQLiteOpenHelper`；`@Dao` 方法支持 suspend、Flow、`@Transaction`。
- 查询返回 `Flow` 时，表变更会自动重新查询（基于 `InvalidationTracker` 监听）。
- 优化：给查询字段加索引（`@Index`）、分页用 Paging 3、批量写用 `@Insert` 列表 + 事务、避免主线程查询、大表考虑分库/归档。
- 升级：`Migration` 手写 SQL，别用 `fallbackToDestructiveMigration`（线上会丢数据）；导出 schema 便于 diff。
- 现状：GreenDAO、Orma 这些老 ORM 都已停止维护，新项目用 Room；只有跨进程高频读写才考虑 MMKV 之类的 KV 方案。

### Q: WorkManager 适合什么场景？原理是什么？
**答**：
- 适合**可延迟、需要保证执行**的任务：日志上报、数据同步、图片压缩上传、定期清理缓存。
- 支持约束（联网、充电、电量不低）、链式任务、唯一任务（`beginUniqueWork`）、重试与退避策略。
- 原理：把任务存进 Room 数据库，由 `Scheduler`（`GcmScheduler`/`JobScheduler`）在满足约束时唤醒，进程死了重启也能恢复。
- 不适合：需要精确时间（用 `AlarmManager`）、需要立刻执行且用户可感知（用前台服务）、短小的异步（直接协程）。
- 注意：Doze 下不保证准时；周期性任务最小间隔 15 分钟（`PeriodicWorkRequest`）。

### Q: Navigation 组件的价值是什么？
**答**：
- 官方推荐的**单 Activity + 多 Fragment** 导航方案，用 `nav_graph.xml` 声明目的地、动作和参数。
- Safe Args 插件在编译期生成类型安全的参数传递类，避免手写 Bundle key。
- 统一处理返回栈、转场动画、Deep Link、`popUpTo`/`popUpToInclusive`，减少手工 FragmentTransaction。
- 和 `BottomNavigationView`、`Toolbar`、`NavigationUI` 集成，自动同步选中态和返回箭头。
- 现状：Compose 项目用 `androidx.navigation:navigation-compose` 或官方新的 Navigation 3（2025 年推出，类型安全、状态驱动），XML 方案在维护老项目时仍常见。

### Q: Paging 3 的核心组件和作用？
**答**：
- `PagingSource`：定义数据从哪来（网络或数据库），负责按页加载；`RemoteMediator` 处理"网络 + 本地缓存"的混合分页。
- `Pager` 配置 `pageSize`、`prefetchDistance`、`enablePlaceholders`，产出 `Flow<PagingData>`。
- UI 层用 `PagingDataAdapter`（View）或 `collectAsLazyPagingItems()`（Compose），只渲染已加载的页。
- 自带加载状态（`LoadState`：Loading/Error/NotLoading）和重试，不用自己维护 page 变量和"是否加载中"标志。
- 注意：`PagingData` 每次都是新对象，列表刷新要保证 key 稳定，否则会闪；不要在 `PagingSource` 里持有 Activity。

### Q: DataStore 和 SharedPreferences 有什么区别？
**答**：
- SharedPreferences：同步 API，首次 `getSharedPreferences` 会**全量读进内存**并阻塞主线程，`commit` 同步写磁盘，`apply` 异步但仍有 ANR 风险。
- DataStore：基于协程 + Flow 的异步 API，读写都在 IO 线程，事务性更新（`edit {}`），不会阻塞主线程。
- 两种实现：`Preferences DataStore`（key-value）和 `Proto DataStore`（强类型 + schema，适合复杂配置）。
- 迁移：官方提供 `SharedPreferencesMigration`，可以平滑迁移老数据。
- 现状：新项目一律 DataStore；超大 key-value 或需要跨进程，考虑 MMKV（但它是同步 mmap 写，注意主线程写大值）。

### Q: Hilt 和 Dagger2、Koin 怎么选？
**答**：
- Hilt 是 Google 在 Dagger 之上的封装，用注解（`@HiltAndroidApp`、`@AndroidEntryPoint`、`@Inject`、`@Module`）自动生成各个 Android 类的注入模板，省掉大量 Component/Subcomponent 样板。
- 编译期生成代码，**没有反射**，性能好、错误在编译期暴露；代价是编译变慢（用 KSP 比 kapt 快很多）。
- Dagger2 仍然可用，但官方明确推荐迁移到 Hilt；纯 Dagger 的多 Component 配置心智负担大。
- Koin 是运行时 DI（DSL + 反射），上手快、编译快，但错误要到运行时才发现，大项目不推荐。
- 现状：新项目 Hilt + KSP 是默认答案；Compose 项目用 `hiltViewModel()` 拿 ViewModel。

### Q: App Startup 解决什么问题？
**答**：
- 多个库各自用一个 `ContentProvider` 做初始化，每个 Provider 都会拖慢启动（Provider 在 `Application.onCreate` 之前创建）。
- App Startup 提供**一个** `Initializer` 入口，把各库的初始化合并，并支持声明依赖顺序。
- 用法：实现 `Initializer<T>`，在 Manifest 里注册 `InitializationProvider` + `meta-data`，可以手动 `AppInitializer.getInstance().initializeComponent()` 延迟初始化。
- 价值：减少 Provider 数量、启动顺序可控、支持懒加载（首次使用时才初始化）。
- 面试延伸：可以用 `StartupTimingMetric` 或 Perfetto 验证 Provider 数量减少带来的启动收益。

### Q: SavedStateHandle 和进程死亡恢复是怎么回事？
**答**：
- 系统在后台杀进程后，重建时会把 `onSaveInstanceState` 的 Bundle 还给新实例；`SavedStateHandle` 就是把这个 Bundle 包装成可观察的键值容器。
- ViewModel 构造参数里带 `SavedStateHandle`，Hilt 会自动注入；存进去的值会参与 `onSaveInstanceState`。
- 限制：Bundle 有大小限制（约 1MB，和 Binder 事务相关），只能存轻量数据；大数据要落库或写文件。
- 和 `rememberSaveable` 的关系：`rememberSaveable` 是组件级、`SavedStateHandle` 是 ViewModel 级，二者最终都进同一个 `SavedStateRegistry`。
- 常见坑：不要在 `SavedStateHandle` 里存 Parcelable 大对象；存了之后要处理"类型不匹配"的 `ClassCastException`。

## 七、性能优化

### Q: 启动优化的整体思路是什么？
**答**：
- 先分清冷启动、温启动、热启动；面试说的通常是**冷启动**（进程不存在 → 创建 → 首帧上屏）。
- 量化指标：`StartupTimingMetric`、`ActivityManager` 的 `Displayed` 日志、线上用 `ProcessLifecycleOwner` 打点或 Perfetto 抓 trace。
- 分阶段治理：`Application` 创建（别做耗时初始化）、`ContentProvider`（合并/延迟）、首屏布局（减少层级、避免 `wrap_content` 嵌套）、首帧前的 IO/SP 读取。
- 手段：异步/延迟初始化、`App Startup`、`Baseline Profile`、`SplashScreen` 兜底、把非关键 SDK 挪到首帧之后（`IdleHandler`、`ReportFragment`）。
- 别只看平均值，要看 P90/P99；启动优化最容易"治了平均值、没治尾延迟"。

### Q: Baseline Profile 和 Cloud Profiles 是什么？
**答**：
- Baseline Profile 是一组"启动和常用路径上会执行的方法"列表，随 APK/AAB 打包，安装时由 dex2oat 预编译成机器码，省掉 JIT warmup。
- 生成方式：写 `BaselineProfileRule` 的 Macrobenchmark（或 Compose 的 `androidx.benchmark`），跑一遍关键用户旅程，自动采集热点，输出 `baseline-prof.txt`。
- Cloud Profiles 是 Play 下发的、来自**真实用户**的热点 profile，覆盖你写不到的路径；两者互补，同时生效。
- 效果：冷启动通常能降 20%~30%，具体看应用；对首帧卡顿也有效。
- 2025 年的状态：AGP 可以把 Cloud Profile 合并进 baseline profile 一起打包；本地自己跑出来的 `baseline-prof.txt` 仍然是启动路径最可靠的一份。

### Q: 怎么定位冷启动慢在哪一段？
**答**：
- 用 Perfetto（或 Android Studio Profiler / `systrace`）抓 `cold start` trace，看 `bindApplication`、`ActivityStart`、`Choreographer#doFrame` 的时间分布。
- 命令：`adb shell am start -W -n 包名/.MainActivity` 拿到 `TotalTime/WaitTime`，再配合 `am trace-ipc start`。
- 常见凶手：`Application.onCreate` 里同步初始化 SDK、主线程读 SharedPreferences/数据库、`ContentProvider` 太多、大图/字体加载、Dex 校验。
- 线上用 `StartupTimingMetric` + 自定义埋点（`Application` 开始、首帧 `onDraw` 结束），做版本对比和分设备对比。
- 定位到具体方法用 `Trace.beginSection` 埋点或 Method Tracing（采样），别一上来就上工具全量抓。

### Q: 内存泄漏的常见场景和排查方法？
**答**：
- 常见：静态变量持有 Activity/Context、非静态内部类（Handler/Runnable/Listener）、单例持有 View、未注销的监听/广播/回调、`WebView`、线程池里跑着的匿名类、`Bitmap` 未回收。
- 排查：LeakCanary 自动抓（debug 包常驻），线上可用 `Debug.dumpHprofData` + MAT/YourKit 分析支配树。
- 关键指标：同页面反复进出后 `Activity` 实例数应回到 1；`onDestroy` 后 GC 一次再做引用链检查。
- 修复套路：Context 用 `applicationContext`、Handler 改静态 + 弱引用、生命周期感知组件自动解绑、`onDestroyView` 里清 ViewBinding。
- 面试加分：说出"引用链最短路径"怎么读（从 GC Root 到泄漏对象），以及为什么 LeakCanary 要延迟几秒再 dump。

### Q: OOM 一般怎么排查和避免？
**答**：
- Android 的 OOM 是"堆到上限"（`ActivityManager.getMemoryClass()`，通常 192~512MB），不是物理内存不足；`OutOfMemoryError` 可能发生在任意分配点。
- 类型：单次大分配（大图、超大数组）、内存泄漏累积、频繁分配导致的碎片、native 内存（Bitmap、WebView、音视频）超限。
- 排查：抓 hprof 看 `Bitmap`/`byte[]` 占比、`adb shell dumpsys meminfo 包名` 看 PSS、Android Profiler 看实时曲线。
- 避免：图片按需采样 + 复用 + 磁盘缓存、列表及时释放、少用 `largeHeap`（掩盖问题）、监听 `onTrimMemory` 主动清缓存。
- 补充：`OutOfMemoryError` 是可以 `try/catch` 的（它是 Error 但能被捕获），但捕获后基本无法恢复，只能降级。

### Q: ANR 是怎么产生的？怎么定位？
**答**：
- 本质是**主线程在规定时间内没响应**：输入事件 5s、前台 Service 20s、广播 10s（后台 60s）、`ContentProvider` 发布超时等。
- 触发条件：主线程被锁/IO/数据库/大计算阻塞、Binder 调用对端慢（同步调用）、`MessageQueue` 被同步屏障卡住、系统 IO 拥塞。
- 定位材料：`/data/anr/traces.txt`（或 `adb bugreport` 里的 anr 目录）、主线程堆栈、`dumpsys activity` 的 `ANR in` 日志。
- 线上：接入 ANR 监控（字节/腾讯的方案或自研 `FileObserver` 监听 traces 目录），上报时带 CPU/IO 负载和主线程栈。
- 预防：主线程不做 IO、Binder 调用加超时（`oneway` 或子线程）、`StrictMode` 在 debug 包开启、SharedPreferences 首读预热。

### Q: 卡顿和 Jank 怎么量化、怎么优化？
**答**：
- 一帧 16.6ms（90Hz 是 11.1ms、120Hz 是 8.3ms）；主线程或 RenderThread 超时就是掉帧。
- 量化工具：`JankStats`（官方，能拿到每帧的 jank 原因）、`FrameMetrics`、Perfetto 抓 `doFrame`/`DrawFrame`、Macrobenchmark 的 `FrameTimingMetric`。
- 定位：主线程看 `Choreographer` 回调耗时（`FrameCallback` 里打点），渲染线程看 `DrawFrame` 的 `dequeueBuffer`/`flush` 耗时（可能是过度绘制或大图）。
- 优化：减少布局层级和过度绘制、避免在 `onDraw` 分配对象、图片降采样、`RecyclerView` 预取和局部刷新、把大计算挪到子线程。
- 注意区分"卡在 UI 线程"和"卡在 GPU"：前者优化代码，后者优化绘制（矢量图、圆角、阴影、`layerType`）。

### Q: 布局和渲染层面有哪些优化点？
**答**：
- 减少层级：`ConstraintLayout` 扁平化、`merge` 合并根节点、`ViewStub` 延迟加载不常用布局。
- 减少测量次数：避免 `RelativeLayout`/`LinearLayout` 的 `weight` 嵌套、避免 `wrap_content` 套 `match_parent`。
- 减少过度绘制：去掉多余背景、用 `canvas.clipRect`、`RecyclerView` 的 `item` 不要设不透明背景叠加。
- 自定义 View：`onDraw` 里不 new 对象（Paint/Path 提前创建）、用 `canvas.saveLayer` 谨慎、复杂静态内容可 `setLayerType(LAYER_TYPE_HARDWARE)`。
- 工具：开发者选项"显示过度绘制"、Layout Inspector、`GPU Rendering Profile`。

### Q: 包体积怎么优化？
**答**：
- 先量化：Android Studio 的 APK Analyzer 看 dex/res/assets/lib 占比，`./gradlew app:dependencies` 找重复依赖。
- 代码：R8 开启 `minifyEnabled` + `shrinkResources`，移除无用的 `-dontwarn` 保留规则；用 `R8 full mode`。
- 资源：WebP 替代 PNG、`shape` 替代图片、去除多语言（`resConfigs("zh","en")`）、压缩 png、删除无用资源（`lint --check UnusedResources`）。
- 分发：用 **AAB** 让 Play 按设备下发（abi/density/language 拆分），国内可用 split APK 或动态特性（Dynamic Feature）把非核心功能后置。
- native：只保留 `arm64-v8a`（和必要的 `armeabi-v7a`）、strip 符号表、`-Wl,--gc-sections`；so 用 `android:extractNativeLibs="false"` 直接映射。

### Q: 电量和网络怎么优化？
**答**：
- 耗电大头：网络请求（尤其是频繁心跳/轮询）、WakeLock、定位、传感器、后台任务唤醒。
- 系统机制：Doze（深度休眠推迟网络和 Job）、App Standby（按使用频率限制后台）、后台执行限制。
- 手段：请求合并/批量、用 `WorkManager` 加"联网 + 充电"约束、长连接用心跳退避 + 厂商推送、定位按精度分级（`PRIORITY_BALANCED` 而不是高精度）。
- 排查：`Battery Historian`（bugreport 可视化）、`adb shell dumpsys batterystats`、Android Studio Energy Profiler。
- 网络：`OkHttp` 连接池复用、`HttpDns`、图片按需分辨率、`Cache-Control` 与离线缓存、弱网重试退避。

### Q: 16 KB 页大小适配是什么？为什么 2025 年必须做？
**答**：
- 传统 Android 设备页大小是 4KB，新设备（尤其 arm64 新硬件）开始用 **16KB 页**，减少 TLB miss、提升性能。
- 影响：所有 native 库（.so）必须按 16KB 对齐编译，否则加载失败；未适配的应用在这些设备上会直接崩。
- 适配动作：升级 NDK（r28+）和 AGP、重新编译 so、检查三方 SDK 是否有 16KB 版本、用 `zipalign -P 16` 对齐 APK。
- 验证：`adb shell getconf PAGE_SIZE` 看设备页大小，Google 提供 16KB 模拟器镜像；用 `check_elf_alignment.sh` 检查 so。
- 时间点：Google Play 要求 **2025 年 11 月 1 日**起，targetSdk ≥ 35 的新应用和更新必须支持 16KB 页大小。

## 八、架构与工程

### Q: MVVM 和 MVI 的区别是什么？
**答**：
- MVVM：View ↔ ViewModel 双向绑定（`LiveData`/`StateFlow`），ViewModel 暴露多个状态和方法，View 直接调方法。
- MVI：**单向数据流**——View 发 `Intent/Action`，ViewModel 用 reducer 更新**单一 UiState**，View 只渲染这个 State。
- MVI 的好处：状态收敛、可回溯（时间旅行调试）、并发更新不容易打架；代价是模板代码多、State 会变大。
- 实践折中：MVVM 的骨架 + 单一 `UiState` data class + `sealed interface` 表达事件，本质是"MVI 化的 MVVM"。
- 面试别站队：说清"团队规模、状态复杂度、是否需要严格可测试"三个判断维度即可。

### Q: 为什么强调单一数据流（UDF）？
**答**：
- 数据只有一个来源（Repository/数据库），UI 是它的投影；状态改变必须走同一条路径，避免多处修改导致不一致。
- 好处：可预测、易测试、易回放 bug；配合不可变 State，重组/刷新时 diff 成本低。
- 落地：`Repository` 暴露 `Flow`，ViewModel 用 `stateIn` 转成 `StateFlow<UiState>`，View 只 `collect` 和发事件。
- 坑：别让 View 直接改 Repository 的缓存对象；别把可变集合塞进 UiState（要 `List` 的不可变副本）。
- 事件用 `Channel`/`SharedFlow(replay=0)`，状态用 `StateFlow`，两者不要混。

### Q: 模块化和组件化怎么做？
**答**：
- 分层：`app`（壳）→ `feature`（业务模块）→ `core`（网络、数据库、UI 基础、utils）→ `build-logic`（Gradle 约定插件）。
- 模块间只依赖 `api` 暴露的接口，实现用 `implementation` 隐藏，避免"牵一发动全身"的重编译。
- 通信：路由（ARouter/Navigation）+ 接口下沉（`Export` 模块放接口，实现靠 DI 注入）。
- 收益：编译提速（增量/并行）、边界清晰、可按需拆分动态特性、团队并行开发。
- 代价：Gradle 配置复杂度上升、模块粒度要克制（几十个模块反而更慢），建议先用"按层 + 少量 feature"起步。

### Q: ARouter 的原理是什么？现在还用吗？
**答**：
- 编译期用注解处理器扫描 `@Route`，为每个模块生成路由表类；运行时通过 `ARouter$$Group$$xxx` 反射/加载汇总成路由表。
- 跳转时按 path 查表，拿到目标 Activity 的 Class 再 `startActivity`；支持拦截器（`IInterceptor`）、参数自动注入（`@Autowired`）、降级（`DegradeService`）。
- 优点：解耦、跨模块跳转、支持编译期分组；缺点：注解处理拖慢编译、反射初始化有启动成本、KSP 支持不完善。
- 现状：新项目更多用 **Navigation**（官方、类型安全）或手写轻量路由 + DI；ARouter 在老项目和大型多团队项目里仍大量存在，但官方维护活跃度下降。
- 如果还要用：一定要做路由表懒加载 + 编译期校验，别让它在 `Application.onCreate` 里全量扫描。

### Q: 插件化和热修复现在是什么状态？
**答**：
- 插件化：把未安装的 APK/dex 加载进来运行。`Shadow`（腾讯）仍在维护，支持宿主+插件、零 Hook；`RePlugin`（360）基本停更；`VirtualApp` 开源版早已停更、商业版收费。
- 现实约束：Android 9+ 的 hidden API 限制、14/15 对动态加载和 `exported` 的收紧，让"全插件化"成本极高。
- 现在的主流替代：**Dynamic Feature / Play Feature Delivery**（官方分包下发）、按需下载 so/资源、小程序容器、Flutter/RN 这类跨端容器。
- 热修复：`Tinker`（腾讯）已停止维护（官方 2023 年发公告），`Sophix`（阿里）商业化、`Robust`（美团）仍在用但需自建。
- 现实做法：Java 层用"补丁 dex + 类加载插队"做紧急修复，配合**灰度 + 服务端开关 + 降级**；能发版解决就别上热修。

### Q: CI/CD 流水线一般包含哪些环节？
**答**：
- 提交触发（GitHub Actions / GitLab CI / Jenkins）→ 静态检查（ktlint/detekt/Android Lint）→ 单元测试 → 编译打包（debug/release、多渠道）→ 签名 → 分发（Firebase App Distribution / 蒲公英 / 内测平台）。
- 质量门禁：单测覆盖率、Lint 阻断级别、`assembleRelease` 必须过 R8、体积增量阈值（超过就告警）。
- 缓存：Gradle 依赖缓存、`build-cache`、`configuration-cache`，能把 CI 时间砍一半以上。
- 发布：Play 用 AAB + 分阶段发布（staged rollout），国内渠道用多渠道包 + 各商店 API 上传。
- 进阶：自动化截图测试、Macrobenchmark 跑在 CI 上做性能回归、`danger` 做 PR 检查。

### Q: Gradle 配置缓存（configuration cache）是什么？怎么开？
**答**：
- 配置阶段（执行 `build.gradle.kts`、解析依赖图）在大型项目里能占 30% 以上构建时间；配置缓存把这次配置的结果序列化缓存，下次直接复用。
- 开启：`org.gradle.configuration-cache=true`（Gradle 8.x），先 `--configuration-cache-problems=warn` 观察不兼容的插件。
- 常见不兼容：在配置阶段读环境变量/时间、用了 `Project` 对象在 task 执行期、自定义插件持有 `Project` 引用。
- 配套优化：`org.gradle.parallel=true`、`org.gradle.caching=true`、`org.gradle.configureondemand`（按需配置）。
- 收益：二次构建配置阶段接近 0，CI 上尤其明显；代价是首次构建和排查不兼容的成本。

### Q: version catalog 和 KSP 是什么？为什么要用？
**答**：
- Version Catalog（`gradle/libs.versions.toml`）集中管理依赖版本，用 `libs.androidx.core` 引用，避免各模块版本打架，IDE 有补全和升级提示。
- 配合 `build-logic` 里的 convention plugin，把"compileSdk、minSdk、混淆配置"统一起来，新模块只写几行。
- KSP 是 Kotlin 的符号处理 API，比 kapt 快（kapt 要生成 Java stub，KSP 直接读 Kotlin AST），增量支持好。
- 现状：Room、Hilt、Moshi、Molecule 等都已支持 KSP；kapt 在 Kotlin 2.x 下仍在但已被官方标记为"维护模式"。
- 建议：新项目直接 KSP；老项目迁移时先确认所有注解处理器都有 KSP 版本。

### Q: 静态检查和代码规范怎么落地？
**答**：
- `ktlint` 管格式、`detekt` 管坏味道（复杂度、长函数、魔法数字）、`Android Lint` 管 API 使用和资源问题。
- 三者都接到 CI 的 `check` 任务上，失败即阻断；本地用 git pre-commit hook 或 IDE 插件提前发现。
- 团队约定要写进 `detekt.yml`/`lint.xml`，别只靠口口相传；新规则先 warn 一段时间再改 error。
- 架构约束可以用 `Konsist` 或模块依赖规则（`module-info` 式的 `api/implementation`）做自动化守护。
- 收益：Code Review 只讨论设计，不再争论空格和命名。

## 九、系统与适配

### Q: Android 12 有哪些关键行为变更？
**答**：
- 启动画面统一：系统强制用 `SplashScreen` API，`windowBackground` 白屏方案失效，要用 `SplashScreen.setKeepOnScreenCondition` 控制时长。
- 组件必须显式声明 `android:exported`，带 intent-filter 不写直接编译失败（安全加固）。
- `PendingIntent` 必须声明可变性（`FLAG_IMMUTABLE` 或 `FLAG_MUTABLE`）。
- 模糊定位：用户可以只授予"大致位置"，`ACCESS_FINE_LOCATION` 要单独请求；蓝牙权限拆成 `BLUETOOTH_SCAN/CONNECT/ADVERTISE`。
- 精确闹钟需要 `SCHEDULE_EXACT_ALARM`（用户可撤销）；通知 trampoline 限制（点通知不能直接起 Service/Activity，要过 PendingIntent）。

### Q: Android 13 有哪些关键行为变更？
**答**：
- 通知运行时权限 `POST_NOTIFICATIONS`：不申请就发不出通知，13 以下默认授予。
- 细分媒体权限：`READ_MEDIA_IMAGES/VIDEO/AUDIO` 替代 `READ_EXTERNAL_STORAGE`；同时提供**照片选择器**（Photo Picker），不授权也能选图。
- 按应用设置语言（`LocaleManager`）、主题图标（Monet）、前台服务通知不可划掉。
- 剪贴板敏感内容会提示用户；`Intent` 过滤器匹配更严格。
- 后台身体传感器权限被拆成 `BODY_SENSORS_BACKGROUND`。

### Q: Android 14 有哪些关键行为变更？
**答**：
- 前台服务必须声明 `foregroundServiceType` 且运行时类型匹配，还要求先拿到对应权限（如 `FOREGROUND_SERVICE_CAMERA`）。
- 隐式 Intent 限制：启动内部组件时必须显式指定包名，否则抛异常。
- 精确闹钟默认拒绝：targetSdk 33+ 的新安装应用默认没有 `SCHEDULE_EXACT_ALARM`，要引导用户开启；闹钟/日历类应用改用 `USE_EXACT_ALARM`（免用户授权但审核严格）。
- 部分照片访问：`READ_MEDIA_VISUAL_USER_SELECTED`，用户可以只给部分照片。
- `minSdk` 低于 23 的应用无法安装；动态注册广播必须声明导出性。

### Q: Android 15 有哪些关键行为变更？
**答**：
- **edge-to-edge 强制**：targetSdk 35 起，应用默认全屏绘制，`statusBarColor` 等 API 失效，必须自己处理 `WindowInsets`。
- 前台服务限制：从 `BOOT_COMPLETED` 启动的 `dataSync`、`camera`、`mediaPlayback` 等类型受限。
- 16KB 页大小支持进入实施阶段（新设备 + Play 要求）。
- 私有空间（Private Space）让应用可被"隐藏"，相关广播/权限要适配。
- `bindService` 用隐式 Intent 时必须指定包名；后台通过 `PendingIntent` 拉起 Activity 的限制更严。

### Q: Android 16 有哪些关键行为变更？
**答**：
- 大屏强制自适应：targetSdk 36 在 `sw >= 600dp` 的设备上会**忽略**应用的 `screenOrientation`、`resizableActivity` 限制，应用必须能自由缩放。
- edge-to-edge 与预测性返回（predictive back）进一步默认开启，返回手势动画由系统接管；16KB 页大小在 `targetSdk 36` 下成为硬要求。
- 通知与 Quick Settings 的视觉规范调整，自定义 `RemoteViews` 的可用空间进一步被压缩。
- 适配建议：别锁方向、用 `WindowSizeClass` 做响应式布局、所有页面测一遍分屏/自由窗口。

### Q: 分区存储（Scoped Storage）怎么理解？
**答**：
- Android 10 引入、11 强制：应用默认只能访问自己的沙盒目录和通过 `MediaStore`/SAF 访问的媒体文件。
- 沙盒目录：`getFilesDir()`、`getCacheDir()`、`getExternalFilesDir()`，卸载即删，不需要权限。
- 共享媒体：图片/视频/音频通过 `MediaStore` 读写，自己的文件用 `insert` 拿 Uri 写入；Android 11 起支持 `MediaStore.createDeleteRequest` 批量删除。
- 其他文件：用 SAF（`ACTION_OPEN_DOCUMENT`）让用户选，拿持久化 Uri 权限。
- `MANAGE_EXTERNAL_STORAGE`（所有文件访问）只给文件管理器/杀毒这类应用，上架要审核。

### Q: 通知权限和通知渠道要注意什么？
**答**：
- Android 8.0 起必须建 `NotificationChannel`，否则通知不展示；渠道的重要性（`IMPORTANCE`）建好之后**不能改**，只能引导用户去设置页。
- Android 13 起 `POST_NOTIFICATIONS` 是运行时权限，要先请求；拒绝后可以再次请求，但用户勾选"不再询问"就只能跳设置。
- 前台服务通知不可划掉，且 14 起要标类型；`setForegroundServiceBehavior` 可以改善显示时机。
- 通道分组（`NotificationChannelGroup`）便于用户批量管理；营销类和事务类要分渠道，否则用户关一个全关。
- 适配建议：在"用户真正需要"的时机请求权限（比如开启提醒时），不要一进 App 就弹。

### Q: 精确闹钟怎么用？各版本有什么差异？
**答**：
- `AlarmManager.setExactAndAllowWhileIdle()` 才能在 Doze 下准点触发；普通 `set()` 会被推迟。
- Android 12 起需要 `SCHEDULE_EXACT_ALARM` 权限，用户可在设置里撤销，用 `canScheduleExactAlarms()` 检查并引导。
- Android 13 起闹钟/日历类应用可申请 `USE_EXACT_ALARM`（安装即授予，但 Play 审核严格，仅限核心功能是闹钟的应用）。
- Android 14 起 targetSdk 33+ 新安装应用默认没有 `SCHEDULE_EXACT_ALARM`，必须走用户授权流程。
- 替代：不要求精确时间就用 `WorkManager` 或 `setWindow()`/`setAndAllowWhileIdle()`，省电也省权限麻烦。

### Q: 大屏和折叠屏怎么做自适应？
**答**：
- 用 `WindowSizeClass`（compact/medium/expanded）驱动布局，而不是判断设备类型或屏幕英寸。
- 布局：列表-详情双栏（`SlidingPaneLayout`/`ListDetailPaneScaffold`）、`NavigationRail` 替代底部栏、限制内容最大宽度。
- 配置：`android:resizeableActivity="true"`，别锁 `screenOrientation`；处理 `onConfigurationChanged` 和窗口大小变化（`WindowMetrics`）。
- 折叠屏：监听 `WindowInfoTracker` 的 `FoldingFeature`，铰链处避免放内容；`Jetpack WindowManager` 是官方方案。
- 测试：用 Android Studio 的 Resizable 模拟器 + 大屏徽章（`android:screenOrientation` 检查）、`letterbox` 模式检查。

### Q: edge-to-edge 怎么正确实现？
**答**：
- 目标：内容绘制到状态栏/导航栏下面，但要给可交互元素留出安全区。
- 传统 View：`WindowCompat.setDecorFitsSystemWindows(window, false)` + `ViewCompat.setOnApplyWindowInsetsListener` 拿 `systemBars()` insets 做 padding。
- Compose：`enableEdgeToEdge()` + `Scaffold` 的 `innerPadding` + `WindowInsets.safeDrawing`。
- 注意：`ime()` insets 处理键盘遮挡、`displayCutout()` 处理刘海、列表底部要加 `navigationBars` padding 否则最后一项被遮。
- Android 15 起 targetSdk 35 默认强制全屏，不处理就会"内容被状态栏压住"，这是最常见的适配 bug。

## 十、开放题

### Q: 如果让你设计一个图片加载库，怎么设计？
**答**：
- 分层：请求层（Uri/尺寸/变换/优先级）→ 缓存层（内存 LruCache + 磁盘 DiskLruCache）→ 解码层（采样 `inSampleSize`、`inPreferredConfig`）→ 显示层（生命周期绑定、占位图、动画）。
- 内存缓存 key 用"Uri + 目标宽高 + 变换"，value 是 `Bitmap`，大小按 `maxMemory/8` 定；磁盘缓存按原图存，避免重复下载。
- 线程模型：请求去重（同 key 合并）、三级线程池（IO/解码/回调）、列表滑动时暂停/恢复。
- 难点：生命周期（页面销毁取消请求）、Bitmap 复用（`inBitmap`）、大图区域解码（`BitmapRegionDecoder`）、GIF/WebP 支持、内存与 OOM 的平衡。
- 最后说取舍：为什么 Glide 用 `ActivityFragmentLifecycle`、为什么 Coil 用 OkHttp + 协程、为什么 Fresco 用 ashmem 匿名共享内存。

### Q: 设计一个下载器要注意什么？
**答**：
- 核心能力：多任务并发、断点续传（`Range` 请求 + 临时文件 + 已完成分片记录）、暂停/恢复、进度回调、失败重试与退避。
- 状态机：`WAITING → RUNNING → PAUSED/FAILED → COMPLETED`，状态要持久化（数据库），进程重启能恢复。
- 文件安全：下载到 `.tmp` 再原子 rename，校验 MD5/文件大小，避免半成品被当成完整文件。
- 并发控制：按域名/全局限制并发数（避免打爆服务端），大文件分片并发下载再合并。
- 工程化：前台服务 + 通知（用户可感知）、`WorkManager` 做约束（仅 Wi-Fi）、流量统计与限速。

### Q: 设计一个日志库呢？
**答**：
- 分级（VERBOSE~ASSERT）+ Tag 过滤 + 线程/时间信息，release 包自动降级或关闭。
- 写入：内存队列 + 单线程/协程串行落盘，按天/大小滚动切割，支持压缩和历史清理（避免占满用户存储）。
- 性能：避免在主线程做字符串拼接（用惰性 lambda 参数）、批量 flush、崩溃时用 `UncaughtExceptionHandler` 同步刷盘。
- 安全：敏感信息脱敏、加密（尤其上报）、可配置采样率，日志文件放沙盒目录。
- 上报：异常聚合（同类堆栈归并）、带设备/版本/场景上下文、支持按用户反馈附带最近 N 行日志。

### Q: 崩溃治理怎么做？
**答**：
- 采集：`Thread.setDefaultUncaughtExceptionHandler` 抓 Java 崩溃，`native` 用 Breakpad/Coil 方案抓 tombstone，ANR 单独链路。
- 上报：崩溃时先写本地文件再异步上报（崩溃现场不能做重活），下次启动补传，保证不丢。
- 治理：按"崩溃率 = 崩溃次数/启动次数"和"影响用户数"双维度排优先级；Top 崩溃逐个定 Owner、定修复版本。
- 止损：服务端开关降级、热修复（谨慎）、灰度回滚；新版本上线盯 24 小时崩溃率曲线。
- 长期：把崩溃率纳入发布门禁（比如超过 0.1% 阻断全量），做崩溃自动分桶和堆栈指纹聚合。

### Q: 怎么保证线上质量？
**答**：
- 左移：单元测试 + 集成测试 + UI 测试（Espresso/Compose Test），CI 上跑，覆盖率设底线（别追求数字，追求核心链路覆盖）。
- 灰度：按用户/设备/地域分批放量（1% → 5% → 20% → 全量），每阶段看崩溃率、ANR 率、核心转化指标。
- 监控：APM（启动、卡顿、网络、页面耗时）+ 业务埋点 + 告警（错误率、P99 延迟），出问题能 5 分钟内定位到版本/机型。
- 兜底：配置中心开关、功能降级、强制更新、热修通道；客户端要有"自杀开关"（远程关闭某个功能）。
- 复盘：每次线上问题产出时间线 + 根因 + 改进项，跟进到落地，别只写文档。

### Q: 技术选型你会怎么判断？
**答**：
- 先问需求：是短期活动页还是长期核心模块？团队有几个人、熟不熟？维护周期多长？
- 看维护状态：最近一次提交、issue 响应、是否有大公司在用（比如选 Coil 而不是已经停更的图片库）。
- 看迁移成本：API 稳定性、包体积增量、编译时间影响、是否能渐进接入（灰度/并存）。
- 看风险：许可证、是否依赖 hidden API、是否强依赖某个云服务、出问题能不能自己改。
- 决策要写下来（ADR）：选了什么、为什么、放弃了什么，半年后回看还能解释。

### Q: 让你主导一次大型重构，你怎么推进？
**答**：
- 先量化痛点：构建时间、崩溃率、需求交付周期，用数据说服而不是"我觉得代码烂"。
- 划定边界：先做"高收益低风险"的（比如统一网络层、升级 AGP/Kotlin），再做伤筋动骨的（模块化、Compose 迁移）。
- 保证可回滚：每一步都能独立上线，用开关控制；新老逻辑并存一段时间，对比指标后再删旧代码。
- 组织层面：拉上测试和业务方定验收标准，把重构拆成可并行的小任务，避免"半年一个大分支"。
- 收尾：补文档和自动化守护（lint 规则、架构测试），否则半年后又烂回去。
