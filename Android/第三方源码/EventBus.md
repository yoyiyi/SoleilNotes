## 1 简介

> **时效提示**：本文写于 2019 年前后，`EventBus` 仍可用，但事件总线模式已不再是主流方案。
> 生产环境推荐 `Kotlin Flow / SharedFlow`（或 `LiveData`），见文末「现状与替代方案」。

EventBus 是用于Android 的事件**发布-订阅**总线。

```java
//1、创建事件实体类
public class MessageEvent {
    private String message;
    //setter/getter
}

//2、注册
EventBus.getDefault().register(this)

//3、发送事件
val message = Message()
message.message = "发送"
EventBus.getDefault().post(message)    

//4、添加方法
@Subscribe(threadMode = ThreadMode.MAIN)
fun onEvent(event: MessageEvent) {
     Log.d("test", event.message)
}    
    
//5、解绑
EventBus.getDefault().unregister(this)    
```

官方原理图：

![](../../asset/event.jpg)

EventBus 的核心就是**观察者模式**。

* EventBus 相当于**被观察者**，内部存放一个**subscriptionsByEventType**（订阅方法）集合，包含所有的观察者，也就是调用了 register 的所有 Activity 或者 Fragment 中的订阅方法。
* 当使用 post 发送事件时，遍历 **subscriptionsByEventType**，拿到观察者，通过反射调用观察者中的事件处理方法。

## 2 原理

从基本使用中，我们可以从 Event 的 getDefault 方法分析其原理。

### 2.1 EventBus.getDefault().register()

```java
//使用 DCl 单例模式创建 EventBus
public static EventBus getDefault() {
        EventBus instance = defaultInstance;
        if (instance == null) {
            synchronized (EventBus.class) {
                instance = EventBus.defaultInstance;
                if (instance == null) {
                    instance = EventBus.defaultInstance = new EventBus();
                }
            }
        }
        return instance;
    }
//new EventBus()
public EventBus() {
     //调用 EventBus 另外一个有参数构造方法
     this(DEFAULT_BUILDER);//DEFAULT_BUILDER 其实就是 EventBusBuilder
    
}

//EventBusBuilder
EventBusBuilder() { //什么也没有做    
}
```

EventBus#register 

```java
 public void register(Object subscriber) {
    Class<?> subscriberClass = subscriber.getClass();
    //根据当前注册类获取 subscriberMethods 订阅方法列表
    List<SubscriberMethod> subscriberMethods = subscriberMethodFinder.findSubscriberMethods(subscriberClass);
    synchronized (this) {
        for (SubscriberMethod subscriberMethod : subscriberMethods) {
            //进行注册
            subscribe(subscriber, subscriberMethod);
        }
    }
}

```

SubscriberMethodFinder#findSubscriberMethods

```java
    List<SubscriberMethod> findSubscriberMethods(Class<?> subscriberClass) {
        //缓存中有 subscriberClass 对象对应的所有订阅方法列表,直接return
        //SubscriberMethod 描述订阅类的订阅方法
        List<SubscriberMethod> subscriberMethods = METHOD_CACHE.get(subscriberClass);
        if (subscriberMethods != null) {
            return subscriberMethods;
        }
        //ignoreGeneratedIndex 判断是否使用生成的 APT 代码去优化寻找接收事件的过程，如开启，将会通过 subscriberInfoIndexes 来快速得到接收事件方法的相关信息，提高了性能
        if (ignoreGeneratedIndex) {//默认 false
            subscriberMethods = findUsingReflection(subscriberClass);
        } else {
            subscriberMethods = findUsingInfo(subscriberClass);
        }
        if (subscriberMethods.isEmpty()) {
           ...
        } else {
            METHOD_CACHE.put(subscriberClass, subscriberMethods);
            return subscriberMethods;
        }
    }
```

SubscriberMethodFinder#findUsingInfo

```java
private List<SubscriberMethod> findUsingInfo(Class<?> subscriberClass) {
        //代码1 创建 FindState 是 SubscriberMethodFinder 内部类，作一些，初始化、回收对象
        FindState findState = prepareFindState();
        findState.initForSubscriber(subscriberClass);
        while (findState.clazz != null) {
            findState.subscriberInfo = getSubscriberInfo(findState);
            if (findState.subscriberInfo != null) {
                SubscriberMethod[] array = findState.subscriberInfo.getSubscriberMethods();
                for (SubscriberMethod subscriberMethod : array) {
                    if (findState.checkAdd(subscriberMethod.method, subscriberMethod.eventType)) {
                        findState.subscriberMethods.add(subscriberMethod);
                    }
                }
            } else {
                //代码2 获取订阅者类中的所有声明方法，寻找以 @Subscribe作为注解的方法进行处理
                //将 threadMode，优先级,sticky 等信息封装到 SubscriberMethod 对象中，添加到 subscriberMethods 列表中
                findUsingReflectionInSingleClass(findState);
            }
            findState.moveToSuperclass();
        }
       //代码4 
        return getMethodsAndRelease(findState);
    }

```

代码1 SubscriberMethodFinder#prepareFindState

```java

private FindState prepareFindState() {
        synchronized (FIND_STATE_POOL) {
            for (int i = 0; i < POOL_SIZE; i++) {
                //从已有的 FindState[] FIND_STATE_POOL对象池中找
                FindState state = FIND_STATE_POOL[i];
                if (state != null) {
                    FIND_STATE_POOL[i] = null;
                    return state;
                }
            }
        }
        //没有 直接 new 一个 FindState
        return new FindState();
    }
```

代码2 SubscriberMethodFinder#findUsingReflectionInSingleClass

```java
private void findUsingReflectionInSingleClass(FindState findState) {
        Method[] methods;
        try {
			//获取订阅者的所有方法,例子中是 MainActivity 
            methods = findState.clazz.getDeclaredMethods();
        } catch (Throwable th) {
            methods = findState.clazz.getMethods();
            findState.skipSuperClasses = true;
        }
        for (Method method : methods) {
            int modifiers = method.getModifiers();//获取方法的修饰符 判断是否 public 
            if ((modifiers & Modifier.PUBLIC) != 0 && (modifiers & MODIFIERS_IGNORE) == 0) {
                Class<?>[] parameterTypes = method.getParameterTypes();
                if (parameterTypes.length == 1) {//判断参数是否是一个,按照上面的实例代码,这里的parameterTypes就是String类
                    Subscribe subscribeAnnotation = method.getAnnotation(Subscribe.class);//获取注解
                    if (subscribeAnnotation != null) {
                        Class<?> eventType = parameterTypes[0];
                        if (findState.checkAdd(method, eventType)) {
                            ThreadMode threadMode = subscribeAnnotation.threadMode();
                            findState.subscriberMethods.add(new SubscriberMethod(method, eventType, threadMode,
                                    subscribeAnnotation.priority(), subscribeAnnotation.sticky()));//添加进subscriberMethods的中的所有订阅方法会在findUsingInfo函数中返回
                        }
                    }
                }
                ...
            }
        }
    }
```

代码4 SubscriberMethodFinder#getMethodsAndRelease

```java
 private List<SubscriberMethod> getMethodsAndRelease(FindState findState) {
      //获取 subscriberMethods   
     List<SubscriberMethod> subscriberMethods = new ArrayList<>(findState.subscriberMethods);
        //回收
        findState.recycle();
        synchronized (FIND_STATE_POOL) {
            for (int i = 0; i < POOL_SIZE; i++) {
                if (FIND_STATE_POOL[i] == null) {
                    FIND_STATE_POOL[i] = findState;
                    break;
                }
            }
        }
       //返回 subscriberMethods
        return subscriberMethods;
    }
```

register() 调用 subscribe 方法

```java
public void register(Object subscriber) {
    Class<?> subscriberClass = subscriber.getClass();
    List<SubscriberMethod> subscriberMethods = subscriberMethodFinder.findSubscriberMethods(subscriberClass);
    synchronized (this) {
        for (SubscriberMethod subscriberMethod : subscriberMethods) {
            //subscribe 
            subscribe(subscriber, subscriberMethod);
        }
    }
}
```

EventBus#subscribe

```java
 private void subscribe(Object subscriber, SubscriberMethod subscriberMethod) {
        Class<?> eventType = subscriberMethod.eventType;
        //在构造函数中记录下订阅者和订阅方法
        Subscription newSubscription = new Subscription(subscriber, subscriberMethod);
        CopyOnWriteArrayList<Subscription> subscriptions = subscriptionsByEventType.get(eventType);
        if (subscriptions == null) {
            subscriptions = new CopyOnWriteArrayList<>();
            subscriptionsByEventType.put(eventType, subscriptions);
        } else {
            ...
        }

        int size = subscriptions.size();
        for (int i = 0; i <= size; i++) {
            ////根据优先级来添加
            if (i == size || subscriberMethod.priority > subscriptions.get(i).subscriberMethod.priority) {
                subscriptions.add(i, newSubscription);
                break;
            }
        }
       //typesBySubscriber:根据订阅者来获取到所有的订阅方法参数类型
        List<Class<?>> subscribedEvents = typesBySubscriber.get(subscriber);
        if (subscribedEvents == null) {
            subscribedEvents = new ArrayList<>();
            typesBySubscriber.put(subscriber, subscribedEvents);
        }
        subscribedEvents.add(eventType);

        if (subscriberMethod.sticky) {//粘性事件
            if (eventInheritance) { 
                Set<Map.Entry<Class<?>, Object>> entries = stickyEvents.entrySet();
                for (Map.Entry<Class<?>, Object> entry : entries) {
                    Class<?> candidateEventType = entry.getKey();
                    if (eventType.isAssignableFrom(candidateEventType)) {
                        Object stickyEvent = entry.getValue();
                        checkPostStickyEventToSubscription(newSubscription, stickyEvent);
                    }
                }
            } else {
                Object stickyEvent = stickyEvents.get(eventType);
                checkPostStickyEventToSubscription(newSubscription, stickyEvent);
            }
        }
    }
```

总结：

* 通过 getDefault 获取 EventBus 实例
* 从缓存获取订阅方法的列表，如果不存在，通过反射获取订阅者所有的方法，遍历再通过权限修饰符、参数长度(只允许一个参数)、@Subscribe 判断是否成为订阅者，构建 SubscriberMethod（订阅方法），最后订阅函数列表构建完成添加进入缓存。
* 遍历订阅方法集合，调用 subscribe ：
  * 初始化并完善 subscriptionsByEventType（map）：存储->事件类型和其对应的订阅方法和订阅类的键值对。
  * 初始化并完善 typesBySubscriber （map）：存储->订阅者类和订阅者类所有订阅方法的事件类型集合的映射对

### 2.2 EventBus.getDefault().post()

```java
 public void post(Object event) {
        //currentPostingThreadState 是 ThreadLocal 类型的对象,里面存储 PostingThreadState
        //PostingThreadState:一个 eventQueue 和 其他标志位
        PostingThreadState postingState = currentPostingThreadState.get();
        List<Object> eventQueue = postingState.eventQueue;
        eventQueue.add(event);
        if (!postingState.isPosting) {
            postingState.isMainThread = isMainThread();
            postingState.isPosting = true;
            if (postingState.canceled) {
                throw new EventBusException("Internal error. Abort state was not reset");
            }
            try {
                while (!eventQueue.isEmpty()) {
                    //代码1 
                    postSingleEvent(eventQueue.remove(0), postingState);
                }
            } finally {
                postingState.isPosting = false;
                postingState.isMainThread = false;
            }
        }
    }
```

代码1  Event#postSingleEvent()

```java
  private void postSingleEvent(Object event, PostingThreadState postingState) throws Error {
      //获取事件类型
        Class<?> eventClass = event.getClass();
        boolean subscriptionFound = false;
        if (eventInheritance) {
            List<Class<?>> eventTypes = lookupAllEventTypes(eventClass);
            int countTypes = eventTypes.size();
            for (int h = 0; h < countTypes; h++) {
                Class<?> clazz = eventTypes.get(h);
                subscriptionFound |= postSingleEventForEventType(event, postingState, clazz);
            }
        } else {
            //代码1
            subscriptionFound = postSingleEventForEventType(event, postingState, eventClass);
        }
        if (!subscriptionFound) {
            //一些错误
            ...
        }
    }

```

代码1 EventBus#postSingleEventForEventType

```java

private boolean postSingleEventForEventType(Object event, PostingThreadState postingState, Class<?> eventClass) {
        CopyOnWriteArrayList<Subscription> subscriptions;
        synchronized (this) {
		//subscriptionsByEventType 装的是订阅者和订阅方法,根据发送事件的类型来获取到对应的订阅者和订阅方法，取出 subscriptions
            subscriptions = subscriptionsByEventType.get(eventClass);
        }
        if (subscriptions != null && !subscriptions.isEmpty()) {
            for (Subscription subscription : subscriptions) {
                postingState.event = event; //事件
                postingState.subscription = subscription;
                boolean aborted = false;
                try {
                    postToSubscription(subscription, event, postingState.isMainThread);
                    aborted = postingState.canceled;
                } finally {
                    postingState.event = null;
                    postingState.subscription = null;
                    postingState.canceled = false;
                }
                if (aborted) {
                    break;
                }
            }
            return true;
        }
        return false;

```



```java
private void postToSubscription(Subscription subscription, Object event, boolean isMainThread) {
      //根据 threadMode 来判断在那个线程中使用
        switch (subscription.subscriberMethod.threadMode) {
            case POSTING://反射
                invokeSubscriber(subscription, event);
            case MAIN:
                if (isMainThread) {
                    invokeSubscriber(subscription, event);
                } else {
                    mainThreadPoster.enqueue(subscription, event);
                }
                break;
            case MAIN_ORDERED:
                if (mainThreadPoster != null) {
                    mainThreadPoster.enqueue(subscription, event);
                } else {                  
                    invokeSubscriber(subscription, event);
                }
                break;
            case BACKGROUND:
                if (isMainThread) {
                    //加入到后台队列中
                    backgroundPoster.enqueue(subscription, event);
                } else {
                    invokeSubscriber(subscription, event);
                }
                break;
            case ASYNC:
                asyncPoster.enqueue(subscription, event);//总是开启线程来调用
                break;
            default:
                throw new IllegalStateException("Unknown thread mode: " + subscription.subscriberMethod.threadMode);
        }
    }
```

总结：

* 将事件加入当前线程的事件队列
* 遍历这个事件队列
  * 获取 subscriptions 
  * 根据 threadMode 判断在那个线程中执行

### 2.3 EventBus.getDefault().postSticky()

```java
public void postSticky(Object event) {
       //锁住了stickyEvents -> private final Map<Class<?>, Object> stickyEvents;
        synchronized (stickyEvents) {
            //存放事件
            stickyEvents.put(event.getClass(), event);
        }       
        post(event);
    }
```

### 2.4 EventBus.getDefault().unregister()

```java
    public synchronized void unregister(Object subscriber) {
        //获取了当前订阅者类的事件类型的类对象集合
        List<Class<?>> subscribedTypes = typesBySubscriber.get(subscriber);
        if (subscribedTypes != null) {
            for (Class<?> eventType : subscribedTypes) {
                //删除所有包含当前订阅者的 subscription
                unsubscribeByEventType(subscriber, eventType);
            }
            //直接 remove 掉
            typesBySubscriber.remove(subscriber);
        } else {
            logger.log(Level.WARNING, "Subscriber to unregister was not registered before: "   subscriber.getClass());
        }
    }
```

## 3 现状与替代方案（2025）

### 3.1 维护状态

EventBus 仍在发布版本（3.3.x），但**事件总线模式在大型项目中已不再推荐**。它不是“不能用”，而是代价被低估了：发布者和订阅者之间没有显式契约，谁发、谁收、在哪个线程收，只能靠全局搜索和运行日志推断；`register/unregister` 与生命周期稍有错配就会泄漏或漏收。

### 3.2 替代方案：Kotlin Flow

ViewModel 中用 `SharedFlow` 承载一次性事件，`StateFlow` 承载 UI 状态：

```kotlin
sealed interface UiEvent {
    data class ShowToast(val message: String) : UiEvent
    data object NavigateToDetail : UiEvent
}

private val _events = MutableSharedFlow<UiEvent>(
    replay = 0,                          // 不重放旧事件
    extraBufferCapacity = 1,
    onBufferOverflow = BufferOverflow.DROP_OLDEST
)
val events: SharedFlow<UiEvent> = _events.asSharedFlow()

fun onSaveClicked() {
    viewModelScope.launch { _events.emit(UiEvent.ShowToast("已保存")) }
}
```

页面侧用 `repeatOnLifecycle` 收集，等价于 EventBus 的 `register/unregister`，但由生命周期自动管理：

```kotlin
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.events.collect { event ->
            when (event) {
                is UiEvent.ShowToast -> Toast.makeText(
                    this@MainActivity, event.message, Toast.LENGTH_SHORT
                ).show()
                UiEvent.NavigateToDetail -> startActivity(...)
            }
        }
    }
}
```

Compose 中直接 `LaunchedEffect` + `collect`；如果确实需要全局事件通道，可以封装成基于 `MutableSharedFlow` 的单例，而不是再引入 EventBus：

```kotlin
object AppEvents {
    private val _events = MutableSharedFlow<Any>(extraBufferCapacity = 64)
    val events: SharedFlow<Any> = _events.asSharedFlow()

    fun post(event: Any) {
        _events.tryEmit(event)
    }
}
```

### 3.3 事件总线的问题

* 隐式依赖：`post` 和 `@Subscribe` 没有编译期约束，删掉订阅方不会报错，重构全靠记忆。
* 难追踪：一个事件可能有多个订阅者，调用链断裂，排查只能全局搜索事件类型。
* 生命周期：忘记 `unregister` 就泄漏，`ThreadMode.MAIN` 与页面可见性无关，容易在后台更新 UI。
* 粘性事件：`postSticky` 语义像全局变量，状态来源不清晰；全局单例还让单测之间互相污染。

### 3.4 迁移步骤

* 把事件模型改成 `sealed interface/class`，按业务归类（如 `UiEvent`、`AppEvent`），替代随意的 `MessageEvent`。
* 持有事件的单例改为 ViewModel 内的 `MutableSharedFlow`，`post()` 改为 `emit()/tryEmit()`。
* `register/unregister` 改为 `repeatOnLifecycle(STARTED)` 内 `collect`，页面不可见时自动停止收集。
* 跨页面通信改走 `SavedStateHandle`、Navigation 返回值或共享的 Repository，不要再用全局总线。

### 3.5 面试怎么答

* 「为什么从 EventBus 迁到 Flow」：Flow 显式、可组合、生命周期感知、可测试；`repeatOnLifecycle` 替代手动注册，冷流按需执行。
* 「EventBus 有什么问题」：隐式依赖、难追踪、生命周期易错、粘性事件像全局变量、事件多时难以维护。
* 「Flow 和 LiveData 区别」：LiveData 生命周期感知但操作符少、以主线程为主；Flow 是冷流、操作符丰富、可切换线程，配合 `repeatOnLifecycle` 使用。
* 「SharedFlow 和 StateFlow 区别」：StateFlow 有初始值、会去重并重放最新值，适合 UI 状态；SharedFlow 可配置 replay/buffer，适合一次性事件，避免页面重建时重复弹 Toast。
* 「模块间解耦除了事件总线还有什么」：接口下沉 + DI、Navigation、Repository 暴露 Flow、跨进程用 Binder 或消息队列。
