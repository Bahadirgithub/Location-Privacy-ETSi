    use pyo3::prelude::*;
    
    #[pyclass]
    #[derive(Clone)]
    pub struct Individual {
        #[pyo3(get, set)]
        pub genome: Vec<u32>,
        #[pyo3(get, set)]
        pub score: f64
    }

    #[pyclass]
    #[derive(Clone)]
    pub struct Transaction {
        #[pyo3(get, set)]
        pub id: u32,
        #[pyo3(get, set)]
        pub detector: u32,
        #[pyo3(get, set)]
        pub time: u32,
        #[pyo3(get, set)]
        pub cost: f32,
    }

    #[pyclass]
    #[derive(Clone)]
    pub struct SimulatedTime {
        #[pyo3(get, set)]
        pub from_detector: u32,
        #[pyo3(get, set)]
        pub to_detector: u32,
        #[pyo3(get, set)]
        pub avg: f32,
        #[pyo3(get, set)]
        pub min: f32,
        #[pyo3(get, set)]
        pub max: f32,
    }

    #[pyclass]
    #[derive(Clone)]
    pub struct Trip {
        #[pyo3(get, set)]
        pub id: usize,
        #[pyo3(get, set)]
        pub cost: u32,
        #[pyo3(get, set)]
        pub start_time: u32,
        #[pyo3(get, set)]
        pub end_time: u32,
        #[pyo3(get, set)]
        pub start_loc_id: usize,
        #[pyo3(get, set)]
        pub end_loc_id: usize,
    }