# -*- coding: utf-8 -*-
# ==================================
#
#    Short Time Fourier Trasform
#
# ==================================
from scipy.signal.windows import hamming, hanning
from scipy.fftpack import fft, ifft
from scipy.io.wavfile import read
import pylab as pl
import sys
import numpy as np

__all__ = ['stft', 'istft']


"""
x : ndarray of shape (n_features)
    input data vector, where n_features is the number of features.
    
win : ndarray of shape (L)
    window function, where L is a length of one frame.
    
step : step size.
    
X : ndarray of shape (K, L)
    output spectrogram matrix, where K is the number of frames and L is the number of discrete frequencies (which equals to the length of one frame).
    i.e. X[k,l] is the spectrogram of frame k and frequency l. 
"""

# ======
#  STFT
# ======

def _stft(x, win, step):
    l = len(x) # Input signal length
    N = len(win) # Window width, i.e., the width to be cut out
    M = int(np.ceil(float(l - N + step) / step)) # Number of time frames in the spectrogram
    step = int(step)
    new_x = np.zeros(N + ((M - 1) * step), dtype= np.float)
    new_x[: l] = x # Make the signal a good length.
    
    X = np.zeros([M, N], dtype = np.complex64) # Spectrogram initialization (complex type)
    #Rows correspond to frames, columns to (normalized) frequencies
    #That is, the (k,l) component is the lth frequency component of the kth frame.
    for m in range(M):
        start = step * m
        X[m, :] = fft(new_x[start : start + N] * win)
    return X

# =======
#  iSTFT
# =======
def _istft(X, win, step):
    M, N = X.shape
    assert (len(win) == N), "FFT length and window length are different."
    
    l = (M - 1) * step + N
    x = np.zeros(l, dtype = np.float)
    wsum = np.zeros(l, dtype = np.float)
    for m in range(M):
        start = step * m
        ### Smooth connection
        x[start : start + N] = x[start : start + N] + ifft(X[m, :]).real * win
        wsum[start : start + N] += win ** 2
    pos = (wsum != 0)
    x_pre = x.copy()
    ### Scale alignment for windows
    x[pos] /= wsum[pos]
    return x



"""
as to window function, hamming window is default
    and another option is hannig function.
as to step size, stpe = fftLen/4 is default.
"""

def stft(data, fftLen, win=None, step=None):
    
    if win is None:
        win = hamming(fftLen)
    elif win == 'hanning':
        win = hanning(fftLen)
    else:
        print ("Window name is invalid.\n")
        sys.exit()

    if step is None:
        step = fftLen / 4
    elif step >fftLen:
        print ("step is longer than fftLen.\n")
        sys.exit()
    elif step <= 0:
        print ("step is invalid.\n")
        sys.exit()

    spectrogram = _stft(data, win, step)

    return spectrogram

def istft(spectrogram, fftLen, win=None, step=None):
    
    if win is None:
        win = hamming(fftLen)
    elif win == 'hanning':
        win = hanning(fftLen)
    else:
        print ("Window name is invalid.\n")
        sys.exit()
    
    if step is None:
        step = fftLen / 4
    elif step >fftLen:
        print ("step is longer than fftLen.\n")
        sys.exit()
    elif step <= 0:
        print ("step is invalid.\n")
        sys.exit()
    
    data = _istft(spectrogram, win, step)

    return data



if __name__ == "__main__":
    wavfile = "input1.wav"
    fs, data = read(wavfile)
    
    fftLen = 512 # とりあえず

    ### STFT
    spectrogram = stft(data, fftLen)
    
    ### iSTFT
    resyn_data = istft(spectrogram, fftLen)
    
    ### Plot
    fig = pl.figure()
    fig.add_subplot(311)
    pl.plot(data)
    pl.xlim([0, len(data)])
    pl.title("Input signal", fontsize = 20)
    fig.add_subplot(312)
    pl.imshow(abs(spectrogram[:, : fftLen / 2 + 1].T), aspect = "auto", origin = "lower")
    pl.title("Spectrogram", fontsize = 20)
    fig.add_subplot(313)
    pl.plot(resyn_data)
    pl.xlim([0, len(resyn_data)])
    pl.title("Resynthesized signal", fontsize = 20)
    pl.show()