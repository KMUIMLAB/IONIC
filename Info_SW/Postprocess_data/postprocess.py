from shapely.geometry import Point, LineString, shape
from shapely.ops import nearest_points
import fiona
import pyproj as proj
import pandas as pd
import pathlib
import os
import numpy as np
import math
from glob import glob
from rtree import index
from config import Config

# http://data.nsdi.go.kr/dataset/20180927ds0062 도로중심선 데이터(국토지리정보원)
# QGIS 이용하여 서울 경기 정보만 추출

# Create directories and csv file paths based on given origin_path, name and folder_name.
def make_path(data_from, data_to, result, folder_name = None):
    paths = sorted(list(data_from.glob("*/*")))
    result_folders = [save_path.name for save_path in data_from.glob("*") if save_path.name.isnumeric()]
    if folder_name:
        # Filter paths by folder_name
        paths = [path for path in paths if any([folder in path.parts for folder in folder_name])]
        result_folders = [save_path.name for save_path in data_from.glob("*") if save_path.name.isnumeric() if any([folder in save_path.parts for folder in folder_name])]
    # Create result folders if they don't exist
    
    result_paths = [data_to / result / folder for folder in result_folders]
    for result_path in result_paths:
        result_path.mkdir(parents=True, exist_ok=True)

    # Create CSV paths
    csv_paths = sorted([f"{str(save_path)}/{result.split('/')[-1]}.csv" for save_path in result_paths])

    return paths, csv_paths


# Remove unused Columns
class RemoveUnusedColumns():
    def __init__(self):
        self.paths, self.csv_paths = make_path(data_path, result_path, result = rm_path, folder_name= Config['folder_name'])
    def remove_TM_Altitude(self) :
        
        for path, csv_path in zip(self.paths, self.csv_paths):
            
            df = pd.read_csv(path)
            df = df.drop(['TM_Altitude'], axis=1)
            df.to_csv(csv_path, index = False)
        print("[INFO] Removing unused columns done.")
        
            

# Add Driving Cycle Column            
class AddDrivingCycle():
    def __init__(self):
        
        self.paths, self.csv_paths = make_path(data_path, result_path, result = cycle_path, folder_name= Config['folder_name'])
        
    def add_Driving_Cycle(self) :
        
        for i, path, csv_path in zip(range(len(self.paths)), self.paths, self.csv_paths):
  
            df = pd.read_csv(path)
            driving_cycle = pd.DataFrame(columns= ['Driving Cycle'])
            
            df = pd.concat([df, driving_cycle], axis=1)
            df['Driving Cycle'] = df['Driving Cycle'].fillna(i)  
            
            df.to_csv(csv_path, index = False)
        print("[INFO] Adding driving cycle column done.")
            

 
# Add Curvature Column
class AddCurvature():
    def __init__(self, columns):
        
        self.columns = columns
        
        self.paths, self.csv_paths = make_path(data_path, result_path, result= curv_path, folder_name= Config['folder_name'])
        self.vectormap_path = os.path.join(origin_path, 'map_data', 'selected.shp')
        self.proj_5179 = 'epsg:5179'
        self.proj_4326 = 'epsg:4326'
            


    # Curvature equation for a get_curv passing through 3 points
    def get_curv(self, x1, y1, x2, y2, x3, y3) :

        """
        Calculates the curvature, center x and center y of a circle defined by three points
        
        Parameters:
        x1 : x coordinate of first point
        y1 : y coordinate of first point
        x2 : x coordinate of second point
        y2 : y coordinate of second point
        x3 : x coordinate of third point
        y3 : y coordinate of third point
        
        Returns:
        curvature, center x, center y
        """
        
        d1= (x2-x1)/(y2-y1)
        d2= (x3-x2)/(y3-y2)
        
        cx= ((y3-y1)+(x2+x3)*d2-(x1+x2)*d1)/(2*(d2-d1))
        cy= -d1*(cx-(x1+x2)/2)+(y1+y2)/2
        
        r= np.sqrt((x1-cx)**2+(y1-cy)**2)
        k = 1/r
        
        return k, cx, cy        
    
    
    def tm2latlong(self, X, Y):
        '''
        Convert X, Y coordinates in EPSG 5179 (TM) to Latitude, Longitude in EPSG 4326
        
        Parameters:
        X : X coordinate in EPSG 5179
        Y : Y coordinate in EPSG 5179
        
        Returns: 
        Latitude, Longitude in EPSG 4326
        '''
        tm2latlong_transformer = proj.Transformer.from_crs(self.proj_5179, self.proj_4326)
        lat, long = tm2latlong_transformer.transform(X, Y)
        return lat, long
        

    def latlong2tm(self, lat, long):
        '''
        Convert Latitude, Longitude in EPSG 4326 to X, Y coordinates in EPSG 5179

        Parameters:
        lat: Latitude in EPSG 4326
        long: Longitude in EPSG 4326

        Returns:
        X, Y coordinates in EPSG 5179
        '''
        latlong2tm_transformer = proj.Transformer.from_crs(self.proj_4326, self.proj_5179)
        X, Y = latlong2tm_transformer.transform(lat, long)
        return X, Y
      
      
    # Create Curvature Column
    def add_Curvature(self) :
        
        for i, path, csv_path in zip(range(len(self.paths)), self.paths, self.csv_paths):
            
            df = pd.read_csv(path)
            gps_points = [(df['Latitude'][i], df['Longitude'][i]) for i in range(len(df))]
            
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
                for gps_point in gps_points:
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
            
            # Convert coordinates to Transverse Mercator projection                
            TM_X1, TM_Y1 = self.latlong2tm(lat1_list, long1_list)
            TM_X2, TM_Y2 = self.latlong2tm(lat2_list, long2_list)
            TM_X3, TM_Y3 = self.latlong2tm(lat3_list, long3_list)
            
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
                    k, tm_cx, tm_cy = self.get_curv(tm_x1, tm_y1, tm_x2, tm_y2, tm_x3, tm_y3)
                    K.append(k)
                    TM_CX.append(tm_cx)
                    TM_CY.append(tm_cy)
                    
            Lat_CX, Long_CY = self.tm2latlong(TM_CX, TM_CY)
            
            
            Curvature = pd.DataFrame(K, columns=['Curvature'])
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
                        
            # curvature direction, The direction of curvature has a (+) sign in the counterclockwise direction and a (-) sign in the clockwise direction
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
                               'Lat_Cx', 'Long_Cy']
            
            if self.columns == 'all' :
                Curv_df = Curv_df
                for i, k in enumerate(Curv_df['Curvature']):
                    if k == -1:
                        Curv_df.loc[i, :] = -1
            elif self.columns == 'onlycurv' :
                Curv_df = Curv_df['Curvature']
            
            
            add_columns_df = pd.concat([df, Curv_df], axis=1) 
            add_columns_df.to_csv(csv_path, index = False)
        print("[INFO] Adding curvature column done.")
        
        
if __name__ == "__main__":
    
    print("[INFO] Start reading files...")
    
    origin_path = pathlib.Path.cwd()
    data_path = origin_path / 'data'
    result_path = origin_path / 'postprocess'
    
    
    if 'remove_unused_column' in Config['postprocess_list']:
        rm_path = 'remove_unused_column'
        rm_column = RemoveUnusedColumns()
        rm_column.remove_TM_Altitude()
        data_path = result_path / rm_path
    
    if 'add_driving_cycle' in Config['postprocess_list']:
        cycle_path = 'add_driving_cycle'
        add_dc = AddDrivingCycle()
        add_dc.add_Driving_Cycle()
        data_path = result_path / cycle_path

    if 'add_curvature' in Config['postprocess_list']:
        curv_path = 'add_curvature'
        curvature_columns = Config['curvature_columns']
        folder_name = Config['folder_name']
        add_curv = AddCurvature(curvature_columns)
        add_curv.add_Curvature()
        data_path = result_path /curv_path
