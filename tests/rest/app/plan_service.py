import time

from smart.rest import RestRoute, RestService, RequestException

from .plan_notify import PlanNotifier

rest = RestRoute()

@rest.service('/plan')
class PlanService(RestService):
    __all_plan = []
    __id_count = 1

    @rest.get('list')
    def list_plan(self):
        return self.__all_plan
    
    @rest.put('')
    def add_plan(self):
        content = self.json_param('content')
        alarm = self.json_param('alarm')

        if content is None:
            raise RequestException('miss content')

        all_plan = self.__all_plan
        id = self.__id_count
        self.__id_count += 1
        plan = {
            'id': id,
            'content': content,
            'alarm': alarm,
            'create_time': time.time()
        }
        all_plan.append(plan)
        PlanNotifier.plan_events.put(('add', plan))
        return plan
    
    @rest.delete('{id}')
    def del_plan(self, id:int):
        all_plan = self.__all_plan

        found = -1
        for i, plan in enumerate(all_plan):
            if plan['id'] == id:
                found = i
                break

        rst = {
            'success': False
        }
        if found >= 0:
            PlanNotifier.plan_events.put(('del', all_plan[found]))
            all_plan.pop(found)
            rst['success'] = True
        else:
            rst['msg'] = 'plan no found'
        
        return rst
        
