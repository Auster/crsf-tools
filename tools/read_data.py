#!/usr/bin/env python

import sys
import argparse
import logging
import struct

import serial

from msp_codes import MspCodes
from crsf_codes import CrsfFrameAddress, CrsfFrameType

SYNC_BYTE = 0xC8

crc8tab = [
    0x00, 0xD5, 0x7F, 0xAA, 0xFE, 0x2B, 0x81, 0x54, 0x29, 0xFC, 0x56, 0x83, 0xD7, 0x02, 0xA8, 0x7D,
    0x52, 0x87, 0x2D, 0xF8, 0xAC, 0x79, 0xD3, 0x06, 0x7B, 0xAE, 0x04, 0xD1, 0x85, 0x50, 0xFA, 0x2F,
    0xA4, 0x71, 0xDB, 0x0E, 0x5A, 0x8F, 0x25, 0xF0, 0x8D, 0x58, 0xF2, 0x27, 0x73, 0xA6, 0x0C, 0xD9,
    0xF6, 0x23, 0x89, 0x5C, 0x08, 0xDD, 0x77, 0xA2, 0xDF, 0x0A, 0xA0, 0x75, 0x21, 0xF4, 0x5E, 0x8B,
    0x9D, 0x48, 0xE2, 0x37, 0x63, 0xB6, 0x1C, 0xC9, 0xB4, 0x61, 0xCB, 0x1E, 0x4A, 0x9F, 0x35, 0xE0,
    0xCF, 0x1A, 0xB0, 0x65, 0x31, 0xE4, 0x4E, 0x9B, 0xE6, 0x33, 0x99, 0x4C, 0x18, 0xCD, 0x67, 0xB2,
    0x39, 0xEC, 0x46, 0x93, 0xC7, 0x12, 0xB8, 0x6D, 0x10, 0xC5, 0x6F, 0xBA, 0xEE, 0x3B, 0x91, 0x44,
    0x6B, 0xBE, 0x14, 0xC1, 0x95, 0x40, 0xEA, 0x3F, 0x42, 0x97, 0x3D, 0xE8, 0xBC, 0x69, 0xC3, 0x16,
    0xEF, 0x3A, 0x90, 0x45, 0x11, 0xC4, 0x6E, 0xBB, 0xC6, 0x13, 0xB9, 0x6C, 0x38, 0xED, 0x47, 0x92,
    0xBD, 0x68, 0xC2, 0x17, 0x43, 0x96, 0x3C, 0xE9, 0x94, 0x41, 0xEB, 0x3E, 0x6A, 0xBF, 0x15, 0xC0,
    0x4B, 0x9E, 0x34, 0xE1, 0xB5, 0x60, 0xCA, 0x1F, 0x62, 0xB7, 0x1D, 0xC8, 0x9C, 0x49, 0xE3, 0x36,
    0x19, 0xCC, 0x66, 0xB3, 0xE7, 0x32, 0x98, 0x4D, 0x30, 0xE5, 0x4F, 0x9A, 0xCE, 0x1B, 0xB1, 0x64,
    0x72, 0xA7, 0x0D, 0xD8, 0x8C, 0x59, 0xF3, 0x26, 0x5B, 0x8E, 0x24, 0xF1, 0xA5, 0x70, 0xDA, 0x0F,
    0x20, 0xF5, 0x5F, 0x8A, 0xDE, 0x0B, 0xA1, 0x74, 0x09, 0xDC, 0x76, 0xA3, 0xF7, 0x22, 0x88, 0x5D,
    0xD6, 0x03, 0xA9, 0x7C, 0x28, 0xFD, 0x57, 0x82, 0xFF, 0x2A, 0x80, 0x55, 0x01, 0xD4, 0x7E, 0xAB,
    0x84, 0x51, 0xFB, 0x2E, 0x7A, 0xAF, 0x05, 0xD0, 0xAD, 0x78, 0xD2, 0x07, 0x53, 0x86, 0x2C, 0xF9
]


def unpack_sting(bytes_list):
    format = "c" * len(bytes_list)
    return struct.pack(">{}".format(format), *bytes_list)


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


def calc_crc(buf):
    length = len(buf)
    crc = 0
    for i in range(length):
        crc = crc8tab[crc ^ int(ord(buf[i]))]
    return crc


class CrsfCrc(object):
    def __init__(self, crc, buf):
        self.buf = buf
        self.crc = crc
        self.calculated_crc = calc_crc(buf)

    def __str__(self):
        if self.crc == self.calculated_crc:
            return "OK"
        else:
            LOG.error("Wrong CRC: {} != {}".format(self.crc, self.calculated_crc))
            return "ERROR"

    def verify(self):
        return self.crc == self.calculated_crc


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
    def decode_device_info(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("rx_device", CrsfFrameAddress(ord(payload[0]))),
            ("tx_device", CrsfFrameAddress(ord(payload[1]))),
            ("info", "".join(payload[2:-15])),
            ("parameter count", ord(payload[-2])),
            ("device info version", ord(payload[-1]))
        )

    @staticmethod
    def decode_unknown_0x34(payload):
        # try:
        #     data = struct.unpack("<I", "".join(payload[2:]))
        # except:
        #     data = payload

        return (
            ("raw", bytes_to_int_list(payload)),
            ("rx_device", CrsfFrameAddress(ord(payload[0]))),
            ("tx_device", CrsfFrameAddress(ord(payload[1]))),
            ("payload", bytes_to_int_list(payload[2:]))
        )

    @staticmethod
    def decode_unknown_0x0f(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("rx_device", CrsfFrameAddress(ord(payload[0]))),
            ("tx_device", CrsfFrameAddress(ord(payload[1]))),
            ("payload", bytes_to_int_list(payload[2:]))
        )

    @staticmethod
    def decode_parameter_write(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("rx_device", CrsfFrameAddress(ord(payload[0]))),
            ("tx_device", CrsfFrameAddress(ord(payload[1]))),
            ("payload", bytes_to_int_list(payload[2:]))
        )

    @staticmethod
    def decode_parameter_read(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("rx_device", CrsfFrameAddress(ord(payload[0]))),
            ("tx_device", CrsfFrameAddress(ord(payload[1]))),
            ("payload", bytes_to_int_list(payload[2:]))
        )

    @staticmethod
    def decode_parameter_settings_entry(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("rx_device", CrsfFrameAddress(ord(payload[0]))),
            ("tx_device", CrsfFrameAddress(ord(payload[1]))),
            ("payload", unpack_sting(payload[2:]))
        )

    @staticmethod
    def decode_msp_resp(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("rx_device", CrsfFrameAddress(ord(payload[0]))),
            ("tx_device", CrsfFrameAddress(ord(payload[1]))),
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
            ("rx_device", CrsfFrameAddress(ord(payload[0]))),
            ("tx_device", CrsfFrameAddress(ord(payload[1]))),
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
            ("rx_device", CrsfFrameAddress(ord(payload[0]))),
            ("tx_device", CrsfFrameAddress(ord(payload[1]))),
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
    def decode_battery_sensor(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
            ("voltage", float((ord(payload[0]) << 8) + ord(payload[1])) / 10),
            ("current", float((ord(payload[2]) << 8) + ord(payload[3])) / 10),
            ("consumption", (ord(payload[4]) << 16) + (ord(payload[5]) << 8) + ord(payload[6])),
            ("battary procentage", bytes_to_uint(payload[7])),
        )

    @staticmethod
    def decode_other(payload):
        return (
            ("raw", bytes_to_int_list(payload)),
        )

    def decode(self):
        try:
            func_name = "decode_{}".format(self.type.name).lower()
            decode = getattr(self, func_name)
            self.payload = decode(self.payload_raw)
        except AttributeError as err:
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
        if self.address == 0 and self.data_size == 0 and self.frame_type == 0 and self.crc.calculated_crc == 0:
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
        buf += self.read_data(1)  # type
        buf += self.read_data(ord(buf[1]) - 2)  # payload
        buf += self.read_data(1)

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
                LOG.debug("Zero frame")
                return None
            elif frame in skip_types:
                return None

            self.crc_ok += 1
            LOG.debug("%s - crc ok" % self.frames_total)
            frame.decode()
            self.frames_decoded += 1
            return frame

        except Exception as err:
            self.frames_bad += 1
            LOG.error("%s - exception while reading/decoding frame" % self.frames_total)
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
            elif bytes_to_uint(byte) == SYNC_BYTE:
                frame = reader.read_frame(address=byte)
                if frame is None:
                    continue
                if frame.frame_type not in show_types and len(show_types) > 0:
                    continue
                if frame.frame_type in skip_types:
                    continue

                if args.extended_view:
                    LOG.info("==========New frame===========")
                    for field in frame.fields:
                        if hasattr(field[1], 'payload'):
                            LOG.info("payload:")
                            for j in getattr(field[1], 'payload'):
                                LOG.info("  %s: %s" % (j[0], j[1]))
                        elif hasattr(field[1], 'name'):
                            LOG.info("%s: %s" % (field[0], field[1].name))
                        else:
                            LOG.info("%s: %s" % (field[0], field[1]))
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
