# 1、简介
这是 Android 进阶笔记第二篇，Retrofit 源码分析，Retrofit 是一个  RESTful 设计风格的网络请求框架，至于什么是 RESTful 设计风格的接口，这里就不展开来讲，感兴趣的同学可以与查阅相关资料，以前搞后台 Spring 全家桶，我们设计的接口全部都是按照 RESTful 来设计，写起来非常爽。扯远了，回到主题，对于 Retrofit而言 ，实际上真正负责网络请求工作的是底层的 **Okhttp**，关于 Okhttp 的解析，可以参考上一篇文章[Android 进阶笔记--Okhttp4.X 源码分析](https://blog.csdn.net/qq_44947117/article/details/104066775)。
# 2、入门
下面写一个小例子，接口用的是[玩安卓](https://wanandroid.com)的接口，请求项目的分类。
```java
//1.定义 API，用来描述请求的接口
public interface WanAndroidService {
    @GET("project/tree/json")
    Call<CategoryEntity> getCategory();
}
//2.创建 Retrofit
val retrofit = Retrofit.Builder()
            .baseUrl("https://www.wanandroid.com/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()

//3.创建网络请求实例
val service = retrofit.create(WanAndroidService::class.java)

//4.调用网络请求 API，生成 Call，执行请求
val call= service.getCategory()
call.enqueue(object : retrofit2.Callback<CategoryEntity> {
            override fun onFailure(call: retrofit2.Call<CategoryEntity>, t: Throwable) {

            }

            override fun onResponse(
                call: retrofit2.Call<CategoryEntity>,
                response: retrofit2.Response<CategoryEntity>
            ) {
                val result = response.body()
                Log.d("result", result.toString())
            }

        })
```
由上面代码我们可以看出，Retrofit 使用流程非常简洁，但是本文不是讲 Retrofit 的使用，我们在学习中，不仅要看表象，更要看本质，才能不断进步。

# 3、源码解析

## 3.1.Retrofit 的创建
在上面使用代码中，有一个非常重要的关键点，就是 Retrofit 的创建，我们来看 Retrofit 是怎样构建的。
### 3.1.1. Builder 的创建
```java
//采用建造者模式构建 Retrofit 
val retrofit = Retrofit.Builder()
            .baseUrl("https://www.wanandroid.com/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
```
接下来我看看看 Builder，Builder 是 Retrofit 一个内部类
```java
public static final class Builder {
    //平台类型
    private final Platform platform;
    //请求工厂，默认为 Okhttp
    private @Nullable okhttp3.Call.Factory callFactory;
    //请求的 url 的地址
    private @Nullable HttpUrl baseUrl;
    //数据转换的工厂集合
    private final List<Converter.Factory> converterFactories = new ArrayList<>();
    //适配器工厂的集合，默认 ExecutorCallAdapterFactory
    private final List<CallAdapter.Factory> callAdapterFactories = new ArrayList<>();
    //回调执行器，把子线程切换成主线程，Android 上的是封装了 handler 的 MainThreadExecutor
    private @Nullable Executor callbackExecutor;
    //缓存，为 true 会创建 ServiceMethod
    private boolean validateEagerly;
 }  
```
我们在看看 Builder 默认初始化
```java
public static final class Builder {
 Builder(Platform platform) {
      this.platform = platform;
    }

    public Builder() {
      this(Platform.get());
    }
  .....  
}
//涉及到 Platform 这个类
class Platform {
  private static final Platform PLATFORM = findPlatform();

  static Platform get() {
    return PLATFORM;
  }

  private static Platform findPlatform() {
    try {
      //判断是否是 Android 平台
      Class.forName("android.os.Build");
      if (Build.VERSION.SDK_INT != 0) {
        //创建一个 Android 类
        return new Android();
      }
    } catch (ClassNotFoundException ignored) {
    }
    return new Platform(true);
  }
  
  //创建默认网络请求适配器工厂
  List<? extends CallAdapter.Factory> defaultCallAdapterFactories(
      @Nullable Executor callbackExecutor) {
    //默认网络适配器  
    DefaultCallAdapterFactory executorFactory = new DefaultCallAdapterFactory(callbackExecutor);
    return hasJava8Types
        ? asList(CompletableFutureCallAdapterFactory.INSTANCE, executorFactory)
        : singletonList(executorFactory);
  }

  int defaultCallAdapterFactoriesSize() {
    return hasJava8Types ? 2 : 1;
  }

  List<? extends Converter.Factory> defaultConverterFactories() {
    return hasJava8Types
        ? singletonList(OptionalConverterFactory.INSTANCE)
        : emptyList();
  }


//继承 Platform
static final class Android extends Platform {
    Android() {
      super(Build.VERSION.SDK_INT >= 24);
    }

    @Override public Executor defaultCallbackExecutor() {
      //切换线程，子线程切换成主线程
      return new MainThreadExecutor();
    }
    // Handler 机制，子线程切换成主线程
    static class MainThreadExecutor implements Executor {
      private final Handler handler = new Handler(Looper.getMainLooper());

      @Override public void execute(Runnable r) {
        handler.post(r);
      }
    }
  }
```
### 3.1.2.添加 baseUrl
```java
//Retrofit.java
public Builder baseUrl(String baseUrl) {
     Objects.requireNonNull(baseUrl, "baseUrl == null");
     //将字符串转换成 HttpUrl
     return baseUrl(HttpUrl.get(baseUrl));
}

public Builder baseUrl(HttpUrl baseUrl) {
     Objects.requireNonNull(baseUrl, "baseUrl == null");
     List<String> pathSegments = baseUrl.pathSegments();
     if (!"".equals(pathSegments.get(pathSegments.size() - 1))) {
       throw new IllegalArgumentException("baseUrl must end in /: " + baseUrl);
     }
     this.baseUrl = baseUrl;
     return this;
  }
```
### 3.1.3.添加 GsonConverterFactory
```java
//1.GsonConverterFactory 的 create
 public static GsonConverterFactory create() {
    return create(new Gson());
 }

//2.调用 create
public static GsonConverterFactory create(Gson gson) {
    if (gson == null) throw new NullPointerException("gson == null");
    return new GsonConverterFactory(gson);
  }

 private final Gson gson;
 //3.创建含有 Gson 对象的 GsonConverterFactory 
 private GsonConverterFactory(Gson gson) {
    this.gson = gson;
}
//4.添加 addGsonConverFactory，说白了就是将含有 Gson 对象 GsonConverterFactory 添加到 数据转换工厂 converterFactories 中
public Builder addConverterFactory(Converter.Factory factory) {
    converterFactories.add(Objects.requireNonNull(factory, "factory == null"));
    return this;
}
```
### 3.1.4.build()
接下来看看 build() 方法里面做了什么。 
```java
 public Retrofit build() {
      if (baseUrl == null) {
        throw new IllegalStateException("Base URL required.");
      }

      okhttp3.Call.Factory callFactory = this.callFactory;
      if (callFactory == null) {
        //默认请求工厂使用 OkHttpClient
        callFactory = new OkHttpClient();
      }

      Executor callbackExecutor = this.callbackExecutor;
      if (callbackExecutor == null) {
       //回调
        callbackExecutor = platform.defaultCallbackExecutor();
      }

      // Make a defensive copy of the adapters and add the default Call adapter.
      List<CallAdapter.Factory> callAdapterFactories = new ArrayList<>(this.callAdapterFactories);
        callAdapterFactories.addAll(platform.defaultCallAdapterFactories(callbackExecutor));//添加默认适配器

      // Make a defensive copy of the converters.
      List<Converter.Factory> converterFactories = new ArrayList<>(
          1 + this.converterFactories.size() + platform.defaultConverterFactoriesSize());

      // Add the built-in converter factory first. This prevents overriding its behavior but also
      // ensures correct behavior when using converters that consume all types.
      converterFactories.add(new BuiltInConverters());
      converterFactories.addAll(this.converterFactories);
      converterFactories.addAll(platform.defaultConverterFactories());

      return new Retrofit(callFactory, baseUrl, unmodifiableList(converterFactories),
          unmodifiableList(callAdapterFactories), callbackExecutor, validateEagerly);
    }
  }
```
## 3.2.创建网络请求
接下来分析 retrofit.create(）流程，这里采用外观模式和代理模式。
```java
 public <T> T create(final Class<T> service) {
   //检验是否是接口
    validateServiceInterface(service);
    //使用动态代理获取请求接口的所有接口注解配置，并且创建网络请求接口实例
    return (T) Proxy.newProxyInstance(service.getClassLoader(), new Class<?>[] { service },
        new InvocationHandler() {
          private final Platform platform = Platform.get();
          private final Object[] emptyArgs = new Object[0];

          @Override public @Nullable Object invoke(Object proxy, Method method,
              @Nullable Object[] args) throws Throwable {
            // If the method is a method from Object then defer to normal invocation.
            if (method.getDeclaringClass() == Object.class) {
              return method.invoke(this, args);
            }
            if (platform.isDefaultMethod(method)) {
              return platform.invokeDefaultMethod(method, service, proxy, args);
            }
            return loadServiceMethod(method).invoke(args != null ? args : emptyArgs);
          }
        });
  }

 private void validateServiceInterface(Class<?> service) {
    if (!service.isInterface()) {
      throw new IllegalArgumentException("API declarations must be interfaces.");
    }

    Deque<Class<?>> check = new ArrayDeque<>(1);
    check.add(service);
    while (!check.isEmpty()) {
      Class<?> candidate = check.removeFirst();
      if (candidate.getTypeParameters().length != 0) {
        StringBuilder message = new StringBuilder("Type parameters are unsupported on ")
            .append(candidate.getName());
        if (candidate != service) {
          message.append(" which is an interface of ")
              .append(service.getName());
        }
        throw new IllegalArgumentException(message.toString());
      }
      Collections.addAll(check, candidate.getInterfaces());
    }

    if (validateEagerly) {
      Platform platform = Platform.get();
      for (Method method : service.getDeclaredMethods()) {
        if (!platform.isDefaultMethod(method) && !Modifier.isStatic(method.getModifiers())) {
          loadServiceMethod(method);
        }
      }
    }
  }
```
接下来看 loadServiceMethod
```java
ServiceMethod<?> loadServiceMethod(Method method) {
    ServiceMethod<?> result = serviceMethodCache.get(method);
    if (result != null) return result;

    synchronized (serviceMethodCache) {
      result = serviceMethodCache.get(method);
      if (result == null) {
        result = ServiceMethod.parseAnnotations(this, method);
        serviceMethodCache.put(method, result);
      }
    }
    return result;
  }

abstract class ServiceMethod<T> {
  static <T> ServiceMethod<T> parseAnnotations(Retrofit retrofit, Method method) {
    //解析请求配置的注解
    RequestFactory requestFactory = RequestFactory.parseAnnotations(retrofit, method);

    Type returnType = method.getGenericReturnType();
    if (Utils.hasUnresolvableType(returnType)) {
      throw methodError(method,
          "Method return type must not include a type variable or wildcard: %s", returnType);
    }
    if (returnType == void.class) {
      throw methodError(method, "Service methods cannot return void.");
    }
    //通过 HttpServiceMethod 构建的请求方法 
    return HttpServiceMethod.parseAnnotations(retrofit, method, requestFactory);
  }

  abstract @Nullable T invoke(Object[] args);
}
```
接下来看看 HttpServiceMethod#parseAnnotations
```java
 static <ResponseT, ReturnT> HttpServiceMethod<ResponseT, ReturnT> parseAnnotations(
      Retrofit retrofit, Method method, RequestFactory requestFactory) {
       
       //1.从Retrofit对象中获取对应的网络请求适配器
       CallAdapter<ResponseT, ReturnT> callAdapter =
        createCallAdapter(retrofit, method, adapterType, annotations);
  
//2.根据网络请求接口方法的 返回值 和 注解类型 从 Retrofit 对象中获取对应的数据转换器 
 Converter<ResponseBody, ResponseT> responseConverter =
        createResponseConverter(retrofit, method, responseType); 
```
接下来看 createCallAdapter 
```java
 private static <ResponseT, ReturnT> CallAdapter<ResponseT, ReturnT> createCallAdapter(
      Retrofit retrofit, Method method, Type returnType, Annotation[] annotations) {
    try {
      //noinspection unchecked
      return (CallAdapter<ResponseT, ReturnT>) retrofit.callAdapter(returnType, annotations);
    } catch (RuntimeException e) { // Wide exception range because factories are user code.
      throw methodError(method, e, "Unable to create call adapter for %s", returnType);
    }
  }
  
 public CallAdapter<?, ?> nextCallAdapter(@Nullable CallAdapter.Factory skipPast, Type returnType,
      Annotation[] annotations) {
    Objects.requireNonNull(returnType, "returnType == null");
    Objects.requireNonNull(annotations, "annotations == null");

    int start = callAdapterFactories.indexOf(skipPast) + 1;
    //循环获取合适请求工厂
    for (int i = start, count = callAdapterFactories.size(); i < count; i++) {
      CallAdapter<?, ?> adapter = callAdapterFactories.get(i).get(returnType, annotations, this);
      if (adapter != null) {
        return adapter;
      }
    }
```
接下来看 createResponseConverter
```java
//最终都走到这个方法里面
 public <T> Converter<ResponseBody, T> nextResponseBodyConverter(
      @Nullable Converter.Factory skipPast, Type type, Annotation[] annotations) {
    Objects.requireNonNull(type, "type == null");
    Objects.requireNonNull(annotations, "annotations == null");

    int start = converterFactories.indexOf(skipPast) + 1;
   //循环获取合适转换工厂
    for (int i = start, count = converterFactories.size(); i < count; i++) {
      Converter<ResponseBody, ?> converter =
          converterFactories.get(i).responseBodyConverter(type, annotations, this);
      if (converter != null) {
        //noinspection unchecked
        return (Converter<ResponseBody, T>) converter;
      }
    }
}
```
最后，执行 HttpServiceMethod#invoke
```java
 @Override final @Nullable ReturnT invoke(Object[] args) {
    //负责网络请求的 OkHttpCall
    Call<ResponseT> call = new OkHttpCall<>(requestFactory, args, callFactory, responseConverter);
    return adapt(call, args);
  }
```
## 3.3.调用网络请求 API，生成 Call，执行请求
```java
val call= service.getCategory()
```
从上面分析得出这个 service 对象其实是动态代理对象 Proxy.newProxyInstance()，得到的 Call 对象。 
### 3.3.1.异步请求
异步请求调用的是 enqueue
```java
//DefaultCallAdapterFactory.java
 @Override public void enqueue(final Callback<T> callback) {
      Objects.requireNonNull(callback, "callback == null");
       //使用静态代理 delegate 进行请求
      delegate.enqueue(new Callback<T>() {
        @Override public void onResponse(Call<T> call, final Response<T> response) {
          //线程切换，子线程切换成主线程
          callbackExecutor.execute(() -> {
            if (delegate.isCanceled()) {
              // Emulate OkHttp's behavior of throwing/delivering an IOException on cancellation.
              callback.onFailure(ExecutorCallbackCall.this, new IOException("Canceled"));
            } else {
              callback.onResponse(ExecutorCallbackCall.this, response);
            }
          });
        }

        @Override public void onFailure(Call<T> call, final Throwable t) {
          callbackExecutor.execute(() -> callback.onFailure(ExecutorCallbackCall.this, t));
        }
      });
    }
```
接下来看看 delegate 中的 enqueue
这个 delegate 实际上是 OkHttpCall
```java
 //OkHttpCall.java
 @Override public void enqueue(final Callback<T> callback) {
    Objects.requireNonNull(callback, "callback == null");

    okhttp3.Call call;
    Throwable failure;

    synchronized (this) {
      if (executed) throw new IllegalStateException("Already executed.");
      executed = true;

      call = rawCall;
      failure = creationFailure;
      if (call == null && failure == null) {
        try {
         //其实就是创建 Okhttp的 Request 对象，调用的是 OkHttp.call。
          call = rawCall = createRawCall();
        } catch (Throwable t) {
          throwIfFatal(t);
          failure = creationFailure = t;
        }
      }
    }

```
### 3.3.2.同步请求
```java
val response = category.execute()
```
调用的还是是 OkhttpCall
```java
  @Override public Response<T> execute() throws IOException {
    okhttp3.Call call;

    synchronized (this) {
      if (executed) throw new IllegalStateException("Already executed.");
      executed = true;

      if (creationFailure != null) {
        if (creationFailure instanceof IOException) {
          throw (IOException) creationFailure;
        } else if (creationFailure instanceof RuntimeException) {
          throw (RuntimeException) creationFailure;
        } else {
          throw (Error) creationFailure;
        }
      }

      call = rawCall;
      if (call == null) {
        try {
          call = rawCall = createRawCall();
        } catch (IOException | RuntimeException | Error e) {
          throwIfFatal(e); //  Do not assign a fatal error to creationFailure.
          creationFailure = e;
          throw e;
        }
      }
    }

    if (canceled) {
      call.cancel();
    }
    //调用 OkHttpCall 的 execute() 发送网络请求
    return parseResponse(call.execute());
  }
  
Response<T> parseResponse(okhttp3.Response rawResponse) throws IOException {
    ResponseBody rawBody = rawResponse.body();

    // Remove the body's source (the only stateful object) so we can pass the response along.
    rawResponse = rawResponse.newBuilder()
        .body(new NoContentResponseBody(rawBody.contentType(), rawBody.contentLength()))
        .build();

    int code = rawResponse.code();
    if (code < 200 || code >= 300) {
      try {
        // Buffer the entire body to avoid future I/O.
        ResponseBody bufferedBody = Utils.buffer(rawBody);
        return Response.error(bufferedBody, rawResponse);
      } finally {
        rawBody.close();
      }
    }

    if (code == 204 || code == 205) {
      rawBody.close();
      return Response.success(null, rawResponse);
    }

    ExceptionCatchingResponseBody catchingBody = new ExceptionCatchingResponseBody(rawBody);
    try {
      //将响应体转为Java对象
      T body = responseConverter.convert(catchingBody);
      return Response.success(body, rawResponse);
    } catch (RuntimeException e) {
      // If the underlying source threw an exception, propagate that rather than indicating it was
      // a runtime exception.
      catchingBody.throwIfCaught();
      throw e;
    }
  }
```
到这里，Retrofit 流程已经非常清晰，用一句话来概括就是，采用动态代理，最终将封装的请求，交给底层的 OkHttp 来处理。
# 4、参考
[Android主流三方库源码分析（二、深入理解Retrofit源码）](https://juejin.im/post/5e1fb9386fb9a0300a4501a6#heading-12)
[Android：手把手带你 深入读懂 Retrofit 2.0 源码](https://www.jianshu.com/p/0c055ad46b6c)