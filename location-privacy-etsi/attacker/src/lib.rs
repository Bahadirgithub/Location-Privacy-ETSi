use pyo3::prelude::*;
//https://cratecode.com/info/genetic-algorithms-implementation-in-python

/// A Python module implemented in Rust.
#[pymodule]
mod genetic {
    use pyo3::prelude::*;
    use rand::Rng;
    use rand::seq::SliceRandom;
    use indicatif::{ProgressBar, ProgressState, ProgressStyle};
    use std::{cmp::min, fmt::Write};

    #[pyclass]
    #[derive(Clone)]
    struct Individual {
        #[pyo3(get, set)]
        genome: Vec<u32>,
        #[pyo3(get, set)]
        score: f64
    }

    #[pyclass]
    #[derive(Clone)]
    struct Trip {
        #[pyo3(get, set)]
        id: usize,
        #[pyo3(get, set)]
        cost: u32,
        #[pyo3(get, set)]
        start_time: u32,
        #[pyo3(get, set)]
        end_time: u32,
        #[pyo3(get, set)]
        start_loc_id: usize,
        #[pyo3(get, set)]
        end_loc_id: usize,
    }

    #[pymethods]
    impl Trip {
        #[new]
        fn new(id: usize, cost: u32, start_time: u32, end_time: u32, start_loc_id:usize, end_loc_id:usize) -> Self {
            Trip { id, cost, start_time, end_time, start_loc_id, end_loc_id }
        }

        fn __repr__(&self) -> String {
            format!("Trip(id={}, cost={}, starttime = {}, endtime = {})", self.id, self.cost, self.start_time, self.end_time)
        }
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

    fn fitness(individual: &[u32], num_wallets: usize, trips: &[Trip], sorted_wallets: &[u32]) -> f64 {
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

        //check for plausibility
        for wallet_trips in wallets.iter_mut() {
            wallet_trips.sort_unstable_by_key(|t| t.start_time);

            for i in 0..wallet_trips.len() - 1{
                //Safe handling (Wenn einem Wallet weniger als 2 Trips hinzugefügt wurden)
                if wallet_trips.len() <= 1{
                    penalty += 1000.0; //Meist 2+ Trips Zuhause->Arbeit->Zuhause->...
                    break;
                }
                let current = wallet_trips[i];
                let next = wallet_trips[i+1];

                if current.end_time > next.start_time{
                    penalty += 1000.0; //penalty prüfen
                }

                //check for simmilarity in start and end location
                if current.end_loc_id != next.start_loc_id {
                    penalty += 100.0;
                }
            }
        }

        let bad = ((total_error as f64) + penalty) * 0.001; //*0.001, da Zahlen sonst zu klein sind
        //let good = bonus;
        //let score = (1.0 + good) / (1.0 + bad);
        let score = 1.0 / (1.0 + bad);

        score
   }


    fn initial_population(population_size: u32, num_trips: usize, num_wallets: usize, trips_costs: &[Trip], sorted_wallets: &[u32]) -> Vec<Individual> {
        let mut population = Vec::new();

        for _ in 0..population_size {
            let genome = create_individual(num_trips, num_wallets);

            // Keine clones mehr!
            let score = fitness(
                &genome,
                num_wallets,
                &trips_costs,
                &sorted_wallets,
            );

            population.push(Individual { genome, score });
        }

        population
   }


    //Tournament Selection
    fn selection(population: &Vec<Individual>, tournament_num:usize, tournament_size:usize) -> Vec<Individual>{
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
    fn crossover(parent_1:Individual, parent_2:Individual, num_wallets:usize, trip_cost:&[Trip], sorted_wallets:&[u32]) -> (Individual, Individual){
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
    fn mutation_small(mut mutant:Individual, num_wallets:usize, trip_cost:&[Trip], sorted_wallets:&[u32]) -> Individual {
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
    fn mutation_big(mut mutant:Individual, num_wallets:usize, trip_cost:&[Trip], sorted_wallets:&[u32]) -> Individual {
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

    //Elitism
    fn select_elitism(population: &mut Vec<Individual>, selection_size: usize) -> Vec<Individual>{
        //https://www.woodruff.dev/day-12-genetic-algorithms-elitism-for-evolution-survival-of-the-fittest/
        let mut result = Vec::new();

        //https://rust-lang-nursery.github.io/rust-cookbook/algorithms/sorting.html
        population.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap()); // sort descending based on score

        for i in 0..selection_size {
            result.push(population[i].clone());
        }

        result
    }
    fn apply_elitism(population: &mut Vec<Individual>, elites: Vec<Individual>) -> Vec<Individual>{
        let selection_size = elites.len();

        population.sort_by(|a, b| a.score.partial_cmp(&b.score).unwrap()); // sort ascending based on score
        //Schlechteste Ergebisse mit entfernen & eliten aus der letzen Generation hinzufügen
        for i in 0..selection_size {
            population.remove(i);
            population.push(elites[i].clone());
        }

        population.to_vec()
    }

    //Main Function
    #[pyfunction]
    fn main(generations: usize, p_mutation_small:f32, p_mutation_big:f32, num_trips: usize, num_wallets: usize, population_size: u32, sorted_wallets: Vec<u32>, trips: Vec<Trip>) -> Vec<Individual>{
        //https://www.datacamp.com/tutorial/genetic-algorithm-python

        //Init
        let mut population = initial_population(population_size, num_trips,num_wallets, &trips, &sorted_wallets);
        let mut mutation_rate = 1.0;
        let mut previous_score = population[0].score;
        let mut no_improvement_generations = 0;
        let mut best_score = 0.0;
        //Create a new progress bar: https://github.com/console-rs/indicatif/blob/HEAD/examples/download.rs
        let pb = ProgressBar::new(generations as u64);

        //Style of progress bar
        pb.set_style(ProgressStyle::with_template("{spinner:.green} [{elapsed_precise}] [{wide_bar:.cyan/blue}] {current}/{total} ({eta}) {msg}")
            .unwrap()
            .with_key("eta", |state: &ProgressState, w: &mut dyn Write| write!(w, "{:.1}s", state.eta().as_secs_f64()).unwrap())
            .progress_chars("#>-"));

        //Main Loop
        for i in 0..generations{

            //Store best individuals
            let mut best_individual = population[0].clone();
            let mut population_sum = 0.0;
            for j in 0..population.len(){
                if population[j].score > best_individual.score{
                    best_individual = population[j].clone();
                }
                population_sum += population[j].score;
            }
            best_score = best_individual.score;
            if best_score <= previous_score{
                no_improvement_generations += 1;
            }
            else{
                no_improvement_generations = 0;
            }
            let avg_score = population_sum / (population.len() as f64);
            //println!("Generation {}: Best score is {}, Avg Score is {}", i, best_score, avg_score);
            pb.set_message(format!("Gen: {} | Best: {:.6} | Avg: {:.4}", i, best_score, avg_score));

            let elite_count = (population.len() as f64 * 0.02) as usize;
            let parents = selection(&population, population_size as usize, 7);

            //Select the best individuals
            let elites = select_elitism(&mut population, elite_count);

            //https://www.woodruff.dev/day-32-when-genetic-algorithms-go-wrong-debugging-poor-performance-and-premature-convergence/
            //Mutation Rate
            if no_improvement_generations == 50{
                mutation_rate *= 1.2;
            }

            let mut next_generation: Vec<Individual> = Vec::new();
            for j in (0..parents.len()).step_by(2){
                let parent1 = &parents[j];
                let parent2 = &parents[j + 1];

                let (mut child1, mut child2) = crossover(parent1.clone(), parent2.clone(), num_wallets as usize, &trips, &sorted_wallets);

                // Apply small mutation (swap) with probability
                if rand::random::<f32>() < (p_mutation_small*mutation_rate) {
                    child1 = mutation_small(child1, num_wallets, &trips, &sorted_wallets);
                }
                if rand::random::<f32>() < (p_mutation_small*mutation_rate) {
                    child2 = mutation_small(child2, num_wallets, &trips, &sorted_wallets);
                }

                // Apply big mutation (scramble) with probability
                if rand::random::<f32>() < (p_mutation_big*mutation_rate) {
                    child1 = mutation_big(child1, num_wallets, &trips, &sorted_wallets);
                }
                if rand::random::<f32>() < (p_mutation_big*mutation_rate) {
                    child2 = mutation_big(child2, num_wallets, &trips, &sorted_wallets);
                }

                next_generation.push(child1);
                next_generation.push(child2);
            }
            //Overwrite the worst Indivuduals of next generation with the best indivuduals of the previous
            next_generation = apply_elitism(&mut next_generation, elites);

            population = next_generation;
            previous_score = best_score;
            // Update the progress bar
            pb.inc(1);
        }
        pb.finish_with_message(format!("Finished! Best Score: {}", best_score.to_string()));
        population
    }

    //funktion um fitness von python aus aufzurufen
    #[pyfunction]
    fn call_fitness(individual: Vec<u32>, num_wallets: usize, trips: Vec<Trip>, sorted_wallets: Vec<u32>) -> f64 {
        fitness(&individual, num_wallets, &trips, &sorted_wallets)
    }
}
