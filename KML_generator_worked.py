import xml.dom.minidom as dom
import os
import glob
import pandas as pd
import numpy as np
import argparse
import math
import time
import datetime

#Change time format in files.
def change_time_format (dataframe1):
    timelist = []
    if args.periodT == 0.0:
        for time in dataframe1.iloc[:, [0]].values:
            for i in time:
                final_datetime = i[:10] + 'T' + i[11:] + 'Z'
                timelist.append(final_datetime)
    else:
        list_index = 19
        if args.periodT == 1.0:
            list_index = list_index
        else:
            x = math.log10(1/args.periodT)
            list_index = list_index + x + 1

        for time in dataframe1.iloc[:, [0]].values:
            for i in time:
                final_datetime = i[:10] + 'T' + i[11:int(list_index)] + 'Z'
                timelist.append(final_datetime)
    time_changed_df = pd.DataFrame({'timestamp':timelist}, index=np.arange(dataframe1.shape[0]))
    dataframe = pd.concat([dataframe1, time_changed_df], axis=1)
    dataframe.reset_index(drop=True, inplace=True)
    return dataframe

def closest(lst, K): 
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))] 

def unix (dataframe):
    unixtime_list = []
    for time in dataframe.iloc[:, [0]].values:
        for i in time:
            unix_second = timestamp_to_unix_converter(i)
            unixtime_list.append(unix_second)
    unixtime_changed_df = pd.DataFrame({'unixtime':unixtime_list}, index=np.arange(dataframe.shape[0]))
    new_dataframe = pd.concat([dataframe, unixtime_changed_df], axis=1)
    new_dataframe.reset_index(drop=True, inplace=True)
    return new_dataframe

def timestamp_to_unix_converter (time_stamp): 
    dt = datetime.datetime(int(time_stamp[:4]), int(time_stamp[5:7]), int(time_stamp[8:10]), int(time_stamp[11:13]), int(time_stamp[14:16]))
    unixtime = int("{:%s}".format(dt)) + float(time_stamp[17:])
    return unixtime

#Cleaning dataframe in 'Timestamp1'. Function calls change_time_format function.
def clean_dataframe (data_frame):
    dataframe_changed = change_time_format(data_frame)
    #dataframe_changed = dataframe_changed.drop_duplicates(subset = 'timestamp1', keep = "first")
    dataframe_changed.reset_index(drop=True, inplace=True)
    return dataframe_changed

#Selecting start time and end time, extract time selected dataframe.
def choose_starting_and_endtime (x, y, df_x):
    index_start_time = df_x.index[df_x['timestamp2'] == x].values
    index_end_time = df_x.index[df_x['timestamp2'] == y].values
    time_selected_df = df_x.iloc[index_start_time[0]: index_end_time[0], :]
    return time_selected_df   

#Color order: GG, RR, BB
def changing_color(velocity):
    ratio_for_vel_below_20 = 255/5.56
    ratio_for_vel_21_to_40 = (velocity - 5.56) / (11.1 - 5.56)
    ratio_for_vel_41_to_60 = (velocity - 11.1) / (16.67 - 11.1)
    
    color_for_red = 0
    color_for_green = 0
    color_for_blue = 0
    if velocity < 0:
        color_for_green = 255
    elif velocity <=5.56:
        color_for_red = ratio_for_vel_below_20*velocity
        color_for_green = 255
    elif velocity <= 11.1:
        color_for_red = 255
        color_for_green = 255 - ((255 - 102) * ratio_for_vel_21_to_40)
    elif velocity <= 16.67:
        color_for_red = 255
        color_for_green = 102 - ((102 - 0) * ratio_for_vel_41_to_60)
    else:
        color_for_red = 255
        
    return [int(color_for_green), int(color_for_red), color_for_blue]

#Change to KML color format : AABBGGRR
def RGB_to_KML_color (list):
    green = list[0]
    red = list[1]
    blue = list[2]
    color_changed = "7f" + '{:02x}{:02x}{:02x}'.format(blue, green, red)
    return color_changed

#Process Child Element in KML file.
def processChild(node):
    for child in node.childNodes:
        processChild(child)

#Creating structure for KML file based on a Dataframe list_of_location, inside this function call processChild function.
#Velocity: 0km/h -> 20km/h: green; 21km/h -> 40km/h: yellow; 41km/h -> 60km/h: orange; >40km/h: red
#Equivilent km/h -> m/s:  <=5.56: green; >5.56 and <=11.1 : yellow; >11.1 and <= 16.67: orange; >16.67: red
def create_google_kml_override_map(list_of_locations):
    """Converts the override location to a KML file for exporting
    Refer to https://developers.google.com/kml/articles/geocodingforkml    
    Args: list_of_locations (list of coordinate pair): A list of all locations    
    Returns: xml.dom.minidom.Document(): A KML document
    """
    kmlDoc = dom.Document()
    kmlRootElement = kmlDoc.createElementNS(
        "http://earth.google.com/kml/2.2", "kml"
    )
    ##Added by Vinh to use TimeStamp
    kmlRootElement.setAttributeNS("", "xmlns", "http://www.opengis.net/kml/2.2")
    kmlRootElement.setAttributeNS("xmls", "xmlns:gx", "http://www.google.com/kml/ext/2.2")

    kmlRootElement = kmlDoc.appendChild(kmlRootElement)
    documentElement = kmlDoc.createElement("Document")
    documentElement = kmlRootElement.appendChild(documentElement)    

    folderElement = kmlDoc.createElement("Folder")

    nameElement = kmlDoc.createElement("name")
    textElement = kmlDoc.createTextNode("Hi")
    nameElement.appendChild(textElement)
    folderElement.appendChild(nameElement)
    
    for location in list_of_locations:

        # Point tag and its children #
        latitude = location[2]
        longitude = location[3]
        timeStamp = location [0]
        type(latitude)
        type(longitude)

        if (not (np.isnan(latitude))) and (not np.isnan(longitude)) and latitude != 0  and longitude != 0: # and (not np.nan == longitude):
            iconStyleElement = kmlDoc.createElement("IconStyle")
            styleElement = kmlDoc.createElement("Style")
            iconElement = kmlDoc.createElement("Icon")
            hrefElement = kmlDoc.createElement("href")
            pointElement = kmlDoc.createElement("Point")
            coorElement = kmlDoc.createElement("coordinates")    
            timeStampElement = kmlDoc.createElement("gx:TimeStamp")   #TimeStamp 

            ## colors to be set this way : aabbggrr #
            color = RGB_to_KML_color(changing_color(location[1]))

            coordinates = str(longitude) + ", " + str(latitude)
            coorElement.appendChild(kmlDoc.createTextNode(coordinates))
            pointElement.appendChild(coorElement)

            whenElement= kmlDoc.createElement("when")
            strtimeStamp = str(timeStamp)
            whenElement.appendChild(kmlDoc.createTextNode(strtimeStamp))
            timeStampElement.appendChild(whenElement)

            placemarkElement = kmlDoc.createElement("Placemark")
            colorElement = kmlDoc.createElement("color")
            scaleElement = kmlDoc.createElement("scale")

            iconStyleElement.appendChild(colorElement)
            iconStyleElement.appendChild(scaleElement)

            strColor = color
            colorText = kmlDoc.createTextNode(strColor)
            colorElement.appendChild(colorText)

            strscaleElement = args.size
            scaleText= kmlDoc.createTextNode(strscaleElement)
            scaleElement.appendChild(scaleText)

            hrefText = kmlDoc.createTextNode("http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png")
            hrefElement.appendChild(hrefText)
            styleElement.appendChild(iconStyleElement)
                

            # Style tag and its children #
            iconStyleElement.appendChild(iconElement)
            iconElement.appendChild(hrefElement) 

            placemarkElement.appendChild(pointElement)
            placemarkElement.appendChild(styleElement)
            placemarkElement.appendChild(timeStampElement)
                

            processChild(placemarkElement)

            folderElement.appendChild(placemarkElement)

    documentElement.appendChild(folderElement)

    return kmlDoc

#Extract the kml File, inside this function call create_google_kml_override_map function. Return KML file.
def extract_kml (dataframe2, filename_of_kml_file):
    #listCol is list_of_location
    listCol = dataframe2.values.tolist()
    #print(listCol)

    kml = create_google_kml_override_map(listCol)
    with open(filename_of_kml_file, "w") as fp:
        fp.write(kml.toprettyxml(" "))

#Return final dataframe
def match_timestamp_filter (data_frame1, data_frame2):

    j = 0

    #Create new dataframe without microseconds
    columns_name = ['Timestamp', 'Velocity', 'Latitude', 'Longitude']
    final_df = pd.DataFrame(index=np.arange(data_frame2.shape[0]), columns=columns_name)

    if args.periodT == 0.0:
        df1_final = unix(data_frame1).rename(columns={'unixtime' : 'unixtime1'})
        df2_final = unix(data_frame2).rename(columns={'unixtime' : 'unixtime2'})
        #print(df2_final)
        column_name = []
        final_df1 = pd.DataFrame(index=np.arange(df1_final.shape[0]), columns=column_name)

        timelist_df1 = []
        for x in df1_final.loc[:,['unixtime1']].values.tolist():
            timelist_df1.append(x[0])
        #print(timelist_df1)
        for bla in df2_final.loc[:,['unixtime2']].values.tolist():
            omg = df1_final.loc[df1_final['unixtime1'] == closest(timelist_df1, bla[0])]
            final_df1 = pd.concat([final_df1, omg], ignore_index=True, sort=True)
        final_df1 = final_df1.dropna()
        final_df1.reset_index(drop=True, inplace=True)
        cols = final_df1.columns.tolist()
        cols = cols[-2:] + cols[:-2]
        final_df1 = final_df1[cols]
        #print(final_df1)

        data_frame1 = change_time_format(final_df1)
        data_frame2 = change_time_format(data_frame2)
        #print(data_frame1)
        #print(data_frame2)

        for i in range(data_frame2.shape[0]):
            final_df.loc[j][0] = data_frame2.iloc[i][3] #Timestamp
            final_df.loc[j][1] = data_frame1.iloc[i][2] #Velocity
            final_df.loc[j][2] = data_frame2.iloc[i][1] #Latitude
            final_df.loc[j][3] = data_frame2.iloc[i][2] #Longitude
            j = j + 1

    else:
        data_frame1 = change_time_format(data_frame1)
        data_frame2 = change_time_format(data_frame2)

        for i in range(data_frame2.shape[0]):
            valTime = data_frame2.iloc[i][3]
            listIndx = (data_frame1.index[data_frame1.loc[:, 'timestamp'] == valTime]).tolist()
            if listIndx:
                index_for_time = listIndx[0]
                final_df.loc[j][0] = valTime #Timestamp
                final_df.loc[j][1] = data_frame1.iloc[index_for_time][1] #Velocity
                final_df.loc[j][2] = data_frame2.iloc[i][1] #Latitude
                final_df.loc[j][3] = data_frame2.iloc[i][2] #Longitude
                j = j + 1

    #print(final_df)
    return final_df

#MAIN
def main ():

    path = args.FilePath
    #set working directory
    os.chdir(path)

    filename_of_kml_file  = args.kmlDes

    #find all csv files in the folder
    #use glob pattern matching -> extension = 'csv'
    #save result in list -> all_filenames
    extension = 'csv'

    #look recursively for all State.csv files
    #Returns a list containing all the paths
    # State_filenames : contains columns latitude, longitude, data Overflow
    # Satellites_filenames : contains columns unix time and all the GPS columns

    vehicle_status_filenames = glob.glob(path + args.VeSta + extension)
    gps_raw_filenames = glob.glob(path + args.GPSR + extension)

    #combine all files in the list
    panda_frame_vehiclestatus = pd.concat([pd.read_csv(f, skiprows=(3)) for f in vehicle_status_filenames])
    panda_frame_gpsraw = pd.concat([pd.read_csv(f, skiprows=(3)) for f in gps_raw_filenames])

    df1 = panda_frame_vehiclestatus.loc[:,[' timestamp', ' velocity']]
    df1_renamed = df1.rename(columns={' timestamp' : 'timestamp1'})
    df1_renamed.reset_index(drop=True, inplace=True)

    df2 = panda_frame_gpsraw.loc[:,[' timestamp', ' latitude', ' longitude']]
    df2_renamed = df2.rename(columns={' timestamp' : 'timestamp2'})
    df2_renamed.reset_index(drop=True, inplace=True)
    if args.startT != "Non" and args.endT != "Non":
        df2_time_chosen = choose_starting_and_endtime (args.startT, args.endT, df2_renamed)
    else:
        df2_time_chosen = df2_renamed
    df2_time_chosen.reset_index(drop=True, inplace=True)
    
    extract_kml (match_timestamp_filter(df1_renamed, df2_time_chosen), filename_of_kml_file)

    print("Your KML file should now in " + filename_of_kml_file)


parser = argparse.ArgumentParser(prog='Choose time', description='Process the cvs files with desire timestamp.')
parser.add_argument('-ST', '--startT',default="Non", required=False, metavar='', type=str, help='Add the starting time.')
parser.add_argument('-ET', '--endT',default="Non", required=False, metavar='', type=str, help='Add the ending time.')
parser.add_argument('-PATH', '--FilePath', required=True, metavar='', type=str, help='Add the path of where to look for CSV files.')
parser.add_argument('-VS', '--VeSta', required=True, metavar='', type=str, help='Add the path of where to look for Vehicle_Status files.')
parser.add_argument('-GR', '--GPSR', required=True, metavar='', type=str, help='Add the path of where to look for GPS_Raw files.')
parser.add_argument('-KML', '--kmlDes', required=True, metavar='', type=str, help='Add the path of where to extract the final KML file.')
parser.add_argument('-PE', '--periodT',default=0.0, required=False, metavar='', type=float, help='Add the desire period.')
parser.add_argument('-SZ', '--size', default="0.2", required=False, metavar='', type=str, help='Add the desire size for pin points.')

args = parser.parse_args() 
print ("The starting time is %s and ending time is %s.\n" % (args.startT, args.endT))
print("The path of the CVS files is %s.\n" % (args.FilePath))
print("The path of the Vehicle_Status files is %s and for GPS_Raw is %s\n" % (args.VeSta, args.GPSR))
print("The chosen period for timestamp is %s and pin point's size is %s\n" % (args.periodT, args.size))

if __name__ == '__main__':
    main()