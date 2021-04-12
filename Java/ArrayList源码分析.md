[TOC]
## 1 简介

ArrayList 是 Java 集合框架中常用的数据结构，底层采用数组队列，相当于动态数组。与 Java 中的数组相比，它的容量能动态增长。ArrayList  继承于 AbstractList，实现了 List，RandomAccess，Cloneable，java.io.Serializable 接口。

```java
public class ArrayList<E> extends AbstractList<E>
        implements List<E>, RandomAccess, Cloneable, java.io.Serializable
    
//1.继承 AbstractList，实现 List,它是一个数组队列，提供相关的添加、删除、修改、遍历等功能。
//2.实现 RandmoAccess 接口，提供随机访问功能，在 ArrayList 中，通过元素的序号快速获取元素对象，这就是快速随机访问。      
//3.实现 Cloneable 接口，即覆盖了函数 clone()，能被克隆。   
//4.实现 java.io.Serializable 接口，支持序列化，能通过序列化去传输。     
```

## 2 源码解析

下面为 ArrayList 源码解析，实现并不复杂。

```java
package java.util;

import java.util.function.Consumer;
import java.util.function.Predicate;
import java.util.function.UnaryOperator;

//继承 AbstractList，实现 RandmoAccess、Cloneable、java.io.Serializable 接口
public class ArrayList<E> extends AbstractList<E>
        implements List<E>, RandomAccess, Cloneable, java.io.Serializable
{
    private static final long serialVersionUID = 8683452581122892189L;

    
    //默认初始容量大小
    private static final int DEFAULT_CAPACITY = 10;
    
    //空数组（用于空实例）     
    private static final Object[] EMPTY_ELEMENTDATA = {};

     //空数组（用于空实例）
     //和EMPTY_ELEMENTDATA 数组区分，以知道在添加第一个元素时容量需要增加多少
    private static final Object[] DEFAULTCAPACITY_EMPTY_ELEMENTDATA = {};
    
     //保存 ArrayList 数据的数组
    transient Object[] elementData;
    
    //ArrayList 实际元素个数
    private int size;   
    //带初始容量参数的构造函数（创建ArrayList对象时指定集合的初始大小）
    public ArrayList(int initialCapacity) {        
        if (initialCapacity > 0) {            
            this.elementData = new Object[initialCapacity];
        } else if (initialCapacity == 0) {           
            this.elementData = EMPTY_ELEMENTDATA;
        } else {            
            throw new IllegalArgumentException("Illegal Capacity: "+
                                               initialCapacity);
        }
    }

   
     //默认无参构造函数
     //DEFAULTCAPACITY_EMPTY_ELEMENTDATA 为 0.初始化为10，初始化时候为空数组,当添加第一个元素的时候数组容量才扩容为 10    
    public ArrayList() {
        this.elementData = DEFAULTCAPACITY_EMPTY_ELEMENTDATA;
    }

    //构造包含指定集合的元素的列表，按照它们由集合的迭代器返回的顺序。
    public ArrayList(Collection<? extends E> c) {
        //将指定集合转换为数组
        elementData = c.toArray();
        if ((size = elementData.length) != 0) {
            // 如果elementData不是Object类型数据（c.toArray可能返回的不是Object类型的数组所以加上下面的语句用于判断）
            if (elementData.getClass() != Object[].class)
                //将原来不是Object类型的elementData数组的内容，赋值给新的Object类型的elementData数组
                elementData = Arrays.copyOf(elementData, size, Object[].class);
        } else {         
            this.elementData = EMPTY_ELEMENTDATA;
        }
    }


     //将当前容量值设为实际元素个数，减少不必要占用内存空间
    public void trimToSize() {
        modCount++;
        if (size < elementData.length) {
            elementData = (size == 0)
              ? EMPTY_ELEMENTDATA
              : Arrays.copyOf(elementData, size);
        }
    }
    //确定ArrarList的容量
    public void ensureCapacity(int minCapacity) {
        //如果是true，minExpand的值为0，如果是false,minExpand的值为10
        int minExpand = (elementData != DEFAULTCAPACITY_EMPTY_ELEMENTDATA)           
            ? 0           
            : DEFAULT_CAPACITY;
        //如果最小容量大于已有的最大容量
        if (minCapacity > minExpand) {
            ensureExplicitCapacity(minCapacity);
        }
    }
    
   //得到最小扩容量
    private void ensureCapacityInternal(int minCapacity) {
        if (elementData == DEFAULTCAPACITY_EMPTY_ELEMENTDATA) {
             //取默认的容量和传入参数之间的最大值
            minCapacity = Math.max(DEFAULT_CAPACITY, minCapacity);
        }
        ensureExplicitCapacity(minCapacity);
    }
    
    //判断是否需要扩容
    private void ensureExplicitCapacity(int minCapacity) {
        modCount++;
        if (minCapacity - elementData.length > 0)
            //调用grow方法进行扩容
            grow(minCapacity);
    }
  
    // 要分配的最大数组大小
    private static final int MAX_ARRAY_SIZE = Integer.MAX_VALUE - 8;

    // 扩容的核心方法。
    private void grow(int minCapacity) {
        //oldCapacity为旧容量，newCapacity为新容量
        int oldCapacity = elementData.length;
        //将oldCapacity 右移一位，其效果相当于oldCapacity /2，结果变为原来 1.5倍       
        int newCapacity = oldCapacity + (oldCapacity >> 1);
        //然后检查新容量是否大于最小需要容量，若还是小于最小需要容量，那么就把最小需要容量当作数组的新容量，
        if (newCapacity - minCapacity < 0)
            newCapacity = minCapacity;
        //检查新容量是否超出最大容量，
        //超出,调用hugeCapacity()来比较minCapacity和 MAX_ARRAY_SIZE，
        //如果minCapacity大于MAX_ARRAY_SIZE，则新容量则为Interger.MAX_VALUE，否则，新容量大小则为 MAX_ARRAY_SIZE。
        if (newCapacity - MAX_ARRAY_SIZE > 0)
            newCapacity = hugeCapacity(minCapacity);
        //进行数组扩容    
        elementData = Arrays.copyOf(elementData, newCapacity);
    }
    //比较minCapacity和 MAX_ARRAY_SIZE
    private static int hugeCapacity(int minCapacity) {
        if (minCapacity < 0) // overflow
            throw new OutOfMemoryError();
        return (minCapacity > MAX_ARRAY_SIZE) ?
            Integer.MAX_VALUE :
            MAX_ARRAY_SIZE;
    }

    //返回元素个数。
    public int size() {
        return size;
    }

    //判断列表是否为空 
    public boolean isEmpty() {       
        return size == 0;
    }

    //判断列表是否包含指定的元素
    public boolean contains(Object o) {
        return indexOf(o) >= 0;
    }

    //获取列表中指定元素的首次出现的索引，如果此列表不包含此元素，则为-1
    public int indexOf(Object o) {
        if (o == null) {
            for (int i = 0; i < size; i++)
                if (elementData[i]==null)
                    return i;
        } else {
            for (int i = 0; i < size; i++)
                if (o.equals(elementData[i]))
                    return i;
        }
        return -1;
    }

    //获取列表中指定元素的最后一次出现的索引，如果此列表不包含元素，则返回-1。.
    public int lastIndexOf(Object o) {
        if (o == null) {
            for (int i = size-1; i >= 0; i--)
                if (elementData[i]==null)
                    return i;
        } else {
            for (int i = size-1; i >= 0; i--)
                if (o.equals(elementData[i]))
                    return i;
        }
        return -1;
    }

    //浅拷贝。 （元素本身不被复制。）
    public Object clone() {
        try {
            ArrayList<?> v = (ArrayList<?>) super.clone();
            v.elementData = Arrays.copyOf(elementData, size);
            v.modCount = 0;
            return v;
        } catch (CloneNotSupportedException e) {
            throw new InternalError(e);
        }
    }

    //返回ArrayList的Object数组
    public Object[] toArray() {
        return Arrays.copyOf(elementData, size);
    }

    //返回ArrayList的模板数组，即可以将T设为任意的数据类型
    @SuppressWarnings("unchecked")
    public <T> T[] toArray(T[] a) {
        if (a.length < size)
            //新建一个运行时类型的数组，但是ArrayList数组的内容
            return (T[]) Arrays.copyOf(elementData, size, a.getClass());
            //调用System.arraycopy()方法实现数组之间的复制
        System.arraycopy(elementData, 0, a, 0, size);
        if (a.length > size)
            a[size] = null;
        return a;
    }

    // Positional Access Operations
    @SuppressWarnings("unchecked")
    E elementData(int index) {
        return (E) elementData[index];
    }

    //返回此列表中指定位置的元素。
    public E get(int index) {
        rangeCheck(index);

        return elementData(index);
    }


    //用指定的元素替换此列表中指定位置的元素。
    public E set(int index, E element) {
        //对index进行界限检查
        rangeCheck(index);
        E oldValue = elementData(index);
        elementData[index] = element;
        //返回原来在这个位置的元素
        return oldValue;
    }


    //将元素追加到列表的末尾
    public boolean add(E e) {
        ensureCapacityInternal(size + 1);        
        elementData[size++] = e;
        return true;
    }

    //指定位置插入元素。  
    public void add(int index, E element) {
        rangeCheckForAdd(index);
        ensureCapacityInternal(size + 1); 
        System.arraycopy(elementData, index, elementData, index + 1,
                         size - index);
        elementData[index] = element;
        size++;
    }

  
    //删除该列表中指定位置的元素
    public E remove(int index) {
        rangeCheck(index);
        modCount++;
        E oldValue = elementData(index);
        int numMoved = size - index - 1;
        if (numMoved > 0)
            System.arraycopy(elementData, index+1, elementData, index,
                             numMoved);
        elementData[--size] = null; // -1
        //从列表中删除的元素
        return oldValue;
    }


    //从列表中删除指定元素的第一个出现
    public boolean remove(Object o) {
        if (o == null) {
            for (int index = 0; index < size; index++)
                if (elementData[index] == null) {
                    fastRemove(index);
                    return true;
                }
        } else {
            for (int index = 0; index < size; index++)
                if (o.equals(elementData[index])) {
                    fastRemove(index);
                    return true;
                }
        }
        return false;
    }

    //快速删除给定索引的元素
    private void fastRemove(int index) {
        modCount++;
        int numMoved = size - index - 1;
        if (numMoved > 0)
            System.arraycopy(elementData, index+1, elementData, index,
                             numMoved);
        elementData[--size] = null; 
    }

    //删除所有元素。
    public void clear() {
        modCount++;
        // 把数组中所有的元素的值设为null
        for (int i = 0; i < size; i++)
            elementData[i] = null;
        size = 0;
    }

     //按指定集合的Iterator返回的顺序将指定集合中的所有元素追加到此列表的末尾。
    public boolean addAll(Collection<? extends E> c) {
        Object[] a = c.toArray();
        int numNew = a.length;
        ensureCapacityInternal(size + numNew);  // Increments modCount
        System.arraycopy(a, 0, elementData, size, numNew);
        size += numNew;
        return numNew != 0;
    }

    //从指定的位置开始，将指定集合中的所有元素插入到此列表中
    public boolean addAll(int index, Collection<? extends E> c) {
        rangeCheckForAdd(index);
        Object[] a = c.toArray();
        int numNew = a.length;
        ensureCapacityInternal(size + numNew); 
        int numMoved = size - index;
        if (numMoved > 0)
            System.arraycopy(elementData, index, elementData, index + numNew,
                             numMoved);

        System.arraycopy(a, 0, elementData, index, numNew);
        size += numNew;
        return numNew != 0;
    }

    //删除 fromIndex 到 toIndex 之间的所有元素
    protected void removeRange(int fromIndex, int toIndex) {
        modCount++;
        int numMoved = size - toIndex;
        System.arraycopy(elementData, toIndex, elementData, fromIndex,
                         numMoved);

        int newSize = size - (toIndex-fromIndex);
        for (int i = newSize; i < size; i++) {
            elementData[i] = null;
        }
        size = newSize;
    }

    //检查给定的索引是否在范围内
    private void rangeCheck(int index) {
        if (index >= size)
            throw new IndexOutOfBoundsException(outOfBoundsMsg(index));
    }

    private void rangeCheckForAdd(int index) {
        if (index > size || index < 0)
            throw new IndexOutOfBoundsException(outOfBoundsMsg(index));
    }

    private String outOfBoundsMsg(int index) {
        return "Index: "+index+", Size: "+size;
    }

    //从列表中删除指定集合中包含的所有元素
    public boolean removeAll(Collection<?> c) {
        Objects.requireNonNull(c);
        //如果此列表被修改则返回true
        return batchRemove(c, false);
    }

    //仅保留此列表中包含在指定集合中的元素
    public boolean retainAll(Collection<?> c) {
        Objects.requireNonNull(c);
        return batchRemove(c, true);
    }

    //从列表中的指定索引开始，返回列表中的元素的列表迭代器
    //指定的索引表示初始调用将返回的第一个元素为next,初始调用previous将返回指定索引减1的元素。
    //返回的列表迭代器是fail-fast
    public ListIterator<E> listIterator(int index) {
        if (index < 0 || index > size)
            throw new IndexOutOfBoundsException("Index: "+index);
        return new ListItr(index);
    }

   
    //返回列表中的列表迭代器（按适当的顺序）
    //返回的列表迭代器是fail-fast 
    public ListIterator<E> listIterator() {
        return new ListItr(0);
    }

    //以正确的顺序返回该列表中的元素的迭代器
    //返回的迭代器是fail-fast 
    public Iterator<E> iterator() {
        return new Itr();
    }
}
```

## 3 扩容机制

从上面的代码中，我们可以很容易发现，当  new ArrayList()，会默认赋值一个空数组，往里面数组里面添加第一个元素，才开始分配容量，数组默认容量为 10。

```java
//添加元素到列表末尾
public boolean add(E e) {
      ensureCapacityInternal(size + 1); 
      //实际就是为下标为 size + 1 数组元素赋值
      elementData[size++] = e;
      return true;
}

//得到最小扩容量
private void ensureCapacityInternal(int minCapacity) {
     //如果使用是无参构造创建
      if (elementData == DEFAULTCAPACITY_EMPTY_ELEMENTDATA) {
          //判断默认容量和传入参数的较大值 DEFAULT_CAPACITY = 10
          //第一个元素 add 进来，默认容量为 minCapacity = 10
          minCapacity = Math.max(DEFAULT_CAPACITY, minCapacity);
      }
      //判断是否需要扩容
      ensureExplicitCapacity(minCapacity);
}

//判断是否需要扩容
private void ensureExplicitCapacity(int minCapacity) {
      modCount++; //修改次数
      if (minCapacity - elementData.length > 0)
          //调用 grow() 进行扩容
          grow(minCapacity);
}


//扩容的核心方法
private void grow(int minCapacity) { 
       //oldCapacity 为旧容量
       int oldCapacity = elementData.length;
       //newCapacity 为新容量 ，oldCapacity >> 1（相当于除2），新容量为原来的 1.5 倍 
       int newCapacity = oldCapacity + (oldCapacity >> 1);
       if (newCapacity - minCapacity < 0)
           newCapacity = minCapacity;
       //MAX_ARRAY_SIZE = Integer.MAX_VALUE - 8
       //如果 newCapacity 比 Integer.MAX_VALUE - 8 还大，
       if (newCapacity - MAX_ARRAY_SIZE > 0) 
           //设置最大容量 
           newCapacity = hugeCapacity(minCapacity);
       //将数据复制到大小为 newCapacity 的新数组中，并将新数组赋值给 elementData
       elementData = Arrays.copyOf(elementData, newCapacity);
}

private static int hugeCapacity(int minCapacity) {
       if (minCapacity < 0) 
           throw new OutOfMemoryError();
       //返回 Integer.MAX_VALUE（2147483647） 或 Integer.MAX_VALUE - 8
       //一般不会有这么大的数组
       return (minCapacity > MAX_ARRAY_SIZE) ? Integer.MAX_VALUE : MAX_ARRAY_SIZE;
}
```

归纳如下：

* new ArrayList 默认赋值一个空数组，size = 0。
* 接着 add 进第 1 个元素，会把实际元素个数 size +1 传入  ensureCapacityInternal() 方法，判断是否需要扩容。
* ensureCapacityInternal() 判断当前是否是使用默认构造的函数，这时候 minCapacity  = MAX(10,1) = 10。
* 紧接着调用 ensureExplicitCapacity(minCapacity )，判断是否需要扩容，此时 elementData.length = 0，显然，minCapacity - elementData.length > 0 成立，数组第一次扩容。
* ensureCapacityInternal() 中判断 minCapacity - elementData.length > 0（10 - 0 > 0），成立，调用 grow() 方法扩容。
* **grow** 为扩容核心方法，旧容量 oldCapacity ，新容量 newCapacity = oldCapacity + (oldCapacity >> 1)，所以 ArrayList 每次扩容之后容量都会变为原来的 1.5 倍左右。
  * 当 add 第 1 个元素时，oldCapacity = 0，newCapacity - minCapacity < 0 （0 - 10  <  0 ）,newCapacity = 10，elementData = **Arrays.copyOf**(elementData, newCapacity) 将原数组扩容成 10 。
  * 当 add 第 11 个元素时，oldCapacity = 11，newCapacity  = 15，第一个判断和第二个判断都不成立，将原数组扩容成 10。
  * 以此类推······

## 4 System.arraycopy() Arrays.copyOf() 方法

在 ArrayList 方法中大量调用这两个方法，那么他们有什么区别，接下来我们来分析一下。

### 4.1 System.arraycopy()

```java
/*
 *复制源数组 src 到目标数组 dest
 *复制从 src 的 srcPos 位置开始，复制个数是 length，复制到 dest 的索引从 destPos 位置开始
 */
public static native void arraycopy(Object src,  int  srcPos,
                                       Object dest, int destPos,
                                        int length);
```

### 4.2 Arrays.copyOf()

```java
/**
 *
 *复制数组，由U类型复制为T类型，最终调用 System.arraycopy()
 *@original  要复制的数组
 *@newLength 要返回的副本的长度
 *@newType   要返回的副本的类型
 *
 */
public static <T,U> T[] copyOf(U[] original, int newLength, Class<? extends T[]> newType) {
        T[] copy = ((Object)newType == (Object)Object[].class)
            ? (T[]) new Object[newLength]
            : (T[]) Array.newInstance(newType.getComponentType(), newLength);
        System.arraycopy(original, 0, copy, 0,
                         Math.min(original.length, newLength));
        return copy;
    }
public static <T> T[] copyOf(T[] original, int newLength) {
    return (T[]) copyOf(original, newLength, original.getClass());
}
```

Arrays.copyOf() 本质最终调用 System.arraycopy()，System.arraycopy()，需要我们传递目标数组，Arrays.copyOf() 则是内部使用反射自己创建好了。

## 5 遍历

### 5.1 迭代器遍历

```java
final ArrayList<String> list = new ArrayList<>();
list.add("第一行代码");
list.add("第二行代码");
list.add("第三行代码");
final Iterator<String> iterator = list.iterator();
while (iterator.hasNext()) {
    System.out.println(iterator.next());
}
```

### 5.2 随机访问，通过索引值遍历

```java
for (int i = 0; i < list.size(); i++) {
     System.out.println(list.get(0));
}
```

### 5.3 for 循环遍历

```java
for (String s : list) {
    System.out.println(list.get(v));
}
```

注：随机访问，通过索引号访问效率最高，使用使用迭代器效率最低。

## 6 参考

[Java 集合系列03之 ArrayList详细介绍(源码解析)和使用示例](https://www.cnblogs.com/skywang12345/p/3308556.html)

[ArrayList详解，看这篇就够了](https://blog.csdn.net/sihai12345/article/details/79382649)