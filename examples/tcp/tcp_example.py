"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Demonstrates how to launch the RAVA TCP server as a subprocess and communicate with it from a TCP 
client that repeatedly requests random bytes.
"""

import subprocess
import sys
import time

import rng_rava as rava

HOST = '127.0.0.1'
PORT = 4884
running = True

N_GEN = 100
T_RUN = 5.
T_GEN_INTERVAL = 0.5

# Start the TCP server using the same Python interpreter as the current process, inheriting the
# Python environment
p = subprocess.Popen(
    [sys.executable, '-m', 'rng_rava.tcp_srv', '--host', str(HOST), '--port', str(PORT)]
    )

# Wait server startupt
time.sleep(0.5)

# Connect to the RAVA TCP server
rng = rava.RAVA8_TCP()
rng.open(HOST, PORT)

# For the duration of T_RUN, request 2xN_GEN bytes every T_GEN_INTERVAL
t0 = time.perf_counter()
while True:
    rnd_a, rnd_b = rng.gen_bytes(n_bytes=N_GEN)
    print(rnd_a)
    print(rnd_b)

    time.sleep(T_GEN_INTERVAL)

    if time.perf_counter() - t0 > T_RUN:
        break

# Close TCP client
rng.close()

# Close TCP server
p.terminate()
p.wait()