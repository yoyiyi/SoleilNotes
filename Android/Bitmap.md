@[TOC]
# 1 简介
`Bitmap` 在安卓中是一个非常重要的概念，翻译成中文就是位图，`Bitmap` 位图包括像素以及长、宽、颜色的描述信息。
# 2 创建方式
## 2.1 BitmapFactory
BitmapFactory 可以从文件、资源、数据流、字节数组中创建 `Bitmap` 对象，可以理解为一个工具类，主要用来解析、创建 `Bitmap` 对象，`BitmapFactory` 创建 `Bitmap` 包含下面所有函数，接下来我们来看看这些函数。
```java
//从资源文件中加载位图
public static Bitmap decodeResource(Resources res, int id)
public static Bitmap decodeResource(Resources res, int id, Options opts)

//从字节数组中加载位图
public static Bitmap decodeByteArray(byte[] data, int offset)
public static Bitmap decodeByteArray(byte[] data, int offset, Options opts)

//从文件路径中加载位图，通常是磁盘存储中
public static Bitmap decodeFile(String pathName) 
public static Bitmap decodeFile(String pathName, Options opts)

//从文件中加载位图，通常是磁盘存储中
public static Bitmap decodeFileDescriptor(FileDescriptor fd) 
public static Bitmap decodeFileDescriptor(FileDescriptor fd, Rect outPadding, Options opts)

//从数据流中加载位图
public static Bitmap decodeStream(InputStream is) 
public static Bitmap decodeStream(InputStream is, Rect outPadding ,Options opts)
```
不难发现他们两个重载函数之间，之差一个 `Options` 参数，那么这个 `Options` 是什么，后面 2.1.2 再讲。
上面的函数都比较好理解，这里不再具体举例子，需要注意的是 `decodeFileDescriptor` 和 `decodeFile` 区别

### 2.1.1 decodeFileDescriptor 与 decodeFile 区别
#### 2.1.1.1 decodeFileDescriptor 
表示从文件中加载位图。
- FileDescriptor fd：包含位图数据的文件路径
- Rect outPadding：返回矩形的内边距，如果位图被解析成功，返回(-1,-1,-1,-1)，一般我们传入 null 就可以。
```java
String path = "/data/data/test.jpg";
FileInputStream is = new FileInputStream(path);
Bitmap bitmap = BitmapFactory.decodeFileDescriptor(is.getFD());
if (bitmap != null){
            
}
```
#### 2.1.1.2 decodeFile 
表示从文件路径中加载位图。
使用示例：
```java
String path = "/data/data/test.jpg";
Bitmap bitmap = BitmapFactory.decodeFile(path);
if (bitmap != null){
            
}
```
#### 2.1.1.3 区别
我们先来看看 `decodeFileDescriptor`。
```java
 public static Bitmap decodeFileDescriptor(FileDescriptor fd, Rect outPadding, Options opts) {
        validate(opts);
        Bitmap bm;

        Trace.traceBegin(Trace.TRACE_TAG_GRAPHICS, "decodeFileDescriptor");
        try {
            if (nativeIsSeekable(fd)) {
               //这是个本地函数，通过 JNI 调用
                bm = nativeDecodeFileDescriptor(fd, outPadding, opts);
            } else {
                FileInputStream fis = new FileInputStream(fd);
                try {
                    bm = decodeStreamInternal(fis, outPadding, opts);
                } finally {
                    try {
                        fis.close();
                    } catch (Throwable t) {/* ignore */}
                }
            }

            if (bm == null && opts != null && opts.inBitmap != null) {
                throw new IllegalArgumentException("Problem decoding into existing bitmap");
            }

            setDensityFromOptions(bm, opts);
        } finally {
            Trace.traceEnd(Trace.TRACE_TAG_GRAPHICS);
        }
        return bm;
    }
```
再来看看 `decodeFile`。
```java
public static Bitmap decodeFile(String pathName, Options opts) {
        validate(opts);
        Bitmap bm = null;
        InputStream stream = null;
        try {
            //最终以流的方式获取，涉及到额外对象的创建
            stream = new FileInputStream(pathName);
            bm = decodeStream(stream, null, opts);
        } catch (Exception e) {
            Log.e("BitmapFactory", "Unable to decode stream: " + e);
        } finally {
            if (stream != null) {
                try {
                    stream.close();
                } catch (IOException e) {
                    // do nothing here
                }
            }
        }
        return bm;
    }

```
所以，我们可以看出 `decodeFileDescriptor ` 比 `decodeFile` 更加节省内存。
### 2.1.2 BitmapFactory.Options
我们来看看 `BitmapFactory.Options` 的常用成员变量。
```java
//获取图片信息
public boolean inJustDecodeBounds;
//设置图片采样率
public int inSampleSize;
//像素在内存中的存储格式，默认为 Bitmap.Config.ARGB_8888
public Bitmap.Config inPreferredConfig = Bitmap.Config.ARGB_8888;
//文件所在文件夹的屏幕分辨率
public int inDensity;
//真实设备屏幕分辨率
public int inTargetDensity;
//设置是否需要缩放
public boolean inScaled;
//图片原始宽度
public int outWidth;
//图片原始高度
public int outHeight;
//图片 MIME 类型，例如 JPEG GIF 等
public String outMineType;
```
#### 2.1.2.1 inJustDecodeBounds
表示是否获取图片信息，如果设置成 `true`，那么表示只解析图片信息，不加载图片到内存中，获取到图片信息有宽度、高度、MIME 类型，分别通过 `options.outWidth`、`optionHeigth`、`options.outMineType` 获取，那么这个字段有什么用，我们在获取图片时候，经常需要对图片进行压缩操作，要不然，一张大图片不管三七二十一，一股脑加载到内存中，会发生 `OOM`，这个字段设置为 `true` 时候，就是在不把图片加载进内存，就可以获取到图片的某些信息，这种情况下获取到的 `Bitmap` 会是 `null`。
使用示例如下：
```java
BitmapFactory.Options options = new BitmapFactory.Options();
options.inJustDecodeBounds = true;
//这里 Bitmap 是 null
Bitmap bitmap = BitmapFactory.decodeResource(getResources(), R.drawable.test, options);
Log.d(TAG, "width:"+options.outWidth+"\nheight:" + options.outHeight + "\nmime:" + options.outMimeType);
```
#### 2.1.2.2 inSampleSize
表示图片采样率，采样率全称采样频率，指每隔多少个样本采样一次。举个例子，将这个值设置成 16，就是把原本图片宽高每 16 个像素采样一次，结果图片宽高变成原理的 1/16，它是一种失真的压缩方式，使用时候要注意，官方建议采用 2 的幂数，如果不满 1 则会按照 1 去，如果不是 2 的幂数，向下取 2 的幂数。
使用示例如下：
```java
//1.获取图片宽高
BitmapFactory.Options options = new BitmapFactory.Options();
options.inJustDecodeBounds = true;
Bitmap bitmap = BitmapFactory.decodeResource(getResources(), R.drawable.test, options);

//2.根据宽高计算 inSampleSize
int sampleSize = countSampleSize(options,200,100);

//3.根据压缩率接下 Bitmap
options.inJustDecodeBounds = false;
options.inSampleSize = sampleSize;
bitmap = BitmapFactory.decodeResource(getResources(), R.drawable.test, options);
iv.setImageBitmap(bitmap);

/**
 * 取目标宽高最大值计算采样率
 *
 * @param options   options
 * @param dstWidth  通常是 ImageView 的宽
 * @param dstHeight 通常是 ImageView 的高
 * @return 采样率
 */
private static int countSampleSize(BitmapFactory.Options options, int dstWidth, int dstHeight) {
       final int width = options.outWidth;
       final int height = options.outHeight;
       int inSampleSize = 1;
        // //使用需要的宽高的最大值来计算比率
       if (height > dstHeight || width > dstWidth) {
            final int value = dstHeight > dstWidth ? dstHeight : dstWidth;
            final int heightRatio = Math.round((float) height / (float) value);
            final int widthRatio = Math.round((float) width / (float) value);
            inSampleSize = heightRatio > widthRatio ? heightRatio : widthRatio;
        }
       return inSampleSize;
    }
```
#### 2.1.2.3 inPreferredConfig 
该字段表示像素在内存中的存储，`Bitmap.Config`  用来描述图片的像素：
- ARGB_8888: 每个像素占 4 字节，共 32 位，默认设置
- Alpha_8: 只保存透明度，每个像素占 1 字节，共8位
- ARGB_4444: 每个像素占 2 字节，共 16 位（失真严重，不推荐使用）
- RGB_565:只存储RGB值，每个像素占 2 字节，共 16 位
#### 2.1.2.4 inScaled、inDensity、inTargetDensity
讲解这三个字段之前我们这里有一个问题，**一张图片需要的内存是如何计算的？**，这里不多讲，详情请参考笔者另外一篇文章 [Android性能优化--图片优化](https://blog.csdn.net/qq_44947117/article/details/104140199)。
结论就是：

- 1.当图片存放在 res 资源目录，图片占用内存大小 = width * scale * height * scale * 一个像素所占内存大小 ，scale = inTargetDensity / inDensity
- 2.当图片存放在磁盘空间，图片占用内存大小 = width * height * 一个像素所占内存大小

我们知道，只有图片位于资源文件夹所对应的屏幕分辨率和正是设备屏幕分辨率不同时候 `Bitmap` 才会缩放，`isScaled` 设置成 `true` 或者不设置，动态缩放，设置为 `false`，不缩放。
`inTargetDensity` 表示真实设备屏幕分辨率。
`inDensity` 表示资源文件所在文件夹的屏幕所对应分辨率。

## 2.2 Bitmap 静态方法
```java
/**
 *创建指定大小的空白图像
 *@param width 宽 单位 px
 *@param height 高 单位 px
 *@param config 单位像素存储格式
 */
static Bitmap createBitmap(int width, int height Bitmap.Config config) 

/**
 *根据一幅图像创建位图
 *@param src源图像
 */
static Bitmap createBitmap(Bitmap src)

/**
 *根据一幅图像创建位图，用于裁剪图像
 *@param src源图像
 *@param x 裁剪源图像 x 坐标
 *@param y 裁剪源图像 y 坐标
 *@param width 宽 单位 px
 *@param height 高 单位 px
 */ 
static Bitmap createBitmap(Bitmap source, int x , int y, int width, int height) 

/**
 *根据一幅图像创建位图，用于裁剪图像
 *@param src源图像
 *@param x 裁剪源图像 x 坐标
 *@param y 裁剪源图像 y 坐标
 *@param width 宽 单位 px
 *@param height 高 单位 px
 *@param Matrix 裁剪后图像添加矩阵
 *@param filter 图像添加滤波效果
 */ 
static Bitmap createBitmap(Bitmap source, int x , int y, int width int height, Matrix m, boolean filter) 

//指定色彩创建图像
static Bitmap createBitmap(int[] colors, int width , int height, Bitmap.Config config)
static Bitmap createBitmap(int[] colors, int offset, int stride , int width , 
int height, Bitmap.Config config) 

/**
 *根据一幅图像创建位图，用于缩放图像
 *@param src 源图像
 *@param dstWidth  目标图像 x 坐标
 *@param dstHeight 目标图像 y 坐标
 *@param filter 图像添加滤波效果
 */ 
static Bitmap createScaledBitmap(Bitmap src, int dstWidth ,int dstHeight, boolean filter) 
boolean filter)
```
# 3 常用函数
## 3.1 copy(Config config, boolean isMutable)
- Config config：像素在内存汇总存储形式
- boolean isMutable：是否可以更改其中像素

通过 `BitmapFactory` 加载的位图不可更改像素，通过 `Bitmap` 静态创建部分才可以更改像素。
```java
copy(Config config, boolean isMutable)
createBitmap(int width, int height Bitmap.Config config) 
createScaledBitmap(Bitmap src, int dstWidth ,int dstHeight, boolean filter) 
boolean filter)
```
## 3.2 extractAlpha()
生成只提取了原图的 `alpha` 通道的位图，新的位图只有 `alpha` 值，`rgb` 值为 0，主要作用是获取原图的轮廓。
## 3.3 分配空间获取
| 函数                 | API           | 描述                                                         |
| -------------------- | ------------- | ------------------------------------------------------------ |
| getAllocationByCount | API 19 中引入 | 在 19 及以上                                                 |
| getByteCount()       | API 12 中引入 | 在 12 - 19 中使用                                            |
| getRowByte()         | API 1 中引入  | 1.获取每行所分配的内存大小，内存 = getRowBytes() * bmp.getHeight()；2.12以下使用 |
## 3.4 recycle()、isRecycled()
强制回收位图，注意：
- 在 API 10 之前，`Bitmap` 的像素级数据存放在 `Native` 内存中，`Bitmap` 本身存放在堆中，两个相互隔离，`Native` 内存数据不主动释放，容易造成内存泄露，需要使用 `recycle()` 函数进行回收。
- 在 API 11 及以后，`Bitmap` 的像素级数据和本身都存放在堆中，不需要使用 `recycle()` 回收。
## 3.5 compress()
作用就是对图片进行质量压缩。
```java
/**
 *@param format 图像的压缩格式
 *@param quality 图像压缩率，0-100, 0 压缩100%，100意味着不压缩
 *@param stream 写入压缩数据的输出流
 */
public boolean compress(Bitmap.CompressFormat format, int quality, OutputStream stream) 
```
## 3.6 getDensity、setDensity
```java
//指定位图屏幕密度，设置图像建议的屏幕尺寸，只影响到缩放，不会改变 Bitmap 本身内存中的大小。
public void setDensity(int density)
//获取屏幕密度
public int getDensity()
    
```