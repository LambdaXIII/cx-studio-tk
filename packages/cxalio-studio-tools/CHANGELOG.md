# Change Log of Cxalio Studio Tools


### [最新修改]

#### cxnote 快速笔记工具（新增）

- **新包 `cx_note`**（第 6 个工具，`__version__` 初始 1.0.0）：终端快速便签——条目 = 内容 + 三态（待办/正在做/已完成）+ 日期，归属「域」字面命名空间（ADR-0009），4 位小写 base36 ID 全局唯一终身不变
- **动词**：`add`（字面 `\n` 转真实换行）/ `list`（缺省；按域分组、当前域在前）/ `done` / `doing` / `reset` / `clear`（ID 精确匹配全库、文本子串匹配可见域）/ `clean`（显式清理超龄已完成条目）/ `config`（读写保留天数，缺省 30，≤0 禁用自动清理）
- **域解析**（`cx_note/common/domain.py` 纯函数）：HOME 下取相对字面、HOME 即根域、HOME 外取去盘符绝对字面；身份键大小写不敏感、首见字面保留；段边界包含判定（`/生活琐事2` 不被 `/生活琐事` 覆盖）
- **存储**：`~/.config/cx-studio/CxNote/notes.json` 单文件；原子重写（tmp + os.replace）；损坏时报 SafeError 不静默清空；变更类动词后自动清理当前域超龄条目
- **展示语义**（列表展示重设计）：默认折叠——当前域条目全显、下级域仅标题行 + `(条目数)`；`--full` 展开下级域条目；当前域标题只显示域名字（末段），根域显示 `GLOBAL`，子域标题相对当前域显示
- **渲染**（列表展示重设计，ADR-0010）：平铺域块——域标题行（`cx.note.section`）外置 + 每域独立无框三列小 Table（标号自然宽 / 内容 ratio=1、含换行按 Markdown 渲染 / ID 徽章 width=4 右对齐贴行尾），块间空行分隔；`cx.note.*` 样式经 push_theme 叠加。初版整表分节行断行割裂回退逐行、`█` 树状符号与徽章灰底均在本批验收返工中废弃
- **ID 徽章**（列表展示重设计）：无底色，8 色高对比亮色池（bright_* + orange1）逐字符值定色（同字符同色）；已完成条目徽章随行 dim
- **`--json`**：全动词 stdout 纯净 JSON（内置 print 防 Rich 折行），提示与错误一律 stderr、exit 0；列表默认仅当前域条目数组，`--full` 扩为当前域 + 全部下级域扁平数组（顺序与人读一致）
- **i18n**：domain `cx-note`，24 条消息接入 gettext，en_US 翻译与 `.mo` 编译完成
- **注册**：`pyproject.toml` scripts/wheel packages/mo include、`babel.cfg` 提取域；CONTEXT.md 词汇与 ADR-0009 随本批入库

### 1.0.0

#### 正式版发布

- **版本统一**：cx_tools 与全部 5 个工具（media_scout / media_killer / jpegger / ffpretty / hosts_keeper）的 `__version__`、发布单元 pyproject 同步跳至 1.0.0，作为首个稳定发布版本号；对 `cx-studio`、`cx-wealthy` 的依赖下限同步升到 `>=1.0.0`


### 0.99.0.1

#### HostsKeeper Windows 提权链路修复（回归）

- **根因**：`_elevated_replace_windows` 的 PowerShell UAC 命令将含单引号的脚本字符串嵌套进外层单引号，PowerShell 把 base64 内容当作 `Start-Process` 的位置参数、参数绑定失败（退出码 1）——**UAC 对话框从未弹出**；此前先尝试的 `sudo copy /Y` 分支同样必败（`copy` 为 cmd 内建命令，sudo 以 CreateProcess 执行找不到可执行文件，退出码 9009，终端曾报"找不到命令"）。两路提权全灭后 `save()` 回退打印 hosts 内容，表现为"不提示鉴权、直接打印 hosts"
- **修复**：删除 `sudo` 分支（历史教训：Windows 原生 sudo 无法执行 cmd 内建命令，PowerShell UAC 为唯一提权路径）；UAC 命令改回 `-EncodedCommand` 整体 base64 编码传递（路径空格/引号不再破坏命令行），超时放宽至 120s，失败时 whisper 输出退出码与 stderr
- **回归源**：7/31 `c601b77` 架构重构重写提权函数时引入（此前 7/17 `6c3dec1` 修复"找不到命令"后的正确实现被替换）
- **debug 分流可观测性**：`save()` 与三个平台提权函数补齐 whisper 诊断——目标路径/pretending 状态、`is_system_hosts` 判断、备份结果、`is_user_admin()` 结果、提权各分支尝试/成功/失败原因，`-d` 模式可完整追踪保存流程走向
- **i18n**：新增 28 条诊断消息接入 gettext（en_US 翻译完成），`.mo` 已重新编译


### 0.99.0

- **版本统一**：cx_tools 与全部 5 个工具的 `__version__`、发布单元 pyproject 同步为 0.99.0，消除历史迭代造成的版本号分叉（此前 cx_tools 0.8.8 与 pyproject 0.9.4 不一致）；此后按根 AGENTS.md 版本管理规则规范迭代
- **依赖版本机制**：对 `cx-studio`、`cx-wealthy` 的依赖由不限版本改为 `>=0.99.0` 下限约束，与发布版本对齐


#### 架构重构：能力归位 + 命名空间即契约

- **执行核心归位 ffpretty**：Mission/Executor/Pretender/Whisperer/MediaInfo/MediaProber/MediaDB 七个模块从 `media_killer.media` 迁入 `ffpretty/common/`（对外提供面）；media_killer 作为组合者从 `ffpretty.common` 消费，`media_killer/media/` 目录消失
- **media_killer.common 落位**：MissionHQ/ExecutorFactory/ExecutorScheduler/TaskProgress/TotalProgress 五个调度层模块迁入 `media_killer/common/`
- **media_scout.common 落位**：inspectors 八个模块迁入 `media_scout/common/inspectors`；消费方改走 `media_scout.common.inspectors` 出口（含 media_killer 深导入）
- **五工具命名统一**：`AppEnv`/`AppContext` → `<Tool>Env`/`<Tool>Context`（FFPrettyEnv/HostsKeeperEnv/JpeggerEnv/MediaKillerEnv/MediaScoutEnv）；jpegger `simple_application.py`/`simple_appcontext.py` 按四件套拆分（application/appcontext/app_help）；media_scout `arg_parser.py` 拆分为 appcontext/app_help
- **MediaDB 共享缓存空间**：`db_path` 允许 None，默认 `~/.config/cx-studio/shared/media_info.db`（工具无关共享缓存）；ffpretty 删除借名 `ConfigManager("MediaKiller")`；media_killer 私有 ConfigManager 保留（last_missions 持久化，支撑 -c/--continue）
- **ffpretty 补齐 i18n**：新建 `ffpretty/i18n/`（domain `ffpretty`，babel/pyproject 配置就位）；迁入模块与既有代码全部接入 `ffpretty.i18n`；翻译条目从 media-killer catalog 物理迁移，新 msgid 补齐英文译文
- **rich_types 出口兑现**：工具层与 cx_tools 的绕路 `from rich.*` 导入迁移至 `cx_wealthy.rich_types`（`rich.traceback.install` 入口与 RegexHighlighter 保留直导）；`__exit__` 修正——ffpretty 删除 `exc_type is None: pass` 空分支，media_killer 的 SafeError 精确比较改为 issubclass
- **开放库清理对齐**：sync FFmpeg/ff_errors/get_root/render_tutorial/progress_task_agent 删除（含 README/AGENTS 文档对齐）；TimeRange duration/end getter 语义修复；FileInfoCache 纳入 `cx_studio.filesystem` 导出；AGENTS.md 新增 common/components 分层规范与组合面契约（工具间 import 只允许指向 `package.common`）


#### HostsKeeper update 行为重定义（排序/查重/异常可见性）

- **优先级排序落地**：update 构建时启用的 profiles 按 `priority` 降序输出（此前未实现，help 声称与实际不符）；相同优先级保持配置文件发现顺序（stable sort，不引入 tie-break）
- **冲突查重（first match wins）**：与平台 hosts 解析行为一致（Linux/Windows 均以首个匹配生效）——用户自定义内容最先输出且域名受保护（绝不覆盖）；profile 之间及同一 profile 内多内容源撞域名时，后出现者以 `# ` 注释保留在自身块内；注释行是生成产物，冲突消失后（如禁用高优先级 profile）下一次 update 自动恢复为有效行
- **查重键提取**：按域名且大小写不敏感；独立实现，避开 `HostRecord.from_line` 对行内注释（`1.2.3.4 example.com # foo`）的解析缺陷
- **L1 结构异常检测与汇报**：反推时检测不配对标记（有 START 无 END / 有 END 无 START）→ 报告 hosts 结构异常并提示手动检查；标记块对应 profile 未注册（已删除/改名）→ 报告残留标记块已清除。仅汇报不自动修复——识别与清除行为不变
- **debug 模式输出生成内容全文**：补齐 help 声称但缺失的行为——`-d` 时 temp 文件生成后 whisper 输出全文（stderr），`-p` 维持 stdout 输出，两者可同时使用
- **help.md / help.en_US.md 重写**：新增「标记契约」章节（`##### <id> START/END #####` 保留格式、块内领地整体覆盖、装饰分区警示）；「优先级机制」替换自相矛盾的旧表述（"后出现者覆盖前者" → 先出现者生效 + 注释保留）
- **i18n**：新报告消息接入 gettext（en_US 翻译完成）；顺带修正既有错误翻译（"已处理配置文件" 误译为 "Profile created"）


#### 统一 Mission 失败反馈链路

- **`MissionFailureInfo` 升级为统一失败数据包**：任何导致 Mission 未正常完成的失败（FFmpeg 执行失败、校验失败、提交失败、executor 外部逃逸异常）均通过它反馈；新增 `ffmpeg: FfmpegErrorInfo | None` 嵌套详情字段（keyword-only），`exception` 改为可选，`stage` 扩展为三值（`factory`/`execution`/`post-execution`）
- **新增 `is_ffmpeg_failure` 属性**：以 `exit_code` 非零判定 FFmpeg 真失败——校验/提交失败（exit_code 为 None/0）不再被误判为「FFmpeg 异常退出」
- **`__rich_detail__` 重构为「头行 + 详情」两层**：所有 execution 失败先展示 `failure_reason`（为什么失败），仅 FFmpeg 真失败才补 FFmpeg 调用详情；校验失败不再显示孤立的 FFmpeg 路径噪音行
- **`MissionHQ._report_failure()` 统一报告入口**：收敛 `_run_one` 中两段平行报告代码（FFmpeg 面板 + 异常面板），统一标题判定（「FFmpeg 异常退出」/「任务失败」）+ 面板渲染 + `MISSION_RESULT(FAILED)` 事件发射
- **executor 全 FAILED 路径统一 whisper**：`execute()` 的 4 个失败返回路径（校验/FFmpeg/提交/兜底）统一 `emit(WHISPERED, failure_reason)`，debug 时间线可看到高层失败原因
- **ffpretty `MissionRunner` 接入统一失败模型**：`_last_error_info`/`make_error_info()` 替换为 `_failure_info`/`failure_info` 属性；`run()` 新增 try/except/finally 包裹全生命周期——修复 `_wire` 失败时 executor 泄漏，逃逸异常构建 `MissionFailureInfo(stage="factory"/"post-execution")`
- **ffpretty 失败面板统一**：FAILED 分支从 `error_tail` 守卫 + `FfmpegErrorInfo` 面板改为 `failure_info` + 动态标题；移除守卫后校验失败等无 stderr 场景也能看到失败原因
- **`FfmpegErrorInfo` 保持为纯详情数据类**：作为 `MissionFailureInfo.ffmpeg` 的嵌套详情，字段与渲染不变


#### IAppComponent 存储重构 & 类型修复

- **IAppComponent 不再存储 appenv/context**：删除 `_appenv`/`_context` 私有属性和 `appenv`/`context` property，`__init__` 参数变更为 optional，仅作签名契约提示
- **IApplication 直接存储**：IApplication 的 `__init__` 直接赋值 `self.appenv = appenv; self.context = context`，子类在 `super().__init__()` 后通过 `self.context = context` 收窄为具体子类类型
- **14 个框架子类全量适配**：5 个 Application 子类（FFPrettyApp/MediaKillerApp/HostsKeeperApp/JpeggerApp/MediaScoutApp）和 9 个 IAppComponent 子类（Help 组件 + HostsBuilder/HostsSaver/ProfileManager/MissionRunner）各自在 `__init__` 中按需存储 appenv/context，不再依赖基类 property
- **app_description 从 AppEnv 移除**：media_killer 和 hosts_keeper 的 AppEnv 删除 `app_description` 字段；media_killer 的使用处改为 `_()` 包装的 i18n 字符串
- **AGENTS.md 更新**：补充"为什么 IAppComponent 不存储 appenv/context"设计说明

#### 应用架构重构：依赖注入化

- **新增 `IAppContext` 抽象基类**（`cx_tools/app/iappcontext.py`）：统一所有工具的 AppContext 契约——持有参数解析结果 + 运行时状态（temp_dir 惰性能力），实现上下文管理器协议（`__enter__`/`__exit__` + `start()`/`stop()`）
- **`IApplication` 签名重构**：从 `(arguments)` 改为 `(appenv, context)`——Application 不再绑定全局 appenv 单例，通过构造参数注入依赖，可被其他工具复用
- **`IAppEnvironment` 增强**：新增 `set_debug_mode()`（debug 状态注入）；`say()`/`whisper()` 恢复为纯输出，Progress 协调逻辑回归各工具 AppEnv 子类覆盖
- **appenv 上下文改为在 Application 外部管理**：工具入口 `with appenv:` 嵌套 `with Application(...)`，appenv 生命周期与 Application 解耦
- **5 个工具全量迁移**：hosts_keeper、ffpretty、media_scout、jpegger、media_killer 的 Application 和子组件改为构造注入，不再 `from .appenv import appenv`
- **ffpretty 新增 `AppContext`**：参数解析从 Application._parse_arguments() 迁移到独立的 AppContext.from_arguments()
- **appenv 瘦身**：各工具 AppEnv 移除业务状态（context、config_manager、media_db、temp_dir 等），仅保留环境能力（console/say/whisper/中断/banner/progress）
- **已知例外**：hosts_keeper `hosts_saver.py` 中 CrossRunner 模块级函数保留全局 appenv 导入（装饰器注册机制要求）

#### 修复

- 修复 Progress Live 显示被 say/whisper override 永久杀死的问题（ffpretty、hosts_keeper、media_killer）
- 修复 media_scout SIGINT handler 挂在死实例上导致 Ctrl+C 无响应
- 修复 media_killer asyncio.run() 覆盖 SIGINT handler 导致 Ctrl+C 无响应
- 修复 hosts_keeper 注册 SIGINT handler 但同步代码不轮询事件导致 Ctrl+C 无响应
- 修复 IApplication.__enter__/__exit__ 缺异常安全导致 context 资源泄漏
- 修复 media_killer garbage 清理计数永远显示 0
- 修复 hosts_saver subprocess.TimeoutExpired 未捕获
- 修复 hosts_builder prepare_custom_lines 静默丢弃用户注释行
- 修复 AbstractContenter appenv 参数泄漏进 package 数据
- 修复 ffpretty SafeError 移出 with 块后无法捕获
- 修复 jpegger SimpleAppContext _temp_dir 泄漏到富文本显示
- 引入 IAppComponent 抽象基类，统一 CLI 特化组件的 appenv+context 持有模式
- 提取 run_async() 共享函数，避免 asyncio.run() 覆盖 SIGINT handler

### v0.9.3

- **适配 cx-studio 0.10.0**：所有 import 路径更新——`collectiontools` → `core`（`flatten_list`/`iter_with_separator`）、`tui` → `clikit`（`DoubleTrigger`/`FIRST_TRIGGERED`/`SECOND_TRIGGERED`）
- **删除弃用代码**：`cx_tools/filesize_counter.py`

### v0.9.2

- **MediaKiller 迭代至 0.9.2**：Mission 数据模型重构——options 从扁平字符串列表改为结构化键值对
- **新增 `FfmpegOption` 数据类**（`media_killer.media`）：frozen dataclass，表示 FFmpeg 选项的 key-value 对，支持 flag（value=None）和键值（如 `-vf scale=1280:720`）
- **新增 `options_from_flat()` / `iter_option_tokens()`**：扁平 token 列表与键值对序列的双向转换，替代旧的 `str.split()` 往返解析
- **`InputSpec.options` / `OutputSpec.options` / `Mission.options`** 字段类型从 `list[str]` 改为 `tuple[FfmpegOption, ...]`
- **`MissionStore` XML 格式重构**：options 从空格拼接文本改为结构化 `<option key="..." value="..."/>` 子元素，无需文本解析
- **新增 `cx_studio.text.cx_shell_escape`** 模块：`escape_arg()` / `join_args()` 平台 shell 转义公用设施，支持 Windows Batch 和 POSIX Shell
- **`ScriptMaker` 引用公用设施**：删除自有的 `_escape_arg`，改用 `cx_shell_escape.join_args()` + `iter_option_tokens()`
- **`PresetTagReplacer.read_value_as_list()`** 返回类型改为 `tuple[FfmpegOption, ...]`，列表分支不再按空格二次拆分
- **MediaKiller 进度条精度优化**：MissionHQ 时长缓存键从 `executor_id`（int）重构为 `Mission` 对象；`_duration_for` 新增 MediaDB 惰性探测回退（排队任务不再使用 1.0 兜底）；消除 Pretend 模式下 `_build_pretender` 与 `_duration_for` 的双重 MediaDB 查询
- **ffpretty `MissionMaker` 适配**：通过 `options_from_flat()` 将原始 CLI 参数转为键值对


### v0.9.0

- **新增 `FfmpegErrorInfo` 数据类**：实现 `__rich_detail__` 协议，结构化封装 FFmpeg 异常退出信息（可执行路径、调用参数、退出码、错误文本、失败原因），供 `WealthyDetailPanel` 渲染
- **ffpretty 错误展示重构**：临时 `r.Panel` + 字符串转义方案替换为 `WealthyDetailPanel(FfmpegErrorInfo, ...)`，`[...]` 不再被 Rich markup 吞掉，错误信息使用 `cx.error` 样式
- **media_killer whisper FfmpegErrorInfo**：任务失败时（debug 模式）通过 `WealthyDetailPanel` 展示结构化错误卡片
- **ffpretty Whisperer 挂接**：`MissionRunner` 挂接 `Whisperer`，executor 内部的 WHISPERED 事件转发至 `IAppEnvironment.whisper()`，与 media_killer 行为对齐
- **`ExecutorStatus` 新增 `ffmpeg_executable` 字段**：status 快照中暴露 FFmpeg 可执行文件路径
- **`MissionExecutor.make_error_info()`**：新增方法，从内部状态构造 `FfmpegErrorInfo`，无副作用
- **HostsKeeper Windows 提权替换修复**：移除 `_elevated_replace_windows` 中的 `sudo` 分支。原 `sudo cp -f` 在提权后的 Windows 环境中因 PATH 不含 `cp` 而报“找不到命令”并把错误泄漏到终端；改用 `sudo cmd /c copy` 又会因 Windows sudo 的窗口模式弹出新控制台窗口。现仅保留 PowerShell UAC 单一提权路径（`Start-Process powershell.exe -Verb RunAs -Wait` 执行 `Copy-Item`），已提权运行时由 `is_user_admin()` 短路直接复制，不受影响

### v0.8.7

- **事件命名规范统一**：
  - 所有 `DoubleTrigger` 订阅方（`iappenv.py`/`ffpretty/appenv.py`/`mission_hq.py`）改用 `FIRST_TRIGGERED`/`SECOND_TRIGGERED` 常量
  - `ffpretty/transcoder.py` 的 FFmpeg 事件订阅（`"started"`/`"finished"`/`"status_updated"`/`"terminated"`）改用 `FFMPEG_EVENT_*` 常量
  - `MissionHQ` 内部 `self.emit()`（`"finished"`/`"mission_started"`/`"mission_result"`）改用已定义的 `MISSION_*` 常量
  - `ExecutorFactory` 的 HQ 桥接发射改用 `MISSION_FILE_LOGGED` 常量
  - `media/__init__.py` 移除全部事件常量 re-export（`CANCELED`/`FAILED`/`FILE_LOGGED`/`FINISHED`/`PROGRESS_UPDATED`/`SAID`/`SKIPPED`/`STARTED`/`STATUS_UPDATED`/`WHISPERED`）
  - `executor.py` 同步更新 `FFMPEG_EVENT_VERBOSE` → `FFMPEG_EVENT_VERBOSE_UPDATED`
- **Abort 提前截断**：`MissionHQ._run_one()` 入口新增 `self._scheduler.is_aborted` 检查，abort 后所有 pending_tasks 直接返回 `CANCELED`，不创建 executor 对象、不等待 semaphore


### v0.8.6

- FFpretty 迭代至 0.8.6，MediaScout 迭代至 0.8.6
- **依赖迁移**：ffpretty 和 media_scout 的 TUI 依赖从 `cx-wealth` 迁移至 `cx-wealthy`（`WealthHelp`→`WealthyHelp`、`WealthLabel`→`RichLabel`、`WealthDetailPanel`/`WealthDetailTable`/`IndexedListPanel` 导入路径更新）
- **API 适配**：`HelpGroup.add_action` 的 `description=` 参数更名为 `detail=`（media_scout/arg_parser.py 中 10 处适配）
- **样式统一**：硬编码颜色样式（`red`/`yellow`/`green`/`blue`/`bright_black`/`cyan`/`dim`/`green1`）替换为 `cx_wealthy` 主题语义样式（`cx.error`/`cx.warning`/`cx.success`/`cx.info`/`cx.debug`/`cx.number`/`cx.whisper`/`cx.argument`/`cx.filepath`），颜色选择委托给主题

### v0.8.5

- HostsKeeper 迭代至 0.8.5
- **帮助系统重构**：`app_help.py` 从扁平参数结构迁移至 `CommandGroup`，usage 行正确展示子命令列表（`list|show|edit|update|new`），每个子命令的专有参数正确归属
- **修复遗漏**：补充 `new` 命令的帮助定义（此前 parser 支持但 help 未显示）
- **修复命名不一致**：搜索参数名从 `--search-pattern` 修正为 `-s, --search`（与 `appcontext.py` 一致）
### v0.8.4

- HostsKeeper 迭代至 0.8.4
- **重构并发模型**：移除 contenter 级并发（原 `asyncio.as_completed` 因同步 `urlopen` 阻塞事件循环形同虚设），简化为 profile 级并发（`max_workers` 控制同时处理的 profile 数），profile 内 contenter 顺序处理
- **解除 URL 阻塞**：`UrlContenter.get_content()` 改为 async，通过 `run_in_executor` 将 `urlopen` 移出事件循环，使多 profile 并行下载真正生效
- **Progress 实时追踪**：`hostskeeper update` 集成 Rich Progress 面板，单 contenter 用回转 spinner，多 contenter 用进度条，实时显示每个 profile 的处理状态
- **迁移至 cx_wealthy**：hosts_keeper 的 TUI 依赖从 `cx-wealth` 完整迁移至 `cx-wealthy`（`WealthLabel`→`RichLabel`、`WealthHelp`→`WealthyHelp`），样式通过 `default_theme` 机制注入
- **cx_wealthy.rich_types 补充**：新增 `Progress`、`TaskID`、`SpinnerColumn`、`TextColumn`、`BarColumn`、`TaskProgressColumn`、`TimeRemainingColumn` 导出
- **contenter 动态状态文本**：`AbstractContenter` 新增 `status_text` 属性，contenter 在处理过程中自行更新，外部通过回调读取以实时更新 progress description
- **修复 HostsSaver 先使用后赋值 bug**：`__init__` 中 else 分支（`source_hosts` 为 `Iterable[str]` 时）先写入临时文件再赋值
- **修复 i18n 遗漏**：`appenv.py` 中 2 处临时目录提示文字、`application.py` 中 `command_list` 表头（ID/Name/Description/Enabled）
- **修复拼写错误**：`prepare_customed_lines` → `prepare_custom_lines`
- **修复缺失类型标注**：`AppContext.show_help`
- **删除死代码**：`application.py` 中未使用的 `url = f"file://{file_path.resolve()}"`
### v0.8.3

- Jpegger 迭代至 0.8.3
- 配合 cx-wealthy 0.1.2 的 `__rich_detail__` str/Text 语义变更：`ImageFilterChain.__rich_detail__` 的 key 改为 yield `Text.from_markup(...)` 对象，保持彩色标签显示
- 修复 jpegger 输出文件重名时的行为：不再自动下划线重命名，改为跳过并警告

### v0.8.2

- Jpegger 迭代至 0.8.2
- 将 Jpegger 的 Rich UI 依赖从 `cx-wealth` 迁移至 `cx-wealthy`（其余 4 个工具仍在 cx-wealth 上，渐进迁移）
- 在 `cxalio-studio-tools` 的 `dependencies` 中新增 `cx-wealthy`，保留 `cx-wealth`
- 在 `IAppEnvironment` 中合并 `cx_wealthy.default_theme`，使应用框架层支持 cx_wealthy 组件渲染
- 修复迁移过程中发现的 cx_wealthy 阻塞性问题（详见 spec 同目录 `audit.md`）：
  - `Group` 类新增 `add_action` 便利方法（延迟导入保持分层）
  - `Action._validate_flags` 放宽校验，支持位置参数名与含连字符的 flag（如 `--force-overwrite`）

### v0.8.1

- Jpegger 迭代至 0.8.1
- 修复 `ResizeFilter` 与 `FactorResizeFilter` 的缩放逻辑：按目标尺寸/缩放因子计算宽高，避免原图尺寸覆盖或传入浮点数导致 `Image.resize` 失败
- 修复 `Mission.filter_chain` 默认共享可变对象的问题，确保每个任务实例拥有独立的过滤器链
- 为 Jpegger 各模块、类、方法补充文档字符串，并在关键执行路径增加说明，提升可维护性
- 修复 `IAppEnvironment` 未从 `cx_tools.app` 正确导出的问题
- 在分发包 `pyproject.toml` 中配置 basedpyright，关闭 `reportUnknownMemberType` 与 `reportExplicitAny` 规则
- 在代码注释中说明：GIF 仅处理第 1 帧为期望行为，Jpegger 的定位是单帧图片处理

### v0.8.0

- HostsKeeper 更新 hosts 后自动执行平台对应的 DNS 缓存刷新（Windows ipconfig /flushdns、macOS killall -HUP mDNSResponder、Linux 提示手动命令）
- 新增 `--skip-flush` 参数，跳过自动刷新仅给出平台特定的手动命令提示
- 帮助文档（--help / --tutorial）中补充 `--skip-flush` 说明
- 所有提示信息仅在系统 hosts 路径更新时触发，自定义 `-t` 路径不触发

- 修复多处 hosts 文件编码处理问题（移除冗余的 platform encoding 检测、强制关闭 BOM 写入、补齐 importlib.resources 显式编码参数）

### v0.7.5

- 修复 MediaKiller 任务执行器中 finally 块的 return 语句问题
- 配置 pyright 类型检查并修复类型安全问题
- 扩展 Python 版本支持范围至 <3.15

### v0.7.1

- 修复了 HostsKeeper 工具处理 URL 内容时的编码问题

### v0.7.0

- 重新调整部分代码以适应cx-studio的更新。
- 去除了 dydantic 的依赖，重新使用轻量的 dataclass。

### v0.6.3.2

- 增加了 HostsKeeper 工具保存 hosts 文件的方法，现在将在需要时调用管理员权限（仅支持sudo）
- 增加了 HostsKeeper 工具指定目标文件的参数，不指定的话仍然是系统hosts文件。
- 修复了 帮助信息中的 typo

### v0.6.2

- 增加了 HostsKeeper 工具，用于管理 hosts 文件
- 为 IAppEnvironment 增加了判断当前用户是否为管理员的方法

### v0.5.1.6

- 为 ffpretty 增加了取消操作的提示信息
- 为 ffpretty 增加了查询模式
- 为 ffpretty 增加了帮助信息
- 为 ffpretty 清理了代码

### v0.5.1.4

- 全面排查bug
- 将默认样式定义为全局主题 cx_default_theme
- 优化了 mediakiller 中的一些输出方式

### v0.5.1.3

- 增加了 CxHighlighter 类，用于高亮显示 CX 相关的日志信息
- 自动安装 CxHighlighter 作为全局输出的高粱显示工具，默认情况下不影响 WealthHelp 的输出

### v0.5.1.2

- 为 Jpegger 定义了无事可做时的处理方式

### v0.5.1.1

- 增加了 Jpegger 工具，用于快速批量转换图片
- 调整了代码格式

### v0.5.0.4

- 修改 mediakiller 的任务保存格式为 XML 格式
- 修改 ConfigManager 的默认配置文件保存位置，增加了一级子目录
- 调整了 mediakiller 中 import 的顺序，避免载入 bug

### v0.5.0.3

- hotfix: mediakiller 文件大小统计的输出 bug
- hotfix: 尝试修复任务自动保存在 macOS 上的 bug

### v0.5.0.1

- 修正错误的 import
- 为 mediakiller 增加文件大小统计功能

### v0.4.9.5

- 全面使用 pydantic 和 Box 替代原生和 cx-studio 的实现

### v0.4.9.4

- hot fix for a packaging bug

### v0.4.9.3

- 修复了 Media Killer 提示信息的 bug
- 增加了 FFpretty 工具

### v0.4.9.1

- Media Scout 现在可以选择输出转义模式了
