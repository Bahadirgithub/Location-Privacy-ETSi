import os
import sys
from time import time
import yaml

def generate():
    print('\n-- Generation module --')
    # Use quotes around arguments that might contain spaces (like districts)
    exe = f"cd {generation.get('path')} && {sys.executable} {generation.get('script')}"
    exe += f" --inpath {generation.get('inpath')}"
    exe += f" --outpath {generation.get('outpath')}"
    exe += f" --agents {generation.get('agents')}"
    exe += f" --agentconfig {generation.get('agentconfig')}"
    exe += f" --days {generation.get('days')}"
    exe += f" --mapin {generation.get('mapin')}"
    exe += f" --routesout {generation.get('groutesout')}"
    exe += f" --vehmapout {generation.get('gvehmapout')}"
    # Quotes added for polygon strings
    exe += f" --homedistrict \"{generation.get('homedistrict')}\""
    exe += f" --workdistrict \"{generation.get('workdistrict')}\""

    if not generation.get('report'):
        exe += ' --no-report '
    exe += f" --reportpath {generation.get('reportpath')}"
    exe += f" --reportname {generation.get('reportname')}"

    print(f"Executing: {exe}") # Debug print
    os.system(exe)

def simulate():
    print('\n-- Simulation module --')
    exe = f"cd {simulation.get('path')} && {sys.executable} {simulation.get('simulator')}"
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
    os.system(exe)

def attack():
    print('\n-- Attacker module --')
    exe = f"cd {attacker.get('path')} && {sys.executable} {attacker.get('attack')}"
    exe += f" --knowledge {attacker.get('input')}"
    exe += f" --output {attacker.get('output')}"
    # 'report' here refers to the filename variable from __main__
    exe += f" --report {report_file}"
    os.system(exe)

def attackerAdvanced():
    print('\n-- Attacker Advanced module --')
    exe = f"cd {attackerAdvanc.get('path')} && {sys.executable} {attackerAdvanc.get('attack')}"
    exe += f" --knowledge {attackerAdvanc.get('input')}"
    exe += f" --output {attackerAdvanc.get('output')}"
    exe += f" --report {report_file}"
    exe += f" --simulatedAnnealing {attackerAdvanc.get('simulatedAnnealing')}"
    exe += f" --simulatedTimes {attackerAdvanc.get('simulatedTimes')}"
    os.system(exe)

def evaluate():
    print('\n-- Evaluation module --')
    # Renamed 'eval' to 'eval_config' to avoid python keyword conflict
    exe = f"cd {eval_config.get('path')} && {sys.executable} {eval_config.get('evaluator')}"
    exe += f" --challenger {eval_config.get('challenger')}"
    exe += f" --attacker {eval_config.get('attacker')}"
    exe += f" --report {report_file}"
    os.system(exe)

if __name__ == "__main__":
    # Load yaml config file
    config = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)

    # Global variable for report filename
    report_file = config.get('report')

    # Initialize report file
    try:
        with open('../reports/' + report_file, 'w') as f:
            f.write("Run started\n")
    except FileNotFoundError:
        print("Warning: Could not write to ../reports/. Check directory existence.")

    # Get sections
    generation = config.get('generation')
    simulation = config.get('simulation')
    attacker = config.get('attacker')
    attackerAdvanc = config.get('attackerAdvanced')
    eval_config = config.get('evaluation') # Renamed variable

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

    # Rename output files for archiving if simulation ran
    if simulation.get('run'):
        # Ensure paths have trailing slashes if needed or handle join cleanly
        base_path = '../' + simulation.get('outpath')

        old_cout = base_path + simulation.get('coutput')
        new_cout = base_path + f"{generation.get('net_prefix')}_{generation.get('agents')}_{generation.get('days')}_{simulation.get('coutput')}"

        old_aout = base_path + simulation.get('aoutput')
        new_aout = base_path + f"{generation.get('net_prefix')}_{generation.get('agents')}_{generation.get('days')}_{simulation.get('aoutput')}"

        if os.path.exists(old_cout):
            os.replace(old_cout, new_cout)
        if os.path.exists(old_aout):
            os.replace(old_aout, new_aout)