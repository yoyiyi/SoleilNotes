## 1  基本使用

Glide 是一个图片加载库，基本使用如下：

```kotlin
Glide.with(this).load("http://xxxx.jpg").apply(RequestOptions()).into(iv)
```

从上面的代码可以看出，Glide 基本使用分为三步：**with() -> load() -> into()**

## 2 with()

进入到 with 代码

```java
@NonNull
public static RequestManager with(@NonNull FragmentActivity activity) {
    return getRetriever(activity).get(activity);
}

//最终调到 initializeGlide(Context, new GlideBuilder()) 初始化 Glide

 private static void initializeGlide(@NonNull Context context, @NonNull GlideBuilder builder) {
        //1.获取带注解的 GlideModule
        Context applicationContext = context.getApplicationContext();
        GeneratedAppGlideModule annotationGeneratedModule = getAnnotationGeneratedGlideModules();
        List<GlideModule> manifestModules = Collections.emptyList();
        if (annotationGeneratedModule == null || annotationGeneratedModule.isManifestParsingEnabled()) {
            manifestModules = (new ManifestParser(applicationContext)).parse();
        }
        ...
        
        //2.初始化 Glide 配置信息   
        Glide glide = builder.build(applicationContext);
        Iterator var13 = manifestModules.iterator();
        while(var13.hasNext()) {
            GlideModule module = (GlideModule)var13.next();
            module.registerComponents(applicationContext, glide, glide.registry);
        }

        if (annotationGeneratedModule != null) {
            annotationGeneratedModule.registerComponents(applicationContext, glide, glide.registry);
        }

        applicationContext.registerComponentCallbacks(glide);
        Glide.glide = glide;
    }


//GlideBuiler.java
 @NonNull
  Glide build(@NonNull Context context) {
    //1.创建请求图片线程池 sourceExecutor  
    if (sourceExecutor == null) {
      sourceExecutor = GlideExecutor.newSourceExecutor();
    }
    //2.创建硬盘缓存线程池 diskCacheExecutor
    if (diskCacheExecutor == null) {
      diskCacheExecutor = GlideExecutor.newDiskCacheExecutor();
    }
    //3.创建动画线程池 animationExecutor
    if (animationExecutor == null) {
      animationExecutor = GlideExecutor.newAnimationExecutor();
    }
    //4.计算内存缓存和 bitmap 池的大小
    if (memorySizeCalculator == null) {
      memorySizeCalculator = new MemorySizeCalculator.Builder(context).build();
    }

    if (connectivityMonitorFactory == null) {
      connectivityMonitorFactory = new DefaultConnectivityMonitorFactory();
    }

    if (bitmapPool == null) {
      int size = memorySizeCalculator.getBitmapPoolSize();
      if (size > 0) {
        //5.创建图片线程池 LruBitmapPool，缓存所有被释放的 bitmap
        bitmapPool = new LruBitmapPool(size);
      } else {
        bitmapPool = new BitmapPoolAdapter();
      }
    }
    //6.创建对象数组缓存池 LruArrayPool，默认 4M
    if (arrayPool == null) {
      arrayPool = new LruArrayPool(memorySizeCalculator.getArrayPoolSizeInBytes());
    }
    //7.创建内存缓存,LruResourceCache
    if (memoryCache == null) {
      memoryCache = new LruResourceCache(memorySizeCalculator.getMemoryCacheSize());
    }

    if (diskCacheFactory == null) {
      diskCacheFactory = new InternalCacheDiskCacheFactory(context);
    }
    //8.创建任务和资源管理引擎（线程池，内存缓存和硬盘缓存对象）
    if (engine == null) {
      engine =
          new Engine(
              memoryCache,
              diskCacheFactory,
              diskCacheExecutor,
              sourceExecutor,
              GlideExecutor.newUnlimitedSourceExecutor(),
              GlideExecutor.newAnimationExecutor(),
              isActiveResourceRetentionAllowed);
    }

    RequestManagerRetriever requestManagerRetriever =
        new RequestManagerRetriever(requestManagerFactory);
    //9.创建 Glide
    return new Glide(
        context,
        engine,
        memoryCache,
        bitmapPool,
        arrayPool,
        requestManagerRetriever,
        connectivityMonitorFactory,
        logLevel,
        defaultRequestOptions.lock(),
        defaultTransitionOptions);
  }
}

//Glide
Glide(...) {
   ...
   //注册管理任务执行对象的类(Registry)    
   registry = new Registry();    
   ... 
   registry
        .append(ByteBuffer.class, new ByteBufferEncoder())    
        ...//配置一堆
    
    
}

//配置完Glide，需要把 Glide 与组件的生命周期关联
@NonNull
public RequestManager get(@NonNull Context context) {
  if (context == null) {
    throw new IllegalArgumentException("You cannot start a load on a null Context");
  } else if (Util.isOnMainThread() && !(context instanceof Application)) {
    //当前线程是主线程且 context 不是 Application，周期与相应的组件关联
    if (context instanceof FragmentActivity) {
      return get((FragmentActivity) context);
    } else if (context instanceof Activity) {
      return get((Activity) context);
    } else if (context instanceof ContextWrapper) {
      return get(((ContextWrapper) context).getBaseContext());
    }
  }
  //直接将请求与ApplicationLifecycle关联
  return getApplicationManager(context);
}
```

**with()作用：**

* 初始化 Glide 各种配置信息
* 把 Glide 生命周期与组件（Activity、Application、Fragment等）关联起来

## 3 load()

load() 方法最终会调用以下：

```java
//RequestManager（绑定管理生命周期） 创建 RequestBuilder
private RequestBuilder<TranscodeType> loadGeneric(@Nullable Object model) {
    this.model = model;//url
    isModelSet = true;
    return this;
  }
```

给 GlideRequest（RequestManager）设置请求的mode（url），并记录url 已设置的状态。

## 4 into()

into 最终会走到 RequestBuilder#into。RequestBuilder 作用：**构建 Request 请求，构建 Target**。

```java
//step1 
@NonNull
  public ViewTarget<ImageView, TranscodeType> into(@NonNull ImageView view) {
    //主线程
    Util.assertMainThread();
  
    //请求信息配置
    RequestOptions requestOptions = this.requestOptions;
    ...
    return into(
        glideContext.buildImageViewTarget(view, transcodeClass),
        /*targetListener=*/ null,
        requestOptions);
  }

//step2
 private <Y extends Target<TranscodeType>> Y into(
      @NonNull Y target,
      @Nullable RequestListener<TranscodeType> targetListener,
      @NonNull RequestOptions options) {   
    //通过 ImageViewTarget 构建 Request 对象
    Request request = buildRequest(target, targetListener, options);
    Request previous = target.getRequest();
    if (request.isEquivalentTo(previous)
        && !isSkipMemoryCacheWithCompletePreviousRequest(options, previous)) {
      request.recycle();
      if (!Preconditions.checkNotNull(previous).isRunning()) {
        //让 Engine 处理 Request 
        previous.begin();
      }
      return target;
    }

  //step3
  //SingleRequest.class   
   public void begin() {
    ...
     if (status == Status.COMPLETE) {
       onResourceReady(resource, DataSource.MEMORY_CACHE);
       return;
     }
    status = Status.WAITING_FOR_SIZE;
    if (Util.isValidDimensions(overrideWidth, overrideHeight)) {
      onSizeReady(overrideWidth, overrideHeight);
    } else {
      target.getSize(this);
    }
     ...
  }

  public void onSizeReady(int width, int height) {
     ...
    loadStatus = engine.load(...);
  } 
//以上代码：如果 Imageview 还没有绘制好 Request.begin() 不会执行，ImageViewTarget 会注册 View 的OnPreDrawListener 事件， View 准备好后，会调用 onSizeReady()    
```

最后的工作交给 **Engine** 处理。

```java
 public <R> LoadStatus load(...) {
     ...
    //创建 EngineJob 用于开启 DecodeJob，管理 load 过程的回调
    EngineJob<R> engineJob = engineJobFactory.build(...);
     //创建 DecodeJob
    DecodeJob<R> decodeJob = decodeJobFactory.build(...);
  } 
    engineJob.addCallback(cb);
    //启动 decodeJob
    engineJob.start(decodeJob);

//DecodeJob 作用
//1.从缓存或数据源中加载原始数据
//2.通过解码器转换为相应的资源类型

//EngineJob.java
  public void start(DecodeJob<R> decodeJob) {
    this.decodeJob = decodeJob;//Runnable
    GlideExecutor executor = decodeJob.willDecodeFromCache()
        ? diskCacheExecutor
        : getActiveSourceExecutor();
    executor.execute(decodeJob);//线程池
  }


//DecodeJob.java
 public void run() {
    try {
      ...
      runWrapped();
    } 
  }

  private void runWrapped() {
    switch (runReason) {
      case INITIALIZE:
        stage = getNextStage(Stage.INITIALIZE);
        //获取 DataFetcherGenerator     
        currentGenerator = getNextGenerator();
        //内部会调用相应 Generator的 startNext()
        runGenerators();
        break;
      case SWITCH_TO_SOURCE_SERVICE:
        runGenerators();
        break;
      case DECODE_DATA:
        decodeFromRetrievedData();
        break;
    }
  }
```

DataFetcherGenerator 是一个接口，有三个具体的实现：

- ResourceCacheGenerator: 资源文件
- DataCacheGenerator:  缓存文件
- SourceGenerator:  网络文件

在 runGenerators 中会调用 startNext(),因为第一次会从网络加载

```java
  private void runGenerators() {
    currentThread = Thread.currentThread();
    startFetchTime = LogTime.getLogTime();
    boolean isStarted = false;
    while (!isCancelled && currentGenerator != null
        && !(isStarted = currentGenerator.startNext())) {
      stage = getNextStage(stage);
      //DataFetcherGenerator  
      currentGenerator = getNextGenerator();
      if (stage == Stage.SOURCE) {
        reschedule();
        return;
      }
    }
  }

//会异步依次生成 ResourceCacheGenerator、DataCacheGenerator 和 SourceGenerator 对象，执行startNext()
private DataFetcherGenerator getNextGenerator() {
    switch (stage) {
      case RESOURCE_CACHE:
        return new ResourceCacheGenerator(decodeHelper, this);
      case DATA_CACHE:
        return new DataCacheGenerator(decodeHelper, this);
      case SOURCE:
        return new SourceGenerator(decodeHelper, this);
      case FINISHED:
        return null;
      default:
        throw new IllegalStateException("Unrecognized stage: " + stage);
    }
  }

//SourceGenerator#startNext
@Override
  public boolean startNext() {
    if (dataToCache != null) {
      Object data = dataToCache;
      dataToCache = null;
      cacheData(data);
    }

    if (sourceCacheGenerator != null && sourceCacheGenerator.startNext()) {
      return true;
    }
    sourceCacheGenerator = null;

    loadData = null;
    boolean started = false;
    while (!started && hasNextModelLoader()) {
      loadData = helper.getLoadData().get(loadDataListIndex++);
      if (loadData != null
          && (helper.getDiskCacheStrategy().isDataCacheable(loadData.fetcher.getDataSource())
          || helper.hasLoadPath(loadData.fetcher.getDataClass()))) {
        started = true;        
        //DataFetcher.loadData  
        loadData.fetcher.loadData(helper.getPriority(), this);
      }
    }
    return started;
  }

//HttpUrlFetcher#load()
  @Override
  public void loadData(@NonNull Priority priority,
      @NonNull DataCallback<? super InputStream> callback) {
    long startTime = LogTime.getLogTime();
    try {
       //获取一个流，再通过一个回调通知上层网络数据获取到了，使用的HttpURLConnection；
      InputStream result = loadDataWithRedirects(glideUrl.toURL(), 0, null, glideUrl.getHeaders());
      //网络数据流获取成功后的回调
      callback.onDataReady(result);
    } catch (IOException e) {
      callback.onLoadFailed(e);
    } 
  }

//SourceGenerator#onDataReady()
 public void onDataReady(Object data) {
    //  写入disk缓存
    DiskCacheStrategy diskCacheStrategy = helper.getDiskCacheStrategy();
    if (data != null && diskCacheStrategy.isDataCacheable(loadData.fetcher.getDataSource())) {
      dataToCache = data;
      cb.reschedule();
    } else {
        // 回调给上一层
      cb.onDataFetcherReady(loadData.sourceKey, data, loadData.fetcher,
          loadData.fetcher.getDataSource(), originalKey);
    }
  }

//DecodeJob#onDataFetcherReady
//接受到网络数据的 stream 后，在 DecodeJob 中的回调逻辑：调用 decodeFromRetrievedData
@Override
  public void onDataFetcherReady(Key sourceKey, Object data, DataFetcher<?> fetcher,
      DataSource dataSource, Key attemptedKey) {
...
    if (Thread.currentThread() != currentThread) {
      runReason = RunReason.DECODE_DATA;
      callback.reschedule(this);
    } else {
      try {
        decodeFromRetrievedData();
      }
    }
  }


  private void decodeFromRetrievedData() {
    ...
    Resource<R> resource = null;
    try {
      //对网络流进行解码获取Bitmap对象
      resource = decodeFromData(currentFetcher, currentData, currentDataSource);
    } catch (GlideException e) {
      e.setLoggingDetails(currentAttemptingKey, currentDataSource);
      throwables.add(e);
    }
    if (resource != null) {
      //解码完成后，回调上层接口
      notifyEncodeAndRelease(resource, currentDataSource);
    } else {
      runGenerators();
    }
  }
```

