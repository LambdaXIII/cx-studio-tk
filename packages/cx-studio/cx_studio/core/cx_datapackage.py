class DataPackage:
    """_summary_
        数据包装类，用于包装数据，支持字典和属性访问
    """
    def def __init__(self):
        self.__data = {}

    @classmethod
    def from_dict(cls,data:dict):
        result = cls()
        for k,v in data.items():
            result.__data[k] = DataPackage.__check_value(v)

    @staticmethod
    def __check_values(value):
        if isinstance(value,list):
            for value in values:
                return [ DataPackage.__check_values(v) for v in value ]
        elif isinstance(value,dict):
            return DataPackage.from_dict(value)
        else:
            return value

    def __getattr__(self,key):
        return self._data[key]

    def __setattr__(self,key,value):
        self._data[key] = DataPackage.__check_value(value)

    def __getitem__(self,key):
        if isinstance(key, str) and ('.' in key):
            keys = key.split('.')
            value = self._data[keys[0]]
            for k in keys[1:]:
                value = value[k]
            return value
        return self._data[key]

    def __setitem__(self,key,value):
        if isinstance(key, str) and ('.' in key):
            keys = key.split('.')
            d = self._data[keys[0]]
            for k in keys[1:-1]:
                d = d[k]
            d[keys[-1]] = DataPackage.__check_value(value)
        else:
            self._data[key] = DataPackage.__check_value(value)
