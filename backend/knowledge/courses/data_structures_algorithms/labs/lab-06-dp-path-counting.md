# 实验六 路径计数 DP

**lab_id**: `lab-06-dp-path-counting` · **chapter_id**: `ch11-dynamic-programming`

## 学习目标

- 建立网格路径 **动态规划** 模型。
- 实现 `unique-paths` 与空间优化一行滚动。

## 核心概念

- 状态 `dp[i][j]`：到格子 \((i,j)\) 的路径数。

## 关键算法或数据结构

- 转移：来自上方与左方；障碍格初始化。

## 常见误区

- 第一行第一列初始化漏障碍。

## 课堂案例

- 3×3 网格手填 DP 表。

## 实操练习

1. OJ `unique-paths`。
2. 扩展：有障碍的 unique paths II（选做）。

## 可生成资源建议

- **trace_animation**：DP 表填格过程。

## 和 OJ/Trace 的结合点

- matrix 视图展示 **动态规划** 数组更新。
