## fdp-admin · FDP 表单字段 + 字典一体化 skills

本目录收纳两个配合使用的 skill，专门处理 fdp-admin（`fdp/sourceFile/**/form/*.xml`）`Sform` 表单的字段新增/修改与字典挂接。

```
fdp-admin/
├── fdp-form/          # 表单字段新增/修改
│   ├── SKILL.md
│   └── references/    # 10 个 html_type 模板（input / textarea / digital / date / search / search_more / radio / checkbox / select / linebar）
└── business-dict/     # 业务域字典库
    ├── SKILL.md
    └── references/    # 每本字典一个 XML 文件（丢文件即上线）
```

## 工作原理

### 触发方式
两个 skill 都按 CLAUDE.md 的触发条件自动激活：

- **fdp-form**：在 `Sform` 根节点 XML 中新增或修改 `<properties>` 字段节点；覆盖 INPUT/TEXTAREA/DIGITAL/DATE/SEARCH/SEARCH_MORE/RADIO/CHECKBOX/SELECT/LINEBAR 全部 html_type；口语触发词——"加字段""新增字段""往表单里加输入框/下拉/日期/单选/多选""FDP 表单加字段"
- **business-dict**：给 SEARCH/SEARCH_MORE/RADIO/CHECKBOX/SELECT 字段挂 `<wordbook>` 片段、选业务域字典（健康档案/病案/护理等），或在 `references/` 下加字典；被 fdp-form 处理字典字段时自动联动；口语触发词——"挂字典""配字典""换字典""这个字段用哪本字典""分类码"

### 协作流程
```
用户贴字段清单（列定义 / ApiModelProperty）到目标 XML
    ↓
fdp-form 接管：Read 目标 XML，Grep 每个 val_key 是否已占用，观察同文件字段风格
    ↓
存在字典字段（SEARCH / SEARCH_MORE / RADIO / CHECKBOX / SELECT）
    ↓
fdp-form 通过 Skill 工具调用 business-dict
    ↓
business-dict 按决策流程（沿用目标 XML 已有字典 → 业务域命中 → 问用户）定位字典
    ↓
返回完整 <wordbook> 片段（{{VALUE}} 已替换为确认过的分类码）
    ↓
fdp-form 输出"待新增字段" markdown 表格；若有冲突/已存在字段再单独输出"已存在字段"表格
    ↓
用户确认 → 选模板 → 机械替换占位符 → Edit 写入 → ET.parse 合法性自检
    ↓
落地后再输出"本次实际写入字段"最终结果表格
```

关键设计：
- **预览前置**：字典字段强制先查 business-dict 再预览，禁止凭记忆填字典
- **双表分离**：预览阶段"待新增字段"与"已存在字段"必须拆成两张表，避免用户误判哪些真正落地
- **表格双关卡**：预览表格（动码前） + 最终结果表格（落地后）都必须输出；预览不能替代最终
- **文件即配置**：新增字典只需往 `business-dict/references/` 丢文件，无需改任何 SKILL.md
- **模板即事实**：`fdp-form/references/*.xml` 是每种 html_type 的权威模板，机械替换占位符即可，不再推断

## 使用示例

### 示例：新增字段

两种等价输入方式（数据库列定义 / java代码）都支持：

```
在表单@file:/form/2044609262595911682.xml 中追加以下字段

rft23	varchar(18)	检查机构代码
rft30	timestamp(6)	登记日期时间
rft05	varchar(2)	是否分娩 #bzd03=151
```
或者
```
在表单@file:/form/2044609262595911682.xml 中 家庭地址 字段的后面继续追加以下字段

@ApiModelProperty("检查机构代码")
private String rft23;

@ApiModelProperty("登记日期时间")
private LocalDateTime rft30;

@ApiModelProperty("是否分娩 #bzd03=151")
private String rft05;
```

fdp-form 接管后会：

1. Read `2044609262595911682.xml`；Grep `rft23` / `rft30` / `rft05` 确认未占用，观察同文件字段风格（是否含 `labelColor` / `placeholder` / `name_i18n` 等）
2. 识别到 `rft05` 带 `#bzd03=151` 分类码标注 → 通过 Skill 调用 business-dict，按决策流程定位字典并返回完整 `<wordbook>` 片段
3. 输出"待新增字段"预览表格：

   | # | val_key | name | html_type | 必填 | 多选 | 字典（字典名 / 分类码） | 备注 |
   |---|---|---|---|---|---|---|---|
   | 1 | rft23 | 检查机构代码 | INPUT | 否 | — | — | max_length=18 |
   | 2 | rft30 | 登记日期时间 | DATE | 否 | — | — | date_format=yyyy-MM-dd HH:mm:ss |
   | 3 | rft05 | 是否分娩 | SEARCH | 否 | 否 | 健康档案数据字典 / bzd03=151 | 沿用目标 XML 已有字典 |

   若存在 `val_key` 冲突或目标 XML 已有同名字段，再单独输出"已存在字段"表格（列：`# / val_key / name / 当前状态 / 备注`）
4. 用户回复"确认" → 按示例 2 的"家庭地址字段后面"锚点，或默认在 `</formFieldList>` 之前插入
5. 打开 `fdp-form/references/{html_type}.xml`，机械替换 `{{NAME}}` / `{{VAL_KEY}}` / `{{MAX_LENGTH}}` / `{{DATE_FORMAT}}` / `{{WORDBOOK_BLOCK}}` 等占位符
6. `python3 -c "import xml.etree.ElementTree as ET; ET.parse('...')"` 验证合法；Grep 新 `<val_key>` 命中且仅命中 1 次
7. 再次输出"本次实际写入字段"最终结果表格（列同第 3 步），用户直接核对落地内容


## 如何添加其他字典

参见 `business-dict/SKILL.md` 的"新增字典 SOP"。简版操作：

**只做一件事**：在 `business-dict/references/` 新建一个 `.xml` 文件。不需要改任何 SKILL.md、不需要改 CLAUDE.md 索引。

### 步骤
1. **复制模板**：把 `business-dict/references/ehr-bzd1-dict.xml` 复制一份改名
2. **命名规范**：`{业务前缀}-{字段系列}-dict.xml`
   - 业务前缀：`ehr`（健康档案）/ `mrms`（病案）/ `nursing`（护理）/ 新业务自定
   - 字段系列：字典核心字段前缀 + 编号，如 `bzd1` / `bsq1` / `brv1`
   - 示例：`lis-blq1-dict.xml`（LIS 检验字典）
3. **改头部注释**（固定顺序，缺一不可）：

   ```xml
   <!--
     字典名：XXX 数据字典
     业务域：XXX / XXX
     字段系列前缀：bxx*

     业务域命中条件：
       - val_key 前缀：xxx* / yyy*
       - 文件名关键词：XXX / YYY

     元数据：
       id              = <字典 id>
       name            = XXX 数据字典
       field_key       = bxx03
       value_key       = bxx01
       show_key        = bxx02
       render_key      = bxx02
       search_key 列表 = abbrw, bxx02, abbrp

     默认分类码：无（必须由用户指定）
     常见分类码：
       xxx = XXXDMB（含义）

     使用方式：拷贝下方 <wordbook>...</wordbook>，把 {{VALUE}} 替换为用户确认过的分类码
   -->
   ```

4. **改 `<wordbook>` 片段**：
   - `<id>` 换成该字典的实际 id
   - `<name>` 换成字典中文名
   - 所有 `<field_key>` / `<value_key>` / `<show_key>` / `<render_key>` / `<search_key>` 按元数据改
   - `<conObj>.<value>` 保持 `{{VALUE}}` 占位符不动
5. **差异字段注意**：不同字典 `<conObj>` 内部结构可能不同（例：护理文书字典用 `<is_compare_field>` 而非 `<compare_field>`）。**以实际字典导出的 XML 为准**，不要硬套模板
6. **校验**：把新文件拖进项目，让 fdp-form 新挂一个测试字段——能跑通即上线

### 字典 XML 必备要素自检

| 要素 | 缺失后果 |
|---|---|
| 头部 `字典名` + `业务域` | 选字典决策看不到候选 |
| 头部 `业务域命中条件` | 自动选字典失败，每次都要问用户 |
| 头部 `元数据`（含 id） | 无法判断 `<wordbook><id>` 是否沿用 |
| `<conObj>` 完整结构 | 字段保存后取值异常 |
| `{{VALUE}}` 占位符 | 分类码硬编码 → 下次换类无法替换 |

## 常见坑速查

- **预览不可跳过**：fdp-form 要求先以 markdown 表格 echo 字段列表，用户回复"确认"才能动 Edit
- **已存在字段必须单独成表**：不能和"待新增字段"混在同一张表，否则用户无法直接判断哪些真正落地
- **落地后必须再输出 markdown 表格**：预览表格不能替代最终结果表格，最终表格以实际写入内容为准
- **跨业务域串字典**：最高发错误。决策第 1 步先看目标 XML 已有 `<wordbook><id>`
- **html_type 必须全大写**
- **日期字段必须配齐** `date_format` + `condition` + `max_date_condition` + `min_date_condition` + `unit` + `max_date_unit` + `min_date_unit`
- **DIGITAL 精度**：`NUMBER(n,m)` → `decimal_length=m`
- **Edit 前必须先 Read**
- **`{{VALUE}}` 占位符不要遗留在最终 XML 里**

## 参考

- 字段模板：`fdp-form/references/*.xml`
- 字典库：`business-dict/references/*.xml`
- 完整规则：`fdp-form/SKILL.md`、`business-dict/SKILL.md`
