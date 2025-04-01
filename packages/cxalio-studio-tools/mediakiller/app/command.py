import click
from cx_studio.utils.cx_pathutils import is_file_in_dir
import rich
from .application import app
from cx_studio.utils import PathUtils
from pathlib import Path


def generate_new_preset(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    print("NEW template.", value)
    ctx.exit()


def show_tutorial(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    print("tutorial")
    ctx.exit()


def setup_script_output(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    app.context.script_output = value


def _is_preset(p: Path) -> bool:
    if p.suffix.lower() == ".toml":
        return True
    if p.suffix == "":
        preset = PathUtils.force_suffix(p, ".toml")
        return Path(preset).exists()


def setup_sources_and_presets(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    for s in value:
        path = Path(s)
        if _is_preset(path):
            app.context.presets.append(path)
        else:
            app.context.sources.append(path)


def setup_continue_mode(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    app.context.continue_mode = value


def setup_pretending_mode(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    app.context.pretending_mode = value


def setup_debug_mode(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    app.context.debug = value


def setup_sort_mode(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    app.context.sort_mode = value


@click.command()
@click.option(
    "--generate",
    "--new",
    "-g",
    help="generate a template preset",
    callback=generate_new_preset,
    expose_value=False,
    is_eager=True,
)
@click.option(
    "--tutorial",
    "--full-help",
    help="Show full turotial.",
    is_flag=True,
    default=False,
    callback=show_tutorial,
    expose_value=False,
    is_eager=True,
)
@click.option(
    "--make-script",
    "-s",
    help="生成脚本文件",
    type=str,
    default=None,
    callback=setup_script_output,
    expose_value=False,
)
@click.option(
    "--sort",
    help="设置排序方式",
    type=click.Choice(["source", "preset", "targetdir", "x"]),
    default="x",
    expose_value=False,
    callback=setup_sort_mode,
)
@click.option(
    "--continue",
    "-c",
    help="继续上次的任务",
    is_flag=True,
    default=False,
    callback=setup_continue_mode,
    expose_value=False,
)
@click.option(
    "--pretend",
    "-p",
    help="假装执行任务",
    is_flag=True,
    default=False,
    callback=setup_pretending_mode,
    expose_value=False,
)
@click.option(
    "--debug",
    "-d",
    help="启动调试模式",
    is_flag=True,
    default=False,
    callback=setup_debug_mode,
    expose_value=False,
    is_eager=True,
)
@click.argument(
    "inputs", nargs=-1, callback=setup_sources_and_presets, expose_value=False
)
def command():
    app.start_app()
    app.logger.info("Application started.")
    app.logger.info(f"Context: {app.context}")
