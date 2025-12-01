from datetime import timedelta
import random
import numpy as np

from model.Agent import Agent
from model.AgentType import AgentType


class PartTimeWorker(Agent):

    def __init__(self, vehicle_id, home, work, chores, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.PART_TIME

        if chores is None:
            self.chores = []
        else:
            self.chores = list(chores)

        self.work = work
        self.config = config

    def _get_gaussian_val(self, key):
        params = self.config[key]
        return random.gauss(params['mean'], params['std_dev'])

    def generate_day(self):
        actions = []

        # Calculate probability based on average work days
        avg_days = sum(self.config['work_days_choices']) / len(self.config['work_days_choices'])
        work_prob = avg_days / 7.0

        if random.random() < work_prob:
            # --- WORK DAY ---
            start_hour = self._get_gaussian_val('work_start')
            duration_hour = max(0.5, self._get_gaussian_val('work_duration'))

            # Clamp and set time
            start_hour = max(0.0, min(23.99, start_hour))
            self.set_time_t(self.time_from_float(start_hour))

            # Drive to work
            a1 = self.advance_step(self.work, timedelta(hours=duration_hour))
            actions.append(a1)

            # Return home
            a2 = self.advance_step(self.home, timedelta(0))
            actions.append(a2)

        else:
            # --- DAY OFF ---
            day_off_cfg = self.config['day_off']

            num_activities = random.randint(
                day_off_cfg['num_activities_min'],
                day_off_cfg['num_activities_max']
            )

            if self.chores and num_activities > 0:
                chore_loc = random.choice(self.chores)

                # Random start time (10 AM - 4 PM)
                start_hour = random.uniform(10.0, 16.0)
                self.set_time_t(self.time_from_float(start_hour))

                stay = random.uniform(
                    day_off_cfg['stay_duration_min'],
                    day_off_cfg['stay_duration_max']
                )

                a1 = self.advance_step(chore_loc, timedelta(hours=stay))
                a2 = self.advance_step(self.home, timedelta(0))
                actions.extend([a1, a2])

        self.end_day()
        return actions