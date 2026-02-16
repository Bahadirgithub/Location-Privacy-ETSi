## Attacker - Traffic Deanonymization
Dieses Repository enthält das `Attacker-Modul`, das darauf abzielt, anonymisierte Transaktionsdaten (z. B. von Mautbrücken) zu rekonstruieren. Das Ziel ist es, Fahrzeugrouten (Trips) wiederherzustellen und die Zugehörigkeit zu bestimmten Wallets (Fahrzeugen) zu ermitteln.

#### Das Projekt nutzt eine hybride Architektur:

**Python:** Für Datenparsing, Graphen-Erstellung und Orchestrierung.

**Rust:** Für performance-kritische Berechnungen *(genetischer Algorithmus)*
#### Projektstruktur:
``` text
attacker/
├── attacks/            # Output: Generierte XML-Dateien mit den rekonstruierten Angriffen
├── reports/            # Output: Textberichte mit Metriken (Laufzeit, Erfolgsrate)
├── src/                # Rust Source Code (lib.rs) für die genetischen Algorithmen
├── attack_random.py      # Baseline: Zufällige Zuweisung
├── attack_advanced.py    # Heuristik: Graphen & Simulated Annealing
├── attack_genetic.py     # High-Performance: Genetischer Algorithmus (Rust)
├── Cargo.toml            # Rust Konfiguration
├── pyproject.toml        # Build-Konfiguration für Python/Rust-Binding
├── sumo/               # Input: Simulationsdaten aus SUMO
│   ├── attacker.xml          # Das "Wissen" des Angreifers (Transaktionen)
│   ├── challenger.xml        # Ground Truth (zur Validierung/Lösung)
│   └── simulated-times.xml   # Generierte statistische Reisezeiten
└── utils/              # Skripte zur Ausführung der Angriffe
    └── simulateTime.py       # Tool zur Generierung der Reisezeiten-Statistik
```