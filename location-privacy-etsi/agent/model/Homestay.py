from datetime import timedelta
import random
import numpy as np

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

        # np.array → list
        if extra_locations is None:
            self.extra = []
        else:
            self.extra = list(extra_locations)

    def generate_day(self):
        actions = []

        # 1) Kids to school
        if random.random() < self.config['school']['prob']:
            self.set_time(self.config['school']['time'])
            a1 = self.advance_step(self.school, timedelta(hours=0.25))
            a2 = self.advance_step(self.home, timedelta(0))
            actions.extend([a1, a2])

        # 2) Grocery
        if random.random() < self.config['grocery']['prob']:
            self.set_time(self.config['grocery']['time'])
            stay = random.uniform(
                self.config['grocery']['stay_min'],
                self.config['grocery']['stay_max']
            )
            a3 = self.advance_step(self.grocery, timedelta(hours=stay))
            a4 = self.advance_step(self.home, timedelta(0))
            actions.extend([a3, a4])

        # 3) Activity
        if random.random() < self.config['activity']['prob']:
            self.set_time(self.config['activity']['time'])
            stay = random.uniform(
                self.config['activity']['stay_min'],
                self.config['activity']['stay_max']
            )
            a5 = self.advance_step(self.activity, timedelta(hours=stay))
            a6 = self.advance_step(self.home, timedelta(0))
            actions.extend([a5, a6])

        # 4) Extra locations
        if self.extra is not None and len(self.extra) > 0:
            if random.random() < self.config['extra']['prob']:
                loc = random.choice(self.extra)
                stay = random.uniform(
                    self.config['extra']['stay_min'],
                    self.config['extra']['stay_max']
                )
                a7 = self.advance_step(loc, timedelta(hours=stay))
                a8 = self.advance_step(self.home, timedelta(0))
                actions.extend([a7, a8])

        self.end_day()
        return actions