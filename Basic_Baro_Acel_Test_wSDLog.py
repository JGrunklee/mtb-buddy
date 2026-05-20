# SPDX-FileCopyrightText: Copyright (c) 2025 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
import time
import board
import os
import busio
import digitalio
import storage
import adafruit_sdcard
import analogio

from adafruit_bmp5xx import BMP5XX
from adafruit_lsm6ds.ism330dhcx import ISM330DHCX

SEALEVELPRESSURE_HPA = 1013.25

vbat_voltage = analogio.AnalogIn(board.A3)

# I2C setup
i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

bmp = BMP5XX.over_i2c(i2c)
gyro_accel_sensor = ISM330DHCX(i2c)

bmp.sea_level_pressure = SEALEVELPRESSURE_HPA

cs = digitalio.DigitalInOut(board.SD_CS)
sd_spi = busio.SPI(board.SD_CLK, board.SD_MOSI, board.SD_MISO)
sdcard = adafruit_sdcard.SDCard(sd_spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

def print_directory(path, tabs=0):
    for file in os.listdir(path):
        stats = os.stat(path + "/" + file)
        filesize = stats[6]
        isdir = stats[0] & 0x4000

        if filesize < 1000:
            sizestr = str(filesize) + " bytes"
        elif filesize < 1000000:
            sizestr = "%0.1f KB" % (filesize / 1000)
        else:
            sizestr = "%0.1f MB" % (filesize / 1000000)

        prettyprintname = ""
        for _ in range(tabs):
            prettyprintname += "   "
        prettyprintname += file
        if isdir:
            prettyprintname += "/"
        print("{0:<40} Size: {1:>10}".format(prettyprintname, sizestr))

        # recursively print directory contents
        if isdir:
            print_directory(path + "/" + file, tabs + 1)


print("Files on filesystem:")
print("====================")
print_directory("/sd")

def get_voltage(pin):
    return pin.value / 65535 * 3.3 * 2

print("Logging data to filesystem")

while True:
    with open("/sd/data.txt",'a') as f:

        # Barometer, Temperature
        if bmp.data_ready:
            BMP_Temp = bmp.temperature * (9 / 5) + 32
            BMP_Pres = bmp.pressure
            BMP_Alt = bmp.altitude
            print(
                f"temp F: {BMP_Temp} "
                f"pressure: {BMP_Pres} hPa "
                f"Approx altitude: {BMP_Alt} m"
            )
            f.write(
                f"temp F: {BMP_Temp} "
                f"pressure: {BMP_Pres} hPa "
                f"Approx altitude: {BMP_Alt} m\n"
            )
            time.sleep(1)

        #Gyro, Acceleration
        accel_x, accel_y, accel_z = gyro_accel_sensor.acceleration
        print(f"Acceleration: X:{accel_x:.2f}, Y: {accel_y:.2f}, Z: {accel_z:.2f} m/s^2")
        gyro_x, gyro_y, gyro_z = gyro_accel_sensor.gyro
        print(f"Gyro X:{gyro_x:.2f}, Y: {gyro_y:.2f}, Z: {gyro_z:.2f} radians/s")
        print("")
        f.write(
            f"Acceleration: X:{accel_x:.2f}, Y: {accel_y:.2f}, Z: {accel_z:.2f} m/s^2\n"
            f"Gyro X:{gyro_x:.2f}, Y: {gyro_y:.2f}, Z: {gyro_z:.2f} radians/s\n"
        )
        time.sleep(0.5)

        # Battery Voltage
        battery_voltage = get_voltage(vbat_voltage)
        print("VBat voltage: {:.2f}".format(battery_voltage))
        f.write("VBat voltage: {:.2f}\n".format(battery_voltage))
    time.sleep(0.5)

