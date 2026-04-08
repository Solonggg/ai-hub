---
name: iho-db-pgsql
description: 用于按 IHO 项目风格设计、评审和整理 PostgreSQL 建表与 DDL 变更脚本。适用于 `com.cnhis.iho` 相关模块中的短码表建表、扩表、字段设计、索引设计、注释规范、JSONB/数组字段设计和 DDL 文档整理。最终输出统一落到项目根目录 `doc/spec/<需求目录名>/ddl-design.md`。
---

# IHO DB PGSQL

## 概述

本 skill 只关注 PostgreSQL 建表与 DDL 设计规范，不涉及 Java 实体、DTO、Mapper、Service 或其他应用层代码。以 [references/style-guide.md](references/style-guide.md) 作为建表风格依据，并将最终产出的建表脚本统一整理到项目根目录的 `doc/spec/<需求目录名>/ddl-design.md`。

## 工作流程

1. 先阅读 [references/style-guide.md](references/style-guide.md)，确认当前短码表的命名、字段、类型、基础列和索引风格。
2. 根据业务域确定表前缀，并保持与现有短码表一致的命名方式，例如 `ndy1`、`ndz1`、`nea1`。
3. 仅从 DDL 角度设计：
   - 表名
   - 字段名
   - 字段类型
   - 默认值
   - 非空约束
   - 主键
   - 索引
   - 表注释和列注释
4. 判断字段类型归属：
   - 短文本快照：通常 `varchar(50)`、`varchar(100)`、`varchar(255)`、`varchar(500)`
   - 长文本：通常 `text`
   - 结构化集合：通常 `jsonb`
   - 代码型字段：通常 `varchar(2)`
   - 主数据关联：优先复用现有编码字段，如 `bck01*`、`bce01*`、`vaa07`
5. 保留该表族的共享基础列：
   - `created_by integer`
   - `created_time timestamp default CURRENT_TIMESTAMP`
   - `updated_by integer`
   - `updated_time timestamp`
   - `delete_flag boolean default false not null`
   - `version integer default 0 not null`
   - `vorg_id bigint`
6. 为明显查询字段增加索引，例如 `bck01a`、`bck01b`、`vaa07`。
7. 最终将输出整理为 Markdown 文档，路径固定为：
   - `项目根目录/doc/spec/<需求目录名>/ddl-design.md`
8. 如果 `doc/specs/<需求目录名>` 不存在，先创建目录，再写入 `ddl-design.md`。

## 输出要求

- 最终交付物必须是 Markdown 文件，而不是只在对话里贴 SQL。
- 文件路径固定为 `doc/spec/<需求目录名>/ddl-design.md`。
- 文件内容建议至少包含：
  - 变更背景
  - 设计原则
  - 建表/改表脚本
  - 索引脚本
  - 注释脚本
  - 风险或兼容性说明
- SQL 统一放在 fenced code block 中，语言标记使用 `sql`。
- 如果同时包含多张表，按表逐段组织，不要把所有 SQL 混成一整块。

## 硬规则

- 只输出 PostgreSQL DDL 规范与脚本，不扩展到 Java 代码规范。
- 表名保持小写、紧凑、短码化，不改造成冗长英文业务名。
- 单表只使用一套主业务前缀，主键通常为 `<prefix>01`。
- 该表族默认包含共享基础列：`created_by`、`created_time`、`updated_by`、`updated_time`、`delete_flag`、`version`、`vorg_id`。
- 表注释和列注释必须完整输出，不接受只有建表语句没有注释。
- 简单结构化集合字段默认使用 `jsonb`，不要降级为普通文本。
- 真数组数据使用 PostgreSQL 数组；不要为省事改成逗号分隔字符串。
- 索引只建在明确的查询、过滤、关联字段上，不盲目堆索引。
- 复用 IHO 既有业务编码字段，不随意重命名成泛化业务名。
- 只有在仓库没有直接 DDL 证据时，才允许写“推断”。

## 评审清单

- 表名、主键名、业务字段名是否遵循前缀加编号风格。
- 字段类型是否贴合既有 DDL 家族，而不是随意放大或缩小。
- 共享基础列是否完整。
- JSON、数组、长文本字段是否使用了正确的 PostgreSQL 类型。
- 常用过滤字段是否补了索引。
- 表注释和列注释是否完整。
- 最终脚本是否已经写入 `doc/spec/<需求目录名>/ddl-design.md`。
