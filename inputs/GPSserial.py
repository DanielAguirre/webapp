import serial
import time

DEFAULT_LOC = {'lat': 37.96713657090229, 'lng': -122.0712176165581}

class GPSserial():
    '''
    GPS serial Output conforms to NMEA format
    See the datasheet in this repo
    '''
    def __init__(self, addy):
        # open a "channel" (technically I think its called a "handle") to Serial port
        # on rasbian the Tx/Rx pins register as '/dev/ttyS0'
        # on Windows my arduino (connected to GPS6MV2) registers as "COM3"
        # addy passed from inputs/cmdArgs.py
        self.dummy = False
        try:
            self.ser = serial.Serial(addy)
        except serial.SerialException:
            self.dummy = True
            print('unable to open', addy)
        self.NS = DEFAULT_LOC['lat']
        self.EW = DEFAULT_LOC['lng']
        self.UTC = ""
        self.line = ""
        self.speed = {"knots": 0.0, "kmph": 0.0}
        self.course = {"true": 0.0, "mag": 0.0}
        self.sat = {"connected": 0, "view": 0, "quality": "Fix Unavailable"}
        self.alt = 0.0
        self.azi = 0.0
        self.elev = 0.0
        self.fix = "no Fix"
        self.status = "unknown"
        
    def getCoords(self):
        pass
    
    def getTime(self):
        if (self.UTC == ""):
            return "no UTC"
        else:
            hr = int(self.UTC[0:2])
            min = int(self.UTC[3:4])
            sec = float(self.UTC[5:])
            return self.UTC

    def parseline(self, str):
        found = False
        if str.find('GLL') != -1:
            NS_start = str.find(',') + 1
            NS_end = str.find(',', NS_start)
            self.NS_dir = str[NS_end + 1]
            print('NS =', self.NS_dir)
            if (str[NS_end + 1] != 'N'):
                self.NS_dir = -1.0
            else:
                self.NS_dir = 1.0
            EW_start = str.find(',', NS_end + 1) + 1
            EW_end = str.find(',', EW_start)
            self.EW_dir = str[EW_end + 1]
            print('EW =', self.EW_dir)
            if (str[EW_end + 1] != 'E'):
                self.EW_dir = -1.0
            else:
                self.EW_dir = 1.0
            UTC_start = str.find(',', EW_end + 1) + 1
            UTC_end = str.find(',', UTC_start) - 1
            self.UTC = str[UTC_start:UTC_end]
            self.NS = float(str[NS_start:NS_end])
            self.EW = float(str[EW_start:EW_end])
            self.convertGPS()
        elif (str.find('VTG') != -1):
            found = True
            C_T_start = str.find(',') + 1
            C_T_end = str.find(',', C_T_start)
            C_M_start = str.find(',', C_T_end + 1) + 1
            C_M_end = str.find(',', C_M_start)
            S_N_start = str.find(',', C_M_end + 1) + 1
            S_N_end = str.find(',', S_N_start)
            S_G_start = str.find(',', S_N_end + 1) + 1
            S_G_end = str.find(',', S_G_start)
            if (C_T_end - C_T_start > 1):
                self.course["true"] = str[C_T_start:C_T_end]
            if (C_M_end - C_M_start > 1):
                self.course["mag"] = str[C_M_start:C_M_end]
            self.speed["knots"] = float(str[S_N_start:S_N_end])
            self.speed["kmph"] = str[S_G_start:S_G_end]
        elif (str.find('GGA') != -1):
            typeStat = ["Fix Unavailable", "Valid Fix (SPS)", "Valid Fix (GPS)"]
            Qual_start = str.find(',') + 1
            for i in range(1,6):
                Qual_start = str.find(',', Qual_start) + 1
            Qual_end = str.find(',', Qual_start)
            Sat_end = str.find(',', Qual_end + 1)
            Alt_start = str.find(',', Sat_end + 1) + 1
            Alt_end = str.find(',', Alt_start)
            self.sat["quality"] = typeStat[int(str[Qual_start:Qual_end])]
            self.sat["connected"] = int(str[Qual_end + 1:Sat_end])
            self.alt = float(str[Alt_start:Alt_end])
        elif (str.find('GSV') != -1):
            '''View_start = str.find(',') + 1
            View_start = str.find(',', View_start) + 1
            View_start = str.find(',', View_start) + 1
            View_end = str.find(',', View_start)
            Elev_start = str.find(',', View_end + 1) + 1
            Elev_start = str.find(',', Elev_start) + 1
            Elev_end = str.find(',', Elev_start)
            Azi_end = str.find(',', Elev_end + 1)
            self.sat["view"] = int(str[View_start:View_end])
            self.elev = int(str[Elev_start:Elev_end])
            self.azi = int(str[Elev_end + 1:Azi_end])
            print('sat["view"]:', self.sat["view"], 'elevation:', self.elev, 'Azimuth:', self.azi)'''
            pass
        elif (str.find('GSA') != -1):
            typeFix = ["No Fix","2D", "3D"]
            Fix_start = str.find(',') + 1
            Fix_start = str.find(',', Fix_start) + 1
            Fix_end = str.find(',', Fix_start)
            # print('typeFix:', int(str[Fix_start:Fix_end]))
            self.fix =typeFix[int(str[Fix_start:Fix_end]) - 1]
        elif (str.find('RMC') != -1):
            status = {"V":"Warning","A": "Valid"}
            Stat_start = str.find(',') + 1
            Stat_start = str.find(',', Stat_start) + 1
            Stat_end = str.find(',', Stat_start)
            self.status = status[str[Stat_start:Stat_end]]

        return found

    def convertGPS(self):
        lat_DD = int(self.NS/100)
        lat_SS = self.NS - (lat_DD*100)
        latDec = lat_DD + lat_SS/60

        lng_DD = int(self.EW/100)
        lng_SS = self.EW - (lng_DD*100)
        lngDec = lng_DD + lng_SS/60
        self.NS = latDec * self.NS_dir
        self.EW = lngDec * self.EW_dir
    
    def getData(self, raw = False):
        found = False
        # discard 1st two lines
        if not self.dummy:
            # self.line = self.ser.readline()
            # self.line = self.ser.readline()
            pass

        while(not found and not self.dummy):
            self.line = self.ser.readline()
            if (raw):
                print(self.line)
            # self.line = list(self.line)
            # self.line[0] = 0x26
            self.line = self.line.decode('utf-8')
            found = self.parseline(self.line)
'''
    def __del__(self):
        del self.ser, self.north, self.west, self.line 
'''
if __name__ == "__main__":
    gps = GPSserial('/dev/ttyS0')
    while (True):
        try:
            gps.getData(True)
            print('RxStatus:', gps.status)
            print('FixType:', gps.fix)
            print('sat["quality"]:', gps.sat["quality"], 'sat["connected"]:', gps.sat["connected"], 'Altitude:', gps.alt)
            print('Course True North:', gps.course["true"], 'Course Magnetic North:', gps.course["mag"], 'speed["knots"]:', gps.speed["knots"], 'speed["kmph"]:', gps.speed["kmph"])
            print('UTC:', gps.getTime(), 'NS:',  gps.NS, 'EW:', gps.EW)
            time.sleep(1)
        except KeyboardInterrupt:
            del gps
            break