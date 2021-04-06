## 1 APK 打包过程

![](../asset/apk签名过程.jpg)

* 打包资源文件，生成 R.java 文件
  - aapt 工具（aapt.exe） -> AndroidManifest.xml 和 布局文件 XMl 都会编译 -> R.java -> AndroidManifest.xml 会被 aapt 编译成二进制
  - res 目录下资源 -> 编译，变成二进制文件，生成 resource id -> 最后生成 resouce.arsc（文件索引表）
  
* 处理 aidl 文件，生成相应的 Java 文件
  
  * aidl 工具（aidl.exe）
  
* 编译项目源代码，生成 class 文件

* 转换所有 class 文件，生成 classes.dex 文件
  
  * dx.bat
  
* 打包生成 APK 文件
  
  ​    
  
  * apkbuilder 工具打包到最终的 .apk 文件中
  
* 对APK文件进行签名

* 对签名后的 APK 文件进行对齐处理（正式包）
  
  * 对 APK 进行对齐处理，用到的工具是 zipalign