from cx_studio.core import DataPackage
from cx_studio.tag_replacer import TagReplacer


class ValueReader:
    def __init__(self,data:DataPackage):
        self.data = data
        self.replacer = TagReplacer()

    @staticmethod
    def __force_list(value):
        if isinstance(value,list):
            return value
        else:
            return str(value).split(" ")

    def provide_preset_info(self,param:str) -> str|None:
        param = str(param).split(" ")[0]
        if not self.data.general:
            return None
        match(param):
            case "id":
                return self.data.general.preset_id
            case "name":
                return self.data.general.name
            case "description":
                return self.data.general.description
            case "ffmpeg":
                return self.data.general.ffmpeg
        return None

    def provide_custom_info(self,param:str) -> str|None:
        param = str(param).split(" ")[0]
        if not self.data.custom:
            return None
        return self.data.custom[param]


