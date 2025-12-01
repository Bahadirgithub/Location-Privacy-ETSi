from datetime import timedelta
import random
import numpy as np

from model.Agent import Agent
from model.AgentType import AgentType


class Freelance(Agent):

    def __init__(self, vehicle_id, home, leisure_locations, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.FREELANCE
        self.config = config

        # Handle numpy array or list
        if leisure_locations is None or len(leisure_locations) == 0:
            self.leisure_locations = []
        else:
            self.leisure_locations = list(leisure_locations)

    def generate_day(self):
        actions = []

        # 1. Stay Home Check
        if random.random() < self.config['stay_home_prob']:
            self.end_day()
            return []

        # 2. Determine Activities
        act_config = self.config['activity']
        num_activities = random.randint(
            act_config['num_activities_min'],
            min(act_config['num_activities_max'], len(self.leisure_locations))
        )

        if num_activities == 0:
            self.end_day()
            return []

        # 3. Generate Schedule
        # Define time window from YAML
        t_min = act_config['time_min']
        t_max = act_config['time_max']

        # Select locations
        todays_locs = random.sample(self.leisure_locations, num_activities)

        current_t = t_min

        for loc in todays_locs:
            # Pick a start time
            # Simple random logic to spread them out between current_t and t_max
            # Ensure we have at least 2 hours buffer or similar
            if current_t >= t_max - 1.0:
                break

            start_t = random.uniform(current_t, t_max - 2.0)

            # --- FIX: Use set_time_t with converter ---
            self.set_time_t(self.time_from_float(start_t))

            stay_dur = random.uniform(
                act_config['stay_duration_min'],
                act_config['stay_duration_max']
            )

            a_loc = self.advance_step(loc, timedelta(hours=stay_dur))
            a_home = self.advance_step(self.home, timedelta(0))
            actions.extend([a_loc, a_home])

            current_t = start_t + stay_dur + 0.5  # Buffer
            if current_t >= t_max:
                break

        self.end_day()
        return actions