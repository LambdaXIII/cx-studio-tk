"""输入解析器。

将命令行原始输入字符串解析为路径集合（输入侧第一环节）：
逐条解析路径（缺失且无扩展名的输入补全 `.toml`）、目录递归展开、
项目文件交 InspectorChain 解析其引用的媒体路径，最后按绝对路径查重并排序。
本环节不感知预设与源后缀，仅有的格式感知是 `.toml` 补全与项目文件类型识别。
"""

from __future__ import annotations

import os
from pathlib import Path

from cx_tools.app import SafeError
from media_killer.i18n import _
from media_scout.common.inspectors import InspectorChain
from media_scout.common.inspectors.filelist_inspector import FileListInspector
from media_scout.common.inspectors.inspector_info import InspectorInfo
from media_scout.common.inspectors import (
    EDLInspector,
    FCPXMLDInspector,
    FCPXMLInspector,
    LegacyXMLInspector,
    ResolveMetadataInspector,
)

# 项目文件扩展名集合
_PROJECT_FILE_EXTENSIONS: set[str] = {
    ".edl",  # EDL 剪辑决定表
    ".xml",  # FCP 7 XML
    ".fcpxml",  # FCPX XML
    ".fcpxmld",  # FCPX XML (目录)
    ".csv",  # DaVinci Resolve CSV
    ".txt",  # 纯文本路径列表
    ".ps1",  # PowerShell 脚本路径列表
    ".sh",  # Shell 脚本路径列表
}


class InputResolver:
    """输入解析器。

    将原始输入字符串解析为存在的、可读的、绝对的路径集合：
    1. 逐条解析：基于 CWD 解析为绝对路径；不存在且无扩展名时补全 `.toml`
       （命中须为文件）；仍不存在报错中止；带扩展名的缺失输入直接报错不补全
    2. 项目文件（见 `_PROJECT_FILE_EXTENSIONS`）交 InspectorChain 解析引用
    3. 目录递归展开为其中的全部文件（不做源后缀过滤）
    4. 结果按绝对路径查重并排序

    项目文件内部的相对引用基于项目文件自身所在目录解析；引用的媒体路径
    不存在时被静默跳过。本组件不感知预设与源后缀——后缀筛选属于资源提炼环节。
    """

    def resolve(self, *inputs: str) -> list[Path]:
        """解析原始输入，返回去重排序后的绝对路径集合。

        Args:
            inputs: 原始输入字符串（文件、目录或项目文件路径，可为相对路径）。

        Returns:
            list[Path]: 按平台路径序排序的绝对路径集合，查重按绝对路径执行。

        Raises:
            SafeError: 输入路径不存在（补全 `.toml` 后仍不存在）、输入路径
                不可读，或项目文件解析过程中抛出异常时。
        """
        collected: set[Path] = set()
        # 链状态不跨调用：每次 resolve 内以 with 使用，关闭链内去重，
        # 查重统一由集合层按绝对路径执行
        with InspectorChain(
            ResolveMetadataInspector(),
            EDLInspector(),
            LegacyXMLInspector(),
            FCPXMLInspector(),
            FCPXMLDInspector(),
            FileListInspector(".txt", ".ps1", ".sh"),
            allow_duplicated=True,
        ) as chain:
            for raw in inputs:
                path = self._resolve_input(raw)
                if path.is_file():
                    if path.suffix.lower() in _PROJECT_FILE_EXTENSIONS:
                        self._inspect_project_file(path, chain, collected)
                    else:
                        collected.add(path)
                elif path.is_dir():
                    collected.update(item for item in path.rglob("*") if item.is_file())
        return sorted(collected)

    @staticmethod
    def _resolve_input(raw: str) -> Path:
        """将单条原始输入解析为存在的可读绝对路径。

        Args:
            raw: 原始输入字符串，基于 CWD 解析。

        Returns:
            Path: 存在且可读的绝对路径；缺失且无扩展名的输入在补全
                `.toml`（命中须为文件）后返回其路径。

        Raises:
            SafeError: 路径不存在（补全后仍不存在）或不可读时。
        """
        path = Path(raw).resolve()
        if not path.exists() and path.suffix == "":
            candidate = path.with_suffix(".toml")
            if candidate.is_file():
                path = candidate
        if not path.exists():
            raise SafeError(_("输入路径不存在: {path}").format(path=raw))
        if not os.access(path, os.R_OK):
            raise SafeError(_("输入路径不可读: {path}").format(path=path))
        return path

    @staticmethod
    def _inspect_project_file(
        project_file: Path, chain: InspectorChain, collected: set[Path]
    ) -> None:
        """解析项目文件，将其引用的媒体路径加入集合。

        相对引用基于项目文件自身所在目录解析；不存在的引用静默跳过
        （项目文件可能引用未就绪的素材）。

        Args:
            project_file: 项目文件路径（绝对路径）。
            chain: 已组装的 Inspector 链。
            collected: 路径集合收集器（副作用写入）。

        Raises:
            SafeError: 项目文件解析过程中抛出异常时。
        """
        try:
            refs = list(chain.inspect(InspectorInfo(project_file)))
        except Exception as e:
            raise SafeError(
                _("解析项目文件 {path} 失败: {err}").format(path=project_file, err=e)
            ) from e
        for ref in refs:
            ref_path = Path(ref)
            # 项目文件内部的相对路径基于项目文件位置解析
            if not ref_path.is_absolute():
                ref_path = (project_file.parent / ref_path).resolve()
            if ref_path.exists():
                collected.add(ref_path)
