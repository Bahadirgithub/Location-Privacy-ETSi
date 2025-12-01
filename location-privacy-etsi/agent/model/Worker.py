from datetime import timedelta
import random
from model.Agent import Agent
from model.AgentType import AgentType

class Worker(Agent):
    def __init__(self, vehicle_id, home, work, grocery, errands, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.WORKER
        self.work = work
        self.grocery = grocery
        self.config = config

        # Handle None or Numpy arrays safely
        if errands is None:
            self.errands = []
        else:
            self.errands = list(errands)

    def generate_day(self):
        actions = []

        # --- 1. Arbeitsbeginn berechnen (Dynamisch vs. Fest) ---
        work_conf = self.config['work']

        # Prüfen, ob statistische Verteilung vorliegt
        if 'mean' in work_conf and 'std' in work_conf:
            start_float = random.gauss(work_conf['mean'], work_conf['std'])
        else:
            start_float = work_conf['start']

        # --- 2. Arbeitsdauer berechnen ---
        # Wir nehmen die Differenz aus der Config (z.B. 16 - 8 = 8h)
        # und wenden sie auf die gewürfelte Startzeit an.
        ref_start = work_conf.get('start', 8.0)
        ref_end = work_conf.get('end', 16.0)
        duration_hours = ref_end - ref_start

        # Sicherheitsnetz, falls Config unlogisch ist
        if duration_hours <= 0:
            duration_hours = 8.0

        # Startzeit setzen
        self.set_time(start_float)

        # 1) Fahrt zur Arbeit
        a1 = self.advance_step(self.work, timedelta(hours=duration_hours))
        actions.append(a1)

        # 2) Rückfahrt nach Hause
        a2 = self.advance_step(self.home, timedelta(0))
        actions.append(a2)

        # 3) Wocheneinkauf (Grocery)
        # Hier nutzen wir get_duration, das mean/std aus der Config liest
        if random.random() < self.config['grocery']['prob']:
            stay_duration = self.get_duration(self.config['grocery'])

            a3 = self.advance_step(self.grocery, stay_duration)
            a4 = self.advance_step(self.home, timedelta(0))
            actions.extend([a3, a4])

        # 4) Besorgungen (Errands)
        if self.errands:
            if random.random() < self.config['errands']['prob']:
                loc = random.choice(self.errands)
                stay_duration = self.get_duration(self.config['errands'])

                a5 = self.advance_step(loc, stay_duration)
                a6 = self.advance_step(self.home, timedelta(0))
                actions.extend([a5, a6])

        self.end_day()
        return actions