## 1 简介

Content Provider 译为内容提供者，为不同的应用之间数据共享，提供统一的接口。

> 2025 更新：Provider 的启动时序从 Android 8 到 Android 16 没有本质变化，它仍然是"应用启动最早期、最容易拖慢冷启动"的组件；变的是使用场景——Android 10（API 29）分区存储之后，`ContentResolver` 更多被用来访问 `MediaStore`/SAF/`FileProvider`，而不是自己实现一个 Provider。

## 2原理

要调用 ContentProvider 使用 getContentResolver()。

```java
getContentResolver().insert(...);
```

getContentResolver() 在 ContextWrapper 中。

### ContextWrapper#getContentResolver()

```java
@Override
public ContentResolver getContentResolver() {
    //mBase 其实就是 ContextImpl
    return mBase.getContentResolver();
}
```

### ContextImpl#getContentResolver()

```java
@Override
public ContentResolver getContentResolver() {
    return mContentResolver;
}
```

### ContentResolver#query

得到 mContentResolver，之后就可以使用了，我们以 query() 举例。

```java
public final @Nullable Cursor query(final @RequiresPermission.Read @NonNull Uri uri,
            @Nullable String[] projection, @Nullable String selection,
            @Nullable String[] selectionArgs, @Nullable String sortOrder,
            @Nullable CancellationSignal cancellationSignal) {
        Preconditions.checkNotNull(uri, "uri");
        //代码一：返回 IContentProvider 类型的 unstableProvider 对象
        IContentProvider unstableProvider = acquireUnstableProvider(uri);
        ...
        try {
           ...
            try {
                //代码二：使用 query 方法
                qCursor = unstableProvider.query(mPackageName, uri, projection,
                        selection, selectionArgs, sortOrder, remoteCancellationSignal);
            } catch (DeadObjectException e) {
               ...
            }
    ...
   }
```

### 代码一：ContentResolver#acquireUnstableProvider

```java
public final IContentProvider acquireUnstableProvider(Uri uri) {
     //校验 scheme 是否为 content
     if (!SCHEME_CONTENT.equals(uri.getScheme())) {
         return null;
     }
     String auth = uri.getAuthority();
     if (auth != null) {
         //调用 acquireUnstableProvider，在 ContentResolver的子类ApplicationContentResolver 中
         return acquireUnstableProvider(mContext, uri.getAuthority());
     }
     return null;
 }
```

### ContextImpl#acquireUnstableProvider

```java
@Override
protected IContentProvider acquireUnstableProvider(Context c, String auth) {
    //return ActivityThread 的 acquireProvider()
    return mMainThread.acquireProvider(c,
            ContentProvider.getAuthorityWithoutUserId(auth),
            resolveUserIdFromAuthority(auth), false);
}
```

### ActivityThread#acquireProvider()

```java
public final IContentProvider acquireProvider(...) {
     //acquireExistingProvider :判断 mProviderMap 中是否有目标ContentProvider存在
     final IContentProvider provider = acquireExistingProvider(c, auth, userId, stable);
     if (provider != null) {
         return provider;
     }
     IActivityManager.ContentProviderHolder holder = null;
     try {
         //代码一：调用 AMP 的 getContentProvider() 
         holder = ActivityManagerNative.getDefault().getContentProvider(
                 getApplicationThread(), auth, userId, stable);
     } catch (RemoteException ex) {
         throw ex.rethrowFromSystemServer();
     }
     ...
     //   
     holder = installProvider(c, holder, holder.info,
             true /*noisy*/, holder.noReleaseNeeded, stable);
     return holder.provider;
 }
```

### 代码一：ActivityManagerService#getContentProvider()

```java
@Override
public final ContentProviderHolder getContentProvider(...) {
    ...
    return getContentProviderImpl(caller, name, null, stable, userId);
}
```

### ActivityManagerService#getContentProviderImpl()

```java
 private ContentProviderHolder getContentProviderImpl(..) {
     ...
       //获取目标ContentProvider的应用程序进程信息  
       ProcessRecord proc = getProcessRecordLocked(cpi.processName, cpr.appInfo.uid, false);
                        if (proc != null && proc.thread != null && !proc.killed) {
                            ...
                            if (!proc.pubProviders.containsKey(cpi.name)) {
                               ...
                                try {
                                    //代码一:该应用进程已经启动,调用 scheduleInstallProvider
                                    proc.thread.scheduleInstallProvider(cpi);
                                } catch (RemoteException e) {
                                }
                            }
                        } else {
                            ...
                            //没有启动，先启动进程
                            proc = startProcessLocked(cpi.processName,
                                    cpr.appInfo, false, 0, "content provider",
                                    new ComponentName(cpi.applicationInfo.packageName,
                                            cpi.name), false, false, false);
                                                     ...
                        }
             ...           
                        
}
```

> 2025 更新：`ActivityManagerNative.getDefault()` 在 Android 8.0 已改名 `ActivityManager.getService()`。这里的成本值得注意：目标 Provider 所在进程没起来时，`startProcessLocked` 会完整拉起对方应用（Application + 全部 Provider），所以"query 别人的 Provider"可能就是一次别人的冷启动。

### 代码一：ActivityThread#scheduleInstallProvider()

AMS 启动 Provider。

```java
@Override
public void scheduleInstallProvider(ProviderInfo provider) {
    //H 是 ActivityThread 的内部类继承了 Handler
     sendMessage(H.INSTALL_PROVIDER, provider);
}
```

### ActivityThread.H

```java
private class H extends Handler {
       public static final int INSTALL_PROVIDER        = 145;
  ...

 public void handleMessage(Message msg) {
           ...
            switch (msg.what) {
                case INSTALL_PROVIDER:
                    //处理 Provider
                    handleInstallProvider((ProviderInfo) msg.obj);
                    break;
                 ...
  }

```

### ActivityThread#handleInstallProvider()

```java
public void handleInstallProvider(ProviderInfo info) {
       final StrictMode.ThreadPolicy oldPolicy = StrictMode.allowThreadDiskWrites();
       try {
           //调用 installContentProviders
           installContentProviders(mInitialApplication, Lists.newArrayList(info)); 
       } finally {
           StrictMode.setThreadPolicy(oldPolicy);
       }
}
```

### ActivityThread#installContentProviders()

```java
 private void installContentProviders(
            Context context, List<ProviderInfo> providers) {
        final ArrayList<IActivityManager.ContentProviderHolder> results =
            new ArrayList<IActivityManager.ContentProviderHolder>();
       //遍历当前应用程序进程的 ProviderInfo 列表
        for (ProviderInfo cpi : providers) { 
            if (DEBUG_PROVIDER) {
                StringBuilder buf = new StringBuilder(128);
                buf.append("Pub ");
                buf.append(cpi.authority);
                buf.append(": ");
                buf.append(cpi.name);
                Log.i(TAG, buf.toString());
            }
            //installProvider 启动 Content Provider
            IActivityManager.ContentProviderHolder cph = installProvider(context, null, cpi,
                    false /*noisy*/, true /*noReleaseNeeded*/, true /*stable*/);  //2
            if (cph != null) {
                cph.noReleaseNeeded = true;
                results.add(cph);
            }
        }
 
        try {
            //AMP.publishContentProviders 将这些 ContentProvider存储在 AMS 的 mProviderMap 中
            ActivityManagerNative.getDefault().publishContentProviders(
                getApplicationThread(), results);  
        } catch (RemoteException ex) {
            ...
        }
    }

```

### ActivityThread#installProvider()

```java
private IActivityManager.ContentProviderHolder installProvider(...) {
       ContentProvider localProvider = null;
  ...
               final java.lang.ClassLoader cl = c.getClassLoader();
               //反射创建ContentProvider类型的localProvider对象。
               localProvider = (ContentProvider)cl.
                   loadClass(info.name).newInstance(); 
               provider = localProvider.getIContentProvider();
               if (provider == null) {
                 ...
                   return null;
               }
               ...
               //代码二：调用 attachInfo   
               localProvider.attachInfo(c, info); 
           } catch (java.lang.Exception e) {
              ...
               }
               return null;
           }
       }
          ...
       return retHolder;

```

> 2025 更新：`cl.loadClass(info.name).newInstance()` 这种反射创建，从 Android 9（API 28）起改为 `AppComponentFactory#instantiateProvider()`（`LoadedApk#getAppFactory()`），`ActivityThread#installProvider` 里也改成了先取 `AppComponentFactory` 再建实例；流程骨架不变，只是创建入口统一到 `AppComponentFactory`。

### 代码二：ContentProvider#attachInfo()

```java
private void attachInfo(Context context, ProviderInfo info, boolean testing) {
        mNoPerms = testing;
            ...
            //启动 onCreate    
            ContentProvider.this.onCreate();
        }
    }
```

> 2025 更新：`attachInfo` → `onCreate()` 发生在 `ActivityThread#handleBindApplication` 的 `installContentProviders()` 里，而 `Application#onCreate()` 要等这之后才被 `Instrumentation#callApplicationOnCreate()` 调用——这就是"Provider 比 Application 先初始化"的根因，也是 App Startup 要解决的问题（见第 3 节）。

## 3 Android 12—16 的变化与面试追问

> 本节覆盖 **Android 12（API 31）—Android 16（API 36）**，并把 Android 9/10 引入的 `AppComponentFactory`、分区存储一并标注，因为它们直接改变 Provider 的写法和成本。

### 3.1 installContentProviders：为什么 Provider 比 Application#onCreate 更早

`ActivityThread#handleBindApplication` 的顺序（Android 8—16 基本一致）：

1. `LoadedApk#makeApplication()` 创建 Application 实例（传 `null` instrumentation，所以此处**不**回调 `onCreate`）；
2. `installContentProviders(app, data.providers)`：对每个 `ProviderInfo` 反射/工厂创建实例 → `attachInfo()` → `ContentProvider#onCreate()`，最后 `publishContentProviders()` 把结果注册到 AMS 的 Provider 表；
3. `mInstrumentation.callApplicationOnCreate(app)`：这时才回调 `Application#onCreate()`。

所以 Provider 的 `onCreate` 一定早于 `Application#onCreate`，也早于任何 Activity/Service——它是应用进程里最早的业务代码执行点。

几个延伸结论：

* 同一进程多个 Provider 时，按 `android:initOrder` 排序（数值大的先初始化；排序细节以 PMS 为准），默认顺序不保证；
* 每个 Provider 的 `onCreate` 都在主线程同步执行，老代码里 `handleInstallProvider` 还会用 `StrictMode.allowThreadDiskWrites()` 临时放开磁盘写——所以"在 Provider 里初始化 SDK"= 冷启动直接多几十毫秒，多个库各自注册时线性叠加；
* Provider 在**别的进程**首次被访问时，会拉起那个进程（`getContentProviderImpl` → `startProcessLocked`），相当于一次完整的冷启动；
* 因此"Provider 多"本身就是启动性能问题，`dumpsys package`/启动 trace 里能直接看到 `installContentProviders` 段的耗时。

### 3.2 App Startup 与 Initializer：合并 Provider，而不是消灭它

`androidx.startup:startup-runtime` 的核心：

* `Initializer<T>` 接口：`T create(Context)` 放初始化逻辑，`List<Class<? extends Initializer<?>>> dependencies()` 声明依赖，框架按拓扑序执行；
* 所有 Initializer 在 manifest 里合并注册到一个 `InitializationProvider`（authority 形如 `${applicationId}.androidx-startup`），由这一个 Provider 在 `Application#onCreate` 之前统一调用；
* 也就是说 **App Startup 没有绕过 Provider 机制**，它省掉的是 N 个 Provider 的固定开销（进程内实例化、`attachInfo`、`publishContentProviders`、AMS 侧登记），初始化逻辑本身仍然阻塞在冷启动路径上。

真要懒加载：

* 用 `tools:node="remove"` 移除 `InitializationProvider`（或对应的 `<provider>` 节点），改为用到时手动 `AppInitializer.getInstance(context).initializeComponent(MyInitializer::class.java)`；
* 移除后要注意依赖方：`WorkManager` 2.6+ 也用 `androidx.startup` 初始化，去掉 Provider 后需要自己确保 `WorkManager` 被初始化；
* 能延迟的 SDK 初始化不要放 Initializer，改成"首次调用时初始化 + 双检锁"，配合 Baseline Profile 降低首帧抖动。

### 3.3 分区存储 / MediaStore / SAF 对 ContentResolver 的影响

* Android 10（API 29）：分区存储（scoped storage）引入，共享存储默认只能通过 `MediaStore`/SAF 访问；targetSdk 29 可以用 `requestLegacyExternalStorage` 临时退出；
* Android 11（API 30）：targetSdk 30+ 强制分区存储，`requestLegacyExternalStorage` 失效；`MediaStore` 增加 `IS_PENDING`（写入中的文件对其他应用不可见）、`RELATIVE_PATH`、`MediaStore.Downloads`；改/删别的应用的媒体要 `MediaStore.createWriteRequest()`/`createDeleteRequest()` 走系统确认弹窗；
* Android 13（API 33）：`READ_EXTERNAL_STORAGE` 对媒体失效，改用 `READ_MEDIA_IMAGES`/`READ_MEDIA_VIDEO`/`READ_MEDIA_AUDIO`；系统照片选择器 `MediaStore.ACTION_PICK_IMAGES`（`PickVisualMedia`）不需要任何存储权限；
* Android 14（API 34）：新增 `READ_MEDIA_VISUAL_USER_SELECTED`，用户可以只授权"选中的照片"，应用必须处理"部分授权"（每次启动重新确认，否则可能拿到空 Cursor 或 `SecurityException`）；
* Android 15/16：继续收紧跨应用媒体访问与 `/sdcard/Android/data` 私有目录；新代码不要再用 `file://`，统一 `content://` + `ContentResolver#openInputStream()`/`openFileDescriptor()`，对外分享用 `FileProvider` + `FLAG_GRANT_READ_URI_PERMISSION`。

对 `ContentResolver` 用法的具体要求：

* `query` 的 `projection` 不要写 `*`：`MediaStore` 的列在不同版本有增减（`IS_PENDING` 29+、`IS_TRASHED` 30+）；
* 批量写入用 `applyBatch()`，大文件/流式读写用 `openOutputStream()`/`openAssetFileDescriptor()`，不要在 UI 线程循环 `insert`；
* `Cursor` 用 try-with-resources 关闭，未关闭的 `Cursor` 会被 StrictMode 的 leaked closable 检测抓到（`detectLeakedClosableObjects`）；
* `query` 是同步 Binder 调用，provider 慢调用方就慢；主线程 query 直接卡 UI，放子线程/协程。

### 3.4 ContentProvider#call() 与跨进程

`ContentProvider#call(String method, String arg, Bundle extras)` 是 AIDL 之外的自定义入口，客户端用 `ContentResolver#call(Uri, method, arg, extras)` 调，返回 `Bundle`。

特点与坑：

* 走 Binder，`extras` 受 Binder 缓冲区限制（约 1MB），别塞 Bitmap/大 JSON，否则 `TransactionTooLargeException`；
* `query`/`insert`/`update`/`delete`/`call` 默认都在 Binder 线程池执行，**不是**主线程，provider 内部共享状态要自己保证线程安全；
* 同一个 Provider 会被并发调用，`SQLiteDatabase` 本身有锁，但内存缓存、`HashMap` 之类要加锁；
* `android:permission` 是整块 Provider 级别的，方法级鉴权要自己用 `Binder.getCallingUid()`/`getCallingPackage()`（Android 12+ 还有归因信息 `getCallingAttributionSource()`，以官方文档为准）；
* Android 14 起隐式 Intent 不再投递给非 exported 组件，但 Provider 是按 authority 寻址的，不受这条影响——受影响的是 `bindService`/`startActivity`。

选型：数据本来就在 Provider 后面（如自己实现的数据库/文件 Provider）→ 用 `call` 复用 authority 和权限模型；纯 RPC、需要回调/双向 → AIDL 或 `Messenger`。

### 3.5 Android 14/15 的权限变化（对 Provider 的影响）

Provider 自身的权限模型没有变：`android:permission`、`android:readPermission`/`writePermission`、`android:grantUriPermissions` + `<grant-uri-permission>`、`FLAG_GRANT_READ_URI_PERMISSION` 都还是那套。变的是"访问什么数据需要什么权限"：

* Android 14：媒体部分授权（`READ_MEDIA_VISUAL_USER_SELECTED`）会让 `MediaStore` 查询结果只包含用户选中的项；`foregroundServiceType` 必填也会影响"Provider + 同步前台服务"的组合；
* Android 15/16：跨应用媒体访问继续收紧，`MediaStore` 的 `_data` 列不可依赖，统一用 `openFileDescriptor()`；`BOOT_COMPLETED` 启动前台服务的限制也会影响"开机后靠 Provider 同步"的链路；
* 完整清单以官方 behavior changes 与 `Manifest.permission` 文档为准，不同 targetSdk 行为不同。

安全实践：

* 能不导出就不导出：`android:exported="false"` 优先；
* 必须导出时：`android:permission` + `grantUriPermissions` + `FLAG_GRANT_READ_URI_PERMISSION`，不要给 `FLAG_GRANT_WRITE_URI_PERMISSION` 除非确实要写；
* `openFile()` 里校验 `Uri` 路径（防 `../` 路径穿越），并处理 `Binder.getCallingUid()` 为 isolated/系统 uid 的情况；
* 对外分享文件用 `FileProvider`，不要自己写一个导出整个目录的 Provider。

### 3.6 面试追问（6—8 个）

1. **为什么 ContentProvider 的 `onCreate` 比 `Application#onCreate` 早？** `handleBindApplication` 里先 `installContentProviders()` 再 `callApplicationOnCreate()`，Provider 的 `attachInfo` 会直接回调 `onCreate`。
2. **应用里有 10 个 Provider，冷启动会慢多少？怎么定位？** 每个都在主线程同步初始化，线性叠加；用启动 trace 看 `installContentProviders`/`attachInfo` 段，或 `dumpsys package` 数 Provider。
3. **App Startup 到底优化了什么？它绕过了 Provider 吗？** 只是把 N 个 Provider 合成 1 个，省固定开销；要懒加载必须移除 `InitializationProvider` 手动初始化。
4. **分区存储之后 `ContentResolver` 的用法有哪些必须改？** 走 `MediaStore`/SAF，`IS_PENDING` 原子写，`RELATIVE_PATH` 代替绝对路径，分享用 `FileProvider`。
5. **`ContentProvider#call()` 和 AIDL 怎么选？它在哪个线程执行？** 数据在 Provider 后面用 `call`；Binder 线程池，非主线程，需自己保证线程安全。
6. **`query` 会阻塞调用方吗？跨进程要注意什么？** 会，同步 Binder；注意 provider 进程被拉起（冷启动）、Cursor 跨进程传输成本、`TransactionTooLargeException`。
7. **`grantUriPermissions` + `FLAG_GRANT_READ_URI_PERMISSION` 的完整链路？** 发送方 `grantUriPermission`/Intent flag → AMS 记录 grant → 接收方拿 `content://` 用 `ContentResolver` 打开 → 权限随任务/生命周期回收。
8. **Android 14/15 上 Provider 相关最容易踩的权限坑是什么？** 媒体部分授权导致查询结果变少、`_data` 列不可用、以及"Provider + 前台服务"被 FGS type/超时规则拦住。



