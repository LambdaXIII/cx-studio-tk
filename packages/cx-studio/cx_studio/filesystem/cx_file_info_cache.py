# file_cache.py
# 遵循规则：初始化无批量操作 | 运行时仅单条校验 | 仅析构执行淘汰 | 线程安全 | 语义化API
import os
from pathlib import Path
import time
import json
import sqlite3
import threading

class FileInfoCache:
    def __init__(self,db_path: Path, max_size: int = -1):
        """初始化：仅连接数据库 + 创建表，无任何清理/淘汰"""
        self.max_size = max_size
        self.db_path = db_path.resolve().absolute()
        self.lock = threading.Lock()

        # 数据库连接
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

        # 创建缓存表
        with self.lock:
            self._sql("""
                CREATE TABLE IF NOT EXISTS file_cache (
                    file_abs_path TEXT PRIMARY KEY,
                    file_mtime REAL NOT NULL,
                    cache_last_access REAL NOT NULL,
                    user_data JSON NOT NULL
                )
            """, commit=True)

    # ====================== 私有工具方法 ======================
    def _get_abs_path(self, file_path: str|Path) -> str:
        """标准化绝对路径"""
        return os.path.realpath(os.path.expanduser(str(file_path)))

    def _sql(self, sql: str, params=(), commit: bool = False):
        """统一SQL执行（线程安全）"""
        self.cursor.execute(sql, params)
        if commit:
            self.conn.commit()
        return self.cursor

    def _validate(self, abs_path: str) -> bool:
        """运行时：仅校验单条缓存有效性，无效则删除"""
        if not os.path.exists(abs_path):
            self._sql("DELETE FROM file_cache WHERE file_abs_path = ?", (abs_path,), commit=True)
            return False

        current_mtime = os.path.getmtime(abs_path)
        res = self._sql("SELECT file_mtime FROM file_cache WHERE file_abs_path = ?", (abs_path,)).fetchone()
        if not res or res[0] != current_mtime:
            self._sql("DELETE FROM file_cache WHERE file_abs_path = ?", (abs_path,), commit=True)
            return False
        return True

    def _batch_clean_invalid(self):
        """【仅析构调用】批量清理无效缓存"""
        if self.max_size <= 0:
            return
        rows = self._sql("SELECT file_abs_path, file_mtime FROM file_cache").fetchall()
        invalid = [(p,) for p, m in rows if not os.path.exists(p) or os.path.getmtime(p) != m]
        if invalid:
            self._sql("DELETE FROM file_cache WHERE file_abs_path = ?", invalid, commit=True)

    def _lru_evict(self):
        """【仅析构调用】LRU 淘汰超量数据"""
        if self.max_size <= 0:
            return
        self._batch_clean_invalid()
        self._sql("""
            DELETE FROM file_cache
            WHERE file_abs_path IN (
                SELECT file_abs_path FROM file_cache
                ORDER BY cache_last_access ASC
                LIMIT MAX(0, (SELECT COUNT(*) FROM file_cache) - ?)
            )
        """, (self.max_size,), commit=True)

    def _update_timestamp(self, abs_path: str):
        """更新缓存记录访问时间"""
        self._sql("UPDATE file_cache SET cache_last_access = ? WHERE file_abs_path = ?",
                 (time.time(), abs_path), commit=True)

    def _get_record(self, abs_path: str) -> dict | None:
        """获取缓存记录（包含所有字段）"""
        res = self._sql("SELECT user_data FROM file_cache WHERE file_abs_path = ?", (abs_path,)).fetchone()
        return json.loads(res[0]) if res else None

    # ====================== 语义化公有 API ======================
    def get(self, file_path: str|Path, key: str):
        """【单个字段】获取值"""
        abs_path = self._get_abs_path(file_path)
        with self.lock:
            if not self._validate(abs_path):
                return None

            # 更新访问时间
            self._update_timestamp(abs_path)
            data = self._get_record(abs_path)
            return data.get(key)

    def get_fields(self, file_path: str|Path, *keys: str) -> dict :
        """【完整字典】获取所有缓存字段"""
        with self.lock:
            abs_path = self._get_abs_path(file_path)
            if not self._validate(abs_path):
                return {}

            self._update_timestamp(abs_path)
            data = self._get_record(abs_path)
            if not keys:
                return data
            return {k: data.get(k) for k in keys}

    def set(self, file_path: str|Path, key: str, value):
        """【单个字段】设置值（自动创建缓存）"""
        with self.lock:
            abs_path = self._get_abs_path(file_path)
            if not os.path.exists(abs_path):
                return

            # 读取现有数据或新建
            res = self._sql("SELECT user_data FROM file_cache WHERE file_abs_path = ?", (abs_path,)).fetchone()
            data = json.loads(res[0]) if res else {}
            data[key] = value

            # 写入数据库
            now = time.time()
            mtime = os.path.getmtime(abs_path)
            self._sql("""
                INSERT OR REPLACE INTO file_cache
                (file_abs_path, file_mtime, cache_last_access, user_data)
                VALUES (?, ?, ?, ?)
            """, (abs_path, mtime, now, json.dumps(data)), commit=True)

    def set_fields(self, file_path: str|Path, data: dict):
        """【完整字典】覆盖设置所有字段"""
        with self.lock:
            abs_path = self._get_abs_path(file_path)
            if not os.path.exists(abs_path):
                return

            now = time.time()
            mtime = os.path.getmtime(abs_path)
            self._sql("""
                INSERT OR REPLACE INTO file_cache
                (file_abs_path, file_mtime, cache_last_access, user_data)
                VALUES (?, ?, ?, ?)
            """, (abs_path, mtime, now, json.dumps(data)), commit=True)

    def update_fields(self, file_path: str|Path, **data):
        """【增量更新】仅更新指定字段，不覆盖其他"""
        with self.lock:
            abs_path = self._get_abs_path(file_path)
            if not os.path.exists(abs_path):
                return

            res = self._sql("SELECT user_data FROM file_cache WHERE file_abs_path = ?", (abs_path,)).fetchone()
            current_data = json.loads(res[0]) if res else {}
            current_data.update(data)

            now = time.time()
            mtime = os.path.getmtime(abs_path)
            self._sql("""
                INSERT OR REPLACE INTO file_cache
                (file_abs_path, file_mtime, cache_last_access, user_data)
                VALUES (?, ?, ?, ?)
            """, (abs_path, mtime, now, json.dumps(current_data)), commit=True)

    def delete(self, file_path: str|Path):
        """删除单条缓存"""
        with self.lock:
            abs_path = self._get_abs_path(file_path)
            self._sql("DELETE FROM file_cache WHERE file_abs_path = ?", (abs_path,), commit=True)

    def clear(self):
        """清空所有缓存"""
        with self.lock:
            self._sql("DELETE FROM file_cache", commit=True)

    def close(self):
        """关闭数据库连接"""
        with self.lock:
            if self.conn:
                self.conn.close()

    # ====================== 析构：唯一淘汰入口 ======================
    def __del__(self):
        try:
            with self.lock:
                self._lru_evict()
        finally:
            self.close()