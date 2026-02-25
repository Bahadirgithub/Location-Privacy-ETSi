### What is the Agents Module?

The **Agents module** is responsible for generating realistic vehicle mobility behavior within the traffic simulation framework.

- Each **Agent** represents a persistent vehicle.
- It generates daily behavioral patterns.
- It produces trips between locations.
- It manages simulation time consistently.
- It outputs `RoutingStep` objects for SUMO.

The module is fully configuration-driven and supports multi-day simulations.

---

### Architecture

The module is built around an abstract base class:

``` python
class Agent(ABC):
```

Concrete implementations:

- Worker
- PartTimeWorker
- NightWorker
- Freelance
- Homestay

Agent types are defined via:

``` python
class AgentType(Enum):
    WORKER = 0
    PART_TIME = 1
    HOMESTAY = 2
    FREELANCE = 3
    NIGHT_WORKER = 4
```

Each subclass implements its own `generate_day()` method.

---

### Core Design Principles

- **Abstract base class** enforces consistent behavior.
- Config-driven probabilistic mobility.
- No time regression allowed (time never moves backwards).
- Strictly increasing departure timestamps.
- SUMO-compatible routing output.
- Continuous time progression across multiple days.

---

### Time & Travel Model

#### Time Handling

- Simulation uses Python `datetime`.
- Internal logical time progresses continuously.
- Simulation start date is fixed at: `2022-02-28 00:00:00`

#### Acceleration Factor

- `TIME_ACCEL = 10.0`

Departure times written to SUMO are scaled as:

``` python
depart = floor((current_time - start_time) / TIME_ACCEL)
```

This compresses simulation time while preserving logical ordering.

#### Travel Time Estimation

Travel time is calculated as:

``` python
distance / 5.0  # ≈ 18 km/h
```

Then adjusted by:

- Random multiplier in `[1.3, 1.5]`
- Minimum travel time of `200` seconds
- Upper bound:

``` python
max(travel * 2.5, travel + 1200)
```

#### Departure Constraints

Each trip must satisfy:

``` python
depart >= last_depart + 1
depart >= last_end_depart + MIN_DEPART_GAP
```

This guarantees strictly increasing and valid departure times.

---

### Core Methods

#### `generate_demand(number_of_days)`

- Initializes simulation time.
- Calls `generate_day()` repeatedly.
- Generates trips across multiple days.
- Returns a list of `RoutingStep` objects.

#### `generate_day()`

- Implemented per agent type.
- Defines daily activities and behavioral logic.

#### `advance_step(destination, stay_time)`

- Computes Euclidean distance.
- Estimates travel time.
- Calculates valid departure timestamp.
- Creates a `RoutingStep`.
- Advances internal time by travel time and stay time.
- Updates current location.

---

### What is a RoutingStep?

Each call to `advance_step()` creates:

``` python
RoutingStep(agent, depart_time, origin, destination)
```

A `RoutingStep` represents:

- One trip in the SUMO route file.
- A departure timestamp (string).
- Origin edge.
- Destination edge.
- A unique trip ID.

The agent stores:

``` python
self.trip_ids.append(new_step.id)
```

This is required for:

- Transaction mapping.
- Trip reconstruction attacks.
- Wallet evaluation.

A `RoutingStep` is the atomic mobility unit of the simulation.

---

### Agent Types

#### Worker

- Full-time employee.
- Pattern: Home → Work → Home
- Optional grocery and errands.
- Work start can be fixed or Gaussian (`mean`, `std`).

#### PartTimeWorker

- Shorter working hours.
- Pattern: Home → Work → Home
- Optional leisure activity.

#### NightWorker

- Overnight shift.
- Correct cross-midnight duration:

``` python
(24 - start) + end
```

- Optional grocery and chores.

#### Freelance

- Flexible daily behavior.
- May stay home with some probability.
- Random number of activities.
- Optional chained trips:
  - Home → A → Home
  - Home → A → B → C → Home
- Prevents time rollback.

#### Homestay

- Caregiver-style behavior.
- Possible activities:
  - School drop-off
  - Grocery
  - Activity
  - Extra location
- Each activity is probability-based with its own time and duration distribution.

---

### Configuration Structure

Agents rely on configuration dictionaries.

Example:

``` yaml
work:
  mean: 8.0
  std: 0.5
  start: 8.0
  end: 16.0

grocery:
  prob: 0.3
  mean: 0.5
  std: 0.2
```

Common configuration fields:

- `prob`
- `mean`
- `std`
- `start`
- `end`
- `time_min`
- `time_max`
- `chain_trips_prob`

Durations are generated via `get_duration()`.

---

### Extending the Module

1. Subclass `Agent`.
2. Set `self.type`.
3. Implement `generate_day()`.
4. Use:
   - `self.set_time()`
   - `self.advance_step()`
   - `self.get_duration()`
   - `self.end_day()`

No other framework changes are required.