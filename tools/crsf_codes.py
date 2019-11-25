from enum import Enum, unique


@unique
class CrsfFrameAddress(Enum):
    # NEW addresses
    # "Cloud" devices ESPCrossfire, ESPFustion, ESPGenericHwId, ESPRaceTracker2, ESPTangoV2
    ESP_MODULE = 0x12
    TBS_FUSION = 0x14
    VTX = 0xCE

    # 0x28
    UNKNOWN_0x01 = 0x01
    UNKNOWN_0x0C = 0x0C
    UNKNOWN_0x16 = 0x16

    '''
        ==========New frame===========
        raw: [200, 8, 52, 25, 0, 16, 231, 46, 0, 32]
        size: 8
        type: CrsfFrameType.UNKNOWN_0x34
        payload:
          raw: [25, 0, 16, 231, 46, 0]
          rx_device: CrsfFrameAddress.UNKNOWN_0x19
          tx_device: CrsfFrameAddress.BROADCAST
          payload: [16, 231, 46, 0]
        crc: OK
    '''
    UNKNOWN_0x19 = 0x19

    '''
        ==========New frame===========
        raw: [200, 8, 15, 206, 48, 17, 22, 211, 0, 168]
        size: 8
        type: CrsfFrameType.UNKNOWN_0x0F
        payload:
          raw: [206, 48, 17, 22, 211, 0]
          rx_device: CrsfFrameAddress.VTX
          tx_device: CrsfFrameAddress.UNKNOWN_0x30
          payload: [17, 22, 211, 0]
        crc: OK


        payload still consistent
        VTX -> RX -> TX -> uart to ESP-12s

    '''
    UNKNOWN_0x30 = 0x30
    UNKNOWN_0xAA = 0xAA
    UNKNOWN_0xAC = 0xAC

    # BF codes
    BROADCAST = 0x00
    USB = 0x10
    TBS_CORE_PNP_PRO = 0x80
    RESERVED1 = 0x8A
    CURRENT_SENSOR = 0xC0
    GPS = 0xC2
    TBS_BLACKBOX = 0xC4
    FLIGHT_CONTROLLER = 0xC8
    RESERVED2 = 0xCA
    RACE_TAG = 0xCC
    RADIO_TRANSMITTER = 0xEA  # TBSTangoII
    CRSF_RECEIVER = 0xEC
    CRSF_TRANSMITTER = 0xEE


@unique
class CrsfFrameType(Enum):
    UNKNOWN_0x0F = 0x0F


    '''
        ==========New frame===========
        raw: [200, 13, 52, 172, 1, 174, 2, 61, 0, 33, 1, 0, 0, 0, 10]
        address: CrsfFrameAddress.FLIGHT_CONTROLLER
        size: 13
        type: CrsfFrameType.UNKNOWN_0x34
        payload:
          raw: [172, 1, 174, 2, 61, 0, 33, 1, 0, 0, 0]
          rx_device: CrsfFrameAddress.UNKNOWN_0xAC
          tx_device: CrsfFrameAddress.UNKNOWN_0x01
          payload: ['\xac', '\x01', '\xae', '\x02', '=', '\x00', '!', '\x01', '\x00', '\x00', '\x00']
        crc: OK
        ==========New frame===========
        raw: [200, 8, 52, 25, 0, 195, 2, 61, 0, 30]
        address: CrsfFrameAddress.FLIGHT_CONTROLLER
        size: 8
        type: CrsfFrameType.UNKNOWN_0x34
        payload:
          raw: [25, 0, 195, 2, 61, 0]
          rx_device: CrsfFrameAddress.UNKNOWN_0x19
          tx_device: CrsfFrameAddress.BROADCAST
          payload: (3998403,)
        crc: OK

        -------------------------------
        payload depends on RX/TX devices
        if TX device is BROADCAST it looks like a time from start in ms
        22:08:19 - [188, 33, 65, 0] -int-> 4268476ms - 4268sec ~ 71min
        22:10:19 - [236, 29, 67, 0] -int-> 4398572ms - 4398sec ~ 73min

    '''
    UNKNOWN_0x34 = 0x34  # Potentially time or so
    UNKNOWN_0x38 = 0x38  # Potentially data frames (FW update)

    GPS = 0x02
    CF_VARIO = 0x07
    BATTERY_SENSOR = 0x08
    LINK_STATISTICS = 0x14
    RC_CHANNELS_PACKED = 0x16
    ATTITUDE = 0x1E
    FLIGHT_MODE = 0x21

    # Extended Header Frames, range: 0x28 to 0x96
    DEVICE_PING = 0x28
    DEVICE_INFO = 0x29
    PARAMETER_SETTINGS_ENTRY = 0x2B
    PARAMETER_READ = 0x2C
    PARAMETER_WRITE = 0x2D
    COMMAND = 0x32

    # MSP commands
    MSP_REQ = 0x7A  # response request using msp sequence as command
    MSP_RESP = 0x7B  # reply with 58 byte chunked binary
    MSP_WRITE = 0x7C  # write with 8 byte chunked binary (OpenTX outbound telemetry buffer limit)
    DISPLAYPORT_CMD = 0x7D  # displayport control command


class CrsfHardwareID(Enum):
    CORE_PNP_PRO = 8192                # 0x02000
    OSD_VTX = 8448                     # 0x02100
    GPS = 12288                        # 0x03000
    DIGITAL_CURRENT_SENSOR = 16384     # 0x04000
    BLACKBOX = 20480                   # 0x05000
    OLED_DOMINATOR_RX = 40960          # 0x0a000

    CROSSFIRE_TX = 65536               # 0x10000
    CROSSFIRE_DIVERSITY_RX = 69632     # 0x11000
    NANO_RX = 73728                    # 0x12000
    CROSSFIRE_MICRO_TX = 77824         # 0x13000
    CROSSFIRE_MICRO_TX_REMOTE = 81920  # 0x14000
    TANGO = 106496                     # 0x1a000
    COLIBRI_RACE_TBSFLIGHT = 114688    # 0x1c000
    BRUSHLESS_WHOOP = 114944           # 0x1c100
    BRUSHED_WHOOP = 115200             # 0x1c200

    # VTX
    UNIFY_EVO = 131072                 # 0x20000
    UNIFY_PRO32 = 135168               # 0x21000
    UNIFY_PRO32_NANO = 139264          # 0x22000

    # "Cloud" devices
    ESP_GENERIC_HW_ID = 200704         # 0x31000
    ESP_TANGO_V2 = 204800              # 0x32000
    ESP_CROSSFIRE = 208896             # 0x33000
    ESP_RACETRACKER2 = 212992          # 0x34000
    ESP_FUSTION = 217088               # 0x35000

    TANGO_II = 262144                  # 0x40000
    FUSION = 393216                    # 0x60000
    COLIBRI = 819200                   # 0xc8000
    POWERCUBE_ESC = 860160             # 0xd2000

