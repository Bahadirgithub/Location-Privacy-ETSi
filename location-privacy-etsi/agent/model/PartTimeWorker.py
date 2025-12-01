from datetime import timedelta
import random
from model.Agent import Agent
from model.AgentType import AgentType

class PartTimeWorker(Agent):
    def __init__(self, vehicle_id, home, work, leisure_locations, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.PART_TIME

        # Renamed 'chores' to 'leisure_locations' for clarity
        if leisure_locations is None:
            self.leisure_locations = []
        else:
            self.leisure_locations = list(leisure_locations)

        self.work = work
        self.config = config

    def generate_day(self):
        actions = []

        start = self.config['work']['start']
        end = self.config['work']['end']

        # 1) Drive to work
        self.set_time(start)
        # Duration calculation
        work_duration = timedelta(hours=end - start)
        action1 = self.advance_step(self.work, work_duration)
        actions.append(action1)

        # 2) Return Home
        action2 = self.advance_step(self.home, timedelta(0))
        actions.append(action2)

        # 3) Leisure / Chores
        if self.leisure_locations:
            # Pick a random location
            loc = random.choice(self.leisure_locations)

            # Calculate stay duration using new helper (supports mean/std)
            stay_duration = self.get_duration(self.config['chores']) # Config key remains 'chores' to match YAML

            action3 = self.advance_step(loc, stay_duration)
            action4 = self.advance_step(self.home, timedelta(0))
            actions.extend([action3, action4])

        self.end_day()
        return actions