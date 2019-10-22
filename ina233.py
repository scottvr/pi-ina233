""" This library supports the TI INA233 current and power monitor
with a Raspberry PI using SMBus/I2C.
"""

from smbus2 import SMBus

class INA233:
    
    CLEAR_FAULTS         = 0x03
    RESTORE_DEFAULT_ALL  = 0x12
    CAPABILITY           = 0x19
    IOUT_OC_WARN_LIMIT   = 0x4A
    VIN_OV_WARN_LIMIT    = 0x57
    VIN_UV_WARN_LIMIT    = 0x58
    PIN_OP_WARN_LIMIT    = 0x6B
    STATUS_BYTE          = 0x78
    STATUS_WORD          = 0x79
    STATUS_IOUT          = 0x79
    STATUS_IOUT          = 0x7B
    STATUS_INPUT         = 0x7C
    STATUS_CML           = 0x7E
    STATUS_MFR_SPECIFIC  = 0x80
    READ_EIN             = 0x86
    READ_VIN             = 0x88
    READ_IIN             = 0x89
    READ_VOUT            = 0x8B
    READ_IOUT            = 0x8C
    READ_POUT            = 0x96
    READ_PIN             = 0x97
    MFR_ID               = 0x99
    MFR_MODEL            = 0x9A
    MFR_REVISION         = 0x9B
    MFR_ADC_CONFIG       = 0xD0
    MFR_READ_VSHUNT      = 0xD1
    MFR_ALERT_MASK       = 0xD2
    MFR_CALIBRATION      = 0xD4
    MFR_DEVICE_CONFIG    = 0xD5
    CLEAR_EIN            = 0xD6
    TI_MFR_ID            = 0xE0
    TI_MFR_MODEL         = 0xE1
    TI_MFR_REVISION      = 0xE2
    
    # from table 1 p 17 of INA233 documentation pdf
    #SHUNT VOLTAGE TELEMETRY & WARNING COEFFICIENTS
    _m_vs = 4
    _R_vs = 5
    _b_vs = 0
    
    _m_c =0
    _R_c = 0
    _m_p = 0
    _R_p = 0
    
    #BUS VOLTAGE TELEMETRY & WARNING COEFFICIENTS
    _R_vb = 2
    _b_vb = 0
    _m_vb = 8
    
    # CURRENT & POWER CONSTANT TELEMETRY & WARNING COEFFICIENTS
    _b_c = 0
    _b_p = 0
    
    _BUS_MILLIVOLTS_LSB = 0.00125
    _SHUNT_MILLIVOLTS_LSB = 0.0000025


    def __init__(self, bus, address): 
        self._bus = SMBus(bus)
        self._address = address

    def calibrate(self, R_shunt, I_max):
        """ Calibration and scaling values per section 7.5.2
        of TI INA233 datasheet
        """
        self._R_shunt = R_shunt
        self._I_max = I_max
        self._Current_LSB = 0
        self._Power_LSB = 0
        self._CAL = 0
        tmp = 0
        round_done = False
        ERROR = 0
    
        self._Current_LSB=self._I_max/(pow(2,15))
        self._Power_LSB=25*self._Current_LSB
        self._CAL=0.00512/(self._R_shunt*self._Current_LSB)
    
        #check if CAL is in the uint16 range
        if self._CAL>0xFFFF:
            ERROR=1
        else:
            self._bus.write_word_data(self._address,self.MFR_CALIBRATION,int(self._CAL))
    
        self._m_c=1/self._Current_LSB
        self._m_p=1/self._Power_LSB
    
        #Calculate m and R for maximum accuracy in current measurement
        tmp=int(self._m_c)
        while ((tmp > 32768) or (tmp < -32768)):
            self._m_c=self._m_c/10
            self._R_c = self._R_c + 1
            tmp=int(self._m_c)
    
        while round_done==False:
            tmp=int(self._m_c)
            if tmp==self._m_c:
                round_done=True
            else:
                tmp=int(self._m_c*10)             #shift decimal to the right
                if ((tmp>32768) or (tmp<-32768)):       #m_c is out of int16 (-32768 to 32768)
                    round_done=True
                else:
                    self._m_c=self._m_c*10
                    self._R_c = self._R_c - 1 
        round_done=False
        #Calculate m and R for maximum accuracy in power measurement
        tmp = int(self._m_p)
        while tmp>32768 or tmp<-32768:
            self._m_p=self._m_p/10
            self._R_p = self._R_p + 1
            tmp = int(self._m_p)
        while round_done == False:
            tmp = int(self._m_p)
            if tmp==self._m_p:
                round_done=True
            else:
                tmp = int(self._m_p*10)          #shift decimal to the right
                if tmp>32768 or tmp<-32768:       #m_p is out of int16 (-32768 to 32768)
                    round_done=True
                else:
                    self._m_p = self._m_p*10
                    self._R_p = self._R_p - 1
    
        self._m_c = int(self._m_c)
        self._m_p = int(self._m_p)
    
    def _getBusVoltage_raw(self):
        value =  self._bus.read_i2c_block_data(self._address, self.READ_VIN, 2)
        return int((value[1] << 8) + value[0])
    
    def _getShuntVoltage_raw(self):
        value =  self._bus.read_i2c_block_data(self._address, self.MFR_READ_VSHUNT, 2)
        return int((value[1] << 8) + value[0])
    
    def _getCurrentOut_raw(self):
        value =  self._bus.read_i2c_block_data(self._address, self.READ_IOUT, 2)
        return int((value[1] << 8) + value[0])
    
    def _getCurrentIn_raw(self):
        value =  self._bus.read_i2c_block_data(self._address, self.READ_IIN, 2)
        return int((value[1] << 8) + value[0])
    
    def getShuntVoltage_mV(self):
        value=self._getShuntVoltage_raw()
        #vshunt=(value*pow(10,-R_vs)-b_vs)/m_vs
        vshunt = value * self._SHUNT_MILLIVOLTS_LSB
        return vshunt * 1000
    
    def getBusVoltage_V(self):
        value=self._getBusVoltage_raw()
        #vbus =(value*pow(10,-R_vb)-b_vb)/m_vb
        vbus = value * self._BUS_MILLIVOLTS_LSB
        return vbus
    
    def getCurrentIn_mA(self):
        value=self._getCurrentIn_raw()
        #current =(value*(pow(10,-R_c))-b_c)/m_c
        current = value * self._Current_LSB
        return float(current * 1000) 
    
    def getCurrentOut_mA(self):
        value=self._getCurrentOut_raw()
        #current =(value*(pow(10,-R_c))-b_c)/m_c
        current = value * self._Current_LSB
        return float(current * 1000) 
    
    def _getPower_raw(self):
        value =  self._bus.read_i2c_block_data(self._address, self.READ_PIN,2)
        return int((value[1] << 8) + value[0])
    
    def _getEnergy_raw(self):
        value = bus.read_i2c_block_data(self._address,READ_EIN,6)
        self._accumulator=(value[1] << 8) or value[0]
        self._roll_over=value[2]
        self._sample_count=value[5]<< 16
        self._sample_count=(value[4]<< 8)or self._sample_count
        self._sample_count=(value[3]or self._sample_count)
    
    def getAv_Power_mW(self):
        accumulator_24=0
        raw_av_power=0
        av_power=0
        self._getEnergy_raw()
        accumulator_24=int(self._roll_over)*65536+int(self._accumulator)
        raw_av_power=accumulator_24/sample_count
    
        #av_power=(raw_av_power*pow(10,-R_p)-b_p)/m_p
        av_power = raw_av_power * self._Power_LSB
        return av_power * 1000
    
    def getPower_mW(self):
        value=self._getPower_raw()
        #power =(value*pow(10,-R_p)-b_p)/m_p
        power = value * self._Power_LSB
        return power*1000
    
