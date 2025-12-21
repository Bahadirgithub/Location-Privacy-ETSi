import argparse
import os
import sys
import time
import numpy as np
import xml.etree.ElementTree as ET
from tqdm import tqdm
from datetime import datetime
import matplotlib.pyplot as plt

# Global lists to store scores
f1_scores_trip = []
f1_scores_wallet = []


def challengerTrips():
    """
    Calculates the F1 score for Trips.
    Returns the average percentage of correct transactions in trips.
    """
    challenger_trips = root_challenger_knowledge[2]

    # Create a list of sets, where each set contains the transaction IDs of a true trip
    tripList = [
        set(int(t.attrib['id']) for t in trip)
        for trip in challenger_trips
    ]

    # Compare the attacker trips with the challenger trips
    for trip in tqdm(root_attacker[0], desc="Challenger Trips"):
        str_list = trip.attrib['ids'].split()
        usedTrips = set(map(int, str_list))

        best_f1_for_this_trip = 0.0

        # Find the best matching trip in ground truth
        for true_trip in tripList:
            intersection = len(usedTrips & true_trip)

            # F1 formula: 2 * Intersection / Sum
            if intersection > 0:
                current_f1 = (2.0 * intersection) / (len(usedTrips) + len(true_trip))

                if current_f1 > best_f1_for_this_trip:
                    best_f1_for_this_trip = current_f1

        f1_scores_trip.append(best_f1_for_this_trip)

    # Return average best f1 scores
    if not f1_scores_trip: return 0.0
    return round((sum(f1_scores_trip) / len(f1_scores_trip)) * 100, 2)


def challengerWallets():
    """
    Calculates the F1 score for Wallets.
    Returns the average percentage of correct transactions in wallets.
    """
    # Create a list of sets, where each set contains transaction IDs from true wallets
    walletList = [
        set(int(t.attrib['id']) for t in wallet.iter('wallet_transaction'))
        for wallet in root_challenger_knowledge.iter('wallet')
    ]

    # Compare the attacker wallets with the challenger wallets
    for wallet in tqdm(root_attacker[1], desc="Challenger Wallets"):
        str_list = wallet.attrib['ids'].split()
        usedWallets = set(map(int, str_list))

        best_f1_for_this_wallet = 0.0

        for true_wallet in walletList:
            intersection = len(usedWallets & true_wallet)

            if intersection > 0:
                # F1 formula
                current_f1 = (2.0 * intersection) / (len(usedWallets) + len(true_wallet))

                if current_f1 > best_f1_for_this_wallet:
                    best_f1_for_this_wallet = current_f1

        f1_scores_wallet.append(best_f1_for_this_wallet)

    # Return average best f1 scores
    if not f1_scores_wallet: return 0.0
    return round((sum(f1_scores_wallet) / len(f1_scores_wallet)) * 100, 2)


def report(detailed):
    time1 = time.time()
    rep_end = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Use context manager for safe file handling
    with open('reports/' + rep_name, 'a') as f:
        f.write('-------------------- Report of ADVANCED EVALUATION --------------------\n\n')
        f.write(f'Name of evaluation script:   {sys.argv[0]}\n')
        f.write(f'Evaluation started at        {rep_start}\n')
        f.write(f'Evaluation ended at          {rep_end}\n')
        f.write(f'Runtime:                     {time1 - time0}\n\n')

        f.write(
            'Measure of success:     Correctly assigned transactions to wallets or trips with Dice-Sørensen coefficient (F1-Score)\n')
        f.write(f'Number of transactions: {rep_transactions}\n')
        f.write(f'Challenger knowledge file is   \'{knowledge_file_name}\'\n')
        f.write(f'- of file size                 {os.path.getsize(knowledge_file_name)} bytes\n\n')

        f.write(f'Avg. percentage of right transactions in trips: {resultTrips}%.\n\n')
        f.write(f'Avg. percentage of right transactions in wallets: {resultWallets}%.\n\n')

        # Trip F1-Scores
        if f1_scores_trip:
            min_f1_trip = round(min(f1_scores_trip) * 100, 2)
            max_f1_trip = round(max(f1_scores_trip) * 100, 2)
            avg_f1_trip = round((sum(f1_scores_trip) / len(f1_scores_trip)) * 100, 2)
        else:
            min_f1_trip = max_f1_trip = avg_f1_trip = 0.0

        f.write(f'Minimum F1-Score for Trips: {min_f1_trip:.2f}%\n')
        f.write(f'Maximum F1-Score for Trips: {max_f1_trip:.2f}%\n')
        f.write(f'Average F1-Score for Trips: {avg_f1_trip:.2f}%\n\n')

        # Wallet F1-Scores (Fixed Bug: Was using f1_scores_trip)
        if f1_scores_wallet:
            min_f1_wallet = round(min(f1_scores_wallet) * 100, 2)
            max_f1_wallet = round(max(f1_scores_wallet) * 100, 2)
            avg_f1_wallet = round((sum(f1_scores_wallet) / len(f1_scores_wallet)) * 100, 2)
        else:
            min_f1_wallet = max_f1_wallet = avg_f1_wallet = 0.0

        f.write(f'Minimum F1-Score for Wallets: {min_f1_wallet:.2f}%\n')
        f.write(f'Maximum F1-Score for Wallets: {max_f1_wallet:.2f}%\n')
        f.write(f'Average F1-Score for Wallets: {avg_f1_wallet:.2f}%\n')

        if detailed:
            f.write('\n-------------------- START of Detailed Report --------------------\n')
            detailed_report(f)

        f.write('-------------------- END of report --------------------\n\n')

    print(f"Report written to 'reports/{rep_name}'")


def detailed_report(f):
    best_trip_score = max(f1_scores_trip)
    worst_trip_score = min(f1_scores_trip)
    best_wallet_score = max(f1_scores_wallet)
    worst_wallet_score = min(f1_scores_wallet)

    best_trip_idx = f1_scores_trip.index(best_trip_score)
    worst_trip_idx = f1_scores_trip.index(worst_trip_score)
    best_wallet_idx = f1_scores_wallet.index(best_wallet_score)
    worst_wallet_idx = f1_scores_wallet.index(worst_wallet_score)

    # --- Ground Truth Listen vorbereiten ---
    challenger_trips_xml = root_challenger_knowledge[2]
    truth_trip_list = []
    for t in challenger_trips_xml:
        truth_trip_list.append(set(int(x.attrib['id']) for x in t))

    truth_wallet_list = []
    for w in root_challenger_knowledge.iter('wallet'):
        ids = set(int(x.attrib['id']) for x in w.iter('wallet_transaction'))
        truth_wallet_list.append(ids)

    f.write('\n-------------------- Best and Worst Matching Trips --------------------\n')

    # --- Best Trip ---
    raw_ids = root_attacker[0][best_trip_idx].attrib["ids"].split()
    best_trip_ids = set(map(int, raw_ids))  # Wichtig: Set für Analyse

    f.write(f'Best Matching Trip (ID {best_trip_idx})\n')
    f.write(f'F1 Score: {round(best_trip_score * 100, 2)}%\n')
    f.write(f'Length of Trip: {len(best_trip_ids)} transactions\n')
    f.write(f'IDs: {", ".join(raw_ids)}\n')

    analyze_match(f, "Trip", best_trip_ids, truth_trip_list)

    # --- Worst Trip ---
    raw_ids = root_attacker[0][worst_trip_idx].attrib["ids"].split()
    worst_trip_ids = set(map(int, raw_ids))

    f.write(f'\nWorst Matching Trip (ID {worst_trip_idx})\n')
    f.write(f'F1 Score: {round(worst_trip_score * 100, 2)}%\n')
    f.write(f'Length of Trip: {len(worst_trip_ids)} transactions\n')
    f.write(f'IDs: {", ".join(raw_ids)}\n')

    analyze_match(f, "Trip", worst_trip_ids, truth_trip_list)

    f.write('\n-------------------- Best and Worst Matching Wallets --------------------\n')

    # --- Best Wallet ---
    raw_ids = root_attacker[1][best_wallet_idx].attrib["ids"].split()
    best_wallet_ids = set(map(int, raw_ids))

    f.write(f'Best Matching Wallet (ID {best_wallet_idx})\n')
    f.write(f'F1 Score: {round(best_wallet_score * 100, 2)}%\n')
    f.write(f'Length of Wallet: {len(best_wallet_ids)} transactions\n')
    f.write(f'IDs: {", ".join(raw_ids)}\n')

    analyze_match(f, "Wallet", best_wallet_ids, truth_wallet_list)

    # --- Worst Wallet ---
    raw_ids = root_attacker[1][worst_wallet_idx].attrib["ids"].split()
    worst_wallet_ids = set(map(int, raw_ids))

    f.write(f'\nWorst Matching Wallet (ID {worst_wallet_idx})\n')
    f.write(f'F1 Score: {round(worst_wallet_score * 100, 2)}%\n')
    f.write(f'Length of Wallet: {len(worst_wallet_ids)} transactions\n')
    f.write(f'IDs: {", ".join(raw_ids)}\n')

    analyze_match(f, "Wallet", worst_wallet_ids, truth_wallet_list)

    f.write('-------------------- END of Detailed Report --------------------\n')

def analyze_match(f, type_name, attacker_ids, ground_truth_list):
    """
    Analysiert den Unterschied zwischen Vorhersage und Wahrheit detailliert
    und gibt Beispiele für TP, FP und FN aus.
    """
    best_truth_ids = set()
    best_f1 = -1

    # 1. Den passenden echten Trip/Wallet wiederfinden (Re-Matching)
    for true_ids in ground_truth_list:
        intersection = len(attacker_ids & true_ids)
        if intersection > 0:
            current_f1 = (2.0 * intersection) / (len(attacker_ids) + len(true_ids))
            if current_f1 > best_f1:
                best_f1 = current_f1
                best_truth_ids = true_ids

    # Wenn gar kein Match gefunden wurde (F1 = 0)
    if not best_truth_ids:
        f.write(f"\n   -> NO MATCH FOUND! This {type_name} consists purely of noise or incorrect transactions.\n")
        return

    # 2. Berechnung der Mengen
    tp = attacker_ids & best_truth_ids  # Richtig (True Positive)
    fp = attacker_ids - best_truth_ids  # Zu viel (False Positive)
    fn = best_truth_ids - attacker_ids  # Fehlt (False Negative)

    precision = len(tp) / len(attacker_ids) if len(attacker_ids) > 0 else 0
    recall = len(tp) / len(best_truth_ids) if len(best_truth_ids) > 0 else 0

    # 3. Ausgabe im Report
    f.write(f"\n   --- Deep Dive Analysis ---\n")
    f.write(f"   Real {type_name} Size:      {len(best_truth_ids)} transactions\n")
    f.write(f"   Predicted {type_name} Size: {len(attacker_ids)} transactions\n")
    f.write(f"   Precision: {precision * 100:.2f}% (How reliable is your prediction?)\n")
    f.write(f"   Recall:    {recall * 100:.2f}% (How much did you find?)\n")

    f.write(f"   --------------------------\n")
    f.write(f"   Correct IDs (TP): {len(tp)}\n")
    f.write(f"   Extra IDs (FP):   {len(fp)}  <- Over-Merging / Noise\n")
    f.write(f"   Missed IDs (FN):  {len(fn)}  <- Over-Splitting / Missing\n")

    # Hilfsfunktion für saubere Ausgabe von Listen
    def format_ids(id_set, limit=15):
        l = list(id_set)
        if len(l) == 0: return "None"
        content = ", ".join(map(str, l[:limit]))
        if len(l) > limit:
            content += f", ... ({len(l) - limit} more)"
        return content

    f.write(f"   \n   [EXAMPLES]\n")
    f.write(f"   True Positives (Matches): {format_ids(tp)}\n")

    if len(fp) > 0:
        f.write(f"   False Positives (Wrong):  {format_ids(fp)}\n")

    if len(fn) > 0:
        f.write(f"   False Negatives (Missed): {format_ids(fn)}\n")


# Helper to stringify and truncate sets
def summarize_set(s):
    l = list(s)
    out = ", ".join(map(str, l[:5]))
    if len(l) > 5:
        out += f" ... (+{len(l) - 5})"
    return out


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
    ax1.set_xticks(np.arange(0, 1.1, 0.1))

    # Create a second y-axis for wallets
    ax2 = ax1.twinx()
    ax2.hist(f1_scores_wallet, bins=50, alpha=0.7, label='F1-Score for Wallets', color='salmon', edgecolor='black',
             linewidth=1.2)
    ax2.set_ylabel("Frequency (Wallets)", fontsize=12)

    ax1.legend(loc='upper right', fontsize=12, title='F1-Scores (Trips)', title_fontsize='13')
    ax2.legend(loc='upper left', fontsize=12, title='F1-Scores (Wallets)', title_fontsize='13')

    ax1.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def get_options():
    parser = argparse.ArgumentParser(description='Parameters')
    parser.add_argument('-p', '--path', dest='rsc_path', type=str, help='Relative path to resource files',
                        default='../rsc/')
    parser.add_argument('-c', '--challenger', dest='knowledge_file_name', type=str,
                        help='Which attacker knowledge file to use?', required=True)
    parser.add_argument('-a', '--attacker', dest='eval_file_name', type=str, help='Set attacker output file',
                        required=True)
    parser.add_argument('-r', '--report', dest='report_name', type=str, help='Set report name', default='report.txt')
    parser.add_argument('-d', '--detailed', action='store_true',
                        help='Add detailed information about best/worst trips/wallets', default=False)
    return parser.parse_args()


def main():
    global root_challenger_knowledge, root_attacker, resultTrips, resultWallets, rep_transactions

    tree_challenger_knowledge = ET.parse(str(knowledge_file_name))
    root_challenger_knowledge = tree_challenger_knowledge.getroot()

    tree_attacker = ET.parse(str(eval_file_name))
    root_attacker = tree_attacker.getroot()

    resultTrips = challengerTrips()
    resultWallets = challengerWallets()

    # Get total transactions count
    rep_transactions = 0
    for i in tree_challenger_knowledge.iter('allTransactions'):
        rep_transactions = i.attrib.get("total_transactions", 0)


if __name__ == "__main__":
    args = get_options()
    rsc_path = args.rsc_path
    knowledge_file_name = args.knowledge_file_name
    eval_file_name = args.eval_file_name
    rep_name = args.report_name

    time0 = time.time()
    rep_start = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    main()

    report(args.detailed)
    plot()