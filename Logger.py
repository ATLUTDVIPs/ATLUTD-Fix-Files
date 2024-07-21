
#---------------------------------------------------------------------------------------------------------------#
# Use
#
# from Logger import CustomLogger                                      # Standardized Logging
#
# # Initialize the logger
# Logger = CustomLogger( "Path", os.path.basename(__file__).split(".py")[0] + '.log', "Debug" )
#
# # Use the log function
# Logger.log('Info', 'This is an info message')
# Logger.log('Error', 'This is an error message')
#---------------------------------------------------------------------------------------------------------------#


#---------------------------------------------------------------------------------------------------------------#
# Load Modules
#
#---------------------------------------------------------------------------------------------------------------#
import os                                                            # used to interact with the file system
import logging
from rich import print


#---------------------------------------------------------------------------------------------------------------#
# Class
#---------------------------------------------------------------------------------------------------------------#
class CustomLogger:
    
    Log_Levels = {
        'Debug':    logging.DEBUG,
        'Info':     logging.INFO,
        'Warning':  logging.WARNING,
        'Error':    logging.ERROR,
        'Critical': logging.CRITICAL
    }
    Log_Level = logging.DEBUG

    #---------------------------------------------------------------------------------------------------------------#
    # Class initialization
    # - Defines the default Progress Bar, Platform type
    #---------------------------------------------------------------------------------------------------------------#
    def __init__(self, Name, Logging_Level='Debug' ):
        Name = os.path.basename( Name )

        if Logging_Level in self.Log_Levels:
            self.Log_Level = self.Log_Levels[Logging_Level]
        else:
            raise ValueError(f"Unexpected log level: {Logging_Level}")

        #print( f"[red]Class initializing from {Name} with logging level: {self.Log_Level}" )

        self.Logger = logging.getLogger( Name )
        self.Logger.setLevel(self.Log_Level)

        # Create a formatter for file logging
        self.File_Formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(funcName)s - Line %(lineno)d\n\t%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p' )

        # Determine the log file path based on the current directory and module name
        Dir_Log = os.path.join( os.getcwd(), 'logs' )
        Log_File = os.path.join( os.getcwd(), "logs", f'{Name.split(".py")[0]}.log' )

        # Ensure the log directory exists
        os.makedirs(Dir_Log, exist_ok=True)

        # File handler for logging to a file (create a new file on each initialization)
        File_Handler = logging.FileHandler(Log_File, mode='w', encoding="utf-8")
        File_Handler.setFormatter( self.File_Formatter )
        self.Logger.addHandler( File_Handler )

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Log
    # Logging
    # Enter a Type and Text
    #---------------------------------------------------------------------------------------------------------------#
    def Log( self, Text, Type=None ):

        if ( Type is None ):
            print( f"[white]{Text}[/white]" )
            return

        Type = Type or 'Info'  # Default to 'Info' if Type is not provided
        Type = self.Log_Levels.get( Type, logging.INFO )  # Defaulting to INFO
        
        Record = logging.LogRecord('custom_logger', Type, '', 0, Text, None, None)
        Formatted_Text = self.File_Formatter.format( Record )
        self.Logger.handle( Record )

         # Conditionally print to the console based on the logging level
        if Type >= self.Logger.getEffectiveLevel():
            if ( Type <= logging.DEBUG ):
                print( f"[blue]{Text}[/blue]" )
            elif ( Type <= logging.INFO ):
                print( f"[white]{Text}[/white]" )
            elif ( Type <= logging.WARNING ):
                print( f"[yellow]{Text}[/yellow]" )
            elif ( Type <= logging.ERROR ):
                print( f"[bold red]{Text}[/bold red]" )
            elif ( Type <= logging.CRITICAL ):
                print( f"[bold white on red]{Text}[/bold white on red]" )
            else:
                print( f"[white]{Text}[/white]" )

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Log
    # Logging
    # Enter a Type and Text
    #---------------------------------------------------------------------------------------------------------------#
    def Log2( self, Type, Text ):
        Set_Level = logging.getLogger().getEffectiveLevel()

        try:
            if Type == 'Debug':
                logging.debug(Text)
                if ( Set_Level <= logging.DEBUG ):
                    print( f"[blue]{Text}[/blue]" )
            elif Type == 'Info':
                logging.info(Text)
                if ( Set_Level <= logging.INFO ):
                    print( f"[white]{Text}[/white]" )
            elif Type == 'Warning':
                logging.warning(Text)
                if ( Set_Level <= logging.WARNING ):
                    print( f"[yellow]{Text}[/yellow]" )
            elif Type == 'Error':
                logging.error(Text)
                if ( Set_Level <= logging.ERROR ):
                    print( f"[bold red]{Text}[/bold red]" )
            elif Type == 'Critical':
                logging.critical(Text)
                if ( Set_Level <= logging.CRITICAL ):
                    print( f"[bold white on red]{Text}[/bold white on red]" )
            else:
                print( f"[white]{Text}[/white]" )
                #raise ValueError(f"Invalid log type: {Type}")
        
        #except PermissionError:
        #    print("Permission error while writing to the log file.")
        except Exception as e:
            print(f"An error has occurred while writing to the log file: {e}")


if __name__ == "__main__":
    #App = CustomLogger()

    # Example usage:
    logger = CustomLogger( __file__, "Debug" )
    logger.Log( f"This is a message without a set type" )
    logger.Log( f"This is a debug message", "Debug" )
    logger.Log( f"This is an info message", "Info" )
    logger.Log( f"This is a warning message", "Warning" )
    logger.Log( f"This is an error message", "Error" )
    logger.Log( f"This is a critical message", "Critical" )
    