## 1 简介

RxJava 是一个在 Java 虚拟机上使用可观测的序列来组成**异步**的、**基于事件流**的程序的库。

## 2 原理

RxJava 基于一种扩展的观察者模式，包含以下四个角色。

* 被观察者（Observable）：产生事件。
* 观察者（Observer）：接收事件，作出响应动作。
* 订阅（Subscribe）：连接被观察者和观察者。
* 事件（Event）：被观察者和 观察者沟通桥梁。

RxJava 的核心 是

## 3 基本使用

RxJava 基本使用如下：

```java
Observable.create(new ObservableOnSubscribe<Object>() {
        @Override
        public void subscribe(ObservableEmitter<Object> emitter) throws Exception {
            emitter.onNext(1);
            emitter.onComplete();
        }
    })                                               			     .subscribeOn(Schedulers.io())//指定事件源代码执行的线程
                .observeOn(AndroidSchedulers.mainThread())//指定订阅者代码执行的线程
                .subscribe(new Observer<Object>() {
                @Override
                public void onSubscribe(Disposable d) {
                    Log.d("RxJava:", "onSubscribe");
                }

                @Override
                public void onNext(Object o) {
                    Log.d("RxJava:", "onNext"+o.toString());
                }

                @Override
                public void onError(Throwable e) {
                    Log.d("RxJava:", "onError");
                }

                @Override
                public void onComplete() {
                    Log.d("RxJava:", "onComplete");
                }
            })//参数是我们创建的一个订阅者，在这里与事件流建立订阅关系
```

从上面我们可以看出 RxJava 的核心包括以下三点：

* 被观察者创建
* 线程切换
* 订阅流程

## 4 原理

### 4.1 被观察者创建

##### Observable#create()

```java
public static <T> Observable<T> create(ObservableOnSubscribe<T> source) {
    ObjectHelper.requireNonNull(source, "source is null");
    //创建 ObservableCreate对象
    return RxJavaPlugins.onAssembly(new ObservableCreate<T>(source));
}
```

##### ObservableCreate

```java
public final class ObservableCreate<T> extends Observable<T> {

    final ObservableOnSubscribe<T> source;

    public ObservableCreate(ObservableOnSubscribe<T> source) {
        //保存 ObservableOnSubscribe
        this.source = source;
    }
    ...
}
```

##### RxJavaPlugins.onAssembly

```java
public static <T> Observable<T> onAssembly(@NonNull Observable<T> source) {
    ...
    //返回 ObservableCreate    
    return source;
}
```

把自定义的 ObservableOnSubscribe 对象包装成了 ObservableCreate对象。

### 4.2 线程切换

#### subscribeOn(Schedulers.io())

这个方法中，需要传入一个 Scheduler 调度类，这里是传入了一个调度到 IO 线程的调度类。

##### Schedulers#io

```java
static final Scheduler IO;
...
public static Scheduler io() {
    //1.处理hook的逻辑，返回传入的 IO 对象
    return RxJavaPlugins.onIoScheduler(IO);
}

static {
    ...
    //2.创建 IOTask 静态内部类 IOTask 实现 Callable 接口
    IO = RxJavaPlugins.initIoScheduler(new IOTask());
}

static final class IOTask implements Callable<Scheduler> {
    @Override
    public Scheduler call() throws Exception {
        //3.返回 IoScheduler
        return IoHolder.DEFAULT;
    }
}

static final class IoHolder {
    static final Scheduler DEFAULT = new IoScheduler();
}
```

##### Observable#subscribeOn()

```java
 public final Observable<T> subscribeOn(Scheduler scheduler) {
    ...
    //将 ObservableCreate 包装成 ObservableSubscribeOn 对象
    return RxJavaPlugins.onAssembly(new ObservableSubscribeOn<T>(this, scheduler));
}
```

##### ObservableSubscribeOn

```java
public final class ObservableSubscribeOn<T> extends AbstractObservableWithUpstream<T, T> {
    final Scheduler scheduler;

    public ObservableSubscribeOn(ObservableSource<T> source, Scheduler scheduler) {
        //1.保存 source 和 scheduler
        super(source);
        this.scheduler = scheduler;
    }

    //实际订阅,执行
    @Override
    public void subscribeActual(final Observer<? super T> observer) {
        //2.自定义的Observer包装成了 SubscribeOnObserver 对象
        final SubscribeOnObserver<T> parent = new SubscribeOnObserver<T>(observer);

        //3.通知观察者
        observer.onSubscribe(parent);

        //4.创建了一个 SubscribeTask
        parent.setDisposable(scheduler.scheduleDirect(new SubscribeTask(parent)));
    }

...
}
```

##### ObservableSubscribeOn#SubscribeTask

```java
//SubscribeTask 实现 Runnable 接口
final class SubscribeTask implements Runnable {
    private final SubscribeOnObserver<T> parent;

    SubscribeTask(SubscribeOnObserver<T> parent) {
        this.parent = parent;
    }

    @Override
    public void run() {
        //source 其实就是 ObservableCreate 对象
        source.subscribe(parent);
    }
}
```

##### Scheduler#scheduleDirect()

```java
public Disposable scheduleDirect(@NonNull Runnable run) {
    return scheduleDirect(run, 0L, TimeUnit.NANOSECONDS);
}

public Disposable scheduleDirect(@NonNull Runnable run, long delay, @NonNull TimeUnit unit) {

    //1.创建 Worker  代码一
    final Worker w = createWorker();

    //2.hook 的封装处理，返回的当前 run
    final Runnable decoratedRun = RxJavaPlugins.onSchedule(run);

    //3.新建 DisposeTask 
    DisposeTask task = new DisposeTask(decoratedRun, w);

    //4.执行 schedule 方法  代码二
    w.schedule(task, delay, unit);
    
    return task;
}
```

#####  代码一：IOScheduler#createWorker()

```java
final AtomicReference<CachedWorkerPool> pool;
...
public IoScheduler(ThreadFactory threadFactory) {
    this.threadFactory = threadFactory;//线程工厂
    this.pool = new AtomicReference<CachedWorkerPool>(NONE);
    start();
}
...

@Override
public Worker createWorker() {
    //1.获取 Worker
    return new EventLoopWorker(pool.get());
}

static final class EventLoopWorker extends Scheduler.Worker {
    ...
    EventLoopWorker(CachedWorkerPool pool) {
        this.pool = pool;
        this.tasks = new CompositeDisposable();
        //2.缓存 Worker
        this.threadWorker = pool.get();
    }
}
```

##### 代码二：IOScheduler#schedule()

```java
@Override
public Disposable schedule(@NonNull Runnableaction, long delayTime, @NonNull TimeUnit unit){
    ...
    //执行 scheduleActual -> NewThreadWorker#scheduleActual()
    return threadWorker.scheduleActual(action,delayTime, unit, tasks);
}
```

##### NewThreadWorker#scheduleActual()

```java
public NewThreadWorker(ThreadFactory threadFactory) {
    executor = SchedulerPoolFactory.create(threadFactory);
}


@NonNull
public ScheduledRunnable scheduleActual(final Runnable run, long delayTime, @NonNull TimeUnit unit, @Nullable DisposableContainer parent) {
    Runnable decoratedRun = RxJavaPlugins.onSchedule(run);

    //1.创建 run 
    ScheduledRunnable sr = new ScheduledRunnable(decoratedRun, parent);

    if (parent != null) {
        if (!parent.add(sr)) {
            return sr;
        }
    }

    Future<?> f;
    try {
        //2.是否延迟时间
        if (delayTime <= 0) {
            //3.调用线程池的 submit() 进行线程切换
            f = executor.submit((Callable<Object>)sr);
        } else {
            //4.延时执行线程切换
            f = executor.schedule((Callable<Object>)sr, delayTime, unit);
        }
        sr.setFuture(f);
    } catch (RejectedExecutionException ex) {
        ...
    }
    return sr;
}
```

#### observeOn(AndroidSchedulers.mainThread())

```java
public final Observable<T> observeOn(Scheduler scheduler, boolean delayError, int bufferSize) {
    ....
    //返回 ObservableObserveOn 对象
    return RxJavaPlugins.onAssembly(new ObservableObserveOn<T>(this, scheduler, delayError, bufferSize));
}
```

##### ObservableObserveOn#subscribeActual()

```java
@Override
protected void subscribeActual(Observer<? super T> observer) {
    //如果是 TrampolineScheduler 不切换
    if (scheduler instanceof TrampolineScheduler) {
        source.subscribe(observer);
    } else {
        //2.创建一个工作者对象
        Scheduler.Worker w = scheduler.createWorker();
        //3.创建 ObserveOnObserver
        source.subscribe(new ObserveOnObserver<T>(observer, w, delayError, bufferSize));
    }
}
```

##### ObserveOnObserver

```java
@Override
public void onNext(T t) {
    ...
    if (sourceMode != QueueDisposable.ASYNC) {
        //1.事件元素存放到队列
        queue.offer(t);
    }
    schedule();
}

@Override
public void onError(Throwable t) {
    ...
    schedule();
}

@Override
public void onComplete() {
    ...
    schedule();
}
```

##### ObserveOnObserver#schedule()

```java
void schedule() {
    if (getAndIncrement() == 0) {
        //调用工作者 worker 内部 Handler进行线程切换
        worker.schedule(this);
    }
}
```

##### ObserveOnObserver#run()

```java
@Override
public void run() {
    //1.背压及操作符相关
    if (outputFused) {
        drainFused();
    } else {
        //2.调用 drainNormal()
        drainNormal();
    }
}
```

##### ObserveOnObserver#run()

```java
oid drainNormal() {
    ...
    //1.队列中取元素
    v = q.poll();

    ...
    //2.调用 onNext
    a.onNext(v);
}

```

### 4.3 订阅流程

##### Observable#subscribe()

```java
public final void subscribe(Observer<? super T> observer) {
    ...
    //1.调用 RxJavaPlugins.onSubscribe
    observer = RxJavaPlugins.onSubscribe(this,observer);
    ...
    //2.调用 subscribeActual
    subscribeActual(observer);

}
```

##### ObservableCreate#subscribeActual()

```java
@Override
protected void subscribeActual(Observer<? super T> observer) {
    //1.创建 CreateEmitter 代码一
    //
    CreateEmitter<T> parent = new CreateEmitter<T>(observer);
    //2.通知观察者已经成功订阅
    observer.onSubscribe(parent);
    try {
        source.subscribe(parent);
    } catch (Throwable ex) {
        ...
    }
}
```

##### 代码一：CreateEmitter

```java
static final class CreateEmitter<T> extends AtomicReference<Disposable>
implements ObservableEmitter<T>, Disposable {
    final Observer<? super T> observer;
    CreateEmitter(Observer<? super T> observer) {
		//缓存设置的观察者 Observer
        this.observer = observer;
    }
	//ObservableOnSubscribe的subscribe 调用的emitter.onNext(1);
    @Override
    public void onNext(T t) {
        ...
		//判断是否取消了订阅
        if (!isDisposed()) {
			//执行 Observer 的 onNext
            observer.onNext(t);
        }
    }
    @Override
    public void onError(Throwable t) {
        if (!tryOnError(t)) {
			//设置hook方法 忽略
            RxJavaPlugins.onError(t);
        }
    }

    @Override
    public boolean tryOnError(Throwable t) {
		//判空
        if (t == null) {
            t = new NullPointerException("onError called with null. Null values are generally not allowed in 2.x operators and sources.");
        }
		//判断是否取消了订阅 取消则不执行
        if (!isDisposed()) {
            try {
				//执行 Observer 的 onError
                observer.onError(t);
            } finally {
                dispose();
            }
            return true;
        }
        return false;
    }
	
    @Override
    public void onComplete() {
        //判断是否取消了订阅 取消则不执行
        if (!isDisposed()) {
            try {
                observer.onComplete();
            } finally {
                dispose();
            }
        }
    }
	//存储Disposable类 用来判断是否取消了订阅
    @Override
    public void setDisposable(Disposable d) {
        DisposableHelper.set(this, d);
    }
	
    @Override
    public void setCancellable(Cancellable c) {
        setDisposable(new CancellableDisposable(c));
    }

    @Override
    public ObservableEmitter<T> serialize() {
        return new SerializedEmitter<T>(this);
    }
	//取消订阅
    @Override
    public void dispose() {
        DisposableHelper.dispose(this);
    }
	//判断是否取消了订阅
    @Override
    public boolean isDisposed() {
        return DisposableHelper.isDisposed(get());
    }

    @Override
    public String toString() {
        return String.format("%s{%s}", getClass().getSimpleName(), super.toString());
    }
}
```

* 创建 ObservableOnSubscribe 对象，并且实现 subscribe(ObservableEmitter emitter)，利用 emitter发射数据。
* 创建 ObservableCreate 对象，该类实现了 Observable 接口。
* Observer 订阅 Observable 调用 ObservableCreate 的 subscribeActual(observer)。
* 创建 ObservableEmitter 对象的 CreateEmitter对象，调用 Observer 的 onSubscribe()。
* 调用 ObservableOnSubscribe 的 subscribe()：即实现的发射数据的方法。