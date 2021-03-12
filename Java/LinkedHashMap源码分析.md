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

### getNode()

```java
//得到桶号
final HashMap.Node<K,V> getNode(int hash, Object key) {
        //定义变量
        HashMap.Node<K,V>[] tab; HashMap.Node<K,V> first, e; int n; K k;
      
        //数组不为空、数组长度>0、 通过hash计算出该元素在数组中存放位置的索引
        if ((tab = table) != null && (n = tab.length) > 0 &&
                (first = tab[(n - 1) & hash]) != null) {
            //hash == key? 判断该数组索引位置处第一个是否要找的元素 
            if (first.hash == hash && // always check first node
                    ((k = first.key) == key || (key != null && key.equals(k))))
                //找到，返回
                return first;
            //没有找到,循环遍历
            if ((e = first.next) != null) {
                //如果第1个的元素是红黑树类型的节点
                if (first instanceof HashMap.TreeNode)
                    //调用红黑树的方法查找节点
                    return ((HashMap.TreeNode<K,V>)first).getTreeNode(hash, key);
                //如果不是,则该为链表,需要遍历查找
                do {
                    //循环判断下一个节点的 hash == key?
                    if (e.hash == hash &&
                            ((k = e.key) == key || (key != null && key.equals(k))))
                        return e;
                    //更新e为下一个
                } while ((e = e.next) != null);
            }
        }
        //没找到返回Null
        return null;
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

### put()

使用父类 HashMap()。

```java
final V putVal(int hash, K key, V value, boolean onlyIfAbsent,
                   boolean evict) {
        Node<K,V>[] tab; Node<K,V> p; int n, i;
        //存放元素的 table 桶不存在,进行初始化
        if ((tab = table) == null || (n = tab.length) == 0)
            n = (tab = resize()).length;
            //用来存放目标hash值得节点不存在,新建
        if ((p = tab[i = (n - 1) & hash]) == null)
            tab[i] = newNode(hash, key, value, null);
        else {
        	//hash相同,key值相同
            Node<K,V> e; K k;
            if (p.hash == hash &&
                ((k = p.key) == key || (key != null && key.equals(k))))
                e = p;
            else if (p instanceof TreeNode)
            //是否是二叉树节点,如是放入二叉树中
                e = ((TreeNode<K,V>)p).putTreeVal(this, tab, hash, key, value);
            else {
                for (int binCount = 0; ; ++binCount) {
                    if ((e = p.next) == null) {
                        p.next = newNode(hash, key, value, null);
                        if (binCount >= TREEIFY_THRESHOLD - 1) // -1 for 1st
                            treeifyBin(tab, hash);
                        break;
                    }
                    if (e.hash == hash &&
                        ((k = e.key) == key || (key != null && key.equals(k))))
                        break;
                    p = e;
                }
            }
            if (e != null) { // existing mapping for key
                V oldValue = e.value;
                if (!onlyIfAbsent || oldValue == null)
                    e.value = value;
                afterNodeAccess(e);
                return oldValue;
            }
        }
        //操作 ++
        ++modCount;
        if (++size > threshold)
            resize();
        //调用 afterNodeInsertion
        afterNodeInsertion(evict);
        return null;
    }
```

### afterNodeInsertion()

```java
   //新节点插入之后回调 ，判断是否需要删除最老插入的节点。
    void afterNodeInsertion(boolean evict) { // possibly remove eldest
        LinkedHashMap.Entry<K,V> first;
        //LinkedHashMap 默认返回 false 则不删除节点
        if (evict && (first = head) != null && removeEldestEntry(first)) {
            K key = first.key;
            //调用 removeNode 移除节点
            removeNode(hash(key), key, null, false, true);
        }
    }

	void afterNodeAccess(Node<K,V> e) { // move node to last
        LinkedHashMap.Entry<K,V> last;
        if (accessOrder && (last = tail) != e) {
            LinkedHashMap.Entry<K,V> p =
                (LinkedHashMap.Entry<K,V>)e, b = p.before, a = p.after;
            p.after = null;
            if (b == null)
                head = a;
            else
                b.after = a;
            if (a != null)
                a.before = b;
            else
                last = b;
            if (last == null)
                head = p;
            else {
                p.before = last;
                last.after = p;
            }
            tail = p;
            ++modCount;
        }
    }

    //LinkedHashMap 默认返回false 则不删除节点。 返回true 代表要删除最早的节点。通常构建一个LRUCache 会在达到Cache的上限是返回true
    protected boolean removeEldestEntry(Map.Entry<K,V> eldest) {
        return false;
    }
```

### remove()

使用 HashMap 的 remove()

```java
public V remove(Object key) {
        Node<K,V> e;
        //调用 removeNode() 删除节点
        return (e = removeNode(hash(key), key, null, false, true)) == null ?
            null : e.value;
}
```

### removeNode

```java

final Node<K,V> removeNode(int hash, Object key, Object value,
                            boolean matchValue, boolean movable) {
    Node<K,V>[] tab; Node<K,V> p; int n, index; // 节点数组、当前节点、数组长度、索引值
    
     //根据 hash 找到节点对象p
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (p = tab[index = (n - 1) & hash]) != null) {
        Node<K,V> node = null, e; K k; V v;

        //如果当前节点的hash 和 key 相等，那么当前节点就是要删除的节点，赋值给node
        if (p.hash == hash &&
            ((k = p.key) == key || (key != null && key.equals(k))))
            node = p;
 
        //检查是否有 next 节点
        else if ((e = p.next) != null) {
            //如果当前节点是TreeNode类型，说明是一个红黑树，调用getTreeNode从树结构中查找满足条件的节点
            if (p instanceof TreeNode)
                node = ((TreeNode<K,V>)p).getTreeNode(hash, key);
            //如果是一个链表，只需要从头到尾逐个节点比对即可    
            else {
                do {
                    //如果e节点的是否和key相等，e节点就是要删除的节点，赋值给node变量
                    if (e.hash == hash &&
                        ((k = e.key) == key ||
                            (key != null && key.equals(k)))) {
                        node = e;
                        break;
                    }
 
                    // 走到这里，说明e也没有匹配上
                    p = e; // 把当前节点p指向e，这一步是让p存储的永远下一次循环里e的父节点，如果下一次e匹配上了，那么p就是node的父节点
                } while ((e = e.next) != null); //如果e存在下一个节点，那么继续去匹配下一个节点。直到匹配到某个节点跳出 或者 遍历完链表所有节点
            }
        }
 
        /*
         * 如果node不为空，说明匹配到了要删除的节点
         * 如果不需要对比value值或需要value 值相等
         * 那么删除该node节点
         */
        if (node != null && (!matchValue || (v = node.value) == value ||
                                (value != null && value.equals(v)))) {
            if (node instanceof TreeNode) // 红黑树
                ((TreeNode<K,V>)node).removeTreeNode(this, tab, movable);
            else if (node == p) 
                tab[index] = node.next; //删除节点
            else
                p.next = node.next;
            ++modCount; //修改次数递增
            --size; // 元素个数递减
            afterNodeRemoval(node); // 调用afterNodeRemoval方法，该方法HashMap 没有任何实现逻辑，目的是为了让子类根据需要自行覆写
            return node;
        }
    }
    return null;
}
```





