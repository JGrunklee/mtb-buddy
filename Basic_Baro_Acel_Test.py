# SPDX-FileCopyrightText: Copyright (c) 2025 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
import time

import board

from adafruit_bmp5xx import BMP5XX
from adafruit_lsm6ds.ism330dhcx import ISM330DHCX

SEALEVELPRESSURE_HPA = 1013.25

# I2C setup
i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

bmp = BMP5XX.over_i2c(i2c)
gyro_accel_sensor = ISM330DHCX(i2c)

bmp.sea_level_pressure = SEALEVELPRESSURE_HPA

while True:
    if bmp.data_ready:
        print(
            f"temp F: {bmp.temperature * (9 / 5) + 32} "
            f"pressure: {bmp.pressure} hPa "
            f"Approx altitude: {bmp.altitude} m"
        )
        time.sleep(1)
    accel_x, accel_y, accel_z = gyro_accel_sensor.acceleration
    print(f"Acceleration: X:{accel_x:.2f}, Y: {accel_y:.2f}, Z: {accel_z:.2f} m/s^2")
    gyro_x, gyro_y, gyro_z = gyro_accel_sensor.gyro
    print(f"Gyro X:{gyro_x:.2f}, Y: {gyro_y:.2f}, Z: {gyro_z:.2f} radians/s")
    print("")
    time.sleep(0.5)# Write your code here :-)
