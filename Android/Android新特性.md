> 2025 更新：本文保留 5.0～10.0 的原始条目，并在每一节补充当年容易漏掉、面试又会追问的点；11.0～16.0 为新增章节，只挑开发者真正要适配的变更。版本行为以 Android 官方文档和对应 targetSdk 为准，API 级别：11=30、12=31、13=33、14=34、15=35、16=36。

## 5.0

* Material Design
* 支持多种设备
* 全新的通知设计
* 64 位的 ART 虚拟机
* Overview （多任务视窗）
* 设备识别锁（附近有智能手表等，解锁）
* 面部解锁
* RecyclerView、CardView
* 三种 Notification（普通、折叠、悬挂）
* Toolbar、Palette

> 2025 更新：原文「Meterial Desigin」拼写已修正。5.0 当年容易漏掉、但面试常追问的三点：
>
> - **JobScheduler（API 21）**：把任务延迟到充电、联网、空闲等条件下执行，是后来 WorkManager 的前身；面试常问它和 WorkManager、AlarmManager 的区别。
> - **WebView 可独立更新**：从 5.0 起 WebView 作为独立 APK 通过应用商店更新，不再必须跟随系统 OTA。
> - **ART 成为默认运行时**：Dalvik 退场，安装时 AOT 编译；后来的 JIT、Profile、Baseline Profile 都是在 ART 上继续演进。

## 6.0

* 应用权限管理
* Android Pay
* 指纹支持
* Doze 电量管理
* App Links

> 2025 更新：这三项是 6.0 最常被面试展开的：
>
> - **运行时权限**：危险权限按权限组申请，用户可随时撤销；代码侧对应 `checkSelfPermission()`、`requestPermissions()` 和 `shouldShowRequestPermissionRationale()`。
> - **Doze 与 App Standby**：Doze 在息屏、静止、未充电时进入维护窗口，延迟网络和 Job；App Standby 则按应用使用频率限制后台。不要把「保活」等同于「绕过 Doze」。
> - **指纹与自动备份**：平台指纹 API 后来被 `BiometricPrompt` 统一；Auto Backup 让应用数据默认参与云备份，需用 `android:allowBackup`、`fullBackupContent` 控制边界。

## 7.0

* 多窗口模式
* Data Saver （流量保护机制）
* 改进 Java 8 语言支持
* 自定义壁纸
* 快速回复
* 后台省电
* 快速设置通知栏快捷界面

> 2025 更新：7.0 最该补的是「文件 URI 暴露」和「多窗口生命周期」：
>
> - **FileProvider**：targetSdk 24 起，应用间直接传 `file://` URI 会抛 `FileUriExposedException`，必须用 `content://` + `FileProvider` 授权临时读写。
> - **多窗口回调**：`onMultiWindowModeChanged()`、`isInMultiWindowMode()` 让页面在分屏/画中画时调整布局；7.0 也是画中画 TV 之外进入手机的重要版本。
> - **Java 8 与 desugaring**：当年的 Jack 工具链已废弃，现代做法是 javac/kotlinc + D8/R8，并按 AGP 要求用 JDK 17 构建。

## 8.0

* 全新的通知中心
* 画中画支持
* 自适应启动器图标
* 多显示器支持
* 后台执行限制（后台Service限制、广播限制）
* 后台位置信息限制

> 2025 更新：8.0 是「后台限制 + 系统可升级」的分水岭，务必补上：
>
> - **Project Treble**：把 HAL 接口化，`/system` 与 `/vendor` 解耦，厂商不必为每次系统升级重写 HAL；这是 Android 更新提速的起点。
> - **NotificationChannel**：targetSdk 26 起通知必须归属渠道，用户可按渠道开关；没有渠道的通知不会展示。
> - **Autofill Framework**：系统级自动填充 API，密码管理器、表单填写都建立在这套框架上。

## 9.0

* 全面屏
* 机制学习
* 室内定位
* 对使用非 SDK 接口的限制

> 2025 更新：9.0 的「全面屏」在代码里主要就是刘海/挖孔适配，另外还有两个高频点：
>
> - **刘海屏适配**：`DisplayCutout`、`layoutInDisplayCutoutMode`，以及全屏内容要主动处理 `WindowInsets`，不能假设状态栏一定在顶部。
> - **默认禁止明文 HTTP**：targetSdk 28 起 `usesCleartextTraffic` 默认为 false，需要显式配置 `networkSecurityConfig`；这是线上「接口突然请求失败」的常见原因。
> - **BiometricPrompt**：统一指纹、面容、虹膜等生物识别交互，替代各厂商指纹 SDK 和已废弃的 `FingerprintManager`。

## 10.0

* 5G 网络支持
* 可折叠设备
* 暗黑主题
* 手势导航
* ART 优化（分代垃圾回收功能）
* 用户隐私

> 2025 更新：10.0 的「用户隐私」落到代码上，最关键的是分区存储和后台启动限制：
>
> - **分区存储（Scoped Storage）**：应用默认只能访问自己的目录和通过 `MediaStore`/SAF 授权的媒体；targetSdk 29 还能用 `requestLegacyExternalStorage` 临时退出，到 11.0 就失效了。
> - **后台启动 Activity 限制**：应用在后台不能随意弹 Activity，需改用通知、前台服务或全屏 Intent（且受后续版本继续收紧）。
> - **暗黑主题适配**：除了 `DayNight` 主题，还要处理 `forceDarkAllowed`、WebView 和自定义 View 的配色，不能只换一张背景图。

## 11.0

> API 30。这一版的主线是「权限与存储继续收紧」，也是分区存储真正强制的一代。

* **分区存储强制**：targetSdk 30 起不能再通过 `requestLegacyExternalStorage` 退出；访问共享媒体走 `MediaStore`，访问文档走 SAF，确实需要全盘文件管理能力才申请 `MANAGE_EXTERNAL_STORAGE`（上架审核严格）。
* **包可见性（Package Visibility）**：查询其他应用（`getPackageInfo`、`queryIntentActivities` 等）会被过滤；需要在清单里用 `<queries>` 声明要交互的应用，或申请受限制的 `QUERY_ALL_PACKAGES`。
* **一次性权限**：位置、麦克风、相机可只授予「仅这一次」；应用进入后台一段时间后权限自动失效，不能假设拿到就永久有效。
* **未使用应用自动重置权限**：长期不用的应用，系统会自动重置其运行时权限；适配时要处理权限被回收后的降级流程。
* **前台服务类型**：`android:foregroundServiceType` 开始区分 camera、microphone、location 等类型；使用对应硬件时要匹配类型和权限。
* **后台启动前台服务受限**：应用在后台时不能随意 `startForegroundService()`，需要符合豁免场景（如高优先级 FCM、闹钟等），否则抛异常。
* **无线调试**：开发者选项里可用配对码在 Wi-Fi 上跑 adb，不再依赖 USB；自动化测试和车机/电视调试都常用。
* **气泡通知（Bubbles）**：类似聊天气泡的悬浮入口，需要通知渠道和用户授权，适合持续会话，不适合所有通知。
* **增量安装与 APK Signature Scheme v4**：通过 Play 的增量安装减少下载体积；v4 签名配合增量安装做校验，发布链路要留意签名配置。

## 12.0

> API 31。这一版「适配项」特别多，常见崩溃几乎都能在 PendingIntent、exported 和蓝牙权限上找到原因。

* **SplashScreen API**：系统统一启动画面，应用可用 `SplashScreen` / `installSplashScreen()` 定制图标、背景和退出动画；不要再用「主题里放一张全屏图」的老办法硬扛。
* **Material You 动态配色**：Android 12 起系统可从壁纸生成配色，`DynamicColors` 让应用跟随系统主题；同时要保证自定义品牌色在动态色下仍有对比度。
* **大致位置**：用户可以选择只给「大致位置」，应用不能假设一定拿到精确位置；需要精确位置时要解释用途并处理降级。
* **PendingIntent 可变性**：targetSdk 31 起创建 PendingIntent 必须显式指定 `FLAG_IMMUTABLE` 或 `FLAG_MUTABLE`，否则直接崩溃；优先不可变，确实需要被填充时才用可变。
* **`android:exported` 必填**：带 intent-filter 的 Activity/Service/Receiver 必须显式声明 exported，否则安装失败；不要把不需要对外暴露的组件误设为 true。
* **蓝牙权限拆分**：`BLUETOOTH_SCAN`、`BLUETOOTH_CONNECT`、`BLUETOOTH_ADVERTISE` 取代旧的 `BLUETOOTH`/`BLUETOOTH_ADMIN`，并按「附近设备」运行时授权；只扫描不定位时可加 `neverForLocation`。
* **精确闹钟权限**：使用 `SCHEDULE_EXACT_ALARM` 属于特殊应用权限，用户可关闭；闹钟、日历类应用才适合申请，普通提醒优先用 WorkManager 或非精确 AlarmManager。
* **前台服务启动限制**：从后台启动前台服务受限制，和 11.0 的限制一起构成后台执行约束；设计上要区分「用户可感知的前台任务」和「可延迟的后台任务」。
* **通知 trampoline 限制**：点击通知后不能先起一个中间 BroadcastReceiver/Service 再启动 Activity，应直接用 PendingIntent 指向目标页面。
* **隐私指示器与开关**：麦克风、相机使用时有系统指示器，用户可一键关闭；应用要处理权限仍在但硬件被系统禁用的情况。
* **应用休眠（App Hibernation）**：长期未使用的应用会被系统休眠，权限、通知、后台任务都会被收紧；适配时不要依赖「应用一定长期活着」。

## 13.0

> API 33。通知权限、照片选择器和按应用语言是这一版最常被问的三件事。

* **通知运行时权限**：targetSdk 33 起，新安装应用默认没有 `POST_NOTIFICATIONS`，必须请求；用户拒绝后仍可通过设置开启，代码要处理「没有通知权限」的完整链路。
* **照片选择器（Photo Picker）**：系统提供的无权限选图入口，用户只授权选中的照片；优先用 `PickVisualMedia`，比申请全量媒体权限更符合隐私要求。
* **按应用语言**：用户可在系统设置为单个应用指定语言；应用通过 `android:localeConfig` 和 `LocaleManager` 声明/读取，AppCompat 1.6+ 提供兼容实现。
* **主题图标（Themed Icons）**：自适应图标增加 monochrome 层，跟随 Material You 主题着色；不提供该层就可能显示为普通图标。
* **细化媒体权限**：`READ_MEDIA_IMAGES`、`READ_MEDIA_VIDEO`、`READ_MEDIA_AUDIO` 取代 `READ_EXTERNAL_STORAGE`，按类型申请，不要继续申请大而全的存储权限。
* **蓝牙/附近设备权限继续收紧**：12.0 已把蓝牙拆成 SCAN/CONNECT/ADVERTISE；13.0 起 Wi-Fi 相关场景新增 `NEARBY_WIFI_DEVICES`，蓝牙扫描若明确不用于定位可声明 `neverForLocation`（该标记自 12.0 起可用），审核和运行时授权都强调最小权限。
* **预测性返回手势（Predictive Back）**：13.0 提供开发者选项预览，后续版本逐步默认开启；应用应迁移到 `OnBackInvokedCallback`，不要在 `onBackPressed()` 里写死所有返回逻辑。
* **剪贴板预览**：复制敏感内容时系统会显示预览，应用可通过 `ClipDescription.EXTRA_IS_SENSITIVE` 标记密码、验证码等内容，避免明文展示。

## 14.0

> API 34。这一版的关键词是「前台服务类型必填」和「精确闹钟默认拒绝」，也是后台适配最容易翻车的一代。

* **前台服务类型必填**：targetSdk 34 起，启动前台服务必须声明 `foregroundServiceType` 并申请对应的 `FOREGROUND_SERVICE_*` 权限；缺类型会抛 `MissingForegroundServiceTypeException`。
* **精确闹钟默认拒绝**：新安装的 targetSdk 33+ 应用默认不授予 `SCHEDULE_EXACT_ALARM`，需要引导用户到设置页开启；只有闹钟、日历等核心场景才适合用 `USE_EXACT_ALARM`。
* **部分照片访问**：用户可以选择「仅允许访问选中的照片」，应用通过 `READ_MEDIA_VISUAL_USER_SELECTED` 处理部分授权；不要假设拿到权限就能遍历整个相册。
* **动态注册广播必须声明导出行为**：targetSdk 34 起，`registerReceiver()` 对非系统广播要显式传 `RECEIVER_EXPORTED` 或 `RECEIVER_NOT_EXPORTED`，否则抛 `SecurityException`；只接收应用内广播时选 NOT_EXPORTED。
* **区域偏好（Regional Preferences）**：用户可单独设置温度单位、一周起始日、日历类型等；应用应读取这些偏好（AndroidX 可用 `LocalePreferences`），不要只用 `Locale` 猜。
* **隐式 Intent 限制**：targetSdk 34 起，隐式 Intent 只会投递给已导出的组件；应用内部跳转应使用显式 Intent，避免「明明注册了却收不到」。
* **最低安装 targetSdk 提高**：Android 14 设备拒绝安装 targetSdk 低于 23 的应用；老项目升级时先确认 targetSdk，不要只改 compileSdk。
* **核心库对齐 OpenJDK 17**：Android 14 的 core libraries 更新到 OpenJDK 17 级别，语言特性和库行为更现代；构建侧仍以 AGP 要求的 JDK 17 为准。

## 15.0

> API 35。这一版是「大屏 + 边到边 + 16 KB」的适配节点，也是后台任务继续收紧的一代。

* **edge-to-edge 强制**：targetSdk 35 起，应用默认边到边绘制，状态栏/导航栏透明，内容延伸到系统栏后面；必须用 `WindowInsets` 处理安全区域，并移除对系统栏颜色的硬编码假设。
* **16 KB 页大小支持**：Android 15 引入 16 KB 页大小设备/开发选项，含 native 代码的应用要按 16 KB 对齐重新编译；否则可能无法安装或运行（Google Play 后续也把它列为上架要求）。
* **前台服务超时**：`dataSync`、`mediaProcessing` 类型的前台服务有运行时长上限（约 6 小时/24 小时），超时后系统调用 `onTimeout()`；长任务要拆分、续跑或改用 WorkManager。
* **后台启动 Activity 限制**：targetSdk 35 起，应用从后台启动 Activity 会被阻止，只有少数豁免；依赖「后台弹全屏页」的产品逻辑要改成通知、悬浮窗或前台服务。
* **部分屏幕共享**：系统屏幕共享支持只共享一个应用窗口，而不是整块屏幕；`MediaProjection` 场景要按新的窗口/权限模型适配，并保留 `mediaProjection` 前台服务类型。
* **预测性返回默认开启**：targetSdk 35 的返回手势会展示目标页面预览，应用要支持 `OnBackInvokedCallback`；自定义返回拦截不能只覆盖 `onBackPressed()`。
* **敏感通知保护**：Android 15 会自动识别含 OTP 的通知，并在不可信应用读取、录屏等场景隐藏内容；应用不要把验证码直接写进通知标题/正文，具体行为以官方文档为准。
* **私密空间（Private Space）**：用户可把应用放进独立空间，进入后应用可见性和状态会变化；应用要正确处理「被隐藏/重新出现」时的生命周期和数据刷新。

## 16.0

> API 36。2025 年发布，重点是「边到边不再可退出、大屏忽略方向限制、16 KB 与后台配额」。

* **edge-to-edge 强制**：targetSdk 36 起，15.0 提供的边到边退出开关失效，应用必须真正适配系统栏 Insets；全屏、手势导航、刘海屏要一起验证。
* **大屏自适应（忽略方向/resizeable）**：在最小宽度 ≥600dp 的大屏设备上，targetSdk 36 的应用会被忽略屏幕方向、可调整大小和宽高比限制，系统按自适应窗口展示；要按响应式布局设计，而不是锁死竖屏（个别兼容场景可用官方标志临时退出，具体以文档为准）。
* **16 KB 页大小强制**：16 KB 设备成为正式兼容目标，含 native 库的应用必须保证 ELF 段对齐；Google Play 自 2025-11-01 起要求面向 Android 15+ 的应用支持 16 KB 页大小（具体以官方政策为准）。
* **JobScheduler 配额调整**：任务配额与 App Standby Bucket 更紧密地挂钩，活跃应用配额更宽松，受限应用更容易被延迟；后台任务要可降级、可重试，不能假设「提交了就准时跑」。
* **ART 更新**：ART 继续作为 Mainline 模块独立更新，16.0 的 ART 版本包含启动、编译和 GC 方向的优化；这部分可通过 Play 系统更新下发，具体行为仍取决于设备厂商实现。
* **Live Updates 通知**：面向外卖、出行、配送等「进行中」场景的进度型通知，可在锁屏/通知栏持续展示进度；使用前要评估通知权限和用户打扰。
* **Safer Intents**：Android 16 继续收紧 Intent 解析和重定向安全，跨应用跳转应尽量使用显式 Intent 并校验目标；具体限制以官方 behavior changes 为准。

## 面试怎么用这张表

1. **按 targetSdk 记，不要按版本号背功能**：真正会导致崩溃/上架失败的是「targetSdk 升到 N 后必须改什么」，例如 31 的 PendingIntent/exported、33 的通知权限、34 的前台服务类型、35 的 edge-to-edge。
2. **每个版本挑 2～3 个有迁移成本的点**：权限（一次性、通知、精确闹钟）、后台（Doze、FGS、BAL）、存储（分区存储、照片选择器）、UI（刘海、edge-to-edge、大屏）是四条主线。
3. **回答时带上项目例子**：不要只说「Android 13 加了通知权限」，要说「我们把通知权限请求放到用户开启提醒的场景，拒绝后保留站内消息兜底」。
4. **区分「新功能」和「行为变更」**：Material You、Live Updates 是功能；分区存储、exported、16 KB 是兼容性要求，面试官更关心后者。
5. **不确定的细节就收口**：可以说「这块以对应版本的 behavior changes 和 targetSdk 为准」，比硬背一个记错的 API 名称更加分。
