# MediaProber / MediaDB / FileInfoCache 设计文档

本文档定义 media_killer 中媒体元数据探测与缓存子系统的设计。三个组件按职责分层：

- **`FileInfoCache`**（`cx-studio`）：通用文件条目缓存机制。
- **`MediaProber`**（`media_killer`）：纯 `ffprobe` 调用器。
- **`MediaDB`**（`media_killer`）：继承 `FileInfoCache`，调度 `MediaProber`，是 media_killer 内媒体信息的唯一入口。

```text
消费者（MissionMaker / MissionScheduler / 未来工具）
    ↓
MediaDB（同步，控制 ffprobe 并发）
    ├── 继承 FileInfoCache（SQLite 持久化缓存）
    └── 调度 MediaProber（无锁，可并发）
            ↓
        ffprobe
```

---

## 1. FileInfoCache

### 1.1 定位

`FileInfoCache` 是 `cx-studio` 提供的轻量文件条目缓存便利设施。它不是通用完美缓存器，目标是：

- **动态控制**：按需 `get` / `set` / `invalidate`，不预加载、不主动扫描。
- **快速启动**：初始化只做配置保存；真正连接数据库在 `connect()` 时发生。
- **够用即可**：基于文件 `mtime` 自动失效，支持 `max_size` LRU 淘汰，满足 media_killer 的需求即可。

### 1.2 接口

```python
from pathlib import Path


class FileInfoCache:
    def __init__(self, db_path: Path, max_size: int = -1) -> None:
        """保存配置，不立即连接数据库。"""
        ...

    def connect(self) -> None:
        """建立 SQLite 连接并创建表结构。"""
        ...

    def close(self) -> None:
        """执行淘汰清理，然后关闭连接。"""
        ...

    def cleanup(self) -> None:
        """独立的淘汰清理方法；可被手动调用，也会被 close() 自动调用。"""
        ...

    def get(self, file_path: Path) -> dict | None:
        """读取 user_data。若缓存不存在或 mtime 已变化，返回 None。"""
        ...

    def set(self, file_path: Path, data: dict) -> None:
        """写入 user_data；同时记录当前文件 mtime。"""
        ...

    def invalidate(self, file_path: Path) -> None:
        """删除指定文件的缓存条目。"""
        ...

    def _get_record(self, file_path: Path) -> dict | None:
        """内部方法：在锁保护下读取完整记录（含 file_mtime, cache_last_access, user_data）。"""
        ...

    def _set_record(self, file_path: Path, record: dict) -> None:
        """内部方法：在锁保护下写入完整记录。"""
        ...

    def __enter__(self) -> "FileInfoCache":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
```

> `get` / `set` 对外暴露，只操作 `user_data`；内部通过 `_get_record` / `_set_record` 在锁保护下一次性读写完整记录，避免多次数据库访问并保证原子性。

### 1.3 生命周期

- `__init__`：仅保存 `db_path` 与 `max_size`，不打开任何资源。
- `connect()` / `__enter__`：建立 `sqlite3.Connection`，创建表（若不存在）。**不做淘汰清理**，避免删除本次会话将要使用的条目。
- `close()` / `__exit__`：先调用 `cleanup()` 执行淘汰，再关闭连接。
- 不再依赖 `__del__`：避免 Python 退出时 `sqlite3` 模块已卸载导致的问题。

### 1.4 缓存 Key

使用**规范化后的绝对路径**作为 key，例如：

```python
key = str(file_path.resolve())
```

不采用哈希摘要。理由：

- 路径长度对 SQLite 索引不构成实际压力。
- 可调试：可直接通过路径查询数据库排查问题。
- 无哈希冲突风险。

### 1.5 失效规则

读取时检查文件当前 `mtime` 与缓存中记录的 `mtime` 是否一致。不一致则视为失效，返回 `None`。

### 1.6 线程安全

`FileInfoCache` 是同步类，使用 `threading.Lock` 保护 `sqlite3` 连接的操作。调用方若处于异步环境，需自行决定如何调度（如使用 `asyncio.to_thread`）。

### 1.7 淘汰策略

- 支持 `max_size` 限制。
- 淘汰只在 `close()` / `cleanup()` 时触发，不在运行时或启动时触发。
- 淘汰采用 LRU：根据最后访问时间删除最久未用的条目，直到总条目数低于阈值。

---

## 2. MediaProber

### 2.1 定位

`MediaProber` 是 media_killer 的底层媒体元数据探测器。它只负责一件事：对单个文件调用 `ffprobe` 并返回结构化的 `MediaInfo`。

### 2.2 接口

```python
from pathlib import Path


class MediaProber:
    def __init__(
        self,
        ffprobe_executable: str | Path | None = None,
    ) -> None:
        ...

    def probe(self, file: Path) -> MediaInfo:
        """同步调用 ffprobe，返回 MediaInfo。"""
        ...
```

### 2.3 无锁、可并发

`MediaProber` **不内部持锁**。它本身支持并发运行；是否并发由调用方（`MediaDB`）决定。

这样设计的好处：

- `MediaProber` 保持纯粹，只关心如何正确调用 `ffprobe`。
- 并发策略由更高层控制，便于根据场景调整（例如 media_killer 中 `MediaDB` 选择串行调用 ffprobe）。

### 2.4 MediaInfo

`MediaInfo` 是承载 `ffprobe` 解析结果的 frozen dataclass。字段设计以 media_killer 的 Preset 标签替换需求为主，同时保留通用媒体信息。

```python
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


@dataclass(frozen=True)
class MediaInfo:
    # 文件身份
    file_path: Path

    # 容器与流
    container_format: str | None = None   # 如 "mov,mp4,m4a"
    stream_count: int = 0
    has_video: bool = False
    has_audio: bool = False

    # 时长（秒）
    duration: float | None = None

    # 视频属性
    width: int | None = None
    height: int | None = None
    fps: Fraction | float | None = None   # 优先 Fraction 保留精确值
    video_codec: str | None = None        # 如 "h264"
    video_bitrate: int | None = None      # bps

    # 音频属性
    audio_codec: str | None = None        # 如 "aac"
    audio_bitrate: int | None = None      # bps
    sample_rate: int | None = None        # Hz
    channels: int | None = None
```

字段说明：

| 字段 | 用途 | 对应标签示例 |
|---|---|---|
| `file_path` | 标识该 MediaInfo 所属文件 | — |
| `container_format` | 容器格式 | `${source:format}` |
| `duration` | 时长（秒） | `${source:duration}`、`-t ${source:duration}` |
| `width` / `height` | 分辨率 | `${source:width}`、`${source:height}` |
| `fps` | 帧率 | `${source:fps}` |
| `video_codec` / `audio_codec` | 编码格式 | `${source:vcodec}`、`${source:acodec}` |
| `video_bitrate` / `audio_bitrate` | 码率 | `${source:vbitrate}`、`${source:abitrate}` |
| `has_video` / `has_audio` | 判断是否有对应流 | 用于 lint 或选项条件 |

> 标签变量名仅为示例，PresetTagReplacer 实现时可按需映射。MediaInfo 字段是稳定的，标签名是 Preset 层的消费约定。

### 2.5 序列化

`MediaInfo` 需要能被 `MediaDB` 序列化后存入 `FileInfoCache.user_data`，也能从 `user_data` 反序列化。

推荐方式：

```python
from dataclasses import asdict

# MediaInfo -> dict
info_dict = asdict(media_info)

# dict -> MediaInfo
media_info = MediaInfo(**info_dict)
```

- `Path` 字段序列化为字符串（`str(file_path)`），反序列化时恢复为 `Path`。
- `Fraction` 字段序列化为字符串（`str(fps)`），反序列化时恢复为 `Fraction`。
- 缺失字段使用默认值（`None` 或 `0` 或 `False`），保证旧缓存可向前兼容。

---

## 3. MediaDB

### 3.1 定位

`MediaDB` 是 media_killer 内媒体元数据的统一入口。它：

- 继承 `FileInfoCache`，使用 SQLite 持久化缓存成功的 `MediaInfo`。
- 调度 `MediaProber` 获取未缓存的媒体元数据。
- 控制 `ffprobe` 的并发调用策略。
- **不缓存探测失败**。真正的 `ffprobe` 失败通过异常暴露，下次请求会重新探测。

普通消费者（如 `MissionMaker`）只与 `MediaDB` 交互，不直接调用 `MediaProber`。

### 3.2 接口

```python
from pathlib import Path


class MediaDB(FileInfoCache):
    def __init__(
        self,
        db_path: Path,
        prober: MediaProber | None = None,
    ) -> None:
        ...

    def get_media_info(self, file: Path) -> MediaInfo | None:
        """同步获取 MediaInfo；先查缓存，未命中则调度 MediaProber。

        返回 None 表示文件存在但非媒体文件；ffprobe 失败则抛出异常。
        """
        ...
```

### 3.3 同步设计

`MediaDB` 是同步类。理由：

- 缓存查询/写入开销很小，同步阻塞可接受。
- `ffprobe` 本身是同步阻塞的 heavy I/O 操作，不应在 asyncio 事件循环中直接运行。
- 若上层（如 `MissionScheduler`）在异步环境中需要使用，由上层自行决定如何调度（例如在线程池中调用 `MediaDB.get_media_info`）。

**异步-同步桥接责任**：

- `MediaDB` 不内部转异步，也不假设自己运行在异步环境中。
- `MissionMaker` 等同步消费者可直接调用 `MediaDB.get_media_info()`。
- `MissionScheduler`（异步）不应在事件循环中直接调用 `MediaDB`。推荐做法：
  - **方案 A（推荐）**：在 `MissionScheduler.run()` 之前，由 `Application` 同步完成所有 Mission 生成（包括 `MissionMaker` 对 `MediaDB` 的调用），再将生成好的 `list[Mission]` 交给异步的 `MissionScheduler`。这样 `MediaScheduler` 运行时不再访问 `MediaDB`。
  - **方案 B**：若必须在 `MissionScheduler.run()` 中访问 `MediaDB`，通过 `asyncio.to_thread()` 或线程池包装 `MediaDB.get_media_info()` 调用。

> 推荐方案 A，因为媒体元数据探测通常只在 Mission 生成阶段需要；将探测与异步执行阶段分离，可避免在异步代码中频繁桥接同步 I/O。

### 3.4 ffprobe 并发控制

`MediaDB` 负责控制是否并发调用 `MediaProber`。

默认策略：**串行调用**。理由：

- `ffprobe` 会大量读取磁盘，多个并发实例会互相争抢 I/O。
- 对同一文件并发探测毫无意义。
- media_killer 的元数据探测阶段通常不是瓶颈，串行更简单可控。

实现方式可选：

- 在 `MediaDB` 内部持有一把 `threading.Lock`，进入 `get_media_info` 后先获取锁，再调用 `MediaProber`。
- 或使用单线程消费者模式，将探测请求放入队列，由一个工作线程串行处理。

`MediaProber` 本身不持锁，因此如果未来某场景需要并发探测，只需换用一个不锁的 `MediaDB` 实现即可。

### 3.5 MediaDB 在 FileInfoCache 中的数据格式

`MediaDB` 通过 `FileInfoCache.set(file, data)` 写入缓存，其中 `data` 是 `dict`。`MediaDB` 使用固定的顶层键 `"media_info"` 存储序列化后的 `MediaInfo`：

```python
# 命中媒体文件
{
    "media_info": {
        "file_path": "/absolute/path/to/video.mp4",
        "container_format": "mov,mp4,m4a",
        "stream_count": 2,
        "has_video": True,
        "has_audio": True,
        "duration": 123.456,
        "width": 1920,
        "height": 1080,
        "fps": "30000/1001",
        "video_codec": "h264",
        "video_bitrate": 5000000,
        "audio_codec": "aac",
        "audio_bitrate": 128000,
        "sample_rate": 48000,
        "channels": 2,
    }
}

# 命中非媒体文件（已确认无媒体元数据）
{
    "media_info": None
}
```

约定：

- `MediaDB` 只读写 `user_data["media_info"]`，不占用其它键，以便上层或未来扩展可以共存其它数据。
- 反序列化时，若 `"media_info"` 为 `None`，返回 `None`；若为 `dict`，恢复为 `MediaInfo`。
- 若 `user_data` 中不存在 `"media_info"` 键，视为未缓存，调度 `MediaProber`。

### 3.6 非媒体文件与失败处理

`MediaDB.get_media_info(file) -> MediaInfo | None`：

- 返回 `MediaInfo`：成功获取到媒体元数据。
- 返回 `None`：文件存在，但不是媒体文件（或无可识别元数据）。这种情况下 `MediaDB` 仍会在 `FileInfoCache` 中写入一条记录，只是 `user_data` 中不包含媒体元数据。不需要专门的 sentinel。
- 抛出异常：`ffprobe` 调用失败（文件损坏、无法访问等）。异常不会被缓存，下次请求会重新探测。

> 不需要失败 sentinel。"缓存存在但无元数据"本身就表示"已确认非媒体文件"；真正的失败通过异常暴露，由调用方处理。

### 3.7 与 AppEnv 的集成

```python
class AppEnv:
    def __init__(self, media_db_path: Path, ...):
        self.media_db = MediaDB(db_path=media_db_path)

    def __enter__(self):
        self.media_db.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.media_db.close()
```

运行时需要单个全局 `MediaDB` 实例，由 `AppEnv` 持有并在进入/退出时启动和关闭。`MediaDB` 不硬编码数据库位置，由 CLI / `AppEnv` 实例化时指定。

---

## 4. 决策记录

### 4.1 FileInfoCache 保留在 cx-studio

`FileInfoCache` 虽然目前只用于 media_killer，但本身是通用文件条目缓存机制，保留在 `cx-studio` 中便于未来复用。

### 4.2 FileInfoCache 不做复杂通用缓存器

网上已有大量优秀通用缓存实现，`FileInfoCache` 只需是 `cx-studio` 内的轻量便利设施。过度设计会增加维护负担。

### 4.3 不使用 `__del__`

Python 退出时模块清理顺序不确定，`sqlite3` 可能在 `__del__` 执行前已卸载。因此改用显式 `connect()` / `close()` 与上下文管理器。

### 4.4 缓存 Key 使用规范化绝对路径

不采用哈希摘要。路径长度不会成为 SQLite 性能问题，而可读性和无冲突更重要。

### 4.5 MediaProber 无锁

`MediaProber` 支持并发运行，是否并发由 `MediaDB` 控制。这样 `MediaProber` 保持简单纯粹。

### 4.6 MediaDB 串行调用 ffprobe

`ffprobe` 开销大且争用 I/O，`MediaDB` 默认串行调用。缓存查询同步执行，开销可忽略。

### 4.7 不使用 sentinel

非媒体文件通过"缓存存在但 `user_data` 中无媒体元数据"表示，不需要专门的 sentinel。真正的失败通过异常暴露，不缓存。

---

## 5. 实现顺序

1. 在 `cx-studio` 中重新设计并实现 `FileInfoCache`。
2. 在 `media_killer` 中实现 `MediaInfo` 值对象。
3. 在 `media_killer` 中实现 `MediaProber`。
4. 在 `media_killer` 中实现 `MediaDB`，继承 `FileInfoCache` 并调度 `MediaProber`。
5. 在 `AppEnv` 中集成 `MediaDB` 的生命周期管理。
