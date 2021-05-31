import numpy as np
from alt_acmnICA import *
from alt_FDICA import *
from alt_jadeICA import *
from perm_align_algos import *
from utils import *
import matplotlib.pyplot as plt
from scipy import signal

#Read the data
data_path = '/Users/stephankrauskopf/Documents/Python_MA/RawData.csv'

xlp = []
R_raw = []
IR_raw = []

with open(data_path, mode="r", encoding="utf8") as csv_file:
    csv_list = list(csv.reader(csv_file, delimiter=","))

    for Value in csv_list[0]:
        xlp.append(float(Value))
    for Value in csv_list[1]:
        R_raw.append(float(Value))
    for Value in csv_list[2]:
        IR_raw.append(float(Value))

#Filter preparation Bandpass and lowpass
cutoff = 1
trans_width = 0.5
Filterband = [1,5]
fs = 1.0 / np.mean(np.abs(np.diff(xlp)))
edges = [0, Filterband[0] - trans_width, Filterband[0], Filterband[1],Filterband[1] + trans_width, 0.5 * fs]
numtaps = 1000

# Bandpass - define filter coefficients (taps)
taps1 = signal.remez(numtaps, [0, cutoff, cutoff + trans_width, 0.5 * fs], [1, 0],Hz=fs)
taps2 = signal.remez(numtaps,edges,[0, 1, 0],Hz=fs)

#Run high pass filter on signals
filtered_red_vec1 = signal.lfilter(taps1, 1.0, R_raw)
filtered_ir_vec1 = signal.lfilter(taps1, 1.0, IR_raw)

#Run bandpass filter on signals
filtered_red_vec2 = signal.lfilter(taps2,1.0,R_raw)
filtered_ir_vec2 = signal.lfilter(taps2,1.0,IR_raw)

# Normalize data
R_normalized = np.divide(filtered_red_vec2, filtered_red_vec1) * (-1)
IR_normalized = np.divide(filtered_ir_vec2, filtered_ir_vec1) * (-1)

#Overlapp add to split up the segments
oa_R = overlap_add(R_normalized)
oa_IR = overlap_add(IR_normalized)

demixed_R_acmn = []
demixed_IR_acmn = []
demixed_R_fdica = []
demixed_IR_fdica = []
demixed_R_jade = []
demixed_IR_jade = []

#Blind Source Seperation
for i in range(len(oa_R)):
    f_R, t_R, Zxx_R = signal.stft(oa_R[i], fs, nperseg=32, noverlap=24)
    f_IR, t_IR, Zxx_IR = signal.stft(oa_IR[i], fs, nperseg=32, noverlap=24)


    #ICA algorithms
    #Adaptable ICA algorithm based on complex generalized Gaussian distribution
    """
    W: array, shape (n_components, n_components)
    Estimated un-mixing matrix.
    K : array, shape (n_components, n_features)
    Sphering Matrix
    A : array, shape(n_components,max_iter)
    Complex valued mixing Matrix
    S : array, shape (n_samples, n_components)
    Estimated sources (S = W K X).
    """
    acmn_R_A,acmn_R_S,acmn_R_K,acmn_R_W = ACMNsym(Zxx_R)
    acmn_IR_A,acmn_IR_S,acmn_IR_K,acmn_IR_W = ACMNsym(Zxx_IR)
    
    demixed_IR_acmn.extend(perm_al_hof_alg1(acmn_IR_S))
    demixed_R_acmn.extend(perm_al_hof_alg1(acmn_R_S))

    #ncmn_R_A,ncmn_R_S,ncmn_R_K,ncmn_R_W = ACMNsym(Zxx_R,model='noncirc')
    #ncmn_IR_A,ncmn_IR_S,ncmn_IR_K,ncmn_IR_W = ACMNsym(Zxx_IR,model='noncirc')

    #A fast fixed-point algorithm for independent component analysis of complex valued signals
    """
    W : array, shape (n_components, n_components)
    Estimated un-mixing matrix.
    K : array, shape (n_components, n_features)
    If whiten is 'True', K is the pre-whitening matrix 
    projecting the data onto the principal components. 
    If whiten is 'False', K is 'None'.
    EG : array, shape(n_components,max_iter)
    Expectation of the contrast function E[G(|W'*X|^2)]. 
    This array may be padded with NaNs at the end.
    S : array, shape (n_samples, n_components)
    Estimated sources (S = W K X).
    
    fdica_R_K,fdica_R_W,fdica_R_S,fdica_R_EG= complex_FastICA(Zxx_R)
    fdica_IR_K,fdica_IR_W,fdica_IR_S,fdica_IR_EG= complex_FastICA(Zxx_IR)

    for k in range(len(fdica_R_S)):
        demixed_R_fdica.extend(permutation_correction(fdica_R_S[k]))
        demixed_IR_fdica.extend(permutation_correction(fdica_IR_S[k]))
   """

    #Source separation of complex signals via Joint Approximate Diagonalization of Eigen-matrices
    """
    A : array, shape (n_mixtures, n_sources) 
    Estimate of the mixing matrix
    S : array, shape (n_sources, n_samples) 
    Estimate of the source signals
    V : array, shape (n_sources, n_mixtures)
    Estimate of the un-mixing matrix
    W : array, shape (n_components, n_mixtures)
    Sphering matrix
    """
    jadeICA_R_A,jadeICA_R_S,jadeICA_R_W,jadeICA_R_V = jade(Zxx_R)
    jadeICA_IR_A,jadeICA_IR_S,jadeICA_IR_W,jadeICA_IR_V = jade(Zxx_IR)

    demixed_IR_jade.extend(perm_al_hof_alg1(jadeICA_IR_S))
    demixed_R_jade.extend(perm_al_hof_alg1(jadeICA_R_S))



#ACMN spectral plot - Alg 1
plot_spectrum(Zxx_R,t_R,f_R)
plot_spectrum(acmn_R_S,t_R,f_R)
plot_spectrum(demixed_R_acmn,t_R,f_R)

plot_spectrum(Zxx_IR,t_IR,f_IR)
plot_spectrum(acmn_IR_S,t_IR,f_IR)
plot_spectrum(demixed_IR_acmn,t_IR,f_IR)

#JADE spectral plot - Alg 1
plot_spectrum(Zxx_R,t_R,f_R)
plot_spectrum(jadeICA_R_S,t_R,f_R)
plot_spectrum(demixed_R_jade,t_R,f_R)

plot_spectrum(Zxx_IR,t_IR,f_IR)
plot_spectrum(jadeICA_IR_S,t_IR,f_IR)
plot_spectrum(demixed_IR_jade,t_IR,f_IR)

'''
Split_spec_R = _get_split_spectrum(T_R,WK_R)
Split_spec_IR = _get_split_spectrum(T_IR,WK_IR)

Corrected_spec_R = _correct_dual_permutation(Split_spec_R)
Corrected_spec_IR = _correct_dual_permutation(Split_spec_IR)

t_R,ISTFT_R = signal.istft(Corrected_spec_R,fs=fs,nperseg=32,noverlap=32)
t_R,ISTFT_IR = signal.istft(Corrected_spec_IR,fs=fs,nperseg=32,noverlap=32)
'''