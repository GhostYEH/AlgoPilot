# 第 7 章 查找（二分、哈希）

**chapter_id**: `ch07-search` · **module_keys**: `hash-table`

## 学习目标

- 掌握有序数组二分查找循环不变式。
- 理解哈希表平均 \(O(1)\) 查找与冲突处理。
- 能在题目中选择 `map`/`set` 或有序结构。

## 核心概念

- **二分查找**：在单调有序序列上每次排除一半。
- **哈希函数**：键映射到桶；冲突：拉链法、开放寻址。
- **查找 ADT**：静态查找 vs 动态查找。

## 关键算法或数据结构

- 二分模板：`while left <= right`，中点 `mid`，收缩区间。
- 哈希表：两数之和、字母异位词、频次统计。
- BST 查找：与第 5 章衔接。

## 常见误区

- 二分 `mid` 溢出（Python 用 `left + (right-left)//2`）。
- 有序性破坏仍用二分。
- 误以为哈希最坏也是 \(O(1)\)。

## 课堂案例

- 手写 `binary-search` 边界：找第一个 ≥ target 的位置。
- 两数之和：暴力 \(O(n^2)\) vs 哈希 \(O(n)\)。

## 实操练习

1. 实现 lower_bound 二分变体。
2. 哈希表统计字母频次。
3. 平台 `hash-table` 模块练习。

## 可生成资源建议

- **exercises**：二分边界选择题。
- **document**：哈希均摊复杂度说明。

## 和 OJ/Trace 的结合点

- 二分 Trace 展示 `left/right/mid` 与 `nums[mid]` 比较结果。
- 哈希题 Trace 可展示 map 键值对插入（associative 视图）。
