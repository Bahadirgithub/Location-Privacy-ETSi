from datetime import timedelta
import random
from model.Agent import Agent
from model.AgentType import AgentType

class PartTimeWorker(Agent):
    def __init__(self, vehicle_id, home, work, leisure_locations, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.PART_TIME

        if leisure_locations is None:
            self.leisure_locations = []
        else:
            self.leisure_locations = list(leisure_locations)

        self.work = work
        self.config = config

    def generate_day(self):
        actions = []

        work_conf = self.config['work']

        # --- 1. Startzeit bestimmen (Gauß oder Fest) ---
        if 'mean' in work_conf and 'std' in work_conf:
            start_float = random.gauss(work_conf['mean'], work_conf['std'])
        else:
            start_float = work_conf['start']

        # --- 2. Dauer bestimmen ---
        ref_start = work_conf.get('start', 10.0)
        ref_end = work_conf.get('end', 14.0)
        duration_hours = ref_end - ref_start
        if duration_hours <= 0: duration_hours = 4.0

        # Setze Zeit und führe Arbeit aus
        self.set_time(start_float)

        # 1) Fahrt zur Arbeit
        action1 = self.advance_step(self.work, timedelta(hours=duration_hours))
        actions.append(action1)

        # 2) Rückfahrt
        action2 = self.advance_step(self.home, timedelta(0))
        actions.append(action2)

        # 3) Freizeit / Chores
        if self.leisure_locations:
            loc = random.choice(self.leisure_locations)

            # Nutzung von get_duration für statistische Aufenthaltsdauer
            stay_duration = self.get_duration(self.config['chores'])

            action3 = self.advance_step(loc, stay_duration)
            action4 = self.advance_step(self.home, timedelta(0))
            actions.extend([action3, action4])

        self.end_day()
        return actions