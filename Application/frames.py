"""This module Contains the UI Elements for the SPIKES Application.
"""
import customtkinter as ctk
import threading

import backend
import plotting

import styling_options

plot_object = None
coms_object = None
progress_object = None
config_lst = None
config_dicts = None
old_choice = "RELOAD"

class Controls(ctk.CTkFrame):
    """Containing the controls.
    """
    def __init__(self, parent: ctk.CTkFrame) -> None:
        """Defines and initializes the controls for the SPIKES application.
        
        :param parent: Parent frame for the controls.
        :type parent: ctk.CTkFrame
        
        :return: None
        """
        super().__init__(parent)

        global config_lst
        global config_dicts
        
        self.init_controls_state = {
            'stop_button_state':  'disabled',
            'start_button_state': 'disabled',
            'clear_button_state': 'disabled',
            'select_config_state':  'normal',
            }
                
        self.frame_width   = 340
        self.widget_width  = self.frame_width - 40
        self.widget_height = 50
        
        self.sweep_time = 0
        
        config_lst, config_dicts = backend.get_yamls()
        
        self.control_frame = ctk.CTkCanvas(
                                    self, 
                                    width=self.frame_width, 
                                    height=0, 
                                    bg=styling_options.color_scheme['face_color'],
                                    highlightthickness=0,
                                    )
        self.control_frame.pack(fill='both', expand=True)
       
        self.stop_button = ctk.CTkButton(
                                    self.control_frame,
                                    command=self.click_stop,
                                    width=self.widget_width,
                                    height=self.widget_height, 
                                    text='Stop', 
                                    font=('Ubuntu Mono', 20), 
                                    text_color=styling_options.color_scheme['text_color'], 
                                    fg_color=styling_options.color_scheme['bg_color'], 
                                    bg_color=styling_options.color_scheme['face_color'],
                                    border_width=0,
                                    hover_color=styling_options.color_scheme['hover_color'],
                                    )
        self.stop_button.pack(side="bottom", pady=(5,10))
       
        self.start_button = ctk.CTkButton(
                                    self.control_frame, 
                                    command=self.click_start, 
                                    width=self.widget_width, 
                                    height=self.widget_height, 
                                    text='Start', 
                                    font=('Ubuntu Mono', 20), 
                                    text_color=styling_options.color_scheme['text_color'], 
                                    fg_color=styling_options.color_scheme['bg_color'], 
                                    bg_color=styling_options.color_scheme['face_color'],
                                    border_width=0,
                                    hover_color=styling_options.color_scheme['hover_color'],
                                    )
        self.start_button.pack(side="bottom", pady=5)
        
        self.clear_plot_button = ctk.CTkButton(
                                    self.control_frame,
                                    command=self.click_clear_plot,
                                    width=self.widget_width,
                                    height=self.widget_height, 
                                    text='Clear Plot', 
                                    font=('Ubuntu Mono', 20), 
                                    text_color=styling_options.color_scheme['text_color'], 
                                    fg_color=styling_options.color_scheme['bg_color'], 
                                    bg_color=styling_options.color_scheme['face_color'],
                                    border_width=0,
                                    hover_color=styling_options.color_scheme['hover_color'],
                                    )
        self.clear_plot_button.pack(side="bottom", pady=(5, 10))
        
        self.save_button = ctk.CTkButton(
                                    self.control_frame,
                                    command=self.click_save,
                                    width=self.widget_width,
                                    height=self.widget_height, 
                                    text='Save', 
                                    font=('Ubuntu Mono', 20), 
                                    text_color=styling_options.color_scheme['text_color'], 
                                    fg_color=styling_options.color_scheme['bg_color'], 
                                    bg_color=styling_options.color_scheme['face_color'],
                                    border_width=0,
                                    hover_color=styling_options.color_scheme['hover_color'],
                                    state='normal',
                                    )
        self.save_button.pack(side="bottom", pady=(0, 5))
        
        self.select_config = ctk.CTkComboBox(
                                        self.control_frame,
                                        width=self.widget_width+8,
                                        height=self.widget_height/1.25,
                                        font=('Ubuntu Mono', 20, 'bold'),
                                        dropdown_font=('Ubuntu Mono', 20),
                                        text_color=styling_options.color_scheme['text_color'],
                                        border_color=styling_options.color_scheme['hover_color'],
                                        fg_color=styling_options.color_scheme['bg_color'], 
                                        bg_color=styling_options.color_scheme['face_color'],
                                        dropdown_fg_color=styling_options.color_scheme['bg_color'],
                                        dropdown_text_color=styling_options.color_scheme['text_color'],
                                        border_width=0,
                                        justify='center',
                                        values=config_lst,
                                        state="readonly",
                                        command=self.load_configuration)
        self.select_config.pack(side="top", pady=(20, 0))
        self.select_config.set("Select Mode")
        self.select_config.bind("<Key>", lambda e: "break")
        
        self.set_controls(self.init_controls_state)
        
        backend.set_controls_callback(self.set_controls)
        
        self.configurations_frame = ctk.CTkCanvas(
                                    self.control_frame, 
                                    width=self.frame_width, 
                                    height=1000, 
                                    bg=styling_options.color_scheme['face_color'],
                                    highlightthickness=0,
                                    )
        self.configurations_frame.pack(side='top', fill='both', expand=True)
        
        self.configurations = Configurations(self.configurations_frame)
        self.configurations.pack(side='top', fill='both', expand=True)
        self.configurations.pack_forget()        
    
    def set_controls(self, callback_dict: dict) -> None:
        """Sets the state of the controls based on the callback dictionary.

        :param callback_dict: Containing the state of the controls.
        :type callback_dict: dict
        
        :return: None
        """
        self.stop_button.configure(state=callback_dict['stop_button_state'])
        self.start_button.configure(state=callback_dict['start_button_state'])
        self.clear_plot_button.configure(state=callback_dict['clear_button_state'])
        self.select_config.configure(state=callback_dict['select_config_state'])
        
    def load_configuration(self, choice: str) -> None:
        """Calls backend.load_config() to load the selected configuration to the spectrum analyzer. 
        
        or 
        
        Reloads the configuration list with call backend.get_yamls().

        :param choice: Name of the selected configuration.
        :type choice: str
        
        :return: None
        """
        global config_lst
        global config_dicts
        global old_choice
        hint = None
        
        if self.proceed_dialog() == False:
            return
        
        self.config_sel = choice

        if choice == 'RELOAD':
            config_lst, config_dicts = backend.get_yamls()
            
            self.select_config.configure(values=config_lst)
            self.select_config.set(old_choice)
            
            self.config_sel = old_choice
            
            if old_choice == 'RELOAD':
                self.select_config.set('Select Mode')
                return
        
        controls_state_ddnd = {
            'stop_button_state':  'disabled',
            'start_button_state': 'disabled',
            'clear_button_state': 'normal',
            'select_config_state':  'disabled',
        }
        self.set_controls(controls_state_ddnd)    
        
        try:
            self.sweep_time, self.mode = backend.load_config(self.config_sel)
            
        except ValueError:
            try:
                self.sweep_time, self.mode, hint = backend.load_config(self.config_sel)
            except ValueError:
                self.sweep_time, self.mode, hint, controls = backend.load_config(self.config_sel)
                self.set_controls(controls)
                text = "\n".join([
                            f'Time per Sweep: {round(self.sweep_time, 3)} s ',
                            '',
                            f'   Hint: {hint}',
                            '',
                            '',
                            '',
                            '',
                            '',
                            '',
                        ])
                Coms.update_coms(coms_object, text)
                self.clear_plot()
                old_choice = self.config_sel
                self.configurations.mode_label.pack(side="top", pady=(15,0), anchor='n')
                self.configurations.pack(side='top', fill='both', expand=True)
                self.configurations.write_configuration(config_dicts[self.config_sel])
                return
            
        except KeyError:
            text = "\n".join([
                f'Error: Configuration "{self.config_sel}.yml" not found.',
                '',
                '',
                '          Try to RELOAD the configuration dropdown',
                '',
                '',
                '',
                '',
                '',
            ])
            Coms.update_coms(coms_object, text)
            self.set_controls(self.init_controls_state)
            return
        except Exception as e:
            Coms.update_coms(coms_object, f'{e} \n\n\n\n\n\n\n\n')
            self.set_controls(self.init_controls_state)
            return
        
        old_choice = self.config_sel
        self.configurations.mode_label.pack(side="top", pady=(15,0), anchor='n')
        self.configurations.pack(side='top', fill='both', expand=True)
        self.configurations.write_configuration(config_dicts[self.config_sel])
        
        controls_state_dnnn = {
            'stop_button_state':  'disabled',
            'start_button_state': 'normal',
            'clear_button_state': 'normal',
            'select_config_state':  'normal',
        }
        self.set_controls(controls_state_dnnn)
        if hint:
            if len(hint) == 1:
                text = "\n".join([
                    f'Time per Sweep: {round(self.sweep_time, 3)} s ',
                    '',
                    f'   Hint: {hint[0]}',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                ])

            elif len(hint) > 1:
                text = "\n".join([
                    f'Time per Sweep: {round(self.sweep_time, 3)} s\n',
                ])
                for i in range(len(hint)):
                    text = "\n".join([text,
                    f' Hint {i+1}: {hint[i]}'])
                for line in range(6-len(hint)):
                    text = "\n".join([text, ''])

        else:
            text = (f"Time per Sweep: {round(self.sweep_time, 3)} s \n\n\n\n\n\n\n\n\n")
        Coms.update_coms(coms_object, text)
        self.clear_plot()

    def click_start(self) -> None:
        """Starts a new thread to call backend.start_measurement() with the selected configuration.
        
        Threading is used to avoid blocking the main thread thus freezing the UI.
        
        :return: None
        """
        self.event = threading.Event()
        self.thread_exception = None
        
        def worker():
            try:
                backend.start_measurement(self.config_sel, config_dicts, plot_object, self.sweep_time, self.event)
            except Exception as e:
                self.thread_exception = e
                self.set_controls(self.init_controls_state)
                self.event.set()
        t1 = threading.Thread(target=worker, daemon=True)
        t1.start()
        
        self.after(100, self.check_thread_exception)
    
    def check_thread_exception(self) -> None:
        """Checks for any exceptions in the worker thread during execution.
        
        :return: None
        """
        if self.thread_exception:
            text = "\n".join([
                f'Error: {self.thread_exception}',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                ])
            Coms.update_coms(coms_object, text)
            self.set_controls(self.init_controls_state)
            self.thread_exception = None

        else:
            self.after(100, self.check_thread_exception)
    
    def click_stop(self) -> None:
        """Set a stopping event to stop the measurement thread AFTER completing current trace.
        """
        self.event.set()
        self.no_controls_state = {
            'stop_button_state': 'disabled',
            'start_button_state': 'disabled',
            'clear_button_state': 'disabled',
            'select_config_state': 'disabled',
        }
        self.set_controls(self.no_controls_state)
        
    def proceed_dialog(self) -> bool:
        
        if plot_object.lines != []:
            proc_obj = ProceedDialog()
            proceed = proc_obj.show()
            
            if proceed==False:
                self.select_config.set(old_choice)
                return proceed
        
    def click_clear_plot(self) -> None:
        
        proceed = self.proceed_dialog()
        if proceed == False:
            return    
        self.clear_plot()

    def clear_plot(self) -> None:
        """Clears the plot and resets the progress bar.
        """        
        plot_object.clear_plot()
        plot_object.lines = []
        progress_object.update_progress(0)

    def click_save(self) -> None:
        """Not implemented yet.
        """
        if plot_object.lines != []:
            save_obj = SaveDialog()
            save = save_obj.show()
            print(save)
        
    def resize(self, height: int) -> None:
        """Resizes the control frame to fit new window height (width stays the same).

        :param height: height of the UI window in px.
        :type height: int
        
        :return: None
        """
        frame_height = height - 40
        self.control_frame.configure(height=frame_height)
        self.control_frame.pack_propagate(False)

class Configurations(ctk.CTkTabview):
    """Containing the configurations info.
    """
    def __init__(self, parent: ctk.CTkFrame) -> None:
        """Defines and initializes the configurations elements for the SPIKES application.

        :param parent: Parent frame for the configurations.
        :type parent: ctk.CTkFrame
        
        :return: None
        """
        super().__init__(parent)
        
        self.frame_width   = 340
        self.widget_width  = self.frame_width - 40
        self.widget_height = 70
                        
        self.hires = self.add(" HIGH-RES ")
        self.fast  = self.add("   FAST   ")
        
        for tab_name in self._name_list:
            self._segmented_button._buttons_dict[tab_name].configure(font=('Ubuntu Mono', 20))

        self.configure(
                border_width=0, 
                width=self.widget_width,
                height=self.widget_height*0.5, 
                fg_color=styling_options.color_scheme['face_color'], 
                bg_color=styling_options.color_scheme['face_color'],
                segmented_button_fg_color=styling_options.color_scheme['face_color'],
                segmented_button_selected_color=styling_options.color_scheme['progress_color'],
                segmented_button_unselected_color=styling_options.color_scheme['bg_color'],
                segmented_button_unselected_hover_color=styling_options.color_scheme['hover_color'],
                segmented_button_selected_hover_color=styling_options.color_scheme['hover_color'],
                text_color_disabled=styling_options.color_scheme['text_color'],
                anchor='n',
                state='disabled',
                corner_radius=0,
                )
        
        self.mode_label = ctk.CTkLabel(
                                parent,
                                text="Mode of Operation         ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )
        
        self.start_freq_label_hires = ctk.CTkLabel(
                                self.hires,
                                text="Start Frequency           ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20),
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.start_freq_label_hires.pack(side="top", pady=(10,0), anchor='n')
        
        self.start_freq_hires = ctk.CTkEntry(
                                self.hires,
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.start_freq_hires.pack(side="top", pady=(0,5), anchor='n')
        
        self.stop_freq_label_hires = ctk.CTkLabel(
                                self.hires,
                                text="Stop Frequency            ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.stop_freq_label_hires.pack(side="top", pady=(5,0), anchor='n')
        
        self.stop_freq_hires = ctk.CTkEntry(
                                self.hires, 
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.stop_freq_hires.pack(side="top", pady=(0,5), anchor='n')
        
        self.res_bw_label_hires = ctk.CTkLabel(
                                self.hires,
                                text="Resolution BW             ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.res_bw_label_hires.pack(side="top", pady=(15,0), anchor='n')
        
        self.res_bw_hires = ctk.CTkEntry(
                                self.hires, 
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.res_bw_hires.pack(side="top", pady=(0,5), anchor='n')

        self.vid_bw_label_hires = ctk.CTkLabel(
                                self.hires,
                                text="Video Bandwidth           ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.vid_bw_label_hires.pack(side="top", pady=(5,0), anchor='n')
        
        self.vid_bw_hires = ctk.CTkEntry(
                                self.hires, 
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.vid_bw_hires.pack(side="top", pady=(0,5), anchor='n')
        
        self.atten_label_hires = ctk.CTkLabel(
                                self.hires,
                                text="Attenuation               ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.atten_label_hires.pack(side="top", pady=(15,0), anchor='n')
        
        self.atten_hires = ctk.CTkEntry(
                                self.hires, 
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.atten_hires.pack(side="top", pady=(0,5), anchor='n')
        
        self.traces_label = ctk.CTkLabel(
                                self.hires,
                                text="Number of Traces          ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='left',
                                )  
        self.traces_label.pack(side="top", pady=(15,0), anchor='n')

        self.traces = ctk.CTkEntry(
                                self.hires, 
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.traces.pack(side="top", pady=(0,5), anchor='n')
        
        
        self.start_freq_label_fast = ctk.CTkLabel(
                                self.fast,
                                text="Start Frequency           ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.start_freq_label_fast.pack(side="top", pady=(10,0), anchor='n')
        
        self.start_freq_fast = ctk.CTkEntry(
                                self.fast,
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.start_freq_fast.pack(side="top", pady=(0,5), anchor='n')
        
        self.stop_freq_label_fast = ctk.CTkLabel(
                                self.fast,
                                text="Stop Frequency            ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.stop_freq_label_fast.pack(side="top", pady=(5,0), anchor='n')
        
        self.stop_freq_fast = ctk.CTkEntry(
                                self.fast, 
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.stop_freq_fast.pack(side="top", pady=(0,5), anchor='n')
        
        self.res_bw_label_fast = ctk.CTkLabel(
                                self.fast,
                                text="Resolution BW             ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.res_bw_label_fast.pack(side="top", pady=(15,0), anchor='n')
        
        self.res_bw_fast = ctk.CTkEntry(
                                self.fast, 
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.res_bw_fast.pack(side="top", pady=(0,5), anchor='n')

        self.vid_bw_label_fast = ctk.CTkLabel(
                                self.fast,
                                text="Video Bandwidth           ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.vid_bw_label_fast.pack(side="top", pady=(5,0), anchor='n')
        
        self.vid_bw_fast = ctk.CTkEntry(
                                self.fast, 
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.vid_bw_fast.pack(side="top", pady=(0,5), anchor='n')
        
        self.atten_label_fast = ctk.CTkLabel(
                                self.fast,
                                text="Attenuation               ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.atten_label_fast.pack(side="top", pady=(15,0), anchor='n')
        
        self.atten_fast = ctk.CTkEntry(
                                self.fast, 
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.atten_fast.pack(side="top", pady=(0,5), anchor='n')
        
        self.refresh_label = ctk.CTkLabel(
                                self.fast,
                                text="Display Refresh           ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.refresh_label.pack(side="top", pady=(15,0), anchor='n')
        
        self.refresh = ctk.CTkEntry(
                                self.fast, 
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.refresh.pack(side="top", pady=(0,5), anchor='n')

        self.integration_label = ctk.CTkLabel(
                                self.fast,
                                text="Integration Time per Trace",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.integration_label.pack(side="top", pady=(5,0), anchor='n')
        
        self.integration = ctk.CTkEntry(
                                self.fast, 
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.integration.pack(side="top", pady=(0,5), anchor='n')

        self.total_traces_label = ctk.CTkLabel(
                                self.fast,
                                text="Number of Traces          ",
                                width=self.widget_width,
                                height=self.widget_height*0.5,
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['face_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                justify='center',
                                )  
        self.total_traces_label.pack(side="top", pady=(5,0), anchor='n')
        
        self.total_traces = ctk.CTkEntry(
                                self.fast, 
                                width=self.widget_width, 
                                height=self.widget_height*0.5, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                state='readonly',
                                )
        self.total_traces.pack(side="top", pady=(0,5), anchor='n')
            
    def write_configuration(self, config_dict: dict) -> None:
        """Updates the configuration to the display elements.
                
        :param config_dict: Configuration parameters.
        :type config_dict: dict
        
        :return: None
        """               
        if config_dict['mode'] == 'HIGH-RES':
            self.set(" HIGH-RES ")
            
            if 'start_freq' in config_dict:
                self.start_freq_hires.configure(textvariable=ctk.StringVar(value=backend.value_parser(config_dict['start_freq'])))
            
            if 'stop_freq' in config_dict:
                self.stop_freq_hires.configure(textvariable=ctk.StringVar(value=backend.value_parser(config_dict['stop_freq'])))
            
            if 'res_bw' in config_dict:
                self.res_bw_hires.configure(textvariable=ctk.StringVar(value=backend.value_parser(config_dict['res_bw'])))
                
            if 'vid_bw' in config_dict:
                self.vid_bw_hires.configure(textvariable=ctk.StringVar(value=backend.value_parser(config_dict['vid_bw'])))
            
            if 'attenuation' in config_dict:
                self.atten_hires.configure(textvariable=ctk.StringVar(value=f'{config_dict['attenuation']} dB'))
            
            if 'num_aver' in config_dict:
                self.traces.configure(textvariable=ctk.StringVar(value=config_dict['num_aver']))
                 
        elif config_dict['mode'] == 'FAST':
            self.set("   FAST   ")
            
            if 'start_freq' in config_dict:
                self.start_freq_fast.configure(textvariable=ctk.StringVar(value=backend.value_parser(config_dict['start_freq'])))
            
            if 'stop_freq' in config_dict:
                self.stop_freq_fast.configure(textvariable=ctk.StringVar(value=backend.value_parser(config_dict['stop_freq'])))
            
            if 'res_bw' in config_dict:
                self.res_bw_fast.configure(textvariable=ctk.StringVar(value=backend.value_parser(config_dict['res_bw'])))
                
            if 'vid_bw' in config_dict:
                self.vid_bw_fast.configure(textvariable=ctk.StringVar(value=backend.value_parser(config_dict['vid_bw'])))
            
            if 'attenuation' in config_dict:
                self.atten_fast.configure(textvariable=ctk.StringVar(value=f'{config_dict['attenuation']} dB'))
            
            if 'display_refresh' in config_dict:
                self.refresh.configure(textvariable=ctk.StringVar(value=f'{config_dict['display_refresh']} sec'))
            
            if 'integration_time' in config_dict:
                self.integration.configure(textvariable=ctk.StringVar(value=backend.value_parser(config_dict['integration_time'], 'sec')))
            
            if 'total_traces' in config_dict:
                if config_dict['total_traces'] == 'cont':
                    self.total_traces.configure(textvariable=ctk.StringVar(value='Continuous'))
                else:
                    self.total_traces.configure(textvariable=ctk.StringVar(value=f'{config_dict['total_traces']}'))
            
class Plot(ctk.CTkFrame):
    """Containing the Matplotlib figure.
    """
    def __init__(self, parent: ctk.CTkFrame) -> None:
        """Initializes frame where the Matplotlib figure will be embedded.
        
        :parent: Parent frame for the plot.
        :type parent: ctk.CTkFrame
        
        :return: None
        """
        super().__init__(parent)

        global plot_object
        
        self.trace_num = 0

        self.plot_container = ctk.CTkFrame(self, width=800, height=400, fg_color=styling_options.color_scheme['face_color'])
        self.plot_container.pack(padx=0, pady=0, fill='both', expand=True)

        plot_object = plotting.Graph(self.plot_container)
        
    def resize(self, width: int, height: int) -> None:
        """Resizes the Plot frame to fit new window height and width.

        :param height: height of the UI window in px.
        :type height: int

        :param width: width of the UI window in px.
        :type width: int

        :return: None
        """
        self.plot_container.configure(width=width-400, height=height-300)
        self.plot_container.pack_propagate(False)

class Progress(ctk.CTkFrame):
    """Contains the progress bar.
    """
    def __init__(self, parent: ctk.CTkFrame) -> None:
        """Initializes the progress bar and the frame holding it.

        :param parent: Parent frame for the progress bar.
        :type parent: ctk.CTkFrame
        
        :return: None
        """
        super().__init__(parent)
        
        global progress_object
        
        self.progress_container = ctk.CTkFrame(
                                        self, 
                                        width=800, 
                                        height=40, 
                                        fg_color=styling_options.color_scheme['face_color'], 
                                        bg_color=styling_options.color_scheme['bg_color']
                                        )
        self.progress_container.pack(fill='both', expand=True)
        
        self.progress_bar = ctk.CTkProgressBar(
                                        self.progress_container, 
                                        width=300, 
                                        height=20,
                                        corner_radius=0,
                                        progress_color=styling_options.color_scheme['progress_color'],
                                        )
        self.progress_bar.pack(pady=10, padx=70)
        
        self.progress_bar.set(0)
        
        progress_object = self
        
        backend.set_progress_callback(self.update_progress)
        
    def update_progress(self, progress: float) -> None:
        """Updates the progress bar with the given progress value.

        :param progress: Progress value between 0 and 1.
        :type progress: float
        
        :return: None
        """
        self.progress_bar.set(progress)
        
    def resize(self, width: int) -> None:
        """Resizes the progress bar to fit new window width.

        :param width: width of the UI window in px.
        :type width: int
        
        :return: None
        """
        frame_width = width - 400
        self.progress_container.configure(width=frame_width, height=40)
        self.progress_bar.configure(width=frame_width-70, height=20)
        self.progress_container.pack_propagate(False)
        
class Coms(ctk.CTkFrame):
    """Containing the coms text box.
    """
    def __init__(self, parent: ctk.CTkFrame) -> None:
        """Initializes the coms text box and the frame holding it.

        :param parent: Parent frame for the coms text box.
        :type parent: ctk.CTkFrame
        
        :return: None
        """
        super().__init__(parent)
        
        global coms_object
        
        self.coms_container = ctk.CTkFrame(
                                    self,
                                    width=800, 
                                    height=400, 
                                    fg_color=styling_options.color_scheme['face_color']
                                    )
        self.coms_container.pack(fill='both', expand=True)
        
        self.coms_text = ctk.CTkTextbox(
                                    self.coms_container, 
                                    state ='disabled',
                                    fg_color=styling_options.color_scheme['face_color'],
                                    text_color=styling_options.color_scheme['text_color'],
                                    font=('Ubuntu Mono', 20, 'bold'),
                                    corner_radius=0,
                                    )
        self.coms_text.pack(pady=0, padx=0, fill='both', expand=True)
        
        coms_object = self
        
        self.i = 0
    
    def update_coms(self, text: str) -> None:
        """Updates the coms text box with the given text.

        :param text: Text to be displayed.
        :type text: str
        
        :return: None
        """
        self.i += 1
        self.coms_text.configure(state='normal')
        self.coms_text.insert("0.0", str(self.i) + ': ' + text)
        self.coms_text.configure(state='disabled')
        
    def resize(self, width: int) -> None:
        """Resizes the coms text box to fit new window width (height stays the same).

        :param width: width of the UI window in px.
        :type width: int
        
        :return: None
        """
        frame_width = width - 400
        self.coms_container.configure(width=frame_width, height=200)
        self.coms_text.configure(width=frame_width, height=200)
        self.coms_container.pack_propagate(False)

class ProceedDialog(ctk.CTkToplevel):
    """Creates a popup to ask user if they want to proceed.
    """
    def __init__(self, parent=None, title="", text="Proceeding will delete unsaved data!") -> None:
        super().__init__(parent)
        self.title(title)
        self.geometry("500x150")
        self.resizable(False, False)
        self.configure(fg_color=styling_options.color_scheme['face_color'])
        self.wm_attributes("-type", "dialog")
    
        self.attributes("-topmost", True)
        self.focus_force()
        self.transient(parent)

        self.result = False

        self.label = ctk.CTkLabel(
                        self, 
                        text=text, 
                        font=('Ubuntu Mono', 18),
                        text_color=styling_options.color_scheme['text_color'],
                    )
        self.label.pack(pady=(20,0))

        self.button_frame = ctk.CTkFrame(
                                self,
                                fg_color="transparent",
                            )
        self.button_frame.pack(pady=10, fill='both', expand=True)

        self.ok_button = ctk.CTkButton(
                            self.button_frame, 
                            text="OK", 
                            command=self.on_ok,
                            width=210,
                            height=50, 
                            font=('Ubuntu Mono', 20), 
                            text_color=styling_options.color_scheme['text_color'], 
                            fg_color=styling_options.color_scheme['bg_color'], 
                            bg_color=styling_options.color_scheme['face_color'],
                            border_width=0,
                            hover_color=styling_options.color_scheme['hover_color'],
                        )
        self.ok_button.pack(side="left", padx=20, pady=10)

        self.cancel_button = ctk.CTkButton(
                            self.button_frame, 
                            text="CANCEL", 
                            command=self.on_cancel,
                            width=210,
                            height=50, 
                            font=('Ubuntu Mono', 20), 
                            text_color=styling_options.color_scheme['text_color'], 
                            fg_color=styling_options.color_scheme['bg_color'], 
                            bg_color=styling_options.color_scheme['face_color'],
                            border_width=0,
                            hover_color=styling_options.color_scheme['hover_color'],
                        )
        self.cancel_button.pack(side="right", padx=20, pady=10)

    def on_ok(self):
        self.result = True
        self.destroy()

    def on_cancel(self):
        self.result = False
        self.destroy()

    def show(self):
        self.update_idletasks() 
        self.grab_set()
        self.wait_window()
        return self.result

class SaveDialog(ctk.CTkToplevel):
    """Creates a popup to ask user if they want to save data.
    """
    def __init__(self, parent=None, title="", text="Save data?") -> None:
        super().__init__(parent)
        self.title(title)
        self.geometry("500x250")
        self.resizable(False, False)
        self.configure(fg_color=styling_options.color_scheme['face_color'])
        self.wm_attributes("-type", "dialog")
        self.attributes("-topmost", True)
        self.focus_force()
        self.transient(parent)
        
        self.result = False
        
        self.label = ctk.CTkLabel(
                        self, 
                        text=text, 
                        font=('Ubuntu Mono', 18),
                        text_color=styling_options.color_scheme['text_color'],
                    )
        self.label.pack(pady=(20,0))
        
        self.add_to_filename = ctk.CTkEntry(
                                self,
                                height=35, 
                                font=('Ubuntu Mono', 20), 
                                text_color=styling_options.color_scheme['text_color'], 
                                fg_color=styling_options.color_scheme['bg_color'], 
                                bg_color=styling_options.color_scheme['face_color'],
                                border_width=0,
                                justify='center',
                                corner_radius=0,
                                placeholder_text='Addition to default name',
                                state='normal',
                                )
        self.add_to_filename.pack(pady=(10,0), fill='x', expand=True)

        self.button_frame = ctk.CTkFrame(
                                self,
                                fg_color="transparent",
                            )
        self.button_frame.pack(pady=10, fill='both', expand=True)

        self.save_button = ctk.CTkButton(
                            self.button_frame, 
                            text="SAVE", 
                            command=self.on_save,
                            width=210,
                            height=50, 
                            font=('Ubuntu Mono', 20), 
                            text_color=styling_options.color_scheme['text_color'], 
                            fg_color=styling_options.color_scheme['bg_color'], 
                            bg_color=styling_options.color_scheme['face_color'],
                            border_width=0,
                            hover_color=styling_options.color_scheme['hover_color'],
                        )
        self.save_button.pack(side="left", padx=20, pady=10)

        self.cancel_button = ctk.CTkButton(
                            self.button_frame, 
                            text="CANCEL", 
                            command=self.on_cancel,
                            width=210,
                            height=50, 
                            font=('Ubuntu Mono', 20), 
                            text_color=styling_options.color_scheme['text_color'], 
                            fg_color=styling_options.color_scheme['bg_color'], 
                            bg_color=styling_options.color_scheme['face_color'],
                            border_width=0,
                            hover_color=styling_options.color_scheme['hover_color'],
                        )
        self.cancel_button.pack(side="right", padx=20, pady=10)
        
    def on_save(self):
        self.result = self.add_to_filename.get()
        self.destroy()
    
    def on_cancel(self):
        self.result = False
        self.destroy()

    def show(self):
        self.update_idletasks() 
        self.grab_set()
        self.wait_window()
        return self.result

