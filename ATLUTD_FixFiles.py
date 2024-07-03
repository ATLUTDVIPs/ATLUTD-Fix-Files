
#---------------------------------------------------------------------------------------------------------------#
# Outside Requirements
# py -m pip install --upgrade package_name
#---------------------------------------------------------------------------------------------------------------#
#   ffprobe - installed and in path
#   ffmpeg - installed and in path


#---------------------------------------------------------------------------------------------------------------#
# Load Modules
# py -m pip install --upgrade
#---------------------------------------------------------------------------------------------------------------#
import os                                                            # interact with the file system
from datetime import datetime                                        # work with dates and times
import subprocess                                                    # used for multi threading

import argparse                                                      # used for easy parsing script input parametesr
import glob                                                          # handling wildcard searches, ex:  *.jpg

from rich.live import Live                                           # the rich modules are used for progress bars
from rich.panel import Panel
from rich.progress import (BarColumn, MofNCompleteColumn, Progress,
                           SpinnerColumn, TextColumn, TimeElapsedColumn)
from rich.table import Table

from concurrent.futures import ThreadPoolExecutor                    # used for multi threading

from hachoir.parser import createParser                              # hachoir is used to handle movie metadata 
from hachoir.metadata import extractMetadata
import sys
import time                                                          # used to add sleep
import shutil                                                        # ability to move files

from wand.image import Image                                         # ability to work with heic files

#---------------------------------------------------------------------------------------------------------------#
# In Progress
#
#---------------------------------------------------------------------------------------------------------------#
# verify .avif image files



#---------------------------------------------------------------------------------------------------------------#
# Defining the Class
#---------------------------------------------------------------------------------------------------------------#
class APP( ):
    Directories = []
    Media_Files = []
    
    Media_Files_Delete = []
    Media_Files_Images = []
    Media_Files_Movies = []
    Media_Files_Other  = []

    Today = datetime.today()
    Age_Convert   = 7
    Total_Deletes = 0
    Total_Images  = 0
    Total_Movies  = 0
    Extensions_Images          = [ '.jpg', '.jpeg', '.webp', '.jfif', '.png', '.heic' ]  # cannot convert .heic files ( as of 2023-02-18 )
    Extensions_Images_Convert  = [ '.webp', '.jfif', '.png', '.heic' ]
    Extensions_Deletes         = [ '.ini', '.aae' ]

    Extensions_Movies          = [ '.mp4', '.mov' ]
    Extensions_Movies_Convert  = [ '.mov' ]
    Dir_Exiftool = "D:/Data/Download/apps/ExifTool/exiftool-12.49"

    File_Search_Pattern = "/**/*.*"

    # Progress Bar
    Job_Progress_Overall_View = ""
    Job_Progress_Detail_View = ""
    Jobs_Overall = ""
    Jobs_Detail = ""

    # Threads
    Number_Threads_Identify = 5
    Number_Threads_Delete   = 2
    Number_Threads_Movies   = 5
    Number_Threads_Images   = 15

    #---------------------------------------------------------------------------------------------------------------#
    # Class initialization
    # - Defines the default Progress Bar, Platform type
    #---------------------------------------------------------------------------------------------------------------#
    def __init__ ( self ):
        self.Job_Progress_Overall_View = Progress( 
            "{task.description}",
            SpinnerColumn(),
            BarColumn(),
            TextColumn( "[progress.percentage]{task.percentage:>3.0f}%" ),
            TimeElapsedColumn(),
            )
        self.Job_Progress_Detail_View = Progress( 
            "{task.description}",
            SpinnerColumn(),
            BarColumn(),
            TextColumn( "[progress.percentage]{task.percentage:>3.0f}%" ),
            TimeElapsedColumn()
            )
        self.Jobs_Overall = self.Job_Progress_Overall_View.add_task( "[blue]Overall Status", total=0 )
        self.Jobs_Detail  = self.Job_Progress_Detail_View.add_task( "[blue]Detail Status", visible=False, total=0 )

        print( f"Media Conversions" )
        print( f"Converting Media older than {self.Age_Convert} days old" )
        print( f"Converting the following file types:" )
        print( f"\t{self.Extensions_Images_Convert}" )
        print( f"\t{self.Extensions_Movies_Convert}" )

    #---------------------------------------------------------------------------------------------------------------#
    # Updates the Total Progress Total value
    #---------------------------------------------------------------------------------------------------------------#
    def Jobs_Update_Overall_Total( self ):
        #Total = sum( task.total for task in self.Job_Progress_Detail_View.tasks )
        Total = len( self.Media_Files_Delete ) + len( self.Media_Files_Images ) + len( self.Media_Files_Movies )

        #print( f"Set Job_Progress_Overall_View total to: {Total}")
        self.Job_Progress_Overall_View.update( self.Jobs_Overall, total = Total, refresh=True )

    #---------------------------------------------------------------------------------------------------------------#
    # Updates the Overall Progress Bar Display
    #---------------------------------------------------------------------------------------------------------------#
    def Jobs_Update_Overall_Progress( self ):
        self.Job_Progress_Overall_View.update( self.Jobs_Overall, advance=1, refresh=True )



    #---------------------------------------------------------------------------------------------------------------#
    # Creates the Jobs Default View
    # Defines the tables, layout
    #---------------------------------------------------------------------------------------------------------------#
    def Jobs_Build_Default_View( self, Overall_Title=None, Detail_Title=None ):
        if not( Overall_Title ):
            Overall_Title = "Overall Progress"
        if not( Detail_Title ):
            Detail_Title = "Detail View"
        New_Table = Table.grid()
        New_Table.add_row( 
            Panel.fit( self.Job_Progress_Overall_View, title="[b]" + Overall_Title, border_style="yellow", padding=(0, 0) )
        )
        New_Table.add_row( 
            Panel.fit( self.Job_Progress_Detail_View, title="[b]" + Detail_Title, border_style="yellow", padding=(1, 1) )
        )
        return New_Table


    #---------------------------------------------------------------------------------------------------------------#
    # Function: Detail_Display_Additional_Info
    # Create additional information to be displayed in the Detail view
    # Returns the Task, to be used later
    #---------------------------------------------------------------------------------------------------------------#
    def Detail_Display_Additional_Info( self, String ):
        Current_Task = self.Job_Progress_Detail_View.add_task( "[cyan]" + String, total=1 )

        return Current_Task

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Detail_Display_Increment_Additional_Info
    # Increments the Task by 1
    #---------------------------------------------------------------------------------------------------------------#
    def Detail_Display_Increment_Additional_Info( self, Current_Task ):
        self.Job_Progress_Detail_View.update( Current_Task, advance=1, refresh=True )


    #---------------------------------------------------------------------------------------------------------------#
    # Function: Detail_Display_Additional_Info
    # Hides the job when done
    #---------------------------------------------------------------------------------------------------------------#
    def Detail_Close_Additional_Info( self, Current_Task ):
        self.Job_Progress_Detail_View.update( Current_Task, visible=False, refresh=True )


    #---------------------------------------------------------------------------------------------------------------#
    # Function: Build_File_List
    # Loop through the directory to get a list of all files
    #---------------------------------------------------------------------------------------------------------------#
    def Build_File_List( self ):

        for Directory in self.Directories:
            print()
            print( f"Looking for files in {Directory}" )
            Files = glob.glob( Directory + os.sep + self.File_Search_Pattern, recursive=True )
            if not Files:
                print( f"\tNo files were found to process." )
                #sys.exit()
            else:
                print( f"\t{len( Files )} files were found to process." )
                #logging.debug( f"A total of {len( Files )} files were found to process." )

                for File in Files:
                    if (os.path.isfile(File) ):
                        self.Media_Files.append( File )

        self.Jobs_Update_Overall_Total()

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Add_Directory
    # Add new directory to the list of directories
    #---------------------------------------------------------------------------------------------------------------#
    def Add_Directory( self, Directory ):
        if os.path.exists( Directory ):
            self.Directories.append( Directory )
        else:
            print( f"Error: The directory does not exist: {Directory}" )


    #---------------------------------------------------------------------------------------------------------------#
    # Function: Process_Files
    # Begin looping through data
    #---------------------------------------------------------------------------------------------------------------#
    def Process_Files( self ):
        Prep_Table = self.Jobs_Build_Default_View( )

        print( "" )
        print( f"___________________________________________" )
        print( f"Beginning to Process over found Media Files" )
        print()

        with Live( Prep_Table, refresh_per_second = 10 ):

            Jobs_Detail_Identify_File = self.Add_Task( self.Job_Progress_Detail_View, "Identifying Media", len( self.Media_Files ) )
            self.Jobs_Update_Overall_Total()
    
            with ThreadPoolExecutor( max_workers = self.Number_Threads_Identify ) as pool:
                for Media_File in self.Media_Files:
                    # Launch Thread - calls function
                    pool.submit( self.Thread_Identify_File, Media_File, Jobs_Detail_Identify_File )

            if ( len ( self.Media_Files_Delete ) > 0 ):
                print( f"Processing Deletes..." )
                Jobs_Detail_Media_Delete = self.Add_Task( self.Job_Progress_Detail_View, "Deletes", len( self.Media_Files_Delete ) )
                self.Jobs_Update_Overall_Total()
                with ThreadPoolExecutor( max_workers = self.Number_Threads_Delete ) as pool:
                    for Media_File in self.Media_Files_Delete:
                        # Launch Thread - calls function
                        pool.submit( self.Thread_Delete, Media_File, Jobs_Detail_Media_Delete )

            if ( len ( self.Media_Files_Movies ) > 0 ):
                print( f"Processing Movies..." )
                Jobs_Detail_Media_Movies = self.Add_Task( self.Job_Progress_Detail_View, "Movies", len( self.Media_Files_Movies ) )
                self.Jobs_Update_Overall_Total()
                with ThreadPoolExecutor( max_workers = self.Number_Threads_Movies ) as pool:
                    for Media_File in self.Media_Files_Movies:
                        # Launch Thread - calls function
                        pool.submit( self.Thread_Movies, Media_File, Jobs_Detail_Media_Movies )

            if ( len ( self.Media_Files_Images ) > 0 ):
                print( f"Processing Images..." )
                Jobs_Detail_Media_Images = self.Add_Task( self.Job_Progress_Detail_View, "Images", len( self.Media_Files_Images ) )
                self.Jobs_Update_Overall_Total()
                with ThreadPoolExecutor( max_workers = self.Number_Threads_Images ) as pool:
                    for Media_File in self.Media_Files_Images:
                        # Launch Thread - calls function
                        pool.submit( self.Thread_Images, Media_File, Jobs_Detail_Media_Images )

            '''
            print( f"The following files could not be processed" )
            for File in self.Media_Files_Other:
                print( File )
            '''

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Add_Task
    # Add a task to the View
    # Returns the Job
    #---------------------------------------------------------------------------------------------------------------#
    def Add_Task( self, View, Title, Size ):
        Job = View.add_task( "[blue]" + Title, visible=True, total=Size )
        return Job

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Thread_Delete
    # The Individual Thread dealing with file deletions
    #---------------------------------------------------------------------------------------------------------------#
    def Thread_Delete( self, Media_File, Jobs_Detail_Media_Delete ):
        #print( f"Thread-delete: {Media_File}" )
        Filename = os.path.basename( Media_File )
        FileSize = os.path.getsize(Media_File)
        try:
            Current_Task = self.Detail_Display_Additional_Info( Filename )
            self.Job_Progress_Detail_View.update( Current_Task, total=FileSize )
            #time.sleep(1)

            print( f"\tDeleting: {Filename}" )
            try:
                os.remove(  Media_File )
            except:
                print( f"\tUnable to delete: {Media_File}" )

            self.Detail_Display_Increment_Additional_Info( Current_Task )

            self.Detail_Close_Additional_Info( Current_Task )
            self.Job_Progress_Detail_View.update( Jobs_Detail_Media_Delete, advance=1 )
            self.Job_Progress_Overall_View.update( self.Jobs_Overall, advance=1 )
        except Exception as e:
            print( f"an error has occurred in the Delete Thread:  {str(e)}" )

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Thread_Movies
    # The Individual Thread dealing with movie files
    #---------------------------------------------------------------------------------------------------------------#
    def Thread_Movies( self, Media_File, Jobs_Detail_Media_Movies ):
        #print( f"Thread-delete: {Media_File}" )
        Filename = os.path.basename( Media_File )
        FileSize = os.path.getsize(Media_File)
        try:
            Current_Task = self.Detail_Display_Additional_Info( Filename )
            self.Job_Progress_Detail_View.update( Current_Task, total=FileSize )
            #time.sleep(1)

            self.Thread_Movie_Convert( Media_File )

            self.Detail_Display_Increment_Additional_Info( Current_Task )

            self.Detail_Close_Additional_Info( Current_Task )
            self.Job_Progress_Detail_View.update( Jobs_Detail_Media_Movies, advance=1 )
            self.Job_Progress_Overall_View.update( self.Jobs_Overall, advance=1 )
        except Exception as e:
            print( f"an error has occurred in the Movies Thread:  {str(e)}" )


    #---------------------------------------------------------------------------------------------------------------#
    # Function: Thread_Images
    # The Individual Thread dealing with image files
    #---------------------------------------------------------------------------------------------------------------#
    def Thread_Images( self, Media_File, Jobs_Detail_Media_Images ):
        #print( f"Thread-delete: {Media_File}" )
        Filename = os.path.basename( Media_File )
        FileSize = os.path.getsize(Media_File)
        try:
            Current_Task = self.Detail_Display_Additional_Info( Filename )
            self.Job_Progress_Detail_View.update( Current_Task, total=FileSize )
            #time.sleep(1)

            self.Thread_Image_Convert( Media_File )

            self.Detail_Display_Increment_Additional_Info( Current_Task )

            self.Detail_Close_Additional_Info( Current_Task )
            self.Job_Progress_Detail_View.update( Jobs_Detail_Media_Images, advance=1 )
            self.Job_Progress_Overall_View.update( self.Jobs_Overall, advance=1 )
        except Exception as e:
            print( f"an error has occurred in the Images Thread:  {str(e)}" )

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Thread_Identify_File
    # The Individual Thread dealing with file identifying media files
    #---------------------------------------------------------------------------------------------------------------#
    def Thread_Identify_File( self, Media_File, Jobs_Detail_Identify_Data ):

        Filename_Extension = os.path.splitext(Media_File)[1]
        Filename_Base = os.path.splitext(Media_File)[0]
        
        if ( Filename_Extension.lower() in self.Extensions_Deletes ):
            self.Media_Files_Delete.append( Media_File )

        elif ( Filename_Extension.lower() in self.Extensions_Images ):
            self.Media_Files_Images.append( Media_File )

        elif ( Filename_Extension.lower() in self.Extensions_Movies ):
            self.Media_Files_Movies.append( Media_File )

        else:
            self.Media_Files_Other.append( Media_File )

        self.Job_Progress_Detail_View.update( Jobs_Detail_Identify_Data, advance=1 )


    #---------------------------------------------------------------------------------------------------------------#
    # Function: Thread_Movie_Convert
    # Convert the indidivdual Movie
    #---------------------------------------------------------------------------------------------------------------#
    def Thread_Movie_Convert( self, Media_File ):
        Filename           = os.path.basename( Media_File )
        Filename_Extension = os.path.splitext(Media_File)[1]
        Filename_Base      = os.path.splitext(Filename)[0]

        File_Modified_date = datetime.fromtimestamp( os.path.getmtime( Media_File ) )
        Age = self.Today - File_Modified_date
        if ( Age.days < self.Age_Convert ):

            try:
                Filename_Date = datetime.now().strftime('%Y-%m-%d_%H24%M%S') # '2022-09-18_111632'
                Directory = os.path.dirname( Media_File ) 
                Directory_Parent = Directory.split( "/" )
                Directory_Parent = Directory_Parent[ len( Directory_Parent ) -1 ]
                Filename_New = Filename_Base + Filename_Extension

                if ( Filename_Extension == ".MP4" ):
                    # Rename to .mp4
                    print( f"Renaming Extension on: {Media_File}" )
                    try: 
                        #Filename_New = Filename_Base + "-" + Filename_Date + '.mp4'
                        os.rename( Media_File, Directory + os.sep + Filename_New )  # not renaming the file, only changing the extension
                    except Exception as e:
                        print( "Unable to rename: " + Media_File )

                if ( Filename_Extension.lower() in self.Extensions_Movies_Convert ):
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
                            subprocess.run( self.Dir_Exiftool + os.sep + "exiftool.exe -q -overwrite_original -ee -TagsFromFile " + Media_File + " \"-FileCreateDate<CreationDate\" \"-CreateDate<CreationDate\" \"-ModifyDate<CreationDate\" \"" + Directory + os.sep + Final_Filename + "\" ", shell=True)
                            os.remove(  Media_File )
                        else:
                            print( "\tFile wasn't converted successfully" )


                    Filename_New = Filename_Base + "-" + Filename_Date + '.mp4'

                # will need to check size on all files
                #Image_Resize( Directory_Parent, Directory, Filename_New )

            except Exception as e:
                print( "An Error has occurred while starting the Movie_Convert procedure: " + str( e ) + "\n\t" + Media_File )



    #---------------------------------------------------------------------------------------------------------------#
    # Function: Thread_Image_Convert
    # Convert the indidivdual image
    #---------------------------------------------------------------------------------------------------------------#
    def Thread_Image_Convert( self, Media_File ):
        Filename           = os.path.basename( Media_File )
        Filename_Extension = os.path.splitext(Media_File)[1]
        Filename_Base      = os.path.splitext(Filename)[0]

        File_Modified_date = datetime.fromtimestamp( os.path.getmtime( Media_File ) )
        Age = self.Today - File_Modified_date
        if ( Age.days < self.Age_Convert ):

            try:
                Filename_Date = datetime.now().strftime('%Y-%m-%d_%H24%M%S') # '2022-09-18_111632'
                Directory = os.path.dirname( Media_File ) 
                #Directory_Parent = Directory.split( os.sep )
                Directory_Parent = Directory.split( "/" )
                Directory_Parent = Directory_Parent[ len( Directory_Parent ) -1 ]
                Filename_New = f"{Filename_Base}{Filename_Extension}"
                #print( "Directory: " + Directory + " Filename_Base: " + Filename_Base + "\tFilename_Extension" + Filename_Extension)
                if ( Filename_Extension == ".JPG" ):
                    # Rename to .jpg
                    #print( "Renaming Extension on : " + Media_File )
                    print( f"Renaming Extension on : {Filename_Base}" )
                    try: 
                        Filename_New = f"{Filename_Base}-{Filename_Date}.jpg"
                        #print( f"to: {Filename_New}" )
                        #time.sleep(10)
                        #os.rename( Media_File, Directory + os.sep + Filename_New )
                        shutil.move( Media_File, Directory + os.sep + Filename_New )
                        #os.rename( Media_File, Filename_New )  # not renaming the file, only changing the extension
                    except Exception as e:
                        print( f"Unable to rename: {Media_File}\n\t{str(e)}" )
                if ( Filename_Extension.lower() == ".jpeg".lower() ):
                    # Rename to .jpg
                    print( "Renaming Extension on : " + Media_File )
                    try: 
                        Filename_New = f"{Filename_Base}-{Filename_Date}.jpg"
                        os.rename( Media_File, Directory + os.sep + Filename_New )
                    except Exception as e:
                        print( "Unable to rename: " + Media_File )
  
                if ( Filename_Extension.lower() in self.Extensions_Images_Convert ):
                    if ( Filename_Extension.lower() == ".heic" ):
                        print( "Converting [" + Directory + "]\t" + Filename_Base + Filename_Extension)
                        try:
                            Filename_New = f"{Filename_Base}-{Filename_Date}.jpg"
                            # Convert HEIC to JPG using wand
                            with Image(filename=Media_File ) as img:
                                #Exif_Orientation = img.metadata.get("exif:Orientation", 1)
                                # ... (orientation correction logic as before) ...
                                img.format = "jpeg"
                                img.save(filename=os.path.join( Directory, Filename_New ) )
                                if ( os.path.exists( os.path.join( Directory, Filename_New ) ) ):
                                    os.remove( Media_File )

                        except Exception as e:
                            print(f"Error processing {Filename_Base}: {e}")  # Handle potential errors
                    else:

                        print( f"Converting [{Directory_Parent}]\t{Filename_Base}{Filename_Extension}" )
                        subprocess.run( "ffmpeg -hide_banner -loglevel error -i " + "\"" + Media_File +  "\"" + " " + "\"" + Directory + os.sep + Filename_Base + "-" + Filename_Date + '.jpg' + "\"", shell=True)
                        os.remove(  Media_File )
                        Filename_New = Filename_Base + "-" + Filename_Date + '.jpg'

                # will need to check size on all files
                self.Image_Resize( Directory_Parent, Directory, Filename_New )
            except Exception as e:
                print( f"An Error has occurred in Thread_Image_Convert(): {e}\n\t{Media_File}" )


    #---------------------------------------------------------------------------------------------------------------#
    # Function: Image_Resize
    # Reisizes images based on the height and width limits.  This is done to help reduce file size issues
    #---------------------------------------------------------------------------------------------------------------#
    def Image_Resize( self, Directory_Parent, Directory, Filename ):
        try:
            Width_Limit = 2000
            Height_Limit = 1500
            Message = "\n  [" + Directory_Parent + "]\t" + Filename
            #Log_Info( "      Checking size on: " + file )
            Path_Check = f"{Directory}\\{Filename}"
            Command = f"ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0:s=x \"{Path_Check}\""
            #Command = f"ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0:s=x {os.sep}{Path_Check}{os.sep}"
            #process = subprocess.run( "ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0:s=x " + "\"" + Path_Check + "\"", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            process = subprocess.run( Command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            output = process.stdout
            #print( f"\n***DEBUG:\nprocess = {process}\nCommand = {Command}" )
            #Log_Info( "      " + str( output ) )
            try:
                Check_Width = int( output.split("x")[0] )
                Check_Height = int( output.split("x")[1] )
            except:
                Message = f"{Message}\n\t*** Invalid file\n{process.stdout}"
                #print( f"{Message}" )
                #print( "\t[" + Directory_Parent + "]\t" + Filename + "\n\t\t " + Message )
                #print( "*** Invalid file: " + Path_Check)
                return

            #print( f"\n***DEBUG A: Filename: {Filename}" + 
            #       f"\nCheck_Width: {Check_Width}" +
            #       f"\nCheck_Height: {Check_Height}" +
            #       f"\nWidth_Limit: {Width_Limit}" +
            #       f"\nHeight_Limit: {Height_Limit}"
            #    )
            #print( f"Output: {output}" )
            #print( f"Check_Width: {Check_Width}" )
            #print( f"Check_Height: {Check_Height}" )
            #print( f"Width_Limit: {Width_Limit}" )
            #print( f"Height_Limit: {Height_Limit}" )
            #print( f"{Message}\n\tWidth:\t{Check_Width}" )
            #print( f"{Message}\n\tHeight:\t{Check_Height}" )
            if ( Check_Width > Width_Limit ) or ( Check_Height > Height_Limit ):
                #print( f"\n***DEBUG" )
                Message = f"{Message}\n\tReducing Size"
                Message = f"{Message}\n\tWidth:\t{Check_Width}"
                Message = f"{Message}\n\tHeight:\t{Check_Height}"
                File_Size_Pre = os.path.getsize( Path_Check )
                Command = f"ffmpeg -y -hide_banner -loglevel error -i \"{Path_Check}\" -vf scale='min(2000,iw)':min'(1500,ih)':force_original_aspect_ratio=decrease \"{Path_Check}\""
                #print( f"\n***DEBUG:\nCommand = {Command}" )
                #process_resize = subprocess.run( "ffmpeg -y -hide_banner -loglevel error -i " + "\"" + Path_Check + "\"" + " -vf scale='min(2000,iw)':min'(1500,ih)':force_original_aspect_ratio=decrease " + "\"" + Path_Check + "\"", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                process_resize = subprocess.run( Command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                #print( f"\n***DEBUG:\nprocess = {process_resize}\nCommand = {Command}" )
                output_resize = process_resize.stdout
                File_Size_Post = os.path.getsize( Path_Check )
                Message = f"{Message}\n\tSize Pre:\t{self.Human_Readable_Size( File_Size_Pre, 2 )}"
                Message = f"{Message}\n\tSize After:\t{self.Human_Readable_Size( File_Size_Post, 2 )}"
                Message = f"{Message}\n\tSize Saved:\t{self.Human_Readable_Size( File_Size_Pre - File_Size_Post, 2 )}"
                print( f"{Message}" )
                #print( f"***DEBUG D: Filename_Extension: {Filename_Extension}" )
        except Exception as e:
            print( f"An Error has occurred in Image_Resize():\n\t{e}" )
    #---------------------------------------------------------------------------------------------------------------#
    # Function: Human_Readable_Size
    # Display file sizes in a human readable format
    # Returns human readable string
    #---------------------------------------------------------------------------------------------------------------#
    def Human_Readable_Size( self, size, decimal_places=2):
        try:
            for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']:
                if size < 1024.0 or unit == 'PiB':
                    break
                size /= 1024.0
            return f"{size:.{decimal_places}f} {unit}"
        except Exception as e:
            print( f"An Error has occurred in Human_Readable_Size():\n\t{e}" )

#---------------------------------------------------------------------------------------------------------------#
# Main start
#---------------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':
    #parser = argparse.ArgumentParser()
    #folder_base = r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/pics"

    #parser.add_argument( "-i", "--input", help="mp3 path, ex: " + folder_base, required=False )
    #args = parser.parse_args()
    #if not args.input:
    #    folder_base = r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/pics"
    #    print( f"Using default base directory: {folder_base}" )


    App = APP()
    print( f"______________________________________" )
    print( f"Investigate Media in the  following locations" )
    print( f"" )

    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/Games" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/Games - ATLUTD2" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/Rumors" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/Dates" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/art" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/pics" )
    #App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/Games/2024" )

    

    App.Build_File_List()
    App.Process_Files()

