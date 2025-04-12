from cx_studio.utils import NumberUtils

class JobCounter:
    def __init__(self,max_value:int,start:int=0) -> None:
        self.total:int = max_value
        self._current:int = start

    @property
    def current(self) -> int:
        if self._current > self.total:
            return self.total
        if self._current < 0:
            return 0
        return self._current
    
    @current.setter
    def current(self,value:int):
        self._current = int(NumberUtils.limit_number(value,bottom=0,top=self.total))

    def increase(self,value:int=1):
        self._current += value

    def decrease(self,value:int=1):
        self._current -= value

    def format(self,format_str:str=r"{current}/{total}") -> str:
        total_digits = len(str(self.total))
        current_str = str(self.current).rjust(total_digits," ")
        total_str = str(self.total)
        return format_str.format(current=current_str,total=total_str)
    
    def __str__(self) -> str:
        return self.format()
    
    def __repr__(self) -> str:
        return "[bright_black]{}[/]".format(self.format())

    