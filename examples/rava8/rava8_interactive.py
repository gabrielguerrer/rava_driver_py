"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This example demonstrates interactive use of the RAVA8 device. It is intended for experimenting 
with and testing the device unique functionalities.

If using Visual Studio Code, press `F6` to start an IPython console. You can then execute the 
script interactively by placing the cursor on a line (or selecting multiple lines) and pressing 
`Shift+Enter`.
"""

import rng_rava as rava
from rng_rava import R_PwmBoostFreq, R_PeriphComms, R_PeriphModes, R_Timer3Prescalers, R_AdcPrescalers

# Open RAVA device
rng = rava.RAVA8_USB()
rng.open(rava.find_rava_sns()[0])

# Set lof level
rng.log_level('INFO')   # Simpler
# rng.log_level('DEBUG')  # More detailed


def EEPROM8():
    rng.eeprom_reset_to_default()

    rng.eeprom_get_rng_config()

    rng.eeprom_set_rng_config(R_PwmBoostFreq.F50_KHZ, 20, 10)
    rng.eeprom_set_rng_config(R_PwmBoostFreq.F50_KHZ, 20, 20)
    rng.eeprom_set_rng_config(R_PwmBoostFreq.F40_KHZ, 15, 20)


def PERIPHERALS8():
    PID = 3
    rng.periph_digi(periph_id=PID, digi_comm=R_PeriphComms.MODE, digi_comm_par=R_PeriphModes.INPUT)
    rng.periph_digi(periph_id=PID, digi_comm=R_PeriphComms.MODE, digi_comm_par=R_PeriphModes.OUTPUT)
    rng.periph_digi(periph_id=PID, digi_comm=R_PeriphComms.WRITE, digi_comm_par=1)
    rng.periph_digi(periph_id=PID, digi_comm=R_PeriphComms.WRITE, digi_comm_par=0)
    rng.periph_digi(periph_id=PID, digi_comm=R_PeriphComms.READ)
    rng.periph_digi(periph_id=PID, digi_comm=R_PeriphComms.PULSE, pulse_duration_us=100)

    rng.periph_digi(periph_id=4, digi_comm=R_PeriphComms.MODE, digi_comm_par=R_PeriphModes.INPUT)
    rng.periph_digi(periph_id=4, digi_comm=R_PeriphComms.MODE, digi_comm_par=R_PeriphModes.OUTPUT)
    rng.periph_digi(periph_id=4, digi_comm=R_PeriphComms.WRITE, digi_comm_par=1)
    rng.periph_digi(periph_id=4, digi_comm=R_PeriphComms.WRITE, digi_comm_par=0)
    rng.periph_digi(periph_id=4, digi_comm=R_PeriphComms.READ)
    rng.periph_digi(periph_id=4, digi_comm=R_PeriphComms.PULSE, pulse_duration_us=100)

    rng.periph_d1_digi_fast(digi_comm=R_PeriphComms.MODE, digi_comm_par=R_PeriphModes.INPUT)
    rng.periph_d1_digi_fast(digi_comm=R_PeriphComms.MODE, digi_comm_par=R_PeriphModes.OUTPUT)
    rng.periph_d1_digi_fast(digi_comm=R_PeriphComms.WRITE, digi_comm_par=1)
    rng.periph_d1_digi_fast(digi_comm=R_PeriphComms.WRITE, digi_comm_par=0)
    rng.periph_d1_digi_fast(digi_comm=R_PeriphComms.READ)
    rng.periph_d1_digi_fast(digi_comm=R_PeriphComms.PULSE, pulse_duration_us=100)

    rng.periph_d1_trigger_input(on=True)
    rng.periph_d1_trigger_input(on=False)

    rng.periph_d1_comparator(on=True, neg_to_d5=True)
    rng.periph_d1_comparator(on=True, neg_to_d5=False)
    rng.periph_d1_comparator(on=False)

    rng.periph_d1_delay_us_test(interval_us=1)
    rng.periph_d1_delay_us_test(interval_us=3)
    rng.periph_d1_delay_us_test(interval_us=5)
    rng.periph_d1_delay_us_test(interval_us=7)
    rng.periph_d1_delay_us_test(interval_us=9)
    rng.periph_d1_delay_us_test(interval_us=10)
    
    rng.periph_d3_periodic_trigger_output(on=True, interval_ms=5)
    rng.periph_d3_periodic_trigger_output(on=True, interval_ms=10)
    rng.periph_d3_periodic_trigger_output(on=True, interval_ms=30)
    rng.periph_d3_periodic_trigger_output(on=False)

    rng.periph_d3_pwm(on=True, freq_prescaler=R_Timer3Prescalers.CLK_DIV_1, top=1000, duty=100)
    rng.periph_d3_pwm(on=True, freq_prescaler=R_Timer3Prescalers.CLK_DIV_8, top=100, duty=10)
    rng.periph_d3_pwm(on=False)

    rng.periph_d3_sound(on=True, volume=255, freq_hz=440)
    rng.periph_d3_sound(on=True, volume=100, freq_hz=600)
    rng.periph_d3_sound(on=False, volume=0, freq_hz=0)

    rng.periph_d4_pin_change(on=True)
    rng.periph_d4_pin_change(on=False)

    rng.periph_d5_adc(on=True, ref_5v=True, clk_prescaler=1, oversampling_n_bits=0)
    rng.periph_d5_adc(on=True, ref_5v=True, clk_prescaler=R_AdcPrescalers.CLK_DIV_128, oversampling_n_bits=3)
    rng.periph_d5_adc(on=False)