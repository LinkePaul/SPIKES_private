"""Utility functions for the SPIKES application.
"""
from math import inf
import time
import os
import yaml
import threading
import numpy as np
from datetime import datetime
from typing import Callable, TYPE_CHECKING

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.colors as mcolors

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
            int_time = int(float(config_dict['integration_time']))
            try:
                total = int(float(config_dict['total_traces']))
            except:
                total = config_dict['total_traces']
                if total == 'cont':
                    total = int(1e15)
                else:
                    raise Exception("total_traces must be int or 'cont'.\n")
    
            refresh = int(float(config_dict['display_refresh']))
            
        except KeyError:
            raise KeyError(f'display_refresh, integration_time and total_traces must be defined in the configuration dictionary for time-based (FAST) mode.')
        except Exception as e:
            raise e
        
        time1 = time.time()
        
        for i in range(total):      
            
            AgilentSA.write('INIT:IMM')
            t_start = time.time()
            while time.time()-time1 < (i+1)*int_time:
                
                trace_thread = AgilentSA.trace_threaded_cont(trace_complete, **config_dict)
                trace_thread.start()    
                
                while trace_thread.is_alive():
                    t_elaps = time.time() - t_start                  
                    time.sleep(1/60)
                    progress_callback(t_elaps/int_time)
                
                trace_thread.join()
                
                parsed_trace = parse_trace(global_trace)
                plot_object.update_plot(parsed_trace[0], clear=True, line_num=l)

                plot_object.update_plot(None, clear=True, line_num=l)
                
                if event.is_set():
                    if controls_callback:
                        controls_callback(controls_state_dnnn)
                    l += 1
                    return 
                
            while t_elaps/int_time < 1:
                t_elaps = time.time() - t_start                 
                time.sleep(1/60)
                progress_callback(t_elaps/int_time)
            l += 1
    
    elif 'mode' in config_dict and config_dict['mode'] == 'HIGH-RES':
        time1 = time.time()
        t_refresh = sweep_time + 2 + 0.01*sweep_time
        t_total = t_refresh * config_dict['num_aver']
                    
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

def make_dir_daily(path: str = r"/home/sonata/local_git/SPIKES_private/Measurements") -> str:
    """Creates a daily directory for saving all measurement data of that date if it does not already exist.

    :return: daily directory in which to save the measurements.
    :rtype: str
    
    :return: date and time object.
    :rtype: datetime
    """
    date_time = datetime.now()

    date = date_time.strftime("%Y-%m-%d")
    
    daily_dir = path + "/" + date
    
    if not os.path.exists(daily_dir):
        os.makedirs(daily_dir)

    return daily_dir, date_time
    
def make_dir_measurement(name: str) -> None:
    """Creates a timestamped directory for saving the current measurement.
    
    :return: None
    """
    daily_dir, date_time = make_dir_daily()

    time = date_time.strftime("%Hh%M")
    
    measurement_dir = daily_dir + "/" + time + "-" + name
    
    if not os.path.exists(measurement_dir):
        os.makedirs(measurement_dir)
        return measurement_dir
    
    else:
        i = 0
        while True:
            i+=1
            if not os.path.exists(measurement_dir + f"_{i}"):
                os.makedirs(measurement_dir + f"_{i}")
                return measurement_dir + f"_{i}"
                
def save_config(path: str, config_dict: dict, config_name: str) -> None:
    """Saves the configuration dictionary to a YAML file.

    :param config_dict: Configuration dictionary to be saved.
    :type config_dict: dict
    
    :return: None
    """
    path = os.path.join(path, "data")
    
    if not os.path.exists(path):
        os.makedirs(path)
    
    file_path = os.path.join(path, f'{config_name}.yaml')
    
    with open(file_path, 'w') as file:
        yaml.dump(config_dict, file, default_flow_style=False)
        
def save_traces(path: str, trace_data: list) -> None:
    """Saves the trace data to a CSV file.

    :path: Path to the directory in which to save the trace data.
    :type path: str

    :param trace_data: List of trace data (Matplotlib.Line2D) to be saved.
    :type 
    
    :return: None
    """
    path = os.path.join(path, "data")
    
    if not os.path.exists(path):
        os.makedirs(path)
    
    for i, trace in enumerate(trace_data):
        file_path = os.path.join(path, f'trace_{i+1}.csv')
        np.savetxt(file_path, np.array([trace.get_xdata()*1e6, trace.get_ydata()]).T, delimiter=',')

def invert_color(color):
    if isinstance(color, str):
        color = mcolors.hex2color(color)
    inverted_color = tuple(1.0 - c for c in color)
    return inverted_color

def save_png(path, lines, legend=False, sweep_time=None):
    
    x_label = 'MHz'
    y_label = 'dBm'
    
    if not legend: 
        path = os.path.join(path, "imgs_nolegend")
        if not os.path.exists(path):
            os.makedirs(path)
        
        fig = Figure(figsize=(10, 5), dpi=300, constrained_layout=True)
        ax = fig.add_subplot()
        
        ax.grid(True, which='both', linestyle='--', linewidth=0.3, alpha=0.6)
        
        for line in lines:
            # Invert the color of the line
            inverted_color = invert_color(line.get_color())
            new_line = Line2D(line.get_xdata(), line.get_ydata(), linestyle=line.get_linestyle(), color=inverted_color, linewidth=line.get_linewidth()+0.2)
            ax.add_line(new_line)
        ax.autoscale()
        y_lim = ax.get_ylim()
        x_lim = ax.get_xlim()
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        
        # Save the combined plot
        fig.savefig(os.path.join(path, "combined_trace.png"))
        plt.close(fig)
        
        for i, line in enumerate(lines):
            fig = Figure(figsize=(10, 5), dpi=300, constrained_layout=True)
            ax = fig.add_subplot()
            ax.grid(True, which='both', linestyle='--', linewidth=0.3, alpha=0.6)
            new_line = Line2D(line.get_xdata(), line.get_ydata(), linestyle=line.get_linestyle(), color=invert_color(line.get_color()), linewidth=line.get_linewidth()+0.7)
            ax.add_line(new_line)
            ax.set_ylim(y_lim[0], y_lim[1])
            ax.set_xlim(x_lim[0], x_lim[1])
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            fig.savefig(os.path.join(path, f"trace_{i+1}.png"))
            plt.close(fig)
    
    elif type(legend) == dict: 
        path = os.path.join(path, "imgs_legend")
        if not os.path.exists(path):
            os.makedirs(path)
        
        res_bw = value_parser(legend['res_bw'])
        vid_bw = value_parser(legend['vid_bw'])
        if sweep_time >= 10:
            sweep_time = f"{int(sweep_time)} s"
        elif sweep_time < 10 and sweep_time >= 1:
            sweep_time = f"{sweep_time:.1f} s"
        elif sweep_time < 1:
            sweep_time = f"{sweep_time*1e3:.0f} ms"
        
        
        if 'mode' in legend and legend['mode'] == 'FAST':
            int_time = value_parser(legend['integration_time'], 's')
            left_text_lines = ["Resolution BW:", "Video BW:", "Sweep Time:", "Integration Time:"]
            right_text_lines = [res_bw, vid_bw, sweep_time, int_time]
            text = "\n".join([f"{left:<17}{right:>9}" for left, right in zip(left_text_lines, right_text_lines)])
        
        elif 'mode' in legend and legend['mode'] == 'HIGH-RES':
            left_text_lines = ["Resolution BW:", "Video BW:", "Sweep Time:"]
            right_text_lines = [res_bw, vid_bw, sweep_time]
            text = "\n".join([f"{left:<17}{right:>9}" for left, right in zip(left_text_lines, right_text_lines)])
        
        else:
            text = ""
        
        fig = Figure(figsize=(10, 5), dpi=300, constrained_layout=True)
        ax = fig.add_subplot()
        
        ax.grid(True, which='both', linestyle='--', linewidth=0.3, alpha=0.6)
        
        for line in lines:
            inverted_color = invert_color(line.get_color())
            new_line = Line2D(line.get_xdata(), line.get_ydata(), linestyle=line.get_linestyle(), color=inverted_color, linewidth=line.get_linewidth()+0.3)
            ax.add_line(new_line)
            
        ax.text(
            0.99, 
            0.98, 
            text, 
            transform=ax.transAxes, 
            fontsize=10, 
            fontfamily='monospace',
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='square', facecolor='wheat', alpha=0.5, edgecolor='wheat')
            )
        
        ax.autoscale()
        y_lim = ax.get_ylim()
        x_lim = ax.get_xlim()
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        
        # Save the combined plot
        fig.savefig(os.path.join(path, "combined_trace.png"))
        plt.close(fig)
        
        for i, line in enumerate(lines):
            fig = Figure(figsize=(10, 5), dpi=300, constrained_layout=True)
            ax = fig.add_subplot()
            ax.grid(True, which='both', linestyle='--', linewidth=0.3, alpha=0.6)
            new_line = Line2D(line.get_xdata(), line.get_ydata(), linestyle=line.get_linestyle(), color=invert_color(line.get_color()), linewidth=line.get_linewidth()+0.5)
            ax.add_line(new_line)
            ax.set_ylim(y_lim[0], y_lim[1])
            ax.set_xlim(x_lim[0], x_lim[1])
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.text(
                0.99, 
                0.98, 
                text, 
                transform=ax.transAxes, 
                fontsize=10, 
                fontfamily='monospace',
                verticalalignment='top',
                horizontalalignment='right',
                bbox=dict(boxstyle='square', facecolor='wheat', alpha=0.5, edgecolor='wheat'),
            )
            fig.savefig(os.path.join(path, f"trace_{i+1}.png"))
            plt.close(fig)
        
if __name__ == "__main__":
    
    config_dict = {
        "start_freq": 1e6,
        "stop_freq": 1e9,
        "mode": "FAST",
        "res_bw": 1000,
        "vid_bw": 10000,
        "integration_time": 0.1,
        "sweep_time": 0.1,
    }
    
    config_name = "hoola_hoop"
    
    sweep_time = 0.1
    
    line_1 = Line2D(np.random.rand(2, 10)[0], np.random.rand(2, 10)[1], linewidth=0.2, color='yellow')
    line_2 = Line2D(np.random.rand(2, 10)[0], np.random.rand(2, 10)[1], linewidth=0.2, color='white')
    line_3 = Line2D(np.random.rand(2, 10)[0], np.random.rand(2, 10)[1], linewidth=0.2, color='green')
    
    lines = [line_1, line_2, line_3]
    path = make_dir_measurement(config_name)
    
    save_config(path, config_dict, config_name)
    
    save_traces(path, lines)
    
    save_png(path, lines)

    save_png(path, lines, config_dict, sweep_time)
    
