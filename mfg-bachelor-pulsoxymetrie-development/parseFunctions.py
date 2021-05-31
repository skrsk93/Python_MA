import os
import random

import numpy as np
import pandas as pd


def parse_heartrate_data_from_txt(filename):
    """

    :param filename: Name of the file to be parsed
    :return: an array containing the values in the file as floats

    Jonas Christiansen
    """

    contents = np.loadtxt(filename, dtype=float, delimiter="\n").tolist()
    return contents


def parse_random_ppg_from_test_data():
    """
    Randomly selects one of the files inside the assets/test_data/ppg/data Folder and stores its values into a one-dimensional list.
    :return: the one-dimensional list with the test values

    Jonas Christiansen
    """
    testdata_path = "assets/test_data/ppg/data/"

    print("-----------------------")
    print("Randomly choose file...")

    # Random choose file from the ppg data folder test set
    r_filenameTSV = random.choice(os.listdir(testdata_path))

    print("The chosen file is " + r_filenameTSV)
    print("")
    print("Importing file...")

    # read the data
    filepath = testdata_path + r_filenameTSV
    #tsv_read = pd.read_csv(filepath, sep='\t')

    text_file = open(filepath, "r")
    lines = text_file.read().split('\t')
    messwerte = []
    # print the first 10 records
    for val in lines:
        try:
            messwerte.append(float(val))
        except:
            ValueError("Some error in file. The value " + val + " was not imported due to inability to convert it to float")

    print("Done")
    print("-----------------------")

    return messwerte