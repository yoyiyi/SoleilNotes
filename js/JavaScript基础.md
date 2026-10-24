## 1 变量与作用域

### 1.1 var / let / const

| 特性 | var | let | const |
| --- | --- | --- | --- |
| 作用域 | 函数 | 块 | 块 |
| 提升 | 是，初始化为 undefined | 是，但未初始化（TDZ） | 同 let |
| 重复声明 | 允许 | 同作用域禁止 | 同作用域禁止 |
| 顶层挂到 globalThis | 是（脚本） | 否 | 否 |
| 必须初始化 | 否 | 否 | 是 |

```js
var a = 1;
let b = 2;
const c = 3;
const obj = { n: 1 };
obj.n = 2; // 可以：const 锁的是绑定
// obj = {}; // TypeError
```

`const` 只保证绑定不变；需要浅层不可变可用 `Object.freeze(obj)`。

### 1.2 作用域链与 TDZ

```js
function outer() {
  const x = 'outer';
  return function inner() { console.log(x); };
}
outer()(); // outer
```

作用域链由函数**定义位置**决定（词法作用域）。`let/const` 在块内提升但不初始化，声明前访问会抛 `ReferenceError`，这段区间叫暂时性死区（TDZ）：

```js
{
  // console.log(v); // ReferenceError
  let v = 1;
}
// typeof tdzVar; let tdzVar = 1; // 同样抛 ReferenceError
```

```js
for (var i = 0; i < 3; i++) setTimeout(() => console.log('var', i)); // 3 3 3
for (let j = 0; j < 3; j++) setTimeout(() => console.log('let', j)); // 0 1 2
```

`let` 为每次循环迭代创建新绑定，`var` 全程共用一个变量。

## 2 原型与原型链

每个对象都有内部槽 `[[Prototype]]`（可用 `Object.getPrototypeOf()` 读）。函数还有 `prototype` 属性，`new` 会把实例的 `[[Prototype]]` 指向 `F.prototype`。

```js
function Animal(name) { this.name = name; }
Animal.prototype.speak = function () { console.log(this.name); };

function Dog(name) { Animal.call(this, name); }
Dog.prototype = Object.create(Animal.prototype);
Dog.prototype.constructor = Dog;

const d = new Dog('旺财');
d.speak();            // 旺财
d instanceof Dog;     // true
d instanceof Animal;  // true
Object.getPrototypeOf(Object.prototype); // null
```

- 属性查找：自身 → 原型 → 原型的原型，直到 `null`；`hasOwnProperty` 只查自身。
- `class` 是原型的语法糖，方法定义在 `prototype` 上且不可枚举。
- `Object.create(null)` 创建无原型对象；`instanceof` 沿原型链查找 `F.prototype`。

## 3 this 绑定规则

| 调用方式 | 示例 | this |
| --- | --- | --- |
| 默认绑定 | `fn()` | 非严格脚本为 `globalThis`，严格模式/模块为 `undefined` |
| 隐式绑定 | `obj.fn()` | `obj` |
| 显式绑定 | `fn.call(obj)` / `apply` / `bind` | 指定对象 |
| new 绑定 | `new Fn()` | 新创建的实例 |
| 箭头函数 | `() => this` | 定义时外层词法作用域的 `this`，不可改 |

```js
const obj = {
  name: 'obj',
  regular() { console.log(this.name); },
  arrow: () => console.log(this.name),
};

obj.regular(); // obj
const detached = obj.regular;
detached();    // 严格模式 undefined，非严格脚本为全局 name
obj.arrow();   // 模块中 undefined：箭头函数不绑定调用者
```

优先级：`new` > `bind` > `call/apply` > 隐式 > 默认。箭头函数没有自己的 `this`、`arguments`、`prototype`，不能 `new`，也不能用 `call/apply/bind` 改 `this`。

## 4 闭包

闭包是函数与其词法环境的组合：内部函数引用的外部变量在外部函数返回后仍然存活。

```js
function createCounter() {
  let count = 0;
  return () => ++count; // 捕获 count
}
const counter = createCounter();
counter(); counter();
console.log(counter()); // 3
```

每次调用 `createCounter()` 都创建独立环境；同一闭包内共享变量。闭包常用于封装私有状态、回调、函数工厂和模块模式。它本身不是内存泄漏，但被长期持有的闭包会让其引用的对象无法回收。

## 5 事件循环

浏览器主线程上的 JS 执行是单线程的，靠事件循环调度：调用栈 → 清空微任务 → 可能渲染 → 取下一个宏任务。

| 队列 | 典型任务 |
| --- | --- |
| 宏任务 | 整段脚本、`setTimeout`/`setInterval`、I/O、UI 事件、`MessageChannel` |
| 微任务 | `Promise.then/catch/finally`、`queueMicrotask`、`MutationObserver`、`await` 之后的代码 |

每个宏任务执行完，必须清空微任务队列（包括执行中新增的微任务），然后才进入下一个宏任务。Node.js 中 `process.nextTick` 优先于 Promise 微任务，`setImmediate` 属于 check 阶段。

```js
console.log('script start');

setTimeout(() => console.log('setTimeout'), 0);

Promise.resolve()
  .then(() => console.log('promise1'))
  .then(() => console.log('promise2'));

(async () => {
  console.log('async start');
  await null; // 之后的代码进入微任务
  console.log('after await');
})();

console.log('script end');

// 输出：
// script start
// async start
// script end
// promise1
// after await
// promise2
// setTimeout
```

`setTimeout(fn, 0)` 不是立刻执行，而是把回调排到宏任务队列；因此它总在同步代码和当前所有微任务之后。

## 6 Promise 与 async/await

Promise 有 pending/fulfilled/rejected 三种状态，状态一旦确定不可变；`then` 返回新 Promise，回调总是异步（微任务）执行。

```js
const p = new Promise((resolve) => {
  console.log('executor'); // 同步执行
  resolve(1);
});
p.then(v => v + 1)
 .then(v => console.log(v))     // 2
 .catch(err => console.error(err))
 .finally(() => console.log('done'));
console.log('sync');
// executor → sync → 2 → done
```

| API | 行为 |
| --- | --- |
| `Promise.all` | 全部成功才成功，任一失败立即 reject |
| `Promise.allSettled` | 等全部结束，返回状态数组 |
| `Promise.race` | 第一个落定（成功或失败）的结果 |
| `Promise.any` | 第一个成功；全部失败抛 `AggregateError` |

`async` 函数总是返回 Promise；`await` 等待 Promise 落定，并把后续代码放回微任务。`await` 非 Promise 值也会让出一次执行权。

```js
async function load(ids) {
  // 并行：不要写成 for + await，否则会串行
  const list = await Promise.all(ids.map(id => fetch(`/api/${id}`)));
  return list.map(r => r.json());
}

async function safe() {
  try {
    return await load([1, 2]);
  } catch (e) {
    console.error('failed', e);
    throw e;
  }
}
```

## 7 深浅拷贝

浅拷贝只复制第一层，嵌套对象仍共享引用；深拷贝递归复制所有层级。

| 方式 | 层级 | 说明 |
| --- | --- | --- |
| `Object.assign({}, obj)` / `{ ...obj }` | 浅 | 复制自身可枚举属性（含 Symbol） |
| `[...arr]` / `arr.slice()` | 浅 | 数组常用 |
| `structuredClone(obj)` | 深 | 现代浏览器/Node 17+，支持 Date/Map/Set/循环引用，函数会抛错 |
| `JSON.parse(JSON.stringify(obj))` | 深 | 丢失 undefined/函数/Symbol，Date 变字符串，RegExp/Map/Set 失真，循环引用报错 |
| 递归 + `WeakMap` | 深 | 手写可控，注意处理循环引用 |

```js
const source = { a: 1, nested: { b: 2 } };
const shallow = { ...source };
shallow.nested.b = 99;
console.log(source.nested.b); // 99，共享嵌套对象

const deep = structuredClone(source);
deep.nested.b = 1;
console.log(source.nested.b); // 99
```

## 8 == 与 ===

`===` 不做类型转换；`==` 会按规范做抽象相等比较。工程上默认用 `===`，只保留 `x == null` 同时判断 `null/undefined` 的惯用法。

| 表达式 | 结果 | 原因 |
| --- | --- | --- |
| `0 == ''` | true | 两边转数字 0 |
| `'0' == false` | true | `false` → 0，`'0'` → 0 |
| `null == undefined` | true | 规范特例 |
| `null == 0` | false | `null` 只与 `undefined` 宽松相等 |
| `NaN == NaN` | false | `NaN` 不等于自身 |
| `[] == false` | true | `[]` → `''` → 0 |
| `[1] == 1` | true | `[1]` → `'1'` → 1 |
| `{} == {}` | false | 对象比较引用 |

`Object.is` 与 `===` 的差异：`Object.is(NaN, NaN)` 为 `true`，`Object.is(0, -0)` 为 `false`。对象与原始值比较时会走 `ToPrimitive`（`Symbol.toPrimitive` → `valueOf` → `toString`），所以 `[1] == 1` 成立。

## 9 模块化（ESM / CommonJS）

| 维度 | ESM | CommonJS |
| --- | --- | --- |
| 语法 | `import` / `export` | `require` / `module.exports` |
| 解析时机 | 静态，编译期确定依赖 | 运行时同步加载 |
| 绑定 | 实时绑定（live binding） | 导出值的拷贝/引用 |
| 顶层 `this` | `undefined` | `module.exports` |
| 严格模式 | 默认开启 | 默认非严格 |
| 顶层 await | 支持 | 不支持 |
| 缓存 | 按 URL 单例 | `require.cache` |

```js
// math.mjs
export const add = (a, b) => a + b;
export default (a, b) => a * b;

// main.mjs
import mul, { add } from './math.mjs';
console.log(add(1, 2), mul(2, 3)); // 3 6
```

```js
// math.cjs
exports.add = (a, b) => a + b;

// main.cjs
const { add } = require('./math.cjs');
```

Node 中通过 `package.json` 的 `"type": "module"` 或 `.mjs`/`.cjs` 后缀区分；ESM 没有 `__dirname`/`__filename`，可用 `import.meta.url` 配合 `fileURLToPath`。CJS 与 ESM 的互操作在 Node 各版本持续演进，以 Node 官方文档为准。

## 10 bind / call / apply

三者的作用都是改变函数执行时的 `this`：

```js
function greet(greeting, punct) {
  return `${greeting}, ${this.name}${punct}`;
}
const user = { name: 'Ann' };

greet.call(user, 'Hi', '!');    // Hi, Ann!
greet.apply(user, ['Hi', '?']); // Hi, Ann?
const hi = greet.bind(user, 'Hi');
hi('!');                        // Hi, Ann!
```

- `call(thisArg, ...args)`：立即调用，参数逐个传。
- `apply(thisArg, argsArray)`：立即调用，参数用数组。
- `bind(thisArg, ...args)`：返回新函数，`this` 固定并可预置参数（偏函数）；绑定后不能用 `call/apply` 再改 `this`。
- 用 `new` 调用绑定函数时，`new` 的优先级更高，`thisArg` 被忽略。
- 箭头函数忽略 `call/apply/bind` 的 `thisArg`。

```js
Function.prototype.myBind = function (ctx, ...preset) {
  const fn = this;
  return function (...args) {
    return fn.apply(ctx, [...preset, ...args]);
  };
};
```

## 11 对 Android 开发者的用处

| 场景 | 对应关系 |
| --- | --- |
| WebView 桥接 | `addJavascriptInterface(obj, "AndroidBridge")` 暴露 Java/Kotlin 方法；`evaluateJavascript()` 调用 JS；`@JavascriptInterface` 是 API 17+ 的安全前提 |
| RN | JS 线程 + 原生模块；旧架构走 Bridge，新架构用 JSI/TurboModules/Fabric；Hermes 执行 JS |
| Flutter | Dart AOT/JIT，不跑 JS；通过 Platform Channel 与原生通信，更接近 Compose 的声明式 UI |
| Kotlin vs JS | Kotlin 静态类型、空安全、协程；JS 动态类型、事件循环、Promise；Kotlin `==` 调 `equals`，JS `===` 比较引用/值且不做隐式转换 |

WebView 注意点：

```kotlin
webView.settings.javaScriptEnabled = true
webView.addJavascriptInterface(bridge, "AndroidBridge")
webView.evaluateJavascript("window.AndroidBridge.onReady()") { result -> /* 主线程回调 */ }
```

- `@JavascriptInterface` 方法运行在 WebView 的 Java Bridge 线程，不是主线程，更新 UI 要切主线程。
- 不要暴露敏感能力；校验来源 URL、限制 `javascript:` 与 `file://` 加载，必要时用 `WebViewClient.shouldOverrideUrlLoading` 做白名单。
- JS 与原生之间传复杂数据要序列化（JSON），大字符串跨桥有性能成本。

## 12 面试问答

**Q1 闭包会导致内存泄漏吗？**
闭包会延长变量生命周期，但不等于泄漏。若闭包被全局变量、未清理的定时器/事件监听、缓存长期持有，其引用的 DOM 或大对象才无法回收；解除引用、`clearInterval`、`removeEventListener` 即可。

**Q2 微任务和宏任务的执行顺序？**
同步代码 → 清空微任务（含新增）→ 渲染（浏览器）→ 下一个宏任务。`Promise.then`、`await` 后续是微任务，`setTimeout`、I/O 是宏任务。

**Q3 `var` 和 `let` 在 for 循环里有什么区别？**
`var` 全循环共用一个变量，回调里读到最终值；`let` 每次迭代创建新绑定，回调捕获当次值。

**Q4 箭头函数能当构造函数吗？`this` 怎么绑定？**
不能，箭头函数没有 `prototype` 和内部 `[[Construct]]`；`this` 在定义时按词法作用域捕获，`call/apply/bind` 也改不了。

**Q5 原型链的终点是什么？`instanceof` 原理？** `Object.prototype` 的原型是 `null`。`instanceof` 沿左侧对象的原型链查找右侧函数的 `prototype`，找到返回 `true`。

**Q6 深拷贝怎么写？JSON 方式有什么坑？**
优先 `structuredClone`；手写用递归 + `WeakMap` 处理循环引用。JSON 方式会丢 `undefined`、函数、Symbol，`Date` 变字符串，`RegExp`/`Map`/`Set` 失真，循环引用直接报错。

**Q7 `==` 和 `===` 怎么选？** 默认 `===`；需要同时判断 `null` 和 `undefined` 时用 `x == null`；`NaN` 判断用 `Number.isNaN`，`-0` 区分用 `Object.is`。

**Q8 `await` 一定异步吗？Promise 和 async/await 是什么关系？**
`await` 后面的代码一定在微任务中执行，即使等待的是普通值。`async/await` 是基于 Promise 的语法糖：`async` 函数返回 Promise，`await` 相当于注册后续回调。

**Q9 ESM 和 CommonJS 的核心区别？** ESM 静态解析、实时绑定、默认严格模式、支持顶层 await；CJS 运行时 `require`、同步加载、导出值拷贝、`this` 指向 `module.exports`。

**Q10 `call`、`apply`、`bind` 的区别？手写 `bind` 要注意什么？**
`call`/`apply` 立即执行，区别只在参数形式；`bind` 返回新函数并固定 `this`。手写时要合并预置参数，并注意用 `new` 调用时忽略绑定的 `this`（可用 `Object.create(fn.prototype)` 或 `Reflect.construct`）。
