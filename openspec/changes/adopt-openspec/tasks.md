# Tasks

## 1. 样本域重铸（cxnote）

- [x] 1.1 通读 ADR-0019/0021/0023/0024/0025 与 cxnote 现行实现（`cxnote --help`、源码行为面），产出逐条映射清单：每条 ADR 内容标注去向（域 spec / CONTEXT.md / AGENTS.md / 退役），并核对实现与 ADR 无未决冲突。验证：清单覆盖五篇 ADR 全部条目，冲突项为零或有处置结论
- [x] 1.2 撰写本变更 `specs/cxnote/spec.md` 增量（条目状态机、命令面行为、批量语义、展示与回显、去重约束），形态按 design D4。验证：`openspec validate adopt-openspec --strict` 通过
- [x] 1.3 以样本实测校准 Requirement 粒度与形态；若样本暴露 D4 不足，先修订本变更 design.md 再继续。验证：校准结论可表述且后续域直接沿用

## 2. 其余三域重铸

- [x] 2.1 撰写 `specs/cx-studio/spec.md` 增量（ADR-0001：时间域资产保护、公开 API 删除约束）。验证：validate --strict 通过
- [x] 2.2 撰写 `specs/cx-wealthy/spec.md` 增量（ADR-0002~0010），逐条核对现行事实（含 i18n、依赖链约束的现行表述）。验证：validate --strict 通过
- [x] 2.3 撰写 `specs/cx-tools/spec.md` 增量（ADR-0011~0018），对照 cx_tools 框架现行接口校准行为面。验证：validate --strict 通过
- [x] 2.4 按映射清单归位非行为内容：决策方法论条目写入 CONTEXT.md 对应 Domain 分区或 AGENTS.md；无现行效力条目列入退役清单。验证：映射清单每一条都有落点，无悬空

## 3. 退旧

- [x] 3.1 删除 `docs/agents/issue-tracker.md` 与 `docs/agents/triage-labels.md`。验证：两文件不存在
- [x] 3.2 按 design D6 改写 `AGENTS.md`（文档地图、必读清单、决策先行条款、Issue tracker / Triage labels 两节替换、全文 ADR 引用改写为独立陈述）。验证：全文无 issue tracker、triage、ADR 编号残留
- [x] 3.3 改写 `docs/agents/domain.md` 开篇技能引用；整体删除 `docs/adr/` 目录（含 README 索引）。验证：目录不存在，domain.md 无旧主语残留
- [x] 3.4 清除 `.scratch/` 追踪内容（cxnote-batch-drop 已由 ADR-0024 与实现承载，无信息丢失）。验证：`.scratch/` 不存在或为空
- [x] 3.5 按 design D7 填充 `openspec/config.yaml` 的 `context:`（清除模板注释）。验证：`openspec context --json` 正常返回，内容指向现行体制

## 4. 收口

- [ ] 4.1 两轮引用扫描（design D5 模式：第一轮扫 `docs/adr`、`ADR-\d{4}`、`.scratch`、`triage`、`issue-tracker`、`wayfinder`；第二轮删除后复扫正文残留指称）。验证：第二轮零命中
- [ ] 4.2 全域结构校验：`openspec validate adopt-openspec --strict`，确认五个能力域 delta 齐备（specs/norms 已在本变更规划期落稿）。验证：命令零错误
- [ ] 4.3 单次原子提交：specs 新增 + 退旧删除 + AGENTS.md/CONTEXT.md/config.yaml 改写收进同一 commit，commit message 独立完备（改了什么、为什么，不赘述 diff）。验证：`git show --stat` 单 commit 覆盖全部改动
