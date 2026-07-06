"""MediaDB 媒体信息统一入口模块。

继承 FileInfoCache，提供媒体元数据的缓存查询入口。
缓存命中时直接返回 MediaInfo，未命中时调度 MediaProber 探测并回填。
内部锁串行化 MediaProber 调用，避免 ffprobe 并发资源争抢。
"""

from __future__ import annotations

import threading
from pathlib import Path

from cx_studio.filesystem.cx_file_info_cache import FileInfoCache

from .media_info import MediaInfo
from .media_prober import MediaProber


class MediaDB(FileInfoCache):
    """媒体元数据统一查询入口。

    继承 FileInfoCache，在缓存层之上增加 MediaProber 调度逻辑：
    - 缓存命中：反序列化并返回 MediaInfo（或 None 表示非媒体文件）
    - 缓存未命中：通过 MediaProber 探测，成功则回填缓存
    - ffprobe 失败：抛出异常，不缓存
    """

    def __init__(
        self,
        db_path: Path,
        prober: MediaProber | None = None,
    ) -> None:
        """初始化 MediaDB。

        Args:
            db_path: SQLite 数据库文件路径
            prober: MediaProber 实例。若为 None，则创建默认实例。
        """
        super().__init__(db_path=db_path)
        self._prober: MediaProber = prober if prober is not None else MediaProber()
        self._probe_lock = threading.Lock()

    def get_media_info(self, file: Path) -> MediaInfo | None:
        """同步获取 MediaInfo；先查缓存，未命中则调度 MediaProber。

        Args:
            file: 媒体文件路径

        Returns:
            MediaInfo | None: 成功返回 MediaInfo，非媒体文件返回 None

        Raises:
            FileNotFoundError: 文件不存在
            RuntimeError: ffprobe 调用失败
        """
        cached = self.get(file)
        if cached is not None and "media_info" in cached:
            raw = cached["media_info"]
            if raw is None:
                return None
            return MediaInfo.from_dict(raw)

        with self._probe_lock:
            info = self._prober.probe(file)

        self.set(file, {"media_info": info.to_dict()})
        return info
