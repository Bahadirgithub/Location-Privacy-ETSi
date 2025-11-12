# coding: utf-8
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from model.Worker import Worker
from model.PartTimeWorker import PartTimeWorker
from model.NightWorker import NightWorker
from model.Homestay import Homestay
from model.Freelance import Freelance

from utils import map_parser
from model.Agent import *
from model.District import *
from model.Location import *

from lxml import etree
import csv, argparse, time, numpy as np, yaml, random
from datetime import datetime
import random

# Globale Variable für die geladene Konfiguration
agent_config = None


# Parse map and create locations from edges
def create_test_locations(map_path):
    locations = []
    edges = map_parser.parse_map_edges(map_path, districts)
    for e in edges:
        loc = Location(e)
        locations.append(loc)
        for d in districts:
            if e in d.edges:
                d.locations.append(loc)
    return locations


# create and test agents
# Nimmt die geladenen Profile und Prozentsätze entgegen
def create_test_agents(number, locations, profiles, percentages):
    test_agents = []

    # Prozente sind Brüche (0–1). Erzeuge Stückzahlen:
    number_of_parttime   = int(number * percentages.get('parttimeworker', 0.0))
    number_of_nightworker = int(number * percentages.get('nightworker', 0.0))
    number_of_homestay   = int(number * percentages.get('homestay', 0.0))
    number_of_freelance  = int(number * percentages.get('freelance', 0.0))
    # Rest sind Worker
    number_of_worker = number - (number_of_parttime + number_of_nightworker +
                                 number_of_homestay + number_of_freelance)

    # Start-Indizes
    start_parttime   = 0
    start_nightworker = start_parttime + number_of_parttime
    start_homestay   = start_nightworker + number_of_nightworker
    start_freelance  = start_homestay + number_of_homestay
    start_worker     = start_freelance + number_of_freelance

    # Debug
    print("Agenten-Verteilung wird erstellt:")
    print(f"  PartTimeWorker: {number_of_parttime}")
    print(f"  NightWorker:    {number_of_nightworker}")
    print(f"  Homestay:       {number_of_homestay}")
    print(f"  Freelance:      {number_of_freelance}")
    print(f"  Worker:         {number_of_worker}")
    print(f"  GESAMT:         {number}")

    for i in range(number):
        if i < start_nightworker:
            # PartTimeWorker
            test_agents.append(
                PartTimeWorker(
                    'pt_worker' + str(i),
                    random.choice(home_district.locations),
                    random.choice(work_district.locations),
                    np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False),
                    profiles['parttimeworker']
                )
            )
        elif i < start_homestay:
            # NightWorker
            test_agents.append(
                NightWorker(
                    'n_worker' + str(i),
                    random.choice(home_district.locations),
                    random.choice(work_district.locations),
                    random.choice(locations),
                    np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False),
                    profiles['nightworker']
                )
            )
        elif i < start_freelance:
            # Homestay
            test_agents.append(
                Homestay(
                    'homestay' + str(i),
                    random.choice(home_district.locations),
                    random.choice(locations),  # school
                    random.choice(locations),  # grocery
                    random.choice(locations),  # activity
                    np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False),
                    profiles['homestay']
                )
            )
        elif i < start_worker:
            # Freelance
            test_agents.append(
                Freelance(
                    'freelance' + str(i),
                    random.choice(home_district.locations),
                    np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False),
                    profiles['freelance']
                )
            )
        else:
            # Worker (Full-Time)
            test_agents.append(
                Worker(
                    'worker' + str(i),
                    random.choice(home_district.locations),
                    random.choice(work_district.locations),
                    random.choice(locations),
                    np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False),
                    profiles['worker']
                )
            )
    return test_agents


# Generate sorted demand XML tags
def generate_demand(agents, duration):
    demand = []
    for a in agents:
        demand += a.generate_demand(duration)
    demand.sort(key=lambda x: int(x.depart))
    return demand


# Generate entire demand and file.
def generate_demand_file(filename, agents, duration):
    root = etree.Element('routes')
    for a in agents:
        root.append(etree.Element('vType', id=a.id, accel='1.0', decel='5.0',
                                  length='5.0', maxSpeed='50.0', sigma='0.0'))
    demand = generate_demand(agents, duration)
    for d in demand:
        # 'from' ist Schlüsselwort; daher set()
        new = etree.Element('trip')
        new.set('id', d.id)
        new.set('type', d.agent.id)
        new.set('depart', d.depart)
        new.set('from', d.start.edge_id)
        new.set('to', d.end.edge_id)
        root.append(new)
    tree = etree.ElementTree(root)
    tree.write(filename, pretty_print=True)


# run script for demand generation
def generate():
    test_locations = create_test_locations(in_path + mapin)

    test_agents = create_test_agents(
        number_of_agents,
        test_locations,
        agent_config['agent_profiles'],
        agent_config['agent_distribution']
    )

    generate_demand_file(out_path + routesout, test_agents, number_of_days)

    veh_map_path = out_path + vehmapout
    with open(veh_map_path, 'w', newline='') as veh_map_file:
        writer = csv.writer(veh_map_file)
        writer.writerow(['trip_id', 'vehicle_id'])
        for agent in test_agents:
            for trip_id in agent.trip_ids:
                writer.writerow([trip_id, agent.id])


# Write report file
def report():
    time1 = time.time()
    rep_end = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open(rep_path + rep_name, 'a', encoding='utf-8') as f:
        f.write('-------------------- Report of AGENT GENERATION --------------------\n\n')
        f.write('Name of script:             ' + os.path.basename(sys.argv[0]) + '\n')
        f.write('Evaluation started at       ' + str(rep_start) + '\n')
        f.write('Evaluation ended at         ' + str(rep_end) + '\n')
        f.write('Runtime:                    ' + str(time1 - time0) + '\n\n')
        f.write('Agent Config File:          ' + str(args.agent_config_path) + '\n')
        f.write('Map used:                   ' + str(mapin) + '\n\n')
        f.write('Number of agents:           ' + str(number_of_agents) + '\n')
        f.write('Agent Distribution:\n')
        for key, value in agent_config['agent_distribution'].items():
            f.write(f'  {key}: {round(value * 100, 2)}%\n')  # value is a fraction
        f.write('Number of days:             ' + str(number_of_days) + '\n\n')
        f.write('Routing written to          ' + str(out_path + routesout) + '\n')
        f.write('Vehicle map written to      ' + str(out_path + vehmapout) + '\n\n')
        f.write('-------------------------- END of report ---------------------------\n\n')
    print("Report written to '" + rep_path + rep_name + "'")


# Gets command line arguments
def get_options():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument('--inpath', dest='in_path', type=str, default='../rsc/traffic/',
                        help='Relative path to resource file directory')
    parser.add_argument('--outpath', dest='out_path', type=str, default='../rsc/traffic/',
                        help='Relative path to output directory')
    parser.add_argument('--agents', dest='number_of_agents', type=int, default=20,
                        help='Number of agents')

    # Pfad zur YAML-Konfiguration der Agenten
    parser.add_argument('--agentconfig', dest='agent_config_path', type=str,
                        default='../rsc/config/agent_profiles.yaml',
                        help='Path to agent profiles config YAML file')

    parser.add_argument('--days', dest='number_of_days', type=int, default=30,
                        help='Number of days')
    parser.add_argument('--mapin', dest='map_input_name', type=str, default='map.xml')
    parser.add_argument('--routesout', dest='routes_output_name', type=str, default='routes.xml')
    parser.add_argument('--vehmapout', dest='vehicle_map_output_name', type=str, default='vehicle_map.csv')
    parser.add_argument('--homedistrict', dest='home_district', type=str, default='')
    parser.add_argument('--workdistrict', dest='work_district', type=str, default='')
    parser.add_argument('--reportpath', dest='report_path', type=str, default='../rsc/reports/',
                        help='Report output directory')
    parser.add_argument('--reportname', dest='report_name', type=str, default='report.txt',
                        help='Set report name')
    parser.add_argument('--no-report', dest='report', action='store_false', help='Do not write report')
    parser.set_defaults(report=True)
    return parser.parse_args()


def string_to_polygon_array(polygon_string):
    if not polygon_string:
        return []
    dist_parse = polygon_string.split(' ')
    result = []
    for pt in dist_parse:
        coords = pt.split(',')
        if len(coords) != 2:
            continue
        result.append([int(coords[0]), int(coords[1])])
    return result


if __name__ == "__main__":
    # CLI args
    args = get_options()
    in_path = args.in_path
    out_path = args.out_path
    rep_path = args.report_path
    rep_name = args.report_name
    number_of_agents = args.number_of_agents

    # Agenten-Konfig laden
    try:
        with open(args.agent_config_path, 'r', encoding='utf-8') as f:
            agent_config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"FATAL ERROR: Agent config file not found at: {args.agent_config_path}")
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR: Could not parse YAML file: {e}")
        sys.exit(1)

    # Prozentwerte in Brüche umrechnen und Summe prüfen
    specialized_percentage_sum = 0.0
    for agent_type, percentage in list(agent_config['agent_distribution'].items()):
        frac = float(percentage) / 100.0
        agent_config['agent_distribution'][agent_type] = frac
        specialized_percentage_sum += frac

    if specialized_percentage_sum > 1.0 + 1e-9:
        raise ValueError("Invalid percentages in YAML. Total of specialized agents exceeds 100%.")

    # Rest = Worker
    agent_config['agent_distribution']['worker'] = max(0.0, 1.0 - specialized_percentage_sum)

    number_of_days = args.number_of_days
    mapin = args.map_input_name
    routesout = args.routes_output_name
    vehmapout = args.vehicle_map_output_name

    home_district = District(string_to_polygon_array(args.home_district))
    work_district = District(string_to_polygon_array(args.work_district))
    districts = [home_district, work_district]

    # Global report variables
    time0 = time.time()
    rep_start = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Generate demand
    generate()

    # Write report except flag --no-report is set
    if args.report:
        report()