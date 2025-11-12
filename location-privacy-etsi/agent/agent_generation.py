# coding: utf-8
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
import csv
import argparse
import sys
import time
import numpy as np
import yaml  # Importiert yaml, um Konfigurationsdateien zu lesen
from datetime import datetime


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
# Diese Funktion nimmt jetzt die geladenen Profile und Prozentsätze entgegen
def create_test_agents(number, locations, profiles, percentages):
    test_agents = []

    # Berechne die genaue Anzahl für jeden Typ basierend auf den Prozentzahlen
    number_of_parttime = int(number * percentages['parttimeworker'])
    number_of_nightworker = int(number * percentages['nightworker'])
    number_of_homestay = int(number * percentages['homestay'])
    number_of_freelance = int(number * percentages['freelance'])
    # Der Rest sind Worker
    number_of_worker = number - (number_of_parttime + number_of_nightworker + number_of_homestay + number_of_freelance)

    # Berechne die Start-Indizes für eine saubere Zuweisung
    start_parttime = 0
    start_nightworker = start_parttime + number_of_parttime
    start_homestay = start_nightworker + number_of_nightworker
    start_freelance = start_homestay + number_of_homestay
    start_worker = start_freelance + number_of_freelance

    # Debug-Ausgabe, um die Verteilung zu prüfen (kann später entfernt werden)
    print(f"Agenten-Verteilung wird erstellt:")
    print(f"  PartTimeWorker: {number_of_parttime}")
    print(f"  NightWorker:    {number_of_nightworker}")
    print(f"  Homestay:       {number_of_homestay}")
    print(f"  Freelance:      {number_of_freelance}")
    print(f"  Worker:         {number_of_worker}")
    print(f"  GESAMT:         {number}")

    for i in range(number):
        if i < start_nightworker:
            # --- Erstelle PartTimeWorker ---
            test_agents.append(
                PartTimeWorker('pt_worker' + str(i),
                               random.choice(home_district.locations),
                               random.choice(work_district.locations),
                               np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False),
                               profiles['parttimeworker']  # Übergibt das Konfigurations-Profil
                               ))
        elif i < start_homestay:
            # --- Erstelle NightWorker ---
            test_agents.append(
                NightWorker('n_worker' + str(i),
                            random.choice(home_district.locations),
                            random.choice(work_district.locations),
                            random.choice(locations),
                            np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False),
                            profiles['nightworker']  # Übergibt das Konfigurations-Profil
                            ))
        elif i < start_freelance:
            # --- Erstelle Homestay ---
            test_agents.append(
                Homestay('homestay' + str(i),
                         random.choice(home_district.locations),
                         random.choice(locations),  # school
                         random.choice(locations),  # grocery
                         random.choice(locations),  # activity
                         np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False),
                         profiles['homestay']  # Übergibt das Konfigurations-Profil
                         ))
        elif i < start_worker:
            # --- Erstelle Freelance ---
            test_agents.append(
                Freelance('freelance' + str(i),
                          random.choice(home_district.locations),
                          np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False),
                          profiles['freelance']  # Übergibt das Konfigurations-Profil
                          ))
        else:
            # --- Erstelle Worker (Full-Time) ---
            test_agents.append(
                Worker('worker' + str(i),
                       random.choice(home_district.locations),
                       random.choice(work_district.locations),
                       random.choice(locations),
                       np.random.choice(locations, random.choice([1, 2, 3, 4, 5]), replace=False),
                       profiles['worker']  # Übergibt das Konfigurations-Profil
                       ))
    return test_agents


# Generate sorted demand XML tags
def generate_demand(agents, duration):
    demand = []
    for a in agents:
        demand += a.generate_demand(duration)
    demand.sort(key=lambda x: int(x.depart), reverse=False)
    return demand


# Generate entire demand and file.
def generate_demand_file(filename, agents, duration):
    root = etree.Element('routes')
    for a in agents:
        root.append(etree.Element('vType', id=a.id, accel='1.0', decel='5.0',
                                  length='5.0', maxSpeed='50.0', sigma='0.0'))
    demand = generate_demand(agents, duration)
    for d in demand:
        # Cannot use the typical constructor etree.Element('trip',id=...) because the word from is a Python keyword which cannot be used outside of string declarations
        # I.e. the string 'from = d.start.edge_id' is not possible
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

    # Übergibt die geladenen Profile und Prozentsätze an die Erstellungs-Funktion
    test_agents = create_test_agents(number_of_agents,
                                     test_locations,
                                     agent_config['agent_profiles'],
                                     agent_config['agent_distribution'])

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
    f = open(rep_path + rep_name, 'a')
    f.write('-------------------- Report of AGENT GENERATION --------------------\n\n')
    f.write('Name of simulation script:   ' + sys.argv[0] + '\n')
    f.write('Evaluation started at        ' + str(rep_start) +'\n')
    f.write('Evaluation ended at          ' + str(rep_end) +'\n')
    f.write('Runtime:                     ' + str(time1 - time0) + '\n\n')
    f.write('Agent Config File:   ' + str(args.agent_config_path) + '\n') # Zeigt an, welche Konfig verwendet wurde
    f.write('Map used:            ' + str(mapin) + '\n\n')
    f.write('Number of agents:    ' + str(number_of_agents) + '\n')
    # Hier könnten wir die Verteilung aus der Config ins Log schreiben
    f.write('Agent Distribution:\n')
    for key, value in agent_config['agent_distribution'].items():
        f.write(f'  {key}: {value}%\n')

    f.write('Number of days:      ' + str(number_of_days) + '\n\n')
    f.write('Routing written to       ' + str(out_path + routesout) + '\n')
    f.write('Vehicle map written to   ' + str(in_path + vehmapout) + '\n\n')
    f.write('-------------------------- END of report ---------------------------\n\n')
    print('Report written to ' + "'" + rep_path + rep_name + "'")


# Gets command line arguments using the argparse module
def get_options():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument('--inpath', dest='in_path', type=str, default='../rsc/traffic/', help='Relative path to resource file directory')
    parser.add_argument('--outpath', dest='out_path', type=str, default='../rsc/traffic/', help='Relative path to output directory')
    parser.add_argument('--agents', dest='number_of_agents', type=int, default=20, help='Number of agents')

    # --- ENTFERNTE ARGUMENTE ---
    # Die Prozent-Argumente werden entfernt, da sie jetzt aus der YAML-Datei kommen
    # parser.add_argument('--parttime', dest='parttime_percentage', type=int, default=10)
    # parser.add_argument('--nighttime', dest='nighttime_percentage', type=int, default=10)
    # parser.add_argument('--homestay', dest='homestay_percentage', type=int, default=15)
    # parser.add_argument('--freelance', dest='freelance_percentage', type=int, default=15)

    # --- NEUES ARGUMENT ---
    # Fügt ein Argument hinzu, um den Pfad zur neuen YAML-Konfigurationsdatei anzugeben
    parser.add_argument('--agentconfig', dest='agent_config_path', type=str, default='../rsc/config/agent_profiles.yaml', help='Path to agent profiles config YAML file')

    parser.add_argument('--days', dest='number_of_days', type=int, default=30, help='Number of days')
    parser.add_argument('--mapin', dest='map_input_name', type=str, default='map.xml')
    parser.add_argument('--routesout', dest='routes_output_name', type=str, default='routes.xml')
    parser.add_argument('--vehmapout', dest='vehicle_map_output_name', type=str, default='vehicle_map.csv')
    parser.add_argument('--homedistrict', dest='home_district', type=str, default='')
    parser.add_argument('--workdistrict', dest='work_district', type=str, default='')
    parser.add_argument('--reportpath', dest='report_path', type=str, default='../rsc/reports/', help='Report output directory')
    parser.add_argument('--reportname', dest='report_name', type=str, help='Set report name', default='report.txt')
    parser.add_argument('--no-report', dest='report', action='store_false', help='Do not write report')
    parser.set_defaults(report=True)
    return parser.parse_args()


def string_to_polygon_array(polygon_string):
    dist_parse = polygon_string.split(' ')
    result = []
    for pt in dist_parse:
        coords = pt.split(',')
        result.append([int(coords[0]), int(coords[1])])
    return result


if __name__ == "__main__":
    # Copy args.arguments to ‘regular’ arguments
    args = get_options()
    in_path = args.in_path
    out_path = args.out_path
    rep_path = args.report_path
    rep_name = args.report_name
    number_of_agents = args.number_of_agents

    # --- NEUE LOGIK ZUM LADEN DER KONFIGURATION ---
    # Lade die Agenten-Konfigurationsdatei
    try:
        with open(args.agent_config_path, 'r') as f:
            agent_config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"FATAL ERROR: Agent config file not found at: {args.agent_config_path}")
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR: Could not parse YAML file: {e}")
        sys.exit(1)

    # Berechne die Prozent-Summe der spezialisierten Agenten
    specialized_percentage_sum = 0
    for agent_type, percentage in agent_config['agent_distribution'].items():
        agent_config['agent_distribution'][agent_type] = percentage / 100.0
        specialized_percentage_sum += percentage / 100.0

    if specialized_percentage_sum > 1.0:
        raise ValueError("Invalid percentages in YAML. Total of specialized agents exceeds 100%.")

    # Füge den 'worker' als den verbleibenden Rest hinzu (z.B. 1.0 - 0.45 = 0.55)
    # Das entspricht deinen 55%
    agent_config['agent_distribution']['worker'] = 1.0 - specialized_percentage_sum

    # --- ENTFERNTE LOGIK ---
    # Die alten Prozent-Berechnungen werden entfernt
    # parttime_percentage = args.parttime_percentage / 100.0
    # ...

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