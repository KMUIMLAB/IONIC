# Data Processing Example
- This code is an example for processing the acquired data.
- You can merge all data into an DataFrame in 100Hz by this code.
## Available data list
- CAN
- GNSS
- bio

## Getting Started
- Check the stucture of the data directory. It should look like the example below.
    ```
    -- 17399 ## parent directory
        |-- bio
            |-- ACC.csv
            |-- BVP.csv
            |-- EDA.csv
            |-- HR.csv
            |-- IBI.csv
            |-- info.txt
            |-- tags.csv
            |-- TEMP.csv
        |-- CAN
            |-- 'CAN_data_time'.csv
        |-- GNSS
            |-- 'GNSS_data'
        |-- START_END_TOTAL_*km.csv  ## Not used in code
    ```

- Modify `Config.py` for your purpose and then execute `process_example.py`.
1. `Config.py`
    - In `'data_names'`, put the data name that will be used.
    - In `'data_freq'`, put the frequency that you want to set for the result. Only multiple of 10 is available for frequency(10, 100, 1000, ...).
    - In `'path'`, put the parent directory of acquired data
    ``` python
    config = {'data_names': ['CAN', 'bio', 'GNSS'],
           'data_freq': 100,
           'path': './17399'}
    ```
2. `process_example.py`
   - You don't need to modify this file.
    ``` python
    python process_example.py
    ```