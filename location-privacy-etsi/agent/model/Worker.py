from datetime import timedelta
from datetime import time
from datetime import datetime
from datetime import date

import random
import numpy as np

from model.Agent import Agent
from model.AgentType import AgentType



class Worker(Agent):
    # Constructor
    # id: A vehicle ID for the given agent
    # locations: A list of locations the agent is able to visit
    # home: A distinct home location
    # chore: chore that is done during the week and on the weekend
    # work: A distinct work location
    def __init__(self, vehicle_id, home, work, chore, weekend_chores):
        super().__init__(vehicle_id, home)
        self.type = AgentType.WORKER
        self.chore = chore
        self.work = work
        self.weekend_chores = weekend_chores # This is a list of locations

        work_time_float = random.normalvariate(8, 1)
        work_duration_float = random.normalvariate(8, 1)
        self.work_time = self.time_from_float(work_time_float)
        self.work_duration = self.timedelta_from_float(work_duration_float)

        chore_time_float = random.uniform(work_time_float + work_duration_float, 22)
        chore_duration_float = random.uniform(0, 23 - chore_time_float)
        self.chore_time = self.time_from_float(chore_time_float)
        self.chore_duration = self.timedelta_from_float(chore_duration_float)

        self.weekend_chore_times = []
        prev_time = 6
        max_time = 23
        for i in range(len(weekend_chores)):
            chores_remaining = (len(weekend_chores) - i)
            remaining_time = max_time - prev_time - 0.5 * chores_remaining
            prev_time = random.uniform(prev_time, prev_time + remaining_time / chores_remaining)
            prev_time += 0.5
            self.weekend_chore_times.append(self.time_from_float(prev_time))

    # Generate a days worth of actions for the given agent.
    # Returns an array of RoutingStep objects
    def generate_day(self):
        actions = []
        if self.current_time.weekday() < 5:
            # --- UPDATED WEEKDAY LOGIC ---
            # Give the worker two different patterns to add variety.

            # Departure time with a random perturbation
            departure_time = (datetime.combine(date.today(), self.work_time) + timedelta(seconds=random.normalvariate(600,300))).time()
            self.set_time_t(departure_time)

            if random.random() < 0.5:
                # Path A (50% chance): "Efficient"
                # Home -> Work -> Chore (on the way home) -> Home
                a1 = self.advance_step(self.work, self.work_duration)
                a2 = self.advance_step(self.chore, self.chore_duration)
                a3 = self.advance_step(self.home, timedelta(0))
                actions.extend([a1, a2, a3])

            else:
                # Path B (50% chance): "Original Logic"
                # Home -> Work -> Home (rest) -> Chore -> Home
                a1 = self.advance_step(self.work, self.work_duration)
                a2 = self.advance_step(self.home, timedelta(0))
                self.set_time_t(self.chore_time) # Set time for later chore
                a3 = self.advance_step(self.chore, self.chore_duration)
                a4 = self.advance_step(self.home, timedelta(0))
                actions.extend([a1, a2, a3, a4])

            self.end_day()

        else:
            # --- UPDATED WEEKEND LOGIC ---
            # Make weekend behavior more realistic.
            # Instead of doing all chores, pick 1 or 2.
            # Add realistic durations.
            # Add trip chaining (e.g., Home -> Gym -> Grocery -> Home).

            if not self.weekend_chores: # Skip if agent has no weekend chores
                self.end_day()
                return []

            # Decide on 1 or 2 activities for the day
            num_activities = random.randint(1, min(2, len(self.weekend_chores)))

            # Get a random subset of activities and their times
            zipped_list = list(zip(self.weekend_chore_times, self.weekend_chores))
            random.shuffle(zipped_list)
            todays_activities = sorted(zipped_list[:num_activities])

            # 50% chance to chain trips (e.g., Home -> A -> B -> Home)
            # 50% chance to do separate trips (e.g., Home -> A -> Home, Home -> B -> Home)
            chain_trips = random.random() < 0.5 and num_activities > 1

            if not chain_trips:
                # --- Path 1: Separate Trips ---
                for activity_time, activity_location in todays_activities:
                    # Set departure time from home
                    self.set_time_t(activity_time)
                    # Stay for a random duration (45 min to 2 hours)
                    stay_duration = self.timedelta_from_float(random.uniform(0.75, 2.0))

                    a1 = self.advance_step(activity_location, stay_duration)
                    a2 = self.advance_step(self.home, timedelta(0)) # Go home after
                    actions.extend([a1, a2])

            else:
                # --- Path 2: Chained Trips ---
                # Start from home for the first activity
                self.set_time_t(todays_activities[0][0])

                for activity_time, activity_location in todays_activities:
                    # Stay for a random duration (45 min to 2 hours)
                    stay_duration = self.timedelta_from_float(random.uniform(0.75, 2.0))

                    # Go from current location (Home or last activity) to the next one
                    a_activity = self.advance_step(activity_location, stay_duration)
                    actions.append(a_activity)

                # After the last activity, go home
                a_home = self.advance_step(self.home, timedelta(0))
                actions.append(a_home)

            self.end_day()
        return actions