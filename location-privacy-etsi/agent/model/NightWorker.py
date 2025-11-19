from datetime import timedelta
import random
import numpy as np

from model.Agent import Agent
from model.AgentType import AgentType


class NightWorker(Agent):

    def __init__(self, vehicle_id, home, work, grocery, chores, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.NIGHTWORKER
        self.work = work
        self.grocery = grocery
        self.config = config

        # np.array → list
        if chores is None:
            self.chores = []
        else:
            self.chores = list(chores)

    def generate_day(self):
        actions = []

        start = self.config['work']['start']      # z.B. 22 Uhr
        end = self.config['work']['end']          # z.B. 6 Uhr

        # Nachtarbeit über Mitternacht
        self.set_time(start)
        duration = (24 - start) + end  # korrekt für Über-Mitternacht
        a1 = self.advance_step(self.work, timedelta(hours=duration))
        actions.append(a1)

        a2 = self.advance_step(self.home, timedelta(0))
        actions.append(a2)

        # Grocery tagsüber
        if random.random() < self.config['grocery']['prob']:
            stay = random.uniform(
                self.config['grocery']['stay_min'],
                self.config['grocery']['stay_max']
            )
            a3 = self.advance_step(self.grocery, timedelta(hours=stay))
            a4 = self.advance_step(self.home, timedelta(0))
            actions.extend([a3, a4])

        # Chores
        if self.chores is not None and len(self.chores) > 0:
            if random.random() < self.config['chores']['prob']:
                loc = random.choice(self.chores)
                stay = random.uniform(
                    self.config['chores']['stay_min'],
                    self.config['chores']['stay_max']
                )
                a5 = self.advance_step(loc, timedelta(hours=stay))
                a6 = self.advance_step(self.home, timedelta(0))
                actions.extend([a5, a6])

        self.end_day()
        return actions