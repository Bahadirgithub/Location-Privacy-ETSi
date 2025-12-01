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

        if errands is None:
            self.errands = []
        else:
            self.errands = list(errands)

    def _get_gaussian_val(self, key):
        params = self.config[key]
        return random.gauss(params['mean'], params['std_dev'])

    def generate_day(self):
        actions = []

        # 1. Work Routine
        start_hour = self._get_gaussian_val('work_start')
        duration_hour = max(1.0, self._get_gaussian_val('work_duration'))

        # Clamp start time (e.g. 5 AM to 12 PM)
        start_hour = max(5.0, min(12.0, start_hour))

        # Fix: use set_time_t with converter
        self.set_time_t(self.time_from_float(start_hour))

        a1 = self.advance_step(self.work, timedelta(hours=duration_hour))
        actions.append(a1)

        # 2. Optional Weekday Chore
        chore_prob = self.config.get('weekday_chore_on_way_home_prob', 0.0)

        if (self.errands or self.grocery) and random.random() < chore_prob:
            chore_cfg = self.config['weekday_chore']

            if self.grocery and random.random() < 0.7:
                loc = self.grocery
            elif self.errands:
                loc = random.choice(self.errands)
            else:
                loc = self.grocery

            if loc:
                stay = random.uniform(chore_cfg['duration_min'], chore_cfg['duration_max'])
                a_chore = self.advance_step(loc, timedelta(hours=stay))
                actions.append(a_chore)

        # 3. Return Home
        a_home = self.advance_step(self.home, timedelta(0))
        actions.append(a_home)

        self.end_day()
        return actions