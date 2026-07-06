# media_killer 参考文档

> 本文档是 media_killer（media_killer 从头重设计版本）的设计参考。它记录
> 重设计过程中确认的所有架构决策及其理由，作为后续实现的依据。文档面向
> 第一次接触本设计的读者，不预设你读过讨论过程。

---

## 1. 为什么要重设计

旧版 media_killer（`packages/cxalio-studio-tools/media_killer/`，v0.8.0）能工作，
但累积了若干结构性问题，使得它既难测试、难复用，也难维护：

- **全局单例硬连**：模块级 `appenv = AppEnv()` 在加载时实例化，所有组件通过
  `from ..appenv import appenv` 直接引用。这导致组件无法脱离 media_killer 的 CLI
  环境单独使用，也是测试的最大障碍。
- **取消机制重叠**：存在 4 种以上互相重叠的取消路径（`_cancel_event`、
  `_cancel_one`、`_cancel_all_event`、`wanna_quit`/`really_wanna_quit`），外加
  一段从未触发的死代码（`_poison_task`/`PoisonError`）。
- **preset 原始数据透传**：`Preset.inputs`/`outputs` 是 `list[Box]`（无类型），
  `raw: Box` 把整个 TOML 原文拖着到处走。字段名写错要跑到运行时才暴露；标签
  模板（`${source:fullpath}` 等）在加载时不校验，用户写错要等到处理某个源文件
  时才炸。
- **工具间穿透**：`source_expander` 直接 import `media_scout.inspectors` 的内部
  模块——一个工具穿透到另一个工具的内部结构。
- **与 ffpretty 重复实现**：ffpretty 的 `Transcoder` 和 media_killer 的
  `MissionRunner` 各自独立实现了"执行一次转码"的整套逻辑（事件监听、进度更新、
  取消信号），存在本可去除的重复。

重设计不从旧版代码出发，而是从用户面对的功能阶段和工具集整体的复用需求出发，
重新推导结构。

---

## 2. 整体定位

media_killer 不是一个孤立的批处理工具，而是三层能力叠在一起：

| 层 | 寄居位置 | 职责 | 谁用它 |
|---|---|---|---|
| 通用文件缓存 | `cx_studio/filesystem/` | 文件数据缓存的存取、失效判断、LRU 淘汰。不碰 ffmpeg，不知道什么是媒体文件 | 所有需要缓存文件附属数据的工具 |
| 共享底座 | `media_killer` 包内 | Mission（转码任务值对象）+ 执行单元（跑一个 Mission）+ 媒体元数据探测件 | media_killer 自身、ffpretty、media_scout 等 |
| 批处理外壳 | `media_killer` 包内 | 批量构造 Mission、调度器、continue 持久化 | 仅 media_killer 的 CLI |

**核心原则：转码在整个工具集只有一条路径——构造 Mission，然后执行。**

Mission 是整个工具集转码场景的中心契约，不是 media_killer 的私有类型。ffpretty
的全部独特性收缩到"从命令行参数构造一个 Mission"这一步，执行完全复用共享底座
的执行单元。media_killer 相对 ffpretty 多出来的，只是"一次处理很多个 Mission"
那一层——即批量构造、调度、continue。

设计重心因此落在"批"这一层：单任务层（Mission + 执行单元）是共享底座，
media_killer 和 ffpretty 都站在上面。

---

## 3. Mission：转码的中心契约

### 3.1 它是什么

Mission 是一个完全解析好的转码任务值对象（frozen dataclass）。它携带执行一次
转码所需的全部信息：源文件、目标路径、FFmpeg 参数、输入/输出组、覆盖标志等。

### 3.2 解析程度——生成阶段与执行阶段之间的契约面

Mission 在**生成阶段**结束时构造完成，此时它应达到以下解析程度：

- **输入已校验**：源文件存在性已在生成阶段检查过。
- **输出已确认**：输出冲突（目标已存在）已在生成阶段暴露——media_killer 靠
  -y/-n 决定覆盖或跳过，ffpretty 靠命令行的 -y/-n。
- **参数已展开**：所有标签模板（`${source.*}`、`${preset.*}` 等）已替换为最终
  值，Mission 内不再保留模板字符串。
- **输出目录未创建**：这是关键边界——目录创建归执行阶段，因为生成阶段（尤其
  media_killer 没有预览、但用户仍可能在执行前 Ctrl+C）不该在文件系统上留下
  空目录。

> **为什么这样切**：按"是否在用户确认执行之前动文件系统"来划分职责。输入校验
> 和输出冲突检查是"告诉用户会怎样"，属于生成阶段；目录创建是"在磁盘上留下
> 东西"，属于执行阶段。这样切之后，生成阶段不碰文件系统的写操作，执行阶段接
> 到的 Mission 是"可以直接跑"的。

### 3.3 谁构造、谁执行

- **构造者**：media_killer 的批量构造器（从 Preset + 源展开生成）、ffpretty 的
  CLI 外壳（从命令行参数生成）。构造者负责把各自的输入形式转换成 Mission。
- **执行者**：执行单元（见第 4 节）。执行单元接收 Mission，负责创建输出目录、
  跑 FFmpeg、报进度、接取消、返回结果。
- **构造完成后，Mission 不再引用 Preset 或源展开器**——它是自洽的值对象。

### 3.4 已解决（见 ARCHITECTURE.md §4.1）

Mission 字段集已在 [ARCHITECTURE.md §4.1](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/ARCHITECTURE.md#41-mission) 中确定：

```python
@dataclass(frozen=True)
class Mission:
    mission_id: ULID
    ffmpeg: str
    source: Path
    standard_target: Path
    overwrite: bool
    hardware_accelerate: str | None
    options: list[str]
    inputs: list[InputSpec]
    outputs: list[OutputSpec]
    preset_id: str | None = None
    preset_name: str | None = None
```

- `preset_id` / `preset_name` 作为展示/调试用的附加字段保留，不参与执行逻辑。
- 所有 `Path` 字段在构造前必须解析为绝对路径。

> 本段保留旧版字段讨论作为历史参考，但实现以 ARCHITECTURE.md 为准。

---

## 4. 执行单元

### 4.1 职责

执行单元跑**一个** Mission。给定一个完全解析的 Mission，它负责：

1. 创建输出目录（生成阶段没创建，这里才动文件系统）；
2. 启动 FFmpeg 进程；
3. 通过 pyee 向外报告进度和状态（开始、进行中、完成、失败）；
4. 通过 `cancel()` 方法接收中断；
5. 返回执行结果（成功/失败/取消）。

### 4.2 边界——不碰 appenv

执行单元**不 import appenv**，不依赖任何全局单例。它需要的两样东西——"往哪报
进度"和"谁有权取消我"——都不来自全局：

- 进度：通过 pyee 往外发事件，谁监听谁收到，执行单元不知道外面有没有 UI。
- 取消：暴露 `cancel()` 方法，外面调它就停，执行单元不知道是谁在调。

> **为什么必须如此**：这是复用的前提。只要执行单元还绑着 appenv，ffpretty 就
> 没法在不拽进一整套 media_killer CLI 环境的前提下单独用它。同时这也是旧版测试
> 障碍的根源——全局单例使得组件无法在隔离环境中实例化。

### 4.3 进度与取消的机制区分

两者方向相反，用不同机制：

| 方向 | 内容 | 机制 |
|---|---|---|
| 往外吐 | 进度、状态（开始/进行/完成/失败） | pyee 事件（延续 `cx_studio.ffmpeg.FFmpegAsync` 已有做法） |
| 往里压 | 中断 | `cancel()` 方法（延续 `FFmpegAsync.cancel()` 已有做法） |

> **为什么不用统一机制**：往外吐是"一对多广播"（可能有多个监听者：进度条、日
> 志、统计），适合事件；往里压是"单一指令"（停下来），适合方法调用。强行统一
> 反而别扭。这也与 `cx_studio.ffmpeg.FFmpegAsync` 的现有设计一致——它既有 pyee
> 事件又有 `cancel()` 方法。

### 4.4 ffpretty 如何复用

ffpretty 没有"批"这一层。它的 CLI 外壳接到命令行参数后：

1. 解析参数（相当于生成阶段）；
2. 做输入校验和输出冲突检查；
3. 构造一个 Mission；
4. 交给执行单元跑。

ffpretty 不需要调度器、不需要两段式中断——单任务场景，CLI 直接把中断挂到执行单
元的 `cancel()` 上，一次就停。

---

## 5. 通用文件缓存（FileInfoCache）

### 5.1 定位

寄居 `cx_studio/filesystem/cx_file_info_cache.py`。它是所有"给文件缓存点东西"的
工具都需要的通用底座，与媒体无关、与 ffmpeg 无关。

### 5.2 职责

- **存取**：以文件绝对路径为主键，存取不透明的 JSON 数据（`user_data`）。底层
  不关心存的是什么内容。
- **失效判断**：基于文件系统信息（`os.path.exists` + `os.path.getmtime` 对比）
  判断缓存是否有效，文件不存在或已修改则自动清除对应记录。
- **淘汰**：LRU 策略，基于 `max_size` 和 `cache_last_access`，在析构时批量淘汰。
- **路径不硬编码**：构造时接收 `db_path`，自己不定位目录。目录定位由上层
  （cx_tools 的配置目录能力）负责，工具不硬编码缓存位置。

### 5.3 不包含的能力

- 不做多媒体元数据获取（不碰 ffmpeg）。
- 底层只做管理器，不主动暴露文件属性（mtime/size）——透明存取，特化层自己存
  需要的属性。（此点在讨论中确认：底层仅作为管理器即可。）

### 5.4 已解决（见 MEDIA_PROBER_AND_CACHE.md）

以下两个 gap 已在后续讨论中确定最终方案：

1. **空值语义**：最终方案是**不缓存探测失败**。`MediaDB.get_media_info(file)` 返回
   `MediaInfo | None`：`None` 仅表示"文件存在但非媒体文件"，此时 `FileInfoCache` 中
   保留一条 `user_data` 不含媒体元数据的记录；真正的 `ffprobe` 失败通过异常暴露，
   **不缓存**。详见
   [MEDIA_PROBER_AND_CACHE.md §3.5](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/MEDIA_PROBER_AND_CACHE.md#35-非媒体文件与失败处理)。
2. **`__del__` 作为唯一淘汰入口**：最终方案是**显式生命周期管理**。`FileInfoCache`
   提供 `connect()` / `close()` 和上下文管理器，`close()` 时执行 LRU 淘汰；不再依赖
   `__del__`。详见
   [MEDIA_PROBER_AND_CACHE.md §1.3](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/MEDIA_PROBER_AND_CACHE.md#13-生命周期)。

> 本段保留旧版讨论作为历史参考，但实现以 MEDIA_PROBER_AND_CACHE.md 为准。
>
> **关于存储格式**：底层用 SQLite（已有实现），适合大量、可增量更新的数据。不
> 用 TOML——配置文件是人写的、少量、低频；缓存是程序写的、可能量很大、随文件
> 变，两者性质不同。

---

## 6. 媒体元数据探测件

### 6.1 定位

寄居 `media_killer` 包内，依赖 ffmpeg，是"媒体类工具"范畴的共享能力。它知道
"对一个媒体文件该用 ffmpeg 探测什么、结果怎么组织"。

### 6.2 与缓存的关系

所有工具（包括 media_scout 自己）都只跟缓存引擎这条路径打交道：

```
工具查询 → 媒体元数据探测件 → 查缓存（FileInfoCache）
                                  ├─ 命中 → 返回
                                  └─ 未命中 → 调 ffmpeg 探测 → 回填缓存 → 返回
```

没有"谁负责填、谁负责读"的角色分裂。媒体元数据探测件是缓存的唯一消费者，它封
装了"查缓存、未命中则探测、回填"的完整流程。

### 6.3 解耦效果

旧版 `source_expander` 直接 import `media_scout.inspectors` 的内部模块——这是工
具之间穿透到对方内部。引入缓存中介后，这条直接依赖消失：media_scout 的探测能力
通过缓存暴露给所有工具，工具之间不再互相 import 内部结构。

### 6.4 "工具特化"的粒度

"特化"指的是相对于 cx_studio 通用层而言的"媒体类工具这个范畴的特化能力"——即
只要是媒体工具就共享同一份探测，不是每个工具各写各的。这与"工具间通过耦合功能
去重"的整体方向一致。

---

## 7. 批处理外壳（media_killer 独有）

### 7.1 批量构造

从 Preset 列表 + 源文件列表，批量生成 Mission 列表。每个 Preset 对应一个
MissionMaker，它展开源文件、对每个源做标签替换、构造 Mission。

批量构造是纯计算过程（不跑 ffmpeg、不写文件系统），可以并行（旧版已用
`asyncio.gather` 并行多 Preset）。

### 7.2 调度器

#### 职责

调度器管理"一批 Mission 的执行"：取 Mission、按并发度起执行单元、分发取消、
聚合进度。它不知道 Mission 怎么构造（那是生成阶段），也不知道 UI 长啥样（它只
往回调吐聚合后的进度）。

#### 中断——两段式语义

批量场景的中断分两段：

| 操作 | 语义 |
|---|---|
| 第一次 Ctrl+C | 停止接受新任务；当前在跑的任务继续运行至自然完成 |
| 短时间内第二次 Ctrl+C | 全局中止：清掉队列，确认在跑的都停了，整个流程结束 |

> **为什么需要两段**：这是真实 UX 选择。用户可能只是想"别再开新任务了，但让手
> 头的跑完"（第一次），也可能想"立刻全部停下"（第二次）。单任务的 ffpretty
> 不需要这个区分——直接 cancel 一次就停。

#### 中断信号的挂接——只挂调度器一个

中断信号**只挂到调度器**，不同时挂到执行单元。这样避免"执行单元和调度器都收到
信号"的混乱。信号路径：

```
appenv.interrupt_handler (DoubleTrigger)
    ├─ "first_triggered"  → 调度器.停当前()
    └─ "second_triggered" → 调度器.全局停()
                              └─ 调度器给在跑的执行单元逐个发 cancel()
```

CLI 创建完调度器后，用 `appenv.interrupt_handler.on()` 把中断信号挂到调度器的入
口上。调度器收到后再分发给手头在跑的执行单元。执行单元始终只知道"调度器调我
cancel，我就停"，不碰 appenv。

> **为什么不让 Application 层层转发**：Application 一层层往下翻译中断信号，链
> 一长就难追踪。直接从 appenv 弹到调度器，链短；调度器再往下分发，路径清晰。
> 这也是用户在讨论中明确提出的偏好。

#### 旧版取消机制的收敛

旧版 4+ 种取消路径（`_cancel_event`、`_cancel_one`、`_cancel_all_event`、
`wanna_quit`/`really_wanna_quit`、死的 `_poison_task`）收敛成上面这一条路径。
不靠全局事件广播，不靠组件轮询 `appenv.xxx_event.is_set()`。

#### 待定

- 并发模型的具体细节（并发度如何配置、Semaphore 还是其他）尚未深入。
- "第一次停完之后、还没等来第二次"那段空档，调度器是干等还是可以恢复——此语
  义尚未最终确定。

### 7.3 continue（-c）

#### 语义

**continue 是任务列表叠加，不是执行状态恢复。**

`-c` 把上次的全部 Mission 加进本次任务列表。本次调用不是上次的复现，而是在本次
调用的任务中增加上次的任务。具体某个任务是跳过还是覆盖，并无特殊行为——完全根
据 -y/-n 的设置进行。

> **含义**：continue 要存的是 **Mission 列表**，不是"跑到哪了"的进度。旧版有
> `MissionXML` 做 Mission 列表的 XML 序列化，这个能力可沿用（存储格式是否换 XML
> 之外的方案，待定）。

### 7.4 没有预览阶段

**明确声明：media_killer 不展示任务列表给用户确认、不让用户修改任务。**

这是设计意图——media_killer 是批量自动化工具，如果都要用户一个个确认，就失去
了它存在的意义。覆盖/跳过靠 -y/-n 双保险开关控制。

> 此点在讨论中曾因误判而被列入"独有能力"，后经用户纠正后划除。记录于此以防回
> 退。

---

## 8. appenv / appcontext 的边界

### 8.1 appenv

- **保持单例**：一个进程里就一个 console、一个 progress，用全局本身没错。
- **仅在 Application 层使用**：appenv 的职责是初始化 CLI 环境和响应中断，仅此。
  Application（最多再多一层）可以使用它，具体的执行功能模块不能依赖它提供信息。
- **执行模块不 import appenv**：执行单元、调度器、缓存引擎等可复用件，需要的
  一切从构造参数传入，不碰任何全局。

### 8.2 appcontext

- **只是命令行参数解析的结构化容器**：把用户的命令行参数解析为结构化数据并保
  存，到此为止。
- **不作全局数据包**：不在各模块之间当传递介质。

### 8.3 执行模块如何与外界沟通

分两个方向：

**调用层面（构造时）**：执行模块定义自己的接口（"我需要什么"），调用方
（CLI 应用）负责从 appenv/appcontext 等处收集相关信息，组织成接口兼容形式后传
入。执行模块不知道这些信息打哪来。

**运行时数据交换**：

| 方向 | 机制 | 说明 |
|---|---|---|
| 往外吐（进度、状态） | pyee 事件 | 执行模块发，外面监听 |
| 往里压（中断） | `cancel()` 方法 | 外面调，执行模块停 |

### 8.4 中断机制的保留

DoubleTrigger（两段式响应工具）和两个 asyncio.Event（`wanna_quit_event`、
`really_wanna_quit_event`，全局语义）都保留：

- **DoubleTrigger** 是响应工具——把 SIGINT 翻译成"第一次/第二次"的区分。
- **两个 Event** 是全局语义——供"轮询 / `await event.wait()`"这种接法使用。

> **两者貌似重复但应保留**：DoubleTrigger 是"怎么响应"，两个 Event 是"全局语
> 义状态"。全改成挂监听的话 Event 可能不需要，但 async 里 `await event.wait()`
> 确实比同步 `on()` 回调好使（回调里不能直接 await）。具体接法在实现时定，不影
> 响现在的方向判断。

---

## 9. preset 系统

### 9.1 数据模型——dataclass，不用 pydantic、不用 Box

Preset 用 `@dataclass(frozen=True)`。

> **为什么不用 pydantic**：太重，循环预处理阶段不方便（旧版最初用 pydantic，
> 后因这些原因换成了 Box）。
>
> **为什么不用 Box**：无类型——`inputs`/`outputs` 是 `list[Box]`，字段名写错要
> 跑到运行时才暴露；`raw: Box` 把整个 TOML 原文拖着到处走，是"原始数据全程透
> 传"的根源。
>
> **dataclass 是中间地带**：有类型边界（挡住字段名写错这种低级错误），但没有框
> 架负担；模板字段照样是 `str`、延迟到运行时替换。

### 9.2 类型化 inputs/outputs

`inputs`/`outputs` 从 `list[Box]` 改成 `list[InputSpec]`（`InputSpec` 是 frozen
dataclass，字段如 `filename: str`（模板）、`options: list[str]`（模板））。
MissionMaker 里就有类型了，字段错加载时报。

### 9.3 去掉 raw 透传

加载解析完就是强类型 Preset，不再拖着原始 TOML 结构。展示从字段渲染，不展示
`raw`。

### 9.4 保持灵活性

dataclass 只挡低级错误（字段存在、类型对），不管语义。灵活性保留在：

- `custom`：保留 `dict`（自由扩展点，强类型化反而限制它）。
- 模板字段：保留 `str`（内容不限，延迟替换）。
- `inputs`/`outputs` 的个数和内容：用户随便定。

### 9.5 lint——加载的一个阶段

加载流程：

```
解析 TOML → lint（结构检查 + 标签检查）→ 构造 Preset
```

任何一步不合法，中止并告诉用户具体哪里不对（哪个字段、哪个标签），不往下走。

#### lint 与模板替换共用同一套标签解析内核

模板替换是"代入具体值，产出最终字符串"；lint 是"只解析标签结构、不真的取值"——
`${source:fullpath}` 在 lint 时只检查"`source` 是已知 provider、`fullpath` 是它
认的 param"，不要求 source 真的在那。

> **为什么共用内核**：如果 lint 和替换是两套独立逻辑，就会出现"lint 放过了、
> 替换时炸了"的不一致。让 lint 复用替换的解析内核（lint 是"跑到取值前一步"），
> 保证两者永远一致。这是"算法层面约定和梳理保证优雅"的具体体现——不是堆一个
> 独立的 lint 模块去复刻标签逻辑，而是让 lint 复用替换的解析内核。

#### 用户反馈回路

用户写错 preset 的反馈从"跑到某个 source 才炸"缩短到"加载时立刻报具体位置"。

### 9.6 preset 的生命周期——media_killer 特有，翻译成 Mission 后退役

preset 是 media_killer 特定的配置形态，只管"怎么从配置 + 源生成 Mission"。生成
完 Mission 后，preset 就没用了——Mission 才是暴露给 ffpretty 等的通用能力。
preset 不进共享底座，不被其他工具 import。

---

## 10. 历史待定项（已解决）

以下事项在 REFERENCE.md 初稿中标记为待定，但已在后续文档中确定，实现时以对应文档为准：

| 事项 | 现状 | 参考文档 |
|---|---|---|
| Mission 具体字段集 | 已确定 | [ARCHITECTURE.md §4.1](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/ARCHITECTURE.md#41-mission) |
| 调度器并发模型 | 已确定：MissionScheduler 通过 `max_workers` 控制并发，MissionExecutor 事件驱动 | [ARCHITECTURE.md §4.10](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/ARCHITECTURE.md#410-missionscheduler) |
| 两段式中断的空档语义 | 已确定：第一次 `Ctrl+C` 停止接新任务、当前任务继续；第二次 `Ctrl+C` 清空队列并取消所有在跑任务 | [CLI_BEHAVIOR.md §6](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/CLI_BEHAVIOR.md#6-中断语义)、[ARCHITECTURE.md §9.12](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/ARCHITECTURE.md#912-missionscheduler-两段式中断) |
| FileInfoCache 空值语义 | 已确定：不缓存探测失败，仅通过 `None` 区分非媒体文件 | [MEDIA_PROBER_AND_CACHE.md §3.5](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/MEDIA_PROBER_AND_CACHE.md#35-非媒体文件与失败处理) |
| FileInfoCache 生命周期 | 已确定：显式 `connect()` / `close()`，不依赖 `__del__` | [MEDIA_PROBER_AND_CACHE.md §1.3](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/MEDIA_PROBER_AND_CACHE.md#13-生命周期) |

| continue 存储格式 | 已确定：沿用 XML | [ARCHITECTURE.md §7](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/ARCHITECTURE.md#7-已确认决策) |
| 进度报告具体机制 | 已确定：`MissionExecutor` 通过 pyee 事件报告，`MissionScheduler` 聚合事件 | [ARCHITECTURE.md §4.5](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/ARCHITECTURE.md#45-missionexecutor-事件) |
| lint 的具体规则集 | 实现细节：必填字段、合法标签、custom 引用等由 PresetLoader 在解析阶段报错 | [ARCHITECTURE.md §4.11.2](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/ARCHITECTURE.md#4112-presetloader) |
| 缓存失效的复杂场景 | 已确定：FileInfoCache 仅按文件级 mtime 失效，不处理流级粒度；MediaDB 按文件缓存 MediaInfo | [MEDIA_PROBER_AND_CACHE.md §1.5](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/MEDIA_PROBER_AND_CACHE.md#15-失效规则) |

> REFERENCE.md 是旧版行为参考与需求背景文档，其中的"待定"状态不代表当前仍有未决事项。所有最终决策以 CLI_BEHAVIOR.md、ARCHITECTURE.md、MEDIA_PROBER_AND_CACHE.md、OUTPUT_AND_UI.md 为准。

---

## 附：决策来源

本文档的决策来自一次从用户阶段出发的从头设计讨论，讨论中明确拒绝了"从架构模
式/层次/边界等术语 inward 推导结构"的方式，改为从用户面对的功能阶段（准备 →
执行 → 清理）和工具集复用需求 outward 推导。讨论过程中纠正过若干误判（全局事
件总线、预览阶段、`__del__` 不可靠等），纠正后的结论以本文档为准。
