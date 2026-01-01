import argparse
import bisect
import collections
import os
import sys
import time
import networkx as nx
import xml.etree.ElementTree as ET
import random
from copy import copy
from tqdm import tqdm
from datetime import datetime
import genetic

#possible trip that was found with all the information
class Trip:
  def __init__(self, vehicle, timeStart, timeEnd, duration, cost, trip, used, deltaSum):
    self.vehicle = vehicle
    self.timeStart = timeStart
    self.timeEnd = timeEnd
    self.duration = duration
    self.cost= cost
    self.trip = trip #String with all Edges
    self.used = used    #int list with all ids that are used in this trip
    self.deltaSum = deltaSum    # the deviation from the avg. times from every edge in this trip


#generates a graph with connected detectors (nodes are the detectors).
def generateGraph():
    
    tree_detectors = ET.parse(simulated_times_file)
    root_detectors = tree_detectors.getroot()

    for detector in root_detectors.iter('route'):

        #nodes
        fromDetector = detector.attrib['fromDetector']  
        toDetector = detector.attrib['toDetector'] 

        #weights
        avg = float(detector.attrib['avg'])
        minTime = float(detector.attrib['minTime'])
        maxTime = float(detector.attrib['maxTime'])

        #create edge
        DG.add_edge(fromDetector, toDetector, avg=avg, min=minTime, max=maxTime)


def precompute_lookahead_cache():
    """
    Erstellt einen Cache für den schnellen Lookahead.
    Optimiert: Keine unnötigen Graph-Abfragen mehr.
    """
    # 1. Letzte Transaktionszeit pro Detektor ermitteln
    max_times = {}
    for det, trans_list in transaction_lookup.items():
        if trans_list:
            max_times[det] = trans_list[-1][0]

    lookahead_cache = {}

    # 2. Cache bauen
    # Wir iterieren über alle Knoten im Graphen. Da 'node' aus DG.nodes() kommt,
    # müssen wir NICHT prüfen, ob er existiert.
    for node in DG.nodes():
        max_future_time = 0

        # out_edges liefert direkt alle Nachbarn
        for _, neighbor, _ in DG.out_edges(node, data=True):
            # Nutze .get() für ultraschnellen Zugriff ohne Absturzrisiko
            t = max_times.get(neighbor, 0)
            if t > max_future_time:
                max_future_time = t

        lookahead_cache[node] = max_future_time

    return lookahead_cache


#find the trips with the best deviation from the avg. times
def findTrips():

    lastDetector = ""

    t=0 #time

    x=0 #used for the agend names

    sorted_indices = sorted(
        range(len(transactions_attacker_knowlege)),
        key=lambda k: int(transactions_attacker_knowlege[k].attrib['time'])
    )

    lookahead_cache = precompute_lookahead_cache()

    #go through every transaction, and try to find a possible trip
    for i in sorted_indices:

        #startpoint of the trip
        transaction = transactions_attacker_knowlege[i]
        first = True

        #string with all detector names, that are used in this trip
        result = ""

        #id of the transaction
        id = int(transaction.attrib['id'])

        #used to start the inner for loop at the right transaction
        inner_start=i

        #only search for a trip if the start transaction was't used before
        if not id in usedTrans:

            #get the informations from this startpoint
            lastDetector = transaction.attrib['detector']
            detector = transaction.attrib['detector']
            timeTrans = int(transaction.attrib['time'])
            cost = int(transaction.attrib['cost'])

            # remember start time
            timeStart = timeTrans

            #was at least one plausible trip edge found
            found = False

            #local used transaction ids
            locUsed = []

            # the deviation from the avg. times from every edge in this trip
            deltaSum = 0

            # list with every delta from this trip
            deltaSumArr=[]

            # array with the best deviations
            bestDeltas = []


            while(True):

                #check all outgoing edges from the detector
                for u, v, data in DG.out_edges(lastDetector, data=True):

                    #get all candidates for vector 'v'
                    if v not in transaction_lookup:
                        continue
                    candidate_transactions = transaction_lookup[v]

                    #calculate time slot we are searching
                    avg = data.get('avg')
                    min_travel = data.get('min') * 0.5
                    max_travel = min(data.get('max') * 3.0, 300)

                    min_time = timeTrans + min_travel
                    max_time = timeTrans + max_travel

                    #find starting point
                    start_index = bisect.bisect_left(candidate_transactions, (min_time, 0, None))

                    #iterate over remaining relevant transactions
                    for k in range(start_index, len(candidate_transactions)):
                        timeTrans_inner, id_inner, transaction_inner = candidate_transactions[k]

                        #stop if we leave the time slot
                        if timeTrans_inner > max_time:
                            break

                        #remaining checks

                        #if id_inner is not used yet
                        if id_inner not in usedTrans:
                            travel_time = timeTrans_inner - timeTrans
                            deltaTemp = abs(avg - travel_time)

                            # Check if the next detector is a dead end.
                            # If so, deltaTemp will be massively penalized (+1000s) so that we only dial it in an emergency.
                            next_det = transaction_inner.attrib['detector']

                            last_possible = lookahead_cache.get(next_det, 0)

                            has_continuation = last_possible > timeTrans_inner

                            # Apply punishment unless it's very late in the day (> 80,000s) where trips end naturally
                            if not has_continuation and timeTrans_inner < 80000:
                                deltaTemp += 1000

                            #save the best deltas
                            if (not found or deltaTemp < bestDeltas[-1][2]):
                                found = True

                                bestDeltas.append([id_inner, transaction_inner, deltaTemp, k])
                                # sort after the deltaTemp
                                bestDeltas.sort(key=lambda c: c[2])

                                # cut the array. only the n best trips will be saved
                                bestDeltas = bestDeltas[0:3]

                #get out the while loop if no trip was found
                if not found:
                    break
                else:

                    #add the values for the first trip node.
                    if first:
                        result = detector[6:-2] #only saves the edge name
                        first = False
                        locUsed.append(id)
                        usedTrans.add(id)

                    #Weighted Randomness
                    #Calculation: Weight = 1 / (delta + 1)^2 | The +1 prevents division by 0
                    weights = [1 / ((x[2] + 1.0) ** 2) for x in bestDeltas]

                    choice_data = random.choices(bestDeltas, weights=weights, k=1)[0]

                    #get one random entry from the array with the best values
                    outcome = bestDeltas.index(choice_data)

                    delta = bestDeltas[outcome][2]
                    transTemp = bestDeltas[outcome][1]
                    inner_start = bestDeltas[outcome][3]

                    #update last the detector
                    lastDetector= transTemp.attrib['detector']
                    t=int(transTemp.attrib['time'])
                    cost2 = int(transTemp.attrib['cost'])

                    #remeber used id
                    k=int(bestDeltas[outcome][0])
                    locUsed.append(k)
                    usedTrans.add(k)

                    #calculate delta avg.
                    deltaSumArr =  deltaSumArr + [delta]
                    deltaSumAvg=sum(deltaSumArr)/len(deltaSumArr)

                    # remove the lane and e1det
                    result = result + " " + lastDetector[6:-2]

                    #update costs
                    cost = cost + cost2

                    #update timestamp from the new detector
                    timeTrans = t

                    #reset
                    delta = -1
                    found = False
                    bestDeltas = []

            #save trip when no new plausible transaction were found
            if result != "":
                results.append(Trip("agent"+str(x),timeStart,t, t-timeStart, cost, set(result.split()), locUsed,deltaSumAvg))
                #update agend number
                x += 1

        
    # find the not used transactions and give them a high weight (100 here) -> a high priority to reduce them
    for l in sorted_indices:
       
        transac= transactions_attacker_knowlege[l]    
        id = int(transac.attrib['id'])
        if id not in usedTrans:
            det = (transac.attrib['detector'])[6:-2]
            
            results.append(Trip("agent"+str(x),int(transac.attrib['time']),int(transac.attrib['time']),int(transac.attrib['time']), int(transac.attrib['cost']),set([det]),[id] ,100))
            usedTrans.add(id)
            x += 1
    #sort results. worst deltaSum first     
    results.sort(key = lambda c: c.deltaSum, reverse=True)

#returns an array backwards
def backwards(array):
    n = 4
    half_n = n // 2
    #does a string transformation and adds it directly to a set instead of creating a temp array
    return {i[half_n:] + i[:half_n] for i in array}

#combines two trips and removes one of them
def copyTrip(tripA,tripB):   
    
    tripA.cost += tripB.cost
    tripA.trip = tripA.trip.union(tripB.trip)
    tripA.deltaSum = (tripA.deltaSum + tripB.deltaSum)/2    
    tripA.used += tripB.used
    results.remove(tripB)


#gives the sum of all deviation values
def delta():
    d = 0
    for trip in results:
        d +=trip.deltaSum        
    return d

#removes the worst trips from the usedTrans list, so that they can be reused
#only the best i/n trips will remain
def analyseTrips2(i, n):
    results.sort(key = lambda c: c.deltaSum)    
    leng = len(results)
    x = int(leng*(i/n))
    for i, trip in enumerate(results):
        if x < i:
            for used in trip.used:
                usedTrans.remove(used)
                
    del[results[x+1:]]            

#generates a new trip 
def randomTrip():
    global results,usedTrans
    results = []
    usedTrans = set([])  
    findTrips() 

#uses the best results with the lowest difference and tries to optimise the routes with simulated annealing
def simAn():
    global results,usedTrans,annealingResult
    
    #iterations for simulated annealing
    n = annealing
    findTrips()
    d = delta()  
    for i in tqdm(range(0,n), desc="Find Plausible Trips"):
        
        rC = copy(results)
        uTC = usedTrans.copy()        
        d = delta()    
        
        #if(i%10 == 0):
            #print (i, d)

        #only use i/n of the trips and calculate the rest again. remove the other transactions from usedTrans list
        analyseTrips2(i, n) 
         
        #calc. new results and store them temp.
        findTrips()
        newResult = copy(results)
        newUsedTrans = usedTrans.copy()  
        newD = delta()
        #calc. completely new results
        randomTrip()
        randomD = delta()
        
        if(d < newD and d < randomD):
                #if the old results were better, restore them
                usedTrans = uTC.copy() 
                results = copy(rC)
        else:
            if(newD < randomD):
                #if the results with only i/n of the trips is better load them
                d = newD
                usedTrans = copy(newUsedTrans) 
                results = newResult.copy()  

            else:
                #else use the random results
                d=randomD
    annealingResult = d


#creates a list with all wallet costs and a list with all result costs
def create_list():
    global walletCosts,resultCosts
    walletCosts = []
    resultCosts=[]
    for i in root_attacker_knowlege.iter('wallet'):
        walletCosts.append(int(i.attrib['total_wallet_cost']))

    for result in results:   
        resultCosts.append(result.cost)


def generate_Hashmap():
    global transaction_lookup
    print("Generating Transaction Lookup...")

    transaction_lookup = {}

    for trans in transactions_attacker_knowlege:
        detector_name = trans.attrib['detector']
        if detector_name not in transaction_lookup:
            transaction_lookup[detector_name] = []

        #Add Time and ID for sorting
        transaction_lookup[detector_name].append(
            (int(trans.attrib['time']), int(trans.attrib['id']), trans)
        )

    #Liste sortieren
    for det_list in transaction_lookup.values():
        det_list.sort()
    print("Hashmap Lookup generated.")


# Gets command line arguments using the argparse module
def get_options():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument('-p', '--path', dest='rsc_path', type=str, help='Relative path to resource files', default='../rsc/')    
    parser.add_argument('-k', '--knowledge', dest='input_file_name', type=str, help='Specify attacker knowledge to be used for attack', required=True)
    parser.add_argument('-o', '--output', dest='output_file_name', type=str, help='Set output xml file name', default='attacker_advanced.xml')
    parser.add_argument('-r', '--report', dest='report_name', type=str, help='Set report name', default='report.txt')
    parser.add_argument('-t', '--simulatedTimes', dest='simulated_times_input_file_name', type=str, help='Specify knowlege for the attacker with traveltimes', default='simulated-times.xml')
    parser.add_argument('-n', '--simulatedAnnealing', dest='simulatedAnnealing', type=int, help='Number of interations', default='2')
    return parser.parse_args()

# Write report file
def report():
    time1 = time.time()
    rep_end = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open('reports/' + rep_name, 'a+') as f:
        f.write('-------------------- Report of ADVANCED ATTACK --------------------\n\n')
        f.write('Name of attack script:   ' + sys.argv[0] + '\n')
        f.write('Attack started at        ' + str(rep_start) +'\n')
        f.write('Attack ended at          ' + str(rep_end) +'\n')
        f.write('Runtime:                 ' + str(time1 - time0) + '\n\n')
        f.write('simulated annealing iterations: ' + str(annealing) +'\n')
        f.write('simulated annealing result: ' + str(annealingResult) +'\n')
        f.write('Best Genetic result: ' + str(best_individual) + '\n')
        f.write('Attacker knowledge file is   ' + "'" + input_file_name + "'\n")
        f.write('- of file size               ' + str(os.path.getsize(input_file_name)) + ' bytes\n\n')
        f.write('Output file is   ' + "'" + 'attacks/' + output_file_name + "'\n")
        f.write('- of file size   ' + str(os.path.getsize('attacks/' + output_file_name)) + ' bytes\n\n')
       
        f.write('-------------------- END of report --------------------\n\n')
    
    print('Report written to ' + "'" + 'reports/' + rep_name + "'")


def main():
    global DG,results,usedTrans,tree_attacker_knowlege,root_attacker_knowlege
    global transactions_attacker_knowlege
    global best_individual
      #create new networkx graph
    DG = nx.DiGraph()

    #list with found trips
    results=[] 

    #set with the used trip ids
    usedTrans = set([])


    tree_attacker_knowlege = ET.parse(input_file_name)
    
    root_attacker_knowlege = tree_attacker_knowlege.getroot()

    
    transactions_attacker_knowlege = root_attacker_knowlege[0]

    output_root = ET.Element('attack')

    

    print("Start Attacker")
    #generate the graph with the detector nodes
    generateGraph()
    #generate Hashmap Lookup
    generate_Hashmap()
    #find trips
    simAn()
    create_list()

    print("Number of Transactions: ", len(transactions_attacker_knowlege), ", Number of Trips: ", len(results), ", Number of Wallets: ", len(walletCosts))


    # Globales Dictionary für das Mapping
    detector_mapping = {}

    def get_detector_id(detector_name):
        if detector_name not in detector_mapping:
            # Die neue ID ist einfach die aktuelle Länge des Dictionaries
            detector_mapping[detector_name] = len(detector_mapping)
        return detector_mapping[detector_name]

    rust_inital_pop = [0] * len(transactions_attacker_knowlege)

    # Build a dictionary for fast lookup
    transaction_dict = {int(t.attrib['id']): idx for idx, t in enumerate(transactions_attacker_knowlege)}

    # Loop through trips and update rust_inital_pop
    for trip_id, trip in enumerate(results):
        for trans_id in trip.used:
            if trans_id in transaction_dict:
                idx = transaction_dict[trans_id]
                rust_inital_pop[idx] = trip_id

    rust_transactions = []
    for trans in transactions_attacker_knowlege:
        t_obj = genetic.Transaction(
            id= int(trans.attrib['id']),
            detector= get_detector_id(str([trans.attrib['detector']])),
            time= int(trans.attrib['time']),
            cost= int(trans.attrib['cost']),
        )
        rust_transactions.append(t_obj)

    rust_sim_times = []
    tree_detectors = ET.parse(simulated_times_file)
    root_detectors = tree_detectors.getroot()
    existing_routes = set()

    for detector in root_detectors.iter('route'):
        u = get_detector_id(str([detector.attrib['fromDetector']]))
        v = get_detector_id(str([detector.attrib['toDetector']]))
        t_obj = genetic.SimulatedTime(
            from_detector= u,
            to_detector= v,
            avg= float(detector.attrib['avg']),
            min= float(detector.attrib['minTime']),
            max= float(detector.attrib['maxTime']),
        )
        rust_sim_times.append(t_obj)
        existing_routes.add((u, v))

    # Genetische Funktion:
    GENERATIONS_TRIPS = 10000 #6000
    GENERATIONS_WALLETS = 15000 #12000
    POPULATION_SIZE = 500

    # Angenommen, Sie haben 5 Trips und 3 Wallets. Individuum A = [0, 1, 0, 2, 1]
    # -> Bedeutung Trip 0 ist in Wallet 0, Trip 1 ist in Wallet 1, Trip 2 ist in Wallet 0 etc.
    (population_wallets, population_trips) = genetic.main(GENERATIONS_TRIPS, GENERATIONS_WALLETS, 0.1, 0.05, POPULATION_SIZE, sorted(walletCosts), rust_inital_pop, rust_transactions, rust_sim_times)

    print("Reconstructing results...")

    best_trip = max(population_trips, key=lambda ind: ind.score)
    best_wallet = max(population_wallets, key=lambda ind: ind.score)
    best_individual = best_wallet.score

    wallet_assignments = {i: [] for i in range(len(walletCosts))}

    # Wir gehen jede Transaktion durch (Reihenfolge wie in transactions_attacker_knowlege)
    for trans_idx, assigned_trip_id in enumerate(best_trip.genome):
        # Sicherheitscheck: Hat dieser Trip (ggf. neu durch Split) ein Wallet?
        if assigned_trip_id < len(best_wallet.genome):
            wallet_id = best_wallet.genome[assigned_trip_id]

            if wallet_id < len(walletCosts):
                # Die echte ID aus dem XML holen
                original_trip = transactions_attacker_knowlege[trans_idx].attrib['id']
                wallet_assignments[wallet_id].append(original_trip)

    #write trip results
    genome = best_trip.genome
    trips_map = collections.defaultdict(list)
    for i, assigned_trip_id in enumerate(genome):
        # Das XML-Objekt der entsprechenden Transaktion holen
        original_trans_xml = transactions_attacker_knowlege[i]
        original_id = original_trans_xml.attrib['id']

        trips_map[assigned_trip_id].append(original_id)

    trips_xml_element = ET.SubElement(output_root, "trips")

    for trip_id, trans_ids_list in trips_map.items():
        ids_string = " ".join(trans_ids_list)
        #<trip ids="..."> erstellen
        ET.SubElement(trips_xml_element, "trip", ids=ids_string)


    #write wallet results
    wallets_xml =  ET.SubElement(output_root, "wallets")
    for wallet_id in range(len(walletCosts)):
        assigned_trips = wallet_assignments[wallet_id]

        ids_string = " ".join(map(str, assigned_trips))
        ET.SubElement(wallets_xml, "wallet", ids=ids_string)

    tree = ET.ElementTree(output_root)
    tree.write('attacks/' + output_file_name)

    print('Finished')



if __name__ == '__main__':

    # Copy args.arguments to ‘regular’ arguments
    args = get_options()
    rsc_path = args.rsc_path
    input_file_name = args.input_file_name
    annealing = args.simulatedAnnealing
    simulated_times_file = args.simulated_times_input_file_name
    output_file_name = args.output_file_name
    rep_name = args.report_name
    

    # Global report variables
    rep_transactions = 0
    rep_vehicles = 0
    failed_assignments = 0
    remaining_transactions = 0
    time0 = time.time()
    rep_start = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    

    resultsWallets = []
    resultsTrips = []
    
    main()    
    report()

