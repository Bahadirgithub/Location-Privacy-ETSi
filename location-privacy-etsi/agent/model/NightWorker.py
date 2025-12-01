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

        start = self.config['work']['start']      # e.g., 22.0 (10 PM)
        end = self.config['work']['end']          # e.g., 6.0 (6 AM)

        # 1) Night Shift (over midnight)
        self.set_time(start)

        # Calculate duration over midnight
        if end < start:
            duration_hours = (24 - start) + end
        else:
            duration_hours = end - start

        a1 = self.advance_step(self.work, timedelta(hours=duration_hours))
        actions.append(a1)

        # 2) Return Home
        a2 = self.advance_step(self.home, timedelta(0))
        actions.append(a2)

        # 3) Grocery (Daytime)
        if random.random() < self.config['grocery']['prob']:
            stay_duration = self.get_duration(self.config['grocery'])
            a3 = self.advance_step(self.grocery, stay_duration)
            a4 = self.advance_step(self.home, timedelta(0))
            actions.extend([a3, a4])

        # 4) Chores
        if self.chores and (random.random() < self.config['chores']['prob']):
            loc = random.choice(self.chores)
            stay_duration = self.get_duration(self.config['chores'])
            a5 = self.advance_step(loc, stay_duration)
            a6 = self.advance_step(self.home, timedelta(0))
            actions.extend([a5, a6])

        self.end_day()
        return actions