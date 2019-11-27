# ESP-12S


### Know ESP8266 (Cloud) devices
| Name | Internal name | Device ID |
| ---- | ------        | ----      |
| - | ESP_GENERIC_HW_ID | 200704 (0x31000)
| Tango 2 | ESP_TANGO_V2 | 204800 (0x32000)
| Crossfire | ESP_CROSSFIRE | 208896 (0x33000)
| Racetracker 2 | ESP_RACETRACKER2 | 212992 (0x34000)
| Fusion | ESP_FUSTION | 217088 (0x35000)
| Micro TX Remote | CROSSFIRE_MICRO_TX_REMOTE | 81920 (0x14000)



### Basic operations

Write firmware

```
esptool.py --port /dev/ttyUSB1 write_flash --flash_mode dio --flash_size 4MB 0x0 firmware.bin
```

Read firmware
```
esptool.py --port /dev/ttyUSB1 read_flash 0 4MB firmware.backup.bin
```


### Diff two binary files (ugly)
```
diff <(xxd firmware1.bin) <(firmware2.bin)
```