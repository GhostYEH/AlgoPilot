# 项目二 校园导航图建模

**project_id**: `project-02-campus-navigation-graph` · **chapter_id**: `ch14-comprehensive-project`

## 学习目标

- 将校园路网抽象为图 \(G=(V,E)\)。
- 用 **图的 BFS** 求无权路网最短路步数（或站点数）。

## 核心概念

- 顶点：路口/建筑；边：道路；权值 1（入门）。

## 关键算法或数据结构

- 邻接表建图；BFS 层次遍历；可选 DFS 连通性检查。

## 常见误区

- 有向道路只建单向边导致路径错误。

## 课堂案例

- 5 个站点小图手算 BFS 最短路。

## 实操练习

1. 提交邻接表代码与 3 组查询样例输出。
2. 说明与 Dijkstra 扩展关系（选做阅读）。

## 可生成资源建议

- **mindmap**：图建模步骤。
- **code_case**：BFS 模板 + 建图 TODO。

## 和 OJ/Trace 的结合点

- BFS 队列 Trace；可选生成 **trace_animation** 资源入库。
