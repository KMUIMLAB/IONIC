# Postprocess Data
- This repository is for postprocessing the acquired data.
- You can remove unused columns and add postprocessed columns.


## Setting
- Use `requirements.txt` for installing the required packages.

``` bash
$ pip install -r ./requirements.txt
```

- Get Merged data from `Process_data` in this repository
- Download map data as follows. Shape files were obtained from some Gyeonggi-do and Seoul areas.
    Map data can be installed using Dropbox link as follows:
    ``` bash
    $ wget https://www.dropbox.com/s/4riq4hko17d8ldi/map_data.zip
    ```
    Unzip map_data.zip file downloaded above.
    ``` bash
    $ unzip -q map_data.zip -d ./map_data
    ```

## Usage
- `postprocess.py` : Postprocessing to remove unused columns or to obtain new columns.
    
### Postprocessing
1. Put the merged data and map data in the same directory
    ```
    | data
       | 19404
            | merged.csv 
       | 19443
       | 19485
       | ...
    | map_data
       | selected.shp
       | selected.cpg
       | ...
    | postprocess.py
    ...
    ```
2. Modify `config.py` for your purpose
    - `postprocess_list` : the post-processing list you want to use
    - `folder_name` : Put the folder name list, if you want to work on only specific folders within the 'data' folder
    - `curvature_columns` : When adding a curvature column, put 'onlycurve' if you want to add only curvature data, or 'all' if you want to add related coordinate data as well.

    ```
    Config = {'postprocess_list' : ['remove_unused_column', 'add_driving_cycle', 'add_curvature'],
          'folder_name' : ['19485','77777'], # default = None
          'curvature_columns' : 'onlycurv',
          }
    ```
4. Run `postprocess.py`
    ``` bash
    $ python add_columns.py
    ```
    You can see `postprocess` folder is newly created, where merged data are postprocessed into the same file in each directory.
