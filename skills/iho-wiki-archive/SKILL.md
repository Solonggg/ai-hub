---
name: iho-wiki-archive
description: 在用户给出 docs.cnhis.com 或 teamwork.cnhis.cc 的内网文档链接，并明确表达"归档/存档/保存到 wiki/archive"意图时使用。负责抓取页面、提取作者与最后更新时间、转换为 Markdown、按业务域（病案/护理/健康档案）归档到本地 LLM Wiki，并维护 _index.json 做去重与更新。
---

# iho-wiki-archive

## 角色定位
将公司内网文档（docs.cnhis.com / teamwork.cnhis.cc）抓取并转换为 Markdown，按业务域归档到 `~/workspace/LLM Wiki/iho/{病案|护理|健康档案}/`，构建可被检索的离线知识库。

## 触发条件
**同时满足**两点才触发：

1. 消息中包含以下任一格式的链接：
   - `https://docs.cnhis.com/document/...`
   - `https://teamwork.cnhis.cc/teamwork/share/konwledge/...`
2. 消息中包含归档意图关键词：`归档` / `存档` / `保存到 wiki` / `存到 wiki` / `archive` / `存一下` / `收录`

仅给链接、未表达归档意图 → **不触发**（可能是问内容）。

## 主流程（8 步）

> 任一步失败必须停下提问，不允许跳过或猜测。

1. **抓取页面**（详细规则见 `references/fetch-and-convert.md`）
   - 工具优先级：`chrome-devtools MCP` → `playwright CLI` → `WebFetch` 兜底
   - 等待 `<div class="markdown-body">` 出现视为加载完成；超时则失败即停
2. **提取元数据**：在 `markdown-body` 之前的 DOM 中定位 `author`、`updated_at`，二者缺一即停下问用户补充
3. **抽取正文**：取 `<div class="markdown-body">` 的 innerHTML 作为正文,剥离脚本与隐藏节点；丢弃页头、侧栏、导航、评论、底栏
4. **HTML → Markdown**：优先 `markitdown` CLI；缺失时降级为代理自行转换。**严禁本地化图片**，所有 `![alt](...)` 保留原始远程 URL；保留超链接、代码块、表格、列表、引用、标题层级
5. **自动分类**（详见 `references/categorization-rules.md`）：根据正文关键词命中得分判定 `病案 / 护理 / 健康档案`；歧义时停下提问
6. **文件落盘**（详见 `references/file-layout.md`）：写入对应子目录，文件名 `<标题>-YYYYMMDDHHMMSS.md`，Front Matter 含 8 个必填字段
7. **去重与更新**：维护子目录下 `_index.json`，按 `source_url + content_hash` 决定跳过/覆盖/新增
8. **更新全局索引 index.md**：把本次条目合并进 `~/workspace/LLM Wiki/iho/index.md` 的 `## wiki目录` → `### <分类>` 表格（7 列：系统、标题、原始链接、本地文件、更新日期、作者、归档日期）；按 `source_url` 去重，组内按归档日期正序；详见 `references/file-layout.md`「index.md 全局索引维护」

## 必须停下提问的红线

- 抓取超时或拿不到 `markdown-body` → 不要伪造正文
- 元数据 `author` 或 `updated_at` 缺失 → 不要写空字符串占位
- 分类无命中或最高分−次高分 < 2 → 出候选清单让用户选
- `markitdown` 缺失且降级转换可能丢格式（命中表格、复杂嵌套时）→ 提示用户后再决定
- 用户给的链接不在白名单两个域名内 → 拒绝并说明本 skill 适用范围
- `index.md` 中 `## wiki目录` 章节缺失 → 不擅自新建外层结构，停下问用户（可能是文件被改名/章节被删）

## Front Matter 模板（8 个必填字段，不得重复键）

```yaml
---
source_url: <原始链接>
platform: <docs.cnhis.com | teamwork.cnhis.cc>
title: <文档标题>
category: <病案 | 护理 | 健康档案>
author: <作者姓名>
updated_at: <文档头中的最后更新时间，原样保留>
content_hash: <sha256，正文 markdown 去除 front matter 后的字节>
archive_at: <YYYY-MM-DDTHH:MM:SS+08:00>
---
```

## 输出回执模板

完成归档后用一次性回复给用户：

```markdown
**归档完成** · `<分类>/<文件名>`
- 来源：<source_url>
- 作者：<author> · 最后更新：<updated_at>
- 正文哈希：<content_hash 前 12 位>
- 状态：<新增 | 已覆盖更新 | 内容未变更，已跳过>
```

## 不会做的事

- 不下载图片、不本地化资源、不做 OCR、不做摘要
- 不修改 settings.json、不安装新依赖（markitdown 缺失就降级或停下）
- 不为不可能的场景写错误处理（用户给非白名单域名 → 拒绝即可，不写正则降级链）

## References（按需加载）

- `references/fetch-and-convert.md` — 抓取工具降级链、DOM 选择器、markitdown 调用与图片保留
- `references/categorization-rules.md` — 三类关键词词表、评分逻辑、歧义提问模板
- `references/file-layout.md` — 目录结构、文件名清洗、Front Matter、`_index.json` 结构与去重决策、`index.md` 全局索引维护
