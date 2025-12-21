use crate::types::Individual;
use crate::ga::{
    crossover::*,
    mutation::*,
};


pub fn evolution(parents: Vec<Individual>, 
                mutation_rate: f32, 
                p_mutation_small: f32,
                p_mutation_big: f32,
                p_mutation_split: f32,
                p_mutation_merge: f32,
            ) -> Vec<Individual>{
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

        // Apply split mutation with probability
        if rand::random::<f32>() < (p_mutation_split*mutation_rate) {
            child1 = mutation_split(child1);
        }
        if rand::random::<f32>() < (p_mutation_split*mutation_rate) {
            child2 = mutation_split(child2);
        }

        // Apply merge mutation with probability
        if rand::random::<f32>() < (p_mutation_merge*mutation_rate) {
            child1 = mutation_merge(child1);
        }
        if rand::random::<f32>() < (p_mutation_merge*mutation_rate) {
            child2 = mutation_merge(child2);
        }

        next_generation.push(child1);
        next_generation.push(child2);
    }
    next_generation
}