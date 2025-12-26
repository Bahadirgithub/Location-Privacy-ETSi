use crate::types::*;
use rayon::prelude::*;

pub fn fitness_trip(individual: &[u32],  transactions: &[Transaction], simulated_times: &[SimulatedTime]) -> f64{
    let max_trip_id = *individual.iter().max().unwrap_or(&0) as usize;
    let mut trips: Vec<Vec<&Transaction>> = vec![Vec::new(); max_trip_id + 1]; //Leere Trip Liste erstellen
    let mut time_dif: f64 = 0.0;
    let mut penalty: f64 = 0.0;
    let mut bonus: f64 = 0.0;

    let num_active_trips = individual.iter().collect::<std::collections::HashSet<_>>().len();

    penalty += num_active_trips as f64 * 2000.0;

    for (trans_id, trip_id) in individual.iter().enumerate() {
        trips[*trip_id as usize].push(&transactions[trans_id]); //Trip Liste befüllen
    }

    for trip in trips{
        if trip.len() < 2 {
            penalty += 1500.0; // Harte Strafe für Singles
        } else if trip.len() < 3 {
            penalty += 100.0; // Leichte Strafe für sehr kurze Trips
        }
        for window in trip.windows(2) {
            let current = window[0];
            let next = window[1];

            //Zeitabweichung berechnen
            let trans_dif: f32 = next.time as f32 - current.time as f32;

            //30min Pause
            if trans_dif > 1800.0 {
                penalty += 1000.0;
            }

            let simulated_time = search_time(current.detector, next.detector, simulated_times);
            if simulated_time.from_detector == 9999 && simulated_time.avg == -1.0 {
                if trans_dif > 0.0 && trans_dif < 3600.0 {
                    penalty += 500.0;
                    
                    // Wir addieren trotzdem eine kleine Zeitstrafe (linear)
                    time_dif += trans_dif as f64 * 0.01;
                } else {
                    // Unmögliche Zeit -> Teleportation -> Strafe höher als Split
                    penalty += 5000.0;
                }
                continue;
            }

            if trans_dif <= simulated_time.max && trans_dif >= simulated_time.min{
                //bonus
                bonus += 50.0;
            }
            else{
                time_dif += (f64::powf((trans_dif - simulated_time.avg) as f64, 2.0)) * 0.05; //x² funktion * 0,05
            }
        }
    }
    let bad = time_dif + penalty;
    let good = bonus;
    let score = (1.0 + good) / (1.0 + bad);

    score
}

fn search_time(from_id: u32, to_id: u32, simulated_times: &[SimulatedTime]) -> SimulatedTime {
    for i in 0..simulated_times.len() {
        if (simulated_times[i].from_detector == from_id) && (simulated_times[i].to_detector == to_id){
            return simulated_times[i].clone();
        }
    }
    return SimulatedTime { from_detector: 9999, to_detector: 9999, avg: -1.0, min: -1.0, max: -1.0 }; //Nothing found! -> 9999 detectors and -1 time
}

pub fn calculate_trip_fitness(population: Vec<Individual>, transactions: &[Transaction], simulated_times: &[SimulatedTime]) -> Vec<Individual>{
    population.into_par_iter().map(|ind| {
        Individual {
            genome: ind.genome.clone(),
            score: fitness_trip(&ind.genome, transactions, simulated_times),
        }
    }).collect()
}