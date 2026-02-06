from enum import Enum

class AaasErrorCode:
    default = 1
    err_param = 100


class AutoTaskDoneFlag(Enum):
    # 任务执行完毕
    done = 1

    # 任务未启动前被终止 (/auto/end_task)
    end_flag = 2

    # 任务执行时被终止 (/auto/end_task)
    interrupt = 3

    @property
    def flag_value(self):
        return self.value