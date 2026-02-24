## Attacker - Traffic Deanonymization

This repository contains the **Attacker** module, which aims to reconstruct anonymized transaction data (e.g., from toll gantries). The objective is to recover vehicle routes (trips) and determine their association with specific wallets (vehicles).

#### Hybrid Architecture

The project uses a hybrid architecture:

- **Python:** Data parsing, graph construction, and orchestration
- **Rust:** Performance-critical computations *(genetic algorithm)*

#### Project Structure

```text
attacker/
├── attacks/            # Output: Generated XML files containing reconstructed attacks
├── reports/            # Output: Text reports with metrics (runtime, success rate)
├── src/                # Rust source code (lib.rs) for genetic algorithms
├── attack_random.py    # Baseline: Random assignment
├── attack_advanced.py  # Heuristic: Graph-based & Simulated Annealing
├── attack_genetic.py   # High-performance: Genetic algorithm (Rust)
├── Cargo.toml          # Rust configuration
├── pyproject.toml      # Build configuration for Python/Rust bindings
├── sumo/               # Input: Simulation data from SUMO
│   ├── attacker.xml        # The attacker's knowledge (transactions)
│   ├── challenger.xml      # Ground truth (for validation/reference)
│   └── simulated-times.xml # Generated statistical travel times
└── utils/              # Scripts to execute attacks
    └── simulateTime.py     # Tool for generating travel time statistics
``` 

# Attacker – Reconstruction of Trips Using a Genetic Algorithm

## Overview
The `attacker` branch implements a genetic algorithm to reconstruct complete trips from fragmented transaction data (e.g., detector timestamps).

The goal is to:
- group individual transactions into trips
- assign trips to vehicles (wallet)

---

## Approach
The attack is performed in two phases:
1. **Trip Reconstruction**

   Grouping Transactions into plausible trips
2. **Wallet Assignment**

   Assigning trips to individual vehicles

---

## Genetic Algorithm

The GA operates iteratively on a population of candidate solutions (individuals). In each generation:

- **Selection:** High-quality solutions are preferentially selected

- **Mutation:** Genomes are randomly modified (small and large changes) to generate new candidate solutions

- **Evolution:** A new population is formed from mutated offspring, typically combined with elitism (best individuals are preserved)

---

## Fitness Function (Core Logic)

Evaluation is based on rewards and penalties:

## Rewards

- **Correct Timing (`PERFECT_TIME_BONUS`)**

  Rewards realistic time differences between detectors

- **Trip Length (`TRIP_LEN_MULT`)**

  Prefers longer, consistent trips

## Penalties

- **Short Trips (`SHORT_TRIP_PENALTY`)**

  Prevents unrealistically short trips

- **Time Travel (`TIMETRAVEL_PENALTY`)**

  Strong penalty for negative time differences

- **Teleportation (`TELEPORTATION_PENALTY`)**

  Penalizes impossible spatial transitions

- **Too Many Trips (`ACTIVE_TRIPS_PENALTY`)**

  Prevents excessive fragmentation

---

## Key Insights (Analysis)
### Ingolstadt (realistic scenario)
- Requires **strong penalties** to filter noise
- Important parameters:
  - high `SHORT_TRIP_PENALTIES`

  - strong structural rewards

- Reason: real-world data is irregular and error-prone

### Spider (synthetic scenario)
- Benefits from **precise timing rather than strict penalties**
- Important parameters:
  - high `PERFECT_TIME_BONUS`
  - lower penalties

- Reason: clean and regularly structured network

--- 

## Implications for Anonymization
A system becomes difficult to attack when:

- no clear start/end points are identifiable
- timestamps are imprecise
- multiple plausible routes exist
- noise cannot be reliably filtered

→ Goal: maximize the attacker’s search space so that the GA cannot converge effectively.