import threading
from collections import defaultdict
from copy import copy
from typing import Hashable

from rich.progress import TaskID


class MultiProgressManager:

    class Status:
        description: str = ""
        total: float | None = None
        completed: float = 0
        visible: bool = False

    def __init__(self):
        self.lock = threading.RLock()
        self.tasks: dict[Hashable, TaskID] = {}
        self.datas: dict[Hashable, MultiProgressManager.Status] = defaultdict(
            lambda: MultiProgressManager.Status()
        )

    def add_task(self, key: Hashable, task_id: TaskID):
        with self.lock:
            self.tasks[key] = task_id

    def update_task(
        self,
        key: Hashable,
        description: str | None = None,
        total: float | None = None,
        completed: float | None = None,
        visible: bool | None = None,
    ):
        with self.lock:
            if description is not None:
                self.datas[key].description = description
            if total is not None:
                self.datas[key].total = total
            if completed is not None:
                self.datas[key].completed = completed
            if visible is not None:
                self.datas[key].visible = visible

    def get(self, key: Hashable) -> tuple[TaskID | None, "MultiProgressManager.Status"]:
        with self.lock:
            return self.tasks.get(key), copy(self.datas[key])

    def get_total_progress(self) -> tuple[float, float]:
        with self.lock:
            total = sum(self.datas[x].total or 0 for x in self.tasks.keys())
            completed = sum(self.datas[x].completed or 0 for x in self.tasks.keys())
            return float(completed), float(total)

    def advance(self, key: Hashable, advance: float = 1):
        with self.lock:
            self.datas[key].completed = (self.datas[key].completed or 0) + advance

    def __len__(self):
        with self.lock:
            return len(self.tasks)

    def keys(self):
        with self.lock:
            return self.tasks.keys()

    def task_ids(self):
        with self.lock:
            return self.tasks.values()
