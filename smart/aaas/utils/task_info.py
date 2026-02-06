import time


class AaasTaskInfoTool:
    MIN_CHECK_INTERVAL = 0.5

    def __init__(self, task_info_map) -> None:
        self.task_info_map = task_info_map
        self._last_query_stage = None
    
    def check_stage_passed(self, task_id, stage_name):
        """查看任务的阶段是否已经过去

        Args:
            task_id (str): 任务ID
            stage_name (str): 阶段名, 支持: start, end

        Returns:
            bool: True表示阶段已执行, False表示阶段未执行
        """
        task_info = self.task_info_map.get(task_id)
        if task_info is None:
            # task_id no exist
            return None

        stage_list = (task_info or {}).get("stage") or []
        self._last_query_stage = stage_list
        return stage_name in stage_list

    def wait_stage(self, task_id, stage_name, wait_time:int=30, wait_end_ts:int=None, check_interval:float=1.0):
        """等待任务的阶段执行

        Args:
            task_id (str): 任务ID
            stage_name (str): 阶段名, 支持: start, end
            wait_time (int, optional): 等待时长. Defaults to 30.
            wait_end_ts (int, optional): 等待过期时间, 非空则wait_time参数无效. Defaults to None.
            check_interval (float, optional): 查看task_info的间隔. Defaults to 1.0.

        Returns:
            bool: True表示阶段已执行, False表示阶段未执行
        """
        if not wait_end_ts:
            wait_end_ts = time.time() + wait_time
        check_interval = max(check_interval, self.MIN_CHECK_INTERVAL)
        
        while True:
            stage_passed = self.check_stage_passed(task_id, stage_name=stage_name)
            if stage_passed is None:
                # task_id no exist
                return None

            if stage_passed:
                return True
            sleep_time = min(check_interval, time.time()-wait_end_ts)
            if sleep_time <= 0:
                return False
            else:
                time.sleep(sleep_time)
