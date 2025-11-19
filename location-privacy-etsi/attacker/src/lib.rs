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
        result //Return
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

}
