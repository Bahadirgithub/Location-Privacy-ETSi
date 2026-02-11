### What is PyO3 and Maturin?
**PyO3** and **Maturin** are both tools in the Python ecosystem that are commonly used to bridge Python and Rust, enabling you to write high-performance Python extensions using Rust.
- **PyO3** is a Rust crate (library) that allows you to write **native Python extensions in Rust**. It provides bindings to the Python C API, which allows you to interact with Python from Rust and vice versa.
- **Maturin** is a tool that **simplifies the process of building and packaging** Python extensions written in Rust . It is specifically designed to handle the *compilation of Rust code into Python modules.*

### Requirements
1. **Install the Rust Compiler**
	-  You need to have the Rust compiler (`rustc`) installed on your machine.
	- To install Rust, visit the official Rust installation page (https://rust-lang.org/tools/install/)
	- You can check if Rust is installed by running: `rustc --version`
2. **Install PyO3 and Maturin**
	- First, make sure you have Python installed on your machine *(version 3.6 or higher)*. Then, install Maturin via `pip`: `pip install maturin`
	- PyO3 is a Rust crate, so it **doesn't require installation** through Python's package manager. Instead, you’ll include it in your `Cargo.toml` file when creating your Rust project.
3. **Create a Virtual Environment for Python**
	- **Important**: Change to the folder where you want the virtual environment to be created. For example, if you're using the folder `attacker`, navigate there with the command: `cd /path/to/attacker`
	- Create a virtual environment: `python -m venv .venv`
	- Activate the virtual environment:
		- On Windows: `.venv\Scripts\activate`
		- On macOs/Linux: `source .venv/bin/activate`
	- To install all the **required Python dependencies**, run the following command:                   `pip install -r ../requirements.txt`

### Compile and Use
1. **Compile with Maturin:**
	- To compile the Rust project as a Python extension, you can use the following command: `maturin develop`
	- This will build the extension in **development mode**. In development mode, the build is not fully optimized, allowing for quicker compilation times and easier debugging.
2. **Compile for Release (Optimized Build):**
	- If you want to **test the performance** of your code , you can compile the extension with optimizations enabled by running: `maturin develop --release`
	- The `--release` flag will **trigger optimizations in the Rust build**, which can significantly improve the performance of the extension but might take longer to compile.
3. **Handling Previous Builds:**
	- If you've already compiled a version of the extension and run `maturin develop` again, the compiled binary will not be overwritten by default.
	- If you want to replace the previously installed version, you'll need to **uninstall the existing Python package** (in this case, `genetic`) first. To do so, run: `pip uninstall genetic`

