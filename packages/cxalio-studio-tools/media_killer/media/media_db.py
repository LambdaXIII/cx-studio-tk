"""MediaDB 媒体信息统一入口模块。

继承 FileInfoCache，提供媒体元数据的缓存查询入口。
缓存命中时直接返回 MediaInfo，未命中时调度 MediaProber 探测并回填。
内部锁串行化 MediaProber 调用，避免 ffprobe 并发资源争抢。
"""

from __future__ import annotations

import threading
from pathlib import Path

from cx_studio.filesystem.file_info_cache import FileInfoCache

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
            cached_media = cached["media_info"]
            if cached_media is None:
                return None
            # 旧格式缓存（0.8.x）不含 top-level "raw" 字段 → 触发热重新探测
            if "raw" in cached_media:
                return MediaInfo.from_dict(cached_media)
            # fall through: 旧缓存降级，走重新探测并覆写

        with self._probe_lock:
            info = self._prober.probe(file)

        self.set(file, {"media_info": info.to_dict()})
        return info

    class FileBytesGetter:
        """文件大小获取闭包对象。

        绑定一个 MediaDB 实例，作为 FileList 的 sizer_function 注入。
        调用时从 MediaDB 缓存拉取文件大小（缓存命中读 file_size 字段），
        不触发 ffprobe 探测。缓存未命中或数据库未连接时回退到 stat()。

        与 MediaDB.get_media_info() 的区别：
        - get_media_info() 会触发 ffprobe 探测并回填缓存
        - FileBytesGetter 只读缓存，不探测——适合 sizer 热路径
        """

        def __init__(self, media_db: "MediaDB") -> None:
            """绑定 MediaDB 实例。

            Args:
                media_db: 要读取缓存的 MediaDB 实例
            """
            self._db = media_db

        def __call__(self, file: Path) -> int:
            """从缓存获取文件大小（字节），未命中时回退到 stat()。

            仅读取缓存，不触发 ffprobe 探测。

            Args:
                file: 文件路径

            Returns:
                文件字节大小；无法获取时返回 0
            """
            try:
                cached = self._db.get(file)
                if cached is not None and "media_info" in cached:
                    raw = cached["media_info"]
                    if raw is not None:
                        size = raw.get("file_size")
                        if size is not None:
                            return int(size)
            except RuntimeError:
                # 数据库未连接，回退到 stat()
                pass
            try:
                return file.stat().st_size
            except OSError:
                return 0

    def make_file_bytes_getter(self) -> "MediaDB.FileBytesGetter":
        """构造绑定本实例的 FileBytesGetter。

        Returns:
            FileBytesGetter 实例，可直接传给 FileList(sizer_function=...)
        """
        return MediaDB.FileBytesGetter(self)
