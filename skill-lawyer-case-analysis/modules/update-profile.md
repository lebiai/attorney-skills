# 模块：更新用户画像

## 何时执行

分析报告输出完毕后，在询问保存之前。

## 操作

检查路径 `../lawyer-strategy/data/user_profile.json` 是否存在。

### 不存在 → 创建

```json
{
  "version": "1.0",
  "created_at": "[当前日期]",
  "last_updated": "[当前日期]",
  "common_case_types": [{"type": "[本案案由]", "count": 1}],
  "preferred_courts": ["[本案法院]"],
  "analysis_preferences": {
    "detail_level": "detailed",
    "focus_areas": [],
    "always_ask_save": true
  },
  "usage_stats": {
    "total_analyses": 1,
    "cases_saved_to_kb": 0
  }
}
```

### 已存在 → 更新

- `common_case_types` 中对应案由的 count +1（不存在则新增 `{"type": "XX纠纷", "count": 1}`）
- `preferred_courts` 中若本案法院不存在则追加（限制最多 10 个）
- `usage_stats.total_analyses` +1
- `last_updated` 更新为当前日期
- 如果用户说了"证据再详细点"等反馈 → 将对应维度加入 `analysis_preferences.focus_areas`（去重）

### 约束

- 文件读写失败时静默跳过，不报错，不影响分析输出
- JSON 格式错误时整文件覆盖重建
