### read_data.py --path <bin_log_file>

### `--path` [`<filename>`]
Path to data source. Binary log or serial port.

### `--type` [`file`/`serial`]
##### file mode
Read data from binary dump.

##### serial mode
Read data directly from the serial port and decrypt in near real-time.

### `--baudrate` [`int number`]
Usually CRSF protocol works on 4200000. But, for instance, internal ESP module and TX works on 500000.

### `--show_type` [`CRSF frame type`]
Show only specific CRSF frame types. Use names from `crsf_codes.CrsfFrameType`.

### `--skip_type` [`CRSF frame type`]
Do not print specific CRSF frame types. Use names from `crsf_codes.CrsfFrameType`.

### `--extended_view`
Show output in more readable format

---

### dump_rt.py

### send_data.py