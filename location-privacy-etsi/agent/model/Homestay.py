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
    # config: Das Konfigurations-Profil aus der YAML-Datei
    def __init__(self, vehicle_id, home, school, grocery, activity, weekend_chores, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.HOMESTAY
        self.school = school
        self.grocery = grocery
        self.activity = activity
        self.weekend_chores = weekend_chores
        self.config = config # Speichert die Konfiguration

        # --- Define Weekday Times ---
        # --- NEU: Verwende Konfigurationswerte statt fester Zahlen ---

        # Morning school drop-off time (z.B. 8:30 AM +/- 15 min)
        school_dropoff_float = random.normalvariate(
            config['school_dropoff']['mean'],
            config['school_dropoff']['std_dev']
        )
        self.school_dropoff_time = self.time_from_float(school_dropoff_float)

        # Afternoon school pick-up time (z.B. 3:30 PM +/- 15 min)
        school_pickup_float = random.normalvariate(
            config['school_pickup']['mean'],
            config['school_pickup']['std_dev']
        )
        self.school_pickup_time = self.time_from_float(school_pickup_float)

        # --- Define Weekday Durations ---
        # --- NEU: Verwende Konfigurationswerte statt fester Zahlen ---

        # Grocery trip duration (z.B. 45 min +/- 12 min)
        grocery_duration_float = random.normalvariate(
            config['grocery_duration']['mean'],
            config['grocery_duration']['std_dev']
        )
        self.grocery_duration = self.timedelta_from_float(grocery_duration_float)

        # Activity duration (z.B. 90 min +/- 15 min)
        activity_duration_float = random.normalvariate(
            config['activity_duration']['mean'],
            config['activity_duration']['std_dev']
        )
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
            # (Diese Logik verwendet die in __init__ dynamisch gesetzten Zeiten)

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
            # (Diese Logik verwendet die in __init__ dynamisch gesetzten Zeiten)

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
            # --- UPDATED WEEKEND LOGIC ---
            # Verwendet jetzt Konfigurationswerte

            if not self.weekend_chores: # Skip if agent has no weekend chores
                self.end_day()
                return []

            # --- NEU: Verwende Konfigurationswerte statt fester Zahlen ---
            num_activities = random.randint(
                self.config['weekend']['num_activities_min'],
                min(self.config['weekend']['num_activities_max'], len(self.weekend_chores))
            )

            # Get a random subset of activities and their times
            zipped_list = list(zip(self.weekend_chore_times, self.weekend_chores))
            random.shuffle(zipped_list)
            todays_activities = sorted(zipped_list[:num_activities])

            # --- NEU: Verwende Konfigurationswert statt fester Zahl ---
            chain_trips = random.random() < self.config['weekend']['chain_trips_prob'] and num_activities > 1

            if not chain_trips:
                # --- Path 1: Separate Trips ---
                for activity_time, activity_location in todays_activities:
                    self.set_time_t(activity_time)
                    # --- NEU: Verwende Konfigurationswerte statt fester Zahlen ---
                    stay_duration = self.timedelta_from_float(random.uniform(
                        self.config['weekend']['stay_duration_min'],
                        self.config['weekend']['stay_duration_max']
                    ))
                    a = self.advance_step(activity_location, stay_duration)
                    a_home = self.advance_step(self.home, timedelta(0))
                    actions.extend([a, a_home])

            else:
                # --- Path 2: Chained Trips ---
                self.set_time_t(todays_activities[0][0]) # Start time for first activity
                for activity_time, activity_location in todays_activities:
                    # --- NEU: Verwende Konfigurationswerte statt fester Zahlen ---
                    stay_duration = self.timedelta_from_float(random.uniform(
                        self.config['weekend']['stay_duration_min'],
                        self.config['weekend']['stay_duration_max']
                    ))
                    a = self.advance_step(activity_location, stay_duration)
                    actions.append(a)

                # Always return home at the end of the day
                if self.current_location != self.home:
                    a_home = self.advance_step(self.home, timedelta(0))
                    actions.append(a_home)

            self.end_day()

        return actions