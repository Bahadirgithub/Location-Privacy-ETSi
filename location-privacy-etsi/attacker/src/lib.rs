use pyo3::prelude::*;

/// A Python module implemented in Rust.
#[pymodule]
mod genetic {
    use pyo3::prelude::*;
    use rand::Rng;

    #[pyclass]
    struct Individual {
        genome: Vec<u32>,
        score: f64
    }


    #[pymethods]
    impl Individual {
        #[new]
        fn new(genome: Vec<u32>, score: f64) -> Self {
            Individual { genome, score }
        }

        fn get_genome(&self) -> Vec<u32> {
            self.genome.clone()
        }

        fn get_score(&self) -> f64 {
            self.score
        }

        fn __repr__(&self) -> String {
            format!("Individual(score={:.6}, genome={:?})", self.score, self.genome)
        }
    }

    fn create_individual(num_trips: u32, num_wallets: u32) -> Vec<u32>{
        let mut result = vec![0u32; num_trips as usize];

        for i in 0..num_trips {
            let id = rand::thread_rng().gen_range(0..num_wallets) as u32;
            result[i as usize] = id;
        }
        result
    }

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

    #[pyfunction]
    fn initial_population(num_trips: u32, num_wallets: u32, population_size: u32, sorted_wallets: Vec<u32>, trips_costs: Vec<u32>) -> Vec<Individual>{
        let mut population: Vec<Individual> = Vec::new();

        for _ in 0..population_size {
            let genome = create_individual(num_trips, num_wallets);

            let score = fitness(genome.clone(), num_wallets as usize, trips_costs.clone(), sorted_wallets.clone()); //Ändern Pointer übergeben statt clone()!!!

            let ind = Individual{genome, score};

            population.push(ind);
        }

        population
    }


    /*
    #[pyfunction]
    fn selection(population: Vec<Individual>, tournament_size:usize) -> Vec<Individual>{
        //https://www.baeldung.com/cs/ga-tournament-selection
        let mut result = vec![Vec::new(); population.len()];

        for i in 0..population.len(){
            //Tournament winners


        }


        result
    }
    */
}
