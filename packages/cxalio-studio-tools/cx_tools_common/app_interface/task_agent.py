import threading
from dataclasses import dataclass, field

from rich.progress import Progress, TaskID


class TaskAgent:

    @dataclass
    class Data:
        task_name: str
        description: str = ""
        completed: float | None = 0
        total: float | None = None
        visible: bool = True
        fields: dict = field(default_factory=dict)

        def __post_init__(self):
            self.description = self.task_name

    def __init__(
        self,
        task_id: TaskID | None = None,
        task_name: str = "",
        total: float | None = None,
        refresh_interval: float = 0.01,
        progress: Progress | None = None,
        auto_update: bool = True,
    ):
        self._refresh_interval = refresh_interval
        self._progress = progress
        self._task_id: TaskID | None = task_id
        self.data = self.Data(
            task_name=task_name,
            total=total,
        )
        self._auto_update = auto_update
        self._lock = threading.Lock()

    def _update_progress(self):
        if self._progress and self._task_id:
            with self._lock:
                self._progress.update(
                    self._task_id,
                    total=self.data.total,
                    completed=self.data.completed,
                    description=self.data.description,
                    visible=self.data.visible,
                    **self.data.fields,
                )

    def update(
        self,
        task_name: str | None = None,
        description: str | None = None,
        completed: float | None = None,
        total: float | None = None,
        visible: bool | None = None,
        auto_update: bool | None = None,
        **fields,
    ):
        with self._lock:
            if task_name is not None:
                self.data.task_name = task_name
            if description is not None:
                self.data.description = description
            if completed is not None:
                self.data.completed = completed
            if total is not None:
                self.data.total = total
            if visible is not None:
                self.data.visible = visible
            if fields:
                self.data.fields.update(fields)
            if auto_update is not None:
                self._auto_update = auto_update

            if self._auto_update:
                self._update_progress()

    @property
    def task_name(self) -> str:
        return self.data.task_name

    @task_name.setter
    def task_name(self, value: str):
        self.update(task_name=value)

    @property
    def description(self) -> str:
        return self.data.description

    @description.setter
    def description(self, value: str):
        self.update(description=value)

    @property
    def completed(self) -> float | None:
        return self.data.completed

    @completed.setter
    def completed(self, value: float | None):
        self.update(completed=value)

    @property
    def total(self) -> float | None:
        return self.data.total

    @total.setter
    def total(self, value: float | None):
        self.update(total=value)

    @property
    def visible(self) -> bool:
        return self.data.visible

    @visible.setter
    def visible(self, value: bool):
        self.update(visible=value)

    def __getitem__(self, key):
        if hasattr(self.data, key):
            return getattr(self.data, key)
        else:
            return self.data.fields.get(key)

    def __setitem__(self, key, value):
        with self._lock:
            if hasattr(self.data, key):
                setattr(self.data, key, value)
            else:
                self.data.fields[key] = value
            self._update_progress()

    def start(self):
        if self._progress is None:
            return

        if self._task_id is None:
            self._task_id = self._progress.add_task(
                self.data.description,
                total=self.data.total,
                visible=self.data.visible,
                **self.data.fields,
            )

        self._progress.start_task(self._task_id)

    def stop(self, delete=False):
        if self._progress and self._task_id:
            self._progress.stop_task(self._task_id)
            if delete:
                self._progress.remove_task(self._task_id)
                self._task_id = None

    def show(self):
        with self._lock:
            self.data.visible = True
            if self._progress and self._task_id:
                self._progress.update(self._task_id, visible=True)

    def hide(self):
        with self._lock:
            self.data.visible = False
            if self._progress and self._task_id:
                self._progress.update(self._task_id, visible=False)

    def reset(self, start: bool = True):
        with self._lock:
            self.data.completed = 0
            self.data.description = self.data.task_name
            if self._progress and self._task_id:
                if self._timer:
                    self._timer.cancel()
                    self._timer = None
                self._progress.reset(
                    self._task_id,
                    start=start,
                    total=self.data.total,
                    completed=self.data.completed,
                    visible=self.data.visible,
                    description=self.data.description,
                    **self.data.fields,
                )

    def advance(self, value: float = 1):
        with self._lock:
            self.data.completed = (self.data.completed or 0) + value
            self._update_progress()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop(True)
        return False
