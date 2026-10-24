## 1 依赖注入解决什么问题

DI 的核心是：**对象不在内部 new 依赖，而由外部把创建好的依赖传进来**，调用方只声明「我需要什么」。手动 new 的写法通常长这样：`UserViewModel` 里直接 `Retrofit.Builder()...`，再 `UserRepository(api, dao)`，构造链会一路向上蔓延。

痛点：耦合具体实现（换 Mock 仓库要改源码）、构造链爆炸（A→B→C 一路向上）、无法替换测试、单例和生命周期难管理、多模块边界模糊；Activity Context 被长生命周期对象持有还会泄漏。

| 方式 | 写法 | 特点 |
| --- | --- | --- |
| 构造器注入 | `class Repo @Inject constructor(private val api: Api)` | 依赖不可变、易测试，首选 |
| 字段注入 | `@Inject lateinit var repo: Repo` | 写法短，Android 组件常用，可能半初始化 |
| 方法注入 | `@Inject fun setUp(repo: Repo)` | 对象创建后回调，适合初始化逻辑 |

控制反转（IoC）是更上位的概念：创建权和装配权从业务代码交给框架。DI 是 IoC 的实现，Hilt/Dagger 是编译期容器；ServiceLocator 则把容器暴露给业务主动 `get()`，方向相反（前者推、后者拉）。

## 2 从 Dagger2 到 Hilt

`第三方源码/Dagger2.md` 是手写 Dagger2：每个 Android 组件自定义 Component、Module、Scope，再在 Activity 里 build 后 `inject()`。

```kotlin
@Module
class UserModule(private val activity: Activity) {
    @Provides fun repo(api: Api): UserRepository = UserRepository(api)
}

@Component(modules = [UserModule::class])
interface UserComponent { fun inject(activity: UserActivity) }
// Activity：DaggerUserComponent.builder().userModule(UserModule(this)).build().inject(this)
```

自定义 Scope（如 `@ActivityScope`）要自己声明；组件、Subcomponent、Builder/Factory 都要手写，忘记 `inject()` 就静默不注入，ViewModel 还得单独写 Factory。

Hilt 是 Dagger2 之上的 **Android 专用 DI 脚手架**，不是另一个运行时框架：

* 预定义七类组件并自动挂到 Android 生命周期，内置 `@Singleton`、`@ActivityScoped` 等作用域。
* `@HiltAndroidApp`、`@AndroidEntryPoint` 由注解处理器生成 `Hilt_App`/`Hilt_MainActivity` 基类，Gradle 插件再做字节码转换，让原类继承基类并在 `super.onCreate()` 注入。
* 所有 `@InstallIn` 模块编译期聚合成一张依赖图，可分散在 library module。
* 集成 `@HiltViewModel`、`SavedStateHandle`、WorkManager、Compose `hiltViewModel()` 和测试库。

关系概括：**Hilt 的注解仍来自 Dagger，底层仍由 Dagger 注解处理器生成 `Factory`/`Provider`，运行时没有反射**。老项目可共存，但同一类型不要重复绑定。

## 3 核心注解与用法

| 注解 | 标注位置 | 作用 |
| --- | --- | --- |
| `@HiltAndroidApp` | Application | 触发 Hilt 代码生成，创建 SingletonComponent |
| `@AndroidEntryPoint` | Activity/Fragment/View/Service/BroadcastReceiver | 标记可注入的 Android 组件 |
| `@Inject` | 构造器/字段/方法 | 声明依赖，或声明「我可以被注入」 |
| `@Module` | 类 | 存放 `@Provides`/`@Binds` 的模块 |
| `@InstallIn` | Module | 指定模块安装到哪个组件 |
| `@Provides` | 方法 | 手工创建并返回实例 |
| `@Binds` | 抽象方法 | 把接口绑定到实现类 |
| `@Singleton` | 类/方法 | 在 SingletonComponent 中单例 |
| `@HiltViewModel` | ViewModel | 让 ViewModel 参与 Hilt 注入 |
| `@ViewModelInject` | ViewModel 构造器 | 已废弃，被 `@HiltViewModel` 取代 |

### 3.1 @HiltAndroidApp

```kotlin
@HiltAndroidApp
class App : Application()
```

在 manifest 的 `<application android:name=".App">` 注册；它触发组件生成，`Hilt_App` 是真正被启动的基类。

### 3.2 @AndroidEntryPoint

```kotlin
@AndroidEntryPoint
class MainActivity : AppCompatActivity() {
    @Inject lateinit var repository: UserRepository // 字段注入
    @Inject fun setUp(repo: UserRepository) { }     // 方法注入
}
```

注入在 `super.onCreate()` 中完成，之前不可用；Activity 必须继承 `ComponentActivity`，Fragment 必须是 `androidx.fragment.app.Fragment`。

### 3.3 @Module + @InstallIn + @Provides

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides @Singleton
    fun provideGson(): Gson = GsonBuilder().create()
}
```

`@Provides` 用来创建第三方类或有判断逻辑的实例；`@Singleton` 表示在 SingletonComponent 内唯一。

### 3.4 @ViewModelInject（废弃）到 @HiltViewModel

```kotlin
// 旧写法：Hilt 早期提供，已废弃
class OldViewModel @ViewModelInject constructor(private val repo: UserRepository) : ViewModel()

// 现在：统一走 Dagger 构造注入
@HiltViewModel
class UserViewModel @Inject constructor(
    private val repo: UserRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel()
```

`@ViewModelInject` 绕开了 Dagger 图，无法复用 `@Binds`/Qualifier；`@HiltViewModel` 让 ViewModel 成为普通节点，并自动注入 `SavedStateHandle`。

## 4 组件与作用域对应表

层级：SingletonComponent → ActivityRetainedComponent → ViewModelComponent/ActivityComponent → FragmentComponent → ViewComponent，另有 SingletonComponent → ServiceComponent；子组件能访问父组件的绑定，反向不行。

| 组件 | 作用域 | 生命周期 | 常见绑定 |
| --- | --- | --- | --- |
| SingletonComponent | `@Singleton` | Application.onCreate → onDestroy（整个进程） | Retrofit、OkHttp、数据库、Repository |
| ActivityRetainedComponent | `@ActivityRetainedScoped` | Activity 首次创建 → finish（配置变更不销毁） | 跨配置变更的状态持有者 |
| ViewModelComponent | `@ViewModelScoped` | ViewModel 创建 → onCleared() | ViewModel 内部协作对象 |
| ActivityComponent | `@ActivityScoped` | Activity onCreate → onDestroy（配置变更重建） | Activity 级 Controller、Adapter |
| FragmentComponent | `@FragmentScoped` | Fragment onAttach → onDetach | Fragment 级状态、Adapter |
| ViewComponent | `@ViewScoped` | View 添加到窗口 → 移除 | 自定义 View 的依赖 |
| ServiceComponent | `@ServiceScoped` | Service onCreate → onDestroy | Service 内使用的依赖 |

依赖方向只能「短生命周期依赖长生命周期」：`@ActivityScoped` 可以注入 `@Singleton`，反过来把 Activity 注入 Singleton 会编译失败或造成泄漏。Hilt 内置 `Application`、`Activity`、`Fragment`、`View`、`Service`、`SavedStateHandle`、`@ApplicationContext`、`@ActivityContext` 等默认绑定。

## 5 实战：从网络层到 ViewModel

### 5.1 Repository 与接口绑定

```kotlin
interface UserRepository { suspend fun getUser(id: String): User }

class UserRepositoryImpl @Inject constructor(
    private val api: ApiService,
    @IoDispatcher private val io: CoroutineDispatcher
) : UserRepository {
    override suspend fun getUser(id: String) = withContext(io) { api.getUser(id).toDomain() }
}

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    @Binds @Singleton
    abstract fun bindUserRepository(impl: UserRepositoryImpl): UserRepository
}
```

`@Binds` 方法必须抽象、参数是实现类、返回值是接口，实现类要带 `@Inject constructor`；它不生成方法体，比 `@Provides` 轻。

### 5.2 Qualifier：@Named 与自定义 @Qualifier

```kotlin
@Qualifier @Retention(AnnotationRetention.RUNTIME)
annotation class IoDispatcher

@Module
@InstallIn(SingletonComponent::class)
object QualifierModule {
    @Provides @IoDispatcher fun io(): CoroutineDispatcher = Dispatchers.IO
    @Provides @Named("internal")
    fun internalApi(retrofit: Retrofit): ApiService = retrofit.create(ApiService::class.java)
}
```

同一类型有多个实例时必须用 Qualifier 区分，例如用 `@Named("internal")` 区分内网、公网两套实例；`@Named` 简单直接，自定义 `@Qualifier` 有类型检查，团队项目优先。

### 5.3 Retrofit + OkHttp Module

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides @Singleton
    fun provideOkHttp(): OkHttpClient = OkHttpClient()

    @Provides @Singleton
    fun provideRetrofit(client: OkHttpClient): Retrofit = Retrofit.Builder()
        .baseUrl("https://api.example.com/")
        .client(client)
        .addConverterFactory(MoshiConverterFactory.create())
        .build()

    @Provides @Singleton
    fun provideApi(retrofit: Retrofit): ApiService = retrofit.create(ApiService::class.java)
}
```

### 5.4 ViewModel 与 Activity

```kotlin
@HiltViewModel
class UserViewModel @Inject constructor(private val repository: UserRepository) : ViewModel() {
    val uiState = MutableStateFlow<UserUiState>(UserUiState.Loading)

    init {
        viewModelScope.launch {
            runCatching { repository.getUser("42") }
                .onSuccess { uiState.value = UserUiState.Success(it) }
                .onFailure { uiState.value = UserUiState.Error(it) }
        }
    }
}

@AndroidEntryPoint
class UserActivity : AppCompatActivity() {
    private val viewModel: UserViewModel by viewModels()
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        lifecycleScope.launch {
            repeatOnLifecycle(STARTED) { viewModel.uiState.collect(::render) }
        }
    }
}
```

`by viewModels()` 会使用 Hilt 注入的 `HiltViewModelFactory`，不要再手动传 Factory；Compose 中对应 `hiltViewModel()`。

## 6 多模块项目与 KSP

Hilt 模块可以放在任意 library module，只要该模块参与编译并被 app 聚合：

```kotlin
// :data 中的模块，不需要知道 app 的存在
@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {
    @Binds abstract fun bindLocalSource(impl: LocalSourceImpl): LocalSource
}
```

app 模块只需 `@HiltAndroidApp`，并在自己的构建中引入插件与 `hilt-compiler`；聚合处理器会收集所有模块的 `@InstallIn` 元数据，生成完整组件图。含 `@AndroidEntryPoint` 的模块**必须**应用 `hilt-android-gradle-plugin`（插件 id `com.google.dagger.hilt.android`）做字节码转换，只提供 `@Module` 的模块也建议应用，保持一致。

```groovy
// app/build.gradle
plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
    id 'com.google.devtools.ksp'
    id 'com.google.dagger.hilt.android'
}

dependencies {
    implementation libs.hilt.android
    ksp libs.hilt.compiler
}
```

版本统一交给 version catalog 管理，不要在每个模块写死小版本。截至 2025 年底，KSP 与 kapt 的取舍如下：

* KSP 直接读 Kotlin 语法树，不生成 Java stub，增量编译明显更快；KSP2 已稳定并成为 Kotlin 2.x 的推荐路线。
* kapt 仍兼容老项目，但构建慢，且在新 Kotlin 版本上处于维护状态。
* 迁移时把 `kapt libs.hilt.compiler` 换成 `ksp libs.hilt.compiler` 并移除 `kapt` 插件；**不要同时用 kapt 和 ksp 处理 Hilt**，否则重复生成类会导致 `duplicate class`。
* Hilt Gradle 插件负责入口类的字节码转换，和 KSP/kapt 是两件事，不能互相替代。
* 生成类缺失时，先确认每个模块都引入了 `hilt-compiler`，再 clean build；新版 AGP 通常默认开启聚合任务（`enableAggregatingTask`）。

## 7 常见坑与测试

| 现象 | 根因 | 处理 |
| --- | --- | --- |
| `lateinit property repository has not been initialized`，Java 字段为 null | Activity/Fragment 忘了 `@AndroidEntryPoint` | 补注解，确认继承 `ComponentActivity`/`androidx Fragment` |
| 编译报 `Expected @AndroidEntryPoint to have a value` | 模块没应用 Hilt Gradle 插件 | 在对应模块 plugins 中加 `com.google.dagger.hilt.android` |
| `[Dagger/MissingBinding]` | 模块没 `@InstallIn`、没被聚合，或实现类无 `@Inject constructor` | 检查 `@InstallIn`、模块的 `hilt-compiler`、构造器 |
| ViewModel 无参构造报错 / 注入为 null | 只写了 `@Inject constructor`，没 `@HiltViewModel` | 加 `@HiltViewModel`，用 `by viewModels()` |
| `Dependency cycle` | A 依赖 B、B 依赖 A | 用 `Provider<B>`/`Lazy<B>` 延迟，或抽第三方类 |
| `incompatible scopes` | Scope 与 `@InstallIn` 的组件不匹配 | 按第 4 节表调整组件与作用域 |

几个高频细节：

* 字段注入不能是 `private`，Kotlin 用 `@Inject lateinit var`，`val` 不行；注入在 `super.onCreate()`/`onAttach()` 之后才可用。
* `@Singleton` 对象不要持有 Activity Context，需要 Context 时注入 `@ApplicationContext`。
* `@HiltAndroidApp` 只能有一个，且必须注册到 manifest 的 `android:name`。

测试三件套：

```kotlin
@HiltAndroidTest
class UserRepositoryTest {
    @get:Rule val hiltRule = HiltAndroidRule(this)
    @Inject lateinit var repository: UserRepository

    @Before fun setUp() = hiltRule.inject()
}
```

* `@UninstallModules(NetworkModule::class)` 卸载真实模块，再用带 `@InstallIn(SingletonComponent::class)` 的测试模块或 `@BindValue` 注入 Fake。
* Instrumented 测试要自定义 Runner，把 Application 换成 `HiltTestApplication`；Robolectric 用 `@Config(application = HiltTestApplication::class)`。
* `@HiltAndroidTest` 的注入不会自动发生，`HiltAndroidRule.inject()` 要在使用依赖前调用。

## 8 Hilt / Koin / ServiceLocator 对比

| 维度 | Hilt | Koin | 手写 ServiceLocator |
| --- | --- | --- | --- |
| 学习成本 | 中高，要理解组件与作用域 | 低，DSL 直观 | 低，但规范靠团队 |
| 校验时机 | 编译期校验依赖图 | 运行期才报缺失 | 运行期，甚至线上才暴露 |
| 运行时性能 | 生成代码，无反射，接近手写 | DSL/反射有少量开销 | 最快，但功能简陋 |
| 多模块 | 编译期聚合，模块可分散 | 需要手动汇总 module | 需要手动注册，易漏 |

## 9 面试高频问答

**Q1：为什么要用依赖注入？**
* 解耦：业务类只依赖接口，替换实现不改调用方。
* 可测：测试时注入 Fake，不必启动真实网络或数据库。
* 可控：单例、线程池、生命周期由容器统一管理，减少重复创建和泄漏。

**Q2：Hilt 和 Dagger2 有什么区别？**
* Hilt 构建在 Dagger2 之上，复用其注解处理器和 `Provider`/`Factory`，不是替代品。
* Hilt 预定义 Android 组件与作用域，自动挂生命周期，省去 Component/Builder 样板。
* Dagger2 更灵活、可自定义组件图；Hilt 约定优于配置，适合标准 Android 项目。

**Q3：@Binds 和 @Provides 有什么区别？**
* `@Binds` 是抽象方法，把接口映射到实现，实现类必须带 `@Inject constructor`，无方法体、更轻。
* `@Provides` 是具体方法，可以 new 第三方类、读配置、做条件判断。
* 能用 `@Binds` 就用 `@Binds`，它还能强制实现类可被注入。

**Q4：Hilt 的组件层级是怎样的？**
* Singleton → ActivityRetained → ViewModel/Activity → Fragment → View，另有 Singleton → Service。
* 子组件能访问父组件的绑定，父组件不能访问子组件。
* 组件由 Hilt 生成，并挂在对应 Android 组件的生命周期上。

**Q5：@Singleton 和 @ActivityScoped 有什么区别？**
* `@Singleton` 是进程级，整个 Application 一个实例；`@ActivityScoped` 每个 Activity 实例一个。
* 作用域必须与所在组件匹配，否则编译期报 `incompatible scopes`。
* 长生命周期对象持有短生命周期 Context 会泄漏，用 `@ApplicationContext` 规避。

**Q6：@HiltViewModel 解决了什么？@ViewModelInject 为什么废弃？**
* 早期 `@ViewModelInject` 由 Hilt 单独处理，绕开了 Dagger 依赖图。
* `@HiltViewModel` 让 ViewModel 走标准构造注入，支持 `@Binds`、Qualifier、`SavedStateHandle`。
* 必须配合 `@Inject constructor` 与 `by viewModels()`/`hiltViewModel()` 使用。

**Q7：@AndroidEntryPoint 的原理是什么？**
* Hilt 注解处理器生成 `Hilt_MainActivity` 基类，Gradle 插件通过字节码转换让 Activity 继承它。
* 你的 Activity 实际继承这个基类，基类在 `super.onCreate()` 中调用注入逻辑。
* 因此注入在 `super` 之后才可用，且 Activity 必须继承 `ComponentActivity`。

**Q8：@InstallIn 的作用是什么？多模块下怎么工作？**
* 指定模块安装到哪个组件，从而决定绑定的作用域和可见范围。
* library module 可以定义模块，app 的 `hilt-compiler` 在编译期聚合所有元数据。
* 含 `@AndroidEntryPoint` 的模块必须应用 Hilt 插件，所有模块都要引入 `hilt-compiler`。

**Q9：Hilt 和 Koin 怎么选？**
* Hilt 编译期校验、生成代码、运行时无反射，但构建慢、学习曲线陡。
* Koin 运行时 DSL、无注解处理器、构建快，但错误留到运行期，大型依赖图难排查。
* 小团队快速迭代可用 Koin；大型长期项目优先 Hilt。

**Q10：Hilt 中出现循环依赖怎么解决？**
* Hilt 在编译期报 `Dependency cycle`，不会静默失败。
* 用 `Provider<T>`/`Lazy<T>` 延迟获取，打破初始化顺序。
* 根因多是职责划分不清，优先抽第三个类或接口重构。

## 10 参考阅读

* [Hilt 官方文档](https://developer.android.com/training/dependency-injection/hilt-android)
* [Dagger 官方文档](https://dagger.dev/hilt/)
* [Hilt 测试指南](https://developer.android.com/training/dependency-injection/hilt-testing)
