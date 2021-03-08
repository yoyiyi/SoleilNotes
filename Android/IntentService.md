## 1 简介

* 本质是一种特殊的Service，继承自Service，本身就是一个抽象类。
* 可以用于在后台执行耗时的异步任务，当任务完成后会自动停止。
* 拥有较高的优先级，不易被系统杀死（继承自Service的缘故），因此比较适合执行一些高优先级的异步任务。
* 内部通过 HandlerThread 和 Handler 实现异步操作。
* 创建 IntentService 时，只需实现 onHandleIntent 和 构造方法，onHandleIntent 为异步方法，可以执行耗时操作。

## 2 原理

先从构造函数入手。

### IntentService

```java
private String mName;

public IntentService(String name) {
       //IntentService 继承 Service，调用 Service。
       super();
       mName = name;
}
```

接下来看看 onCreate() 方法。

### IntentService#onCreate()

```java
@Override
    public void onCreate() {
        super.onCreate();
        //创建 HandlerThread 的变量，结合mName 进行命名，为了获取它的 Looper 和消息队列
        HandlerThread thread = new HandlerThread("IntentService[" + mName + "]");
        thread.start();
        //获取到 HandlerThread 的 Looper
        mServiceLooper = thread.getLooper();
        //创建 ServiceHandler
        mServiceHandler = new ServiceHandler(mServiceLooper);
    }
```

### ServiceHandler

```java
  private final class ServiceHandler extends Handler {
        public ServiceHandler(Looper looper) {
            super(looper);
        }

        @Override
        public void handleMessage(Message msg) {
            //将消息转换为 Inetnt
            onHandleIntent((Intent)msg.obj);
            //msg.arg1:Message 的startId
            stopSelf(msg.arg1);
        }
    }
	//全部任务都调用 stopSelf 过后才会回调 onDestroy()，退出工作线程的Looper循环
    public void onDestroy() {
        mServiceLooper.quit();
    }
```

### IntentService#onStart()

从上面可以看出有一个 Message，创建在 onStart()

```java
    @Override
    public int onStartCommand(@Nullable Intent intent, int flags, int startId) {
        onStart(intent, startId);
        return mRedelivery ? START_REDELIVER_INTENT : START_NOT_STICKY;
    }

    @Override
    public void onStart(@Nullable Intent intent, int startId) {
        Message msg = mServiceHandler.obtainMessage();
        msg.arg1 = startId;
        msg.obj = intent;
        //mServiceHandler 发送消息
        mServiceHandler.sendMessage(msg);
    }

```

IntentService的机制核心是 **Handler 和 消息队列**，每次调用 startService(new Intent)，给 IntentService 添加一个任务。在 IntentService 的内部，第一次启动时，会构建 IntentService 对象，开始初始化工作：通过 HandlerThread 获取到一个工作线程的 Looper，用来构建它的核心Handler。然后每当有一个任务被添加进来，内部就会创建一个附带着 Intent 的 Message 对象，使用 IntentService 内部的 Handler 发送 Message。Looper 从消息队列中循环地取出 Message 传递给这个 Handler，Handler 就会在工作线程上依次处理这些消息任务的Intent。
