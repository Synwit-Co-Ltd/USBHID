#! python3
import os
import sys
import collections
import configparser

from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QPushButton, QHBoxLayout

os.environ['PATH'] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ['PATH']
from interface import USB_BACKEND, HID_BACKEND

import codec


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

        self.initSetting()

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
        
        if not self.conf.has_section('device'):
            self.conf.add_section('device')
            self.conf.set('device', 'port', '')

            self.conf.add_section('codec')
            self.conf.set('codec', 'name', 'None')

            self.conf.add_section('history')
            self.conf.set('history', 'hist1', '')
            self.conf.set('history', 'hist2', '')

        index = self.cmbPort.findText(self.conf.get('device', 'port'))
        self.cmbPort.setCurrentIndex(index if index != -1 else 0)

        self.cmbCode.setCurrentIndex(self.cmbCode.findText(self.conf.get('codec', 'name')))

        self.txtSend.setPlainText(self.conf.get('history', 'hist1'))

    @pyqtSlot()
    def on_btnOpen_clicked(self):
        if self.btnOpen.text() == '打开连接':
            try:
                self.dev = self.devices[self.cmbPort.currentText()]
                self.dev.open()
            except Exception as e:
                print(e)
            else:
                self.cmbPort.setEnabled(False)
                self.btnOpen.setText('断开连接')
        else:
            self.dev.close()

            self.cmbPort.setEnabled(True)
            self.btnOpen.setText('打开连接')

    @pyqtSlot()
    def on_btnSend_clicked(self):
        if self.btnOpen.text() == '断开连接':
            text = self.txtSend.toPlainText()
            self.codec.send(text)

    def on_tmrRcv_timeout(self):
        if self.btnOpen.text() == '断开连接':
            list = self.dev.read()
            if list:
                self.codec.recv(list)
        
        else:
            self.tmrRcv_Cnt += 1
            if self.tmrRcv_Cnt % 100 == 0:
                devices = self.get_devices()
                if len(devices) != self.cmbPort.count():
                    self.devices = devices
                    self.cmbPort.clear()
                    self.cmbPort.addItems(devices.keys())

    @pyqtSlot(str)
    def on_cmbCode_currentIndexChanged(self, text):
        self.codec = codec.Codecs[text](self)
        
        self.codec.info()

    @pyqtSlot()
    def on_btnClear_clicked(self):
        self.txtMain.clear()
    
    def closeEvent(self, evt):
        self.conf.set('codec', 'name', self.cmbCode.currentText())
        self.conf.set('device', 'port', self.cmbPort.currentText())
        self.conf.set('history', 'hist1', self.txtSend.toPlainText())
        self.conf.write(open('setting.ini', 'w', encoding='utf-8'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    usb = USBHID()
    usb.show()
    app.exec()
