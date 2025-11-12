from datetime import timedelta
from datetime import time
from datetime import datetime
from datetime import date

import random

from model.Agent import Agent
from model.AgentType import AgentType

import numpy as np

class PartTimeWorker(Agent):
    # Constructor
    # id: A vehicle ID for the given agent
    # locations: A list of locations the agent is able to visit
    # home: A distinct home location
    # chore: chore that is done during the week and on the weekend
    # work: A distinct work location
    # config: Das Konfigurations-Profil aus der YAML-Datei
    def __init__(self, vehicle_id, home, work, chores, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.PART_TIME
        self.chores = chores # This is a list of chore locations
        self.work = work
        self.config = config # Speichert die Konfiguration

        # --- NEU: Verwende Konfigurationswerte statt fester Zahlen ---
        self.work_time = self.time_from_float(random.normalvariate(
            config['work_start']['mean'],
            config['work_start']['std_dev']
        ))
        self.work_duration = self.timedelta_from_float(random.normalvariate(
            config['work_duration']['mean'],
            config['work_duration']['std_dev']
        ))

        # Parttime worker works for random days
        # --- NEU: Verwende Konfigurationswert statt fester Liste ---
        self.work_days = np.random.choice(
            range(5),
            np.random.choice(config['work_days_choices']),
            replace=False
        )

        # chore_days are all days (Mon-Sun) that are NOT work days
        self.chore_days = np.setdiff1d(range(7), self.work_days)

        # Distribute chores randomly around the day
        self.chore_times = []
        prev_time = 6
        max_time = 23
        for i in range(len(chores)):
            chores_remaining = (len(chores) - i)

            # Plan to have at least 30min between all chores
            remaining_time = max_time - prev_time - 0.5 * chores_remaining
            prev_time = random.uniform(prev_time, prev_time + remaining_time/chores_remaining)
            prev_time += 0.5
            self.chore_times.append(self.time_from_float(prev_time))

    # Generate a days worth of actions for the given agent.
    # Returns an array of RoutingStep objects
    def generate_day(self):
        actions = []
        if self.current_time.weekday() in self.work_days:
            # --- This is a WORK day (Logik unverändert) ---
            departure_time = (datetime.combine(date.today(), self.work_time) + timedelta(seconds=random.normalvariate(600,300))).time()
            self.set_time_t(departure_time)
            a1 = self.advance_step(self.work, self.work_duration)
            a2 = self.advance_step(self.home, timedelta(0))
            actions.extend([a1, a2])
            self.end_day()

        elif self.current_time.weekday() in self.chore_days:
            # --- UPDATED "DAY OFF" LOGIC ---
            # Verwendet jetzt Konfigurationswerte

            if not self.chores: # Skip if agent has no chores
                self.end_day()
                return []

            # --- NEU: Verwende Konfigurationswerte statt fester Zahlen ---
            num_activities = random.randint(
                self.config['day_off']['num_activities_min'],
                min(self.config['day_off']['num_activities_max'], len(self.chores))
            )

            # Get a random subset of activities and their times
            zipped_list = list(zip(self.chore_times, self.chores))
            random.shuffle(zipped_list)
            todays_activities = sorted(zipped_list[:num_activities])

            # --- NEU: Verwende Konfigurationswert statt fester Zahl ---
            chain_trips = random.random() < self.config['day_off']['chain_trips_prob'] and num_activities > 1

            if not chain_trips:
                # --- Path 1: Separate Trips ---
                for activity_time, activity_location in todays_activities:
                    # Set departure time from home
                    self.set_time_t(activity_time)
                    # --- NEU: Verwende Konfigurationswerte statt fester Zahlen ---
                    stay_duration = self.timedelta_from_float(random.uniform(
                        self.config['day_off']['stay_duration_min'],
                        self.config['day_off']['stay_duration_max']
                    ))

                    a1 = self.advance_step(activity_location, stay_duration)
                    a2 = self.advance_step(self.home, timedelta(0)) # Go home after
                    actions.extend([a1, a2])

            else:
                # --- Path 2: Chained Trips ---
                # Start from home for the first activity
                self.set_time_t(todays_activities[0][0])

                for activity_time, activity_location in todays_activities:
                    # --- NEU: Verwende Konfigurationswerte statt fester Zahlen ---
                    stay_duration = self.timedelta_from_float(random.uniform(
                        self.config['day_off']['stay_duration_min'],
                        self.config['day_off']['stay_duration_max']
                    ))

                    # Go from current location (Home or last activity) to the next one
                    a_activity = self.advance_step(activity_location, stay_duration)
                    actions.append(a_activity)

                # After the last activity, go home
                a_home = self.advance_step(self.home, timedelta(0))
                actions.append(a_home)

            self.end_day()

        else:
            # This should not be reachable, but as a fallback, just end the day
            self.end_day()

        return actions