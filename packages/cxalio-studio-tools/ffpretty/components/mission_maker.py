"""MissionMaker — 原始 FFmpeg 参数 → Mission 转换器。

独立于 Preset 体系的 Mission 构造器。media_killer 的 MissionMaker 依赖
Preset 模板和标签替换，ffpretty 不需要这些——直接从原始命令行参数构造。

覆盖策略由调用方通过 ``overwrite`` 参数传入，不在本模块中解析
``-y``/``-n`` 标志——它们已被 argparse 从参数列表中移除。
"""

from pathlib import Path

from cx_studio.ffmpeg import FFmpegArgumentsPreProcessor
from ..common import InputSpec, Mission, OutputSpec, options_from_flat

# -i 不从属于任何 input/output，构造选项列表时排除
# （-y/-n 已被 argparse 在 Application 层消费，不会出现在参数中）
_SKIP_ARGS: frozenset[str] = frozenset({"-i"})


def _find_last_input_end(arguments: list[str]) -> int:
    """返回最后一个 -i <file> 对的结束索引 + 1。无 -i 时返回 0。"""
    last_end = 0
    for i, a in enumerate(arguments):
        if a == "-i" and i + 1 < len(arguments):
            last_end = i + 2
    return last_end


class MissionMaker:
    """从原始 FFmpeg 命令行参数构造 Mission。

    不依赖 Preset，直接将参数按 input/output 段分拆为 InputSpec/OutputSpec。
    """

    def __init__(self, ffmpeg_executable: str):
        self._ffmpeg_executable = ffmpeg_executable

    def make(self, arguments: list[str], overwrite: bool = False) -> Mission:
        """从原始参数构造 Mission。

        Args:
            arguments: 命令行参数列表（不含程序名，已由 Application 层
                从 argparse.parse_known_args() 的 unknowns 中取出，
                不再含 -y/-n 等消费过的标志）
            overwrite: 是否覆盖已存在的目标文件

        Returns:
            Mission 值对象
        """
        processor = FFmpegArgumentsPreProcessor(*arguments)
        input_files = list(processor.iter_input_files())
        output_files = list(processor.iter_output_files())

        # 用于识别 output 文件名（任何参数值等于某输出文件的应被排除）
        output_names: set[str] = set(output_files)

        # 分割点：最后一个 -i 之后的所有 args 归入 output 段
        split_idx = _find_last_input_end(arguments)
        # 前段收集不属于 input 的 global options
        global_opts: list[str] = []
        input_opts: list[list[str]] = [[] for _ in input_files]
        output_opts: list[str] = []

        cur_input_idx = 0
        i = 0
        while i < split_idx:
            a = arguments[i]
            if a == "-i" and i + 1 < len(arguments):
                # -i <file> — 归入 input，跳过
                i += 2
                cur_input_idx += 1
                continue
            if a not in _SKIP_ARGS:
                if cur_input_idx > 0 and cur_input_idx <= len(input_files):
                    # 在某个 -i 之后、下一个 -i 之前 → 属于该 input 的 options
                    input_opts[cur_input_idx - 1].append(a)
                else:
                    global_opts.append(a)
            i += 1

        # 后段：output 段的所有非 -i 参数（排除 output 文件名本身）
        j = split_idx
        while j < len(arguments):
            a = arguments[j]
            if a == "-i" and j + 1 < len(arguments):
                j += 2
                continue
            if a not in _SKIP_ARGS and a not in output_names:
                output_opts.append(a)
            j += 1

        # 构造 InputSpec / OutputSpec
        inputs = (
            [
                InputSpec(filename=Path(f), options=options_from_flat(opts))
                for f, opts in zip(input_files, input_opts)
            ]
            if input_files
            else []
        )

        outputs = [
            OutputSpec(filename=Path(f), options=options_from_flat(output_opts))
            for f in output_files
        ]

        source = inputs[0].filename if inputs else Path(".")
        standard_target = outputs[0].filename if outputs else source

        return Mission(
            ffmpeg=self._ffmpeg_executable,
            source=source,
            standard_target=standard_target,
            overwrite=overwrite,
            options=options_from_flat(global_opts),
            inputs=inputs,
            outputs=outputs,
        )
