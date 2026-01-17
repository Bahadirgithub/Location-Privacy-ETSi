use crate::types::*;

use rand::Rng;

//Two-Point Crossover
pub fn crossover(parent_1:Individual, parent_2:Individual) -> (Individual, Individual){
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