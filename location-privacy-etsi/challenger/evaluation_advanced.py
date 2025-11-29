import argparse
import os
import sys
import time
import networkx as nx
import numpy as np
from lxml import etree
import xml.etree.ElementTree as ET
import random
from copy import copy
from tqdm import tqdm
from datetime import datetime
import matplotlib.pyplot as plt

f1_scores_trip = []
f1_scores_wallet = []


#returns the avg. percentage of correct transactions in trips
def challengerTrips():
    challenger_trips = root_challenger_knowlege[2]
    per = set([]) #set with the success percentage of the trips
    tripList =  []
    #create a list with sets, the sets contain the ids from the trips
    for i in range(0, len(challenger_trips)):
            challenger_trip  =  challenger_trips[i]
            
            ids=set([])
            
            for j in range(0, len(challenger_trip)):
                ids.add(int(challenger_trip[j].attrib['id']))
            tripList.append(ids)

    #compare the attacker trips with the challenger trips
    for trip in tqdm(root_attacker[0], desc="Challenger Trips"):
        str_list = trip.attrib['ids'].split(' ')
        usedTrips = set(map(int, str_list))

        best_f1_for_this_trip = 0.0

        #find the best trip where the percentage is the highest 
        for true_trip in tripList:
            #Build intersection
            intersection = len(usedTrips & true_trip)

            # F1 formula: 2 * Intersection / Sum
            if intersection > 0:
                current_f1 = (2.0 * intersection) / (len(usedTrips) + len(true_trip))

                if current_f1 > best_f1_for_this_trip:
                    best_f1_for_this_trip = current_f1

        f1_scores_trip.append(best_f1_for_this_trip)

    #Average best f1 scores
    return round((sum(f1_scores_trip) / len(f1_scores_trip)) * 100,2)



#returns the avg. percentage of correct transactions in wallets
def challengerWallets():
    walletList =  [] #list with sets, the sets cotain the wallet ids

    #create a list with a sets with ids from wallets
    for i in root_challenger_knowlege.iter('wallet'):
            ids=set([])  
            for j in i.iter('wallet_transaction'):
                ids.add(int(j.attrib['id']))
            walletList.append(ids)

    #compare the attacker trips with the challenger trips
    for wallet in tqdm(root_attacker[1], desc="Challenger Wallets"):
        str_list = wallet.attrib['ids'].split(' ')
        usedWallets = set(map(int, str_list))

        best_f1_for_this_wallet = 0.0

        for true_wallet in walletList:
            intersection = len(usedWallets & true_wallet)

            if intersection > 0:
                #F1 formula
                current_f1 = (2.0 * intersection) / (len(usedWallets) + len(true_wallet))

                if current_f1 > best_f1_for_this_wallet:
                    best_f1_for_this_wallet = current_f1

        f1_scores_wallet.append(best_f1_for_this_wallet)

    # Average best f1 scores
    return round((sum(f1_scores_wallet) / len(f1_scores_wallet)) * 100, 2)
    
    


# Write report file
def report(detailed):
    time1 = time.time()
    rep_end = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    f = open('reports/' + rep_name, 'a')
    f.write('-------------------- Report of ADVANCED EVALUATION --------------------\n\n')
    f.write('Name of evaluation script:   ' + sys.argv[0] + '\n')
    f.write('Evaluation started at        ' + str(rep_start) +'\n')
    f.write('Evaluation ended at          ' + str(rep_end) +'\n')
    f.write('Runtime:                     ' + str(time1 - time0) + '\n\n')

    f.write('Measure of success:     Correctly assigned transactions to wallets or trips with Dice-Sørensen coefficient (F1-Score)' +"\n")
    f.write('Number of transactions: ' + str(rep_transactions) + '\n')
    f.write('Challenger knowledge file is   ' + "'" + knowledge_file_name + "'\n")
    f.write('- of file size                 ' + str(os.path.getsize(knowledge_file_name)) + ' bytes\n\n')

    f.write('Avg. percentage of right transactions in trips: ' + str(resultTrips) + '%.\n\n')
    f.write('Avg. percentage of right transactions in wallets: ' + str(resultWallets) + '%.\n\n')

    # F1-Scores
    min_f1_trip = min(f1_scores_trip)
    max_f1_trip = max(f1_scores_trip)
    avg_f1_trip = sum(f1_scores_trip) / len(f1_scores_trip)
    f.write(f'Minimum F1-Score for Trips: {min_f1_trip:.2f}%\n')
    f.write(f'Maximum F1-Score for Trips: {max_f1_trip:.2f}%\n')
    f.write(f'Average F1-Score for Trips: {avg_f1_trip:.2f}%\n\n')

    min_f1_wallet = min(f1_scores_trip)
    max_f1_wallet = max(f1_scores_trip)
    avg_f1_wallet = sum(f1_scores_trip) / len(f1_scores_trip)
    f.write(f'Minimum F1-Score for Wallets: {min_f1_wallet:.2f}%\n')
    f.write(f'Maximum F1-Score for Wallets: {max_f1_wallet:.2f}%\n')
    f.write(f'Average F1-Score for Wallets: {avg_f1_wallet:.2f}%\n')

    if detailed:
        f.write('\n-------------------- START of Detailed Report --------------------\n')
        detailed_report(f)
    
    f.write('-------------------- END of report --------------------\n\n')
    print('Report written to ' + "'" + 'reports/' + rep_name + "'")


def detailed_report(f):
    best_trip_score = max(f1_scores_trip)
    worst_trip_score = min(f1_scores_trip)
    best_wallet_score = max(f1_scores_wallet)
    worst_wallet_score = min(f1_scores_wallet)

    best_trip_idx = f1_scores_trip.index(best_trip_score)
    worst_trip_idx = f1_scores_trip.index(worst_trip_score)
    best_wallet_idx = f1_scores_wallet.index(best_wallet_score)
    worst_wallet_idx = f1_scores_wallet.index(worst_wallet_score)

    # Prepare detailed report
    f.write('\n-------------------- Best and Worst Matching Trips --------------------\n')

    # Best Trip
    best_trip_ids = root_attacker[0][best_trip_idx].attrib["ids"].split()

    f.write(f'Best Matching Trip (ID {best_trip_idx})\n')
    f.write(f'F1 Score: {round(best_trip_score * 100, 2)}%\n')
    f.write(f'Length of Trip: {len(best_trip_ids)} transactions\n')  # Hier die Länge der Liste nehmen
    f.write(f'IDs: {", ".join(best_trip_ids)}\n')

    # Worst Trip
    worst_trip_ids = root_attacker[0][worst_trip_idx].attrib["ids"].split()

    f.write(f'\nWorst Matching Trip (ID {worst_trip_idx})\n')
    f.write(f'F1 Score: {round(worst_trip_score * 100, 2)}%\n')
    f.write(f'Length of Trip: {len(worst_trip_ids)} transactions\n')
    f.write(f'IDs: {", ".join(worst_trip_ids)}\n')

    f.write('\n-------------------- Best and Worst Matching Wallets --------------------\n')

    # Best Wallet
    best_wallet_ids = root_attacker[1][best_wallet_idx].attrib["ids"].split()

    f.write(f'Best Matching Wallet (ID {best_wallet_idx})\n')
    f.write(f'F1 Score: {round(best_wallet_score * 100, 2)}%\n')
    f.write(f'Length of Wallet: {len(best_wallet_ids)} transactions\n')
    f.write(f'IDs: {", ".join(best_wallet_ids)}\n')

    # Worst Wallet
    worst_wallet_ids = root_attacker[1][worst_wallet_idx].attrib["ids"].split()

    f.write(f'\nWorst Matching Wallet (ID {worst_wallet_idx})\n')
    f.write(f'F1 Score: {round(worst_wallet_score * 100, 2)}%\n')
    f.write(f'Length of Wallet: {len(worst_wallet_ids)} transactions\n')
    f.write(f'IDs: {", ".join(worst_wallet_ids)}\n')

    f.write('-------------------- END of Detailed Report --------------------\n')

def plot():
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot F1-scores for trips
    ax1.hist(f1_scores_trip, bins=50, alpha=0.7, label='F1-Score for Trips', color='skyblue', edgecolor='black',
             linewidth=1.2)
    ax1.set_xlabel("F1-Score", fontsize=12)
    ax1.set_ylabel("Frequency (Trips)", fontsize=12)
    ax1.set_title("Distribution of F1-Scores for Trips and Wallets", fontsize=14, weight='bold')

    # Set x-axis range (0 to 1)
    ax1.set_xlim([0, 1])

    # Fine-tune x-axis ticks
    ax1.set_xticks(np.arange(0, 1.1, 0.1))

    # Create a second y-axis for wallets
    ax2 = ax1.twinx()
    ax2.hist(f1_scores_wallet, bins=50, alpha=0.7, label='F1-Score for Wallets', color='salmon', edgecolor='black',
             linewidth=1.2)
    ax2.set_ylabel("Frequency (Wallets)", fontsize=12)

    # Legends for both axes
    ax1.legend(loc='upper right', fontsize=12, title='F1-Scores (Trips)', title_fontsize='13')
    ax2.legend(loc='upper left', fontsize=12, title='F1-Scores (Wallets)', title_fontsize='13')

    # Add gridlines for better readability
    ax1.grid(True, linestyle='--', alpha=0.7)

    # Optimize layout for better display
    plt.tight_layout()
    plt.show()

# Gets command line arguments using the argparse module
def get_options():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument('-p', '--path', dest='rsc_path', type=str, help='Relative path to resource files', default='../rsc/')
    parser.add_argument('-c', '--challenger', dest='knowledge_file_name', type=str, help='Which attacker knowledge file to use?', required=True)
    parser.add_argument('-a', '--attacker', dest='eval_file_name', type=str, help='Set attacker output file', required=True)
    parser.add_argument('-r', '--report', dest='report_name', type=str, help='Set report name', default='report.txt')
    parser.add_argument('-d', '--detailed', action='store_true', help='Add detailed information about best/worst trips/wallets', default=False)
    return parser.parse_args()

def main():
    global root_challenger_knowlege, root_attacker, resultTrips, resultWallets, rep_transactions
   
    tree_challenger_knowlege = ET.parse(str(knowledge_file_name))
    root_challenger_knowlege = tree_challenger_knowlege.getroot()
   

    tree_attacker = ET.parse(str(eval_file_name))
    root_attacker = tree_attacker.getroot()
    resultTrips = challengerTrips()
    resultWallets =challengerWallets()

    for i in tree_challenger_knowlege.iter('allTransactions'):
       rep_transactions = i.attrib["total_transactions"]



# Run main method on start
if __name__ == "__main__":
    # Copy args.arguments to ‘regular’ arguments
    args = get_options()
    rsc_path = args.rsc_path
    knowledge_file_name = args.knowledge_file_name
    eval_file_name = args.eval_file_name
    rep_name = args.report_name
    
    # Global report variables
    rep_transactions = 0
    rep_vehicles = 0
    rep_success = 0
    output_tag = None
    time0 = time.time()
    rep_start = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    main()
    if args.detailed:
        report(True)
    else:
        report(False)
    plot()
