"""Preset 数据模型。

Preset 是 media_killer 的私有概念，表示转码配置模板。
加载时进行结构和标签 lint，生成 Mission 后退役。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator

from media_killer.i18n import _
from cx_studio import text as tt
from cx_studio.filesystem import PathUtils

# 默认支持的源文件后缀集合
DEFAULT_SUFFIXES: set[str] = {
    # 视频容器
    ".mov",
    ".mp4",
    ".mkv",
    ".avi",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".ts",
    ".m2ts",
    ".m2t",
    ".mts",
    ".m2v",
    ".vob",
    ".3gp",
    ".3g2",
    ".f4v",
    ".ogv",
    ".ogg",
    ".mpg",
    ".mpeg",
    ".mxf",
    ".asf",
    ".rm",
    ".rmvb",
    ".divx",
    ".xvid",
    # 视频编码
    ".h264",
    ".h265",
    ".hevc",
    ".vp8",
    ".vp9",
    ".av1",
    ".avc",
    ".avchd",
    # 音频容器
    ".flac",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".ogg",
    ".wma",
    ".flac",
    ".alac",
    ".aiff",
    ".ape",
    ".dsd",
    ".pcm",
    ".ac3",
    ".dts",
    ".eac3",
    ".mp2",
    ".mpa",
    ".opus",
    ".mka",
    ".mkv",
    ".webm",
    ".flv",
    ".ts",
    ".m2ts",
    ".m2t",
    ".mts",
    ".m2v",
    ".m4v",
    ".vob",
    # 音频编码
    ".wav",
    ".m4a",
    ".aac",
    ".ogg",
    ".wma",
    ".flac",
    ".aiff",
    ".ape",
    ".dsd",
    ".pcm",
    ".ac3",
    ".dts",
    ".eac3",
    ".mp2",
    ".mpa",
    ".opus",
    ".mka",
    ".mxf_op1a",
}


@dataclass(frozen=True)
class InputTemplate:
    """输入文件模板。

    Attributes:
        filename: 模板字符串，可包含标签占位符
        options: 专属该输入的 FFmpeg 选项列表
    """

    filename: str
    options: list[str]

    def __rich_detail__(self) -> Generator[tuple[str, Any], None, None]:
        """详情面板渲染，展示输入模板字段。"""
        yield _("文件名模板"), self.filename
        yield _("选项"), " ".join(self.options) if self.options else _("无")


@dataclass(frozen=True)
class OutputTemplate:
    """输出文件模板。

    Attributes:
        filename: 模板字符串，可包含标签占位符
        options: 专属该输出的 FFmpeg 选项列表
    """

    filename: str
    options: list[str]

    def __rich_detail__(self) -> Generator[tuple[str, Any], None, None]:
        """详情面板渲染，展示输出模板字段。"""
        yield _("文件名模板"), self.filename
        yield _("选项"), " ".join(self.options) if self.options else _("无")


@dataclass(frozen=True)
class Preset:
    """转码预设配置。

    Preset 是强类型 frozen dataclass，表示从 TOML 文件加载的转码配置。
    加载时进行结构和标签 lint，生成 Mission 后退役，不进入共享底座。

    Attributes:
        id: 预设唯一标识符
        name: 预设显示名称
        description: 预设描述
        path: 预设文件的绝对路径
        ffmpeg: FFmpeg 可执行文件路径或名称
        overwrite: 是否覆盖已存在的目标文件
        options: 全局 FFmpeg 选项（适用于所有输入输出）
        source_suffixes: 源文件后缀过滤集合
        target_suffix: 目标文件后缀
        target_folder: 目标文件夹路径
        keep_parent_level: 保留父目录层级数
        inputs: 输入文件模板列表
        outputs: 输出文件模板列表
        custom: 自定义键值对，透传给标签替换器
    """

    id: str
    name: str
    description: str
    path: Path
    ffmpeg: str = "ffmpeg"
    overwrite: bool = False
    options: str | list[str] = ""
    source_suffixes: set[str] = field(default_factory=set)
    target_suffix: str = ""
    target_folder: Path = Path(".")
    keep_parent_level: int = 0
    inputs: list[InputTemplate] = field(default_factory=list)
    outputs: list[OutputTemplate] = field(default_factory=list)
    custom: dict[str, Any] = field(default_factory=dict)

    def __eq__(self, value: object) -> bool:
        """基于 (id, path) 判断相等，用于去重和集合操作。"""
        if not isinstance(value, Preset):
            return False
        return self.id == value.id and self.path == value.path

    def __hash__(self) -> int:
        """基于 (id, path) 计算哈希，用于去重和集合操作。"""
        return hash((self.id, self.path))

    def __rich_label__(self) -> Generator[str, None, None]:
        """紧凑标签渲染，用于列表行标题。

        格式：P [inputs->outputs] name description (path)
        """
        yield "[cx.debug]P[/]"
        yield f"[cx.whisper][{len(self.inputs)}->{len(self.outputs)}][/]"
        yield f"[cx.mk.mission.name]{self.name}[/]"
        if self.description:
            yield f"[cx.whisper]{self.description}[/]"
        yield f"[cx.debug]({self.path})[/]"

    def __rich_detail__(self) -> Generator[tuple[str, Any], None, None]:
        """详情面板渲染，展示完整 Preset 信息。

        yield (key, value) 二元组，渲染为两列表格。
        """
        yield _("ID"), self.id
        yield _("预设名称"), self.name
        yield _("预设描述"), self.description
        yield _("预设文件路径"), str(self.path)
        yield _("FFmpeg 路径"), self.ffmpeg
        yield _("是否覆盖"), str(self.overwrite)
        yield _("全局参数"), self.options
        yield _("源文件扩展名"), ", ".join(sorted(self.source_suffixes))
        yield _("目标文件扩展名"), self.target_suffix
        yield _("目标文件夹"), str(self.target_folder)
        yield _("保留父级层级"), str(self.keep_parent_level)
        yield _("输入模板"), self.inputs
        yield _("输出模板"), self.outputs
        yield _("自定义参数"), self.custom

    @staticmethod
    def compute_source_suffixes(
        ignore_default_suffixes: bool,
        suffix_includes: str | list[str],
        suffix_excludes: str | list[str],
    ) -> set[str]:
        """计算最终的源文件后缀集合。

        根据 ignore_default_suffixes 决定是否包含默认后缀，
        然后解析 includes 和 excludes，最终集合 = 默认 | 包含 - 排除。

        Args:
            ignore_default_suffixes: 是否忽略默认后缀集合
            suffix_includes: 需要包含的后缀（字符串或列表）
            suffix_excludes: 需要排除的后缀（字符串或列表）

        Returns:
            最终的源文件后缀集合
        """
        default_suffixes = set() if ignore_default_suffixes else DEFAULT_SUFFIXES

        includes = {
            PathUtils.normalize_suffix(s) for s in tt.auto_list_text(suffix_includes)
        }
        excludes = {
            PathUtils.normalize_suffix(s) for s in tt.auto_list_text(suffix_excludes)
        }

        return default_suffixes | includes - excludes
