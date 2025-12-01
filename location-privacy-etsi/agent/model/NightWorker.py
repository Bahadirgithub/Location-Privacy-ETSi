from datetime import timedelta
import random
import numpy as np

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

    def _get_gaussian_val(self, key):
        params = self.config[key]
        return random.gauss(params['mean'], params['std_dev'])

    def generate_day(self):
        actions = []

        # 1. Optional Chores BEFORE Work
        chore_cfg = self.config['weekday_chore']
        current_time = 0.0

        if self.chores and random.random() < 0.5:
            start_chore = random.uniform(chore_cfg['start_min'], chore_cfg['start_max'])
            duration_chore = random.uniform(chore_cfg['duration_min'], chore_cfg['duration_max'])

            # Fix: set_time_t
            self.set_time_t(self.time_from_float(start_chore))

            loc = random.choice(self.chores)
            a1 = self.advance_step(loc, timedelta(hours=duration_chore))
            a2 = self.advance_step(self.home, timedelta(0))
            actions.extend([a1, a2])

            current_time = start_chore + duration_chore

        # 2. Night Work
        start_work = self._get_gaussian_val('work_start')
        duration_work = max(1.0, self._get_gaussian_val('work_duration'))

        # Ensure start time is after chore (add buffer)
        start_work = max(start_work, current_time + 0.5)
        # Ensure it doesn't crash time object (stay < 24.0 for start)
        start_work = min(23.99, start_work)

        # Fix: set_time_t
        self.set_time_t(self.time_from_float(start_work))

        a_work = self.advance_step(self.work, timedelta(hours=duration_work))
        actions.append(a_work)

        a_return = self.advance_step(self.home, timedelta(0))
        actions.append(a_return)

        self.end_day()
        return actions