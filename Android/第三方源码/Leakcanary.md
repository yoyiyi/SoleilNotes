## 1 基本使用

```java
debugImplementation 'com.squareup.leakcanary:leakcanary-android:2.6'
```

假如导入成功，logcat 会打印。

```java
D/LeakCanary: LeakCanary is running and ready to detect memory leaks.
```

和 1.x 版本不同，不需要使用 LeakCanary.install(this)。

## 2 原理

```java
internal sealed class AppWatcherInstaller : ContentProvider() {
  internal class MainProcess : AppWatcherInstaller()
  internal class LeakCanaryProcess : AppWatcherInstaller()
  //AppWatcher.install 初始化在 ContentProvider.onCreate
  override fun onCreate(): Boolean {
    val application = context!!.applicationContext as Application
    AppWatcher.manualInstall(application)
    return true
  }
  ...  
}
```

