## 1 简介

LinkedList 的底层数据结构是**双向链表**。可以当作链表、栈、队列、双端队列来使用。有以下特点：

* 在插入或删除数据时，性能好；
* 允许有 null 值；
* 查询效率不高；
* 线程不安全；

```java
public class LinkedList<E>
    extends AbstractSequentialList<E>
    implements List<E>, Deque<E>, Cloneable, java.io.Serializable
{}
```

## 2 源码

LinkedList 数据结构：

```java
private static class Node<E> {
     E item; //结点值
     Node<E> next; //后驱节点
     Node<E> prev; //前驱节点

     Node(Node<E> prev, E element, Node<E> next) {
         this.item = element;
         this.next = next;
         this.prev = prev;
     }
}
```

LinkedList 两个构造函数：

```java
public LinkedList() {}

public LinkedList(Collection<? extends E> c) {
     this();
     addAll(c);
}
```

### addAll()

```java
 public boolean addAll(int index, Collection<? extends E> c) {
        //校验 index 是否合理
        checkPositionIndex(index);
        
        Object[] a = c.toArray();
        int numNew = a.length;
        if (numNew == 0)
            return false;
       //succ：待添加节点的位置。
       //pred：待添加节点的前驱节点。  
        Node<E> pred, succ;
        if (index == size) {//在末尾插入
            succ = null;
            pred = last;
        } else { //不在末尾插入
            succ = node(index); //这个方法 会折半
            pred = succ.prev;
        }

        for (Object o : a) {
            //创建新节点
            @SuppressWarnings("unchecked") E e = (E) o;
            Node<E> newNode = new Node<>(pred, e, null);
            if (pred == null)
                first = newNode;
            else
                pred.next = newNode;
            pred = newNode;
        }

        if (succ == null) {
            last = pred;
        } else {
            pred.next = succ;
            succ.prev = pred;
        }
        //把集合的大小设置为新的大小 
        size += numNew;
        modCount++;
        return true;
    }
```

### get() -> 会有折半

```java
public E get(int index) {
     //校验 index 是否越界
      checkElementIndex(index);
      return node(index).item;
}

Node<E> node(int index) {
        // assert isElementIndex(index);
        //分一半查找
        if (index < (size >> 1)) {
            Node<E> x = first;
            for (int i = 0; i < index; i++)
                x = x.next;
            return x;
        } else {
            Node<E> x = last;
            for (int i = size - 1; i > index; i--)
                x = x.prev;
            return x;
        }
    }
```

### add()

```java
public boolean add(E e) {
   //在末尾追加元素的方法。
    linkLast(e);
    return true;
}

void linkLast(E e) {
      final Node<E> l = last;
      final Node<E> newNode = new Node<>(l, e, null);
      last = newNode;
      if (l == null) //为空链表
          first = newNode;
      else
          l.next = newNode;
      size++;//size 自增
      modCount++;
}
```

### remove()

```java
public boolean remove(Object o) {
    if (o == null) {
        for (Node<E> x = first; x != null; x = x.next) {
            if (x.item == null) {
                //移除节点
                unlink(x);
                return true;
            }
        }
    } else {
        for (Node<E> x = first; x != null; x = x.next) {
            if (o.equals(x.item)) {
                unlink(x);
                return true;
            }
        }
     }
    return false;
}

//删除节点
E unlink(Node<E> x) {
      // assert x != null;
      final E element = x.item;
      final Node<E> next = x.next;
      final Node<E> prev = x.prev;
      //1 -> 2 -> 3      1 -> 3
      if (prev == null) { //移除的是头节点
          first = next;
      } else {
          prev.next = next;
          x.prev = null;
      }

      if (next == null) { //移除的是尾节点
          last = prev;
      } else {
          next.prev = prev;
          x.next = null;
      }

      x.item = null;
      size--;
      modCount++;
      return element;
 }
```

### toArray()

```java
public Object[] toArray() {
       //创建一个新数组 然后遍历链表，将每个元素存在数组里，返回
       Object[] result = new Object[size];
       int i = 0;
       for (Node<E> x = first; x != null; x = x.next)
           result[i++] = x.item;
       return result;
}
```

