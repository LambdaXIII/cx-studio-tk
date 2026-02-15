# Change logs of cx-studio

### v0.7.0
 - 拆分了utils，进行了大量模块层级改动

### v0.6.3
 - 为 SystemUtils 增加了迭代检查文件权限的方法。

### v0.6.1
 - 增加了 SystemUtils.flush_dns_cache 方法。

### v0.6.0
 - 在 cx_studio.utils 中增加了一个 SystemUtils 模块，提供一些判断操作系统和运行环境的方法。
 - 为 path_expander 中添加了一个 SuffixFinder 类，用于快速根据扩展名搜索文件。
 - 修改了 FunctionalUtils.flatten_list 方法的实现。

### v0.5.2
 - 修复了 FFmpeg 命令行参数预处理的问题。

### v0.5.1.5
 - 增加了 FFmpegArgumentsPreProcessor 类，用于预处理 FFmpeg 命令行参数。

### v0.2.1.9

- 为 PathUtils 增加了一个 ensure_parents 方法，用于自动创建文件夹。

### v0.2.1.8

- hotfix: pathexpander 的 macos 兼容性问题

### v0.2.1.7

- 应用 pydantic

### v0.2.1.6

- 删除了没用的文件
- 重新整理的代码格式

### v0.2.1.5

- FFmpeg 同步版本已经可以使用了

### v0.2.1.4

- PathUtils.quote now supports `escape` mode.
- Rewrite ffmpeg(thread safe version).

### v0.2.1.3

- rewrite DataPackage with proper annotations.
- `DataPackage` now supports index of list as key.
