# Linux 网络编程
面向面试的 socket 编程笔记：从「应用层怎么用 socket」讲到可直接编译的 echo 服务，再把 IO 多路复用、Reactor 与线上排障串起来。协议栈原理见 [Linux详解](Linux详解.md) 第 7 章，`errno` 与文件 IO 的写法见 [C详解](C详解.md) 第 8 章。

- 定位：面试要能默写服务端/客户端骨架，并说清每个系统调用在内核里做了什么。
- 约定：Linux + glibc，示例端口 9000~9002，统一 `gcc -std=c11 -Wall -Wextra -O2`，Linux 扩展靠 `_GNU_SOURCE` 打开。
- 环境：内核 5.10+；`epoll`、`accept4`、`SO_REUSEPORT` 均可用。

## 1 TCP/IP 与 socket 的关系
TCP/IP 是内核里的协议实现，应用层唯一能碰的是 socket 这层接口：`socket()` 让内核创建一个协议控制块，`bind`/`listen`/`connect` 只是往这个对象里填状态，`read`/`write` 则是在用户缓冲区和内核收发队列之间搬字节。**可靠传输、分包、重传、拥塞控制都由协议栈负责，应用只看到一条字节流**——这是理解后面所有问题的前提。
### 1.1 socket 在内核里是什么
- `struct socket`：系统调用看到的壳，记录类型（`SOCK_STREAM`/`SOCK_DGRAM`）、状态、关联的 `struct file`、等待队列。
- `struct sock`：协议控制块，四元组、TCP 状态机、接收队列 `sk_receive_queue`、发送队列、定时器与回调都挂在它上面；TCP 专用的 `struct tcp_sock` 内嵌其中。
- `struct sk_buff`（skb）：报文的内存载体，穿过协议栈时只改指针，不复制负载。
- `struct file` + fd：`socket()` 返回的整数是进程 fd 表的下标，指向 `struct file`，其 `f_op` 是 `socket_file_ops`，所以 socket 能像文件一样 `read`/`write`/`close`/`poll`。

一句话：**socket 是「协议族 + 类型 + 协议」的内核对象，`struct sock` 是它的协议控制块，fd 只是进程指向这个对象的一个句柄。**
### 1.2 每个调用在内核里做了什么
| 调用 | 内核动作 | 状态变化 |
| --- | --- | --- |
| `socket` | 分配 `struct socket`/`struct sock`，挂到 fd 表 | `CLOSED` |
| `bind` | 记录本地 IP 与端口（`inet_bind`），检查端口占用 | `CLOSED` |
| `listen` | 创建 SYN 队列与 accept 队列，开始收握手包 | `LISTEN` |
| `connect` | 发 SYN，阻塞到握手完成或失败 | `SYN-SENT` → `ESTABLISHED` |
| `accept` | 从 accept 队列取一条已完成握手的连接，**新建一个 fd** | 新 fd 为 `ESTABLISHED` |
| `read`/`write` | 在 skb 队列与用户缓冲区之间拷贝 | `ESTABLISHED` |
| `close` | 引用计数减一，发 FIN（有未读数据则发 RST） | `FIN-WAIT-1`/`LAST-ACK` |

三次握手由内核完成，`accept` 只是取队列——所以「握手成功但应用没 accept」的连接会占满 accept 队列，客户端表现为连上了却没有响应。
### 1.3 文件描述符视角
```bash
ls -l /proc/$$/fd                 # 当前 shell 的 fd 表
ss -tanp | head                   # 内核 socket 表：状态、队列、进程
lsof -p $$ -a -i                  # 进程打开了哪些网络 fd
```
1. `ulimit -n` 决定单进程 fd 上限；每条连接至少占一个 fd，百万连接必须先调 `ulimit`、`fs.file-max` 并算够内存。
2. `dup`/`fork` 共享同一个 `struct file`，引用计数归零才真正关闭；`O_NONBLOCK` 标记在 `struct file` 上，所以 `dup` 出来的 fd 也受影响。
3. socket 在 `sockfs` 上有 inode，但没有磁盘文件和数据偏移，`lseek` 无意义；`read` 返回 0 表示对端发了 FIN，不是「读到文件尾」。

## 2 字节序与地址结构
### 2.1 大端、小端与网络字节序
- 大端（big-endian）：高位字节放在低地址；小端相反。x86 与默认配置的 ARM 都是小端。
- 网络字节序统一是大端，所以主机序与网络序之间的转换不是可选项。
- 只转**多字节整数**：端口 16 位、IPv4 地址 32 位；字符串和 `char` 数组不转。
- `sin_addr.s_addr` 用 `inet_pton` 填好后已经是网络序，**不要再 `htonl`**（最常见的错误）。

| 函数 | 方向 | 宽度 | 典型用途 |
| --- | --- | --- | --- |
| `htons` | 主机 → 网络 | 16 位 | 端口 `sin_port` |
| `htonl` | 主机 → 网络 | 32 位 | IPv4 地址（`INADDR_ANY` 等） |
| `ntohs` | 网络 → 主机 | 16 位 | 打印端口、比较端口 |
| `ntohl` | 网络 → 主机 | 32 位 | 打印地址（一般直接用 `inet_ntop`） |

名字里的 `s`/`l` 是 short/long（16/32 位），与 C 的 `short`/`long` 宽度无关；`htonll` 不是标准接口。
### 2.2 inet_pton / inet_ntop
`inet_addr` 已过时：返回 `in_addr_t`，失败与广播地址 `255.255.255.255` 都返回 `INADDR_NONE`，无法区分；只支持 IPv4；配套的 `inet_ntoa` 用静态缓冲区，不可重入。改用：

| 函数 | 原型要点 | 返回值 |
| --- | --- | --- |
| `inet_pton(af, src, dst)` | 文本 → 二进制，`dst` 为 `struct in_addr *` 或 `struct in6_addr *` | 1 成功、0 格式错、-1 `af` 不支持 |
| `inet_ntop(af, src, dst, size)` | 二进制 → 文本，`size` 用 `INET_ADDRSTRLEN`(16) / `INET6_ADDRSTRLEN`(46) | 成功返回 `dst`，失败返回 `NULL` 并置 `errno` |

判断本机字节序：`*(unsigned char *)&(unsigned int){1}` 为 1 是小端、为 0 是大端；`htons` 与 `ntohs` 成对使用后端口值回到主机序，若把小端的 `sin_port` 当主机序整数直接打印，9000 会显示成 10275（`0x2823`）。
### 2.3 sockaddr_in、sockaddr_storage 与 IPv6
`sockaddr` 是通用占位类型，只有 `sa_family` 有意义；具体地址用 `sockaddr_in`/`sockaddr_in6`，传参时统一强转 `(struct sockaddr *)` 并带长度。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `sin_family` | `sa_family_t` | `AF_INET`；IPv6 用 `sin6_family = AF_INET6` |
| `sin_port` | `in_port_t` | **网络序**，必须 `htons` |
| `sin_addr` | `struct in_addr` | 4 字节网络序地址 |
| `sin_zero[8]` | `char` | 填充，使结构体与 `sockaddr` 等长；用 `memset` 清零 |

- `sockaddr_storage` 足够大（128 字节）且对齐，能装下 `sockaddr_in`、`sockaddr_in6`、`sockaddr_un`；写同时支持 v4/v6 的库时用它接 `accept`/`recvfrom` 的对端地址，再按 `ss_family` 分支。
- IPv6 兼容写法：不写死 `sockaddr_in`，用 `getaddrinfo` 拿链表逐个尝试 `socket(ai_family, ai_socktype, ai_protocol)`；`accept` 用 `sockaddr_storage` + `socklen_t`。
- 双栈：Linux 上 `AF_INET6` socket 默认 `IPV6_V6ONLY=0`，能同时收 IPv4-mapped 地址（`::ffff:1.2.3.4`）；只服务 v6 就显式 `setsockopt(IPPROTO_IPV6, IPV6_V6ONLY, &one, sizeof one)`。
- `sin6_scope_id` 是链路本地地址（`fe80::/10`）的网卡索引，`getaddrinfo` 会填，手写时别漏。

## 3 TCP 服务端完整流程
固定顺序 `socket → bind → listen → accept → read/write → close`；监听 fd 只负责收连接，真正通信的是 `accept` 返回的新 fd。下面的 echo server 是完整可编译版本，重点看错误分支与 `SIGPIPE`。
### 3.1 完整 echo server
```c
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define PORT 9000
#define BACKLOG 128
static int send_all(int fd, const char *buf, size_t len)
{
    for (size_t off = 0; off < len;) {
        ssize_t n = send(fd, buf + off, len - off, MSG_NOSIGNAL);
        if (n < 0) {
            if (errno == EINTR) continue;
            return -1;
        }
        off += (size_t)n;
    }
    return 0;
}

int main(void)
{
    struct sockaddr_in addr;
    char buf[4096];
    int lfd, yes = 1;
    signal(SIGPIPE, SIG_IGN);          /* 对端 RST 后只返回 EPIPE，不杀进程 */
    lfd = socket(AF_INET, SOCK_STREAM, 0);
    if (lfd < 0) { perror("socket"); return 1; }
    if (setsockopt(lfd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof yes) < 0) {
        perror("setsockopt");
        close(lfd);
        return 1;
    }
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(PORT);
    if (bind(lfd, (struct sockaddr *)&addr, sizeof addr) < 0) { perror("bind"); close(lfd); return 1; }
    if (listen(lfd, BACKLOG) < 0) { perror("listen"); close(lfd); return 1; }
    printf("echo server listening on :%d\n", PORT);
    for (;;) {
        struct sockaddr_in peer;
        socklen_t plen = sizeof peer;
        char ip[INET_ADDRSTRLEN];
        int cfd;
        ssize_t n;
        cfd = accept(lfd, (struct sockaddr *)&peer, &plen);
        if (cfd < 0 && (errno == EINTR || errno == ECONNABORTED)) continue;
        if (cfd < 0) { perror("accept"); break; }
        inet_ntop(AF_INET, &peer.sin_addr, ip, sizeof ip);
        printf("accept %s:%d\n", ip, ntohs(peer.sin_port));
        while ((n = read(cfd, buf, sizeof buf)) != 0) {
            if (n < 0) {
                if (errno == EINTR) continue;
                if (errno != ECONNRESET) perror("read");
                break;
            }
            if (send_all(cfd, buf, (size_t)n) < 0) { perror("send"); break; }
        }
        close(cfd);                    /* 演示用：串行处理，一个连接处理完再 accept */
    }
    close(lfd);
    return 0;
}
```

要点：
1. `SO_REUSEADDR` 让重启时能 bind 处于 `TIME_WAIT` 的端口，**必须在 `bind` 前设置**。
2. `SIGPIPE` 默认终止进程：对端已关闭或 RST 后再写，内核发 `SIGPIPE` 并让写操作返回 `EPIPE`。忽略信号后再配合 `MSG_NOSIGNAL` 双保险。
3. `accept` 可能被信号中断（`EINTR`）或遇到已断开的连接（`ECONNABORTED`），重试即可；其他错误才退出。
4. `read` 返回 0 是对端 `close`/`shutdown(SHUT_WR)`，不是错误；返回 -1 且 `EINTR` 要重试，`ECONNRESET` 说明对端发了 RST。
5. 这里单线程串行处理连接，只为看清流程；并发写法见第 7、8 章。

```bash
gcc -std=c11 -Wall -Wextra -O2 echo_server.c -o echo_server
./echo_server &                        # 后台跑，结束用 kill %1
printf 'hello\n' | nc 127.0.0.1 9000
ss -ltnp 'sport = :9000'               # Recv-Q 是 accept 队列当前长度
```

## 4 TCP 客户端完整流程
客户端不用 `bind`（内核自动选源地址和临时端口），`connect` 成功即三次握手完成，之后就是对称的 `write`/`read`。下面把 `connect` 做成带超时版本：**非阻塞 connect + `select` 等可写**，这是线上防止连接卡死的标准写法。
### 4.1 完整 client（含 connect 超时）
```c
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <unistd.h>

static int connect_timeout(const char *ip, unsigned short port, int timeout_ms)
{
    struct sockaddr_in addr;
    struct timeval tv;
    fd_set wset;
    int fd, flags, ret, err;
    socklen_t len;
    fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return -1;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    if (inet_pton(AF_INET, ip, &addr.sin_addr) != 1) { close(fd); errno = EINVAL; return -1; }
    flags = fcntl(fd, F_GETFL, 0);
    if (flags < 0 || fcntl(fd, F_SETFL, flags | O_NONBLOCK) < 0) { close(fd); return -1; }
    ret = connect(fd, (struct sockaddr *)&addr, sizeof addr);
    if (ret == 0) goto restore;                /* 回环等场景可能立即成功 */
    if (errno != EINPROGRESS) { close(fd); return -1; }
    for (;;) {
        FD_ZERO(&wset);
        FD_SET(fd, &wset);
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;
        ret = select(fd + 1, NULL, &wset, NULL, &tv);
        if (ret < 0 && errno == EINTR) continue;
        break;
    }
    if (ret == 0) { close(fd); errno = ETIMEDOUT; return -1; }
    if (ret < 0) { close(fd); return -1; }
    err = 0;
    len = sizeof err;
    if (getsockopt(fd, SOL_SOCKET, SO_ERROR, &err, &len) < 0) { close(fd); return -1; }
    if (err != 0) { close(fd); errno = err; return -1; }
restore:
    if (fcntl(fd, F_SETFL, flags) < 0) { close(fd); return -1; }
    return fd;
}

int main(int argc, char *argv[])
{
    const char *host = argc > 1 ? argv[1] : "127.0.0.1";
    const char *msg = "hello socket\n";
    char buf[4096];
    ssize_t n;
    int fd = connect_timeout(host, 9000, 3000);
    if (fd < 0) { perror("connect_timeout"); return 1; }
    n = send(fd, msg, strlen(msg), MSG_NOSIGNAL);
    if (n < 0 || (size_t)n != strlen(msg)) { perror("send"); close(fd); return 1; }
    n = read(fd, buf, sizeof buf - 1);
    if (n < 0) { perror("read"); close(fd); return 1; }
    buf[n] = '\0';
    printf("echo: %s", buf);
    close(fd);
    return 0;
}
```

关键点：
1. 非阻塞 `connect` 返回 -1 且 `errno == EINPROGRESS` 是**正常**的，表示握手进行中；其他 errno 才是失败。
2. `select` 可写不代表连接成功，必须用 `getsockopt(SO_ERROR)` 取真实结果，这是面试常问的坑。
3. 超时后直接 `close`，内核回收半开连接；把 `errno` 设为 `ETIMEDOUT` 方便上层区分。
4. 连上后把 `O_NONBLOCK` 恢复，后续 `read` 保持阻塞语义；要全程非阻塞就别恢复（epoll 场景必须保持）。
5. 生产代码里地址解析交给 `getaddrinfo`，这里写死 IPv4 是为了聚焦流程。

```bash
gcc -std=c11 -Wall -Wextra -O2 tcp_client.c -o tcp_client
./tcp_client 127.0.0.1
strace -f -e trace=network ./tcp_client 127.0.0.1   # 看 socket/connect/send 的返回值
```

## 5 UDP：无连接的数据报
UDP 只做「加端口、算校验和、交给 IP」，不建连接、不重传、不排序、不去重；每个 `sendto` 是一个独立数据报，`recvfrom` 一次取一个。**没有粘包，但会丢包、乱序、重复**。
### 5.1 sendto / recvfrom 与 echo 示例
```c
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int main(void)
{
    struct sockaddr_in addr;
    char buf[2048];
    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) { perror("socket"); return 1; }
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(9001);
    if (bind(fd, (struct sockaddr *)&addr, sizeof addr) < 0) {
        perror("bind");
        close(fd);
        return 1;
    }
    for (;;) {
        struct sockaddr_in peer;
        socklen_t plen = sizeof peer;
        ssize_t n = recvfrom(fd, buf, sizeof buf, 0, (struct sockaddr *)&peer, &plen);
        if (n < 0) {
            if (errno == EINTR) continue;
            perror("recvfrom");
            break;
        }
        if (sendto(fd, buf, (size_t)n, 0, (struct sockaddr *)&peer, plen) < 0) perror("sendto");
    }
    close(fd);
    return 0;
}
```

- `recvfrom` 的后两个参数回填对端地址，服务端靠它知道回给谁；不关心就传 `NULL`。
- `sendto` 每次都要给目的地址；固定对端可以先 `connect` UDP socket，之后用 `send`/`recv`，内核会过滤其他来源的包。
- 数据报边界保留：发 100 字节，对端要么收到 100 字节，要么收不到，不会变成 60+40。
- 单包上限约 65507 字节（IPv4），但超过 MTU（典型 1500，UDP 载荷 1472）会 IP 分片，任一分片丢失整包丢弃，所以应用层应把包控制在 MTU 以内。
- UDP 没有流控：缓冲满时 `sendto` 可能返回 `ENOBUFS`/`EAGAIN`，靠应用限速。
- 适用场景：DNS、DHCP、NTP、VoIP/游戏/直播（低延迟、可容忍丢包）、QUIC（在 UDP 上自己做可靠传输）、广播/组播。要可靠就在应用层补序号、ACK、重传与拥塞控制。

```bash
gcc -std=c11 -Wall -Wextra -O2 udp_echo.c -o udp_echo
./udp_echo &
printf 'ping' | nc -u -w1 127.0.0.1 9001
```

## 6 阻塞与非阻塞、五种 IO 模型
一次网络 IO 分两段：**等数据就绪**（网卡 → 内核接收队列）和**把数据从内核拷到用户态**。五种模型的差别只在第一段怎么等。
### 6.1 五种 IO 模型
| 模型 | 等数据 | 拷贝数据 | 典型接口 | 特点 |
| --- | --- | --- | --- | --- |
| 阻塞 IO | 阻塞在 `read` | 阻塞 | `read`/`write` | 最简单，一连接一线程，线程数撑不住 |
| 非阻塞 IO | 轮询，无数据立即返回 `EAGAIN` | 阻塞 | `O_NONBLOCK` + `read` | 不阻塞但空转烧 CPU，单独用没意义 |
| IO 多路复用 | 阻塞在 `select`/`poll`/`epoll` | 阻塞 | `epoll_wait` 等 | 一个线程管大量 fd，事件驱动的基础 |
| 信号驱动 IO | 内核 `SIGIO` 通知 | 阻塞 | `O_ASYNC` + `F_SETOWN` | 信号难调试、开销大，很少用 |
| 异步 IO | 不阻塞，内核全程完成 | 内核完成拷贝 | `io_uring`（glibc 的 `aio_*` 是线程模拟） | 真异步，编程复杂，5.1+ 高性能场景新宠 |

### 6.2 设置非阻塞
- `fcntl(fd, F_SETFL, fcntl(fd, F_GETFL, 0) | O_NONBLOCK)`：必须先用 `F_GETFL` 取原标志，直接 `F_SETFL, O_NONBLOCK` 会清掉其他标志。
- `accept4(lfd, NULL, NULL, SOCK_NONBLOCK | SOCK_CLOEXEC)`：一次完成 accept + 非阻塞 + close-on-exec，比 `accept` 后再 `fcntl` 少两次系统调用，也没有竞态。
- 也可以在创建时指定：`socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK, 0)`。
- 非阻塞 fd 上：`read` 无数据、`write` 发送缓冲满、`accept` 无新连接，都返回 -1 且 `errno == EAGAIN`（`EWOULDBLOCK` 同值）。**`EAGAIN` 不是错误，是「现在没有，等通知」**，绝不能当失败去关连接。

## 7 IO 多路复用：select / poll / epoll
### 7.1 select
- `fd_set` 是位图，`FD_SETSIZE` 默认 1024，**编译期固定**；想更大要改 glibc 重编，不现实。
- 每次调用都要 `FD_ZERO` 并重新 `FD_SET` 所有关心的 fd，因为返回时内核会改写集合（只留就绪位）。
- 返回后还要 O(n) 遍历找哪个 fd 就绪；用户态与内核态之间每次都拷贝整个位图。
- `select` 的第一个参数是「最大 fd + 1」，不是 fd 个数，写错会漏掉 fd。
### 7.2 poll
- 用 `struct pollfd { int fd; short events; short revents; }` 数组，没有 1024 限制，`fd` 为负则跳过该项。
- 仍然每次把整个数组拷进内核并 O(n) 扫描，连接多时和 select 一样慢。
- `events` 是关注的事件（`POLLIN`/`POLLOUT`），`revents` 是返回结果；每次调用前要重置 `revents`。超时单位是毫秒，`-1` 永久阻塞。
### 7.3 epoll
| 调用 | 作用 |
| --- | --- |
| `epoll_create1(EPOLL_CLOEXEC)` | 创建 epoll 实例返回 fd；替代废弃的 `epoll_create(size)` |
| `epoll_ctl(epfd, op, fd, &ev)` | `ADD`/`MOD`/`DEL` 注册或修改关注事件，红黑树管理 |
| `epoll_wait(epfd, events, maxevents, timeout)` | 只返回就绪链表里的 fd，O(就绪数) |

- 内核用红黑树存注册的 fd、用就绪链表存已触发事件；`epoll_wait` 只拷贝就绪的那几个，不用每次传全量集合。
- `EPOLL_CTL_ADD` 对同一 fd 重复添加会 `EEXIST`；fd 关闭后会自动从集合移除（`dup` 出来的副本除外）。
- `EPOLLERR`/`EPOLLHUP` 永远会被上报，不用注册；`data` 是 union，可用 `data.fd`，也可用 `data.ptr` 带出连接对象。

**LT 与 ET**：

| 对比项 | 水平触发 LT（默认） | 边缘触发 ET（`EPOLLET`） |
| --- | --- | --- |
| 通知时机 | 缓冲区还有数据，每次 `epoll_wait` 都通知 | 只在状态变化时通知一次 |
| 是否必须读干净 | 不必，可下次再读 | **必须循环读到 `EAGAIN`**，否则剩余数据不再通知 |
| fd 是否必须非阻塞 | 不强制 | 强制，否则最后一次 `read` 会永久阻塞 |
| 编程难度 / 效率 | 简单 / 可能重复通知 | 复杂 / 系统调用更少 |
| 典型使用者 | 多数业务服务 | Nginx、高性能代理 |

ET 的正确写法是 `for (;;) { n = read(...); if (n < 0 && errno == EAGAIN) break; ... }`；多线程下同一 fd 还可能被多个线程同时处理，用 `EPOLLONESHOT` 保证一次只有一个线程，处理完再 `MOD` 重新注册。
### 7.4 三者对比
| 对比项 | select | poll | epoll |
| --- | --- | --- | --- |
| fd 上限 | `FD_SETSIZE`=1024 | 无硬上限（受内存/fd 限制） | 无硬上限 |
| 时间复杂度 | O(n) 每次遍历 | O(n) | O(就绪数) |
| 内核/用户拷贝 | 每次全量位图 | 每次全量数组 | 注册时一次，`wait` 只拷就绪 |
| 触发方式 | 只有 LT | 只有 LT | LT + ET |
| 跨平台 | 最好 | POSIX | 仅 Linux |
| 适用规模 | 几十~几百 | 几百~几千 | 万级以上 |
### 7.5 epoll 版 echo server
```c
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <sys/epoll.h>
#include <sys/socket.h>
#include <unistd.h>

#define PORT 9002
#define MAX_EVENTS 64
int main(void)
{
    struct epoll_event ev, events[MAX_EVENTS];
    struct sockaddr_in addr;
    char buf[4096];
    int lfd, epfd, yes = 1, n, i;
    lfd = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK, 0);   /* 监听 fd 也必须非阻塞 */
    if (lfd < 0) { perror("socket"); return 1; }
    setsockopt(lfd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof yes);
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(PORT);
    if (bind(lfd, (struct sockaddr *)&addr, sizeof addr) < 0) { perror("bind"); return 1; }
    if (listen(lfd, 128) < 0) { perror("listen"); return 1; }
    epfd = epoll_create1(EPOLL_CLOEXEC);
    if (epfd < 0) { perror("epoll_create1"); return 1; }
    ev.events = EPOLLIN;
    ev.data.fd = lfd;
    if (epoll_ctl(epfd, EPOLL_CTL_ADD, lfd, &ev) < 0) { perror("epoll_ctl"); return 1; }
    for (;;) {
        n = epoll_wait(epfd, events, MAX_EVENTS, -1);
        if (n < 0) {
            if (errno == EINTR) continue;
            perror("epoll_wait");
            break;
        }
        for (i = 0; i < n; i++) {
            int fd = events[i].data.fd;
            if (fd == lfd) {
                for (;;) {
                    int cfd = accept4(lfd, NULL, NULL, SOCK_NONBLOCK | SOCK_CLOEXEC);
                    if (cfd < 0) {
                        if (errno == EINTR) continue;
                        if (errno != EAGAIN && errno != EWOULDBLOCK) perror("accept4");
                        break;
                    }
                    ev.events = EPOLLIN;
                    ev.data.fd = cfd;
                    if (epoll_ctl(epfd, EPOLL_CTL_ADD, cfd, &ev) < 0) {
                        perror("epoll_ctl");
                        close(cfd);
                    }
                }
            } else {
                int keep = 1;
                ssize_t r = read(fd, buf, sizeof buf);
                if (r > 0) {
                    /* 简化：一次 send 写完；EAGAIN 应注册 EPOLLOUT 并把剩余数据挂到发送缓冲 */
                    if (send(fd, buf, (size_t)r, MSG_NOSIGNAL) < 0 && errno != EAGAIN) keep = 0;
                } else if (r == 0) {
                    keep = 0;
                } else if (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR) {
                    keep = 0;
                }
                if (!keep) {
                    epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
                    close(fd);
                }
            }
        }
    }
    close(epfd);
    close(lfd);
    return 0;
}
```

核心：监听 fd 本身也要非阻塞并注册进 epoll，`accept` 要循环到 `EAGAIN` 为止；每个连接 fd 设非阻塞；读返回 0 时 `DEL` + `close`。LT 模式下不必一次读完，但 `accept` 必须循环——否则监听 fd 会一直处于就绪态，每次 `epoll_wait` 都重复上报，白白占掉一个事件槽位。

## 8 Reactor 与线程模型
Reactor = 「IO 多路复用 + 事件分发 + 回调」：一个循环等事件，把就绪 fd 交给对应 handler。按「谁 accept、几个线程跑事件循环」分三种。

| 模型 | 结构 | 优点 | 缺点 | 代表 |
| --- | --- | --- | --- | --- |
| 单 Reactor 单线程 | 一个线程 accept + 读 + 算 + 写 | 简单、无锁、无上下文切换 | 一个慢业务阻塞全服，多核浪费 | Redis 的命令处理 |
| 单 Reactor 多线程 | 一个 IO 线程收事件，业务丢线程池 | IO 与计算分离，利用多核 | 共享连接状态要加锁，线程池队列可能堆积 | 多数 Java/Python 框架 |
| 主从 Reactor | 主线程只 accept，从线程组各自跑 epoll | accept 不被业务拖慢，扩展性好 | 实现复杂，连接分配要有策略 | Nginx、Netty、muduo |

- **accept 与业务分离**：`accept` 本身很快，但 TLS 握手、鉴权、建连回调可能慢，放主线程会拖慢新连接。主从模型把新 fd 分给某个从 Reactor（round-robin 或按 fd 哈希），连接生命周期内固定在同一线程，避免锁。
- **线程池配合**：IO 线程只做「读 → 解包 → 投递任务」，业务线程算完把响应写回；写回要么加锁，要么把待写数据投递回 IO 线程，保证同一 fd 只有一个线程写。
- **惊群**：多个线程/进程阻塞在同一监听 fd 上，新连接到来全部被唤醒，只有一个 `accept` 成功，其余白跑。手段：① 只在主线程 `accept` 再分发；② `EPOLLEXCLUSIVE`（Linux 4.5+），多个 epoll 实例挂同一 fd 时内核只唤醒一个；③ `SO_REUSEPORT`（Linux 3.9+），每个 worker 各自 `socket` + `bind` 同一端口，内核按四元组哈希分流，天然无惊群。
- `SO_REUSEPORT` 注意：要求同一 UID、都在 `bind` 前设置；每个 socket 有独立监听队列，短连接多时可能哈希不均；重启时新旧进程可短暂共存，能实现平滑发布。

## 9 常见问题与排查
### 9.1 粘包与拆包
TCP 是字节流，没有消息边界：两次 `write` 可能被合并到达（Nagle、拥塞窗口、接收缓冲），一次 `write` 也可能被拆成多段。**UDP 有边界，不存在这个问题。**

| 方案 | 做法 | 优点 | 缺点 |
| --- | --- | --- | --- |
| 定长 | 每条消息固定 N 字节，不够补零 | 实现最简单 | 浪费带宽，长度不灵活 |
| 分隔符 | 用 `\n`、`\0` 等结尾，如 HTTP 头 | 可读性好，适合文本协议 | 内容含分隔符要转义，需扫描 |
| 长度前缀 | 先发 4 字节大端长度，再发 body | 二进制友好、可预分配、效率高 | 长度字段本身也要处理拆包 |

工程上还要配「读缓冲 + 状态机」：把 `read` 到的数据追加到连接缓冲区，循环按协议切出完整包，剩下的留到下次；长度字段必须做上限校验，防止恶意长度导致 OOM。
### 9.2 TIME_WAIT 过多
- 主动关闭方进入 `TIME_WAIT`，等 2MSL（Linux 的 MSL=30s，即约 60s），目的是让最后一个 ACK 丢失时对端重发的 FIN 仍能被 ACK，同时让旧连接的迟到报文在网络中过期。
- 它是**正常状态**，不是泄漏；短连接多、并发高时数量大是必然的，先考虑连接池/长连接。
- 调优：`net.ipv4.tcp_tw_reuse=1` 只对**主动发起**的连接生效且要求时间戳；`tcp_max_tw_buckets` 只是限制上限，超了直接销毁并打日志；`tcp_tw_recycle` 在 4.12 已移除，不要再用。
- `tcp_fin_timeout` 管的是 `FIN_WAIT_2`，不是 `TIME_WAIT`，这是常见误答。
### 9.3 CLOSE_WAIT 堆积
对端发了 FIN，本端内核回 ACK 后进入 `CLOSE_WAIT`，**等应用调用 `close()`**。堆积说明代码漏关 fd：异常分支没关、连接对象被缓存没释放、回调里忘了 `close`。用 `ss -tan state close-wait` 找到端口与进程，再查 fd 泄漏（`lsof -p PID | wc -l`）。
### 9.4 SIGPIPE 导致进程退出
往已收到 RST 的 socket 写数据，内核发 `SIGPIPE`，默认动作是终止进程，而且不会留下任何错误日志——服务「莫名其妙挂了」的常见原因。处理：`signal(SIGPIPE, SIG_IGN)` 全局忽略，写操作改用 `send(..., MSG_NOSIGNAL)`，并检查 `EPIPE`。
### 9.5 EAGAIN / EWOULDBLOCK
非阻塞 fd 上表示「暂时不可读写」，两者在 Linux 上值相同。正确处理是**等待事件**（epoll 注册 `EPOLLIN`/`EPOLLOUT`），而不是 `while` 重试；`EINTR` 才是「被信号打断，直接重试」。把 `EAGAIN` 当错误关连接，会造成随机断连。
### 9.6 端口复用与半关闭
| 选项 | 作用 | 使用场景 |
| --- | --- | --- |
| `SO_REUSEADDR` | 允许 bind 处于 `TIME_WAIT` 的端口；允许更具体的地址绑定 | 服务端重启必开 |
| `SO_REUSEPORT` | 多个 socket 绑同一端口，内核分流 | 多进程负载均衡、平滑重启 |

- 两者都要在 `bind` 前设置，只影响 bind，不影响 connect。
- `shutdown(fd, SHUT_WR)` 发 FIN 但保留读方向，用于「请求发完了，还在等响应」的半关闭；`close` 是双向的，且只减引用计数。
- `shutdown(SHUT_RDWR)` 可唤醒阻塞在 `read` 的线程；`SHUT_RD` 在 TCP 上通常不发报文。

## 10 性能与调优
### 10.1 常用 socket 选项
| 选项 | 默认 | 作用与建议 |
| --- | --- | --- |
| `TCP_NODELAY` | 0（开 Nagle） | 禁用 Nagle，小包立即发；RPC/游戏/交互式协议必开，大文件传输可关 |
| `SO_KEEPALIVE` | 0 | 默认 2 小时无数据才探测，太长；用应用层心跳更可控 |
| `SO_SNDBUF` / `SO_RCVBUF` | 内核自动调整 | 设置后内核会翻倍（含开销），受 `wmem_max`/`rmem_max` 限制；高带宽时延积链路要调大 |
| `SO_LINGER` | 关 | 设 `l_onoff=1, l_linger=0` 时 `close` 发 RST、跳过 `TIME_WAIT`，但会丢未发数据，慎用 |
| `TCP_CORK` | 0 | 攒包再发，适合「头 + body」连续写；写完记得置 0 或 `close` |

- **Nagle**：有未确认的小包时，后续小包攒着等 ACK 或攒够 MSS 再发；和接收方的**延迟 ACK**（最多 40ms）叠加会产生明显延迟，所以交互式协议关掉它。
- **keepalive 参数**：`tcp_keepalive_time`（7200）、`tcp_keepalive_intvl`（75）、`tcp_keepalive_probes`（9）；按连接设置用 `TCP_KEEPIDLE`/`TCP_KEEPINTVL`/`TCP_KEEPCNT`。
### 10.2 backlog 与 accept 队列
- `listen(fd, backlog)` 的 backlog 是 **accept 队列**（已完成三次握手、等应用 accept）的长度上限，内核还会用 `net.core.somaxconn` 截断；SYN 队列受 `tcp_max_syn_backlog` 影响。
- 队列满时：SYN 队列满丢 SYN（客户端重传）；accept 队列满默认丢新 ACK（客户端以为连上了，服务端却不处理），`tcp_abort_on_overflow=1` 则回 RST。
- 观察：`ss -lnt` 的 `Recv-Q` 是当前 accept 队列长度、`Send-Q` 是 backlog 上限；`ListenOverflows`/`ListenDrops` 持续增长就是溢出。

```bash
ss -lnt                                          # Recv-Q/Send-Q 看队列
nstat -az | grep -iE 'ListenOverflows|ListenDrops'
sysctl net.core.somaxconn net.ipv4.tcp_max_syn_backlog
sysctl -w net.core.somaxconn=4096                # 持久化写 /etc/sysctl.d/
```
### 10.3 零拷贝 sendfile
原型是 `ssize_t sendfile(int out_fd, int in_fd, off_t *offset, size_t count);`，`in_fd` 必须是普通文件，`out_fd` 必须是 socket。传统 `read` + `write` 要四次拷贝（磁盘 → 页缓存 → 用户 → socket 缓冲 → 网卡）和四次上下文切换；`sendfile` 省掉用户态这一环，通常剩三次拷贝和两次上下文切换，网卡支持 SG-DMA 时可由网卡直接从页缓存取数据，CPU 拷贝再省一次，才真正接近「零拷贝」。

约束：`in_fd` 必须是支持 `mmap` 的文件（不能是 socket），`out_fd` 必须是 socket；数据不能修改，所以 HTTPS 用不了（除非 kTLS）；`splice` 可在两个 fd 之间搬数据，`copy_file_range` 适合文件到文件。

## 11 面试问答
1. **socket 是文件吗？** 从用户态看是：`socket()` 返回 fd，能 `read`/`write`/`close`/`select`，`/proc/<pid>/fd` 里也能看到。但它在 `sockfs` 上，没有磁盘文件和数据偏移，内核里对应 `struct socket` + `struct sock`；「一切皆文件」是接口统一，不是实现相同。
2. **epoll 为什么快？** 注册一次，内核用红黑树管理 fd、用就绪链表记录事件；`epoll_wait` 只返回就绪的 fd，不用每次传全量集合，也不遍历所有 fd。select/poll 每次都要拷贝并 O(n) 扫描，fd 越多差距越大。
3. **ET 和 LT 的区别？** LT 只要缓冲区还有数据就反复通知，不读干净也行；ET 只在状态变化时通知一次，必须循环读到 `EAGAIN`，且 fd 必须非阻塞。ET 系统调用更少，但漏读会让连接「卡死」。
4. **粘包怎么解决？** 根因是 TCP 字节流没有消息边界，与「发送次数」无关。三种方案：定长、分隔符、长度前缀；工程上用读缓冲 + 状态机切包，并给长度字段加上限。UDP 有边界，不需要处理。
5. **TIME_WAIT 为什么要 2MSL？** 一是最后一个 ACK 丢失时，对端重发的 FIN 还能收到 ACK；二是让旧连接的重复报文在网络中过期，避免污染使用同一四元组的新连接。Linux 下 MSL=30s，所以约 60s。
6. **一个连接占多少内存？** 内核侧空闲连接约 2~3 KB（`struct sock`/`tcp_sock`、`struct file`、dentry 等），加收发缓冲后通常 10 KB 量级；`ss -m` 能看 `skmem`，缓冲受 `tcp_rmem`/`tcp_wmem` 自动调整影响。百万连接粗算 10 GB 起步，还要算应用层对象。
7. **如何实现百万连接？** epoll + 少量事件循环线程（不要一连接一线程）；提高 `ulimit -n`、`fs.file-max`、`somaxconn`、`tcp_max_syn_backlog`；控制每连接内存（小缓冲、避免应用层大对象）；`SO_REUSEPORT` 多进程分摊；用时间轮/心跳清理死连接。
8. **accept 发生在三次握手之后吗？** 是。握手由内核完成，完成的连接进入 accept 队列，`accept` 只是把队列里的连接取出来新建 fd。所以「握手成功但没 accept」会占满队列，客户端表现为连上但无响应。
9. **UDP 会粘包吗？** 不会，UDP 保留消息边界，一次 `sendto` 对应一次 `recvfrom`（或者整包丢失）。但 UDP 会丢包、乱序、重复，需要应用层自己做序号、ACK、重传。
10. **SO_REUSEADDR 和 SO_REUSEPORT 有什么区别？** `SO_REUSEADDR` 解决重启时 bind `TIME_WAIT` 端口的问题；`SO_REUSEPORT` 允许多个 socket 同时绑同一端口，由内核按四元组哈希分流，用于多进程负载均衡。两者都要在 `bind` 前设置。
11. **sendfile 为什么快？** 数据不经过用户态，页缓存直接挂到 socket 发送队列，由 DMA 发到网卡，减少两次拷贝和两次上下文切换。缺点是不能修改数据（HTTPS 需 kTLS）、只能文件到 socket。
12. **为什么写 socket 会收到 SIGPIPE？** 对端已关闭或 RST 后继续写，内核发 `SIGPIPE`，默认终止进程。忽略信号并用 `MSG_NOSIGNAL`，再处理 `EPIPE`；这也是「服务突然退出、日志却无异常」的常见原因。

自测建议：合上文档手写一遍 echo server 与 epoll 版本，再用 `ss`、`strace`、`nstat` 各验证一次；协议细节回看 [计算机网络](../计算机网络/计算机网络.md) 的传输层章节。
