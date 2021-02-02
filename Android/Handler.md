## 1 消息机制

Android 消息机制本质上是 Handler 运行机制和 MessageQueue 以及Looper 工作过程，这三者所组成的一个整体运行机制。Android 消息循环机制如下图所示：

![](../asset/消息机制.png)

具体分为四大要素:

- Message(消息)：需要被传递的消息，消息分为硬件产生的消息(如按钮、触摸)和软件生成的消息。
- MessageQueue(消息队列)：**负责消息的存储与管理**，负责管理由 Handler 发送过来的Message。读取会自动删除消息，单链表维护，插入和删除上有优势。在其 next() 方法中会无限循环，不断判断是否有消息，有就返回这条消息并移除。
- Handler(消息处理器)：负责 Message 的发送及处理。主要向消息池发送各种消息事件(Handler.sendMessage())和处理相应消息事件(Handler.handleMessage())，按照先进先出执行，内部使用的是单链表的结构。
- Looper(消息循环器)：负责关联线程以及消息的分发，在该线程下从 MessageQueue获取 Message，分发给Handler，Looper创建的时候会创建一个 MessageQueue，调用loop()方法的时候消息循环开始，其中会不断调用messageQueue的next()方法，当有消息就处理，否则阻塞在messageQueue的next()方法中。当Looper的quit()被调用的时候会调用messageQueue的quit()，此时next()会返回null，然后loop()方法也就跟着退出。

整个消息的循环流程还是比较清晰的：

* Handler 通过 sendMessage() 发送消息 Message 到消息队列 MessageQueue，MessageQueue 负责消息的存储与管理。
* Looper 通过loop() 不断获取 Message，并将 Message 交给对应的 target handler 来处理。

* target handler 调用自身的 handleMessage() 方法来处理 Message。

## 2 消息队列创建

消息机制中有一个很重要的部分就是消息队列 MessageQueue，主要有两个操作插入（enqueueMessage）和读取（next）。我们先来看看消息队列的创建。

```java
public final class MessageQueue {
    ...
    private long mPtr; // 地址值
    private native static long nativeInit();
    ...
    MessageQueue(boolean quitAllowed) {
        mQuitAllowed = quitAllowed;
        mPtr = nativeInit();//本地方法
    }    
}

//Looper 中创建 MessageQueue
public final class Looper {
    
  private Looper(boolean quitAllowed) {
      //创建消息队列
      mQueue = new MessageQueue(quitAllowed);
      //指向当前线程
      mThread = Thread.currentThread();
   }  
}
```

我们可以看到调用本地方法完成初始化。

```c++
static jlong android_os_MessageQueue_nativeInit(JNIEnv* env, jclass clazz) {
    //构建 NativeMessageQueue 对象
    NativeMessageQueue* nativeMessageQueue = new NativeMessageQueue();
    if (!nativeMessageQueue) {
        jniThrowRuntimeException(env, "Unable to allocate native queue");
        return 0;
    }

    nativeMessageQueue->incStrong(env);
    //将对象的地址值转成 long 型传递给 Java 层
    return reinterpret_cast<jlong>(nativeMessageQueue);
}
```

接下来我们看看 NativeMessageQueue。

```c++
NativeMessageQueue::NativeMessageQueue() : //继承 NativeMessageQueue
        mPollEnv(NULL), mPollObj(NULL), mExceptionObj(NULL) {
   
    //判断是否为当前线程创建过了 Looper 对象
    mLooper = Looper::getForThread();
    if (mLooper == NULL) {
        //创建 Looper 对象
        mLooper = new Looper(false);
        //为线程设置 Looper
        Looper::setForThread(mLooper);
    }
}
```

接下来看看如何构造 Looper。

```java
Looper::Looper(bool allowNonCallbacks) :
        mAllowNonCallbacks(allowNonCallbacks), mSendingMessage(false),
        mResponseIndex(0), mNextMessageUptime(LLONG_MAX) {
    int wakeFds[2];
    //创建管道
    int result = pipe(wakeFds);
    LOG_ALWAYS_FATAL_IF(result != 0, "Could not create wake pipe.  errno=%d", errno);
    //读端文件描述符
    mWakeReadPipeFd = wakeFds[0];
    //写端文件描述符
    mWakeWritePipeFd = wakeFds[1];
    ...
    //创建 epoll 实例，将它的文件描述符保存在变量 mEpollFd 中
    mEpollFd = epoll_create(EPOLL_SIZE_HINT);
    LOG_ALWAYS_FATAL_IF(mEpollFd < 0, "Could not create epoll instance.  errno=%d", errno);
    struct epoll_event eventItem;
    memset(& eventItem, 0, sizeof(epoll_event)); // zero out unused members of data field union
    eventItem.events = EPOLLIN;
    eventItem.data.fd = mWakeReadPipeFd;
    //将管道读端描述符添加到 epoll 中，以便监听管道的写操作
    result = epoll_ctl(mEpollFd, EPOLL_CTL_ADD, mWakeReadPipeFd, & eventItem);
    LOG_ALWAYS_FATAL_IF(result != 0, "Could not add wake read pipe to epoll instance.  errno=%d",
            errno);
}
```

pipe、epoll 是 Linux 端的知识，这里简单解释一下。

* 管道（pipe）是一种最基本的 IPC 机制，作用于有血缘关系的进程之间，完成数据传递。
* epoll：I/O多路复用，监听多个文件描述符的IO读写事件，是Linux内核为处理大批量文件描述符]而作了改进的poll。

## 3 消息的添加

我们通常会调用 handler 的 sendXXX() 或 postXXX() ，实际调用的 MessageQueue的enqueueMessage()方法，将消息插入到目标线程的消息队列中。

```java
public final class MessageQueue {
    
      boolean enqueueMessage(Message msg, long when) {
            //每个消息都必须有个target handler
            if (msg.target == null) {
                throw new IllegalArgumentException("Message must have a target.");
            }
            
            //每个消息必须没有被使用
            if (msg.isInUse()) {
                throw new IllegalStateException(msg + " This message is already in use.");
            }
            //加锁
            synchronized (this) {
                //正在退出时，回收 Message，加入消息池。
                if (mQuitting) {
                    ...
                    //回收   
                    msg.recycle();
                    return false;
                }
    
                msg.markInUse();
                msg.when = when;
                //mMessages表示当前需要处理的消息，队头的消息
                Message p = mMessages;
                boolean needWake;
                
                if (p == null || when == 0 || when < p.when) {
                    // New head, wake up the event queue if blocked.
                    msg.next = p;
                    mMessages = msg;
                    needWake = mBlocked;
                } else {
                    needWake = mBlocked && p.target == null && msg.isAsynchronous();
                    //将消息按照时间顺序插入到消息队列中
                    Message prev;
                    for (;;) {
                        prev = p;
                        p = p.next;
                        if (p == null || when < p.when) {
                            break;
                        }
                        if (needWake && p.isAsynchronous()) {
                            needWake = false;
                        }
                    }
                    msg.next = p; // invariant: p == prev.next
                    prev.next = msg;
                }
                //唤醒消息队列
                if (needWake) {
                    nativeWake(mPtr);
                }
            }
            return true;
        }
}
```

## 3 消息循环

使用 Looper 来进行消息循环。

```java
public class LooperThread extends Thread {
    public Handler mHandler;
    public void run() {
        Looper.prepare();
        mHandler = new Handler() {
            public void handleMessage(Message msg) {
                // process incoming messages here
            }
        };
        Looper.loop();
    }
        
//Looper.prepare()
private static void prepare(boolean quitAllowed) {
  if (sThreadLocal.get() != null) {
    throw new RuntimeException("Only one Looper may be created per thread");
  }
  sThreadLocal.set(new Looper(quitAllowed));
}
    
//创建主线程的Looper，在 ActivityThread 中使用，一般我们用不到
public static void prepareMainLooper() {
        prepare(false);
        synchronized (Looper.class) {
            if (sMainLooper != null) {
                throw new IllegalStateException("The main Looper has already been prepared.");
            }
            sMainLooper = myLooper();
       }
}    
```

Looper 使用 Looper.prepare() 方法来创建 Looper ，并且会使用 ThreadLocal 来实现与当前线程的绑定功能。然后 Looper.loop()  则不断从 MessageQueue 中获取 Message 。

```java
public final class Looper {
     ...
     public static void loop() {
        //获取当前线程的 Looper
        final Looper me = myLooper();
        if (me == null) {
            throw new RuntimeException("No Looper; Looper.prepare() wasn't called on this thread.");
        }
        
        //获取当前线程的消息队列
        final MessageQueue queue = me.mQueue;
        //确保当前线程处于本地进程中，Handler仅限于处于同一进程间的不同线程的通信。
        Binder.clearCallingIdentity();
        final long ident = Binder.clearCallingIdentity();
        //进入loop主循环方法
        for (;;) {
            //不断的获取下一条消息，这个方法可能会被阻塞
            Message msg = queue.next();
            if (msg == null) {
                return;
            }       
            ...
            //处理消息
            try {
                msg.target.dispatchMessage(msg);
            } finally {
                ...
            }
            ...  
            //把message回收到消息池，复用。
            msg.recycleUnchecked();
        }
     }
}
```

loop() 方法主要做了三件事：

* 调用 MessageQueue#next() 读取下一条 Message。

* 把 Message 分发给相应的 target，调用 dispatchMessage()。
* 再把分发的 Message 回收到消息池，以便重复利用。

## 5 消息的分发与处理

Looper.loop() 里面调用 next()  和 dispatchMessage() 对消息进行分发与处理。

### 5.1 消息的分发

```java
public final class MessageQueue {
    
    Message next() {
            ...
           //注册到消息队列中空闲Handler个个数
           int pendingIdleHandlerCount = -1; 
           //表示无消息到来时，当前线程需要进入睡眠状态的时间，
           //0:不进入睡眠状态，-1:进入无限等待的睡眠状态，直到有人将它唤醒
           int nextPollTimeoutMillis = 0;
           for (;;) {
               if (nextPollTimeoutMillis != 0) {
                   Binder.flushPendingCommands();
               }
   
               //阻塞操作，检测当前线程的消息队列中是否有消息需要处理
               //里面也是 pipe / epoll
               nativePollOnce(ptr, nextPollTimeoutMillis);
   
               //查询下一条需要执行的消息
               synchronized (this) {
                   final long now = SystemClock.uptimeMillis();
                   Message prevMsg = null;
                   //mMessages代表了当前线程需要处理的消息
                   Message msg = mMessages;               
                   if (msg != null && msg.target == null) {
                       do {
                           prevMsg = msg;
                           msg = msg.next;
                       } while (msg != null && !msg.isAsynchronous());
                   }
                   if (msg != null) {
                       
                       if (now < msg.when) {
                           //如果当前消息头是延时消息，比当前时间长的话，计算延时等待的时间并赋值
                           nextPollTimeoutMillis = (int) Math.min(msg.when - now, Integer.MAX_VALUE);
                       } 
                       //如果消息的执行时间小于当前时间，则说明该消息需要立即执行，则将该消息返回，并从消息队列中                    
                       else {
                           mBlocked = false;
                           if (prevMsg != null) {
                               prevMsg.next = msg.next;
                           } else {
                               mMessages = msg.next;
                           }
                           msg.next = null;
                           ...
                           return msg;
                       }
                   } else {
                       // 如果没有消息需要处理，将nextPollTimeoutMillis置为-1，让当前线程进入无限睡眠状态，直到被其他线程唤醒。
                       nextPollTimeoutMillis = -1;
                   }
   
                   //所有消息都已经被处理，准备退出。
                   if (mQuitting) {
                       dispose();
                       return null;
                   }  
                   //pendingIdleHandlerCount:等待执行的Handler的数量
                   //mIdleHandlers:空闲 Handler 列表
                   if (pendingIdleHandlerCount < 0
                           && (mMessages == null || now < mMessages.when)) {
                       pendingIdleHandlerCount = mIdleHandlers.size();
                   }
                   if (pendingIdleHandlerCount <= 0) {
                       //当没有空闲的Handler需要执行时进入阻塞状态
                       mBlocked = true;
                       continue;
                   }
   
                   //mPendingIdleHandler:IdleHandler数组
                   if (mPendingIdleHandlers == null) {
                       mPendingIdleHandlers = new IdleHandler[Math.max(pendingIdleHandlerCount, 4)];
                   }
                   mPendingIdleHandlers = mIdleHandlers.toArray(mPendingIdleHandlers);
               }
   
               //只有在第一次循环时，才会去执行idle handlers，执行完成后重置pendingIdleHandlerCount为0
               for (int i = 0; i < pendingIdleHandlerCount; i++) {
                   final IdleHandler idler = mPendingIdleHandlers[i];
                   //释放 Handler 的引用
                   mPendingIdleHandlers[i] = null;
   
                   boolean keep = false;
                   try {
                       keep = idler.queueIdle();
                   } catch (Throwable t) {
                       Log.wtf(TAG, "IdleHandler threw exception", t);
                   }
   
                   if (!keep) {
                       synchronized (this) {
                           mIdleHandlers.remove(idler);
                       }
                   }
               }
               pendingIdleHandlerCount = 0;         
               nextPollTimeoutMillis = 0;
           }
       } 
}
```



### 5.2 消息的处理

```java
public class Handler {
        ...
        public void dispatchMessage(Message msg) {
            //当Message存在回调方法时，优先调用Message的回调方法message.callback.run()
            if (msg.callback != null) {
                //实际调用的就是message.callback.run();
                handleCallback(msg);
            } else {
                //如果我们设置了Callback回调，优先调用Callback回调。
                if (mCallback != null) {
                    if (mCallback.handleMessage(msg)) {
                        return;
                    }
                }
                //如果我们没有设置了Callback回调，则回调自身的Callback方法。
                handleMessage(msg);
            }
        }
}
```

Looper.loop() 是个死循环，不断调用 MessageQueue.next() 获取 Message ，并调用msg.target.dispatchMessage(msg) 切换到 Handler 来分发消息，以此来完成消息的回调。