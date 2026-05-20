###############################################################################
#
# mtb-buddy
#
# Main file (for now)
#
###############################################################################

import time
import board
import os
import busio
import digitalio
import storage
import adafruit_sdcard
import analogio
import adafruit_gps

from adafruit_bmp5xx import BMP5XX
from adafruit_lsm6ds.ism330dhcx import ISM330DHCX

###############################################################################
# CONSTANTS
###############################################################################

SEALEVELPRESSURE_HPA = 1013.25
LOG_FILE = "/sd/gps.txt"
LOG_MODE = "ab"
DATA_FILE = "/sd/data.txt"
DATA_MODE = "a"
MAIN_LOOP_INTERVAL_MS = 1000

###############################################################################
# FUNCTIONS
###############################################################################

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

def init_sdcard():
    cs = digitalio.DigitalInOut(board.SD_CS)
    sd_spi = busio.SPI(board.SD_CLK, board.SD_MOSI, board.SD_MISO)
    sdcard = adafruit_sdcard.SDCard(sd_spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")

    print("Files on filesystem:")
    print("====================")
    print_directory("/sd")

def get_voltage(pin):
    return pin.value / 65535 * 3.3 * 2

###############################################################################
# INITIALIZATION
###############################################################################

print("... Inititializing ...")

# Battery voltage pin
vbat_voltage = analogio.AnalogIn(board.A3)

# I2C setup
i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

# IMU sensor
bmp = BMP5XX.over_i2c(i2c)
bmp.sea_level_pressure = SEALEVELPRESSURE_HPA

# Gyro
gyro_accel_sensor = ISM330DHCX(i2c)

# SD Card
init_sdcard()

# Create a serial connection for the GPS connection using default speed and
# a slightly higher timeout (GPS modules typically update once a second).
# These are the defaults you should use for the GPS FeatherWing.
# For other boards set RX = GPS module TX, and TX = GPS module RX pins.
uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)
# Create a GPS module instance.
gps = adafruit_gps.GPS(uart)  # Use UART/pyserial

print("Initialization completed.")

###############################################################################
# MAIN LOOP
###############################################################################

next_mainloop_time = time.ticks_ms() + 1; # *soon*

while True:

    # Basic scheduler - Run the mainloop body at most every MAIN_LOOP_INTERVAL_MS

    now = time.ticks_ms()
    diff = time.ticks_diff(next_mainloop_time, now)
    if diff > 0: # We have to poll a little longer for the next mainloop
        continue
    elif diff < 0: # Loop took longer than the MAIN_LOOP_INTERVAL_MS
        print(f"!!! Warning: Mainloop just before time ({now}) took {diff}ms longer than we would like !!!")
    next_mainloop_time = next_mainloop_time + MAIN_LOOP_INTERVAL_MS

    # File handle setup (open and close files every mainloop)
    with open(DATA_FILE, DATA_MODE) as f:
        with open(LOG_FILE, LOG_MODE) as outfile:

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

            # Battery Voltage
            battery_voltage = get_voltage(vbat_voltage)
            print("VBat voltage: {:.2f}".format(battery_voltage))
            f.write("VBat voltage: {:.2f}\n".format(battery_voltage))

            # GPS
            sentence = gps.readline()
            if not sentence:
                continue
            print(str(sentence, "ascii").strip())
            outfile.write(sentence)

        # Close LOG_FILE
    # Close DATA_FILE

# End of Mainloop
