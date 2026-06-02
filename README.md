# Co-Sight Competition Edition

基于 Co-Sight 的竞赛增强版本，针对复杂检索、多步推理和事实验证类任务进行了优化，在不修改原有 Agent 工作流的前提下，通过新增竞赛模式提升答案准确率、执行稳定性和推理质量。

## ✨ 特性

- 竞赛模式开关（Mode Switch）
- 竞赛专用 Prompt 工程
- 工具超时保护机制
- 工具错误压缩与容错
- 长上下文管理策略
- Final Answer 自动捕获
- Wikipedia 专项工具集
- 检索结果清洗与优化

---

## 🚀 设计理念

本项目遵循：

> 不修改原有流程，只增加竞赛能力。

所有竞赛相关优化均通过独立模块实现，通过模式开关启用，避免对原有框架进行侵入式修改。

核心目标：

- 提高答案准确率
- 提高轨迹质量
- 提高执行稳定性
- 提高复杂问题解决能力

---

## 🔧 核心优化

### Prompt 工程

新增竞赛专用 System Prompt 与 Task Prompt，引导模型采用：

```text
问题分析
→ 任务拆解
→ 证据收集
→ 工具计算
→ 最终回答
```

减少模型直接猜测答案的情况。

### 工具超时保护

针对搜索工具、网络请求等容易卡死的问题，增加统一 Timeout 包装器：

- 超时自动终止
- 不阻塞主流程
- 支持重新规划执行路径

### 工具错误优化

工具异常不再返回大量 Traceback，而是压缩为简洁错误信息。

优点：

- 减少 Token 消耗
- 防止错误污染上下文
- 提高推理稳定性

### 长上下文保护

针对竞赛任务中 Prompt、搜索结果和推理轨迹过长的问题，增加上下文管理策略。

目标：

- 防止 Context Overflow
- 降低无效信息占用
- 提升长任务稳定性

### Final Answer 捕获

新增最终答案提取逻辑，实现：

- 推理轨迹与最终答案分离
- 前端正确显示最终结果
- 避免答案丢失

---

## 🛠 Wikipedia 工具集

为解决比赛中大量 Wikipedia 相关题目，新增专项工具：

| 工具名称 | 功能 |
|----------|------|
| count_wikipedia_edits_in_year | 统计某年编辑次数 |
| get_wikipedia_revisions | 获取 Revision 历史 |
| get_wikipedia_revision_before_date | 获取指定时间前版本 |
| count_references_for_revision | 统计引用数量 |
| compute_wikipedia_reference_delta | 对比引用增量 |
| find_wikipedia_revision_by_size_delta | 根据字节变化定位编辑 |
| extract_section_from_revision | 提取指定章节 |
| get_wikipedia_revision_content | 内容预览与清洗 |

这些工具能够将依赖模型推理的问题转化为程序计算问题，从而提升准确率。

---

## 💡 经验总结

在复杂问答竞赛中，许多问题本质上属于：

```text
信息获取
→ 数据提取
→ 程序计算
→ 结果验证
```

而不是单纯的语言生成问题。

因此，相比不断增强 Prompt，更重要的是：

- 构建可靠工具链
- 建立证据获取系统
- 提高执行稳定性
- 强化结果验证能力

---

## 📌 后续计划

- 搜索结果自动压缩
- 检索证据排序
- 自动上下文裁剪
- 多阶段答案验证
- 竞赛专用 Planner 优化
- 轨迹质量评估系统