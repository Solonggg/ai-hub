---
name: ui-ux-pro-max
description: 在需要为中文产品、中文页面或面向中国用户的 Web/App 界面提供风格、配色、排版、交互、图表或组件建议时使用
---

# ui-ux-pro-max

这是一个面向中文产品设计语境的 UI/UX 检索型 skill。它通过本地 CSV 数据和脚本，为你提供风格、配色、版式、交互、图表与移动端体验建议。

## 使用前提

确认本机可用 `python3`：

```bash
python3 --version
```

## 何时使用

用户出现以下需求时启用本 skill：

- 新做一个中文站点、App 页面、后台或小程序页面
- 想确定风格、配色、排版、图标或图表方案
- 想评审现有 UI 的体验、无障碍、层级或视觉质量
- 想为某个具体页面补充结构建议，例如首页、登录页、详情页、支付页、仪表盘

## 核心原则

- 默认优先中文语义：查询词可以直接写中文，脚本会自动扩展常见中英关键词。
- 默认优先中文可读性：中文界面优先使用支持中文的字体方案，不直接照搬只适合西文的字体组合。
- 先出设计系统，再补局部细节：除非用户只问一个很窄的问题，否则先跑 `--design-system`。
- 保留业务语气：医疗、金融、政务、教育等场景优先考虑信任感、可读性和信息层级，而不是单纯追求“酷”。

## 标准工作流

### 1. 先判断产品语境

从用户请求里提取四类信息：

- 产品类型：如医疗、教育、电商、内容社区、企业服务、工具、后台
- 用户类型：如大众消费者、专业用户、运营人员、销售、医生、学生
- 风格关键词：如极简、科技感、高级感、年轻化、玻璃拟态、深色模式
- 终端形态：Web、移动端、App、小程序、后台大屏

### 2. 必须先生成设计系统

```bash
python3 /ui-ux-pro-max/scripts/search.py "<中文查询>" --design-system -p "<项目名>"
```

推荐中文示例：

```bash
python3 /ui-ux-pro-max/scripts/search.py "医疗健康应用 极简 可信" --design-system -p "问诊助手"
python3 /ui-ux-pro-max/scripts/search.py "电商首页 年轻化 高转化" --design-system -p "潮流商城"
python3 /ui-ux-pro-max/scripts/search.py "企业服务后台 高密度 清晰" --design-system -p "运营后台"
```

这个命令会同时聚合：

- 产品类型建议
- 风格建议
- 配色建议
- 页面结构建议
- 排版建议
- 反模式与交付前检查项

### 3. 只在需要时补局部检索

```bash
python3 /ui-ux-pro-max/scripts/search.py "<中文查询>" --domain <domain>
```

常用领域：

- `product`：产品类型和推荐风格
- `style`：视觉风格、质感、动效
- `color`：语义配色
- `typography`：排版气质
- `landing`：落地页结构、CTA 位置
- `chart`：图表类型
- `ux`：交互与无障碍建议
- `react`：React/Next 性能与体验建议
- `web`：移动端界面、表单、可访问性

示例：

```bash
python3 /ui-ux-pro-max/scripts/search.py "搜索页 加载 骨架屏" --domain ux
python3 /ui-ux-pro-max/scripts/search.py "金融产品 配色 稳重" --domain color
python3 /ui-ux-pro-max/scripts/search.py "后台 仪表盘 图表" --domain chart
```

### 4. 需要落盘时使用持久化

```bash
python3 /ui-ux-pro-max/scripts/search.py "<中文查询>" --design-system --persist -p "<项目名>" --page "<页面名>"
```

它会生成：

- `design-system/<project>/MASTER.md`：全局设计主规则
- `design-system/<project>/pages/<page>.md`：页面级覆盖规则

使用顺序：

1. 先看页面级规则
2. 页面规则存在时覆盖主规则
3. 页面规则不存在时完全遵循 `MASTER.md`

## 中文查询策略

- 直接用中文写需求，不需要先翻译成英文。
- 查询词至少包含 `产品类型 + 风格/目标 + 页面/终端形态` 三部分。
- 如果第一次结果偏泛，补充业务语气词，例如：`可信`、`高转化`、`高密度`、`内容优先`、`年轻化`、`高级感`。
- 如果是中国常见业务形态，优先显式写出：`小程序`、`后台`、`详情页`、`支付页`、`内容社区`、`问诊`、`预约`、`直播`。

## 字体与中文界面约束

- 中文项目默认优先使用支持中文的字体方案，例如 `Noto Sans SC`、`Noto Serif SC`。
- 如果数据集返回的是西文字体组合，只借鉴其气质、层级和字重关系，不直接原样照搬。
- 信息密度高的页面，优先考虑字重层级、行高和留白，而不是复杂装饰。

## 交付前最低检查

- 所有可点击元素都有清晰状态反馈
- 浅色与深色模式都单独校验对比度
- 图标不用表情符号替代
- 375px 移动端宽度下不炸布局
- 固定头部、底部按钮和弹层不会遮挡主要内容
- 表单错误、加载状态、空状态都明确可见

## 输出格式

```bash
# 终端盒状输出
python3 /ui-ux-pro-max/scripts/search.py "企业服务后台 高密度" --design-system

# Markdown 输出，适合写文档
python3 /ui-ux-pro-max/scripts/search.py "企业服务后台 高密度" --design-system -f markdown
```
