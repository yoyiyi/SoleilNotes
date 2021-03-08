
## 1 例子
实际项目中，使用 DataBinding 例子

```java
class ConversationViewModel(application: Application) : BaseInjectViewModel<IMModel>(application) {
    var name = ObservableField<String>()
}
```

activity_conversation.xml

```xml
<layout xmlns:android="http://schemas.android.com/apk/res/android"
        xmlns:app="http://schemas.android.com/apk/res-auto">

    <data>

        <variable
            name="viewModel"
            type="com.zp.im.ui.msg.ConversationViewModel"/>
    </data>
    <RelativeLayout>
      <TextView
         android:id="@+id/tv_name"
         android:text="@{viewModel.name}"/>
    </RelativeLayout>

</layout>

```

## 2 原理

AS 会生成 XXXImpl.java 代码
```java
public class ActivityConversationBindingImpl extends ActivityConversationBinding  {
    ...
    public ActivityConversationBindingImpl(@Nullable androidx.databinding.DataBindingComponent bindingComponent, @NonNull View root) {
        this(bindingComponent, root, mapBindings(bindingComponent, root, 9, sIncludes, sViewsWithIds));
    } 
    //mapBindings 这个方法将 bindings 数组强转为我们的控件类型
    
    private ActivityConversationBindingImpl(androidx.databinding.DataBindingComponent bindingComponent, View root, Object[] bindings) {
        super(bindingComponent, root, 5
            , (android.widget.FrameLayout) bindings[8]
            , (android.widget.ImageView) bindings[6]
            , (android.widget.ImageView) bindings[7]
            , (android.widget.ImageView) bindings[2]
            , (androidx.appcompat.widget.Toolbar) bindings[5]
            , (com.zpparts.res.widget.MarqueeTextView) bindings[1]
            , (android.widget.TextView) bindings[4]
            );
        //根据tag找到控件
        this.ivOnline.setTag(null);
        this.mboundView0 = (android.widget.LinearLayout) bindings[0];
        this.mboundView0.setTag(null);
        this.mboundView3 = (com.zpparts.res.widget.MarqueeTextView) bindings[3];
        this.mboundView3.setTag(null);
        this.tvName.setTag(null);
        this.tvShop.setTag(null);
        setRootTag(root);
        // 这个方法调用 requestRebind -> 通过 handler 形式更新 ui
        // mUIThreadHandler.post(mRebindRunnable);
        // mRebindRunnable -> executeBindings()
        invalidateAll();
    }
    @Override
    public boolean setVariable(int variableId, @Nullable Object variable)  {
        boolean variableSet = true;
        if (BR.viewModel == variableId) {
            //setViewModel
            setViewModel((com.zp.im.ui.msg.ConversationViewModel) variable);
        }
        else {
            variableSet = false;
        }
            return variableSet;
    }

    public void setViewModel(@Nullable com.zp.im.ui.msg.ConversationViewModel ViewModel) {
        this.mViewModel = ViewModel;
        synchronized(this) {
            mDirtyFlags |= 0x20L;
        }
        notifyPropertyChanged(BR.viewModel);
        super.requestRebind();
    }
    
    @Override
    protected void executeBindings() {
        ...
        androidx.databinding.ObservableField<java.lang.String> viewModelName = null;
        ...

        if ((dirtyFlags & 0x70L) != 0) {

                    if (viewModel != null) {
                        // read viewModel.name
                        viewModelName = viewModel.getName();
                    }
                    //注册观察者，来监听绑定的数据，通过观察者模式，监视绑定的数据，数据一旦变化，就会更新
                    updateRegistration(4, viewModelName);

                    if (viewModelName != null) {
                        // read viewModel.name.get()
                        viewModelNameGet = viewModelName.get();
                    }
            } 
       
        //根据数据修改UI
        if ((dirtyFlags & 0x70L) != 0) {
            // api target 1
            //this.tvName 就是布局中id 为 tv_name 的 TextView 
            androidx.databinding.adapters.TextViewBindingAdapter.setText(this.tvName, viewModelNameGet);
        }

    }

}

```
* 通过调用 XXXbinding 的 setVariable() 调用 setViewModel()，将绑定数据实例（这里就是ViewModel）传入了。
* executeBindings() 注册观察者，来监听绑定的数据，通过观察者模式，监视绑定的数据，数据一旦变化，就会更新 UI

## 3 总结

* dataBinding 只是一种工具，和 MVVM(设计思想)是完全没有关系的，MVC、MVP同样可以使用dataBinding。
* 使用 DataBinding 会导致大量的内存消耗。
  * 会产生多余的数组，存放 view 对象
  * 存在大量 handler，looper 不断的循环消息
  * 针对每一个控件都会产生一个回调对象

* dataBinding 使用 APT 技术，编译期间生成控件与 model 的绑定代码。所以会产生很多类，随着布局文件的增加，编译会越来越慢。