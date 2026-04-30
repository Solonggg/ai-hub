# iho-wiki-archive

把公司内网文档（`docs.cnhis.com` / `teamwork.cnhis.cc`）抓取、转换为 Markdown，按业务域归档到本地 LLM Wiki。

> 本文档面向人读。Claude 在会话中实际执行的是 `SKILL.md` —— 触发条件、流程红线、字段约束都以 `SKILL.md` 为准。

## 它做什么

1. 用 playwright 启 chromium 渲染 SPA 页面，等到 `<div class="markdown-body">` 出现且正文非空
2. 在 `markdown-body` 之前的 DOM 中抽 `author` / `updated_at`
3. 用 `markitdown` 把 `markdown-body` 转成 Markdown，**保留远程图片 URL**
4. 按关键词命中得分判定 `病案 / 护理 / 健康档案`，歧义就停下提问
5. 写入 `~/workspace/LLM Wiki/iho/<分类>/<标题>-YYYYMMDDHHMMSS.md`，含 8 字段 Front Matter
6. 按 `source_url + content_hash` 去重，更新分类下 `_index.json`
7. 同步 `iho/index.md` 全局索引（按归档日期正序）

## 怎么触发

在 Claude Code 会话中说一句包含**白名单链接**且**带归档意图**的话即可，例如：

```
归档 https://docs.cnhis.com/document/#/share-page?shareCode=4ojD0lbPHgfsZ57nNDNzVinV
```

意图关键词：`归档` / `存档` / `保存到 wiki` / `存到 wiki` / `archive` / `存一下` / `收录`

仅给链接、不带意图 → **不触发**（视为问内容）。

## 依赖

| 工具 | 用途 | 安装 |
|------|------|------|
| Python 3.x | 跑脚本 | 任意非 PEP 668 限制的 Python（python.org / pyenv 都可） |
| `playwright` | 浏览器自动化 | `pip install playwright` |
| `chromium-headless-shell` | 实际渲染内核 | `python3 -m playwright install chromium-headless-shell` |
| `markitdown` | HTML → Markdown | `pip install markitdown` |

> playwright 1.49+ 默认 launch 使用 `chrome-headless-shell`，**不是**完整 `chromium`。只装 `chromium` 会报 `Executable doesn't exist`。

一次性环境准备：

```bash
pip install playwright
pip install markitdown
python3 -m playwright install chromium-headless-shell
```

## 目录结构

```
iho-wiki-archive/
├── README.md                       # 本文件（人读）
├── SKILL.md                        # 触发条件 + 8 步主流程 + 红线（Claude 读）
├── bin/
│   ├── fetch.py                    # CLI: URL → 整页渲染后 HTML（stdout）
│   └── extract-body.py             # CLI: URL → markdown-body 的 outerHTML
└── references/
    ├── fetch-and-convert.md        # 抓取降级链、DOM 选择器、markitdown 调用
    ├── categorization-rules.md     # 三类词表、评分逻辑、提问模板
    └── file-layout.md              # 目录结构、文件命名、Front Matter、_index.json、index.md 维护
```

## 手工跑（绕开 Claude 直接验证）

```bash
# 1. 渲染整页（含 head + body，便于在 markdown-body 之前抽元数据）
python3 bin/fetch.py 'https://docs.cnhis.com/document/#/share-page?shareCode=4ojD0lbPHgfsZ57nNDNzVinV' > /tmp/page.html

# 2. 仅抽 markdown-body（已剥离 script/style，喂 markitdown 用）
python3 bin/extract-body.py 'https://docs.cnhis.com/document/#/share-page?shareCode=4ojD0lbPHgfsZ57nNDNzVinV' > /tmp/mb.html

# 3. HTML → Markdown
markitdown -x html /tmp/mb.html -o /tmp/page.md
# 或当 markitdown CLI 不在 PATH 时：
python3 -m markitdown -x html /tmp/mb.html -o /tmp/page.md
```

`fetch.py` 退出码：`0` 成功 / `2` 参数错 / `3` 加载失败 / `4` markdown-body 为空。

## 落盘位置

```
~/workspace/LLM Wiki/iho/
├── index.md                # 全局索引（人读视图，按业务域分组的 7 列表）
├── 病案/
│   ├── _index.json         # 去重权威源（机器读，4 字段）
│   └── *.md                # 每篇含 8 字段 Front Matter
├── 护理/
│   ├── _index.json
│   └── *.md
└── 健康档案/
    ├── _index.json
    └── *.md
```

## 不会做

- 不下载图片、不本地化资源（图片 URL 原样保留）
- 不安装新依赖（`markitdown` 缺失就降级转换或停下）
- 不修改 `settings.json`、不动 hooks
- 不为不可能的场景写错误处理（白名单外域名直接拒）
- 不擅自改判分类、不擅自跨分类迁移

## 相关 skill

- `dingtalk-wiki-assistant` — 钉钉来源问题答疑，**只读检索**已归档的 Wiki，与本 skill 互补：本 skill 写入，那个 skill 读出
