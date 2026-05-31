# 《数据结构与算法》课程大纲

**课程编号**：CS-DSA-101  
**课程名称**：数据结构与算法  
**学分学时**：64 学时  
**适用专业**：计算机类、软件工程、人工智能、信息安全等  

## 课程定位

本课程是高校计算机类专业核心课，讲授抽象数据类型、经典算法范式、复杂度分析与课内编程实践。AlgoPilot 以本大纲为 **课程级知识库**（`course_id: data_structures_algorithms`），支撑多智能体资源生成、RAG 检索与学习路径规划。

## 章节一览

| 章 | 章节 ID | 主题 | 先修 |
|----|---------|------|------|
| 1 | ch01-introduction-complexity | 绪论与复杂度 | — |
| 2 | ch02-linear-list | 线性表 | ch01 |
| 3 | ch03-stack-queue | 栈与队列 | ch02 |
| 4 | ch04-string | 字符串与双指针 | ch02, ch03 |
| 5 | ch05-tree-binary-tree | 树与二叉树 | ch03 |
| 6 | ch06-graph | 图与 BFS/DFS | ch05, ch03 |
| 7 | ch07-search | 查找 | ch02, ch05 |
| 8 | ch08-sorting | 排序 | ch02, ch01 |
| 9 | ch09-recursion-divide-conquer | 递归与分治 | ch05, ch08 |
| 10 | ch10-greedy | 贪心 | ch08, ch05 |
| 11 | ch11-dynamic-programming | 动态规划 | ch09, ch10 |
| 12 | ch12-backtracking | 回溯 | ch09, ch05 |
| 13 | ch13-heap-union-find | 堆与并查集 | ch05, ch06 |
| 14 | ch14-comprehensive-project | 综合项目 | ch11, ch06, ch12 |

## 实践环节

- **实验**：`labs/` 下 6 个课内实验（复杂度、链表、栈队列、树遍历、图搜索、DP 路径计数）
- **项目**：`projects/` 下 2 个综合项目（Trace 调试器、校园导航图）

## 与平台模块映射

课程章节通过 `course_manifest.yaml` 的 `module_keys` 字段关联平台学习模块（如 `array`、`dp`、`graph`），便于 OJ 题单、Trace 动画与路径 Agent 统一调度。
