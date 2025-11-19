from datetime import timedelta
import random
import numpy as np

from model.Agent import Agent
from model.AgentType import AgentType


class Worker(Agent):

    def __init__(self, vehicle_id, home, work, grocery, errands, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.WORKER
        self.work = work
        self.grocery = grocery
        self.config = config

        # np.array → list
        if errands is None:
            self.errands = []
        else:
            self.errands = list(errands)

    def generate_day(self):
        actions = []

        start = self.config['work']['start']
        end = self.config['work']['end']

        # 1) Work start
        self.set_time(start)
        a1 = self.advance_step(self.work, timedelta(hours=end - start))
        actions.append(a1)

        # 2) Return home
        a2 = self.advance_step(self.home, timedelta(0))
        actions.append(a2)

        # 3) Grocery
        if random.random() < self.config['grocery']['prob']:
            stay = random.uniform(
                self.config['grocery']['stay_min'],
                self.config['grocery']['stay_max']
            )
            a3 = self.advance_step(self.grocery, timedelta(hours=stay))
            a4 = self.advance_step(self.home, timedelta(0))
            actions.extend([a3, a4])

        # 4) Optional errands
        if self.errands is not None and len(self.errands) > 0:
            if random.random() < self.config['errands']['prob']:
                loc = random.choice(self.errands)
                stay = random.uniform(
                    self.config['errands']['stay_min'],
                    self.config['errands']['stay_max']
                )
                a5 = self.advance_step(loc, timedelta(hours=stay))
                a6 = self.advance_step(self.home, timedelta(0))
                actions.extend([a5, a6])

        self.end_day()
        return actions