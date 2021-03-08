
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
