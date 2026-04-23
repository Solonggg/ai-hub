---
name: business-dict
description: 在 fdp-admin 表单字段挂接 `<wordbook>` 字典片段、为字段选择业务域字典、或在 `references/` 新增一本字典文件时使用；通常由 `fdp-form` 处理字典字段时自动调用
---

# business-dict · fdp-admin 业务域字典库

本 skill 是 fdp-admin 字典配置的**唯一可信源**。所有字典作为独立 XML 文件存放在 `references/`——**丢一个文件进去就是新增一本字典**，无需修改本 SKILL.md。

## 运行时使用流程

当 `fdp-form` 或用户需要挂字典时：

1. `Glob references/*.xml` 列出所有字典文件。
2. 对候选文件 `Read` 头部注释，获取 `字典名` / `业务域` / `业务域命中条件` / `元数据`。
3. 按下方"选字典决策流程"定位应用哪本。
4. 拷贝该文件 `<wordbook>...</wordbook>` 整段，`{{VALUE}}` 替换为用户确认过的分类码。
5. 把完整片段填到 `fdp-form` 模板里的 `{{WORDBOOK_BLOCK}}` 占位符。

## 选字典决策流程

无论 `references/` 下有多少本字典，判定顺序**恒定**：

1. **沿用目标 XML 已有字典**（最可靠）：`Grep` 目标 XML 现存 SEARCH/SEARCH_MORE/RADIO/CHECKBOX/SELECT 字段的 `<wordbook><id>`，找 `references/` 下 `<id>` 匹配的那本。
2. **按业务域命中条件匹配**：逐一读 `references/*.xml` 头部注释的"业务域命中条件"，命中谁用谁。
3. 以上都不命中 → **必须问用户**。不要猜，不要按字典名硬拼 `<id>`。

## 分类码（`<conObj>.<value>`）来源

分类码决定从字典中筛哪一类（例：健康档案数据字典 `bzd03=141` 取"有无情况类"、`bzd03=117` 取"国籍"）。

- 用户直接给数字 → 直接用
- 用户只给字典编码名（如 `YWQKDMB` / `HJBZDMB`）不给数字 → 先 `Grep` 同文件已有同类字段参考；仍不确定 → **问用户**
- 永远不要凭字典编码名拼数字

## 新增字典 SOP（丢文件即上线）

**只做一件事**：在 `references/` 新建一个 `.xml` 文件。

命名：`{业务前缀}-{字段系列}-dict.xml`
- 业务前缀：`ehr`（健康档案）/ `mrms`（病案）/ `nursing`（护理）/ …
- 字段系列：字典核心字段前缀 + 编号，如 `bzd1` / `bsq1` / `brv1`

文件内容（缺一不可）：
1. **头部注释**（按固定顺序）：`字典名` / `业务域` / `字段系列前缀` / `业务域命中条件` / `元数据` / `默认分类码` / `差异说明`（可选）/ `使用方式`
2. **完整 `<wordbook>...</wordbook>` 片段**，`<conObj>.<value>` 用 `{{VALUE}}` 占位

直接复制 `references/ehr-bzd1-dict.xml` 作模板最稳。**不需要**改本 SKILL.md、不需要改 `fdp-form`、不需要改 CLAUDE.md 索引。

## 常见坑

- **切换字典时整段替换 `<wordbook>`**：不同字典的 `<conObj>` 内部结构、`search_key` 顺序、是否含 `<openWindowType>` 都可能不同（例：护理文书字典用 `<is_compare_field>` 而不是 `<compare_field>`）
- **新字典文件必须含完整头部注释**：缺"业务域命中条件"会导致自动选字典失败
- **`{{VALUE}}` 占位符不要遗留**
- **跨业务域给字段挂错字典**是高发错误，先跑决策流程第 1 步
