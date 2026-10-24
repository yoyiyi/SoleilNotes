## 1 简介

> **时效提示**：本文写于 2019 年前后，`Dagger2` 仍在维护，但 Android 官方已推荐 `Hilt`。
> 生产环境推荐 `Hilt`（`@HiltAndroidApp` + `@AndroidEntryPoint`），见文末「现状与替代方案」。

Dagger2 主要为了模块间解耦、提高代码的健壮性和可维护性，基于 Java 注解来实现的完全在**编译**阶段完成依赖注入的开源库。

## 2 Dagger2 注解

Dagger2 是基于 Java 注解来实现依赖注入，常用的注解主要包括以下：@Inject, @Module, @Provides, @Component, @Qulifier, @Scope, @Singleten。

### 2.1 @Inject

标记需要依赖的变量和构造函数，告诉 Dagger2 为它提供依赖。

### 2.2 @Module

类注解，标注提供依赖的类。

### 2.3 @Provides

只在 @Module 中使用，用于提供构造好的实例。

### 2.4  @Component

标注接口，是依赖需求方和依赖提供方之间的桥梁，被 Component 标注的接口在编译时会生成该接口的实现类。

### 2.5 @Qulifier

用于自定义注解。

### 2.6 @Scope

用于自定义注解，限定注解作用域，实现单例（分局部和全局）

### 2.7  @Singleton

实现全局单例。但实际上它并不能提前全局单例，是否能提供全局单例还要取决于对应的 Component 是否为一个全局对象。

## 3 基本使用

以 MVP 使用为例子，基本都是一个模板。

```java
//1.新建 Presenter
public class MainPresenter {
    private MainContract.View mView;
    @Inject
    MainPresenter(MainContract.View view) {
        mView = view;
    }    
    public void loadData() {
        //加载数据
        ...
        //回调方法
        mView.showList(List<PersonEntity> list);
    }
}
//2.Module
@Module
public class MainModule {
    private final MainContract.View mView;
    public MainModule(MainContract.View view) {
        mView = view;
    }

    @Provides
    MainView provideMainView() {
        //提供 View
        return mView;
    }
}

//3.Component
@Component(modules = MainModule.class)
public interface MainComponent {
    //注入
    void inject(MainActivity activity);
}

//4.使用
public class MainActivity extends AppCompatActivity implements MainContract.View {
    @Inject
    MainPresenter mainPresenter;
    ...
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
         
        //注入
        DaggerMainComponent.builder()
                .mainModule(new MainModule(this))
                .build()
                .inject(this);
         //调用 Presenter 方法加载数据
         mainPresenter.loadData();        
         ...
    }
}
```

## 4 原理

Dagger2 原理也简单，就是通过 apt 插件在编译阶段生成相应的注入代码。

```java
public class MainPresenter {
    MainContract.View mView;
    @Inject
    MainPresenter(MainContract.View view) {
        mView = view;
    }
 }

//生成的代码
public final class MainPresenter_Factory implements Factory<MainPresenter> {
   //MainContract.View 是一个依赖 
  private final Provider<MainContract.View> viewProvider;

  public MainPresenter_Factory(Provider<MainContract.View> viewProvider) {
    assert viewProvider != null;
    this.viewProvider = viewProvider;
  }

  @Override
  public MainPresenter get() {
     //创建 Presenter，而参数 View 需要 viewProvider.get() 获取
    return new MainPresenter(viewProvider.get());
  }

  public static Factory<MainPresenter> create(Provider<MainContract.View> viewProvider) {
    return new MainPresenter_Factory(viewProvider);
  }
}
```

viewProvider 是由 MainModule 提供。

```java
@Module
public class MainModule {
    private final MainContract.View mView;

    public MainModule(MainContract.View view) {
        mView = view;
    }

    @Provides
    MainContract.View provideMainView() {
        return mView;
   }   
}

//@Provides 修饰的方法会对应的生成一个工厂类
public final class MainModule_ProvideMainViewFactory implements Factory<MainContract.View> {
  private final MainModule module;

  public MainModule_ProvideMainViewFactory(MainModule module) {
    assert module != null;
    this.module = module;
  }

  @Override
  public MainContract.View get() {
      //获取 View
    return Preconditions.checkNotNull(
        module.provideMainView(), "Cannot return null from a non-@Nullable @Provides method");
  }

  public static Factory<MainContract.View> create(MainModule module) {
     //创建  MainModule_ProvideMainViewFactory 
    return new MainModule_ProvideMainViewFactory(module);
  }
}
```

MainPresenter_Factory 的创建是由 create() 完成的，create()  又是那里调用呢？

@Component 标注接口，是依赖需求方和依赖提供方之间的桥梁，被 Component 标注的接口在编译时会生成该接口的实现类，答案就在  @Component  里面。

```java
@Component(modules = MainModule.class)
public interface MainComponent {
    void inject(MainActivity activity);
}

//生成 DaggerMainComponent
public final class DaggerMainComponent implements MainComponent {
  private Provider<MainContract.View> provideMainViewProvider;

  private Provider<MainPresenter> mainPresenterProvider;

  private MembersInjector<MainActivity> mainActivityMembersInjector;

  private DaggerMainComponent(Builder builder) {
    assert builder != null;
    initialize(builder);
  }

  public static Builder builder() {
    return new Builder();
  }

  @SuppressWarnings("unchecked")
  private void initialize(final Builder builder) {
    //调用 MainModule_ProvideMainViewFactory.create 提供 View
    this.provideMainViewProvider = MainModule_ProvideMainViewFactory.create(builder.mainModule);

    //调用 MainPresenter_Factory.create   
    this.mainPresenterProvider = MainPresenter_Factory.create(provideMainViewProvider);

    //调用 MainActivity_MembersInjector.create     
    this.mainActivityMembersInjector = MainActivity_MembersInjector.create(mainPresenterProvider);
  }

  @Override
  public void inject(MainActivity activity) {
    //代码一：调用 mainActivityMembersInjector.injectMembers，activity 为参数。
    //这个方法中 最终提供 Presenter -> instance.mainPresenter = mainPresenterProvider.get();  
    mainActivityMembersInjector.injectMembers(activity);
  }

  public static final class Builder {
    private MainModule mainModule;

    private Builder() {}

    public MainComponent build() {
      if (mainModule == null) {
        throw new IllegalStateException(MainModule.class.getCanonicalName() + " must be set");
      }
      return new DaggerMainComponent(this);
    }

    public Builder mainModule(MainModule mainModule) {
      this.mainModule = Preconditions.checkNotNull(mainModule);
      return this;
    }
  }
}

```

代码一：MainActivity_MembersInjector

```java
public final class MainActivity_MembersInjector implements MembersInjector<MainActivity> {
  private final Provider<MainPresenter> mainPresenterProvider;

  public MainActivity_MembersInjector(Provider<MainPresenter> mainPresenterProvider) {
    assert mainPresenterProvider != null;
    this.mainPresenterProvider = mainPresenterProvider;
  }

  public static MembersInjector<MainActivity> create(
      Provider<MainPresenter> mainPresenterProvider) {
    return new MainActivity_MembersInjector(mainPresenterProvider);
  }

  @Override
  public void injectMembers(MainActivity instance) {
    if (instance == null) {
      throw new NullPointerException("Cannot inject members into a null reference");
    }
     //关键：提供 Presenter 
    instance.mainPresenter = mainPresenterProvider.get();
  }

  public static void injectMainPresenter(
      MainActivity instance, Provider<MainPresenter> mainPresenterProvider) {
    instance.mainPresenter = mainPresenterProvider.get();
  }
}
```

## 5 现状与替代方案（2025）

### 5.1 维护状态

Dagger2 仍在维护，Google 持续发布 2.x 版本并已支持 KSP；但 **Android 官方推荐 Hilt**。Hilt 构建在 Dagger 之上，把 `@Component`、`@Subcomponent`、`@Module` 的模板代码交给注解处理器生成，并自动绑定 Android 生命周期组件。面试时只会背 `@Inject / @Module / @Component` 却不了解 Hilt，容易被认为没有跟进 Jetpack 生态。

### 5.2 替代方案：Hilt

```kotlin
// 1. Application
@HiltAndroidApp
class App : Application()

// 2. Activity / Fragment
@AndroidEntryPoint
class MainActivity : AppCompatActivity() {
    @Inject lateinit var presenter: MainPresenter
}

// 3. ViewModel
@HiltViewModel
class MainViewModel @Inject constructor(
    private val repository: UserRepository
) : ViewModel()

// 4. 获取 ViewModel
private val viewModel: MainViewModel by viewModels()
```

提供依赖的 Module 用 `@InstallIn` 指定安装到哪个组件：

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideRetrofit(): Retrofit = Retrofit.Builder()
        .baseUrl("https://example.com/")
        .build()
}
```

构建配置（KSP 方式，KAPT 仍可用）：

```groovy
plugins {
    id 'com.google.dagger.hilt.android' version '2.51.1'
    id 'com.google.devtools.ksp'
}

dependencies {
    implementation 'com.google.dagger:hilt-android:2.51.1'
    ksp 'com.google.dagger:hilt-compiler:2.51.1'
}
```

### 5.3 迁移要点

* `DaggerMainComponent.builder().mainModule(...).build().inject(this)` → 删掉，Activity 加 `@AndroidEntryPoint`，字段加 `@Inject` 由 Hilt 注入。
* `@Module` 增加 `@InstallIn(SingletonComponent::class)`（应用级），或安装到 `ActivityComponent`、`FragmentComponent`、`ViewModelComponent`。
* 自定义 `@Scope` → Hilt 内置作用域 `@Singleton`、`@ActivityScoped`、`@ViewModelScoped`；`@Subcomponent` → Hilt 的组件层级。
* 多模块工程：`@InstallIn` 的 Module 会跨模块聚合，不需要把 Component 暴露到 `:app`。
* 非 Android 场景（Java/Kotlin 后端、KMP 共享代码）仍直接使用 Dagger2，Hilt 只解决 Android 组件注入。
* 本文源码部分没有白读：`DaggerXxxComponent`、`Xxx_Factory`、`Xxx_MembersInjector` 正是 Hilt 生成的底层代码。

### 5.4 面试怎么答

* 「Dagger2 和 Hilt 什么关系」：Hilt = Dagger2 + Android 生命周期组件模板，Hilt 生成的仍是 Dagger 组件，只是不需要手写。
* 「为什么用 Hilt 不用 Koin」：Hilt 编译期校验、零反射、错误提前暴露；Koin 是运行期 DSL，上手简单但大项目里错误发现晚、启动有成本。
* 「Hilt 的组件层级」：SingletonComponent → ActivityRetainedComponent → ViewModelComponent → ActivityComponent → FragmentComponent → ViewComponent。
* 「@HiltViewModel 怎么用」：`@HiltViewModel` + `@Inject constructor`，用 `by viewModels()` 或 Compose 的 `hiltViewModel()` 获取。
* 「Dagger2 源码还记得吗」：`@Component` 生成 `DaggerXxxComponent`，`@Provides` 生成 `Xxx_ProvideYyyFactory`，字段注入生成 `Xxx_MembersInjector`，全部在编译期完成。
