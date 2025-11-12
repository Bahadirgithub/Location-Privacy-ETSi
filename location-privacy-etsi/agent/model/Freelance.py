from datetime import timedelta, time, datetime, date
import random
import numpy as np

from model.Agent import Agent
from model.AgentType import AgentType


class Freelance(Agent):
    """
    Freelance agent: works independently, has flexible schedules, and performs
    optional leisure activities during the day.
    """

    def __init__(self, vehicle_id, home, leisure_locations, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.FREELANCE
        self.config = config
        self.leisure_times = []

        # ✅ Fix: handle numpy arrays, None, or empty lists properly
        if leisure_locations is None or len(leisure_locations) == 0:
            self.leisure_locations = []
            return
        else:
            # convert np.ndarray to normal list for consistency
            self.leisure_locations = list(leisure_locations)

        # Generate potential "activity times" based on config
        prev_time = config['activity']['time_min']   # e.g. 9.0 (9 AM)
        max_time = config['activity']['time_max']    # e.g. 20.0 (8 PM)

        for i in range(len(self.leisure_locations)):
            leisure_remaining = len(self.leisure_locations) - i
            # ensure at least 30 min buffer per remaining activity
            remaining_time = max_time - prev_time - 0.5 * leisure_remaining

            # Prevent negative time intervals
            if remaining_time <= 0:
                prev_time = random.uniform(prev_time, max_time)
            else:
                prev_time = random.uniform(prev_time, prev_time + remaining_time / leisure_remaining)

            # ensure time stays within max_time
            prev_time = min(prev_time + 0.5, max_time)
            if prev_time >= max_time:
                break

            self.leisure_times.append(self.time_from_float(prev_time))

    # Generate a day's worth of actions.
    # This agent has no strict routine—behavior is the same on weekdays/weekends.
    def generate_day(self):
        actions = []

        # --- 40% chance (or config value) of staying home all day ---
        if (
                random.random() < self.config['stay_home_prob']
                or not self.leisure_locations
                or not self.leisure_times
        ):
            self.end_day()
            return []

        # Decide number of activities (bounded by config)
        num_activities = random.randint(
            self.config['activity']['num_activities_min'],
            min(
                self.config['activity']['num_activities_max'],
                len(self.leisure_locations),
                len(self.leisure_times)
            )
        )

        # Shuffle and select subset of activities
        zipped_list = list(zip(self.leisure_times, self.leisure_locations))
        random.shuffle(zipped_list)
        todays_activities = sorted(zipped_list[:num_activities])

        # Determine if trips are chained
        chain_trips = (
                random.random() < self.config['activity']['chain_trips_prob']
                and num_activities > 1
        )

        if not chain_trips:
            # Separate trips (home → activity → home)
            for activity_time, activity_location in todays_activities:
                self.set_time_t(activity_time)
                stay_duration = self.timedelta_from_float(random.uniform(
                    self.config['activity']['stay_duration_min'],
                    self.config['activity']['stay_duration_max']
                ))
                a1 = self.advance_step(activity_location, stay_duration)
                a2 = self.advance_step(self.home, timedelta(0))
                actions.extend([a1, a2])

        else:
            # Chained trips (home → multiple activities → home)
            self.set_time_t(todays_activities[0][0])

            for _, activity_location in todays_activities:
                stay_duration = self.timedelta_from_float(random.uniform(
                    self.config['activity']['stay_duration_min'],
                    self.config['activity']['stay_duration_max']
                ))
                a_activity = self.advance_step(activity_location, stay_duration)
                actions.append(a_activity)

            # Return home at end
            a_home = self.advance_step(self.home, timedelta(0))
            actions.append(a_home)

        self.end_day()
        return actions