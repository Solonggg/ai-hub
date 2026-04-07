# 视觉辅助使用指南

这是 `brainstorming` 阶段配套的浏览器可视化工具，用来展示草图、图表、布局对比和其他视觉选项。

## 何时使用

按**每个问题**判断，而不是按整个会话判断。标准只有一个：

**用户看图会不会比看文字更容易理解？**

适合使用浏览器的场景：

- UI 草图、线框图、导航结构
- 架构图、数据流、关系图
- 两个布局或两种视觉方向的对比
- 需要点击选择的设计方案

应继续用终端的场景：

- 需求澄清
- 范围和优先级判断
- 技术设计、接口设计、数据建模
- 所有本质上更适合文字回答的问题

## 工作原理

服务端会监听一个目录中的 HTML 文件，并始终把**最新文件**展示给浏览器。

- 你写入 `screen_dir`
- 浏览器展示最新页面
- 用户点击后的事件会写入 `state_dir/events`
- 你在下一轮读取这些事件并继续推进

### 内容片段 vs 完整页面

- 如果 HTML 以 `<!DOCTYPE` 或 `<html` 开头，服务端会按整页处理
- 否则服务端会自动包进统一框架模板，并注入样式和辅助脚本

默认优先写**内容片段**，不要默认手写整页 HTML。

## 启动会话

```bash
scripts/start-server.sh --project-dir /path/to/project
```

返回结果大致如下：

```json
{"type":"server-started","port":52341,"url":"http://localhost:52341","screen_dir":"/path/to/project/.superpowers/brainstorm/12345-1706000000/content","state_dir":"/path/to/project/.superpowers/brainstorm/12345-1706000000/state"}
```

你需要记住：

- `screen_dir`
- `state_dir`
- `url`

然后通知用户打开这个 `url`。

### 获取连接信息

服务端也会把启动信息写入 `$STATE_DIR/server-info`。  
如果你没拿到 stdout，就从这个文件取 URL 和端口。

### Codex 下的启动建议

Codex 往往会回收脱离控制的后台进程，因此通常直接运行脚本即可。  
如果当前环境会回收后台进程，应使用前台模式并结合 Codex 自身的后台执行能力。

### 远端 / 容器场景

如果浏览器无法打开返回的 URL，可显式指定监听地址：

```bash
scripts/start-server.sh \
  --project-dir /path/to/project \
  --host 0.0.0.0 \
  --url-host localhost
```

## 交互循环

1. 确认服务仍存活，再写新 HTML 到 `screen_dir`
2. 告诉用户当前页面用途，并附上 URL
3. 下一轮读取 `$STATE_DIR/events`
4. 结合浏览器点击和终端反馈理解用户意图
5. 根据反馈生成新页面，继续迭代
6. 需要切回终端时，推一个“后续继续在终端沟通”的等待页

### 写页面时的规则

- 用有语义的文件名，例如 `layout.html`、`layout-v2.html`
- **不要重复使用文件名**
- 用写文件工具生成 HTML，不要用 `cat` 或 heredoc
- 当前问题未确认前，不要切到下一个问题

## 最小示例

```html
<h2>哪个布局更合适？</h2>
<p class="subtitle">重点看可读性和视觉层级</p>

<div class="options">
  <div class="option" data-choice="a" onclick="toggleSelect(this)">
    <div class="letter">A</div>
    <div class="content">
      <h3>单栏布局</h3>
      <p>更聚焦，阅读负担更低</p>
    </div>
  </div>
  <div class="option" data-choice="b" onclick="toggleSelect(this)">
    <div class="letter">B</div>
    <div class="content">
      <h3>双栏布局</h3>
      <p>侧边导航更强，但视觉更复杂</p>
    </div>
  </div>
</div>
```

不需要自己补 `<html>`、CSS 或 `<script>`，服务端会自动处理。

## 常用样式

可直接使用的结构包括：

- `.options` / `.option`
- `.cards` / `.card`
- `.mockup`
- `.split`
- `.pros-cons`
- `.subtitle`

对应的样式和交互由以下文件提供：

- 样式框架：`scripts/frame-template.html`
- 前端辅助脚本：`scripts/helper.js`

## 收尾提醒

如果项目中使用了 `.superpowers/brainstorm/` 目录而它尚未被忽略，应提醒用户补到 `.gitignore`，避免把临时草图和事件文件误提交进仓库。
