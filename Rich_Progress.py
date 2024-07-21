# rich_progress.py
from rich.progress import (
    Progress, 
    ProgressColumn,
    BarColumn, 
    TextColumn, 
    TimeRemainingColumn,
    TimeElapsedColumn,
    SpinnerColumn
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.console import Group
from rich.live import Live
from rich import print
from rich.theme import Theme

from threading import Lock
import threading
import time

#---------------------------------------------------------------------------------------------------------------#
# Class: DynamicColorBarColumn
# A custom progress bar column that dynamically changes color based on completion percentage.
#---------------------------------------------------------------------------------------------------------------#
class DynamicColorBarColumn(ProgressColumn):
    def render(self, Task ) -> str:
        Percent = Task.completed / Task.total if Task.total else 0
        Bar_Width = 50
        Completed_Width = int(Percent * Bar_Width)
        Remaining_Width = Bar_Width - Completed_Width
        color = self.Calculate_Rainbow_Color(Percent)
        return f"[{color}]{ '-' * Completed_Width }{' ' * Remaining_Width}[/{color}]"

    def Calculate_Rainbow_Color(self, Percent):
        # Rainbow color calculation
        r = int(255 * (1 - Percent))
        g = int(255 * Percent)
        b = 0
        return f"#{r:02x}{g:02x}{b:02x}"

#---------------------------------------------------------------------------------------------------------------#
# Class: CustomStateColumn
# Display a column with State information
#---------------------------------------------------------------------------------------------------------------#
class CustomStateColumn(ProgressColumn):
    def render( self, task ) -> str:
        state = task.fields.get( "state", "" )
        return f"[{state}]"

#---------------------------------------------------------------------------------------------------------------#
# Class: Rich_Progress
# A class to manage rich progress bars for total and detailed progress tracking.
#---------------------------------------------------------------------------------------------------------------#
class Rich_Progress:
    def __init__(self):
        self.Console = Console()
        #self.Console = Console( 
        #    theme=Theme( 
        #        { "bar.complete": "cyan",
        #          "bar.finished": "rgb(114,156,31)",
        #          "bar.pulse": "cyan",
        #          "progress.percentage": "italic bright_cyan"
        #        }
        #    ) 
        #)
        self.Progress_Detailed = Progress(
            TextColumn("[progress.description]{task.description}"),
            SpinnerColumn(),
            BarColumn(),
            #DynamicColorBarColumn(),
            CustomStateColumn(),
            "[progress.percentage]{task.percentage:>3.1f}%",
            TimeElapsedColumn(),
            console=self.Console,
            transient=True
        )

        self.Progress_Overall = Progress(
            TextColumn("[progress.description]{task.description}"),
            SpinnerColumn(),
            BarColumn(),
            #DynamicColorBarColumn(),
            "[progress.percentage]{task.percentage:>3.1f}%",
            TimeElapsedColumn(),
            console=self.Console,
            transient=False
        )

        self.Progress_Sleep = Progress(
            TextColumn("[progress.description]{task.description}"),
            SpinnerColumn(),
            BarColumn(),
            #DynamicColorBarColumn(),
            "[progress.percentage]{task.percentage:>3.1f}%",
            TimeElapsedColumn(),
            console=self.Console,
            transient=False
        )
        
        self.Progress_Table = Table.grid()

        self.Task_Lock = Lock()
        #self.Tasks = {}
        self.Total_Task_ID = self.Progress_Overall.add_task("[blue]Total Progress", total=100)

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Start
    # Start the rich progress context manager.
    #---------------------------------------------------------------------------------------------------------------#
    def Start(self, Text_Overall="Overall Progress", Text_Detailed="Detailed Progress" ):
        #self.Live = Live(
        #    Group(
        #        Panel( self.Progress_Overall, title=Text_Overall, padding=( 1, 2) ),
        #        Panel( self.Progress_Detailed, title=Text_Detailed, padding=( 1, 2) )
        #    ),
        #    console=self.Console,
        #    refresh_per_second=10
        #)
        self.Progress_Table.add_row( 
            Panel.fit( self.Progress_Overall, title= Text_Overall, padding= ( 1, 2 ) )
        )
        self.Progress_Table.add_row( 
            Panel.fit( self.Progress_Detailed, title= Text_Detailed, padding= ( 1, 2 ) )
        )
        self.Progress_Table.add_row( 
            Panel.fit( self.Progress_Sleep, title= "Sleeping", padding= ( 0, 0 ) )
        )
        self.Live = Live ( self.Progress_Table )
        self.Live.start()

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Stop
    # Stop the rich progress context manager.
    #---------------------------------------------------------------------------------------------------------------#
    def Stop(self):
        self.Live.stop()

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Add_Task
    # Add a new detailed task.
    # Returns the task ID.
    #---------------------------------------------------------------------------------------------------------------#
    def Add_Task(self, Description, Total):
        try:
            #print( f"Add_Task: {description}" )
            with self.Task_Lock:
                Task_ID = self.Progress_Detailed.add_task( Description, total=Total )
                #self.Tasks[Task_ID] = {"total": Total, "completed": 0, "visible": True, "description": Description}
                self.Update_Total_Progress()
                return Task_ID
        except Exception as e:
            print( f"An Error occurred in Add_Task():\n{e}" )

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Add_Task
    # Add a new detailed task.
    # Returns the task ID.
    #---------------------------------------------------------------------------------------------------------------#
    def Add_Sleep(self, Description, Seconds ):
        try:
            #print( f"Add_Task: {description}" )
            #with self.Task_Lock:
            Task_ID = self.Progress_Sleep.add_task( Description, total=Seconds )
            #self.Tasks[Task_ID] = {"total": Total, "completed": 0, "visible": True, "description": Description}
            #self.Update_Total_Progress()
            return Task_ID
        except Exception as e:
            print( f"An Error occurred in Add_Task():\n{e}" )


    #---------------------------------------------------------------------------------------------------------------#
    # Function: Update_Task
    # Update the progress of a detailed task.
    #---------------------------------------------------------------------------------------------------------------#
    def Update_Task(self, Task_ID, Advance=None, Total=None, Description=None, State=None ):
        try:
            with self.Task_Lock:
                if ( Advance is not None ):
                    #print( f"Updating {Task_ID} Advance" )
                    self.Progress_Detailed.update(Task_ID, advance=Advance )
                    #self.Tasks[Task_ID]["completed"] += Advance
                if ( Total is not None ):
                    #print( f"Updating {Task_ID} Total" )
                    self.Progress_Detailed.update(Task_ID, total=Total )
                    #self.Tasks[Task_ID]["total"] = Total
                if ( Description is not None ):
                    #print( f"Updating {Task_ID} Description" )
                    self.Progress_Detailed.update(Task_ID, description=Description )
                    #self.Tasks[Task_ID]["description"] = Description
                if ( State is not None ):
                    self.Progress_Detailed.update(Task_ID, state=State )
                self.Update_Total_Progress()
        except Exception as e:
            print( f"An Error occurred in Update_Task():\n{e}" )

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Validate_Task
    # Displays current Task settings - used in debugging
    #---------------------------------------------------------------------------------------------------------------#
    def Validate_Task( self, Task_ID ):
        try:
            with self.Task_Lock:
                Task = self.Progress_Detailed.tasks[Task_ID]

                #Task = self.Tasks.get( Task_ID )
                if Task is None:
                    print(f"Task {Task_ID} not found.")
                else:
                    print( f"Task ID: {Task_ID}" )
                    print( f"\tDescription: {Task.description}" )
                    print( f"\tTotal: {Task.total}" )
                    print( f"\tCompleted: {Task.completed}" )
                    print( f"\tRemaining: {Task.remaining}" )
                    print( f"\tFinished: {Task.finished}" )
                    print( f"\tPercent: {Task.percentage}" )
        except Exception as e:
            print( f"An Error occurred in Validate_Task():\n{e}" )

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Update_Total_Progress
    # Update the overall total progress based on detailed tasks.
    #---------------------------------------------------------------------------------------------------------------#
    def Update_Total_Progress(self):
        try: 
            #Total_Completed = sum(task["completed"] for task in self.Tasks.values())
            Total_Completed = sum( task.completed for task in self.Progress_Detailed.tasks )
            #Total = sum( task["total"] for task in self.Tasks.values() )
            Total = sum( task.total for task in self.Progress_Detailed.tasks )
            if Total > 0:
                self.Progress_Overall.update(self.Total_Task_ID, completed=Total_Completed / Total * 100 )
        except Exception as e:
            print( f"An Error occurred in Update_Total_Progress():\n{e}" )

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Hide_Task
    # Hide a detailed task from the display but keep its progress data.
    #---------------------------------------------------------------------------------------------------------------#
    def Hide_Task(self, Task_ID):
        with self.Task_Lock:
            if Task_ID in self.Tasks:
                self.Progress_Detailed.update(Task_ID, visible=False)
                self.Tasks[Task_ID]["visible"] = False
                self.Update_Total_Progress()


    #---------------------------------------------------------------------------------------------------------------#
    # Function: Update_Total
    # Increase the total of a specified task.
    #---------------------------------------------------------------------------------------------------------------#
    def Update_Total( self, Task_ID, Addition ):
        try:
            with self.Task_Lock:
                Task = self.Progress_Detailed.tasks[Task_ID]

                #Task = self.Tasks.get( Task_ID )
                if Task is None:
                    print(f"Task {Task_ID} not found.")
                else:
                    New_Total = Task.total + Addition
                    self.Progress_Detailed.update( Task_ID, total=New_Total )

        except Exception as e:
            print( f"An Error occurred in Validate_Task():\n{e}" )

    #---------------------------------------------------------------------------------------------------------------#
    # Function: Sleep
    # Sleep for a time period, while providing a status
    #---------------------------------------------------------------------------------------------------------------#
    def Sleep( self, Sleep_Seconds ):
        try:
            #print( f"Getting sleepy" )
            with self.Task_Lock:
                #Task_ID = self.Progress_Detailed.add_task( "Sleeping", total=Seconds )
                Minutes, Seconds = divmod( Sleep_Seconds, 60 )
                Formatted_Time = f"{int(Minutes)} minutes, {int(Seconds)} seconds"
                ID_Sleep = self.Add_Sleep( f"{Formatted_Time}", Sleep_Seconds )
                #print( f"Sleeping: {Seconds} seconds" )
                #ID_Sleep = self.Progress_Overall.add_task( ID_Sleep, description=f"Sleeping...", total=Seconds )
                for i in range( 1, Sleep_Seconds ):
                    time.sleep(1)
                    self.Progress_Sleep.update( ID_Sleep, advance=1 )
                    #self.Update_Task( ID_Sleep, Advance=1 )
                    #print( f"Sleeping... {i} - {i/Seconds * 100}" )
                    #self.Progress_Overall.update( ID_Sleep, completed=i )
                    #completed=Total_Completed / Total * 100
                    # ERIC - this is displaying "Sleeping", but not increasing the progress
                    # it also never stopped sleeping
                
                #self.Progress_Overall.update( ID_Sleep, visible=False )
                self.Progress_Sleep.update( ID_Sleep, visible=False )
        except Exception as e:
            print( f"An Error occurred in Sleep():\n{e}" )


# Example usage
if __name__ == "__main__":
    progress = Rich_Progress()

    def task_worker(task_id, progress, steps=10):
        for _ in range(steps):
            progress.update_task(task_id, advance=10)
            time.sleep(0.5)
        progress.hide_task(task_id)

    progress.Start()

    for i in range(5):
        task_id = progress.add_task(f"Task {i+1}", total=100)
        threading.Thread(target=task_worker, args=(task_id, progress)).start()

    time.sleep(6)  # Simulate doing other work

    progress.Stop()
