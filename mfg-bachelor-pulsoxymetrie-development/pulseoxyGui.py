import datetime
import docx2pdf
from docx.shared import Cm
import matplotlib.pyplot as plt
import sys
import ctypes
import os
import PyQt5
import numpy as np
from docxtpl import DocxTemplate, InlineImage

# 1. Import `QApplication` and all the required widgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog, QFormLayout, QLineEdit, QLabel, QWidget
from matplotlib.backends.qt_compat import QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)

from matplotlib.figure import Figure


def createPulsoxyGui(virtual_instrument_object):
    """
    Creates the User Interface using the given object of a Type that inherits from Virtual Interface, and shows this GUI to the user.
    :param virtual_instrument_object: object of a Type that inherits from Virtual Interface
    """
    # 2. Create an instance of QApplication
    qapp = QApplication(sys.argv)

    app = DisplayPulsoxyValuesApplicationWindow(device_heartrate_and_spo2=virtual_instrument_object)
    app.setWindowTitle('Pulsoxy Monitor @ TU Berlin MFG/Bachelor Project # WS 2020/21')

    app_icon = QIcon("assets/img/desktop-256.png")

    if os.name == 'nt':  # Windows
        # Workaround for MS Windows so that icon shows up in tray
        myappid = 'tuberlin.mfg2021pulsoxymetrie'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    elif os.name == 'posix':  # unix-oid
        if sys.platform == 'darwin':  # macOS
            pass
            # TODO für macOS ggf herausfinden wie ich das Icon auch im Dock ändern kann...

    app.setWindowIcon(app_icon)

    # 4. Show your application's GUI
    app.show()

    # 5. Run your application's event loop (or main loop)
    qapp.exec_()

    # If user terminated the GUI, we also need to stop getting data from device
    qapp.device_heartrate_and_spo2.stop_logging()


class SettingsWindow(QWidget):
    """
    This "window" will display input fields for first- and last name of patient.

    Recently saved setting will appear in the corresponding fields, if there was a save before.

    Saving is done by closing the window (closeEvent is called, see this function below)
    and selecting "Yes" when asked if saving should be done.
    Thus, no save button is needed.

    Values are stored within the users registry (windows), property list files (macOS) or depending on distribution
    mainly in INI files (Unix) - see https://doc.qt.io/qt-5/qsettings.html
    The path is specified in the DisplayPulsoxyValuesApplicationWindow Class in the __init__ function in self.settings

    """

    def __init__(self, settingsRef):
        # settingsRef: a reference to the QtCore.QSettings object from main window
        self.settings = settingsRef
        super().__init__()
        boxLayout = QFormLayout()
        self.label = QLabel("Einstellungen")
        self.setWindowTitle('Einstellungen')

        self.vorname_gui_field = QLineEdit(self.settings.value('vorname'))
        self.nachname_gui_field = QLineEdit(self.settings.value('nachname'))

        boxLayout.addRow(QLabel("Ihr Vorname:"), self.vorname_gui_field)
        boxLayout.addRow(QLabel("Ihr Nachname:"), self.nachname_gui_field)

        self.setLayout(boxLayout)

    def save_settings(self):
        print("Saving...")
        self.settings.setValue('vorname', self.vorname_gui_field.text())
        self.settings.setValue('nachname', self.nachname_gui_field.text())
        print("Saved")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Änderungen speichern?',
                                     'Möchten Sie Ihre Änderungen speichern?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            self.save_settings()
            print('Window closed WITH SAVE')
        else:
            event.accept()
            print('Window closed WITHOUT SAVE')


class DisplayPulsoxyValuesApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, device_heartrate_and_spo2):
        """
        Class that represents the Pulseoxy Main Window.
        :param device_heartrate_and_spo2: A VirtualInstrument Object, e.g. a SimulatedPulseoxymeter
        """
        super().__init__()
        self.settings = QtCore.QSettings('TUBerlin_Student_397742', 'Pulsoxygui') # Registry path for storing properties like first- and last name of patient
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        self.device_heartrate_and_spo2 = device_heartrate_and_spo2  # reference to digital instrument measurement data store
        layout = QtWidgets.QGridLayout(self._main)

        # Menu Bar
        bar = self.menuBar()
        file = bar.addMenu("Extras")
        settings = file.addAction("Einstellungen")
        settings.triggered.connect(self.openSettingsWindow)

        # Adding widgets using the form
        # addWidget(name, zeile, spalte, rowSpan, colSpan)

        # TUB Logo and Headline
        tu_logo = QLabel(self)
        pixmap = PyQt5.QtGui.QPixmap('assets/img/TU_Logo_lang_RGB_rot.svg').scaledToHeight(80)
        tu_logo.setPixmap(pixmap)
        layout.addWidget(tu_logo, 0, 0, 1, 2)

        headl = QLabel(
            '<center><h1>MFG/Project Bachelor - Pulse Oxymetry</h1>\n<h2>Winter Term 2020/21</h2></center>')
        layout.addWidget(headl, 0, 2, 1, 10)

        # Initialize three canvas' where we will put the graphs later

        spo2_live_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        layout.addWidget(spo2_live_canvas, 1, 0, 1, 6)

        heartbeat_live_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        layout.addWidget(heartbeat_live_canvas, 2, 0, 1, 6)

        dynamic_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        layout.addWidget(dynamic_canvas, 1, 6, 2, 6)


        # Buttons for Start / Stop / Save Gathered Data
        # Button for Stop Data Gathering and Storing Data must be disabled at the start as we cannot stop gathering or store data if we did not have started gathering

        self.start_messung_button = QtWidgets.QPushButton("Neue Messung st&arten", self)
        self.start_messung_button.setIcon(QIcon("assets/img/play-button.png"))
        self.start_messung_button.setEnabled(True)
        layout.addWidget(self.start_messung_button, 3, 6, 1, 2)
        self.start_messung_button.clicked.connect(self.startMessungButtonClick)

        self.stop_messung_button = QtWidgets.QPushButton("Messung st&oppen", self)
        self.stop_messung_button.setIcon(QIcon("assets/img/stop.png"))
        self.stop_messung_button.setEnabled(False)
        layout.addWidget(self.stop_messung_button, 3, 8, 1, 2)
        self.stop_messung_button.clicked.connect(self.stopMessungButtonClick)

        self.show_messung_button = QtWidgets.QPushButton("Messung speicher&n", self)
        self.show_messung_button.setIcon(QIcon("assets/img/floppy-disk.png"))
        self.show_messung_button.setEnabled(False)
        layout.addWidget(self.show_messung_button, 3, 10, 1, 2)
        self.show_messung_button.clicked.connect(self.saveMessungButtonClick)


        # ============================ LIVE PLOTS: ============================

        # Need to start a timer for each plot so that they will be updated regularly with the new data
        # The timer is set to periodically call a function that will redraw the plots.
        # Furthermore, before drawing the plot the first time, we need to create the plot/axis

        # INITIALIZE LIVE PLOT FOR SPO2
        self._spo2_live_ax = spo2_live_canvas.figure.subplots()
        self._timer_spo2_live_canvas = spo2_live_canvas.new_timer(
            50, [(self._update_spo2_live_canvas, (), {})])
        self._timer_spo2_live_canvas.start()

        # INITIALIZE LIVE PLOT FOR PPG
        self._heartbeat_live_ax = heartbeat_live_canvas.figure.subplots()
        self._timer_heartbeat_live_canvas = heartbeat_live_canvas.new_timer(
            50, [(self._update_heartbeat_live_canvas, (), {})])
        self._timer_heartbeat_live_canvas.start()

        # INITIALIZE LIVE PLOT FOR ALL MEASURED DATA SINCE START OF DATA GATHERING (Both SpO2 and PPG in one diagram)
        self._measure_ax = dynamic_canvas.figure.subplots()
        self._measure_ax2 = self._measure_ax.twinx()  # instantiate a second axes that shares the same x-axis
        self._timer = dynamic_canvas.new_timer(
            50, [(self._update_measure_canvas, (), {})])
        self._timer.start()

        # =====================================================================



    def openSettingsWindow(self):
        """
            Display the settings window.
        """
        print("!Hi!")
        self.settingsWindow = SettingsWindow(self.settings)
        self.settingsWindow.show()

    def closeEvent(self, event):
        """
            Event that is called when user clicks on the "X" in the window bar. Asks the user if she is sure about closing the window.
        """
        reply = QMessageBox.question(self, 'Programm beenden?',
                                     'Möchten Sie das Programm wirklich beenden? Ggfs. laufende Messungen werden beendet und Daten der letzten Messung gehen dann verloren. Bitte vorher speichern, falls nötig. ',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Messung stoppen:
            if self.device_heartrate_and_spo2.logging_running():
                self.device_heartrate_and_spo2.stop_logging()  # This will throw an error in console, but works as intended.
            event.accept()
            print('Window closed')
        else:
            event.ignore()

    def startMessungButtonClick(self):
        """
            Event that is called when "Start Messung" is clicked.
            Recording must be started and the "Stop Messung" button must be enabled, other buttons disabled
        """
        self.device_heartrate_and_spo2.start_recording()
        self.start_messung_button.setEnabled(False)
        self.show_messung_button.setEnabled(False)
        self.stop_messung_button.setEnabled(True)

    def stopMessungButtonClick(self):
        """
            Event for stopping gathering data
        """
        self.device_heartrate_and_spo2.stop_recording()
        self.start_messung_button.setEnabled(True)
        self.show_messung_button.setEnabled(True)
        self.stop_messung_button.setEnabled(False)

    def saveMessungButtonClick(self):
        """
            Event for saving gathered data.
            Will display a window for selecting a folder and file name, then will create a CSV or PDF (based on selection) with the selected filename and -path
        :return:
        """
        # If First- and/or Last name of patient was never set or is empty (""), notify user and abort
        if (self.settings.value('vorname') == None) or (self.settings.value('nachname') == None) or (
                self.settings.value('vorname') == "") or (self.settings.value('nachname') == ""):
            QMessageBox.about(self, "Achtung!",
                              "Ihr Vor- oder Nachname sind noch nicht eingespeichert. Bitte machen Sie dies über Menü > Einstellungen, bevor Sie fortfahren. Vielen Dank!")
            return

        # Prepare and show file dialog, suggest current date and time as file name
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        datetimestr = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        fileName, fileType = QFileDialog.getSaveFileName(self, "Messergebnisse speichern",
                                                         "ppg-spo2-export-" + datetimestr,
                                                         "CSV-Datei (*.csv);;PDF-Report (*.pdf)", options=options)
        if fileName:
            print(fileName)
            print(fileType)

            if (fileType == "CSV-Datei (*.csv)"): # Export as CSV selected
                filename_full = fileName + ".csv"
                self.device_heartrate_and_spo2.get_record_df().to_csv(filename_full)

            elif (fileType == "PDF-Report (*.pdf)"): # Export as PDF selected

                df = self.device_heartrate_and_spo2.get_record_df()

                # ===== PPG IMAGE CREATION =====
                fig = plt.figure()
                ax = plt.subplot(111)
                ax.plot(df["timestamp"], df["value_heartrate"])

                # ax.set_title("PPG - Zeitverlauf", fontweight='bold', fontsize=16)
                ax.set_xlabel("Zeit", loc="right")
                ax.set_ylabel("y")
                # to prevent visual bugs : Explicitly set Position of Legend and reduce number of xticks
                ax.legend(loc='upper right')

                # Calculate the values of the xticklabels: 4 time points: start time, end time as well as two in between. difference between those is 1/3 of full difference between start and end
                min_date = df["timestamp"].min()
                max_date = df["timestamp"].max()
                ternil1 = min_date + (max_date - min_date) / 3.0
                ternil2 = max_date - (max_date - min_date) / 3.0
                l1 = min_date.strftime("%d.%m.%Y\n%H:%M:%S")
                l2 = max_date.strftime("%d.%m.%Y\n%H:%M:%S")
                l3 = ternil1.strftime("%d.%m.%Y\n%H:%M:%S")
                l4 = ternil2.strftime("%d.%m.%Y\n%H:%M:%S")
                ax.set_xticks([min_date, ternil1, ternil2, max_date])
                ax.set_xticklabels([l1, l2, l3, l4], rotation=45)  # ,rotation=90)

                filename_plot1 = fileName + "_tempfile_ppg.png"
                fig.savefig(filename_plot1, dpi=600, papertype="a4", bbox_inches="tight") # Store plot temporary

                # ===== SpO2 IMAGE CREATION =====

                fig = plt.figure()
                ax = plt.subplot(111)
                ax.plot(df["timestamp"], df["value_spo2"])

                # ax.set_title("PPG - Zeitverlauf", fontweight='bold', fontsize=16)
                ax.set_xlabel("Zeit", loc="right")
                ax.set_ylabel("y")
                # to prevent visual bugs : Explicitly set Position of Legend and reduce number of xticks
                ax.legend(loc='upper right')

                # Calculate the values of the xticklabels: 4 time points: start time, end time as well as two in between. difference between those is 1/3 of full difference between start and end
                min_date = df["timestamp"].min()
                max_date = df["timestamp"].max()
                ternil1 = min_date + (max_date - min_date) / 3.0
                ternil2 = max_date - (max_date - min_date) / 3.0
                l1 = min_date.strftime("%d.%m.%Y\n%H:%M:%S")
                l2 = max_date.strftime("%d.%m.%Y\n%H:%M:%S")
                l3 = ternil1.strftime("%d.%m.%Y\n%H:%M:%S")
                l4 = ternil2.strftime("%d.%m.%Y\n%H:%M:%S")
                ax.set_xticks([min_date, ternil1, ternil2, max_date])
                ax.set_xticklabels([l1, l2, l3, l4], rotation=45)  # ,rotation=90)

                filename_plot2 = fileName + "_tempfile_spo2.png"
                fig.savefig(filename_plot2, dpi=600, papertype="a4", bbox_inches="tight")

                # ===== PDF CREATION =====

                # A) create the docx, prepare contents and fill them to the docx template, then save
                tpl = DocxTemplate("assets/templates/report.docx")
                json_contents = {
                    "ppgImage": InlineImage(tpl, filename_plot1, width=Cm(9)),
                    "spo2Image": InlineImage(tpl, filename_plot2, width=Cm(9)),
                    "patient_vorname": self.settings.value('vorname'),
                    "patient_nachname": self.settings.value('nachname'),
                    "creation_date": datetime.datetime.now().strftime("%d. %B %Y %H:%M")
                }
                tpl.render(json_contents)
                filename_full = fileName + ".docx"
                tpl.save(filename_full)

                # B) convert to pdf
                docx2pdf.convert(filename_full)

                # Remove temporarily created files
                os.remove(filename_full)
                os.remove(filename_plot1)
                os.remove(filename_plot2)

            QMessageBox.about(self, "Erfolgreich gespeichert", "Der Report wurde erfolgreich gesichert")
            # (TODO)Error werfen falls fehler?

    def _update_measure_canvas(self):
        """
            Function to update the plot that shows all gathered data since measure start (PPG and Spo2 together in one plot)
            The axis self._dynamic_ax and self._dynamix_ax2 was initialized in the DisplayPulsoxyValuesApplicationWindow class initialization
            Moreover, the periodic call of this function is done by the timer set in the DisplayPulsoxyValuesApplicationWindow class initialization
        """

        self._measure_ax.clear()
        self._measure_ax2.clear()

        df = self.device_heartrate_and_spo2.get_record_df()
        if not df.empty:
            plt = self.device_heartrate_and_spo2.get_record_df().plot(kind='line', x='timestamp', y='value_heartrate',
                                                                      ax=self._measure_ax, color='b')

            plt2 = self.device_heartrate_and_spo2.get_record_df().plot(kind='line', x='timestamp', y='value_spo2',
                                                                       ax=self._measure_ax2, color='r')

            self._measure_ax.set_title("PPG - Zeitverlauf", fontweight='bold', fontsize=16)
            self._measure_ax.set_xlabel("Zeit", loc="right")
            self._measure_ax.set_ylabel("Herzrate (PPG)")
            self._measure_ax2.set_ylabel("Sauerstoffsättigung (SpO2)")
            # to prevent visual bugs : Explicitly set Position of Legend and reduce number of xticks
            self._measure_ax.legend(loc='upper right')

            # Calculate the values of the xticklabels: 4 time points: start time, end time as well as two in between. difference between those is 1/3 of full difference between start and end
            min_date = df["timestamp"].min()
            max_date = df["timestamp"].max()
            ternil1 = min_date + (max_date - min_date) / 3.0
            ternil2 = max_date - (max_date - min_date) / 3.0
            l1 = min_date.strftime("%d.%m.%Y\n%H:%M:%S")
            l2 = max_date.strftime("%d.%m.%Y\n%H:%M:%S")
            l3 = ternil1.strftime("%d.%m.%Y\n%H:%M:%S")
            l4 = ternil2.strftime("%d.%m.%Y\n%H:%M:%S")
            self._measure_ax.set_xticks([min_date, ternil1, ternil2, max_date])
            self._measure_ax.set_xticklabels([l1, l2, l3, l4], rotation=45)  # ,rotation=90)


        # Now finally draw
        self._measure_ax.figure.canvas.draw()

    def _update_heartbeat_live_canvas(self):
        """
            Function to update the plot that shows the ppg live signal
            The axis self._heartbeat_live_ax was initialized in the DisplayPulsoxyValuesApplicationWindow class initialization
            Moreover, the periodic call of this function is done by the timer set in the DisplayPulsoxyValuesApplicationWindow class initialization
        """
        self._heartbeat_live_ax.clear()

        self._heartbeat_live_ax.plot(self.device_heartrate_and_spo2.get_buf_storage().x,
                                     self.device_heartrate_and_spo2.get_buf_storage().y_heartrate)

        self._heartbeat_live_ax.set_title("PPG - Live", fontweight='bold', fontsize=16)
        self._heartbeat_live_ax.set_xlabel("Zeit", loc="right")
        self._heartbeat_live_ax.set_ylabel("y")
        self._heartbeat_live_ax.set(xticklabels=[])
        self._heartbeat_live_ax.figure.canvas.draw()

    def _update_spo2_live_canvas(self):
        """
            Function to update the plot that shows the spo2 live signal
            The axis self._spo2_live_ax was initialized in the DisplayPulsoxyValuesApplicationWindow class initialization
            Moreover, the periodic call of this function is done by the timer set in the DisplayPulsoxyValuesApplicationWindow class initialization
        """
        self._spo2_live_ax.clear()

        self._spo2_live_ax.plot(self.device_heartrate_and_spo2.get_buf_storage().x,
                                self.device_heartrate_and_spo2.get_buf_storage().y_spo2)

        self._spo2_live_ax.set_title("SpO2 - Live", fontweight='bold', fontsize=16)
        self._spo2_live_ax.set_xlabel("Zeit", loc="right")
        self._spo2_live_ax.set_ylabel("y")
        self._spo2_live_ax.set(xticklabels=[])
        self._spo2_live_ax.figure.canvas.draw()
