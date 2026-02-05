from datetime import timedelta
import random
from model.Agent import Agent
from model.AgentType import AgentType

class Homestay(Agent):

    def __init__(self, vehicle_id, home, school, grocery, activity, extra_locations, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.HOMESTAY

        self.school = school
        self.grocery = grocery
        self.activity = activity
        self.config = config

        if extra_locations is None:
            self.extra = []
        else:
            self.extra = list(extra_locations)

    def generate_day(self):
        actions = []

        # Helper: Startzeit holen (unterstützt mean/std falls in YAML, sonst 'time')
        def get_start_time(conf):
            if 'mean' in conf and 'std' in conf:
                return random.gauss(conf['mean'], conf['std'])
            elif 'time' in conf:
                return conf['time']
            else:
                return 8.0 # Fallback

        # 1) Kinder zur Schule
        if random.random() < self.config['school']['prob']:
            start_time = get_start_time(self.config['school'])
            self.set_time(start_time)

            # Dauer des "Abgebens" (Drop-off) statistisch berechnen
            dropoff_duration = self.get_duration(self.config['school'])

            a1 = self.advance_step(self.school, dropoff_duration)
            a2 = self.advance_step(self.home, timedelta(0))
            actions.extend([a1, a2])

        # 2) Einkauf
        if random.random() < self.config['grocery']['prob']:
            start_time = get_start_time(self.config['grocery'])
            self.set_time(start_time)

            stay_duration = self.get_duration(self.config['grocery'])

            a3 = self.advance_step(self.grocery, stay_duration)
            a4 = self.advance_step(self.home, timedelta(0))
            actions.extend([a3, a4])

        # 3) Aktivität
        if random.random() < self.config['activity']['prob']:
            start_time = get_start_time(self.config['activity'])
            self.set_time(start_time)

            stay_duration = self.get_duration(self.config['activity'])

            a5 = self.advance_step(self.activity, stay_duration)
            a6 = self.advance_step(self.home, timedelta(0))
            actions.extend([a5, a6])

        # 4) Extra
        if self.extra and (random.random() < self.config['extra']['prob']):
            # Extra hat oft keine feste Startzeit in YAML, wir nehmen an es passiert nachmittags
            # oder nutzen eine Logik wie beim Freelancer. Hier einfach random:
            if 'time' in self.config['extra']:
                self.set_time(self.config['extra']['time'])

            loc = random.choice(self.extra)
            stay_duration = self.get_duration(self.config['extra'])

            a7 = self.advance_step(loc, stay_duration)
            a8 = self.advance_step(self.home, timedelta(0))
            actions.extend([a7, a8])

        self.end_day()
        return actions