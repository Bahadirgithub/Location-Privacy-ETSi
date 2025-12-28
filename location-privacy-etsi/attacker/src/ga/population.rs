use crate::types::*;
use crate::fitness::{trip::*, wallet::*};
use crate::ga::mutation::*;
use std::collections::HashMap;

use rand::{Rng, seq::SliceRandom};

fn create_individual(num_trips: usize, num_wallets: usize) -> Vec<u32>{
    let mut result = vec![0u32; num_trips];

    for i in 0..num_trips {
        let id = rand::thread_rng().gen_range(0..num_wallets) as u32;
        result[i] = id;
    }
    result
}


pub fn initial_population(population_size: u32, num_trips: usize, num_wallets: usize, trips_costs: &[Trip], sorted_wallets: &[u32]) -> Vec<Individual> {
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

pub fn initial_trip_pop(individual: &[u32], population_size: u32, transactions: &[Transaction], simulated_times: &HashMap<(u32, u32), SimulatedTime>) -> Vec<Individual>{
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
            ind = mutation_split(ind);
        }
        else {
            ind = mutation_merge(ind);
        }
        //score
        ind.score = fitness_trip(&ind.genome, transactions, simulated_times);

        population.push(ind);
    }
    population
}

//Tournament Selection
pub fn selection(population: &Vec<Individual>, tournament_num:usize, tournament_size:usize) -> Vec<Individual>{
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

//Elitism
pub fn select_elitism(population: &mut Vec<Individual>, selection_size: usize) -> Vec<Individual>{
    //https://www.woodruff.dev/day-12-genetic-algorithms-elitism-for-evolution-survival-of-the-fittest/
    let mut result = Vec::new();

    //https://rust-lang-nursery.github.io/rust-cookbook/algorithms/sorting.html
    population.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap()); // sort descending based on score

    for i in 0..selection_size {
        result.push(population[i].clone());
    }

    result
}
pub fn apply_elitism(population: &mut Vec<Individual>, elites: Vec<Individual>) -> Vec<Individual>{
    let selection_size = elites.len();

    population.sort_by(|a, b| a.score.partial_cmp(&b.score).unwrap()); // sort ascending based on score
    //Schlechteste Ergebisse mit entfernen & eliten aus der letzen Generation hinzufügen
    population.drain(0..selection_size);
    
    for elite in elites{
        population.push(elite);
    }

    population.to_vec()
}