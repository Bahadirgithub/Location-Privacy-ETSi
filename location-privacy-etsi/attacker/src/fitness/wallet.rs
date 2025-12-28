use crate::types::*;
use rayon::prelude::*;

pub fn fitness_wallet(individual: &[u32], num_wallets: usize, trips: &[Trip], sorted_wallets: &[u32]) -> f64 {
    let mut wallets: Vec<Vec<&Trip>> = vec![Vec::new(); num_wallets];
    let mut current_wallet_sums = vec![0u32; num_wallets];

    for (trip_id, wallet_id) in individual.iter().enumerate() {
        let trip_sum = trips[trip_id].cost;
        wallets[*wallet_id as usize].push(&trips[trip_id]);
        current_wallet_sums[*wallet_id as usize] += trip_sum;
    }

    current_wallet_sums.sort_unstable();

    let mut total_error: u32 = 0;

    for i in 0..num_wallets {
        total_error += current_wallet_sums[i].abs_diff(sorted_wallets[i]);
    }

    let mut penalty = 0.0;
    let mut bonus = 0.0;

    //check for plausibility
    for wallet_trips in wallets.iter_mut() {
        let trip_count = wallet_trips.len();

        wallet_trips.sort_unstable_by_key(|t| t.start_time);

        for i in 0..trip_count - 1{
            if i>0 && (wallet_trips[i].start_loc_id == wallet_trips[0].start_loc_id || wallet_trips[i].end_loc_id == wallet_trips[0].start_loc_id){
                bonus += 30.0;
            }
            //Safe handling (Wenn einem Wallet weniger als 2 Trips hinzugefügt wurden)
            if trip_count <= 1{
                penalty += 1000.0; //Meist 2+ Trips Zuhause->Arbeit->Zuhause->...
                break;
            }

            let current = wallet_trips[i];
            let next = wallet_trips[i+1];

            if current.end_time > next.start_time{
                penalty += 5000.0; //penalty prüfen
            }

            //check for simmilarity in start and end location
            if current.end_loc_id != next.start_loc_id {
                penalty += 1000.0;
            }          
        }
    }

    let bad = (total_error as f64) + penalty;
    //let good = bonus;
    //let score = (1.0 + good) / (1.0 + bad);
    let score = (10000.0 + bonus) / (1000.0 + bad);

    score
}

pub fn calculate_wallet_fitness(population: Vec<Individual>, num_wallets: usize, trips: &[Trip], sorted_wallets: &[u32]) -> Vec<Individual>{
    population.into_par_iter().map(|ind| {
        Individual {
            genome: ind.genome.clone(),
            score: fitness_wallet(&ind.genome, num_wallets, trips, sorted_wallets),
        }
    }).collect()
}