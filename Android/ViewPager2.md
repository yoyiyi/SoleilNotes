## 1 ViewPage2 简介

基本使用：

```java
//依赖包
implementation "androidx.viewpager2:viewpager2:1.0.0"

//添加布局    
<androidx.viewpager2.widget.ViewPager2
        android:id="@+id/vp2"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />    
```

特性：

- RTL 从右到左的布局支持：android:layoutDirection="rtl"
- 支持垂直方向：android:orientation="vertical"
- RecyclerView.Adapter 取代 PagerAdapter
- FragmentStateAdapter 取代 FragmentStatePagerAdapter
- registerOnPageChangeCallback 取代 addPageChangeListener
- 更高效的 notifyDataSetChanged

一个简单的例子

```java
//1.添加布局    
<androidx.viewpager2.widget.ViewPager2
        android:id="@+id/vp2"
        android:layout_width="match_parent"
        android:layout_height="match_parent" /> 

//2.定义 Adapter
public class BaseAdapter extends RecyclerView.Adapter<BaseAdapter.MyViewHolder> {
        
        @NonNull
        @Override
        public BaseAdapter.MyViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_test, parent, false);
            return new MyViewHolder(view);
        }

        @Override
        public void onBindViewHolder(@NonNull BaseAdapter.MyViewHolder holder, int position) {
            holder.tv_name.setText("第" + position + "页");
        }

        @Override
        public int getItemCount() {
            return 0;
        }

        class MyViewHolder extends RecyclerView.ViewHolder {
            private TextView tv_name;

            public MyViewHolder(@NonNull View itemView) {
                super(itemView);
                tv_name = itemView.findViewById(R.id.tv_name);
            }
        }

    }

//3.设置 Adapter
ViewPager2 vp2 = findViewById(R.id.vp2);
vp2.setAdapter(new BaseAdapter());
```

## 2 原理

ViewPager2继承ViewGroup，核心其实就是 **RecycleView + LinearLayoutManager**，其实就是对RecycleView封装了一层，所有功能都是围绕着 RecyclerView 和LinearLayoutManager展开。

```java
 private void initialize(Context context, AttributeSet attrs) {
        mAccessibilityProvider = sFeatureEnhancedA11yEnabled
                ? new PageAwareAccessibilityProvider()
                : new BasicAccessibilityProvider();
        
        //RecyclerView基本设置
        mRecyclerView = new RecyclerViewImpl(context);
        mRecyclerView.setId(ViewCompat.generateViewId());
        //设置 LayoutManager
        mLayoutManager = new LinearLayoutManagerImpl(context);
        mRecyclerView.setLayoutManager(mLayoutManager);
        mRecyclerView.setScrollingTouchSlop(RecyclerView.TOUCH_SLOP_PAGING);
        setOrientation(context, attrs);
        mRecyclerView.setLayoutParams(
                new ViewGroup.LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT));
        mRecyclerView.addOnChildAttachStateChangeListener(enforceChildFillListener());
       
        //将 RecyclerView.OnScrollListener事件转变为ViewPager2.OnPageChangeCallback 事件
        mScrollEventAdapter = new ScrollEventAdapter(this);      
        //创建模拟拖动事件
        mFakeDragger = new FakeDrag(this, mScrollEventAdapter, mRecyclerView);    
        //创建PagerSnapHelper对象，用来拦截fling事件，实现切面切换的效果
        mPagerSnapHelper = new PagerSnapHelperImpl();
        mPagerSnapHelper.attachToRecyclerView(mRecyclerView);
      
        mRecyclerView.addOnScrollListener(mScrollEventAdapter);

        mPageChangeEventDispatcher = new CompositeOnPageChangeCallback(3);
        mScrollEventAdapter.setOnPageChangeCallback(mPageChangeEventDispatcher);

        //页面切换事件
        final OnPageChangeCallback currentItemUpdater = new OnPageChangeCallback() {
            @Override
            public void onPageSelected(int position) {
                if (mCurrentItem != position) {
                    mCurrentItem = position;
                    mAccessibilityProvider.onSetNewCurrentItem();
                }
            }

            @Override
            public void onPageScrollStateChanged(int newState) {
                if (newState == SCROLL_STATE_IDLE) {
                    updateCurrentItem();
                }
            }
        };
        mPageChangeEventDispatcher.addOnPageChangeCallback(currentItemUpdater);
        mAccessibilityProvider.onInitialize(mPageChangeEventDispatcher, mRecyclerView);
        mPageChangeEventDispatcher.addOnPageChangeCallback(mExternalPageChangeCallbacks);

        //PageTransformerAdapter 作用是将页面的滑动事件转变为比率变化，比如，一个页面从左到右滑动，positionOffset变化是从0~1
        mPageTransformerAdapter = new PageTransformerAdapter(mLayoutManager);
        mPageChangeEventDispatcher.addOnPageChangeCallback(mPageTransformerAdapter);
        attachViewToParent(mRecyclerView, 0, mRecyclerView.getLayoutParams());
    }
```



## 3 参考阅读

* [ViewPager 2 使用讲解](https://blog.csdn.net/xiangshiweiyu_hd/article/details/104005810)

* [ViewPager2的原理和使用](https://www.jianshu.com/p/86573026e314?utm_campaign=maleskine)

