"""
Starts the GUI
author: Jonas Christiansen
"""

import pulseoxyGui
import customClasses

# create and start virtual device
# pox = customClasses.RealPulseoxymeterTest(buf_storage_size=3000, frequency=50, SERIAL_PORT='COM5') #Beispielaufruf für das reale Testpulsoxymeter, ungetestet!!! - um es zu benutzen, die andere, mit pox startende Zeile auskommentieren und bei dieser hier ganz vorne den # wegnehmen!
                                                                                # Frequency = 50 ist hier statisch. Ggf. für genauere Analyse später lieber dynamisch berechnen?!
                                                                                # Change SERIAL_PORT to your specific Arduino Port, e.g. /dev/ttyACM0
pox = customClasses.SimulatedPulseoxymeter(buf_storage_size=3000, frequency=1000) # PPG
pox.start_logging() # Starts gathering data from sensor

# start GUI
pulseoxyGui.createPulsoxyGui(pox)

