"""The main application file for SPIKES - Spectrum Plotter and Interfacing Kit for EMI Scanning.

This file contains the main CustomTkinter application class and the main loop.

Further details about the application can be found in the Github repository.
"""
import customtkinter as ctk

import frames

import styling_options

class App(ctk.CTk):
    """The main Custom Tkinter application class for SPIKES 
    """
    def __init__(self) -> None:
        """Initializes the SPIKES application window and its component frames.
        """
        super().__init__()
        
        self.minsize(1400, 800)
        
        self.title("SPIKES - Spectrum Plotter and Interfacing Kit for EMI Scanning")
        
        self.configure(fg_color=styling_options.color_scheme['bg_color'], text_color=styling_options.color_scheme['text_color'])
        
        self.controls = frames.Controls(self)
        self.controls.place(x=20, y=20)

        self.plot = frames.Plot(self)
        self.plot.place(x=20, y=20) 

        self.progress = frames.Progress(self)
        self.progress.place(x=20, y=20)

        self.coms = frames.Coms(self)
        self.coms.place(x=20, y=20)
    
        self.initial_width = self.winfo_width()
        self.initial_height = self.winfo_height()

        self.bind("<Configure>", self.on_resize)
        self.wm_attributes('-zoomed', True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def on_resize(self, event) -> None:
        """Triggers on resizing of the application window and adjusts the layout of its components accordingly.

        :param event: Configure event.
        :type event: tkinter.Event
        
        :return: None
        """
        current_height = self.winfo_height()
        current_width = self.winfo_width()
        
        if event.widget == self and (self.initial_width != current_width or self.initial_height != current_height):            
            self.controls.resize(current_height)
            self.controls.place(x = current_width - 360, y = 20)
            
            self.plot.resize(current_width, current_height)
            self.plot.place(x = 20, y = 20)
            
            self.progress.resize(current_width)
            self.progress.place(x = 20, y = current_height - 280)

            self.coms.resize(current_width)
            self.coms.place(x = 20, y = current_height - 220)

        self.initial_width = self.winfo_width()
        self.initial_height = self.winfo_height()
    
    def on_close(self) -> None:
        """Show confirmation dialog before closing
        """
        if frames.plot_object.lines == [] and frames.progress_object.progress_bar.get() == 0:
            self.destroy()
            return

        dialog = frames.ProceedDialog(self)
        result = dialog.show()
        if result:
            self.destroy()
            return        
            
if __name__ == "__main__":
    app = App()
    app.mainloop()