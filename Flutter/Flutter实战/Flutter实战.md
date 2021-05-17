# 第一章 起步

跨平台技术：

- H5 + 原生（Cordova、Ionic、微信小程序）
- JS + 原生渲染 （RN、Weex、快应用）
- 自绘UI + 原生(QT for mobile、Flutter)

# 第二章 第一个 Flutter 应用

## 路由管理

路由管理：管理页面跳转，也被称为导航管理。

```dart
//导航到新路由   
Navigator.push( context,
  MaterialPageRoute(builder: (context) {
    return NewRoute();
}));
```

Navigator：路由管理，入栈和出栈

```dart
Future push(BuildContext context, Route route) //入栈,打开新的页面
bool pop(BuildContext context, [ result ]) //出栈
```

### 路由传值

```dart
//跳转
RaisedButton(
                onPressed: () => Navigator.pop(context, "我是返回值"),
                child: Text("返回"),
              )

//返回
var result = await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) {
                return TipRoute(
                  // 路由参数
                  text: "我是提示xxxx",
                );
              },
            ),
          );    
```

### 命名路由

```dart
MaterialApp(
  //注册路由表
  routes:{
   "new_page":(context) => NewRoute(),
   "/":(context) => MyHomePage(title: 'Flutter Demo Home Page'), //注册首页路由
  } 
);

//跳转
onPressed: () {
  Navigator.pushNamed(context, "new_page");
},

//参数
Navigator.of(context).pushNamed("new_page", arguments: "hi");
//获取参数
class NewRoute extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    //获取路由参数  
    var args=ModalRoute.of(context).settings.arguments;
  }
}
```

通过`onGenerateRoute`做一些全局的路由跳转前置处理逻辑。

## 资源管理

资源管理：assets包括静态数据（例如JSON文件）、配置文件、图标和图片（JPEG，WebP，GIF，动画WebP / GIF，PNG，BMP和WBMP）。

```dart
flutter:
  assets:
    - assets/my_icon.png
```

加载图片

```dart
new AssetImage('icons/heart.png', package: 'my_icons')
new Image.asset('icons/heart.png', package: 'my_icons')    
```

# 第三章 基础组件

Flutter 中几乎所有的对象都是 Widget。

Widget：描述一个 UI 元素的**配置数据**。

Element：显示元素，一个 Widget 可以对应多个 Element。

StatelessWidget：无状态

StatefulWidget：有状态



生命周期：

* initState()： Widget 第一次插入到 Widget 树时调用。

* didChangeDependencies()：State 对象的依赖发生变化时会被调用。

* build

  * 在调用`initState()`之后。

  * 在调用`didUpdateWidget()`之后。
  * 在调用`setState()`之后。
  * 在调用`didChangeDependencies()`之后。
  * 在State对象从树中一个位置移除后（会调用deactivate）又重新插入到树的其它位置之后。

* reassemble()：调试，热重载(hot reload)时会被调用。

* didUpdateWidget()：Widget.canUpdate、

* deactivate()：State对象从树中被移除时。

* dispose()：永久移除

### 获取 State 对象

```dart
// 查找父级最近的Scaffold对应的ScaffoldState对象
ScaffoldState _state = context.findAncestorStateOfType<ScaffoldState>();

//自己暴露


//通过GlobalKey
//定义一个globalKey, 由于GlobalKey要保持全局唯一性，我们使用静态变量存储
static GlobalKey<ScaffoldState> _globalKey= GlobalKey();
...
Scaffold(
    key: _globalKey , //设置key
    ...  
)
_globalKey.currentState.openDrawer()
```

# 第五章  容器类组件







