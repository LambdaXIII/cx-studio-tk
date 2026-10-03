# Tasks

## 0. 时间域交叠判定调整（cx-studio）

- [ ] 0.1 `cx_studio/core/cx_timerange.py`：`is_overlapped_with` 改为严格交叠（`start < other.end and other.start < end`，端点相触不视为交叠）；同步修改三处 docstring 的语义表述（模块 docstring、`ITimeRange` 契约 docstring、方法 docstring）；`is_contained_by`/`contains_time` 不动（本节依赖：2.4 的裂变分组调用调整后的判定；cx-studio 域 spec 的折回在 archive 时进行）

## 1. 字幕模型（subtitler/common · model）

- [ ] 1.1 `model/segment.py`：`SubtitleSegment` frozen dataclass（`TimeRange` + text + speaker + extra），`start`/`duration` 派生属性，含 docstring——模型预置字段的唯一载体，扩展位承接格式私货；docstring 声明「已入集片段的时间范围不得改写」（`TimeRange` 可变，frozen 挡不住）
- [ ] 1.2 `model/collection.py`：`SubtitleCollection`——`list` + `bisect.insort` 按 start 维持有序，相等 key 稳定落位，遍历恒时序，无交叠检查——读取路径不出现排序
- [ ] 1.3 `model/work.py`：`SubtitleWork`——集合 ×N 的显式增/取，无隐式合并推断
- [ ] 1.4 `model/__init__.py` 符号导出

## 2. Loader/Saver 契约与 engine（subtitler/common 本体）

- [ ] 2.1 `reader.py` / `saver.py`：`SubtitleReader.parse`、`SubtitleSaver.serialize` 抽象基类 + `allows_overlap`/`time_pattern` 声明 + 七条子类契约写入 docstring；`errors.py`：`FormatError`（带位置信息）
- [ ] 2.2 `timecodec.py`：模式驱动的时间解析/格式化/单调取整——算法统一在框架、模式由声明驱动；自建严格实现（不复用 `CxTime.from_timestamp` 的宽松前缀匹配，边界理由写入 docstring）；精度由模式串末位单位推出
- [ ] 2.3 `engine.py` 导入 `load(path, fmt)`：读字节 → `detect_file_encoding` → 解码 → parse → 单文件单集合，异常忠实保留；探测返回 `None`/解码失败/语法失败均显式抛 `FormatError`
- [ ] 2.4 `engine.py` 导出 `save(collection, target, fmt)`（**单集合入参**）：单调取整 → 按 `allows_overlap` 决定单序列或贪心分组裂变（交叠判定调 `is_overlapped_with`，任务 0.1 已调整语义）→ **写前一次性预检全部目标路径**（已存在则报错零输出）→ serialize → UTF-8 无 BOM 写出 → 返回产出路径列表；`.part<k>` 命名按各组首片段 start 升序

## 3. 三格式实现（subtitler.common.formats）

- [ ] 3.1 `formats/srt.py`：`SrtFormat`（name/extensions/SrtReader/SrtSaver 打包），`allows_overlap=False`，`time_pattern="HH:MM:SS,mmm"`，编号按框架交付顺序写出、多行文本按多文本行读写
- [ ] 3.2 `formats/ttml.py`：`xml.etree` 子集（`<tt><body><div><p begin end>`，时间读入接受 clock 与带单位偏移字面量并在 parse 内归一、写出统一 clock `HH:MM:SS.mmm`），`<br/>` ↔ 换行互逆，样式入 extra（键加 `ttml_` 前缀），`allows_overlap=True`
- [ ] 3.3 `formats/csv.py`：RFC 4180 引号规则（含引号内换行）+ 表头契约 `start,end,text,speaker` + 扩展列，时间列 `time_pattern="HH:MM:SS.mmm"`，`allows_overlap=True`
- [ ] 3.4 `formats/__init__.py` 与 `common/__init__.py` 三层汇聚导出（模型层/语法层/编排层）——能力符号经 `subtitler.common` 一层导出，工具顶不转发（`__version__` 归 4.6）

## 4. CLI 前台（前台装配 + i18n）

- [ ] 4.1 `application.py` / `appenv.py`：`SubtitlerApplication(IApplication)` / `SubtitlerEnv`，banner.txt 启动横幅，`__exit__` 覆盖模式（先 `super().__exit__()`，再捕获 `SafeError` 与 `KeyboardInterrupt`——`IApplication` 基类不捕获，责任在工具子类，镜像 `cx_note/application.py`）；appenv 模块级单例按现有工具惯例
- [ ] 4.2 `appcontext.py`：`SubtitlerContext.from_arguments` 白名单工厂，字段 input/output/debug_mode/show_help/show_full_help，`subtitler INPUT OUTPUT [-d] [-h|--tutorial]`
- [ ] 4.3 `app_help.py`：`SubtitlerHelp(IAppComponent, WealthyHelp)`，模板 hosts_keeper——分组帮助与完整教程
- [ ] 4.4 `components/wiring.py`：显式 dict 登记本工具启用的格式（SRT/TTML/CSV，`from subtitler.common.formats import …`），汇总扩展名表——格式面唯一来源，`subtitler.common` 无注册表；`components/__init__.py` 导出
- [ ] 4.5 `components/converter.py`：转换编排——扩展名查表识别源/目标、调 `subtitler.common.engine` 的 load/save、产出路径列表经 `say()` 呈现（无裂变也报目标路径）、`FormatError`/`IOError` 转 `SafeError` 报错中止
- [ ] 4.6 `__init__.py` 入口 `run()` 标准组装——模块级只留 `__version__` 与 `run()` 定义，app 栈 import（cx_tools/cx_wealthy/argparse）下沉 `run()` 体内（common 复用面不被入口污染）；**共享 `pyproject.toml` 接入**：`[project.scripts]` 注册 `subtitler` 入口，`[tool.hatch.build.targets.wheel]` 的 `packages` 与 `include` 追加 `subtitler` 与 `*/i18n/locales/**/*.mo` 对应项（逐包显式列举，漏了打包不进源码与翻译）——pyproject 修改需用户同意；`subtitler/__init__.py` 定义 `__version__` 并与 pyproject 同步
- [ ] 4.7 `i18n/` 初始化（domain `subtitler`，`_()` 中文 msgid）：`babel.cfg` 追加 `[python: subtitler/**.py] domain = …` 段、`docs/agents/i18n.md` 提取命令清单追加 subtitler 行、按其流程提取/编译 `.po`/`.mo`
- [ ] 4.8 `help.md`（源语言）+ `help.en_US.md`：WealthyHelp 教程文本（转换用法、支持格式、CSV 表头契约、多输出命名）

## 5. 文档归位

- [ ] 5.1 根 `CONTEXT.md`：cxalio-studio-tools 分区收录 `subtitler` 工具（`common/` 承载字幕能力：模型/契约/格式实现、对外提供面、无 CLI 依赖纪律；前台职责、注册接线）；并修正同分区「`SafeError` 由 `Application.__exit__` 捕获」的失实表述——基类 `IApplication.__exit__` 只做 stop/清理不捕获，捕获责任在工具子类的覆盖（ffpretty/media_killer/cx_note 现行模式）
- [ ] 5.2 根 `AGENTS.md`：工具清单、`uv run` 命令示例、i18n domain 表——新增第 7 个工具必然涉及，逐处更新
- [ ] 5.3 `uv run black .` 全仓格式化

## 6. 端到端验证（无测试基础设施，以实际运行为准）

- [ ] 6.1 三格式互转矩阵冒烟：SRT→TTML→CSV→SRT 干净输入往返等价（片段、时间、顺序），用例含**多行台词**与 CSV 引号内换行
- [ ] 6.2 交叠裂变验证：含交叠集合导出 SRT → 多文件 `.part<k>`（按首片段 start 升序）、各序列内不交叠、无丢失、各自从 1 编号；**相邻衔接（端点相触，如 [0,5s]+[5,10s]）不裂**，保持单文件
- [ ] 6.3 异常路径验证：解析失败报错中止无输出、编码探测返回 `None` 报 `FormatError`、目标已存在（含 part 路径预检）零输出不覆盖、未识别扩展名报错
- [ ] 6.4 common 层复用面验证：从另一上下文 `from subtitler.common import …`（模型 + 契约 + engine）与 `from subtitler.common.formats import …` 符号可用，且 import 后 `sys.modules` 无 `cx_tools`/`cx_wealthy`/`argparse`（不引入任何 CLI 依赖）
- [ ] 6.5 `uv run subtitler --help` 与无参/错误参数实际运行，帮助（中/英）、banner、错误呈现正常
