# Android 版本适配：6.0 到 16 的行为变更与适配清单

面向真实面试复习：每个版本的**行为变更（Behavior Changes）**什么时候生效、会炸在哪里、工程上怎么改。

## 1 为什么要适配

### 1.1 三个 SDK 版本的分工

| 配置项 | 含义 | 说明 |
| --- | --- | --- |
| `compileSdk` | 编译期使用的 SDK | 决定能调用哪些新 API，不影响运行时行为 |
| `targetSdk` | 声明"我已适配到哪个行为级别" | **决定行为变更是否生效**，是适配的核心开关 |
| `minSdk` | 最低可安装版本 | 决定要兼容到多老的设备，与行为变更无关 |

结论：**行为变更只对 `targetSdk` 达到该版本的应用生效**。同一台 Android 15 手机，targetSdk 33 的应用不会触发 edge-to-edge 强制，targetSdk 35 的会。少数变更与 targetSdk 无关（如 16 KB 页大小是设备/系统层面的要求），要单独确认。

### 1.2 不升级 targetSdk 的后果

* **无法更新**：Google Play 对 targetSdk 有硬性下限，低于下限的新包与更新直接拒收，已有包也不能再发版。
* **可能被下架**：超过宽限期仍未达标的存量应用，Play 会限制可见性，国内各商店跟进时间与规则不同（以各商店公告为准）。
* **错过安全与隐私修复**：新系统的大多数隐私保护、权限收紧都挂在 targetSdk 门槛上，不升级等于主动留在旧行为里。
* **反而更容易崩**：系统的兼容开关（compat change）只覆盖有限窗口，旧 targetSdk 在新系统上会吃到"无开关"的底层变更。

### 1.3 官方时间表（面试要能报出来）

| 时间点 | 要求 |
| --- | --- |
| 2025-08-31 起 | Google Play 新应用与应用更新 `targetSdk` ≥ 35（Android 15） |
| 2025-11-01 起 | 含 native 代码且 `targetSdk` ≥ 35 的应用/游戏，必须支持 16 KB 页大小（可申请延期） |
| 2026-08-31 起 | Google Play 新应用与应用更新 `targetSdk` ≥ 36（Android 16） |

Android 16 对应 API 36，2025 年发布。以上条款的细则与延期政策以 [Google Play 的 targetSdk 要求](https://support.google.com/googleplay/android-developer/answer/11926878) 与官方文档为准。

## 2 各版本关键行为变更

| 版本 | API 级别 | 主题词 |
| --- | --- | --- |
| 6.0 | 23 | 运行时权限、Doze |
| 7.0 | 24 | FileProvider、多窗口 |
| 8.0 | 26 | 后台限制、通知渠道 |
| 9 | 28 | 明文流量、非 SDK 接口 |
| 10 | 29 | 分区存储、后台启动 Activity |
| 11 | 30 | 分区存储强制、包可见性 |
| 12 | 31 / 32 | SplashScreen、exported、PendingIntent |
| 13 | 33 | 通知权限、照片选择器 |
| 14 | 34 | 前台服务类型、精确闹钟 |
| 15 | 35 | edge-to-edge、16 KB、前台服务超时 |
| 16 | 36 | edge-to-edge 收口、大屏自适应 |

下面只列面试与线上事故高发的变更，完整清单以官方 [Behavior Changes](https://developer.android.com/about/versions) 为准。

### 2.1 Android 6.0（API 23）

| 变更点 | 影响 | 适配做法 |
| --- | --- | --- |
| 运行时权限 | 危险权限不再安装时授予，未授予就调用会抛 `SecurityException` 或拿到空数据 | 调用点先 `ContextCompat.checkSelfPermission`；用 `ActivityResultContracts.RequestPermission` 请求；区分"拒绝"与"拒绝并不再询问"（`shouldShowRequestPermissionRationale` 为 false），后者引导到设置页 |
| Doze 与 App Standby | 灭屏、静止、未充电时进入 Doze，网络访问与 Alarm 被推迟到维护窗口 | 周期任务改用 `WorkManager`/`JobScheduler`；必须准时的用 `setExactAndAllowWhileIdle`；实时性要求高的走高优先级 FCM；长任务用前台服务 |
| Apache HttpClient 移除 | 编译期就报错 | 换 OkHttp 或 `HttpURLConnection` |
| BLE 扫描需定位权限 | 无定位权限时扫不到设备（且返回空而不报错） | 6.0~11 申请 `ACCESS_COARSE_LOCATION`，12 起改用 `BLUETOOTH_SCAN` |

### 2.2 Android 7.0（API 24）

| 变更点 | 影响 | 适配做法 |
| --- | --- | --- |
| FileProvider（`FileUriExposedException`） | 用 `file://` 通过 Intent 传文件给别的应用直接崩溃（相机、裁剪、安装 APK 最典型） | 声明 `FileProvider` + `file_paths.xml`，改成 `content://`，Intent 加 `FLAG_GRANT_READ_URI_PERMISSION`；相机 `EXTRA_OUTPUT`、APK 安装 `ACTION_INSTALL_PACKAGE` 都要换 |
| 多窗口 | 可调整大小的窗口里 `screenOrientation` 被忽略；可见但失焦的 Activity 只走 `onPause` 不走 `onStop` | `onMultiWindowModeChanged` / `isInMultiWindowMode` 里暂停视频；布局避免写死高度；状态保存放 `onPause` 也要能用；`android:resizeableActivity` 按需关闭 |
| 隐式广播 `CONNECTIVITY_ACTION` | target 24 起，清单注册的后台应用收不到 | 改用 `registerDefaultNetworkCallback`，或前台动态注册 |
| Doze 增强（on the go） | 熄屏移动中也会进入 Doze，后台网络更不可靠 | 同上：任务调度统一收到 `WorkManager`，不要靠隐式广播拉起 |
| 通知直接回复 / `MessagingStyle` | 不升级不崩，但体验落后 | 用 `RemoteInput` + `MessagingStyle` 做通知内回复 |

### 2.3 Android 8.0（API 26）

| 变更点 | 影响 | 适配做法 |
| --- | --- | --- |
| 后台 Service 限制 | 后台 `startService` 抛 `IllegalStateException`；`startForegroundService` 后 5 秒内没 `startForeground` 会抛 `RemoteServiceException` | 判断前后台：前台用 `startForegroundService` + 立即 `startForeground`（带渠道）；可延迟的任务用 `WorkManager`/`JobScheduler`；`IntentService` 在 8.0 上行为不可靠 |
| 通知渠道 | target 26 未创建渠道，通知**完全不展示**；渠道创建后 importance、声音不可修改（只能引导用户去设置） | 在 `Application` 里幂等 `createNotificationChannel`；按业务规划渠道 ID 与等级；改等级要换新渠道 ID |
| 广播限制 | 清单注册的隐式广播大多不再投递（豁免列表除外） | 动态注册、显式广播、`JobScheduler` 替代；不要依赖 `ACTION_*` 唤醒 |
| 自适应图标 | 桌面图标被裁成白底方块/圆形，观感差 | `mipmap-anydpi-v26/ic_launcher.xml` 配前景/背景层，另加 `roundIcon` |
| 后台位置与传感器限制 | 后台定位更新频率被限制 | 定位放前台服务，声明 `foregroundServiceType="location"` |

### 2.4 Android 9（API 28）

| 变更点 | 影响 | 适配做法 |
| --- | --- | --- |
| 明文流量默认禁止 | target 28 起 `http://` 请求失败，报 `CLEARTEXT communication to ... not permitted` | 全站 HTTPS；必须保留的域名写 `network_security_config.xml`，用 `cleartextTrafficPermitted` 精确白名单，不要全局开 |
| 非 SDK 接口限制 | 反射/JNI 访问灰名单 API 打警告，黑名单直接抛异常 | 换公开 API；用 `StrictMode.detectNonSdkApiUsage` 或 veridex 扫描；详见 `Android9.0非SDK接口限制.md` |
| `FOREGROUND_SERVICE` 权限 | target 28 起前台服务需要该普通权限 | 清单声明 `<uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>` |
| 设备标识 | `Build.SERIAL` 需 `READ_PHONE_STATE` 且值不稳定；`getImei` 逐步收紧 | 用 `Settings.Secure.ANDROID_ID` 或自建 UUID，不要拿 IMEI/MAC 做唯一标识 |
| 后台相机/麦克风/传感器 | 后台应用访问被拒或返回空 | 相关能力放前台服务，并遵守"使用时"限制 |
| SQLite 兼容 WAL 默认开启 | 多线程读写行为变化，极端场景出现锁等待 | 单写多读、写操作串行化，避免跨线程复用同一 `SQLiteDatabase` 连接 |
| 刘海屏 | 内容被 `displayCutout` 遮挡 | `layoutInDisplayCutoutMode` + `WindowInsets` 处理 |

### 2.5 Android 10（API 29）

| 变更点 | 影响 | 适配做法 |
| --- | --- | --- |
| 分区存储（可 opt-out） | 共享目录任意路径读写受限，`WRITE_EXTERNAL_STORAGE` 基本失效 | 迁移到 `MediaStore`（写入用 `IS_PENDING`）或 SAF；过渡期可 `requestLegacyExternalStorage="true"`，但仅对 target ≤ 29 有效 |
| 后台启动 Activity 限制 | 后台应用 `startActivity` 被静默拦截 | 用全屏通知 `fullScreenIntent`（需 `USE_FULL_SCREEN_INTENT`）；回到前台再跳；`AlarmManager` 全屏 Intent 也要走通知 |
| 深色主题 | 硬编码色值在深色下不可读 | `values-night` 资源 + `DayNight` 主题；图片用 `forceDarkAllowed` 控制；同时验证 `uiMode` 变化时的重建 |
| 设备标识符 | `getImei()` 需系统级 `READ_PRIVILEGED_PHONE_STATE`，普通应用拿不到 | 同 9：`ANDROID_ID` / 自建 ID |
| 手势导航 | 底部/侧边手势区与滑动控件冲突，系统栏高度变化 | `WindowInsets` 动态取高度；必要控件用 `setSystemGestureExclusionRects` 排除手势区 |
| 引入 `foregroundServiceType` | 后台定位需要类型声明 | 清单声明 `location` 类型，配合 `ACCESS_BACKGROUND_LOCATION` |

### 2.6 Android 11（API 30）

| 变更点 | 影响 | 适配做法 |
| --- | --- | --- |
| 分区存储强制 | target 30 起 `requestLegacyExternalStorage` 直接失效；直接路径访问共享文件受限 | 全面走 `MediaStore`/SAF；确需全盘访问的申请 `MANAGE_EXTERNAL_STORAGE`（特殊权限，商店审核严格） |
| 包可见性（`<queries>`） | `queryIntentActivities`、`getPackageInfo` 只返回"可见"的包，检测微信/支付宝、判断应用是否安装全部失效 | 清单加 `<queries>`（`<package>`、`<intent>`、`<provider>` 三种写法）；`QUERY_ALL_PACKAGES` 只在极少数场景且需过审 |
| 一次性权限 | 位置、麦克风、相机可被授予"仅这一次"，回到后台后自动回收 | 每次使用前检查权限；不要假设授权长期有效；处理"授权被回收"后的降级 |
| 权限自动重置 | 长期未使用的应用权限被自动重置 | 启动时校验权限并重新引导；target 30 起重置还会杀掉进程 |
| 前台服务类型（`camera`/`microphone`）限制 | 后台启动的前台服务不能使用相机/麦克风 | 在前台时启动并立即使用；类型用 `camera`/`microphone` 且满足"使用时"条件 |
| 后台定位授权 | target 30 起权限对话框不再提供"始终允许"，需去设置页 | 分两步申请：先前台定位，再解释并跳转设置；`ACCESS_BACKGROUND_LOCATION` 单独请求 |
| Toast 自定义 View | 后台应用的自定义 Toast 被禁用 | 用系统 Toast 或通知 |

### 2.7 Android 12（API 31 / 32）

| 变更点 | 影响 | 适配做法 |
| --- | --- | --- |
| SplashScreen | 冷/热启动统一显示系统启动画面，自定义 `windowBackground` 做启动图的方式失效（会被拉伸或出现双闪） | 用 `androidx.core:core-splashscreen` 的 `installSplashScreen()`（兼容到低版本）；主题配 `windowSplashScreenBackground`、`windowSplashScreenAnimatedIcon`、`postSplashScreenTheme`；用 `setKeepOnScreenCondition` 控制停留 |
| 大致位置 | 用户可只给模糊位置，`ACCESS_FINE_LOCATION` 申请后可能只授到 coarse | fine 与 coarse 一起申请；按"实际授予的精度"分支处理；定位结果精度降级时提示用户 |
| PendingIntent 可变性 | target 31 起必须显式 `FLAG_IMMUTABLE` 或 `FLAG_MUTABLE`，否则抛 `IllegalArgumentException` | 默认 `FLAG_IMMUTABLE`；只有需要系统回填 extras（通知、`AlarmManager`、`RemoteInput`）才用 `FLAG_MUTABLE` |
| `android:exported` 必填 | 带 `intent-filter` 的组件不写 `exported` 会导致构建/安装失败 | 四个组件逐个声明；默认 `false`，确实要被外部调起才 `true`；注意 launcher Activity 必须 `true` |
| 蓝牙权限拆分 | `BLUETOOTH`/`BLUETOOTH_ADMIN` 在 31+ 不再覆盖扫描/连接 | 12+ 申请 `BLUETOOTH_SCAN`/`BLUETOOTH_CONNECT`/`BLUETOOTH_ADVERTISE`；配 `usesPermissionFlags="neverForLocation"`；低版本走旧权限分支 |
| 精确闹钟 | `SCHEDULE_EXACT_ALARM` 是特殊权限，未授予时 `setExact*` 抛 `SecurityException` | `canScheduleExactAlarms()` 判断，未授予用 `setWindow` 降级或引导 `ACTION_REQUEST_SCHEDULE_EXACT_ALARM` |
| 通知 trampoline 限制 | 点击通知后经 Service/Receiver 间接启动 Activity 被拦 | `PendingIntent` 直接 `getActivity` 指向目标页 |
| 应用休眠（Hibernation） | 长期不用被休眠，任务、通知、权限全部停用 | 用 `ACTION_APPLICATION_DETAILS_SETTINGS` 引导唤醒；不要依赖后台常驻 |

### 2.8 Android 13（API 33）

| 变更点 | 影响 | 适配做法 |
| --- | --- | --- |
| `POST_NOTIFICATIONS` 运行时权限 | target 33 未授权时通知不展示；系统在创建首个渠道时会弹权限框 | 在"用户能理解为什么要通知"的时机主动请求；`NotificationManagerCompat.areNotificationsEnabled()` 判断；被拒后降级为应用内提醒 |
| 照片选择器 | 不需要媒体权限即可选图，但入口与回调变了 | 用 `ActivityResultContracts.PickVisualMedia` / `ACTION_PICK_IMAGES`；低版本由 Play 服务回移（以官方文档为准） |
| 按应用语言 | 用户可单独设置某应用语言，系统会重启应用 | 声明 `android:localeConfig`；用 `LocaleManager`/`AppCompatDelegate.setApplicationLocales` 切语言 |
| 主题图标 | 不支持 `monochrome` 时无法跟随壁纸主题 | 自适应图标里加 `<monochrome>` 图层 |
| 媒体权限拆分 | `READ_EXTERNAL_STORAGE` 在 33+ 对新应用无效，改用 `READ_MEDIA_IMAGES/VIDEO/AUDIO` | 按 `Build.VERSION` 分支申请；只申请实际需要的媒体类型 |
| `NEARBY_WIFI_DEVICES` | Wi-Fi 相关 API 不再借用定位权限 | 声明该权限并加 `neverForLocation` |
| 剪贴板 | 复制内容会被系统预览，敏感数据暴露 | `ClipDescription.EXTRA_IS_SENSITIVE` 标记敏感内容 |

### 2.9 Android 14（API 34）

| 变更点 | 影响 | 适配做法 |
| --- | --- | --- |
| 前台服务类型必填 | 未声明 `android:foregroundServiceType` 或缺少对应权限，`startForeground` 抛 `MissingForegroundServiceTypeException`/`SecurityException` | 清单写类型，并加 `FOREGROUND_SERVICE_DATA_SYNC`、`FOREGROUND_SERVICE_MEDIA_PLAYBACK`、`FOREGROUND_SERVICE_CAMERA` 等配套权限；类型必须与真实用途一致（上架会查） |
| 精确闹钟默认拒绝 | 新安装且 target ≥ 33 的应用默认不授予 `SCHEDULE_EXACT_ALARM` | `canScheduleExactAlarms()` 先判断；闹钟/日历类可用 `USE_EXACT_ALARM`（需商店声明），其余降级到 `setWindow`/`WorkManager` |
| 部分照片访问 | 用户可只授权"选中的照片"，返回的是临时授权 | 处理 `READ_MEDIA_VISUAL_USER_SELECTED`；每轮都允许"重新选择"；不要假设能遍历整个相册 |
| 动态注册广播必须声明导出 | `registerReceiver` 不传 `RECEIVER_EXPORTED`/`RECEIVER_NOT_EXPORTED` 抛 `SecurityException` | 只收系统/自家广播用 `RECEIVER_NOT_EXPORTED`；确实要收外部广播才 `RECEIVER_EXPORTED` |
| 隐式 Intent 限制 | 指向内部组件的隐式 Intent 被系统拦截 | 显式 `setComponent`/`setPackage`，或改成 `Intent(context, XxxActivity::class.java)` |
| `PendingIntent` 可变 + 隐式 Intent | 组合非法，创建时抛异常 | 显式 Intent，或改用 `FLAG_IMMUTABLE` |
| 全屏 Intent 收紧 | `USE_FULL_SCREEN_INTENT` 仅通话/闹钟类默认可用，其余需用户授权 | 非通话/闹钟场景改普通通知，引导用户在设置里授予 |
| targetSdk < 23 无法安装 | 老包装不上 | 提升 `minSdk`/`targetSdk` |

### 2.10 Android 15（API 35）

| 变更点 | 影响 | 适配做法 |
| --- | --- | --- |
| edge-to-edge 强制 | target 35 起窗口默认不再为系统栏留白，状态栏/导航栏透明，内容被遮挡 | `enableEdgeToEdge()` 或 `WindowCompat.setDecorFitsSystemWindows(window, false)`；根布局用 `ViewCompat.setOnApplyWindowInsetsListener` 取 `systemBars` + `displayCutout` insets 加 padding；`fitsSystemWindows` 在复杂布局里不可靠 |
| 16 KB 页大小 | 4 KB 假设的 native 库可能加载失败或崩溃 | 见第 3 节 |
| 前台服务超时 | `dataSync` 类型 24 小时内累计最多 6 小时，`mediaProcessing` 最多 6 小时；超时回调 `onTimeout(startId, fgsType)` | 在 `onTimeout` 里保存进度并 `stopSelf()`，否则系统抛异常；长任务改成分片 + `WorkManager`，或改类型 |
| 后台启动 Activity 再收紧 | `SYSTEM_ALERT_WINDOW` 等旧例外被移除；`PendingIntent` 启动 Activity 需创建方显式 opt-in | `ActivityOptions.setPendingIntentBackgroundActivityStartMode` 显式允许；产品层面尽量不后台弹页 |
| `elegantTextHeight` 默认 true | 文本高度/行高变化，截断位置偏移 | 固定行高或用 `lineHeight`，UI 回归时重点看列表项高度 |

### 2.11 Android 16（API 36）

| 变更点 | 影响 | 适配做法 |
| --- | --- | --- |
| edge-to-edge 强制（去掉 opt-out） | target 36 起 `windowOptOutEdgeToEdgeEnforcement` 失效，15 上用"关闭开关"糊过去的地方会重新暴露 | 按 15 的方案彻底处理 insets，检查沉浸式页面、视频全屏、底部输入框顶起；同时验证三键导航与手势导航 |
| 大屏自适应 | 在 `smallestWidth ≥ 600dp` 的大屏上，系统忽略方向限制、`resizeableActivity=false` 与宽高比限制，应用被强制可调整大小 | 用 `WindowSizeClass` 做响应式布局（列表-详情两栏）；不要依赖竖屏锁定；`onConfigurationChanged` 要能正确处理尺寸变化；极端比例下避免内容被裁 |
| 16 KB 页大小强制 | 16 KB 设备与 Play 要求全面落地 | 见第 3 节 |
| 其他行为变更 | 通知冷却（同一应用连续通知被合并降噪）、预测性返回默认启用、后台任务与精确闹钟配额调整等 | 逐条对照官方 Behavior Changes 清单，重点回归通知与返回手势；`onBackPressed` 迁移到 `OnBackPressedCallback` |

大屏自适应的兼容开关属性名、以及"其他行为变更"的最终范围以官方文档为准。

## 3 16 KB 页大小适配

### 3.1 背景：为什么从 4 KB 提到 16 KB

* 内存以页（page）为最小管理单位，`mmap`、缺页、TLB 缓存都按页工作，页大小由内核在编译时决定（ARM64 支持 4 KB / 16 KB / 64 KB）。
* 页更大 → **TLB 能覆盖更多内存**，缺页次数和页表遍历减少，内存压力下系统更从容；对大内存设备尤其明显。
* 代价是**内部碎片变大**、小文件/小内存分配更浪费，所以只在 64 位大内存设备上启用。
* Android 15 起系统开始支持 16 KB 页大小的设备（先在开发者选项/模拟器镜像里提供），Android 16 上进一步铺开；Play 从 2025-11-01 起对含 native 代码的应用做硬性要求。
* 收益的具体数字官方有说明（应用启动、内存回收等），细节以官方文档为准。

### 3.2 影响面

| 受影响项 | 具体要求 | 不满足的后果 |
| --- | --- | --- |
| ELF `LOAD` 段对齐 | `.so` 的 `p_align` 必须是 16384（0x4000）或 16 KB 的整数倍 | 库加载失败（`dlopen` 报错），或运行期随机崩溃 |
| APK 内未压缩 `.so` | `useLegacyPackaging = false` 时，zip 内 `.so` 需 16 KB 对齐（`zipalign -P 16`） | 安装后无法 `mmap` 加载，启动即崩 |
| NDK 版本 | NDK r28 起默认按 16 KB 对齐；r27 可加 `-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON` | 旧 NDK 编出的库全部不合格 |
| AGP 版本 | AGP 8.5.1+ 会自动对未压缩 `.so` 做 16 KB 对齐 | 旧 AGP 打出的包对齐错误 |
| 代码假设 | 硬编码 4096 的偏移、缓冲区、`mmap` 长度会算错 | 越界/`SIGSEGV`，且只在 16 KB 设备复现 |
| 三方 SDK | 预编译 `.so` 由厂商提供，自己无法重编 | 只能等厂商更新，或换库/去掉依赖 |

### 3.3 检查命令

```bash
# 1. 检查 APK 的 zip 对齐（-P 16 表示按 16 KB 对齐，4 是 zipalign 的版本号）
zipalign -c -P 16 -v 4 app-release.apk

# 2. 检查单个 .so 的 ELF LOAD 段对齐：看 Align 列，期望 0x4000
#    Align = 0x1000 表示还是 4 KB 对齐，不合格
readelf -lW lib/arm64-v8a/libnative.so | grep LOAD

# 3. 没有 readelf 时用 NDK 自带的 llvm-readelf / llvm-objdump
$ANDROID_NDK/toolchains/llvm/prebuilt/*/bin/llvm-readelf -lW libnative.so

# 4. 批量检查 APK 里所有 .so：每行列出一个 LOAD 段，p_align 应为 0x4000
mkdir -p /tmp/so && unzip -o -q app-release.apk 'lib/*/*.so' -d /tmp/so
find /tmp/so -name '*.so' -exec sh -c 'echo "== $1"; readelf -lW "$1" | grep LOAD' _ {} \;

# 5. 在 16 KB 环境里做真机/模拟器验证（Android 15+ 提供 16 KB 镜像）
adb shell getconf PAGE_SIZE   # 期望输出 16384
adb install app-release.apk   # 能装能启动，才算真正通过
```

### 3.4 修复方式

* **升级工具链**：NDK 升到 r28+，AGP 升到 8.5.1+，`compileSdk`/`targetSdk` 跟到 35/36，然后**重新编译全部 `.so`**（含 `androidTest`、`jniLibs` 里手工放的库）。
* **显式链接参数**（旧 NDK / 自建 CMake 工程兜底）：`-Wl,-z,max-page-size=16384`。
* **改代码假设**：所有页大小用 `sysconf(_SC_PAGESIZE)` / `getpagesize()` 取，禁止写死 4096。
* **检查三方库**：`jniLibs`、aar 里的 `.so` 逐个跑 3.3 的检查；不支持的联系厂商升级，升级不了就评估替换。
* **打包配置**：`jniLibs.useLegacyPackaging = false`（不压缩，直接 mmap）；若必须压缩，用 `true` 但体积和启动都变差，且仍要保证 ELF 对齐。

```kotlin
// app/build.gradle.kts
android {
    compileSdk = 36
    ndkVersion = "28.2.13676358" // 以本机实际安装的 r28+ 版本为准

    defaultConfig {
        targetSdk = 36
        externalNativeBuild {
            cmake {
                // NDK r28 默认已开启；r27 需要显式打开
                arguments += listOf("-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON")
            }
        }
    }

    packaging {
        jniLibs {
            // 不压缩 .so：16 KB 对齐的前提，也利于按需 mmap
            useLegacyPackaging = false
        }
    }
}
```

### 3.5 Play 的时间要求

| 时间点 | 要求 |
| --- | --- |
| 2025-11-01 起 | 含 native 代码、且 `targetSdk` ≥ 35 的**新包与更新**必须支持 16 KB 页大小，否则 Play 拒收 |
| 可延期 | 无法按期完成的可提交延期申请，理由与新的时间点以 Play 后台公告为准 |
| 2026-08-31 起 | `targetSdk` ≥ 36，16 KB 要求继续叠加 |

自查顺序建议：`zipalign -c -P 16` → 全量 `.so` 的 `readelf` 对齐 → 16 KB 模拟器跑核心链路 → 再提审。官方说明见 [16 KB page sizes](https://developer.android.com/guide/practices/page-sizes)。

## 4 版本适配清单（面试可直接背）

| 分类 | 版本 | 变更 | 一句话做法 |
| --- | --- | --- | --- |
| 权限 | 6.0 | 运行时权限 | 调用点 check + 请求，处理"不再询问" |
| 权限 | 11 | 一次性权限 / 自动重置 | 每次用前校验，不做长期假设 |
| 权限 | 12 | 大致位置 | fine+coarse 一起申请，按实际精度分支 |
| 权限 | 13 | `POST_NOTIFICATIONS` | 合适时机请求，被拒降级应用内提醒 |
| 权限 | 14 | 部分照片访问 | 支持"选中的照片"与重新选择 |
| 存储 | 7.0 | `FileUriExposedException` | FileProvider + `content://` + 读权限 Flag |
| 存储 | 10 | 分区存储（可 opt-out） | `requestLegacyExternalStorage` 过渡，迁 MediaStore/SAF |
| 存储 | 11 | 分区存储强制 | 全面 MediaStore/SAF，慎用 `MANAGE_EXTERNAL_STORAGE` |
| 存储 | 13 | 媒体权限拆分 | `READ_MEDIA_IMAGES/VIDEO/AUDIO` |
| 存储 | 14 | 部分照片访问 | 同上，处理临时授权 |
| 后台 | 6.0 | Doze | `WorkManager`、`setExactAndAllowWhileIdle`、FCM |
| 后台 | 8.0 | 后台 Service/广播限制 | FGS 或 JobScheduler，隐式广播改动态注册 |
| 后台 | 9 | 后台相机/麦克风限制 | 使用期内的前台服务 |
| 后台 | 10 | 后台启动 Activity 限制 | 全屏通知，回前台再跳 |
| 后台 | 15 | 后台启动 Activity 再收紧 | `PendingIntent` 创建方显式 opt-in |
| 通知 | 8.0 | 通知渠道 | Application 里幂等建渠道，等级设计好 |
| 通知 | 13 | 通知运行时权限 | 同上，权限 + 渠道双检查 |
| 通知 | 16 | 通知冷却 | 合并/降低连续通知频率 |
| 前台服务 | 9 | `FOREGROUND_SERVICE` 权限 | 清单声明 |
| 前台服务 | 10 | `foregroundServiceType` | 声明 `location` 等类型 |
| 前台服务 | 11 | 相机/麦克风使用限制 | 前台启动，类型匹配用途 |
| 前台服务 | 14 | 类型必填 + 配套权限 | 类型与用途一致，补齐 `FOREGROUND_SERVICE_*` |
| 前台服务 | 15 | `dataSync`/`mediaProcessing` 超时 | `onTimeout` 存进度并 `stopSelf`，任务分片 |
| 大屏 | 7.0 | 多窗口 | `resizeableActivity`、响应式布局、生命周期适配 |
| 大屏 | 15 | edge-to-edge 强制 | `enableEdgeToEdge` + insets 处理 |
| 大屏 | 16 | 大屏忽略方向/固定尺寸 | `WindowSizeClass` 两栏布局，不锁方向 |
| 安全 | 9 | 明文流量默认禁止 | HTTPS + `networkSecurityConfig` 白名单 |
| 安全 | 9 | 非 SDK 接口限制 | 换公开 API，StrictMode 自检 |
| 安全 | 12 | `exported` 必填 | 组件逐个声明，默认 false |
| 安全 | 12 | `PendingIntent` 可变性 | 默认 `FLAG_IMMUTABLE` |
| 安全 | 14 | 动态注册广播声明导出 | `RECEIVER_NOT_EXPORTED` 优先 |
| 安全 | 14 | 隐式 Intent 拦截 | 显式 `setComponent`/`setPackage` |
| 打包 | 15 / 16 | 16 KB 页大小 | NDK r28+、AGP 8.5.1+、`zipalign -P 16` 验证 |

## 5 面试问答

### Q1 targetSdk 升级要注意什么？

* 先看**官方 Behavior Changes 清单**，按 targetSdk 筛出"target ≥ N 才生效"的条目，逐条评估影响面。
* 重点四类：权限（新增运行时权限）、存储（分区存储/媒体权限）、后台（Service/广播/Activity 启动）、组件安全（`exported`、`PendingIntent` 可变性）。
* 升级顺序：`compileSdk` → `targetSdk` 灰度，配 `debuggable` 包在各系统版本真机回归。
* 大版本升级常伴随"强制"项（如 14 前台服务类型必填），要先改完再提测，否则线上必崩。
* 最后对齐商店时间表：2025-08-31 起需 ≥ 35，2026-08-31 起需 ≥ 36。

### Q2 Android 12 的 SplashScreen 怎么适配？

* 12 起系统统一接管启动画面：`windowBackground` 做启动图会失效，容易双闪或拉伸。
* 接入 `androidx.core:core-splashscreen`，在 `onCreate` 前 `installSplashScreen()`，低版本也能统一表现。
* 主题三件套：`windowSplashScreenBackground`（背景）、`windowSplashScreenAnimatedIcon`（图标，注意 2/3 安全区）、`postSplashScreenTheme`（启动后主题）。
* 需要等数据再进首页用 `setKeepOnScreenCondition { !ready }`，别在启动图里做重活。
* 退场动画用 `setOnExitAnimationListener` 自定义；老项目要把 `windowBackground` 里的启动图删掉。

### Q3 Android 13 的通知权限怎么处理？

* 新增运行时权限 `POST_NOTIFICATIONS`，target 33 未授权则通知完全不展示。
* 时机比"冷启动就要"重要：在用户开启某个提醒功能时请求，说明收益。
* 先判断 `NotificationManagerCompat.areNotificationsEnabled()`，再决定请求还是引导设置页。
* 注意系统也会在创建首个渠道时弹框，避免和自家弹框撞车。
* 被拒后降级：应用内红点/横幅兜底，并提供去设置页的入口。

### Q4 Android 14 的前台服务类型怎么改？

* 14 起 `startForeground` 必须匹配清单里的 `android:foregroundServiceType`，否则抛 `MissingForegroundServiceTypeException`。
* 每个类型还有配套权限，如 `dataSync` 要 `FOREGROUND_SERVICE_DATA_SYNC`，`mediaPlayback` 要 `FOREGROUND_SERVICE_MEDIA_PLAYBACK`。
* 类型必须与真实用途一致：定位只能用 `location`，录音用 `microphone`，上架审核会核对。
* 15 起 `dataSync`（24 小时内累计 6 小时）、`mediaProcessing`（6 小时）会超时，要处理 `onTimeout`。
* 能用 `WorkManager` 解决的别用 FGS，减少审核与超时风险。

### Q5 Android 15 的 edge-to-edge 怎么适配？

* target 35 起窗口默认 `setDecorFitsSystemWindows(false)`，内容绘制到状态栏/导航栏下面。
* 用 `enableEdgeToEdge()`（androidx activity 1.8+）一行开启，并统一状态栏图标明暗（`isAppearanceLightStatusBars`）。
* 根布局用 `ViewCompat.setOnApplyWindowInsetsListener` 取 `systemBars()` 与 `displayCutout()`，分别加 padding，不要只加 top。
* 列表/滚动页要 `clipToPadding=false`，让内容能滑到系统栏下面；输入框页面要处理 IME insets（`ime()`）。
* 别再用 `fitsSystemWindows` 和写死的 `statusBarHeight`；16 起 15 的 opt-out 属性失效。

### Q6 16 KB 页大小是什么，怎么检查？

* 系统内存按页管理，Android 长期用 4 KB 页，新设备改用 16 KB 以提升 TLB 命中、降低缺页开销。
* 影响的是 native 层：`.so` 的 ELF `LOAD` 段必须 16 KB 对齐，APK 里未压缩 `.so` 的 zip 对齐也要 16 KB。
* 检查：`zipalign -c -P 16 -v 4 app.apk` 看 zip 对齐，`readelf -lW lib.so` 看 `p_align` 是否 `0x4000`。
* 修复：NDK r28+、AGP 8.5.1+ 重编全部 `.so`（含三方库），页大小用 `getpagesize()` 而非 4096。
* 时间点：2025-11-01 起，含 native 代码且 targetSdk ≥ 35 的新包与更新必须支持，可申请延期。

### Q7 分区存储怎么适配，10 和 11 有什么区别？

* 10 是"可退出"：target ≤ 29 可 `requestLegacyExternalStorage="true"` 继续用老路径。
* 11 是"强制"：target 30 起该属性直接失效，必须走 `MediaStore` 或 SAF。
* 写媒体用 `MediaStore` + `IS_PENDING`，写完清标记，避免半成品被扫到。
* 自己的文件放 `getExternalFilesDir()`，无需权限、卸载即清；跨应用共享用 SAF 拿持久化 URI 授权。
* 确实需要全盘访问才申请 `MANAGE_EXTERNAL_STORAGE`，属特殊权限，商店审核严格。

### Q8 为什么 7.0 之后要用 FileProvider？

* 7.0 起把 `file://` URI 暴露给其他应用会抛 `FileUriExposedException`，防止泄露私有路径。
* 用 `FileProvider` 把文件映射成 `content://`，通过 `<provider>` + `file_paths.xml` 配置可共享目录。
* 传 Intent 时要加 `FLAG_GRANT_READ_URI_PERMISSION`（写则 `WRITE`），否则对方无权限读。
* 典型场景：拍照 `EXTRA_OUTPUT`、裁剪、APK 安装、分享文件，全都必须换。
* 自检可开 `StrictMode.detectFileUriExposure()`，测试期直接暴露问题。

### Q9 PendingIntent 为什么必须指定可变性？

* 12 起 target 31 必须显式 `FLAG_IMMUTABLE` 或 `FLAG_MUTABLE`，否则创建时抛 `IllegalArgumentException`。
* 原则：默认不可变，防止其他应用篡改 Intent 里的 extras/action 造成越权。
* 只有需要系统或发送方回填数据时才用可变，如通知的 `RemoteInput`、`AlarmManager` 的部分场景。
* 14 起"可变 + 隐式 Intent"组合直接非法，必须显式指定组件。
* 顺带：14 起带 `intent-filter` 的组件必须写 `android:exported`，两个问题常一起出现。

### Q10 后台 Service 被限制后，长任务怎么做？

* 8.0 起后台 `startService` 抛异常，必须 `startForegroundService` 并在 5 秒内 `startForeground`。
* 可延迟、可断点续跑的任务用 `WorkManager`，带约束（网络、充电）更省电。
* 用户可感知的持续任务（导航、播放、录音）才用前台服务，且要声明正确类型。
* 15 起 `dataSync`、`mediaProcessing` 有 6 小时上限，超时会回调 `onTimeout`，必须存进度并退出。
* 不要用"双进程守护/1 像素 Activity"绕过，新系统会直接拦或掉电更快。

### Q11 包可见性 `<queries>` 是什么？

* 11 起应用默认只能看到"自己 + 系统 + 有交互"的包，`queryIntentActivities` 等接口返回被过滤。
* 需要在清单里用 `<queries>` 声明要查询的包名、Intent 签名或 provider authority。
* 不声明就检测不到微信/支付宝是否安装，`PackageManager` 相关逻辑会静默失效。
* `QUERY_ALL_PACKAGES` 能一次放开，但属敏感权限，Play 审核要求说明必要性。
* 注意：`startActivity` 隐式启动通常仍可用，被限制的是"查询"，别一概而论。

### Q12 精确闹钟权限被拒了怎么降级？

* 12 引入 `SCHEDULE_EXACT_ALARM` 特殊权限，14 起新装且 target ≥ 33 默认不授予。
* 先 `alarmManager.canScheduleExactAlarms()` 判断，为 false 绝不直接 `setExact`（会抛 `SecurityException`）。
* 降级策略：`setWindow`（允许窗口内触发）或 `setAndAllowWhileIdle`，配合 `WorkManager` 做补偿。
* 真正的闹钟/日历类应用可申请 `USE_EXACT_ALARM`（安装即授予，但商店有类别限制）。
* 引导用户授权用 `ACTION_REQUEST_SCHEDULE_EXACT_ALARM`，并解释为什么需要准点。
