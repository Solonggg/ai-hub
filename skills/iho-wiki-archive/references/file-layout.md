# 目录结构、文件命名、Front Matter、_index.json

## 目录结构

```
~/workspace/LLMWiki/iho/
├── 病案/
│   ├── _index.json
│   └── *.md
├── 护理/
│   ├── _index.json
│   └── *.md
└── 健康档案/
    ├── _index.json
    └── *.md
```

`_index.json` 三类各一份，互不影响，不做全局聚合索引。

## 文件名规范

格式：`<清洗后的标题>-YYYYMMDDHHMMSS.md`

时间戳取 `archive_at` 的本地时间（Asia/Shanghai），精确到秒。

### 标题清洗规则
1. 替换非法字符：`< > : " / \ | ? *` → `_`
2. 折叠连续空白为单个空格，去首尾空白
3. 去除控制字符（`\x00-\x1F`）
4. 长度上限 80 字符（按 Unicode 字符数，非字节），超出截断
5. 若清洗后为空字符串 → 用 `untitled` 兜底

例：`新版护理大屏部署 (V2) - 2025` → `新版护理大屏部署 (V2) - 2025-20260429181500.md`

## Front Matter（YAML）

8 个字段全部必填，不得有重复键，不得有空值占位。

```yaml
---
source_url: https://docs.cnhis.com/document/abc123
platform: docs.cnhis.com
title: 新版护理大屏部署
category: 护理
author: 张三
updated_at: "2026-04-20 15:30:00"
content_hash: 9f2c4e7a6b8d1f3e5c0a2b4d6e8f0a1c3d5e7f9b2a4c6e8d0f2b4a6c8e0d2f4
archive_at: "2026-04-29T18:15:00+08:00"
---
```

字段约束：
- `platform`：仅取 `docs.cnhis.com` 或 `teamwork.cnhis.cc`
- `category`：仅取 `病案` / `护理` / `健康档案`
- `updated_at`：保留页面原文格式，加双引号避免被 YAML 解析为日期
- `content_hash`：sha256 全长 64 位小写
- `archive_at`：ISO8601 + 时区偏移

## content_hash 算法

```
1. 取最终落地的 markdown 全文
2. 去掉首尾的 --- ... --- front matter 块
3. 对剩余字节做 sha256，输出 64 位小写十六进制
```

只对正文哈希，不含 front matter 本身（否则 archive_at 每次都变，永远算"内容变更"）。

## _index.json 结构

```json
{
  "entries": [
    {
      "source_url": "https://docs.cnhis.com/document/abc123",
      "content_hash": "9f2c4e7a...",
      "filename": "新版护理大屏部署-20260429181500.md",
      "archive_at": "2026-04-29T18:15:00+08:00"
    }
  ]
}
```

- 文件不存在 → 视为空 `{ "entries": [] }`
- 写入用 UTF-8、缩进 2、保留中文（`ensure_ascii=false`）
- 不维护额外字段（如 author/title），保持索引精简

## 去重与更新决策表

| 场景 | 操作 |
|------|------|
| `source_url` 在 `_index.json` 中不存在 | **新增**：写入新文件 + append entry |
| `source_url` 存在 且 `content_hash` 一致 | **跳过**：不动文件，不动索引，回执显示"内容未变更" |
| `source_url` 存在 且 `content_hash` 不一致 | **覆盖更新**：删除旧文件（按 entry.filename）、写入新文件、原 entry 原地更新 `content_hash` / `filename` / `archive_at` |

注意事项：
- 覆盖时旧文件名通常与新文件名不同（时间戳变了）→ 必须先删旧文件再写新文件，避免遗留
- 跨分类的同 URL 不应出现；若用户改判分类导致同 URL 在另一类已存在 → 停下问用户是迁移还是新增

## 写入顺序（避免半成品）

```
1. 计算 content_hash（基于已转换好的 markdown 正文）
2. 查 _index.json，决定 新增 / 跳过 / 覆盖 / 跳过 index.md 更新
3. 若是覆盖：先 unlink 旧文件
4. 写新文件（含 front matter）
5. 更新 _index.json
6. 更新全局索引 index.md（见下一节）
7. 输出回执
```

任何一步失败 → 停下，回滚未完成动作不强求；告知用户当前状态，让用户决定。

## index.md 全局索引维护

### 文件位置与定位
- 路径：`~/workspace/LLMWiki/iho/index.md`（脚本内需 `os.path.expanduser` 或 shell 自动展开 `~`）
- 结构：`## wiki目录` 章节下分三个二级子章节 `### 病案` / `### 护理` / `### 健康档案`，每个子章节内一张 7 列 Markdown 表格

### 章节定位规则
1. 找到二级标题 `## wiki目录`
   - 找不到 → **停下提问**（不要自动新建顶层章节，可能文件被改）
2. 在该章节范围内找三级标题 `### <分类>`
   - 找不到对应分类小节 → 自动追加（标题 + 表头空表）至章节末尾，按 `病案 → 护理 → 健康档案` 顺序保持
3. 表头不全（缺列）→ **停下提问**（不要静默重写，可能用户手工编辑过）

### 表格规范

7 列固定表头：

```markdown
| 系统 | 标题 | 原始链接 | 本地文件 | 更新日期 | 作者 | 归档日期 |
|------|------|----------|----------|----------|------|----------|
```

各列填值：
- **系统**：`病案` / `护理` / `健康档案`（与所在子章节一致；冗余但保留以便整张表外抽时仍可读）
- **标题**：Front Matter 中的 `title`，原样
- **原始链接**：`[链接](<source_url>)`
- **本地文件**：`[<分类>/<filename>](<分类>/<filename>)` —— 相对 `index.md` 的相对路径，与现有风格一致
- **更新日期**：Front Matter 中的 `updated_at`，按需截取到 `YYYY-MM-DD`
- **作者**：Front Matter 中的 `author`
- **归档日期**：Front Matter 中的 `archive_at`，截取到 `YYYY-MM-DD`

### 新增 / 更新 / 跳过决策

按 `source_url` 在所属分类小节内查重：

| 场景 | 操作 |
|------|------|
| 同 `source_url` 不存在 | **新增**一行至表末，再按归档日期重排 |
| 同 `source_url` 存在 且 `_index.json` 判定为"内容未变更" | **跳过**，不动表格 |
| 同 `source_url` 存在 且发生覆盖更新 | **原地更新**该行的「标题 / 本地文件 / 更新日期 / 作者 / 归档日期」5 列 |
| 同 `source_url` 出现在另一分类小节 | **停下提问**（用户改判分类的语义不明：迁移？拆分？） |

### 排序

每个分类小节内：**按「归档日期」升序（正序）**——最早归档在上，最新归档在下。日期相同则保持原相对顺序（稳定排序），不强行按其他维度二次排序。

### 最小条目示例

```markdown
## wiki目录

### 病案

| 系统 | 标题 | 原始链接 | 本地文件 | 更新日期 | 作者 | 归档日期 |
|------|------|----------|----------|----------|------|----------|
| 病案 | 病案常见问题处理 | [链接](https://docs.cnhis.com/document/#/share-page?shareCode=XXX) | [病案/病案常见问题处理-20260430101530.md](病案/病案常见问题处理-20260430101530.md) | 2026-04-25 | 王洁 | 2026-04-30 |

### 护理

| 系统 | 标题 | 原始链接 | 本地文件 | 更新日期 | 作者 | 归档日期 |
|------|------|----------|----------|----------|------|----------|

### 健康档案

| 系统 | 标题 | 原始链接 | 本地文件 | 更新日期 | 作者 | 归档日期 |
|------|------|----------|----------|----------|------|----------|
```

### 与 `_index.json` 的分工
- `_index.json`：去重权威源，机器读，仅 4 字段（source_url / content_hash / filename / archive_at）
- `index.md`：人读视图，从各文件 Front Matter + `_index.json` 派生
- 二者不一致时以 `_index.json` 为准；index.md 的修复属于"重建"，应基于 `_index.json` 与文件 Front Matter 全量重写对应小节
