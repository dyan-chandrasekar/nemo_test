import numpy as np
import serial
import struct
import sys
import time
import threading
import os

import pyqtgraph as pg 
import msgpack as mp
import msgpack_numpy as mpn

from PyQt5.QtWidgets import *
from pyqtgraph import *
from guiDesign import Ui_MainWindow
from sys import stdout
from datetime import datetime

from PyQt5 import QtWidgets 
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import serial.tools.list_ports

class WorkerSignals(QObject):
    finished = pyqtSignal()
    result = pyqtSignal()
    progress = pyqtSignal(list)
    

""""threading class"""

class Worker(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            pass
        else:
            pass
        finally:
            self.signals.finished.emit()  # Done


"""Main Program"""

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, serialport, serialrate=115200, *args, **kwargs):
        
        # Initialise serial payload
        self.plSz = 0
        self.prevval=0
        self.prevval1=0
        self.payload = bytearray()

        ports = serial.tools.list_ports.comports()
        serial_ports = []
        description_list = []
        hardware_list = []
        for port, desc, hwid in sorted(ports):
            serial_ports.append(port)
            description_list.append(desc)
            hardware_list.append(hwid)
            print("{}: {} [{}]".format(port, desc, hwid))
        inx = hardware_list.index('USB VID:PID=16C0:0483 SER=10597030 LOCATION=1-1')
        serialport = serial_ports[inx]
        


        self.serialport = serialport
        self.ser_port = serial.Serial(serialport, serialrate)
    
        stdout.write("Initializing serial program\n")
        self.threadpool = QThreadPool()
        print("Multi-threading with maximum %d threads" % self.threadpool.maxThreadCount())

        #superconstructor

        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.pressEnter)


        self.closeButton.clicked.connect(self.close_app)
        self.closeButton.setStyleSheet("background-color : red")



        #initializing the plot

        self.scene = QGraphicsScene()
        self.myplot.setScene(self.scene)
        self.plotWdgt= pg.PlotWidget()
        self.plot_item = self.plotWdgt.plot(np.zeros(2500))
        self.proxy_widget = self.scene.addWidget(self.plotWdgt)  
        self.plotWdgt.setGeometry(0, 0, 798, 438) 
        

        # proxy_widget.setData
        self.myplot.hide()

        self.display_start = False
        self.saveCMAP = False

        #hide plot screen and params

        self.pulAmpli.hide()
        self.pulWid.hide()
        self.pulAmp.hide()
        self.pulWidth.hide()
        self.dte_2.hide()
        self.Dte_2.hide()
        self.tme_2.hide()
        self.Tme_2.hide()
        # self.label_4.hide()

    
        #DATE and TIME

        timer = QTimer(self)
        timer.timeout.connect(self.displayTime)
        timer.start(1000)

        self.click_counter = 0

    def close_app(self, serialport ,serialrate = 115200):
        sys.exit(app.exec_())
        self.ser_port = serial.Serial(serialport, serialrate).close()
    
    #read serial port

    def serial_read(self):
        """returns bool for valid read, also returns the data read"""
         # FORMAT
         # | 255 | 255 | no. of bytes | payload | checksum |

        if (self.ser_port.read() == b'\xff') and (self.ser_port.read() == b'\xff'):
            
            chksum = 255 + 255
            self.plSz = self.ser_port.read()[0]
            chksum += self.plSz
            self.payload = self.ser_port.read(self.plSz - 1)
            chksum += sum(self.payload)
            chksum = bytes([chksum % 256])
            _chksum = self.ser_port.read()
            return _chksum == chksum

        return False

    # diplay date and time 

    def displayTime(self):
        currTime= QTime.currentTime()
        displayText = currTime.toString('hh:mm:ss')
        currDate = QDate.currentDate()
        displayText2 = currDate.toString('dd/MM/yyyy')
        self.Tme.setText(displayText)
        self.Dte.setText(displayText2)
        self.Tme_2.setText(displayText)
        self.Dte_2.setText(displayText2)


    #to initialize UI after pressing enter and pop up the qgraphics plot 

    def pressEnter(self):

    
        if self.patient_name.text() == "" and self.hospital_number.text() == "":

            error = QMessageBox()
            error.setWindowTitle("CANT INITIALIZE")
            error.setIcon(QMessageBox.Warning)
            error.setText("CANT INITIALIZE")
            x = error.exec_()

        else:
           
            self.initUI()
            self.after_Enter()
            self.hospital_number.text()
            print(self.hospital_number.text())
            self.patient_name.text()
            print(self.patient_name.text())
            self.pulWidth.setText("500ms")
            self.ifEnter()
    
    # def Key_hosp(self):

    #     k = AlphaNeumericVirtualKeyboard(self.hospital_number)
    #     k.display(self.hospital_number)
       
    # def Key_pat(self):
    #     g = AlphaNeumericVirtualKeyboard(self.patient_name )
    #     g.display(self.patient_name)

    #worker 

    def initUI(self): 

        worker = Worker(self.run_program)  # Any other args, kwargs are passed to the run function
        worker.signals.progress.connect(self.plot)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.result.connect(self.thread_complete)
        self.threadpool.start(worker)
        self.show()


    def thread_complete(self):
        print("THREAD COMPLETE!")

    #create a directory to save cmap data 

    def ifEnter(self):
        directory = self.hospital_number.text()
        parent_dir = r"F:\CMC\Neuro Stimulator Project\data"
        self.folder_name = os.path.join(parent_dir, directory)
        try:
            os.mkdir(self.folder_name)
        except:
            pass
        # os.listdir(self.folder_name) 
        fol_list = len(os.listdir(self.folder_name))
        self.click_counter = fol_list

        # print(fol_list)
        print("Directory '% s' created" % directory)
    
    #to pop up the qgraphics plot after entering patient details and initilaizing the UI

    def after_Enter(self):
        self.label.hide()
        self.label_2.hide()
        self.hospital_number.hide()
        self.patient_name.hide()
        self.pushButton.hide()
        
        self.dte.hide()
        self.Dte.hide()
        self.tme.hide()
        self.Tme.hide()
        self.line.hide()
        self.line_2.hide()
        self.line_3.hide()
        self.line_4.hide()
        # self.line_5.hide()

        self.dte_2.show()
        self.dte_2.setStyleSheet("background-color : white")
        self.Dte_2.show()
        self.Dte_2.setStyleSheet("background-color : white")
        self.tme_2.show()
        self.tme_2.setStyleSheet("background-color : white")
        self.Tme_2.show()
        self.Tme_2.setStyleSheet("background-color : white")

        self.pulAmpli.show()
        self.pulAmpli.setStyleSheet("background-color : white")
        self.pulWid.show()
        self.pulWid.setStyleSheet("background-color : white")
        self.pulAmp.show()
        self.pulAmp.setStyleSheet("background-color : white")
        self.pulWidth.show()
        self.pulWidth.setStyleSheet("background-color : white")
        # self.label_4.show()
        # self.label_4.setStyleSheet("color : black")
        # self.label_4.setStyleSheet("background-color : white")
        self.batt_perc.setStyleSheet("background-color : white")
        self.doneSig.show()
        self.myplot.show()
        


    #save_CMAP data

    def CMAPdata(self):
        if self.saveCMAP:
            print(self.click_counter)
            # try:
            _temp_pth = os.path.join(self.folder_name, "CMAPdata" + str(self.click_counter) + ".msgpack" )
            
            #open_file
            self.cmap_file = open(_temp_pth, 'wb')

            #hospital number in file 
            c_packed = mp.packb(self.hospital_number.text(), default=mpn.encode)
            self.cmap_file.write(c_packed)

            #Patient name in file 
            c_packed = mp.packb(self.patient_name.text(), default=mpn.encode)
            self.cmap_file.write(c_packed)

            #date time in file
            self.nw= datetime.now()
            self.nw1= str(self.nw)
            c_packed = mp.packb(self.nw1, default=mpn.encode)
            self.cmap_file.write(c_packed)

            #CMAP data in file
            c_packed = mp.packb(self.cmap_data, default=mpn.encode)
            self.cmap_file.write(c_packed)
            self.cmap_file.close()
            self.saveCMAP = False


    #pulse sent signal

    def pulseSent(self):

        if self.display_start:
            var= 0
            self.doneSig.setFont(QFont('TIMES', 10))
            time.sleep(4)
            self.doneSig.setText("")
            self.display_start = False
        pass
    

    #receive and unpack data 

    def run_program(self, progress_callback):
        self.emg=[]
        self.ampbtn=[]
        self.stimbtn=[]
        self.CMAP=[]
        self.batVolt=[]
        _tempvar = 0
        counter = 0
        

        
        while True:
            if self.serial_read():
                ampbtn = self.payload[0:1]
                self.ampbtn.append(ampbtn)
                stimbtn = self.payload[1:2]
                self.stimbtn.append(stimbtn)
                emgval = struct.unpack("f", self.payload[2:6])    # EMG values
                self.emg.append(emgval[0])

                if len(self.emg) > 2500:
                    self.emg = self.emg[1:]

                batval = list(struct.unpack("f", self.payload[6:]))  
                bat_perc = (batval[0] / 2.6) * 100
                self.batVolt = round(bat_perc)
                print(self.batVolt)
                self.batt_perc.setText("BATTERY :" + " " + str(self.batVolt) + "%")

              
                counter +=1

                # if bat_perc <= 20:
                    # self.batt_perc.setStyleSheet("color : red")
                
                if stimbtn==b'\x01':                          #PULSE SENT
                    _tempvar = counter
                    self.click_counter+=1       
                                              
                    if stimbtn!=self.prevval1:
                        self.display_start = True
                        t1 = threading.Thread(target=self.pulseSent)
                        t1.start()
                        # t1.join()
                        self.doneSig.setText("PULSE SENT at" + " " + str(var) + "mA")
                        self.doneSig.setStyleSheet("color : green")


                if ampbtn==b'\x00':                                       #for 0 mA
                    var = 0
                    if ampbtn!=self.prevval:
                        # print ("AMPLITUDE SET TO 0 mA") 
                        self.pulAmp.setText("0mA")   
                        
                        
                if ampbtn==b'\x01':                                       #for 0.5 mA
                    var =0.5
                    if ampbtn!=self.prevval:
                        # print ("AMPLITUDE SET TO 0.5 mA")
                        self.pulAmp.setText("0.5mA")
                       
                   
                        
                if ampbtn==b'\x02':                                        #for 1 mA
                    var =1 
                    if ampbtn!=self.prevval:
                        # print ("AMPLITUDE SET TO 1 mA")
                        self.pulAmp.setText("1mA")
                       
                        
                        
                if ampbtn==b'\x03':                                        #for 2 mA
                    var =2
                    if ampbtn!=self.prevval:
                        # print ("AMPLITUDE SET TO 2 mA")
                        self.pulAmp.setText("2mA")
                 
             

                if len(self.emg[_tempvar:])>2500 and _tempvar is not 0:
                    CMAP=self.emg[_tempvar-500:_tempvar+2000]
                    self.cmap_data = CMAP
                    progress_callback.emit(CMAP)
                    _tempvar = 0
                    
                if stimbtn==b'\x01':    
                    self.saveCMAP = True
                    t2 = threading.Thread(target=self.CMAPdata)
                    t2.start()
                    t2.join()               


    #update the plot for every stimulation 

    @pyqtSlot(list)
    def plot(self, CMAP):
        self.plot_item.clear()
        self.x = np.linspace(0, 10, 2500)
        CMAP = np.array(CMAP)
        self.y_val = CMAP
        CMAP1 = CMAP.reshape(len(CMAP))
        print (CMAP1)
        self.plotWdgt.clear()
        self.plot_item = self.plotWdgt.plot(CMAP1)
        
        self.start_ymin = np.min(CMAP1)
        self.start_ymax = np.max(CMAP1)
        amptd = self.start_ymax - self.start_ymin
        self.Amplitude.setText("AMPLITUDE"+ " "+":"+ " "+str(amptd))
        self.Amplitude.setStyleSheet("color : green")
        
        strtPulse_x = [500,500]
        endPulse_x = [1000,1000]
        endPulse_y = [self.start_ymin,self.start_ymax]
        self.plot_item = self.plotWdgt.plot(strtPulse_x,endPulse_y,pen='y', symbol='x', symbolPen='y', symbolBrush=0.5, name='yellow')
        # self.plot_item = self.plotWdgt.plot(endPulse_x, endPulse_y,pen='y', symbol='x', symbolPen='y', symbolBrush=0.5, name='yellow')
        
        self.plotWdgt.setLabel('left', 'AMPLITUDE (mV)')
        self.plotWdgt.setLabel('bottom', 'TIME (mS)')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(serialport="COM3",serialrate= 115200)
    # w.resize(800, 480)
    w.show()
    # w.showFullScreen()
    sys.exit(app.exec_())
    # myport = SerialPort("COM6", 115200)