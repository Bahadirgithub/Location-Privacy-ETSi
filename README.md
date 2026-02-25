# ETSi – A Simulation Framework for Location Data in Electronic Toll Collection

This repository contains the **ETSi (Electronic Tolling Simulation)** framework, designed to systematically analyze reconstruction attacks on privacy-preserving Electronic Toll Collection (ETC) systems.

The goal of this project is to determine the extent to which physical constraints—such as travel times, road network topology, and vehicle behavior—leak sensitive location information, even when privacy-preserving systems (e.g., wallet-based tolling) are used. 

This README provides **technical** information about the framework's architecture, modules, and execution pipeline. For the theoretical background and scientific results, please refer to the accompanying paper in the documentation folder.

---

## 🏗️ Project Structure

The project is divided into four main modules, which can be run independently or orchestrated via the built-in pipeline (`run.py`):

1. **Agent/Demand Generation** (`/agent`)
2. **Traffic Simulation & Data Generation** (`/simulation`)
3. **Attacker** (`/attacker`)
4. **Evaluation** (`/evaluation`)