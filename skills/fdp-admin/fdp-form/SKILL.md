---
name: fdp-form
description: 在 fdp-admin 表单 XML（Sform 根节点，通常位于 `fdp/sourceFile/**/form/*.xml`）中新增 `<properties>` 字段节点时使用
---

# fdp-form · FDP 表单字段新增

## 概览

把"加一个字段"的口语指令，转换为合法的 `<properties>` 节点并写入目标 XML。支持全部 FDP 原生 `html_type`（INPUT / TEXTAREA / DIGITAL / DATE / SEARCH / SEARCH_MORE / RADIO / CHECKBOX / SELECT / LINEBAR）。

## 何时使用

- 用户给出形如 `在 {xml_path} 中新增字段 {name}，val_key={val_key}，类型={html_type}` 的指令
- 用户要求往任意 fdp-admin `Sform` 表单追加字段
- 目标字段位于 `<formFieldList type="List">` 内

## 输入参数

| 参数 | 必需 | 说明 |
|---|---|---|
| `xml_path` | ✓ | 目标 XML 绝对路径 |
| `name` | ✓ | 字段中文名 → `<name>` |
| `val_key` | ✓ | 字段标识 → `<val_key>`，全文件唯一 |
| `html_type` | ✓ | FDP 原生类型（大写） |
| `dict` | 字典类型必需 | SEARCH / SEARCH_MORE / RADIO / CHECKBOX / SELECT 的字典 + 分类码；来源见 `business-dict` |
| `multi_select` | 可选 | SEARCH_MORE/CHECKBOX 默认 `1`；SEARCH/RADIO/SELECT 默认 `0` |
| `max_length` | 可选 | INPUT 默认 300、TEXTAREA 默认 500 |
| `decimal_length` | 可选 | DIGITAL 小数位，默认 0 |
| `date_format` | 可选 | DATE 格式，默认 `yyyy-MM-dd HH:mm:ss` |
| `position` | 可选 | 默认追加到 `</formFieldList>` 之前；想放别处必须先问 |
| `is_show` | 可选 | 默认 `0`（隐藏） |
| `is_empty` | 可选 | 默认 `1`（非必填） |

### 口语 → html_type

| 用户说 | html_type | 模板 |
|---|---|---|
| TEXT / 文本 / 输入框 | `INPUT` | `references/input.xml` |
| TEXTAREA / 多行文本 | `TEXTAREA` | `references/textarea.xml` |
| NUMBER / 数字 | `DIGITAL` | `references/digital.xml` |
| DATE / 日期 / 时间 | `DATE` | `references/date.xml` |
| 下拉 / 单选字典 | `SEARCH` | `references/search.xml` |
| 多选字典 / 标签多选 | `SEARCH_MORE` | `references/search_more.xml` |
| RADIO / 单选 | `RADIO` | `references/radio.xml` |
| CHECKBOX / 复选 | `CHECKBOX` | `references/checkbox.xml` |
| 原生 SELECT 下拉 | `SELECT` | `references/select.xml` |
| 分组条 / 标题栏 | `LINEBAR` | `references/linebar.xml` |

## 执行步骤

### 1. 参数与环境校验
- `Read` 目标 XML；`Grep` 检查每个 `val_key` 是否已占用。
- 观察同文件字段风格（是否含 `labelColor` / `placeholder` / `name_i18n` 等），后续模板选型与之对齐。

### 2. 字典字段先触发 business-dict（强制）

当 `html_type ∈ {SEARCH, SEARCH_MORE, RADIO, CHECKBOX, SELECT}`，在步骤 3 预览**之前**必须通过 `Skill` 调用 `business-dict`，拿到：
- 目标 XML 应绑定的字典
- 该字典完整的 `<wordbook>` 片段
- 分类码来源

预览表格里的字典列**必须**来自 `business-dict` 查询结果，不得凭记忆填写。

### 3. 预览确认（强制关卡，不可跳过）

动代码前**必须**以 markdown 表格列出全部新增字段等用户批准。用户显式回复"确认 / OK / 可以"之前：**不得调用 Edit / Write**。

表格列：

| # | val_key | name | html_type | 必填 | 多选 | 字典（字典名 / 分类码） | 备注 |

非字典字段的"多选""字典"列填 `—`。

表格外同步声明：
- **插入位置**：默认 `</formFieldList>` 之前或用户指定锚字段
- **所用字典及判断依据**（"沿用目标 XML 已有字典 → 病案数据字典" 之类）
- **待确认项**：分类码未知 / `val_key` 冲突 / 字典编码无法解析
- **被跳过字段**：如 `sysId` 等非 UI 字段、已存在的 `val_key`

用户修改参数 → 重新渲染表格。**反复预览 → 一次落地**，好于边改边问。

### 4. 选模板 + 替换占位符
- 按 `html_type` 打开对应 `references/*.xml`。
- 字典字段：把 `business-dict` 提供的 `<wordbook>` 整段（`{{VALUE}}` 已替换为确认分类码）填到 `{{WORDBOOK_BLOCK}}`。
- 替换其他占位符：`{{NAME}}` / `{{VAL_KEY}}` / 视类型 `{{MAX_LENGTH}}` / `{{DECIMAL_LENGTH}}` / `{{DATE_FORMAT}}`。
- 此步只做机械替换，不再猜测。

### 5. 定位锚点并写入
默认：插在最后一个 `</properties>` 之后、`</formFieldList>` 之前。
```
<old_string>
                <val_key>{最后一个字段}</val_key>
                ...
            </properties>
        </formFieldList>
</old_string>
<new_string>
                <val_key>{最后一个字段}</val_key>
                ...
            </properties>
            {新字段块}
        </formFieldList>
</new_string>
```
指定位置：锚点改为"在 `{锚字段}` 的 `</properties>` 之后"。

### 6. 写入后自检
- `python3 -c "import xml.etree.ElementTree as ET; ET.parse('{xml_path}')"` 验证合法
- `Grep` 确认新 `<val_key>` 命中**且仅命中 1 次**
- 输出改动摘要：新增字段 + 插入位置 + 默认生效的属性

## 字段属性速查

| 属性 | 默认 | 含义 |
|---|---|---|
| `<is_empty>` | `1` | `0`=必填、`1`=可空 |
| `<is_null>` | `1` | 旧校验位 |
| `<is_edit>` | `1` | 是否可编辑 |
| `<is_show>` | `0` | 是否显示 |
| `<is_back>` | `0` | 是否回填 |
| `<is_system_fields>` | `1` | 系统字段标识 |
| `<elem_width>` | `3` | 栅格宽度；LINEBAR/CHECKBOX/TEXTAREA 常用 12 |
| `<hide_title>` | `0` | 是否隐藏 label |
| `<auto_branch>` | `0` | 分支联动 |

## 常见坑

- **预览 → 确认 → 改码，顺序不可颠倒，预览不可跳过，且必须用 markdown 表格预览**：参数再明确也要先 markdown 表格 echo 一遍
- **`html_type` 必须全大写**
- **不要跨字典串用**：高发错误（把病案字段挂到健康档案字典）。新增字典字段前先 `Grep` 目标 XML 现有 `<wordbook><id>` 对齐，判定以 `business-dict` 决策流程为准
- **不要跨风格串模板**：目标文件不带的标签（`labelColor` / `placeholder` / `name_i18n` 等）不要凭空加，先 `Grep` 同文件样例
- **`val_key` 冲突必须 STOP**，由用户裁决（换号 / 迁移 / 放弃）
- **日期字段必须配齐** `date_format` + `condition` + `max_date_condition` + `min_date_condition` + `unit` + `max_date_unit` + `min_date_unit`
- **DIGITAL 精度**：`NUMBER(n,m)` → `decimal_length=m`
- **Edit 前必须先 Read**

## references 索引

- `references/input.xml` — 单行文本
- `references/textarea.xml` — 多行文本
- `references/digital.xml` — 数字
- `references/date.xml` — 日期 / 日期时间
- `references/search.xml` — 单选字典（搜索下拉）
- `references/search_more.xml` — 多选字典（标签多选）
- `references/radio.xml` — 单选按钮（字典）
- `references/checkbox.xml` — 复选按钮（字典）
- `references/select.xml` — 原生 SELECT 下拉
- `references/linebar.xml` — 分组标题栏

### 关联 skill

- `business-dict` — 字典元数据、`<wordbook>` 片段、选字典决策。字典字段**强制触发**。
