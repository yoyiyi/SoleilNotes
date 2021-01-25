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

