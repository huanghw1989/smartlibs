from enum import Enum


class CommandType(Enum):
    end = 0 # 结束命令
    app = 1 # 应用自定义命令


class Command():
    def __init__(self, type:CommandType, **kwargs):
        self.type = type
        self.args = kwargs
    
    def cmd2tuple(self):
        return tuple((self.type.name if self.type is not None else None, self.args))
    
    def tuple2cmd(self, cmd_data:tuple):
        type_str, *other = cmd_data
        type = CommandType.__members__.get(type_str)
        kwargs = other[0] if len(other) and isinstance(other[0], dict) else {}
        return Command(type, **kwargs)


end_cmd = Command(CommandType.end)


def app_cmd(**kwargs):
    return Command(CommandType.app, **kwargs)