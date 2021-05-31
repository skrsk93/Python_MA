import scipy.signal
import scipy.stats
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression


def smooth(signal,window_len=50):
    #''' Smoothen and detrend signal by removing 50 Hz using notch and Savitzky-Golay Filter for smoothening''' 
  # num,denom = scipy.signal.iirnotch(50,1,600) ### How is the quality factor choosen?
  # notched = scipy.signal.lfilter(num,denom,signal)
  # y = savgol_filter(notched, window_len, 1) ### How is the window length and the polynomial required choosen?
  # detrend, pred, t = fit_trendline(y)
    y = pd.DataFrame(signal).rolling(window_len,center = True, min_periods = 1).mean().values.reshape((-1,))
    return y

def detrend(signal):
    R, IR = signal[0],signal[1]
    R_detrended = fit_trendline(R)[0]
    IR_detrended = fit_trendline(IR)[0]

    signal = np.concatenate([R_detrended,IR_detrended], axis = 1)

    return signal

def fit_trendline(y, fs = 600): 
    '''Fit Trendline for detrending '''
    model = LinearRegression()
    X = np.array([j for j in range(len(y))])

    X= X.reshape((-1,1))
    x = np.concatenate([X,X**2], axis = 1)
    model.fit(x,y)
    pred = model.predict(x)

    t = X.reshape(len(X))/fs
    return [np.array([y[j] - pred[j] + np.mean(y) for j in range(X.shape[0])]).reshape((-1,1)), pred, t]

def peaks_and_valleys(signal, prominence = 300, is_smooth = True , distance = 250):

    """ Return prominent peaks and valleys based on scipy's find_peaks function """

    if is_smooth:

        smoothened = smooth(signal)
        peak_loc = scipy.signal.find_peaks(smoothened, prominence = prominence, distance = distance)[0] #,scipy.signal.find_peaks(smoothened, prominence = prominence, distance = distance )[1]["prominences"]
    
        signal = signal*(-1)
        smoothened = smooth(signal)
        valley_loc = scipy.signal.find_peaks(smoothened, prominence = prominence,distance = distance)[0]
    
        final_peaks_loc, final_valley_loc = discard_outliers(smooth(signal),peak_loc,valley_loc)
    else:
        peak_loc = scipy.signal.find_peaks(signal, prominence = prominence,distance = distance)[0]
        signal = signal*(-1)
        valley_loc = scipy.signal.find_peaks(signal, prominence = prominence,distance = distance)[0]
    
        final_peaks_loc, final_valley_loc = discard_outliers(signal,peak_loc,valley_loc)
 
    return final_peaks_loc, final_valley_loc

def discard_outliers(signal,peaks,valleys):
    """Find peaks or valleys in a signal. 
    Returns peak, and groups of valleys"""
    val = [[valleys[x-1],valleys[x]] for x in range(1,len(valleys))]
    peak = {}
    for i in range(len(val)) :
        x= val[i]
        try:     
            peak[i] = int(peaks[np.where(np.logical_and(peaks> x[0],peaks < x[1]))[0][0]])
        except:
            pass
    i=0
    val_ = []
    while i<len(val):
        if i not in peak.keys():
            pass
        else:
            val_.append(val[i])
        i+=1
        
    try:
        assert len(peak) == len(val_)
    except AssertionError:


        return None,None
    
    
    final_val =list(set([x for j in val_ for x in j]))
    final_val.sort()
    final_peak = [peak[i] for i in peak.keys()]
    final_peak.sort()
 
    return final_peak,final_val

def return_info(signal, is_smooth):
    """ Get smoothened signal, peak location and valley location 
  Input: 
    signal: RAW SIGNAL"""

    detrended_signal = detrend(signal)
    R_signal = detrended_signal[:,0].reshape((-1,))
    IR_signal = detrended_signal[:,1].reshape((-1,))
    peaks_R, valleys_R = peaks_and_valleys(R_signal, is_smooth)
    peaks_IR, valleys_IR = peaks_and_valleys(IR_signal, is_smooth)
  
    if peaks_R is None or valleys_R is None or peaks_IR is None or valleys_IR is None:
#         print (" No valleys detected by scipy")
        return [None, None, None], [None, None,None]
    if is_smooth:
        return [smooth(signal[0]),peaks_R,valleys_R],[smooth(signal[1]),peaks_IR,valleys_IR]
    else:
        return [signal[0], peaks_R,valleys_R],[signal[1],peaks_IR,valleys_IR]

def plot_signal(signal, is_smooth = True):

    """ plot Red and IR signals along with peaks and valleys"""

    [R_signal,peaks_R, valleys_R],[IR_signal,peaks_IR, valleys_IR] = return_info(signal, is_smooth)

    if R_signal is not None and IR_signal is not None:
        plt.subplot(121)
        plt.title("SMOOTHENED")
        plt.scatter(valleys_R[0],R_signal[valleys_R[0]],c = "b")
        plt.plot(R_signal)
        plt.subplot(122)
        plt.plot(IR_signal)
        plt.show()

        plt.subplot(121)
        plt.title("LOCATIONS")
        plt.plot(R_signal)
        plt.scatter(peaks_R ,R_signal[peaks_R], c= "r")
        plt.scatter(valleys_R,R_signal[valleys_R], c= "g")
        plt.subplot(122)
        plt.plot(IR_signal)
        plt.scatter(peaks_IR, IR_signal[peaks_IR], c= "r")
        plt.scatter(valleys_IR , IR_signal[valleys_IR], c= "g")
        plt.show()


data = [np.genfromtxt(r'/Users/stephankrauskopf/Documents/Python_MA/Dataset/Data File/0_subject/2_1.txt'),np.genfromtxt(r'/Users/stephankrauskopf/Documents/Python_MA/Dataset/Data File/0_subject/2_2.txt')]
time = np.arange(0,2.1,0.001)
#signal = [time,data] #länge = 2100


[R_data,peaks_R,valleys_R],[IR_data,peaks_IR,valleys_IR]= return_info(data,is_smooth=False) # Gibt den gesamten Bereich der Intensitäten(data), sowie Peaks und Täler zurück. Indizes der Peaks und Täler gesucht für die Zeitliche Rekonstruktion.

plot_signal(data)

plt.xlabel('Time')
plt.plot(time,data[0])
plt.show()
print(R_data[peaks_R])
print(R_data[valleys_R])
print(IR_data[peaks_IR])
print(IR_data[valleys_IR])