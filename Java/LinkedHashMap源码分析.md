## 1 简介

LinkedHashMap 继承 HashMap，内部有一个双向链表维护键值对的顺序，在 LinkedHashMap 中可以保持两种顺序，分别是**插入顺序和访问顺序**。

```java
public class LinkedHashMap<K,V> extends HashMap<K,V> implements Map<K,V> {}
```

## 2 源码

LinkedHashMap 继承 HashMap，数据数据结构也继承了 HashMap.Node，还有几个重要的属性。

```java
// Entry 继承 HashMap.Node
static class Entry<K,V> extends HashMap.Node<K,V> {
    //前驱节点 后继节点
    Entry<K,V> before, after;
    Entry(int hash, K key, V value, Node<K,V> next) {
        super(hash, key, value, next);
    }
}
// 用于指向双向链表的头部
transient LinkedHashMap.Entry<K,V> head;

//用于指向双向链表的尾部
transient LinkedHashMap.Entry<K,V> tail;

//false  按插入顺序存储数据 默认为 false
//true   按访问顺序存储数据  -> 用来实现 LRU 策略缓存。
final boolean accessOrder;
```

LinkedHashMap 有多个重载的构造方法，默认初始化中，`accessOrder` 的初始值都为 false，也可以通过以下构造方法进行设置：

```java
//多了一个 accessOrder的参数，用来指定按照LRU排列方式还是顺序插入的排序方式
public LinkedHashMap(int initialCapacity,
                         float loadFactor,
                         boolean accessOrder) {
   super(initialCapacity, loadFactor);
   this.accessOrder = accessOrder;
 }
```

### get()

```java
public V get(Object key) {
  Node<K,V> e;
  //调用 HashMap#getNode() 取出节点
  if ((e = getNode(hash(key), key)) == null)
    return null;
  //如果 accessOrder == true，执行afterNodeAccess，把节点移动到链表末尾
  if (accessOrder)
    afterNodeAccess(e);
  return e.value;
}
```

###  afterNodeAccess()

```java
//把节点移动到链表末尾
void afterNodeAccess(Node<K,V> e) {
        LinkedHashMap.Entry<K,V> last;
        //如果 accessOrder == true，并且访问的节点不是尾节点
        if (accessOrder && (last = tail) != e) {
            //取出前驱和后继节点
            LinkedHashMap.Entry<K,V> p =
                (LinkedHashMap.Entry<K,V>)e, b = p.before, a = p.after;
            p.after = null;
            //p的前驱节点为空，则将a赋值给头节点
            if (b == null)
                head = a;
            else
                //把p节点从链表中移除
                b.after = a;
            //构建双向链表
            if (a != null)
                a.before = b;
            else
                last = b;
            //把p节点放到双向链表尾
            if (last == null)
                head = p;
            else {
                p.before = last;
                last.after = p;
            }
            //尾节点为p
            tail = p;
            ++modCount;
        }
    }
```

