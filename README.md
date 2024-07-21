

## *ATLUTD - FixFiles.py*


![](https://github.com/ATLUTDVIPs/ATLUTD-Fix-Files/blob/bc7538cedcb429ac024a2ea194a02128d494fdd5/pics/Processing%20-%20Completed.jpg)


##### Updates 2024-07-21
The script has been re-written from scratch.
- Makes use of custom Rich_Progress class.  Making the reporting easier.
- Makes use of custom Logger class.  Making logging more consistent.
- Can now handle and convert .avif files.
- Can now handle and convert .heic files.
- File types, processing now uses json variables in the class.
- Keeping track of total reduced size pre and post processing.



##### Use Case

I utilize Google drive to keep track of my media. Utilizing Drive allows me to access files on a variety of platforms and keep the media in sync. I'm able to share individual files, or entire folders with others easily.
In keeping files in sync, I'm able to keep files on my iphone, access them in the cloud through a browser, or from my home windows computer.
The limitation is that google current caps the space at 15 GB. I will blow past this with the amount of media I produce / acquire. And individual image files may not take up much space, but 4000 of them does. A single .mov file can. 100 of them certainly does.

I needed a way to go through my directory structures, and re-size the media. I needed to have this done efficiently and repeatedly. As new media is added from any source and synced to drive, then pushed to the various resources, I needed to ensure the new media would then be re-sized.

I've written a python script that will run on my home windows machine. Scheduled to run hourly.


**Requirements**

- ffmpeg
- ffprobe

Both are acquired from: https://ffmpeg.org/ These are an application which allow you to read and write the media tags on movie files. Not all movie files work the same however. I won't go into specifics here as that's not the scope. It took some trial and error to get the conversion to work probably from format to format with the correct quality and ensuring the tags are passed from source to destination. It's not documented as there are simply too many variations.
Note: I've since learned that python does have a module for ffmpeg. However, I do not believe there is one for ffprobe, which I require.

I've written this script as a multithreaded class script. It will first gather a list of files to process, then for each file found, it will initiate a new thread. For my processing. I separate out processing into 3 separate groups. One for the deletes, Movies, and Images. Each have a separate number of threads and will be processed in a separate order due to distinct processing rules and requirements.

I also needed a way to show progress back to the user. While looping through thousands of files on the file system is fast, looping through files AND processing each of them as an image or movie is slow. So I needed to show to the user that something is actually going on.

**Script**

The main process beings by creating the class, then adding in different directories to process. Each directory is added to an array in the class.


```

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

```



*Variables*

Highlighting a few of the variables used throughout the script.

Class variables handling image and movie processing are stored in a json format.  This helps keep things clean, more consistent, and easier to maintain.

```
    Data_Types = {
        "Deletes":        [ '.ini', '.aae' ],
        "Images":         [ '.jpg', '.jpeg', '.webp', '.jfif', '.png', '.heic', '.avif' ],
        "Images_Convert": [ '.webp', '.jfif', '.png', '.heic', '.avif' ],
        "Movies":         [ '.mp4', '.mov' ],
        "Movies_Convert": [ '.mov' ]
    }
```

Data_Types - this is used to identify image formats.  I need to identify the files vs movies.  Most files will be resized, some will be converted into jpg's.  

- Data_Types["Images_Convert"] - Used to identify which file formats will be converted into jpg files
- Data_Types["Movies"] - identifying movie files.  I'm aware there are other move formats than .mp4 and .mov.  But to date, I am not dealing with them in this context and do not need to convert them nor store them in drive.  ( I prefer not to have to store movie files in drive if I don't need to due their sizing contraints. )
- Data_Types["Movies_Convert"] - identifying movies which can be converted into mp4 files.  Note: MOV usually take up considerably more space than .mp4 files. 
- Dir_Exiftool - this is simply the directory where the ffmpeg and ffprobe executables are installed.  I am directly invoking the scripts as an outside process from within my script. 
- Age_Convert - this is the age, in days, the script checks before attempting to convert them. ex: if Age_Convert is set at 10, and the file is 11 days old, the script will not attempt to convert it to another format. This saves on needless processing time/resources.
- Threads["Deletes"] - When performing deletes, how many files to be deleting at once.
- Threads["Movies"] - When converting movies, how many files to be processing at once. Converting movies can be resource intensive, so this just depends on how many you expect to have.
- Threads["Images"] - When converting images, how many files to be processing at once. Converting images aren't as resource intensive, and complete quickly per image.
- Media[] - During the initial folder scan, this holds a listing of all files found based on type.

Note: for my use case here, information on the threads will end up displaying on screen in the Progress Bars. And few new files are added each iteration. So I don't need a large number of threads.



```
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
        "Movies_Convert": [ '.mov' ]
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

```
*Build_File_List()*
This function is used to scan the directories and keep track of what files need to be processed.  When data is found, the file location is appended into the Media{} variable.  ex:  if an image is found, it is appended to Media["Images"].
Then, based on what media types are found, the appropriate progress bars will be created.

![](https://github.com/ATLUTDVIPs/ATLUTD-Fix-Files/blob/781d8436200a989598c504fe00e0951b44ad0852/pics/Processing%20-%20Started.jpg)

```
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
```

*Process_Files*
This begins processing.  Each data type will be processed separately.  This was done to ensure movies to limit resources being used.
Deletes are not resource instensive.  File processing doesn't take much.  However, converting movies can be resource heavy.
Each file for the different types is launched in a separate thread.  
"pool.submit" is what is used to invoke the thread. In this case, it invokes a function ( the first parameter to pool.submit ). The following paramters are what is required by the function.

```
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
```




*Thread_Image()*

This function deals with image conversion, resizing, renames.
First, if files are older than a cutoff time period, they are ignored. This prevents us from needing to process every file on the file system. I do not check this earlier, as google docs and windows doesn't always play nice with each other meaning the modified or creation dates can get out of sync at times.
Functionality here will depend on the file type itself ( .jpg, .png, etc ) So those are identified.
I rename all filename extensions to lowercase. Personal preference.
Rename all jpeg's to jpg for standardization.
Other image types are converted into jpg.
Conversion to jpg - this is calling ffmpeg to convert the image file into a jpg. The original image file remains and is deleted afterwards
.heic files are handled separately from other media types, based on what is required for those types of files.
For each file, the metadata is copied across from the original file to the final file.  This required scanning the original file for data, then copying it across.

*The full function*


```
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

```






Any time a file is modified, I add a date-time onto the filename prior to the file extension.  So a filename of File_001.jpg will end up as File_001-2023-01-01_07244944.jpg  This is done to ensure there are NO duplication of filenames.  While google docs by itself can handle filenames, the syncing process will not sync properly when there are duplicates. 

ex:  two files named as file.jpg will not sync to windows with google's sync application, or to the linux version.  The application will either sync one of them, or throw an error indicating that it cannot sync.  This will continue even if you rename one file locally to prevent the duplicate - google sync cannot tell which file to rename properly on google docs, and then simply, doesn't.  Then the files are out of sync.

This remains a danger - if a user adds a file into google docs before my python script runs with a duplicate name, the only fix will be to login to google docs via a browser and rename the filenames.



*Image_Resize()*

This function resizes images based on the width and height limits defined.  I have determined those limits based on my experience and desired applications.  These dimensions still produce "good enough" images retaining their quality for what I need, which isn't print quality, but social media.  I can receive a single image from the team which is 25 MB.  I can then reduce it to 340k.  Which is indispensable when it comes to the long-term storage.

Here I'm using ffprobe to obtain the current file dimensions.
The ffmpeg process doesn't bring across metadata during the resize process.  As such, the script needs to scan the file prior to resizing, and copy the metadata across after resizing.

![](https://github.com/ATLUTDVIPs/ATLUTD-Fix-Files/blob/c8ac6fd077372466bad6e7c46aa493dfc29a3e7c/pics/Resizing.jpg)


*The full function:*

```
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
```






*Thread_Movie()*

The movie convert function will be similar to the image convert function.  
Overall processing is similar to processing an image, with slight differences.


*The full function:*

```
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

```



I have a few utility functions.

*Human_Readable_Size()*
This is strictly to show file sizes in a human readable format.
```
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
```



*Get_Unique_Filename()*
During processing, I will need to rename files.  As such, I first need to ensure the new filename doesn't already exist.
If an existing filename is found, this function will add a counter onto the filename.  And will keep doing so, for a configurable amount, until a unique filename is found.

```
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
```


![](https://github.com/ATLUTDVIPs/ATLUTD-Fix-Files/blob/bc7538cedcb429ac024a2ea194a02128d494fdd5/pics/Processing%20-%20Completed.jpg)


Once this script runs, all matching media in the directory structure has been renamed, converted, and resized. As a result, it will now be re-synced to google drive, and re-distributed to whomever is sharing the media.
This is able to keep the overall storage requirements down. ex: In my storage, I was well over the 15 GB limit, and have reduced this to below 1 GB.

Here's a quick randomized example of doing conversion with a directory structure of files. Some files in the directory include those to be deleted, ignored, Movies to be converted, and images to be converted.

![](https://github.com/ATLUTDVIPs/ATLUTD-Fix-Files/blob/535089f578944aa459097b95b12666405a4b4b5d/pics/Directory%20Structure%20-%20Before.jpg)

Directory structure after script is run

![](https://github.com/ATLUTDVIPs/ATLUTD-Fix-Files/blob/535089f578944aa459097b95b12666405a4b4b5d/pics/Directory%20Structure%20-%20After.jpg)

