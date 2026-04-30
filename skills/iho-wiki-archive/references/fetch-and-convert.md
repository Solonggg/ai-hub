# 抓取与转换细则

## 抓取工具降级链

按以下顺序尝试，前一个不可用立刻降级，**全部失败即停下提问**，不要硬跑。

### 1. chrome-devtools MCP（首选）
若会话中提供 `mcp__chrome-devtools__*` 系列工具，使用之：
- 打开链接 → 等待 DOM
- 用 `evaluate_script` 检查 `document.querySelector('div.markdown-body')` 是否存在
- 不存在则轮询，最长 15s；超时即视为加载失败

### 2. Python playwright（次选）

探测：
```bash
python3 -c "import playwright; print(playwright.__version__ if hasattr(playwright,'__version__') else 'ok')"
ls ~/Library/Caches/ms-playwright/    # 检查浏览器内核
```

若 playwright Python 包缺失，**先征求用户同意再装**（逐个装，不要写 requirements.txt，不要指定版本）：
```bash
pip3 install playwright
pip3 install markitdown
```

若浏览器内核缺失，**先征求用户同意再装**（首装约 150MB；Node 版与 Python 版共享 `~/Library/Caches/ms-playwright/`）：
```bash
python3 -m playwright install chromium-headless-shell
```

> playwright 1.49+ launch 默认使用 `chrome-headless-shell`，**不是**完整 chromium。只装 `chromium` 会报 `Executable doesn't exist`。

调用本 skill 内置脚本抓取：

```bash
# 整页 HTML（含 head，便于在 markdown-body 之前抽元数据）
python3 $SKILLS/iho-wiki-archive/bin/fetch.py <url> > /tmp/iho-fetch-<ts>.html

# 仅 markdown-body outerHTML（已剥离 script/style，喂 markitdown 用）
python3 $SKILLS/iho-wiki-archive/bin/extract-body.py <url> > /tmp/iho-mb-<ts>.html
```

`bin/fetch.py` 行为：
- 等待 `div.markdown-body` 出现（20s 超时）
- 等待 `markdown-body.innerText.length > 50`（10s 超时，防异步渲染未完成）
- 输出整页 HTML 到 stdout
- 退出码：0 成功 / 2 参数错 / 3 加载失败 / 4 markdown-body 为空

### 3. WebFetch（兜底，能力有限）
仅当上述两条都不可用时启用：
- 直接 `WebFetch` 该 URL，获取响应体
- 若响应体中能 grep 到 `markdown-body` 且包含正文 → 可继续
- 若响应是 SPA 外壳（仅包含 `<div id="root"></div>` 之类），**判定失败 → 停下提问**，告知用户该页面需要 JS 渲染，请改用 chrome-devtools / playwright 环境再试

## DOM 抽取规则

### 元数据定位
在 `<div class="markdown-body">` **之前**的祖先或兄弟节点中查找文档头容器，从中提取：

- **author**：常见选择器候选（按命中优先级探测）
  - `.doc-header .author`
  - `.doc-meta .creator`
  - `[data-field="author"]`
  - 文本中匹配 `作者[:：]\s*(\S+)` 的相邻节点

- **updated_at**：常见选择器候选
  - `.doc-header .updated-at`
  - `.doc-meta time[datetime]`
  - `[data-field="updateTime"]`
  - 文本中匹配 `(最后更新|更新时间|修改时间)[:：]\s*([\d\-:\s]+)` 的相邻节点

两个站点的实际选择器可能不同，**探测优先**：能拿到文本就用，命名空间不重要。两项缺一即停下问用户。

### 正文抽取
- 取 `document.querySelector('div.markdown-body').innerHTML`
- 剥离：`<script>`、`<style>`、`display:none` 节点、空 `<div>`
- 不剥离：`<a>`、`<code>`、`<pre>`、`<table>`、`<ol>/<ul>`、`<blockquote>`、`<h1..h6>`、`<img>`

## HTML → Markdown 转换

### 优先：markitdown

```bash
# 探测（CLI 可能未在 PATH 中，此时用 python -m）
which markitdown || python3 -m markitdown --help

# 转换
markitdown -x html /tmp/iho-mb-<ts>.html -o /tmp/iho-mb-<ts>.md
# 或
python3 -m markitdown -x html /tmp/iho-mb-<ts>.html -o /tmp/iho-mb-<ts>.md
```

注意：markitdown CLI **不支持 URL 输入**（其 Python API 内部用静态 HTTP 抓取，不渲染 JS，对 SPA 无效）。所以管道必须先经 playwright 拿到渲染后 HTML，再喂给 markitdown 做格式转换。

### 缺失时的降级策略
代理自行做 HTML→Markdown，但必须满足：

- `<h1..h6>` → `#..######`（保留层级）
- `<a href="X">T</a>` → `[T](X)`
- `<img src="X" alt="A">` → `![A](X)` — **X 必须保留远程绝对 URL**
- `<pre><code class="lang">` → ` ```lang ` 围栏
- `<table>` → GFM 表格语法
- `<ul>/<ol>/<li>` → `-` / `1.`
- `<blockquote>` → `> `

若正文含复杂嵌套表格或被剥离会丢信息的结构 → 停下，告诉用户 markitdown 缺失、降级转换可能丢格式，让用户选"继续/中止"。

## 图片处理（铁律）

- **保留原始远程 URL，原样不动**
- 严禁：下载到本地、替换为相对路径、改写为 `cdn` 镜像、加查询参数
- 转换前后做一次正则校验：所有 `![...](...)` 中括号内必须以 `http://` 或 `https://` 开头，否则视为转换错误，停下检查

## 失败排错速查

| 症状 | 处理 |
|------|------|
| 401/403 | 提示用户登录态过期，**不要**尝试绕过 |
| 加载超过 15s 仍无 `markdown-body` | 视为失败，提示页面结构异常或非文档页 |
| `markdown-body` 为空 | 视为失败，可能是权限页或空文档 |
| 元数据选择器全部命中失败 | 不写空字符串占位，停下问用户 |
| markitdown 调用非 0 退出 | 读 stderr，转告用户原文，再判断是否降级 |
