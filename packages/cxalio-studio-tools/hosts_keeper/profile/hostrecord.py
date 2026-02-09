from dataclasses import dataclass, field


@dataclass
class HostRecord:
    ip: str | None = None
    domains: list[str] = field(default_factory=list)
    comment: str | None = None

    def is_pure_comment(self) -> bool:
        """
        判断是否为注释行。
        """
        return (self.ip is None) and (self.comment is not None)

    def is_valid(self) -> bool:
        """
        判断是否为有效记录。
        """
        is_useful = (self.ip is not None) and self.domains
        return is_useful or self.is_pure_comment()

    @classmethod
    def from_line(cls, line: str) -> "HostRecord":
        """
        从 hosts 内容行创建 HostRecord 对象。
        """
        if not line:
            return cls()

        if line.startswith("#"):
            return cls(comment=line.removeprefix("#").strip())

        # TODO: 使用regex精细化解析
        ip, *domains = line.split()
        return cls(ip, domains)

    @classmethod
    def from_comment(cls, comment: str) -> "HostRecord":
        """
        创建注释记录。
        """
        return cls(comment=comment)

    def __str__(self) -> str:
        """
        将 HostRecord 对象转换为 hosts 内容行。
        """
        if not self.is_valid():
            return ""
        if self.is_pure_comment():
            return f"# {self.comment}"
        result = f"{self.ip}\t{' '.join(self.domains)}"
        if self.comment:
            result += f" #{self.comment}"
        return result
