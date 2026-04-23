## fdp-admin · FDP 表单字段 + 字典一体化 skills

本目录收纳两个配合使用的 skill，专门处理 fdp-admin（`fdp/sourceFile/**/form/*.xml`）`Sform` 表单的字段新增与字典挂接。

```
fdp-admin/
├── fdp-form/          # 表单字段新增
│   ├── SKILL.md
│   └── references/    # 10 个 html_type 模板（input / textarea / digital / date / search / search_more / radio / checkbox / select / linebar）
└── business-dict/     # 业务域字典库
    ├── SKILL.md
    └── references/    # 每本字典一个 XML 文件（丢文件即上线）
```

## 工作原理

### 触发方式
两个 skill 都按 CLAUDE.md 的触发条件自动激活：

- **fdp-form**：匹配到 `Sform` 根节点的 XML 新增 `<properties>` 字段节点
- **business-dict**：需要挂 `<wordbook>` 字典片段，或在 `references/` 下加字典

### 协作流程
```
用户说"在 xxx.xml 新增字段 yyy，类型 SEARCH，挂 X 字典"
    ↓
fdp-form 接管，校验 val_key + 读目标 XML 风格
    ↓
字段是字典类型（SEARCH / SEARCH_MORE / RADIO / CHECKBOX / SELECT）
    ↓
fdp-form 通过 Skill 工具调用 business-dict
    ↓
business-dict 按决策流程（沿用 → 业务域命中 → 问用户）定位字典
    ↓
返回完整 <wordbook> 片段（{{VALUE}} 已替换为分类码）
    ↓
fdp-form 以 markdown 表格预览字段列表等用户确认
    ↓
用户确认 → 选模板 → 替换占位符 → Edit 写入 → XML 合法性自检
```

关键设计：
- **预览前置**：字典字段强制先查 business-dict 再预览，禁止凭记忆填字典
- **文件即配置**：新增字典只需往 `business-dict/references/` 丢文件，无需改任何 SKILL.md
- **模板即事实**：`fdp-form/references/*.xml` 是每种 html_type 的权威模板，机械替换占位符即可，不再推断

## 使用示例

### 示例 ：新增字段
```
在表单@file:/Users/wangjie/workspace/project/fdp/sourceFile/100504/form/2044609262595911682.xml 中追加以下字段

rft02	timestamp(6)	检查日期
rft26	varchar(18)	登记机构代码
rft27	varchar(80)	登记机构名称
rft30	timestamp(6)	登记日期时间
rft03	varchar(400)	临床处置
rft04	varchar(1000)	医生指导
rft05	varchar(2)	是否分娩 #bzd03=151
rft06	varchar(18)	分娩机构代码
rft07	varchar(80)	分娩机构名称
rft08	varchar(2)	妊娠风险专案是否结案 #bzd03=151
```

或者

```
在表单@file:/Users/wangjie/workspace/project/fdp/sourceFile/100504/form/2044609262595911682.xml 中 家庭地址 字段的后面继续追加以下字段

@ApiModelProperty("是否转诊 #bzd03=151")
private String rft10;

@ApiModelProperty("是否分娩 #bzd03=151")
private String rft05;

@ApiModelProperty("是否预约 #bzd03=151")
private String rft15;

@ApiModelProperty("检查机构代码")
private String rft23;

@ApiModelProperty("检查机构名称")
private String rft24;

@ApiModelProperty("登记日期时间")
private LocalDateTime rft30;
```

fdp-form 会：
1. 读 `2044609262595911682.xml`，Grep `上述提供的字段` 确认未占用
2. 输出预览表格：

   | # | val_key | name | html_type | 必填 | 多选 | 字典 | 备注 |
   |---|---|---|---|---|---|---|---|
   | 1 | phone_no | 联系电话 | INPUT | 否 | — | — | max_length=20 |

3. 用户回复"确认"后，打开 `fdp-form/references/*.xml`，把 `{{NAME}}`/`{{VAL_KEY}}`/`{{MAX_LENGTH}}` 替换为 `字段名`/`字段编码`/`字段长度（非必需，默认 300)`
4. 在 `</formFieldList>` 之前插入新节点
5. 用 `python3 -c "import xml.etree.ElementTree as ET; ET.parse('...')"` 自检


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
