from tkinter import *
from tkinter import ttk
import sqlite3
from sqlite3 import Error
import csv
from psycopg2 import sql


#set-up variables
input_received =0 
albums_requested = 0
database_name = "Photos.sqlite"
print("*****", database_name, "parser ****")
database_path = "Waiting for user"
output_path = "Waiting for user"
camera_roll_output_name = "CameraRoll.csv"
album_stats_output_name = "AlbumDetails.csv"
Pictures =[]
Albums =[]
camera_roll_keys=("Z_PK", "ZDIRECTORY", "ZFILENAME", "ZORIGINALFILENAME", "ZDURATION","ZFAVORITE","ZCREATORBUNDLEID","ZEDITORBUNDLEID","ZADDEDDATE","ZDATECREATED","ZMODIFICATIONDATE", "ZEXIFTIMESTAMPSTRING", "ZTRASHEDSTATE", "ZTRASHEDDATE", "ZTIMEZONENAME", "ZTIMEZONEOFFSET", "ZLATITUDE","ZLONGITUDE","AlbumName")
album_keys=("ZTITLE", "CreationDate", "PhotoCount", "VideoCount", "StartDate", "EndDate", "ParentFolderID", "ParentFolderName")
variable_table_name=''
variable_ASSETScolumn_name=''
variable_ALBUMScolumn_name=''

SQL_Q3a = 'SELECT \
            ZADDITIONALASSETATTRIBUTES.Z_PK,\
            ZGENERICASSET.ZDIRECTORY,\
            ZGENERICASSET.ZFILENAME,\
            ZADDITIONALASSETATTRIBUTES.ZORIGINALFILENAME,\
            ZGENERICASSET.ZDURATION,\
            ZGENERICASSET.ZFAVORITE,\
            ZADDITIONALASSETATTRIBUTES.ZCREATORBUNDLEID,\
            ZADDITIONALASSETATTRIBUTES.ZEDITORBUNDLEID,\
            ZGENERICASSET.ZADDEDDATE,\
            ZGENERICASSET.ZDATECREATED,\
            ZGENERICASSET.ZMODIFICATIONDATE,\
            ZADDITIONALASSETATTRIBUTES.ZEXIFTIMESTAMPSTRING,\
            ZGENERICASSET.ZTRASHEDSTATE,\
            ZGENERICASSET.ZTRASHEDDATE,\
            ZADDITIONALASSETATTRIBUTES.ZTIMEZONENAME,\
            ZADDITIONALASSETATTRIBUTES.ZTIMEZONEOFFSET,\
            ZGENERICASSET.ZLATITUDE,\
            ZGENERICASSET.ZLONGITUDE,\
            Album_Membership.Album_Name as "Album Name"\
        FROM ZADDITIONALASSETATTRIBUTES INNER JOIN ZGENERICASSET\
        ON ZADDITIONALASSETATTRIBUTES.Z_PK=ZGENERICASSET.Z_PK\
            LEFT JOIN (SELECT\
                ZGENERICALBUM.ZTITLE as Album_Name,\
                %s.%s as Z_PK\
                FROM ZGENERICALBUM \
                JOIN %s \
                ON ZGENERICALBUM.Z_PK=%s.%s \
                JOIN ZGENERICASSET \
                ON %s.%s=ZGENERICASSET.Z_PK) AS Album_Membership \
                ON Album_Membership.Z_PK = ZADDITIONALASSETATTRIBUTES.Z_PK'

#parse album info:
SQL_Q4 = 'select A1.ZTITLE,\
                    A1.ZCREATIONDATE as CreationDate,\
                    A1.ZCACHEDPHOTOSCOUNT as PhotoCount, \
                    A1.ZCACHEDVIDEOSCOUNT as VideoCount, \
                    A1.ZSTARTDATE as StartDate,\
                    A1.ZENDDATE as EndDate,\
                    A1.ZPARENTFOLDER as ParentFolderID, \
                    A2.ZTITLE as ParentFolderName \
                    FROM ZGENERICALBUM A1 \
                    LEFT OUTER JOIN ZGENERICALBUM A2 on A1.ZPARENTFOLDER = A2.Z_PK'

 
def create_connection(database_path, database_name):
    '''opens connetion with photos.sqlite database, as specified by the given path'''
    database = database_path+database_name
    print ("full database location: ", database)
    try:
        conn = sqlite3.connect(database)
        print("Database connection created")           
        return conn
    except Error as e:
        print(e)

#find variable table name
SQL_Q1 = "select name from sqlite_master where name like 'Z___ASSETS'"

def find_table(conn):
    print("Finding variable table name")
    cur=conn.cursor()
    cur.execute(SQL_Q1)
    VTABLE = cur.fetchall()
    global variable_table_name
    variable_table_name =str(VTABLE[0])
    variable_table_name=variable_table_name.replace("(","").replace(")","").replace(",","")
    #print("variable_table_name is: ",variable_table_name)
    return variable_table_name

#find variable ASSETS column name:
SQL_Q2a = "select name from PRAGMA_table_info(%s) where name like 'Z___ASSETS'" 

def find_ASSETScolumn(conn,variable_table_name):
    print ("Finding variable ASSETS column name")
    cur=conn.cursor()
    cur.execute(SQL_Q2a % variable_table_name)
    VCOLUMN = cur.fetchall()
    global variable_ASSETScolumn_name
    variable_ASSETScolumn_name = str(VCOLUMN[0])
    variable_ASSETScolumn_name=variable_ASSETScolumn_name.replace("(","").replace(")","").replace(",","")
    #print("variable_column_name is: ",variable_column_name)
    return variable_ASSETScolumn_name

#find variable ALBUMS column name:
SQL_Q2b = "select name from PRAGMA_table_info(%s) where name like 'Z___ALBUMS'" 
def find_ALBUMScolumn(conn,variable_table_name):
    print ("Finding variable ALBUMS column name")
    cur=conn.cursor()
    cur.execute(SQL_Q2b % variable_table_name)
    VCOLUMN = cur.fetchall()
    global variable_ALBUMScolumn_name
    variable_ALBUMScolumn_name = str(VCOLUMN[0])
    variable_ALBUMScolumn_name=variable_ALBUMScolumn_name.replace("(","").replace(")","").replace(",","")
    return variable_ALBUMScolumn_name

def parse_cameraroll(conn):
    '''executes main query which combines info from ZGENERICASSET and ZADDITIONALASSETATTRIBUTES tables, returning core information about all the items on the camera roll'''
    print ("Parsing cameraroll")
    cur=conn.cursor()
    cur.execute(SQL_Q3a % (variable_table_name,variable_ASSETScolumn_name, variable_table_name, variable_table_name, variable_ALBUMScolumn_name, variable_table_name,variable_ASSETScolumn_name))
    CameraRoll = cur.fetchall()
    for Photo in CameraRoll:
        Pictures.append(dict(zip(camera_roll_keys,Photo)))
    print("Camera roll data:")
    print(Pictures)
    return Pictures

def picture_info_csv(Pictures, output_path, camera_roll_output_name):
    '''generates a csv file and writes headers followed by corresponding key values for each dictionary in the Pictures list of dictionaries'''
    print("Exporting Camera Roll data to csv")
    with open(output_path+camera_roll_output_name,'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=camera_roll_keys, extrasaction="ignore")
        writer.writeheader()
        for i in range (0,len(Pictures)):
            writer.writerow(Pictures[i])
        print("Picture_info_csv exported to ", output_path+camera_roll_output_name)

def parse_album_stats(conn):
    print("Parsing album info")
    cur=conn.cursor()
    cur.execute(SQL_Q4)
    AlbumStats = cur.fetchall()
    for Album in AlbumStats:
        Albums.append(dict(zip(album_keys, Album)))
    print("Album stats:")
    print(Albums)
    return Albums

def album_stats_csv(Albums, output_path, album_stats_output_name):
    print("Exporting Album data to csv")
    with open(output_path+album_stats_output_name,'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=album_keys, extrasaction="ignore")
        writer.writeheader()
        for i in range (0,len(Albums)):
            writer.writerow(Albums[i])
        print("Album_info_csv exported to ", output_path+album_stats_output_name)

    
def Parse():        
    database_path = path_textbox.get()
    output_path= output_textbox.get()
    print("User selected path: ", database_path)
    print("Output location: ", output_path)
    conn=create_connection(database_path, database_name)    
    find_table(conn)
    print("variable_table_name is: ", variable_table_name)
    find_ASSETScolumn(conn, variable_table_name)
    print("variable_ASSETScolumn_name is: ", variable_ASSETScolumn_name)
    find_ALBUMScolumn(conn, variable_table_name)
    print("variable_ALBUMscolumn_name is: ", variable_ALBUMScolumn_name)
    parse_cameraroll(conn)
    picture_info_csv(Pictures, output_path, camera_roll_output_name)
    print("albumvar= ", albumvar.get())
    if albumvar.get() == 1:
        print("Album details requested")
        parse_album_stats(conn)
        album_stats_csv(Albums, output_path, album_stats_output_name)
    
        
        
#set-up GUI
root=Tk()
content= ttk.Frame(root)
frame=ttk.Frame(content, borderwidth=5)
albumvar = IntVar()
db_label = ttk.Label(content, text="Enter path for folder containing db: ")
path_textbox = ttk.Entry(content)
output_label = ttk.Label(content, text="Enter path for output files:  ")
album_check = ttk.Checkbutton(content, text="Album info", variable=albumvar, onvalue=1, offvalue=0)
output_textbox = ttk.Entry(content)
GO_button = ttk.Button(content, text="Forensicate!", command=Parse)

#creating grid
content.grid(column=0, row=0)
frame.grid(column=0, row=0, columnspan=100, rowspan=4)

#placing objects within grid
db_label.grid(column=1, row=1)
path_textbox.grid(column=2, row=1, columnspan=99)
output_label.grid(column=1, row=2)
output_textbox.grid(column =2, row=2, columnspan=99)
album_check.grid(column=1, row=4)
GO_button.grid(column=2, row=4, columnspan=6)

#import values from entry boxes
database_path = path_textbox.get()
output_path = output_textbox.get()


root.mainloop()

