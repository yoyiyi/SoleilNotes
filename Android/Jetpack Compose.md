## 1 为什么有 Compose

Compose 是 Android 的声明式 UI 工具包，1.0 稳定版发布于 2021 年。它换的不是控件，而是描述界面的方式：界面是状态的函数，状态变化后由框架推导最小更新，不再手动找 View 改属性。

### 1.1 命令式 UI 的问题

* 状态散落在 View、Adapter、成员变量里，任何一处都能改界面，出问题难定位。
* 状态与视图手动同步，漏一行就"数据变了、界面没变"。
* 复用靠继承和 include；逻辑在代码、布局在 XML，两处维护，强依赖框架对象。

### 1.2 声明式 UI 的思想

* UI = f(state)：同样的状态应产出同样的描述（幂等）。
* 只描述"长什么样"，不描述"怎么改"，框架比较前后描述并应用差异。
* 组合优于继承：Composable 是普通函数，Modifier 链式描述样式与行为。

### 1.3 与 View 体系对比

| 维度 | View 体系 | Jetpack Compose |
| --- | --- | --- |
| 范式 | 命令式，手动改属性 | 声明式，UI = f(state) |
| 描述 | XML + 代码两处 | Kotlin 函数，单一来源 |
| 更新 | 拿到 View 再改属性 | 状态变化触发重组，框架算最小更新 |
| 状态 | 散落，手动同步 | 读到状态处自动订阅 |
| 复用 | 继承 View、include 布局 | @Composable 函数、Modifier |
| 布局 | MeasureSpec，weight 二次测量 | MeasurePolicy，单次测量为主 |
| 列表 | RecyclerView + Adapter | LazyColumn + item key |
| 测试 | Espresso、Robolectric | createComposeRule + 语义树 |

## 2 组合与重组

### 2.1 组合与组合树

* 组合（Composition）是首次执行 @Composable、生成 UI 描述的过程，产物是组合树。
* 运行时用 **SlotTable** 保存 group 位置、remember 的值与参数，重组按位置复用而不是重建。
* 每个 @Composable 调用在编译期被包成一个 group；重组就是重跑失效的 group。
* 组合树映射为 **LayoutNode** 树，由它测量、布局、绘制，全程没有 View 对象参与。

### 2.2 重组的触发与范围

* 触发一：组合中读取的 State 被写入，读取它的 scope 失效并调度重组。
* 触发二：父级重组后，子级参数不稳定或与旧值不等，无法跳过。
* 范围以 restartable 的 Composable 调用为界，只有真正读到状态的函数重跑。
* 重组可跳过、可同帧多次、可并行调度，所以必须幂等，不能依赖执行次数。

### 2.3 @Composable 的约束

* 只能在 @Composable 内调用（编译器注入 Composer 参数改写函数）。
* 不能声明为 suspend，需要协程时用 rememberCoroutineScope 或 effect API。
* 必须幂等、无副作用：写状态、发请求、注册监听都放到回调或 effect 里。
* 只有返回 Unit 的 Composable 才会被编译成 restartable / skippable。

### 2.4 remember 与 rememberSaveable

```kotlin
var keyword by rememberSaveable { mutableStateOf("") } // 跨配置变更、进程重建
val focusRequester = remember { FocusRequester() }    // 只跨重组
```

| 对比项 | remember | rememberSaveable |
| --- | --- | --- |
| 存活范围 | 跟随组合，离开即丢 | 组合 + 配置变更 + 进程重建 |
| 存储 | SlotTable（内存） | Bundle / SavedStateRegistry |
| 数据要求 | 任意对象 | 可被 Bundle 保存，或提供 Saver |
| 用途 | 派生状态、协程作用域 | 输入内容、选中项、滚动位置 |

## 3 状态管理

### 3.1 mutableStateOf 与 State

* `State<T>` 只读，`MutableState<T>` 可写，`mutableStateOf()` 返回后者，`by` 委托需导入 getValue/setValue。
* 读取 value 登记依赖，写入让依赖它的 scope 失效并调度重组。
* 集合用 `mutableStateListOf` / `mutableStateMapOf`；普通 List 增删元素不触发重组。

```kotlin
var count by remember { mutableIntStateOf(0) }
Text("count = $count")                       // 读取：订阅
Button(onClick = { count++ }) { Text("+1") } // 写入：事件回调
```

### 3.2 derivedStateOf

* 把"由其它 State 计算出的值"包成一个 State，只有结果变化才通知下游。
* 适合输入合法性、过滤后的列表、滚动后是否显示"回到顶部"；通常与 remember 配合。

```kotlin
val isValid by remember { derivedStateOf { text.length in 3..20 } } // 只在翻转时重组
```

### 3.3 状态提升与单向数据流

状态提升（state hoisting）是把状态移到调用方，子组件只留 `value` 和 `onValueChange`，变成无状态组件。

* 单一数据源，避免两份状态互相覆盖；子组件可预览、可测试、可复用。
* 数据向下、事件向上，形成单向数据流（UDF）。

| 状态持有者 | 生命周期 | 适合放什么 |
| --- | --- | --- |
| remember | 跟随组合 | 展开收起、临时草稿 |
| rememberSaveable | 组合 + 进程重建 | 输入内容、选中项 |
| ViewModel | Activity / NavBackStackEntry | 业务状态、请求、跨页面数据 |

### 3.4 collectAsStateWithLifecycle

* `collectAsState()` 只要组合存在就一直收集，页面退到后台仍在收，浪费资源。
* `collectAsStateWithLifecycle()` 按 Lifecycle 启停，STARTED 以上才收集，回前台重新订阅；依赖 `lifecycle-runtime-compose`。

## 4 副作用 API

组合应是纯函数，但请求数据、注册监听、打点必须发生。副作用 API 把它们绑定到组合生命周期，在正确时机执行与清理。

| API | 触发时机 | 挂起 | 清理 | 典型用途 |
| --- | --- | --- | --- | --- |
| LaunchedEffect(keys) | 首次进入、keys 变化时执行 | 是 | 协程取消 | 首次加载、延时、Snackbar |
| DisposableEffect(keys) | 首次进入、keys 变化时执行 | 否 | 必须写 onDispose | 注册/反注册监听、广播 |
| SideEffect | 每次成功重组并提交后 | 否 | 无 | 同步外部非 Compose 状态 |
| rememberCoroutineScope | 返回绑定组合的 scope | 否 | 离开组合自动取消 | onClick 里启动协程 |
| produceState | 首次进入启动协程，keys 变化重启 | 是 | 协程取消 | 非 Compose 数据源转 State |

```kotlin
@Composable
fun DetailScreen(id: Long) {
    // id 变化时取消旧协程并重新加载；传 Unit 表示只执行一次
    LaunchedEffect(id) { viewModel.load(id) }
    // 成对注册/反注册，onDispose 是唯一可靠的释放点，漏写就泄漏
    DisposableEffect(Unit) {
        val callback = NetworkCallback()
        onDispose { /* 反注册 */ }
    }
    // 每次重组提交后同步外部状态，不要在这里启动协程
    SideEffect { analytics.track("detail_$id") }
    // 点击里启动协程，作用域跟随组合
    val scope = rememberCoroutineScope()
    Button(onClick = { scope.launch { snackbar.showSnackbar("已刷新") } }) { Text("刷新") }
}
```

`produceState` 把回调式数据源适配成 State：`produceState<User?>(null, id) { value = repository.load(id) }`；`rememberUpdatedState` 让长跑 effect 读到最新 lambda 而不重启。

## 5 性能

### 5.1 重组优化

* 子组件要被跳过，需要参数稳定且与上次相等，否则父级重组会带着它一起重组。
* 状态读取范围越小越好：只读需要的字段，别让整个页面订阅整个 UiState。
* 组合可能被并行、中断、多次执行，所以 IO、解析、排序都要挪到 ViewModel 或 effect。
* 需要缓存用 `remember(key) { compute() }`；不要在组合函数体里写状态，容易死循环。

### 5.2 @Stable 与 @Immutable

```kotlin
@Immutable
data class UserUi(val id: Long, val name: String) // 全 val，equals 可比较

@Stable
class ExpandState {
    var expanded by mutableStateOf(false) // 变化会通知 Compose
}
```

* `@Immutable` 承诺对象不可变；`@Stable` 承诺 equals 稳定且属性变化会通知。
* List 接口实现可能可变，所以被视为不稳定；用 ImmutableList 或 @Immutable 包装类。
* 注解是承诺，乱标注解会导致数据变了界面不刷新。

### 5.3 key 与 LazyColumn 复用

* `items(repos, key = { it.id })` 给 item 稳定身份，`contentType` 让不同类 item 分开复用；不传 key 时用下标，插入、删除、排序会让状态错位。
* key 必须唯一且可被 Bundle 保存，不要用 index。
* LazyColumn 只组合可见项，滚出屏幕的被回收，滚回来靠 key + SaveableStateHolder 恢复。

### 5.4 derivedStateOf 减少重组

```kotlin
val listState = rememberLazyListState()
// 滚动时下标每帧都变，但布尔值只在翻转时才通知
val showTopBar by remember { derivedStateOf { listState.firstVisibleItemIndex > 0 } }
```

### 5.5 strong skipping mode

* Kotlin 2.0 起 Compose 编译器并入 Kotlin 仓库，以 `org.jetbrains.kotlin.plugin.compose` 插件随 Kotlin 发布。
* strong skipping mode 现已默认开启：不稳定参数也会被记忆化，lambda 自动 remember，并用引用相等（===）判断能否跳过；但内容相同、实例不同的对象仍会重组。

## 6 与 View 互操作

### 6.1 AndroidView：Compose 里放 View

```kotlin
@Composable
fun MapPane(center: LatLng, modifier: Modifier = Modifier) {
    AndroidView(
        modifier = modifier,
        factory = { context -> MapView(context) },   // 只执行一次
        update = { view -> view.moveCamera(center) } // 每次重组后执行
    )
}
```

factory 只建一次，update 每次重组后同步；`onRelease` 做释放，LazyColumn 里用 `onReset` 重置复用状态。

### 6.2 ComposeView：View 里放 Compose

在 Activity/Fragment 里用 `ComposeView(context).apply { setContent { App() } }` 局部嵌入，或直接把根布局换成 `setContent`；记得 `setViewCompositionStrategy` 与宿主对齐。

释放策略：Fragment 用 `DisposeOnViewTreeLifecycleDestroyed`，RecyclerView item 用 `DisposeOnDetachedFromWindowOrReleasedFromPool`，否则容易泄漏。

### 6.3 存量项目渐进接入

* 新页面先用 Compose，老页面保持 View，通过路由或 Fragment 衔接。
* 局部替换风险最小：把某个卡片、某个 item 换成 ComposeView。
* 共享 ViewModel：Compose 的 `viewModel()` 依赖 LocalViewModelStoreOwner，与 Fragment 保持一致才能拿到同一实例。

## 7 导航与架构

### 7.1 Navigation-Compose

```kotlin
NavHost(navController = rememberNavController(), startDestination = "repos") {
    composable("repos") {
        RepoScreen(onOpenDetail = { id -> navController.navigate("repo/$id") })
    }
    composable("repo/{id}") { entry ->
        val id = entry.arguments?.getString("id")?.toLongOrNull() ?: return@composable
        RepoDetailScreen(id)
    }
}
```

* 每个 destination 对应一个 NavBackStackEntry，`viewModel()` 默认绑定它，出栈即销毁，天然是页面级作用域。
* 新版支持类型安全路由（@Serializable 路由对象 + kotlinx.serialization），不必手拼字符串。

### 7.2 ViewModel + StateFlow 标准写法

| 角色 | 职责 |
| --- | --- |
| UiState | 描述界面所需全部数据，不可变 data class |
| Event | 用户意图，sealed interface |
| ViewModel | 处理事件、请求数据、更新 StateFlow |
| Composable | 渲染状态、上报事件，不含业务逻辑 |

一次性事件（导航、Snackbar）用 Channel + receiveAsFlow 避免重放；Compose 只"读状态、发事件"。

### 7.3 完整小例子：列表页

```kotlin
data class Repo(val id: Long, val name: String)
data class RepoUiState(val loading: Boolean = false, val repos: List<Repo> = emptyList(), val error: String? = null)
sealed interface RepoEvent { data object Refresh : RepoEvent; data class Click(val id: Long) : RepoEvent }

class RepoViewModel(private val repository: RepoRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(RepoUiState(loading = true))
    val uiState: StateFlow<RepoUiState> = _uiState.asStateFlow()
    private val _openDetail = Channel<Long>(Channel.BUFFERED)
    val openDetail: Flow<Long> = _openDetail.receiveAsFlow()
    init { refresh() }

    fun onEvent(event: RepoEvent) {
        when (event) {
            RepoEvent.Refresh -> refresh()
            is RepoEvent.Click -> _openDetail.trySend(event.id)
        }
    }

    private fun refresh() = viewModelScope.launch {
        _uiState.update { it.copy(loading = true, error = null) }
        runCatching { repository.loadRepos() }
            .onSuccess { r -> _uiState.update { it.copy(loading = false, repos = r) } }
            .onFailure { e -> _uiState.update { it.copy(loading = false, error = e.message) } }
    }
}

@Composable
fun RepoScreen(viewModel: RepoViewModel = viewModel(), onOpenDetail: (Long) -> Unit) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    LaunchedEffect(viewModel) { viewModel.openDetail.collect(onOpenDetail) }
    RepoContent(uiState) { viewModel.onEvent(it) }
}

@Composable
private fun RepoContent(state: RepoUiState, onEvent: (RepoEvent) -> Unit) {
    when {
        state.loading -> CircularProgressIndicator()
        state.error != null -> TextButton({ onEvent(RepoEvent.Refresh) }) { Text("重试") }
        else -> LazyColumn {
            items(state.repos, key = { it.id }) { repo ->
                Text(repo.name, Modifier.fillMaxWidth()
                    .clickable { onEvent(RepoEvent.Click(repo.id)) }
                    .padding(16.dp))
            }
        }
    }
}
```

## 8 测试与工具

### 8.1 createComposeRule

```kotlin
class RepoContentTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun clickRow_reportsId() {
        var clicked = 0L
        composeRule.setContent {
            RepoContent(RepoUiState(repos = listOf(Repo(1, "Compose")))) { event ->
                clicked = (event as RepoEvent.Click).id
            }
        }
        composeRule.onNodeWithText("Compose").performClick()
        assertEquals(1L, clicked)
    }
}
```

* `createComposeRule()` 不需要 Activity；需要真实 Activity（权限、Context）时用 `createAndroidComposeRule<ComponentActivity>()`。
* 查找基于语义树：onNodeWithText / onNodeWithTag / onNodeWithContentDescription，配合 Modifier.testTag 与 useUnmergedTree；异步用 waitUntil，动画用 mainClock 控制。

### 8.2 Compose 预览

* `@Preview` 只渲染 UI、不跑真实业务，所以无状态组件最好预览。
* `@PreviewParameter` 批量展示加载中、空列表、错误态；自定义 multipreview 注解复用一组设备与主题配置。

### 8.3 Layout Inspector 重组计数

* Layout Inspector 的 recomposition counts 需要 debuggable 应用：交互后看哪个 Composable 计数异常增长、跳过次数为 0，通常是参数不稳定或状态读取范围过大；配合编译器稳定性报告可定位到具体参数。

## 9 面试高频问答

**Q1：Compose 和 View 的本质区别？为什么 Google 要推 Compose？**
* View 是命令式：状态散落、手动同步、靠继承复用。
* Compose 是声明式：UI = f(state)，框架算最小更新，靠函数组合复用。
* 收益是状态一致性、可组合、可测试；代价是学习成本与包体积。

**Q2：重组是什么触发的？为什么能只更新局部？**
* 组合中读取的 State 被写入，会把所在 restartable scope 标记为失效。
* 父级重组且子级参数不稳定或不相等时，子级无法跳过。
* 只有失效的 group 重跑，其余从 SlotTable 复用，所以是局部更新。

**Q3：remember 和 ViewModel 有什么区别？**
* remember 跟随组合，离开组合即丢；ViewModel 跟随 ViewModelStoreOwner，配置变更后仍在。
* remember 放 UI 状态与派生对象；ViewModel 放业务状态、请求、跨页面数据。
* 两者都避免重组中重复创建对象，但生命周期与职责不同。

**Q4：remember 和 rememberSaveable 的区别？**
* remember 只跨重组，进程被杀或配置变更后丢失；rememberSaveable 走 Bundle，可恢复。
* rememberSaveable 要求值可保存，复杂对象需要自定义 Saver。
* 输入内容、选中项用 saveable；协程 scope、焦点请求器只能用 remember。

**Q5：Compose 的测量、布局、绘制和 View 有何不同？**
* View 用 MeasureSpec 三种模式，weight 与 RelativeLayout 会二次测量，结构是 View 树。
* Compose 是 LayoutNode 树，MeasurePolicy 一般单次测量，需要 intrinsic 尺寸才二次。
* 绘制直接记录绘制命令，没有 XML 解析与 findViewById；同样受每帧 16ms 预算约束。

**Q6：Compose 比 View 快还是慢？**
* 不绝对。结构不变只改状态时重组范围小，可能比 requestLayout 更省。
* 首帧要做类加载与 SlotTable 构建，启动阶段可能比 View 慢。
* 错误用法（不稳定参数、组合里做重活、无 key 列表）会放大开销，更易卡顿。

**Q7：为什么 @Composable 必须幂等？在组合里写状态会怎样？**
* 组合可能执行 0 次、1 次或多次，也可能并行、被中断、被跳过。
* 在函数体里写状态会立刻让当前 scope 失效，可能无限重组或直接抛异常。
* 正确做法是回调改状态，或交给 effect API。

**Q8：LaunchedEffect、DisposableEffect、SideEffect 怎么选？**
* 要协程且随 key 重启：LaunchedEffect，首次加载常用 LaunchedEffect(Unit)。
* 要成对注册/反注册：DisposableEffect，清理写在 onDispose。
* 每次重组后同步外部状态：SideEffect；点击里起协程：rememberCoroutineScope。

**Q9：derivedStateOf 解决什么问题？**
* 把多个 State 的派生结果收敛成一个 State，只有结果变化才通知下游。
* 典型是滚动位置 → 是否显示顶部栏，避免每帧重组。
* 它不减少计算，减少的是上游高频变化引起的重组。

**Q10：LazyColumn 为什么要传 key？不传会怎样？**
* 不传时用下标当身份，插入、删除、排序会让 item 状态错位。
* key 提供稳定身份，动画、复用与状态恢复才正确。
* key 必须唯一且可被 Bundle 保存，不要用 index。

**Q11：@Stable 和 @Immutable 有什么用？为什么 List 不是 stable？**
* @Immutable 承诺不可变，@Stable 承诺属性变化会通知 Compose。
* 编译器据此判断能否跳过；List 接口实现可能可变，所以不稳定。
* 用 ImmutableList 或 @Immutable 包装类；乱标注解会导致界面不刷新。

**Q12：collectAsState 和 collectAsStateWithLifecycle 的区别？**
* 前者在组合存在期间一直收集，页面在后台也会更新状态。
* 后者跟随 Lifecycle，STARTED 以下停止收集，回前台重新订阅，更省电。
* 需要 lifecycle-runtime-compose；新项目统一用带 Lifecycle 的版本。

**Q13：Compose 中状态该放在哪？如何做单向数据流？**
* UI 状态放 remember / rememberSaveable，业务状态放 ViewModel 的 StateFlow。
* 组件接收 value 和 onValueChange，只读状态、只发事件。
* 状态提升带来可预览、可测试，避免双向绑定与多份状态覆盖。

**Q14：Compose 与 View 如何互操作？老项目怎么渐进接入？**
* Compose 里用 AndroidView 放 View，View 里用 ComposeView 或 setContent 放 Compose。
* 按页面或组件逐步替换，先新页面、再局部卡片，风险可控。
* 注意组合释放策略、共享 ViewModel 的 owner、主题与导航统一。
