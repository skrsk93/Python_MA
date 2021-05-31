the device is most likely attached to user group dialout. Just add your user to the dialout group so you have appropriate permissions on the device.

sudo usermod -a -G dialout $USER

(You may need to logout and back in for the new group to take effect.)

Nachchecken ob succeeded: getent group dialout

# Contribution Hinweise
Im Gitlab einen Schlüssel erstellen, den dann im System registieren (Git Bash or vice versa); dann kann im Pycharm das gecloned werden
Ggf. Anaconda installieren...
Dann: Branch auf develoment_(kürzel) bitte umstellen
Ich merge den Kram von uns dann. -jonas

# Used packages (hoffentlich vollständig)
* PyQt5 (package "pyqt")
* Numpy
* Matplotlib
* Pyserial (package "pyserial")

# Hinweise zu den Testdaten
## Heart Rate
Series 1 und 2: "Each series contains 1800 evenly-spaced measurements of instantaneous heart rate from a single subject. The two subjects were engaged in comparable activities for the duration of each series. The measurements (in units of beats per minute) occur at 0.5 second intervals, so that the length of each series is exactly 15 minutes." (Source see MIT Source in Sources Section below)

## PPG Test Data
https://pubmed.ncbi.nlm.nih.gov/29485624/
"The PPG sensor model was SEP9AF-2 (SMPLUS Company, Korea), which contains dual LED with 660nm (Red light) and 905 nm (Infrared) wavelengths, with a sampling rate of 1 kHz and 12-bit ADC, and the hardware filter design is 0.5‒12Hz bandpass."
=> 1kHz Frequenz

#Genutzte Fremdquellen
## für Testdaten:
* Heart rate test data by MIT: http://ecg.mit.edu/time-series/
##  für die GUI:
* <div>Icons made by <a href="https://www.flaticon.com/authors/freepik" title="Freepik">Freepik</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>