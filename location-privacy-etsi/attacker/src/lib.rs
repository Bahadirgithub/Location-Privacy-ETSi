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
        #[pyo3(get, set)]
        genome: Vec<u32>,
        #[pyo3(get, set)]
        score: f64
    }


    #[pymethods]
    impl Individual {
        #[new]
        fn new(genome: Vec<u32>, score: f64) -> Self {
            Individual { genome, score }
        }

        fn __repr__(&self) -> String {
            format!("Individual(score={:.6}, genome={:?})", self.score, self.genome)
        }
    }

    fn create_individual(num_trips: usize, num_wallets: usize) -> Vec<u32>{
        let mut result = vec![0u32; num_trips];

        for i in 0..num_trips {
            let id = rand::thread_rng().gen_range(0..num_wallets) as u32;
            result[i] = id;
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


    fn initial_population(population_size: u32, num_trips: usize, num_wallets: usize, trips_costs: &[u32], sorted_wallets: &[u32]) -> Vec<Individual> {
        let mut population = Vec::new();

        for _ in 0..population_size {
            let genome = create_individual(num_trips, num_wallets);

            // Keine clones mehr!
            let score = fitness(
                &genome,
                num_wallets,
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

        let swap_1 = rand::thread_rng().gen_range(0..genome_size/2);
        let swap_2 = rand::thread_rng().gen_range(genome_size/2..genome_size);

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
    fn mutation_small(mut mutant:Individual, num_wallets:usize, trip_cost:&[u32], sorted_wallets:&[u32]) -> Individual {
        //https://www.tutorialspoint.com/genetic_algorithms/genetic_algorithms_mutation.htm
        let genome_size = mutant.genome.len();

        let rand_1 = rand::thread_rng().gen_range(0..genome_size);
        let mut rand_2 = rand::thread_rng().gen_range(0..genome_size);
        //rand1 cannot be the same number as rand2
        while rand_1 == rand_2 {
            rand_2 = rand::thread_rng().gen_range(0..genome_size);
        }

        //Swap
        let temp = mutant.genome[rand_1];
        mutant.genome[rand_1] = mutant.genome[rand_2];
        mutant.genome[rand_2] = temp;

        //Calculate fitness
        mutant.score = fitness(&mutant.genome, num_wallets, &trip_cost, &sorted_wallets);

        mutant
    }

    //Scramble Mutation
    fn mutation_big(mut mutant:Individual, num_wallets:usize, trip_cost:&[u32], sorted_wallets:&[u32]) -> Individual {
        //https://www.tutorialspoint.com/genetic_algorithms/genetic_algorithms_mutation.htm
        let genome_size = mutant.genome.len();

        let slice_len = rand::thread_rng().gen_range(1..genome_size);
        let rand_1 = rand::thread_rng().gen_range(0..genome_size - slice_len + 1);
        let rand_2 = rand_1 + slice_len;

        let slice = &mut mutant.genome[rand_1..rand_2];
        slice.shuffle(&mut rand::thread_rng());

        //Calculate fitness
        mutant.score = fitness(&mutant.genome, num_wallets, &trip_cost, &sorted_wallets);

        mutant
    }

    //Main Function
    #[pyfunction]
    fn main(generations: usize,p_mutation_small:f32, p_mutation_big:f32, num_trips: usize, num_wallets: usize, population_size: u32, sorted_wallets: Vec<u32>, trips_costs: Vec<u32>) -> Vec<Individual>{
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

            let parents = selection(population, population_size as usize, 7);

            let mut next_generation: Vec<Individual> = Vec::new();
            for j in (0..parents.len()).step_by(2){
                let parent1 = &parents[j];
                let parent2 = &parents[j + 1];

                let (mut child1, mut child2) = crossover(parent1.clone(), parent2.clone(), num_wallets as usize, &trips_costs, &sorted_wallets);

                // Apply small mutation (swap) with probability
                if rand::random::<f32>() < p_mutation_small {
                    child1 = mutation_small(child1, num_wallets, &trips_costs, &sorted_wallets);
                }
                if rand::random::<f32>() < p_mutation_small {
                    child2 = mutation_small(child2, num_wallets, &trips_costs, &sorted_wallets);
                }

                // Apply big mutation (scramble) with probability
                if rand::random::<f32>() < p_mutation_big {
                    child1 = mutation_big(child1, num_wallets, &trips_costs, &sorted_wallets);
                }
                if rand::random::<f32>() < p_mutation_big {
                    child2 = mutation_big(child2, num_wallets, &trips_costs, &sorted_wallets);
                }

                next_generation.push(child1);
                next_generation.push(child2);
            }
            population = next_generation;
        }
        population
    }
}
