

##### *ATLUTD - FixFiles.py*


![](https://github.com/ATLUTDVIPs/ATLUTD-Fix-Files/blob/535089f578944aa459097b95b12666405a4b4b5d/pics/Processing%20-%2013%25.jpg)

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

    App = APP()
    print( f"______________________________________" )
    print( f"Investigate Media in the  following locations" )
    print( f"" )


    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/Games" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/Rumors" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/Dates" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/art" )
    App.Add_Directory( r"D:/Data/Pics/Atlanta United/ATLUTD VIPs/pics" )
    
    


    App.Build_File_List()
    App.Process_Files()

```



*Variables*

Highlighting a few of the variables used throughout the script.

Extensions_Images - this is used to identify image formats.  I need to identify the files vs movies.  Most files will be resized, some will be converted into jpg's.  

Note: I am processing others currently, the .heic format, but I haven't found a proper and decent file conversion process that I trust yet. 
- Extensions_Images_Convert - Used to identify which file formats will be converted into jpg files
- Extensions_Movies - identifying movie files.  I'm aware there are other move formats than .mp4 and .mov.  But to date, I am not dealing with them in this context and do not need to convert them nor store them in drive.  ( I prefer not to have to store movie files in drive if I don't need to due their sizing contraints. )
- Extensions_Movies_Convert - identifying movies which can be converted into mp4 files.  Note: MOV usually take up considerably more space than .mp4 files. 
- Dir_Exiftool - this is simply the directory where the ffmpeg and ffprobe executables are installed.  I am directly invoking the scripts as an outside process from within my script. 
- Age_Convert - this is the age, in days, the script checks before attempting to convert them. ex: if Age_Convert is set at 10, and the file is 11 days old, the script will not attempt to convert it to another format. This saves on needless processing time/resources.
- Number_Threads_Delete - When performing deletes, how many files to be deleting at once.
- Number_Threads_Movies - When converting movies, how many files to be processing at once. Converting movies can be resource intensive, so this just depends on how many you expect to have.
- Number_Threads_Images - When converting images, how many files to be processing at once. Converting images aren't as resource intensive, and complete quickly per image.

Note: for my use case here, information on the threads will end up displaying on screen in the Progress Bars. And few new files are added each iteration. So I don't need a large number of threads.



```

Extensions_Images  = [ '.jpg', '.jpeg', '.webp', '.jfif', '.png' ]  # cannot convert .heic files ( as of 2023-02-18 )
Extensions_Images_Convert  = [ '.webp', '.jfif', '.png' ]
Extensions_Deletes = [ '.ini', '.aae' ]


Extensions_Movies  = [ '.mp4', '.mov' ]
Extensions_Movies_Convert  = [ '.mov' ]
Dir_Exiftool = "D:/Data/Download/apps/ExifTool/exiftool-12.49"

Age_Convert   = 7

Number_Threads_Delete   = 2
Number_Threads_Movies   = 5
Number_Threads_Images   = 15

```

*Media_Loop*


The init builds the Progress Bars in the background in preparation for the data to be obtained. Initially, the Progress Bars are set to hidden. They will be later be changed to be viewed when needed.


```
    #---------------------------------------------------------------------------------------------------------------
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
        print( self.Extensions_Images_Convert )
        print( self.Extensions_Movies_Convert )


```


*Process_Files*

This is the main process flow. At a high level, the job of this flow is to first identify all files needed. Then invoke separate threads for each data type ( Deletes, Movies, Images ).
As each of the sections are essentially the same, I've created a variety of reusable functions for the Progress Bar functionality. Such as creation of Tasks, Updates, clears, etc. These are used here when adding Deletes, Movies, Images, and the individual files to and From the Progress Bar.
The flow initializes the Progress Bar with the following line:


```
with Live( Prep_Table, refresh_per_second = 10 ):

```

Once done, it's up to the process to loop over data and update the Progress Bar data accordingly ( increment totals, make some visible, invisible, etc ).
First up is the Thread_Identify_File - which is used to loop over all files identified in the directory structures. This function is simply sorting individual files into separate lists ( Delete, Movies, or Images ) based on filename extension.

Next up is the Movie section. ( Images is next and will work the same way ). This loops over each individual file and invokes a separate thread. "pool.submit" is what is used to invoke the thread. In this case, it invokes a function ( the first parameter to pool.submit ). The following paramters are what is required by the function.

```

            if ( len ( self.Media_Files_Movies ) > 0 )
                print( f"Processing Movies..." )
                Jobs_Detail_Media_Movies = self.Add_Task( self.Job_Progress_Detail_View, "Movies", len( self.Media_Files_Movies ) )
                self.Jobs_Update_Overall_Total()
                with ThreadPoolExecutor( max_workers = self.Number_Threads_Movies ) as pool:
                    for Media_File in self.Media_Files_Movies:
                        # Launch Thread - calls function
                        pool.submit( self.Thread_Movies, Media_File, Jobs_Detail_Media_Movies ):
						

```


*Thread_Image_Convert*

This function deals with image conversion, resizing, renames.
First, if files are older than a cutoff time period, they are ignored. This prevents us from needing to process every file on the file system. I do not check this earlier, as google docs and windows doesn't always play nice with each other meaning the modified or creation dates can get out of sync at times.
Functionality here will depend on the file type itself ( .jpg, .png, etc ) So those are identified.
I rename all filename extensions to lowercase. Personal preference.
Rename all jpeg's to jpg for standardization.
Other image types are converted into jpg.
Conversion to jpg - this is calling ffmpeg to convert the image file into a jpg. The original image file remains and is deleted afterwards


```
subprocess.run( "ffmpeg -hide_banner -loglevel error -i " + "\"" + Media_File +  "\"" + " " + "\"" + Directory + os.sep + Filename_Base + "-" + Filename_Date + '.jpg' + "\"", shell=True)

```

*The full function*


```

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
                Filename_New = Filename_Base + Filename_Extension
                #print( "Directory: " + Directory + " Filename_Base: " + Filename_Base + "\tFilename_Extension" + Filename_Extension)
                if ( Filename_Extension == ".JPG" ):
                    # Rename to .jpg
                    print( "Renaming Extension on : " + Media_File )
                    try: 
                        Filename_New = Filename_Base + "-" + Filename_Date + '.jpg'
                        os.rename( Media_File, Directory + os.sep + Filename_New )  # not renaming the file, only changing the extension
                     except Exception as e:
                         print( f"Unable to rename: {Media_File}\n\t{str(e)}" )
                if ( Filename_Extension.lower() == ".jpeg".lower() ):
                    # Rename to .jpg
                    print( "Renaming Extension on : " + Media_File )
                    try: 
                        Filename_New = Filename_Base + "-" + Filename_Date + '.jpg'
                        os.rename( Media_File, Directory + os.sep + Filename_New )
                    except Exception as e:
                        print( "Unable to rename: " + Media_File )
                if ( Filename_Extension.lower() in self.Extensions_Images_Convert ):
                    print( "Converting [" + Directory_Parent + "]\t" + Filename_Base + Filename_Extension)
                    subprocess.run( "ffmpeg -hide_banner -loglevel error -i " + "\"" + Media_File +  "\"" + " " + "\"" + Directory + os.sep + Filename_Base + "-" + Filename_Date + '.jpg' + "\"", shell=True)
                    os.remove(  Media_File )
                    Filename_New = Filename_Base + "-" + Filename_Date + '.jpg'


                # will need to check size on all files
                self.Image_Resize( Directory_Parent, Directory, Filename_New )
            except Exception as e:
                print( "An Error has occurred while starting the Image_Convert procedure: " + str( e ) + "\n\t" + Media_File )




```

Any time a file is modified, I add a date-time onto the filename prior to the file extension.  So a filename of File_001.jpg will end up as File_001-2023-01-01_07244944.jpg  This is done to ensure there are NO duplication of filenames.  While google docs by itself can handle filenames, the syncing process will not sync properly when there are duplicates. 

ex:  two files named as file.jpg will not sync to windows with google's sync application, or to the linux version.  The application will either sync one of them, or throw an error indicating that it cannot sync.  This will continue even if you rename one file locally to prevent the duplicate - google sync cannot tell which file to rename properly on google docs, and then simply, doesn't.  Then the files are out of sync.

This remains a danger - if a user adds a file into google docs before my python script runs with a duplicate name, the only fix will be to login to google docs via a browser and rename the filenames.



*Image_Resize*

This function resizes images based on the width and height limits defined.  I have determined those limits based on my experience and desired applications.  These dimensions still produce "good enough" images retaining their quality for what I need, which isn't print quality, but social media.  I can receive a single image from the team which is 25 MB.  I can then reduce it to 340k.  Which is indispensable when it comes to the long-term storage.

Here I'm using ffprobe to obtain the current file dimensions.

```
process = subprocess.run( "ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0:s=x " + "\"" + Path_Check + "\"", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

```

If the dimensions are larger than desired, I run it through the ffmpeg to resize:


```
process_resize = subprocess.run( "ffmpeg -y -hide_banner -loglevel error -i " + "\"" + Path_Check + "\"" + " -vf scale='min(2000,iw)':min'(1500,ih)':force_original_aspect_ratio=decrease " + "\"" + Path_Check + "\"", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

```

*The full function:*

```
    #---------------------------------------------------------------------------------------------------------------
    # Function: Image_Resize
    # Reisizes images based on the height and width limits.  This is done to help reduce file size issues
    #---------------------------------------------------------------------------------------------------------------#
    def Image_Resize( self, Directory_Parent, Directory, Filename ):
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
            Message = Message + "\n\tSize Pre:\t" + self.Human_Readable_Size( File_Size_Pre, 2 )
            Message = Message + "\n\tSize After:\t" + self.Human_Readable_Size( File_Size_Post, 2 )
            Message = Message + "\n\tSize Saved:\t" + self.Human_Readable_Size( File_Size_Pre - File_Size_Post, 2 )
            print( Message )
```
![](https://github.com/ATLUTDVIPs/ATLUTD-Fix-Files/blob/535089f578944aa459097b95b12666405a4b4b5d/pics/Processing%20-%2045%25.jpg)

![](https://github.com/ATLUTDVIPs/ATLUTD-Fix-Files/blob/535089f578944aa459097b95b12666405a4b4b5d/pics/Processing%20-%20converting%202.jpg)

*Thread_Movie_Convert*

The movie convert function will be similar to the image convert function.  

This is the process to convert into an mp4

```
subprocess.run( "ffmpeg -hide_banner -loglevel error -i " + "\"" + Media_File +  "\"" + " " + "\"" + Directory + os.sep + Final_Filename + "\" -map_metadata 1", shell=True)

```

A difference however, is in doing the conversion with movies vs images, is that I need to copy across exif data.  This is really where dates comes from in movies.  And especially .MOV files.  Without getting the exif data, the date will default to the date of "NOW", when the file is being modified.  Which is completely inaccurate.  Think if you've copied a movie made a year ago.  You wouldn't want today's date on it!  So if the exif date exist in the original file, this will end up copying it.

```
subprocess.run( Dir_Exiftool + os.sep + "exiftool.exe -q -overwrite_original -ee -TagsFromFile " + Media_File + " \"-FileCreateDate<CreationDate\" \"-CreateDate<CreationDate\" \"-ModifyDate<CreationDate\" \"" + Directory + os.sep + Final_Filename + "\" ", shell=True)

```


*The full function:*

```


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

```


Once this script runs, all media in the directory structure has been renamed, converted, and resized. As a result, it will now be re-synced to google drive, and re-distributed to whomever is sharing the media.
This is able to keep the overall storage requirements down. ex: In my storage, I was well over the 15 GB limit, and have reduced this to below 1 GB.

Here's a quick randomized example of doing conversion with a directory structure of files. Some files in the directory include those to be deleted, ignored, Movies to be converted, and images to be converted.

![Alt Text](https://github.com/ATLUTDVIPs/ATLUTD-Fix-Files/blob/535089f578944aa459097b95b12666405a4b4b5d/pics/Directory%20Structure%20-%20Before.jpg)

Directory structure after script is run
![](https://github.com/ATLUTDVIPs/ATLUTD-Fix-Files/blob/535089f578944aa459097b95b12666405a4b4b5d/pics/Directory%20Structure%20-%20After.jpg)

