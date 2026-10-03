# Design

## Context

动机见 proposal.md（Why）。现状与约束：

- 时间域核心资产 `CxTime`（毫秒级）、`TimeRange`（起止段）已在 `cx_studio.core`，字幕模型建立其上，不新造时间类型
- 现有工具应用层骨架同构（`application.py` / `appenv.py` / `appcontext.py` / `app_help.py` / `help.md` / `i18n/`），`app_help.py` 为标准件（`<Tool>Help(IAppComponent, WealthyHelp)`，模板来自 hosts_keeper）；带 `common/`+`components/` 分层的先例为 cxnote 与 ffpretty（`CONTEXT.md`：不提供 common 的工具不强制区分 common/components）
- 工具内部分层惯例：`common/`（不依赖 appenv 的非耦合能力，工具间 import 只允许指向 `package.common`）/ `components/`（appenv 依赖或工具特化）
- 仓库已有 SPI 先例：media_scout 的 `MediaPathInspector`/`InspectorChain`——探测器在构造时显式注入，无全局注册表
- 本变更无新第三方依赖；仓库无测试基础设施，验证以实际运行为准

## Goals / Non-Goals

**Goals:**

- 字幕能力（模型 + Loader/Saver 契约与 engine + 三格式实现）在 `subtitle` 独立包落地，可被其它工具 import；`subtitler` 只剩纯 CLI 前台
- subtitler CLI 完成 SRT/TTML/CSV 互转的端到端闭环
- 收口 proposal 遗留的开放项：转换公共动作细节、多输出文件命名

**Non-Goals:**

- 字幕内容的编辑、修剪、重排、质检——工具只搬运模型
- 格式发现的高级手段（内容嗅探、`--from/--to` 显式覆盖）——按扩展名查表，等真实场景出现再议
- 模型/框架迁往 `cx-studio` 独立子包——按「能力包 `subtitle` 就地开放」的讨论定案执行
- 测试基础设施搭建（仓库无测试基建，不在本变更内引入）

## Decisions

### D1. 包结构：能力包 + 纯前台，两级切分

```
packages/cxalio-studio-tools/
├── subtitle/                  # 字幕能力包：模型 + Loader/Saver 定义 + 格式实现
│   ├── __init__.py            # 三层汇聚导出（模型/语法/编排）
│   ├── model/
│   │   ├── segment.py         # SubtitleSegment = TimeRange + text + speaker + extra
│   │   ├── collection.py      # 片段集合（按 start 插入维持有序）
│   │   └── work.py            # 作品 = 集合 ×N
│   ├── reader.py              # SubtitleReader 抽象基类（Loader 契约）
│   ├── saver.py               # SubtitleSaver 抽象基类（Saver 契约，含约束声明）
│   ├── timecodec.py           # TimeCodec：时间解析/格式化/单调取整
│   ├── errors.py              # FormatError
│   ├── engine.py              # load / save：IO、编码、裂变、取整、命名
│   └── formats/               # 具体格式实现（SRT / TTML / CSV）
│       ├── srt.py             # Format 对象 + SrtReader/SrtSaver
│       ├── ttml.py
│       └── csv.py
└── subtitler/                 # 纯 CLI 前台：只装配，不承载能力
    ├── __init__.py            # run()：组装入口
    ├── application.py         # SubtitlerApplication(IApplication)
    ├── appenv.py              # SubtitlerEnv(IAppEnvironment)
    ├── appcontext.py           # SubtitlerContext(IAppContext)
    ├── app_help.py            # SubtitlerHelp(IAppComponent, WealthyHelp)
    ├── help.md                # WealthyHelp 教程文本（源语言，load_localized_text 加载）
    ├── help.en_US.md          # 英文帮助（镜像多数现有工具）
    ├── banner.txt             # 启动 banner（镜像 cxnote/hosts_keeper/media_killer）
    ├── i18n/                  # 本工具 gettext（domain: subtitler）
    └── components/
        ├── wiring.py          # 本工具格式面（显式 dict 登记，扩展名表唯一来源）
        └── converter.py       # 转换编排（IAppComponent：say/whisper、错误呈现）
```

依据：按**能力**切包而非按工具内角色切目录——`model/formats/adapters` 是一个能力的三个角色，拆成工具内三目录等于在工具里造小项目（角色目录不构成功能包）；正确边界是「字幕能力」（`subtitle`：集合模型 + Loader/Saver 契约 + engine + 格式实现）与「字幕工具前台」（`subtitler`：装配与交互）。能力包落位 `cxalio-studio-tools` 内的 import 包（随 `cx_tools` 先例：消费方在本 workspace 内，不值当新开 workspace 包；不进 `cx-studio`——字幕领域模型不是通用基础设施）。`subtitler` 无 `common/`：能力全部外置于 `subtitle`，前台只剩 `components/`（appenv 依赖的接线与编排）。

### D2. 模型实现：组合非继承，集合用 `list` + `bisect`

- `SubtitleSegment`：`frozen dataclass`，持有 `TimeRange`、`text: str`、`speaker: str | None`、`extra: dict[str, Any]`。`start`/`duration` 为 `TimeRange` 的派生视图属性，不独立存储。注意 `TimeRange` 本身可变（带 setter）——frozen 只挡字段重绑：**已入集片段的时间范围 MUST NOT 再改写**（集合有序性以插入时刻确立，改写已入集片段的时间属调用方违约、行为未定义）；此约束写入 `SubtitleSegment` 与 `SubtitleCollection` 的 docstring
- `SubtitleCollection`：内部 `list` + `bisect.insort`（按 `range.start`）。查找 O(log n)、搬移 O(n)——字幕量级千行、插入低频，不引入树结构或第三方依赖
- 稳定落位：`bisect` 对相等 key 取右侧插入点，新片段落既有相等元素之后，无需自实现 tie-breaker
- 交叠不做任何检查；「读取恒为时序」由插入方式保证，读取路径上无排序步骤
- `SubtitleWork`：`list[SubtitleCollection]`，仅提供显式增/取，不提供跨集合合并或推断

**替代方案**：无序存储 + 读取排序——被否决（顺序是模型本质属性，租来的顺序每次读取都要付成本，且视图与可变容器的一致性无法保证）。

### D3. Reader/Saver 基类与子类契约

**拆分为两个基类而非单个双向适配器**：讨论定案的方向不对称——导入恒 1:1，导出才有 1..N 裂变。导出侧的约束声明（是否允许交叠、时间精度）只对导出生效，读侧永不裂变、不重编；拆开后声明长在它生效的方向上。附带收益：将来只读/只写格式无需实现用不到的半边。

```python
class SubtitleReader(ABC):
    """语法读向：一个序列的文本 → 片段表。"""
    @abstractmethod
    def parse(self, text: str) -> list[SubtitleSegment]: ...

class SubtitleSaver(ABC):
    """语法写向：一个序列的片段表 → 文本。"""
    allows_overlap: ClassVar[bool]   # 交叠约束声明（执行在 engine）
    time_pattern: ClassVar[str]      # 时间模式声明（如 "HH:MM:SS,mmm"）

    @abstractmethod
    def serialize(self, segments: Sequence[SubtitleSegment]) -> str: ...

@dataclass(frozen=True)
class Format:
    """格式身份：名称 + 所认扩展名 + 双向实现。"""
    name: str
    extensions: tuple[str, ...]
    reader: SubtitleReader
    saver: SubtitleSaver
```

**`TimeCodec`（框架提供）**：时间解析、格式化、单调取整的算法统一在框架，模式由适配器声明——落实 spec「换算由框架执行、适配器声明表示方式」。**与 `CxTime` 既有方法的边界**：`CxTime.to_timestamp/from_timestamp` 是宽松的前缀匹配解析（`[:;.,]` 分隔符混用、末段不按三位补零换算），语义与格式契约所需的严格模式解析不同——TimeCodec **不复用也不包装**这两个方法，自建模式驱动的严格实现，`CxTime` 仅作为毫秒值载体。`time_pattern` 是**写出模式串**，精度由末位单位推出（`mmm` → 毫秒）；**读入形式的识别归适配器**——TTML 的 clock 与带单位偏移（`10s`、`1.5s`、`100ms` 等字面量）两种接受形式由 TTML reader 在 `parse` 内归一为 `CxTime`（底层换算调 TimeCodec），写出只用 clock。engine 在调 `serialize` 前按精度对全片段做单调取整（单调函数不产生逆序，保证换算不颠倒时序）。

**子类继承契约**（写入基类 docstring）：

1. 不依赖 appenv/context/前台组件——`subtitle` 包不得依赖 `subtitler` 或任何 CLI 组件
2. `parse`/`serialize` 为纯函数：同输入同输出，不做 IO（开文件、编码探测归 engine）
3. `parse` 输出按时序排列、忠实保留交叠；语法错误抛 `FormatError`（带位置信息），禁止静默跳过或部分返回
4. `serialize` 的输入由 engine 保证：已排序、已按精度预舍入、`allows_overlap=False` 时已分组无交叠——saver 不再检查、不排序、不分组
5. 序号是序列侧语法，编号语义归框架（每序列独立从 1、按时序、不沿用来源）：框架分组交付后，`serialize` 按交付顺序写出编号字面（SRT 等有编号格式）
6. 扩展位键必须带格式前缀（如 `ttml_style`），读写对称，避免与未来预置字段撞名
7. 格式实现以 `Format` 对象打包——identity 集中一处，engine 与前台都以它为参数

### D4. 三格式的规范依据与实现范围

|格式|依据|实现范围|约束声明|
|---|---|---|---|
|SRT|SubRip 事实标准（**无正式规范**；「不许交叠」是本工具采用的约定）：序号行、`HH:MM:SS,mmm --> HH:MM:SS,mmm`、文本行、空行分隔|完整|`allows_overlap=False`|
|TTML|W3C TTML1 / IMSC 文本子集|`<tt><body><div><p begin end>`；时间读入接受 clock 与带单位偏移字面量（`10s`/`1.5s`/`100ms`…），写出统一 clock（`HH:MM:SS.mmm`）；样式等非预置字段入 extra|`allows_overlap=True`|
|CSV|RFC 4180 引号规则 + 本工具自定表头契约（`start,end,text,speaker` + 扩展列；字幕 CSV 无标准，以本契约为准）；时间列 `time_pattern="HH:MM:SS.mmm"`（毫秒）|完整|`allows_overlap=True`|

XML 解析用标准库 `xml.etree.ElementTree`（不引入 `lxml`）。

**多行文本的跨格式表示**（往返对称的前提）：模型 `text` 持真实换行（`\n`）——SRT 直接按多文本行写出/读入；TTML 以 `<br/>` 表达行分隔（读写互逆）；CSV 以 RFC 4180 引号内换行表达。三格式两两互转保持换行等价。

### D5. engine 语义与 IO

- **导入** `load(path, Format) -> SubtitleCollection`：读字节 → `cx_studio.filesystem.detect_file_encoding`（按路径缓存）→ 解码 → `reader.parse` → 单文件单集合。多文件导入 = 多次 `load` 由调用方组装，框架不合并；编码探测返回 `None`（无法判定，如空文件）或解码失败、语法错误，均显式抛 `FormatError`（不得让 `bytes.decode(None)` 之类裸 `TypeError` 冒泡），不做编码猜测兜底
- **导出** `save(collection, target, Format) -> list[Path]`——**单集合入参**（多集合由调用方逐集合调用，各自给目标；避免复数入参与单目标命名规则的歧义）：
  1. 按 `time_pattern` 精度单调取整全部片段
  2. `allows_overlap=False` 时贪心分组（按 start 扫描，片段与当前组内最晚 end 冲突则另起一组）——保证各组不交叠、无丢失；组数不求最优（区间图着色无必要）；`.part<k>` 序号按贪心产生顺序 = 各组首片段 start 升序
  3. **写前一次性预检**全部目标路径（原名或派生 `.part<k>` 清单）：任一已存在 → 报错中止、零输出（杜绝写完 part1 才发现 part2 被占的半套输出）
  4. 每组 `serialize` → UTF-8（无 BOM）写出
- **多输出命名**（导出语义的一部分，放 engine 而非前台——任何调 `save` 的外部工具都面临同一问题）：目标 `out.srt` 无交叠时原名；裂变 N>1 时 `out.part1.srt`、`out.part2.srt`…（stem 后缀 `.part<k>`，从 1 起，不补零）。目录与扩展名跟随目标路径
- **序号重编**：编号语义（每序列独立从 1、按时序）由框架保证——模型不存序号，框架按分组独立交付；SRT `serialize` 按交付顺序写出编号字面，裂变后各文件各自独立

### D6. CLI 接口

单动作工具，无动词表（cxnote 的 VERBS 是多动作模式，此处不适用）：

```
subtitler INPUT OUTPUT [-d] [-h | --tutorial]
```

- `SubtitlerContext` 按 `from_arguments()` 白名单工厂模式构造；字段：`input`、`output`、`debug_mode`、`show_help`、`show_full_help`
- 格式识别：按输入/输出文件扩展名查 wiring 的表；未识别 → 报错中止（不做内容嗅探：SRT 纯文本无可靠特征头）
- 转换为瞬时文件操作，不设 progress；输出走 `say()`（stderr）——`save` 返回的产出路径列表 MUST 经 `say()` 呈现（无裂变也报目标路径）；`SafeError` 由 **`SubtitlerApplication.__exit__`**（工具子类覆盖）捕获呈现并连同 `KeyboardInterrupt` 一并处理——`IApplication.__exit__` 基类只做 stop/清理、不捕获，责任在工具子类（镜像 `cx_note/application.py` 的覆盖模式）

### D7. 前台接线（无全局注册表）

`components/wiring.py` 显式 dict 登记本工具启用的格式并汇总扩展名表——格式面唯一来源。**不在 `subtitle` 包设全局注册表**：仓库 SPI 先例 `InspectorChain` 是构造时显式注入；讨论定案「注册机制绑定 CLI」。`subtitle` 包只提供 `Format` 对象，不含登记动作；无隐藏状态、可测、换一个前台可接不同格式子集。

### D8. 依赖清单

**仓库内能力复用**：

|来源|能力|
|---|---|
|`cx_studio.core`|`CxTime`、`TimeRange`（时间原语）|
|`cx_studio.filesystem`|`detect_file_encoding`（编码探测）|
|`cx_studio.i18n`|`load_localized_text`（帮助文本按 locale 加载）|
|`cx_tools.app`|`IApplication`/`IAppEnvironment`/`IAppContext`/`IAppComponent`、`SafeError`|
|`cx_wealthy`|`WealthyHelp`（帮助 DSL）、`rich_types`、theme|

**外部依赖：零新增**。候选逐一评估否决：`lxml`（`xml.etree` 对 TTML 子集足够）、`pysrt`/`srt`（买轮子等于放弃自己的模型，本变更目的就是建模型）、`sortedcontainers`（千行量级 `bisect` 足够）、独立编码探测库（复用 `detect_file_encoding`）。

### D9. `subtitle` 包公开接口与外部使用路径

包顶 `__init__.py` 三层汇聚导出：

- **模型层**（程序化构建/遍历）：`SubtitleSegment`、`SubtitleCollection`、`SubtitleWork`
- **语法层**（格式身份与双向实现）：`Format`、`SubtitleReader`、`SubtitleSaver`、`FormatError`、`SrtFormat`/`TtmlFormat`/`CsvFormat`（实现于 `subtitle.formats`）
- **编排层**：`engine.load`、`engine.save`

预期三种外部用法，各有直通路径：**转换**（`load → save` 两行）、**消费**（`load` 后只读遍历，供将来 QC/统计工具）、**生成**（代码构建集合 → `save`，供将来烧字幕/报表工具）。

## Risks / Trade-offs

- **TTML 子集**：TTML 规范庞大（区域、样式、帧率时基），按「能表达时间+文本+说话人的子集」实现；超出子集的结构元素不建模，复杂 TTML 降级保时间文本、样式入 extra——模型扩展位兜底
- **裂变贪心分组的最优性**：贪心产出的序列数不保证最少，但保证合法（各组不交叠、无丢失）；最少分组是区间图着色，无必要
- **CSV 表头为自定契约**：与他工具互转时以本契约为准
- **`extra` 键冲突**：适配器键加格式前缀（`ttml_` 等）规避
