"""
Module to work with Angstrom WS7 wavelength meter
"""

import argparse
import ctypes, os, sys, random, time
from datetime import datetime
import serial

class WavelengthMeter:

    def __init__(self, dllpath="C:\Windows\System32\wlmData.dll", debug=False):
        """
        Wavelength meter class.
        Argument: Optional path to the dll. Default: "C:\Windows\System32\wlmData.dll"
        """
        self.channels = []
        self.dllpath = dllpath
        self.debug = debug
        self.recordtime = datetime.now()
        if not debug:
            self.dll = ctypes.WinDLL(dllpath)
            self.dll.GetWavelengthNum.restype = ctypes.c_double
            self.dll.GetFrequencyNum.restype = ctypes.c_double
            self.dll.GetSwitcherMode.restype = ctypes.c_long
        try:
            self.ser = serial.Serial("COM5", 9600, timeout=1)
            self.ser.setRTS(False)
            self.ser.setDTR(True)
        except Exception as e:
            print("Could not connect to frequency counter")
        self.freq = 0
        self.waiting = False

    def GetExposureMode(self):
        if not self.debug:
            return (self.dll.GetExposureMode(ctypes.c_bool(0))==1)
        else:
            return True

    def SetExposureMode(self, b):
        if not self.debug:
            return self.dll.SetExposureMode(ctypes.c_bool(b))
        else:
            return 0

    def GetWavelength(self, channel=1):
        if not self.debug:
            wl = self.dll.GetWavelengthNum(ctypes.c_long(channel), ctypes.c_double(0))
            self.recordtime = datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")
            return wl
        else:
            wavelengths = [460.8618, 689.2643, 679.2888, 707.2016, 460.8618*2, 0, 0, 0]
            if channel>5:
                return 0
            return wavelengths[channel-1] + channel * random.uniform(0,0.0001)

    def GetFrequency(self, channel=1):
        if not self.debug:
            return self.dll.GetFrequencyNum(ctypes.c_long(channel), ctypes.c_double(0))
        else:
            return 38434900

    def GetAll(self):
        return {
            "debug": self.debug,
            "wavelength": self.GetWavelength(),
            "frequency": self.GetFrequency(),
            "exposureMode": self.GetExposureMode()
        }

    @property
    def wavelengths(self):
        return [self.GetWavelength(i+1) for i in range(8)]
    @property
    def wavelength(self):
        return self.GetWavelength(1)

    async def get_freq(self):
        if self.waiting:
            try:
                if self.ser.in_waiting > 9:
                    self.waiting = False
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8')
                    self.freq = float(data.split(" ")[0])
            except Exception as e:
                print("could not get frequency counter value: {}".format(e))
        else:
            try:
                self.ser.write("D0\r".encode())
                self.waiting = True
            except Exception as e:
                pass

    @property
    def time(self):
        return self.recordtime
        
    @property
    def switcher_mode(self):
        if not self.debug:
        	return self.dll.GetSwitcherMode(ctypes.c_long(0))
        else:
            return 0

    @switcher_mode.setter
    def switcher_mode(self, mode):
        if not self.debug:
        	self.dll.SetSwitcherMode(ctypes.c_long(int(mode)))
        else:
            pass

if __name__ == '__main__':

    # command line arguments parsing
    parser = argparse.ArgumentParser(description='Reads out wavelength values from the High Finesse Angstrom WS7 wavemeter.')
    parser.add_argument('--debug', dest='debug', action='store_const',
                        const=True, default=False,
                        help='runs the script in debug mode simulating wavelength values')
    parser.add_argument('channels', metavar='ch', type=int, nargs='*',
                        help='channel to get the wavelength, by default all channels from 1 to 8',
                        default=range(1,8))

    args = parser.parse_args()

    wlm = WavelengthMeter(debug=args.debug)

    for i in args.channels:
        print("Wavelength at channel %d:\t%.4f nm" % (i, wlm.wavelengths[i]))

    print(wlm.wavelengths[1:6:2])
    # old_mode = wlm.switcher_mode

    # wlm.switcher_mode = True

    # print(wlm.wavelengths)
    # time.sleep(0.1)
    # print(wlm.wavelengths)

    # wlm.switcher_mode = old_mode

