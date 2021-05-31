import abc
import datetime
import threading
import time
import types
from abc import ABC, abstractmethod

### FÜR SYNCHRONISIERUNG ZWISCHEN DEN THREADS DER METHODEN MEASURE_VALUE UND LOGGING_LOOP IM REAL PULSEOXYMETER

from threading import Thread

lock = threading.Lock()
all_data = []  # Zwischenspeicher für Messwertverarbeitung/Darstellung auf der GUI, nach Stopp eines Virtual Instruments ist der inhalt "egal" und kann beim nächsten mal wieder auf [] gesetzt werden

### ENDE SYNCHRONISATION INITIALISIERUNG

import numpy as np
import pandas as pd
import serial

import parseFunctions


class DataStorage:
    def __init__(self):
        """
            An abstract class for storing timestamps and corresponding data values for analysis / display / save later

            Jonas Christiansen

        """

    @abstractmethod
    def reset(self):
        """
            Turns all variables in data structure to the values they had right after the object was created
            Useful for restart of measure to omit old saved values in RAM or vice versa.
        """
        return NotImplementedError

    @abstractmethod
    def getTimestamps(self) -> list:
        """
            Returns the stored timestamp array sorted by time of insertion,

            :return: the list stored in the class sorted by time of insertion
        """
        return NotImplementedError

    @abstractmethod
    def getValues_heartrate(self) -> list:
        """
            Returns the stored heart rate values array sorted by time of insertion,

            :return: the list stored in the class sorted by time of insertion
        """
        return NotImplementedError

    @abstractmethod
    def getValues_spo2(self) -> list:
        """
            Returns the stored SpO2 values array sorted by time of insertion,

            :return: the list stored in the class sorted by time of insertion
        """
        return NotImplementedError

    @abstractmethod
    def push(self, datetime_of_capture: datetime, value_heartrate, value_spo2, verbose=False):
        """
        Pushes the new value to the list, in case of fixed size queue also overwriting the oldest value in the list.

        :param value_heartrate: The heartrate value to be pushed to the list. Should be float
        :param value_spo2: The SpO2 value to be pushed to the list. Should be float
        :param datetime_of_capture: The date and time when the measured data was captured by the Arduino. Must be object of python datetime class
        :return:
        """
        return NotImplementedError

    def __str__(self):
        """
        Only useful for debugging purposes. Shows the content of the data structure in form of a string to the console
        :return: String representation of data storage
        """
        retval = ""
        retval += "[("

        for i in range(0, len(self.getTimestamps())):
            retval += str(self.getTimestamps()[i]) + ", " + str(self.getValues_heartrate()[i]) + ", " + str(
                self.getValues_spo2()[i]) + "),"
        retval += "]"
        return retval

    def length(self) -> int:
        """

        :return: The length of the list (number of stored elements / max. number in case of live queue)
        """
        return len(self.getTimestamps())


class InfiniteDataStorage(DataStorage):
    def __init__(self):
        """
            A class that simply holds a list for timestamps and corresponding data each; serving as a possibility to
            save several measure results; for later export

            Jonas Christiansen
        """
        super().__init__()

        self._df = pd.DataFrame(columns=['timestamp', 'value_heartrate', 'value_spo2'])

    def getTimestamps(self):
        return self._df['timestamp']

    def getValues_heartrate(self):
        return self._df['value_heartrate']

    def getValues_spo2(self):
        return self._df['value_spo2']

    def push(self, datetime_of_capture: datetime, value_heartrate, value_spo2, verbose=False):
        self._df.loc[len(self._df.index)] = [datetime_of_capture, value_heartrate, value_spo2]

        if verbose:
            print("Got new data point: Time: " + str(datetime_of_capture) + " Value Heartrate: " + str(
                value_heartrate) + " Value SpO2: " + str(value_spo2))

    def reset(self):
        # Drop all rows from dataframe
        self._df = self._df.iloc[0:0]

    def get_values_df(self):
        return self._df


class FixedSizeDataQueue(DataStorage):
    def __init__(self, n: int):
        """
            Creates a Queue with fixed length: on every insert, elements are shifted one position to the left,
            aka each push on the end of queue results also in a pop at the start so that the list keeps its size.
            (Stores last n inserted values and returns them in order of insertion)
            This queue will work as two lists: one for timestamps, one for measure data. Same index then means timestamp
            belongs to this data. this is made so that handling inside matplotlib will be easier.

            BUT: on first iteration, if there are not all elements filled, the empty ones will not be in output list!
        :param n: the length that the liveList should have


        Jonas Christiansen
        """

        super().__init__()

        self._array_timestamps = []
        self._array_data_heartrate = []
        self._array_data_spo2 = []

        if not type(n) is int:
            raise TypeError("Only integers are allowed as list length")

        if n < 1:
            raise ValueError("Length must be greater than or equal 1!")

        self.__length = n # Not to be confused with the self.length() method of the DataStorage class!!!

        # Initialize the Data Structure with zeros
        for i in range(0, n):
            self._array_timestamps.append(datetime.datetime.now())
            self._array_data_heartrate.append(0)
            self._array_data_spo2.append(0)

        self.__cursor = 0
        self.__isFirstLoop = True  # True => there have been no overwrites yet..; False => at least one value has
        # been overwritten, or will be overwritten the next time an element is pushed

    def reset(self):
        """
            Turn all values in the list to zero and set cursor to start
        """
        for i in range(0, self.length()):
            self._array_timestamps.append(datetime.datetime.now())
            self._array_data_heartrate.append(0)
            self._array_data_spo2.append(0)

        self.__cursor = 0
        self.__isFirstLoop = True

    def push(self, datetime_of_capture: datetime, value_heartrate, value_spo2, verbose=False):

        self._array_timestamps[self.__cursor] = datetime_of_capture
        self._array_data_heartrate[self.__cursor] = value_heartrate
        self._array_data_spo2[self.__cursor] = value_spo2

        # Move cursor 1 position to left; if end is reached then move cursor to start
        self.__cursor += 1
        if self.__cursor == self.length():  # "Overflow" -> go to 0
            self.__cursor = 0
            if self.__isFirstLoop:
                # End of first iteration, from now on do overwrite old values
                self.__isFirstLoop = False
            return

        # A string representing datetime and value of new measure data point.
        if verbose:
            print("Got new data point: Time: " + str(datetime_of_capture) + " Value Heartrate: " + str(
                value_heartrate) + " Value SpO2: " + str(value_spo2))

    def __sort_by_cursor_pos(self, arr):
        """
            Sort - using the cursor (position of cursor-1 is the position of last element that was inserted.)
        """
        if (self.__cursor == 0) or self.__isFirstLoop:
            return arr[0:self.__cursor]

        return arr[self.__cursor:self.__length] + arr[0:self.__cursor]

    def getTimestamps(self):
        return self.__sort_by_cursor_pos(self._array_timestamps)

    def getValues_heartrate(self):
        return self.__sort_by_cursor_pos(self._array_data_heartrate)

    def getValues_spo2(self):
        return self.__sort_by_cursor_pos(self._array_data_spo2)

    def getCurrentCursorPosition(self):
        """
        Only for develoment purposes. No useful usage in production.
        :return:
        """
        return self.__cursor


# Abstract class for instrument representation with measure values
class VirtualInstrument:
    def __init__(self, buf_storage_size, device_name="Virtual Instrument"):
        """
            Virtual Instrument: represents an actual physical or simulated device as class interface.
            Connection to the device is made up in the measure_value method in corporation with logging_loop
            The instrument can be started to gather data from device by calling start_logging and stopped with stop_logging

            On start of each logging, the record data store will be reset.
            Recording of data can be done with start_recording and stop_recording

            Abstract class; so that actual implementations of an Instrument need to inherit from this class, then implement
            the methods marked abstract there

            Jonas Christiansen
        :param buf_storage_size: The size of the non-permanent data storage that will only contain the last n captured items,
        with n = storage_size
        """
        self.__buf_storage_size = buf_storage_size
        self.__reset_device()  # Initializes self.__buf_storage AND self.__record_storage AS WELL AS self.__measure_thread as class attributes
        self.__logging_running = False
        self.__record_data_bool = False

        self.__device_name = device_name

    def __reset_device(self):
        # Reset storage
        self.__buf_storage = FixedSizeDataQueue(self.__buf_storage_size)
        self.__record_storage = InfiniteDataStorage()

        # Reset thread
        self.__measure_thread = Thread(target=self.logging_loop, args=())

    def start_recording(self):
        """
            start recording the gathered data to the RAM without time limitations
        """
        print("Starting data recording of device '" + self.__device_name + '...')
        if not self.__record_data_bool:
            self.__record_data_bool = True
            self.__record_storage.reset()
            print("Successfully started data recording of device'" + self.__device_name + "'")
        else:
            raise Exception("The device '" + self.__device_name + "' is already recording its data!")

    def stop_recording(self):
        """
            stop recording the gathered data to the RAM
        """
        print("Stopping data recording of device '" + self.__device_name + '...')
        if self.__record_data_bool:
            self.__record_data_bool = False
            print("Successfully stopped data recording of device'" + self.__device_name + "'")

        else:
            raise Exception("The device '" + self.__device_name + "' is currently not recording any data!")

    def start_logging(self):
        """
            start gathering data by starting the logging_loop function in a thread.
        """
        print("Starting device '" + self.__device_name + '...')
        if not self.__logging_running:
            self.__logging_running = True

            # Fork a Thread
            self.__measure_thread.start()

            # Cleanup permanent data list
            self.__record_storage.reset()
            # self.__record_data_bool = True

            print("Device '" + self.__device_name + "' started.")

        else:
            raise Exception("The device '" + self.__device_name + "' was already started!")

    def stop_logging(self):
        """
            stop gathering data by joining the thread running the logging_loop function; then prepare the virtual instrument
            for the potential next start of the data gathering
        """
        print("Stopping device '" + self.__device_name + "'...")
        if self.__logging_running:

            self.__logging_running = False
            # Join the thread
            self.__measure_thread.join()

            # Create a new thread so that we can restart measure again (threads can only be started once.)
            # this is done in the way that it is included in the reset_device func
            self.__reset_device()

            print("Device '" + self.__device_name + "' stopped.")
        else:
            raise Exception("The device '" + self.__device_name + "' is already stopped / not started!")

    def logging_running(self):
        return self.__logging_running

    @abstractmethod
    def logging_loop(self):
        """
            Must be implemented in inherited child class function.
            Holds a while loop that constantly gathers getting a value
            from the physical or simulated device (e.g. via COM connection). The value gathering itself must(!) be
            implemented inside the measure_value method.

        """
        return NotImplementedError

    @abstractmethod
    def _measure_value(self, verbose=False, **kwargs):
        """
            Must be implemented in inherited child class function.
            Gather a value from the simulated or physical device and push it to the data storage.

        :param kwargs: can be used to pass needed variables between logging_loop and measure_value (e.g. object of
        established Serial Connection as call by reference)
        :param verbose: Should a string containing time stamp and value be printed to console after each data gathering?
        (True/False)
        :return: no return!
        """
        return NotImplementedError

    def get_buf_storage(self):
        # Can then be later accessed with get_buf_storage().x and get_buf_storage().y_heartrate; respectively get_buf_storage().x and get_buf_storage().y_spo2
        return types.SimpleNamespace(x=self.__buf_storage.getTimestamps(),
                                     y_heartrate=self.__buf_storage.getValues_heartrate(),
                                     y_spo2=self.__buf_storage.getValues_spo2())

    def get_record_df(self):
        return self.__record_storage.get_values_df()

    def get_buf_storage_size(self):
        return self.__buf_storage_size

    def _push_to_storage(self, datetime_of_capture, value_heartrate, value_spo2, verbose):
        """
            This protected, predefined function can be used by inheriting child classes to push the gathered value
            to the data store from inside the measure_value function.


        :param verbose: Should a string containing time stamp and value be printed to console after each data gathering?
        (True/False)
        :return: no return!
        """
        # Protected method - must be accessible for child classes but not from the outside
        # if verbose=True, the new data point will be also printed to python interpreter console
        self.__buf_storage.push(datetime_of_capture, value_heartrate, value_spo2, verbose=verbose)

        if self.__record_data_bool:
            self.__record_storage.push(datetime_of_capture, value_heartrate, value_spo2, verbose=verbose)


class SimulatedPulseoxymeter(VirtualInstrument):
    def __init__(self, buf_storage_size, frequency):
        """
            Creates an object acting as a "simulated pulseoxymeter": Reads data from database PPG Data and adds each point
            in it to the data storage, but waits some time between every data point (frequency), this way "simulating"
            a real device
        :param buf_storage_size: number of values to be kept in the live storage
        :param frequency: frequency of how often a new value should be read from the test data [Hz]
        """

        super().__init__(buf_storage_size)
        self.__cntr = 0
        self.__testdata_ppg = parseFunctions.parse_random_ppg_from_test_data()
        self.__inv_freq = 1.0 / float(frequency)  # Inverse of Frequency is time between each data point..

    def logging_loop(self):

        while self.logging_running():
            self._measure_value()
            time.sleep(self.__inv_freq)

    def _measure_value(self, verbose=False, **kwargs):

        # if verbose=True, the new data point will be also printed to python interpreter console

        # If we have read all values from the test data, continue with the first value from the test data again, ensuring permanent simulation
        if self.__cntr == len(self.__testdata_ppg):
            self.__cntr = 0

        # Put the value to the data storage: PPG signal from the test data, SpO2 is some random placeholder function...
        self._push_to_storage(datetime.datetime.now(), self.__testdata_ppg[self.__cntr],
                              self.__cntr * np.sin(self.__cntr),
                              verbose=verbose)  # Only using self.__cntr * sin(self.__cnt) as placeholder for Spo2 Value - to be replaced by actual values
        self.__cntr += 1


class RealPulseoxymeterTest(VirtualInstrument):
    def __init__(self, buf_storage_size, frequency, SERIAL_PORT='COM5'):
        """
            Class that incorporates plotting real sensor data.
            Currently only plotting the values from R/IR LED.
            Untested!
            Might be modified to use the real data coming from the RSCD algorithm.
        :param buf_storage_size: number of values to be kept in the live storage
        :param frequency: frequency of how often a new value should be read from the test data [Hz]
        :param SERIAL_PORT: Change this to your specific Arduino Port, e.g. /dev/ttyACM0
        """
        super().__init__(buf_storage_size)

        # Sensor Data
        SERIAL_RATE = 115200

        # Initialize Serial Port and set Interval between each data gathering
        self.__ser = serial.Serial(SERIAL_PORT, SERIAL_RATE)
        self.__inv_freq = 1.0 / float(frequency)  # Inverse of Frequency is time between each data point..

        # Resetting the all_data - we need this for synchronous access to all_data in logging_loop as well as measure_data
        global all_data
        lock.acquire()
        all_data = []
        lock.release()

    def logging_loop(self):

        # ===================================================================================== Daten aufnehmen

        global all_data
        __calc_thread = Thread(target=self._measure_value(), args=())
        __calc_thread.start()

        datetime_start = datetime.datetime.now()

        cntr = 0 # Needed to leave out the first 250 values, see below
        while self.logging_running():
            curr_line = self.__ser.readline() # Read from sensor
            cntr += 1

            if cntr >= 250: # Leaves out the first 5s as there will only be "trash data"
                try:
                    curr_data = curr_line.decode("utf-8").split(',')
                except:
                    continue
                if cntr == 250:
                    # First value to be kept - store value of time from sensor to later calculate the actual time points from differences since start
                    t0 = float(curr_data[0]) / 1000000.0
                t = datetime_start + datetime.timedelta(seconds=((float(curr_data[0]) / 1000000.0) - t0))
                ir = float(curr_data[1])
                red = float(curr_data[2])

                # Add to allData - using lock/unlock to prevent synchronization issues
                lock.acquire()
                all_data.append([t, ir, red])
                lock.release()

            time.sleep(self.__inv_freq) # 50 Hz Abtastrate...

        __calc_thread.join()

    def _measure_value(self, verbose=False, **kwargs):
        """
            Periodically checks for new data points and, if any, adds them all to the data storage
            Might be changed to incorporate the RSCD algorithm...

        """
        global all_data
        while self.logging_running():
            # Alle neuen Daten hinzufügen, dann kurz warten, dann wieder...
            new_data = []
            lock.acquire()
            while len(all_data) > 0:
                # Hier können wir uns soviele Werte wie wir brauchen aus dem Speicher ziehen, mit dem wir dann nach dem unlock arbeiten können. Müssen herausgenommene natürlich entfernen...
                new_data.append(all_data.pop(0))
            lock.release()
            for element in new_data:
                [t, ir, red] = element
                self._push_to_storage(t, ir, red, verbose=verbose)  # Eigentlich (t, ppgwert, spo2wet)
            time.sleep(0.5) # damit wir nicht ewig oben loopen wenn noch gar keine werte da sind....
