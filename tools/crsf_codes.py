from enum import Enum, unique


@unique
class CrsfFrameAddress(Enum):
    # NEW addresses
    # "Cloud" devices ESPCrossfire, ESPFustion, ESPGenericHwId, ESPRaceTracker2, ESPTangoV2
    ESP_MODULE = 0x12  # or Bluetooth
    FUSION = 0x14
    VTX = 0xCE

    UNKNOWN_0x01 = 0x01
    UNKNOWN_0x0C = 0x0C
    UNKNOWN_0x16 = 0x16

    '''
        Example:
        raw: [200, 8, 52, 25, 0, 16, 231, 46, 0, 32]
    '''
    UNKNOWN_0x19 = 0x19

    '''
        Example:
        raw: [200, 8, 15, 206, 48, 17, 22, 211, 0, 168]

        Comments:
        payload still consistent
        VTX -> RX -> TX -> uart to ESP-12s

    '''
    UNKNOWN_0x30 = 0x30
    UNKNOWN_0xAA = 0xAA
    UNKNOWN_0xAE = 0xAE
    UNKNOWN_0xAC = 0xAC

    # BF codes
    BROADCAST = 0x00
    USB = 0x10
    CORE_PNP_PRO = 0x80
    RESERVED1 = 0x8A
    CURRENT_SENSOR = 0xC0
    GPS = 0xC2
    BLACKBOX = 0xC4
    FLIGHT_CONTROLLER = 0xC8
    RESERVED2 = 0xCA
    RACE_TAG = 0xCC
    RADIO_TRANSMITTER = 0xEA  # TangoII
    RESERVED = 0xEB
    CRSF_RECEIVER = 0xEC
    CRSF_TRANSMITTER = 0xEE


@unique
class CrsfFrameType(Enum):
    ###############################################
    # Bootloader related
    # START_BOOTLOADER = 0x0A
    # ERASE_MEMORY = 0x0B
    # UNKNOWN_0x28 = 0x28
    ###############################################

    '''
        Example:
        raw: [200, 13, 52, 172, 1, 174, 2, 61, 0, 33, 1, 0, 0, 0, 10]
        -------------------------------
        Comment:
        payload depends on RX/TX devices
        if TX device is BROADCAST it looks like a time from start in ms
        22:08:19 - [188, 33, 65, 0] -int-> 4268476ms - 4268sec ~ 71min
        22:10:19 - [236, 29, 67, 0] -int-> 4398572ms - 4398sec ~ 73min

    '''
    UNKNOWN_0x34 = 0x34  # Potentially time or so

    '''
        Example:
        raw: [200, 37, 54, 238, 18, 1, 102, 148, 7, 44, 124, 247, 194, 178, 163, 13, 103, 176, 31, 34, 5, 43, 100, 127, 171, 127, 107, 11, 137, 46, 91, 15, 240, 72, 73, 226, 192, 213, 131]
    
    '''
    UNKNOWN_0x36 = 0x36  # Data frames ESP. Starts after WiFi connection and connection to internet.
    UNKNOWN_0x38 = 0x38  # Potentially FW update data frames. Also technical info.
    UNKNOWN_0x8D = 0x8D


    GPS = 0x02
    CF_VARIO = 0x07
    BATTERY_SENSOR = 0x08
    HEARTBEAT = 0x0B

    '''
        Comment:
        ~15.1s delay between frames with Pro32
    '''
    VTX = 0x0F
    LINK_STATISTICS = 0x14
    RC_CHANNELS_PACKED = 0x16
    ATTITUDE = 0x1E
    FLIGHT_MODE = 0x21

    # Extended Header Frames, range: 0x28 to 0x96
    '''
        Example:
        USB->BROADCAST: [200, 4, 40, 0, 16, 134]
        USB->VTX: [206, 16, 10, 10, 236]
    '''
    DEVICE_PING = 0x28
    DEVICE_INFO = 0x29
    PARAMETER_SETTINGS_ENTRY = 0x2B
    PARAMETER_READ = 0x2C
    PARAMETER_WRITE = 0x2D

    # Commands
    COMMAND = 0x32

    # MSP commands
    MSP_REQ = 0x7A  # response request using msp sequence as command
    MSP_RESP = 0x7B  # reply with 58 byte chunked binary
    MSP_WRITE = 0x7C  # write with 8 byte chunked binary (OpenTX outbound telemetry buffer limit)
    DISPLAYPORT_CMD = 0x7D  # displayport control command


@unique
class CrsfCommandID(Enum):
    FC = 0x01
    BLUETOOTH = 0x03
    OSD = 0x05
    VTX = 0x08
    LED = 0x09

    UNKNOWN = 0x0A  # Start bootloader?


@unique
class CrsfVtxInterface(Enum):
    SMART_AUDIO_V1 = 0
    SMART_AUDIO_V2 = 1
    CRSF = 6


@unique
class CrsfVtxXPower(Enum):
    POWER_25mW = 0
    POWER_100mW = 1  # or 200mW
    POWER_200mW = 2  # or 500mW
    POWER_800mW = 3


@unique
class CrsfVtxPitmode(Enum):
    OFF = 0
    IN_BAND = 1
    OUT_BAND = 2


@unique
class CrsfDataType(Enum):
    UINT8 = 0
    INT8 = 1
    UINT16 = 2
    INT16 = 3
    FLOAT = 8
    TEXT_SELECTION = 9
    STRING = 10
    FOLDER = 11
    INFO = 12
    COMMAND = 13
    OUT_OF_RANGE = 127

    UNKNOWN_0x82 = 130

    #           10  0  3  0x8D E   x    i    t        P   i    t    M   o    d    e
    # [16, 206, 10, 0, 3, 141, 69, 120, 105, 116, 32, 80, 105, 116, 77, 111, 100, 101, 0, 0, 15, 0]
    # ('dst address', <CrsfFrameAddress.USB: 16>)
    # ('src address', <CrsfFrameAddress.VTX: 206>)
    # ('parameter number', 10)
    # ('parameter chunks', 0)
    # ('parent folder', 3)
    # ('data type', 'UNKNOWN_0x8D')
    # ('payload', 'Exit PitMode\x00\x00\x0f\x00')
    UNKNOWN_0x8D = 141


@unique
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

