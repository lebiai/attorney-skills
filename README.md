# 乐彼AI · 律师 Codex Skill 套件

为律师定制的 Codex Skill，让 AI 成为你的法律助手。

## 包含的 Skill

| Skill | 说明 | 安装路径 |
|-------|------|---------|
| `skill-lawyer-case-analysis` | 案件深度分析 | `~/.codex/skills/skill-lawyer-case-analysis/` |
| `skill-lawyer-strategy` | 诉讼策略分析 | `~/.codex/skills/skill-lawyer-strategy/` |

## 安装

### 方式一：Codex CLI 安装（推荐）

在 Codex 中说：

> "安装 lawyer-case-analysis skill"
> "安装 lawyer-strategy skill"

Codex 会自动从 GitHub clone 到本机。

### 方式二：手动安装

```bash
# 克隆仓库
git clone https://github.com/aodunsenmai-dot/attorney-skills.git

# 复制到 Codex skills 目录
cp -r attorney-skills/skill-lawyer-case-analysis ~/.codex/skills/
cp -r attorney-skills/skill-lawyer-strategy ~/.codex/skills/
```

### 方式三：ZIP 下载

1. 从 GitHub Releases 下载最新 ZIP
2. 解压
3. 将两个文件夹复制到 `~/.codex/skills/`

## 使用方法

### 案件深度分析

在 Codex 中说：

> "帮我分析这份判决书"

然后上传或粘贴判决书原文。AI 会自动输出 9 章分析报告。

### 诉讼策略分析

在 Codex 中说：

> "我有个离婚案子，男方婚前买房婚后一起还贷，现在离婚女方要分60%。帮我看看怎么打。"

AI 会检索知识库中的相似判例，基于真实判决结果给出策略建议。

## 首次使用前

策略分析 skill 首次使用时，会自动下载知识库（约 7MB），仅需几秒钟。后续知识库更新时会询问是否下载新版本。

## 数据本地化

- 所有分析在本机完成，不上传至任何服务器
- 私人知识库仅保存在本机 `data/personal.db`
- 用户画像保存在本机 `data/user_profile.json`
- git pull 更新 skill 时不影响个人数据

## 知识库更新

知识库（distilled.db）通过 GitHub Releases 发布。使用策略分析时，系统会自动检测是否有新版本并询问是否更新。

## 文件结构

```
attorney-skills/
├── skill-lawyer-case-analysis/
│   ├── SKILL.md
│   ├── references/
│   │   ├── evidence-rules.md
│   │   ├── law-citation.md
│   │   └── quality-control.md
│   └── agents/openai.yaml
│
├── skill-lawyer-strategy/
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── setup_knowledge.py
│   │   └── search_knowledge.py
│   ├── data/              ← 运行期数据，git pull 不影响
│   │   ├── distilled.db   ← 公共知识库（自动下载）
│   │   ├── personal.db    ← 私人知识库（律师积累）
│   │   └── user_profile.json
│   └── agents/openai.yaml
│
└── README.md
```

## 前置要求

- Codex CLI (推荐) 或其他支持 Codex Skill 的 AI 终端
- Python 3（Codex 自带）
- 出网权限（首次下载知识库时需访问 GitHub）

## 隐私说明

- 不收集任何用户数据
- 不联网发送分析内容
- 知识库更新仅检测版本号，不涉及用户使用数据
