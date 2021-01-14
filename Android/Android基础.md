### Activity 生命周期 

* onCreate()：正在被创建，常用来**初始化工作**，比如调用 setContentView 加载界面布局资源，初始化 Activity 所需数据等；

* onRestart()：正在重新启动，一般情况下，当前 Acitivty 从不可见重新变为可见时，OnRestart 就会被调用；

* onStart()：正在被启动，此时 Activity 可见但不在前台，还处于后台，无法与用户交互；

* onResume()：获得焦点，此时 Activity 可见且在前台并开始活动，这是 与onStart 的区别所在；

* onPause()：正在停止，此时可做一些存储数据、停止动画等工作，但不能太耗时，因为这会影响到新 Activity 的显示，onPause 必须先执行完，新 Activity 的 onResume 才会执行；

* onStop()：即将停止，可以做一些稍微重量级的回收工作，比如注销广播接收器、关闭网络连接等，同样不能太耗时；

* onDestroy()：即将被销毁，Activity 生命周期中的最后一个回调，常做回收工作、资源释放；

### 横竖屏切换时候 Activity 的生命周期

* 不设置  **android:configChanges** ，切屏会销毁当前 Activity，重新加载各个生命周期，切横屏时会执行一次，切竖屏时会执行两次。

* 设置 android:configChanges="orientation"
  * 在Android5.1 即 API 23级别下，切屏会重新调用各个生命周期，切横、竖屏时只会执行一次。
  * 在Android9 即API 28级别下，切屏不会重新调用各个生命周期，只会执行 onConfigurationChanged 方法
* 设置 android:configChanges="orientation|keyboardHidden|screenSize"：切屏不会重新调用各个生命周期，只会执行onConfigurationChanged方法。


### ActivityA 跳转 ActivityB 然后 B 按 back 返回 A，各自的生命周期顺序，A 与 B 均不透明？如果B是透明主题的又或是个DialogActivity 呢？

```java
A -> B
A:onPause
B:onCreate -> onStart -> onResume
A:onStop
    
B -> A
B:onPause
A:onRestart -> onStart -> onResume
B:onStop -> onDestroy 

//B是透明主题
//A:不会调用 onStop   
```

### Android中进程的优先级？

* 前台进程：与用户正在交互的 Activity 或者 Activity 用到的 Service 等，如果系统内存不足时前台进程是最晚被杀死的。
* 可见进程：处于暂停状态(onPause)的 Activity 或者绑定在其上的 Service，即被用户可见，但由于失了焦点而不能与用户交互。
* 服务进程：其中运行着使用 startService 方法启动的 Service，虽然不被用户可见，但是却是用户关心的，例如用户正在非音乐界面听的音乐或者正在非下载页面下载的文件等；当系统要空间运行，前两者进程才会被终止。
* 后台进程：其中运行着执行 onStop 方法而停止的程序，但是却不是用户当前关心的，例如后台挂着的QQ，这时的进程系统一旦没了有内存就首先被杀死。
* 空进程：不包含任何应用程序的进程，这样的进程系统是一般不会让他存在的。

### Activty 和 Fragmengt 之间怎么通信，Fragmengt 和 Fragmengt怎么通信？

* Handler
* 广播
* 事件总线：EventBus、RxBus、Otto
* 接口回调
* Bundle 和 setArguments(bundle)

### onSaveInstanceState()方法的作用 ? 何时会被调用？

系统**配置发生改变**时导致 Activity 被杀死并重新创建、资源内存不足导致优先级低的 Activity 被杀死。

系统会调用 onSaveInstanceState 来保存当前 Activity 的状态，此方法调用在onStop之前，与onPause 没有既定的时序关系；

当Activity被重建后，系统会调用 onRestoreInstanceState，并且把 onSaveInstanceState 方法所保存的 Bundle 对象同时传参给 onRestoreInstanceState 和 onCreate()，因此可以通过这两个方法判断Activity 是否被重建 ，调用在 onStart 之后；

###  Activity的四种启动模式、应用场景 ？

**standard标准模式**：每次启动一个 Activity 都会重新创建一个新的实例，不管这个实例是否已经存在，此模式的 Activity 默认会进入启动它的 Activity 所属的任务栈中；

**singleTop栈顶复用模式**：如果新 Activity 已经位于任务栈的栈顶，那么此 Activity 不会被重新创建，同时会回调 **onNewIntent** 方法，如果新 Activity 实例已经存在但不在栈顶，那么 Activity 依然会被重新创建；

**singleTask栈内复用模式**：只要 Activity 在一个任务栈中存在，那么多次启动此 Activity 都不会重新创建实例，并回调 **onNewIntent** 方法，此模式启动 Activity，系统首先会寻找是否 Activity 存在想要的任务栈，如果不存在，就会重新创建一个任务栈，然后把创建好 Activity 的实例放到栈中，具有 clearTop 功能；

**singleInstance单实例模式**：这是一种加强的 singleTask 模式，具有此种模式的 Activity 只能单独地位于一个任务栈中，且此任务栈中只有唯一一个实例；

### Activity 常用的标记位 Flags？

**FLAG_ACTIVITY_NEW_TASK :** 对应singleTask启动模式；

**FLAG_ACTIVITY_SINGLE_TOP :** 对应singleTop启动模式；

**FLAG_ACTIVITY_CLEAR_TOP :**当它启动时，在同一个任务栈中所有位于它上面的 Activity 都要出栈。这个标记位一般会和 **singleTask** 模式一起出现，在这种情况下，被启动 Activity 的实例如果已经存在，那么系统就会回调 onNewIntent。如果被启动的 Activity 采用 standard 模式启动，那么它以及连同它之上的 Activity 都要出栈，系统会创建新的 Activity 实例并放入栈中；

**FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS :** 具有这个标记的 Activity 不会出现在历史 Activity 列表中；

### Activity 跟 window，view 之间的关系？

window （实现类是 PhoneWindow ）相当于一个容器，里面盛放着很多 view，这些 view 是以树状结构组织起来的。

一个 Activity 对应一个 Window，Activity 本身是没办法处理显示什么控件（view）的，是通过PhoneWindow 进行显示的。

### 如何启动其他应用的 Activity？

在保证有权限访问的情况下，通过隐式 Intent 进行目标 Activity 的 **IntentFilter** 匹配，原则是：

- 一个 intent 只有同时匹配某个 Activity 的 intent-filter 中的 action、category、data 才算完全匹配，才能启动该Activity；
- 一个 Activity 可以有多个 intent-filter，一个 intent 只要成功匹配任意一组 intent-filter，就可以启动该Activity；

### 什么是 ANR？ 如何避免？

应用程序有一段时间响应不够灵敏，系统会向用户显示一个对话框，这个对话框称作应用程序无响应（ANR：Application Not Responding）对话框。用户可以选择让程序继续运行，但是，用户在使用应用程序时，并不希望每次都要处理这个对话框。因此，在程序里对响应性能的设计很重要，这样，系统不会显示 ANR 给用户。

不同的组件发生 ANR 的时间不同（均为前台）：

* Activity 5s
* BroadcastReceiver 10s
* Service 20s

开发机器上出现问题，可以通过查看 **/data/anr/traces.txt** 。

出现原因：

* 主线程做了耗时操作（IO操作等）
* 主线程使用 Object.wait()、Thread.sleep() 等错误的操作
* 应用在规定时间内没有处理完相关事件（Activity、BroadcastReceiver 、Service ）

处理：

* 使用 AsyncTask、Thread、HandlerThread 等处理耗时操作
* 使用 Handler 线程之间的通信，而不是使用 Object.wait() 或者 Thread.sleep() 来阻塞主线程
* onCreate 和 onResume 回调中尽量避免耗时的代码

### AsyncTask 的缺陷和问题，说说他的原理？

AsyncTask 是一种**轻量级的异步任务类**，可以在线程池中执行后台任务，然后把执行的进度和最终结果传递给主线程并主线程中更新 UI，通过 AsyncTask 可以更加方便执行后台任务以及在主线程中访问 UI，但是 AsyncTask 并不适合进行特别耗时的后台任务，对于特别耗时的任务来说，建议使用线程池。

AsyncTask 是一个抽象的泛型类，提供了 Params（参数类型）、Progress（后台任务的执行进度和类型） 和 Result（后台任务的返回结果的类型）这三个泛型参数，如果 AsyncTask 不需要传递具体的参数，那么这三个泛型参数可以用 Void 来代替。

#### 线程池

AsyncTask 里面线程池是一个核心线程数为 CPU + 1，最大线程数为 CPU * 2 + 1，工作队列长度为128 的线程池，线程等待队列的最大等待数为 28，但是可以自定义线程池。线程池是由 AsyncTask 来处理的，线程池允许tasks并行运行，需要注意的是并发情况下数据的一致性问题，新数据可能会被老数据覆盖掉。所以希望tasks能够串行运行的话，使用SERIAL_EXECUTOR。

#### 原理

- AsyncTask 中有两个线程池（SerialExecutor 和 THREAD_POOL_EXECUTOR）和一个Handler（InternalHandler），SerialExecutor 用于任务的排队，THREAD_POOL_EXECUTOR 用于真正地执行任务，InternalHandler 用于将执行环境从线程池切换到主线程。
- sHandler 是一个静态的 Handler 对象，为了能够将执行环境切换到主线程，这就要求 sHandler这个对象必须在主线程创建。由于静态成员会在加载类的时候进行初始化，因此这就变相要求AsyncTask 的类必须在主线程中加载，否则同一个进程中的 AsyncTask 都将无法正常工作。

#### 缺陷

* 生命周期：Activity 销毁之前，没有取消 AsyncTask，有可能让应用崩溃(crash)。
* 内存泄漏：如果 AsyncTask 被声明 非静态内部类，会保留一个对 Activity 的引用，AsyncTask 的后台线程还在执行，它将继续在内存里保留这个引用，导致 Activity 无法被回收，引起内存泄漏。
* 结果丢失：屏幕旋转或 Activity 在后台被系统杀掉等情况会导致 Activity 的重新创建，之前运行的 AsyncTask  会持有一个之前 Activity 的引用，这个引用已经无效，这时调用 onPostExecute()再去更新界面将不再生效。
* 并行还是串行
  * Android1.6 之前，串行
  * Android 1.6 之后，采用线程池处理并行任务
  * 从Android 3.0开始，一个线程来串行执行任务。可以使用 executeOnExecutor() 方法来并行地执行任务。

### 动画

- View 动画：
  - 作用对象是 View，可用 xml 定义，建议使用 xml 比较易读
  - 四种类型：平移、缩放、旋转、透明度
- 帧动画：
  - 通过 AnimationDrawable 实现，容易 OOM
- 属性动画：
  - 可作用于任何对象，可用 xml 定义，Android 3 引入，建议代码实现比较灵活
  - 包括 ObjectAnimator、ValuetAnimator、AnimatorSet
  - 时间插值器：根据时间流逝的百分比计算当前属性改变的百分比，系统预置匀速、加速、减速等插值器
  - 类型估值器：根据当前属性改变的百分比计算改变后的属性值，系统预置整型、浮点、色值等类型估值器
  - 使用注意事项：避免使用帧动画，容易OOM；界面销毁时停止动画，避免内存泄漏；开启硬件加速，提高动画流畅性
  - 硬件加速原理：将 cpu 一部分工作分担给 gpu ，使用 gpu 完成绘制工作；从工作分摊和绘制机制两个方面优化了绘制速度

#### 属性动画和 View 动画区别：

属性动画真正的实现了 view 的移动，补间动画对 view 的移动只是在不同地方绘制了一个影子，实际对象还是处于原来的地方。 当动画的 repeatCount 设置为无限循环时，如果在 Activity 退出时没有及时将动画停止，属性动画会导致Activity无法释放而导致内存泄漏，而补间动画却没问题。 xml 文件实现的补间动画，复用率极高。在 Activity切换，窗口弹出时等情景中有着很好的效果。 使用帧动画时需要注意，不要使用过多特别大的图，容导致内存不足。

#### 原理：

* 属性动画：其实就是利用插值器和估值器，来计算出各个时刻 View 的属性，然后通过改变View的属性来，实现View的动画效果。
* View 动画：只是影像变化，view的实际位置还在原来的地方。
* 帧动画：是在xml中定义好一系列图片之后，使用 AnimationDrawable 来播放的动画。
* 属性动画：
  - 插值器：根据时间的流逝的百分比来计算属性改变的百分比
  - 估值器：根据插值器的结果计算出属性变化了多少数值

### Bundle 传递对象为什么需要序列化？

为 bundle 传递数据时，只支持基本数据类型，所以在传递数据时，要将对象序列化转化成可以存储或者可以传输的本质状态，即**字节流**。序列化后的对象可以在网络，页面之间传递，也可以存储到本地。

### Android 各版本新版本

#### Android5.0

- **MaterialDesign设计风格**
- **支持 64 位ART虚拟机**（5.0推出的ART虚拟机，在5.0之前都是Dalvik。他们的区别是： Dalvik,每次运行,字节码都需要通过即时编译器转换成机器码(JIT)。 ART,第一次安装应用的时候,字节码就会预先编译成机器码(AOT)）
- 通知详情可以用户自己设计

#### Android6.0

- **动态权限管理**
- 支持快速充电的切换
- 支持文件夹拖拽应用
- 相机新增专业模式

#### Android7.0

- **多窗口支持**
- **V2签名**
- 增强的Java8语言模式
- 夜间模式

#### Android8.0（O）

- **优化通知**

  通知渠道 (Notification Channel) 通知标志 休眠 通知超时 通知设置 通知清除

- **画中画模式**：清单中 Activity 设置 android:supportsPictureInPicture

- **后台限制**

#### Android9.0（P）

- **室内WIFI定位**
- **“刘海”屏幕支持**
- 安全增强

#### Android10.0（Q）

- **夜间模式**：包括手机上的所有应用都可以为其设置暗黑模式。
- **桌面模式**：提供类似于PC的体验，但是远远不能代替PC。
- **屏幕录制**：通过长按“电源”菜单中的"屏幕快照"来开启。

#### Android11.0（R）

* 短信更新改进：聊天泡泡
* 隐私和权限：位置、麦克风和摄像头的一次性权限许可
* 内置屏幕录制
* 适配不同设备：折叠手机等
* **网络优化**：5G

### Serialzable 和 Parcelable 的区别？

##### Serializable（Java自带）：

Serializable 是序列化的意思，表示将一个对象转换成存储或可传输的状态。序列化后的对象可以在网络上进传输，也可以存储到本地。

##### Parcelable（android专用）：

除了 Serializable 之外，使用 Parcelable 也可以实现相同的效果，不过不同于将对象进行序列化，Parcelable方式的实现原理是将一个完整的对象进行**分解**，而分解后的每一部分都是Intent所支持的数据类型，这也就实现传递对象的功能了。

作用：

* 永久性保存对象，保存对象的字节序列到本地文件中；

* 通过序列化对象在网络中传递对象；

* 通过序列化在进程间传递对象。

序列化方法的原则

* 在使用内存的时候，Parcelable 比 Serializable 性能高，所以推荐使用 Parcelable。

* Serializable 在序列化的时候会产生大量的临时变量，从而引起频繁的GC。

* Parcelable 不能使用在要将数据存储在磁盘上的情况，因为 Parcelable 不能很好的保证数据的持续性在外界有变化的情况下。尽管 Serializable 效率低点，但此时还是建议使用 Serializable 。

### Json

JSON 的全称是 JavaScript Object Notation，也就是 JavaScript 对象表示法 JSON是存储和交换文本信息的语法，类似XML，但是比XML更小、更快，更易解析 JSON是轻量级的文本数据交换格式，独立于语言，具有可描述性，更易理解，对象可以包含多个名称/值对，比如：

```java
{"name":"test" , "age":25}
```

### Android 为每个应用程序分配的内存大小是多少？

不同手机型号，分配的内存大小不同，可以设置  android:largeheap = "true"。

### Activity 的 startActivity 和 context 的 startActivity区别？

* 从 Activity 中启动新的 Activity 时，可以直接 mContext.startActivity(intent) 

*  Context 中启动 Activity 须给 intent 设置Flag:

```java
intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
```

### 怎么在Service中创建Dialog对话框？

```java
//设置类型
dialog.getWindow().setType(WindowManager.LayoutParams.TYPE_SYSTEM_ALERT)
//权限
<uses-permission android:name="android.permission.SYSTEM_ALERT_WINOW" />
```

### 程序A能否接收到程序B的广播？

可以，使用全局的 BroadCastRecevier 能进行跨进程通信，但是注意它只能被动接收广播，此外，LocalBroadCastRecevier 只限于本进程的广播间通信。

### 数据加载更多涉及到分页，你是怎么实现的？



#### 编译期注解跟运行时注解有何不同？

编译期注解：RetentionPolicy.CLASS，作用域 class 字节码上，生命周期只有在编译器间有效，常使用 APT（注解处理器）+ JavaPoet（Java源代码生成框架），EventBus、Dagger、Retrofit 等使用。

运行时注解：RetentionPolicy.RUNTIME，注解不仅被保存到 class 文件中，jvm 加载 class 文件之后，仍然存在；获取注解，需要通过反射来获取运行时注解。

### 如何解析 xml？

#### SAX

**SAX(Simple API for XML)**：是一种**基于事件的解析器**，事件驱动的流式解析方式，从文件的开始顺序解析到文档的结束，不可暂停或倒退。 
**优点：**解析速度快，占用内存少。非常适合在 Android 移动设备中使用。 
**缺点：**不会记录标签的关系，而要让你的应用程序自己处理，这样就增加了你程序的负担。 
**工作原理：**对文档进行顺序扫描，当扫描到文档(document)开始与结束、元素(element)开始与结束、文档 (document)结束等地方时通知事件处理函数，由事件处理函数做相应动作，然后继续同样的扫描，直至文档结束。 

#### PULL

**PULL：**运行方式和 SAX 类似，都是**基于事件的模**式。不同的是，在 PULL 解析过程中返回的是**数字**，且我们需要自己获取产生的事件然后做相应的操作，而不像 SAX 那样由处理器触发一种事件的方法，执行我们的代码。 

**优点：** PULL解析器小巧轻便，解析速度快，简单易用，非常适合在Android移动设备中使用，Android系统内部在解析各种 XML 时也是用 PULL 解析器，**Android官方推荐开发者们使用Pull解析技术**。Pull解析技术是第三方开发的开源技术，它同样可以应用于 JavaSE 开发。

#### DOM

DOM：即对象文档模型，它是将整个XML文档载入内存(所以效率较低，不推荐使用)，每一个节点当做一个对象，结合代码分析。DOM实现时首先为XML文档的解析定义一组接口，解析器读入整个文档，然后构造一个驻留内存的树结构，这样代码就可以使用DOM接口来操作整个树结构。 由于DOM在内存中以树形结构存放，因此检索和更新效率会更高。**但是对于特别大的文档，解析和加载整个文档将会很耗资源。 当然，如果XML文件的内容比较小，采用DOM是可行的。** 
**工作原理：**使用DOM对XML文件进行操作时，首先要解析文件，将文件分为独立的元素、属性和注释等，然后以节点树的形式在内存中对XML文件进行表示，就可以通过节点树访问文档的内容，并根据需要修改文档。 

### 更新 UI 方式

- Activity.runOnUiThread(Runnable)
- Handler
- View.post(Runnable)，View.postDelay(Runnable, long)（可以理解为在当前操作视图UI线程添加队列）
- AsyncTask
- RxJava
- LiveData

#### merge、ViewStub、include 的作用？

Merge: 删减多余的层级，优化 UI，多用于替换 FrameLayout 或者当一个布局包含另一个时

ViewStub: 按需加载，不会影响 UI 初始化时的性能

include：能够重用布局文件

### jar 和 aar 的区别

jar 包里面只有代码，aar 里面不光有代码还包括资源文件，比如 drawable 文件，xml资源文件。对于一些不常变动的 Android Library，我们可以直接引用 aar，加快编译速度。