## 1 存储类

存储类定义 C++ 程序中变量/函数的范围（可见性）和生命周期，这些说明符放置在它们所修饰的类型之前。

- auto
- register
- static
- extern
- mutable
- thread_local (C++11)

从 C++ 17 开始，auto 关键字不再是 C++ 存储类说明符，且 register 关键字被弃用。

```c++
//1.auto:声明变量时根据初始化表达式自动推断该变量的类型、声明函数时函数返回值的占位符
auto a = 4.5 //double
auto a = new auto(4) //int*    

//2.register:定义存储在寄存器中而不是 RAM 中的局部变量,用于需要快速访问的变量，比如计数器
 register int count;

//3.static:修饰局部变量：编译器在程序的生命周期内保持局部变量的存在，而不需要在每次它进入和离开作用域时进行创建和销毁，修饰全局变量：会使变量的作用域限制在声明它的文件内

//4.extern:通常用于当有两个或多个文件共享相同的全局变量或函数的时候,告诉编译器需要去其他文件找
//first.cpp
#include <iostream>
int count ;
extern void a();
 
int main() {
   count = 5;
   a();
}

//secord.cpp
#include <iostream>
 
void a(void){
   std::cout << "第二个文件" << std::endl;
}

//5.thread_local:变量副本，这些变量(或者说对象）在线程开始的时候被生成(allocated)，在线程结束的时候被销毁(deallocated)
thread_local int x;  // 命名空间下的全局变量
class X {
    static thread_local std::string s; // 类的static成员变量
};

static thread_local std::string X::s;  // X::s 是需要定义的
 
void foo()
{
    thread_local std::vector<int> v;  // 本地变量
}
```

1 注释

```c++
//1.单行注释
/*2.双行注释 */
//3.块注释符（/*...*/）是不可以嵌套使用的。使用 #if 0 ... #endif 来实现注释，且可以实现嵌套
#if condition   ->  如果 condition 条件为 true 执行 code1 ，否则执行 code2
  code1
#else  
  code2 
#endif  
```

## 2 数据类型

### 2.1 基本的内置类型

| 类型     | 关键字                                  |
| :------- | :-------------------------------------- |
| 布尔型   | bool                                    |
| 字符型   | char                                    |
| 整型     | int                                     |
| 浮点型   | float                                   |
| 双浮点型 | double                                  |
| 无类型   | void                                    |
| 宽字符型 | wchar_t  ->  typedef short int wchar_t; |

```c++
//wchar_t 类型定义
typedef short int wchar_t;
```

各种变量类型在内存中存储值时需要占用的内存，以及该类型的变量所能存储的最大值和最小值，不同系统会有所差异。

* unsigned ：无符号
* signed ：有符号

| 类型               | 位            | 范围                                                         |
| :----------------- | :------------ | :----------------------------------------------------------- |
| char               | 1 个字节      | -128 到 127 或者 0 到 255                                    |
| unsigned char      | 1 个字节      | 0 到 255                                                     |
| signed char        | 1 个字节      | -128 到 127                                                  |
| int                | 4 个字节      | -2147483648 到 2147483647                                    |
| unsigned int       | 4 个字节      | 0 到 4294967295                                              |
| signed int         | 4 个字节      | -2147483648 到 2147483647                                    |
| short int          | 2 个字节      | -32768 到 32767                                              |
| unsigned short int | 2 个字节      | 0 到 65,535                                                  |
| signed short int   | 2 个字节      | -32768 到 32767                                              |
| long int           | 8 个字节      | -9,223,372,036,854,775,808 到 9,223,372,036,854,775,807      |
| signed long int    | 8 个字节      | -9,223,372,036,854,775,808 到 9,223,372,036,854,775,807      |
| unsigned long int  | 8 个字节      | 0 到 18,446,744,073,709,551,615                              |
| float              | 4 个字节      | 精度型占4个字节（32位）内存空间，+/- 3.4e +/- 38 (~7 个数字) |
| double             | 8 个字节      | 双精度型占8 个字节（64位）内存空间，+/- 1.7e +/- 308 (~15 个数字) |
| long double        | 16 个字节     | 长双精度型 16 个字节（128位）内存空间，可提供18-19位有效数字。 |
| wchar_t            | 2 或 4 个字节 | 1 个宽字符                                                   |

### 2.2 typedef 声明

 typedef 为一个已有的类型取一个新的名字。

```c++
typedef int feet; //int 取名 feet
feet a;
```

### 2.3 枚举类型

```c++
enum color { red, green, blue } c;
c = blue;
//默认，第一个名称的值为 0，第二个名称的值为 1； c = 2

//例：
int main() {
    enum color{red,green,blue} c;
    c = blue;
    switch (c) {
        case red:
            std::cout << "red" << std::endl;
            break;
        case green:
            std::cout << "green" << std::endl;
            break;
        case blue:
            std::cout << "blue" << std::endl;
            break;
    }
    return 0;
}
```

## 3 变量类型

变量名称规定：

* 变量的名称可以由字母、数字和下划线字符组成
* 必须以字母或下划线开头
* 大小写敏感

```c++
//例：
int d = 3,a = 3;
short r = 3;
char a = 'a';
float = 4.5;
```

### 3.1 变量声明

向编译器保证变量以给定的类型和名称存在，这样编译器在不需要知道变量完整细节的情况下也能继续进一步的编译 （保证编译通过）

变量声明只在编译时有它的意义，在程序连接时编译器需要实际的变量声明。

使用多个文件，且只在其中一个文件中定义变量时，可以使用变量声明。``

```c++
#include <iostream>
//变量声明
extern int a, b;
int main(){
    //变量定义
    int a,b;
    a = 10;
    b = 20;
    std::count << a << std::endl;
    return 0;
}


//函数声明时，提供一个函数名，而函数的实际定义则可以在任何地方进行
int func();
int main(){
    //函数调用
    int i = func();
}
 
//函数定义
int func() {
    return 0;
}

//区别
int a = 0;     //定义并声明了变量 a
extern int a;  //只是声明了有一个变量 a 存在，具体 a 在哪定义的，需要编译器编译的时候去找。
```

## 4 变量作用域

- 局部变量：在函数或一个代码块内部声明的变量。
- 形式参数：在函数参数的定义中声明的变量。
- 全局变量：在所有函数外部声明的变量。

```c++
//1.局部变量
#include <iostream>
int main(){
    int a,b;
}

//1.全局变量
#include <iostream>
int b = 23;
int main(){
    int b = 13; //局部变量会覆盖全局变量
}

```

### 4.1 初始化局部变量和全局变量

局部变量被定义时，系统不会对其初始化。

全局变量被定义时，系统初始化如下表所示。

| 数据类型 | 初始化默认值 |
| :------- | :----------- |
| int      | 0            |
| char     | '\0'         |
| float    | 0            |
| double   | 0            |
| pointer  | NULL         |

## 5 常量

常量是固定值，在程序执行期间不会改变。这些固定的值，又叫做**字面量**。

### 5.1 定义常量

```c++
//1.#define 预处理
#include <iostream>
using namespace std;
 
#define LENGTH 10   //没有 ;
#define WIDTH  5

int main(){
   int area;  
   area = LENGTH * WIDTH;
   cout << area << endl;  
   return 0;
}

//2.const关键字
#include <iostream>
using namespace std;

int main(){
   int area;  
   const int LENGTH = 10;
   const int WIDTH = 10;
   area = LENGTH * WIDTH;
   cout << area << endl;  
   return 0;
}

```

## 6 修饰符类型

C++ 允许在 **char、int 、 double** 数据类型前放置修饰符。修饰符用于改变基本类型的含义，所以它更能满足各种情境的需求。

- signed
- unsigned
- long
- short

**signed、unsigned、long 和 short** 可应用于整型

**signed** 和 **unsigned** 可应用于字符型

**long** 可应用于双精度型

修饰符 **signed** 和 **unsigned** 也可以作为 **long** 或 **short** 修饰符的前缀。例如：**unsigned long int**。

C++ 允许使用速记符号来声明**无符号短整数**或**无符号长整数**，可以不写 int，只写 **unsigned、short** 或 **unsigned、long**，int 是隐含的。

```c++
unsigned x;
unsigned int y;  //这两个类似
```

### 6.1 类型限定符

| 限定符   | 含义                                                         |
| :------- | :----------------------------------------------------------- |
| const    | 常量，在程序执行期间不能被修改改变。                         |
| volatile | 修饰符 **volatile** 告诉编译器不需要优化volatile声明的变量，让程序可以直接从内存中读取变量。对于一般的变量编译器会对变量进行优化，将内存中的变量值放在寄存器中以加快读写效率。 |
| restrict | 由 **restrict** 修饰的指针是唯一一种访问它所指向的对象的方式。只有 C99 增加了新的类型限定符 restrict。 |

## 7 存储类

存储类定义 C++ 程序中变量/函数的范围（可见性）和生命周期，这些说明符放置在它们所修饰的类型之前。

- auto
- register
- static
- extern
- mutable
- thread_local (C++11)

从 C++ 17 开始，auto 关键字不再是 C++ 存储类说明符，且 register 关键字被弃用。

```c++
//1.auto:声明变量时根据初始化表达式自动推断该变量的类型、声明函数时函数返回值的占位符
auto a = 4.5 //double
auto a = new auto(4) //int*    

//2.register:定义存储在寄存器中而不是 RAM 中的局部变量,用于需要快速访问的变量，比如计数器
 register int count;

//3.static:修饰局部变量：编译器在程序的生命周期内保持局部变量的存在，而不需要在每次它进入和离开作用域时进行创建和销毁，修饰全局变量：会使变量的作用域限制在声明它的文件内

//4.extern:通常用于当有两个或多个文件共享相同的全局变量或函数的时候,告诉编译器需要去其他文件找
//first.cpp
#include <iostream>
int count ;
extern void a();
 
int main() {
   count = 5;
   a();
}

//secord.cpp
#include <iostream>
 
void a(void){
   std::cout << "第二个文件" << std::endl;
}

//5.thread_local:变量副本，这些变量(或者说对象）在线程开始的时候被生成(allocated)，在线程结束的时候被销毁(deallocated)
thread_local int x;  // 命名空间下的全局变量
class X {
    static thread_local std::string s; // 类的static成员变量
};

static thread_local std::string X::s;  // X::s 是需要定义的
 
void foo()
{
    thread_local std::vector<int> v;  // 本地变量
}
```

## 8 运算符

- 算术运算符：+、-、*、/、%、++、--
- 关系运算符：==、!=、>、<、 <=、>= 
- 逻辑运算符:&&、||、!
- 位运算符:&、|、^、~、<<、 >>
- 赋值运算符
- 杂项运算符

```c++
//1.sizeof:返回变量大小

//2.条件运算符: Exp1 ? Exp2 : Exp3;
int x, y = 10;
x = (y < 10) ? 30 : 40;

//3.逗号运算符:使用逗号运算符是为了把几个表达式放在一起,整个逗号表达式的值为系列中最后一个表达式的值。
int i = 1, j;
i = (i++, j++, j++);
cout << j << endl; // 2

//4.. 和 ->
struct Employee {
  char first_name[16];
  int  age;
} emp;
//（.）点运算符
strcpy(emp.first_name, "张三");
//（->）箭头运算符
// p_emp 是指针，指向类型为 Employee 的对象，则要把值 "zara" 赋给对象 emp 的 first_name 成员
strcpy(p_emp -> first_name, "张三");

```

## 9 循环

```c++
#include <iostream>
using namespace std;
 
int main (){
   int a = 10;
    // 1.while
    while (a < 20) {
        cout << "a:" << a << endl;
        a++;
    }

    //2.for
    for (int b = 10; b < 20; b++) {
        cout << "b:" << b << endl;
    }
    
    //基于范围的for循环(C++11)
    int my_array[5] = { 1, 2, 3, 4, 5 };
    // 不会改变 my_array 数组中元素的值
    // x 将使用 my_array 数组的副本
    for (int x : my_array) {
        x *= 2;
        cout << x << endl;
    }

    // 会改变 my_array 数组中元素的值
    // 符号 & 表示 x 是一个引用变量，将使用 my_array 数组的原始数据
    // 引用是已定义的变量的别名
    for (int &x : my_array) {
        x *= 2;
        cout << x << endl;
    }

    // 还可直接使用初始化列表
    for (int x : {1, 2, 3, 4, 5}) {
        x *= 2;
        cout << x << endl;
    }
}
```

### 9.1 循环控制语句

| 控制语句      | 描述                                                         |
| :------------ | :----------------------------------------------------------- |
| break         | 终止 **loop** 或 **switch** 语句，程序流将继续执行紧接着 loop 或 switch 的下一条语句。 |
| continue 语句 | 引起循环跳过主体的剩余部分，立即重新开始测试条件。           |
| goto 语句     | 将控制转移到被标记的语句，不建议在程序中使用 goto 语句。     |

## 10 判断语句

```c++
if
if..else
if..else..if
switch  case break 
    
//三目运算符
int x, y = 10;
x = (y < 10) ? 30 : 40;    
```

## 11 函数

每个 C++ 程序都至少有一个函数，主函数 **main()** 。

```c++
//函数返回两个数中较大的那个数
int max(int num1, int num2) {
   // 局部变量声明
   int result;
   if (num1 > num2){
      result = num1;
   }
   else{
      result = num2; 
   }     
   return result; 
}
```

### 11.1 函数声明

告诉编译器函数名称及如何调用函数。函数的实际主体可以单独定义。

```c++
int max(int num1, int num2);
//参数的名称并不重要，只有参数的类型是必需的
int max(int, int);
```

一个源文件中定义函数且在另一个文件中调用函数时，函数声明是必需的，应该在调用函数的文件顶部声明函数。

```c++
#include <iostream>
using namespace std;
int max(int, int);
int main() {
    int a = max(4, 78);
    cout << a << endl;
    return 0;
}
int max(int num1, int num2) {
   // 局部变量声明
   int result;
   if (num1 > num2){
      result = num1;
   }
   else{
      result = num2; 
   }     
   return result; 
}
```

### 11.2 函数参数

#### 11.2.1 传值调用

不会更改原值

```c++
// 函数定义
void swap(int x, int y){
   int temp;
   temp = x; 
   x = y;    
   y = temp;  
}

#include <iostream>
using namespace std;
 
// 函数声明
void swap(int, int);
 
int main (){
   // 局部变量声明
   int a = 100;
   int b = 200;
   cout << "交换前，a 的值：" << a << endl;
   cout << "交换前，b 的值：" << b << endl;
   // 调用函数来交换值
   swap(a, b);
   cout << "交换后，a 的值：" << a << endl;
   cout << "交换后，b 的值：" << b << endl;
 
   return 0;
}
//交换前，a 的值： 100
//交换前，b 的值： 200
//交换后，a 的值： 100
//交换后，b 的值： 200
```

#### 11.2.2 指针调用

向函数传递参数的**指针调用**方法，把参数的地址复制给形式参数。在函数内，该地址用于访问调用中要用到的实际参数，修改形式参数会影响实际参数。

```c++
// 函数定义
void swap(int *x, int *y){
   int temp;
   temp = *x; 
   *x = *y;    
   *y = temp;  
}

#include <iostream>
using namespace std;
 
// 函数声明
void swap(int *x, int *y);
 
int main (){
   // 局部变量声明
   int a = 100;
   int b = 200;
   cout << "交换前，a 的值：" << a << endl;
   cout << "交换前，b 的值：" << b << endl;
   // 调用函数来交换值
   swap(&a, &b);
   cout << "交换后，a 的值：" << a << endl;
   cout << "交换后，b 的值：" << b << endl;
 
   return 0;
}
//交换前，a 的值： 100
//交换前，b 的值： 200
//交换后，a 的值： 200
//交换后，b 的值： 100
```

#### 11.2.3 引用调用

向函数传递参数的**引用调用**方法，把引用的地址复制给形式参数。在函数内，该引用用于访问调用中要用到的实际参数。这意味着，修改形式参数会影响实际参数。

```c++
// 函数定义
void swap(int &x, int &y){
   int temp;
   temp = x; 
   x = y;    
   y = temp;  
}

#include <iostream>
using namespace std;
 
// 函数声明
void swap(int *x, int *y);
 
int main (){
   // 局部变量声明
   int a = 100;
   int b = 200;
   cout << "交换前，a 的值：" << a << endl;
   cout << "交换前，b 的值：" << b << endl;
   // 调用函数来交换值
   swap(a, b);
   cout << "交换后，a 的值：" << a << endl;
   cout << "交换后，b 的值：" << b << endl;

   return 0;
}
//交换前，a 的值： 100
//交换前，b 的值： 200
//交换后，a 的值： 200
//交换后，b 的值： 100
```

### 11.3 参数的默认值

定义一个函数，以为参数列表中后边的每一个参数指定默认值。

```c++
// 函数定义
int sum(int x, int y = 300){
   return x + y;
}

sum(5);
sum(5,899);
```

### 11.4 Lambda 函数与表达式

C++11 提供了对匿名函数的支持,称为 Lambda 函数(也叫 Lambda 表达式)。

```c++
[capture](parameters) mutable ->return-type{statement}
```

-  **[capture]**：捕捉列表。捕捉列表总是出现在 lambda 表达式的开始处。事实上，[] 是 lambda 引出符。编译器根据该引出符判断接下来的代码是否是 lambda 函数。捕捉列表能够捕捉上下文中的变量供 lambda 函数使用。
-  (parameters)：参数列表。与普通函数的参数列表一致。如果不需要参数传递，则可以连同括号 () 一起省略。
-  **mutable**：mutable 修饰符。默认情况下，lambda 函数总是一个 const 函数，mutable 可以取消其常量性。在使用该修饰符时，参数列表不可省略（即使参数为空）。
-  **->return_type**：返回类型。用追踪返回类型形式声明函数的返回类型。出于方便，不需要返回值的时候也可以连同符号 -> 一起省略。此外，在返回类型明确的情况下，也可以省略该部分，让编译器对返回类型进行推导。
-  **{statement}**：函数体。内容与普通函数一样，不过除了可以使用参数之外，还可以使用所有捕获的变量。

```c++
[](int x, int y){ return x < y; }
[]{ x++; }
[](int x, int y) -> int { int z = x + y; return z + x; } //指定返回类型
```

```c++
[]      // 沒有定义任何变量。使用未定义变量会引发错误。
[x, &y] // x以传值方式传入（默认），y以引用方式传入。
[&]     // 任何被使用到的外部变量都隐式地以引用方式加以引用。
[=]     // 任何被使用到的外部变量都隐式地以传值方式加以引用。
[&, x]  // x显式地以传值方式加以引用。其余变量以引用方式加以引用。
[=, &z] // z显式地以引用方式加以引用。其余变量以传值方式加以引用。
```

##  12 数字

当我们需要用到数字时，我们会使用原始的数据类型，如 int、short、long、float 和 double 等等

### 12.1  随机数

srand() 和 srand()

```c++
#include <iostream>
#include <ctime>
#include <cstdlib>
 #include <ctime>
using namespace std;
 
int main (){
   int i,j; 
   // 设置种子
   srand( (unsigned)time( NULL ) );
 
   /* 生成 10 个随机数 */
   for( i = 0; i < 10; i++ )
   {
      // 生成实际的随机数
      j= rand();
      cout <<"随机数： " << j << endl;
   }
 
   return 0;
}
```

## 13 数组

存储一个固定大小的相同类型元素的顺序集合。

```c++
#include <iostream>
using namespace std;
int main(){
    int a[10];
    for(int i = 0;i < 5;i++){
        a[i] = i; //访问数组
    }    
}

```

### 13.1 指向数组的指针

```c++
double *p;
double a[10];
p = a;
//*p、*(p + 1) 等访问数组元素
```

### 13.2 传递数组给函数

```c++
void func(int *p)
void func(int p[10])
void func(int p[])    
```

### 13.3 函数返回数组

```c++
int * getRandom(){
    static int r[1]; // 局部函数 必须使用 static
    r[1] = 10;
    return r;
}
```

## 14 字符串

C++ 提供了以下两种类型的字符串表示形式：

* C 风格字符串
* C++ 引入的 string 类类型

```c++
//1.c
char a[6] = {'H', 'e', 'l', 'l', 'o', '\0'};
char b[] = "Hello";

//2.c++
#include <string>

string c = "Hello";

```

## 15 指针

指针是一个变量，其值为另一个变量的地址，即内存位置的直接地址。

```c++
int    *ip;    /* 一个整型的指针 */
double *dp;    /* 一个 double 型的指针 */
float  *fp;    /* 一个浮点型的指针 */
char   *ch;    /* 一个字符型的指针 */

```

### 16.1 使用指针

```c++
#include <iostream>
using namespace std;

int main (){
   int  var = 20;   // 实际变量的声明
   int  *ip;        // 指针变量的声明
   ip = &var;       // 在指针变量中存储 var 的地址
   cout << var << endl;
   
   // 输出在指针变量中存储的地址
   cout << ip << endl; 
 
   // 访问指针中地址的值
   cout << *ip << endl;
 
   return 0;
}

```

### 15.2 Null 指针

空指针：在变量声明的时候，如果没有确切的地址可以赋值，建议为指针变量赋一个 NULL 值。

```c++
#include <iostream>
using namespace std;
int main (){
   int *ptr = NULL;
   cout << "ptr 的值是 " << ptr ; // 0
   return 0;
}
//检查空指针
if(ptr)
```

### 15.3 从函数返回指针

```c++
int * func(){
    static int r[1]; // 局部函数 必须使用 static
    r[1] = 10;
    return r;
}
//不支持在函数外返回局部变量的地址，除非定义局部变量为 static 变量

```

## 16 引用

引用变量是一个**别名**，它是某个已存在变量的另一个名字。一旦把引用初始化为某个变量，就可以使用该引用名称或变量名称来指向变量。

引用不会内存分配，减少资源。

### 16.1 使用

```c++
#include <iostream> 
using namespace std;
int main (){
   int i;
   // 声明引用变量
   int& r = i;
   i = 5;
   cout << i << endl;
   return 0;
}
```

### 16.2  把引用作为参数

```c++
#include <iostream>
using namespace std;
 
// 函数声明
void swap(int& x, int& y);
 
int main (){
   // 局部变量声明
   int a = 100;
   int b = 200;
 
   cout << "交换前，a 的值：" << a << endl;
   cout << "交换前，b 的值：" << b << endl;
 
   /* 调用函数来交换值 */
   swap(a, b);
 
   cout << "交换后，a 的值：" << a << endl;
   cout << "交换后，b 的值：" << b << endl;
 
   return 0;
}
 
// 函数定义
void swap(int& x, int& y) {
   int temp;
   temp = x; /* 保存地址 x 的值 */
   x = y;    /* 把 y 赋值给 x */
   y = temp; /* 把 x 赋值给 y  */ 
   return;
}
```

### 16.4 把引用作为返回值

过使用引用来替代指针，会使 C++ 程序更容易阅读和维护。

```c++
#include <iostream>
 
using namespace std;
 
double vals[] = {10.1, 12.6, 33.1, 24.1, 50.0};
 
double& setValues( int i ){
  return vals[i];   // 返回第 i 个元素的引用
}
 
int main () {
   cout << "改变前的值" << endl;
   for ( int i = 0; i < 5; i++ ){
       cout << "vals[" << i << "] = ";
       cout << vals[i] << endl;
   }
   setValues(1) = 20.23; // 改变第 2 个元素
   setValues(3) = 70.8;  // 改变第 4 个元素
   cout << "改变后的值" << endl;
   for ( int i = 0; i < 5; i++ ){
       cout << "vals[" << i << "] = ";
       cout << vals[i] << endl;
   }
   return 0;
}
```

## 17  日期和时间

C++ 标准库没有提供所谓的日期类型，需要引用 <ctime> 头文件。

```c++
#include <iostream>
#include <ctime>
 
using namespace std;
int main( ){
   // 基于当前系统的当前日期/时间
   time_t now = time(0);
   
   // 把 now 转换为字符串形式
   char* dt = ctime(&now);
    
   cout << "本地日期和时间：" << dt << endl;
 
   // 把 now 转换为 tm 结构
   tm *gmtm = gmtime(&now);
   dt = asctime(gmtm);
   cout << "UTC 日期和时间："<< dt << endl;
}
```

## 18 I/O 库头文件

| 头文件     | 函数和描述                                                   |
| :--------- | :----------------------------------------------------------- |
| <iostream> | 该文件定义了 **cin、cout、cerr** 和 **clog** 对象，分别对应于标准输入流、标准输出流、非缓冲标准错误流和缓冲标准错误流。 |
| <iomanip>  | 该文件通过所谓的参数化的流操纵器（比如 **setw** 和 **setprecision**），来声明对执行标准化 I/O 有用的服务。 |
| <fstream>  | 该文件为用户控制的文件处理声明服务。                         |

```c++
#include <iostream>
using namespace std;
int main( ){
   //标准输出流 cout 
   char str[] = "cout";
   cout << str << endl;
    
   char name[50];
 
    //标准输入流 cin  
   cout << "请输入您的名称： ";
   cin >> name;
   cout << "您的名称是： " << name << endl;
    
   //标准错误流 cerr  
   char err[] = "cerr";
   cerr << err << endl;
    
   //标准日志流 clog 
   char log[] = "clog";
   clog << log << endl;
    
   return 0;
}

```

## 19 数据结构

数据结构 是 C++ 中另一种用户自定义的可用的数据类型存储不同类型的数据项。

```c++
#include <iostream>
#include <cstring>
using namespace std;

void printBook(struct Book);
void printBook2(struct Book *);
struct Book {
    char title[40];
    double price;
};

int main() {
    Book book;
    strcpy(book.title, "Java");
    book.price = 39.0;
    //cout << book.title << endl;
    //cout << book.price << endl;
    printBook(book);
    printBook2(&book);
    return 0;
}

//作为参数
void printBook(struct Book book){
    cout << book.title << endl;
    cout << book.price << endl;
}


//指针使用 ->
void printBook2(struct Book *book){
    cout << book->title << endl;
    cout << book->price << endl;
}
```

## 20 类和对象

```c++
class Person {
public://访问修饰符：public、rotected、private
    static int count; //静态成员,无论创建多少个类的对象，静态成员都只有一个副本。
    string name;

    void setName(string name);

    string getName();

    void setAge(int age);

    int getAge();

    Person();//构造函数

    Person(string name);//带参数构造函数

private:
    int age;
};

Person::Person() {}

Person::Person(string name) {
    this->name = name;
}

void Person::setAge(int age) {
    this->age = age;
}

int Person::getAge() {
    return age;
}

void Person::setName(string name) {
    this->name = name;
}

string Person::getName() {
    return name;
}

int main() {
    Person person;
    person.setName("Jack");
    person.setAge(30);

    Person person1("Maria");
    
    cout << person.getName() << endl;
    return 0;
}

```

### 20.1 拷贝构造函数

一种特殊的构造函数，它在创建对象时，是使用同一类中之前创建的对象来初始化新创建的对象。拷贝构造函数通常用于：

- 通过使用另一个同类型的对象来初始化新创建的对象。
- 复制对象把它作为参数传递给函数。
- 复制对象，并从函数返回这个对象。

如果在类中没有定义拷贝构造函数，编译器会自行定义一个。如果类带有指针变量，并有动态内存分配，则它必须有一个拷贝构造函数。

```c++
#include <iostream>
 
using namespace std;
 
class Line{
public:
     int getLength( void );
     Line( int len );            // 简单的构造函数
     Line(const Line &obj);      // 拷贝构造函数
     ~Line();                    // 析构函数,跳出程序（比如关闭文件、释放内存等）前释放资源
 
private:
    int *ptr;
};
 
// 成员函数定义，包括构造函数
Line::Line(int len){
   cout << "调用构造函数" << endl;
    // 为指针分配内存
   ptr = new int;
   *ptr = len;
}
 
Line::Line(const Line &obj){
   cout << "调用拷贝构造函数并为指针 ptr 分配内存" << endl;
   ptr = new int;
   *ptr = *obj.ptr; // 拷贝值
}
 
Line::~Line(void){
   cout << "释放内存" << endl;
   delete ptr;
}

int Line::getLength(void){
   return *ptr;
}
 
void display(Line obj){
   cout << "line 大小 : " << obj.getLength() <<endl;
}
 
int main( ){
   Line line(10); 
   display(line); 
   return 0;
}
```

### 20.2  友元函数

定义在类外部，但有权访问类的所有私有（private）成员和保护（protected）成员。

```c++
#include <iostream>
 
using namespace std;
 
class Box{
   double width;
public:
   friend void printWidth(Box box);
   void setWidth(double width);
};
 
// 成员函数定义
void Box::setWidth(double width){
    this ->width = wid;
}
 
//printWidth()不是任何类的成员函数
void printWidth(Box box){
   /* 因为 printWidth() 是 Box 的友元，它可以直接访问该类的任何成员 */
   cout << "Width of box : " << box.width <<endl;
}
 
// 程序的主函数
int main( ){
   Box box; 
   // 使用成员函数设置宽度
   box.setWidth(10.0);   
   // 使用友元函数输出宽度
   printWidth(box); 
   return 0;
}
```

### 20.3 内联函数（inline）

如果函数是内联的，那么在编译时，编译器会把该函数的代码副本放置在每个调用该函数的地方，每次修改，都要重新编译所有，空间换时间。

```c++
#include <iostream>
using namespace std;
inline int Max(int x, int y){
   return (x > y)? x : y;
}

// 程序的主函数
int main( ){
   cout << "Max (20,10): " << Max(20,10) << endl;
   cout << "Max (0,200): " << Max(0,200) << endl;
   cout << "Max (100,1010): " << Max(100,1010) << endl;
   return 0;
}
```

## 21 继承

当创建一个类时，您不需要重新编写新的数据成员和成员函数，只需指定新建的类继承了一个已有的类的成员即可。这个已有的类称为**基类**，新建的类称为**派生类**。

```c++
//基类
class Animal {
    // eat() 函数
    // sleep() 函数
};

//派生类
class Dog : public Animal {
    
};

class Dog : public Animal {
    // bark() 函数
};
//注意：和 Java 不同 c++ 支持 多继承
class Dog:public Animal,public Person {
    
}
```



## 22 重载

```c++
#include <iostream>
using namespace std;
 
class Person{
   public:
      void play(int i) {
        cout << "整数为: " << i << endl;
      }
 
      void ply(double f) {
        cout << "浮点数为: " << f << endl;
      }
};
```

## 23 多态

意味着调用成员函数时，会根据调用函数的对象的类型来执行不同的函数。

```c++
class Animal {
public:
    virtual void eat() {//虚函数,动态链接(后期绑定),告诉派生类不要链接

    }
    
    //virtual void eat() = 0 //纯虚函数,啥也不干，派生类自己去干    
};

class Dog : public Animal {
public:
    void eat() {
        cout << "狗吃狗粮" << endl;
    }
};

class Cat : public Animal {
public:
    void eat() {
        cout << "猫吃猫粮" << endl;
    }
};


int main() {
     Animal *animal;
    Dog dog;
    animal = &dog;
    animal->eat();

    Cat cat;
    animal = &cat;
    animal->eat();

    return 0;
}
```

## 24 数据抽象

只向外界提供关键信息，并隐藏其后台的实现细节，即只表现必要的信息而不呈现细节。

## 25 数据封装

把数据和操作数据的函数绑定在一起的一个概念，这样能避免受到外界的干扰和误用，从而确保了安全。数据封装引申出了另一个重要的 OOP 概念，即**数据隐藏**。

```c++
class Person{
public:
    string getName();
private:
    string name;   
}
```

## 26 接口（抽象类）

```c++
class Animal {
public:
    virtual void eat() = 0 //提供接口框架的纯虚函数 
};
```

## 27 文件和流

| 数据类型 | 描述                                                         |
| :------- | :----------------------------------------------------------- |
| ofstream | 该数据类型表示输出文件流，用于创建文件并向文件写入信息。     |
| ifstream | 该数据类型表示输入文件流，用于从文件读取信息。               |
| fstream  | 该数据类型通常表示文件流，且同时具有 ofstream 和 ifstream 两种功能，这意味着它可以创建文件，向文件写入信息，从文件读取信息。 |

### 27.1 打开文件

```c++
//打开的文件的名称和位置   文件被打开的模式
void open(const char *filename, ios::openmode mode);
```

打开模式

| 模式标志   | 描述                                                         |
| :--------- | :----------------------------------------------------------- |
| ios::app   | 追加模式。所有写入都追加到文件末尾。                         |
| ios::ate   | 文件打开后定位到文件末尾。                                   |
| ios::in    | 打开文件用于读取。                                           |
| ios::out   | 打开文件用于写入。                                           |
| ios::trunc | 如果该文件已经存在，其内容将在打开文件之前被截断，即把文件长度设为 0。 |

### 27.2 例子

```c++
#include <fstream>
#include <iostream>
using namespace std;
 
int main (){   
   char data[100];
 
   // 以写模式打开文件
   ofstream outfile;
   outfile.open("afile.dat");
 
   cout << "Writing to the file" << endl;
   cout << "Enter your name: "; 
   cin.getline(data, 100);
 
   // 向文件写入用户输入的数据
   outfile << data << endl;
 
   cout << "Enter your age: "; 
   cin >> data;
   cin.ignore();
   
   // 再次向文件写入用户输入的数据
   outfile << data << endl;
 
   // 关闭打开的文件
   outfile.close();
 
   // 以读模式打开文件
   ifstream infile; 
   infile.open("afile.dat"); 
 
   cout << "Reading from the file" << endl; 
   infile >> data; 
 
   // 在屏幕上写入数据
   cout << data << endl;
   
   // 再次从文件读取数据，并显示它
   infile >> data; 
   cout << data << endl; 
 
   // 关闭打开的文件
   infile.close();
   return 0;
}
```

##  28 异常处理

```c++
try
{
   // 保护代码
}catch( ExceptionName e1 ){
   // catch 块
}catch( ExceptionName e2 ){
   // catch 块
}catch( ExceptionName eN ){
   // catch 块
}
```

| 异常                   | 描述                                                         |
| :--------------------- | :----------------------------------------------------------- |
| **std::exception**     | 该异常是所有标准 C++ 异常的父类。                            |
| std::bad_alloc         | 该异常可以通过 **new** 抛出。                                |
| std::bad_cast          | 该异常可以通过 **dynamic_cast** 抛出。                       |
| std::bad_exception     | 这在处理 C++ 程序中无法预期的异常时非常有用。                |
| std::bad_typeid        | 该异常可以通过 **typeid** 抛出。                             |
| **std::logic_error**   | 理论上可以通过读取代码来检测到的异常。                       |
| std::domain_error      | 当使用了一个无效的数学域时，会抛出该异常。                   |
| std::invalid_argument  | 当使用了无效的参数时，会抛出该异常。                         |
| std::length_error      | 当创建了太长的 std::string 时，会抛出该异常。                |
| std::out_of_range      | 该异常可以通过方法抛出，例如 std::vector 和 std::bitset<>::operator[]()。 |
| **std::runtime_error** | 理论上不可以通过读取代码来检测到的异常。                     |
| std::overflow_error    | 当发生数学上溢时，会抛出该异常。                             |
| std::range_error       | 当尝试存储超出范围的值时，会抛出该异常。                     |
| std::underflow_error   | 当发生数学下溢时，会抛出该异常。                             |

### 28.1 定义新的异常

```c++
#include <iostream>
#include <exception>
using namespace std;
 
struct MyException : public exception{
  const char * what () const throw () {
    return "C++ Exception";
  }
};
 
int main(){
  try {
    throw MyException();
  }
  catch(MyException& e){
    std::cout << "MyException caught" << std::endl;
    std::cout << e.what() << std::endl;
  }
  catch(std::exception& e) {
    //其他的错误
  }
}
```

## 29 动态内存

```c++
//new 和 delete 运算符
#include <iostream>
using namespace std;
 
int main (){
   double* pvalue  = NULL; // 初始化为 null 的指针，尽量不要使用 malloc() 函数
   pvalue  = new double;   // 使用 new 动态分配内存 
 
   *pvalue = 29494.99;     // 在分配的地址存储值
   cout << "Value of pvalue : " << *pvalue << endl;
   delete pvalue;         // 释放内存 
   return 0;
}
```

### 29.1 数组的动态内存分配

```c++
char* pvalue  = NULL;   // 初始化为 null 的指针
pvalue  = new char[20]; // 为变量请求内存
delete [] pvalue;//释放内存
```

### 29.2 对象的动态内存分配

```c++
#include <iostream>
using namespace std;
 
class Box{
   public:
      Box() { 
         cout << "调用构造函数！" <<endl; 
      }
      ~Box() { 
         cout << "调用析构函数！" <<endl; 
      }
};
 
int main( ){
   Box* a = new Box[4];
   delete [] a; 
   return 0;
}
```

## 30 命名空间

作为附加信息来区分不同库中相同名称的函数、类、变量，区分有相同的名称。

```c++
#include <iosteam>
using namespace std;
namespace a{
    void f(){
        cout << "a.f()" << endl;
    }
}

namespace b{
    void f(){
         cout << "b.f()" << endl;
    }
}

namespace c{
    void f(){
         cout << "c.f()" << endl;
    }
    namespace d{ //嵌套命名空间
       void f(){
         cout << "d.f()" << endl;
       }
    }
}

using namespace c::d;
int main(){
    a::f();
    b::f();
    f();//调用 d
}
```

## 31 模板

模板是泛型编程的基础，泛型编程即以一种独立于任何特定类型的方式编写代码。

```c++
#include <iostream>
#include <string>
using namespact std;
template <typename T>
inline T const& max(T const& a,T const& b){
    return a < b ? b : a:
}

int main(){
    max(2.3,3.6);
    max(2,4);       
}
```

### 31.1 类模板

```c++
#include <iostream>
#include <vector>
#include <cstdlib>
#include <string>
#include <stdexcept>
 
using namespace std;
 //定义一个栈模板
template <class T>
class Stack { 
  private: 
    vector<T> elems;     // 元素 
 
  public: 
    void push(T const&);  // 入栈
    void pop();               // 出栈
    T top() const;            // 返回栈顶元素
    bool empty() const{       // 如果为空则返回真。
        return elems.empty(); 
    } 
}; 
 
template <class T>
void Stack<T>::push (T const& elem) { 
    // 追加传入元素的副本
    elems.push_back(elem);    
} 
 
template <class T>
void Stack<T>::pop () { 
    if (elems.empty()) { 
        throw out_of_range("Stack<>::pop(): empty stack"); 
    }
    // 删除最后一个元素
    elems.pop_back();         
} 
 
template <class T>
T Stack<T>::top () const { 
    if (elems.empty()) { 
        throw out_of_range("Stack<>::top(): empty stack"); 
    }
    // 返回最后一个元素的副本 
    return elems.back();      
} 
 
int main() { 
    try { 
        Stack<int>  intStack;  // int 类型的栈 
        Stack<string> stringStack;    // string 类型的栈 
 
        // 操作 int 类型的栈 
        intStack.push(7); 
        cout << intStack.top() <<endl; 
 
        // 操作 string 类型的栈 
        stringStack.push("hello"); 
        cout << stringStack.top() << std::endl; 
        stringStack.pop(); 
        stringStack.pop(); 
    } 
    catch (exception const& ex) { 
        cerr << "Exception: " << ex.what() <<endl; 
        return -1;
    } 
}
```

## 32 预处理器

预处理器是一些指令，指示编译器在实际编译之前所需完成的预处理。(程序开始前，需要处理一些东西)。

```c++
//#define 预处理
//1.宏定义 可以理解常量
#define PI 3.14159

//2.带参数宏定义
#define MIN(a,b)(a < b ? a : b)
```

### 32.1 条件编译 

条件编译：用来有选择地对部分程序源代码进行编译。

```c++
#ifdef NULL
   #define NULL 0
#endif

//可以只在调试时进行编译，调试开关可以使用一个宏来实现
#ifdef DEBUG
   cerr <<"Variable x = " << x << endl;
#endif

//或
#if 0
   不进行编译的代码
#endif
```

### 32.2 # 和 ## 运算符

```c++
#include <iostream>
#define MKSTR(x) #x  //参数转换成一个字符串
#define CONCAT(x, y)  x ## y // 连接符号，把参数连在一起。
int main (){
    cout << MKSTR(HELLO C++) << endl;//HELLO C++
    
    int xy = 100; 
    cout << concat(x, y); //100
    return 0;
}

```

## 33 线程

c++ 11 之后有了标准的线程库。

```c++
#include <iostream>

#include <thread>

std::thread::id main_thread_id = std::this_thread::get_id();

void hello()  
{
    std::cout << "Hello Concurrent World\n";
    if (main_thread_id == std::this_thread::get_id())
        std::cout << "This is the main thread.\n";
    else
        std::cout << "This is not the main thread.\n";
}

void pause_thread(int n) {
    std::this_thread::sleep_for(std::chrono::seconds(n));
    std::cout << "pause of " << n << " seconds ended\n";
}

int main() {
    std::thread t(hello);
    std::cout << t.hardware_concurrency() << std::endl;//可以并发执行多少个(不准确)
    std::cout << "native_handle " << t.native_handle() << std::endl;//可以并发执行多少个(不准确)
    t.join();
    std::thread a(hello);
    a.detach();
    std::thread threads[5];                         // 默认构造线程

    std::cout << "Spawning 5 threads...\n";
    for (int i = 0; i < 5; ++i)
        threads[i] = std::thread(pause_thread, i + 1);   // move-assign threads
    std::cout << "Done spawning threads. Now waiting for them to join:\n";
    for (auto &thread : threads)
        thread.join();
    std::cout << "All threads joined!\n";
}
```

## 34 STL 

C++ STL（标准模板库）是一套功能强大的 C++ 模板类，提供了通用的模板类和函数，这些模板类和函数可以实现多种流行和常用的算法和数据结构，如向量、链表、队列、栈。

| 组件                | 描述                                                         |
| :------------------ | :----------------------------------------------------------- |
| 容器（Containers）  | 容器是用来管理某一类对象的集合。如 deque、list、vector、map 等。 |
| 算法（Algorithms）  | 算法作用于容器。它们提供了执行各种操作的方式，包括对容器内容执行初始化、排序、搜索和转换等操作。 |
| 迭代器（iterators） | 迭代器用于遍历对象集合的元素。这些集合可能是容器，也可能是容器的子集。 |

## 35 信号处理

信号是由操作系统传给进程的中断，会提早终止一个程序，有些信号不能被程序捕获，但是下表所列信号可以在程序中捕获，并可以基于信号采取适当的动作。这些信号是定义在 C++ 头文件 <csignal> 中。

| 信号    | 描述                                         |
| :------ | :------------------------------------------- |
| SIGABRT | 程序的异常终止，如调用 **abort**。           |
| SIGFPE  | 错误的算术运算，比如除以零或导致溢出的操作。 |
| SIGILL  | 检测非法指令。                               |
| SIGINT  | 程序终止(interrupt)信号。                    |
| SIGSEGV | 非法访问内存。                               |
| SIGTERM | 发送到程序的终止请求。                       |

```c++
#include <iostream>
#include <csignal>
#include <unistd.h>
 
using namespace std;
 
void signalHandler(int signum) {
    cout << "Interrupt signal (" << signum << ") received.\n";
    // 清理并关闭
    // 终止程序  
   exit(signum);  
}
 
int main (){
    // 注册信号 SIGINT 和信号处理程序
    signal(SIGINT, signalHandler);  
    while(1){
       cout << "Going to sleep...." << endl;
       if( i == 3 ){
          raise(SIGINT); //raise():生成信号，带有一个整数信号编号作为参数
       }
       sleep(1);
    }
    return 0;
}
//Ctrl+C 来中断程序
```

