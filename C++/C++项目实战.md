## 1 C++ 工程结构
「做过 C++ 项目」不是写了几个类，而是能把公开头文件、内部实现、测试、第三方依赖和构建产物分开，让别人一条命令就能配置、编译、测试、安装。下面这套布局适用于中小型 C++ 项目，第 8 节的线程池库直接套用。
```text
threadpool/
├── include/threadpool/        # 对外头文件，随库安装
│   └── thread_pool.hpp
├── src/                       # 实现文件与私有头
│   ├── thread_pool.cpp
│   └── detail/thread_pool_impl.hpp
├── tests/
│   ├── CMakeLists.txt
│   ├── test_thread_pool.cpp   # 单元测试
│   └── test_thread_pool_integration.cpp
├── third_party/               # 内置第三方源码，锁定版本并保留 LICENSE
├── cmake/                     # 安装模板、公共编译选项模块
│   └── ThreadPoolConfig.cmake.in
├── examples/main.cpp          # 可运行示例，也是最快的回归验证
├── build/                     # 生成目录，可整目录删除，不入库
├── CMakeLists.txt
├── .clang-format
├── .clang-tidy
├── README.md
├── LICENSE
└── .gitignore
```

| 路径 | 职责 | 不该放什么 |
| --- | --- | --- |
| `src/` | `.cpp` 实现、程序入口 | 公共头文件 |
| `src/detail/` | 私有头，只被本库 `.cpp` 包含 | 对外承诺的接口 |
| `include/<项目名>/` | 调用方唯一需要包含的头文件，可随库安装 | 内部实现细节、第三方头 |
| `tests/` | 单元测试、集成测试、测试数据 | 生产逻辑 |
| `third_party/` | 内置依赖源码，锁定提交号 | 自己写的业务代码 |
| `cmake/` | `FindXXX.cmake`、`Config.cmake.in`、公共编译选项 | 构建产物 |
| `build/` | CMake 生成的一切 | 任何要提交的文件 |

1. **头文件目录约定**：写 `#include "threadpool/thread_pool.hpp"` 而不是 `#include "thread_pool.hpp"`。前者在包含路径上唯一，避免不同库的同名头互相覆盖，这也是 `<fmt/format.h>`、`<boost/asio.hpp>` 的做法。公共头只放声明和必须内联的定义，实现细节收进 `detail` 命名空间与 `src/detail/`。
2. **源文件与私有头**：`src/detail/*.hpp` 不安装、不导出，可以随意改；一旦进 `include/` 就要承担兼容义务（见第 10.6 节 ABI）。
3. **README** 写清依赖、构建命令、运行示例、测试命令、目录说明和许可证；面试官常追问「换台机器怎么跑」。
4. **LICENSE** 明确授权（MIT/Apache-2.0/BSD）；`third_party/` 里每个依赖保留原始许可证，避免授权冲突。
5. **`.clang-format`** 提交入库，格式变成工具问题而非评审争论，见第 4 节。
6. **`.gitignore`** 忽略构建目录、目标文件、覆盖率与 IDE 缓存，构建产物一律不入库：`build*/`、`*.o`、`*.a`、`*.so`、`*.gcda`、`*.gcno`、`compile_commands.json`、`.cache/`、`coverage/`、IDE 配置目录。

## 2 CMake 工程实践
CMake 不直接编译，而是先生成 Ninja/Makefile/VS 工程再执行。C++ 项目的正确写法是「现代 CMake」：一切以 target 为中心，用 `PUBLIC/PRIVATE/INTERFACE` 描述传播关系，不用全局 `include_directories`。开局两行决定了整个工程的下限：
```cmake
cmake_minimum_required(VERSION 3.16)              # 3.16 起 target 属性与生成器表达式较完整
project(threadpool VERSION 1.0.0 LANGUAGES CXX)   # 只启用 C++，避免误要求 C 编译器
```
`LANGUAGES CXX` 显式声明语言；`project` 还会定义 `PROJECT_VERSION`/`PROJECT_VERSION_MAJOR` 等变量，供安装与配置文件生成使用。

| 目标类型 | 产物 | 典型用途 | 注意 |
| --- | --- | --- | --- |
| `STATIC` | `.a` / `.lib` | 内部库、可执行文件共用代码 | 要再链进 `.so` 需 `-fPIC` |
| `SHARED` | `.so` / `.dll` | 对外发布、插件、热替换 | 注意导出符号与 SONAME |
| `INTERFACE` | 无产物 | 纯头文件库、选项集合、别名 | 只能用 `INTERFACE` 关键字 |

`ALIAS` 让使用方只认 `threadpool::threadpool`，将来改成 `SHARED` 或换成 `find_package` 导出的目标时，调用方一行都不用改（见完整示例里的 `add_library(... ALIAS ...)`）。`target_include_directories` 的三个关键字决定「谁能看到这个目录」：

| 关键字 | 本目标编译时可用 | 向下游使用者传播 | 适用场景 |
| --- | --- | --- | --- |
| `PUBLIC` | 是 | 是 | 库的公共头目录，如 `include/` |
| `PRIVATE` | 是 | 否 | 仅实现需要的目录，如 `src/detail/` |
| `INTERFACE` | 否 | 是 | 自己不需要、只给别人用（纯头文件库） |

误用后果很具体：把 `src/detail/` 写成 `PUBLIC`，下游就能包含私有头，你以后改不动它；把公共头写成 `PRIVATE`，本库照常编译，但链接它的可执行文件报「找不到头文件」，因为路径没传播。正确写法要配生成器表达式（完整工程里连续写更紧凑，只要 `PUBLIC`/`PRIVATE` 作用域正确）：
```cmake
target_include_directories(threadpool
    PUBLIC  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
            $<INSTALL_INTERFACE:include>
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)
```
`$<BUILD_INTERFACE:...>` 只在源码树内有效，`$<INSTALL_INTERFACE:...>` 只在安装后的导出中保留；不写它们，导出的 target 会带绝对源码路径，别的机器 `find_package` 后立刻找不到头文件。`target_link_libraries` 同理：类型出现在公共头里的依赖（如 `std::thread` 需要的 `Threads::Threads`）写 `PUBLIC`，只在 `.cpp` 里用的写 `PRIVATE`。`target_compile_features` 按能力而非编译器开关声明标准，`set(CMAKE_CXX_STANDARD 17)` 只是目录级默认值、不传播，`cxx_std_17` 会随 `find_package` 导出，两者配合、优先后者：
```cmake
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)   # 编译器不支持就报错，而非静默降级
set(CMAKE_CXX_EXTENSIONS OFF)         # 关掉 GNU 扩展，代码更可移植
target_compile_features(threadpool PUBLIC cxx_std_17)
```
`find_package` 有两种模式：`CONFIG` 模式找依赖自带的 `FooConfig.cmake`（vcpkg/Conan/自装库都提供），`MODULE` 模式找 CMake 自带的 `FindFoo.cmake`；统一使用导入目标 `Foo::Foo`，不写裸库名，例如 `find_package(Threads REQUIRED)` 后链接 `Threads::Threads`。`install` + `export` 让别人能 `find_package(threadpool)`，关键是 `NAMESPACE`、版本文件与 `find_dependency` 三件事；`ctest` 由 `include(CTest)` 启用，它定义 `BUILD_TESTING` 开关并生成 `CTestTestfile.cmake`，不 `include(CTest)` 就直接 `add_test`，`ctest` 会显示 0 个测试。

下面是**完整可用的 CMakeLists.txt**（多目录 + 库 + 可执行 + 测试），与第 8 节源码严格对应：
```cmake
# ===== 根 CMakeLists.txt =====
cmake_minimum_required(VERSION 3.16)
project(threadpool VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)              # 供 clangd / clang-tidy 使用
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE RelWithDebInfo CACHE STRING "Build type" FORCE)
endif()

find_package(Threads REQUIRED)

# 公共告警选项抽成 INTERFACE 目标，避免全局 add_compile_options 污染所有目标
add_library(project_warnings INTERFACE)
if(MSVC)
    target_compile_options(project_warnings INTERFACE /W4 /permissive- /utf-8)
else()
    target_compile_options(project_warnings INTERFACE -Wall -Wextra -Wpedantic -Wshadow -Wconversion)
endif()

# 核心库
add_library(threadpool STATIC src/thread_pool.cpp)
add_library(threadpool::threadpool ALIAS threadpool)
target_include_directories(threadpool
    PUBLIC  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
            $<INSTALL_INTERFACE:include>
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_compile_features(threadpool PUBLIC cxx_std_17)
target_link_libraries(threadpool PUBLIC Threads::Threads)
target_link_libraries(threadpool PRIVATE project_warnings)
# 示例可执行
add_executable(threadpool_demo examples/main.cpp)
target_link_libraries(threadpool_demo PRIVATE threadpool::threadpool)

# 测试
include(CTest)
if(BUILD_TESTING)
    add_subdirectory(tests)
endif()
# 安装与导出
include(GNUInstallDirs)
install(TARGETS threadpool EXPORT threadpoolTargets ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
install(EXPORT threadpoolTargets FILE threadpoolTargets.cmake NAMESPACE threadpool::
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/threadpool)
include(CMakePackageConfigHelpers)
configure_package_config_file(cmake/ThreadPoolConfig.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/threadpoolConfig.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/threadpool)
write_basic_package_version_file(${CMAKE_CURRENT_BINARY_DIR}/threadpoolConfigVersion.cmake
    VERSION ${PROJECT_VERSION} COMPATIBILITY SameMajorVersion)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/threadpoolConfig.cmake
              ${CMAKE_CURRENT_BINARY_DIR}/threadpoolConfigVersion.cmake
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/threadpool)
```
```cmake
# ===== cmake/ThreadPoolConfig.cmake.in =====
@PACKAGE_INIT@
include(CMakeFindDependencyMacro)
find_dependency(Threads)                 # 依赖必须在这里再写一遍
include("${CMAKE_CURRENT_LIST_DIR}/threadpoolTargets.cmake")
check_required_components(threadpool)
# ===== tests/CMakeLists.txt =====
add_executable(test_thread_pool
    test_thread_pool.cpp
    test_thread_pool_integration.cpp)
target_link_libraries(test_thread_pool
    PRIVATE threadpool::threadpool GTest::gtest_main project_warnings)
include(GoogleTest)
gtest_discover_tests(test_thread_pool DISCOVERY_TIMEOUT 30 PROPERTIES LABELS "unit")
# 集成测试：单独分组，cmake 3.22 起可用 TAGS 给 add_test 打标签
add_test(NAME integration.smoke COMMAND threadpool_demo --tasks 64) TAGS "integration"
```
`gtest_discover_tests` 在构建后扫描用例并逐个注册到 ctest，能单跑且失败信息精确到用例；`add_test` 只能把整个可执行文件当一个测试，`DISCOVERY_TIMEOUT` 在 Windows 上几乎必需。
```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build -j && ctest --test-dir build --output-on-failure -j4
cmake --install build --prefix /tmp/threadpool-stage
# 其它常用：ctest --test-dir build -N（列出用例）、-R ThreadPoolTest（正则筛选）、
#           --repeat until-fail:50（并发代码反复跑到首次失败）
```
用 `cmake --install` 而不是 `make install`，Windows 多配置生成器也一致。四种构建类型：`Debug`=`-g -O0`（调试、ASan），`Release`=`-O3 -DNDEBUG`（发布），`RelWithDebInfo`=`-O2 -g -DNDEBUG`（线上定位，推荐默认），`MinSizeRel`=`-Os -DNDEBUG`（体积敏感）。

## 3 依赖管理
C++ 没有官方包管理器，四种常见做法取舍差别很大：

| 方案 | 机制 | 优点 | 缺点 | 适用 |
| --- | --- | --- | --- | --- |
| vcpkg | `vcpkg.json` 清单模式 + 工具链注入 | 与 CMake 集成好、三元组/多平台 | 首次全量编译慢，CI 需缓存 | 团队统一环境 |
| Conan 2 | 独立包管理器 + `conanfile.py` | 二进制缓存成熟、可自建仓库 | 学习曲线，需生成 toolchain | 私有依赖、多团队共享 |
| FetchContent | 内置，下载源码随主工程编译 | 零额外工具、可 pin commit | 全量重编、离线需镜像 | 依赖少（<5 个） |
| Git Submodule | 仓库内嵌子模块 | 版本锁定直观、离线可读 | 克隆易出错 | 极小依赖、需改源码 |

选型建议：一两个依赖想零额外工具 → FetchContent；依赖 5 个以上、要 CI 与新人机器一致 → vcpkg 清单模式（`vcpkg.json` 入库并缓存安装目录）；需要私有二进制与多团队共享 → Conan 2；`third_party/` 放源码只适合「要改代码」或「许可证要求随源码分发」。FetchContent 引入 googletest 的最小示例：
```cmake
include(FetchContent)
FetchContent_Declare(
    googletest
    URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.tar.gz
    URL_HASH SHA256=8ad598c73ad796e0d8280b082cebd82a630d73e73cd3c70057938a6501bba5d7
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE)
set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)   # 不安装 googletest，只供本工程使用
set(BUILD_GMOCK OFF CACHE BOOL "" FORCE)     # 不用 gmock 时少编一半
FetchContent_MakeAvailable(googletest)
# 之后可直接：target_link_libraries(test_thread_pool PRIVATE GTest::gtest_main)
```
`FetchContent_MakeAvailable` 同时完成下载与 `add_subdirectory`。三个常见坑：不写 `URL_HASH` 就无法发现上游篡改；忘了关 `BUILD_GMOCK` 会多编一大批用例；需要增量更新时用 `GIT_REPOSITORY` + `GIT_TAG <commit>`。想「先找系统包，找不到再下载」就把 `find_package(... QUIET)` 放在前面。

## 4 代码规范
规范的目的不是审美，而是降低评审成本、让检查自动化。团队统一一套即可，关键是工具化：`clang-format` 管格式，`clang-tidy` 管语义。

| 主题 | Google C++ Style 要点 | 理由 |
| --- | --- | --- |
| 头文件 | 每个 `.cc/.cpp` 第一行包含自身头 | 立刻暴露头文件缺依赖 |
| 命名空间 | 小写、以项目为根，禁止 `using namespace` | 避免 ADL 冲突与隐式引入 |
| 命名 | 类型/函数 `PascalCase`，变量 `snake_case`，成员 `snake_case_`，常量 `kPascalCase` | 全局一致、易搜索 |
| 所有权 | 尽量 `unique_ptr` 表达独占，裸指针只做观察 | 资源生命周期可读 |
| 错误处理 | 入口统一校验，错误走返回值或 `optional` | 少用异常做控制流 |
| 行宽 | 80 列（Google）或 100 列（多数团队） | 评审与 diff 友好 |

`.clang-format`（基于 Google，放宽行宽并对齐指针）：
```yaml
BasedOnStyle: Google
Language: Cpp
Standard: c++17
ColumnLimit: 100
IndentWidth: 4
PointerAlignment: Left
DerivePointerAlignment: false
AllowShortFunctionsOnASingleLine: Empty
IncludeBlocks: Regroup
IncludeCategories:
  - Regex: '^"(threadpool)/'
    Priority: 1
  - Regex: '^<[a-z_]+>'
    Priority: 2
  - Regex: '.*'
    Priority: 3
FixNamespaceComments: true
```
`clang-tidy` 依赖 `compile_commands.json`（`CMAKE_EXPORT_COMPILE_COMMANDS=ON` 生成）：
```yaml
# .clang-tidy
Checks: >
  bugprone-*,
  performance-*,
  modernize-use-nullptr,
  modernize-use-emplace,
  readability-identifier-naming,
  -cppcoreguidelines-owning-memory
CheckOptions:
  - key: readability-identifier-naming.ClassCase
    value: CamelCase
  - key: readability-identifier-naming.PrivateMemberSuffix
    value: '_'
```

`clang-tidy -p build src/thread_pool.cpp`（`-p` 指向含 `compile_commands.json` 的构建目录）即可检查单个文件。
`bugprone-*` 找 `std::move` 之后的误用、悬垂引用、条件里赋值等真 bug；`performance-*` 找多余拷贝与大对象按值传参。别一上来全开，先把 `bugprone` + `performance` 打到零，再逐步加规则。命名约定（与第 8 节代码一致）：文件 `thread_pool.cpp`、类型 `ThreadPool`、方法 `Submit`、局部变量 `worker_count`、私有成员 `tasks_`、常量 `kDefaultWorkers`、命名空间 `threadpool`/`threadpool::detail`。

头文件顺序：自身头 → C 标准库 → C++ 标准库 → 第三方 → 本项目其他头，组间空行：
```cpp
#include "threadpool/thread_pool.hpp"   // 1. 自身头，第一行暴露缺失依赖

#include <condition_variable>           // 2. 标准库
#include <mutex>
#include <utility>

#include "detail/thread_pool_impl.hpp"  // 3. 本项目其他头
```
`#pragma once` 与头文件卫士都能防重复包含：前者按文件路径去重，一行搞定但非标准；后者按宏去重、标准可移植，但要维护唯一宏名（如 `THREADPOOL_THREAD_POOL_HPP_`），宏撞名会导致某个头被静默跳过。新项目首选 `#pragma once`，需要极致可移植或担心符号链接路径问题时用卫士，二者也可叠用。

## 5 单元测试
单元测试把行为固定下来：重构后几分钟内知道有没有回归，边界条件成为可执行文档。测试针对公开行为，不绑定内部实现。
```cpp
#include <atomic>
#include <vector>

#include "gtest/gtest.h"
#include "threadpool/thread_pool.hpp"

TEST(ThreadPoolTest, RunsEverySubmittedTask) {
    threadpool::ThreadPool pool(4);
    std::atomic<int> counter{0};
    for (int i = 0; i < 1000; ++i) {
        pool.Submit([&counter] { counter.fetch_add(1, std::memory_order_relaxed); });
    }
    pool.Stop();                                    // 等待队列清空并回收线程
    EXPECT_EQ(counter.load(), 1000);
}
TEST(ThreadPoolTest, RejectsSubmitAfterStop) {
    threadpool::ThreadPool pool(1);
    pool.Stop();
    EXPECT_FALSE(pool.Submit([] {}));               // bool 返回值便于断言
}
TEST(ThreadPoolTest, FuturesCarryResults) {
    threadpool::ThreadPool pool(2);
    std::vector<std::future<int>> futures;
    for (int i = 0; i < 8; ++i) futures.push_back(pool.SubmitTask([](int n) { return n * n; }, i));
    for (int i = 0; i < 8; ++i) {
        ASSERT_TRUE(futures[static_cast<size_t>(i)].valid());
        EXPECT_EQ(futures[static_cast<size_t>(i)].get(), i * i);
    }
}
// 测试夹具：每个用例独立构造/析构，避免用例间状态泄漏
class ThreadPoolFixture : public ::testing::Test {
protected:
    void SetUp() override { pool_ = std::make_unique<threadpool::ThreadPool>(2); }
    std::unique_ptr<threadpool::ThreadPool> pool_;
};
TEST_F(ThreadPoolFixture, WorkerCountIsRespected) {
    ASSERT_NE(pool_, nullptr);                      // 后续依赖 pool_，用 ASSERT 先确认
    EXPECT_EQ(pool_->WorkerCount(), 2u);
}
```

| 断言 | 失败行为 | 使用场景 |
| --- | --- | --- |
| `EXPECT_*` | 记录失败后继续执行 | 普通断言，优先使用 |
| `ASSERT_*` | 立即从当前函数返回 | 后续代码依赖该值（如指针非空） |
| `EXPECT_THROW` / `EXPECT_NO_THROW` | 检查是否抛异常 | 参数校验、构造失败 |
| `EXPECT_DEATH` | 子进程运行并检查崩溃 | 断言 `assert`/未定义行为，慎用 |

`TEST_F` 只能配合同一个夹具类，`TEST` 是独立用例；`ASSERT_*` 在 `EXPECT_*` 之前用于保护后续解引用，否则断言失败后继续解空指针会掩盖真实错误。链接 `GTest::gtest_main` 会自动提供 `main` 并调用 `InitGoogleTest`，无需手写。Catch2 的等价写法（v3 需要 `catch2::catch2_main` 或 `CATCH_CONFIG_MAIN`）：
```cpp
#include <catch2/catch_test_macros.hpp>
#include "threadpool/thread_pool.hpp"

TEST_CASE("ThreadPool executes tasks", "[threadpool][unit]") {
    threadpool::ThreadPool pool(2);
    int sum = 0;
    for (int i = 1; i <= 10; ++i) pool.Submit([&sum, i] { sum += i; });
    pool.Stop();
    REQUIRE(sum == 55);
    SECTION("after stop, submit fails") { REQUIRE_FALSE(pool.Submit([] {})); }
}
```
Catch2 更接近自然语言，`REQUIRE` 失败终止当前 `SECTION`、`CHECK` 继续；宏会把表达式展开多次，带副作用的调用不要写进断言。接入 ctest 与测试分层：`ctest --test-dir build -N` 列出发现的用例，`-R ThreadPoolTest` 正则筛选，`-L unit` 按标签分层，`--repeat until-fail:50` 反复跑到首次失败——对线程池几乎必选，单次通过不代表没有竞态。分层上：单元测试单线程、毫秒级，验证 `Submit` 返回值、`Stop` 幂等、任务异常不外抛；集成测试多线程 + 真实规模（如 10 万任务全完成），带 `TIMEOUT` 并在 ASan/TSan 构建里再跑；基准测试单独目标，不进默认 `ctest`，避免 CI 抖动。覆盖率：
```bash
cmake -S . -B build-cov -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_FLAGS="--coverage -O0 -g"
cmake --build build-cov -j && ctest --test-dir build-cov --output-on-failure
gcovr -r . build-cov --exclude tests/ --fail-under-line 80 --html-details build-cov/cov.html
lcov --capture --directory build-cov --output-file build-cov/coverage.info --rc branch_coverage=1
genhtml build-cov/coverage.info --output-directory build-cov/html
```
`gcov` 看单文件行覆盖，`gcovr` 一行给出 CI 门槛，`lcov/genhtml` 出可视化报告。`--coverage` 必须同时加在编译和链接上，否则缺 `__gcov_*` 符号；覆盖率构建要关优化，否则行号错乱；别为凑数字写无意义用例。

## 6 调试与排错
排错顺序固定下来能少走弯路：先让告警清零（`-Wall -Wextra -Wpedantic`，CI 加 `-Werror`），再用 Sanitizer 定位，最后才进调试器猜。

gdb 常用命令：

| 命令 | 作用 | 备注 |
| --- | --- | --- |
| `run` / `r` | 启动程序，可带参数 | `r --tasks 8` |
| `break f` / `b f:12` | 函数或行号断点 | `b threadpool::ThreadPool::Submit` |
| `bt` / `bt full` | 调用栈 / 含局部变量 | `bt 10` 只看最近 10 层 |
| `frame N` / `f N` | 切换栈帧 | 再 `p` 查该层变量 |
| `next` / `n`、`step` / `s`、`finish` | 单步 / 进入 / 返回调用层 | `finish` 会打印返回值 |
| `p expr`、`p/x`、`p/d` | 打印表达式与进制 | `p *ptr`、`p tasks_.size()` |
| `info threads` / `thread N` | 列出全部线程 / 切到第 N 个线程 | 切换后需重新 `bt` |
| `x/16xb ptr` | 按字节抽查内存 | `x/4gx` 看指针数组 |
| `info vtbl obj` | 查看虚表与虚函数地址 | 排查「析构不虚」「调错重载」 |
| `watch var` / `display var` | 数据断点 / 每次停下自动打印 | 抓无锁竞态 |
| `thread apply all bt` | 所有线程打印调用栈 | 多线程崩溃必做 |

```bash
gdb -q --args ./build/threadpool_demo --tasks 8
(gdb) break threadpool::ThreadPool::Submit
(gdb) run
(gdb) bt
(gdb) frame 1
(gdb) p *pool
(gdb) info vtbl *pool
(gdb) info threads
(gdb) thread 3
(gdb) thread apply all bt
(gdb) x/8gx pool
```
`p std::string` 常只显示内部指针，要看内容用 `p s.c_str()`；指针为野指针时报 `Cannot access memory`，先看 `bt` 判断栈是否被破坏。valgrind 与 Sanitizer：
```bash
valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./build/threadpool_demo --tasks 8
valgrind --tool=helgrind ./build/threadpool_demo    # 竞争检查（helgrind 与 drd 都用于并发，误报比 TSan 多）
valgrind --tool=massif ./build/threadpool_demo      # 堆内存峰值
# AddressSanitizer：越界、UAF、double free、泄漏
g++ -std=c++17 -g -O1 -fno-omit-frame-pointer -fsanitize=address -Iinclude \
    src/thread_pool.cpp examples/main.cpp -o build/demo_asan -pthread
# UBSan：有符号溢出、空指针、移位、对齐、vptr 损坏
g++ -std=c++17 -g -O1 -fsanitize=undefined -fno-sanitize-recover=all -Iinclude \
    src/thread_pool.cpp examples/main.cpp -o build/demo_ubsan -pthread
# TSan：数据竞争
g++ -std=c++17 -g -O1 -fsanitize=thread -Iinclude \
    src/thread_pool.cpp examples/main.cpp -o build/demo_tsan -pthread
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 ./build/demo_asan --tasks 8
UBSAN_OPTIONS=print_stacktrace=1 ./build/demo_ubsan --tasks 8
TSAN_OPTIONS=second_deadlock_stack=1:halt_on_error=1 ./build/demo_tsan --tasks 8
```

| Sanitizer | 捕获问题 | 主要限制 |
| --- | --- | --- |
| address | 堆/栈/全局越界、UAF、double free | 内存 2~3 倍开销，不能与 TSan 共存 |
| undefined | 有符号溢出、移位、空解引用、vptr | 不检查越界，需配 ASan |
| thread | 数据竞争、锁顺序反转 | 不能与 ASan 共存，可能漏报 |
| leak | 不可达内存泄漏 | 只报可达性，逻辑泄漏查不到 |

valgrind 不用重编但慢 10~50 倍，且**不能与 ASan/TSan 同开**。ASan 与 TSan 必须编成两个独立目标、用两套 ctest 配置分别跑；`-fno-sanitize-recover=all` 让 UBSan 直接失败，否则 CI 会静默通过。

`-g -O0` 与 `-g -O2` 的差别在调试时非常具体：

| 对比项 | `-g -O0` | `-g -O2`（RelWithDebInfo） |
| --- | --- | --- |
| 变量值 | 与源码一一对应，`p` 准确 | 变量被寄存器化/复用，常显示 `<optimized out>` |
| 单步 | 严格按行 | 语句乱序、循环展开，跳行严重 |
| 内联 | 无 | 小函数被内联，`bt` 看不到中间层 |
| 适用 | 定位逻辑 bug、写测试 | 只在优化后出现的 bug、线上 core |

因为以上差异，Valgrind 会误报优化后代码的 `Conditional jump ... uninitialised`（寄存器复用造成），排查时应切换到 `-O0` 版本复核。规则：能用 `-O0` 复现就在 `-O0` 查；只在 `-O2` 出现的 bug（典型是 UB、竞态、少一次拷贝暴露的生命周期问题）就留在 `-O2 + -g`，配合 `p/x` 看内存并在 `-O2` 上再跑一遍 ASan/UBSan。永远不要用无 `-g` 的 Release 二进制分析线上 core。core dump 分析：
```bash
ulimit -c unlimited
cat /proc/sys/kernel/core_pattern          # 例如 core.%e.%p 或 systemd-coredump 管道
./build/threadpool_demo --tasks 100000     # 复现崩溃
gdb ./build/threadpool_demo core.12345
(gdb) bt
(gdb) frame 2
(gdb) info locals
(gdb) p *this
(gdb) thread apply all bt                  # 看其他线程是否持锁
```
崩溃线程往往只是受害者，死锁/竞态证据常在别的线程，所以 `thread apply all bt` 是必备。栈损坏时 `bt` 会出现 `??`，加 `-fstack-protector-strong` 并回 ASan 版本复现。定位后回答三件事：哪一行、哪个对象生命周期错、同类路径还有没有。

## 7 性能与优化
优化顺序固定为：**算法 → 数据结构 → 内存布局 → 编译选项 → 微优化**。算法层面把 O(n²) 换成 O(n log n) 或哈希通常 10 倍起；数据结构上 `std::vector` 代替 `std::list`（缓存友好）、减少 `std::map` 指针跳转、`reserve` 预留容量；内存布局上冷热字段拆分、SoA 替代 AoS，减少随机指针追逐；编译选项用 `-O2/-O3`、LTO、PGO，`-march=native` 只能用于本机；最后才是手动内联、去虚调用、`string_view`。

过早优化是明确的反模式：没测量就假设瓶颈，时间花在 1% 的路径上，还牺牲可读性。正确流程是「先基准 → 有 profile → 只改热点 → 用同一基准验证」，且基准必须在 `-O2` 下跑。perf 与火焰图：
```bash
perf record -F 999 -g --call-graph dwarf ./build/threadpool_demo --tasks 1000000
perf report --stdio | head -n 40
perf stat -e cycles,instructions,cache-misses,branch-misses ./build/threadpool_demo
# 生成火焰图（需 FlameGraph 仓库）
perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl \
    --title "threadpool" > build/flame.svg
```
读火焰图三条：宽度=占用时间，看最宽的块而非最深的块；自下而上是调用者到被调用者；顶部平顶说明时间在叶子函数（计算密集），宽而浅通常是调用次数多。若大量时间落在 `std::mutex::lock` 或内核 `futex`，说明瓶颈是锁竞争，应减小临界区或分片队列，而不是调编译选项。

`std::chrono` 基准要用 `steady_clock`（单调时钟，不受校时影响），且多轮取中位数：
```cpp
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <vector>

template <typename Fn>
double MeasureMs(Fn&& fn, int rounds = 5) {          // 多轮取中位数，削掉调度噪声
    std::vector<double> samples;
    for (int r = 0; r < rounds; ++r) {
        const auto start = std::chrono::steady_clock::now();
        fn();
        const auto end = std::chrono::steady_clock::now();
        samples.push_back(std::chrono::duration<double, std::milli>(end - start).count());
    }
    std::sort(samples.begin(), samples.end());
    return samples[samples.size() / 2];
}

int main() {
    std::printf("push_back: %.3f ms\n", MeasureMs([] {
        std::vector<int> v;
        for (int i = 0; i < 1000000; ++i) v.push_back(i);
    }));
    std::printf("reserve:   %.3f ms\n", MeasureMs([] {
        std::vector<int> v;
        v.reserve(1000000);
        for (int i = 0; i < 1000000; ++i) v.push_back(i);
    }));
}
# 单次耗时小于 1 ms 时噪声占主导，应放大迭代次数；基准数字只在本机本编译器下可比
```
需要更严谨的数据时用 google-benchmark（框架自动校准迭代次数、`DoNotOptimize` 防止结果被优化掉）：
```cpp
#include <benchmark/benchmark.h>
#include <vector>

static void BM_VectorPushBack(benchmark::State& state) {
    for (auto _ : state) {                           // 框架自动决定循环次数
        std::vector<int> v;
        v.reserve(static_cast<size_t>(state.range(0)));
        for (int i = 0; i < state.range(0); ++i) v.push_back(i);
        benchmark::DoNotOptimize(v.data());          // 防止整个循环被优化掉
    }
    state.SetComplexityN(state.range(0));
}
BENCHMARK(BM_VectorPushBack)->RangeMultiplier(4)->Range(1 << 10, 1 << 20);
BENCHMARK_MAIN();

// 命令行：g++ -std=c++17 -O2 -DNDEBUG bench.cpp -lbenchmark -lpthread -o build/bench
//         ./build/bench --benchmark_repetitions=5 --benchmark_report_aggregates_only=true
```

## 8 案例：线程池 + 任务队列
目标：C++17 线程池库，固定 N 个工作线程从任务队列取 `std::function<void()>` 执行；提供 `Submit`（无返回值）与 `SubmitTask`（返回 `future`），`Stop` 幂等地结束并回收全部线程。核心组件是 `std::mutex` + `std::condition_variable` + `std::function` + `std::vector<std::thread>`。完整工程结构（`include/`、`src/`、`tests/`、`cmake/`、`examples/`）见第 1 节，构建脚本见第 2 节。
```cpp
// include/threadpool/thread_pool.hpp
#pragma once

#include <condition_variable>
#include <cstddef>
#include <functional>
#include <memory>
#include <queue>
#include <thread>
#include <tuple>
#include <type_traits>
#include <utility>
#include <vector>

namespace threadpool {
class ThreadPool {
public:
    explicit ThreadPool(std::size_t worker_count = std::thread::hardware_concurrency());
    ~ThreadPool();
    ThreadPool(const ThreadPool&) = delete;              // 互斥量与线程都不可拷贝
    ThreadPool& operator=(const ThreadPool&) = delete;
    ThreadPool(ThreadPool&&) = delete;
    ThreadPool& operator=(ThreadPool&&) = delete;

    bool Submit(std::function<void()> task);             // 已停止时返回 false
    template <typename Fn, typename... Args>
    std::future<std::invoke_result_t<std::decay_t<Fn>, std::decay_t<Args>...>>
    SubmitTask(Fn&& fn, Args&&... args) {
        using Result = std::invoke_result_t<std::decay_t<Fn>, std::decay_t<Args>...>;
        auto bound = [f = std::forward<Fn>(fn),
                      tup = std::make_tuple(std::forward<Args>(args)...)]() mutable {
            return std::apply(std::move(f), std::move(tup));
        };
        // C++17 没有 move_only_function，用 shared_ptr 转移所有权给队列
        auto task = std::make_shared<std::packaged_task<Result()>>(std::move(bound));
        std::future<Result> future = task->get_future();
        if (!Submit([task] { (*task)(); })) return std::future<Result>();
        return future;
    }

    void Stop();                                          // 幂等：已入队任务执行完再退出
    std::size_t PendingCount() const;
    std::size_t WorkerCount() const noexcept { return worker_count_; }

private:
    friend void WorkerLoop(ThreadPool* pool);             // 见本节末尾说明
    void JoinAll();
    const std::size_t worker_count_;
    mutable std::mutex mutex_;
    std::condition_variable cv_;
    std::queue<std::function<void()>> tasks_;
    std::vector<std::thread> workers_;
    bool stopping_ = false;
};
}  // namespace threadpool
```
实现文件把 worker 循环放在**具名**命名空间里（不能放匿名命名空间，否则无法作为友元被访问）：
```cpp
// src/thread_pool.cpp
#include "threadpool/thread_pool.hpp"

#include <algorithm>
#include <cstdio>
#include <exception>
#include <system_error>
#include <utility>

namespace threadpool {
void WorkerLoop(ThreadPool* pool) {
    for (;;) {
        std::function<void()> task;
        {
            std::unique_lock<std::mutex> lock(pool->mutex_);
            pool->cv_.wait(lock, [pool] { return pool->stopping_ || !pool->tasks_.empty(); });
            if (pool->stopping_ && pool->tasks_.empty()) return;   // 停止且队列空：退出
            task = std::move(pool->tasks_.front());
            pool->tasks_.pop();
        }
        try {
            task();                                             // 锁外执行，避免串行化
        } catch (const std::exception& e) {
            std::fprintf(stderr, "[threadpool] task threw: %s\n", e.what());
        } catch (...) {
            std::fprintf(stderr, "[threadpool] task threw unknown exception\n");
        }
    }
}
ThreadPool::ThreadPool(std::size_t worker_count)
    : worker_count_(std::max<std::size_t>(worker_count, 1)) {   // hardware_concurrency 可能是 0
    workers_.reserve(worker_count_);
    try {
        for (std::size_t i = 0; i < worker_count_; ++i) {
            workers_.emplace_back([this] { WorkerLoop(this); });
        }
    } catch (const std::system_error&) {                       // 建线程失败：收尾后抛出，
        { std::lock_guard<std::mutex> lock(mutex_); stopping_ = true; }   // 构造失败必须抛
        cv_.notify_all();
        JoinAll();
        throw;
    }
}
ThreadPool::~ThreadPool() { Stop(); }                           // 析构必须收尾，不依赖使用者

bool ThreadPool::Submit(std::function<void()> task) {
    if (!task) return false;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (stopping_) return false;
        tasks_.push(std::move(task));                           // 移动而非拷贝
    }
    cv_.notify_one();                                           // 锁外通知，减少无谓唤醒
    return true;
}
void ThreadPool::Stop() {
    { std::lock_guard<std::mutex> lock(mutex_); stopping_ = true; }
    cv_.notify_all();
    JoinAll();
}
std::size_t ThreadPool::PendingCount() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return tasks_.size();
}
void ThreadPool::JoinAll() {
    for (auto& worker : workers_) {
        if (worker.joinable() && worker.get_id() != std::this_thread::get_id()) worker.join();
    }
}
}  // namespace threadpool
```
`WorkerLoop` 是 `threadpool::` 下的非成员函数，靠头文件里的 `friend void WorkerLoop(ThreadPool*);` 访问私有成员，又不在公共头里暴露成 API。不想用友元就把它改成 `ThreadPool` 的 `static` 私有成员函数、在 `.cpp` 中定义，取舍是「少一个成员声明」与「不多暴露一个自由函数」。
```cpp
// examples/main.cpp（--tasks 个数由参数决定，未给默认 16）
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <future>
#include <vector>

#include "threadpool/thread_pool.hpp"

int main(int argc, char** argv) {
    int n = 16;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--tasks") == 0 && i + 1 < argc) n = std::atoi(argv[++i]);
    }
    if (n <= 0) { std::fprintf(stderr, "usage: %s [--tasks N]\n", argv[0]); return 1; }

    threadpool::ThreadPool pool;                     // 默认 hardware_concurrency 个线程
    std::vector<std::future<long long>> futures;
    futures.reserve(static_cast<std::size_t>(n));
    for (int i = 0; i < n; ++i) {
        futures.push_back(pool.SubmitTask([](int x) {
            long long sum = 0;
            for (int k = 1; k <= x; ++k) sum += k;
            return sum;
        }, n));
    }
    long long total = 0;
    for (auto& f : futures) {
        if (f.valid()) total += f.get();              // get() 会传播任务内异常
    }
    std::printf("tasks=%d workers=%zu total=%lld\n", n, pool.WorkerCount(), total);
    return 0;                                         // ~ThreadPool -> Stop -> join
}
// 构建运行：cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo
//           cmake --build build -j && ./build/threadpool_demo --tasks 64
// 8 核机器输出：tasks=64 workers=8 total=...（--tasks 缺省为 16）
```
设计取舍：

| 决策 | 选择 | 备选与代价 |
| --- | --- | --- |
| 任务类型 | `std::function<void()>` | 模板化 `enqueue` 少一次类型擦除但会膨胀代码；C++17 无 `move_only_function`，只能靠 `shared_ptr<packaged_task>` 转移 |
| 队列 | `std::queue` + `std::mutex` | 无锁队列适合高并发，但 ABA/内存回收极难，先用锁保证正确 |
| 唤醒 | `notify_one`，尽量在锁外 | 锁内通知会让被唤醒线程立刻又阻塞在锁上 |
| 停止语义 | 已入队任务跑完再退出 | 立刻丢弃需额外协议通知等待方，易出 future 永不就绪 |
| 异常 | worker 内捕获，`packaged_task` 把异常存进 future | 让异常逃出线程会直接 `std::terminate` |
| 线程数 | 默认 `hardware_concurrency()`，0 时回落 1 | 该函数可能返回 0，必须兜底 |
可扩展方向：`WaitIdle()`、任务优先级、定时任务、每线程私有队列减少争抢、C++20 `std::jthread` 自动 join。面试时主动说一句「当前是无界队列，提交长期快于消费会撑爆内存，生产版要加背压或限流」，比假装完美更可信。

## 9 面试怎么答项目题
项目题不是复述代码，而是证明你能在约束下做决策。用 STAR 组织，控制在一分半到两分钟，先给结论再给证据：Situation（图像处理管线，8 核，单帧 200 个可并行子任务）→ Task（P95 从 90 ms 降到 40 ms，线程数固定避免频繁创建）→ Action（固定工作线程 + 任务队列，`std::function` 统一入口，worker 内捕获异常）→ Result（P95 降到 42 ms，CPU 利用率 65%→88%，无界队列仍是风险）。
讲 C++ 特性时一律绑定「它解决了项目里的什么具体问题」，而不是背特性定义：
1. **RAII 管理资源**：「析构里调 `Stop()` 再 `join`，锁一律用 `lock_guard`/`unique_lock`，所以任何提前 `return` 或抛异常都不会漏锁、漏线程。早期手写 `mutex.lock()` 因为一个异常路径漏解锁死锁过。」
2. **智能指针**：「`packaged_task` 要同时被队列和 `future` 持有，用 `shared_ptr` 表达共享所有权；`ThreadPool` 本身禁用拷贝，避免两个对象操作同一个队列；测试夹具用 `unique_ptr` 独占资源。」
3. **移动语义减少拷贝**：「`tasks_.push(std::move(task))` 把 `std::function` 的捕获移入队列，`std::apply(std::move(f), std::move(tup))` 同理，压测里省掉的一次深拷贝让总耗时降了约 [X]%。」
4. **模板与完美转发**：「`SubmitTask` 用 `std::invoke_result_t` 推导返回类型、`std::decay_t` 消掉引用，调用方不写 `std::function` 也能拿到 `future`——复杂度和类型擦除开销都被挡在库内部。」

三个可套用的量化模板：
1. **延迟型**：「在 [规模/硬件] 下，[操作] 的 P95 从 [A] ms 降到 [B] ms（约 -X%）；用 [perf/benchmark] 连测 3 轮，瓶颈从 [函数] 转移；代价是 [内存/复杂度] 上升。」
2. **吞吐/并发型**：「[服务] 的 QPS 从 [A] 提升到 [B]（约 +X%），P99 保持在 [C] ms 内；关键动作是 [固定线程池/减小临界区/批量提交]，CPU 利用率 [D]%；代价是 [队列积压风险]。」
3. **资源型**：「峰值 RSS 从 [A] MB 降到 [B] MB（约 -X%），冷启动从 [C] s 降到 [D] s；做法是 [换数据结构/延迟加载/支持移动]；用 [valgrind massif/ASan 泄漏报告] 验证，代价是 [首次访问变慢]。」

再准备两个「翻车点」：一次数据竞争如何被 TSan 抓到（例如误以为 `stopping_` 不加锁也安全）、一次链接错误如何定位（模板定义放 `.cpp` 导致 `undefined reference`，见第 10.3 节）。能讲清失败和修复，比只讲成功更能证明工程能力。

## 10 常见工程坑
### 10.1 ODR 违反
ODR（One Definition Rule）要求类、函数、模板在每个翻译单元中只有一个定义，且不同翻译单元的定义必须**逐 token 相同**。最常见的违规是头文件里的内联函数依赖影响语义的宏：库以 `-DNDEBUG` 编译、应用以 Debug 编译时，`#ifdef NDEBUG` 会让两份 `Foo::Check` 定义不同，链接器随机选一个，行为不可预测且不报错。规则：**头文件中的内联定义不得依赖会影响语义的宏**，需要条件编译就放进 `.cpp`，或改用 pimpl 隔离；另一个变体是头文件里定义 `static`/匿名命名空间的 `const` 对象，每个翻译单元一份，取地址后指针必然不相等。
### 10.2 头文件循环包含
`a.hpp` 包含 `b.hpp`，`b.hpp` 又包含 `a.hpp`，第二次包含被 `#pragma once` 挡住，于是 `b.hpp` 用到的 `A` 类型缺失，报「未知类型」。四种修法：

| 修法 | 做法 | 适用 |
| --- | --- | --- |
| 前向声明 | `class B;` 后用 `B*`/`B&` | 只用到指针、引用、参数、返回值 |
| 抽出公共头 | 把互相依赖的类型/枚举移到 `common.hpp` | 两边都要完整定义 |
| pimpl | 头里只留 `struct Impl; std::unique_ptr<Impl> impl_;` | 隐藏实现、稳定 ABI |
| 只在 `.cpp` 包含 | 实现文件里 include 对方头 | 仅成员函数内部使用 |

```cpp
// b.hpp —— 前向声明即可，不要 #include "a.hpp"
#pragma once
class A;                                   // 只声明
class B {
public:
    void Use(A& a);
};
```
pimpl 要注意：`unique_ptr<Impl>` 的析构必须在使用它的 `.cpp` 里定义（头里只写 `~Foo();`，实现文件写 `Foo::~Foo() = default;`），否则包含处看到不完整类型，`delete` 的实例化会失败。

### 10.3 模板定义的链接问题
模板不是代码而是「配方」，只有实例化才生成机器码。定义放 `.cpp` 时，另一个翻译单元用 `Stack<int>` 看不到定义，链接器报 `undefined reference to 'Stack<int>::Push(int const&)'`。正确做法是把定义与声明一起放头文件：
```cpp
// stack.hpp —— 声明与定义同在头文件；模板成员函数/友元定义放 .cpp 属于同一类错误
#pragma once
#include <vector>

template <typename T>
class Stack {
public:
    void Push(const T& v) { data_.push_back(v); }
    std::size_t Size() const { return data_.size(); }
private:
    std::vector<T> data_;
};
// 必须隐藏实现时：.cpp 里写 template class Stack<int>;，头文件末尾写
// extern template class Stack<int>; 抑制其他单元重复实例化，代价是 T 必须在编译期固定
```

### 10.4 `inline` 变量
C++17 的 `inline` 变量把「每个翻译单元一份」变成「全程序唯一一份」，是头文件里定义常量和静态成员的正确姿势：

```cpp
// settings.hpp —— C++17 正确做法
#pragma once
#include <string>

inline constexpr int kMaxWorkers = 64;               // 头文件定义常量，取地址处处相同
inline const std::string kDefaultName = "default";   // 需要非字面量类型时同样用 inline

class Config {
public:
    static inline int instance_count = 0;            // 静态成员就地定义
};
// 对比 static const int kMaxWorkers = 64;：每个翻译单元各一份、地址不同，且不能是 std::string
```

### 10.5 静态初始化顺序问题
不同翻译单元的全局对象构造顺序未定义：`registry.cpp` 里的 `g_registry` 可能在 `logger.cpp` 的 `g_logger` 之前构造，构造函数里调用 `g_logger` 就可能在未构造的对象上操作而崩溃。修法：用 **Meyers 单例**把初始化推迟到首次调用（函数内静态变量，C++11 起线程安全）——`Logger& GetLogger() { static Logger instance; return instance; }`；同时尽量避免全局可变状态，把依赖作为构造参数显式传入，只读常量用 `constexpr` 在编译期求值。延迟初始化有每次一次原子检查的开销，热路径上应缓存引用。

### 10.6 ABI 兼容
ABI 兼容指「按旧头文件编译的二进制能链接并运行新版本的库」。C++ 没有标准 ABI，以下改动会**破坏兼容**：

| 改动 | 破坏 ABI | 说明 |
| --- | --- | --- |
| 新增非虚成员函数 | 否 | 符号新增，不影响布局 |
| 增删或重排数据成员 | 是 | 对象大小与偏移全变 |
| 增删虚函数 | 是 | 虚表布局变 |
| 改函数签名/参数类型 | 是 | mangled name 变 |
| 改变量是否 `inline` | 是 | 符号定义数量与链接语义变 |
| 换编译器/标准库/`_GLIBCXX_USE_CXX11_ABI` | 是 | 同一符号不同实现 |
实践：对外库用 pimpl + 稳定接口，版本号与 `SONAME` 走 `libfoo.so.1.2.3`（`SameMajorVersion` 表示同 major 保证兼容）；用 `abi-compliance-checker`/`abi-dumper` 对比新旧版本并纳入 CI。混用 Debug/Release 的 STL（`std::string` 布局不同）或 GCC4/GCC5 ABI 的双编译库，会在运行时出现极难定位的崩溃，属于最坑的一类问题。
