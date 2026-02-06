import time
import multiprocessing as mp
import queue

from smart.rest import RestRoute, RestService, RequestException, cron_timing

from .notify_manage import NotifyManage


class PlanNotifier:
    all_plan = {}
    plan_events = mp.Queue()

    @staticmethod
    def sync_plan():
        all_plan = PlanNotifier.all_plan

        while True:
            try:
                # ev_name, plan = PlanNotifier.plan_events.get(block=True, timeout=1)
                ev_name, plan = PlanNotifier.plan_events.get(block=False)

                if ev_name in ('add', 'update'):

                    all_plan[plan.get('id')] = plan
                elif ev_name == 'del':

                    id = plan.get('id')
                    if id in all_plan:
                        del all_plan[id]

            except queue.Empty:
                break

    @staticmethod
    @cron_timing(3)
    async def check_plan():
        curr_ts = time.time()
        print('PlanNotifier.check_plan at', curr_ts)

        PlanNotifier.sync_plan()

        # print('PlanNotifier.all_plan', PlanNotifier.all_plan)

        for id, plan in PlanNotifier.all_plan.items():
            alarm, alarmed = plan.get('alarm'), plan.get('alarmed')
            # print('PlanNotifier.check', plan, alarm, alarmed, curr_ts)

            if alarm and curr_ts >= alarm and not alarmed:
                print('To notify plan:', plan)
                NotifyManage.notify_plans.put(plan)
                plan['alarmed'] = curr_ts