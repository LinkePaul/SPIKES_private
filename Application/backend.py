"""Utility functions for the SPIKES application.
"""
import time
import os
import yaml
import threading
import numpy as np
from typing import Callable, TYPE_CHECKING

import spectrum_coms

if TYPE_CHECKING:
    from plotting import Graph

global_trace = None
progress_callback = None
controls_callback = None
l = 0

def set_progress_callback(callback: Callable[[float], None]) -> None:
    """Sets the callback function for progress bar updates.

    :param callback: The callback function to be called with the progress value.
    :type callback: Callable[[float], None]
    
    :return: None
    """
    global progress_callback
    progress_callback = callback

def set_controls_callback(callback: Callable[[dict], None]) -> None:
    """Sets the callback function for activating/deactivating indiviadual controls.

    :param callback: The callback function to be called with a dictionary.
    :type callback: Callable[[dict], None]
    
    :return: None
    """
    global controls_callback
    controls_callback = callback

def trace_complete(trace_data: str) -> None:
    """Sets the global trace data.

    :param trace_data: Raw trace data to be set.
    :type trace_data: str
    
    :return: None
    """
    global global_trace
    global_trace = trace_data

def get_yamls() -> tuple[list, dict]:
    """Fetches the YAML configuration files from the specified directory.

    :return: A tuple containing a list of configuration names and a dictionary of configuration data.
    :rtype: tuple[list, dict]
    """
    path = r"/home/sonata/local_git/SPIKES_private/Configuration"
    config_dict = {}

    for file_name in os.listdir(path):

        if file_name.endswith('.yaml') or file_name.endswith('.yml'):
            file_path = os.path.join(path, file_name)

            try:
                with open(file_path, 'r') as file:
                    base_name = os.path.splitext(file_name)[0]  # Remove .yaml extension
                    config_dict[base_name] = yaml.safe_load(file)
            except PermissionError:
                print(f"Permission denied: {file_path}")
            except FileNotFoundError:
                print(f"File not found: {file_path}")
            except yaml.YAMLError as e:
                print(f"Error parsing YAML in {file_path}: {e}")

        file_name = file_name.split('.')[0]
    
    config_list = list(config_dict.keys())
    config_list.insert(0, "RELOAD")
    
    return config_list, config_dict

def load_config(config_selection: str) -> tuple[float, str]:
    """Loads the configuration for the specified config_selection onto the spectrum analyzer.

    :param config_selection: Name of the configuration to be loaded.
    :type config_selection: str
    
    :return: Sweep time and mode of the loaded configuration.
    :rtype: tuple[float, str]
    
    :raises Exception: If an error occurs while connecting to the spectrum analyzer.
    """
    config_dict = get_yamls()[1][config_selection]
    
    try:
        AgilentSA = spectrum_coms.SpectrumControl()
    
    except Exception as e:
        raise e
    
    sweep_time_tuple = AgilentSA.send_config(**config_dict)
    
    mode = config_dict['mode']
        
    if type(sweep_time_tuple) == tuple and len(sweep_time_tuple) == 2:
        sweep_time = sweep_time_tuple[0]
        error_message = sweep_time_tuple[1]
        return sweep_time, mode, error_message
    
    elif type(sweep_time_tuple) == tuple and len(sweep_time_tuple) == 3:
        sweep_time = sweep_time_tuple[0]
        error_message = sweep_time_tuple[1]
        controls_state_ddnn = {
            'stop_button_state':  'disabled',
            'start_button_state': 'disabled',
            'clear_button_state': 'normal',
            'select_config_state':  'normal',
        }
        return sweep_time, mode, error_message, controls_state_ddnn
        
    return sweep_time_tuple, mode

def parse_trace(trace_data: str) -> tuple[np.ndarray, dict]:
    '''Parses the trace data from the Agilent N9010A Spectrum Analyzer (or similar) into a 2D numpy array and a dictionary of configuration data in the form of {key: [value, type, description]}.
    
    :param trace_data: Raw trace data to be parsed.
    :type trace_data: str
    
    :return: A tuple containing the parsed trace and configuration data.
    :rtype: tuple[np.ndarray, dict]
    '''
    trace_raw = trace_data.split('DATA')[1].strip().split('\r\n')             
    parsed = [list(map(float, point.split(','))) for point in trace_raw]
    trace = np.array(parsed)
    
    desc_raw = trace_data.split('DATA')[0].strip().split('\r\n')              
    desc = {}
    
    for item in desc_raw:
        
        if 'Number of Points,' in item:
            val = int(item.split(',')[1])
            desc['num_points'] = [val, 'int', 'Number of Points']
        
        if 'Start Frequency,' in item:
            val = float(item.split(',')[1])
            desc['start_freq'] = [val, 'Hz', 'Start Frequency']
        
        if 'Stop Frequency,' in item:
            val = float(item.split(',')[1])
            desc['stop_freq'] = [val, 'Hz', 'Stop Frequency']
        
        if 'RBW,' in item:
            val = float(item.split(',')[1])
            desc['res_bw'] = [val, 'Hz', 'Resolution Bandwidth']
        
        if 'VBW,' in item:
            val = float(item.split(',')[1])
            desc['video_bw'] = [val, 'Hz', 'Video Bandwidth']
            
        if 'Sweep Time' in item:
            val = float(item.split(',')[1])
            desc['sweep_time'] = [val, 's', 'Sweep Time']
        
        if 'Attenuation,' in item:
            val = float(item.split(',')[1])
            desc['atten'] = [val, 'dB', 'Attenuation']
        
        if 'X Axis Units,' in item:
            val = item.split(',')[1]
            desc['x_units'] = [val, 'str', 'X Axis Units']
        
        if 'Y Axis Units,' in item:
            val = item.split(',')[1]
            desc['y_units'] = [val, 'str', 'Y Axis Units']
        
        if 'Average Count,' in item:
            val = int(item.split(',')[1])
            desc['avg_count'] = [val, 'int', 'Average Count']
        
        if 'Trace Type,' in item:
            val = item.split(',')[1]
            desc['trace_type'] = [val, 'str', 'Trace Type']
            
        if 'Sweep Type,' in item:
            val = item.split(',')[1]
            desc['sweep_type'] = [val, 'str', 'Sweep Type']
        
        if 'Detector,' in item:
            val = item.split(',')[1]
            desc['detector'] = [val, 'str', 'Detector Mode']
        
        val = None
        
    span = desc['stop_freq'][0] - desc['start_freq'][0]
    desc['span'] = [span, 'Hz', 'Frequency Span']
    
    return trace, desc

def start_measurement(config_selection: str, config_dicts: dict, plot_object: 'Graph', sweep_time: float, event: threading.Event) -> None:
    """Initializes the measurement process for the specified configuration.

    :param config_selection: Name of the configuration to be used.
    :type config_selection: str
    
    :param config_dicts: Parent dictionary containing the Dictionaries of configuration data.
    :type config_dicts: dict
    
    :param plot_object: Graph object for plotting the data.
    :type plot_object: Graph
    
    :param sweep_time: Returned sweep time for the measurement.
    :type sweep_time: float
    
    :param event: Stop event for the measurement (stops after current trace finishes).
    :type event: threading.Event
    
    :return: None
    
    :raises KeyError: if the configuration dictionary is missing required keys.
    :raises ValueError: if the configuration dictionary is missing a valid mode definition.
    :raises Exception: if the configuration dictionary is missing required keys.
    :raises Exception: if an error occurs while connecting to the spectrum analyzer.
    """
        
    global l
    global progress_callback
    
    controls_state_nddd = {
        'stop_button_state':  'normal',
        'start_button_state': 'disabled',
        'clear_button_state': 'disabled',
        'select_config_state':  'disabled',
    }
    controls_state_dnnn = {
        'stop_button_state': 'disabled',
        'start_button_state': 'normal',
        'clear_button_state': 'normal',
        'select_config_state': 'normal',
        }   
    
    controls_callback(controls_state_nddd)
    
    config_dict = config_dicts[config_selection]
    
    try:
        AgilentSA = spectrum_coms.SpectrumControl()
    
    except Exception as e:
        controls_callback(controls_state_dnnn)
        raise e
    
    AgilentSA.send_config(**config_dict)
        
    if 'mode' in config_dict and config_dict['mode'] == 'FAST':
        try:
            reset = int(float(config_dict['reset_period']))
            total = int(float(config_dict['total_time']))
            refresh = int(float(config_dict['refresh_period']))
            
        except KeyError:
            raise KeyError(f'refresh_period, reset_period and total_time must be defined in the configuration dictionary for time-based mode.')
        except Exception as e:
            raise Exception(f'refresh_period, reset_period and total_time must be defined in the configuration dictionary for time-based mode.\n\n          {e}')
        
        time1 = time.time()
        int_mult = int(total/reset)
        
        for i in range(int_mult):      
            
            AgilentSA.write('INIT:IMM')
            t_start = time.time()
            while time.time()-time1 < (i+1)*reset:
                
                trace_thread = AgilentSA.trace_threaded_cont(trace_complete, **config_dict)
                trace_thread.start()    
                
                while trace_thread.is_alive():
                    t_elaps = time.time() - t_start                  
                    time.sleep(1/60)
                    progress_callback(t_elaps/reset)
                
                trace_thread.join()
                
                parsed_trace = parse_trace(global_trace)
                plot_object.update_plot(parsed_trace[0], clear=True, line_num=l)

                plot_object.update_plot(None, clear=True, line_num=l)
                
                if event.is_set():
                    if controls_callback:
                        controls_callback(controls_state_dnnn)
                    l += 1
                    return 
                
            while t_elaps/reset < 1:
                t_elaps = time.time() - t_start                 
                time.sleep(1/60)
                progress_callback(t_elaps/reset)
            l += 1
    
    elif 'mode' in config_dict and config_dict['mode'] == 'HIGH-RES':
        time1 = time.time()
        t_refresh = sweep_time + 2 + 0.01*sweep_time
        t_total = t_refresh * config_dict['num_aver']
        int_mult = int(t_total/t_refresh)
                    
        AgilentSA.write('INIT:IMM')
        
        i = 0
        if 'trace_type' in config_dict and config_dict['trace_type'] == 'MAXH':
            while time.time()-time1 < t_total:
                
                trace_thread = AgilentSA.trace_threaded_cont(trace_complete, t_refresh=t_refresh, **config_dict)
                trace_thread.start()    
                t_start = time.time()
                while trace_thread.is_alive():
                    if progress_callback:
                        t_elaps = time.time() - t_start            
                        time.sleep(1/60)
                        progress_callback(t_elaps/t_refresh)
            
                trace_thread.join()
                
                parsed_trace = parse_trace(global_trace)
                plot_object.update_plot(parsed_trace[0], clear=True, line_num=l)

                plot_object.update_plot(None, clear=True, line_num=l)
                
                i += 1
                
                if event.is_set():
                    if controls_callback:
                        controls_callback(controls_state_dnnn)
                    l += 1
                    return    
                
                while t_elaps/t_refresh < 1:
                    t_elaps = time.time() - t_start                
                    time.sleep(1/60)
                    progress_callback(t_elaps/t_refresh)
            l += 1
        else:
            for i in range(config_dict['num_aver']):
                
                trace_thread = AgilentSA.trace_threaded_cont(trace_complete, t_refresh=t_refresh, **config_dict)
                trace_thread.start()    
                t_start = time.time()
                while trace_thread.is_alive():
                    if progress_callback:
                        t_elaps = time.time() - t_start            
                        time.sleep(1/60)
                        progress_callback(t_elaps/t_refresh)
            
                trace_thread.join()
                
                parsed_trace = parse_trace(global_trace)
                plot_object.update_plot(parsed_trace[0], clear=True, line_num=l)

                plot_object.update_plot(None, clear=True, line_num=l)
                
                if event.is_set():
                    if controls_callback:
                        controls_callback(controls_state_dnnn)
                    l += 1
                    return    
                
                while t_elaps/t_refresh < 1:
                    t_elaps = time.time() - t_start                
                    time.sleep(1/60)
                    progress_callback(t_elaps/t_refresh)
                
                l += 1
                
    else:
        raise ValueError(f'No valid Mode definition in configuration dictionary.\n\n          {config_dict['mode']}')
        
    event.set()
    controls_callback(controls_state_dnnn)
    
def value_parser(num: str, unit: str='Hz') -> str:
    """Parses a numerical value and its unit into a human-readable format for display in the configuration section.

    :param num: Numerical value to be parsed.
    :type num: str
    
    :param unit: Unit of numerical Value to be parsed, defaults to 'Hz'
    :type unit: str, optional
    
    :return: Readable numerical value with unit and unit prefix.
    :rtype: str
    
    :raises ValueError: If input value is not a valid number.
    """
    try:
        num = int(float(num))
        num_string = str(int(float(num)))
    
    except:
        printable_num = f'{num} {unit} (invalid)'
        return printable_num
    
    
    for zeros in range(len(num_string)):
        if num_string[-(zeros+1)] == '0':
            continue
        else:
            break
    
    if num < 1e3:
        num = num
        prefix = ''
    
    elif num >= 1e3 and num < 1e6:
        num = num/1e3
        prefix = 'k'
        if zeros >= 3:
            num = round(num)
        else:
            num = round(num, max(0, 3 - zeros))
            
    elif num >= 1e6 and num < 1e9:
        num = num / 1e6
        prefix = 'M'
        if zeros >= 6:
            num = round(num)
        else:
            num = round(num, max(0, 6 - zeros))
    
    else:
        num = num / 1e9
        prefix = 'G'
        if zeros >= 9:
            num = round(num)
        else:
            num = round(num, max(0, 9 - zeros))
    
    printable_num = f'{num} {prefix}{unit}'

    return printable_num
