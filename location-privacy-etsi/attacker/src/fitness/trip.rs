use crate::types::*;

pub fn fitness_trip(individual: &[u32],  transactions: &[Transaction], simulated_times: &[SimulatedTime]) -> f64{
    let max_trip_id = *individual.iter().max().unwrap_or(&0) as usize;
    let mut trips: Vec<Vec<&Transaction>> = vec![Vec::new(); max_trip_id + 1]; //Leere Trip Liste erstellen
    let mut time_dif: f64 = 0.0;
    let mut penalty: f64 = 0.0;

    let d = (transactions.len() as f64 - max_trip_id as f64).abs();
    penalty += d.powf(2.0) * 0.0001;

    for (trans_id, trip_id) in individual.iter().enumerate() {
        trips[*trip_id as usize].push(&transactions[trans_id]); //Trip Liste befüllen
    }

    for trip in trips{
        for window in trip.windows(2) {
            let current = window[0];
            let next = window[1];

            //Zeitabweichung berechnen
            let trans_dif: f32 = next.time as f32 - current.time as f32;
            let simulated_time = search_time(current.detector, next.detector, simulated_times);
            if simulated_time.from_detector == 9999 && simulated_time.avg == -1.0 {
                penalty += 1000.0;
                continue;
            }
            time_dif += f64::powf((trans_dif - simulated_time.avg) as f64, 2.0) * 0.001; //x² funktion * 0.01 <- sonst zu stark
        }
    }
    let bad = time_dif + penalty;
    let good = 0.0;
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
    let mut result: Vec<Individual> = Vec::new();
    for ind in population{
        result.push(Individual{
            genome: ind.genome.clone(),
            score: fitness_trip(&ind.genome, transactions, simulated_times)
        });
    }
    result
}