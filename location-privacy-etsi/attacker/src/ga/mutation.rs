use crate::types::*;

use rand::{Rng, seq::SliceRandom};

//Swap Mutation
pub fn mutation_small(mut mutant:Individual) -> Individual {
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
pub fn mutation_big(mut mutant:Individual) -> Individual {
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
pub fn mutation_split(mut mutant:Individual) -> Individual {
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
        if mutant.genome[i] == id_target{
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

pub fn mutation_merge(mut mutant:Individual) -> Individual {
    let genome_len = mutant.genome.len();

    let id_pick = rand::thread_rng().gen_range(0..genome_len);
    let id_target = mutant.genome[id_pick];

    //Zufälligen Teil auswählen & den kleinsten Trip mergen
    let tournament_size = 10;
    let tournament:Vec<u32> = mutant.genome.choose_multiple(&mut rand::thread_rng(), tournament_size).cloned().collect();
    let mut id_victim = id_target;
    let mut victim_trip_size = 9999;
    for trip in tournament{
        let trip_size = mutant.genome.iter().filter(|&n| *n == trip).count();
        if trip_size < victim_trip_size{
            victim_trip_size = trip_size;
            id_victim = trip;
        }
    }
    if id_victim == id_target { return mutant; } //Falls wir keinen anderen Trip gefunden haben

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