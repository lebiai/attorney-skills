# 模块：保存到策略知识库

## 何时执行

用户说了"保存"或"保存到知识库"之后。

## 操作

1. 确认路径 `../lawyer-strategy/data/personal.db` 是否存在
2. 不存在 → 提示"策略知识库数据库未安装，请先使用 strategy skill"
3. 存在 → 询问用户："确认将本案分析加入您的私人策略知识库？仅保存在本机。"
4. 用户拒绝 → 不保存，告知"已跳过保存"
5. 用户同意 → 写入 personal.db：

### 建表（如不存在）

personal.db 使用与公共库一致的 schema，确保 search_knowledge.py 的双源检索能正常工作。

```sql
-- cases 表（与 distilled.db 的 cases 表结构一致）
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    case_no TEXT,
    case_type TEXT,
    court_name TEXT,
    result_type TEXT,
    analysis JSON
);

-- FTS5 全文索引（用于双源检索）
CREATE VIRTUAL TABLE IF NOT EXISTS cases_fts USING fts5(
    case_id, case_no, case_type, court_name, analysis
);
```

### 写入内容

```sql
-- 1) 写入 cases 表
INSERT INTO cases (id, case_no, case_type, court_name, result_type, analysis)
VALUES (?, ?, ?, ?, ?, ?);

-- 2) 同步写入 FTS5 索引
INSERT INTO cases_fts (case_id, case_no, case_type, court_name, analysis)
VALUES (?, ?, ?, ?, ?);
```

### 实际写入的字段

| 字段 | 内容 | 示例 |
|------|------|------|
| `id` | UUID | `a1b2c3d4...` |
| `case_no` | 案号 | （2026）甘3027民初24号 |
| `case_type` | 案由 | 离婚纠纷 |
| `court_name` | 法院 | 甘肃省夏河县人民法院 |
| `result_type` | 判决类型 | 部分支持 |
| `analysis` | 完整分析报告（第1-9章全文） | JSON格式，约3-5KB |

### 不存储的内容

- ❌ 判决书原文
- ❌ 用户个人信息
- ❌ 对话历史

### 保存成功后的反馈

"已保存！以后做策略分析时，这个案例会被参考。"
