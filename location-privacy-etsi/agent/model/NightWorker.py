from datetime import timedelta
from datetime import time
from datetime import datetime
from datetime import date

import math
import random
import numpy as np

from model.Agent import Agent
from model.AgentType import AgentType



class NightWorker(Agent):
    # Constructor
    # id: A vehicle ID for the given agent
    # locations: A list of locations the agent is able to visit
    # home: A distinct home location
    # chore: chore that is done during the week and on the weekend
    # work: A distinct work location
    # config: Das Konfigurations-Profil aus der YAML-Datei
    def __init__(self, vehicle_id, home, work, chore, weekend_chores, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.WORKER # This was likely a copy-paste error in the original, but we'll leave it
        self.chore = chore
        self.work = work
        self.weekend_chores = weekend_chores
        self.config = config # Speichert die Konfiguration

        # --- NEU: Verwende Konfigurationswerte statt fester Zahlen ---
        work_time_float = random.normalvariate(
            config['work_start']['mean'],
            config['work_start']['std_dev']
        )
        work_duration_float = random.normalvariate(
            config['work_duration']['mean'],
            config['work_duration']['std_dev']
        )
        self.work_time = self.time_from_float(work_time_float)
        self.work_duration = self.timedelta_from_float(work_duration_float)

        # Die alte Logik war kompliziert und an die Arbeitszeit gekoppelt.
        # Die neue Logik liest einfach die in der YAML definierten Grenzen.
        # --- NEU: Verwende Konfigurationswerte statt fester Zahlen ---
        chore_time_float = random.uniform(
            config['weekday_chore']['start_min'],
            config['weekday_chore']['start_max']
        )
        chore_duration_float = random.uniform(
            config['weekday_chore']['duration_min'],
            config['weekday_chore']['duration_max']
        )
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
            # --- Weekday logic is unchanged (verwendet die oben dynamisch gesetzten Zeiten) ---
            self.set_time_t(self.chore_time)
            a1 = self.advance_step(self.chore, self.chore_duration)
            a2 = self.advance_step(self.home, timedelta(0))
            self.set_time_t(self.work_time)
            a3 = self.advance_step(self.work, self.work_duration)
            a4 = self.advance_step(self.home, timedelta(0))
            actions.extend([a1, a2, a3, a4])
            self.end_day()
        else:
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
                    # Set departure time from home
                    self.set_time_t(activity_time)
                    # --- NEU: Verwende Konfigurationswerte statt fester Zahlen ---
                    stay_duration = self.timedelta_from_float(random.uniform(
                        self.config['weekend']['stay_duration_min'],
                        self.config['weekend']['stay_duration_max']
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
                        self.config['weekend']['stay_duration_min'],
                        self.config['weekend']['stay_duration_max']
                    ))

                    # Go from current location (Home or last activity) to the next one
                    a_activity = self.advance_step(activity_location, stay_duration)
                    actions.append(a_activity)

                # After the last activity, go home
                a_home = self.advance_step(self.home, timedelta(0))
                actions.append(a_home)

            self.end_day()
        return actions
