## 1 标识符

- 第一个字符必须是字母表中字母或下划线 **_** 。
- 标识符的其他的部分由字母、数字和下划线组成。
- 标识符对大小写敏感。

## 2 python保留字

保留字即关键字，不能用作任何标识符名称。Python 的标准库提供了一个 keyword 模块，可以输出当前版本的所有关键字：

```python
import keyword

res = keyword.kwlist
print(res)

['False', 'None', 'True', '__peg_parser__', 'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield']
```

## 3 注释

```python
# 1.注释
print ("Hello, Python!") # 注释

'''
2.注释
'''

"""
3.注释
"""
```

## 4 基本数据类型

### 4.1 Number 数字

* int 
* float
* bool
* complex 复数

```python
a = 1
b = 1.1
c = True
print(type(a))
print(type(b))
print(type(c))

'''
<class 'int'>
<class 'float'>
<class 'bool'>
'''
```

### 4.2 String 字符串

使用 '' 或 ''''

```python
a = '单引号'
b = "双引号"
print(type(a))
print(type(b))

'''
<class 'str'>
<class 'str'>
'''

'''
索引
0  1  2  3  4  5
-6 -5 -4 -3 -2 -1
P  y  t  h  o  n
'''
str = 'Python'
print(str)          # 输出字符串  Python
print(str[0:-1])    # 输出第一个到倒数第二个的所有字符 Pytho
print(str[0])       # 输出字符串第一个字符 P
print(str[2:5])     # 输出从第三个开始到第五个的字符 tho
print(str[2:])      # 输出从第三个开始的后的所有字符 thon
print(str * 2)      # 输出字符串两次，也可以写成 print (2 * str) PythonPython
print(str + "Java") # 连接字符串 PythonJava

# 原始字符串
print(r'Java\nC') # Java\nC

# 格式化
print ("书籍：%s 价格：%d " % ('Python', 29))

# Python 3.6 
name = 'Python'
print(f'Hello {name}')
```

### 4.3 List 列表

```python
l1 = ['A', 1, 1.2, True]
l2 = ['B', 33]
print(l1)            # 输出完整列表 ['A', 1, 1.2, True]
print(l1[0])         # 输出列表第一个元素 A
print(l1[1:3])       # 从第二个开始输出到第三个元素 切片 [1, 1.2]
print(l1[2:])        # 输出从第三个元素开始的所有元素 [1.2, True]
print(l2 * 2)        # 输出两次列表 ['B', 33, 'B', 33]
print(l1 + l2)       # 连接列表 ['A', 1, 1.2, True, 'B', 33]

l1[2:4] = []         # 将对应的元素值设置为 []
print(l1)            # ['A', 1]

l3 = ['A', 'B', 'C', 'D', 'E']
print(l3[::2])       # 设置步长 ['A', 'C', 'E']
print(l3[::-2])      # 负数后往前 ['E', 'C', 'A']
print(l3[1:4:2])     # ['B', 'D']

l1 = ['A', 'B', 'C', 'D']
len(l1) # 列表元素个数
max(l1) # 列表元素最大值
min(l1) # 列表元素最小值
t1 = ('1', '2')
l2 = list(t1) # 将元组或字符串转换为列表
l3 = list('Hello')
l1.append('D') # 列表末尾添加新的对象
l1.count('D') # 统计某个元素在列表中出现的次数
l3=list(range(5))
l1.extend(l3) # 列表末尾一次性追加另一个序列中的多个值（用新列表扩展原来的列表）
l1.index('D') # 从列表中找出某个值第一个匹配项的索引位置
l1.insert(0, 'B++') # 指定对象插入列表的指定位置
l1.pop() # 移除列表中的一个元素（默认最后一个元素）
l1.pop(-2) # index 索引值
l1.remove('B++') # 移除列表中某个值的第一个匹配项
l1.reverse() # 反向列表中元素
l1.sort() # 原列表进行排序
l1.clear() # 清空列表
l3 = l1.copy() # 复制列表


l7 = ['A', 'B', 'C', 'D', 'E']
for v in l7:         # 遍历
    print(v, end=' ')
   
for i, v in enumerate(l7):  # enumerate() 获取 index、value
    print("下标=%s 值=%s" % (i, v))
```



### 4.4 Tuple 元组

Python 的元组与列表类似，不同之处在于元组的元素不能修改。

元组使用小括号 ()，列表使用方括号 [],。

操作和 list 差不多

```python
t1 = ('A', 'B', 'C', 'D', 'E')
for i, v in enumerate(t1):
    print("下标=%s 值=%s" % (i, v))
    
t2 = (1, 2)
t3 = ("A", "B")
print(t2 + t3)   # (1, 2, 'A', 'B')  
```

### 4.5 Set 集合

集合（set）是一个无序的不重复元素序列。

括号  { }  或者 set() 函数创建集合。

```python
a = set('abracadabra')
print(a) # {'a', 'r', 'b', 'c', 'd'}

b = set(("A", "B", "C"))
b.add('E') # 添加
b.update({1,3}) # 添加多个
b.remove('A') # 移除
len(b) # 计算集合元素个数
b.clear() # 清空

```

### 4.6 Dictionary 字典

字典是另一种可变容器模型，且可存储任意类型对象。类似与 Java 中的 Map。

不允许同一个键出现两次。创建时如果同一个键被赋值两次，会覆盖。

```python
d1 = {'name': 'Java', 'price': 76}
print(d1['name'], d1['price'])

d1['name'] = 'Python' # 修改
print(d1)

d1['des'] = '不会写' # 增加
print(d1)

del d1['des'] # 删除
print(d1)

d2 = {'name': 'Java', 'price': 76}
for k, v in d2.items(): # 遍历
    print("key=%s value=%s" % (k, v))
    
"""
key=name value=Java
key=price value=76
"""    
```

## 5 条件语句

```python
# if...elif..esle   if...else
x = 1
if x == 1:
   print('A')
elif x == 2
   print('B')
else 
   print('C')
```

## 6 循环

```python
# while
sum = 0
counter = 1
while counter <= n:
    sum = sum + counter
    counter += 1
print("1 到 %d 之和为: %d" % (n,sum))

# while...else  在 while … else 在条件语句为 false 时执行 else 的语句块。
count = 0
while count < 5:
   print (count, " 小于 5")
   count = count + 1
else:
   print (count, " 大于或等于 5")

# for
languages = ["C", "C++", "Python"] 
for x in languages
    print(x)
```

## 6 pass 语句

pass 不做任何事情，一般用做占位语句。

```python
x = 1
if x == 1:
   pass

```

## 7 迭代器和生成器

迭代器对象从集合的第一个元素开始访问，直到所有的元素被访问完结束。迭代器只能往前不会后退。

* iter()
* next()

```python
list=[1,2,3,4]
it = iter(list)    # 创建迭代器对象
for x in it:
    print (x, end=" ")
    
# 循环  
import sys         # 引入 sys 模块
list=[1,2,3,4]
it = iter(list)    # 创建迭代器对象
while True:
    try:
        print (next(it))
    except StopIteration: # 异常用于标识迭代的完成
        sys.exit()    
```

### 7.1 生成器

使用了 yield 的函数被称为生成器（generator），生成器是一个返回迭代器的函数，只能用于迭代操作。

```python
import sys
def fibonacci(n,w=0): # 生成器函数 - 斐波那契
    a, b, counter = 0, 1, 0
    while True:
        if (counter > n): 
            return
        yield a
        a, b = b, a + b
        print('%d,%d' % (a,b))
        counter += 1
        
f = fibonacci(10,0) # f 是一个迭代器，由生成器返回生成

while True:
    try:
        print (next(f), end=" ")
    except :
        sys.exit()


```

## 8 函数

```python
def max(a,b)
   if a > b:
        return a
   else:
        return b

# 默认参数
def printInfo(name,age = 34)
    print(name,age)
    return
printInfo("张三")

# 不定长参数
def printInfo( arg1, *vartuple ):
   print("输出: ")
   print(arg1)
   print(vartuple) # 参数会以元组(tuple)的形式导
printinfo( 70, 60, 50 )

# **参数会以字典的形式导入
def printInfo( arg1, **vartuple ): 
    
# 匿名函数  
sum = lambda arg1, arg2: arg1 + arg2
print("相加后的值为 : ", sum( 10, 20 ))
```

## 9  import 语句

```python
# support.py
def print_func(par):
    print ("Hello : ", par)
    return

# main.py
# 导入模块
import support
support.print_func("Runoob")

# from … import 语句
# Python 的 from 语句让你从模块中导入一个指定的部分到当前命名空间中
from fibo import fib, fib2

# from … import *， 把一个模块的所有内容全都导入到当前的命名空间

```

## 10 输入与输出

* print()：打印
* str()： 函数返回一个用户易读的表达形式
* repr()：产生一个解释器易读的表达形式
* str.format() ：
  * print('{}'.format('Python'))
  * print('{name}'.format(name = 'Python'))
  * print('{0}，{1}'.format('Python','Java'))

## 11 File

```python
#  open() 方法用于打开一个文件，并返回文件对象，在对文件进行处理过程都需要使用到这个函数，如果该文件无法被打开，会抛出 OSError。记得调用 close() 方法
open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None)
```

- file: 必需，文件路径（相对或者绝对路径）。
- mode: 可选，文件打开模式
- buffering: 设置缓冲
- encoding: 一般使用utf8
- errors: 报错级别
- newline: 区分换行符
- closefd: 传入的file参数类型
- opener: 设置自定义开启器，开启器的返回值必须是一个打开的文件描述符。

## 12 错误和异常

Python 有两种错误很容易辨认：语法错误和异常。

```python
# 异常处理
# try/except

while True:
    try:
        x = int(input("请输入一个数字: "))
        break
    except ValueError:
        print("您输入的不是数字，请再次尝试输入！")
        
# try/except...else  
try:
   ... # 执行代码
except ...: # 发生异常时执行的代码
   ...
else: # 没有异常时执行的代码
   ...
finally: # 都会执行
    
# raise 抛出异常
x = 10
if x > 5:
    raise Exception('x 不能大于 5。x 的值为: {}'.format(x))
```

## 13 面向对象

```python
class MyClass:
    i = 12
    name = ""
    price = 0
    __age = 0 # 私有方法
    def f(self):
        return 'Hello World'
    # def __init__(self): # 默认构造方法
    def __init__(self,name,price): # 构造方法
        self.name = name
        self.price = price
        
# x = MyClass()
x = MyClass('张三',34)

# 继承
class People:
    name = ''
    age = 0
    def __init__(self,name,age)
        self.name = name
        self.age = age
    def speak(self):
        print('Hello')
        
class Student(Person): # 继承  class Student(Person,Speaker) # 多继承
    def speak(self):
        print('覆写父类的方法')
```

简单例子

```python
class Person:
    # 1.公有变量
    name = ''
    age = 0
    # 2.私有变量
    __weight = 0.0

    # 3.构造函数
    def __init__(self, name, age, weight):
        self.name = name
        self.age = age
        self.__weight = weight

    # 4.自定义方法
    def learn(self, course):
        print("%s 学习  %s" % (self.name, course))

    # 5.私有方法
    def __sleep(self):
        print("%s sleep" % self.name)


class Speaker:
    topic = ''
    time = 0

    def __init__(self, topic):
        self.topic = topic

    # 6.重载，可以使用默认 say() say(time = 0) say(time = '40',info = 'Java 学习')
    def say(self, time=0, info=''):
        print("%s 演讲时间 %d 分" % (info, time))


# 7.继承
class Student(Person):
    def __init__(self, name, age, weight):
        super().__init__(name, age, weight)

    # 8.方法重写
    def learn(self, course):
        # 9.调用父类方法
        super(course)
        print("%s 已经不学习  %s" % (self.name, course))


# 9.多继承:Person,Speaker
class Doctor(Person, Speaker):
    def __init__(self, name, age, weight, topic):
        Person.__init__(self, name, age, weight)
        Speaker.__init__(self, topic)


# 静态方法: 用 @staticmethod 装饰的不带 self 参数的方法叫做静态方法，类的静态方法可以没有参数，可以直接使用类名调用。
# 普通方法: 默认有个self参数，且只能被对象调用。
# 类方法: 默认有个 cls 参数，可以被类和对象调用，需要加上 @classmethod 装饰器。
class Teacher:
    @staticmethod
    def a():
        print('静态方法')

    @classmethod
    def b(cls):
        print('类方法')

    def c(self):
        print('类方法')


if __name__ == '__main__':
    speaker = Speaker("Java 编程")
    speaker.say(40, "如何学习 Java")
    speaker.say(info="如何不学习 Java")

    student = Student()
    student.learn("Python")
    print(speaker.topic)

    doctor = Doctor("张三", 40, 25, "Python 学习")
```



## 14 命名空间和作用域

命名空间(Namespace)是从名称到对象的映射，大部分的命名空间都是通过 Python 字典来实现的。作用，避免名字冲突的一种方法

变量查找顺序：当前域 -> 外部域(如果有) -> 全局域 -> 内置域。

```python
# 当内部作用域想修改外部作用域的变量时，就要用到global和nonlocal关键字了。

# 修改全局变量 num
num = 1
def fun1():
    global num  # 需要使用 global 关键字声明
    print(num) 
    num = 123
    print(num)
fun1()
print(num)

# 要修改嵌套作用域（enclosing 作用域，外层非全局作用域）中的变量则需要 nonlocal 关键字了
def outer():
    num = 10
    def inner():
        nonlocal num   # nonlocal关键字声明
        num = 100
        print(num)
    inner()
    print(num)
outer()
```

