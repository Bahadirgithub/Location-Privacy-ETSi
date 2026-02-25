# ETSi – Simulation Framework for Location Privacy in Electronic Toll Collection

This repository contains the **ETSi (Electronic Tolling Simulation)** framework. It is designed to systematically analyze reconstruction attacks on privacy-preserving Electronic Toll Collection (ETC) systems. 

The goal is to investigate how much sensitive location information is leaked through physical constraints (travel times, network topology, traffic behavior) even when privacy-enhancing billing systems (wallets) are used.

---

## 🏗️ Project Structure & Modules

The project is divided into four main modules, centrally orchestrated via the pipeline (`run.py`):

### 1. Agents & Demand Generation (`/agent`)
Generates realistic, configuration-driven mobility behavior across multiple days.
* **Agent Types:** Worker, Part-Time, Night Worker, Freelance, Homestay.
* **Time Model:** Continuous time progression with no backward jumps. Travel times are based on Euclidean distances with realistic variance.

### 2. Traffic Simulation & Data Generation (`/simulation`)
Executes a SUMO simulation based on the generated agent routes.
* **Transactions:** Records detector crossings and filters out unrealistic double detections.
* **Data Split:** Generates *Challenger Knowledge* (complete ground truth) and *Attacker Knowledge* (anonymized transaction fragments + aggregated wallet totals).

### 3. Attacker (`/attacker`)
Attempts to reconstruct the anonymized transactions back into trips and wallets (vehicles).
* **Heuristic Attack (`attack_advanced.py`):** Uses graph-based routing and *Simulated Annealing* to reconstruct trips based on average travel times.
* **Genetic Algorithm (`attack_genetic.py`):** A high-performance, evolutionary algorithm written in **Rust**. It globally optimizes the search space using a fitness function (rewards realistic times/lengths; severely penalizes time travel or teleportation).

### 4. Evaluation (`/evaluation`)
Compares the attacker's reconstructed data against the ground truth. The primary metric used is the **F1-Score** to ensure fair evaluation, especially for slightly fragmented trips.

---

## 🚀 Setup and Compilation

The project uses Python for orchestration and Rust for the computationally intensive genetic algorithm.

### Prerequisites
1. Python 3.6+
2. [Rust Compiler](https://rustup.rs/) (verify with `rustc --version`).

### Installation
1. Clone the repository and navigate into the folder.
2. Create and activate a virtual Python environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate

---

⚠️ Known Issues & Notes
- **SUMO Instability:** Running extremely dense simulations can sometimes cause SUMO to generate physical artifacts (e.g., overlapping trips).