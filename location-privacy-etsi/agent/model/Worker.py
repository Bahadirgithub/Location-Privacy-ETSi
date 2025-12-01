from datetime import timedelta
import random
from model.Agent import Agent
from model.AgentType import AgentType

class Worker(Agent):
    def __init__(self, vehicle_id, home, work, grocery, errands, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.WORKER
        self.work = work
        self.grocery = grocery
        self.config = config

        # Handle None or Numpy arrays safely
        if errands is None:
            self.errands = []
        else:
            self.errands = list(errands)

    def generate_day(self):
        actions = []

        # Determine start time (Support Mean/Std or Fixed Range)
        if 'mean' in self.config['work']:
            # If using Gaussian for start time
            start_float = random.gauss(self.config['work']['mean'], self.config['work']['std'])
            # Simple duration assumption if start is variable, or use fixed end?
            # Assuming standard 8 hour day if variable start, or calc from config
            duration = 8.5 # Example default or read from config
        else:
            # Fallback to original logic
            start_float = self.config['work']['start']
            duration = self.config['work']['end'] - start_float

        self.set_time(start_float)

        # 1) Drive to Work
        a1 = self.advance_step(self.work, timedelta(hours=duration))
        actions.append(a1)

        # 2) Return home
        a2 = self.advance_step(self.home, timedelta(0))
        actions.append(a2)

        # 3) Grocery Shopping
        if random.random() < self.config['grocery']['prob']:
            stay_duration = self.get_duration(self.config['grocery'])
            a3 = self.advance_step(self.grocery, stay_duration)
            a4 = self.advance_step(self.home, timedelta(0))
            actions.extend([a3, a4])

        # 4) Optional Errands
        if self.errands:
            if random.random() < self.config['errands']['prob']:
                loc = random.choice(self.errands)
                stay_duration = self.get_duration(self.config['errands'])

                a5 = self.advance_step(loc, stay_duration)
                a6 = self.advance_step(self.home, timedelta(0))
                actions.extend([a5, a6])

        self.end_day()
        return actions