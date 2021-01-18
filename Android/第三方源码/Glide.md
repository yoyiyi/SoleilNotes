## 1  基本使用

Glide 是一个图片加载库，基本使用如下：

```kotlin
Glide.with(this).load("http://xxxx.jpg").apply(RequestOptions()).into(iv)
```

