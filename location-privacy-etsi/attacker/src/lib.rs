use pyo3::prelude::*;
//https://cratecode.com/info/genetic-algorithms-implementation-in-python

/// A Python module implemented in Rust.
#[pymodule]
mod genetic {
    use pyo3::prelude::*;
    use rand::{Error, Rng, seq::SliceRandom};
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
    struct Transaction {
        #[pyo3(get, set)]
        id: u32,
        #[pyo3(get, set)]
        detector: u32,
        #[pyo3(get, set)]
        time: u32,
        #[pyo3(get, set)]
        cost: f32,
    }

    #[pyclass]
    #[derive(Clone)]
    struct SimulatedTime {
        #[pyo3(get, set)]
        from_detector: u32,
        #[pyo3(get, set)]
        to_detector: u32,
        #[pyo3(get, set)]
        avg: f32,
        #[pyo3(get, set)]
        min: f32,
        #[pyo3(get, set)]
        max: f32,
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
    impl SimulatedTime {
        #[new]
        fn new(from_detector: u32, to_detector: u32, avg: f32, min: f32, max: f32) -> Self {
            SimulatedTime { from_detector, to_detector, avg, min, max }
        }

        fn __repr__(&self) -> String {
            format!("Simulated Time(from_detector={}, to_detector={}, avg = {}, min = {}, max = {})", self.from_detector, self.to_detector, self.avg, self.min, self.max)
        }
    }

    #[pymethods]
    impl Transaction {
        #[new]
        fn new(id: u32, detector: u32, time: u32, cost: f32) -> Self {
            Transaction { id, detector, time, cost }
        }

        fn __repr__(&self) -> String {
            format!("Transaction(id={}, detector={}, time = {}, cost = {})", self.id, self.detector, self.time, self.cost)
        }
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
        fn new(genome_trip: Vec<u32>, genome: Vec<u32>, score: f64) -> Self {
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

    fn search_time(from_id: u32, to_id: u32, simulated_times: &[SimulatedTime]) -> SimulatedTime {
        for i in 0..simulated_times.len() {
            if ((simulated_times[i].from_detector == from_id) && (simulated_times[i].to_detector == to_id)){
                return simulated_times[i].clone();
            }
        }
        return SimulatedTime { from_detector: 9999, to_detector: 9999, avg: -1.0, min: -1.0, max: -1.0 }; //Nothing found! -> 9999 detectors and -1 time
    }

    fn fitness_trip(individual: &[u32],  transactions: &[Transaction], simulated_times: &[SimulatedTime]) -> f64{
        let max_trip_id = *individual.iter().max().unwrap_or(&0) as usize;
        let mut trips: Vec<Vec<&Transaction>> = vec![Vec::new(); max_trip_id + 1]; //Leere Trip Liste erstellen
        let mut time_dif: f64 = 0.0;
        let mut penalty: f64 = 0.0;

        let d = (transactions.len() as f64 - max_trip_id as f64).abs();
        penalty += d.powf(4.0);

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
                if (simulated_time.from_detector == 9999 && simulated_time.avg == -1.0){
                    penalty += 1000.0;
                    continue;
                }
                time_dif += (f64::powf((trans_dif - simulated_time.avg) as f64, 2.0) * 0.001); //x² funktion * 0.01 <- sonst zu stark
            }
        }
        let bad = time_dif + penalty;
        let good = 0.0;
        let score = (1.0 + good) / (1.0 + bad);

        score
    }

    fn fitness_wallet(individual: &[u32], num_wallets: usize, trips: &[Trip], sorted_wallets: &[u32]) -> f64 {
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
            wallet_trips.sort_unstable_by_key(|t| t.start_time);

            for i in 0..wallet_trips.len() - 1{
                if i>0 && (wallet_trips[i].start_loc_id == wallet_trips[0].start_loc_id || wallet_trips[i].end_loc_id == wallet_trips[0].start_loc_id){
                    bonus += 1.0;
                }
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

        let bad = (total_error as f64) + penalty;
        //let good = bonus;
        //let score = (1.0 + good) / (1.0 + bad);
        let score = (1.0 + bonus) / (1.0 + bad);

        score
   }


    fn initial_population(population_size: u32, num_trips: usize, num_wallets: usize, trips_costs: &[Trip], sorted_wallets: &[u32]) -> Vec<Individual> {
        let mut population = Vec::new();

        for _ in 0..population_size {
            let genome = create_individual(num_trips, num_wallets);

            // Keine clones mehr!
            let score = fitness_wallet(
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
    fn crossover(parent_1:Individual, parent_2:Individual) -> (Individual, Individual){
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

        child_1.score = -1.0;
        child_2.score = -1.0;

        (child_1, child_2)
    }

    //Swap Mutation
    fn mutation_small(mut mutant:Individual) -> Individual {
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

        //Calculate fitness_wallet
        mutant.score = -1.0;

        mutant
    }

    //Scramble Mutation
    fn mutation_big(mut mutant:Individual) -> Individual {
        //https://www.tutorialspoint.com/genetic_algorithms/genetic_algorithms_mutation.htm
        let genome_size = mutant.genome.len();

        let slice_len = rand::thread_rng().gen_range(1..genome_size);
        let rand_1 = rand::thread_rng().gen_range(0..genome_size - slice_len + 1);
        let rand_2 = rand_1 + slice_len;

        let slice = &mut mutant.genome[rand_1..rand_2];
        slice.shuffle(&mut rand::thread_rng());

        //Calculate fitness_wallet later
        mutant.score = -1.0;

        mutant
    }

    //Split Mutation (Trips)
    fn mutation_split(mut mutant:Individual) -> Individual {
        let genome_len = mutant.genome.len();
        let max_id = *mutant.genome.iter().max().unwrap_or(&0);

        let mut used_ids = vec![false; (max_id + 1) as usize];
        for &id in &mutant.genome {
            used_ids[id as usize] = true;
        }

        let mut new_id = max_id + 1;
        for (id, &is_used) in used_ids.iter().enumerate() {
            if !is_used {
                new_id = id as u32;
                break;
            }
        }

        // Wähle zufällig einen Trip zum Splitten aus
        let id_pick = rand::thread_rng().gen_range(0..genome_len);
        let id_target = mutant.genome[id_pick];

        // Sammle alle Transaktionen, die zu diesem Trip gehören
        let mut transaction_ids: Vec<usize> = Vec::new();
        for i in 0..genome_len{
            if(mutant.genome[i] == id_target){
                transaction_ids.push(i);
            }
        }

        let ids_length: usize =  transaction_ids.len();

        if ids_length < 2 { return mutant; } // Trip mit nur 1 Transaktion kann nicht gesplittet werden

        // Alles ab diesem Punkt bekommt die NEUE ID
        let split_point: usize = rand::thread_rng().gen_range(1..ids_length);

        for i in split_point..ids_length {
        mutant.genome[transaction_ids[i]] = new_id;
    }

        mutant.score = -1.0;
        mutant
    }

    fn mutation_merge(mut mutant:Individual) -> Individual {
        let genome_len = mutant.genome.len();

        let mut id_pick = rand::thread_rng().gen_range(0..genome_len);
        let id_target = mutant.genome[id_pick];

        let mut id_victim = id_target;
        let mut alt_victim = id_target;
        for i in 0..genome_len {
            id_pick = rand::thread_rng().gen_range(0..genome_len);
            if mutant.genome[id_pick] != id_target {
                id_victim = mutant.genome[id_pick];
                break;
            }
            else if mutant.genome[i] != id_target {
                alt_victim = mutant.genome[i];
            }
        }
        if (id_victim == id_target) && (alt_victim != id_target) { id_victim = alt_victim }
        else { return mutant; } //Falls wir keinen anderen Trip gefunden haben

        // Ersatze alle vorkommen von id_victim mit id_target
        for gene in mutant.genome.iter_mut() {
            if *gene == id_victim {
                *gene = id_target;
            }
        }

        // Setze die höchste TripId = id_victim, damit keine Lücken bleiben
        let max_id = *mutant.genome.iter().max().unwrap_or(&0);
        for gene in mutant.genome.iter_mut() {
            if *gene == max_id {
                *gene = id_victim;
            }
        }

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
    fn generate_Trips(individual: &[u32], transactions: &[Transaction]) -> Vec<Trip>{
        let max_trip_id = *individual.iter().max().unwrap_or(&0) as usize;
        let mut trips: Vec<Vec<&Transaction>> = vec![Vec::new(); max_trip_id + 1]; //Leere Trip Liste erstellen
        let mut result: Vec<Trip> = Vec::new();

        for (trans_id, trip_id) in individual.iter().enumerate() {
            trips[*trip_id as usize].push(&transactions[trans_id]); //Trip Liste befüllen
        }

        for (trip_id, trip_trans) in trips.iter().enumerate() {
            if trip_trans.is_empty() { continue; }
            let mut trip_cost: f32 = 0.0;
            let trip_lenght = trip_trans.len();
            for trans in trip_trans{
                trip_cost += trans.cost;
            }
            let obj = Trip {
                id: trip_id,
                cost: trip_cost.round() as u32,
                start_time: trip_trans[0].time,
                end_time: trip_trans[trip_lenght-1].time,
                start_loc_id: trip_trans[0].detector as usize,
                end_loc_id: trip_trans[trip_lenght-1].detector as usize,
            };
            result.push(obj);
        }
        result
    }

    fn initial_trip_pop(individual: &[u32], population_size: u32, transactions: &[Transaction], simulated_times: &[SimulatedTime]) -> Vec<Individual>{
        let mut population: Vec<Individual> = Vec::new();
        //original trip
        population.push(Individual{
            genome: individual.to_vec(),
            score: fitness_trip(individual, transactions, simulated_times)
        });
        for i in 1..(population_size){ //Erste Hälfte
            let mut ind = Individual{
                genome: individual.to_vec(),
                score: -1.0,
            };
            if i <= population_size / 2{
                ind = mutation_small(ind);
            }
            else {
                ind = mutation_big(ind);
            }
            //score
            ind.score = fitness_trip(&ind.genome, transactions, simulated_times);

            population.push(ind);
        }
        population
    }

    //Main Function
    #[pyfunction]
    fn main(generations_trips: usize, generations_wallets: usize, p_mutation_small:f32, p_mutation_big:f32, population_size: u32, sorted_wallets: Vec<u32>, initial_population_trips: Vec<u32>, transactions: Vec<Transaction>, simulated_times: Vec<SimulatedTime>) -> (Vec<Individual>, Vec<Individual>){
        //https://www.datacamp.com/tutorial/genetic-algorithm-python

        //Main Loop Trips
        //Init
        
        println!("Initial fitness score: {}", fitness_trip(&initial_population_trips, &transactions, &simulated_times));

        //Initialize initial populations
        let mut population = initial_trip_pop(&initial_population_trips, population_size, &transactions, &simulated_times);
        let mut mutation_rate = 1.0;
        let mut previous_score = population[0].score;
        let mut no_improvement_generations = 0;
        let mut best_score = 0.0;
        for i in 0..generations_trips{

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
            println!("Generation {}: Best score is {}, Avg Score is {}", i, best_score, avg_score);

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

                let (mut child1, mut child2) = crossover(parent1.clone(), parent2.clone());

                // Apply small mutation (swap) with probability
                if rand::random::<f32>() < (p_mutation_small*mutation_rate) {
                    child1 = mutation_small(child1);
                }
                if rand::random::<f32>() < (p_mutation_small*mutation_rate) {
                    child2 = mutation_big(child2);
                }

                // Apply big mutation (scramble) with probability
                if rand::random::<f32>() < (p_mutation_big*mutation_rate) {
                    child1 = mutation_split(child1);
                }
                if rand::random::<f32>() < (p_mutation_big*mutation_rate) {
                    child2 = mutation_merge(child2);
                }

                //Score childs
                child1.score = fitness_trip(&child1.genome, &transactions, &simulated_times);
                child2.score = fitness_trip(&child2.genome, &transactions, &simulated_times);

                next_generation.push(child1);
                next_generation.push(child2);
            }
            //Overwrite the worst Indivuduals of next generation with the best indivuduals of the previous
            next_generation = apply_elitism(&mut next_generation, elites);

            population = next_generation;
            previous_score = best_score;

        } //-> Return trips + num_trips
        let population_trips = population.clone();

        let mut best_trip = population[0].clone();
        for trip in population{
            if trip.score > best_trip.score{
                best_trip = trip;
            }
        }

        let trips = generate_Trips(&best_trip.genome, &transactions);
        let num_trips: usize = trips.len();
        

        //Main Loop Wallets
        //Init
        let num_wallets = sorted_wallets.len();
        let mut population = initial_population(population_size, num_trips, num_wallets, &trips, &sorted_wallets);
        let mut mutation_rate = 1.0;
        let mut previous_score = population[0].score;
        let mut no_improvement_generations = 0;
        let mut best_score = 0.0;
        //Create a new progress bar: https://github.com/console-rs/indicatif/blob/HEAD/examples/download.rs
        let pb = ProgressBar::new(generations_wallets as u64);
                
        //Style of progress bar
        pb.set_style(ProgressStyle::with_template("{spinner:.green} [{elapsed_precise}] [{wide_bar:.cyan/blue}] {current}/{total} ({eta}) {msg}")
            .unwrap()
            .with_key("eta", |state: &ProgressState, w: &mut dyn Write| write!(w, "{:.1}s", state.eta().as_secs_f64()).unwrap())
            .progress_chars("#>-"));


        for i in 0..generations_wallets{

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

                let (mut child1, mut child2) = crossover(parent1.clone(), parent2.clone());

                // Apply small mutation (swap) with probability
                if rand::random::<f32>() < (p_mutation_small*mutation_rate) {
                    child1 = mutation_small(child1);
                }
                if rand::random::<f32>() < (p_mutation_small*mutation_rate) {
                    child2 = mutation_small(child2);
                }

                // Apply big mutation (scramble) with probability
                if rand::random::<f32>() < (p_mutation_big*mutation_rate) {
                    child1 = mutation_big(child1);
                }
                if rand::random::<f32>() < (p_mutation_big*mutation_rate) {
                    child2 = mutation_big(child2);
                }

                //Score childs
                child1.score = fitness_wallet(&child1.genome, num_wallets, &trips, &sorted_wallets);
                child2.score = fitness_wallet(&child2.genome, num_wallets, &trips, &sorted_wallets);

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
        (population, population_trips)
    }

    //funktion um fitness_wallet von python aus aufzurufen
    #[pyfunction]
    fn call_fitness_wallet(individual: Vec<u32>, num_wallets: usize, trips: Vec<Trip>, sorted_wallets: Vec<u32>) -> f64 {
        fitness_wallet(&individual, num_wallets, &trips, &sorted_wallets)
    }
}
