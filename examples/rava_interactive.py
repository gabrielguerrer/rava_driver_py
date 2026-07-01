<<<<<<< HEAD
'''
This file should be opened in an interactive Python environment. In VSCode, the
users can utilize the F6 shortcut to execute the initial code, establishing a
connection with the device. Next, users can navigate the code and execute each
line by positioning the cursor and pressing Shift + Enter. This approach
facilitates comprehensive testing of the RAVA's functionality.

This example code is in the public domain.
Author: Gabriel Guerrer
'''

import rng_rava as rava

# Create RAVA instance and set logging level to INFO
rng = rava.RAVA_RNG_LED()
rng.log_level('INFO')

# Find RAVA device and connect
rava_sns = rava.find_rava_sns()
if len(rava_sns):
    rng.connect(serial_number=rava_sns[0])
else:
    print('No device found')


def DEVICE():

    rng.connect(serial_number=rava_sns[0])
    rng.connected()
    rng.close()

    rng.get_device_serial_number()
    rng.get_device_free_ram()

    rng.snd_device_reboot()


def EEPROM():

    rng.snd_eeprom_reset_to_default()

    rng.get_eeprom_firmware()

    rng.get_eeprom_pwm_boost()
    rng.snd_eeprom_pwm_boost(freq_id=rava.D_PWM_BOOST_FREQ['30_KHZ'], duty=12)
    rng.snd_eeprom_pwm_boost(freq_id=rava.D_PWM_BOOST_FREQ['40_KHZ'], duty=12)
    rng.snd_eeprom_pwm_boost(freq_id=rava.D_PWM_BOOST_FREQ['50_KHZ'], duty=20)
    rng.snd_eeprom_pwm_boost(freq_id=rava.D_PWM_BOOST_FREQ['60_KHZ'], duty=25)
    rng.snd_eeprom_pwm_boost(freq_id=rava.D_PWM_BOOST_FREQ['75_KHZ'], duty=25)

    rng.get_eeprom_rng()
    rng.snd_eeprom_rng(sampling_interval_us=5)
    rng.snd_eeprom_rng(sampling_interval_us=10)
    rng.snd_eeprom_rng(sampling_interval_us=15)

    rng.get_eeprom_led()
    rng.snd_eeprom_led(led_n=16)

    rng.get_eeprom_lamp()
    rng.snd_eeprom_lamp(exp_movwin_n_trials=600, exp_deltahits_sigevt=94, exp_dur_max_s=300, exp_mag_smooth_n_trials=70, exp_mag_colorchg_thld=207, sound_volume=153)


def PWM():

    rng.get_pwm_boost_setup()

    rng.snd_pwm_boost_setup(freq_id=rava.D_PWM_BOOST_FREQ['30_KHZ'], duty=12)
    rng.snd_pwm_boost_setup(freq_id=rava.D_PWM_BOOST_FREQ['40_KHZ'], duty=12)
    rng.snd_pwm_boost_setup(freq_id=rava.D_PWM_BOOST_FREQ['50_KHZ'], duty=20)
    rng.snd_pwm_boost_setup(freq_id=rava.D_PWM_BOOST_FREQ['60_KHZ'], duty=25)
    rng.snd_pwm_boost_setup(freq_id=rava.D_PWM_BOOST_FREQ['75_KHZ'], duty=25)


def RNG():

    rng.get_rng_setup()

    rng.snd_rng_setup(sampling_interval_us=5)
    rng.snd_rng_setup(sampling_interval_us=10)
    rng.snd_rng_setup(sampling_interval_us=15)

    rng.snd_rng_timing_debug_d1(on=True)
    rng.snd_rng_timing_debug_d1(on=False)

    rng.get_rng_pulse_counts(n_counts=15, output_type='list')

    rng.get_rng_bits(bit_source_id=rava.D_RNG_BIT_SRC['AB'])
    rng.get_rng_bits(bit_source_id=rava.D_RNG_BIT_SRC['A'])
    rng.get_rng_bits(bit_source_id=rava.D_RNG_BIT_SRC['B'])
    rng.get_rng_bits(bit_source_id=rava.D_RNG_BIT_SRC['AB_XOR'])
    rng.get_rng_bits(bit_source_id=rava.D_RNG_BIT_SRC['AB_RND'])

    rng.get_rng_bytes(n_bytes=15, postproc_id=rava.D_RNG_POSTPROC['NONE'], output_type='array')
    rng.get_rng_bytes(n_bytes=15, postproc_id=rava.D_RNG_POSTPROC['XOR'], output_type='array')
    rng.get_rng_bytes(n_bytes=15, postproc_id=rava.D_RNG_POSTPROC['XOR_DICHTL'], output_type='array')
    rng.get_rng_bytes(n_bytes=15, postproc_id=rava.D_RNG_POSTPROC['VON_NEUMANN'], output_type='array')

    rng.get_rng_int8s(n_ints=15, int_delta=10)
    rng.get_rng_int8s(n_ints=15, int_delta=100)
    rng.get_rng_int16s(n_ints=15, int_delta=1000)
    rng.get_rng_floats(n_floats=15)

    rng.get_rng_byte_stream_status()
    rng.snd_rng_byte_stream_start(n_bytes=100, stream_interval_ms=100, postproc_id=rava.D_RNG_POSTPROC['NONE'])
    rng.snd_rng_byte_stream_start(n_bytes=10, stream_interval_ms=0, postproc_id=rava.D_RNG_POSTPROC['NONE'])
    rng.get_rng_byte_stream_data(output_type='array')
    rng.snd_rng_byte_stream_stop()


def HEALTH():

    rng.snd_health_startup_run()
    rng.get_health_startup_results()
    rava.print_health_startup_results(*rng.get_health_startup_results())

    rng.get_health_continuous_errors()


def PERIPHERALS_DIGITAL_IO():

    rng.snd_periph_digi_mode(periph_id=1, mode_id=rava.D_PERIPH_MODES['INPUT'])
    rng.snd_periph_digi_mode(periph_id=1, mode_id=rava.D_PERIPH_MODES['OUTPUT'])
    rng.get_periph_digi_state(periph_id=1)
    rng.snd_periph_digi_state(periph_id=1, digi_state=0)
    rng.snd_periph_digi_state(periph_id=1, digi_state=1)
    rng.snd_periph_digi_pulse(periph_id=1, pulse_duration_us=100)

    rng.snd_periph_digi_mode(periph_id=2, mode_id=rava.D_PERIPH_MODES['INPUT'])
    rng.snd_periph_digi_mode(periph_id=2, mode_id=rava.D_PERIPH_MODES['OUTPUT'])
    rng.get_periph_digi_state(periph_id=2)
    rng.snd_periph_digi_state(periph_id=2, digi_state=0)
    rng.snd_periph_digi_state(periph_id=2, digi_state=1)
    rng.snd_periph_digi_pulse(periph_id=2, pulse_duration_us=100)

    rng.snd_periph_digi_mode(periph_id=3, mode_id=rava.D_PERIPH_MODES['INPUT'])
    rng.snd_periph_digi_mode(periph_id=3, mode_id=rava.D_PERIPH_MODES['OUTPUT'])
    rng.get_periph_digi_state(periph_id=3)
    rng.snd_periph_digi_state(periph_id=3, digi_state=0)
    rng.snd_periph_digi_state(periph_id=3, digi_state=1)
    rng.snd_periph_digi_pulse(periph_id=3, pulse_duration_us=100)

    rng.snd_periph_digi_mode(periph_id=4, mode_id=rava.D_PERIPH_MODES['INPUT'])
    rng.snd_periph_digi_mode(periph_id=4, mode_id=rava.D_PERIPH_MODES['OUTPUT'])
    rng.get_periph_digi_state(periph_id=4)
    rng.snd_periph_digi_state(periph_id=4, digi_state=0)
    rng.snd_periph_digi_state(periph_id=4, digi_state=1)
    rng.snd_periph_digi_pulse(periph_id=4, pulse_duration_us=100)

    rng.snd_periph_digi_mode(periph_id=5, mode_id=rava.D_PERIPH_MODES['INPUT'])
    rng.snd_periph_digi_mode(periph_id=5, mode_id=rava.D_PERIPH_MODES['OUTPUT'])
    rng.get_periph_digi_state(periph_id=5)
    rng.snd_periph_digi_state(periph_id=5, digi_state=0)
    rng.snd_periph_digi_state(periph_id=5, digi_state=1)
    rng.snd_periph_digi_pulse(periph_id=5, pulse_duration_us=100)


def PERIPHERALS():

    rng.snd_periph_d1_trigger_input(on=True)
    rng.snd_periph_d1_trigger_input(on=False)

    rng.snd_periph_d1_comparator(neg_to_d5=False)
    rng.snd_periph_d1_comparator(neg_to_d5=True)
    rng.snd_periph_d1_comparator(on=False)

    rng.snd_periph_digi_mode(periph_id=1, mode_id=rava.D_PERIPH_MODES['OUTPUT'])
    rng.snd_periph_d1_delay_us_test(delay_us=1)
    rng.snd_periph_d1_delay_us_test(delay_us=5)
    rng.snd_periph_d1_delay_us_test(delay_us=10)

    # Running with an unconnected D2 may flood the driver with random signaling
    rng.snd_periph_d2_input_capture(on=True)
    rng.snd_periph_d2_input_capture(on=False)
    rng.get_periph_d2_input_capture()

    rng.snd_periph_d3_timer3_trigger_output(interval_ms=1)
    rng.snd_periph_d3_timer3_trigger_output(interval_ms=10)
    rng.snd_periph_d3_timer3_trigger_output(interval_ms=100)
    rng.snd_periph_d3_timer3_trigger_output(on=False)

    rng.snd_periph_d3_timer3_pwm(freq_prescaler=1, top=2**16-1, duty=1000)
    rng.snd_periph_d3_timer3_pwm(freq_prescaler=1, top=2**8-1, duty=10)
    rng.snd_periph_d3_timer3_pwm(freq_prescaler=1, top=2**5-1, duty=10)
    rng.snd_periph_d3_timer3_pwm(on=False)

    rng.snd_periph_d3_timer3_sound(freq_hz=220, volume=255)
    rng.snd_periph_d3_timer3_sound(freq_hz=440, volume=255)
    rng.snd_periph_d3_timer3_sound(freq_hz=880, volume=255)
    rng.snd_periph_d3_timer3_sound(freq_hz=0)

    rng.snd_periph_d4_pin_change(on=True)
    rng.snd_periph_d4_pin_change(on=False)

    rng.get_periph_d5_adc_read(ref_5v=0, clk_prescaler=6, oversampling_n_bits=0)
    rng.get_periph_d5_adc_read(ref_5v=1, clk_prescaler=6, oversampling_n_bits=0)
    rng.get_periph_d5_adc_read(ref_5v=0, clk_prescaler=6, oversampling_n_bits=6)
    rng.get_periph_d5_adc_read(ref_5v=1, clk_prescaler=6, oversampling_n_bits=6)


def INTERFACES():

    rng.get_interface_ds18bs0()


def LED():

    rng.snd_led_color(color_hue=rava.D_LED_COLOR['RED'], intensity=255)
    rng.snd_led_color(color_hue=rava.D_LED_COLOR['ORANGE'], intensity=255)
    rng.snd_led_color(color_hue=rava.D_LED_COLOR['YELLOW'], intensity=255)
    rng.snd_led_color(color_hue=rava.D_LED_COLOR['GREEN'], intensity=255)
    rng.snd_led_color(color_hue=rava.D_LED_COLOR['CYAN'], intensity=255)
    rng.snd_led_color(color_hue=rava.D_LED_COLOR['BLUE'], intensity=255)
    rng.snd_led_color(color_hue=rava.D_LED_COLOR['PURPLE'], intensity=255)
    rng.snd_led_color(color_hue=rava.D_LED_COLOR['PINK'], intensity=255)

    rng.snd_led_color_fade(color_hue_tgt=rava.D_LED_COLOR['RED'], duration_ms=1000)
    rng.snd_led_color_fade(color_hue_tgt=rava.D_LED_COLOR['ORANGE'], duration_ms=1000)
    rng.snd_led_color_fade(color_hue_tgt=rava.D_LED_COLOR['YELLOW'], duration_ms=1000)
    rng.snd_led_color_fade(color_hue_tgt=rava.D_LED_COLOR['GREEN'], duration_ms=1000)
    rng.snd_led_color_fade(color_hue_tgt=rava.D_LED_COLOR['CYAN'], duration_ms=1000)
    rng.snd_led_color_fade(color_hue_tgt=rava.D_LED_COLOR['BLUE'], duration_ms=1000)
    rng.snd_led_color_fade(color_hue_tgt=rava.D_LED_COLOR['PURPLE'], duration_ms=1000)
    rng.snd_led_color_fade(color_hue_tgt=rava.D_LED_COLOR['PINK'], duration_ms=1000)

    rng.snd_led_color_oscillate(n_cycles=3, duration_ms=4000)
    rng.snd_led_color_oscillate(n_cycles=10, duration_ms=10000)

    rng.snd_led_intensity(intensity=0)
    rng.snd_led_intensity(intensity=63)
    rng.snd_led_intensity(intensity=127)
    rng.snd_led_intensity(intensity=191)
    rng.snd_led_intensity(intensity=255)

    rng.snd_led_intensity_fade(intensity_tgt=0, duration_ms=1000)
    rng.snd_led_intensity_fade(intensity_tgt=255, duration_ms=1000)

    rng.snd_led_fade_stop()

    rng.get_led_status()


def LAMP():

    rng.snd_lamp_mode(on=True)
    rng.snd_lamp_mode(on=False)

    rng.snd_lamp_debug(on=True)
    rng.get_lamp_debug_data()
    rng.snd_lamp_debug(on=False)

    rng.get_lamp_statistics()
=======
"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This example demonstrates interactive use of the RAVA device. It is intended for experimenting with
and testing the device functionality.

If using Visual Studio Code, press `F6` to start an IPython console. You can then execute the
script interactively by placing the cursor on a line (or selecting multiple lines) and pressing
`Shift+Enter`.
"""

import rng_rava as rava
from rng_rava import R_RngCores, R_RngPP, R_PwmBoostFreq

# Open RAVA device
rng = rava.RAVA_USB()
rng.open(rava.find_rava_sns()[0])

# Set lof level
rng.log_level('INFO')   # Simpler
# rng.log_level('DEBUG')  # More detailed

# Number of samples
N = 100


def DEVICE():
    rng.dev_ping()
    rng.dev_get_info()
    rng.dev_get_usage()
    rng.dev_get_free_ram()
    rng.dev_get_temperature()
    rng.dev_get_vcc()

    rng.dev_monitor(n_pulse_counts=100, n_bytes=100)


def HEALTH():
    rng.health_startup_run()
    rng.health_startup_get_results()

    rng.health_continuous_get_errors()


def RNG():
    # Config
    rng.get_config()
    rng.set_config(pwm_boost_freq=R_PwmBoostFreq.F50_KHZ, pwm_boost_duty=20, rng_sampling_interval=10)
    rng.set_config(pwm_boost_freq=R_PwmBoostFreq.F50_KHZ, pwm_boost_duty=20, rng_sampling_interval=20)

    rng.set_timing_debug(True)
    rng.set_timing_debug(False)

    # Pulse counts
    rng.gen_pulse_counts(n_counts=N, rng_cores=R_RngCores.AB_DUAL)
    rng.gen_pulse_counts(n_counts=N, rng_cores=R_RngCores.AB_ALT)
    rng.gen_pulse_counts(n_counts=N, rng_cores=R_RngCores.A)
    rng.gen_pulse_counts(n_counts=N, rng_cores=R_RngCores.B)

    # Bit
    rng.gen_bit(rng_cores=R_RngCores.AB_DUAL)
    rng.gen_bit(rng_cores=R_RngCores.AB_ALT)
    rng.gen_bit(rng_cores=R_RngCores.AB_XOR)
    rng.gen_bit(rng_cores=R_RngCores.A)
    rng.gen_bit(rng_cores=R_RngCores.B)

    # Bytes
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.AB_DUAL, postproc=R_RngPP.NONE)
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.AB_ALT, postproc=R_RngPP.NONE)
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.AB_XOR, postproc=R_RngPP.NONE)
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.A, postproc=R_RngPP.NONE)
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.B, postproc=R_RngPP.NONE)

    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.AB_DUAL, postproc=R_RngPP.NONE)
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.AB_DUAL, postproc=R_RngPP.XOR)
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.AB_DUAL, postproc=R_RngPP.XOR_DICHTL)

    # Byte stream
    rng.start_byte_stream(n_bytes=N, interval_ms=1000, rng_cores=R_RngCores.AB_DUAL, postproc=R_RngPP.NONE)
    rng.start_byte_stream(n_bytes=N, interval_ms=1000, rng_cores=R_RngCores.AB_ALT, postproc=R_RngPP.XOR)

    rng.get_byte_stream()
    rng.get_status_byte_stream()
    rng.stop_byte_stream()

    # Int8s
    rng.gen_int8s(n_ints=N, delta=100, postproc=R_RngPP.NONE)
    rng.gen_int8s(n_ints=N, delta=100, postproc=R_RngPP.XOR)
    rng.gen_int8s(n_ints=N, delta=100, postproc=R_RngPP.XOR_DICHTL)

    # Int16s
    rng.gen_int16s(n_ints=N, delta=1000, postproc=R_RngPP.NONE)
    rng.gen_int16s(n_ints=N, delta=1000, postproc=R_RngPP.XOR)
    rng.gen_int16s(n_ints=N, delta=1000, postproc=R_RngPP.XOR_DICHTL)

    # Floats
    rng.gen_floats(n_floats=N, postproc=R_RngPP.NONE)
    rng.gen_floats(n_floats=N, postproc=R_RngPP.XOR)
    rng.gen_floats(n_floats=N, postproc=R_RngPP.XOR_DICHTL)

    # Floats Downey
    rng.gen_floats_downey(n_floats=N, postproc=R_RngPP.NONE)
    rng.gen_floats_downey(n_floats=N, postproc=R_RngPP.XOR)
    rng.gen_floats_downey(n_floats=N, postproc=R_RngPP.XOR_DICHTL)
>>>>>>> 4fcf521 (Update v3.0.0)
