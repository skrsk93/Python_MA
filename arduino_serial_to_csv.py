from numpy.core.fromnumeric import size
import serial
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.signal import lfilter
from scipy.fft import fftfreq
from serial import Serial
from serial.serialutil import SerialBase

# Initialize serial port INCLUDE YOUR SERIAL PORT  at 115200 baud rate
ser = serial.Serial('/dev/tty.usbmodem142401', 115200)
all_data = []

# read and write serial data
while True:
    try:
        curr_line = SerialBase.readline(ser)
        all_data.append(curr_line)
    except KeyboardInterrupt:
        break
print("Exited Loop")


# define vectors for time stamp and signals
t_vec, ir_vec, red_vec = [], [], []
for ii in range(3, len(all_data)):
    try:
        curr_data = (all_data[ii][0:-3]).decode("utf-8").split(',')
    except:
        continue
    t_vec.append(float(curr_data[0]) / 1000000)
    ir_vec.append(float(curr_data[1]))
    red_vec.append(float(curr_data[2]))
SR1 = 1.0 / np.mean(np.abs(np.diff(t_vec)))  # sample rate

# time count starts after 5 s (250 sample points / 50 Hz = 5 s)
s1 = 250
s2 = len(t_vec)
t_vec = np.array(t_vec[s1:s2])
ir_vec = np.array(ir_vec[s1:s2])
red_vec = np.array(red_vec[s1:s2])


# time count starts from 0 s
base = t_vec[0]
for i in range(0, len(t_vec)):
    t_vec[i] = t_vec[i] - base

final_data = [t_vec, ir_vec, red_vec]

# save raw signals as data.csv
np.savetxt('RawData.csv', final_data, delimiter=',')

# plot of signals
fig, axs = plt.subplots(2)
axs[0].plot(t_vec, red_vec, label="Rote LED")
axs[0].plot(t_vec, ir_vec, label="IR LED")
axs[0].set_xlabel('Zeit [s]')
axs[0].set_ylabel('Amplitude')
axs[0].set_xlim([t_vec[0], t_vec[-1]])
axs[0].set_title('Signale')

# sample values for infobox
Y = ir_vec
N = len(Y)
T = 1.0 / SR1
N = int(N)
TT = N * T

# infobox in plot
textstr = '\n'.join((
    r'$Sample Rate=%.2f Hz$' % (SR1,),
    r'$Sample Points=%.2f$' % (N,),
    r'$Sample Spacing=%.6f s$' % (T,),
    r'$Total Time=%.2f s$' % (TT,)))

props = dict(boxstyle='round', alpha=0.5)
axs[0].text(0.05, 0.75, textstr, transform=axs[0].transAxes, fontsize=8, verticalalignment='top', bbox=props)

axs[0].legend()

# frequency FFT plot - define axes first
yf = np.fft.fft(ir_vec)
yf = 2.0 / N * np.abs(yf[0:N // 2])
xf = fftfreq(N, T)[:N // 2]
xf = xf * 60

axs[1].set_xlabel('Frequenzen in BPM')
axs[1].set_ylabel('Amplitude')
axs[1].plot(xf, yf)
axs[1].grid()
axs[1].set_yscale('log')
axs[1].set_xscale('log')
axs[1].set_title('Frequenzspektrum')

plt.tight_layout()

# save plot as freq.png
plt.savefig('freq.png', dpi=300, facecolor=[252 / 255, 252 / 255, 252 / 255])
plt.show()


# filtering of signals - functions for plots (signal plots, infobox, frequency response)
def sub_plots_filtered(line, row, x, y, title):
    axs[line, row].plot(x, y)
    axs[line, row].set_title(title)
    axs[line, row].set_xlabel('Zeit [s]')
    axs[line, row].set_ylabel('Amplitude')

def infobox(Eintrag1, line, row, type, Eintrag2):
    if type == True:
        textstr = '\n'.join((
            r'$Grenzfrequenz=%.2f Hz$' % (Eintrag1,),
            r'$Abtastrate=%.2f Hz$' % (Abtastrate,)))
    else:
        textstr = '\n'.join((
            r'$Grenzfrequenz 1=%.2f Hz$' % (Eintrag1,),
            r'$Grenzfrequenz 2=%.2f Hz$' % (Eintrag2,),
            r'$Abtastrate=%.2f Hz$' % (Abtastrate,)))
    props = dict(boxstyle='round', alpha=0.5)
    axs[line, row].text(0.05, 0.75, textstr, transform=axs[line, row].transAxes, fontsize=8, verticalalignment='top',
                        bbox=props)

def plot_response(fs, w, h, title, line, row):
    axs[line, row].plot(0.5 * fs * w / np.pi, 20 * np.log10(np.abs(h)))
    axs[line, row].set_ylim(-40, 5)
    axs[line, row].set_xlim(0, 0.5 * fs)
    axs[line, row].grid(True)
    axs[line, row].set_xlabel('Frequency (Hz)')
    axs[line, row].set_ylabel('Gain (dB)')
    axs[line, row].set_title(title)

# filtering of signals - parameters
Abtastrate = SR1
Grenzfrequenz1 = 0.5
Filterband = [0.6, 5]
trans_width = 0.5  # Width of transition from pass band to stop band, Hz
numtaps = 101  # Size of the FIR filter.

# time axes definition
stop = len(red_vec) / Abtastrate
step = int(len(red_vec))
xlp = np.linspace(0, stop, step)

# plot filtered signals and frequency responses
fig, axs = plt.subplots(2, 2)

# lowpass 1 - define filter coefficients (taps)
taps01 = signal.remez(numtaps, [0, Grenzfrequenz1, Grenzfrequenz1 + trans_width, 0.5 * Abtastrate], [1, 0],
                      Hz=Abtastrate)

# run filter on signals
filtered_red_vec1 = lfilter(taps01, 1.0, red_vec)
filtered_ir_vec1 = lfilter(taps01, 1.0, ir_vec)

sub_plots_filtered(0, 0, xlp, filtered_red_vec1, 'FIR Tiefpassfilterung / Gleichanteil')
sub_plots_filtered(0, 0, xlp, filtered_ir_vec1, 'FIR Tiefpassfilterung / Gleichanteil')

infobox(Grenzfrequenz1, 0, 0, True, Grenzfrequenz1)

# filter coefficients for plot response
w1, h1 = signal.freqz(taps01, [1], worN=2000)
plot_response(Abtastrate, w1, h1, "Frequenzgang Gleichanteilfilter", 0, 1)

# bandpass - define band edges
edges = [0, Filterband[0] - trans_width, Filterband[0], Filterband[1],
         Filterband[1] + trans_width, 0.5 * Abtastrate]

# define filter coefficients
taps02 = signal.remez(numtaps, edges, [0, 1, 0], Hz=Abtastrate)

# run filter on signals
filtered_red_vec21 = lfilter(taps02, 1.0, red_vec)
filtered_ir_vec2 = lfilter(taps02, 1.0, ir_vec)

sub_plots_filtered(1, 0, xlp, filtered_red_vec21, 'FIR Bandpassfilterung / Wechselanteil')
sub_plots_filtered(1, 0, xlp, filtered_ir_vec2, 'FIR Bandpassfilterung / Wechselanteil')

infobox(Filterband[0], 1, 0, False, Filterband[1])

# define filter coefficients for plot response
w2, h2 = signal.freqz(taps02, [1], worN=2000)
plot_response(Abtastrate, w2, h2, "Frequenzgang Wechselanteilfilter", 1, 1)

plt.tight_layout()

# save plot as filter.png
plt.savefig('filter.png', dpi=300, facecolor=[252 / 255, 252 / 255, 252 / 255])
plt.show()

# normalized intensities and r-value - function for plots
def sub_plots_normalized(row, y, type, type_red, title):
    if type == True:
        if type_red == True:
            axs[row].plot(xlp, y, label="Rot, norm.")
        else:
            axs[row].plot(xlp, y, label="IR, norm.")
        axs[row].set_title('Normalisierte Intensitäten,' + title)
        axs[row].set_xlabel('Zeit [s]')
        axs[row].set_ylabel('Normalisierte Amplitude')
    else:
        axs[row].plot(xlp, y)
        axs[row].set_title('Ratio of Ratios' + title)
        axs[row].set_ylabel('Verhältnis R')
        axs[row].set_xlabel('Zeit [s]')

# calculate normalized intensities
I_RACDC = np.divide(filtered_red_vec21, filtered_red_vec1) * (-1)
I_IRACDC = np.divide(filtered_ir_vec2, filtered_ir_vec1) * (-1)

# calculate r-value
R = np.divide(I_RACDC, I_IRACDC)

fig, axs = plt.subplots(1, 2)

sub_plots_normalized(0, I_RACDC, True, True, ' ACDC')
sub_plots_normalized(0, I_IRACDC, True, False, ' ACDC')
axs[0].legend()
axs[0].set_ylim(0, -0.04)
sub_plots_normalized(1, R, False, False, ' ACDC')
axs[1].set_ylim(0.5, 1.5)

# save plot as ACDCnorm.png
plt.savefig('TESTnorm.png', dpi=300, facecolor=[252 / 255, 252 / 255, 252 / 255])
plt.show()

final_NORMdata = [xlp, I_RACDC, I_IRACDC, R]

# save normalized signals and r-value as NORMdata.csv
np.savetxt('TESTdata.csv', final_NORMdata, delimiter=',')