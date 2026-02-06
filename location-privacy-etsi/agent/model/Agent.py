import math
import random
from datetime import time, datetime, timedelta
import numpy as np
from abc import ABC, abstractmethod

# Requires RoutingStep to be imported or available in path
from model.RoutingStep import RoutingStep

class Agent(ABC):
    """
    Abstract base class for all vehicle agents.
    Manages time, location, and route logging.
    """
    def __init__(self, vehicle_id, home):
        self.id = vehicle_id
        self.home = home

        self.current_time = None
        self.start_time = None
        self.current_location = home
        self.trip_ids = []
        #Track last departure
        self.last_depart = -1

    def generate_demand(self, number_of_days):
        """Generate demand for N days starting from a fixed date."""
        output = []
        self.current_location = self.home
        # Fixed start date as per your original code
        self.start_time = self.current_time = datetime.strptime('2022-02-28 00:00:00', '%Y-%m-%d %H:%M:%S')
        stop_timedate = self.current_time + timedelta(days=number_of_days)

        while self.current_time < stop_timedate:
            next_day = self.generate_day()
            if next_day:
                output.extend(next_day)
        return output

    @abstractmethod
    def generate_day(self):
        """Implementation specific to the agent type (Worker, Freelance, etc.)"""
        pass

    def advance_step(self, destination, stay_time):
        """
        Moves the agent to the destination and records the trip.
        stay_time: timedelta object representing how long they stay at the destination.
        """
        self.print_route(self.current_time, self.current_location, destination)

        #Calculate Distance (Euclidean)
        dx = self.current_location.x - destination.x
        dy = self.current_location.y - destination.y
        dist_meters = math.sqrt(dx * dx + dy * dy)

        #Estimate Travel Time
        avg_speed_mps = 5 #5m/s = 18km/h
        travel_seconds = dist_meters / avg_speed_mps

        #Add buffer
        travel_seconds *= random.uniform(1.3, 1.5)
        #Ensure min travel time
        travel_seconds = max(200.0, travel_seconds)

        # Calculate departure time relative to simulation start
        # NOTE: The /10 factor speeds up the simulation depart times.
        TIME_ACCEL = 10.0
        # Ensure this matches your SUMO config.
        total_seconds = (self.current_time - self.start_time).total_seconds()
        depart_int = int(math.floor(total_seconds / TIME_ACCEL))

        if depart_int < self.last_depart:
            depart_int = self.last_depart + 1

        self.last_depart = depart_int
        depart = str(depart_int)

        new_step = RoutingStep(self, depart, self.current_location, destination)
        self.trip_ids.append(new_step.id)

        self.current_time += timedelta(seconds=travel_seconds)

        self.current_location = destination
        self.current_time += stay_time
        return new_step

    # --- HELPER FUNCTIONS ---

    def set_time(self, time_input):
        """
        Sets the current time of the day.
        Added safety: Never travels backwards
        Accepts:
        - float (e.g. 14.5 = 14:30)
        - datetime.time object
        """
        if isinstance(time_input, (float, int)):
            t = self.time_from_float(float(time_input))
        elif isinstance(time_input, time):
            t = time_input
        else:
            raise ValueError(f"set_time expects float or datetime.time, got {type(time_input)}")

        desired_dt = datetime.combine(self.current_time.date(), t)

        if desired_dt > self.current_time:
            self.current_time = desired_dt

    def get_duration(self, config_entry):
        """
        Calculates a duration based on config.
        Supports both Uniform (min/max) and Gaussian (mean/std) distributions.
        Returns: timedelta
        """
        hours = 0.0

        # Option A: Gaussian (Normal) Distribution
        if 'mean' in config_entry and 'std' in config_entry:
            val = random.gauss(config_entry['mean'], config_entry['std'])
            # Ensure we don't get negative time or extremely long times if desired
            # basic clamping to positive:
            hours = max(0.1, val)

        # Option B: Uniform Distribution (Min/Max)
        elif 'stay_min' in config_entry and 'stay_max' in config_entry:
            hours = random.uniform(config_entry['stay_min'], config_entry['stay_max'])

        # Option C: Fixed time or alternative keys (fallback)
        elif 'duration' in config_entry:
            hours = config_entry['duration']

        else:
            # Default fallback if config is missing keys
            hours = 1.0

        return self.timedelta_from_float(hours)

    def print_route(self, timestamp, start, end):
        # Using string formatting for cleaner output
        print(f"{self.id} at {timestamp.strftime('%H:%M:%S')}: {start.edge_id} -> {end.edge_id}")

    def time_from_float(self, timefloat):
        # Handle overflow (e.g. 24.5 -> 00:30) if necessary,
        # but usually start times are 0-24.
        timefloat = max(0.0, min(23.999, float(timefloat)))
        hours = int(math.floor(timefloat))
        minutes = int((timefloat - hours) * 60)
        return time(hours, minutes)

    def timedelta_from_float(self, timefloat):
        hours = int(math.floor(timefloat))
        minutes = int((timefloat - hours) * 60)
        return timedelta(hours=hours, minutes=minutes)

    def end_day(self):
        """Moves clock to the start of the next day (00:00)."""
        self.current_time += timedelta(days=1)
        self.current_time = datetime.combine(self.current_time.date(), time(0, 0))

    def set_time_t(self, t):
        self.current_time = datetime.combine(self.current_time.date(), t)