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

        if extra_locations is None:
            self.extra = []
        else:
            self.extra = list(extra_locations)

    def _get_gaussian_val(self, key):
        params = self.config[key]
        return random.gauss(params['mean'], params['std_dev'])

    def generate_day(self):
        actions = []

        # 1. School Dropoff
        drop_time = self._get_gaussian_val('school_dropoff')
        drop_time = max(6.0, min(10.0, drop_time))  # Safety clamp

        # Fix: set_time_t
        self.set_time_t(self.time_from_float(drop_time))

        a1 = self.advance_step(self.school, timedelta(minutes=15))
        a2 = self.advance_step(self.home, timedelta(0))
        actions.extend([a1, a2])

        current_time = drop_time + 0.25

        # 2. Grocery (Mid-day)
        if random.random() < 0.5:
            shop_start = max(current_time + 1.0, random.gauss(10.0, 1.0))
            shop_dur = self._get_gaussian_val('grocery_duration')

            # Fix: set_time_t
            self.set_time_t(self.time_from_float(shop_start))

            a3 = self.advance_step(self.grocery, timedelta(hours=shop_dur))
            a4 = self.advance_step(self.home, timedelta(0))
            actions.extend([a3, a4])

        # 3. School Pickup
        pick_time = self._get_gaussian_val('school_pickup')
        if pick_time <= current_time:
            pick_time = current_time + 3.0

        # Fix: set_time_t
        self.set_time_t(self.time_from_float(pick_time))

        a5 = self.advance_step(self.school, timedelta(minutes=15))
        actions.append(a5)

        # 4. Activity
        if self.activity and random.random() < 0.6:
            act_dur = self._get_gaussian_val('activity_duration')
            a6 = self.advance_step(self.activity, timedelta(hours=act_dur))
            actions.append(a6)

        # Return Home
        a7 = self.advance_step(self.home, timedelta(0))
        actions.append(a7)

        self.end_day()
        return actions