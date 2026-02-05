from datetime import timedelta
import random
from model.Agent import Agent
from model.AgentType import AgentType

class NightWorker(Agent):

    def __init__(self, vehicle_id, home, work, grocery, chores, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.NIGHT_WORKER
        self.work = work
        self.grocery = grocery
        self.config = config

        if chores is None:
            self.chores = []
        else:
            self.chores = list(chores)

    def generate_day(self):
        actions = []
        work_conf = self.config['work']

        # --- 1. Startzeit (Gauß um 22.0 Uhr) ---
        if 'mean' in work_conf and 'std' in work_conf:
            start_float = random.gauss(work_conf['mean'], work_conf['std'])
        else:
            start_float = work_conf['start']

        # --- 2. Dauer über Mitternacht berechnen ---
        ref_start = work_conf.get('start', 22.0)
        ref_end = work_conf.get('end', 6.0)

        if ref_end < ref_start:
            # Beispiel: Start 22, Ende 6 -> (24-22) + 6 = 8 Stunden
            duration_hours = (24.0 - ref_start) + ref_end
        else:
            duration_hours = ref_end - ref_start

        if duration_hours <= 0: duration_hours = 8.0

        self.set_time(start_float)

        # 1) Nachtschicht
        a1 = self.advance_step(self.work, timedelta(hours=duration_hours))
        actions.append(a1)

        # 2) Nach Hause
        a2 = self.advance_step(self.home, timedelta(0))
        actions.append(a2)

        # 3) Einkaufen (Tagsüber nach Schlaf)
        if random.random() < self.config['grocery']['prob']:
            stay_duration = self.get_duration(self.config['grocery'])
            a3 = self.advance_step(self.grocery, stay_duration)
            a4 = self.advance_step(self.home, timedelta(0))
            actions.extend([a3, a4])

        # 4) Erledigungen
        if self.chores and (random.random() < self.config['chores']['prob']):
            loc = random.choice(self.chores)
            stay_duration = self.get_duration(self.config['chores'])
            a5 = self.advance_step(loc, stay_duration)
            a6 = self.advance_step(self.home, timedelta(0))
            actions.extend([a5, a6])

        self.end_day()
        return actions