## 1 简介

CopyOnWriteArrayList 在 JUC 包下，支持并发的 List，它是个**线程安全**，读操作通过无锁的 ArrayList，写操作通过**创建底层数组副本**，是一种**读写分离**的并发策略，称这种容器为"**写时复制器**"。由于这个特性，CopyOnWriteArrayList 适用于**读多写少**的并发场景。但是也有缺点，一是内存占用，每次写都要创建副本，二是无法**保证实时性**。

## 2 源码

### 2.1 add

```java
public boolean add(E e) {
        //使用 ReentrantLock 加锁，保证线程安全
        final ReentrantLock lock = this.lock;
        lock.lock();
        try {
            Object[] elements = getArray();
            int len = elements.length;
            //拷贝原容器，长度为原容器长度加一
            Object[] newElements = Arrays.copyOf(elements, len + 1);
            //在新副本上执行添加操作
            newElements[len] = e;
            //将原容器引用指向新副本
            setArray(newElements);
            return true;
        } finally {
            //解锁
            lock.unlock();
        }
    }
}
```

### 2.2 remove

```java
 public E remove(int index) {
        //使用 ReentrantLock 加锁，保证线程安全
        final ReentrantLock lock = this.lock;
        lock.lock();
        try {
            Object[] elements = getArray();
            int len = elements.length;
            E oldValue = get(elements, index);
            int numMoved = len - index - 1;
            if (numMoved == 0)
                //如果要删除的是列表末端数据，拷贝前len-1个数据到新副本上，再切换引用
                setArray(Arrays.copyOf(elements, len - 1));
            else {
                //否则，将除要删除元素之外的其他元素拷贝到新副本中，并切换引用
                Object[] newElements = new Object[len - 1];
                System.arraycopy(elements, 0, newElements, 0, index);
                System.arraycopy(elements, index + 1, newElements, index,
                                 numMoved);
                setArray(newElements);
            }
            return oldValue;
        } finally {
            //解锁
            lock.unlock();
        }
    }
}
```

### 2.3 get

```java
//直接读取，无需加锁
public E get(int index) {
      return get(getArray(), index);
}

private E get(Object[] a, int index) {
      return (E) a[index];
}
```

