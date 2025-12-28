use crate::types::*;
use rayon::prelude::*;
use std::collections::HashSet;
use std::collections::HashMap;

pub fn fitness_trip(individual: &[u32],  transactions: &[Transaction], simulated_times: &HashMap<(u32, u32), SimulatedTime>) -> f64{
    let max_trip_id = *individual.iter().max().unwrap_or(&0) as usize;
    let mut trips: Vec<Vec<&Transaction>> = vec![Vec::new(); max_trip_id + 1]; //Leere Trip Liste erstellen
    let mut total_error: f64 = 0.0;
    let mut penalty: f64 = 0.0;
    let mut bonus: f64 = 0.0;

    let num_active_trips = individual.iter().collect::<HashSet<_>>().len();
    penalty += (num_active_trips as f64) * 500.0;

    for (trans_id, trip_id) in individual.iter().enumerate() {
        trips[*trip_id as usize].push(&transactions[trans_id]); //Trip Liste befüllen
    }

    for trip in trips.iter_mut(){
        if trip.is_empty() { continue; }

        //Detektor darf nie doppel vorkommen
        let mut detectors_seen: HashSet<u32> = HashSet::new();
        for trans in trip.iter(){
            let detector_id = trans.detector;
            if !detectors_seen.insert(detector_id){
                //False bedeutet Id wurde bereits hinzugefügt
                penalty += 5000.0;
                break;
            }
        }


        trip.sort_unstable_by_key(|t| t.time); //Sortieren der Transaktionen nach Zeitpunkt

        let trip_len = trip.len();
        //Bewertung der Trip-Länge
        if trip_len < 2 {
            penalty += 2000.0;
            continue;
        } else {
            bonus += (trip_len as f64).powi(2) * 10.0;
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
                penalty += 10000.0; // Tödliche Strafe
                continue;
            }

            let sim_data = search_time(current.detector, next.detector, simulated_times);

            if sim_data.from_detector == 9999 {
                // Ist die Zeitdifferenz plausibel? (Oft fehlende Verbindungen in Simulated Times)
                if dt > 2.0 && dt < 60.0 {
                    bonus += 100.0 - dt;
                } else {
                    // Unmögliche Zeit (Teleportation) -> TÖDLICHE Strafe
                    penalty += 5000.0; 
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
                    total_error += violation.powi(2) * 0.5;
                    penalty += 50.0; // Grundstrafe für "Out of Bounds"
                }
            }
        }
        if trip_valid_segments > 0 && trip_valid_segments == total_segments {
            // Wenn alle Segmente valid sind gibt es einen Bonus
            bonus += (trip_len as f64) * 100.0;
        }
    }
    let score = (10000.0 + bonus) / (1.0 + total_error + penalty);

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