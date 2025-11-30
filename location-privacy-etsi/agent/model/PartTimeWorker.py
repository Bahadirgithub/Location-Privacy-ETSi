from datetime import timedelta
import random
import numpy as np

from model.Agent import Agent
from model.AgentType import AgentType


class PartTimeWorker(Agent):

    def __init__(self, vehicle_id, home, work, chores, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.PART_TIME

        # np.array → list
        if chores is None:
            self.chores = []
        else:
            self.chores = list(chores)

        self.work = work
        self.config = config

    # Tagesroutine
    def generate_day(self):
        actions = []

        # Falls keine Arbeitszeit definiert ist
        start = self.config['work']['start']
        end = self.config['work']['end']

        # 1) Fahrt zur Arbeit
        self.set_time(start)
        action1 = self.advance_step(self.work, timedelta(hours=end - start))
        actions.append(action1)

        # 2) Zurück nach Hause
        action2 = self.advance_step(self.home, timedelta(0))
        actions.append(action2)

        # 3) Chores (falls existent)
        if self.chores is None or len(self.chores) == 0:
            self.end_day()
            return actions

        # Wähle 1 chore zufällig
        chore_loc = random.choice(self.chores)
        stay = random.uniform(
            self.config['chores']['stay_min'],
            self.config['chores']['stay_max']
        )
        action3 = self.advance_step(chore_loc, timedelta(hours=stay))
        action4 = self.advance_step(self.home, timedelta(0))
        actions.extend([action3, action4])

        self.end_day()
        return actions