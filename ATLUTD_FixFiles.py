
#---------------------------------------------------------------------------------------------------------------#
# Outside Requirements
# py -m pip install --upgrade package_name
#---------------------------------------------------------------------------------------------------------------#
# ffprobe - installed and in path
# ffmpeg - installed and in path
# Obtained from: https://www.videohelp.com/software/ffmpeg



#---------------------------------------------------------------------------------------------------------------#
# Load Modules
# py -m pip install --upgrade
#---------------------------------------------------------------------------------------------------------------#
import sys
import os                                                        # interact with the file system
from Rich_Progress import Rich_Progress                          # Used for displaying progress bars and other rich text in the console
from Logger import CustomLogger                                  # Standardized Logging
from datetime import datetime                                    # work with dates and times
from rich import print
import glob                                                      # handling wildcard searches, ex:  *.jpg
from concurrent.futures import ThreadPoolExecutor                # used for multi threading
import subprocess                                                # used for multi threading

from hachoir.parser import createParser                          # hachoir is used to handle movie metadata 
from hachoir.metadata import extractMetadata                     # working with movie metadata
from wand.image import Image                                     # ability to work with heic files
from time import sleep                                           # ability to introduce time delays


#---------------------------------------------------------------------------------------------------------------#
# Class: Album_Parser
# Parses albums and downloads images from provided JSON data
#---------------------------------------------------------------------------------------------------------------#
class Fix_Files():
    Logger = CustomLogger( __file__, "Debug" )
    Today = datetime.today()

    Age_Convert  = 7
    Width_Limit  = 2000
    Height_Limit = 1500
    Size_Before = 0
    Size_After  = 0

    Dir_Exiftool = r"D:\Data\Download\apps\ExifTool\exiftool-12.89_64"
    Dir_FFMpeg   = r"D:\Data\Scripts\ffmpeg"

    Media = {
        "Directories": [],
        "Files":       [],
        "Deletes":     [],
        "Images":      [],
        "Movies":      [],
        "Others":      []
    }

    Data_Types = {
        "Deletes":        [ '.ini', '.aae' ],
        "Images":         [ '.jpg', '.jpeg', '.webp', '.jfif', '.png', '.heic', '.avif' ],
        "Images_Convert": [ '.webp', '.jfif', '.png', '.heic', '.avif' ],
        "Movies":         [ '.mp4', '.mov' ],
        "Movies_Convert": [ '.mov' ],

    }

    Threads = {
        "Deletes":  2,
        "Movies":   5,
        "Images":   15
    }

    Tasks = {
        "Deletes": None,
        "Movies":  None,
        "Images":  None,
        "Others":  None
    }


    #---------------------------------------------------------------------------------------------------------------#
    # Initialize the class
    #---------------------------------------------------------------------------------------------------------------#
    def __init__( self ):
        self.Progress = Rich_Progress()

        self.Logger.Log( f"[cyan]__________________________________________________________________________________[/cyan]" )
        self.Logger.Log( f"[cyan] Media Conversions[/cyan]" )
        self.Logger.Log( f"[cyan]__________________________________________________________________________________[/cyan]" )
        self.Logger.Log( f"Converting Media older than {self.Age_Convert} days old" )
        self.Logger.Log( f"Working on the following file types:" )
        for Key, Values in self.Data_Types.items():
            self.Logger.Log( f"\t{Key}\t{Values}")
        #self.Logger.Log( f"\t{self.Data_Types}" )


    #---------------------------------------------------------------------------------------------------------------#
    # Add new directory to the list of directories
    #---------------------------------------------------------------------------------------------------------------#
    def Add_Directory( self, Directory ):

        if ( os.path.exists( Directory ) ):
            self.Media["Directories"].append( Directory )
        else:
            self.Logger.Log( f"Error: The directory does not exist: {Directory}", "Error" )


    #---------------------------------------------------------------------------------------------------------------#
    # Function: Build_File_List
    # Loop through the directory to get a list of all files
    #---------------------------------------------------------------------------------------------------------------#
    def Build_File_List( self ):
        print()
        self.Logger.Log( f"Scanning the following Directories" )
        self.Progress.Start( "Overall Status", "Files" )

        for directory in self.Media["Directories"]:
            self.Logger.Log( f"\t{directory}" )
            directory_files = glob.glob( directory + os.sep + "/**/*.*", recursive=True )

            for File in directory_files:
                File_Modified_date = datetime.fromtimestamp( os.path.getmtime( File ) )
                Age = self.Today - File_Modified_date
                if ( Age.days < self.Age_Convert ):

                    self.Media["Files"].append( File )
                    Filename_Extension = os.path.splitext( File )[1].lower()

                    # Log file and its extension
                    #self.Logger.Log(f"Processing file: {file} with extension: {filename_extension}")

                    if Filename_Extension in self.Data_Types["Deletes"]:
                        if len(self.Media["Deletes"]) == 0:
                            self.Tasks["Deletes"] = self.Progress.Add_Task("Deletes", Total=0)
                        self.Media["Deletes"].append( File )
                    elif Filename_Extension in self.Data_Types["Movies"]:
                        if len(self.Media["Movies"]) == 0:
                            self.Tasks["Movies"] = self.Progress.Add_Task("Movies", Total=0)
                        self.Media["Movies"].append( File )
                    elif Filename_Extension in self.Data_Types["Images"]:
                        if len(self.Media["Images"]) == 0:
                            self.Tasks["Images"] = self.Progress.Add_Task("Images", Total=0)
                        self.Media["Images"].append( File )
                    else:
                        self.Media["Others"].append( File )

        if len(self.Media["Files"]) == 0:
            self.Logger.Log( f"\tNo files were found to process.", "Warning" )
        else:
            # Files found
            self.Logger.Log(f"Found the following data: ")
            if "Deletes" in self.Tasks and self.Tasks["Deletes"] is not None:
                self.Progress.Update_Task( self.Tasks["Deletes"], Total=len(self.Media["Deletes"]) )
                self.Logger.Log( f"\tDeletes: {len(self.Media['Deletes'])}" )
            if "Images" in self.Tasks and self.Tasks["Images"] is not None:
                self.Progress.Update_Task( self.Tasks["Images"], Total=len(self.Media["Images"]) )
                self.Logger.Log( f"\tImages: {len(self.Media['Images'])}")
            if "Movies" in self.Tasks and self.Tasks["Movies"] is not None:
                self.Progress.Update_Task( self.Tasks["Movies"], Total=len(self.Media["Movies"]) )
                self.Logger.Log( f"\tMovies: {len(self.Media['Movies'])}" )
            if "Others" in self.Tasks and self.Tasks["Others"] is not None:
                self.Progress.Update_Task( self.Tasks["Others"], Total=len(self.Media["Others"]) )
                self.Logger.Log( f"\tOthers: {len(self.Media['Others'])}" )


    #---------------------------------------------------------------------------------------------------------------#
    # Begin looping through data
    #---------------------------------------------------------------------------------------------------------------#
    def Process_Files( self ):
        self.Logger.Log( f"[cyan]__________________________________________________________________________________[/cyan]" )
        self.Logger.Log( f"[cyan] Processing Files less than {self.Age_Convert} days old[/cyan]" )
        self.Logger.Log( f"[cyan]__________________________________________________________________________________[/cyan]" )


        if ( len( self.Media["Deletes"] ) > 0 ):
            with ThreadPoolExecutor( max_workers = self.Threads["Deletes"] ) as pool:
                for File in self.Media["Deletes"]:
                    # Launch Thread - calls function
                    pool.submit( self.Thread_Delete, File )

        if ( len( self.Media["Images"] ) > 0 ):
            with ThreadPoolExecutor( max_workers = self.Threads["Images"] ) as pool:
                for File in self.Media["Images"]:
                    # Launch Thread - calls function
                    pool.submit( self.Thread_Image, File )

        if ( len( self.Media["Movies"] ) > 0 ):
            with ThreadPoolExecutor( max_workers = self.Threads["Movies"] ) as pool:
                for File in self.Media["Movies"]:
                    # Launch Thread - calls function
                    pool.submit( self.Thread_Movie, File )


    #---------------------------------------------------------------------------------------------------------------#
    # Function: Thread_Delete
    # The Individual Thread dealing with file deletions
    #---------------------------------------------------------------------------------------------------------------#
    def Thread_Delete( self, File ):
        try: 
            Filename = os.path.basename( File )
            FileSize = os.path.getsize( File )
            self.Logger.Log( f"\tDeleting: {Filename}", "Debug" )
            self.Delete_File_With_Retries( File )

            self.Progress.Update_Task( self.Tasks["Deletes"], Advance=1 )

        except Exception as e:
            self.Logger.Log( f"An error has occurred in Thread_Delete():\n\t{str(e)}", "Error" )


    #---------------------------------------------------------------------------------------------------------------#
    # The Individual Thread dealing with Images
    #---------------------------------------------------------------------------------------------------------------#
    def Thread_Image( self, File ):
        try: 
            Filename           = os.path.basename( File )
            Filename_Extension = os.path.splitext( File )[1]
            Filename_Base      = os.path.splitext( Filename )[0]
            Directory = os.path.dirname(  File )
            Directory_Parent = os.path.basename( Directory )

            File_Modified_date = datetime.fromtimestamp( os.path.getmtime( File ) )
            Age = self.Today - File_Modified_date
            if ( Age.days < self.Age_Convert ):
                self.Logger.Log( f"Processing: /{Directory_Parent}\t{Filename}" )
                Filename_Date = datetime.now().strftime('%Y-%m-%d_%H24%M%S') # '2022-09-18_111632'
                Directory = os.path.dirname( File ) 
                #Directory_Parent = Directory.split( os.sep )
                #Directory_Parent = Directory.split( "/" )
                #Directory_Parent = Directory_Parent[ len( Directory_Parent ) -1 ]
                #Filename_New = self.Get_Unique_Filename( Directory=Directory, Filename_Base=Filename_Base, Filename_Extension=Filename_Extension )
                Filename_New = f"{Filename_Base}{Filename_Extension}" # Default case for unprocessed files
                
                if ( Filename_Extension == ".JPG" ):
                    # rename to .jpg
                    try:
                        self.Logger.Log( f"Renaming Extension on: {File}" )
                        #Filename_New = f"{Filename_Base}-{Filename_Date}{Filename_Extension.lower()}"
                        Filename_New = f"{Filename_Base}{Filename_Extension.lower()}"
                        os.rename( File, os.path.join( Directory, Filename_New ) )  # not renaming the file, only changing the extension
                    except Exception as e:
                        self.Logger.Log( f"Unable to rename: {File}", "Error" )
                elif ( Filename_Extension.lower() == ".jpeg".lower() ):
                    try:
                        self.Logger.Log( f"Renaming Extension on: {File}" )
                        Filename_New = self.Get_Unique_Filename( Directory=Directory, Filename_Base=Filename_Base, Filename_Extension=".jpg" )
                        os.rename( File, os.path.join( Directory, Filename_New ) )  # not renaming the file, only changing the extension
                    except Exception as e:
                        self.Logger.Log( f"Unable to rename: {File}", "Error" )
                elif ( Filename_Extension.lower() in self.Data_Types["Images_Convert"] ):
                    self.Logger.Log( f"Converting: [[{Directory_Parent}]]\t{Filename_Base + Filename_Extension}" )
                    if ( Filename_Extension.lower() == ".heic" ):
                        try:
                            Filename_New = self.Get_Unique_Filename( Directory=Directory, Filename_Base=f"{Filename_Base}-{Filename_Date}", Filename_Extension=".jpg" )
                            with Image(filename=File ) as img:
                                img.format = "jpeg"
                                img.save( filename=os.path.join( Directory, Filename_New ) )
                                if ( os.path.exists( os.path.join( Directory, Filename_New ) ) ):
                                    self.Delete_File_With_Retries( File )

                        except Exception as e:
                            self.Logger.Log( f"Error processing: {File}\n{e}", "Error" )
                    else:
                        Filename_New = self.Get_Unique_Filename( Directory=Directory, Filename_Base=f"{Filename_Base}-{Filename_Date}", Filename_Extension=".jpg" )
                        cmd = f"{os.path.join(self.Dir_FFMpeg, "ffmpeg.exe")} -hide_banner -loglevel error -i \"{File}\" \"{os.path.join( Directory, Filename_New )}\""
                        cmd_Result = subprocess.run( cmd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE )
                        if ( cmd_Result.returncode != 0 ):
                            Status = cmd_Result.stderr #.decode('utf-8')
                            self.Logger.Log( f"Error in Thread_Image(), performing conversion:\n{cmd}\n\n{Status}", "Error" )
                        else:
                            self.Delete_File_With_Retries( File )

                # For all files, resize
                self.Image_Resize( Directory_Parent, Directory, Filename_New )

            self.Progress.Update_Task( self.Tasks["Images"], Advance=1 )

        except Exception as e:
            self.Logger.Log( f"An error has occurred in Thread_Images():\n\t{str(e)}", "Error" )


    #---------------------------------------------------------------------------------------------------------------#
    # The Individual Thread dealing with Movies
    #---------------------------------------------------------------------------------------------------------------#
    def Thread_Movie( self, File ):
        try: 
            Filename           = os.path.basename( File )
            Filename_Extension = os.path.splitext( File )[1]
            Filename_Base      = os.path.splitext( Filename )[0]

            File_Modified_date = datetime.fromtimestamp( os.path.getmtime( File ) )
            Age = self.Today - File_Modified_date
            
            if ( Age.days < self.Age_Convert ):
                # File is new
                Filename_Date = datetime.now().strftime('%Y-%m-%d_%H24%M%S') # '2022-09-18_111632'
                Directory = os.path.dirname(  File ) 
                Directory_Parent = os.path.basename( Directory )
                #Filename_New = Filename_Base + Filename_Extension
                Filename_New = self.Get_Unique_Filename( Directory=Directory, Filename_Base=Filename_Base, Filename_Extension=Filename_Extension )
                
                if ( Filename_Extension == ".MP4" ):
                    # Rename to .mp4
                    self.Logger.Log( f"Renaming Extension on: {File}" )
                    try:
                        #Filename_New = Filename_Base + "-" + Filename_Date + '.mp4'
                        Filename_New = Filename_New = Filename_Base + Filename_Extension.lower()
                        os.rename( File, os.path.join( Directory, Filename_New ) )  # not renaming the file, only changing the extension
                    except Exception as e:
                        self.Logger.Log( f"Unable to rename: {File}", "Error" )
                if ( Filename_Extension.lower() in self.Data_Types["Movies_Convert"] ):
                    self.Logger.Log( f"Converting: /{Directory_Parent}\t{Filename_Base + Filename_Extension}" )
                    
                    Parser = createParser( File )

                    if ( Parser ):
                        File_Size_Before = os.path.getsize( File )
                        self.Size_Before = self.Size_Before + File_Size_Before

                        # Attempt to extract metadata.  If not found, set to null
                        try:
                            Metadata = extractMetadata( Parser )
                        except Exception as e:
                            self.Logger.Log( f"Unable to extract Metadata\n{e}", "Error" )
                            Metadata = None

                        for Info in Metadata.exportPlaintext():
                                if Info.split(':')[0] == '- Creation date':
                                    Date_Temp = Info.partition( "date: " )[2]
                                    Date_Object = datetime.strptime( Date_Temp, "%Y-%m-%d %H:%M:%S" )
                                    #Date_Metadata = str( Date_Object.year ) + "-" + str( Date_Object.month ) + "-" + str( Date_Object.day ) + "_" + str( Date_Object.hour ) + "-" + str( Date_Object.minute ) + "-" + str( Date_Object.second )
                                    Date_Metadata = f"{Date_Object.year}-{Date_Object.month}-{Date_Object.day}_{Date_Object.hour}-{Date_Object.minute}-{Date_Object.second}"
                        Parser.stream._input.close()
                        #Final_Filename = Filename_Base + "-" + Date_Metadata + ".mp4"
                        Filename_New = self.Get_Unique_Filename( Directory=Directory, Filename_Base=f"{Filename_Base}-{Date_Metadata}", Filename_Extension=".mp4" )
                        # Attepting to convert the file
                        cmd = f"{os.path.join(self.Dir_FFMpeg, "ffmpeg.exe")} -hide_banner -loglevel error -i \"{File}\" \"{os.path.join( Directory, Filename_New )}\" -map_metadata 1"
                        cmd_Result = subprocess.run( cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
                        #print( cmd_Result )

                        if ( cmd_Result.returncode != 0 ):
                            Status = cmd_Result.stderr #.decode('utf-8')
                            self.Logger.Log( f"Error in Thread_Movie(), performing conversion:\n{cmd}\n\n{Status}", "Error" )
                        else:
                            if ( os.path.isfile( os.path.join( Directory, Filename_New ) ) ):
                                # Copy the original metadata to the new file ( ex: preserve the create date )
                                cmd = f"{os.path.join(self.Dir_Exiftool, "exiftool.exe")} -q -overwrite_original -ee -TagsFromFile \"{File}\" \"-FileCreateDate<CreationDate\" \"-CreateDate<CreationDate\" \"-ModifyDate<CreationDate\" \"{os.path.join(Directory, Filename_New)}\""
                                #self.Logger.Log( f"cmd: {cmd}")
                                #subprocess.run( self.Dir_Exiftool + os.sep + "exiftool.exe -q -overwrite_original -ee -TagsFromFile " + Media_File + " \"-FileCreateDate<CreationDate\" \"-CreateDate<CreationDate\" \"-ModifyDate<CreationDate\" \"" + Directory + os.sep + Final_Filename + "\" ", shell=True)
                                cmd_Result = subprocess.run( cmd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE )
                                if ( cmd_Result.returncode != 0 ):
                                    Status = cmd_Result.stderr #.decode('utf-8')
                                    self.Logger.Log( f"Error in Thread_Movie(), writing metadata:\n{cmd}\n\n{Status}", "Error" )
    
                                self.Delete_File_With_Retries( File )
                                File_Size_After = os.path.getsize( os.path.join( Directory, Filename_New ) )
                                self.Size_After  = self.Size_After + File_Size_After


                    else:
                        self.Logger.Log( f"Unable to parse file for metadata", "Error" )
                   

            self.Progress.Update_Task( self.Tasks["Movies"], Advance=1 )

        except Exception as e:
            self.Logger.Log( f"An error has occurred in Thread_Movie():\n\t{File}\n\t{str(e)}", "Error" )

    #---------------------------------------------------------------------------------------------------------------#
    # Reisizes images based on the height and width limits.  This is done to help reduce file size issues
    #---------------------------------------------------------------------------------------------------------------#
    def Image_Resize( self, Directory_Parent, Directory, Filename ):
        try:
            #self.Logger.Log( f"Resizing: [[{Directory_Parent}]]\t{Filename}" )
            Path_Check = f"{Directory}\\{Filename}"
            cmd = f"{os.path.join(self.Dir_FFMpeg, "ffprobe.exe")} -v error -select_streams v -show_entries stream=width,height -of csv=p=0:s=x \"{Path_Check}\""

            cmd_Result = subprocess.run( cmd, shell=True, stdout=subprocess.PIPE )
            #process = subprocess.run( Command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            #output = cmd_Result.stdout
            if ( cmd_Result.returncode != 0 ):
                Status = cmd_Result.stderr #.decode('utf-8')
                self.Logger.Log( f"Error in Image_Resize(): ffprobe\n{cmd}\n\n{Status}", "Error" )
            else:
                #self.Logger.Log( f"stdout.split(x)[0]: {cmd_Result.stdout}", "Debug" )
                # Decode the output
                try:
                    Output = cmd_Result.stdout.decode().strip()
                    Check_Width, Check_Height = Output.split('x')
                    Check_Width  = int( Check_Width )
                    Check_Height = int( Check_Height )
                    #self.Logger.Log( f"\tWidth: {Check_Width}\tHeight: {Check_Height}\t{Filename}", "Debug" )
                except Exception as e:
                    self.Logger.Log( f"Error in Image_Resize(): Checking Size\n{e}", "Error" )
                if ( Check_Width > self.Width_Limit ) or ( Check_Height > self.Height_Limit ):
                    Directory_Parent = os.path.basename( Directory )
                    self.Logger.Log( f"\tWidth: {Check_Width}\tHeight: {Check_Height}\t{Directory_Parent}/{Filename}", "Debug" )
                    File_Size_Before = os.path.getsize( Path_Check )
                    self.Size_Before = self.Size_Before + File_Size_Before

                    Filename_Extension = os.path.splitext( Filename )[1]
                    Filename_Base      = os.path.splitext( Filename )[0]
                    
                    Filename_New = self.Get_Unique_Filename( Directory=Directory, Filename_Base=f"{Filename_Base}", Filename_Extension=Filename_Extension )
                    Filename_New = os.path.join( Directory, Filename_New )
                    # This is not copying the metadata across correctly.  Will need to copy it manually
                    cmd = f"{os.path.join(self.Dir_FFMpeg, "ffmpeg.exe")} -y -hide_banner -loglevel error -i \"{Path_Check}\" -vf scale='min({self.Width_Limit},iw)':min'({self.Height_Limit},ih)':force_original_aspect_ratio=decrease -map_metadata 0 \"{Filename_New}\""
                    cmd_Result = subprocess.run( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True )
                    #cmd_Result = subprocess.run( cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)                    
                    
                    if ( cmd_Result.returncode != 0 ):
                        Status = cmd_Result.stderr #.decode('utf-8')
                        self.Logger.Log( f"Error in Image_Resize(): resize\n{cmd}\n\n{cmd_Result.returncode}\n\n{Status}", "Error" )
                        #self.Logger.Log( f"{cmd_Result}", "Error" )
                    else:
                        cmd = f"{os.path.join(self.Dir_Exiftool, "exiftool.exe")} -q -overwrite_original -ee -TagsFromFile \"{os.path.join( Directory, Filename)}\" -all:all \"{Filename_New}\""
                        cmd_Result = subprocess.run( cmd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE )
                        if ( cmd_Result.returncode != 0 ):
                            Status = cmd_Result.stderr #.decode('utf-8')
                            self.Logger.Log( f"Error in Image_Resize(), writing metadata:\n{cmd}\n\n{Status}", "Error" )
                            self.Delete_File_With_Retries( Filename_New )
                        else:
                            self.Delete_File_With_Retries( os.path.join( Directory, Filename ) )
                            os.rename( Filename_New, os.path.join( Directory, Filename ) )

                        File_Size_After = os.path.getsize( Path_Check )
                        self.Size_After  = self.Size_After + File_Size_After
                        self.Logger.Log( f"\tPresize: {self.Human_Readable_Size( File_Size_Before )}\tPostsize: {self.Human_Readable_Size( File_Size_After )}\t{Filename}" )

        except Exception as e:
            self.Logger.Log( f"An Error has occurred in Image_Resize():\n\t{e}", "Error" )
        

    #---------------------------------------------------------------------------------------------------------------#
    # Display file sizes in a human readable format
    # Returns human readable string
    #---------------------------------------------------------------------------------------------------------------#
    def Human_Readable_Size( self, size, decimal_places=2 ):
        try:
            for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']:
                if size < 1024.0 or unit == 'PiB':
                    break
                size /= 1024.0
            return f"{size:.{decimal_places}f} {unit}"
        except Exception as e:
            print( f"An Error has occurred in Human_Readable_Size():\n\t{e}" )

    #---------------------------------------------------------------------------------------------------------------#
    # Ensures the filename is unique by appending a counter if necessary
    #---------------------------------------------------------------------------------------------------------------#
    def Get_Unique_Filename( self, Directory, Filename_Base, Filename_Extension, Max_Attempts=10 ):
        Counter = 0
        Filename_New = Filename_Base + Filename_Extension

        while os.path.exists( os.path.join( Directory, Filename_New ) ):
            Counter += 1
            if Counter > Max_Attempts:
                raise Exception(f"Error: Unable to find a unique filename after {Max_Attempts} attempts.")
            Filename_New = f"{Filename_Base}_{Counter}{Filename_Extension}"
        
        return Filename_New

    #---------------------------------------------------------------------------------------------------------------#
    # Final Stats
    #---------------------------------------------------------------------------------------------------------------#
    def Report( self ):
        print()
        self.Logger.Log( f"\tTotal Directories Processed: {len( self.Media['Directories'])}" )
        self.Logger.Log( f"\tTotal Files Processed: {len( self.Media['Files'])}" )
        self.Logger.Log( f"\tTotal Deletes: {len( self.Media['Movies'])}" )
        self.Logger.Log( f"\tTotal Images: {len( self.Media['Images'])}" )
        self.Logger.Log( f"\tTotal Others: {len( self.Media['Others'])}" )
        print()
        self.Logger.Log( f"\tTotal Size Before: {self.Human_Readable_Size( self.Size_Before )}" )
        self.Logger.Log( f"\tTotal Size After:  {self.Human_Readable_Size( self.Size_After )}" )
        self.Logger.Log( f"\tTotal Size Saved:  {self.Human_Readable_Size( self.Size_Before - self.Size_After )}" )
        print()

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Delete_File_With_Retries
    # Tries to delete a file with a specified number of retries.
    # Logs an error message if unable to delete the file after the retries.
    #---------------------------------------------------------------------------------------------------------------#
    def Delete_File_With_Retries( self, File, Retries=3, Delay=1 ):
        for Attempt in range( Retries ):
            try:
                os.remove( File )
                break
            except Exception as e:
                if Attempt < Retries - 1:
                    sleep( Delay )  # Wait before retrying
                else:
                    self.Logger.Log( f"Unable to delete: {File}\n\t{e}", "Error" )


#---------------------------------------------------------------------------------------------------------------#
# Main Processing
#---------------------------------------------------------------------------------------------------------------#
if __name__ == "__main__":
    App = Fix_Files()

    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/Games" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/Games - ATLUTD2" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/Rumors" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/Dates" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/art" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/pics" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/temp" )

    App.Build_File_List()
    App.Process_Files()
    App.Report()
    print()
