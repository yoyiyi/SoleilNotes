# C 笔试手写题
> 面向笔试/机试：每题含题意、边界、完整实现、测试与复杂度；C11，建议 `-Wall -Wextra -Wpedantic`。公共头文件与前置定义如下，单题复制时一起带上。
```c
#include <assert.h>
#include <ctype.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(e) do { if (!(e)) { fprintf(stderr, "FAIL: %s\n", #e); exit(1); } } while (0)
typedef struct Node { int val; struct Node *next; } Node;
```
**测试**：各题「测试」是断言表达式，如 `CHECK(my_strlen("abc") == 3)`；**目录**：1 字符串（8）｜2 内存（3）｜3 位运算（6）｜4 数组与排序（7）｜5 链表（6）｜6 其他（5）｜7 套路｜8 改错（10）。
## 1 字符串（8 题）
### 1.1 手写 strlen
**题意**：返回字符串长度，不含结尾 `'\0'`。
**边界**：`NULL`、空串、没有 `'\0'`（无法检测，属调用方违约）；返回值用 `size_t`。
**实现**：
```c
size_t my_strlen(const char *s)
{
    const char *p = s; if (!s) return 0;
    while (*p) ++p;
    return (size_t)(p - s);
}
```
**测试**：`NULL` → 0；`""` → 0；`"abc"` → 3；`"a\0b"` → 1。
**复杂度**：O(n) 时间，O(1) 空间。
### 1.2 手写 strcpy
**题意**：把 `src`（含 `'\0'`）复制到 `dst`，返回 `dst` 以支持链式调用。
**边界**：空指针；`dst` 容量必须 ≥ `strlen(src)+1`；重叠行为未定义；`dst == src` 应原样成功。
**实现**：
```c
char *my_strcpy(char *dst, const char *src)
{
    char *ret = dst; if (!dst || !src) return NULL;
    while ((*dst++ = *src++) != '\0') { }
    return ret;
}
```
**测试**：`char b[8]; my_strcpy(b,"abc")` → 返回 `b` 且 `strcmp(b,"abc")==0`；复制 `""` → `b[0]=='\0'`。
**复杂度**：O(n) 时间，O(1) 空间。
### 1.3 手写 strcmp
**题意**：按 `unsigned char` 比较，返回 `<0`、`0`、`>0`。
**边界**：空指针按空串处理；必须用无符号字节相减，否则高位字符的顺序可能随平台变化。
**实现**：
```c
int my_strcmp(const char *a, const char *b)
{
    const unsigned char *x = (const unsigned char *)a, *y = (const unsigned char *)b;
    if (!a || !b) return (a != NULL) - (b != NULL);
    while (*x && *x == *y) { ++x; ++y; }
    return (int)*x - (int)*y;
}
```
**测试**：`"abc","abc"` → 0；`"abc","abd"` → 负数；`"a","aa"` → 负数；`"",""` → 0。
**复杂度**：O(min(n,m)) 时间，O(1) 空间。
### 1.4 手写 strstr
**题意**：返回 `needle` 在 `haystack` 中首次出现的地址，找不到返回 `NULL`。
**边界**：空指针；`needle` 为空返回 `haystack`；`haystack` 为空且 `needle` 非空返回 `NULL`；模式可重叠。
**实现**：
```c
char *my_strstr(const char *hay, const char *needle)
{
    if (!hay || !needle) return NULL;
    if (!*needle) return (char *)hay;
    for (; *hay; ++hay) { const char *h=hay, *n=needle;
        while (*h && *n && *h == *n) { ++h; ++n; }
        if (!*n) return (char *)hay; }
    return NULL;
}
```
**测试**：`"hello","ll"` → 下标 2；`"hello",""` → 下标 0；`"hello","lo"` → 下标 3；`"abc","d"` → `NULL`；`"aaa","aa"` → 下标 0。
**复杂度**：O(n·m) 时间，O(1) 空间；KMP 可降到 O(n+m)，笔试优先写对朴素版。
### 1.5 手写 atoi（含溢出与 INT_MIN）
**题意**：跳过前导空白，解析可选正负号和连续数字，返回 `int`。
**边界**：`NULL`/空串/只有符号/非数字返回 0；溢出饱和到 `INT_MAX` 或 `INT_MIN`；`INT_MIN` 不能先取绝对值。
**实现**：
```c
int my_atoi(const char *s)
{
    int sign=1, acc=0; if(!s)return 0;
    while(isspace((unsigned char)*s))++s;
    if(*s=='+'||*s=='-')sign=(*s++=='-')?-1:1;
    while(isdigit((unsigned char)*s)){int d=*s++-'0';
        if(acc<(INT_MIN+d)/10)return sign<0?INT_MIN:INT_MAX;
        acc=acc*10-d;}
    return sign<0?acc:(acc==INT_MIN?INT_MAX:-acc);
}
```
**测试**：`"123"` → 123；`"  -42x"` → -42；`"2147483647"` → `INT_MAX`；`"2147483648"` → `INT_MAX`；`"-2147483648"` → `INT_MIN`；`"-2147483649"` → `INT_MIN`；`"x"` → 0。
**复杂度**：O(n) 时间，O(1) 空间。负累加器把上界自然变成 `INT_MIN`，避免对 `INT_MIN` 取负。
### 1.6 手写 itoa
**题意**：把整数转成 `base`（2~36）进制字符串，支持负数，写入调用方缓冲区。
**边界**：`buf` 至少 `sizeof(int)*CHAR_BIT+2` 字节；`base` 越界返回 `NULL`；`INT_MIN` 不能直接取负；0 要输出 `"0"`。
**实现**：
```c
char *my_itoa(int v, char *buf, int base)
{
    static const char d[]="0123456789abcdefghijklmnopqrstuvwxyz";
    char tmp[sizeof(int)*CHAR_BIT+2], *ret=buf; int i=0, neg=v<0;
    unsigned int u; if(!buf||base<2||base>36)return NULL;
    u=neg?0u-(unsigned int)v:(unsigned int)v;
    do{tmp[i++]=d[u%(unsigned int)base];u/=(unsigned int)base;}while(u);
    if(neg)tmp[i++]='-';
    while(i>0)*buf++=tmp[--i]; *buf='\0'; return ret;
}
```
**测试**：`0,10` → `"0"`；`-255,16` → `"-ff"`；`255,2` → `"11111111"`；`INT_MIN,10` → `"-2147483648"`。
**复杂度**：O(log_base |v|) 时间，O(log |v|) 栈上临时空间。
### 1.7 字符串反转
**题意**：原地反转字符串。
**边界**：`NULL`、空串、单字符；原地版不改长度；按字节反转，UTF-8 多字节字符会乱码，需按码点处理。
**实现**：
```c
void reverse_string(char *s)
{
    if (!s) return; size_t i = 0, j = strlen(s);
    while (i < j) { char t = s[i]; s[i] = s[--j]; s[j] = t; ++i; }
}
```
**测试**：`""` → `""`；`"a"` → `"a"`；`"abc"` → `"cba"`；`"abcd"` → `"dcba"`。
**复杂度**：O(n) 时间，O(1) 空间。
### 1.8 回文判断
**题意**：忽略大小写和非字母数字，判断字符串是否回文。
**边界**：`NULL` 返回 0；空串返回 1；只有标点返回 1；`ctype` 参数必须先转 `unsigned char`。
**实现**：
```c
int is_palindrome(const char *s)
{
    const unsigned char *p=(const unsigned char *)s; size_t i=0,j;
    if(!s)return 0; j=strlen(s);
    while(i<j){
        while(i<j&&!isalnum(p[i]))++i;
        while(i<j&&!isalnum(p[j-1]))--j;
        if(i<j&&tolower(p[i])!=tolower(p[j-1]))return 0;
        ++i;--j;
    }
    return 1;
}
```
**测试**：`"A man, a plan, a canal: Panama"` → 1；`"abc"` → 0；`""` → 1；`".,"` → 1。
**复杂度**：O(n) 时间，O(1) 空间。
## 2 内存函数（3 题）
> 三者都按字节操作并返回 `dst`。`unsigned char *` 的步长严格为 1，能访问任意对象的字节表示且不受符号与严格别名影响；库实现还会先对齐、再按字长循环展开，减少分支并便于 SIMD。
### 2.1 手写 memcpy（重叠与对齐）
**题意**：把 `src` 的 `n` 个字节复制到 `dst`，返回 `dst`。
**边界**：`dst`/`src` 非空（`n==0` 可宽松放行）；**重叠时行为未定义**；任意对齐都要能工作；不关心 `'\0'`。
**实现**：
```c
void *my_memcpy(void *dst, const void *src, size_t n)
{
    unsigned char *d = (unsigned char *)dst;
    const unsigned char *s = (const unsigned char *)src;
    if (!dst || !src) return dst;
    for (size_t i = 0; i < n; ++i) d[i] = s[i];
    return dst;
}
```
**测试**：`int a[4]={1,2,3,4},b[4]; my_memcpy(b,a,sizeof a)` → `memcmp(a,b,sizeof a)==0`；`n=0` 不写字节。
**复杂度**：O(n) 时间，O(1) 空间。
**重叠与对齐**：跨对象比较 `d < s` 在标准里没有定义，重叠应改用 `memmove`；字节循环对任意对齐安全，库的快路径先把头部搬到字对齐，再按 `size_t`/SIMD 批量搬，尾部收字节。
### 2.2 手写 memmove
**题意**：复制 `n` 个字节，允许源和目标重叠。
**边界**：`dst == src` 或 `n == 0` 直接返回；目标在低地址从前向后，目标在高地址从后向前，避免覆盖未读源字节。
**实现**：
```c
void *my_memmove(void *dst, const void *src, size_t n)
{
    unsigned char *d=(unsigned char *)dst;
    const unsigned char *s=(const unsigned char *)src;
    if(!dst||!src||n==0||d==s)return dst;
    if((uintptr_t)d<(uintptr_t)s){for(size_t i=0;i<n;++i)d[i]=s[i];}
    else{for(size_t i=n;i>0;--i)d[i-1]=s[i-1];}
    return dst;
}
```
**测试**：`char b[]="abcdef"; my_memmove(b+2,b,4)` → `"ababcd"`；`my_memmove(b,b+2,4)` → `"cdefef"`；`b,b,0` 不变。
**复杂度**：O(n) 时间，O(1) 空间。`uintptr_t` 比较属于实现定义的工程写法，纯标准无法完美检测跨对象重叠。
### 2.3 手写 memset
**题意**：把 `s` 开始的 `n` 个字节设为 `c` 的低 8 位，返回 `s`。
**边界**：`s` 为空；`n==0`；`c` 截断成 `unsigned char`；不能把 `int` 数组各元素设成 1（全 0 字节才碰巧为 0）。
**实现**：
```c
void *my_memset(void *s, int c, size_t n)
{
    unsigned char *p = (unsigned char *)s; if (!s) return s;
    for (size_t i = 0; i < n; ++i) p[i] = (unsigned char)c;
    return s;
}
```
**测试**：`char b[4]; my_memset(b,'x',4)` → `"xxxx"`；`my_memset(b,0,4)` → 全 0；`n=0` 不变。
**复杂度**：O(n) 时间，O(1) 空间；库版本按 4/8 字节展开，一次写更多字节。
## 3 位运算（6 题）
### 3.1 置位、清位、翻转与测试
**题意**：对无符号整数第 `n` 位（从 0 开始）置 1、清 0、取反、读取。
**边界**：`0 <= n < sizeof(unsigned int)*CHAR_BIT`；越界移位是 UB；必须用 `1u`，不要用有符号 `1`。
**实现**：
```c
static unsigned int bit_mask(unsigned n)
{
    assert(n < sizeof(unsigned int) * CHAR_BIT);
    return 1u << n;
}
unsigned int bit_set(unsigned int x, unsigned n)    { return x |  bit_mask(n); }
unsigned int bit_clear(unsigned int x, unsigned n)  { return x & ~bit_mask(n); }
unsigned int bit_toggle(unsigned int x, unsigned n) { return x ^  bit_mask(n); }
int bit_test(unsigned int x, unsigned n)            { return (x & bit_mask(n)) != 0; }
```
**测试**：`bit_set(0,3)==8`；`bit_clear(0xF,1)==0xD`；`bit_toggle(0xF,0)==0xE`；`bit_test(0x8,3)==1`；`bit_test(0x8,2)==0`。
**复杂度**：O(1) 时间，O(1) 空间。
### 3.2 统计 1 的个数（三种写法）
**题意**：返回无符号整数中值为 1 的位数。
**边界**：0 → 0；全 1 → 位宽；移位次数不超过类型位宽；查表法控制表大小。
**实现**：
```c
int popcount_loop(unsigned int x) { int n=0; while(x){n+=x&1u;x>>=1;} return n; }
int popcount_kernighan(unsigned int x) { int n=0; while(x){x&=x-1;++n;} return n; }
int popcount_table(unsigned int x)
{
    static const unsigned char t[16]={0,1,1,2,1,2,2,3,1,2,2,3,2,3,3,4};
    int n=0; while(x){n+=t[x&0xFu];x>>=4;} return n;
}
```
**测试**：`0` → 0；`0xF0F0` → 8；`UINT_MAX` → `sizeof(unsigned)*CHAR_BIT`；三种实现返回值一致。
**复杂度**：循环 O(位数)，Kernighan O(1 的个数)，查表 O(位数/4)；位宽固定时都可视为 O(1)。完整字节表 256 项，半字节表 16 项更省缓存。
### 3.3 判断 2 的幂
**题意**：判断无符号整数 `x` 是否为 2 的整数次幂。
**边界**：0 不是；1 是（2^0）；负数在无符号语境下按大正数处理；`x & (x-1)` 清掉最低位的 1。
**实现**：
```c
int is_power_of_two(unsigned int x)
{
    return x != 0 && (x & (x - 1)) == 0;
}
```
**测试**：`0` → 0；`1` → 1；`2` → 1；`3` → 0；`1024` → 1；`UINT_MAX` → 0。
**复杂度**：O(1) 时间，O(1) 空间。
### 3.4 交换两个数
**题意**：不借助临时变量交换两个整数（异或版）。
**边界**：空指针；`a == b`（同一地址）时异或会把值清零，必须提前返回；生产代码优先临时变量。
**实现**：
```c
void swap_xor(int *a, int *b)
{
    if (!a || !b || a == b) return;
    *a ^= *b; *b ^= *a; *a ^= *b;
}
```
**测试**：`3,5` → `5,3`；`-1,INT_MIN` → 正确交换；`swap_xor(&x,&x)` 后 `x` 不变。
**复杂度**：O(1) 时间，O(1) 空间。
### 3.5 找出只出现一次的数
**题意**：除一个数外其余都出现两次，找出那个数。
**边界**：空数组/空指针返回 0（调用方保证恰有一个答案）；异或满足交换律、结合律，`a^a=0`、`a^0=a`；不修改数组。
**实现**：
```c
int single_number(const int *a, size_t n)
{
    int r = 0; if (!a) return 0;
    for (size_t i = 0; i < n; ++i) r ^= a[i];
    return r;
}
```
**测试**：`{2,3,2,4,4}` → 3；`{7}` → 7；`{0,0,5}` → 5。
**复杂度**：O(n) 时间，O(1) 空间。
### 3.6 反转二进制位
**题意**：把 32 位无符号整数的二进制位整体反转。
**边界**：0 和全 1 保持不变；循环次数必须是 32；用 `uint32_t` 避免位宽假设。
**实现**：
```c
uint32_t reverse_bits(uint32_t x)
{
    uint32_t r = 0;
    for (int i = 0; i < 32; ++i) { r = (r << 1) | (x & 1u); x >>= 1; }
    return r;
}
```
**测试**：`0x1` → `0x80000000`；`0x0000FFFF` → `0xFFFF0000`；`0` → `0`。
**复杂度**：O(32)=O(1) 时间，O(1) 空间。
## 4 数组与排序（7 题）
### 4.1 二分查找（含左右边界）
**题意**：升序数组中查 `key`，并给出第一个 `>= key`、第一个 `> key` 的位置。
**边界**：空数组；重复元素；找不到；`mid=lo+(hi-lo)/2` 防 `lo+hi` 溢出；区间统一 `[lo,hi)`。
**实现**：
```c
int lower_bound(const int *a, int n, int key)
{
    int lo=0,hi=n; while(lo<hi){int m=lo+(hi-lo)/2;if(a[m]<key)lo=m+1;else hi=m;} return lo;
}
int upper_bound(const int *a, int n, int key)
{
    int lo=0,hi=n; while(lo<hi){int m=lo+(hi-lo)/2;if(a[m]<=key)lo=m+1;else hi=m;} return lo;
}
int binary_search(const int *a, int n, int key)
{
    int p=lower_bound(a,n,key); return (p<n&&a[p]==key)?p:-1;
}
```
**测试**：`{1,2,2,2,4,5}` 查 2：`lower=1`、`upper=4`、`search=1`；查 3：`lower=upper=4`、`search=-1`；空数组：`lower=upper=0`。
**复杂度**：O(log n) 时间，O(1) 空间。
### 4.2 冒泡排序
**题意**：相邻逆序就交换，每轮把当前最大值冒到末尾。
**边界**：空数组/单元素；加 `swapped` 后最好 O(n)；相等不交换，稳定。
**实现**：
```c
void bubble_sort(int *a, int n)
{
    for (int i=0;i<n;++i){int sw=0;
        for(int j=0;j+1<n-i;++j) if(a[j]>a[j+1]){int t=a[j];a[j]=a[j+1];a[j+1]=t;sw=1;}
        if(!sw)break;}
}
```
**测试**：`{3,1,2}` → `{1,2,3}`；`{1,2,3}` → 一轮后退出；`{}` 不崩；`{2,2,1}` → `{1,2,2}`。
**复杂度**：最坏/平均 O(n²)，最好 O(n)，O(1) 空间，稳定。
### 4.3 插入排序
**题意**：维护已排序前缀，把 `a[i]` 插入正确位置。
**边界**：空数组；已排序只比较不移动；逆序移动最多；相等不越过，稳定。
**实现**：
```c
void insertion_sort(int *a, int n)
{
    for (int i=1;i<n;++i){int key=a[i],j=i;
        while(j>0 && a[j-1]>key){a[j]=a[j-1];--j;} a[j]=key;}
}
```
**测试**：`{3,1,2}` → `{1,2,3}`；`{1,1,0}` → `{0,1,1}`；`{}` 不崩。
**复杂度**：最坏/平均 O(n²)，最好 O(n)，O(1) 空间，稳定。
### 4.4 快速排序
**题意**：选基准划分成左右两段，递归排序。
**边界**：空/单元素；大量重复；基准取中间值并用 Hoare 划分；最坏 O(n²)（每次划分极不均衡），可随机化。
**实现**：
```c
static void quick_rec(int *a, int lo, int hi) {
    if(lo>=hi)return; int p=a[lo+(hi-lo)/2],i=lo,j=hi;
    while(i<=j){while(a[i]<p)++i;while(a[j]>p)--j;
        if(i<=j){int t=a[i];a[i]=a[j];a[j]=t;++i;--j;}}
    quick_rec(a,lo,j); quick_rec(a,i,hi);
}
void quick_sort(int *a,int n){if(a&&n>1)quick_rec(a,0,n-1);}
```
**测试**：`{3,1,2}` → `{1,2,3}`；`{5,5,5,1}` → `{1,5,5,5}`；已排序 `{1,2,3,4}` 仍正确；`{}` 不崩。
**复杂度**：平均 O(n log n)，最坏 O(n²)，平均栈 O(log n)；不稳定。
### 4.5 归并排序
**题意**：递归对半拆分，合并两个有序子数组。
**边界**：空数组；`malloc` 失败返回 -1；合并用 `<=` 保证稳定；需要 O(n) 辅助空间。
**实现**：
```c
static void merge_rec(int *a,int *tmp,int lo,int hi) {
    if(lo>=hi)return; int mid=lo+(hi-lo)/2,i=lo,j=mid+1,k=lo;
    merge_rec(a,tmp,lo,mid); merge_rec(a,tmp,mid+1,hi);
    while(i<=mid&&j<=hi)tmp[k++]=(a[i]<=a[j])?a[i++]:a[j++];
    while(i<=mid)tmp[k++]=a[i++]; while(j<=hi)tmp[k++]=a[j++];
    for(i=lo;i<=hi;++i)a[i]=tmp[i];
}
int merge_sort(int *a,int n) {
    if(!a||n<2)return 0; int *tmp=malloc((size_t)n*sizeof*tmp);
    if(!tmp)return -1; merge_rec(a,tmp,0,n-1); free(tmp); return 0;
}
```
**测试**：`{3,1,2}` → `{1,2,3}`；`{2,1,2,1}` → `{1,1,2,2}`；`{}` → 0；`NULL,3` → 0。
**复杂度**：O(n log n) 时间，O(n) 空间，稳定。
### 4.6 堆排序
**题意**：原地建最大堆，反复把堆顶换到末尾并下沉。
**边界**：空数组；`n/2-1` 在 `n=0` 时为 -1，循环不执行；下标用 `int` 防无符号下溢；不稳定。
**实现**：
```c
static void sift_down(int *a,int n,int i) {
    while(1){int l=2*i+1,r=l+1,m=i;
        if(l<n&&a[l]>a[m])m=l; if(r<n&&a[r]>a[m])m=r;
        if(m==i)return; int t=a[i];a[i]=a[m];a[m]=t;i=m;}
}
void heap_sort(int *a,int n) {
    for(int i=n/2-1;i>=0;--i)sift_down(a,n,i);
    for(int e=n-1;e>0;--e){int t=a[0];a[0]=a[e];a[e]=t;sift_down(a,e,0);}
}
```
**测试**：`{3,1,2}` → `{1,2,3}`；`{4,4,1,4}` → `{1,4,4,4}`；`{}` 不崩；已排序仍正确。
**复杂度**：O(n log n) 时间，O(1) 空间，不稳定。
### 4.7 第 K 大（快速选择）
**题意**：返回数组中第 `k` 大的元素（`k` 从 1 开始），平均 O(n)。
**边界**：非法 `k`/空指针返回 -1；会修改输入；重复元素用 Hoare 划分；最坏 O(n²)。
**实现**：
```c
int kth_largest(int *a,int n,int k,int *out)
{
    if(!a||!out||k<1||k>n)return -1; int target=n-k,lo=0,hi=n-1;
    while(lo<=hi){int p=a[lo+(hi-lo)/2],i=lo,j=hi;
        while(i<=j){while(a[i]<p)++i;while(a[j]>p)--j;
            if(i<=j){int t=a[i];a[i]=a[j];a[j]=t;++i;--j;}}
        if(target<=j)hi=j; else if(target>=i)lo=i; else {*out=a[target];return 0;}}
    return -1;
}
```
**测试**：`{3,2,1,5,6,4},k=2` → 5；`k=1` → 6；`k=6` → 1；`{2,2,2},k=2` → 2；`k=0` → -1。
**复杂度**：平均 O(n) 时间，最坏 O(n²)，O(1) 空间。
## 5 链表（6 题）
### 5.1 反转链表
**题意**：把单链表原地反转，返回新头结点。
**边界**：空链表、单节点；必须先保存 `next` 再改指针，否则丢失后半段。
**实现**：
```c
Node *reverse_list(Node *head)
{
    Node *prev=NULL;
    while(head){Node *next=head->next;head->next=prev;prev=head;head=next;}
    return prev;
}
```
**测试**：`1→2→3` → `3→2→1`；`NULL` → `NULL`；`1` → `1`。
**复杂度**：O(n) 时间，O(1) 空间；递归版 O(n) 栈。
### 5.2 找中间结点
**题意**：快慢指针，快指针每次走两步，慢指针走一步。
**边界**：空链表返回 `NULL`；偶数个节点返回第二个中间节点；访问 `fast->next->next` 前必须判 `fast->next`。
**实现**：
```c
Node *middle_node(Node *head)
{
    Node *slow=head,*fast=head;
    while(fast&&fast->next){slow=slow->next;fast=fast->next->next;}
    return slow;
}
```
**测试**：`1→2→3` → 2；`1→2→3→4` → 3；`NULL` → `NULL`；`1` → 1。
**复杂度**：O(n) 时间，O(1) 空间。
### 5.3 判断环与找入口
**题意**：Floyd 判环；相遇后慢指针放回头，两指针同速再相遇的位置就是入口。
**边界**：空表/单节点无环；自环；入口就是头结点；快指针每次检查 `fast` 和 `fast->next`。
**实现**：
```c
Node *cycle_entry(Node *head) {
    Node *slow=head,*fast=head;
    while(fast&&fast->next){slow=slow->next;fast=fast->next->next;
        if(slow==fast){slow=head;while(slow!=fast){slow=slow->next;fast=fast->next;}return slow;}}
    return NULL;
}
int has_cycle(Node *head){return cycle_entry(head)!=NULL;}
```
**测试**：`1→2→3→4→2` → 入口值 2；`1→1`（自环）→ 1；`1→2→3` → `NULL`。
**复杂度**：O(n) 时间，O(1) 空间。
### 5.4 合并两个有序链表
**题意**：把两个升序链表合并成一个升序链表，复用原结点。
**边界**：任一为空返回另一个；值相等取第一个链表，保持稳定；不新建结点。
**实现**：
```c
Node *merge_sorted(Node *a, Node *b)
{
    Node dummy={0,NULL}, *tail=&dummy;
    while(a&&b){if(a->val<=b->val){tail->next=a;a=a->next;}else{tail->next=b;b=b->next;}tail=tail->next;}
    tail->next=a?a:b;
    return dummy.next;
}
```
**测试**：`1→3→5` 与 `2→4` → `1→2→3→4→5`；`NULL` 与 `2→4` → `2→4`；两个空 → `NULL`。
**复杂度**：O(m+n) 时间，O(1) 空间。
### 5.5 删除倒数第 k 个结点
**题意**：一次遍历删除倒数第 `k` 个结点，返回头结点。
**边界**：`k<=0`/空表；`k` 大于长度不改链表；删头结点必须用哑结点；释放被删结点。
**实现**：
```c
Node *remove_kth_from_end(Node *head, int k) {
    Node dummy={0,head}, *fast=&dummy, *slow=&dummy;
    if(!head||k<=0)return head;
    for(int i=0;i<k;++i){if(!fast->next)return head;fast=fast->next;}
    while(fast->next){fast=fast->next;slow=slow->next;}
    Node *victim=slow->next;slow->next=victim->next;free(victim);
    return dummy.next;
}
```
**测试**：`1→2→3→4→5,k=2` → `1→2→3→5`；单节点 `k=1` → `NULL`；`k=6` 原样；`k=0` 原样。
**复杂度**：O(n) 时间，O(1) 空间。
### 5.6 判断两个链表是否相交
**题意**：返回两个单链表的第一个公共结点，不相交返回 `NULL`。
**边界**：任一为空；按结点地址比较，不能比值；两链可等长或不等长；相交后是 Y 形。
**实现**：
```c
static int list_len(const Node *p){int n=0;while(p){++n;p=p->next;}return n;}
Node *get_intersection(Node *a, Node *b)
{
    int la=list_len(a),lb=list_len(b);
    while(la>lb){a=a->next;--la;} while(lb>la){b=b->next;--lb;}
    while(a!=b){a=a->next;b=b->next;}
    return a;
}
```
**测试**：共享尾 `7→8` 的两链 → 值为 7 的结点；等长不相交 → `NULL`；一条为空 → `NULL`。
**复杂度**：O(m+n) 时间，O(1) 空间。
## 6 其他经典（5 题）
### 6.1 斐波那契数列
**题意**：返回第 `n` 个斐波那契数（`n>=0`，`F(0)=0,F(1)=1`）。
**边界**：`n=0/1`；递归有大量重复子问题；结果增长快，`unsigned long long` 也会溢出。
**实现**：
```c
unsigned long long fib_rec(int n){return n<2?(unsigned long long)n:fib_rec(n-1)+fib_rec(n-2);}
unsigned long long fib_iter(int n)
{
    unsigned long long a=0,b=1;
    for(int i=0;i<n;++i){unsigned long long t=a+b;a=b;b=t;}
    return a;
}
```
**测试**：`fib_rec(0..10)` 与 `fib_iter(0..10)` 都得 `0,1,1,2,3,5,8,13,21,34,55`；两版一致。
**复杂度**：递归 O(2^n)、O(n) 栈；迭代 O(n)、O(1)。矩阵快速幂：`[[1,1],[1,0]]^n` 的右上角（或左下角）是 `F(n)`，O(log n)。
### 6.2 大数相加（字符串）
**题意**：两个非负十进制字符串相加，返回新分配的字符串，调用方 `free`。
**边界**：空指针返回 `NULL`；空串按 0；结果最多 `max(len)+1` 位加 `'\0'`；末尾对齐处理进位；含非数字未定义。
**实现**：
```c
char *big_add(const char *a, const char *b) {
    if(!a||!b)return NULL;
    size_t la=strlen(a),lb=strlen(b),n=la>lb?la:lb;
    char *r=malloc(n+2); if(!r)return NULL;
    size_t i=la,j=lb,k=0; int carry=0;
    if(n==0){r[0]='0';r[1]='\0';return r;}
    while(i>0||j>0||carry){int sum=carry;
        if(i>0)sum+=a[--i]-'0'; if(j>0)sum+=b[--j]-'0';
        r[k++]=(char)('0'+sum%10); carry=sum/10;}
    r[k]='\0'; for(size_t x=0;x<k/2;++x){char t=r[x];r[x]=r[k-1-x];r[k-1-x]=t;}
    return r; }
```
**测试**：`"123"+"89"` → `"212"`；`"999"+"1"` → `"1000"`；`"0"+"0"` → `"0"`；`""+""` → `"0"`。
**复杂度**：O(max(m,n)) 时间，O(max(m,n)) 空间。
### 6.3 判断大小端
**题意**：判断最低地址是否存放整数的最低有效字节。
**边界**：不假设 `int` 是 4 字节，但本方法只看首字节；必须通过 `unsigned char *` 观察对象表示。
**实现**：
```c
int is_little_endian(void) {
    unsigned int x = 1;
    return *(unsigned char *)&x == 1;
}
```
**测试**：x86/ARM 小端 → 1；大端机器 → 0；网络字节序是大端。
**复杂度**：O(1) 时间，O(1) 空间。共用体写法等价：`union { unsigned int i; unsigned char c[sizeof(unsigned int)]; } u={1}; return u.c[0]==1;`。
### 6.4 整数反转
**题意**：反转十进制整数的数字，溢出时返回 0 并通过 `ok` 报告失败。
**边界**：负数、结尾 0、`INT_MIN`、反转后越界；用更宽类型承接中间结果，最后统一比较范围。
**实现**：
```c
int reverse_int(int x, int *ok) {
    long long v=x,r=0; int sign=v<0?-1:1;
    if(!ok)return 0; *ok=1; if(v<0)v=-v;
    while(v>0){r=r*10+v%10;v/=10;}
    r*=sign;
    if(r<INT_MIN||r>INT_MAX){*ok=0;return 0;}
    return (int)r; }
```
**测试**：`123` → 321；`-123` → -321；`120` → 21；`1534236469` 越界 → 0 且 `ok=0`；`INT_MIN` → 0 且 `ok=0`。
**复杂度**：O(log10 |x|) 时间，O(1) 空间。
### 6.5 判断回文数
**题意**：不转字符串，判断整数正读反读是否相同。
**边界**：负数不是；末尾为 0 且数不为 0 不是；0 是；只反转后一半，避免整体反转溢出。
**实现**：
```c
int is_pal_number(int x) {
    if(x<0||(x%10==0&&x!=0))return 0;
    int rev=0;
    while(x>rev){rev=rev*10+x%10;x/=10;}
    return x==rev||x==rev/10;
}
```
**测试**：`121` → 1；`-121` → 0；`10` → 0；`0` → 1；`1221` → 1；`12321` → 1。
**复杂度**：O(log10 x) 时间，O(1) 空间。
## 7 手写题的通用套路
**先问边界、先写测试**：空指针、长度 0、容量不足/重叠、下标范围、整数溢出、返回值与错误码；链表再问空表、单节点、环、两表关系。动手前写下正常、边界、异常各一个，例如 `atoi("2147483648")==INT_MAX`、`reverse(NULL)` 不应崩溃。
**再写主逻辑**：先说清接口契约（返回什么、谁释放、可不可重叠、失败怎么表示），再找循环不变式，最后补防御与注释。
**白板 5 条**：① 变量先初始化，指针先判空；② 覆盖前保存旧值，链表先存 `next`；③ `mid=lo+(hi-lo)/2`，`size_t` 倒序用 `i-- > 0`；④ 主动报平均/最坏复杂度与稳定性；⑤ 手动走小例子，检查所有 `return` 与资源释放。
## 8 附：10 个代码改错小练习
### 8.1 数组越界
**错误代码**：`int a[3]; for (int i = 0; i <= 3; ++i) a[i] = 0;`
**问题/正确**：`i==3` 写 `a[3]`，越界踩坏相邻栈变量；改为 `i < 3`。
### 8.2 变量未初始化
**错误代码**：`int sum; for (int i = 0; i < 3; ++i) sum += i;`
**问题/正确**：`sum` 是不确定值，读取未初始化对象是 UB；改为 `int sum = 0;`。
### 8.3 sizeof 误用
**错误代码**：`void f(int a[10]) { size_t n = sizeof(a) / sizeof(a[0]); }`
**问题/正确**：数组参数退化为指针，64 位下 `n==2` 而不是 10；额外传 `size_t n`，或在退化前算好长度。
### 8.4 strcpy 缓冲区溢出
**错误代码**：`char dst[4]; strcpy(dst, "hello");`
**问题/正确**：`"hello"` 含结尾共 6 字节，写爆 4 字节缓冲区；保证 `sizeof dst >= strlen(src)+1`，或改用会截断的 `snprintf`。
### 8.5 free 后继续使用
**错误代码**：`char *p = malloc(8); free(p); p[0] = 'x';`
**问题/正确**：释放后指针悬空，再读写是 use-after-free；`free(p); p = NULL;`，此后不再解引用。
### 8.6 整数溢出
**错误代码**：`int mid = (lo + hi) / 2;`
**问题/正确**：`lo+hi` 超过 `INT_MAX` 是有符号溢出（UB）；改为 `lo + (hi-lo)/2`。
### 8.7 返回值未检查
**错误代码**：`FILE *fp=fopen("data.txt","r"); char buf[128]; fgets(buf,sizeof buf,fp);`
**问题/正确**：`fp` 可能为 `NULL`，`fgets` 返回值也没查；先 `if(!fp){perror("fopen");return -1;}`，再判断 `fgets(...)!=NULL`，最后 `fclose(fp)`。
### 8.8 空指针解引用
**错误代码**：`char *s=NULL; printf("%zu\n", strlen(s));`
**问题/正确**：`strlen(NULL)` 是 UB；先判空 `if (s) printf("%zu\n", strlen(s));`，或规范化为 `""`。
### 8.9 无符号循环下溢
**错误代码**：`for (size_t i = n - 1; i >= 0; --i) a[i] = 0;`
**问题/正确**：无符号 `i` 减到 0 后再减会回绕成 `SIZE_MAX`，条件永真；改为 `for (size_t i=n; i-- > 0; ) a[i]=0;`。
### 8.10 提前 return 导致内存泄漏
**错误代码**：`char *p=malloc(100); if (error) return -1; free(p);`
**问题/正确**：错误分支直接返回，`p` 泄漏；返回前 `free(p)`，或用统一 `cleanup:` 标签集中释放。
