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

        # 1) Kids to school
        if random.random() < self.config['school']['prob']:
            self.set_time(self.config['school']['time'])

            # Check if config has a specific duration for school dropoff, else 15 mins
            if 'duration' in self.config['school']:
                dropoff_time = self.timedelta_from_float(self.config['school']['duration'])
            else:
                dropoff_time = timedelta(hours=0.25)

            a1 = self.advance_step(self.school, dropoff_time)
            a2 = self.advance_step(self.home, timedelta(0))
            actions.extend([a1, a2])

        # 2) Grocery
        if random.random() < self.config['grocery']['prob']:
            self.set_time(self.config['grocery']['time'])
            stay_duration = self.get_duration(self.config['grocery'])

            a3 = self.advance_step(self.grocery, stay_duration)
            a4 = self.advance_step(self.home, timedelta(0))
            actions.extend([a3, a4])

        # 3) Activity
        if random.random() < self.config['activity']['prob']:
            self.set_time(self.config['activity']['time'])
            stay_duration = self.get_duration(self.config['activity'])

            a5 = self.advance_step(self.activity, stay_duration)
            a6 = self.advance_step(self.home, timedelta(0))
            actions.extend([a5, a6])

        # 4) Extra locations
        if self.extra and (random.random() < self.config['extra']['prob']):
            loc = random.choice(self.extra)
            stay_duration = self.get_duration(self.config['extra'])

            a7 = self.advance_step(loc, stay_duration)
            a8 = self.advance_step(self.home, timedelta(0))
            actions.extend([a7, a8])

        self.end_day()
        return actions