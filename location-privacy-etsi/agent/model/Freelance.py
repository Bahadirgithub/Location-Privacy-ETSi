from datetime import timedelta
from datetime import time
from datetime import datetime
from datetime import date

import random
import numpy as np

from model.Agent import Agent
from model.AgentType import AgentType


class Freelance(Agent):
    # Constructor
    # id: A vehicle ID
    # home: A distinct home location
    # leisure_locations: A list of locations for leisure (e.g., coffee, gym, park)
    def __init__(self, vehicle_id, home, leisure_locations):
        super().__init__(vehicle_id, home)
        self.type = AgentType.FREELANCE
        self.leisure_locations = leisure_locations
        self.leisure_times = []

        # Generate some potential "activity times" for the whole simulation
        # These will be randomly chosen from.
        prev_time = 9  # Start at 9 AM
        max_time = 20  # End at 8 PM

        if not leisure_locations:
            return

        for i in range(len(leisure_locations)):
            leisure_remaining = (len(leisure_locations) - i)
            # Ensure at least 30 min between activities
            remaining_time = max_time - prev_time - 0.5 * leisure_remaining

            # Handle potential negative remaining_time if many locations are passed
            if remaining_time <= 0:
                prev_time = random.uniform(prev_time, max_time)
            else:
                prev_time = random.uniform(prev_time, prev_time + remaining_time / leisure_remaining)

            prev_time = min(prev_time + 0.5, max_time) # ensure it doesn't go over max_time
            if prev_time >= max_time:
                break

            self.leisure_times.append(self.time_from_float(prev_time))

    # Generate a day's worth of actions.
    # This agent has no routine and behavior is the same on weekdays/weekends.
    def generate_day(self):
        actions = []

        # --- KEY BEHAVIOR: 40% chance of staying home all day ---
        # Also check if agent has any locations/times to go to
        if random.random() < 0.4 or not self.leisure_locations or not self.leisure_times:
            self.end_day()
            return []

        # Decide on 1 or 2 activities for the day
        num_activities = random.randint(1, min(2, len(self.leisure_locations), len(self.leisure_times)))

        # Get a random subset of activities and their times
        zipped_list = list(zip(self.leisure_times, self.leisure_locations))
        random.shuffle(zipped_list)
        todays_activities = sorted(zipped_list[:num_activities])

        # Use the same trip-chaining logic as other agents
        chain_trips = random.random() < 0.5 and num_activities > 1

        if not chain_trips:
            # --- Path 1: Separate Trips ---
            for activity_time, activity_location in todays_activities:
                self.set_time_t(activity_time)
                # Shorter duration for freelance trips: 30-90 min
                stay_duration = self.timedelta_from_float(random.uniform(0.5, 1.5))

                a1 = self.advance_step(activity_location, stay_duration)
                a2 = self.advance_step(self.home, timedelta(0))
                actions.extend([a1, a2])

        else:
            # --- Path 2: Chained Trips ---
            self.set_time_t(todays_activities[0][0])

            for activity_time, activity_location in todays_activities:
                # Shorter duration for freelance trips: 30-90 min
                stay_duration = self.timedelta_from_float(random.uniform(0.5, 1.5))

                a_activity = self.advance_step(activity_location, stay_duration)
                actions.append(a_activity)

            # After the last activity, go home
            a_home = self.advance_step(self.home, timedelta(0))
            actions.append(a_home)

        self.end_day()
        return actions