import threading
from rich.progress import Progress, TaskID
from rich.text import Text
from dataclasses import dataclass, field


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
        task_name: str,
        total: float | None = None,
        refresh_interval: float = 0.01,
        progress: Progress | None = None,
    ):
        self._refresh_interval = refresh_interval
        self._progress = progress
        self._task_id: TaskID | None = None
        self._data = self.Data(
            task_name=task_name,
            total=total,
        )
        self._lock = threading.Lock()
        self._timer = None

    def __del__(self):
        if self._timer:
            self._timer.cancel()

    def _update_progress(self):
        if self._progress and self._task_id:
            with self._lock:
                self._progress.update(
                    self._task_id,
                    total=self._data.total,
                    completed=self._data.completed,
                    description=self._data.description,
                    visible=self._data.visible,
                    **self._data.fields,
                )
                self._timer = None

    def _start_timer(self):
        if self._refresh_interval <= 0:
            self._update_progress()
        elif self._timer is None:
            self._timer = threading.Timer(self._refresh_interval, self._update_progress)

    def update(
        self,
        task_name: str | None = None,
        description: str | None = None,
        completed: float | None = None,
        total: float | None = None,
        visible: bool | None = None,
        **fields,
    ):
        with self._lock:
            if task_name is not None:
                self._data.task_name = task_name
            if description is not None:
                self._data.description = description
            if completed is not None:
                self._data.completed = completed
            if total is not None:
                self._data.total = total
            if visible is not None:
                self._data.visible = visible
            if fields:
                self._data.fields.update(fields)
        self._start_timer()

    @property
    def task_name(self) -> str:
        return self._data.task_name

    @task_name.setter
    def task_name(self, value: str):
        self.update(task_name=value)

    @property
    def description(self) -> str:
        return self._data.description

    @description.setter
    def description(self, value: str):
        self.update(description=value)

    @property
    def completed(self) -> float | None:
        return self._data.completed

    @completed.setter
    def completed(self, value: float | None):
        self.update(completed=value)

    @property
    def total(self) -> float | None:
        return self._data.total

    @total.setter
    def total(self, value: float | None):
        self.update(total=value)

    @property
    def visible(self) -> bool:
        return self._data.visible

    @visible.setter
    def visible(self, value: bool):
        self.update(visible=value)

    def __getitem__(self, key):
        if hasattr(self._data, key):
            return getattr(self._data, key)
        else:
            return self._data.fields.get(key)

    def __setitem__(self, key, value):
        with self._lock:
            if hasattr(self._data, key):
                setattr(self._data, key, value)
            else:
                self._data.fields[key] = value
            self._start_timer()

    def start(self):
        if self._progress is None:
            return

        if self._task_id is None:
            self._task_id = self._progress.add_task(
                self._data.description,
                total=self._data.total,
                visible=self._data.visible,
                **self._data.fields,
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
            self._data.visible = True
            if self._progress and self._task_id:
                self._progress.update(self._task_id, visible=True)

    def hide(self):
        with self._lock:
            self._data.visible = False
            if self._progress and self._task_id:
                self._progress.update(self._task_id, visible=False)

    def reset(self, start: bool = True):
        with self._lock:
            self._data.completed = 0
            self._data.description = self._data.task_name
            if self._progress and self._task_id:
                if self._timer:
                    self._timer.cancel()
                    self._timer = None
                self._progress.reset(
                    self._task_id,
                    start=start,
                    total=self._data.total,
                    completed=self._data.completed,
                    visible=self._data.visible,
                    description=self._data.description,
                    **self._data.fields,
                )

    def advance(self, value: float = 1):
        with self._lock:
            self._data.completed = (self._data.completed or 0) + value
        self._start_timer()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop(True)
        return False
