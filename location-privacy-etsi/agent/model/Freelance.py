from datetime import timedelta, time, datetime
import random
import math
from model.Agent import Agent
from model.AgentType import AgentType

class Freelance(Agent):
    """
    Freelance Agent: Arbeitet unabhängig, hat flexible Zeitpläne und erledigt
    verschiedene Freizeitaktivitäten (Leisure) über den Tag verteilt.
    """

    def __init__(self, vehicle_id, home, leisure_locations, config):
        super().__init__(vehicle_id, home)
        self.type = AgentType.FREELANCE
        self.config = config

        # Sicherstellen, dass Locations als Liste vorliegen
        if leisure_locations is None:
            self.leisure_locations = []
        else:
            self.leisure_locations = list(leisure_locations)

    def generate_day(self):
        actions = []

        # 1. Prüfen, ob der Agent heute zuhause bleibt
        # (z.B. Home Office ohne Außentermine)
        if (random.random() < self.config.get('stay_home_prob', 0.0)
                or not self.leisure_locations):
            self.end_day()
            return []

        # 2. Anzahl der Aktivitäten für heute bestimmen
        num_activities_min = self.config['activity'].get('num_activities_min', 1)
        num_activities_max = self.config['activity'].get('num_activities_max', len(self.leisure_locations))

        # Sicherstellen, dass max >= min
        num_activities_max = max(num_activities_min, num_activities_max)

        # Tatsächliche Anzahl (begrenzt durch verfügbare Orte)
        count = random.randint(num_activities_min, min(num_activities_max, len(self.leisure_locations)))

        if count == 0:
            self.end_day()
            return []

        # 3. Zufällige Orte auswählen
        todays_locations = random.sample(self.leisure_locations, count)

        # 4. Zeiten für diese Aktivitäten generieren
        # Wir generieren hier dynamisch Zeiten, damit jeder Tag anders ist.
        todays_schedule = []

        current_time_float = self.config['activity']['time_min']   # z.B. 9.0 (09:00 Uhr)
        max_time_float = self.config['activity']['time_max']       # z.B. 20.0 (20:00 Uhr)

        for i in range(count):
            remaining_activities = count - i
            # Puffer von 30 Min (0.5h) pro Aktivität einplanen, damit sie nicht alle am Ende kleben
            buffer = 0.5 * remaining_activities
            available_window = max_time_float - current_time_float - buffer

            if available_window <= 0:
                # Falls Zeit knapp ist, einfach kleine Schritte machen
                start_time = current_time_float + 0.1
            else:
                # Zufälligen Startpunkt im möglichen Fenster wählen
                # Wir schieben das Fenster etwas nach vorne durch / remaining_activities
                step = available_window / remaining_activities
                start_time = random.uniform(current_time_float, current_time_float + step)

            # Zeit in Schedule speichern (als datetime.time)
            todays_schedule.append((self.time_from_float(start_time), todays_locations[i]))

            # Zeit für nächsten Loop hochsetzen (mindestens 30 min später)
            current_time_float = start_time + 0.5

        # 5. Trips generieren (Chain oder Einzeln)
        chain_trips = (
                random.random() < self.config['activity'].get('chain_trips_prob', 0.0)
                and count > 1
        )

        if not chain_trips:
            # Separate Trips: Zuhause -> Ziel -> Zuhause
            for activity_time, location in todays_schedule:
                self.set_time(activity_time)

                # Dauer aus Config (unterstützt jetzt Mean/Std)
                stay_duration = self.get_duration(self.config['activity'])

                a1 = self.advance_step(location, stay_duration)
                a2 = self.advance_step(self.home, timedelta(0))
                actions.extend([a1, a2])

        else:
            # Trip-Kette: Zuhause -> Ziel A -> Ziel B ... -> Zuhause
            # Startzeit ist die Zeit der ersten Aktivität
            first_time = todays_schedule[0][0]
            self.set_time(first_time)

            for _, location in todays_schedule:
                stay_duration = self.get_duration(self.config['activity'])

                # Fahrt zum Ziel
                a_loc = self.advance_step(location, stay_duration)
                actions.append(a_loc)

            # Ganz am Ende zurück nach Hause
            a_home = self.advance_step(self.home, timedelta(0))
            actions.append(a_home)

        self.end_day()
        return actions