#!/usr/bin/python3

''' In this example, we have two INA233's, at addresses 0x40 and 0x41
for a hypothetical solar battery charging system.
'''

from ina233 import INA233

R_shunt_ohms = 0.020 # shunt resistor value in Ohms
I_max_amps = 10 # max expected current in Amps

bus = 1 # I2C bus
battery_address = 0x40 # address of INA233 connected to battery circuit
solar_address = 0x41 # address of INA233 connected to solar charging circuit

battery_ina233 = INA233(bus, battery_address)
solar_ina233 = INA233(bus, solar_address)
   
battery_ina233.calibrate(R_shunt_ohms, I_max_amps)
solar_ina233.calibrate(R_shunt_ohms, I_max_amps) 

print("Battery Bus Voltage    : %.3f V" % battery_ina233.getBusVoltage_V())
print("Battery Bus Current    : %.3f mA" % battery_ina233.getCurrentIn_mA())
print("Solar Bus Voltage      : %.3f V" % solar_ina233.getBusVoltage_V())
