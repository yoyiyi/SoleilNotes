## 1 简介

「算法小抄」的核心不是背题，而是提炼**一套可复用的框架**：绝大多数算法题都可以归结为「遍历一个数据结构，并在遍历过程中做选择」，区别只在于遍历顺序、状态定义和剪枝方式。

* 计算机解决问题的本质是穷举，算法优化的本质是「聪明地穷举」——用记忆化、有序性、单调性去掉重复计算。
* 遇到新题先归类：它属于二叉树、动态规划、回溯、BFS、二分、滑动窗口、双指针中的哪一类，再套对应框架；框架负责「骨架」，题目负责「细节」。

| 框架 | 解决的问题 | 核心要素 |
| --- | --- | --- |
| 二叉树遍历 | 递归类问题、树/图上的搜索 | 前中后序位置 |
| 动态规划 | 最值、计数、可行性 | 状态、选择、转移方程、base case |
| 回溯 | 求所有解（排列/组合/子集） | 路径、选择列表、结束条件 |
| BFS | 最短路径、层序遍历 | 队列、visited、层数 |
| 二分查找 | 有序数据上找目标/边界 | 搜索区间、循环不变量 |
| 滑动窗口 | 连续子数组/子串 | 左右指针、窗口内统计量 |
| 双指针 | 原地修改、有序数组求和 | 快慢指针、左右指针 |
| 单调栈 | 下一个更大/更小元素 | 栈内单调性 |
| 并查集 | 连通性、集合合并 | parent 数组、路径压缩 |
| 前缀和/差分 | 区间求和、区间加减 | 预处理数组 |

## 2 数据结构的存储方式

* 数组（顺序存储）：内存连续，随机访问 O(1)，插入删除 O(n)，扩容有拷贝代价。
* 链表（链式存储）：内存不连续，访问 O(n)，已知前驱时插入删除 O(1)，每个节点有指针开销。
* 其他结构都是这两种的「上层建筑」：栈和队列可用数组或链表实现；哈希表是「数组 + 拉链」；堆是完全二叉树，直接用数组存储；图用邻接表或邻接矩阵。

```java
class Solution {
    // 数组：连续内存，下标随机访问
    public int arraySum(int[] nums) {
        int sum = 0;
        for (int i = 0; i < nums.length; i++) sum += nums[i];
        return sum;
    }

    // 链表：节点离散，靠 next 指针跳转
    public int listSum(ListNode head) {
        int sum = 0;
        for (ListNode p = head; p != null; p = p.next) sum += p.val;
        return sum;
    }
}
```

## 3 二叉树遍历框架

* 递归三要素：确定函数语义（参数与返回值）、确定 base case、确定单层递归逻辑。
* 前序位置在「刚进入节点」时执行，适合自顶向下传递信息（深度、路径）；中序位置在「左子树处理完」时执行，二叉搜索树的中序遍历天然有序。
* 后序位置在「左右子树都处理完」时执行，适合自底向上汇总信息（高度、直径）。

```java
class Solution {
    void traverse(TreeNode root) {
        if (root == null) return;
        // 前序位置：刚进入节点，自顶向下传信息
        traverse(root.left);
        // 中序位置：左子树处理完，BST 的中序有序
        traverse(root.right);
        // 后序位置：左右子树都处理完，自底向上汇总
    }
}
```

**例题：104. 二叉树的最大深度**

```java
class Solution {
    public int maxDepth(TreeNode root) {
        if (root == null) return 0;
        // 后序位置：先拿到左右子树高度，再汇总
        return Math.max(maxDepth(root.left), maxDepth(root.right)) + 1;
    }
}
```

## 4 动态规划框架

动态规划 = 穷举 + 消除重叠子问题，按下面五步走：

* 状态定义：`dp[i]` 表示什么，必须能用一句话说清，并明确是「以 i 结尾」还是「前 i 个」。
* 选择：每个状态有哪几种转移来源（选或不选、拿哪个硬币、走哪一步）。
* 转移方程：`dp[i] = f(dp[i-1], ...)`，写不出方程说明状态定义有问题。
* 遍历顺序：保证依赖的状态已经算出来（一维正向/反向、二维行优先或斜向）。
* base case：最小子问题的答案，以及「不可达」状态用什么哨兵值表示。

| 写法 | 方向 | 空间 | 适用场景 |
| --- | --- | --- | --- |
| 备忘录递归 | 自顶向下 | O(n) 栈 + O(n) 表 | 依赖复杂、不好定遍历顺序 |
| dp 数组 | 自底向上 | O(n) 或 O(n*m) | 绝大多数题，可读性好 |
| 递推（滚动变量） | 自底向上 | O(1) | 状态只依赖前一两项时 |

**例题：322. 零钱兑换（备忘录版本）**

```java
class Solution {
    public int coinChange(int[] coins, int amount) {
        int[] memo = new int[amount + 1];
        Arrays.fill(memo, -666); // -666 表示还没算过
        return dp(coins, amount, memo);
    }
    private int dp(int[] coins, int amount, int[] memo) {
        if (amount == 0) return 0;
        if (amount < 0) return -1;
        if (memo[amount] != -666) return memo[amount];
        int res = Integer.MAX_VALUE;
        for (int coin : coins) {
            int sub = dp(coins, amount - coin, memo);
            if (sub != -1) res = Math.min(res, sub + 1);
        }
        return memo[amount] = res == Integer.MAX_VALUE ? -1 : res;
    }
}
```

同一个题的 dp 数组版本，省掉递归栈，也是面试更常写的版本：

```java
class Solution {
    public int coinChange(int[] coins, int amount) {
        int[] dp = new int[amount + 1];
        Arrays.fill(dp, amount + 1); // 哨兵：比任何合法答案都大
        dp[0] = 0;
        for (int i = 1; i <= amount; i++) {
            for (int coin : coins) {
                if (i - coin < 0) continue;
                dp[i] = Math.min(dp[i], dp[i - coin] + 1);
            }
        }
        return dp[amount] == amount + 1 ? -1 : dp[amount];
    }
}
```

递推写法（滚动变量）：只保留 `dp[i-1]` 和 `dp[i-2]` 两个变量，以 198. 打家劫舍为例，核心就是 `int next = Math.max(cur, prev + num); prev = cur; cur = next;`，最后返回 `cur`。

## 5 回溯框架

* 回溯 = 递归遍历一棵决策树，本质是 DFS，时间复杂度通常是指数级。
* 三个要素：路径（已做的选择）、选择列表（当前能做的选择）、结束条件（到达叶子）；关键动作固定为三步：做选择 → 递归进入下一层 → 撤销选择。
* 组合、子集类问题用 `start` 控制选择范围；含重复元素时先排序，再用 `if (i > start && nums[i] == nums[i - 1]) continue;` 剪枝。

```java
class Solution {
    private List<List<Integer>> res = new ArrayList<>();

    public List<List<Integer>> permute(int[] nums) {
        LinkedList<Integer> track = new LinkedList<>();
        boolean[] used = new boolean[nums.length];
        backtrack(nums, track, used);
        return res;
    }

    private void backtrack(int[] nums, LinkedList<Integer> track, boolean[] used) {
        if (track.size() == nums.length) {
            res.add(new LinkedList<>(track)); // 必须拷贝，否则存的是同一个引用
            return;
        }
        for (int i = 0; i < nums.length; i++) {
            if (used[i]) continue;
            track.add(nums[i]); // 做选择
            used[i] = true;
            backtrack(nums, track, used);
            track.removeLast(); // 撤销选择
            used[i] = false;
        }
    }
}
```

**例题：46. 全排列** 就是上面这段代码，输入 `[1,2,3]` 输出 6 个排列。

## 6 BFS 框架

* BFS 用队列逐层扩展，第一次到达目标时的层数就是最短距离（前提是边权相同）；模板四要素：队列、visited（图必须，树可省）、深度/步数、一次 for 循环处理一整层。
* 与 DFS 的区别：BFS 空间换时间，适合找最短；DFS 适合枚举所有路径。图上的 BFS 要在**入队时**标记 visited，出队时标记会重复入队。

```java
class Solution {
    public int minDepth(TreeNode root) {
        if (root == null) return 0;
        Queue<TreeNode> queue = new LinkedList<>();
        queue.offer(root);
        int depth = 1;
        while (!queue.isEmpty()) {
            int size = queue.size();
            for (int i = 0; i < size; i++) {
                TreeNode cur = queue.poll();
                if (cur.left == null && cur.right == null) return depth; // 首次遇叶子即最短
                if (cur.left != null) queue.offer(cur.left);
                if (cur.right != null) queue.offer(cur.right);
            }
            depth++;
        }
        return depth;
    }
}
```

**例题：111. 二叉树的最小深度** 即上面代码；若求图上最短路径，把树换成图并加上 visited 集合即可。

## 7 二分查找框架

* 先明确搜索区间：`[left, right]`（左闭右闭）时循环条件写 `left <= right`；`[left, right)`（左闭右开）时写 `left < right`，两种写法不能混用；`mid` 统一写 `left + (right - left) / 2`，避免 `left + right` 溢出。
* 找左边界：`nums[mid] == target` 时继续收缩右边界；找右边界：相等时继续收缩左边界。34 题「第一个和最后一个位置」就是两者组合。

```java
class Solution {
    // 例题 704. 二分查找：左闭右闭区间
    public int search(int[] nums, int target) {
        int left = 0, right = nums.length - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (nums[mid] == target) return mid;
            else if (nums[mid] < target) left = mid + 1;
            else right = mid - 1;
        }
        return -1;
    }
    // 左边界：第一个 >= target 的下标（左闭右开区间）
    private int leftBound(int[] nums, int target) {
        int left = 0, right = nums.length;
        while (left < right) {
            int mid = left + (right - left) / 2;
            if (nums[mid] < target) left = mid + 1;
            else right = mid;
        }
        return left; // 可能等于 nums.length，表示不存在
    }
    // 右边界：最后一个 <= target 的下标
    private int rightBound(int[] nums, int target) {
        int left = 0, right = nums.length;
        while (left < right) {
            int mid = left + (right - left) / 2;
            if (nums[mid] <= target) left = mid + 1;
            else right = mid;
        }
        return left - 1; // 可能等于 -1，表示不存在
    }
}
```

## 8 滑动窗口框架

* 右指针负责扩张窗口，左指针负责在窗口不合法时收缩，窗口内维护「统计量」（计数数组、和、哈希表）；适用条件是求连续子数组/子串，且扩张与收缩具有单调性。
* 求最小窗口：在 `while (窗口满足条件)` 里先更新答案再收缩；求最大窗口：在收缩完成后更新答案。

```java
class Solution {
    // 例题 3. 无重复字符的最长子串
    public int lengthOfLongestSubstring(String s) {
        int[] count = new int[128];
        int left = 0, right = 0, res = 0;
        while (right < s.length()) {
            char c = s.charAt(right++);
            count[c]++;
            while (count[c] > 1) { // 窗口内出现重复，收缩左边界
                count[s.charAt(left++)]--;
            }
            res = Math.max(res, right - left);
        }
        return res;
    }
}
```

76. 最小覆盖子串、567. 字符串的排列都是同一模板，只是「统计量」不同：前者用两个哈希表并维护 `valid` 计数，后者用长度为 26 的定长数组。

## 9 双指针技巧

* 快慢指针：慢指针指向「已处理区」末尾，快指针探路，用于原地去重、原地删除、判断链表环、找链表中点。
* 左右指针：从两端向中间收缩，用于有序数组两数之和、反转数组/字符串、二分查找；分离双指针则分别在两个数组/链表上移动，用于合并两个有序数组、求交集。

```java
class Solution {
    // 例题 26. 删除有序数组中的重复项
    public int removeDuplicates(int[] nums) {
        if (nums.length == 0) return 0;
        int slow = 0;
        for (int fast = 0; fast < nums.length; fast++) {
            if (nums[fast] != nums[slow]) {
                slow++;
                nums[slow] = nums[fast];
            }
        }
        return slow + 1;
    }
}
```

左右指针的典型用法是 167. 两数之和 II：`left = 0`、`right = n - 1`，和小于目标就 `left++`，和大于目标就 `right--`。

## 10 单调栈

* 单调栈解决「下一个更大/更小元素」这一类问题：栈里存下标，人为保持栈内元素单调。
* 求下一个更大元素：从右往左遍历，栈内保持递减，当前元素把比它小的都弹掉；求下一个更小元素时栈内保持递增。
* 每个元素最多进栈一次、出栈一次，所以时间复杂度 O(n)，空间 O(n)。

```java
class Solution {
    // 例题 739. 每日温度
    public int[] dailyTemperatures(int[] temperatures) {
        int n = temperatures.length;
        int[] res = new int[n];
        Deque<Integer> stack = new ArrayDeque<>(); // 存下标，栈底到栈顶递减
        for (int i = n - 1; i >= 0; i--) {
            while (!stack.isEmpty() && temperatures[stack.peek()] <= temperatures[i]) stack.pop();
            res[i] = stack.isEmpty() ? 0 : stack.peek() - i;
            stack.push(i);
        }
        return res;
    }
}
```

## 11 并查集

* 两个核心操作：`find(x)` 找根节点，`union(a, b)` 合并两个集合。
* 路径压缩：`find` 时把路径上所有节点直接挂到根上，均摊复杂度接近 O(1)；按秩/按大小合并可进一步降低树高，但有路径压缩后通常可以省略。
* 典型应用：连通分量个数、朋友圈/省份数量、等式方程可满足性、Kruskal 最小生成树。

```java
class Solution {
    // 例题 547. 省份数量
    private int[] parent;
    private int count;

    public int findCircleNum(int[][] isConnected) {
        int n = isConnected.length;
        parent = new int[n];
        count = n;
        for (int i = 0; i < n; i++) parent[i] = i;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                if (isConnected[i][j] == 1) union(i, j);
            }
        }
        return count;
    }
    private int find(int x) {
        if (parent[x] != x) parent[x] = find(parent[x]); // 路径压缩
        return parent[x];
    }
    private void union(int a, int b) {
        int rootA = find(a), rootB = find(b);
        if (rootA == rootB) return;
        parent[rootA] = rootB;
        count--;
    }
}
```

## 12 前缀和与差分数组

* 前缀和：`preSum[i]` 表示前 i 个元素之和，区间 `[left, right]` 的和为 `preSum[right + 1] - preSum[left]`，单次查询 O(1)。
* 前缀和 + 哈希表：把「子数组和为 k」转化为「`preSum[j] - preSum[i] == k`」，即查 `preSum[i] == preSum[j] - k` 是否出现过。
* 差分数组：`diff[i] = a[i] - a[i - 1]`，对区间 `[l, r]` 整体加 v 只需 `diff[l] += v; diff[r + 1] -= v;`，最后做一次前缀和还原。两者互为逆运算：一个查询快，一个修改快。

```java
class NumArray {
    // 例题 303. 区域和检索 - 数组不可变
    private int[] preSum;

    public NumArray(int[] nums) {
        preSum = new int[nums.length + 1];
        for (int i = 1; i <= nums.length; i++) preSum[i] = preSum[i - 1] + nums[i - 1];
    }

    public int sumRange(int left, int right) {
        return preSum[right + 1] - preSum[left];
    }
}
```

差分数组：1109. 航班预订统计

```java
class Solution {
    public int[] corpFlightBookings(int[][] bookings, int n) {
        int[] diff = new int[n + 1];
        for (int[] b : bookings) {
            diff[b[0] - 1] += b[2];
            diff[b[1]] -= b[2];
        }
        for (int i = 1; i < n; i++) diff[i] += diff[i - 1]; // 前缀和还原
        return Arrays.copyOf(diff, n);
    }
}
```

## 13 刷题方法论

* 不要盲目刷题：按框架归类，同一框架下集中刷 5~10 道，形成肌肉记忆，比散着刷 100 道有效。
* 一题多解：每道题至少想清楚暴力解、框架解、最优解，并比较时间与空间复杂度，面试时先讲最优解再补充其他思路。
* 三遍法：第一遍看思路并写出代码，第二遍隔天默写，第三遍一周后复盘，能独立写出来才算掌握。
* 推荐顺序：二叉树遍历 → 回溯 → 动态规划 → BFS/DFS → 二分查找 → 滑动窗口/双指针 → 单调栈/并查集 → 前缀和技巧。
* 记录错题：写清「卡在哪一步」「正确思路的关键点」「下次靠什么特征识别出这个框架」，而不是只抄一份答案。
* 面试表达：先说思路和复杂度，再动手写代码，最后主动用边界用例（空输入、单元素、重复元素、越界）自测。
* 学框架的目的是「不用想就能写出骨架」，把思考留给题目本身的细节，这才是小抄真正的价值。
