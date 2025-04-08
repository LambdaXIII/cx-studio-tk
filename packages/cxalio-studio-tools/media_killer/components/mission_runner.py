from .mission import Mission
from .preset import Preset
from media_killer.appenv import appenv
from cx_studio.ffmpeg import FFmpeg, FFmpegProcessInfo, FFmpegCodingInfo


class MissionRunner:
    def __init__(self, mission: Mission) -> None:
        self._mission = mission

    @property
    def mission(self) -> Mission:
        return self._mission

    @property
    def preset(self) -> Preset:
        return self._mission.preset

    def run(self) -> bool:
        ffmpeg = FFmpeg()

        @ffmpeg.on("started")
        def on_started(process_info: FFmpegProcessInfo) -> None:
            appenv.say(f"Started: {process_info.bin} {process_info.args}")

        @ffmpeg.on("progress_updated")
        def on_progress_updated(
            process_info: FFmpegProcessInfo, coding_info: FFmpegCodingInfo
        ) -> None:
            c = coding_info.current_time.total_seconds
            t = (
                process_info.media_duration.total_seconds
                if process_info.media_duration is not None
                else "N/A"
            )
            appenv.say(f"{c}/{t}")

        @ffmpeg.on("finished")
        def on_finished(process_info: FFmpegProcessInfo) -> None:
            appenv.say(
                f"Finished: {process_info.bin} {process_info.args}, took time: {process_info.time_took}"
            )

        result = ffmpeg.run(self._mission.iter_arguments())
        return result
