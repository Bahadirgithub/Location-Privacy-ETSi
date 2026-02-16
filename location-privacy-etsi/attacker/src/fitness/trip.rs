use crate::types::*;
use rayon::prelude::*;
use std::collections::{HashSet, HashMap};

#[derive(Clone, Copy)]
struct TripPoint {
    id: usize,
    loc: i32,     // Location ID (Detektor)
    time: i32,
    used: bool,
}

pub fn fitness_trip(individual: &[u32],  transactions: &[Transaction], simulated_times: &HashMap<(u32, u32), SimulatedTime>) -> f64{
    let max_trip_id = *individual.iter().max().unwrap_or(&0) as usize;
    let mut trips: Vec<Vec<&Transaction>> = vec![Vec::new(); max_trip_id + 1]; //Leere Trip Liste erstellen
    let mut time_dif: f64 = 0.0;
    let mut penalty: f64 = 0.0;
    let mut bonus: f64 = 0.0;

    /*Gefundene Parameter: Spider
    const TRIP_LEN_EXP: f64 = 0.79;
    const TRIP_LEN_MULT: f64 = 339.2;
    const SHORT_TRIP_PENALTY: f64 = 9863.8;
    const TIMETRAVEL_PENALTY: f64 = 91318.7;
    const TELEPORTATION_PENALTY: f64 = 66647.9;
    const ACTIVE_TRIPS_PENALTY: f64 = 339.5;
    const SIM_DATA_PENALTY: f64 = 229;

    const PERFECT_TIME_BONUS: f64 = 967.45;
    const DETECTOR_MATCH_BONUS: f64 = 2085.6;
    */

    //Gefundene Parameter: Ingolstadt
    const TRIP_LEN_EXP: f64 = 0.79;
    const TRIP_LEN_MULT: f64 = 109.9;
    const SHORT_TRIP_PENALTY: f64 = 10528.5;
    const TIMETRAVEL_PENALTY: f64 = 90261.5;
    const TELEPORTATION_PENALTY: f64 = 79404.8;
    const ACTIVE_TRIPS_PENALTY: f64 = 353.6;
    const SIM_DATA_PENALTY: f64 = 243.3;

    const PERFECT_TIME_BONUS: f64 = 909.1;
    const DETECTOR_MATCH_BONUS: f64 = 5211.1;

    for (trans_id, trip_id) in individual.iter().enumerate() {
        trips[*trip_id as usize].push(&transactions[trans_id]); //Trip Liste befüllen
    }

    let num_active_trips = trips.iter().filter(|t| !t.is_empty()).count();
    penalty += (num_active_trips as f64) * ACTIVE_TRIPS_PENALTY;

    //Start und Endpunkte
    let mut start_points: Vec<TripPoint> = Vec::with_capacity(num_active_trips);
    let mut end_points: Vec<TripPoint> = Vec::with_capacity(num_active_trips);
    for trip in trips.iter_mut(){
        if trip.is_empty() { continue; }

        //Sortieren der Transaktionen nach Zeitpunkt
        trip.sort_unstable_by_key(|t| t.time);

        // Start-/Enddetektor erfassen
        let start_trans = trip.first().unwrap();
        let end_trans = trip.last().unwrap();


        //Start-/Endwerte befüllen
        start_points.push(TripPoint {
            id: start_trans.id as usize,
            loc: start_trans.detector as i32,
            time: start_trans.time as i32,
            used: false
        });

        end_points.push(TripPoint {
            id: end_trans.id as usize,
            loc: end_trans.detector as i32,
            time: end_trans.time as i32,
            used: false // bei Endpunkten irrelevant
        });

        let trip_len = trip.len();
        //Bewertung der Trip-Länge
        if trip_len < 2 {
            penalty += SHORT_TRIP_PENALTY; //Auf keinen Fall einzelne Trips!
            continue;
        }
        else {
            let len_exp = TRIP_LEN_EXP;
            let len_mult = TRIP_LEN_MULT;

            bonus += (trip_len as f64).powf(len_exp) * len_mult;
        }

        //Detektor darf nie doppel vorkommen
        let mut detectors_seen: HashSet<u32> = HashSet::new();
        for trans in trip.iter(){
            let detector_id = trans.detector;
            if !detectors_seen.insert(detector_id){
                //False bedeutet Id wurde bereits hinzugefügt
                penalty += 10_000.0;
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
                penalty += TIMETRAVEL_PENALTY; // Tödliche Strafe
                continue;
            }

            let sim_data = search_time(current.detector, next.detector, simulated_times);

            if sim_data.from_detector == 9999 {
                // Ist die Zeitdifferenz plausibel? (Oft fehlende Verbindungen in Simulated Times)
                if dt > 1.0 && dt < 45.0 {
                    penalty += SIM_DATA_PENALTY + (dt * 5.0);
                }
                else {
                    // Unmögliche Zeit (Teleportation) -> TÖDLICHE Strafe
                    penalty += TELEPORTATION_PENALTY;
                }
            }
            else{
                let min_t = sim_data.min as f64;
                let max_t = sim_data.max as f64;
                let avg_t = sim_data.avg as f64;

                let range_width = max_t - min_t;
                let min_sigma = (avg_t * 0.1).max(5.0); //Min. 10% Abweichung oder 5 Sekunden

                //Standardabweichung berechnen
                let sigma = (range_width / 4.0).max(min_sigma);

                //Weiche Grenzen basierend auf Sigma
                let soft_min = avg_t - (3.0 * sigma);
                let soft_max = avg_t + (3.0 * sigma);

                if dt >= soft_min && dt <= soft_max {
                    // Perfekt
                    bonus += PERFECT_TIME_BONUS;

                    // Zusatz-Bonus für Nähe zum Durchschnitt (Genauigkeit)
                    let diff_avg = (dt - avg_t).abs();

                    bonus += PERFECT_TIME_BONUS - (diff_avg / sigma).powi(2);

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
    //Globale Analyse Start & Ende der Trips
    for end_p in end_points.iter() {
        //Passenden Startdetector finden
        let mut best_match_time = 99999;
        let mut best_match_id = -1;
        for (i, start_p) in start_points.iter().enumerate() {
            if start_p.used { continue; }

            if end_p.loc == start_p.loc {
                //Gleicher Ort
                if start_p.time > end_p.time {
                    //Passende Zeit: Start ist später als vorheriges Ende
                    let time_diff = start_p.time - end_p.time;
                    if time_diff < best_match_time{
                        best_match_time = time_diff;
                        best_match_id = i as i32;
                    }
                }
            }
        }
        if best_match_id != -1 {
            //Bonus belohnen
            bonus += DETECTOR_MATCH_BONUS;
            //Detektor Match entfernen
            start_points[best_match_id as usize].used = true;
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