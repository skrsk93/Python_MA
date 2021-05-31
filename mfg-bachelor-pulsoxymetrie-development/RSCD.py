import csv
import numpy as np
import scipy.stats
from scipy import signal
import matplotlib.pyplot as plt
import math


def RSCD(data, fs=50):
    """
    Robust Signal Convolutive Demixing (RSCD): demixes the data-Set by statistic methods and calculates the SPO_2 Value with the following steps:

    1. imports the time signal from csv into two arrays (normalized_R - normalized time signal of the reflection in the red sprectrum, normalized_IR - normalized time signal of the reflection in the infrared spectrum).
    2. Overlap-add: turns the two arrays into segments of 10.24 seconds with with the bartlett window.
    3. Short-time Fourier transform (STFT): transforms every segment of part 2 with the STFT into 17 frequency bands (segments = 32, overlap = 24)
    4. prewhites a set of 17 frequency bands to decorrelate the signals (preparation for the ICA in step 5) -> FIXME: mean the signal before!
    5. Independed Component Analysis (ICA): Uses a statistcal second order demixing method on every sequency band to demix the signals
    6. ToDo: permutation correction of the 17 demixed frequenz bands (try a new algorithm for a better running time -> now > 65!)
    7. Inverse Short-time Fourier transform (ISTFT): transforms the 17 demixed frequenz bands with the ISTFT
    8. entropy method: matches the demixed signals either to the pulse-signal or the artefact by using the statistical entropy
    9. ToDo: calculates the SpO2 - Value with the demixing matrice from part 5.

    :param string data:  path to the csv file with the reflection-data of the red and infrared reflection
    :param integer fs: sampling frequency
    :return: [integer], [integer]: time-signal of the pulse, SPO2-Value
    """

    normalized_R, normalized_IR = import_data(data)

    normalized_R_segments = overlap_add(normalized_R)
    normalized_IR_segments = overlap_add(normalized_IR)
    entmischte_Segmente_R = []
    entmischte_Segmente_IR = []

    for i in range(len(normalized_R_segments)):

        f_R, t_R, Zxx_R = signal.stft(normalized_R_segments[i], fs=fs, nperseg=32, noverlap=24)
        # plot(t_R, f_R, Zxx_R)

        prewhitened_R = prewhitening(Zxx_R)
        plot(t_R, f_R, prewhitened_R)
        entmischte_R_frequenzband = []

        for k in range(len(Zxx_R)):
            entmischte_R_frequenzband.append(np.dot(SOBI(prewhitened_R[k]), prewhitened_R[k]))

        # plot(t_R, f_R, entmischte_R_frequenzband)
        sortierte_entmischte_frequenzbänder_R = permutation_correction(entmischte_R_frequenzband)

        sortierte_entmischte_Segmente_R = signal.istft(sortierte_entmischte_frequenzbänder_R)

        entmischte_Segmente_R.append(sortierte_entmischte_Segmente_R)

    for j in range(len(normalized_IR_segments)):

        f_IR, t_IR, Zxx_IR = signal.stft(normalized_IR_segments[j], fs=fs, nperseg=32, noverlap=24)
        prewhitened_IR = prewhitening(Zxx_IR)

        entmischte_IR_frequenzband = []

        for l in range(len(Zxx_IR)):
            entmischte_IR_frequenzband.append(np.dot(SOBI(prewhitened_IR[l], prewhitened_IR[l])))

        sortierte_entmischte_frequenzbänder_IR = permutation_correction(entmischte_IR_frequenzband)
        sortierte_entmischte_Segmente_IR = signal.istft(sortierte_entmischte_frequenzbänder_IR)
        entmischte_Segmente_IR.append(sortierte_entmischte_Segmente_IR)


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


def center(data):
    """
    ToDO: centers a array of data by substrating the mean
    :param [[np.complex]] data: Zxx after STFT
    :return: [[np.complex]]
    """
    mean = data.mean
    return data - mean


def prewhitening(data):
    """
    prewhitening decorrelates the data (Dissertation by Volmer maybe shows the wrong equation): we used: X_whiten = E * D^(-1/2) * E^T * x
    Source: Unterdrückung von Bewegungsartefakten beim Langzeitmonitoring zur Anwendung in Personal-Healthcare-Systemen, Achim Volmer, p. 123 eq. 6.53
    :param [[np.complex]] data: Zxx after STFT
    :return: [[np.complex]]
    """
    # data = center(data) # TODO: center the data!
    cov = np.cov(data)

    d, E = np.linalg.eigh(cov)
    D = np.diag(d)
    D_inv = np.sqrt(np.linalg.inv(D))
    X_whiten = np.dot(E, np.dot(D_inv, np.dot(E.T, data)))

    return X_whiten


def overlap_add(data, n=512, overlap=256):
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


def SOBI(data, set_cov=50):
    """
    Second Order Blind Identification (SOBI): calculates the demixing matrix by a statistical second order method.
    source: Unterdrückung von Bewegungsartefakten beim Langzeitmonitoring zur Anwendung in Personal-Healthcare-Systemen, Achim Volmer, p. 128 ff. section 6.9.4.
    :param [np.complex] data: the frequency band, to calculate the demixing matrix for
    :param integer set_cov: number of time shifted covariances, used as Cov_set to calculate the demixing-matrix.
    :return: demixing matrix for the frequency band
    """
    Cov_set = []
    zero_padding = np.zeros(set_cov)
    data_padded = np.append(data, zero_padding)

    for i in range(set_cov):
        X = np.vstack((data, data_padded[i + 1:i + 65 + 1]))
        Cov_set.append(np.cov(X.T))

    Sum_Cov = Cov_set[0]

    for j in range(1, len(Cov_set)):
        Sum_Cov = Sum_Cov + Cov_set[j]

    row = 0
    column = 0

    rotation_matrices = []

    while row < len(Sum_Cov):

        while column < row:
            rotation_matrices.append(get_rotation_matrix(Sum_Cov, row, column))
            column = column + 1

        row = row + 1

    reversed(rotation_matrices)
    rotation_matrix = rotation_matrices[0]

    for k in range(1, len(rotation_matrices)):
        rotation_matrix = rotation_matrix * rotation_matrices[k]

    return rotation_matrix


def get_rotation_matrix(matrix, row, column):
    """
    gets the rotation matrix to set the Value [row][column] from a given matrix to zero by rotation
    :param [[np.complex]] matrix: matrix to rotate
    :param integer row: row of the value in the given matrix
    :param integer column: columns of the value in the given matrix
    :return: rotation matrix
    """
    length_matrix = len(matrix)
    identity = np.identity(length_matrix, dtype=complex)

    if matrix[row][column] == 0:
        return identity
    """
    Berechnung D, c, s --> Mathematik 2.Auflage, (T.Ahres, H.Hettlich, Ch.Karpfinger), Spektrum Akademischer Verlag, S.612 
    """
    D = (matrix[row][row] - matrix[column][column]) / np.sqrt(
        ((matrix[row][row] - matrix[column][column]) ** 2 + 4 * (matrix[row][column]) ** 2))
    c = np.sqrt((1 + D) / 2)

    if matrix[row][column] > 0:
        s = np.sqrt((1 - D) / 2)
    else:
        s = -np.sqrt((1 - D) / 2)

    R = identity

    R[row][row], R[column][column] = c, c
    R[row][column], R[column][row] = s, -s

    return R


def plot(t, f, Zxx):
    """
    shows the plot of a STFT-result
    :param t: time-vector
    :param f: frequency-vector
    :param Zxx: signals-matrix of a STFT result
    :return: just plotting
    """

    plt.pcolormesh(t, f, np.abs(Zxx), shading='gouraud')

    plt.title('STFT Magnitude')

    plt.ylabel('Frequency [Hz]')

    plt.xlabel('Time [sec]')

    plt.show()


def permutation_correction(covariance_matrices_matrix):
    """
    Calculates the Permutation Correction following the correlation-based method by Rahbar and Reilly

    According to dissertation p. 127 to be found in:
    Rahbar, K.; Reilly, J. P.: A Frequency Domain Method for Blind Source
    Separation of Convolutive Audio Mixtures. In: IEEE Transactions on Speech and
    Audio Processing 13 (2005), Nr. 5, S. 832–844
    Via http://www.ece.mcmaster.ca/~reilly/assp_02_daft8.pdf

    Hilfreiche Beschreibung des Korrelationskoeffizienten:
    https://www.crashkurs-statistik.de/der-korrelationskoeffizient-nach-pearson/


    :param covariance_matrices_matrix: A 2-D list holding all diagonal covariance matrices. index 0 = Omega, index 1 = τ (tau) time point, index 2 = kth diagonal element of the corresponding matrix
    e.g. covariance_matrices_matrix[1][2][3] means the 3rd diagonal element of the Λ(ω=ω_k,τ=2) with k corresponding to the 2nd omega element of the list
    :type self: object

    Jonas Christiansen
    """

    # Matrix erstellen für die jeweils besten normierte Korrelation pro Kreuzkombination aller Frequenzbänder - zunächst alle 0
    num_freq_bands = len(covariance_matrices_matrix)
    best_perm_matrix = np.zeros((num_freq_bands, num_freq_bands))

    # Get highest tau value. should be equal across all those matrices, so:
    tau_value = len(covariance_matrices_matrix[0])

    # Calculate best Permutation for every combination of omega_k and omega_j by calculating every rho_q_p using formula
    # and storing it in permutation matrix only if the newly calculated value is higher then a previous
    # one stored in the permutationm matrix for this (k,j) combination

    for k in range(0, num_freq_bands):
        for j in range(0, num_freq_bands):

            for q in range(0, covariance_matrices_matrix[k][0]):
                for p in range(0, covariance_matrices_matrix[j][0]):

                    zaehler = 0
                    for tau in range(0, tau_value):
                        zaehler += (covariance_matrices_matrix[k][tau][q] * covariance_matrices_matrix[j][tau][p])

                    sum1 = 0
                    for tau in range(0, tau_value):
                        sum1 += covariance_matrices_matrix[k][tau][q] ** 2

                    sum2 = 0
                    for tau in range(0, tau_value):
                        sum2 += covariance_matrices_matrix[j][tau][p] ** 2

                    nenner = math.sqrt(sum1) * math.sqrt(sum2)

                    rho_q_p = zaehler / nenner

                    if (rho_q_p > best_perm_matrix[k][j]):
                        best_perm_matrix[k][j] = rho_q_p

    return best_perm_matrix


def entropy(x, num_bins):
    '''
    Dissertation Seite 130, Formel 6.67
    Lt. https://en.wikipedia.org/wiki/Logarithm und https://en.wikipedia.org/wiki/Entropy_(information_theory),
    scheint ld der Logarithmus zur Basis 2 zu sein

    :param num_bins: Genauigkeit - in so viele bereiche werden die Daten unterteilt für die Berechnung der rel.Häufigkeit
    :param x: Liste mit den xi Elementen
    :return:

    Jonas Christiansen
    '''

    # group values to bins using histogram helper
    frequency, bins = np.histogram(x, bins=num_bins)

    # Absoulte Häufigkeiten in Relative umwandeln
    total_num_signals = frequency.sum()
    frequency = np.array(frequency) / total_num_signals

    # create array of xi values from the bin values using mean
    xi_arr = []
    # bins hat die start- und end-x-werte der jew. balken d. histograms
    # immer zwei benachbarte werte nehmen, mittelwert berechnen, den nehmen wir äqivalent als xi value
    for i in range(0, len(bins) - 1):
        xi_arr.append(((bins[i] + bins[i + 1]) / 2))

    # calculate the entropy
    return scipy.stats.entropy(frequency, qk=xi_arr, base=2)


if __name__ == "__main__":
    RSCD("NORMdata.csv")
