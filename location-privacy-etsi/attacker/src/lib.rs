use pyo3::prelude::*;
//https://cratecode.com/info/genetic-algorithms-implementation-in-python

pub mod types;
pub mod fitness;
pub mod ga;


/// A Python module implemented in Rust.
use crate::types::*;
use crate::fitness::{
    trip::*, 
    wallet::*,
};
use crate::ga::{
    population::*,
    crossover::*,
    mutation::*,
};

use rand::{Rng, seq::SliceRandom};
use indicatif::{ProgressBar, ProgressState, ProgressStyle};
use std::{cmp::min, fmt::Write};


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
impl Individual {
    #[new]
    fn new(genome_trip: Vec<u32>, genome: Vec<u32>, score: f64) -> Self {
        Individual { genome, score }
    }

    fn __repr__(&self) -> String {
        format!("Individual(score={:.6}, genome={:?})", self.score, self.genome)
    }
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

// --- MODUL REGISTRIERUNG (DAS WICHTIGSTE!) ---
// Der Funktionsname "genetic" muss mit dem Namen in Cargo.toml [lib] name = "genetic" übereinstimmen!
#[pymodule]
fn genetic(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // 1. Klassen registrieren
    // Hinweis: add_class funktioniert auch mit der Bound API weiterhin so
    m.add_class::<Transaction>()?;
    m.add_class::<Individual>()?;
    m.add_class::<SimulatedTime>()?;
    m.add_class::<Trip>()?;

    // 2. Funktionen registrieren
    // wrap_pyfunction! benötigt jetzt das "Bound" Objekt 'm'
    m.add_function(wrap_pyfunction!(main, m)?)?;

    Ok(())
}
