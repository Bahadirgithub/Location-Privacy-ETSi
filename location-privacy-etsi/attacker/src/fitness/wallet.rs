use crate::types::*;
use rayon::prelude::*;
use std::collections::HashSet;

pub fn fitness_wallet(individual: &[u32], num_wallets: usize, trips: &[Trip], sorted_wallets: &[u32]) -> f64 {
    let mut wallets: Vec<Vec<&Trip>> = vec![Vec::new(); num_wallets];
    let mut current_wallet_sums = vec![0u32; num_wallets];

    /*Gefundene Parameter: Spider
    const TOTAL_ERROR_MULT: f64 = 2.23;
    const HOME_BONUS: f64 = 183.2;
    const SHORT_TRIP_PENALTY: f64 = 5784.6;
    const TIME_TELEP_PENALTY: f64 = 381.0;
    const LOC_TELEP_PENALTY: f64 = 2332.47;
    const JACCARD_THRESHOLD: f64 = 0.59;
    const JACCARD_BONUS: f64 = 150.0;
    */

    //Gefundene Parameter: Ingolstadt
    const TOTAL_ERROR_MULT: f64 = 2.9;
    const HOME_BONUS: f64 = 186.7;
    const SHORT_TRIP_PENALTY: f64 = 8023.9;
    const TIME_TELEP_PENALTY: f64 = 568.9;
    const LOC_TELEP_PENALTY: f64 = 2756.5;
    const JACCARD_THRESHOLD: f64 = 0.72;
    const JACCARD_BONUS: f64 = 261.5;

    for (trip_id, wallet_id) in individual.iter().enumerate() {
        let trip_sum = trips[trip_id].cost;
        wallets[*wallet_id as usize].push(&trips[trip_id]);
        current_wallet_sums[*wallet_id as usize] += trip_sum;
    }

    current_wallet_sums.sort_unstable();

    let mut total_error: f64 = 0.0;

    for i in 0..num_wallets {
        total_error += current_wallet_sums[i].abs_diff(sorted_wallets[i]) as f64 * TOTAL_ERROR_MULT;
    }

    let mut penalty = 0.0;
    let mut bonus = 0.0;

    //check for plausibility
    for wallet_trips in wallets.iter_mut() {
        let trip_count = wallet_trips.len();

        wallet_trips.sort_unstable_by_key(|t| t.start_time);

        for i in 0..trip_count - 1{
            if i>0 && (wallet_trips[i].start_loc_id == wallet_trips[0].start_loc_id || wallet_trips[i].end_loc_id == wallet_trips[0].start_loc_id){
                bonus += HOME_BONUS;
            }
            //Safe handling (Wenn einem Wallet weniger als 2 Trips hinzugefügt wurden)
            if trip_count <= 1{
                penalty += SHORT_TRIP_PENALTY; //Meist 2+ Trips Zuhause->Arbeit->Zuhause->...
                break;
            }

            let current = wallet_trips[i];
            let next = wallet_trips[i+1];

            if current.end_time > next.start_time{
                let overlap = current.end_time - next.start_time;
                penalty += TIME_TELEP_PENALTY * overlap as f64; //penalty prüfen
            }

            //check for simmilarity in start and end location
            if current.end_loc_id != next.start_loc_id {
                penalty += LOC_TELEP_PENALTY;
            }
        }
        //Änhlichkeit mit Jaccard Index bewerten
        for i in 0..trip_count{
            //Trip Paare belohnen
            let mut best_jaccard_score = 0.0;
            for j in (i+1)..trip_count {
                let jaccard_score = jaccard_index(
                    &wallet_trips[i].transactions,
                    &wallet_trips[j].transactions
                );

                if jaccard_score > best_jaccard_score { best_jaccard_score = jaccard_score};

                if jaccard_score > JACCARD_THRESHOLD{
                    break; //Falls Score hoch genug ist
                }
            }

            if best_jaccard_score > JACCARD_THRESHOLD{
                bonus += best_jaccard_score * JACCARD_BONUS;
            }
        }
    }

    let bad = (total_error as f64) + penalty;
    //let good = bonus;
    //let score = (1.0 + good) / (1.0 + bad);
    let score = (1.0 + bonus) / (1.0 + bad);

    score
}

fn jaccard_index(a: &[u32], b: &[u32]) -> f64{
    //O(N+M) Komplexität
    //https://www.geeksforgeeks.org/dsa/find-the-jaccard-index-and-jaccard-distance-between-the-two-given-sets/
    //https://www.geeksforgeeks.org/dsa/intersection-of-two-arrays/
    let mut sa: HashSet<u32> = a.iter().copied().collect();
    let mut intersection = 0;

    for &item in b.iter() {
        if sa.remove(&item) {
            intersection += 1;
        }
    }

    let union = a.len() + b.len() - intersection;
    if union == 0 { 0.0 } else { intersection as f64 / union as f64 }
}

pub fn calculate_wallet_fitness(population: Vec<Individual>, num_wallets: usize, trips: &[Trip], sorted_wallets: &[u32]) -> Vec<Individual>{
    population.into_par_iter().map(|ind| {
        Individual {
            genome: ind.genome.clone(),
            score: fitness_wallet(&ind.genome, num_wallets, trips, sorted_wallets),
        }
    }).collect()
}