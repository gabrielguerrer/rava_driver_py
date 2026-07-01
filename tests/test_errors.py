"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Intentionally trigger invalid transport operations and malformed protocol messages to verify that 
the expected RAVA exceptions are raised.
"""

import queue
import struct

import rng_rava as rava


def send_retrieve_msg(rng, request_id, msg_out_bytes):
    q = queue.Queue()
    rng.comm_pending_msgs[request_id] = q
    rng.write(msg_out_bytes)
    msg_in = q.get()

    return msg_in


def test_transport_errors():  
    rng = rava.RAVA_USB()

    # RAVAConnectError
    try:
        rng.open('abcdef12345')

    except Exception as exc:
        assert isinstance(exc, rava.RAVAConnectError)

    # RAVAClosedError
    try:
        rng.gen_bytes(1)

    except Exception as exc:
        assert isinstance(exc, rava.RAVAClosedError)


def test_protocol_errors():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA_USB()
        rng.open(sns[0])
        
        # INVALID_RAND_LEN
        request_id = 1
        command_id = rava.R_MessageComm.RNG_GEN_BYTES
        data = b''
        rand = bytes(2**16-1)
        msg_out = rava.RAVAMessage(0, request_id, rava.R_MessageError.OK, command_id, data, rand)
        msg_in = send_retrieve_msg(rng, request_id, msg_out.to_bytes())

        try:
            msg_in.validate()

        except Exception as exc:        
            assert isinstance(exc, rava.RAVAProtocolError)
            assert 'INVALID_RAND_LEN' in str(exc)

        # INVALID_DATA_LEN
        request_id = 2
        command_id = rava.R_MessageComm.RNG_GEN_BYTES
        data = bytes(2**8-1)
        rand = b''
        msg_out = rava.RAVAMessage(0, request_id, rava.R_MessageError.OK, command_id, data, rand)
        msg_in = send_retrieve_msg(rng, request_id, msg_out.to_bytes())

        try:
            msg_in.validate()

        except Exception as exc:        
            assert isinstance(exc, rava.RAVAProtocolError)
            assert 'INVALID_DATA_LEN' in str(exc)
        
        # INVALID_CRC
        request_id = 3
        command_id = rava.R_MessageComm.RNG_GEN_BYTES
        data = b''
        rand = b''
        msg_out = rava.RAVAMessage(0, request_id, rava.R_MessageError.OK, command_id, data, rand)
        msg_out_bytes = bytearray(msg_out.to_bytes())
        msg_out_bytes[10] = 0
        msg_in = send_retrieve_msg(rng, request_id, msg_out_bytes)

        try:
            msg_in.validate()

        except Exception as exc:        
            assert isinstance(exc, rava.RAVAProtocolError)
            assert 'INVALID_CRC' in str(exc)
        
        # INVALID_COMM_ID
        request_id = 4
        command_id = 8
        data = b''
        rand = b''
        msg_out = rava.RAVAMessage(0, request_id, rava.R_MessageError.OK, command_id, data, rand)
        msg_in = send_retrieve_msg(rng, request_id, msg_out.to_bytes())

        try:
            msg_in.validate()

        except Exception as exc:        
            assert isinstance(exc, rava.RAVAProtocolError)
            assert 'INVALID_COMM_ID' in str(exc)

    # Close
    finally:
        rng.close()


def test_parameter_errors():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA_USB()
        rng.open(sns[0])

        # INVALID_INPUT_TYPES
        request_id = 1
        command_id = rava.R_MessageComm.RNG_GEN_BYTES
        n_bytes = 100
        rng_cores = rava.R_RngCores.AB_DUAL
        postproc = rava.R_RngPP.NONE
        data = struct.pack('<HHH', n_bytes, rng_cores, postproc)
        rand = b''
        msg_out = rava.RAVAMessage(0, request_id, rava.R_MessageError.OK, command_id, data, rand)
        msg_in = send_retrieve_msg(rng, request_id, msg_out.to_bytes())

        try:
            msg_in.validate()

        except Exception as exc:
            assert isinstance(exc, rava.RAVAParameterError)
            assert 'INVALID_INPUT_TYPES' in str(exc)

        # INVALID_INPUT_VALUES
        request_id = 1
        command_id = rava.R_MessageComm.RNG_GEN_BYTES
        n_bytes = 100
        rng_cores = 100
        postproc = 100
        data = struct.pack('<HBB', n_bytes, rng_cores, postproc)
        rand = b''
        msg_out = rava.RAVAMessage(0, request_id, rava.R_MessageError.OK, command_id, data, rand)
        msg_in = send_retrieve_msg(rng, request_id, msg_out.to_bytes())

        try:
            msg_in.validate()

        except Exception as exc:
            assert isinstance(exc, rava.RAVAParameterError)
            assert 'INVALID_INPUT_VALUES' in str(exc)

    # Close
    finally:
        rng.close()


def test_byte_streaming_error():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA_USB()
        rng.open(sns[0])

        # RAVAByteStreamingError
        rng.start_byte_stream(1, 1000)

        try:
            rng.start_byte_stream(1, 1000)

        except Exception as exc:
            assert isinstance(exc, rava.RAVAByteStreamingError)

    # Close
    finally:
        rng.close()