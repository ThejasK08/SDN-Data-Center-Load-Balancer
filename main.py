import numpy as np
import random
import operator
import os
import copy
import itertools


AB = ' >> abc.xml'
class Centroid():
    def __init__(self, cl, acc):
        self.cl = cl
        self.acc = acc
        self.count = 1

    def append(self, data):
        for i, val in enumerate(self.acc):
            self.acc[i] += data[i]
            self.count += 1

    def getCentroid(self):
        return self.acc / self.count


# Reads and normalize the database, returns the data and classes apart
def readDatabase(filename, has_id, class_position):
    filepath = filename
    with open(filepath) as f:
        # Getting only the lines without missing attribute
        lines = (line for line in f if '?' not in line)
        dataset = np.loadtxt(lines, delimiter = ',')

    # Shuffing the dataset, once sometimes the data are grouped by class
    np.random.shuffle(dataset)

    # Considering the last column being the class column
    if class_position == 'first':
        classes = dataset[:, 0]
        dataset = np.delete(dataset, 0, axis = 1)
    else:
        classes = dataset[:, -1]
        dataset = np.delete(dataset, -1, axis = 1)

    if has_id:
        # Remove the first column (ID)
        dataset = np.delete(dataset, 0, axis = 1)

    # Normalizing the data in the [0 1] interval
    arr_max = np.max(dataset, axis = 0) # gets the max of each column
    arr_min = np.min(dataset, axis = 0) # gets the min of each column
    #print("\n arr max ",arr_max,'\n arr min ',arr_min)
    rows, cols = np.shape(dataset)
    for i in range(rows):
        for j in range(cols):
            #dataset[i][j] = (dataset[i][j] - arr_min[j]) / (arr_max[j] - arr_min[j])
            dataset[i][j] = (dataset[i][j])
    #list=[dataset]
    #print("\n list",list)

    return dataset, classes

# Determine the classes centroids as the mean values of the data
# in each class
def determineCentroids(dataset, classes):
    rows, cols = np.shape(dataset)

    sstats = {}

    for i, row in enumerate(dataset):
        class_id = str(classes[i])
        if class_id in sstats:
            sstats[class_id].append(row)
        else:
            sstats[class_id] = Centroid(classes[i], row)
    #print("stats",stats)
    ccentroids = {}
    for key in sstats:
        ccentroids[key] = sstats[key].getCentroid()
    #print("\n centroids",centroids)
    return sstats, ccentroids

# Simple Euclidian distance between two arrays
def euclidianDistance(a, b):
    diff_sqrt = [(x - y)**2 for x, y in zip(a, b)]

    return np.sqrt(np.sum(diff_sqrt))

def wavg(a, b):
    c=[0.2,0.1,0.1,0.2,0.2,0.2]
    diff_sqrt = [(x*y) for x,y in zip(c,b)]
    suml = len(b)
    #print("\n suml",np.sum(diff_sqrt),suml)
    return np.sum(diff_sqrt)/suml

# The sum of the distances between a data point and its class centroid
# in the trainning set
def costFunction(dataset, classes, cl, centroid):
    # 'cl' will be the string representation of the class already
    #print ("\nclasses",classes)
    #print cl
    #print centroid
    distances_sum = 0
    count = 0
    for i, d in enumerate(dataset):
        #print("d ")
        if str(classes[i]) == cl: # limiting the search only in the specific class
            #distances_sum += euclidianDistance(d, centroids[cl])
            distances_sum += wavg(d, centroid)
            count += 1
    print(cl,distances_sum / count)
    return distances_sum / count

def fitnessFunction(costs):
    fitness = copy.copy(costs)
    for key in fitness:
        fitness[key] = 1/(1 + costs[key])
        #fitness[key] = costs[key]*costs[key] - 10 * np.cos(2 * np.pi * costs[key])
        print(key,fitness[key])
    return fitness

def rouletteWheelFunction(P):
    p_sorted_asc = sorted(P.items(), key = operator.itemgetter(1))
    p_sorted_desc = dict(reversed(p_sorted_asc))

    pick = np.random.uniform(0, 1)
    current = 0
    for key in p_sorted_desc:
        current += p_sorted_desc[key]
        if current > pick:
            return key



# Artificial Bee Colony algorithm implementation
def ABC(dataset, classes, centroids, a_limit, max_iter):
    n_data, n_attr = np.shape(dataset) # Number of cases and number of attributes in each case
    n_bees = len(centroids) # Number of bees in the problem
    var_min = 0 # Minimum possible for each variable
    var_max = 100 # Maximum possible for each variable

    keys = [key for key in centroids] # centroid keys
    #print("\n keys ",keys)
    # Initialize the counter of rejections array
    C = copy.copy(centroids)
    for key in C:
        C[key] = 0

    # Initilize the cost array
    costs = copy.copy(centroids)
    print("----------------------Costs of intial population---------------------------")
    for cl in costs:
        #print("\n cl, load averages",cl, centroids[cl])
        costs[cl] = costFunction(dataset, classes, cl, centroids[cl])

    #print("cost[cl] ",costs)


    best_solution = 99999999
    best_solutions = np.zeros(max_iter)
    print("-----------------------------------EMPLOYED BEE----------------------------------")

    for it in range(max_iter):
        # Employed bees phase
        for cl in centroids:
            _keys = copy.copy(keys) # copying to maintain the original dict
            index = _keys.index(cl)
            del _keys[index]
            k = random.choice(_keys) # getting a index k different from i

            # Define phi coefficient to generate a new solution
            phi = np.random.uniform(-1, 1, n_attr)
            print("phi")
            print(phi)
            # Generating new solution
            # centroids: numpy array
            # phi: numpy array
            # (centroids[cl] - centroids[k]): numpy array
            # The operation will be element by element given that all the operands
            # are numpy arrays
            # TODO: ceil and floor of the new solution
            new_solution = centroids[cl] + phi * (centroids[cl] - centroids[k])
            print("xij")
            print(centroids[cl])
            print("xkj")
            print(centroids[k])
            print("vij calculation-------------------------------------")
            #print(centroids[cl],phi,cl,centroids[k],k)
            print(" new solution")
            print(new_solution)

            # Calculate the cost of the dataset with the new centroid
            new_solution_cost = costFunction(dataset, classes, cl, new_solution)
            #print "new_solution_cost"
            #print(new_solution_cost)

            # Greedy selection: comparing the new solution to the old one
            if new_solution_cost <= costs[cl]:
                centroids[cl] = new_solution
                costs[cl] = new_solution_cost
                C[cl] = 0
            else:
                # Increment the counter for discarted new solutions
                C[cl] += 1
        print("---------------costs after greedy selection------------------------")
        print(costs)
        print("---------------fitness values of new costs------------------------")
        F = fitnessFunction(costs) # calculate fitness of each class
        f_sum_arr = [F[key] for key in F]
        f_sum = np.sum(f_sum_arr)
        #print("\n fsumarr",f_sum_arr)
        P = {} # probabilities of each class
        print("---------------probability for each solutions------------------------")
        for key in F:
            P[key] = F[key]/f_sum
            print(key,P[key])

        print("-----------------------------------ONLOOKER BEE----------------------------------")
        # Onlooker bees phase
        for cl_o in centroids:
            selected_key = rouletteWheelFunction(P)
            print("selected key")
            print(selected_key)

            _keys = copy.copy(keys) # copying to maintain the original dict
            index = _keys.index(selected_key)
            del _keys[index]
            k = random.choice(_keys) # getting a index k different from i

            # Define phi coefficient to generate a new solution
            phi = np.random.uniform(-1, 1, n_attr)
            print("phi")
            print(phi)
            # Generating new solution
            # centroids: numpy array
            # phi: numpy array
            # (centroids[selected_key] - centroids[k]): numpy array
            # The operation will be element by element given that all the operands
            # are numpy arrays]

            new_solution = centroids[selected_key] + phi * (centroids[selected_key] - centroids[k])
            print("onlookerxij")
            print(centroids[cl])
            print("onlookerxkj")
            print(centroids[k])
            print(" new solution")
            print(new_solution)
            print("---------------costs of new solutions------------------------")
            # Calculate the cost of the dataset with the new centroid
            new_solution_cost = costFunction(dataset, classes, selected_key, new_solution)

            # Greedy selection: comparing the new solution to the old one
            if new_solution_cost <= costs[selected_key]:
                centroids[selected_key] = new_solution
                costs[selected_key] = new_solution_cost
                C[selected_key] = 0
            else:
                # Increment the counter for discarted new solutions
                C[selected_key] += 1

        print("----------------------------------SCOUT BEE----------------------------------")
        # Scout bees phase
        for cl_s in centroids:
            if C[cl_s] > 0:
                random_solution = np.random.uniform(0, 1, n_attr)
                random_solution_cost = costFunction(dataset, classes, cl_s, random_solution)
                print("--------------------------Random_solution----------------------------------")
                print(random_solution)

                centroids[cl_s] = new_solution
                costs[cl_s] = random_solution_cost
                C[cl_s] = 0

        # Update best solution for this iteration
        best_solution = 9999999999
        for cl in centroids:
            print("current_best_solution server costs[cl] ",best_solution,cl,costs[cl])
            if costs[cl] < best_solution:
                #print("\n best solution costs[cl] cl ",best_solution,costs[cl],cl)
                best_solution = costs[cl]
                xcl = cl

        #print("\n best solution costs[cl] cl ",best_solution,costs[cl],cl)
        best_solutions[it] = best_solution
        best_class = xcl

        #print('Iteration: {it}; Best cost: {best_solution}'.format(it = "%03d" % it, best_solution = best_solution))
    print("\n best solution",best_solutions,xcl)
    #print("\n xcl",xcl)
    return best_solutions, centroids, xcl


def getSets(dataset, classes):
    size = len(dataset)
    size = int(round(size*0.99))
    trainning_set = dataset[:size, :]
    trainning_set_classes = classes[:size]

    test_set = dataset[size:, :]
    test_set_classes = classes[size:]

    return trainning_set, test_set, trainning_set_classes, test_set_classes
def lbdm(dataset,classes,cl):
    capacity = 3600
    distances_sum = 0
    count = 0
    print(classes)
    for i, d in enumerate(dataset):
        #print("d ")
        if str(classes[i]) == cl:
            distances_sum += wavg(d, centroid)
            count += 1
    print( count)
    return distances_sum , count

def ss():
    databases = [{ 'filename': 'mas.csv', 'has_id': True, 'class_position': 'last' }]
    for database in databases:
        d, c = readDatabase(database['filename'], database['has_id'], database['class_position'])
        trainning_set, test_set, trainning_set_classes, test_set_classes = getSets(copy.copy(d), copy.copy(c))
        stats, centroids1 = determineCentroids(trainning_set, trainning_set_classes)

    print("-------------lbdm--------------")
    xz = lbdm(trainning_set, trainning_set_classes)
    limits = [5]
    for limit in limits:
        best_soltions, new_centroids1,xcl1 = ABC(trainning_set, trainning_set_classes, copy.copy(centroids1), a_limit = limit, max_iter = 2)
        print("server load factor",xcl,best_soltions[0])
    return xcl

databases = [{ 'filename': 'mas.csv', 'has_id': True, 'class_position': 'last' }]

for database in databases:
    d, c = readDatabase(database['filename'], database['has_id'], database['class_position'])
    trainning_set, test_set, trainning_set_classes, test_set_classes = getSets(copy.copy(d), copy.copy(c))
    stats, centroids = determineCentroids(trainning_set, trainning_set_classes)
limits = [50]
print("-------------lbdm--------------")
xz = lbdm(trainning_set, trainning_set_classes, copy.copy(centroids))
for limit in limits:
    best_soltions, new_centroids,xcl = ABC(trainning_set, trainning_set_classes, copy.copy(centroids), a_limit = limit, max_iter = 1)
    print('\n\n## DATABASE: {filename}, limit = {limit}'.format(filename = database['filename'], limit = limit))
    #print("best sol",new_centroids)
    print("server load factor",xcl,best_soltions[0])
