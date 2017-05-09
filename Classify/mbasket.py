#!/usr/bin/env python

"""
Market basket python program
v1.3
3/19/17
"""

import sys, csv, os
from Models.models import FileQueue, db
from config import app

totalsupcount = 0

def get_named_set_from_numbered_csv_row(csv_row, field_names):
    """When provided the csv_row and the csv field_names, this will
    build a set of the fields populated with a value > 0.
    """
    result = []
    for field in field_names:
        value = str(csv_row[field]).strip()
        try:
            if float(value) > 0:
                result.append(field)
        except ValueError:
            continue
    return set(result)

def read_data(file_name, upformat=2):
    """Read a csv file that lists possible transactions"""
    result = list()
    if upformat == 1:
        with open(file_name, 'r') as file_reader:
            lineNum = 0
            for line in file_reader:
                lineNum += 1
                #print('Reading Line: ' + str(lineNum))
                order_set = set(line.strip().split(','))
                result.append(order_set)
    elif upformat == 2:
        with open(file_name, 'r') as file_reader:
            the_csv = csv.DictReader(file_reader)
            field_names = the_csv.fieldnames
            for line in the_csv:
                clean_row = get_named_set_from_numbered_csv_row(line,field_names)
                if len(clean_row) > 0:
                    result.append(list(clean_row))
                else:
                    continue
        #print("Number of rows in result: "+str(len(result)))
    return result


def support_count(orders, item_set):
    """Calculate support count of item set from orders 2D list"""
    count = 0

    global totalsupcount
    totalsupcount += 1

    for order in orders:
        if item_set.issubset(order):
            # print("Found {} in {}".format(item_set, order))
            count += 1
        else:
            # print("Didn't find {} in {}".format(item_set, order)) + ': ' + str(count)
            pass
        #print('Processing Support Count ' + str(totalsupcount) + ': ' + str(count))
        writeme = ('\rProcessing Support Count ' + str(totalsupcount) + ': ' + str(count))
        #sys.stdout.write('\rProcessing Support Count ' + str(totalsupcount) + ': ' + str(count))
        #sys.stdout.flush()
    #print('\n')
    return count


def support_frequency(orders, item_set):
    """Calculate support frequency of item set from orders 2D list"""
    #print('\nProcessing Support Frequency')
    N = len(orders)
    return support_count(orders, item_set)/float(N)

def confidence(orders, left, right):
    """Calculate confidence of item set from orders 2D list"""
    #print('\nProcessing Confidence')
    left_count = support_count(orders, left)
    right = right.union(left)
    right_count = support_count(orders, right)
    result = right_count/left_count
    return result
    #print('\n')
# Calculate Conviction (1- support_frequency)/(1-confidence )

def apriori(orders, support_threshold, confidence_threshold, antqnt):
    """Accepts a list of item sets (i.e. orders) and returns a list of
    association rules matching support and confidence thresholds. """
    candidate_items = set()

    for items in orders:
        candidate_items = candidate_items.union(items)

    #print("Candidate items are {}".format(candidate_items))

    def apriori_next(item_set=set()):
        """Accepts a single item set and returns list of all association rules
        containing item_set that match support and confidence thresholds.
        """
        result = []

        # print("Calling APN with {}".format(item_set))
        # print("Candidates are {}".format(candidate_items))

        #print(len(item_set))
        #print("CAND: " + str(candidate_items))

        if len(item_set) == len(candidate_items):
            # Recursion base case.
            # print("{} == {}".format(item_set, candidate_items))
            return result

        elif not item_set:
            # Initialize with every item meeting support threshold.
            # print("Initializing APN.\n")
            for item in candidate_items:
                item_set = {item}
                if support_frequency(orders, item_set) >= support_threshold:
                    # print("Item '{}' crosses support threshold".format(item))
                    result.extend(apriori_next(item_set))
                else:
                    pass

        else:
            # Given an item set, find all candidate items meeting thresholds
            for item in candidate_items.difference(item_set):
                # print("Testing {}".format(item_set.union({item})))
                if confidence(orders, item_set, {item}) >=\
                        confidence_threshold:
                    # print("\n\n{} => {} crosses confidence threshold at {}".format(item_set, item, confidence(orders, item_set, {item})))
                    if support_frequency(orders, item_set.union({item})) >=\
                            support_threshold:
                       #print("\nItem set {} crosses support threshold at {}".format(item_set.union({item}), support_frequency(orders, item_set.union({item}))))
                        result.append((item_set, item))
                        if antqnt == 'many':
                            result.extend(apriori_next(item_set.union({item})))
                    else:
                        pass
                else:
                    pass

        return [rule for rule in result if rule]

    return apriori_next()


def calc(support_threshold, confidence_threshold, uploadname, savename, key, antqnt, file_types='both', upformat=2):
    with app.app_context():

        fileq = FileQueue.query.filter_by(key=key).filter(FileQueue.status=='processing').first()

        data = read_data('Classify/temp/uploads/'+uploadname, upformat)

        #CSV
        if 'csv' in file_types or 'both' in file_types:
            final_results = []
            for item_set, item in apriori(data[1:], support_threshold, confidence_threshold, antqnt):
                str_item_set = str(item_set).replace('{', '')
                str_item_set = str_item_set.replace('}', '')
                str_item_set = str_item_set.replace("'", '')
                results = {
                    'Antecedent': str_item_set,
                    'Consequent': item,
                    'Support': "{:0.3f}".format(support_frequency(data[1:], item_set.union({item}))),
                    'Confidence': "{:0.3f}".format(confidence(data[1:], item_set, {item})),
                    'Conviction': "{:0.3f}".format((1 - support_frequency(data[1:], {item})) / (1 - min(confidence(data[1:], item_set, {item}),0.99))),
                    'Lift': "{:0.3f}".format(support_frequency(data[1:], item_set.union({item}))/(support_frequency(data[1:], {item})*support_frequency(data[1:], item_set)))
                }
                final_results.append(results)

            written = []
            columns = ['Antecedent','Consequent','Support','Confidence','Conviction','Lift']

            with open('Classify/temp/'+key+'/'+savename, 'w', newline="") as destfile:
                f = csv.DictWriter(destfile, fieldnames=columns)
                f.writeheader()
                for result in final_results:
                    if result not in written:
                        written.append(result)
                        f.writerow(result)
        #JSON
        final_results_json = {}
        final_results_json_cons = {}

        if 'json' in file_types or 'both' in file_types:
            with open('Classify/temp/'+key+'/'+savename, 'r') as f:
                tempres = csv.DictReader(f)
                for row in tempres:
                    if len(row["Antecedent"].split(',')) == 1:
                        try:
                            final_results_json_cons[row["Consequent"]].append(row["Antecedent"])
                        except KeyError:
                            final_results_json_cons[row["Consequent"]] = [row["Antecedent"]]

                        try:
                            final_results_json[row["Consequent"]][row["Antecedent"]] = row["Confidence"]
                        except KeyError:
                            final_results_json[row["Consequent"]] = {row["Antecedent"]: row["Confidence"]}


            with open('Classify/temp/'+key+'/'+savename.split('.csv')[0]+'.json', 'w') as f:
                f.write('var strength = ' + str(final_results_json) + ';\nvar persons = ' + str(final_results_json_cons) + ';')

        fileq = FileQueue.query.filter_by(key=key).filter(FileQueue.status=='processing').first()

        if fileq.status != 'cancelled':
            fileq.status = 'complete'
            with open('Classify/temp/uploads/'+uploadname, 'r') as r:
                rowcount = len(r.read().split('\n'))
                fileq.complete = rowcount
                fileq.total = rowcount
            db.session.commit()
        os.remove(os.path.join('Classify/temp/uploads', uploadname))
