## 1 简介

在 Android 9.0 中，通过反射或 JNI 访问非公开接口时会触发警告/异常等。当我们调用反射 java.lang.Class.getDeclaredMethod(String) 最终调用到  getDeclaredMethodInternal 这个 native 方法。

```java
static jobject Class_getDeclaredMethodInternal(JNIEnv* env, jobject javaThis,
                                               jstring name, jobjectArray args) {
  ...
  if (result == nullptr || ShouldBlockAccessToMember(result->GetArtMethod(), soa.Self())) {
    //ShouldBlockAccessToMember 触发系统的限制，如果不满足相关条件，直接抛异常。 
    return nullptr;
  }
  return soa.AddLocalReference<jobject>(result.Get());
}

//ShouldBlockAccessToMember
ALWAYS_INLINE static bool ShouldBlockAccessToMember(T* member, Thread* self)
    REQUIRES_SHARED(Locks::mutator_lock_) {
  //hiddenapi::GetMemberAction 
  hiddenapi::Action action = hiddenapi::GetMemberAction(
      member, self, IsCallerTrusted, hiddenapi::kReflection);
  if (action != hiddenapi::kAllow) {
    hiddenapi::NotifyHiddenApiListener(member);
  }
  return action == hiddenapi::kDeny;
}

//hidden_api.cc 
template<typename T>
inline Action GetMemberAction(T* member,
                              Thread* self,
                              std::function<bool(Thread*)> fn_caller_is_trusted,
                              AccessMethod access_method)
    REQUIRES_SHARED(Locks::mutator_lock_) {
  DCHECK(member != nullptr);
  //获取 HiddenApiAccessFlags 列表  
  HiddenApiAccessFlags::ApiList api_list = member->GetHiddenApiAccessFlags();
  Action action = GetActionFromAccessFlags(member->GetHiddenApiAccessFlags());
  //很明显，如果能干涉这3个语句的返回值，就能影响到系统对隐藏 API 的判断 欺骗系统 绕过限制。
  if (action == kAllow) {
    return action;
  }
  if (fn_caller_is_trusted(self)) {
    return kAllow;
  }
  return detail::GetMemberActionImpl(member, api_list, action, access_method);
}
```

* 针对 action == kAllow ：动态搜索到 hidden_api_policy_，直接修改内存
* 针对 fn_caller_is_trusted(self)：修改偏移的方式直接修改 ClassLoader
* 针对 GetMemberActionImpl：修改 runtime 的内存，或修改signature

**绕过 API 限制**

* **通过某种方式修改函数的执行流程** （**inline hook**）
* **以系统类的身份去反射**
  * 直接把我们自己变成系统类
  * 借助系统类去调用反射（通过 「元反射」来反射调用 `VMRuntime.setHiddenApiExemptions` 将要使用的隐藏 API 全部都豁免掉了）

## 2 参考阅读

* [一种绕过Android P对非SDK接口限制的简单方法](http://weishu.me/2018/06/07/free-reflection-above-android-p/)

* [另一种绕过 Android P以上非公开API限制的办法](http://weishu.me/2019/03/16/another-free-reflection-above-android-p/)

