# Preprocess Data
This repository is for adding driving cycle and curvature columns.

## Setting
Use `requirements.txt` for installing the required packages.

``` bash
$ pip install -r ./requirements.txt
```

## Usage
- `add_columns.py` : Add 'Driving Cycle' & 'Curvature' Columns.
    
### Add 'Driving Cycle' & 'Curvature' Columns
1. Put the preprocessed data in the same directory
    ```
    | data
       | 19404
            | merged.csv 
       | 19443
       | 19485
       | ...
    | map_data
       | selected.shp
       | ...
    | add_columns.py
    | preprocess_raw.py
    ...
    ```
2. Map Data can be installed using Dropbox link as follows:
    ``` bash
    $ wget https://www.dropbox.com/s/4riq4hko17d8ldi/map_data.zip
    ```
   Unzip map_data.zip file downloaded above.
    ``` bash
    $ unzip -q map_data.zip -d ./map_data
    ```
3. Put map_data folder in the same directory.
    ```
    | data
       | 19404
            | merged.csv 
       | 19443
       | 19485
       | ...
    | map_data
       | selected.shp
       | ...
    | add_columns.py
    | preprocess_raw.py
    ...
    ```
4. Run `add_columns.py`
    ``` bash
    $ python add_columns.py
    ```
    You can see `add_columns` folder is newly created, where merged data are added columns into the same file in each directory.
