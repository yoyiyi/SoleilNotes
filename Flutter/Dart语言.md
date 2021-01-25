## 1 变量和常量

### 1.1 变量

Dart 语言的变量有四种方式可以声明。

```dart
var name1 = 'yoyiyi';
Object name2 = 'yoyiyi';
dynamic name2 = 'yoyiyi'; //运行时根据值明确类型
String name4 = 'yoyiyi';

//默认值，未初始化的变量的初始值为null
int num; 
print(num); //null
```

### 1.2 常量

声明时就初始化，不能改变，使用 final 和 const。

```dart
//1.final 运行时常量
final a = 1;
final int a = 2;

//2.const 编译时常量
const b = 1;
const int b = 2;

//3.const 可以用来创建常量值
final list1 = const [1];
const list2 = const [];
 
//不能更改 final 变量或 const 变量的值
```

类的变量可以为 final，不能为 const，如果要使用 const，必须使用 static const 静态变量。

## 2 数据类型

### 2.1 num

有两个子类 int 和 double

```dart
int a = 1;
double b = 1.23

//String num 互转
int c = int.parse("1");
double d = double.parse("2.2");
String e = 1.toString();

```

### 2.2 String

是 UTF-16 编码的字符序列，可以使用单引号或双引号创建，单引号和双引号可以嵌套使用。

```dart
var a = "yoyiyi";
String b = 'yoyiyi';

// + 号拼接字符串
var c = "This is" + "Dart";

//单引号和双引号可以嵌套
String d = "This is 'Dart'";
String f = 'This is "Dart"';

//${表达式} 计算变量值
var e = "This is Dart";
var f = "${e.toUpperCase()}";

//使用三个单引号或者双引号可以创建多行字符串对象
var g = ''' 
  This is
  Dart
'''
var h = """
  This is
  Dart 
 """

//r 前缀可以创建一个原始 raw 字符串
var i = r'This is \n' //没有换行了 

```

### 2.3 bool

布尔类型 `true` 和 `false`，和 Java 一样。

### 2.4 List 集合

在Dart中，数组就是 List 对象。

```dart
//创建
var list = [1,2,3];
var list1 = List(1);
list1[0] = 1;

//在前添加 const，定义一个不变的 list 对象（编译时常量）
var list =  const [1,2,3];
list.add(4); //错误，list 不可变

```

### 2.5 Map 集合

键和值相关联的对象。

```dart
//创建
var a = Map();
a['1'] = "a";

//指定类型
var b = Map<int, String>();
b[1] = 'yoyiyi';

//在前添加 const，定义一个不变的 Map 对象（编译时常量）
var d = const{"1":C++","2":"Java"};
```

### 2.6 Runes

用于在字符串中表示 Unicode 字符(多用于表情包),用到非常少。

```dart
var clapping = '\u{1f44f}';
print(clapping);
print(clapping.codeUnits);//返回十六位的字符单元数组
print(clapping.runes.toList());

Runes input = new Runes(
      '\u2665  \u{1f605}  \u{1f60e}  \u{1f47b}  \u{1f596}  \u{1f44d}');
print(new String.fromCharCodes(input));
```

### 2.7 Symbols

声明的操作符或者标识符,类似于 c 宏定义。

```dart
var sym1 = Symbol(‘name‘);
print(sym1); // Symbol("name")

var sym2 = #tt;
print(sym2); // Symbol("tt")
```

## 3 操作符

### 3.1 类型判定操作符

| 操作符 | 解释                           |
| ------ | ------------------------------ |
| as     | 类型转换                       |
| is     | 如果对象是指定的类型返回 True  |
| is!    | 如果对象是指定的类型返回 False |

```dart
var a  = "c";
if(a is String){
 print("${a}");
}
```

### 3.2 赋值操作符

`=`、`+=`、`\=`、`*=` 等

```dart
//??=
var b = null;
b ??= "cc"; //如果 b 是 null，b 赋值 cc；

```

### 3.3 条件表达式

三元表达式 `condition ? expr1 : expr2`  替代 if -else 语句

```dart
var a = 1
var b= a == 1 ? "c": "d";
```

### 3.4 级联操作符

级联操作符 `..` 可以在同一个对象上连续调用多个函数以及访问成员变量

```dart
var sb = StringBuffer();
sb..write('foo')
  ..write('bar');
```

### 3.5 安全操作符

`?.`,左边的操作对象如果为 null 则返回 null

```dart
String a;
print(a?.length)
```

## 4 方法

### 4.1 方法

```dart
int add(int i,int j){
  return i + j;
}

//可以省略类型，不推荐
int add(i,j){
  return i + j;
}

//只有一个表达式的方法，可以选择使用缩写语法
int add(int i, int j) => i + j;

```

### 4.2 一等方法对象

在 Dart 语言中，方法也是对象。

```dart
var list = [1,2,3];
//将 print 方法 作为参数传递给 forEach
list.forEach(print);
//将方法赋值给一个变量
var p = print;
list.forEach(p);
```

### 4.3 可选命名参数

把方法的参数放到 `{}` 中。

```dart
int add({int i,int j}){
  return i + j;
}

//无必须参数
add()

//选择传递参数
add(i:2)

//位置无关
add(i:1, j:2)
add(j:1, i:2)
```

### 4.4 可选位置参数

把方法的参数放到 `[]` 中。

```dart
int add([int i,int j]){
  return i + j;
}

//赋值给 i
add(1);
//按照顺序赋值
add(1,2);
```

### 4.5 默认参数值

`=` 定义可选参数的默认值。

```dart
int add([int i = 1, int j = 2]) => i + j;
int add({int i = 1, int j = 2}) => i + j;
```

### 4.6 匿名方法

没有名字的方法,也称为 lambda 或 closure 闭包

```dart
([Type] param1, …) { 
  codeBlock; 
}; 

//例
var list = ['apples', 'oranges', 'grapes', 'bananas', 'plums'];
list.forEach((i) {
  print(list[i]);
});

```

### 4.7 异常

* 所有的 Dart 异常是非检查异常，方法不一定声明了他们所抛出的异常， 并且不要求你捕获任何异常。   
* Dart 提供了 `Exception`和`Error` 类型，和子类型。可以定义自己的异常类型。但是， Dart 代码可以抛出任何非 null 对象为异常，不仅仅是实现了 `Exception` 或者` Error` 的对象。

```dart
throw new Exception('异常');
throw '异常';
throw 123;
```

* Dart中的`catch`无法指定异常类型，需结合`on`来使用

```dart
try {
	throw 123;
} on int catch(e){
	//使用 on 指定捕获int类型的异常对象       
} catch(e,s){//可以带有一个或两个参数，为抛出的异常对象和堆栈信息 ( StackTrace 对象)
    rethrow; //使用 `rethrow` 关键字可以把捕获的异常重新抛出
} finally{
	
}

```

## 5 类

### 5.1 简介

Dart 是一个面向对象编程语言，每个对象都是一个类的实例，类都继承于 `Object`。

```dart
class Point {
   //自动生成一个 getter 方法（隐含的）。 非final 实例变量还会自动生成一个 setter 方法。
   num x;
   num y;
}
```

### 5.2 构造函数

```dart
class Point {
   num x;
   num y;
  
   Point(num x, num y) {      
      this.x = x;
      this.y = y;
   }
   //可以简化
   Point(this.x,this.y);
}
```

### 5.3 命名构造函数

Dart 不支持构造函数的重载，使用命名构造函数为一个类实现多个构造函数。

```dart
class Point {
   num x;
   num y;
  
   Point(this.x,this.y);
   Point.y(this.y){
     x = 0;
   }  
}   
//使用
var p = Ponit.y(1)

```

### 5.4 初始化列表

```dart
class Point {
   num x;
   num y;
  
   Point(this.x,this.y);
   
   //初始化列表在构造函数运行前设置实例变量。
   Point.fromMap(Map json)
      :x = map['x'];
	   y = map['y'];
     
}   
//使用
var p = Ponit(1)

```

### 5.5 静态构造函数

类产生的对象永远不会改变，让这些对象成为编译时常量。

```dart
class Point{
  final num x;
  final num y;
  const Point(this.x,this.y);
  static final var origin = const Point(0,0);

}

```

### 5.6 重定向构造函数

重定向到该类的另一个构造函数

```dart
class Point {
    num x;
    num y;

    //主构造函数
    Point(this.x, this.y) {
        print("Point($x, $y)");
    }

    //重定向构造函数，指向主构造函数，函数体为空
    Point.alongXAxis(num x) : this(x, 0);
}

void main() {
    var p1 = new Point(1, 2);
    var p2 = new Point.alongXAxis(4);
}

```

### 5.7 工厂构造函数

使用 factory 关键词修饰的构造函数时，这个构造函数不必创建类的新实例。

```dart
class Logger {
   final String name;
   bool mute = false;

   // _cache 是一个私有库,名字前有个 _ 。 
   static final Map<String, Logger> _cache = <String, Logger>{};

   factory Logger(String name) {
       if (_cache.containsKey(name)) {
          return _cache[name];
       } else {
          final logger = new Logger._internal(name);
		  //工厂构造函数需要返回 Logger 实例对象
          _cache[name] = logger;
          return logger;
       }
    }

   ////以 _ 开头的函数、变量无法在库外使用
    Logger._internal(this.name);

    void log(String msg) {
       if (!mute) {
          print(msg);
       }
    }
    
 }


```

借助工厂构造函数实现单例。

```dart
class Manager {
  static Manager _instance;
  factory Manager.getInstance() {
     if(_instance == null){
	     _instance = Manager._internal;
	 }
	 return _instance;
  }
  Manager._internal;
}

```

### 5.8 Getters 和 Setters

Dart 每个实例变量都隐含的具有一个 getter，如果变量不是 final 还有一个 setter，可以通过实现 getter 和 setter 来创建新的属性。

```dart
class Rect {
   num left;
   num top;
   num width;
   num height;
   Rect(this.left,this.top,this.width,this.height);
   
   num get right => left + width;
   set right(num value) => left = value - width;  
}

void main(){
  var p = Point(1,2,3,4);
  var right = p.right //4
}
```

### 5.9 抽象类

使用 `abstract` 修饰符定义一个抽象类，抽象类中允许出现无方法体的方法。

```dart
abstract class Person {
  String name;
  void printName();

}

```

抽象类不能被实例化，但是可以定义工厂方法并返回子类。

```dart
abstract class Parent {
  String name;
  //默认构造方法
  Parent(this.name);
  //工厂方法返回Child实例
  factory Parent.test(String name){
    return new Child(name);
  }
  void printName();
}
//extends 继承抽象类
class Child extends Parent{
  Child(String name) : super(name);

  @override
  void printName() {
    print(name);
  }
}

void main() {
  var p = Parent.test("test");
  print(p.runtimeType); //输出类型 Child
  p.printName();		
}


```

### 5.9 类-隐式接口

每个类隐式的定义了一个接口，含有类的所有实例和它实现的所有接口。

```dart
class Person {
  final _name;

  Person(this._name);

  String greet(who) => "$who";
}

class Son implements Person {
  @override
  get _name => "";

  @override
  String greet(who) => "$who";
}




```

### 5.10 类-继承

使用 extends 创建一个子类，同时 supper 将指向父类。

```dart
class Child extends Person{
  Child(name) : super(name);
}
```

### 5.11 可调用的类

类实现了 `call()` 函数,则可以当做方法来调用。

```dart
class Closure {
  call(String a, String b) => '$a $b';
}

void main() {
  var c = new Closure();
  var out = c("Hello","Dart");
  print(out);
}
```

### 5.12 混合mixins

多类继承中重用一个类代码的方法，被mixin(混入)的类不能有构造函数。

```dart
class A {
  void a() {}

  String getMessage() => "TEST_A";
}

class B {
  void b() {}

  //和 A 同名方法
  String getMessage() => "TEST_B";
}

class P {
  String getMessage() => "TEST_P";
}

class AB with A, B {}
class BA with B, A {}

//继承与mixins是兼容的
class PAB estends P with B, A {}
//简化
class PAB = P with A, B;


void printMessage(obj) => print(obj.getMessage());
void main(){
  //假设A与B 存在相同的方法，以最右侧的混入类为主
  printMessage(AB()); //TEST_B
  printMessage(BA()); //TEST_A
  
  printMessage(PAB()); //TEST_B
}


```

mixins 弥补了接口和继承的不足，继承只能单继承，而接口无法复用实现。

## 6 异步编程

### 6.1 isolate 机制

Dart 语言中使用的并发机制，叫做 isolate 机制，不同于 Android 中的中线程，isolate 无法共享内存。Dart 是事件驱动，也有自己的Event Loop。

### 6.2 Event Loop

有两个队列，分别为微服务队列（Microtask queue），事件队列（Event queue）。

* 事件队列：包含外部事件，例如 I/O、Timer、绘制事件。
* 微服务队列：Dart 内部微服务，通过 scheduleMicrotask 来调度。

![](C:/Users/zpparts/Desktop/SoleilNotes/pic/Event-Loop.png)

1. 先检查 Microtask queue是否为空，不为空，执行 MicroTask。
2. 如果 Microtask queue 为空，判断 Event queue 是否为空，不为空执行 Event
3. 每执行完一个 Event，就检查 Microtask queue，如此循环。

由上面可知，Microtask queue 优先级比较高，可以利用微服务来进行插队。

### 6.3 异步支持

Dart 异步支持常使用的特性是async 方法和 await 表达式。Dart 库大多方法返回 Future 和 Stream 对象，这些方法是异步的，在设置耗时操作（比如 I/O 操作）之后返回，无需等待操作完成。

### 6.4 异步任务调度

有两种方式，通过 dart:async 这个库的API。

#### 6.4.1 将任务添加到 Microtask queue

```dart
import  'dart:async';

void  myTask(){
    print("this is my task");
}

void  main() {
    //1.使用 scheduleMicrotask 方法添加
    scheduleMicrotask(myTask);

    //2.使用 Future
    Future.microtask(myTask);
}
```

#### 6.4.2 将任务添加到 Event queue　

```dart
import  'dart:async';

void  myTask(){
    print("this is my task");
}

void  main() {
    
    //1.使用 Future
    Future.microtask(myTask);
}
```

### 6.5 Future

通常异步函数返回的对象是 Future，表示在事件队列中的处理一个事件的结果。使用 `then()` 来在 future 完成的时候执行其他代码。

```dart
void main(){
  Future(()=>getName())
         .then((m)=>"result:${m}")
		 .then((m) => {print(m)})
		 .catchError((e, s) {
             print(s); //异常处理
         }
		 .whenComplete(() => whenTaskCompelete);  //当所有任务完成后的回调函数

}

String getName() => "V1.0.0";

void whenTaskCompelete() => print("任务完成");


Future.delayed(const Duration(seconds: 1), () => getName); //延时任务
```

### 6.6 async/await

从Dart 1.9开始，Dart添加了async、await关键字实现异步的功能,当我们需要获得A的结果，再执行 B，需要使用 .then().then() 这种回调地狱，利用`async`与`await` 则可以避免。

```dart
Future<String>  getName() async => 'V1.0.1';


Future<String> getName() async {
  //await 等待future执行完成再执行后续代码
  String name = await getNameFromNet();
  return name;
}

Future getNameFromNet() async => "V1.1.0";

```

## 7 库的可见性

### 7.1 库的可见性

import,part,library 指令创建一个模块化、可共享的代码库，下划线(_) 开头的标识符只对内部库可见。

### 7.2 使用库

使用 import 来导入库。

```dart
import 'dart:html';
import 'package:utils/utils.dart';
```

### 7.3 库前缀

如果导入两个库是有冲突的标识符，需要指定一个或两个库的前缀。

```dart
import 'package:lib1/lib1.dart';
import 'package:lib2/lib2.dart' as lib2;

//使用lib1里的元素
var element1 = new Element();

//使用lib2里的元素
var element2 = lib2.Element();  

```

### 7.4 导入部分库

想使用的库一部分，可以选择性导入库。

```dart
//只导入foo库
 import 'package:lib1/lib1.dart' show foo;

//导入所有除了foo
import 'package:lib2/lib2.dart' hide foo;

```

### 7.6 延迟加载库

延迟(deferred)加载（也称为延迟(lazy)加载）允许应用程序按需加载库。

```dart
import 'package:deferred/hello.dart' deferred as hello;

//使用 LoadLibrary() 加载
greet() async {
   await hello.loadLibrary();
   hello.printGreeting();
}
```

### 7.7 实现库

使用 library 来实现库。

```dart
//声明库
library game

```

### 7.8 关联文件与库

使用 part of 标识符来添加文件。

```dart
//game.dart
library game;
part 'name.dart';


//name.dart;
part of game

```

### 7.9 导出库

使用 export ，将多个较小的库组合为一个较大的库或者重新导出库的一部分作为一个新的库。

```dart
//material.dart        这是一个组合库，建议不要在其中有功能代码  
library material;

export 'src/material/about.dart';
export 'src/material/animated_icons.dart';
export 'src/material/app.dart';
export 'src/material/app_bar.dart';

```



