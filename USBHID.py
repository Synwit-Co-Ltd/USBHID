#! python3
import os
import sys
import collections
import configparser

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtChart import QChart, QChartView, QLineSeries

os.environ['PATH'] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ['PATH']
from interface import USB_BACKEND, HID_BACKEND

import codec
import waves


ADC_CHNL_N = 8  # ADC Channel Count

DAC_CHNL_N = 4  # DAC Channel Count


'''
from USBHID_UI import Ui_USBHID
class USBHID(QWidget, Ui_USBHID):
    def __init__(self, parent=None):
        super(USBHID, self).__init__(parent)
        
        self.setupUi(self)
'''
class USBHID(QWidget):
    def __init__(self, parent=None):
        super(USBHID, self).__init__(parent)
        
        uic.loadUi('USBHID.ui', self)

        self.devices = self.get_devices()
        self.cmbPort.addItems(self.devices.keys())

        self.cmbCode.addItems(codec.Codecs.keys())

        self.cmbWave.addItems(waves.Waves.keys())

        self.initSetting()

        self.initQwtPlot()

        self.tmrRcv = QtCore.QTimer()
        self.tmrRcv.setInterval(10)
        self.tmrRcv.timeout.connect(self.on_tmrRcv_timeout)
        self.tmrRcv.start()

        self.tmrRcv_Cnt = 0
    
    def get_devices(self):
        hids = HID_BACKEND.get_all_connected_interfaces()
        hids = [(f'HID: {dev.info()}', dev) for dev in hids]
        usbs = USB_BACKEND.get_all_connected_interfaces()
        usbs = [(f'USB: {dev.info()}', dev) for dev in usbs]

        return collections.OrderedDict(hids + usbs)

    def initSetting(self):
        if not os.path.exists('setting.ini'):
            open('setting.ini', 'w', encoding='utf-8')
        
        self.conf = configparser.ConfigParser()
        self.conf.read('setting.ini', encoding='utf-8')
        
        if not self.conf.has_section('USB'):
            self.conf.add_section('USB')
            self.conf.set('USB', 'port', '')
            self.conf.set('USB', 'codec', 'ADC')

            self.conf.add_section('ADC')
            self.conf.set('ADC', 'chnl', '0x01')

            self.conf.add_section('DAC')
            self.conf.set('DAC', 'chnl', '1')
            self.conf.set('DAC', 'wave', '')

        index = self.cmbPort.findText(self.conf.get('USB', 'port'))
        self.cmbPort.setCurrentIndex(index if index != -1 else 0)

        self.cmbCode.setCurrentIndex(self.cmbCode.findText(self.conf.get('USB', 'codec')))

        self.cmbWave.setCurrentIndex(self.cmbWave.findText(self.conf.get('DAC', 'wave')))

        try:
            self.adcChnl = int(self.conf.get('ADC', 'chnl'), 16)
        except:
            self.adcChnl = 0x01

        for i in range(ADC_CHNL_N):
            if self.adcChnl & (1 << i):
                eval(f'self.chkCH{i}').setCheckState(Qt.Checked)

        try:
            self.dacChnl = int(self.conf.get('DAC', 'chnl'))
        except:
            self.dacChnl = 0

        eval(f'self.rdoCH{self.dacChnl}').setChecked(True)

    def initQwtPlot(self):
        self.PlotData  = [[0                    for j in range(1000)] for i in range(ADC_CHNL_N)]
        self.PlotPoint = [[QtCore.QPointF(j, 0) for j in range(1000)] for i in range(ADC_CHNL_N)]

        self.PlotChart = QChart()

        self.ChartView = QChartView(self.PlotChart)
        self.ChartView.setVisible(False)
        self.vLayout.insertWidget(3, self.ChartView)
        
        self.PlotCurve = []
        for i in range(ADC_CHNL_N):
            self.PlotCurve.append(QLineSeries())
            self.PlotCurve[i].setName(f'CH{i}')

        for i in range(ADC_CHNL_N):
            if self.adcChnl & (1 << i):
                self.PlotChart.addSeries(self.PlotCurve[i])
        self.PlotChart.createDefaultAxes()

    @pyqtSlot()
    def on_btnOpen_clicked(self):
        if self.btnOpen.text() == '打开连接':
            try:
                self.dev = self.devices[self.cmbPort.currentText()]
                self.dev.open()

                if self.cmbCode.currentText() == 'DAC':
                    self.dev.packet_size = 32   # 没这句 Win7 下发送不出数据
            except Exception as e:
                print(e)
            else:
                self.cmbPort.setEnabled(False)
                self.cmbCode.setEnabled(False)
                self.btnOpen.setText('断开连接')
        else:
            self.dev.close()

            self.cmbPort.setEnabled(True)
            self.cmbCode.setEnabled(True)
            self.btnOpen.setText('打开连接')

    def on_tmrRcv_timeout(self):
        if self.btnOpen.text() == '断开连接':
            if self.cmbCode.currentText() == 'ADC':
                data = self.dev.read()
                if len(data) != ADC_CHNL_N * 2: # 2-byte per channel
                    return

                data = [dl | (dh << 8) for (dl, dh) in zip(data[0::2], data[1::2])]

                if self.chkWave.isChecked():
                    for i, y in enumerate(data):
                        self.PlotData[i].pop(0)
                        self.PlotData[i].append(y)
                        self.PlotPoint[i].pop(0)
                        self.PlotPoint[i].append(QtCore.QPointF(0, y))

                    if self.tmrRcv_Cnt % 4 == 0:
                        for i in range(ADC_CHNL_N):
                            for j, point in enumerate(self.PlotPoint[i]):
                                point.setX(j)
                        
                            self.PlotCurve[i].replace(self.PlotPoint[i])
                        
                        miny, maxy = [], []
                        for i in range(ADC_CHNL_N):
                            if self.adcChnl & (1 << i):
                                miny.append(min(self.PlotData[i]))
                                maxy.append(max(self.PlotData[i]))

                        if miny and maxy:
                            miny, maxy = min(miny), max(maxy)
                        
                            self.PlotChart.axisY().setRange(miny, maxy)
                            self.PlotChart.axisX().setRange(0000, 1000)

                else:
                    text = '   '.join([f'{data[i]:03X}' for i in range(ADC_CHNL_N) if self.adcChnl & (1 << i)])

                    if len(self.txtMain.toPlainText()) > 25000: self.txtMain.clear()
                    self.txtMain.append(text)

            else:
                list = self.dev.read()
                if list:
                    self.codec.recv(list)
        
        else:
            if self.tmrRcv_Cnt % 100 == 0:
                devices = self.get_devices()
                if len(devices) != self.cmbPort.count():
                    self.devices = devices
                    self.cmbPort.clear()
                    self.cmbPort.addItems(devices.keys())

        self.tmrRcv_Cnt += 1

    @pyqtSlot(str)
    def on_cmbCode_currentIndexChanged(self, text):
        self.grpADC.setVisible(text == 'ADC')
        self.grpDAC.setVisible(text == 'DAC')

        self.grpSend.setHidden(text in ('ADC', 'DAC'))

        if text == 'ADC':
            self.txtMain.clear()

        elif text == 'DAC':
            self.on_cmbWave_currentIndexChanged(self.cmbWave.currentText())
            
        else:
            self.codec = codec.Codecs[text](self)
            
            self.codec.info()

    @pyqtSlot(QtWidgets.QAbstractButton, bool)
    def on_bgrpADC_buttonToggled(self, button, checked):
        if not hasattr(self, 'PlotChart'): return

        chnl = int(button.text()[-1])

        if checked:
            self.adcChnl |=  (1 << chnl)

            self.PlotChart.addSeries(self.PlotCurve[chnl])

        else:
            self.adcChnl &= ~(1 << chnl)

            self.PlotChart.removeSeries(self.PlotCurve[chnl])

        self.PlotChart.createDefaultAxes()

    @pyqtSlot(int)
    def on_chkWave_stateChanged(self, state):
        self.ChartView.setVisible(state == Qt.Checked)
        self.txtMain.setVisible(state == Qt.Unchecked)

    @pyqtSlot(QtWidgets.QAbstractButton, bool)
    def on_bgrpDAC_buttonToggled(self, button, checked):
        if checked:
            self.dacChnl = int(self.bgrpDAC.checkedButton().text()[-1])

    @pyqtSlot(str)
    def on_cmbWave_currentIndexChanged(self, text):
        if self.cmbCode.currentText() != 'DAC': return

        self.Wave = waves.Waves[text]

        self.txtMain.clear()
        self.txtMain.append(' '.join([f'{x:03X},' for x in self.Wave]))

    @pyqtSlot()
    def on_wavSend_clicked(self):
        if self.btnOpen.text() == '断开连接':
            i = 0
            while i < len(self.Wave):
                dword = self.Wave[i:i+15]   # 每个包 32 字节（16 字），第一个字是控制字，后面跟 15 个字的数据

                dbyte = [i & 0xFF, (self.dacChnl << 4) | (i >> 8)]  # 控制字高 4 位为 DAC 通道号，低 12 位为数据在波形上的偏移

                for x in dword:
                    dbyte.append(x & 0xFF)
                    dbyte.append(x >> 8)

                self.dev.write(dbyte)
                
                i += 15

    @pyqtSlot()
    def on_btnSend_clicked(self):
        if self.btnOpen.text() == '断开连接':
            text = self.txtSend.toPlainText()
            self.codec.send(text)
    
    @pyqtSlot()
    def on_btnClear_clicked(self):
        self.txtMain.clear()
    
    def closeEvent(self, evt):
        self.conf.set('USB', 'port', self.cmbPort.currentText())
        self.conf.set('USB', 'codec',self.cmbCode.currentText())

        self.conf.set('ADC', 'chnl', f'0x{self.adcChnl:02X}')

        self.conf.set('DAC', 'chnl', f'{self.dacChnl}')
        self.conf.set('DAC', 'wave', self.cmbWave.currentText())

        self.conf.write(open('setting.ini', 'w', encoding='utf-8'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    usb = USBHID()
    usb.show()
    app.exec()
