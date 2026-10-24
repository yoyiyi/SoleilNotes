## 1 基本使用

> **时效提示**：本文写于 2019 年前后，`ButterKnife` 目前已归档停止维护（最后版本 10.2.1）。
> 生产环境推荐 `ViewBinding`（复杂场景可了解 DataBinding / Compose），见文末「现状与替代方案」。

app 的 build.gradle 导入

```java
implementation 'com.jakewharton:butterknife:10.2.1'
annotationProcessor 'com.jakewharton:butterknife-compiler:10.2.1'
```

在 Activity 使用
```java
public class MainActivity extends AppCompatActivity {
    @BindView(R.id.tv_name)
    TextView mTvName;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        ButterKnife.bind(this);
        mTvName.setText("ButterKnife");
    }
}

```

## 2 原理
在基本使用的，很明显，ButterKnife.bind(this) 应该是 ButterKnife 工作的入口。
```java
  //ButterKnife 和 Activity 建立绑定关系的过程
  @NonNull @UiThread
  public static Unbinder bind(@NonNull Activity target) {
    View sourceView = target.getWindow().getDecorView();
    return bind(target, sourceView);
  }
  
  //最终调到以下函数
  @NonNull @UiThread
  public static Unbinder bind(@NonNull Object target, @NonNull View source) {
    Class<?> targetClass = target.getClass();
    if (debug) Log.d(TAG, "Looking up binding for " + targetClass.getName());
    //代码1 Class 中查找 constructor 本例子  MainActivity_ViewBinding
    Constructor<? extends Unbinder> constructor = findBindingConstructorForClass(targetClass);
    
    if (constructor == null) {
      return Unbinder.EMPTY;
    }
    try {
      //执行构造函数 本例子使用例子，就是生成 MainActivity_ViewBinding 类 
      return constructor.newInstance(target, source);
    } 
    //下面抛出一些异常  
    ... 
  }  
```

代码1 ButterKnife#findBindingConstructorForClass

```java
//1.LinkedHashMap 保存 MainActivity 与 MainActivity_ViewBinding 的构造器对象
@VisibleForTesting
static final Map<Class<?>, Constructor<? extends Unbinder>> BINDINGS = new LinkedHashMap<>();
@Nullable @CheckResult @UiThread
  private static Constructor<? extends Unbinder> findBindingConstructorForClass(Class<?> cls) {
    //2.根据 key 获取 xxx_ViewBinding
    Constructor<? extends Unbinder> bindingCtor = BINDINGS.get(cls);
    if (bindingCtor != null || BINDINGS.containsKey(cls)) {
      if (debug) Log.d(TAG, "HIT: Cached in binding map.");
      return bindingCtor;
    }
    //3.忽略 android、androidx、java 原生文件
    String clsName = cls.getName();
    if (clsName.startsWith("android.") || clsName.startsWith("java.")
        || clsName.startsWith("androidx.")) {
      if (debug) Log.d(TAG, "MISS: Reached framework class. Abandoning search.");
      return null;
    }
    try {
      Class<?> bindingClass = cls.getClassLoader().loadClass(clsName + "_ViewBinding");
      bindingCtor = (Constructor<? extends Unbinder>) bindingClass.getConstructor(cls, View.class);
      ...
    } catch (ClassNotFoundException e) {
     ...
      //4.父类寻找
      bindingCtor = findBindingConstructorForClass(cls.getSuperclass());
    } catch (NoSuchMethodException e) {
      throw new RuntimeException("Unable to find binding constructor for " + clsName, e);
    }
     //put 进去  MainActivity 与 MainActivity_ViewBinding 之间的映射
    BINDINGS.put(cls, bindingCtor);
    return bindingCtor;
  }
```

通过以上代码，有一个问题 xxx_ViewBinding 这个类哪里来，涉及以下技术。

* **JavaPoet：用来生成.java文件**
* **Annotation Processor + APT（Annotation Processing Tool ）：编译时扫描和解析 Java 注解的工具**

```java
public class MainActivity_ViewBinding implements Unbinder {
  private MainActivity target;

  @UiThread
  public MaintActivity_ViewBinding(MainActivity target) {
    this(target, target.getWindow().getDecorView());
  }

  @UiThread
  public MainActivity_ViewBinding(MainActivity target, View source) {
    this.target = target;

    target.mTvName = Utils.findRequiredViewAsType(source, R.id.tv_name, "field 'mTvName'", TextView.class);
  }

  @Override
  @CallSuper
  public void unbind() {
    MainActivity target = this.target;
    if (target == null) throw new IllegalStateException("Bindings already cleared.");
    this.target = null;
    target.mTvName = null;
  }
}

```

在  butterknife-compiler 这个模块中有一个 ButterKnifeProcessor，这个类用来完成了注解处理器的核心逻辑。

```java
@AutoService(Processor.class)
@IncrementalAnnotationProcessor(IncrementalAnnotationProcessorType.DYNAMIC)
@SuppressWarnings("NullAway") // TODO fix all these...
public final class ButterKnifeProcessor extends AbstractProcessor {//注解处理器
   ...     
  //init 入口
  @Override public synchronized void init(ProcessingEnvironment env) {
    super.init(env);
    //判断最低的支持的 sdk 版本   
    String sdk = env.getOptions().get(OPTION_SDK_INT);
    if (sdk != null) {
      try {
        this.sdk = Integer.parseInt(sdk);
      } catch (NumberFormatException e) {
        ...
      }
    }
    typeUtils = env.getTypeUtils();
    filer = env.getFiler();  
   }
    
   ... 
   //重点：目标类注解信息的收集并生成对应 java 类    
   @Override public boolean process(Set<? extends TypeElement> elements, RoundEnvironment env) {
     //注解信息的扫描收集
    Map<TypeElement, BindingSet> bindingMap = findAndParseTargets(env);
    for (Map.Entry<TypeElement, BindingSet> entry : bindingMap.entrySet()) {
      TypeElement typeElement = entry.getKey();
      BindingSet binding = entry.getValue();
      //---> 收集完注解信息之后 得到 java 类源码 开始生成 java 文件 
      JavaFile javaFile = binding.brewJava(sdk, debuggable);
      try {
        //生成 java 文件 
        javaFile.writeTo(filer);
      } catch (IOException e) {
        error(typeElement, "Unable to write binding for type %s: %s", typeElement, e.getMessage());
      }
    }

    return false;
  }  
}

```

ButterKnifeProcessor#findAndParseTargets

```java
private Map<TypeElement, BindingSet> findAndParseTargets(RoundEnvironment env) {
    Map<TypeElement, BindingSet.Builder> builderMap = new LinkedHashMap<>();
    Set<TypeElement> erasedTargetNames = new LinkedHashSet<>();
    //获取 BindView 注解
    for (Element element : env.getElementsAnnotatedWith(BindView.class)) {
      // we don't SuperficialValidation.validateElement(element)
      // so that an unresolved View type can be generated by later processing rounds
      try {
        parseBindView(element, builderMap, erasedTargetNames);
      } catch (Exception e) {
        logParsingError(element, BindView.class, e);
      }
    }
    ...
    //将 builderMap 中的数据添加到队列中
    Deque<Map.Entry<TypeElement, BindingSet.Builder>> entries =
        new ArrayDeque<>(builderMap.entrySet());
    Map<TypeElement, BindingSet> bindingMap = new LinkedHashMap<>();
    while (!entries.isEmpty()) {
      Map.Entry<TypeElement, BindingSet.Builder> entry = entries.removeFirst();

      TypeElement type = entry.getKey();
      BindingSet.Builder builder = entry.getValue();

      TypeElement parentType = findParentType(type, erasedTargetNames, classpathBindings.keySet());
      if (parentType == null) {
        bindingMap.put(type, builder.build());
      } else {
        BindingInformationProvider parentBinding = bindingMap.get(parentType);
        if (parentBinding == null) {
          parentBinding = classpathBindings.get(parentType);
        }
        if (parentBinding != null) {
          builder.setParent(parentBinding);
          bindingMap.put(type, builder.build());
        } else {
          // Has a superclass binding but we haven't built it yet. Re-enqueue for later.
          entries.addLast(entry);
        }
      }
    }

    return bindingMap;

}   

```

ButterKnifeProcessor#parseBindView

```java
//解析 BindView 元素
private void parseBindView(Element element, Map<TypeElement, BindingSet.Builder> builderMap,
      Set<TypeElement> erasedTargetNames) {
    TypeElement enclosingElement = (TypeElement) element.getEnclosingElement();

    //下面就是开始校验数据合法性
    boolean hasError = isInaccessibleViaGeneratedCode(BindView.class, "fields", element)
        || isBindingInWrongPackage(BindView.class, element);
    // Verify that the target type extends from View.
    TypeMirror elementType = element.asType();
    if (elementType.getKind() == TypeKind.TYPEVAR) {
      TypeVariable typeVariable = (TypeVariable) elementType;
      elementType = typeVariable.getUpperBound();
    }
    Name qualifiedName = enclosingElement.getQualifiedName();
    Name simpleName = element.getSimpleName();
    if (!isSubtypeOfType(elementType, VIEW_TYPE) && !isInterface(elementType)) {
      if (elementType.getKind() == TypeKind.ERROR) {
        note(element, "@%s field with unresolved type (%s) "
                + "must elsewhere be generated as a View or interface. (%s.%s)",
            BindView.class.getSimpleName(), elementType, qualifiedName, simpleName);
      } else {
        error(element, "@%s fields must extend from View or be an interface. (%s.%s)",
            BindView.class.getSimpleName(), qualifiedName, simpleName);
        hasError = true;
      }
    }

    if (hasError) {
      return;
    }

    //获取元素使用 BindView 注解时设置的属性值，View 对应的 xml 中 id 值
    int id = element.getAnnotation(BindView.class).value();
    //获取父元素对应的 BindingSet.Builder 
    //BindingSet 保存要生成目标类的基本特征信息，和 ButterKnife 注解的元素的信息
    //BindingSet 和 ButterKnife 类对应起来
    BindingSet.Builder builder = builderMap.get(enclosingElement);
    //资源 id
    Id resourceId = elementToId(element, BindView.class, id);
    if (builder != null) {
      String existingBindingName = builder.findExistingBindingName(resourceId);
      //如果id已经被绑定，会抛出异常
      if (existingBindingName != null) {
        error(element, "Attempt to use @%s for an already bound ID %d on '%s'. (%s.%s)",
            BindView.class.getSimpleName(), id, existingBindingName,
            enclosingElement.getQualifiedName(), element.getSimpleName());
        return;
      }
    } else {
      //创建一个新的 BindingSet.Builder 并返回，  
      builder = getOrCreateBindingBuilder(builderMap, enclosingElement);
    }

    String name = simpleName.toString();
    TypeName type = TypeName.get(elementType);
    //判断当前元素是否使用 Nullable 注解
    boolean required = isFieldRequired(element);
    //FieldViewBinding 包含元素名、类型等，和元素id一起添加到 BindingSet.Builder
    builder.addField(resourceId, new FieldViewBinding(name, type, required));
    //记录当前元素的父类元素
    erasedTargetNames.add(enclosingElement);
  }

```

当收集完目标类的基本信息，就会使用 JavaPoet生成相关的 java 类文件。

ButterKnifeProcessor#init

```java
public final class ButterKnifeProcessor extends AbstractProcessor {//注解处理器
   ...     
 //重点：目标类注解信息的收集并生成对应 java 类    
   @Override public boolean process(Set<? extends TypeElement> elements, RoundEnvironment env) {
     //注解信息的扫描收集
    Map<TypeElement, BindingSet> bindingMap = findAndParseTargets(env);
    for (Map.Entry<TypeElement, BindingSet> entry : bindingMap.entrySet()) {
      TypeElement typeElement = entry.getKey();
      BindingSet binding = entry.getValue();
      //---> 收集完注解信息之后 得到 java 类源码 开始生成 java 文件 
      JavaFile javaFile = binding.brewJava(sdk, debuggable);
      try {
        //生成 java 文件 
        javaFile.writeTo(filer);
      } catch (IOException e) {
        error(typeElement, "Unable to write binding for type %s: %s", typeElement, e.getMessage());
      }
    }

    return false;
  }  
}
```

## 3 现状与替代方案（2025）

### 3.1 维护状态

ButterKnife 已归档停止维护。作者 Jake Wharton 于 2021 年将仓库设为只读，最后一个正式版本是 2019 年的 10.2.1。它被淘汰的根本原因不是“不好用”，而是 ViewBinding 把它的核心价值——省掉 findViewById、编译期生成绑定——变成了官方能力，还不需要注解处理器、不需要额外依赖、不在运行期反射查找 `Xxx_ViewBinding`。

### 3.2 替代方案：ViewBinding

在 `app/build.gradle` 中开启（Android Gradle Plugin 3.6+）：

```groovy
android {
    buildFeatures {
        viewBinding true
    }
}
```

开启后每个布局 `activity_main.xml` 会生成 `ActivityMainBinding`，Java 用法：

```java
public class MainActivity extends AppCompatActivity {
    private ActivityMainBinding binding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());
        binding.tvName.setText("ViewBinding");
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        binding = null; // Fragment 中在 onDestroyView 置空，避免内存泄漏
    }
}
```

Kotlin 写法：

```kotlin
class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        binding.tvName.text = "ViewBinding"
    }
}
```

### 3.3 迁移要点

* `@BindView(R.id.tv_name) TextView mTvName` → `binding.tvName`，字段声明和 `ButterKnife.bind(this)` 一起删掉。
* `@OnClick(R.id.btn)` → `binding.btn.setOnClickListener(v -> ...)`，不再需要注解。
* `ButterKnife.unbind()` 不再需要：binding 随 Activity/Fragment 的 View 生命周期释放，Fragment 记得在 `onDestroyView` 置空。
* RecyclerView：`ViewHolder` 直接持有 `ItemXxxBinding`，在 `onCreateViewHolder` 中 `inflate`，`onBindViewHolder` 中赋值。
* 清理 `annotationProcessor 'com.jakewharton:butterknife-compiler'` 与混淆文件里的 butterknife `-keep` 规则。
* 复杂场景才用 DataBinding（`<layout>` 表达式、双向绑定、`BindingAdapter`），纯新项目可以直接上 Compose；Kotlin Synthetics（`kotlinx.android.synthetic`）已随 Kotlin 1.8 移除，不要作为迁移目标。

### 3.4 面试怎么答

* 「简历写了 ButterKnife 会被问什么」：先讲它解决什么问题（免 `findViewById`、`@OnClick`），再讲原理（APT 生成 `Xxx_ViewBinding`，`bind()` 反射加载构造器并缓存），最后主动说“已归档，新项目用 ViewBinding”，把话题带到熟悉的新方案。
* 「为什么换 ViewBinding」：编译期生成、类型安全（id 写错直接编译失败）、零反射、无额外依赖、官方维护；代价只是每个布局多一个绑定类。
* 「ViewBinding 和 DataBinding 区别」：ViewBinding 只提供视图引用，轻量单向；DataBinding 额外支持 `<layout>` 表达式、双向绑定、可观察字段，但编译更慢。
* 「Fragment 里怎么避免内存泄漏」：`onCreateView` 创建、`onDestroyView` 置空，因为 Fragment 实例比它的 View 活得久。
* 「Compose 项目还要 ViewBinding 吗」：纯 Compose 不需要，存量的 View 页面可以和 Compose 混用。
