# Design

## Context

动机见 proposal.md（Why）。现状与约束：

- 时间域核心资产 `CxTime`（毫秒级）、`TimeRange`（起止段）已在 `cx_studio.core`，模型建立其上，不新造时间类型
- `ITimeRange.is_overlapped_with` 现为闭区间语义（端点相触视为重叠），仓库内无调用者；字幕模型以相邻衔接（首尾相接）为合法常态，本变更将其调整为严格交叠（见 D9）
- 现有工具应用层骨架同构（`application.py` / `appenv.py` / `appcontext.py` / `app_help.py` / `help.md` / `i18n/`），`app_help.py` 为标准件（`<Tool>Help(IAppComponent, WealthyHelp)`，模板来自 hosts_keeper）；带 `common/`+`components/` 分层的先例为 cxnote 与 ffpretty
- 工具内部分层惯例：`common/`（不依赖 appenv 的非耦合能力，工具间 import 只允许指向 `package.common`）/ `components/`（appenv 依赖或工具特化）
- 仓库已有 SPI 先例：media_scout 的 `MediaPathInspector`/`InspectorChain`——探测器在构造时显式注入，无全局注册表
- 本变更无新第三方依赖；仓库无测试基础设施，验证以实际运行为准

模型（Project/Sequence/Item）与格式侧（Loader/Saver 自治）为讨论定案，工件全文以此为准：Item 是可独立存在的普通对象，容器持引用；Sequence 是排列容器（尽力时序插入、读取恒时序视图）；Project 是组织者（不交叠路由、自动增列、元数据机制）；格式侧只认识 Item，语法提取与输出组织都归格式本体。

## Goals / Non-Goals

**Goals:**

- 字幕模型（Item/Sequence/Project）与格式框架（Loader/Saver 契约 + TimeCodec + Format）在 `subtitler.common` 层落地，可被其它工具 import；前台严格隔离
- subtitler CLI 完成 SRT/TTML/CSV 互转的端到端闭环
- `ITimeRange.is_overlapped_with` 调整为严格交叠

**Non-Goals:**

- 字幕内容的编辑、修剪、重排、质检——工具只搬运模型
- 格式发现的高级手段（内容嗅探、`--from/--to` 显式覆盖）——按扩展名查表，等真实场景出现再议
- 文件级元数据通道（如 TTML 头信息的读出与回写）——本变更不做，`Project.meta` 机制留待消费者
- 模型/框架迁往 `cx-studio` 独立子包——能力在 `subtitler.common` 层就地开放
- 测试基础设施搭建（仓库无测试基建，不在本变更内引入）

## Decisions

### D1. 包结构：common 层承载能力 + 纯前台，两级切分

```
packages/cxalio-studio-tools/
└── subtitler/                 # 工具包：common 层承载字幕能力，前台只装配
    ├── __init__.py            # 工具顶：__version__ + run() 组装入口；app 栈 import 下沉 run() 体内
    ├── common/                # 字幕能力层（对外提供面）：不依赖 appenv/前台，可被其它工具 import
    │   ├── __init__.py        # 汇聚导出（模型/格式框架）
    │   ├── model/
    │   │   ├── item.py        # SubtitleItem = TimeRange + text + speaker + extra
    │   │   ├── sequence.py    # SubtitleSequence：Item 排列容器
    │   │   └── project.py     # SubtitleProject：Sequence 容器 + 路由 + 元数据
    │   ├── loader.py          # SubtitleLoader 抽象基类（来源 → Items）
    │   ├── saver.py           # SubtitleSaver 抽象基类（Items + 目标 → 输出文件）
    │   ├── timecodec.py       # TimeCodec：模式驱动时间解析/格式化/单调取整
    │   ├── errors.py          # FormatError
    │   └── formats/           # 具体格式实现（SRT / TTML / CSV）
    │       ├── srt.py         # SrtFormat（含 SrtLoader/SrtSaver）
    │       ├── ttml.py
    │       └── csv.py
    ├── application.py         # SubtitlerApplication(IApplication)
    ├── appenv.py              # SubtitlerEnv(IAppEnvironment)
    ├── appcontext.py          # SubtitlerContext(IAppContext)
    ├── app_help.py            # SubtitlerHelp(IAppComponent, WealthyHelp)
    ├── help.md                # WealthyHelp 教程文本（源语言，load_localized_text 加载）
    ├── help.en_US.md          # 英文帮助（镜像多数现有工具）
    ├── banner.txt             # 启动 banner（镜像 hosts_keeper/media_killer 的加载模式）
    ├── i18n/                  # 本工具 gettext（domain: subtitler，仅前台文本；common 层不设 gettext）
    └── components/
        ├── wiring.py          # 本工具格式面（显式 dict 登记，扩展名表唯一来源）
        └── converter.py       # 转换编排（Loader → Project → Saver；错误呈现）
```

依据：按**能力**切层而非按工具内角色切目录——正确边界是「字幕能力」（`subtitler.common`：模型 + Loader/Saver 契约 + 格式实现）与「字幕工具前台」（四文件骨架 + `components/`：装配与交互）。能力层落 `common/` 而非顶层独立包，依据仓库组合面契约（CONTEXT.md：工具间 import 只允许指向 `package.common`，先例 `ffpretty.common.executor`）与 common 判别标准（不依赖 appenv 的对外提供面）。隔离靠两条纪律保证：common 不 import 前台任何模块；入口 `subtitler/__init__.py` 模块级只留 `__version__` 与 `run()`（app 栈 import 下沉 `run()` 体内——`cx_note` 为模块级 import，此处为刻意偏差），复用面验证（tasks 6.5：import common 后 `sys.modules` 无 `cx_tools`/`cx_wealthy`/`argparse`）常驻守卫。**无 engine**：Loader/Saver 各自完整自治（含自身 IO），编排只有一条——CLI 的 converter 组件，属前台；common 层不设编排组件。

### D2. 模型实现：引用语义 + list + bisect

- `SubtitleItem`：`frozen dataclass`，持有 `TimeRange`、`text: str`、`speaker: str | None`、`extra: dict[str, Any]`。`start`/`duration` 为 `TimeRange` 的派生视图属性，不独立存储。注意 `TimeRange` 本身可变（带 setter）——frozen 只挡字段重绑；Item 是普通对象，改写时间合法，Sequence 的读取面负责消化（见下）。`extra` 键带格式前缀（如 `ttml_style`），模型不解释
- `SubtitleSequence`：内部 `list[SubtitleItem]`；`add(item)`/`add_from(iterable)` 用 `bisect.insort` 按 start 定位（尽力时序；相等 key 取右侧插入点，无需自实现 tie-breaker）；无交叠检查。读取恒时序的活视图：常态由 insort 维持有序，读取路径做一次有序性检查（O(n)），检测到乱序（时间改写所致）则排序后给出。`take(item)` 按 `is` 身份匹配摘除并返回实例，未命中返回 None；`contains(item)` 同为身份匹配。无元数据、无名称、不暴露 index
- `SubtitleProject`：`sequences: list[SubtitleSequence]`（创建序，新增 append 尾部）+ `meta: dict[str, Any]`。`add(item)` 路由：按创建序遍历 Sequence，各序列内 bisect 找时序位置并检查与相邻 Item 的严格交叠（复用调整后的 `is_overlapped_with`，端点相触不算）——首个可容纳者即插入；全部容不下则新增 Sequence。`add_from` 逐个走 add。全量迭代：扁平归并各序列（量级千行，扁平排序 O(n log n) 足够）；`sequences` 按创建序迭代；`contains`/`take` 按身份定位所属 Sequence 摘除
- 传输语义：容器只收不放出复制——`take` 返回真实实例，`add`/`add_from` 收引用；无所有权转移、无复制
- **替代方案**：无序存储 + 读取排序——被否决（常态路径每次读取都付排序成本）；id 句柄/get——被否决（引用即句柄，零机制；「丢引用后凭句柄找回」无消费者且自带失效边角）；remove——被否决（take 已覆盖减员，销毁语义无消费者）

### D3. Loader/Saver 契约：格式本体完整自治

**两个基类，各自含 IO**——语法提取与输出组织都归格式本体，框架不持有格式知识的执行权，无约束声明机制（`allows_overlap`/`time_pattern` 之类不进接口；时间模式是各实现内部常量，经 TimeCodec 取用）：

```python
class SubtitleLoader(ABC):
    """格式读向：来源文件 → Item 列表。"""
    @abstractmethod
    def load(self, path: Path) -> list[SubtitleItem]: ...

class SubtitleSaver(ABC):
    """格式写向：Item 集合 + 目标路径 → 实际产出的文件路径列表。"""
    @abstractmethod
    def save(self, items: Iterable[SubtitleItem], target: Path) -> list[Path]: ...

@dataclass(frozen=True)
class Format:
    """格式身份：名称 + 所认扩展名 + 双向实现。"""
    name: str
    extensions: tuple[str, ...]
    loader: SubtitleLoader
    saver: SubtitleSaver
```

**Loader 自治**：自读文件（`cx_studio.filesystem.detect_file_encoding` 判定编码；探测返回 None 或解码失败 → `FormatError`）、自解析；来源入口为单文件路径，一次导入涉及的文件数由格式规范决定——Loader 可为一个入口自行读取关联文件（三格式均为单文件）。忠实提取：不重排、不丢弃、不改写；语法错误抛 `FormatError`（带位置信息）。**对容器无知**：接口只见 Item 与来源。

**Saver 自治**：收 Item 集合（可迭代）+ 目标路径，自主组织输出——单文件或多文件、交叠如何处理是它自己的事（SRT 自己分组拆文件，TTML/CSV 单文件照收）；组织后**写前一次性预检**全部目标路径（任一已存在 → 报错中止、零输出）、逐文件 UTF-8（无 BOM）写出、返回实际产出路径列表。多文件命名：目标 stem + `.part<k>`（从 1 起，按输出顺序），目录与扩展名跟随目标路径。有编号格式的 Saver 按其组织结果逐文件从 1、按 Item 时序写出编号字面。

**子类契约**（写入基类 docstring）：

1. 不依赖 appenv/context/前台组件——`subtitler.common` 层不得 import 前台任何模块，不得引入 `cx_tools`/`cx_wealthy` 任何符号；common 层不设 gettext（`FormatError` 详情按技术细节原样携带，用户面组合消息在前台用 `_()` 完成）
2. Loader 对模型容器一无所知；Saver 的输入是无结构的 Item 流——导出不读 Sequence 结构
3. Loader 忠实提取（不重排/丢/改）；Saver 自主组织且保证不丢片
4. 扩展位键必须带格式前缀（如 `ttml_style`），读写对称
5. 时间模式为各实现内部常量，解析/格式化/取整经 TimeCodec；严格解析，不做宽松兜底
6. 格式实现以 `Format` 对象打包——identity 集中一处，前台以它为参数

### D4. 三格式的规范依据与实现范围

|格式|依据|Loader|Saver|
|---|---|---|---|
|SRT|SubRip 事实标准（**无正式规范**；「序列不许交叠」是本工具采用的约定）|块解析（序号行忽略）、`HH:MM:SS,mmm` 严格解析、多行文本|按 start 扫描贪心分组（与当前组最晚 end 严格交叠冲突则另起组，组数不求最优）拆文件；每文件编号从 1；多行文本多行写出|
|TTML|W3C TTML1 / IMSC 文本子集|`<tt><body><div><p>`；时间接受 clock 与带单位偏移字面量（`10s`/`1.5s`/`100ms`…），底层换算调 TimeCodec；样式等入 extra（`ttml_` 前缀）|单文件（交叠照收）；`<br/>` ↔ 换行互逆；写出统一 clock（`HH:MM:SS.mmm`）；文件头信息无通道、不回写|
|CSV|RFC 4180 引号规则 + 本工具自定表头契约（字幕 CSV 无标准）|表头 `start,end,text,speaker` + 扩展列与 extra 键**原样互映射**（不加不减前缀；extra 键与保留列同名 → `FormatError`）；空单元格 ↔ `speaker=None` 与 extra 缺键|单文件（交叠照收）；扩展列集合 = 各 Item extra 键并集，缺失记空单元格；引号内换行表达多行|

时间模式（`HH:MM:SS,mmm` / clock / `HH:MM:SS.mmm`）为各实现内部常量。XML 解析用标准库 `xml.etree.ElementTree`（不引入 `lxml`）。

**多行文本的跨格式表示**（往返对称的前提）：模型 `text` 持真实换行（`\n`）——SRT 直接按多文本行读写；TTML 以 `<br/>` 表达（读写互逆）；CSV 以 RFC 4180 引号内换行表达。三格式两两互转保持换行等价。

### D5. CLI 接口

单动作工具，无动词表（cxnote 的 VERBS 是多动作模式，此处不适用）：

```
subtitler INPUT OUTPUT [-d] [-h | --tutorial]
```

- `SubtitlerContext` 按 `from_arguments()` 白名单工厂模式构造；字段：`input`、`output`、`debug_mode`、`show_help`、`show_full_help`
- 格式识别：按输入/输出文件扩展名查 wiring 的表；未识别 → 报错中止（不做内容嗅探：SRT 纯文本无可靠特征头）
- 转换为瞬时文件操作，不设 progress；输出走 `say()`（stderr）——Saver 返回的产出路径列表 MUST 经 `say()` 呈现（无裂变也报目标路径）；`SafeError` 由 **`SubtitlerApplication.__exit__`**（工具子类覆盖）捕获呈现并连同 `KeyboardInterrupt` 一并处理——`IApplication.__exit__` 基类只做 stop/清理、不捕获，责任在工具子类（镜像 `cx_note/application.py` 的覆盖模式）

### D6. 转换编排与前台接线（无全局注册表）

`components/converter.py`（IAppComponent）：扩展名查表定格式 → `Format.loader.load(input)` 得 Items → 逐个 `project.add(item)`（路由组织）→ `Format.saver.save(project, output)` 得产出路径 → `say()` 呈现。`FormatError`/`OSError` 转 `SafeError` 报错中止。

`components/wiring.py` 显式 dict 登记本工具启用的格式并汇总扩展名表——格式面唯一来源。**不在 `subtitler.common` 层设全局注册表**：仓库 SPI 先例 `InspectorChain` 是构造时显式注入；`subtitler.common` 只提供 `Format` 对象，不含登记动作；无隐藏状态、可测、换一个前台可接不同格式子集。

### D7. 依赖清单

|来源|能力|
|---|---|
|`cx_studio.core`|`CxTime`、`TimeRange`（时间原语）|
|`cx_studio.filesystem`|`detect_file_encoding`（编码探测，Loader 取用）|
|`cx_studio.i18n`|`load_localized_text`（帮助文本按 locale 加载）|
|`cx_tools.app`|`IApplication`/`IAppEnvironment`/`IAppContext`/`IAppComponent`、`SafeError`|
|`cx_wealthy`|`WealthyHelp`（帮助 DSL）、`rich_types`、theme|

**外部依赖：零新增**。候选逐一评估否决：`lxml`（`xml.etree` 对 TTML 子集足够）、`pysrt`/`srt`（买轮子等于放弃自己的模型，本变更目的就是建模型）、`sortedcontainers`（千行量级 `bisect` 足够）、独立编码探测库（复用 `detect_file_encoding`）。

### D8. `subtitler.common` 公开接口与外部使用路径

`subtitler/common/__init__.py` 汇聚导出（工具顶 `subtitler/__init__.py` 不转发——只留 `__version__` 与 `run()`，能力入口唯一指向 `subtitler.common`）：

- **模型层**：`SubtitleItem`、`SubtitleSequence`、`SubtitleProject`
- **格式层**：`Format`、`SubtitleLoader`、`SubtitleSaver`、`FormatError`、`SrtFormat`/`TtmlFormat`/`CsvFormat`（实现于 `subtitler.common.formats`）
- **工具**：TimeCodec

预期三种外部用法，各有直通路径：**转换**（Loader → Project → Saver）、**消费**（Loader 后只读遍历，供将来 QC/统计工具；Project 双层读取面按需取用）、**生成**（代码构建 Item → Project 路由 → Saver 写出）。

### D9. `ITimeRange.is_overlapped_with` 调整为严格交叠

Project 路由与 SRT Saver 分组的交叠判定复用 `ITimeRange.is_overlapped_with`。该方法现行闭区间语义（端点相触视为重叠）会把首尾相接的正常字幕衔接（如 [0,5s] 与 [5,10s]）判为交叠——相邻衔接在字幕领域是常态而非异常。调整为严格交叠（`start < other.end and other.start < end`，端点相触不视为交叠）：

- `is_contained_by`/`contains_time` 的闭区间语义不变
- 方法在仓库内无既有调用者，唯一受影响的行为契约是 `openspec/specs/cx-studio/spec.md` 的对应 Requirement——判定场景整体改写（原「共享端点视为重叠」场景预期反转），以 REMOVED + ADDED delta 承载（`specs/cx-studio/`，REMOVED 携 Reason/Migration），archive 时折回
- 同步修改 `cx_timerange.py` 三处 docstring 的语义表述（模块、`ITimeRange` 契约、方法）

## Risks / Trade-offs

- **TTML 子集**：TTML 规范庞大（区域、样式、帧率时基），按「能表达时间+文本+说话人的子集」实现；超出子集的结构元素不建模，复杂 TTML 降级保时间文本、样式入 extra——模型扩展位兜底。文件头信息（如 `xml:lang`）本变更不回写（无通道，Non-Goal）
- **SRT 贪心分组的最优性**：SRT Saver 的贪心分组不保证文件数最少，但保证合法（各组不交叠、无丢失）；最少分组是区间图着色，无必要
- **CSV 表头为自定契约**：与他工具互转时以本契约为准
- **`extra` 键冲突**：适配器键加格式前缀（`ttml_` 等）规避
- **引用即句柄的边界**：放下 Item 引用即无法定位（无 id/无 index）；当前与可预见消费者都以迭代为主要读取方式，将来若出现「只有句柄没有引用」的场景再补句柄机制，不与现有语义冲突
