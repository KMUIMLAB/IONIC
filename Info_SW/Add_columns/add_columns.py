from shapely.geometry import Point, LineString, shape
from shapely.ops import nearest_points
import fiona
import pyproj as proj
import pandas as pd
import pathlib
import os
import numpy as np
import math
import requests
from glob import glob
from rtree import index


# http://data.nsdi.go.kr/dataset/20180927ds0062 도로중심선 데이터(국토지리정보원)
# QGIS 이용하여 서울 경기 정보만 추출

class add_columns():
    def __init__(self, data_path) -> None:
        
        # Select 'all' if verification step is required, 'onlycurv' if only curvature is required
        self.columns = 'onlycurv' # 'all'
        
        self.paths = sorted(list(data_path.glob("data/*/*")))       
        result_paths = data_path / 'add_columns'
        result_folders = [save_path.name for save_path in data_path.glob("data/*") if save_path.name.isnumeric()]
        result_paths = [result_paths / folder_name for folder_name in result_folders]
        for save_path in result_paths:
            save_path.mkdir(parents=True, exist_ok=True)
        self.result_paths = sorted([save_path / 'add_columns.csv' for save_path in result_paths])
        self.vectormap_path = os.path.join(data_path, 'map_data', 'selected.shp')
        self.proj_5179 = 'epsg:5179'
        self.proj_4326 = 'epsg:4326'
            
        print("[INFO] Start reading files...")


    # Curvature equation for a circle passing through 3 points
    def circle(self, x1, y1, x2, y2, x3, y3) :
        
        d1= (x2-x1)/(y2-y1)
        d2= (x3-x2)/(y3-y2)
        
        cx= ((y3-y1)+(x2+x3)*d2-(x1+x2)*d1)/(2*(d2-d1))
        cy= -d1*(cx-(x1+x2)/2)+(y1+y2)/2
        
        r= np.sqrt((x1-cx)**2+(y1-cy)**2)
        k = 1/r
        
        return k, cx, cy        
    
    

        
    def TM2latlong(self, X, Y):
        TM2latlong = proj.Transformer.from_crs(self.proj_5179, self.proj_4326)
        lat, long = TM2latlong.transform(X, Y)
        
        return lat, long
        
        
    def latlong2TM(self, lat, long):
        latlong2TM = proj.Transformer.from_crs(self.proj_4326, self.proj_5179)
        X, Y = latlong2TM.transform(lat, long)
        
        return X, Y        
      
      
    # Create Driving Cycle & Curvature Columns  
    def add_columns(self) :
        
        
        for i, path, res_path in zip(range(len(self.paths)), self.paths, self.result_paths):
            
            # Add Driving Cycle Columns
            new_path = path
            df = pd.read_csv(new_path)
            driving_cycle = pd.DataFrame(columns= ['Driving Cycle'])
            
            df = pd.concat([df, driving_cycle], axis=1)
            df['Driving Cycle'] = df['Driving Cycle'].fillna(i)  
            # Remove unused TM_Altitude Column
            df = df.drop(['TM_Altitude'], axis=1)

            gps_points = []
            for i in range(len(df)):
                tmp = (df['Latitude'][i], df['Longitude'][i])
                gps_points.append(tmp)
            
            # import road center line shape file 
            with fiona.open(self.vectormap_path) as src:
                # Create spatial index for map features
                idx = index.Index()
                for i, feature in enumerate(src):
                    geometry = shape(feature['geometry'])
                    if geometry.type == 'LineString':
                        idx.insert(i, geometry.bounds)
                # List to store the closest points and nodes
                closest_points = []
                closest_nodes = []
                for _, gps_point in enumerate(gps_points):
                    gps_point = Point(gps_point[1], gps_point[0])

                    closest_distance = float('inf')
                    closest_line = None
                    # Search for nearest line within a certain distance
                    for j in list(idx.nearest((gps_point.x, gps_point.y, gps_point.x, gps_point.y), 1)):
                        line = shape(src[j]['geometry'])
                        # Find the closest point in the line
                        for point in line.coords:
                            point = Point(point)
                            if gps_point.distance(point) < closest_distance:
                                closest_distance = gps_point.distance(point)
                                closest_point = point
                                closest_line = line

                    # Find the two closest nodes on the same link as the closest point
                    if closest_line is not None:
                        i = list(closest_line.coords).index(closest_point.coords[0])
                        if i+1 < len(closest_line.coords) and i-1 >= 0:
                            closest_nodes.append([closest_line.coords[i-1], closest_line.coords[i+1]])
                        elif i+1 >= len(closest_line.coords) and i-1 >= 1:
                            closest_nodes.append([closest_line.coords[i-1], closest_line.coords[i-2]])
                        elif i-1 < 0 and i+1 < len(closest_line.coords)-1:
                            closest_nodes.append([closest_line.coords[i+1], closest_line.coords[i+2]])
                        else:
                            closest_nodes.append([(-1, -1),(-1, -1)])
                        closest_points.append(closest_point.coords[0])
             
            lat1_list = []
            lat2_list = []
            lat3_list = []
            long1_list = []
            long2_list = []
            long3_list = []
                        
            for closest_point in closest_points :
                long1, lat1 = closest_point
                long1_list.append(long1)
                lat1_list.append(lat1)
            for closest_node in closest_nodes :
                long2, lat2 = closest_node[0]
                long3, lat3 = closest_node[1]
                long2_list.append(long2)
                lat2_list.append(lat2)
                long3_list.append(long3)
                lat3_list.append(lat3)
                            
            TM_X1, TM_Y1 = self.latlong2TM(lat1_list, long1_list)
            TM_X2, TM_Y2 = self.latlong2TM(lat2_list, long2_list)
            TM_X3, TM_Y3 = self.latlong2TM(lat3_list, long3_list)
            
            K = []
            TM_CX = []
            TM_CY = []
            
            for tm_x1, tm_y1, tm_x2, tm_y2, tm_x3, tm_y3 in zip(TM_X1,TM_Y1, TM_X2, TM_Y2, TM_X3, TM_Y3):
                # if lat&long = -1, values are -1
                if tm_x2 < 0 :
                    K.append(-1)
                    TM_CX.append(-1)
                    TM_CY.append(-1)
                else :
                    k, tm_cx, tm_cy = self.circle(tm_x1, tm_y1, tm_x2, tm_y2, tm_x3, tm_y3)
                    K.append(k)
                    TM_CX.append(tm_cx)
                    TM_CY.append(tm_cy)
                    
            Lat_CX, Long_CY = self.TM2latlong(TM_CX, TM_CY)
            
            
            Curvature = pd.DataFrame(K, columns=['Curvature'])
            Cx = pd.DataFrame(TM_CX, columns=['Cx'])
            Cy = pd.DataFrame(TM_CY, columns=['Cy'])
            Curvature['Curvature'].loc[Curvature['Curvature'] != -1] = abs(Curvature['Curvature'].loc[Curvature['Curvature'] != -1])
            
            # Set distance threshold of 30m between road centerline & actual coordinates
            for i in range(len(Curvature)):
                if not Curvature['Curvature'][i] == -1:
                    dis = math.sqrt((df['TM_X'][i]- TM_X1[i])**2 + (df['TM_Y'][i]- TM_Y1[i])**2)
                    if dis > 30 :
                        Curvature['Curvature'][i] = -1
                        
            # Set curvature threshold to 0.06
            for i in range(len(Curvature)):
                if not Curvature['Curvature'][i] == -1:
                    if Curvature['Curvature'][i] > 0.06 :
                        Curvature['Curvature'][i] = -1
                        
            # curvature direction
            for i in range(len(df['TrueNorth'])):

                if Curvature['Curvature'][i] != -1 :
                    TrueNorth = 90 - df['TrueNorth'][i]
                    TN =  math.tan(TrueNorth/ 180.0 * math.pi)
                    b = long1_list[i] - TN*lat1_list[i]
                    heading = Long_CY[i] -TN*Lat_CX[i] - b 
                    k = Curvature['Curvature'][i]

                    if  0 <= TrueNorth <= 90 :
                        if heading > 0:
                            k = k*(-1)
                            Curvature['Curvature'][i] = k
                            
                    elif  -270 < TrueNorth <= -180 :
                        if heading > 0:
                            k = k*(-1)
                            Curvature['Curvature'][i] = k
                            
                    elif  -180 < TrueNorth <= -90 :
                        if heading < 0:
                            k = k*(-1)
                            Curvature['Curvature'][i] = k
                            
                    elif  -90 < TrueNorth < 0 :
                        if heading < 0:
                            k = k*(-1)
                            Curvature['Curvature'][i] = k
                                
            Curv_df = pd.DataFrame(zip(lat1_list, long1_list, lat2_list, long2_list, lat3_list, long3_list, Lat_CX, Long_CY)) 
            Curv_df = pd.concat([Curvature, Curv_df], axis= 1) 
            Curv_df.columns = ['Curvature', 'Centerline_Lat1', 'Centerline_Long1', 'Centerline_Lat2', 'Centerline_Long2', 'Centerline_Lat3', 'Centerline_Long3',
                               'Lat_Cx', 'Lat_Cy']
            
            for i, k in enumerate(Curv_df['Curvature']):
                if k == -1:
                    Curv_df.loc[i, :] = -1
            
            add_columns_df = pd.concat([df, Curv_df], axis=1)
                        
            if self.columns == 'all' :
                use_columns = ['Timestamp', 'Latitude', 'Longitude',
                    'GPSMode', 'Altitude', 'Yaw', 'Pitch', 'Roll', 'TrueNorth',
                    'NorthDeclination', 'TM_X', 'TM_Y', 'E_Status', 'B_Depth', 'A_Depth',
                    'E_Speed', 'V_Speed', 'G_Status', 'B_PRES', 'B_FLAG', 'LAT_ACCEL',
                    'LONG_ACCEL', 'YAW_RATE', 'WHL_SPD_FL', 'WHL_SPD_FR', 'WHL_SPD_RL',
                    'WHL_SPD_RR', 'S_Angle', 'HL_High', 'HL_Low', 'DriveMode', 'F_Economy',
                    'HevMode', 'E_Col_Temp', 'BA_SoC', 'Inhibit_D', 'Inhibit_N',
                    'Inhibit_P', 'Inhibit_R', 'Odometer', 'Driving Cycle',
                    'Curvature', 'Centerline_Lat1', 'Centerline_Long1',
                    'Centerline_Lat2', 'Centerline_Long2', 'Centerline_Lat3', 'Centerline_Long3',
                    'Lat_Cx', 'Lat_Cy']
                
            elif self.columns == 'onlycurv' :
                use_columns = ['Timestamp', 'Latitude', 'Longitude', 'GPSMode', 'Altitude', 'Yaw',
                'Pitch', 'Roll', 'TrueNorth', 'NorthDeclination', 'TM_X', 'TM_Y',
                'E_Status', 'B_Depth', 'A_Depth', 'E_Speed', 'V_Speed', 'G_Status',
                'B_PRES', 'B_FLAG', 'LAT_ACCEL', 'LONG_ACCEL', 'YAW_RATE', 'WHL_SPD_FL',
                'WHL_SPD_FR', 'WHL_SPD_RL', 'WHL_SPD_RR', 'S_Angle', 'HL_High',
                'HL_Low', 'DriveMode', 'F_Economy', 'HevMode', 'E_Col_Temp', 'BA_SoC',
                'Inhibit_D', 'Inhibit_N', 'Inhibit_P', 'Inhibit_R', 'Odometer',
                'Driving Cycle', 'Curvature']
                
            add_columns_df = add_columns_df[use_columns]
            
            add_columns_df.to_csv(res_path, index = False)
        print("[INFO] Adding columns done.")
        
        
if __name__ == "__main__":
    
    data_path = pathlib.Path.cwd()
    
    add_columns = add_columns(data_path)
    
    add_columns.add_columns()
                
