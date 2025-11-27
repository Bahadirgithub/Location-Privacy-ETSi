use pyo3::prelude::*;
//https://cratecode.com/info/genetic-algorithms-implementation-in-python

/// A Python module implemented in Rust.
#[pymodule]
mod genetic {
    use pyo3::prelude::*;
    use rand::Rng;
    use rand::seq::SliceRandom;

    #[pyclass]
    #[derive(Clone)]
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

    fn fitness(individual: &[u32], num_wallets: usize, trip_cost: &[u32], sorted_wallets: &[u32]) -> f64 {
        let mut current_wallet_sums = vec![0u32; num_wallets];

        for (trip_id, wallet_id) in individual.iter().enumerate() {
            let trip_sum = trip_cost[trip_id];
            current_wallet_sums[*wallet_id as usize] += trip_sum;
        }

        current_wallet_sums.sort_unstable();

        let mut total_error: u32 = 0;

        for i in 0..num_wallets {
            total_error += current_wallet_sums[i].abs_diff(sorted_wallets[i]);
        }

        1.0 / (1.0 + (total_error as f64))
   }


    fn initial_population(population_size: u32, num_trips: u32, num_wallets: u32, trips_costs: &[u32], sorted_wallets: &[u32]) -> Vec<Individual> {
        let mut population = Vec::new();

        for _ in 0..population_size {
            let genome = create_individual(num_trips, num_wallets);

            // Keine clones mehr!
            let score = fitness(
                &genome,
                num_wallets as usize,
                &trips_costs,
                &sorted_wallets
            );

            population.push(Individual { genome, score });
        }

        population
   }


    //Tournament Selection
    fn selection(population: Vec<Individual>, tournament_num:usize, tournament_size:usize) -> Vec<Individual>{
        //https://www.baeldung.com/cs/ga-tournament-selection
        //https://cratecode.com/info/genetic-algorithms-selection-techniques
        let mut result = Vec::new();
        
        for _ in 0..tournament_num {
            //Select a random subset from population
            let tournament:Vec<Individual> = population.choose_multiple(&mut rand::thread_rng(), tournament_size).cloned().collect();

            //Select a winner of the tournament (highest score)
            let mut winner = &tournament[0];
            for j in 1..tournament.len(){
                if tournament[j].score > winner.score {
                    winner = &tournament[j];
                }
            }
            result.push(winner.clone());
        }
        result
    }

    //Two-Point Crossover
    fn crossover(parent_1:Individual, parent_2:Individual, num_wallets:usize, trip_cost:&[u32], sorted_wallets:&[u32]) -> (Individual, Individual){
        //https://www.geeksforgeeks.org/machine-learning/crossover-in-genetic-algorithm/
        let genome_size = parent_1.genome.len();

        let mut child_1 = Individual { genome: vec![0; genome_size], score: 0.0};
        let mut child_2 = Individual { genome: vec![0; genome_size], score: 0.0};

        let swap_1 = rand::thread_rng().gen_range(0..genome_size/2) as usize;
        let swap_2 = rand::thread_rng().gen_range(genome_size/2..genome_size) as usize;

        //parent_1 & parent_2 should have the same genome size!
        for i in 0..genome_size{
            if i < swap_1{
                child_1.genome[i] = parent_1.genome[i];
                child_2.genome[i] = parent_2.genome[i];
            }
            else if (i >= swap_1) && (i < swap_2){
                child_1.genome[i] = parent_2.genome[i];
                child_2.genome[i] = parent_1.genome[i];
            }
            else{
                child_1.genome[i] = parent_1.genome[i];
                child_2.genome[i] = parent_2.genome[i];
            }
        }

        child_1.score = fitness(&child_1.genome, num_wallets, &trip_cost, &sorted_wallets);
        child_2.score = fitness(&child_2.genome, num_wallets, &trip_cost, &sorted_wallets);

        (child_1, child_2)
    }

    //Swap Mutation
    fn mutation_small(){
        //https://www.tutorialspoint.com/genetic_algorithms/genetic_algorithms_mutation.htm

    }

    //Scramble Mutation

    //Main Function
    #[pyfunction]
    fn main(generations: usize, num_trips: u32, num_wallets: u32, population_size: u32, sorted_wallets: Vec<u32>, trips_costs: Vec<u32>) -> Vec<Individual>{
        //https://www.datacamp.com/tutorial/genetic-algorithm-python

        //Init
        let mut population = initial_population(population_size, num_trips,num_wallets, &trips_costs, &sorted_wallets);

        //Main Loop
        for i in 0..generations{

            //Store best individuals
            let mut best_individual = population[0].clone();
            for j in 0..population.len(){
                if population[j].score > best_individual.score{
                    best_individual = population[j].clone();
                }
            }
            let best_score = best_individual.score;
            println!("Generation {}: Best score is {}", i, best_score);

            population = selection(population, population_size as usize, 7);

            //let mut next_population: Vec<Individual> = Vec::new();
            for j in (0..population.len()).step_by(2){
                let parent1 = &population[j];
                let parent2 = &population[j + 1];

                let (child1, child2) = crossover(parent1.clone(), parent2.clone(), num_wallets as usize, &trips_costs, &sorted_wallets);

                population.push(child1);
                population.push(child2);
            }
        }
        population
    }
}
