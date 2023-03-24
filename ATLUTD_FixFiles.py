

#---------------------------------------------------------------------------------------------------------------#
# Outside Requirements
#
#---------------------------------------------------------------------------------------------------------------#
#   ffprobe - installed and in path
#   ffmpeg - installed and in path


#---------------------------------------------------------------------------------------------------------------#
# Load Modules
#
#---------------------------------------------------------------------------------------------------------------#
import os                                                            # interact with the file system
from datetime import datetime                                        # work with dates and times
import subprocess                                                    # used for multi threading

import argparse                                                      # used for easy parsing script input parametesr
import glob                                                          # handling wildcard searches, ex:  *.jpg

from rich.live import Live                                           # the rich modules are used for progress bars
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table

from concurrent.futures import ThreadPoolExecutor                    # used for multi threading

from hachoir.parser import createParser                              # hachoir is used to handle movie metadata 
from hachoir.metadata import extractMetadata


#---------------------------------------------------------------------------------------------------------------#
# In Progress
#
#---------------------------------------------------------------------------------------------------------------#
# get .heic to work, added it to the convert list but it isn't




#---------------------------------------------------------------------------------------------------------------#
# Variables
#
#---------------------------------------------------------------------------------------------------------------#
Media_Files = []
#Media_Files_Resize = []
#Today = datetime.datetime.today()
Today = datetime.today()
folder_base = ""
Age_Convert   = 7
Total_Deletes = 0
Total_Images  = 0
Total_Movies  = 0
Extensions_Images  = [ '.jpg', '.jpeg', '.webp', '.jfif', '.png' ]  # cannot convert .heic files ( as of 2023-02-18 )
Extensions_Images_Convert  = [ '.webp', '.jfif', '.png' ]
Extensions_Deletes = [ '.ini' ]

Extensions_Movies  = [ '.mp4', '.mov' ]
Extensions_Movies_Convert  = [ '.mov' ]
Dir_Exiftool = "D:/Data/Download/apps/ExifTool/exiftool-12.49"


#---------------------------------------------------------------------------------------------------------------#
# Functions
#
#---------------------------------------------------------------------------------------------------------------#


#---------------------------------------------------------------------------------------------------------------#
# Function: Media_Search
# Search all Directory structure and add files into array
#---------------------------------------------------------------------------------------------------------------#
def Media_Search( Directory ):
    #print( "______________________________________" )
    #print( "Prepping to investigate media" )
    print( "\tFolder: " + Directory )
    #print( "" )

    Files_Found = glob.glob( Directory + os.sep + "/**/*.*", recursive=True )
    for File_Found in Files_Found:
        #print( "File: " + File_Found )
        Media_Files.append( File_Found )



#---------------------------------------------------------------------------------------------------------------#
# Function: New_Fix_Files
# Per media file, determine the type ( image, movie ).  If the age is new enough, call the appropriate function
#---------------------------------------------------------------------------------------------------------------#
def New_Fix_Files( Media_File, job_progress, job_progress_overall, Jobs_Overall, Jobs_Pics, Jobs_Deletes, Jobs_Movies ):
    #print(uniform(1, 10))
    #sleep( uniform(0, 1) )
    #print( "Check_Meta: " + Media_File )

    Filename = os.path.basename(Media_File)
    
    Filename_Extension = os.path.splitext(Filename)[1]
    Filename_Base = os.path.splitext(Filename)[0]

    # Images
    if ( Filename_Extension.lower() in Extensions_Images ):
        #print( "debug" )
        try:
            File_Modified_date = datetime.fromtimestamp( os.path.getmtime( Media_File ) )
            Age = Today - File_Modified_date
            if ( Age.days < Age_Convert ):
                Image_Convert( Media_File, Filename_Base, Filename_Extension )

        except Exception as e:
            print( "An error has occured:" + str( e ) )
            exit(-1)

        job_progress.update( Jobs_Pics, advance=1, refresh=True )
        job_progress_overall.update( Jobs_Overall, advance=1, refresh=True )
    if ( Filename.lower() == "desktop.ini" ):
        try:
            print( "Deleting: " + Media_File )
            os.remove(  Media_File )
            job_progress.update( Jobs_Deletes, advance=1, refresh=True )
            job_progress_overall.update( Jobs_Overall, advance=1, refresh=True )
        except Exception as e:
            print( "Unable to delete: " + Media_File )
            job_progress_overall.update( Jobs_Overall, advance=1, refresh=True )


    # Movies
    if ( Filename_Extension.lower() in Extensions_Movies ):
        try:
            File_Modified_date = datetime.fromtimestamp( os.path.getmtime( Media_File ) )
            Age = Today - File_Modified_date
            if ( Age.days < Age_Convert ):
                Movie_Convert( Media_File, Filename_Base, Filename_Extension )

        except Exception as e:
            print( "An error has occured:" + str( e ) )
            exit(-1)

        job_progress.update( Jobs_Movies, advance=1, refresh=True )
        job_progress_overall.update( Jobs_Overall, advance=1, refresh=True )


#---------------------------------------------------------------------------------------------------------------#
# Function: Get_Totals
# Determine the total, for use in the progress bars
#---------------------------------------------------------------------------------------------------------------#
def Get_Totals( Media_File ):
    global Total_Deletes
    global Total_Images
    global Total_Movies
    Filename = os.path.basename(Media_File)
    Filename_Extension = os.path.splitext(Filename)[1]
    
    if ( Filename.lower() == "desktop.ini" ):
        #print( "Found a desktop.ini: " + Media_File )
        Total_Deletes = Total_Deletes + 1
    if ( Filename_Extension.lower() in Extensions_Images ):
        Total_Images = Total_Images + 1
    if ( Filename_Extension.lower() in Extensions_Movies ):
        Total_Movies = Total_Movies + 1


#---------------------------------------------------------------------------------------------------------------#
# Function: Movie_Convert
# Convert movie file to mp4
#---------------------------------------------------------------------------------------------------------------#
def Movie_Convert( Media_File, Filename_Base, Filename_Extension ):
    try:
        Filename_Date = datetime.now().strftime('%Y-%m-%d_%H24%M%S') # '2022-09-18_111632'
        Directory = os.path.dirname( Media_File ) 
        Directory_Parent = Directory.split( "/" )
        Directory_Parent = Directory_Parent[ len( Directory_Parent ) -1 ]
        Filename_New = Filename_Base + Filename_Extension

        if ( Filename_Extension == ".MP4" ):
            # Rename to .jpg
            print( "Renaming Extension on : " + Media_File )
            try: 
                #Filename_New = Filename_Base + "-" + Filename_Date + '.mp4'
                os.rename( Media_File, Directory + os.sep + Filename_Base )  # not renaming the file, only changing the extension
            except Exception as e:
                print( "Unable to rename: " + Media_File )

        if ( Filename_Extension.lower() in Extensions_Movies_Convert ):
            print( "Converting [" + Directory_Parent + "]\t" + Filename_Base + Filename_Extension )
            parser = createParser( Media_File )

            if ( parser ):
                try:
                    metadata = extractMetadata( parser )
                except Exception as e:
                    print( "Unable to extract Metadata %s " % e)
                    metadata = None
                for info in metadata.exportPlaintext():
                    if info.split(':')[0] == '- Creation date':
                        date_temp = info.partition( "date: " )[2]
                        #dateobj = datetime.strptime( info.split(':')[1].split()[0], "%Y-%m-%d" )
                        #print( " temp: " + str( temp ) )
                        dateobj = datetime.strptime( date_temp, "%Y-%m-%d %H:%M:%S" )
                        #print( " Date: " + str( info ) )
                        date_Metadata = str( dateobj.year ) + "-" + str( dateobj.month ) + "-" + str( dateobj.day ) + "_" + str( dateobj.hour ) + "-" + str( dateobj.minute ) + "-" + str( dateobj.second )
                parser.stream._input.close()
                Final_Filename = Filename_Base + "-" + date_Metadata + ".mp4"
                # Attepting to convert the file
                #print( "ffmpeg -hide_banner -loglevel error -i " + "\"" + Media_File +  "\"" + " " + "\"" + Directory + os.sep + Final_Filename + "\" -map_metadata 1" )
                subprocess.run( "ffmpeg -hide_banner -loglevel error -i " + "\"" + Media_File +  "\"" + " " + "\"" + Directory + os.sep + Final_Filename + "\" -map_metadata 1", shell=True)
                if ( os.path.isfile( Directory + os.sep + Final_Filename ) ):
                    # Copy the original metadata to the new file ( ex: preserve the create date )
                    subprocess.run( Dir_Exiftool + os.sep + "exiftool.exe -q -overwrite_original -ee -TagsFromFile " + Media_File + " \"-FileCreateDate<CreationDate\" \"-CreateDate<CreationDate\" \"-ModifyDate<CreationDate\" \"" + Directory + os.sep + Final_Filename + "\" ", shell=True)
                    os.remove(  Media_File )
                else:
                    print( "\tFile wasn't converted successfully" )


            Filename_New = Filename_Base + "-" + Filename_Date + '.mp4'

        # will need to check size on all files
        #Image_Resize( Directory_Parent, Directory, Filename_New )

    except Exception as e:
        print( "An Error has occurred while starting the Movie_Convert procedure: " + str( e ) + "\n\t" + Media_File )




#---------------------------------------------------------------------------------------------------------------#
# Function: Image_Convert
# Convert movie file to jpg
#---------------------------------------------------------------------------------------------------------------#
def Image_Convert( Media_File, Filename_Base, Filename_Extension ):
    try:
        Filename_Date = datetime.now().strftime('%Y-%m-%d_%H24%M%S') # '2022-09-18_111632'
        Directory = os.path.dirname( Media_File ) 
        #Directory_Parent = Directory.split( os.sep )
        Directory_Parent = Directory.split( "/" )
        Directory_Parent = Directory_Parent[ len( Directory_Parent ) -1 ]
        Filename_New = Filename_Base + Filename_Extension
        #print( "Directory: " + Directory + " Filename_Base: " + Filename_Base + "\tFilename_Extension" + Filename_Extension)
        if ( Filename_Extension == ".JPG" ):
            # Rename to .jpg
            print( "Renaming Extension on : " + Media_File )
            try: 
                Filename_New = Filename_Base + "-" + Filename_Date + '.jpg'
                os.rename( Media_File, Directory + os.sep + Filename_Base )  # not renaming the file, only changing the extension
            except Exception as e:
                print( "Unable to rename: " + Media_File )
        if ( Filename_Extension.lower() == ".jpeg".lower() ):
            # Rename to .jpg
            print( "Renaming Extension on : " + Media_File )
            try: 
                Filename_New = Filename_Base + "-" + Filename_Date + '.jpg'
                os.rename( Media_File, Directory + os.sep + Filename_New )
            except Exception as e:
                print( "Unable to rename: " + Media_File )
        if ( Filename_Extension.lower() in Extensions_Images_Convert ):
            print( "Converting [" + Directory_Parent + "]\t" + Filename_Base + Filename_Extension)
            subprocess.run( "ffmpeg -hide_banner -loglevel error -i " + "\"" + Media_File +  "\"" + " " + "\"" + Directory + os.sep + Filename_Base + "-" + Filename_Date + '.jpg' + "\"", shell=True)
            os.remove(  Media_File )
            Filename_New = Filename_Base + "-" + Filename_Date + '.jpg'

        # will need to check size on all files
        Image_Resize( Directory_Parent, Directory, Filename_New)
    except Exception as e:
        print( "An Error has occurred while starting the Image_Convert procedure: " + str( e ) + "\n\t" + Media_File )

#---------------------------------------------------------------------------------------------------------------#
# Function: Image_Resize
# Reisizes images based on the height and width limits.  This is done to help reduce file size issues
#---------------------------------------------------------------------------------------------------------------#
def Image_Resize( Directory_Parent, Directory, Filename ):
    Width_Limit = 2000
    Height_Limit = 1500
    Message = "\n  [" + Directory_Parent + "]\t" + Filename
    #Log_Info( "      Checking size on: " + file )
    Path_Check = Directory + "\\" + Filename
    process = subprocess.run( "ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0:s=x " + "\"" + Path_Check + "\"", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    output = process.stdout
    #Log_Info( "      " + str( output ) )
    try:
        Check_Width = int( output.split("x")[0] )
        Check_Height = int( output.split("x")[1] )
    except:
        Message = + "\n\t\t*** Invalid file"
        print( Message )
        #print( "\t[" + Directory_Parent + "]\t" + Filename + "\n\t\t " + Message )
        #print( "*** Invalid file: " + Path_Check)
        return

    if ( Check_Width > Width_Limit ) or ( Check_Height > Height_Limit ):
        Message = Message + "\n\tReducing Size"
        Message = Message + "\n\tWidth:\t" + str( Check_Width )
        Message = Message + "\n\tHeight:\t" + str( Check_Height )
        File_Size_Pre = os.path.getsize( Path_Check )
        process_resize = subprocess.run( "ffmpeg -y -hide_banner -loglevel error -i " + "\"" + Path_Check + "\"" + " -vf scale='min(2000,iw)':min'(1500,ih)':force_original_aspect_ratio=decrease " + "\"" + Path_Check + "\"", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        output_resize = process_resize.stdout
        File_Size_Post = os.path.getsize( Path_Check )
        Message = Message + "\n\tSize Pre:\t" + human_readable_size( File_Size_Pre, 2 )
        Message = Message + "\n\tSize After:\t" + human_readable_size( File_Size_Post, 2 )
        Message = Message + "\n\tSize Saved:\t" + human_readable_size( File_Size_Pre - File_Size_Post, 2 )
        print( Message )

#---------------------------------------------------------------------------------------------------------------#
# Function: human_readable_size
# Display file sizes in a human readable format
# Returns human readable string
#---------------------------------------------------------------------------------------------------------------#
def human_readable_size( size, decimal_places=2):
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']:
        if size < 1024.0 or unit == 'PiB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


#---------------------------------------------------------------------------------------------------------------#
# Function: Media_Loop
# Prep the status bar, and Loop through all found Media, launching each file as a separate thread
#---------------------------------------------------------------------------------------------------------------#
def Media_Loop():
    job_progress = Progress(
      "{task.description}",
      SpinnerColumn(),
      BarColumn(),
      TextColumn( "[progress.percentage]{task.percentage:>3.0f}%" ),
    )
    job_progress_overall = Progress(
      "{task.description}",
      SpinnerColumn(),
      BarColumn(),
      TextColumn( "[progress.percentage]{task.percentage:>3.0f}%" ),
    )

    total = sum(task.total for task in job_progress.tasks)
    overall_progress = Progress()

    Jobs_Deletes = job_progress.add_task("[blue]Deletes",  total=0 )
    Jobs_Images  = job_progress.add_task("[blue]Pics",     total=0 )
    Jobs_Movies  = job_progress.add_task("[blue]Movies",   total=0 )
    Jobs_Overall = job_progress_overall.add_task("[blue]All Jobs",  total=0 )

    
    #print( "Before Loop: \n\t Pics: " + str( Total_Images ) + "\n\t Deletes: " + str( Total_Deletes ) )

    for Media_File in Media_Files:
        Get_Totals( Media_File )

    job_progress.update( Jobs_Deletes, total=Total_Deletes )
    job_progress.update( Jobs_Images,  total=Total_Images )
    job_progress.update( Jobs_Movies,  total=Jobs_Movies )
    job_progress_overall.update( Jobs_Overall, total=Total_Images + Total_Deletes + Jobs_Movies )


    progress_table = Table.grid()
    progress_table.add_row(
        Panel.fit( job_progress_overall, title="[b]Overall Progress", border_style="yellow", padding=(2, 2) ),
        Panel.fit(job_progress, title="[b]Jobs", border_style="yellow", padding=(1, 1) ),
    )

    print( "" ) 
    print( "______________________________________" ) 
    print( "Processing over found Media Files" ) 
    print( "" ) 
    with Live(progress_table, refresh_per_second=10):

        with ThreadPoolExecutor(max_workers=25) as pool:

            for Media_File in Media_Files:
                # launch thread
                pool.submit(  New_Fix_Files, Media_File, job_progress, job_progress_overall, Jobs_Overall, Jobs_Images, Jobs_Deletes, Jobs_Movies )




#---------------------------------------------------------------------------------------------------------------#
# Main process
# 
#---------------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument( "-i", "--input", help="mp3 path, ex: \"D:/Data/mp3/", required=False )
    args = parser.parse_args()
    if not args.input:
        folder_base = "D:/Data/Pics/Atlanta United/ATLUTD VIPs/"
        print( "Using default directory: " + folder_base )
        #exit(-1)

    print( "______________________________________" )
    print( "Investigate Media in the  following locations" )
    print( "" )

    Media_Search( folder_base + "Games" )
    Media_Search( folder_base + "Rumors" )
    Media_Search( folder_base + "Dates" )
    Media_Search( folder_base + "art" )
    Media_Search( folder_base + "pics" )
    #Media_Search( folder_base + "temp" )

    print( "\tA total of " + str( len( Media_Files ) ) + " were found" ) 


    Media_Loop()


