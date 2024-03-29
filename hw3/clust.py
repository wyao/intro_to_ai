# clust.py
# -------
# Irene Chen and Willie Yao

import sys
import random
from utils import *
import utils
import operator
from optparse import OptionParser
import math
import time
import py.test

DATAFILE = "adults.txt"

#validateInput()

def validateInput():
    if len(sys.argv) != 3:
        return False
    if sys.argv[1] <= 0:
        return False
    if sys.argv[2] <= 0:
        return False
    return True


#-----------


def parseInput(datafile):
    """
    params datafile: a file object, as obtained from function `open`
    returns: a list of lists

    example (typical use):
    fin = open('myfile.txt')
    data = parseInput(fin)
    fin.close()
    """
    data = []
    for line in datafile:
        instance = line.split(",")
        instance = instance[:-1]
        data.append(map(lambda x:float(x),instance))
    return data


def printOutput(data, numExamples):
    for instance in data[:numExamples]:
        print ','.join([str(x) for x in instance])

# main
# ----
# The main program loop
# You should modify this function to run your experiments

def main():
    parser = OptionParser()
    parser.add_option('-k', action='store_true',
        dest='k_means', default=False)
    parser.add_option('--min', action='store_true', default=False)
    parser.add_option('--max', action='store_true', default=False)
    parser.add_option('--mean', action='store_true', default=False)
    parser.add_option('--cent', action='store_true', default=False)
    parser.add_option('--bern', action='store_true', default=False)
    parser.add_option('--mix', action='store_true', default=False)
    parser.add_option('--small', action='store_true', default=False)

    (opt, args) = parser.parse_args()

    numClusters = int(args[0]) #K
    numExamples = int(args[1]) #n

    #Initialize the random seed
    random.seed()

    #Initialize the data
    dataset = None
    attributes = utils.attributes
    if opt.small:
        attributes = utils.attributes_small
        dataset = file('adults-small.txt', 'r')
    elif opt.k_means or opt.bern or opt.mix:
        dataset = file(DATAFILE, "r")
    elif opt.max or opt.min or opt.mean or opt.cent:
        dataset = file('adults-small.txt', 'r')
    if dataset == None:
        print "Unable to open data file"
        exit(1)

    data = parseInput(dataset)
    
    dataset.close()
    assert(numExamples <= len(data))
    assert(numClusters <= numExamples)

    # ==================== #
    # WRITE YOUR CODE HERE #
    # ==================== #

    dimensions = len(data[0])

    # K-means
    if opt.k_means:
        chosen = set()
        prototypes = []
        assignments = [] # Aka responsibility vectors

        # Initialize prototype vectors
        for _ in xrange(numClusters):
            r = None
            while True:
                r = random.randint(0, numExamples-1)
                if r not in chosen:
                    chosen.add(r)
                    break
            prototypes.append(list(data[r]))

        # Repeatedly update responsibility and prototype vectors
        converged = False
        iteration = 0
        total_time = 0.
        while not converged:
            start = time.time()
            # Update responsibility vectors
            newAssignments = []
            for n in xrange(numExamples):
                bestProto = None
                minDistance = float('inf')
                for k in xrange(numClusters):
                    d = squareDistance(data[n], prototypes[k])
                    if d < minDistance:
                        bestProto = k
                        minDistance = d
                newAssignments.append(bestProto)
            converged = (newAssignments == assignments)
            assignments = newAssignments

            # Update prototype vectors
            for k in xrange(numClusters):
                prototypes[k] = [0.]*dimensions
            counts = [0]*numClusters
            for n in xrange(numExamples):
                k = assignments[n]
                counts[k] += 1
                prototypes[k] = map(operator.add, prototypes[k], data[n])
            for k in xrange(numClusters):
                prototypes[k] = map(lambda x: x/counts[k], prototypes[k])

            total_time += (time.time()-start)
            iteration += 1

        # Print mean
        print "Means:"
        print prototypes
        print ""

        # Calculate mean squared error
        sqrErr = 0.
        for n in xrange(numExamples):
            sqrErr += squareDistance(data[n], prototypes[assignments[n]])
        print "Mean Squared Error:", sqrErr/numExamples
        print ""
        print "Iterations:", iteration
        print ""
        print "Time per iteration (averaged in seconds): ", (total_time/float(iteration))

    # HAC
    elif opt.max or opt.min or opt.mean or opt.cent:
        clusters = [[list(p)] for p in data[:numExamples]]

        while len(clusters) > numClusters:
            shortest, a, b = float('inf'), None, None
            for i in xrange(len(clusters)-1):
                for j in xrange(i+1, len(clusters)):
                    # Find distance
                    dist = None
                    if opt.min:
                        dist = cmin(clusters[i], clusters[j], squareDistance)
                    elif opt.max:
                        dist = cmax(clusters[i], clusters[j], squareDistance)
                    elif opt.mean:
                        dist = cmean(clusters[i], clusters[j], squareDistance)
                    else:
                        dist = ccent(clusters[i], clusters[j], squareDistance)
                    # Update shortest distance
                    if dist < shortest:
                        shortest = dist
                        a = i
                        b = j
            # Merge clusters
            clusters[a] = clusters[a] + clusters[b]
            clusters.pop(b)
        # Print mean
        clusterMeans = []
        for cluster in clusters:
            means = [0.] * len(cluster[0])
            for x in cluster:
                for i,xi in enumerate(x):
                    means[i] += xi
            clusterMeans.append([xi/len(cluster) for xi in means])
        print "Means:"
        print clusterMeans
        print "\nInstances per cluster:"
        print [len(c) for c in clusters]

        # Plot 3D
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for c,color in zip(clusters, ['r','b','g','black']):
            for i in xrange(len(c)):
                ax.scatter(c[i][0],c[i][1], \
                    c[i][2],c=color)
        plt.show()

    # Autoclass with simple Bernoulli model for all features
    elif opt.bern:
        # Set up discretization info
        assert(dimensions == len(attributes))

        E = {} # Expected values
        P = {} # Parameters
        discrete = float(len([a for a in attributes if not a['isContinuous']]))

        # Set initial parameters
        for k in xrange(numClusters):
            P[k] = random.random()
            for d in xrange(dimensions):
                P[(k,d)] = random.random()
        # Run EM
        converged_count = 0
        likelihood = float('inf')
        iterations = 0
        while converged_count < 2:
            # Calculate expected values step
            # Set all expected values to 0
            for k in xrange(numClusters):
                E[k] = 0.
                for d in xrange(dimensions):
                    E[(k,d)] = 0.
            # For each input
            for n,x in enumerate(data[:numExamples]):
                # Per input temporary probabilities for each cluster
                prob = []
                for _ in xrange(numClusters):
                    prob.append(float(P[k]))
                # For each attribute calculate probabilities
                for d,xi in enumerate(x):
                    # w_denominator = 0.
                    for k in xrange(numClusters):
                        if attributes[d]['isContinuous']:
                            if xi > .5:
                                prob[k] *= P[(k,d)]
                            else:
                                prob[k] *= (1-P[(k,d)])
                        else:
                            if xi > 0:
                                prob[k] *= P[(k,d)]
                            else:
                                prob[k] *= (1-P[(k,d)])
                # Sum up expected values
                totalProb = sum(prob) # 0 if every discrete xi is 0.0 TODO
                for k in xrange(numClusters):
                    if totalProb: # If totalProb != 0.0
                        E[k] += prob[k]/totalProb
                        for d in xrange(dimensions):
                            if not attributes[d]['isContinuous'] \
                                and x[d] > 0:
                                E[(k,d)] += prob[k]/totalProb
                            elif attributes[d]['isContinuous'] and x[d] > .5:
                                E[(k,d)] += prob[k]/totalProb
            # Maximization step
            for k in xrange(numClusters):
                # Update parameters for Bernoulli's
                P[k] = E[k]/numExamples
                for d in xrange(dimensions):
                    P[(k,d)] = E[(k,d)]/E[k]
            #print [P[k] for k in xrange(numClusters)]

            new_likelihood = 0.
            # Assign cluster
            for x in data[:numExamples]:
                pick = []
                for k in xrange(numClusters):
                    pick.append(P[k])
                    for d in xrange(dimensions):
                        if attributes[d]['isContinuous']:
                            pick[k] *= P[(k,d)] if x[d] > .5 \
                                else (1-P[(k,d)])
                        else:
                            pick[k] *= P[(k,d)] if x[d] > 0 \
                                else (1-P[(k,d)])
                k = pick.index(max(pick))
                for d,xi in enumerate(x):

                    if attributes[d]['isContinuous']:
                        new_likelihood += math.log(P[(k,d)]) if xi > .5 \
                            else math.log(1-P[(k,d)])
                    else:
                        new_likelihood += math.log(P[(k,d)]) if xi > 0 \
                            else math.log(1-P[(k,d)])

            converged_count = converged_count + 1 \
                if (likelihood - new_likelihood > math.exp(-5)) else 0
            likelihood = new_likelihood
            print likelihood
            iterations += 1
        print 'Interations: ', iterations

    elif opt.mix:
        # Set up discretization info
        assert(dimensions == len(attributes))

        E = {} # Expected values
        P = {} # Parameters
        mean = {}
        var = {}
        w = {} # gamma for the Gaussians
        discrete = float(len([a for a in attributes if not a['isContinuous']]))

        # Set initial parameters
        for k in xrange(numClusters):
            P[k] = random.random()
            for d in xrange(dimensions):
                if attributes[d]['isContinuous']:
                    mean[(k,d)] = random.random()
                    var[(k,d)] = random.random()
                else:
                    P[(k,d)] = random.random()
        # Run EM
        converged_count = 0
        likelihood = float('inf')
        iterations = 0
        total_time = 0.
        while converged_count < 2:
            start = time.time()
            # Calculate expected values step
            # Set all expected values to 0
            for k in xrange(numClusters):
                E[k] = 0.
                for d in xrange(dimensions):
                    E[(k,d)] = 0.
            # For each input
            for n,x in enumerate(data[:numExamples]):
                # Per input temporary probabilities for each cluster
                prob = []
                for _ in xrange(numClusters):
                    prob.append(float(P[k]))
                # For each attribute calculate probabilities
                for d,xi in enumerate(x):
                    w_denominator = 0.
                    for k in xrange(numClusters):
                        if attributes[d]['isContinuous']:
                            # TODO
                            w[(k,d,n)] = getPDF(float(xi), var[(k,d)], \
                                mean[(k,d)])
                            w_denominator += w[(k,d,n)]
                        else:
                            if xi > 0:
                                prob[k] *= P[(k,d)]
                            else:
                                prob[k] *= (1-P[(k,d)])
                    # Calibrate gamma
                    for k in xrange(numClusters):
                        if attributes[d]['isContinuous']:
                            w[(k,d,n)] /= w_denominator
                # Sum up expected values
                totalProb = sum(prob) # 0 if every discrete xi is 0.0 TODO
                for k in xrange(numClusters):
                    if totalProb: # If totalProb != 0.0
                        E[k] += prob[k]/totalProb
                        for d in xrange(dimensions):
                            if not attributes[d]['isContinuous'] \
                                and x[d] > 0:
                                E[(k,d)] += prob[k]/totalProb
            # Maximization step
            for k in xrange(numClusters):
                # Update parameters for Bernoulli's
                P[k] = E[k]/numExamples
                for d in xrange(dimensions):
                    if not attributes[d]['isContinuous']:
                        P[(k,d)] = E[(k,d)]/E[k]
                    else:
                        # Update parameters Gaussians
                        denominator = 0.
                        meanNumerator = 0.
                        varNumerator = 0.
                        for n in xrange(numExamples):
                            denominator += w[(k,d,n)]
                            meanNumerator += w[(k,d,n)] * data[n][d]
                        mean[(k,d)] = meanNumerator/denominator
                        for n in xrange(numExamples):
                            varNumerator += w[(k,d,n)] * \
                                math.pow(data[n][d] - mean[(k,d)],2)
                        var[(k,d)] = varNumerator/denominator
            # Update cluster's probability by mixing
            for k in xrange(numClusters):
                P[k] *= discrete/dimensions
                for d in xrange(dimensions):
                    if attributes[d]['isContinuous']:
                        N = 0. # Same as denominator from above
                        for n in xrange(numExamples):
                            N += w[(k,d,n)]
                        P[k] += ( (N/numExamples) /dimensions)

            # Update runtime
            total_time += time.time() - start

            new_likelihood = 0.
            # Assign cluster
            for x in data[:numExamples]:
                pick = []
                for k in xrange(numClusters):
                    pick.append(P[k])
                    for d in xrange(dimensions):
                        if not attributes[d]['isContinuous']:
                            pick[k] *= P[(k,d)] if x[d] > 0 \
                                else (1-P[(k,d)])
                k = pick.index(max(pick))
                for d,xi in enumerate(x):

                    if not attributes[d]['isContinuous']:
                        new_likelihood += math.log(P[(k,d)]) if xi > 0 \
                            else math.log(1-P[(k,d)])

            converged_count = converged_count + 1 \
                if (new_likelihood - likelihood < math.exp(-5)) else 0
            likelihood = new_likelihood
            print likelihood
            iterations += 1

        # Calculate means
        means = []
        for k in xrange(numClusters):
            m = []
            for d in xrange(dimensions):
                if attributes[d]['isContinuous']:
                    m.append(mean[(k,d)])
                else:
                    if d in [43,47]: # If not nomial
                        m.append(P[(k,d)])
                    else:
                        m.append(P[(k,d)] / (math.sqrt(2.)))
            means.append(m)
        print "Means: ", means

        print 'Interations: ', iterations

        print 'Time per iteration (averaged in seconds): ', \
            (total_time / float(iterations))

        if opt.small:
            plot(data,numExamples,numClusters,dimensions,P,var,mean,attributes)


if __name__ == "__main__":
    validateInput()
    main()
