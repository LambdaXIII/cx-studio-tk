"""轻量文件条目缓存，基于 SQLite 持久化。

设计要点：
- 初始化仅保存配置，connect() 建立连接，close() 执行淘汰后关闭。
- 基于文件 mtime 自动失效。
- LRU 淘汰在 close()/cleanup() 时触发。
- threading.Lock 保证线程安全。
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path


class FileInfoCache:
    """基于 SQLite 的文件条目缓存。

    缓存以文件规范化绝对路径为 key，存储 user_data（JSON 序列化的 dict）
    以及文件的 mtime 用于失效判断。LRU 淘汰在 close()/cleanup() 时执行。
    """

    _CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS file_cache (
            path        TEXT PRIMARY KEY,
            mtime       REAL NOT NULL,
            last_access REAL NOT NULL,
            user_data   TEXT NOT NULL
        )
    """

    def __init__(self, db_path: Path, max_size: int = -1) -> None:
        """保存配置，不立即连接数据库。

        Args:
            db_path: SQLite 数据库文件路径。
            max_size: 最大缓存条目数。<=0 表示不限制。
        """
        self._db_path = db_path
        self._max_size = max_size
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None

    # ====================== 生命周期 ======================

    def connect(self) -> None:
        """建立 SQLite 连接并创建表结构。

        重复调用会先关闭旧连接再重新建立。
        """
        with self._lock:
            if self._conn is not None:
                self._conn.close()
            resolved = self._db_path.resolve()
            self._conn = sqlite3.connect(str(resolved), check_same_thread=False)
            self._conn.execute(self._CREATE_TABLE_SQL)
            self._conn.commit()

    def close(self) -> None:
        """执行淘汰清理，然后关闭连接。"""
        self.cleanup()
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def cleanup(self) -> None:
        """执行 LRU 淘汰清理。

        当 max_size > 0 且缓存条目数超过限制时，按 last_access 升序
        删除最久未使用的条目。可被手动调用，也会被 close() 自动调用。
        """
        if self._max_size <= 0:
            return
        with self._lock:
            conn = self._ensure_conn()
            conn.execute(
                """
                DELETE FROM file_cache
                WHERE path IN (
                    SELECT path FROM file_cache
                    ORDER BY last_access ASC
                    LIMIT MAX(0, (SELECT COUNT(*) FROM file_cache) - ?)
                )
                """,
                (self._max_size,),
            )
            conn.commit()

    # ====================== 公开 API ======================

    def get(self, file_path: Path) -> dict | None:
        """读取 user_data。

        若缓存不存在或文件 mtime 已变化，返回 None。
        命中时自动更新 last_access 时间戳。

        Args:
            file_path: 目标文件路径。

        Returns:
            缓存的 user_data dict，或 None（未命中/已失效）。
        """
        record = self._get_record(file_path)
        if record is None:
            return None
        return json.loads(record["user_data"])

    def set(self, file_path: Path, data: dict) -> None:
        """写入 user_data，同时记录当前文件 mtime。

        Args:
            file_path: 目标文件路径。
            data: 要缓存的字典数据。
        """
        key = str(file_path.resolve())
        now = time.time()
        mtime = os.path.getmtime(file_path)
        record = {
            "mtime": mtime,
            "last_access": now,
            "user_data": json.dumps(data),
        }
        self._set_record(file_path, record)

    def invalidate(self, file_path: Path) -> None:
        """删除指定文件的缓存条目。

        Args:
            file_path: 目标文件路径。
        """
        key = str(file_path.resolve())
        with self._lock:
            conn = self._ensure_conn()
            conn.execute("DELETE FROM file_cache WHERE path = ?", (key,))
            conn.commit()

    # ====================== 内部方法 ======================

    def _get_record(self, file_path: Path) -> dict | None:
        """在锁保护下读取完整记录。

        读取时检查 mtime 一致性：若文件不存在或 mtime 不匹配，
        自动删除失效条目并返回 None。命中时更新 last_access。

        Args:
            file_path: 目标文件路径。

        Returns:
            包含 mtime、last_access、user_data 的 dict，或 None。
        """
        key = str(file_path.resolve())
        with self._lock:
            conn = self._ensure_conn()
            row = conn.execute(
                "SELECT mtime, last_access, user_data FROM file_cache WHERE path = ?",
                (key,),
            ).fetchone()
            if row is None:
                return None

            cached_mtime = row[0]
            # 检查文件是否存在且 mtime 一致
            try:
                current_mtime = os.path.getmtime(file_path)
            except OSError:
                # 文件已不存在，删除失效条目
                conn.execute("DELETE FROM file_cache WHERE path = ?", (key,))
                conn.commit()
                return None

            if current_mtime != cached_mtime:
                # mtime 变化，删除失效条目
                conn.execute("DELETE FROM file_cache WHERE path = ?", (key,))
                conn.commit()
                return None

            # 命中：更新 last_access
            now = time.time()
            conn.execute(
                "UPDATE file_cache SET last_access = ? WHERE path = ?",
                (now, key),
            )
            conn.commit()
            return {
                "mtime": row[0],
                "last_access": now,
                "user_data": row[2],
            }

    def _set_record(self, file_path: Path, record: dict) -> None:
        """在锁保护下写入完整记录。

        使用 INSERT OR REPLACE 实现 upsert 语义。

        Args:
            file_path: 目标文件路径。
            record: 包含 mtime、last_access、user_data 的 dict。
        """
        key = str(file_path.resolve())
        with self._lock:
            conn = self._ensure_conn()
            conn.execute(
                """
                INSERT OR REPLACE INTO file_cache (path, mtime, last_access, user_data)
                VALUES (?, ?, ?, ?)
                """,
                (key, record["mtime"], record["last_access"], record["user_data"]),
            )
            conn.commit()

    # ====================== 上下文管理器 ======================

    def __enter__(self) -> FileInfoCache:
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ====================== 内部工具 ======================

    def _ensure_conn(self) -> sqlite3.Connection:
        """确保连接可用（调用方须已持有锁）。

        Returns:
            当前活跃的 sqlite3.Connection。

        Raises:
            RuntimeError: 连接尚未建立。
        """
        if self._conn is None:
            raise RuntimeError(
                "数据库连接尚未建立，请先调用 connect() 或使用上下文管理器"
            )
        return self._conn
