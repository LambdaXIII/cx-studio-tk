"""Shell 命令行参数转义工具。

为生成 .bat / .sh 脚本时对单个参数进行平台特定的转义，
确保空格、特殊字符、变量名等不会在 shell 中被错误解析。
"""


def escape_arg(arg: str, *, batch: bool = False) -> str:
    """对单个命令行参数做平台 shell 转义。

    Args:
        arg: 待转义的参数值
        batch: ``True`` 使用 Windows Batch (.bat/.cmd) 规则，
               ``False``（默认）使用 POSIX Shell (.sh) 规则

    Returns:
        转义后的参数字符串，可直接嵌入脚本
    """
    if not arg:
        return '""' if batch else "''"
    if batch:
        if any(c in arg for c in ' \t"&|()<>^%'):
            escaped = arg.replace("%", "%%").replace('"', '""')
            return f'"{escaped}"'
        return arg
    else:
        if any(c in arg for c in " \t\"'$`\\!#&|;<>(){}[]?*~"):
            escaped = arg.replace("'", "'\\''")
            return f"'{escaped}'"
        return arg


def join_args(args: list[str], *, batch: bool = False) -> str:
    """将参数列表拼接为完整的 shell 命令行字符串。

    每个参数通过 :func:`escape_arg` 转义后，以空格连接。

    Args:
        args: 命令行参数列表（不含程序名）
        batch: 平台选择，同 :func:`escape_arg`

    Returns:
        空格分隔的完整命令行字符串
    """
    return " ".join(escape_arg(a, batch=batch) for a in args)
