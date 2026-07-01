"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Run all RAVA8 module commands with different parameter configurations, checking for execution
errors.
"""

import rng_rava as rava
from rng_rava import R_PeriphComms, R_PeriphModes, R_Timer3Prescalers, R_AdcPrescalers


def test_eeprom():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA8_USB()
        rng.open(sns[0])

        # EEPROM methods
        eeprom_cfg = rng.eeprom_get_rng_config()
        rng.eeprom_reset_to_default()
        rng.eeprom_set_rng_config(*eeprom_cfg)

    finally:
        # Close RAVA device
        rng.close()


def test_peripherals():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA8_USB()
        rng.open(sns[0])

        # Peripherals Enabled?
        if not rng.firmw_modules.peripherals_enabled:
            rng.close()
            return

        # Peripherals methods

        ## Digi
        for pid in [1, 2, 3, 4, 5]:

            # MODE INPUT
            rng.periph_digi(periph_id=pid, digi_comm=R_PeriphComms.MODE, digi_comm_par=R_PeriphModes.INPUT)

            # READ
            rng.periph_digi(periph_id=pid, digi_comm=R_PeriphComms.READ)

            # MODE OUTPUT
            rng.periph_digi(periph_id=pid, digi_comm=R_PeriphComms.MODE, digi_comm_par=R_PeriphModes.OUTPUT)

            # WRITE
            for w in [1, 0]:
                rng.periph_digi(periph_id=pid, digi_comm=R_PeriphComms.WRITE, digi_comm_par=w)

            # PULSE
            rng.periph_digi(periph_id=pid, digi_comm=R_PeriphComms.PULSE, pulse_duration_us=100)

        ## Digi Fast
        rng.periph_d1_digi_fast(digi_comm=R_PeriphComms.MODE, digi_comm_par=R_PeriphModes.INPUT)
        rng.periph_d1_digi_fast(digi_comm=R_PeriphComms.MODE, digi_comm_par=R_PeriphModes.OUTPUT)
        rng.periph_d1_digi_fast(digi_comm=R_PeriphComms.WRITE, digi_comm_par=1)
        rng.periph_d1_digi_fast(digi_comm=R_PeriphComms.WRITE, digi_comm_par=0)
        rng.periph_d1_digi_fast(digi_comm=R_PeriphComms.READ)
        rng.periph_d1_digi_fast(digi_comm=R_PeriphComms.PULSE, pulse_duration_us=100)

        ## D1 Trigger Input
        rng.periph_d1_trigger_input(on=True)
        rng.periph_d1_trigger_input(on=False)

        ## D1 Comparator
        # rng.periph_d1_comparator(on=True, neg_to_d5=True)    # Requires a valid signal on the comparator inputs to operate
        rng.periph_d1_comparator(on=True, neg_to_d5=False)
        rng.periph_d1_comparator(on=False)

        ## D1 Delay us test
        for i in range(1, 5+1):
            rng.periph_d1_delay_us_test(interval_us=i)

        ## D3 Periodic Trigger
        rng.periph_d3_periodic_trigger_output(on=True, interval_ms=10)
        rng.periph_d3_periodic_trigger_output(on=False)

        ## D3 PWM
        rng.periph_d3_pwm(on=True, freq_prescaler=R_Timer3Prescalers.CLK_DIV_1, top=1000, duty=100)
        rng.periph_d3_pwm(on=True, freq_prescaler=R_Timer3Prescalers.CLK_DIV_8, top=100, duty=10)
        rng.periph_d3_pwm(on=False)

        ## D3 Sound
        for freq in [220, 440, 600]:
            rng.periph_d3_sound(on=True, volume=255, freq_hz=freq)
        rng.periph_d3_sound(on=False, volume=0, freq_hz=0)

        ## D4 Pin Change
        rng.periph_d4_pin_change(on=True)
        rng.periph_d4_pin_change(on=False)

        ## D5 ADC
        for cp in R_AdcPrescalers:
            for ovs in range(3):
                rng.periph_d5_adc(on=True, ref_5v=True, clk_prescaler=cp, oversampling_n_bits=ovs)
        rng.periph_d5_adc(on=False)

    finally:
        # Close RAVA device
        rng.close()