---
name: lawyer-case-analysis
description: >
  深度分析法院裁判文书（判决书/裁定书/调解书）。
  当用户上传或粘贴一份法院裁判文书并请求分析时使用。
  从11个维度以10个模块化的分析步骤输出结构化报告。
---

# lawyer-case-analysis — 案件深度分析

## 触发条件

- 用户上传/粘贴了一份法院裁判文书并请求分析
- 用户说"帮我分析这个案子"并附带了文书内容

## 工作流

```
Step 1: 读取 user_profile.json 了解律师偏好（如有）
Step 2: 按 workflow/01~10 顺序逐维度分析判决书
Step 3: 按 output/template.md 输出报告
Step 4: 逐条核对原文（rules/quality-control.md）
Step 5: 执行 modules/feedback.md（对话反馈）
Step 6: 询问保存知识库（modules/save-to-knowledge.md）
Step 7: 更新 user_profile（modules/update-profile.md）
```

## 分析维度（10 个模块）

分析时必须按以下顺序依次考察每个维度，每个维度的分析指引见对应文件：

| # | 维度 | 文件 |
|:-:|------|------|
| 1 | 案件基本信息 | workflow/01-basic-info.md |
| 2 | 争议焦点 | workflow/02-dispute-focus.md |
| 3 | 诉讼动机分析 | workflow/03-litigation-motive.md |
| 4 | 证据链分析 | workflow/04-evidence-analysis.md |
| 5 | 法律路径 | workflow/05-legal-paths.md |
| 6 | 推理链条 | workflow/06-reasoning-chain.md |
| 7 | 关键转折点 | workflow/07-turning-points.md |
| 8 | 法官裁判倾向 | workflow/08-judge-style.md |
| 9 | 模式标签 | workflow/09-patterns.md |
| 10 | 实战启示（新增） | workflow/10-retrospective.md |

## 约束规则

分析过程中遇到以下场景时读取对应规则文件：

| 场景 | 文件 |
|------|------|
| 证据分类/清洗/采信评价 | rules/evidence-rules.md |
| 法条引用格式 | rules/law-citation.md |
| 质量约束/反例/自查 | rules/quality-control.md |

## 输出模板

报告按 output/template.md 的模板组织，不可改变章节标题和顺序。

## 个性化

- 分析前检查 `user_profile.json`：`focus_areas` 优先加强，`common_case_types` 参照历史领域深度
- 文件不存在或路径不可达时正常继续，不报错
