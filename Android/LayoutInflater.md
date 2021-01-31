## 1 LayoutInflater 简介

简单来说 LayoutInflater 是用来加载布局，把 xml 布局文件加载成一个 View，有三种方法获取 LayoutInflater：

* Context.getSystemService(Context.LAYOUT_INFLATER_SERVICE) ;
* Activity.getLayoutInflater()； -> 后面调用  LayoutInflater.from(context);
* LayoutInflater.from(context); -> Context.getSystemService(Context.LAYOUT_INFLATER_SERVICE) ;

得到 LayoutInflater  之后，就可以使用 **inflate** 加载布局，inflate 有好几个重载方法，最终调用下面这个方法：

```java
public View inflate(@LayoutRes int resource, @Nullable ViewGroup root, boolean attachToRoot)   
```

* int resource：布局ID

* ViewGroup root：根布局
*  boolean attachToRoot：是否要添加到父布局root中去

其中有个关键参数 root 作用：

- attachToRoot == true && root ！= null， View 会被 add 到 root 中去，将 root 返回。
- attachToRoot == false && root ！= null，View 会直接返回，root 会为 View 生成 LayoutParams 并设置到该 View 中去。
- attachToRoot == false && root == null，新解析的View会直接作为结果返回。

## 2 源码

inflate 代码如下：

```java
  public View inflate(XmlPullParser parser, @Nullable ViewGroup root, boolean attachToRoot) {
        synchronized (mConstructorArgs) {
            Trace.traceBegin(Trace.TRACE_TAG_VIEW, "inflate");

            final Context inflaterContext = mContext;
            final AttributeSet attrs = Xml.asAttributeSet(parser);
            Context lastContext = (Context) mConstructorArgs[0];
            mConstructorArgs[0] = inflaterContext;
            View result = root;

            try {
                // Look for the root node.
                int type;
                // 1.判断布局的合理性
                while ((type = parser.next()) != XmlPullParser.START_TAG &&
                        type != XmlPullParser.END_DOCUMENT) {
                    // Empty
                }
                if (type != XmlPullParser.START_TAG) {
                    throw new InflateException(parser.getPositionDescription()
                            + ": No start tag found!");
                }
                final String name = parser.getName();
                if (TAG_MERGE.equals(name)) {
                // 2.如果是Merge标签，必须依附于一个RootView，否则抛出异常
                    if (root == null || !attachToRoot) {
                        throw new InflateException("<merge /> can be used only with a valid "
                                + "ViewGroup root and attachToRoot=true");
                    }
                    //3.解析布局 -> 加入检验 然后调用 createViewFromTag 来解析
                    rInflate(parser, root, inflaterContext, attrs, false);
                } else {                 
                    //4.根据节点名来创建 View 对象  <<<代码1
                    final View temp = createViewFromTag(root, name, inflaterContext, attrs);
                    ..
                }
            } catch (XmlPullParserException e) {
                ......
            }
            return result;
        }
    }
```

从上面代码，我们可以看出重要的方法的 代码1  **createViewFromTag()**

```java
View createViewFromTag(View parent, String name, Context context, AttributeSet attrs,
            boolean ignoreThemeAttr) {
        if (name.equals("view")) {
            name = attrs.getAttributeValue(null, "class");
        }
        // Apply a theme wrapper, if allowed and one is specified.
        if (!ignoreThemeAttr) {
            final TypedArray ta = context.obtainStyledAttributes(attrs, ATTRS_THEME);
            final int themeResId = ta.getResourceId(0, 0);
            if (themeResId != 0) {
                context = new ContextThemeWrapper(context, themeResId);
            }
            ta.recycle();
        }
        if (name.equals(TAG_1995)) {
            // Let's party like it's 1995!
            return new BlinkLayout(context, attrs);
        }
        try {
            View view;
            if (mFactory2 != null) {
                //1.调用 mFactory2 的 onCreateView() <<< 代码 1
                view = mFactory2.onCreateView(parent, name, context, attrs);
            } else if (mFactory != null) {
                //2.调用 mFactory 的 onCreateView() 
                view = mFactory.onCreateView(name, context, attrs);
            } else {
                view = null;
            }
            if (view == null && mPrivateFactory != null) {
                //3.调用 mPrivateFactory 的 onCreateView()
                view = mPrivateFactory.onCreateView(parent, name, context, attrs);
            }
            if (view == null) {
                //4.开始自己创建 View ,使用反射
                final Object lastContext = mConstructorArgs[0];
                mConstructorArgs[0] = context;
                try {
                    if (-1 == name.indexOf('.')) {                       
                        view = onCreateView(parent, name, attrs);
                    } else {
                        view = createView(name, null, attrs);
                    }
                } finally {
                    mConstructorArgs[0] = lastContext;
                }
            }
            return view;
        } catch (InflateException e) {
            throw e;
        } 
    }
```

代码1 从方法名我们可以比较容易看出创建 View，流程都差不多。

```java
//Factory2 是一个接口
public interface Factory2 extends Factory {       
      @Nullable
      View onCreateView(@Nullable View parent, @NonNull String name,
              @NonNull Context context, @NonNull AttributeSet attrs);
}

//AppCompatViewInflater#createView
final View createView(View parent, final String name, @NonNull Context context,
            @NonNull AttributeSet attrs, boolean inheritContext,
            boolean readAndroidTheme, boolean readAppTheme, boolean wrapContext) {
        
        switch (name) {
            case "TextView":
                view = createTextView(context, attrs);
                verifyNotNull(view, name);
                break;
        ...
        }
    return view;
}               

```

这个源码还是比较简单，包括如下步骤：

* 通过 XML 的 Pull 解析方式获取 View 的标签；

* 通过标签以**反射**的方式来创建 View 对象；

* 如果是 ViewGroup 的话，会对子 View 遍历并重复以上步骤，然后 add 到父 View 中；

相关的方法：inflate ->  rInflate ->  createViewFromTag -> createView ；