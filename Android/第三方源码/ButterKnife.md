## 1 基本使用

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

