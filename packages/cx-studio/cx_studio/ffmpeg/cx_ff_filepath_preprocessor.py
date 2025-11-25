from typing import Iterable


class FFmpegArgumentsPreProcessor:
    """
    对FFmpeg命令行参数中的文件路径进行预处理
    """

    def __init__(self, *arguments) -> None:
        self._arguments = list(*arguments)

    def iter_input_files(self) -> Iterable[str]:
        """
        提取输入文件列表

        解析命令行参数，找到所有标记为输入的文件

        Yields:
            str: 输入文件路径
        """
        input_marked = False
        for a in self._arguments:
            if a == "-i":
                # 标记下一个参数为输入文件
                input_marked = True
            elif input_marked:
                # 当前参数是输入文件
                yield a
                input_marked = False

    def iter_output_files(self) -> Iterable[str]:
        """
        提取输出文件列表

        解析命令行参数，找到所有输出文件（不包括输入文件）

        Yields:
            str: 输出文件路径
        """
        prev_key = None
        for a in self._arguments:
            if a.startswith("-"):
                # 当前参数是选项键
                prev_key = a
                continue

            # 如果参数包含点号且不是输入参数，则认为是输出文件
            if "." in a and prev_key != "-i":
                yield a

    def iter_option_pairs(self) -> Iterable[tuple[str, str]]:
        """
        提取选项键值对

        解析命令行参数，找到所有选项键值对

        Yields:
            tuple[str, str]: 选项键值对 (键, 值)
        """
        prev_key = None
        for a in self._arguments:
            if a.startswith("-"):
                # 当前参数是选项键
                prev_key = a
                continue

            # 如果参数不包含点号且前一个参数是选项键，则认为是选项值
            if "." not in a and prev_key is not None:
                if prev_key.strip() == "-i":
                    # 忽略独立的选项值
                    continue
                yield (prev_key, a)
                prev_key = None
