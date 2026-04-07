# IHO PostgreSQL DDL 风格参考

## 证据来源

当前主要 DDL 证据来自：

- `doc/feat/feat_v4.3.4.md`

本参考只保留对建表和 DDL 设计有直接价值的内容，不涉及 Java 映射规则。

## 样本表

- `ndy1`：工作讨论表
- `ndz1`：业务学习表
- `nea1`：病例讨论表

用户最初提到 `ndyz1`，但当前仓库中实际可确认的是 `ndz1`。

## 样本特征

### 1. `ndy1`

关键 DDL 特征：

- 表名：`ndy1`
- 主键：`ndy01 bigint primary key`
- 字段类型：
  - `bck01a integer`
  - `bck01b integer`
  - `ndy02 timestamp`
  - `bce01 integer`
  - `bce03 varchar(50)`
  - `ndy05 varchar(500)`
  - `ndy06 varchar(255)`
  - `ndy07 jsonb`
  - `ndy08 text`
  - `ndy09 jsonb`
- 共享基础列：
  - `created_by integer`
  - `created_time timestamp default CURRENT_TIMESTAMP`
  - `updated_by integer`
  - `updated_time timestamp`
  - `delete_flag boolean default false not null`
  - `version integer default 0 not null`
  - `vorg_id bigint`
- 索引：
  - `idx_ndy1_bck01a`
  - `idx_ndy1_bck01b`

### 2. `ndz1`

关键 DDL 特征：

- 表名：`ndz1`
- 主键：`ndz01 bigint primary key`
- 字段类型：
  - `bck01a integer`
  - `bck01b integer`
  - `ndz02 timestamp`
  - `bce01a integer`
  - `bce03a varchar(50)`
  - `ndz03 varchar(2)`
  - `ndz04 varchar(2)`
  - `ndz05 varchar(500)`
  - `ndz06 jsonb`
  - `ndz07 varchar(500)`
  - `ndz08 text`
  - `ndz09 text`
  - `ndz10 jsonb`
  - `ndz11 jsonb`
- 共享基础列：
  - `created_by integer`
  - `created_time timestamp default CURRENT_TIMESTAMP`
  - `updated_by integer`
  - `updated_time timestamp`
  - `delete_flag boolean default false not null`
  - `version integer default 0 not null`
  - `vorg_id bigint`
- 索引：
  - `idx_ndz1_bck01a`
  - `idx_ndz1_bck01b`

### 3. `nea1`

关键 DDL 特征：

- 表名：`nea1`
- 主键：`nea01 bigint primary key`
- 字段类型：
  - `bck01a integer`
  - `bck01b integer`
  - `nea02 timestamp`
  - `bce01a integer`
  - `bce03a varchar(50)`
  - `bce01b integer`
  - `bce03b varchar(50)`
  - `bce01c integer`
  - `bce03c varchar(50)`
  - `vaa07 bigint`
  - `vaa05 varchar(100)`
  - `nea03 jsonb`
  - `nea04 varchar(500)`
  - `nea05 varchar(2)`
  - `nea06 varchar(2)`
  - `nea07 varchar(2)`
  - `nea08 jsonb`
  - `nea09 text`
  - `nea10 text`
  - `nea11 text`
  - `nea12 text`
  - `nea13 text`
  - `nea14 text`
  - `nea15 text`
- 共享基础列：
  - `created_by integer`
  - `created_time timestamp default CURRENT_TIMESTAMP`
  - `updated_by integer`
  - `updated_time timestamp`
  - `delete_flag boolean default false not null`
  - `version integer default 0 not null`
  - `vorg_id bigint`
- 索引：
  - `idx_nea1_bck01a`
  - `idx_nea1_bck01b`
  - `idx_nea1_vaa07`

## 归纳出的 DDL 风格

### 表命名

- 使用小写、短码化表名。
- 常见形式为三位业务前缀加数字后缀 `1`。
- 不要默认改成冗长英文业务名。

示例：

- `ndy1`
- `ndz1`
- `nea1`

### 字段命名

- 主键通常使用 `<prefix>01`。
- 业务字段通常继续使用同前缀加编号，如 `<prefix>02`、`<prefix>03`。
- 公共主数据字段直接沿用既有编码，不改成泛化业务名。

示例：

- `bck01a`、`bck01b`
- `bce01a`、`bce03a`
- `vaa07`

### 字段类型风格

- 人员姓名类快照：通常 `varchar(50)`
- 关联性短文本：常见 `varchar(100)`、`varchar(255)`、`varchar(500)`
- 类别、层次、能级等代码值：常见 `varchar(2)`
- 长文本叙述：通常 `text`
- 结构化集合：通常 `jsonb`
- id 及主键：常见 `bigint`
- 科室、病区、员工编号：常见 `integer`

### 共享基础列

这一类表统一保留：

```sql
created_by integer,
created_time timestamp default CURRENT_TIMESTAMP,
updated_by integer,
updated_time timestamp,
delete_flag boolean default false not null,
version integer default 0 not null,
vorg_id bigint
```

### 索引风格

- 优先给明确过滤和关联字段建索引。
- 样本中常见索引字段：
  - `bck01a`
  - `bck01b`
  - `vaa07`

不要无依据地添加大量索引。

### 注释风格

- 每张表必须有 `COMMENT ON TABLE`
- 每个业务字段和共享基础字段都应有 `COMMENT ON COLUMN`
- 注释内容直接表达业务含义，不写空泛占位词

## 输出文件规范

最终输出统一写入：

- `项目根目录/doc/specs/ddl-design.md`

建议文件结构：

````md
# DDL 设计说明

## 背景

## 设计原则

## 表 1：xxx

```sql
create table ...
comment on table ...
comment on column ...
create index ...
```

## 表 2：xxx

```sql
...
```

## 风险与兼容性说明
````

要求：

- 使用 Markdown 保存，不要只回复一段 SQL 文本
- SQL 使用 `sql` fenced code block
- 多张表按表分段组织
- 如果目录不存在，先创建 `doc/specs`

## 新表模板

可按如下风格起草：

```sql
create table nxx1 (
    nxx01 bigint primary key,
    bck01a integer,
    bck01b integer,
    nxx02 timestamp,
    bce01a integer,
    bce03a varchar(50),
    nxx03 varchar(32),
    nxx04 jsonb,
    nxx05 text,
    created_by integer,
    created_time timestamp default CURRENT_TIMESTAMP,
    updated_by integer,
    updated_time timestamp,
    delete_flag boolean default false not null,
    version integer default 0 not null,
    vorg_id bigint
);
```

实际落地前仍需确认：

- 字段语义
- 字符串长度
- 是否需要 `jsonb`
- 是否需要索引
- 表注释和列注释的完整性

## 反例

- 只写 `create table`，不补 `comment on table` 和 `comment on column`
- 把结构化集合字段降级成普通文本
- 把应建索引的过滤字段漏掉
- 共享基础列缺失
- 无依据地把短码表重命名成冗长英文表
