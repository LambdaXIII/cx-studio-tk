# Tasks

## 0. 时间域交叠判定调整（cx-studio）

- [x] 0.1 `cx_studio/core/cx_timerange.py`：`is_overlapped_with` 改为严格交叠（`start < other.end and other.start < end`，端点相触不视为交叠）；同步修改三处 docstring 的语义表述（模块 docstring、`ITimeRange` 契约 docstring、方法 docstring）；`is_contained_by`/`contains_time` 不动（依赖方：1.3 的 Project 路由与 3.1 的 SRT Saver 分组；cx-studio 域 spec 的折回在 archive 时进行）

## 1. 字幕模型（subtitler/common/model）

- [x] 1.1 `model/item.py`：`SubtitleItem` frozen dataclass（`TimeRange` + text + speaker + extra dict），`start`/`duration` 派生属性；docstring 声明——独立存在的普通对象、扩展位键格式前缀约定、模型不解释 extra、frozen 只挡字段重绑（TimeRange 可变，改写时间合法）
- [x] 1.2 `model/sequence.py`：`SubtitleSequence`——内部 `list`；`add(item)`/`add_from(iterable)` 用 `bisect.insort` 按 start 定位（尽力时序，无交叠检查）；迭代/查询恒时序且为活视图（读取路径有序性检查，乱序则排序兜底——Item 时间改写后排列可能陈旧）；`take(item)` 按 `is` 身份匹配摘除返回（未命中 None）；`contains(item)`；无元数据无名称、不暴露 index
- [x] 1.3 `model/project.py`：`SubtitleProject`——`sequences`（创建序，新增 append 尾部）+ `meta` dict；`add(item)` 路由（按创建序 first-fit：逐 Sequence bisect 找位 + 邻位 `is_overlapped_with` 严格交叠检查，无处可容自动新增 Sequence）；`add_from` 逐个走 add；全量迭代为跨 Sequence 归并的时序流（扁平排序实现）；`sequences` 按创建序迭代；`contains`/`take`（定位所属 Sequence 摘除，未命中 None）
- [x] 1.4 `model/__init__.py` 符号导出

## 2. 格式框架（subtitler/common 本体）

- [x] 2.1 `loader.py`：`SubtitleLoader` 抽象基类——`load(path: Path) -> list[SubtitleItem]`，自读文件（`detect_file_encoding` 判定编码，探测 None/解码失败 → `FormatError`）、自解析；`errors.py`：`FormatError`（带位置信息）；子类契约写入 docstring（自主 IO、忠实提取不重排不丢不改、扩展位前缀、对模型容器无知、严格语法）
- [x] 2.2 `saver.py`：`SubtitleSaver` 抽象基类——`save(items, target: Path) -> list[Path]`，自主组织输出（单/多文件与交叠处理是格式自己的事）；子类契约写入 docstring（写前一次性预检全部目标路径、已存在报错零输出不覆盖、UTF-8 无 BOM、多文件 `.part<k>` 按输出顺序、编号字面逐文件从 1 按时序、时间模式为内部常量经 TimeCodec）
- [x] 2.3 `timecodec.py`：模式驱动的时间解析/格式化/单调取整——严格实现，不复用 `CxTime.from_timestamp` 的宽松前缀匹配（边界理由写入 docstring）；精度由模式串末位单位推出
- [x] 2.4 `formats/__init__.py` 与 `common/__init__.py` 汇聚导出（模型层/格式层）——能力符号经 `subtitler.common` 一层导出，工具顶不转发（`__version__` 归 4.6）

## 3. 三格式实现（subtitler/common/formats）

- [x] 3.1 `formats/srt.py`：`SrtFormat`（name/extensions/SrtLoader/SrtSaver 打包）——loader：块解析（序号行忽略）、`HH:MM:SS,mmm` 严格解析、多行文本；saver：按 start 扫描贪心分组（与当前组最晚 end 严格交叠冲突则另起组，组数不求最优）拆文件、每文件编号从 1、多行文本多行写出
- [x] 3.2 `formats/ttml.py`：`xml.etree` 子集（`<tt><body><div><p>`）——loader：clock 与带单位偏移字面量（`10s`/`1.5s`/`100ms`…）归一为 CxTime（底层换算调 TimeCodec）、p → Item、样式等入 extra（`ttml_` 前缀）；saver：单文件交叠照收、`<br/>` ↔ 换行互逆、写出统一 clock；文件头信息无通道不回写（往返等价以 Item 内容为界）
- [x] 3.3 `formats/csv.py`：RFC 4180 引号规则（含引号内换行）+ 表头契约 `start,end,text,speaker` + 扩展列与 extra 键原样互映射（extra 键与保留列同名 → `FormatError`）；空单元格 ↔ `speaker=None` 与 extra 缺键；扩展列集合 = 各 Item extra 键并集；单文件
- [x] 3.4 三格式 loader/saver 各自完整自治（自读自写），无共享编排组件

## 4. CLI 前台（前台装配 + i18n）

- [x] 4.1 `application.py` / `appenv.py`：`SubtitlerApplication(IApplication)` / `SubtitlerEnv`，banner.txt 启动横幅，`__exit__` 覆盖模式（先 `super().__exit__()`，再捕获 `SafeError` 与 `KeyboardInterrupt`——基类不捕获，责任在工具子类，镜像 `cx_note/application.py`）；appenv 模块级单例按现有工具惯例
- [x] 4.2 `appcontext.py`：`SubtitlerContext.from_arguments` 白名单工厂，字段 input/output/debug_mode/show_help/show_full_help，`subtitler INPUT OUTPUT [-d] [-h|--tutorial]`
- [x] 4.3 `app_help.py`：`SubtitlerHelp(IAppComponent, WealthyHelp)`，模板 hosts_keeper——分组帮助与完整教程
- [x] 4.4 `components/wiring.py`：显式 dict 登记本工具启用的格式（SRT/TTML/CSV，`from subtitler.common.formats import …`），汇总扩展名表——格式面唯一来源，`subtitler.common` 无注册表；`components/__init__.py` 导出
- [x] 4.5 `components/converter.py`：扩展名查表识别源/目标 → `Format.loader.load(input)` 得 Items → 逐个 `project.add(item)` → `Format.saver.save(project, output)` → 产出路径列表经 `say()` 呈现（无裂变也报目标路径）；`FormatError`/`OSError` 转 `SafeError` 报错中止
- [x] 4.6 `__init__.py` 入口 `run()` 标准组装——模块级只留 `__version__` 与 `run()` 定义，app 栈 import（cx_tools/cx_wealthy/argparse）下沉 `run()` 体内（common 复用面不被入口污染）；**共享 `pyproject.toml` 接入**：`[project.scripts]` 注册 `subtitler` 入口，`[tool.hatch.build.targets.wheel]` 的 `packages` 与 `include` 追加 `subtitler` 与 `*/i18n/locales/**/*.mo` 对应项（逐包显式列举，漏了打包不进源码与翻译）——pyproject 修改需用户同意；`subtitler/__init__.py` 定义 `__version__` 并与 pyproject 同步
- [x] 4.7 `i18n/` 初始化（domain `subtitler`，`_()` 中文 msgid）：`babel.cfg` 追加 `[python: subtitler/**.py] domain = …` 段、`docs/agents/i18n.md` 提取命令清单追加 subtitler 行、按其流程提取/编译 `.po`/`.mo`
- [x] 4.8 `help.md`（源语言）+ `help.en_US.md`：WealthyHelp 教程文本（转换用法、支持格式、多输出命名、交叠处理行为、CSV 表头契约）

## 5. 文档归位

- [x] 5.1 根 `CONTEXT.md`：cxalio-studio-tools 分区收录 `subtitler` 工具（`common/` 承载字幕能力：模型/Loader/Saver 契约/格式实现、对外提供面、无 CLI 依赖纪律；前台职责、注册接线）；并修正同分区「`SafeError` 由 `Application.__exit__` 捕获」的失实表述——基类 `IApplication.__exit__` 只做 stop/清理不捕获，捕获责任在工具子类的覆盖（ffpretty/media_killer/cx_note 现行模式）
- [x] 5.2 根 `AGENTS.md`：工具清单、`uv run` 命令示例、i18n domain 表——新增第 7 个工具必然涉及，逐处更新
- [x] 5.3 `uv run black .` 全仓格式化

## 6. 端到端验证（无测试基础设施，以实际运行为准）

- [x] 6.1 三格式互转矩阵冒烟：SRT→TTML→CSV→SRT 干净输入往返内容等价（时间/台词/说话人/扩展位），用例含**多行台词**与 CSV 引号内换行
- [x] 6.2 交叠处理验证：交叠 SRT→SRT 产出多个不交叠输出文件（`.part<k>` 按输出顺序、各文件内部不交叠、全部 Item 无丢失、编号各自从 1）；交叠 SRT→TTML 单文件交叠保留；**相邻衔接（端点相触，如 [0,5s]+[5,10s]）不拆**，保持单文件
- [x] 6.3 模型行为验证（临时脚本，放 `temp/`）：乱序批次入 Project 后各 Sequence 内部无交叠；去交叠 = iter 全部 Item 喂新 Project（原 Project 不受影响）；活视图（改写 Item 时间后再迭代反映新时序）；take→add 转移与未命中返回 None
- [x] 6.4 异常路径验证：解析失败报错中止零输出、编码判定失败报 `FormatError`、目标已存在（含 part 路径预检）零输出不覆盖、未识别扩展名报错
- [x] 6.5 common 层复用面验证：从另一上下文 `from subtitler.common import …`（模型 + 契约 + 格式）符号可用，且 import 后 `sys.modules` 无 `cx_tools`/`cx_wealthy`/`argparse`（不引入任何 CLI 依赖）
- [x] 6.6 `uv run subtitler --help` 与无参/错误参数实际运行，帮助（中/英）、banner、错误呈现正常
