use pyo3::prelude::*;

/// A Python module implemented in Rust.
#[pymodule]
mod genetic {
    use pyo3::prelude::*;
    use rand::Rng;
    #[pyfunction]
    fn create_individual(num_trips: u32, num_wallets: u32) -> Vec<u32>{
        let mut result = vec![0u32; num_trips as usize];

        for i in 0..num_trips {
            let id = rand::thread_rng().gen_range(0..num_wallets) as u32;
            result[i as usize] = id;
        }
        result
    }

    #[pyfunction]
    fn initial_population(num_trips: u32, num_wallets: u32, population_size: u32) -> Vec<Vec<u32>>{
        let mut result = vec![Vec::new(); population_size as usize];

        for i in 0..population_size {
            let individual = create_individual(num_trips, num_wallets);
            result[i as usize] = individual;
        }

        result
    }

    #[pyfunction]
    fn fitness(individual: Vec<u32>, num_wallets: usize, trip_cost: Vec<u32>, sorted_wallets: Vec<u32>) -> f64{
        let mut current_wallet_sums= vec![0u32; num_wallets];

        for(trip_id, wallet_id) in individual.iter().enumerate(){
            let trip_sum = trip_cost[trip_id];

            current_wallet_sums[*wallet_id as usize] += trip_sum;
        }

        //current_wallets sortieren
        current_wallet_sums.sort_unstable(); //schneller sortier algorithmus

        let mut total_error:u32 = 0;

        for i in 0..num_wallets{
            total_error += current_wallet_sums[i].abs_diff(sorted_wallets[i]);
        }

        //Score berechnen
        1.0 / (1.0 + (total_error as f64))
    }

}
