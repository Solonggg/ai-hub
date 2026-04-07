# iho Java 开发规范

本规范适用于 `com.cnhis.iho` 体系下的 Java 项目，例如 `iho-mrms`、`iho-nursing`、`iho-cssd` 等。

当前内容基于 `iho-mrms` 项目提炼，但规则按 `iho-*` 通用工程约束表述。遇到具体项目存在明确既有风格时，以当前项目中的稳定风格为准。

## 项目事实

- 构建方式：Maven 多模块工程。
- Java 版本：11。
- 当前样本项目模块：
  - `iho-*-api`：DTO、常量、服务接口。
  - `iho-*-provider`：业务实现、Mapper、Entity、配置、远程调用。
  - `iho-*-rest`：Spring Boot 启动类、Controller、表单对象、对外接口。
  - `iho-*-sdk`：SDK 相关代码。
  - `iho-*-dependencies`：依赖和插件版本管理。
- 常见技术栈：Spring Boot、MyBatis/MyBatis-Plus、Lombok、Swagger、缓存、重试、异步。
- 常见包前缀：`com.cnhis.iho.*`。

## 分层约束

- 新增接口契约、请求响应对象、常量、服务接口，优先放到 `api` 模块。
- `provider` 负责业务实现、数据访问、远程调用适配，不把核心业务逻辑堆进 `rest`。
- `rest` 只做参数接收、基础转换、鉴权/路由编排、结果包装。
- 不要在这个项目里引入与现有分层冲突的新范式，比如把 MyBatis 访问改成 JPA/Hibernate。
- 新增包结构优先沿用已有语义目录，如 `controller/...`、`service/impl`、`mapper`、`remote`、`config`、`dto`。

## 控制器规范

- 沿用 `@RestController + @RequestMapping` 风格。
- Controller 返回值如无特殊情况，统一使用 `com.cnhis.cloud.health.common.core.response.Result`。
- 查询、保存、删除、批量操作、校验等普通 JSON 接口，都应返回 `Result<T>` 或 `Result<Void>`，不要直接返回裸对象、`List`、`Map`、`Boolean`、`String`。
- 分页查询接口统一返回 `Result<Page<T>>`；不要返回裸 `Page<T>`，也不要把分页结果拆成 `Result<List<T>>` 再额外拼总数等字段，除非已有明确历史协议必须兼容。
- 只有在以下场景可以不返回 `Result`：文件下载/导出、直接写 `HttpServletResponse` 流、框架约束的回调接口、确实需要返回非 JSON 原始响应的兼容接口。
- 已有历史接口如果返回裸对象，新增接口不要继续复制这种做法；优先按 `Result` 收口，存量接口仅在兼容性要求明确时保持原样。
- 有既有 Swagger 风格的模块，延续 `@Api`、`@ApiOperation`；新增 Controller 默认补齐类级和方法级 Swagger 注解。
- 对外接口方法的复杂入参优先沿用 `@ApiParam`、`@RequestBody`、`@Valid` 等当前项目已有组合，避免接口文档缺字段或缺约束说明。
- Controller 中不写复杂业务、不直接拼 SQL、不做重型状态处理。
- 参数校验、时间边界处理、简单装配可以放在 Controller，但业务分支和事务必须下沉到 Service。
- Controller 允许直接返回 Service 层的 `Result`，这是当前项目中的稳定写法；前提是控制层没有额外响应结构需要组装。
- 如果 Controller 需要先做参数补齐、时间边界修正、权限或来源判断、下载响应头设置等控制层处理，应先处理再调用 Service，最后仍统一返回 `Result`。
- 不要在 Controller 中随意混用“部分方法直接透传 Service 的 `Result`、部分方法手工拼另一套响应结构”的写法；除非该接口是明确的历史兼容例外。

## Service 规范

- 服务接口命名沿用 `xxxService`，实现类使用 `xxxServiceImpl`。
- 写操作、跨表修改、需要保证一致性的逻辑，放在 Service 层并使用 `@Transactional(rollbackFor = Exception.class)`。
- 公共业务逻辑先复用已有 Service、Util、Remote、Template，不重复造轮子。
- 日志使用项目现有 `@Slf4j` 风格，日志内容只记录排障所需关键信息，不输出无意义重复日志。
- 优先做最小必要抽象；只有当重复逻辑已经明确出现时，再抽公共方法或组件。
- 默认保持主流程局部线性可读，不要为了“方法短”把顺序执行的简单逻辑拆成一串私有方法。
- 只有在以下场景才进一步拆方法：逻辑会复用、需要形成稳定抽象边界、需要隔离副作用/便于测试、或者不拆会明显损伤理解。
- 对只调用一次且没有抽象价值的方法保持克制；读代码的人应尽量能在一个方法内看完整个业务主干。

## Mapper 与数据访问规范

- 继续使用 MyBatis / MyBatis-Plus 的 `@Mapper`、`QueryWrapper`、`LambdaQueryWrapper` 风格。
- 先检查是否已有对应 Mapper、XML、通用查询方法，避免重复定义近似 SQL。
- Mapper 接口命名与 XML 命名保持一致，方法名与 SQL 语义保持一致。
- 如果当前项目像 `iho-mrms` 一样把 `src/main/java` 下的 `mapper/**/*.xml` 当资源打包，新增 Mapper XML 要放在约定目录下，避免放错到不会被打包的位置。
- 查询条件优先复用现有 DTO / ReqDTO，不轻易新增含义重复的对象。
- 涉及分页时，优先沿用项目已有 `com.baomidou.mybatisplus.extension.plugins.pagination.Page` `Page<T>` 模式。

## DTO / Entity / Form 规范

- DTO 大量使用 Lombok，优先沿用 `@Data`、`@Builder`、`@NoArgsConstructor`、`@AllArgsConstructor` 等现有组合。
- 网关请求对象需要承接当前登录人、机构、网关上下文时，优先继承 `com.cnhis.cloud.health.common.core.model.GwUserReqBaseDTO`。
- 只要接口语义是“分页查询 / 分页检索 / 分页列表”，并且需要页码、页大小等分页参数时，优先继承 `com.cnhis.cloud.health.common.db.model.GwUserReqPageDTO`，不要再手工重复定义分页字段。
- 如果只是单条查询、详情查询、保存、修改、删除、批量动作、状态流转、导出条件、同步调用等非分页请求，即使字段很多，也优先继承 `GwUserReqBaseDTO` 而不是 `GwUserReqPageDTO`。
- `GwUserReqPageDTO` 适用于“分页查询条件对象”，`GwUserReqBaseDTO` 适用于“普通业务请求对象”；不要因为“以后可能分页”而提前继承分页基类。
- 返回对象、响应对象、VO 原则上不要继承 `GwUserReqBaseDTO` / `GwUserReqPageDTO`；如果历史代码里存在少量反例，不视为新增代码模板。
- 只要对象会进入 `api` 模块 Service 接口签名、会被 `rest` 与 `provider` 共同依赖、会被 SDK/第三方接口复用，或者本质上属于跨模块契约，请求对象必须放到 `api/dto/req` 或对应业务子目录下。
- 如果对象只用于某一个 Controller 的表单接收、字段重组、页面提交结构适配，且不会进入 `api` Service 契约、不会被其他模块复用，可以放在 `rest/controller/form`。
- 能放 `api/dto/req` 的对象，不要为了图省事留在 `rest/controller/form`；`Form` 是控制层局部适配对象，不是默认的通用请求契约目录。
- 新增字段命名、注释、Swagger 注解风格与同目录现有类保持一致。
- 对外暴露的请求对象、响应对象、DTO、Form、VO、嵌套静态类，优先补齐 `@ApiModel` 与字段级 `@ApiModelProperty`。
- 字段级 Swagger 注解不是只写主对象字段；集合元素、嵌套对象、状态码字段、布尔标识字段、时间字段等也要写清中文含义、取值语义和必要的业务备注。
- `ReqDTO` 用于跨层请求契约，重点表达请求参数；`RespDTO` 用于接口返回契约，重点表达返回结果。
- `QueryDTO` 用于查询、筛选、检索条件对象；如果同时带分页语义，优先让 `QueryDTO` 继承 `GwUserReqPageDTO`。
- `Form` 用于 Controller 层接收页面或接口特定提交结构，允许更贴近前端报文；进入 Service 前如有必要应转换为 `ReqDTO`。
- `VO` 用于视图展示、树结构、卡片结构、嵌套子结构等输出模型，通常服务于展示，不要把 `VO` 当成通用请求入参名称。
- 同一层级不要混用后缀表达同一种语义，例如同为查询入参时，不要一部分叫 `*ReqDTO`、一部分叫 `*VO`、一部分叫 `*Form`。
- 不要为了少量字段手写冗长样板代码，除非该类已有明确的手写约束。

## 依赖与版本规范

- 版本优先走父 `pom` 与统一 dependencies 模块的依赖管理，不随意在子模块硬编码新版本。
- 新增依赖前先确认现有依赖树里是否已经提供同类能力。
- 避免引入会显著改变启动方式、ORM 方案、序列化规则或缓存行为的重量级依赖。

## 代码风格

- 保持 Java 11 兼容，不使用更高版本语法。
- 优先复用项目里已经存在的工具类和库，如 `StringUtils`、`ObjectUtils`、`CollectionUtils`、`Optional`、`BeanUtils`。
- 空值处理先保证语义清楚，再追求链式写法；不要为了“炫技”降低可读性。
- 不要加入“由 AI 生成”“ChatGPT”“Codex”之类标记。

## 注释规范

- 注释的目标是降低理解成本，不是为了“看起来规范”而堆字数；能靠命名、抽象边界和顺序表达清楚的简单代码，默认不补注释。
- 修改代码时同步审视注释：缺失的要补，啰嗦的要删，已经与实现不一致的要立即改，不允许留下误导性旧注释。
- 注释优先解释“为什么这样做”“业务约束是什么”“不这样做会出什么问题”，不要逐行复述“赋值”“判空”“循环”“调用方法”等代码表面动作。
- 优先在代码块前写中文注释，交代后续一段逻辑的意图、边界或兼容背景；行尾注释只保留给特别容易误解的枚举值、状态位、魔法值或临时兼容条件。
- 一段代码如果只是顺序执行的简单 CRUD、参数透传、基础判空、普通 DTO 拷贝、明显的集合遍历，一般不需要额外注释。
- 以下场景默认必须补中文注释：参数开关分支、兼容历史数据或历史接口的特殊处理、反射或动态能力、复杂流式转换、跨系统字段映射、补偿/修复逻辑、事务边界、缓存读写策略、异步/重试/幂等控制、状态流转与权限判断。
- 对外契约优先用结构化注释表达清楚：Controller 接口继续依赖 Swagger 注解说明接口语义，`api` 模块暴露的服务接口、关键扩展点、行为不直观的方法可补充 Javadoc 说明入参约束、返回语义、副作用和异常边界。
- DTO、Form、VO 等对象的字段说明优先通过 `@ApiModel`、`@ApiModelProperty` 等现有 Swagger 风格承载；字段语义复杂、存在取值约束或兼容含义时，再补充必要的字段注释。
- 私有方法不是都要写方法注释；只有当方法名仍不足以说明其业务意图、前置条件、状态影响或兼容原因时，才补方法级或代码块级注释。
- 注释内容保持短、准、稳，避免出现“临时方案”“先这样”“这里很重要”这类无信息量表述；需要跟踪后续处理时，用 `TODO(wangjie):` 或 `FIXME(wangjie):` 明确说明待办原因和触发条件。
- 发现一个方法必须靠大量碎片注释才能读懂时，先反查是不是命名、结构或职责划分有问题；注释用于补足必要上下文，不用于掩盖糟糕设计。

### 注释判断准则

- 读者如果只看方法名和局部变量名，仍然无法快速判断业务意图、前置条件、兼容原因、状态影响或失败后果，就应该补注释。
- 读者如果删掉注释后，仍能在几十秒内准确理解该段代码，而且不会误判边界条件，就不要为了“完整性”补注释。
- 同一个判断分支一旦承载业务规则、历史包袱或跨系统约束，宁可写一条准确注释，也不要让维护者靠上下文猜。

### 注释示例

```java
// 错误：只是把代码动作翻译成中文，没有增加任何信息
// 判断 patientId 是否为空
if (StringUtils.isBlank(patientId)) {
    return Result.failed("患者ID不能为空");
}

// 正确：交代业务原因和边界，说明这不是普通判空
// 老护理单据补录场景允许前端不传 patientId，这里回退到住院号反查，避免历史补录失败
if (StringUtils.isBlank(req.getPatientId()) && StringUtils.isNotBlank(req.getInHospitalNo())) {
    req.setPatientId(queryPatientIdByInHospitalNo(req.getInHospitalNo()));
}
```

## 改动策略

- 先找相邻实现作为模板，再做同风格扩展。
- 优先局部修复，不主动顺手改 unrelated 代码。
- 如果发现现有代码风格不完全一致，遵循“离修改点最近的稳定风格”。
- 涉及 SQL、事务、外部接口、缓存、异步、重试时，必须明确行为影响和回滚风险。

## 验证建议

- 能局部编译就不要默认全量构建，优先按模块验证。
- 常用验证方式：
  - `mvn -pl iho-*-provider -am test`
  - `mvn -pl iho-*-rest -am test`
  - `mvn -pl iho-*-api -am test`
- 如果项目缺少有效测试或环境依赖太重，至少说明未验证部分和潜在风险。
