## 1 从 2019 到 2025：这篇补什么

[MVC、MVP、MVVM.md](MVC、MVP、MVVM.md) 是 LiveData + DataBinding 时代的记录：XML 里写 `@{person.name}`，代码里 `ViewModelProviders.of(this).get(...)`，双向绑定一开就算上了 MVVM。写法还能跑，但主流实践已经换了一代，本文不重复 MVC/MVP 的历史（LiveData / ViewModel 的原理见 [Jetpack.md](Jetpack.md)），只讲 MVVM 现在怎么写、MVI 解决什么问题、面试会怎么追问：

* View 从 XML + DataBinding 换成 Compose，双向绑定退出主流（调试难、编译慢、生成的类多）。
* 状态容器从 `LiveData` 换成 `StateFlow`：操作符完整、支持结构化并发、可用于 KMP。
* 数据流从"双向绑定"改成单向数据流（UDF）：状态向下流、事件向上走；分层也从"一个 ViewModel 什么都干"改成 data / domain / presentation + 多模块。

## 2 架构演进：MVC → MVP → MVVM → MVI

### 2.1 职责划分与数据流向

| 模式 | 职责划分 | 数据流向 |
| --- | --- | --- |
| MVC | Model 管数据与规则，View 是布局，Controller 就是 Activity/Fragment | 用户操作 → Controller → Model → View，Controller 可直接改 View |
| MVP | View 抽成接口，Presenter 持有 View 接口与 Model 并负责调度 | View ↔ Presenter ↔ Model，双向但契约明确 |
| MVVM | View 观察 ViewModel 的状态，ViewModel 不引用 View，由 ViewModelStore 持有 | View → 事件 → ViewModel → State → View，理想单向 |
| MVI | View 只发 Intent、只渲染 State，ViewModel 用 Reducer 算出新 State | Intent → Reducer → State → View，严格单向闭环 |

### 2.2 优缺点对比

| 模式 | 优点 | 缺点 |
| --- | --- | --- |
| MVC | 分层直观、上手快，小页面零模板代码 | Activity 既是 Controller 又是 View 宿主，几千行；View 与 Model 耦合，无法单测 |
| MVP | Presenter 是纯 JVM 类可单测；View 与 Model 解耦 | View 接口爆炸；手动 attach/detach，忘了就泄漏；生命周期要自己转发 |
| MVVM | 不用写 View 接口；状态驱动 UI；旋转不丢数据；只测 ViewModel | 多状态源会出现"loading 结束了但列表和错误都空"的非法组合；双向绑定让数据流不可追踪 |
| MVI | 状态永远自洽；重放 Intent 可复现现场；Reducer 是纯函数最好测 | 模板代码多；状态膨胀成巨型 data class；简单页面属于过度设计 |

选型结论：**状态会互相打架的复杂页面用 MVI，常规页面用 MVVM，历史代码里的 MVC/MVP 不必急着重构。**

## 3 MVVM 的现代写法

调用链是单向的：`UI → 事件 → ViewModel → State → UI`；ViewModel 向下调 `UseCase/Repository → Retrofit/Room`，但 View 永远拿不到 Repository。

### 3.1 ViewModel + StateFlow + Repository（UseCase 可选）

```kotlin
data class ArticleUiState(
    val loading: Boolean = false,
    val articles: List<Article> = emptyList(),
    val error: String? = null,
)
@HiltViewModel
class ArticleViewModel @Inject constructor(
    private val repo: ArticleRepository,               // 注入 domain 层接口
) : ViewModel() {
    private val _uiState = MutableStateFlow(ArticleUiState())
    val uiState: StateFlow<ArticleUiState> = _uiState.asStateFlow()    // 对外只读
    init { load() }
    fun onRefresh() = load()
    private fun load() = viewModelScope.launch {
        _uiState.update { it.copy(loading = true, error = null) }
        try {
            _uiState.update { it.copy(loading = false, articles = repo.getArticles()) }
        } catch (e: CancellationException) {
            throw e                                    // 取消不是错误，必须继续抛
        } catch (e: Exception) {
            _uiState.update { it.copy(loading = false, error = e.message ?: "加载失败") }
        }
    }
}
```

### 3.2 单向数据流（UDF）

* State 只允许 ViewModel 改，UI 只读：对外暴露 `asStateFlow()`，绝不暴露 `MutableStateFlow`；UI 也不知道数据来自网络还是数据库。
* 每个用户操作对应一个方法（或一个 Intent），方法里只做两件事：改状态、发请求。

### 3.3 UIEvent 与一次性事件

* **状态型事件**属于 State，比如"当前选中的 tab""错误文案"，进程重建后还得在。
* **一次性事件**只该消费一次：Toast、导航、弹 Dialog。塞进 State 就会粘性重放——转屏后再弹一次，返回栈变化导致重复导航。

| 方案 | 语义 | 适用 |
| --- | --- | --- |
| `Channel(BUFFERED)` + `receiveAsFlow()` | 点对点，一个事件只被一个收集者消费 | ViewModel 只对应一个 UI 消费者（绝大多数页面） |
| `MutableSharedFlow(extraBufferCapacity = 1)` | 广播，多订阅者各收一份，可配 replay | 多观察者，或需要 replay 的场景 |
| `StateFlow` 装事件 | 粘性，新订阅者会收到最后一个值 | 不要用于一次性事件 |

坑：`Channel.trySend` 在缓冲区满时丢事件（`BUFFERED` 默认 64），别为了"只保留最新"设 `CONFLATED`，连续两次导航会被合并；`SharedFlow(replay = 0)` 在没有订阅者时 `emit` 直接丢弃，冷启动早期容易丢 Toast；收集必须跟生命周期（`LaunchedEffect` / `repeatOnLifecycle(STARTED)`），不要在 `lifecycleScope.launch` 里裸 `collect`。

## 4 MVI：Intent / State / Reducer

### 4.1 三元组

* **Intent**：用户意图的穷举，`sealed interface`；点击、输入、下拉刷新、重试都是 Intent（`data object` 需要 Kotlin 1.9+）。
* **State**：`data class` + 全 `val`，描述"界面此刻长什么样"，不放行为、不放 Context。
* **Reducer**：`(State, Result) -> State` 的纯函数，不产生副作用、不调 Repository，可以 100% 单测。

### 4.2 单一状态树与不可变 State

* 一个页面只有一个 `StateFlow<XxxState>`，UI 只订阅它，不再有"第 N 个 LiveData"；改状态只能 `copy()`，线程安全，Compose 也才能靠 `equals` 跳过重组。

### 4.3 副作用（SideEffect）

* Reducer 里不能做的事都归入 Effect：导航、Toast、Snackbar、权限请求、列表滚动。
* 由 ViewModel 走 `Channel` 发出、UI 侧 `LaunchedEffect` 消费一次；Effect 不进 State，所以旋转不重放；重启后必须还在的"副作用"（比如"保存失败"横幅）不是 Effect，而是 State 里的字段。

### 4.4 完整示例：列表页（Intent → ViewModel → State → Compose）

```kotlin
data class FeedState(                              // 单一状态树
    val loading: Boolean = false,
    val items: List<FeedItem> = emptyList(),
    val error: String? = null,
)
sealed interface FeedIntent {                      // 用户意图穷举
    data object Refresh : FeedIntent
    data class ClickItem(val id: String) : FeedIntent
}
sealed interface FeedEffect {                      // 一次性副作用，不进 State
    data class Toast(val msg: String) : FeedEffect
    data class ToDetail(val id: String) : FeedEffect
}
sealed interface FeedResult {                      // 只在 ViewModel 内部流转
    data object Loading : FeedResult
    data class Success(val items: List<FeedItem>) : FeedResult
    data class Failure(val message: String) : FeedResult
}
object FeedReducer {                               // 纯函数，无副作用
    fun reduce(s: FeedState, r: FeedResult): FeedState = when (r) {
        FeedResult.Loading -> s.copy(loading = true, error = null)
        is FeedResult.Success -> s.copy(loading = false, items = r.items, error = null)
        is FeedResult.Failure -> s.copy(loading = false, error = r.message)
    }
}
// ---------- ViewModel ----------
@HiltViewModel
class FeedViewModel @Inject constructor(
    private val repo: FeedRepository,
) : ViewModel() {
    private val _state = MutableStateFlow(FeedState())
    val state: StateFlow<FeedState> = _state.asStateFlow()
    private val _effect = Channel<FeedEffect>(Channel.BUFFERED)
    val effect: Flow<FeedEffect> = _effect.receiveAsFlow()
    fun send(intent: FeedIntent) {
        when (intent) {
            FeedIntent.Refresh -> load()
            is FeedIntent.ClickItem -> _effect.trySend(FeedEffect.ToDetail(intent.id))
        }
    }
    private fun load() {
        viewModelScope.launch {
            apply(FeedResult.Loading)
            try {
                apply(FeedResult.Success(repo.load()))
            } catch (e: CancellationException) {
                throw e                            // 取消不是错误，继续抛
            } catch (e: Exception) {
                apply(FeedResult.Failure(e.message ?: "加载失败"))
                _effect.trySend(FeedEffect.Toast("请稍后重试"))
            }
        }
    }
    private fun apply(result: FeedResult) = _state.update { FeedReducer.reduce(it, result) }
}
```

```kotlin
@Composable
fun FeedRoute(vm: FeedViewModel = hiltViewModel(), onDetail: (String) -> Unit) {
    val state by vm.state.collectAsStateWithLifecycle()
    val host = remember { SnackbarHostState() }
    LaunchedEffect(Unit) {                          // 副作用只消费一次
        vm.effect.collect {
            when (it) {
                is FeedEffect.Toast -> host.showSnackbar(it.msg)
                is FeedEffect.ToDetail -> onDetail(it.id)
            }
        }
    }
    FeedScreen(state, host, onIntent = vm::send)    // 状态向下，事件向上
}

@Composable
fun FeedScreen(state: FeedState, host: SnackbarHostState, onIntent: (FeedIntent) -> Unit) {
    Scaffold(snackbarHost = { SnackbarHost(host) }) { pad ->
        when {
            state.loading -> CircularProgressIndicator(Modifier.padding(pad))
            state.error != null && state.items.isEmpty() ->
                ErrorView(state.error.orEmpty(), Modifier.padding(pad)) { onIntent(FeedIntent.Refresh) }
            else -> LazyColumn(Modifier.padding(pad)) {
                items(state.items, key = { it.id }) { item ->
                    FeedRow(item) { onIntent(FeedIntent.ClickItem(item.id)) }
                }
            }
        }
    }
}
```

## 5 分层与模块化

### 5.1 data / domain / presentation 三层职责

| 层 | 职责 | 允许依赖 | 典型内容 |
| --- | --- | --- | --- |
| presentation | 渲染 UI、把用户操作转成意图 | domain | Composable、ViewModel、UiState |
| domain | 业务规则与用例编排，纯 Kotlin | 无 | Model、Repository 接口、UseCase |
| data | 数据来源实现、缓存策略、DTO 映射 | domain | Retrofit API、Room DAO、RepositoryImpl、Mapper |

关键：**domain 不依赖 Android**，才能纯 JVM 单测、被 KMP 复用。分层失败通常始于 domain 里偷偷 `import android.content.Context`。

### 5.2 模块拆分

```
:app                  壳：Application、导航图、DI 装配
:core:common|model|ui   Result、纯数据模型、Compose 主题与通用组件
:core:domain            Repository 接口 + UseCase，纯 Kotlin
:core:data             Retrofit / Room + RepositoryImpl
:feature:home          列表页（本文示例）；:feature:detail 详情页
```

* `:feature:*` 之间不互相依赖，跳转靠 `:app` 或独立的 `:core:navigation` 接口中转；拆分标准是"能否并行开发、能否单独编译"，`:core:data` 只在 `:app` 里依赖，feature 编译期看不到 Retrofit。

### 5.3 依赖方向与接口下沉

```kotlin
// :core:domain —— 接口在 domain，实现放 data（依赖倒置）
interface FeedRepository {
    suspend fun load(): List<FeedItem>
    fun observeItems(): Flow<List<FeedItem>>
}
```

`FeedRepositoryImpl` 放 `:core:data`：Retrofit 拉取、Room 缓存、断网降级读 dao，并做 DTO→Domain 的 `toDomain()` 映射。依赖方向是 `feature → domain ← data`、`app → 全部`，将来换成 gRPC 只改 data，feature 一行不动；UseCase 只在"多页面复用、有校验分支、要合并多个数据源"时才抽，纯透传的 `operator fun invoke() = repo.get()` 只是样板代码。

### 5.4 Hilt 跨模块注入

```kotlin
// :core:data/di/DataModule.kt —— 由 app 的 @HiltAndroidApp 聚合
@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {
    @Binds @Singleton
    abstract fun bindFeedRepository(impl: FeedRepositoryImpl): FeedRepository
}
```

* `:feature:home` 只依赖 `:core:domain` 并注入 `FeedRepository` 接口，`:app` 才依赖 `:core:data`；每个用到注解的 module 都要开 kapt/ksp 并引入 `hilt-compiler`，否则 `@HiltViewModel` 不会生成 `_HiltModules`。

## 6 状态管理细节

### 6.1 UiState：密封类还是 data class

| 形态 | 适合 | 代价 |
| --- | --- | --- |
| 密封类 `Loading/Success/Error` | 三态互斥、整页一次性切换（引导页、支付结果） | 想保留旧数据要另加字段；刷新失败时列表直接没了 |
| data class + `loading/error/items` | 增量更新、需要保留旧数据（列表、详情） | 可能出现非法组合，需要约定和 review |

结论：**能"带着旧数据进入 loading"的页面用 data class，真正互斥的流程页用 sealed interface**，两者可混用（外层 sealed，内层 data class）。

### 6.2 错误处理与重试

* 错误统一建模成可展示对象（`error: String?` 或 `UiText`），ViewModel 不弹 Toast，只改状态或发 Effect；并分开处理"首屏失败"（整页错误 + 重试按钮）与"刷新失败"（保留列表 + Snackbar 重试）。
* `runCatching` 会把 `CancellationException` 一起吞掉，导致 `viewModelScope.cancel()` 后还在更新状态；用 `try/catch` 并显式 rethrow。
* 重试分层：网络层交给 OkHttp `retryOnConnectionFailure` + 退避，业务层只做"用户点重试"，不自动无限重试。

### 6.3 StateFlow 的 stateIn

```kotlin
val uiState: StateFlow<FeedState> = repo.observeItems()
    .map { FeedState(items = it) }
    .stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = FeedState(loading = true),
    )
```

* `scope`：用 `viewModelScope`，ViewModel 销毁时自动停止上游，防止泄漏。
* `started`：`WhileSubscribed(5_000)` 是标准答案。转屏时订阅者短暂为 0，5 秒内回来就复用同一条上游，不重新请求；`Eagerly` 没人订阅也在跑，`Lazily` 首个订阅后永不停止。
* `initialValue`：必须有。给 `loading = true`，别给空的 `Success`，否则首帧会闪一下"暂无内容"；`stateIn` 只把冷流变热、不缓存数据，进程重建后仍要重新请求。

### 6.4 配置变更与进程死亡

* 配置变更：ViewModel 存在 `ViewModelStore` 里，Activity 重建但 store 未清空，所以状态和协程都还在。
* 进程死亡：ViewModel 一起没了，只有写进 `SavedStateHandle` 的内容进了 `Bundle` 被系统恢复。

```kotlin
@HiltViewModel
class SearchViewModel @Inject constructor(handle: SavedStateHandle) : ViewModel() {
    val keyword: StateFlow<String> = handle.getStateFlow("keyword", "")   // 恢复与更新都走它
    fun onKeywordChange(value: String) { handle["keyword"] = value }
}
```

* 能放的：关键词、页码、选中 id、筛选条件等轻量可序列化数据；不能放列表、Bitmap、整份响应（`Bundle` 走 Binder，超过约 1MB 直接 `TransactionTooLargeException`）。列表页只存页码和查询条件，重建后重新请求，UI 先用缓存或骨架屏兜住首帧。

## 7 测试

### 7.1 ViewModel 单元测试

```kotlin
// 替换 Dispatchers.Main，viewModelScope 才能在测试里跑
class MainDispatcherRule(
    val dispatcher: TestDispatcher = UnconfinedTestDispatcher(),
) : TestWatcher() {
    override fun starting(d: Description) = Dispatchers.setMain(dispatcher)
    override fun finished(d: Description) = Dispatchers.resetMain()
}

class FeedViewModelTest {
    @get:Rule val mainRule = MainDispatcherRule()
    private val vm by lazy { FeedViewModel(FakeFeedRepository()) }

    @Test
    fun `刷新成功进入 Success 状态`() = runTest {
        vm.send(FeedIntent.Refresh)
        advanceUntilIdle()                     // 等 viewModelScope 里的协程跑完
        assertFalse(vm.state.value.loading)
        assertEquals(1, vm.state.value.items.size)
    }
}
```

* 三件套：`runTest` + `MainDispatcherRule` + `advanceUntilIdle()`；断言只看 `StateFlow.value` 或收到的状态序列，测 Effect 用 Turbine 的 `test {}` 并先收集再 send。

### 7.2 UI 测试的分层

| 层级 | 工具 | 测什么 | 依赖 |
| --- | --- | --- | --- |
| Composable 组件 | `createComposeRule` | 给定 State 渲染是否正确、点击是否发出正确 Intent | 无 ViewModel、无网络 |
| Screen + ViewModel | `createAndroidComposeRule` + Hilt 测试规则 | 状态驱动 UI 的联动、Effect 是否被消费 | fake Repository |
| 端到端 | Espresso / `ActivityScenario` + MockWebServer | 真实导航、深链、返回栈、进程恢复 | 假服务端 |

* 组件层只测纯函数式的 `FeedScreen`：`setContent { FeedScreen(FeedState(items = listOf(FeedItem("1", "Kotlin"))), SnackbarHostState(), onIntent = {}) }` 后断言 `onNodeWithText("Kotlin").assertIsDisplayed()`；优先 `testTag` 或无歧义文案，别用 `onNodeWithIndex`，老 View 页面仍用 Espresso。

## 8 常见面试难点

### 8.1 ViewModel 为什么不能持有 View / Context

* 生命周期不匹配：转屏时 Activity 重建而 ViewModel 存活，引用就变成泄漏；持有 `View` 还会让状态绑死在一棵已销毁的视图树上。
* 需要字符串/资源用 `Application`（`AndroidViewModel` 或 Hilt 的 `@ApplicationContext`），或者把 `R.string.id` 交给 UI 层解析；确实需要 Context 的活（数据库、DataStore、`ContentResolver`）下沉到 data 层，导航、`SnackbarHostState`、`ActivityResultLauncher` 归 UI 层。

### 8.2 LiveData 与 StateFlow 怎么选

| 维度 | LiveData | StateFlow |
| --- | --- | --- |
| 生命周期感知 | 内建，自动停止分发 | 需 `repeatOnLifecycle` / `collectAsStateWithLifecycle` |
| 初始值 | 可为空，`value` 可能为 null | 必须有 |
| 线程 | `setValue` 限主线程，`postValue` 合并（多次只留最后一次） | 任意线程，`update` 原子 |
| 操作符 | 只有 map / switchMap / MediatorLiveData | 完整 Flow 操作符，可与其它 Flow 组合 |

新代码一律 `StateFlow`；只在维护老代码、或"不想引入协程又要自动感知生命周期"的场景用 LiveData。

### 8.3 MVI 的缺点与取舍

* **模板代码**：一个页面至少 3 个 sealed interface 加 1 个 Reducer，Intent 一多 `when` 就膨胀；状态还容易膨胀成几十字段的巨型 data class，`copy` 满天飞。
* **性能敏感**：每次 `copy` 都是新对象，Compose 靠 `equals` 判断重组，所以 State 里别放大对象和可变集合，长列表用 `kotlinx.collections.immutable` 的 `ImmutableList`。
* 取舍：列表 + 筛选 + 分页 + 多数据源这类复杂页面用 MVI，设置页、关于页用 MVVM 甚至 Composable 内部 `remember` 就够。

### 8.4 内存泄漏从哪来

* ViewModel 持有 `Activity` / `Fragment` / `View` / 匿名 Listener，或自建的 `CoroutineScope` / `GlobalScope` 没取消却在回调里引用 UI；Flow 收集没跟生命周期（`lifecycleScope.launch { flow.collect {} }` 退到后台还在收），应该用 `repeatOnLifecycle`。
* 单例 / `object` 里存了 `Context` 或 `Callback`：只存 `applicationContext`，不用时注销；排查接 LeakCanary 看 `Activity` 被谁引用。

## 9 面试高频问答

1. **MVVM 与 MVI 的本质区别是什么？**
   * 状态源数量：MVVM 允许多个（`isLoading`、`list`、`error` 各一个），MVI 强制单一状态树。
   * 输入方式与可回放性：MVVM 里 View 可以直接调多个 ViewModel 方法，MVI 只能 `send(Intent)`，但重放 Intent 序列就能复现任意界面；代价是样板代码和状态膨胀更重。
2. **ViewModel 为什么不能持有 Activity 或 View？**
   * 生命周期不匹配：转屏时 Activity 重建而 ViewModel 存活，引用即泄漏。
   * 职责不匹配：ViewModel 管状态、View 管绘制，绑在一起状态就无法脱离视图树存在。
   * 需要 Context 用 `Application`；需要启动页面或弹窗，用 Effect 交给 UI 执行。
3. **LiveData 和 StateFlow 该怎么选？**
   * 新项目一律 `StateFlow`：操作符完整、支持背压、`update` 原子、可跨平台。
   * LiveData 只剩"自带生命周期感知"一个优势（`collectAsStateWithLifecycle` 已补齐），而它的 `postValue` 会合并多次写入只留最后一次，是老代码的经典 bug；迁移时不要两种状态并存。
4. **一次性事件为什么不能放进 State？Channel 和 SharedFlow 怎么选？**
   * 事件进了 State 就有"值"，会粘性重放：转屏后 Toast 再弹一次、返回时又导航一次。
   * `Channel` 点对点，一个事件只被消费一次，适合 ViewModel 对单个 UI。
   * `SharedFlow(replay = 0)` 是广播，无订阅者时事件直接丢弃，适合多观察者或需要 replay；收集都要放在 `LaunchedEffect` / `repeatOnLifecycle`。
5. **`stateIn` 的 `WhileSubscribed(5_000)` 为什么是 5 秒？**
   * 转屏、短暂切后台时订阅者会短暂为 0，5 秒窗口内回来就复用同一条上游，不重新请求。
   * 超过 5 秒仍在后台就停止上游，省流量省电，也不会在后台查数据库；`Eagerly` 永不停、`Lazily` 停了不回收，都可能浪费资源，这个值要配 `initialValue` 一起看。
6. **UiState 用密封类还是 data class？**
   * 密封类表达互斥状态，`when` 穷举不会漏分支，但刷新失败会丢掉已有数据。
   * data class 用布尔/可空字段表达组合，能带着旧数据进入 loading，但要约定约束非法组合。
   * 列表、详情、Feed 选 data class；引导页、支付结果选密封类；也可外层 sealed 内层 data class。
7. **MVI 有哪些缺点？工程上如何取舍？**
   * 模板代码多：Intent / State / Effect / Reducer 四件套，一个小页面也要写一遍。
   * 状态膨胀：单棵状态树容易变成几十字段的巨型 data class，`copy` 满天飞。
   * 性能雷区：State 里放可变集合会破坏 Compose 的重组跳过；取舍是复杂页面 MVI、简单页面 MVVM。
8. **转屏为什么 ViewModel 不丢数据？进程被杀又怎么办？**
   * `ViewModelStore` 由 `ComponentActivity` 通过 `onRetainNonConfigurationInstance` 传给新实例，重建时复用，所以 ViewModel 和它启动的协程都在。
   * 真正销毁发生在 `isChangingConfigurations == false` 的 `onDestroy`，此时才回调 `onCleared()`。
   * 进程被杀后 ViewModel 全丢，只有 `SavedStateHandle` 里的内容随 `Bundle` 恢复；大对象会 `TransactionTooLargeException`，长列表只存条件、重建后重拉。
9. **Repository 和 UseCase 一定要有吗？**
   * Repository 必须有：它是"数据从哪来"的边界，也是唯一能替换网络/数据库实现的位置。
   * UseCase 按需：多页面复用、有业务规则、要合并多个数据源时才抽，纯透传的只会多一层跳转。
   * 判断标准：这段逻辑能否脱离 Android 单测？能，就值得放进 domain。
10. **多模块下如何让 feature 不依赖 data？**
    * 接口定义在 `:core:domain`，实现放 `:core:data`，feature 只依赖 domain。
    * `@Binds` 模块写在 data 模块，`@InstallIn(SingletonComponent::class)` 由 app 聚合。
    * app 里 `implementation(project(":core:data"))`，这样 feature 编译期看不到 Retrofit，换实现只改一个模块。
