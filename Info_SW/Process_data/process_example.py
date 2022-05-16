import pathlib
import datetime
import numpy as np
import pandas as pd
from pyparsing import col

import config

def process_CAN(path, freq):
    print("CAN processing starts.")
    df = pd.read_csv(path, low_memory= False)
    df = df.rename(columns={'timestamp': 'TimestampFromDevice',
                            'timestamp2': 'Timestamp'})

    categorical_dict = {'CF_Ems_EngStat': {'ES(Engine Stop)': 0, 'PL(Part Load)': 1, 'PU(Pull)': 2,
                                        'PUC(Fuel Cut off)': 3, 'ST(Start)': 4, 'IS(Idle speed)': 5},
                        'CF_Tcu_TarGe': {'If N or P are detected(No frictional conncetion)': 0,
                                        'Reverse': -1, '1st speed': 1, '2nd speed': 2, '3rd speed': 3,
                                         '4th speed': 4, '5th speed': 5, '6th speed': 6},
                        'CYL_PRES_FLAG': {'On': 1, 'Off': 0},
                        'CF_Gway_HeadLampHigh': {'On': 1, 'Off': 0},
                        'CF_Gway_HeadLampLow': {'On': 1, 'Off': 0},
                        'CF_Hcu_DriveMode' : {'Normal': 0, 'Eco' : 1, 'Sports': 2, 'Invalid' : -1},
                        'CR_Hcu_HevMod': {'Vehicle Stop': 0, 'Engine Generation': 1, 'Engine Generation/Motor Drive': 2,
                                          'Engine Generation/ Regeneration': 3, 'Engine Brake / Regeneration': 4,'Regeneration': 5, 'EV Propulsion': 6,
                                          'Engine Only Propulsion': 7, 'Power Researve': 8, 'Power Assist': 9, 'Power Assist': 10, 'None' : -1},
                         'CF_Ems_BrkForAct': {'On': 1, 'Off': 0},
                         'CF_Clu_InhibitD': {'(On)D': 1, 'Off': 0},
                         'CF_Clu_InhibitN': {'(On)N': 1, 'Off': 0},
                         'CF_Clu_InhibitP': {'(On)P': 1, 'Off': 0},
                        'CF_Clu_InhibitR': {'(On)R': 1, 'Off': 0}}

    for col in df.columns:
        if col in categorical_dict.keys():
            df[col] = df[col].interpolate(method='pad').fillna(method='bfill').fillna(method='ffill')

        elif col == 'CR_Ems_AccPedDep_Pc':
            df.loc[df[col] == 'Accelerator Pedal not activated', 'CR_Ems_AccPedDep_Pc'] = 0
            df.loc[df[col] == 'Accelerator Pedal fully activated', 'CR_Ems_AccPedDep_Pc'] = 100
            df.loc[df[col] == 'Accelerator Pedal is defective (fail state) or Non-ETC system (APS is not installed)', 'CR_Ems_AccPedDep_Pc'] = -1
            df.loc[df[col].notna(), 'CR_Ems_AccPedDep_Pc'] = df.loc[df[col].notna(), 'CR_Ems_AccPedDep_Pc'].astype('float64')
            df[col] = df[col].interpolate(method='pad').fillna(method='bfill').fillna(method='ffill').astype('float64')

        elif col == 'CF_Clu_VehicleSpeed':
            df.loc[df[col] == '0x0~0xFE:Speed', 'CF_Clu_VehicleSpeed'] = 0
            df.loc[df[col].notna(), 'CF_Clu_VehicleSpeed'] = df.loc[df[col].notna(), 'CF_Clu_VehicleSpeed'].astype('float64')
            df[col] = df[col].interpolate().fillna(method='bfill').fillna(method='ffill').astype('int64')

        elif col == 'CR_Hcu_EcoLvl':
            df.loc[df[col] == 'Not Display', 'CR_Hcu_EcoLvl'] = -1
            df[col] = df[col].interpolate(method='pad').fillna(method='bfill').fillna(method='ffill').astype('float64')


        elif col == 'CR_Brk_StkDep_Pc' or col == 'CR_Ems_EngSpd_rpm' or col == 'CR_Ems_VehSpd_Kmh' \
            or col == 'BAT_SOC' or col == 'CR_Hcu_HigFueEff_Pc' or col == 'CR_Hcu_NorFueEff_Pc' \
            or col == 'CR_Fatc_OutTempSns_C' or col == 'CR_Ems_EngColTemp_C':
            df[col] = df[col].interpolate().fillna(method='bfill').fillna(method='ffill').astype('float64')

        else :
            df[col] = df[col].interpolate().fillna(method='bfill').fillna(method='ffill')


    df = df.replace(categorical_dict)

    df['CF_Clu_Odometer'] = df['CF_Clu_Odometer'].round(2).astype('float64')

    int_col_list = ['CF_Clu_InhibitD', 'CF_Clu_InhibitN', 'CF_Clu_InhibitP', 'CF_Clu_InhibitR', 'CF_Ems_EngStat', 'CF_Tcu_TarGe', \
                    'CYL_PRES_FLAG', 'CF_Gway_HeadLampHigh', 'CF_Gway_HeadLampLow', 'CF_Ems_BrkForAct', 'CF_Hcu_DriveMode', \
                    'CR_Hcu_HevMod', 'CR_Brk_StkDep_Pc', 'CR_Ems_EngSpd_rpm', 'CR_Ems_VehSpd_Kmh', 'BAT_SOC', 'CR_Hcu_HigFueEff_Pc', \
                    'CR_Hcu_NorFueEff_Pc', 'CR_Fatc_OutTempSns_C', 'CR_Hcu_EcoLvl', 'CR_Ems_EngColTemp_C', 'CF_Clu_VehicleSpeed']
    for col in df.columns:
        if col in int_col_list:
            df[col] = df[col].astype('int64')
    print("CAN processing done.")
    return df


def reset_timestamp(df, freq):
    st_time = df['Timestamp'].iloc[0]
    end_time = df['Timestamp'].iloc[-1]
    period = 1 / freq
    new_timestamp = np.arange(st_time, end_time + period, period) * freq
    new_timestamp = pd.DataFrame(new_timestamp, columns=['Timestamp']).astype('int64')
    df['Timestamp'] = (df['Timestamp'] * freq).astype('int64')
    
    df = pd.merge(new_timestamp, df, how='outer', on='Timestamp')
    df = df.interpolate().ffill().bfill()
    df['Timestamp'] = df['Timestamp'] / freq        
    
    return df


def process_HOD_CAN(path, freq):
    print("HOD_CAN processing starts.")
    df = []
    for i, p in enumerate(path):
        tmp_df = pd.read_csv(p, low_memory=False)
        tmp_df = tmp_df.rename(columns={'TS': 'Timestamp'})
        if 'GT' in tmp_df.columns:
            tmp_df = tmp_df.drop(['GT'], axis=1)
        if 'TH' in tmp_df.columns:
            tmp_df = tmp_df.drop(['TH'], axis=1)
            
        tmp_df = reset_timestamp(tmp_df, freq)     
        if i == 0:
            df = tmp_df
        else:
            df = pd.concat([df, tmp_df], ignore_index=True, axis=0)
    
    if len(path) > 1:
        columns = df.columns
        tmp_np = df.to_numpy()
        timestamp_np = tmp_np[:, 0]
        indices = np.argsort(timestamp_np)
        tmp_np = tmp_np[indices]
        df = pd.DataFrame(tmp_np, columns=columns)

    print("HOD_CAN processing done.")
    return df


def process_bio(path, freq):
    print("BIO processing starts.")
    dfs = []
    st_time = -1
    max_end_time = -1
    data_period = 1 / freq
    for i, p in enumerate(path):
        if p.stem == "ACC":
            names = ["X", "Y", "Z"]
        elif p.stem == "IBI":
            continue
        else:
            names = [p.stem]
        df = pd.read_csv(p, names=names, low_memory=False)
        st_time = float(df.iloc[0, 0])
        feq = float(df.iloc[1, 0])
        period = 1 / feq
        data_num = df.iloc[2:].shape[0]
        end_time = st_time + (data_num - 1) * period
        if max_end_time < end_time:
            max_end_time = end_time
        timestamp = np.arange(st_time, end_time + period, period)

        df = df.iloc[2:, :]
        df.insert(0, 'Timestamp', timestamp)
        dfs.append(df)
    bio_df = np.arange(st_time, max_end_time + data_period, data_period)
    bio_df = bio_df * freq
    bio_df = pd.DataFrame(bio_df, columns=['Timestamp']).astype('int64')
    for df in dfs:
        df['Timestamp'] = (df['Timestamp'] * freq).astype('int64')
        bio_df = pd.merge(bio_df, df, how='left', on='Timestamp')
    bio_df['Timestamp'] = bio_df['Timestamp'] / freq
    bio_df = bio_df.interpolate().ffill().bfill()

    print("BIO processing done.")
    return bio_df


def process_gnss(path, freq):
    print("GNSS processing starts.")
    date = list(map(int, path.stem.split('_')))
    first = True
    cnt = 1
    with open(path, 'r', encoding='utf-8') as f:
        while True:
            line = f.readline()
            if line == '':
                break
            data = line.strip().split(',')
            if data[1] == '':
                continue
            else:
                time_only = data[1]
                hour = int(time_only[:2])
                minute = int(time_only[2:4])
                sec = int(time_only[4:6])
                msec = int(time_only[7:]) * 10000
                dt = datetime.datetime(date[0], date[1], date[2], hour, minute, sec, msec)
                timestamp = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
                data[1] = f"{timestamp:.2f}"

                lat_dd = float(data[2][:2])
                lon_dd = float(data[4][:3])

                lat_mm = float(data[2][2:]) / 60
                lon_mm = float(data[4][3:]) / 60
        
                lat = round(lat_dd + lat_mm, 7)
                lon = round(lon_dd + lon_mm, 7)
                data[2] = lat
                data[4] = lon
                if data[13] == '':
                    data[13] = -1.0
                else:
                    data[13] = float(data[13])
                data = np.array(data, dtype='object')
                try:
                    if first:
                        gnss_np = data
                        first = False
                    else:
                        gnss_np = np.vstack([gnss_np, data])
                except:
                    continue
            print(f"{cnt} GNSS data has been processed. This might take some times.", end='\r')
            cnt += 1
    columns = ['Identifier', 'Timestamp', 'Latitude', 'North', 'Longitude', 'East', 'GPSMode', 'SatelliteNum', \
               'HDOP', 'AntennaHeight(m)', 'meter', 'HeightDifference(m)', 'm', 'DGPSAge', 'Checksum']                    
    gnss_df = pd.DataFrame(gnss_np, columns=columns)
    gnss_df = gnss_df.dropna(subset=['Timestamp'])
    gnss_df = gnss_df.drop(['Identifier', 'North', 'East', 'meter', 'm', 'Checksum'], axis=1)
    float_col = ['Timestamp', 'Latitude', 'Longitude', 'HDOP', 'AntennaHeight(m)', 'HeightDifference(m)', 'DGPSAge']
    gnss_df[float_col] = gnss_df[float_col].astype('float64')
    int_col = ['GPSMode', 'SatelliteNum']
    gnss_df[int_col] = gnss_df[int_col].astype('int64')

    gnss_df = reset_timestamp(gnss_df, freq)
    gnss_df[int_col] = gnss_df[int_col].astype('int64')
    print("GNSS processing done.")
    return gnss_df


def merge_data(dfs, freq):
    for i, data in enumerate(dfs):
        name, df = data
        df['Timestamp'] = (df['Timestamp'] * freq).astype('int64')
        df = df.groupby('Timestamp', as_index=False).mean()
        if i == 0:
            merged_df = df
        else:
            merged_df = pd.merge(merged_df, df, how='inner', on='Timestamp')
            
    merged_df['Timestamp'] = merged_df['Timestamp'] / freq
    merged_df = merged_df.interpolate().ffill().bfill()
    int_col = ['CYL_PRES_FLAG', 'CF_Ems_EngStat', 'CR_Brk_StkDep_Pc', 'CR_Ems_AccPedDep_Pc', \
                'CR_Ems_EngSpd_rpm', 'CR_Ems_VehSpd_Kmh', 'CF_Tcu_TarGe', 'BAT_SOC', \
                'CF_Gway_HeadLampHigh', 'CF_Gway_HeadLampLow', 'CR_Hcu_HigFueEff_Pc', \
                'CR_Hcu_NorFueEff_Pc', 'CR_Fatc_OutTempSns_C', 'CR_Hcu_EcoLvl', 'CR_Ems_EngColTemp_C', \
                'CF_Ems_BrkForAct', 'CF_Clu_InhibitP', 'CF_Clu_InhibitR', 'CF_Clu_InhibitN', 'CF_Clu_InhibitD', \
                'CF_Clu_VehicleSpeed', 'GPSMode', 'SatelliteNum']
    merged_df[int_col] = merged_df[int_col].astype('int64')
    return merged_df


def drop_data(df):
    columns = ['TimestampFromDevice', 'CR_Hcu_HigFueEff_Pc', 'CR_Hcu_NorFueEff_Pc', 'CR_Fatc_OutTempSns_C', \
        'CR_Hcu_EcoLvl', 'CR_Ems_FueCon_uL', 'CF_Ems_BrkForAct', 'CF_Clu_VehicleSpeed', \
        'VS', 'SA', 'YR', 'HDOP', 'AntennaHeight(m)', 'HeightDifference(m)', \
        'DGPSAge', 'LinkName', 'Description', 'TrafficUpdateTime', 'LinkRoadType', \
        'StartNodeName', 'EndNodeName']
    for col in columns:
        if col in df.columns:
            df = df.drop(columns=col)
    return df


def rename_columns(df):
    name_dict = {'SAS_Angle': 'S_Angle', 'CYL_PRES': 'B_PRES', 'CYL_PRES_FLAG': 'B_FLAG', \
                'CF_Ems_EngStat': 'E_Status', 'CR_Brk_StkDep_Pc': 'B_Depth', 'CR_Ems_AccPedDep_Pc': 'A_Depth', \
                'CR_Ems_EngSpd_rpm': 'E_Speed', 'CR_Ems_VehSpd_Kmh': 'V_Speed', 'CF_Tcu_TarGe': 'G_Status', \
                'BAT_SOC': 'BA_SoC', 'CF_Gway_HeadLampHigh': 'HL_High', 'CF_Gway_HeadLampLow': 'HL_Low', \
                'CF_Hcu_DriveMode': 'DriveMode', 'CR_Hcu_FuelEco_MPG': 'F_Economy', \
                'CR_Hcu_HevMod': 'HevMode', 'CF_Clu_InhibitD': 'Inhibit_D', 'CF_Clu_InhibitP': 'Inhibit_P', \
                'CF_Clu_InhibitN': 'Inhibit_N', 'CF_Clu_InhibitR': 'Inhibit_R', 'CF_Clu_Odometer': 'Odometer', \
                'CR_Ems_EngColTemp_C': 'E_Col_Temp'}
    
    df = df.rename(columns=name_dict)
    df['Odometer'] = df['Odometer'].round(1).astype('float64')
    return df


def retype(df):
    int_col = ['B_FLAG', 'E_Status', 'B_Depth', 'A_Depth', 'E_Speed', 'V_Speed', 'G_Status', \
                'BA_SoC', 'HL_High', 'HL_Low', 'E_Col_Temp', 'Inhibit_D', 'Inhibit_P', 'Inhibit_N', 'Inhibit_R', \
                'DriveMode', 'HevMode', 'GPSMode', 'SatelliteNum']
    float_col = ['Timestamp', 'CT', 'MS', 'MC', 'S_Angle', 'B_PRES', 'LAT_ACCEL', 'LONG_ACCEL', \
                'YAW_RATE', 'WHL_SPD_RR', 'WHL_SPD_RL', 'WHL_SPD_FR', 'WHL_SPD_FL', 'F_Economy', \
                'Odometer', 'X', 'Y', 'Z', 'BVP', 'HR', 'EDA', 'TEMP', 'Latitude', 'Longitude']
    df[int_col] = df[int_col].astype('int64')
    df[float_col] = df[float_col].astype('float64')
    
    return df

def main(data_names, data_freq, base_path):
    df_list = []
    if 'CAN' in data_names:
        can_path = base_path / 'CAN'
        if can_path.is_dir():
            can_path = list(can_path.glob('*.csv'))[0]
            can_df = process_CAN(can_path, data_freq)
            df_list.append(('CAN', can_df))
        else:
            print(f"FileNotExist. {can_path}")

    if 'HOD_CAN' in data_names:
        hod_can_path = base_path / 'HOD_CAN'
        if hod_can_path.is_dir():
            hod_can_path = list(hod_can_path.glob("*.csv"))[0]
            hod_can_df = process_HOD_CAN(hod_can_path, data_freq)
            df_list.append(('HOD_CAN', hod_can_df))
        else:
            print(f"FileNotExist. {hod_can_path}")

    if 'bio' in data_names:
        bio_path = base_path / 'bio'
        if bio_path.is_dir():
            bio_path = [p for p in bio_path.glob("*.csv") if "tags" not in str(p)]
            bio_df = process_bio(bio_path, data_freq)
            df_list.append(('BIO', bio_df))
        else:
            print(f"FileNotExist. {bio_path}")

    if 'GNSS' in data_names:
        gnss_path = base_path / 'GNSS'
        if gnss_path.is_dir():
            gnss_path = list(gnss_path.glob("*"))[0]
            gnss_df = process_gnss(gnss_path, data_freq)
            df_list.append(('GNSS', gnss_df))
        else:
            print(f"FileNotExist. {gnss_path}")

    merged_df = merge_data(df_list, data_freq)
    
    merged_df = drop_data(merged_df)
    
    merged_df = rename_columns(merged_df)
    
    merged_df = retype(merged_df)
    
    merged_df.to_csv("./merged_data.csv", index=False)

if __name__ == "__main__":
    data_names = config.config['data_names']
    data_freq = config.config['data_freq']
    base_path = pathlib.Path(config.config['path'])

    main(data_names, data_freq, base_path)