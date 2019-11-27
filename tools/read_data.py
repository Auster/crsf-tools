#!/usr/bin/env python
import sys
import argparse
import logging
import struct

import serial
from enum import Enum

from msp_codes import MspCodes
from crsf_crc import CrsfCrc, calc_crc
from crsf_codes import CrsfFrameAddress, CrsfFrameType, CrsfCommandID,\
    CrsfDataType, CrsfVtxXPower, CrsfVtxPitmode, CrsfVtxInterface, CrsfHardwareID


SYNC_BYTE = 0xC8
MAX_FRAME_SYZE = 62


def unpack_sting(bytes_list):
    format = "c" * len(bytes_list)
    return struct.pack(">{}".format(format), *bytes_list)


def list_to_bytes(data):
    format = "B" * len(data)
    return struct.pack(">{}".format(format), *data)


def setup_logging():
    log_dateformat = "%H:%M:%S"
    log_format = "%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s"

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(log_format, datefmt=log_dateformat)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def bytes_to_uint(bytes):
    result = 0
    step = 0
    for i in bytes:
        result += ord(i) << 8 * (len(bytes) - 1 - step)
        step += 1
    return result


def bytes_to_int_list(bytes):
    result = []
    for i in bytes:
        result.append(int(ord(i)))
    return result


class CrsfPayload(object):
    payload = None

    def __init__(self, type, payload):
        self.type = type
        self.payload_raw = payload
        self.decode()

    @staticmethod
    def decode_flight_mode(payload):
        is_armed = True
        end_index = -1
        if payload[-2] == '*':
            is_armed = False
            end_index = -2
        return (
            ("raw", bytes_to_int_list(payload)),
            ("mode", "".join(payload[0:end_index])),
            ("is_armed", is_armed)
        )

    @staticmethod
    def decode_battery_sensor(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("voltage", float((ord(payload[0]) << 8) + ord(payload[1])) / 10),
            ("current", float((ord(payload[2]) << 8) + ord(payload[3])) / 10),
            ("consumption", (ord(payload[4]) << 16) + (ord(payload[5]) << 8) + ord(payload[6])),
            ("battary procentage", bytes_to_uint(payload[7])),
        )

    @staticmethod
    def decode_unknown_0x38(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("dst address", CrsfFrameAddress(ord(payload[0]))),
            ("src address", CrsfFrameAddress(ord(payload[1]))),
            ("payload", bytes_to_int_list(payload[2:]))
        )

    @staticmethod
    def decode_unknown_0x34(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("dst address", CrsfFrameAddress(ord(payload[0]))),
            ("src address", CrsfFrameAddress(ord(payload[1]))),
            ("payload", bytes_to_uint(payload[2:13]))
        )

    @staticmethod
    def decode_unknown_0x36(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("dst address", CrsfFrameAddress(ord(payload[0]))),
            ("src address", CrsfFrameAddress(ord(payload[1]))),
            ("payload", bytes_to_int_list(payload[2:]))
        )

    @staticmethod
    def decode_vtx(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("src address", CrsfFrameAddress(ord(payload[0]))),
            ("comm mode", CrsfVtxInterface(ord(payload[0]) >> 5)),
            ("is VTX available", ord(payload[0]) >> 4 & 1),
            ("is manual freq", ord(payload[0]) >> 1 & 1),  # TODO: test
            ("is PitMode", ord(payload[0]) & 1),
            ("band",  ord(payload[2])),
            ("manual frequency", bytes_to_uint(payload[3:4])),
            ("PitMode", CrsfVtxPitmode(ord(payload[5]) >> 4)),
            ("power", CrsfVtxXPower(ord(payload[5]) & int('111', 2)))
        )

    @staticmethod
    def decode_device_ping(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("dst address", CrsfFrameAddress(ord(payload[0]))),
            ("src address", CrsfFrameAddress(ord(payload[1]))),
        )

    @staticmethod
    def decode_device_info(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("dst address", CrsfFrameAddress(ord(payload[0]))),
            ("src address", CrsfFrameAddress(ord(payload[1]))),
            ("name", "".join(payload[2:-15])),
            # Zero byte
            ("serial number", bytes_to_uint(payload[-14:-10])),
            ("hardware id", hex(bytes_to_uint(payload[-10:-6]))),  # CrsfHardwareID
            ("hardware id (decoded)", CrsfHardwareID(bytes_to_uint(payload[-10:-6]) >> 3 << 3)),
            ("firmware id", bytes_to_uint(payload[-6:-2])),
            ("parameter count", ord(payload[-2])),
            ("device info version", ord(payload[-1]))
        )

    # FIXME
    @staticmethod
    def decode_parameter_settings_entry(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("dst address", CrsfFrameAddress(ord(payload[0]))),
            ("src address", CrsfFrameAddress(ord(payload[1]))),
            ("parameter number", ord(payload[2])),
            ("parameter chunks", ord(payload[3])),
            ("parent folder", ord(payload[4])),
            # ("hidden", bytes_to_uint(payload[5]) >> 7),  # TODO: test with hidden fields
            ("data type", CrsfDataType(ord(payload[5]))),
            ("payload", unpack_sting(payload[6:]))  # TODO: Unpack more data
        )

    @staticmethod
    def decode_parameter_read(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("dst address", CrsfFrameAddress(ord(payload[0]))),
            ("src address", CrsfFrameAddress(ord(payload[1]))),
            ("parameter number", ord(payload[2])),
            ("parameter chunk number", ord(payload[3]))
        )

    @staticmethod
    def decode_parameter_write(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("dst address", CrsfFrameAddress(ord(payload[0]))),
            ("src address", CrsfFrameAddress(ord(payload[1]))),
            ("parameter number", ord(payload[2])),
            ("data", bytes_to_int_list(payload[3:]))
        )

    @staticmethod
    def decode_command(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("dst address", CrsfFrameAddress(ord(payload[0]))),
            ("src address", CrsfFrameAddress(ord(payload[1]))),
            ("command id", CrsfCommandID(ord(payload[2]))),
            ("command payload", bytes_to_int_list(payload[3:-1])),
            ("command crc", ord(payload[-1])),
            ("calculated crc", calc_crc(list_to_bytes([0x32] + bytes_to_int_list(payload[0:-1])), 'cmd'))  # FIXME
        )

    @staticmethod
    def decode_msp_resp(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("dst address", CrsfFrameAddress(ord(payload[0]))),
            ("src address", CrsfFrameAddress(ord(payload[1]))),
            ("MSP data raw", bytes_to_int_list(payload[2:])),
            ("MSP seq num", int(bytes_to_uint(payload[2]))),
            ("MSP payload length", int(ord(payload[3]))),
            ("MSP code", MspCodes(ord(payload[4]))),
            ("MSP payload", bytes_to_int_list(payload[5:4+int(ord(payload[3]))])),
            ("MSP checksum", bytes_to_int_list(payload[-1]))
        )

    @staticmethod
    def decode_msp_req(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("dst address", CrsfFrameAddress(ord(payload[0]))),
            ("src address", CrsfFrameAddress(ord(payload[1]))),
            ("MSP data raw", bytes_to_int_list(payload[2:])),
            ("MSP seq num", int(bytes_to_uint(payload[2]))),
            ("MSP payload length", int(ord(payload[3]))),
            ("MSP code", MspCodes(ord(payload[4]))),
            ("MSP payload", bytes_to_int_list(payload[5:-1])),
            ("MSP checksum", bytes_to_int_list(payload[-1]))
        )

    @staticmethod
    def decode_msp_write(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("dst address", CrsfFrameAddress(ord(payload[0]))),
            ("src address", CrsfFrameAddress(ord(payload[1]))),
            ("MSP data raw", bytes_to_int_list(payload[2:])),
            ("MSP seq num", int(bytes_to_uint(payload[2]))),
            ("MSP payload length", int(ord(payload[3]))),
            ("MSP code", MspCodes(ord(payload[4]))),
            ("MSP payload", bytes_to_int_list(payload[5:-1])),
            ("MSP checksum", bytes_to_int_list(payload[-1]))
        )

    @staticmethod
    def decode_attitude(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("pitch", float((ord(payload[0]) << 8) + ord(payload[1])) / 1000),
            ("roll", float((ord(payload[2]) << 8) + ord(payload[3])) / 1000),
            ("yaw", float((ord(payload[4]) << 8) + ord(payload[5])) / 1000)
        )

    @staticmethod
    def decode_other(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
        )

    def decode(self):
        func_name = "decode_{}".format(self.type.name).lower()
        if hasattr(self, func_name):
            decode = getattr(self, func_name)
            self.payload = decode(self.payload_raw)
        else:
            self.payload = self.decode_other(self.payload_raw)

    def __str__(self):
        return str(self.payload)


class CrsfFrame(object):
    raw = None
    address = None
    data_size = 0
    frame_type = 0
    payload = None
    crc = None

    def unpack(self):
        buf = self.raw
        self.address = ord(buf[0])
        self.data_size = ord(buf[1])
        self.frame_type = ord(buf[2])
        self.payload = buf[3:-1]
        self.crc = ord(buf[-1])

    def verify_crc(self):
        self.crc = CrsfCrc(self.crc, self.raw[2:-1])

    def verify_zero(self):
        if self.data_size == 0 and self.frame_type == 0 and self.crc.calculated_crc == 0:
            return False
        return True

    def decode(self):
        self.address = CrsfFrameAddress(self.address)
        self.data_size = ord(self.raw[1])
        self.frame_type = CrsfFrameType(self.frame_type)
        self.payload = CrsfPayload(self.frame_type, self.payload)

    def __str__(self):
        return "Data size: {}; Data type: {}; " \
               "Payload: {}; CRC: {};".format(self.data_size, self.frame_type.name,
                                              self.payload, self.crc)

    @property
    def fields(self):
        return (
            ('raw', bytes_to_int_list(self.raw)),
            # ('address', self.address),
            ('size', self.data_size),
            ('type', self.frame_type),
            ('payload', self.payload),
            ('crc', str(self.crc))
        )


class Reader(object):
    bytes_skipped = 0
    bytes_total = 0

    frames_bad = 0
    frames_decoded = 0
    frames_total = 0

    crc_wrong = 0
    crc_ok = 0

    def __init__(self, reader_type='file', path=None, raw_log=None, baudrate=420000):
        self.reader_type = reader_type
        self.reader_path = path
        self.reader = None
        self.raw_log_path = raw_log
        self.raw_log = None

        self.baudrate = baudrate

        self.__init_raw_log()
        self.__open_reader()

    def __init_raw_log(self):
        if self.raw_log_path is not None:
            self.raw_log = open(self.raw_log_path, 'wb')

    def __open_reader(self):
        if self.reader_type == 'file':
            self.reader = open(self.reader_path, 'rb')
        elif self.reader_type == 'serial':
            self.reader = serial.Serial()
            self.reader.port = self.reader_path
            self.reader.baudrate = int(self.baudrate)
            # self.reader.timeout(1)
            self.reader.open()
        else:
            print("Unknown reader type")
            sys.exit(1)

    def read_data(self, length=1):
        if length <= 0:
            return ''

        self.bytes_total += length
        data = self.reader.read(length)

        if self.raw_log:
            self.raw_log.write(data)

        return data

    def read_frame(self, address=None):
        self.frames_total += 1
        LOG.debug("%s - Reading frame" % self.frames_total)

        buf = [address]
        buf += self.read_data(1)  # length
        if ord(buf[1]) > MAX_FRAME_SYZE:
            return None

        buf += self.read_data(1)  # type
        buf += self.read_data(ord(buf[1]) - 2)  # payload
        buf += self.read_data(1)  # crc

        try:
            frame = CrsfFrame()
            frame.raw = buf
            frame.unpack()
            frame.verify_crc()
            if not frame.crc.verify():
                self.frames_bad += 1
                self.crc_wrong += 1
                return None
            elif not frame.verify_zero():
                LOG.debug("Frame #%s - Zero frame" % self.frames_total)
                return None
            elif frame in skip_types:
                return None

            self.crc_ok += 1
            LOG.debug("Frame #%s - crc ok" % self.frames_total)
            frame.decode()
            self.frames_decoded += 1
            return frame

        except Exception as err:
            self.frames_bad += 1
            LOG.error("Frame #%s - exception while reading/decoding frame" % self.frames_total)
            LOG.info(bytes_to_int_list(buf))
            LOG.exception(err)


def parse_args():
    parser = argparse.ArgumentParser(description='Script for parsing Crossfire protocol')
    parser.add_argument('--type', choices=['serial', 'file'], default='file')
    parser.add_argument("--path", action="store", required=True, help="path")
    parser.add_argument("--baudrate", action="store", help="read serial", default=420000)
    parser.add_argument("--show_types", action="store", help="Show specific frame types")
    parser.add_argument("--skip_types", action="store", help="Skip specific frame types")
    parser.add_argument("--extended_view", action="store_true", help="Extended view")
    parser.add_argument("--debug", action="store_true", help="debug level")
    # parser.add_argument("--raw-log", action="store", help="raw log path")

    return parser.parse_args()


def print_frame(frame):
    LOG.info("==========New frame===========")

    for field in frame.fields:
        if hasattr(field[1], 'payload'):
            LOG.info("payload:")
            for j in getattr(field[1], 'payload'):
                name = j[0]
                value = j[1]
                if isinstance(value, Enum) and hasattr(value, 'name'):
                    value = getattr(value, 'name')
                LOG.info("  %s: %s" % (name, value))
        elif hasattr(field[1], 'name'):
            LOG.info("%s: %s" % (field[0], field[1].name))
        else:
            LOG.info("%s: %s" % (field[0], field[1]))


if __name__ == "__main__":
    args = parse_args()
    LOG = setup_logging()
    LOG.debug("Cli args: %s", args)

    if args.skip_types:
        skip_types = [CrsfFrameType[i] for i in args.skip_types.split(',')]
    else:
        skip_types = []

    if args.show_types:
        show_types = [CrsfFrameType[i] for i in args.show_types.split(',')]
    else:
        show_types = []

    if args.debug:
        LOG.setLevel(logging.DEBUG)

    reader = Reader(args.type, path=args.path, baudrate=args.baudrate)

    try:
        while True:
            byte = reader.read_data()
            if byte == "":
                break
            # elif bytes_to_uint(byte) in [CrsfFrameAddress(e).value for e in CrsfFrameAddress.__members__.values()]:
            elif ord(byte) == SYNC_BYTE:
                frame = reader.read_frame(address=byte)
                if frame is None:
                    continue
                if frame.frame_type not in show_types and len(show_types) > 0:
                    continue
                if frame.frame_type in skip_types:
                    continue

                if args.extended_view:
                    print_frame(frame)
                else:
                    LOG.info(frame)
            else:
                reader.bytes_skipped += 1
    except KeyboardInterrupt as err:
        print(err)

    print("Bytes skipped: %s" % reader.bytes_skipped)
    print("Bytes total: %s" % reader.bytes_total)
    print("Frames bad: %s" % reader.frames_bad)
    print("Frames decoded: %s" % reader.frames_decoded)
    print("Frames total: %s" % reader.frames_total)
    print("CRC wrong: %s" % reader.crc_wrong)
    print("CRC ok: %s" % reader.crc_ok)
