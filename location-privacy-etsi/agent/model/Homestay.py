from datetime import timedelta
from datetime import time
from datetime import datetime
from datetime import date

import random
import numpy as np

from model.Agent import Agent
from model.AgentType import AgentType


class Homestay(Agent):
    # Constructor
    # id: A vehicle ID for the given agent
    # home: A distinct home location
    # school: A distinct school location
    # grocery: A distinct grocery store location
    # activity: A distinct location for after-school activities (e.g., sports)
    # weekend_chores: A list of locations for weekend chores
    def __init__(self, vehicle_id, home, school, grocery, activity, weekend_chores):
        super().__init__(vehicle_id, home)
        self.type = AgentType.HOMESTAY
        self.school = school
        self.grocery = grocery
        self.activity = activity
        self.weekend_chores = weekend_chores

        # --- Define Weekday Times ---

        # Morning school drop-off time (e.g., 8:30 AM +/- 15 min)
        school_dropoff_float = random.normalvariate(8.5, 0.25)
        self.school_dropoff_time = self.time_from_float(school_dropoff_float)

        # Afternoon school pick-up time (e.g., 3:30 PM +/- 15 min)
        school_pickup_float = random.normalvariate(15.5, 0.25)
        self.school_pickup_time = self.time_from_float(school_pickup_float)

        # --- Define Weekday Durations ---

        # Grocery trip duration (e.g., 45 min +/- 12 min)
        grocery_duration_float = random.normalvariate(0.75, 0.2)
        self.grocery_duration = self.timedelta_from_float(grocery_duration_float)

        # Activity duration (e.g., 90 min +/- 15 min)
        activity_duration_float = random.normalvariate(1.5, 0.25)
        self.activity_duration = self.timedelta_from_float(activity_duration_float)


        # --- Define Weekend Times ---
        # This logic is copied from Worker.py to generate random weekend chore times
        self.weekend_chore_times = []
        prev_time = 6  # Start at 6 AM
        max_time = 23  # End at 11 PM
        for i in range(len(weekend_chores)):
            chores_remaining = (len(weekend_chores) - i)
            # Ensure at least 30 min between chores
            remaining_time = max_time - prev_time - 0.5 * chores_remaining
            prev_time = random.uniform(prev_time, prev_time + remaining_time / chores_remaining)
            prev_time += 0.5
            self.weekend_chore_times.append(self.time_from_float(prev_time))

    # Generate a day's worth of actions for the given agent.
    # Returns an array of RoutingStep objects
    def generate_day(self):
        actions = []
        if self.current_time.weekday() < 5:  # Weekday

            # --- Morning Trip Chain (School Drop-off + Groceries) ---

            # Add small randomness to departure time
            departure_time_am = (datetime.combine(date.today(), self.school_dropoff_time)
                                 + timedelta(seconds=random.normalvariate(300, 150))).time()
            self.set_time_t(departure_time_am)

            # 1. Home -> School (short 5-min stop)
            a1 = self.advance_step(self.school, timedelta(minutes=5))

            # 2. School -> Grocery (stay for grocery duration)
            a2 = self.advance_step(self.grocery, self.grocery_duration)

            # 3. Grocery -> Home
            a3 = self.advance_step(self.home, timedelta(0))

            # --- Afternoon Trip Chain (School Pickup + Activity) ---

            # Add small randomness to departure time
            departure_time_pm = (datetime.combine(date.today(), self.school_pickup_time)
                                 + timedelta(seconds=random.normalvariate(300, 150))).time()
            self.set_time_t(departure_time_pm)

            # 4. Home -> School (short 10-min stop)
            a4 = self.advance_step(self.school, timedelta(minutes=10))

            # 5. School -> Activity (stay for activity duration)
            a5 = self.advance_step(self.activity, self.activity_duration)

            # 6. Activity -> Home
            a6 = self.advance_step(self.home, timedelta(0))

            actions.extend([a1, a2, a3, a4, a5, a6])
            self.end_day()

        else:  # Weekend
            # Generate weekend chores just like the Worker agent
            for i in range(len(self.weekend_chore_times)):
                self.set_time_t(self.weekend_chore_times[i])
                # Stay duration is 0, assuming they go home after (or to the next chore)
                # To be more realistic, we could add a random duration
                a = self.advance_step(self.weekend_chores[i], timedelta(hours=random.uniform(0.5, 1.5)))
                actions.append(a)

            # Always return home at the end of the day
            if self.current_location != self.home:
                a_home = self.advance_step(self.home, timedelta(0))
                actions.append(a_home)

            self.end_day()

        return actions