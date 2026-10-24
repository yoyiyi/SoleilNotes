## 1 一个 C 项目的目录长什么样
「做过项目」不是写过一个 `main.c`，而是能把源码、公开头文件、测试、第三方依赖和构建产物分开，让别人一条命令就能编译、测试和清理。下面这个布局适用于中小型 C 项目，第 9 节的词频工具直接套用。
```text
wordcount/
├── src/              # main.c、wordcount.c
├── include/          # wordcount.h（对外头文件）
├── tests/            # test_wordcount.c
├── third_party/      # unity/（固定版本并保留 LICENSE）
├── build/            # 编译产物，整目录可删除
├── Makefile
├── CMakeLists.txt
├── README.md
├── LICENSE
└── .gitignore
```

| 路径 | 职责 | 不该放什么 |
| --- | --- | --- |
| `src/` | 只放 `.c` 实现和程序入口 | 公共头文件、生成文件 |
| `include/` | 对调用方暴露的 `.h`，可随库安装 | 内部私有头、第三方头 |
| `tests/` | 单元测试、夹具和测试数据 | 生产逻辑 |
| `third_party/` | Unity、CMocka 等源码，锁定版本 | 自己写的业务代码 |
| `build/` | 编译器和 CMake 生成的一切 | 任何要提交的源码 |

1. `README.md` 写清依赖、构建命令、运行示例、测试命令、目录说明和许可证；面试官常追问「换台机器怎么跑」。
2. `LICENSE` 明确授权方式；第三方目录保留原始许可证，避免授权冲突。
3. `.gitignore` 忽略 `build/`、`*.o`、`*.a`、`*.so`、`*.d`、`compile_commands.json` 和覆盖率文件；构建产物不入库。

## 2 编译单个文件与多个文件
`gcc -c` 只做预处理、编译和汇编，产出可重定位目标文件 `.o`，外部符号尚未解析。多文件项目先把每个翻译单元编成 `.o`，再统一链接；改一个 `.c` 只需重编一个 `.o`。
```bash
mkdir -p build
gcc -std=c11 -Wall -Wextra -Iinclude -c src/wordcount.c -o build/wordcount.o
gcc -std=c11 -Wall -Wextra -Iinclude -c src/main.c -o build/main.o
gcc build/main.o build/wordcount.o -o build/wordcount
nm build/main.o          # U wc_count_file 表示等待链接器解析
```
链接顺序遵循「使用者在前、被依赖者在后」：目标文件在前，库在后；`liba` 依赖 `libb` 就写 `-la -lb`。链接器从左到右扫描，扫描到 `-la` 时才把其中未解析的符号拉进来，顺序反了会报 `undefined reference`。循环依赖可临时用 `-Wl,--start-group ... -Wl,--end-group`，但优先重构依赖。

| 选项 | 作用 | 示例与注意点 |
| --- | --- | --- |
| `-I` | 增加头文件搜索目录（预处理） | `-Iinclude` |
| `-L` | 增加库搜索目录（链接） | `-Lbuild`，不改变运行时搜索 |
| `-l` | 指定库名，自动补 `lib` 和 `.a`/`.so` | `-lwordcount` |
| `-D` | 命令行定义宏 | `-DDEBUG=1` 等价于 `#define DEBUG 1` |
| `-U` | 取消宏定义 | `-UDEBUG`；后面的 `-D`/`-U` 覆盖前面的 |
| `-Wl,-rpath,...` | 透传参数给链接器 | `-Wl,-rpath,'$ORIGIN/../lib'` |

`-DDEBUG` 等价于 `-DDEBUG=1`，但 `-DDEBUG=0` 仍是「已定义」，`#ifdef DEBUG` 依旧为真，按值判断要写 `#if DEBUG`。发布版常用 `-DNDEBUG` 关掉 `assert`，调试版保留 `-g -O0`。

头文件里不能定义变量，这是 C 项目最经典的链接错误。被两个 `.c` 包含时，每个翻译单元都会产生一次定义：
```c
/* counter.h —— 错误：每个包含者都定义一次 */
int g_count;
/* counter.h —— 正确：只声明，在 counter.c 中写 int g_count = 0; */
extern int g_count;
```
C 没有 C++ 的 ODR 术语，但链接层面同样要求全局符号全程序唯一。GCC 10 起默认 `-fno-common`，两个 `.o` 都有 `g_count` 会直接报 `multiple definition`（重定义）；更早的 `-fcommon` 会把未初始化的 tentative definition 合并，看似能链接，却可能掩盖错误。C 中文件作用域的 `const int N = 10;` 也是外部链接，同样不能放头文件；常量用 `enum`、`#define` 或 `static const`。头文件可以放类型、宏、函数原型、`extern` 声明和 `static inline` 函数，普通函数定义放进去也会重复定义。

## 3 静态库与动态库
静态库是 `.o` 的归档，链接时只把被引用到的成员复制进可执行文件；共享库在链接时只记录依赖，运行时由动态链接器加载。两者部署模型完全不同。
```bash
ar rcs build/libwordcount.a build/wordcount.o
gcc build/main.o build/libwordcount.a -o build/wordcount_static
gcc -shared -fPIC -std=c11 -Iinclude src/wordcount.c -o build/libwordcount.so
gcc build/main.o -Lbuild -lwordcount -Wl,-rpath,'$ORIGIN' -o build/wordcount
```
`ar rcs` 的 `r` 是替换/插入、`c` 是创建、`s` 是写索引（相当于随后跑 `ranlib`）。共享库必须用 `-fPIC` 生成位置无关代码；静态库不要求，但同一批对象复用时可统一加。若同时存在 `libfoo.a` 和 `libfoo.so`，`-lfoo` 默认选 `.so`；强制静态用 `-Wl,-Bstatic -lfoo -Wl,-Bdynamic` 或直接写 `.a` 路径。生产共享库还应设置 `SONAME` 并保留版本软链接，例如 `-Wl,-soname,libwordcount.so.1`。

| 对比项 | 静态库 `.a` | 动态库 `.so` |
| --- | --- | --- |
| 链接时 | 复制用到的 `.o` 进可执行文件 | 只记录 `NEEDED` 依赖 |
| 运行时 | 不依赖库文件 | 动态链接器必须能找到 `.so` |
| 体积 | 可执行文件大，多程序重复 | 库可共享，程序本身小 |
| 升级 | 必须重新链接 | 替换 `.so` 即可，注意 ABI 兼容 |
| 部署 | 简单，单文件可跑 | 需要安装库或配置搜索路径 |

排查依赖常用：
```bash
nm -C build/libwordcount.a | grep ' T '   # 静态库中的全局函数
nm -D build/libwordcount.so               # 动态符号表
ldd build/wordcount                       # 运行时依赖；勿对不可信程序执行
readelf -d build/wordcount | grep -E 'NEEDED|RPATH|RUNPATH'
```
`nm` 中 `T` 是全局代码、`t` 是 `static` 局部代码、`U` 是未定义，`D/B/R` 分别是已初始化数据、BSS、只读数据。`ldd` 会让动态加载器报告依赖，对不明二进制有风险；`readelf -d` 只读 ELF 头，更安全。

运行时找不到 `.so` 的三种解决办法：

| 方法 | 命令 | 适用与代价 |
| --- | --- | --- |
| 环境变量 | `LD_LIBRARY_PATH=$PWD/build ./build/wordcount` | 临时调试；setuid 程序会忽略它 |
| 写入 rpath | 链接时 `-Wl,-rpath,'$ORIGIN/../lib'` | 随二进制发布；`$ORIGIN` 是可执行文件目录，Makefile 中写 `$$ORIGIN` |
| 系统缓存 | 装入 `/usr/local/lib`，在 `/etc/ld.so.conf.d/` 加配置后 `sudo ldconfig` | 全局安装；需要 root，换库后重新执行 |

`readelf -d` 中 `RPATH` 与 `RUNPATH` 的优先级不同：有 `RUNPATH` 时 `LD_LIBRARY_PATH` 优先于它，而旧式 `RPATH` 在 `LD_LIBRARY_PATH` 之前。安装后用 `ldconfig -p | grep wordcount` 验证缓存。

## 4 Makefile
Makefile 的三要素是目标（target）、依赖（prerequisites）、命令（recipe）。Make 递归比较修改时间，依赖比目标新或目标不存在时才执行命令，这就是增量编译。命令行缩进必须是 Tab。
```makefile
target: prerequisites
	command
```
变量用 `:=` 立即展开、`=` 延迟展开、`?=` 仅在未定义时赋值；命令行传入的值会覆盖 Makefile 内的普通赋值。自动变量是模式规则的粘合剂：

| 自动变量 | 含义 | 典型用途 |
| --- | --- | --- |
| `$@` | 当前目标 | `-o $@` |
| `$<` | 第一个依赖 | 编译单个源文件 |
| `$^` | 所有依赖（去重） | 链接、打包 |

`wildcard` 收集源文件，`patsubst` 做后缀替换；`build/obj/%.o: src/%.c` 是模式规则。`.PHONY: all clean` 声明伪目标，防止目录里有同名文件导致 `clean` 不执行。`make -j8` 并行执行互不依赖的规则，目录创建用 `@mkdir -p $(@D)`（或 order-only 依赖），避免竞争。
```makefile
CC       := gcc
AR       := ar
CFLAGS   := -std=c11 -Wall -Wextra -Wpedantic -O2 -g
CPPFLAGS := -Iinclude
B        := build
OBJ      := $(B)/obj
SRCS     := $(wildcard src/*.c)
OBJS     := $(patsubst src/%.c,$(OBJ)/%.o,$(SRCS))
LIB_OBJS := $(filter-out $(OBJ)/main.o,$(OBJS))
LIB      := $(B)/libwordcount.a
APP      := $(B)/wordcount

.PHONY: all clean
all: $(APP)
$(APP): $(OBJ)/main.o $(LIB)
	$(CC) $< $(LIB) -o $@
$(LIB): $(LIB_OBJS)
	$(AR) rcs $@ $^
$(OBJ)/%.o: src/%.c
	@mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@
clean:
	rm -rf $(B)
-include $(OBJS:.o=.d)
```
`-MMD -MP` 生成 `.d` 文件，记录每个 `.o` 依赖哪些头文件；末尾 `-include` 引入它们，改头文件才能触发相关源文件重编。Make 不跟踪编译器版本和 `CFLAGS` 变化，切换编译选项后应 `make clean`。

## 5 CMake
CMake 不直接编译，而是先生成 Makefile 或 Ninja 文件，再由生成器执行。它擅长跨平台、依赖发现、安装和 IDE 集成，代价是多一层配置步骤和一套自己的语言。
```cmake
cmake_minimum_required(VERSION 3.16)
project(wordcount VERSION 1.0.0 LANGUAGES C)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()
add_library(wordcount STATIC src/wordcount.c)
target_include_directories(wordcount PUBLIC include)
add_executable(wordcount_app src/main.c)
set_target_properties(wordcount_app PROPERTIES OUTPUT_NAME wordcount)
target_link_libraries(wordcount_app PRIVATE wordcount)
include(CTest)
if(BUILD_TESTING)
    add_library(unity STATIC third_party/unity/src/unity.c)
    target_include_directories(unity PUBLIC third_party/unity/src)
    add_executable(test_wordcount tests/test_wordcount.c)
    target_link_libraries(test_wordcount PRIVATE wordcount unity)
    add_test(NAME wordcount.basic COMMAND test_wordcount)
endif()
find_package(Threads REQUIRED)   # 示例：需要 pthread 时
target_link_libraries(wordcount_app PRIVATE Threads::Threads)
```
`add_library(wordcount SHARED ...)` 即生成 `.so`；`target_include_directories(... PUBLIC ...)` 把包含路径传播给链接该库的目标，`PRIVATE` 不传播；`target_link_libraries` 优于全局 `link_libraries`，依赖关系更清晰。`find_package` 通常提供 `Foo::Foo` 导入目标，比手写 `-I`/`-L` 可移植；`include(CTest)` 会定义 `BUILD_TESTING` 并启用 `ctest`。
```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build -j
(cd build && ctest --output-on-failure)
```

| 对比项 | Makefile | CMake |
| --- | --- | --- |
| 本质 | 直接描述规则并执行 | 生成构建系统，再执行 |
| 跨平台 | 需自己处理平台差异 | 内置编译器和平台探测 |
| 依赖发现 | 手写 `pkg-config` 等 | `find_package`、导入目标 |
| IDE | 需额外生成 | 可生成 VS、Xcode、Ninja |
| 适用 | 小型、单平台、内核/嵌入式 | 多平台、多目标、需安装打包 |

## 6 单元测试
单元测试把行为固定下来：重构后几分钟内知道有没有回归，边界条件成为可执行文档，CI 能在合并前拦住问题。测试应针对公开行为，不绑定内部实现，否则重构时测试先坏。
```c
#include "unity.h"
#include "wordcount.h"
void setUp(void) {} void tearDown(void) {}
static void test_empty(void) {
    FILE *fp = tmpfile();
    TEST_ASSERT_NOT_NULL(fp);
    WCResult r;
    TEST_ASSERT_EQUAL_INT(WC_OK, wc_count_stream(fp, &r));
    TEST_ASSERT_EQUAL_INT(0, (int)r.size);
    wc_result_free(&r); fclose(fp);
}
int main(void) {
    UNITY_BEGIN(); RUN_TEST(test_empty);
    return UNITY_END();
}
```
```c
#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>
#include "wordcount.h"
static void test_empty(void **state) {
    (void)state; FILE *fp = tmpfile();
    assert_non_null(fp);
    WCResult r;
    assert_int_equal(WC_OK, wc_count_stream(fp, &r));
    assert_int_equal(0, r.size);
    wc_result_free(&r); fclose(fp);
}
int main(void) {
    const struct CMUnitTest tests[] = { cmocka_unit_test(test_empty) };
    return cmocka_run_group_tests(tests, NULL, NULL);
}
```

| 对比项 | `assert` | 测试框架 |
| --- | --- | --- |
| 失败行为 | `abort`，整个进程结束 | 记录失败并继续跑其他用例 |
| 信息 | 只有表达式和行号 | 用例名、期望值、实际值、统计 |
| 生命周期 | 无 `setUp`/`tearDown` | 支持夹具、mock、参数化 |
| 发布构建 | `NDEBUG` 下被移除 | 测试目标独立编译，不受影响 |
| 适用 | 开发期自检、内部不变量 | 回归测试、CI、验收 |

不要在 `assert` 表达式里写有副作用的代码，例如 `assert(fp = fopen(...))`；`NDEBUG` 下整句会消失。静态函数不能直接链接调用，常见做法是把实现文件包含进测试翻译单元：
```c
#include "wordcount.c"   /* 测试 TU 内可见 static 函数 */
```
这种写法能测内部函数，但会重复编译实现、无法同时链接库，且测试与实现强耦合。取舍是优先通过公开 API 测行为；要测复杂内部函数时拆成独立模块并加内部头文件，或只在专门测试目标中 `#include`，不要用 `-Dstatic=` 破坏语义。

覆盖率用 `gcov` 看单文件行覆盖，`lcov` 汇总并生成 HTML：
```bash
cmake -S . -B build-cov -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_FLAGS="--coverage -O0 -g"
cmake --build build-cov && (cd build-cov && ctest)
gcov -b -c build-cov/CMakeFiles/wordcount.dir/src/wordcount.c.gcno
lcov --capture --directory build-cov --output-file coverage.info
genhtml coverage.info --output-directory build-cov/coverage
```
## 7 调试与排错流程
排错顺序固定下来能少走弯路：编译阶段先让告警清零（`-Wall -Wextra -Wpedantic`，CI 加 `-Werror`），再用运行时工具定位，最后才用调试器猜。定位用 `-O0 -g`，发布用 `-O2`。

| 场景 | 工具 | 关键命令 |
| --- | --- | --- |
| 编译告警 | GCC/Clang | `-Wall -Wextra -Wpedantic -Werror` |
| 逻辑断点 | gdb | `gdb -q ./build/wordcount` |
| 越界/泄漏 | ASan、valgrind | `-fsanitize=address,undefined` |
| 未定义行为 | UBSan | `-fsanitize=undefined` |
| 崩溃现场 | core + gdb | `gdb ./app core` 后 `bt full` |

```bash
gcc -std=c11 -g -O0 -Iinclude src/*.c -o build/wordcount
gdb -q ./build/wordcount
(gdb) break wc_count_stream
(gdb) run README.md
(gdb) next
(gdb) step
(gdb) backtrace
(gdb) frame 0
(gdb) print len
(gdb) x/16xb w
```
`next` 不进入函数，`step` 进入，`finish` 回到调用层；`bt` 看调用栈，`frame N` 切换栈帧后再 `p` 变量；`x/16xb p` 按十六进制逐字节看内存；`watch` 抓「谁改了它」。段错误时先 `bt`，再切到出错帧看指针、下标和缓冲区大小。

Sanitizer 比 gdb 更快给出根因：
```bash
gcc -std=c11 -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Iinclude src/*.c -o build/wordcount_asan
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 ./build/wordcount_asan README.md
valgrind --leak-check=full --show-leak-kinds=all ./build/wordcount README.md
```
ASan 捕获越界、use-after-free、double free、栈溢出；UBSan 捕获有符号溢出、空指针解引用、移位越界。两者都要重新编译，不能用于已发布的无插桩二进制；valgrind 不需重编，但慢 10~50 倍，且不要和 ASan 同时开。

core dump：先 `ulimit -c unlimited`，确认 `/proc/sys/kernel/core_pattern` 指向可取回的位置，复现后 `gdb ./build/wordcount core`，执行 `bt full` 看完整栈和局部变量。栈损坏时用 `-fstack-protector-strong` 加 canary，或回到 ASan 版本复现。定位后回答三个问题：哪个指针/下标越界、为什么没检查、同类路径还有没有。

## 8 代码规范与工程习惯
规范的目标是降低 review 成本和链接/内存错误概率，不是审美。团队统一即可，关键是自动化：`clang-format` 管格式，`-Wall -Wextra` 加静态分析管语义。

| 对象 | 约定 | 示例 |
| --- | --- | --- |
| 文件 | 小写 + 下划线 | `wordcount.c`、`hash_table.h` |
| 类型 | 大驼峰 | `WCResult` |
| 函数 | 小写 + 下划线，模块前缀 | `wc_count_file` |
| 宏/枚举 | 全大写 + 模块前缀 | `WC_MAX_WORD`、`WC_OK` |
| 全局变量 | `g_` 前缀，尽量少用 | `g_verbose` |

头文件包含顺序：自身头文件 → C 标准库 → 平台/POSIX → 第三方库 → 本项目其他头文件，组间空行。自身头文件放第一能立刻暴露「头文件缺少依赖」，避免别人调整顺序就编译失败。

`static` 把函数和变量的链接属性收窄到当前翻译单元，既避免符号污染，也给编译器内联机会。只在本文件用的辅助函数一律 `static`，公共 API 才放头文件。`const` 要落在正确位置：`const char *p` 是不能改字符，`char *const p` 是不能改指针；接口参数能加 `const` 就加，例如 `wc_count_file(const char *path, WCResult *out)`，让调用方和编译器都知道所有权。

错误处理优先「返回状态码 + 输出参数」，不要用 `-1` 兼作合法数据，也不要用返回值同时表达结果和错误。系统调用失败后立刻保存 `errno`，因为后续 `printf` 可能覆盖它。资源释放用统一的 `goto cleanup`，每申请一个资源就多一个清理分支：
```c
int process(const char *path) {
    FILE *fp = fopen(path, "rb"); char *buf = NULL; int rc = -1;
    if (!fp) goto cleanup;
    if (!(buf = malloc(4096))) goto cleanup;
    /* ... 使用 fp / buf ... */
    rc = 0;
cleanup:
    free(buf);
    if (fp) fclose(fp);
    return rc;
}
```
日志分级别，默认只输出 WARN 及以上，调试信息用 `-DDEBUG` 或运行参数打开：

| 级别 | 用途 | 例子 |
| --- | --- | --- |
| ERROR | 功能失败、需要人工处理 | 文件打不开、内存不足 |
| WARN | 可恢复但异常 | 跳过超长单词、配置缺失用默认值 |
| INFO | 关键生命周期 | 开始处理、统计完成 |
| DEBUG | 排查细节 | 桶数量、每阶段耗时 |
| TRACE | 高频内部路径 | 逐词解析，默认关闭 |

日志写 `stderr`，正常结果写 `stdout`，这样管道和重定向不会把日志混进数据；错误信息带上下文（路径、错误码），不要只打印 `failed`。

## 9 一个完整小项目案例
目标：命令行工具 `wordcount FILE` 统计文本词频，按次数降序、同次数按字典序输出。数据流是「读文件 → 逐字符切词 → 哈希表计数 → 展平数组 → 排序」。词定义为字母、数字、下划线、单引号组成的串，统一转小写；超过 63 字符的词丢弃。
```c
/* include/wordcount.h */
#ifndef WORDCOUNT_H
#define WORDCOUNT_H
#include <stddef.h>
#include <stdio.h>
#define WC_MAX_WORD 64
typedef enum { WC_OK, WC_ERR_ARGS, WC_ERR_IO, WC_ERR_NOMEM } WCStatus;
typedef struct { char *word; size_t count; } WCEntry;
typedef struct { WCEntry *items; size_t size, capacity; } WCResult;
WCStatus wc_count_stream(FILE *fp, WCResult *out);
WCStatus wc_count_file(const char *path, WCResult *out);
void wc_result_sort(WCResult *r);
void wc_result_free(WCResult *r);
#endif
```
```c
/* src/wordcount.c */
#include "wordcount.h"
#include <ctype.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define WC_BUCKETS 65536u          /* 2 的幂；固定桶数，示例从简 */
static uint64_t hash_word(const char *s) {
    uint64_t h = 14695981039346656037ULL;   /* FNV-1a */
    while (*s) { h ^= (unsigned char)*s++; h *= 1099511628211ULL; }
    return h;
}
static char *dup_word(const char *s) {
    size_t n = strlen(s) + 1;
    char *p = malloc(n);
    if (p) memcpy(p, s, n);
    return p;
}
static int add_word(WCEntry *t, const char *w) {
    size_t i = (size_t)hash_word(w) & (WC_BUCKETS - 1);
    for (size_t n = 0; n < WC_BUCKETS; n++) {
        if (!t[i].word) {
            t[i].word = dup_word(w);
            if (!t[i].word) return -1;
            t[i].count = 1;
            return 0;
        }
        if (strcmp(t[i].word, w) == 0) { t[i].count++; return 0; }
        i = (i + 1) & (WC_BUCKETS - 1);
    }
    return -1;                     /* 表满：生产版应 rehash */
}
static void free_table(WCEntry *t) {
    if (!t) return;
    for (size_t i = 0; i < WC_BUCKETS; i++) free(t[i].word);
    free(t);
}
WCStatus wc_count_stream(FILE *fp, WCResult *out) {
    if (!fp || !out) return WC_ERR_ARGS;
    *out = (WCResult){0};
    WCEntry *t = calloc(WC_BUCKETS, sizeof *t);
    if (!t) return WC_ERR_NOMEM;
    char w[WC_MAX_WORD]; size_t len = 0; int in = 0, over = 0;
    WCStatus st = WC_OK;
    for (;;) {
        int ch = fgetc(fp);
        if (ch != EOF && (isalnum((unsigned char)ch) || ch == '_' || ch == '\'')) {
            in = 1;
            if (len + 1 < sizeof w) w[len++] = (char)tolower((unsigned char)ch);
            else over = 1;
            continue;
        }
        if (in) {
            w[len] = '\0';
            if (!over && add_word(t, w) != 0) { st = WC_ERR_NOMEM; goto done; }
            len = 0; over = 0; in = 0;
        }
        if (ch == EOF) break;
    }
    if (ferror(fp)) { st = WC_ERR_IO; goto done; }
    size_t n = 0;
    for (size_t i = 0; i < WC_BUCKETS; i++) n += t[i].word != NULL;
    if (n && !(out->items = malloc(n * sizeof *out->items))) { st = WC_ERR_NOMEM; goto done; }
    size_t k = 0;
    for (size_t i = 0; i < WC_BUCKETS; i++)
        if (t[i].word) out->items[k++] = t[i];   /* 转移 word 所有权 */
    out->size = out->capacity = n;
    free(t); return WC_OK;
done:
    free_table(t);
    wc_result_free(out);
    return st;
}
WCStatus wc_count_file(const char *path, WCResult *out) {
    if (!path || !out) return WC_ERR_ARGS;
    *out = (WCResult){0};
    FILE *fp = fopen(path, "r");
    if (!fp) return WC_ERR_IO;
    WCStatus st = wc_count_stream(fp, out);
    if (fclose(fp) != 0 && st == WC_OK) { wc_result_free(out); st = WC_ERR_IO; }
    return st;
}
static int cmp_entry(const void *a, const void *b) {
    const WCEntry *x = a, *y = b;
    if (x->count != y->count) return x->count < y->count ? 1 : -1;
    return strcmp(x->word, y->word);
}
void wc_result_sort(WCResult *r) {
    if (r && r->size > 1) qsort(r->items, r->size, sizeof r->items[0], cmp_entry);
}
void wc_result_free(WCResult *r) {
    if (!r) return;
    for (size_t i = 0; i < r->size; i++) free(r->items[i].word);
    free(r->items);
    *r = (WCResult){0};
}
```
```c
/* src/main.c */
#include <stdio.h>
#include <stdlib.h>
#include "wordcount.h"
int main(int argc, char *argv[]) {
    if (argc != 2) { fprintf(stderr, "usage: %s FILE\n", argc > 0 ? argv[0] : "wordcount"); return EXIT_FAILURE; }
    WCResult r;
    WCStatus st = wc_count_file(argv[1], &r);
    if (st != WC_OK) { fprintf(stderr, "cannot process '%s' (error %d)\n", argv[1], (int)st); return EXIT_FAILURE; }
    wc_result_sort(&r);
    for (size_t i = 0; i < r.size; i++)
        printf("%8zu  %s\n", r.items[i].count, r.items[i].word);
    wc_result_free(&r);
    return EXIT_SUCCESS;
}
```
```makefile
# 第 9 节对应的最小 Makefile；完整版见第 4 节
CC       := gcc
AR       := ar
CFLAGS   := -std=c11 -Wall -Wextra -Wpedantic -O2 -g
CPPFLAGS := -Iinclude
B        := build
LIB      := $(B)/libwordcount.a
APP      := $(B)/wordcount
all: $(APP)
$(APP): $(B)/main.o $(LIB)
	$(CC) $< $(LIB) -o $@
$(LIB): $(B)/wordcount.o
	$(AR) rcs $@ $^
$(B)/%.o: src/%.c include/wordcount.h
	@mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@
clean:
	rm -rf $(B)
.PHONY: all clean
```
```bash
make
./build/wordcount README.md | head -n 5
make clean
```
典型输出形如 `12  the`、`7  build`。复杂度：切词 O(文件大小)，计数平均 O(词数)，排序 O(U log U)（U 为不同词数），内存 O(U)。可扩展方向：UTF-8 码点切词、动态扩容、`--top N`、`--min-count`、大文件 `mmap`。面试时说明「固定 65536 桶在词量极大时退化，生产版应 rehash 或增加溢出处理」，比假装完美可信。

## 10 面试怎么答项目题
项目题不是复述代码，而是证明你能在约束下做决策。用 STAR 组织，控制在一分半到两分钟，先给结论，再给证据：

| 要素 | 要讲什么 | 词频项目的例子 |
| --- | --- | --- |
| Situation | 背景、规模、约束 | 1 GB 日志，4 核，要求 30 秒内出结果 |
| Task | 目标与指标 | 词频 Top N，内存不超过 512 MB |
| Action | 2~3 个关键决策 | 哈希表 + 动态数组、缓冲读取、静态库拆分 |
| Result | 量化结果、代价、复盘 | 9.4 秒完成，峰值 310 MB；固定桶数仍是优化点 |

讲构建系统选型按「约束 → 候选 → 决策 → 结果」：先讲单平台还是多平台、几个 target、是否要 IDE/安装包、CI 用什么、团队是否熟悉；再说明候选与放弃理由，例如「选 CMake 是因为 CI 要同时出 Linux/Windows 产物，代价是配置层更复杂，我们用 preset 固定选项」；最后给构建时间和复现成本，不要只说「CMake 更现代」。

性能优化要给出基线、方法、结果和代价，三个可套用的量化模板：

1. 延迟型：「在 [规模/硬件] 下，[操作] 的 P95 从 [A] ms 降到 [B] ms（约 -X%）；用 [perf/基准脚本] 连测 3 轮，瓶颈从 [函数] 转移；代价是 [内存/复杂度] 上升。」
2. 吞吐型：「[服务/工具] 的 QPS 从 [A] 提升到 [B]（约 +X%），P99 保持在 [C] ms 内；关键动作是 [减少拷贝/批处理/缓存]，命中率 [D]%；代价是 [一致性/内存]。」
3. 资源型：「峰值 RSS 从 [A] MB 降到 [B] MB（约 -X%），冷启动从 [C] s 降到 [D] s；做法是 [换数据结构/延迟加载/去掉冗余依赖]；用 [valgrind massif/time] 验证，代价是 [首次访问变慢]。」

再准备两个「翻车点」：一次内存泄漏或越界如何被 ASan/valgrind 抓到，一次链接错误（头文件定义变量、库顺序、运行时找不到 `.so`）如何定位。能讲清失败和修复，比只讲成功更能证明工程能力。
