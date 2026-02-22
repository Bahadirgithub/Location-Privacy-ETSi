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

# Attacker – Rekonstruktion von Fahrten mittels Genetischem Algorithmus

## Überblick

Der attacker-Branch implementiert einen genetischen Algorithmus, um aus fragmentierten Transaktionsdaten (z. B. Detektor-Zeitstempel) vollständige Fahrten zu rekonstruieren.

Ziel ist es:
- einzelne Transaktionen zu Trips zu gruppieren
- Trips Fahrzeugen (Wallets) zuzuordnen

---

## Vorgehen

Der Angriff erfolgt in zwei Phasen:

1. *Trip-Rekonstruktion*  
   Gruppierung von Transaktionen zu plausiblen Fahrten

2. *Wallet-Zuordnung*  
   Zuordnung der Fahrten zu einzelnen Fahrzeugen

---

## Fitness-Funktion (Kernlogik)

Die Bewertung basiert auf Boni und Strafen:

### Boni
- *Korrektes Timing (PERFECT_TIME_BONUS)*  
  Belohnung für realistische Zeitabstände zwischen Detektoren

- *Trip-Länge (TRIP_LEN_MULT)*  
  Längere, konsistente Trips werden bevorzugt

### Strafen
- *Short Trips (SHORT_TRIP_PENALTY)*  
  Verhindert unrealistisch kurze Fahrten

- *Zeitreisen (TIMETRAVEL_PENALTY)*  
  Harte Strafe für negative Zeitdifferenzen

- *Teleportation (TELEPORTATION_PENALTY)*  
  Bestraft unmögliche Ortswechsel

- *Zu viele Trips (ACTIVE_TRIPS_PENALTY)*  
  Verhindert übermäßige Fragmentierung

---

## Zentrale Erkenntnisse (Analyse)

### Ingolstadt (realistisch)
- Benötigt *starke Strafen*, um Rauschen zu filtern
- Wichtige Parameter:
  - hohe Short-Trip-Strafen
  - hohe Struktur-Boni
- Grund: reale Daten sind unregelmäßig und fehleranfällig

### Spider (synthetisch)
- Profitiert von *präzisem Timing statt Strenge*
- Wichtige Parameter:
  - hoher PERFECT_TIME_BONUS
  - geringere Strafen
- Grund: saubere, gleichmäßige Netzstruktur

---

## Unterschied der Szenarien

| Eigenschaft        | Ingolstadt              | Spider                  |
|------------------|------------------------|--------------------------|
| Datenqualität     | verrauscht, real       | sauber, synthetisch      |
| Struktur          | unregelmäßig           | regelmäßig               |
| Optimale Strategie| Strenge & Filterung    | Timing & Präzision       |

---

## Implikation für Anonymisierung

Ein System ist schwer angreifbar, wenn:

- *keine klaren Start-/Endpunkte erkennbar sind*
- *Zeitstempel ungenau sind*
- *mehrere plausible Routen existieren*
- *Rauschen nicht eindeutig filterbar ist*

→ Ziel: Suchraum für den Angreifer maximieren, sodass der GA nicht konvergiert.