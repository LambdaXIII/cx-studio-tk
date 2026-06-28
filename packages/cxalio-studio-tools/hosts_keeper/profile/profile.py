import asyncio
import importlib.resources
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncGenerator, Self, Sequence
from collections.abc import Generator

from box import Box, BoxList

from cx_studio.filesystem import force_suffix
from .contenter_base import ContenterBase, AbstractContenter
from .hostrecord import HostRecord


@dataclass(frozen=True)
class Profile:

    id: str = ""
    name: str = ""
    description: str = ""
    priority: int = 0
    enabled: bool = True
    path: Path = field(default_factory=Path)

    metadata: Box = field(default_factory=Box)
    packages: Box = field(default_factory=Box)

    @classmethod
    def load(cls, filename: Path | str) -> Self | None:
        filename = force_suffix(filename, ".toml")
        with open(filename, "rb") as f:
            toml_data = tomllib.load(f)
        data = Box(toml_data)

        metadata = data.get("hosts_profile")
        if not metadata:
            return None

        packages_data = data.copy()
        packages_data.pop("hosts_profile")

        return cls(
            id=metadata.profile_id,  # type: ignore
            name=metadata.profile_name,  # type: ignore
            description=metadata.description,  # type: ignore
            path=Path(filename).resolve(),
            priority=metadata.priority,  # type: ignore
            enabled=metadata.enabled,  # type: ignore
            metadata=metadata,  # type: ignore
            packages=packages_data,  # type: ignore
        )

    @staticmethod
    def create(profile_id: str, target: Path) -> Path:
        target = force_suffix(target, ".toml")
        target.parent.mkdir(parents=True, exist_ok=True)

        assert __package__ is not None, "Profile must be imported as part of a package"
        example = importlib.resources.read_text(__package__, "example_profile.toml")
        example = example.replace("example-id", profile_id)

        with open(target, "w", encoding="utf-8") as f:
            f.write(example)

        return target

    @property
    def profile_start_marker(self) -> str:
        """配置文件开始标记"""
        return f"##### {self.id} START #####"

    PROFILE_START_MARKER_PATTERN = r"#####\s+(.+)\s+START\s+#####"

    @property
    def profile_end_marker(self) -> str:
        """配置文件结束标记"""
        return f"##### {self.id} END #####"

    PROFILE_END_MARKER_PATTERN = r"#####\s+(.+)\s+END\s+#####"

    async def async_iter_records(self) -> AsyncGenerator[HostRecord, None]:
        """迭代记录"""

        async def expand_contenter(_contenter: AbstractContenter):
            result = []
            async for record in _contenter.iter_records():  # type: ignore[attr-defined]  # pyright 对抽象 async generator 类型推断限制
                result.append(record)
            return result

        tasks = []

        for schema, packages in self.packages.items():
            if not isinstance(packages, list | BoxList):
                packages = [packages]
            for package in packages:
                contenter = ContenterBase.create_contenter(
                    schema, package, self.metadata
                )
                if contenter is None:
                    continue
                tasks.append(asyncio.create_task(expand_contenter(contenter)))

        async for task in asyncio.as_completed(tasks):  # type: ignore[arg-type]  # pyright 对 AsyncIterator 类型推断限制
            result = await task
            for record in result:
                yield record

    async def async_iter_lines(
        self, include_markers: bool = True
    ) -> AsyncGenerator[str, None]:
        """迭代行"""
        if include_markers:
            yield ""
            yield self.profile_start_marker
        async for record in self.async_iter_records():
            yield str(record)
        if include_markers:
            yield self.profile_end_marker
            yield ""

    def __rich_label__(self) -> Generator[str, None, None]:
        enabled = "✅" if self.enabled else "❌"
        yield enabled
        yield self.id

    def __rich_repr__(self):
        # yield "id", self.id
        yield "name", self.name
        yield "description", self.description
        yield "priority", self.priority
        yield "enabled", self.enabled
        yield "path", self.path
        for k, v in self.packages.items():
            if isinstance(v, Sequence):
                for i in range(len(v)):
                    yield f"{k} {i}", v[i]
            else:
                yield k, v
