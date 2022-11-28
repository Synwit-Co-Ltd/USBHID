import os
import logging
from .interface import Interface
from .pyusb_backend import PyUSB
from .hidapi_backend import HIDApi
from .pywinusb_backend import PyWinUSB


if PyUSB.isAvailable:
    USB_BACKEND = PyUSB
else:
    USB_BACKEND = Interface


if HIDApi.isAvailable:
    HID_BACKEND = HIDApi
elif PyWinUSB.isAvailable:
    HID_BACKEND = PyWinUSB
else:
    HID_BACKEND = Interface
