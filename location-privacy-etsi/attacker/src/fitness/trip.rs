use crate::types::*;
use rayon::prelude::*;
use std::collections::{HashSet, HashMap};
use std::f64::consts::E;

pub fn fitness_trip(individual: &[u32],  transactions: &[Transaction], simulated_times: &HashMap<(u32, u32), SimulatedTime>) -> f64{
    let max_trip_id = *individual.iter().max().unwrap_or(&0) as usize;
    let mut trips: Vec<Vec<&Transaction>> = vec![Vec::new(); max_trip_id + 1]; //Leere Trip Liste erstellen
    let transaction_size = transactions.len();
    let mut time_dif: f64 = 0.0;
    let mut penalty: f64 = 0.0;
    let mut bonus: f64 = 0.0;

    //Arten der Strafen
    const DEATH_PENALTY: f64 = 100_000.0;

    for (trans_id, trip_id) in individual.iter().enumerate() {
        trips[*trip_id as usize].push(&transactions[trans_id]); //Trip Liste befüllen
    }

    let num_active_trips = trips.iter().filter(|t| !t.is_empty()).count();
    penalty += (num_active_trips as f64) * 200.0;

    let mut location_stats: HashMap<u32, (i32, i32)> = HashMap::new();
    for trip in trips.iter_mut(){
        if trip.is_empty() { continue; }

        //Sortieren der Transaktionen nach Zeitpunkt
        trip.sort_unstable_by_key(|t| t.time); 

        // Start-/Enddetektor erfassen
        let start_det = trip.first().unwrap().detector;
        let end_det = trip.last().unwrap().detector;

        let entry_start = location_stats.entry(start_det).or_insert((0, 0));
        entry_start.0 += 1; // +1 Start Count

        let entry_end = location_stats.entry(end_det).or_insert((0, 0));
        entry_end.1 += 1; // +1 End Count

        let trip_len = trip.len();
        //Bewertung der Trip-Länge
        if trip_len < 2 {
            penalty += DEATH_PENALTY; //Auf keinen Fall einzelne Trips!
            continue;
        }
        // In ingolstadt trip size 3-43
        else if trip_len < 4 {
            penalty += 200.0;
        }
        else if trip_len > (transaction_size / 10){ //Trip ist so groß wie 10% der Transaktionen -> Strafe
            penalty += 2000.0;
        }
        else {
            let l = 10_000.0;  // Maximale Belohnung
            let k = 0.2;     // Steigung der Funktion
            let x0 = 20.0;   // Wendepunkt bei Trip-Länge
                
            // Berechnung des Bonus mit der sigmoiden Funktion
            bonus += l / (1.0 + E.powf(-k * (trip_len as f64 - x0)));
        }

        //Detektor darf nie doppel vorkommen
        let mut detectors_seen: HashSet<u32> = HashSet::new();
        for trans in trip.iter(){
            let detector_id = trans.detector;
            if !detectors_seen.insert(detector_id){
                //False bedeutet Id wurde bereits hinzugefügt
                penalty += DEATH_PENALTY;
                break;
            }
        }

        //Segment-Analyse
        let mut trip_valid_segments = 0;
        let total_segments = trip.len() - 1;

        for window in trip.windows(2) {
            let current = window[0];
            let next = window[1];

            //Zeitabweichung berechnen
            let dt: f64 = next.time as f64 - current.time as f64;

            if dt <= 0.0 { //Zeitreisen verboten!
                penalty += DEATH_PENALTY; // Tödliche Strafe
                continue;
            }

            let sim_data = search_time(current.detector, next.detector, simulated_times);

            if sim_data.from_detector == 9999 {
                // Ist die Zeitdifferenz plausibel? (Oft fehlende Verbindungen in Simulated Times)
                if dt > 1.0 && dt < 60.0 {
                    penalty += 100.0 + dt;
                } 
                else if dt < 120.0 {
                    penalty += 1000.0;
                }
                else {
                    // Unmögliche Zeit (Teleportation) -> TÖDLICHE Strafe
                    penalty += DEATH_PENALTY; 
                }
            }
            else{
                let min_t = sim_data.min as f64;
                let max_t = sim_data.max as f64;
                let avg_t = sim_data.avg as f64;

                if dt >= min_t && dt <= max_t {
                    // Perfekt
                    bonus += 300.0;
                    
                    // Zusatz-Bonus für Nähe zum Durchschnitt (Genauigkeit)
                    let diff_avg = (dt - avg_t).abs();
                    bonus += 50.0 - diff_avg;
                    
                    trip_valid_segments += 1;
                } else {
                    // Quadratische Strafe 
                    let violation = if dt < min_t { min_t - dt } else { dt - max_t };
                    time_dif += violation.powi(2) * 0.1;
                    penalty += 50.0; // Grundstrafe für "Out of Bounds"
                }
            }
        }
        if trip_valid_segments > 0 && trip_valid_segments == total_segments {
            // Wenn alle Segmente valid sind gibt es einen Bonus
            bonus += (trip_len as f64) * 100.0;
        }
    }
    //Globale Analyse
    for (_, (starts, ends)) in location_stats {
        if starts > 0 && ends > 0 {
            //Ort ist sowohl Start als auch Ende
            bonus += 1000.0;
        }

        let total_usage = starts + ends;
        if total_usage >= 4 {
            //Ort wird öfters benutzt (HUB: Zuhause oder Arbeit)
            bonus += 500.0 * (total_usage as f64);
        }
    }


    let score = (100.0 + bonus) / (1.0 + time_dif + penalty);

    score
}

fn search_time(from_id: u32, to_id: u32, simulated_times: &HashMap<(u32, u32), SimulatedTime>) -> SimulatedTime {
    simulated_times.get(&(from_id, to_id))
        .cloned()
        .unwrap_or_else(|| SimulatedTime { from_detector: 9999, to_detector: 9999, avg: -1.0, min: -1.0, max: -1.0 })
}

pub fn calculate_trip_fitness(population: Vec<Individual>, transactions: &[Transaction], simulated_times: &HashMap<(u32, u32), SimulatedTime>) -> Vec<Individual>{
    population.into_par_iter().map(|ind| {
        Individual {
            genome: ind.genome.clone(),
            score: fitness_trip(&ind.genome, transactions, simulated_times),
        }
    }).collect()
}