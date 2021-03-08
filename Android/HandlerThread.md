## 1 简介

* 继承自 Thread 的类，本质是一个线程；
* 持有一个可用来构建 Handler 的子线程 Looper；

## 2 原理

通常使用如下：

```java
handlerThread = new HandlerThread("HandlerThread-1");
handlerThread.start();
//handlerThread.getLooper() 获取子线程的 Looper
taskHandler = new TaskHandler(handlerThread.getLooper());
```

### HandlerThread#getLooper()

```java
public Looper getLooper() {
        //判断当前线程是否已经开启
        if (!isAlive()) {
            return null;
        }       
        // 如果线程已开启但Looper未被创建，会进入同步代码块，阻塞-->直到Looper被创建
        synchronized (this) {
            while (isAlive() && mLooper == null) {
                try {
                    //mLooper==null-->线程进入阻塞状态
                    wait();
                } catch (InterruptedException e) {
                }
            }
        }
        //确保 返回的mLooper不为null
        return mLooper;
    }
```

那么 mLooper 在那里赋值，接着往下看。

### HandlerThread#run()

```java
   @Override
    public void run() {
        mTid = Process.myTid();
        //创建此线程的 Looper 和 MessageQueue
        Looper.prepare();
        synchronized (this) {
            //给 mLooper 赋值
            mLooper = Looper.myLooper();
            //此时 mLooper!=null--> 取消线程阻塞
            notifyAll();
        }
        //为线程设置mPriority优先级
        Process.setThreadPriority(mPriority);
        onLooperPrepared();
        //开始 loop
        Looper.loop();
        mTid = -1;
    }  
```

开启 HandlerThread 线程后，会创建此线程的 Looper 和 MessageQueue，设置线程优先级，并且开始 Looper 循环。

那么，还有一个问题 Handler 在那里。

HandlerThread#getThreadHandler()

```java
   private @Nullable Handler mHandler;
    
    /**
     * 返回与此线程相关联的一个Handler实例
     * @hide 目前此方法是被隐藏的，无法正常直接调用
     */
	@NonNull
    public Handler getThreadHandler() {
        if (mHandler == null) {
            mHandler = new Handler(getLooper());
        }
        return mHandler;
    }
```

当外界调用 getThreadHandler() 的时候，才会对 mHandler 实例化。

HandlerThread 这个类与 Looper 的关系是密不可分，所以也会有退出Looper的办法。

```java
    public boolean quit() {
        Looper looper = getLooper();
        if (looper != null) {
            looper.quit();
            return true;
        }
        return false;
    }
    
    public boolean quitSafely() {
        Looper looper = getLooper();
        if (looper != null) {
            //允许消息队列中还在排队的消息都被取出后再关闭，避免所有挂起的任务无法有序的被完成。
            looper.quitSafely();
            return true;
        }
        return false;
    }
```

HandlerThread 本质是一个 Thread，在 run 中不是执行耗时任务，而是创建了该线程的 **Looper 和 消息队列**，外界 Handler 可以很方便获取到这个 Looper，搭配执行耗时任务，适合串行执行耗时任务等场景。源码当中典型场景就是 IntentService 。

