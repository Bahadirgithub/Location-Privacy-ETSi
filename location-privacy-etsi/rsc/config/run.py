import os
import sys
from time import time
import yaml


# Helper to run commands safely
def run_command(module_name, exe_cmd):
    print(f"Executing: {exe_cmd}")
    exit_code = os.system(exe_cmd)
    if exit_code != 0:
        print(f"❌ ERROR: {module_name} failed with exit code {exit_code}")
        sys.exit(1)


def generate():
    print('\n-- Generation module --')
    # FIX: Added escaped quotes \" around path and sys.executable to handle spaces
    exe = f"cd \"{generation.get('path')}\" && \"{sys.executable}\" {generation.get('script')}"

    exe += f" --inpath {generation.get('inpath')}"
    exe += f" --outpath {generation.get('outpath')}"
    exe += f" --agents {generation.get('agents')}"
    exe += f" --agentconfig {generation.get('agentconfig')}"
    exe += f" --days {generation.get('days')}"
    exe += f" --mapin {generation.get('mapin')}"
    exe += f" --routesout {generation.get('groutesout')}"
    exe += f" --vehmapout {generation.get('gvehmapout')}"
    # Quotes for arguments that might contain spaces
    exe += f" --homedistrict {generation.get('homedistrict')}"
    exe += f" --workdistrict {generation.get('workdistrict')}"

    if not generation.get('report'):
        exe += ' --no-report '
    exe += f" --reportpath {generation.get('reportpath')}"
    exe += f" --reportname {generation.get('reportname')}"

    run_command("Generation", exe)


def simulate():
    print('\n-- Simulation module --')
    # FIX: Added escaped quotes \" around path and sys.executable
    exe = f"cd \"{simulation.get('path')}\" && \"{sys.executable}\" {simulation.get('simulator')}"

    exe += f" --inpath {simulation.get('inpath')}"
    exe += f" --outpath {simulation.get('outpath')}"
    if simulation.get('gui'):
        exe += ' --gui'
    exe += f" --sumocfg {simulation.get('sumocfg')}"
    exe += f" --cout {simulation.get('coutput')}"
    exe += f" --aout {simulation.get('aoutput')}"
    exe += f" --junctions {simulation.get('junctions')}"
    exe += f" --detectors {simulation.get('detectors')}"
    exe += f" --tripinfo {simulation.get('tripinfo')}"
    exe += f" --seed {simulation.get('seed')}"

    if not simulation.get('report'):
        exe += ' --no-report '
    exe += f" --reportpath {simulation.get('reportpath')}"
    exe += f" --reportname {simulation.get('reportname')}"

    run_command("Simulation", exe)


def attack():
    print('\n-- Attacker module --')
    # FIX: Added escaped quotes \"
    exe = f"cd \"{attacker.get('path')}\" && \"{sys.executable}\" {attacker.get('attack')}"

    exe += f" --knowledge {attacker.get('input')}"
    exe += f" --output {attacker.get('output')}"
    exe += f" --report {report_file}"

    run_command("Attacker", exe)


def attackerAdvanced():
    print('\n-- Attacker Advanced module --')
    # FIX: Added escaped quotes \"
    exe = f"cd \"{attackerAdvanc.get('path')}\" && \"{sys.executable}\" {attackerAdvanc.get('attack')}"

    exe += f" --knowledge {attackerAdvanc.get('input')}"
    exe += f" --output {attackerAdvanc.get('output')}"
    exe += f" --report {report_file}"
    exe += f" --simulatedAnnealing {attackerAdvanc.get('simulatedAnnealing')}"
    exe += f" --simulatedTimes {attackerAdvanc.get('simulatedTimes')}"

    run_command("Attacker Advanced", exe)


def evaluate():
    print('\n-- Evaluation module --')
    # FIX: Added escaped quotes \"
    exe = f"cd \"{eval_config.get('path')}\" && \"{sys.executable}\" {eval_config.get('evaluator')}"

    exe += f" --challenger {eval_config.get('challenger')}"
    exe += f" --attacker {eval_config.get('attacker')}"
    exe += f" --report {report_file}"

    run_command("Evaluation", exe)


if __name__ == "__main__":
    # Load yaml config file
    config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)

    # Global variable for report filename
    report_file = config.get('report')

    # Initialize report file
    try:
        report_dir = '../reports/'
        if not os.path.exists(report_dir):
            os.makedirs(report_dir, exist_ok=True)

        with open(report_dir + report_file, 'w') as f:
            f.write("Run started\n")
    except FileNotFoundError:
        print("Warning: Could not write to ../reports/. Check directory existence.")

    # Get sections
    generation = config.get('generation')
    simulation = config.get('simulation')
    attacker = config.get('attacker')
    attackerAdvanc = config.get('attackerAdvanced')
    eval_config = config.get('evaluation')

    # Execution Logic
    if generation.get('run'):
        generate()

    if simulation.get('run'):
        simulate()

    if attacker and attacker.get('run'):
        attack()

    if attackerAdvanc and attackerAdvanc.get('run'):
        attackerAdvanced()

    if eval_config and eval_config.get('run'):
        evaluate()

    # Rename output files for archiving if simulation ran successfully
    if simulation.get('run'):
        base_path = '../' + simulation.get('outpath')
        # Ensure base path ends with / if not empty
        if base_path and not base_path.endswith('/'):
            base_path += '/'

        old_cout = base_path + simulation.get('coutput')
        new_cout = base_path + f"{generation.get('net_prefix')}_{generation.get('agents')}_{generation.get('days')}_{simulation.get('coutput')}"

        old_aout = base_path + simulation.get('aoutput')
        new_aout = base_path + f"{generation.get('net_prefix')}_{generation.get('agents')}_{generation.get('days')}_{simulation.get('aoutput')}"

        if os.path.exists(old_cout):
            os.replace(old_cout, new_cout)
            print(f"Renamed {old_cout} -> {new_cout}")
        else:
            print(f"Warning: {old_cout} not found.")

        if os.path.exists(old_aout):
            os.replace(old_aout, new_aout)
            print(f"Renamed {old_aout} -> {new_aout}")