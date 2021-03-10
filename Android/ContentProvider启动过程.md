## 1 简介

Content Provider 译为内容提供者，为不同的应用之间数据共享，提供统一的接口。

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



