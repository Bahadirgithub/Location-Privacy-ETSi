from datetime import timedelta, time, datetime
import random
import math
from model.Agent import Agent
from model.AgentType import AgentType


class Freelance(Agent):
    """
    Freelance Agent: Arbeitet unabhängig, hat flexible Zeitpläne.
    """

    def __init__(self, vehicle_id, home, leisure_locations, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.FREELANCE
        self.config = config

        if leisure_locations is None:
            self.leisure_locations = []
        else:
            self.leisure_locations = list(leisure_locations)

    def generate_day(self):
        actions = []

        if (random.random() < self.config.get('stay_home_prob', 0.0)
                or not self.leisure_locations):
            self.end_day()
            return []

        # Anzahl Aktivitäten bestimmen
        act_conf = self.config['activity']
        num_min = act_conf.get('num_activities_min', 1)
        num_max = act_conf.get('num_activities_max', len(self.leisure_locations))
        num_max = max(num_min, num_max)  # Safety

        count = random.randint(num_min, min(num_max, len(self.leisure_locations)))
        if count == 0:
            self.end_day()
            return []

        todays_locations = random.sample(self.leisure_locations, count)
        todays_schedule = []

        # Zeitfenster für Aktivitäten
        current_time_float = act_conf.get('time_min', 9.0)
        max_time_float = act_conf.get('time_max', 20.0)

        for i in range(count):
            remaining = count - i
            buffer = 0.5 * remaining
            window = max_time_float - current_time_float - buffer

            if window <= 0:
                start_time = current_time_float + 0.1
            else:
                step = window / remaining
                start_time = random.uniform(current_time_float, current_time_float + step)

            todays_schedule.append((self.time_from_float(start_time), todays_locations[i]))
            current_time_float = start_time + 0.5

        # Trips ausführen
        chain_trips = (random.random() < act_conf.get('chain_trips_prob', 0.0) and count > 1)

        if not chain_trips:
            # Einzelne Trips
            for activity_time, location in todays_schedule:

                # --- FIX START ---
                # Check if we are early or late. Never set time backwards!
                target_start = datetime.combine(self.current_time.date(), activity_time)

                if target_start > self.current_time:
                    # We are early, wait until schedule
                    self.set_time(activity_time)
                else:
                    # We are late, start immediately (pass)
                    # This preserves the travel time accumulated from the previous trip
                    pass
                # --- FIX END ---

                # WICHTIG: Hier wird nun mean/std für die Dauer verwendet
                stay_duration = self.get_duration(act_conf)

                a1 = self.advance_step(location, stay_duration)
                a2 = self.advance_step(self.home, timedelta(0))
                actions.extend([a1, a2])
        else:
            # Trip-Kette (This block was already safe because it uses flow logic)
            first_time = todays_schedule[0][0]
            self.set_time(first_time)

            for _, location in todays_schedule:
                stay_duration = self.get_duration(act_conf)
                actions.append(self.advance_step(location, stay_duration))

            actions.append(self.advance_step(self.home, timedelta(0)))

        self.end_day()
        return actions