---
name: iho-java
description: 在 `com.cnhis.iho` 体系的 Java、Spring Boot、MyBatis、Maven 多模块项目中新增、修改或评审代码时使用。
---

# IHO Java 规范

## 概览

在 `com.cnhis.iho` 体系及相近的 Java 工程中，先读取 [references/iho-java.md](references/iho-java.md) 再实现；其中“注释规范”与分层、DTO、数据访问规则同等重要。

## 执行要求

- 先核对当前项目的模块划分、已有代码风格，再套用参考规范。
- 如果参考规范与当前项目稳定实现冲突，以离修改点最近的稳定风格为准，并在回复中说明依据。
- 保持改动最小化，不主动引入与现有分层或技术栈冲突的新范式。
- 方法拆分以复用和抽象边界为前提，避免为了缩短方法而拆出大量只调用一次、降低局部可读性的私有方法。
- 把注释视为代码的一部分；新增或修改关键逻辑时，同步判断注释是否缺失、过度或已经失真，必要时一并补齐、删减或改写。

## 参考资料

- [references/iho-java.md](references/iho-java.md)：IHO Java 项目的分层、命名、数据访问、注释、依赖与验证规范。
