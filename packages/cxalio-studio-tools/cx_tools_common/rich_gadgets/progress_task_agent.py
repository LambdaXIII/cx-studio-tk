from rich.progress import Progress, TaskID
from cx_studio.utils import TextUtils
import asyncio


class ProgressTaskAgent:
    def __init__(self, progress: Progress | None = None, task_name: str | None = None):
        self._progress = progress
        self._task_name: str = task_name or TextUtils.random_string(5)
        self._task_id: TaskID | None = None

    @property
    def progress(self) -> Progress | None:
        return self._progress

    @property
    def task_name(self) -> str:
        return self._task_name

    @property
    def task_id(self) -> TaskID | None:
        return self._task_id

    async def __aenter__(self):
        if self._progress:
            self._task_id = self._progress.add_task(self._task_name)
        if self._progress and self._task_id:
            self._progress.update(self._task_id, visible=True)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._progress and self._task_id:
            self._progress.stop_task(self._task_id)
            self._progress.update(self._task_id, visible=False)
        self._task_id = None
        return False

    def __enter__(self):
        if self._progress:
            self._task_id = self._progress.add_task(self._task_name)
        if self._progress and self._task_id:
            self._progress.update(self._task_id, visible=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._progress and self._task_id:
            self._progress.stop_task(self._task_id)
            self._progress.update(self._task_id, visible=False)
        self._task_id = None
        return False

    def start(self):
        if self._progress and self._task_id:
            self._progress.start_task(self._task_id)

    def stop(self):
        if self._progress and self._task_id:
            self._progress.stop_task(self._task_id)

    def update(
        self,
        *args,
        total: float | None = None,
        completed: float | None = None,
        advance: float | None = None,
        description: str | None = None,
        visible: bool | None = None,
        refresh: bool = False,
        **fields: object,
    ):
        if self._progress and self._task_id:
            self._progress.update(
                self._task_id,
                *args,
                total=total,
                completed=completed,
                advance=advance,
                description=description,
                visible=visible,
                refresh=refresh,
                **fields,
            )

    def advance(self, advance: float = 1.0):
        if self._progress and self._task_id:
            self._progress.update(self._task_id, advance=advance)

    def set_total(self, total: float | None):
        if self._progress and self._task_id:
            self._progress.update(self._task_id, total=total)

    def set_description(self, description: str):
        if self._progress and self._task_id:
            self._progress.update(self._task_id, description=description)

    def set_completed(self, completed: float):
        if self._progress and self._task_id:
            self._progress.update(self._task_id, completed=completed)

    def set_progress(self, completed: float, total: float | None):
        if self._progress and self._task_id:
            self._progress.update(self._task_id, completed=completed, total=total)

    def show(self):
        if self._progress and self._task_id:
            self._progress.update(self._task_id, visible=True)

    def hide(self):
        if self._progress and self._task_id:
            self._progress.update(self._task_id, visible=False)

    def refresh(self):
        if self._progress and self._task_id:
            self._progress.update(self._task_id, refresh=True)
