import csv
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt


# Added from RSCD

def import_data(data):
    """
    reads data csv-file and returns two float arrays: [normalized R],[normalized IR]
    :param string data: path to csv file
    :return: [normalized R],[normalized IR]
    """
    normalized_R = []
    normalized_IR = []

    with open(data, mode="r", encoding="utf8") as csv_file:
        csv_list = list(csv.reader(csv_file, delimiter=","))

        for Value in csv_list[1]:
            normalized_R.append(float(Value))

        for Value in csv_list[2]:
            normalized_IR.append(float(Value))

    return normalized_R, normalized_IR

def overlap_add(data, n=256, overlap=128):
    """
    Decomposition of Data in segments of n = 512 Values with an overlap = 256. Each segment gets multiplied by a bartlett-window.

    :param [float] data: imported time-signals
    :param integer n: Length of Segment
    :param integer overlap: length of overlap
    :return: array of segments
    """
    segments = []

    for i in range(0, len(data), n - overlap):

        if i + n > len(data):  # cuts the last signals from the data, if they are not long enough, for a segment.
            break

        segment = data[i:i + n]
        segment = segment * np.bartlett(n)
        segments.append(segment)

    return segments

#Plot STFT
def plot_spectrum(Zxx,t,f):
    plt.pcolormesh(t, f, np.abs(Zxx), vmin=0, vmax=2*np.sqrt(2), shading='gouraud')
    plt.title('Spectrum Magnitude')
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
    plt.show()  

#Permutations with pick
def combinations(iterable, r):
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = list(range(r))
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)