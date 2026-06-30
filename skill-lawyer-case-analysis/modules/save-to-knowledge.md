# 模块：保存到策略知识库

## 何时执行

用户说了"保存"或"保存到知识库"之后。

## 操作

1. 确认路径 `../lawyer-strategy/data/personal.db` 是否存在
2. 不存在 → 提示"策略知识库数据库未安装，请先使用 strategy skill"
3. 存在 → 询问用户："确认将本案分析加入您的私人策略知识库？仅保存在本机。"
4. 用户拒绝 → 不保存，告知"已跳过保存"
5. 用户同意 → 写入 personal.db：

### 写入字段

```sql
INSERT INTO personal_kb (case_no, case_type, court_name, result_type, 
       dispute_focus, analysis, created_at)
VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
```

- `analysis` 字段写入第10章之前的完整分析报告文本
- 如 personal.db 无 `personal_kb` 表，创建：

```sql
CREATE TABLE IF NOT EXISTS personal_kb (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_no TEXT,
    case_type TEXT,
    court_name TEXT,
    result_type TEXT,
    dispute_focus TEXT,
    analysis TEXT,
    created_at TEXT
);
```

成功后告知："已保存！以后做策略分析时，这个案例会被参考。"
