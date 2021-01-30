## 1 简介

[MMKV](https://github.com/Tencent/MMKV/blob/master/README_CN.md) 是基于 **mmap 内存映射的 key-value 组件**，底层序列化/反序列化使用 **protobuf 实现**，性能高，稳定性强。

## 2 使用

```groovy
dependencies {
    implementation 'com.tencent:mmkv-static:1.2.7'
}
```

封装工具类：

```java
public class SPUtils {
    private static MMKV mv;
    private volatile static SPUtils mSPUtils;

    private SPUtils() {  }

    public static SPUtils getInstance() {
        if (mSPUtils == null) {
            synchronized (SPUtils.class) {
                if (mSPUtils == null) {
                    mSPUtils = new SPUtils();
                }
            }
        }
        return mSPUtils;
    }

    public static void init(Context context) {
        MMKV.initialize(context);
        mv = MMKV.defaultMMKV();
    }

    public static void encode(String key, Object object) {
        if (object instanceof String) {
            mv.encode(key, (String) object);
        } else if (object instanceof Integer) {
            mv.encode(key, (Integer) object);
        } else if (object instanceof Boolean) {
            mv.encode(key, (Boolean) object);
        } else if (object instanceof Float) {
            mv.encode(key, (Float) object);
        } else if (object instanceof Long) {
            mv.encode(key, (Long) object);
        } else if (object instanceof Double) {
            mv.encode(key, (Double) object);
        } else if (object instanceof byte[]) {
            mv.encode(key, (byte[]) object);
        } else {
            mv.encode(key, object.toString());
        }
    }

    public static void encodeSet(String key, Set<String> sets) {
        mv.encode(key, sets);
    }

    public static void encodeParcelable(String key, Parcelable obj) {
        mv.encode(key, obj);
    }


    public static Integer decodeInt(String key) {
        return mv.decodeInt(key, 0);
    }

    public static Double decodeDouble(String key) {
        return mv.decodeDouble(key, 0.00);
    }

    public static Long decodeLong(String key) {
        return mv.decodeLong(key, 0L);
    }

    public static Boolean decodeBoolean(String key) {
        return mv.decodeBool(key, false);
    }

    public static Float decodeFloat(String key) {
        return mv.decodeFloat(key, 0F);
    }

    public static byte[] decodeBytes(String key) {
        return mv.decodeBytes(key);
    }

    public static String decodeString(String key) {
        return mv.decodeString(key, "");
    }

    public static Set<String> decodeStringSet(String key) {
        return mv.decodeStringSet(key, Collections.<String>emptySet());
    }

    public static Parcelable decodeParcelable(String key) {
        return mv.decodeParcelable(key, null);
    }

    public static void removeKey(String key) {
        mv.removeValueForKey(key);
    }

    public static void clearAll() {
        mv.clearAll();
    }
}
```

## 3 原理

- **内存准备**
  通过 mmap 内存映射文件，提供一段可供随时写入的内存块，App 只管往里面写数据，由操作系统负责将内存回写到文件，不必担心 crash 导致数据丢失。
- **数据组织**
  数据序列化方面我们选用 protobuf 协议，pb 在性能和空间占用上都有不错的表现。
- **写入优化**
  考虑到主要使用场景是频繁地进行写入更新，我们需要有增量更新的能力。我们考虑将增量 kv 对象序列化后，append 到内存末尾。
- **空间增长**
  使用 append 实现增量更新带来了一个新的问题，就是不断 append 的话，文件大小会增长得不可控。我们需要在性能和空间上做个折中。