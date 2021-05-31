from numpy.core.defchararray import index
from numpy.core.fromnumeric import sort
from scipy.stats import weibull_min, weibull_max, exponweib, entropy
import numpy as np
import scipy.spatial.distance as sd
from itertools import combinations, permutations

#permutation alginment alogrithm 1 from Eugen Hoffmann (page 60)
def perm_al_hof_alg1(Sources):
    #norm the source vectors
    norm_X = np.abs(Sources)

    #Permuted source signals
    P = []
    
    #List of weibull parameters
   
    weibull_pdf = []

    #estimate weibull parameters with MLE 
    for i in range(len(Sources)):
        b = weibull_min.fit(norm_X[i],floc = 0, fscale = 1) #estimate weibull parameters for all frequency bands
        weibull_pdf.append(weibull_min.pdf(norm_X[i],b[0]))

    #calculate all permutations for weibull distributions of the frequency bands
    Permutations = list(permutations(weibull_pdf,r=2))

    #Calculate Jensen-Shannon divergence for every permutation
    Distances = []

    for j in range(len(Permutations)):
        Distances.append(sd.jensenshannon(Permutations[j][0],Permutations[j][1])) 
    
    #Sort for lowest to largest and remove duplicates
    Distances_sorted = list(dict.fromkeys(sort(Distances)))

    P_weib = Permutations[Distances.index(Distances_sorted[0])]
    
    Pdf_count = weibull_pdf

    #Remove corrected frequency bins from Pdf_count
    for k in range(len(P_weib)):
        Pdf_index_1 = np.where(np.all(weibull_pdf==(P_weib[k]), axis = 1))
        Pdf_count.pop(Pdf_index_1[0][0])
    
    l = len(Pdf_count)
    while l > 0:
        #mean for all power density functions
        Weibull_mean = [np.mean(P_weib, axis=0)]
        
        #calculate all combinations of mean and the rest of frequency pdfs
        all_combinations = Pdf_count
        for m in range(len(Pdf_count)):
            all_combinations.append(Weibull_mean[0])

        #get shortest distance and add frequency bin to corrected frequencys
        x_distance = []
        for n in range(len(all_combinations)):
           x_distance.append(sd.jensenshannon(all_combinations[n][0],all_combinations[n][1]))

        x_sorted = list(dict.fromkeys(sort(x_distance)))
        P_weib.append(all_combinations[x_distance.index[x_sorted[1]]])

        l = l - 1 

    return P

#permutation alginment alogrithm 2 from Eugen Hoffmann (page 61)
def perm_al_hof_alg2(Sources):

    #norm the source vectors
    norm_X = np.abs(Sources) 
    
    #estimate weibull parameters for normed sources
    weibull_pdf =[] 

    #estimate weibull parameters with MLE 
    for i in range(len(Sources)):
        b = weibull_min.fit(norm_X[i],floc = 0, fscale = 1) #estimate weibull parameters for all frequency bands
        weibull_pdf.append(weibull_min.pdf(norm_X[i],b[0]))

    #calculate all permutations for weibull distributions of the frequency bands
    Permutations = list(permutations(weibull_pdf,r=2))

    #Calculate Jenson-Shannon divergence for every permutation (includes 'AB' 'BA') - Wie bestimmt man die richtige Reihenfolge? Symmetrisches Maß, unterscheidung nicht möglich?
    Distances_start = []
    for j in range(len(Permutations)):
        Distances_start.append(sd.jensenshannon(Permutations[j][0],Permutations[j][1]))

    #Sort for lowest to largest and remove duplicates
    Distances_sorted = list(dict.fromkeys(sort(Distances_start)))

    #Get the two closest frequency bands to use them as a start 
    B = Permutations[Distances_start.index(Distances_sorted[0])]
    Sources_norm = [norm_X[weibull_pdf.index(B[0])],norm_X[weibull_pdf.index(B[1])]]

    #Calculate permutations for mean of corrected frquency bands
    for k in range(len(Sources)-2):

        #get the mean of corrected frequency bands
        bands = np.mean(Sources_norm, axis = 1)

        #calculate the weibull parameters for the mean
        b = weibull_min.fit(bands,floc = 0, fscale = 1)
        weibull_1 = weibull_min.pdf(bands,b[0])

        #calculate the Jensen-Shannon divergence and look for the closest frequency band and add it to the corrected batch
        ent = []
        for l in range(len(a)):
            ent.append(sd.jensenshannon(a[l],weibull_1))

        ent_sorted = list(dict.fromkeys(sort(ent)))
        #permutations of a and weibull_1
        Sort_frq = ent.index(ent_sorted[0])
        Sources_norm.append(norm_X[Sort_frq])

    P = []

    return P
