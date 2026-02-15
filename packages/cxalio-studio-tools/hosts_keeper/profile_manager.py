from .profile import Profile
from pathlib import Path
from .appenv import appenv
from cx_studio.filesystem import force_suffix
from collections.abc import Iterable
import fnmatch


class ProfileManager:
    # _FINDER = SuffixFinder(".toml")

    def __init__(self, profile_dir: Path | None = None):
        self.profile_dir = (
            profile_dir.resolve() if profile_dir else appenv.config_manager.config_dir
        )
        self.__profiles: dict[str, Profile] = {}
        self.__needs_refresh: bool = True

    def __find_profiles(self) -> Iterable[Path]:
        yield from self.profile_dir.glob("**/*.toml")

    @property
    def profiles(self) -> dict[str, Profile]:
        if self.__needs_refresh:
            self.__profiles.clear()
            for filename in self.__find_profiles():
                profile = Profile.load(filename)
                if profile is None:
                    appenv.whisper(f"[cx.error]{filename} 为非法配置文件，已跳过。")
                    continue
                if profile.id in self.__profiles:
                    old_profile = self.__profiles[profile.id]
                    appenv.whisper(
                        f"[cx.warning]配置文件 {profile.id} 已经由 {old_profile.path.name} 提供，将被 {profile.path.name} 覆盖。"
                    )
                self.__profiles[profile.id] = profile
            self.__needs_refresh = False
        return self.__profiles

    @property
    def enabled_profiles(self) -> Iterable[Profile]:
        for profile in self.profiles.values():
            if profile.enabled:
                yield profile

    @property
    def disabled_profiles(self) -> Iterable[Profile]:
        for profile in self.profiles.values():
            if not profile.enabled:
                yield profile

    @property
    def all_profiles(self) -> Iterable[Profile]:
        yield from self.profiles.values()

    def find_profile(self, search_pattern: str | None = None) -> Iterable[Profile]:
        for profile in self.all_profiles:
            if (
                not search_pattern
                or fnmatch.fnmatch(profile.id, search_pattern)
                or fnmatch.fnmatch(profile.name, search_pattern)
                or fnmatch.fnmatch(profile.description, search_pattern)
                or fnmatch.fnmatch(profile.path.name, search_pattern)
            ):
                yield profile

    def generate_profile_path(self, profile_id: str) -> Path:
        return self.profile_dir / Path(force_suffix(profile_id, ".toml"))

    def create_profile(self, profile_id: str, path: Path | None = None) -> Path | None:
        filename = path or self.generate_profile_path(profile_id)
        if filename.exists():
            return None
        Profile.create(profile_id, filename)
        self.__needs_refresh = True
        return filename
