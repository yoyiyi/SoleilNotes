## 一、前言
关于C/C++这两个玩意，自从大学毕业之后，接触到的地方也比较少了，抽空把以前零散笔记整理下，不过以前也是整理菜鸟教程。虽然业务中涉及到的 C/C++ 部分，有专门 C大佬搞。但是 Android 底层涉及到 C/C++，看一些源码 C/C++ 还是非常重要的。
## 二、开始
### 2.1 简介
1. 通用、面向过程的语言，1972 年，为了移植与开发 UNIX 操作系统，丹尼斯·里奇在贝尔电话实验室设计开发了 C 语言。
2. 最新标准为 C11，之前标准为 C99。
```c
# include <stdio.h>//头文件
//main 函数
int main(){
  printf("Hello World");
  return 0; //退出程序
}
```
### 2.1.1 特点
1. 易于学习
2. 结构化语言
3. 产生高效率的程序
4. 可以处理底层活动
5. 多种计算机平台上编译
### 2.1.2 关于 C
1. 为编写 UNIX 操作系统而发明
2. 以 B 语言为基础
3. 标准有 ANSI 制定
4. 截止 1973年，UNIX 操作系统完全使用 C
5. C 语言是最广泛的使用语言
6. 大多数先进的软件都是 C 编写
7. Linux 和关系型数据库（MySql） 等由 C 编写
### 2.1.3 为什么要使用 C
1. 所产生的代码运行速度与汇编语言编写代码速度几乎一样。
# 三、语法
## 3.1 C 程序结构
1. 组成
1.预处理器指令
2.函数
3.变量
4.语句、表达式
5.注释
## 3.2 C 的令牌（Tokens）
1. C 由各种令牌组成，可以是关键字、标识符、常量、字符串常量、或者符号等
## 3.3 注释
```c
1.//   /*/ 单行注释
2./*
   多行注释 
  */ 
```
## 3.4 标识符
1. 标识符用来标识变量、函数等，由 A-Z、a-2、_下划线开始，不允许出现标点字符串（@、$、%），C 区分大小写

## 3.5 关键字
1. 关键字不能作为常量名、变量名、或其他标识符名称
## 3.6 空格
1. 只包含空格的行，称为空白行。
## 3.7 数据类型
| 类型      | 说明                                                       |
| --------- | ---------------------------------------------------------- |
| 基本类型  | 整数类型、浮点类型                                         |
| 枚举类型  | 也是算术类型，用来定义程序中只能赋予一定的离散整数值的变量 |
| void 类型 | 说明符，没有可用值                                         |
| 派生类型  | 指针类型、数组类型、结构类型、共用体类型、函数类型         |
1. 数组类型和结构类型称为聚合类型
## 3.8 整数类型
| 类型          | 字节     | 大小            |
| ------------- | -------- | --------------- |
| char          | 1字节    | -128-127、0-255 |
| unsigned char | 1字节    | 0-255           |
| signed char   | 1字节    | -128-127        |
| int           | 2或4字节 |                 |
| unsigned int  | 2或4字节 |                 |
| short         | 2字节    |                 |
| unsigned int  | 2字节    |                 |
| long          | 4字节    |                 |
| unsigned long | 4字节    |                 |

1. 获取某个类型、某个变量在特定平台上的准确大小，sizeof(type) 得到对象或类型的存储字节大小 

## 3.9 浮点类型
| 类型        | 存储大小 | 值范围              | 精度 |
| ----------- | -------- | ------------------- | ---- |
| float       | 4        | 1.2E-38 3.4E+38     | 6    |
| double      | 8        | 2.3E-308 1.7E+308   | 15   |
| long double | 16       | 3.4E-1932 1.1E+4932 | 19   |
## 3.10 void 类型
1. 函数返回为空
2. 函数参数为空
3. 指针指向 void  （void * 的指针代表对象的地址）
## 3.11 变量
### 3.11.1 变量定义
```c
type variable_list
int a;
```
### 3.11.2 变量声明
1. 需要建立存储空间
2. 不需要建立存储空间，通常使用 extern 关键字声明变量名而不去定义它
```c
extern int i;//声明，不是定义，i 可以在别的文件中定义
int i;//声明，也是定义
```
```c
//在一个源文件中引用另外一个源文件中定义的变量，加 extern
//addtwonum.c
extern int x;
extern int y;
int addtwonum(){
  return x+y;
}

//test.c
# include <stdio.h>
int x = 1;
int y = 2;
int addtwonum();
int main(void) {
 int result;
 result = addtwonum();
 return 0;
}
```
### 3.11.3 左值和右值
1. 左值：可以出现在表达式左边右边
2. 右值：只能出现在右边
## 3.12 常量
1. 常量是固定值，执行期间不会改变，又叫字面量
### 3.12.1 整数常量
221、215u、0xFeel
### 3.12.2 浮点常量
3.142
### 3.12.3 字符常量
'x'、'\t'
### 3.12.4 字符串常量
"hello"
### 3.12.5 定义常量
```c
1.#define
  #define indentifier value
  #define MAX 100;

2.const
  const type variable = value
  const int MAX = 100;
```
## 3.13 存储类
1. 定义C 程序中变量/函数的范围（可见性）和生命周期，说明符放置在修饰类型之前
### 3.13.1 auto
1. 是所有局部变量默认的存储类，只能修饰局部变量
```c
{
  int mount;
  auto int month;
}
```
### 3.13.2 register
1. 定义存储在寄存器而不是RAM中变量，最大尺寸等于寄存器大小，不能应用一元 & 运算符
```c
{
  register int miles;
}
```
### 3.13.3 static
1. 编译器在程序生命周期内保持局部变量存在
### 3.13.4 extern
1. 提供一个全局变量引用，全局变量对所有程序文件可见，当年使用 extern，无法初始化变量，会把变量名指向一个之前定义过存储位置，修饰两个或过个文件共享相同的全局变量或函数时候。
```c
//main.c
#include <stdio.h>
int count ;
extern void write_extern();
 
int main()
{
   count = 5;
   write_extern();
}

//support.c
#include <stdio.h>
extern int count;
 
void write_extern(void)
{
   printf("count is %d\n", count);
}
```
## 3.14 运算符
| 运算符 |                                                |
| ------ | ---------------------------------------------- |
| 算术   | +、-、*、/、%、++、--                          |
| 关系   | ==、!=、>、<、>=、<=                           |
| 逻辑   | &&、!、\|\|                                    |
| 位     | &、^ 、\|                                      |
| 赋值   | =                                              |
| 杂项   | sizeof()、&(变量实际地址)、*(指向一个变量)、?: |

## 3.15 判断
| 符号       |
| ---------- |
| if         |
| if...else  |
| switch     |
| 嵌套switch |
| 三元 ? :   |
## 3.16 循环
### 3.16.1 循环类型
| 符号      |
| --------- |
| while     |
| for       |
| do..while |
| 嵌套      |
### 3.16.2 循环控制
| 符号     | 简介                           |
| -------- | ------------------------------ |
| break    |                                |
| continue |                                |
| goto     | 将控制转移到标记的语句，不建议 |

```c
#include <stdio.h>
int main ()
{
   int a = 10;
   LOOP:do
   {
      if( a == 15)
      {
         a = a + 1;
         goto LOOP;
      }
      printf("a 的值： %d\n", a);
      a++; 
   } while( a < 20 );
   return 0;
}
```
## 3.17 函数
1. 每个 C 语言都有一个函数，主函数 main()
```c
# include<stdio.h>
int max(int num1,int num2);
int main() {
  int result = max(1,6);
}

int max(int num1,int num2){
  if(num1 > num2) {
    return num1;
  } else {
     return num2;
  }
}

```
### 3.17.1 函数参数
1. 传值调用
2. 引用调用（指针）
## 3.18 作用域规则
1. 局部变量
2. 全局变量
3. 形式参数

## 3.19 数组
```c
//声明数组
type arrayName[size];
double balance[10];
//初始化数组
double balance[2] = {100.0,2.0};
double balance[] = {100.0,2.0}
//访问数组
double i = balance[0];
//传递数组给函数
int *param
int param[10]
int param[]
```
## 3.20 枚举
```c
enum DAY {
  //第一个默认为0，后面+1
  MON=1, TUE, WED, THU, FRI, SAT, SUN
}
//1.向定义枚举类型，再定义枚举变量
enum DAY {
  MON=1, TUE, WED, THU, FRI, SAT, SUN
};
enum DAY day;

//2.定义枚举类型的同时定义枚举变量
enum DAY {
  MON=1, TUE, WED, THU, FRI, SAT, SUN
} day;

//3.省略枚举名称，直接定义枚举变量
enum  {
  MON=1, TUE, WED, THU, FRI, SAT, SUN
} day;

//遍历枚举
#include<stdio.h> 
enum 
{
    MON=1, TUE, WED, THU, FRI, SAT, SUN
} day;
int main()
{
    // 遍历枚举元素
    for (day = MON; day <= SUN; day++) {
        printf("枚举元素：%d \n", day);
    }
}
```
## 3.21 指针
1. & 访问内存地址
2. 指针是一个变量，其值为另一个变量的地址，内存位置的直接地址，就像其他变量或常量一样，必须先声明。
```c
//1.声明
type *var-name
int *ip;
//2.使用
int var = 20;
int *ip = NULL; //空指针
ip = &var 
//2.1.在指针变量中存储的地址
printf("%p\n", ip) 
//2.2.使用指针访问值
printf("%d\n", *ip) 
//3.算术运算
//3.1.递增
ptr++ //加入 ptr 指向地址 1000 整型指针 ptr++ 为 1004
//3.2
int var[] = {100,200,300};
int i,*ptr;
//指向数组地址
ptr = var
for(i= 0;i < 3;i++){
   printf("值：%d\n", *ptr );//100 200 300
   ptr++;
}
//3.3.递减一个指针
ptr = &var[2];
for ( i = 3; i > 0; i--)
    {
      printf("%d\n", *ptr );
      /* 移动到下一个位置 */
      ptr--;
   }
 //3.4.指针比较
 ptr = var;
 i = 0;
 while ( ptr <= &var[MAX - 1] )
 {
     printf("Value of var[%d] = %d\n", i, *ptr );
     /* 指向上一个位置 */
     ptr++;
     i++;
 }  
```
## 3.21.1 指针数组
```c
//1.
int *ptr[3];
ptr[i] = &var[i]; /* 赋值为整数的地址 */
printf("Value of var[%d] = %d\n", i, *ptr[i] );
//2.
const char *name[]={"zz","aa"};
printf("Value of names[%d] = %s\n", i, names[i] );
```
### 3.22.2 指向指针的指针
```c
int var = 300;
int *ptr;
int *pptr
ptr = &var;
pptr = &ptr;
printf("%d",*ptr);
printf("%d",**pptr);

```
### 3.22.3 传递指针给函数
```c
void getSeconds(unsigne long *par){
   *par = time(NULL);
}
```
### 3.22.4 函数中返回指针
```c
int * getRandom(){
   static int  r[10];
   int i 
   /* 设置种子 */
   srand( (unsigned)time( NULL ) );
   for ( i = 0; i < 10; ++i)
   {
      r[i] = rand();
      printf("%d\n", r[i] );
   }
   return r;
}
```
## 3.23 函数指针
1. 指向函数的指针变量
```c
// 声明一个指向同样参数、返回值的函数指针类型
typedef int (*fun_ptr)(int ,int)

int max(int x, int y)
{
    return x > y ? x : y;
}
// p 是函数指针 
int (* p)(int, int) = & max; // &可以省略
// 与直接调用函数等价，d = max(max(a, b), c)
d = p(p(a, b), c); 
```
## 3.24 回调函数
1. 回调函数是由别人的函数执行时调用你实现的函数
```c
// 回调函数
void test(int (*getValue)(void))
{
    getValue();
}
int getValue(void)
{
    return 8;
}
test(getValue)
```
## 3.25 字符串
1. 字符串实际使用 null 字符 "\0" 终止的一维字符数组
```c
char greeting[6] = {'H', 'e', 'l', 'l', 'o', '\0'};
char greeting[] = "Hello";
```
| 操作            | 简介                                                         |
| --------------- | ------------------------------------------------------------ |
| strcpy(s1, s2); | 复制字符串 s2 到字符串 s1。                                  |
| strcat(s1, s2); | 连接字符串 s2 到字符串 s1 的末尾。                           |
| strlen(s1);     | 返回字符串 s1 的长度。                                       |
| strcmp(s1, s2); | 如果 s1 和 s2 是相同的，则返回 0；如果 s1<s2 则返回小于 0；如果 s1>s2 则返回大于 0。 |
| strchr(s1, ch); | 返回一个指针，指向字符串 s1 中字符 ch 的第一次出现的位置。   |
| strstr(s1, s2); | 返回一个指针，指向字符串 s1 中字符串 s2 的第一次出现的位置。 |

## 3.26 结构体
1. C 数组允许定义可存储相同类型数据项的变量，结构是 C 编程中另一种用户自定义的可用的数据类型，存储不同类型的数据项。
```c
struct tag { 
    member-list
    member-list 
    member-list  
    ...
} variable-list ;

struct Books
{
   char  title[50];
   char  author[50];
   char  subject[100];
   int   book_id;
} book;
```
2. 一般情况下，tag、member-list、variable-list 这 3 部分至少要出现 2 个
```c
1.
struct 
{
    int a;
} s1;
2.
//此声明声明了拥有3个成员的结构体，分别为整型的a，字符型的b和双精度的c
//结构体的标签被命名为SIMPLE,没有声明变量
struct SIMPLE
{
    int a;
    char b;
    double c;
};
//用SIMPLE标签的结构体，另外声明了变量t1、t2、t3
struct SIMPLE t1, t2[20], *t3;
3.
//也可以用typedef创建新类型
typedef struct
{
    int a;
    char b;
    double c; 
} Simple2;
//现在可以用Simple2作为类型声明新的结构体变量
Simple2 u1, u2[20], *u3;
```
3. 结构体可以包含其他结构体
```c
//其他的结构体
struct COMPLEX
{
    char string[100];
    struct SIMPLE a;
};
 
//此包含了指向自己类型的指针
struct NODE
{
    char string[100];
    struct NODE *next_node;
};
```
4. 如果两个结构体互相包含，则需要对其中一个结构体进行不完整声明
```c
//对结构体B进行不完整声明
struct B;   
//结构体A中包含指向结构体B的指针
struct A
{
    struct B *partner;
};
//结构体B中包含指向结构体A的指针，在A声明完后，B也随之进行声明
struct B
{
    struct A *partner;
};
```
5. 结构体变量的初始化
```c
struct Books
{
   char  title[50];
} book = {"C 语言", "RUNOOB", "编程语言", 123456};
booke.title;
```
6. 访问结构成员
```c
struct Books
{
   char  title[50];
};

struct Book book1;
//赋值
strcpy( Book1.title, "C"); 
```
7. 结构作为函数参数
```c
#include <stdio.h>
struct Book {
   char title[50];
};
void printBook(struct Book book);
int main()
{
   struct Book book1;
   strcpy(book1.title, "C");
   printBook(book1);
   return 0;
}

void printBook(struct Book book){
   printf( "Book title : %s\n", book.title);
}

```
8. 指向结构的指针
```c
//定义指针
struct Books *struct_pointer;
//存储地址
struct_pointer = &Book1;
//使用
struct_pointer->title;

#include <stdio.h>
struct Book {
   char title[50];
};
void printBook(struct Book *book);
int main()
{
   struct Book book1;
   strcpy(book1.title, "C");
   printBook(&book1);
   return 0;
}

void printBook(struct Book *book){
   printf( "Book title : %s\n", book->title);
}
```
## 3.27 位域
1. 把一个字节中的二进位划分为几个不同的区域，并说明每个区域的位数。每个域有一个域名，允许在程序中按域名进行操作。这样就可以把几个不同的对象用一个字节的二进制位域来表示。
2. 例子
1.用 1 位二进位存放一个开关量时，只有 0 和 1 两种状态。
2.读取外部文件格式——可以读取非标准的文件格式。例如：9 位的整数。
```c
//定义
struct 位域结构名 
{
 位域列表
};
//data 为 bs 变量，共占2个字节，
struct bs{
   int a:8; //8位
   int b:2; //2位
   int c:6; //6位
}data;
//1.一个位域存储在同一个字节中，如一个字节所剩空间不够存放另一位域时，则会从下一单元起存放该位域。也可以有意使某位域从下一单元开始。
struct bs{
    unsigned a:4;
    unsigned  :4;   // 空域 
    unsigned b:4;   // 从下一单元开始存放
    unsigned c:4
}
//2.位域不允许跨两个字节，因此位域的长度不能大于一个字节的长度，也就是说不能超过8位二进位。如果最大长度大于计算机的整数字长，一些编译器可能会允许域的内存重叠，另外一些编译器可能会把大于一个域的部分存储在下一个字中。
//3.位域可以是无名位域，这时它只用来作填充或调整位置。无名的位域是不能使用的。
struct bs{
    int a:1;
    int  :2;    // 该 2 位不能使用
    int b:3;
    int c:2;
};
//4.位域使用 与 结构体一样
//位域变量名.位域名
//位域变量名->位域名
```
## 3.28 共用体
1. 特殊的数据类型，允许在相同的内存位置存储不同的数据类。型。
```c
//1.定义
union [union tag]
{
   member definition;
   member definition;
   ...
   member definition;
} [one or more union variables];

union Data
{
   int i;
   float f;
   char str[20]; //占用20个字节
} data;
//2.访问
union Data
{
   int i;
   float f;
   char  str[20];
};
union Data data; 
data.i = 10; 
data.f = 220.5; 
strcpy( data.str, "C"); //c
printf( "data.i : %d\n", data.i); // 1917853763
printf( "data.f : %f\n", data.f);
printf( "data.str : %s\n", data.str);
...
data.i = 10; 
printf( "data.i : %d\n", data.i); // 10

```
## 3.29 typedef
1. 使用它来为类型取一个新的名字
```c
//1.给 unsigned char 取名 BYTE（大写）
typedef unsigned char BYTE;
BYTE  b1, b2;
//2.结构体取名字
typedef struct Books
{
   char  title[50];
   char  author[50];
   char  subject[100];
   int   book_id;
} Book;
//使用
Book book;
```
### 3.29.1 typedef vs #define
1. #define 是 C 指令，用于为各种数据类型定义别名。
2. typedef 仅为类型定义符号名称，#define 不仅可以为类型定义别名，也能为数值定义别名，比如定义 1 为 ONE。
3. typedef 是由编译器执行解释的，#define 语句是由预编译器进行处理的。
## 3.30 输入、输出
| 标准文件 | 文件指针 | 设备     |
| -------- | -------- | -------- |
| 标准输入 | stdin    | 键盘     |
| 标准输出 | stdout   | 屏幕     |
| 标准错误 | stderr   | 您的屏幕 |

1. scanf() 从标准输入（键盘）读取并格式化
2.  printf() 格式化输出到标准输出（屏幕）
### 3.30.1 getchar() & putchar() 
1.  getchar() :函数从屏幕读取下一个可用的字符，并把它返回为一个整数
2. putchar():把字符输出到屏幕上，并返回相同的字符
### 3.30.2 gets() & puts()
1. gets(): stdin 读取一行到 s 所指向的缓冲区，直到一个终止符或 EOF
2. puts():把字符串 s 和一个尾随的换行符写入到 stdout
## 3.31 文件读写
### 3.31.1 打开文件
```c
FILE *fopen( const char * filename, const char * mode );
```
| 模式 | 描述                                                         |
| ---- | ------------------------------------------------------------ |
| r    | 打开一个已有的文本文件，允许读取文件。                       |
| w    | 打开一个文本文件，允许写入文件。如果文件不存在，则会创建一个新文件。在这里，您的程序会从文件的开头写入内容。如果文件存在，则该会被截断为零长度，重新写入。 |
| a    | 打开一个文本文件，以追加模式写入文件。如果文件不存在，则会创建一个新文件。在这里，您的程序会在已有的文件内容中追加内容。 |
| r+   | 打开一个文本文件，允许读写文件。                             |
| w+   | 打开一个文本文件，允许读写文件。如果文件已存在，则文件会被截断为零长度，如果文件不存在，则会创建一个新文件。 |
| a+   | 打开一个文本文件，允许读写文件。如果文件不存在，则会创建一个新文件。读取会从文件的开头开始，写入则只能是追加模式。 |

### 3.31.2 关闭文件
```c
int fclose( FILE *fp );
```
### 3.31.2 写入文件
```c
//字符写入到流中
int fputc( int c, FILE *fp );
//字符串 s 写入到 fp 所指向的输出流中
int fputs( const char *s, FILE *fp );
```
### 3.31.3 读取文件
```c
// fp 所指向的输入文件中读取一个字符
int fgetc( FILE * fp );
//从 fp 所指向的输入流中读取 n - 1 个字符。它会把读取的字符串复制到缓冲区 buf，并在最后追加一个 null 字符来终止字符串。
char *fgets( char *buf, int n, FILE *fp );
```
### 3.31.4 二进制 I/O 函数
```c
//用于存储块的读写 - 通常是数组或结构体。
size_t fread(void *ptr, size_t size_of_elements, 
             size_t number_of_elements, FILE *a_file);
              
size_t fwrite(const void *ptr, size_t size_of_elements, 
             size_t number_of_elements, FILE *a_file);
```
## 3.32 预处理器
1. 不是编译器组成部分，编译过程中有个单独步骤，文本替换工具而已。

| 指令     | 描述                                                    |
| -------- | ------------------------------------------------------- |
| #define  | 宏                                                      |
| #include | 源文件代码                                              |
| #undef   | 取消宏                                                  |
| #ifdef   | 宏已经定义，则返回真                                    |
| #ifndef  | 宏没有定义，则返回真                                    |
| #if      | 给定条件为真，则编译下面代码                            |
| #else    | if 的替代方案                                           |
| #elif    | 前面的 #if 给定条件不为真，当前条件为真，则编译下面代码 |
| #endif   | 结束一个 #if……#else 条件编译块                          |
| #error   | 当遇到标准错误时，输出错误消息                          |
| #pragma  | 使用标准化方法，向编译器发布特殊的命令到编译器中        |

### 3.32.1 预定义宏
| 宏        | 描述                                              |
| --------- | ------------------------------------------------- |
| \__DATE__ | 当前日期，一个以 "MMM DD YYYY" 格式表示的字符常量 |
| \__TIME__ | 当前时间，一个以 "HH:MM:SS" 格式表示的字符常量    |
| \__FILE__ | 包含当前文件名，一个字符串常量                    |
| \__LINE__ | 包含当前行号，一个十进制常量                      |
| \__STDC__ | 当编译器以 ANSI 标准编译时，则定义为 1。          |
### 3.32.2 预处理器运算符
```c
//1.宏延续运算符（\） 换行
#define  message_for(a, b)  \
    printf(#a " and " #b ": We love you!\n")

//2.字符串常量化运算符（#） 参数转换为字符串常量
#define  message_for(a, b)  \
    printf(#a " and " #b ": We love you!\n")
int main(void)
{
   message_for(Carole, Debra);
   return 0;
}

//3.标记粘贴运算符（##） 合并两个参数
#define tokenpaster(n) \
     printf ("token" #n " = %d", token##n)
int main(void)
{
   int token34 = 40;
   tokenpaster(34);//token34 = 40
   return 0;
}

//4.defined() 运算符 常量表达式中 确定一个标识符是否已经使用 #define 定义过
#include <stdio.h>
#if !defined (MESSAGE)
   #define MESSAGE "You wish!"
#endif

int main(void)
{
   printf("Here is the message: %s\n", MESSAGE);  
   return 0;
}

//5.参数化的宏
#define MAX(x,y) ((x) > (y) ? (x) : (y))

```
## 头文件
```c
//1.
#include <file>
#include "file"
```
## 3.33 强制类型转换
```c
//1.类型转换
mean = (double)sum;
//2.整数提升
//把小于 int 或 unsigned int 的整数类型转换为 int 或 unsigned int
```
## 3.34 错误处理
```c
errno、perror()、strerror()
perror():显示传给它的字符串，后跟一个冒号、一个空格和当前 errno 值的文本表示形式
strerror()：返回一个指针，指针指向当前 errno 值的文本表示形式。

程序退出状态
 exit(EXIT_FAILURE); -1
 exit(EXIT_SUCCESS);  0
```
## 3.35 递归
1. 函数自己调用自己
## 3.36 可变参数
```c
//1.引入
#include <stdarg.h>

double average(int num,...){
   //2.定义va_list 类型变量
   va_list valist;
   //3.为 num 个参数初始化 valist 
   va_start(valist, num);
   //4.访问所有赋给 valist 的参数 
   for (i = 0; i < num; i++)
   {
       sum += va_arg(valist, int);
    }
   //5.清理为 valist 保留的内存 
   va_end(valist);
   return sum/num;
}
```
## 3.37 内存管理
```c
//内存中动态地分配 num 个长度为 size 的连续空间
void *calloc(int num, int size);
//释放动态分配的内存空间
void free(void *address); 
//堆区分配一块指定大小的内存空间，用来存放数据
void *malloc(int num);
//重新分配内存，把内存扩展到 newsize
void *realloc(void *address, int newsize); 	

//动态分配内存
char name[100];

//重新调整内存的大小和释放内存
//在不需要内存时，都应该调用函数 free() 来释放内存
```
## 3.38 命令行参数
```c
int main( int argc, char *argv[] )  
```