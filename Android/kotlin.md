#### 1 什么是内联函数？

内联函数 使用 inline 修饰，空间换时间，比正常函数少了压栈和出栈的操作，当函数体少，以及被频繁调用的函数才适合被定义为内联函数。简单来说，就是把调用函数替换成函数里面的内容。

#### 2 apply、run、let、also、with 之间的区别？

with、T.run、T.apply 接收者是 this，T.let、T.also 接收者是 it。

with、T.run、T.let 返回值是作用域的最后一个对象（this），T.apply、T.also 返回值是调用者本身(itself)。

#### 3 数据类的使用，data class 会继承什么？

默认生成下面：

* equals() / hashCode()
* toString() 
* componentN()
* copy()

#### 4  "==" 和 "===" 区别？

== 比较的是数值是否相等, 而 === 比较的是两个对象的地址是否相等。



#### 5 kotlin 中 var、val、const val 区别？

var 定义变量 private，带有 public 的 set 和 get 属性。

val 定义常量 private，带有 public 的 get 方法，可见性为 private final static，并且 val 会生成方法getNormalObject()，通过方法调用访问。

const val 定义的常量，可见性为 public final static，可以直接访问。

#### 6 介绍一下伴生对象和静态成员？

```kotlin
class NewFragment {
    companion object {
       val instance = NewFragment()
    }
}
//类似于 Java 中使用类访问静态成员的语法
```



#### 7 @JvmField 和 @JvmStatic 的使用

```kotlin
class NumberTest {
    companion object {
        @JvmField //修饰属性
        var flag = false

        @JvmStatic //修饰方法
        fun plus(num1: Int, num2: Int): Int {
            return num1 + num2
        }
    }
}

 public static void main(String[] args) {
      System.out.println(NumberTest.plus(2, 3));
      NumberTest.flag = true;
      System.out.println(NumberTest.flag);
}
```

#### 8  @JvmOverloads 的作用？

为了暴露多个重载方法。

```java
fun f(a: String, b: Int = 0, c: String="abc"){}
//相当于 java 中
void f(String a, int b, String c){}

@JvmOverloads 
fun f(a: String, b: Int=0, c:String="abc"){}
//相当于 java 中
void f(String a)
void f(String a, int b)
void f(String a, int b, String c)
```

#### 9 List 与 MutableList 区别？

List ：只能读，不能更改元素；

MutableList ：可读写，返回的是一个 ArrayList；

#### 10 Kotlin 中的数据类型有隐式转换吗？

没有，需要显式的转换。

#### 11 Kotlin中 Unit 类型的作用以及与Java中 Void 的区别？

* Java中必须指定返回类型，void 不能省略，但是在 kotlin 中，如果返回为 unit，可以省略。
* Java中 void 为一个关键字，但是在 kotlin 中 Void 是一个类。