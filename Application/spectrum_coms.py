"""This module contains the SpectrumControl class, which is used to control the Agilent N9010A Spectrum Analyzer using the gpib_coms module.
"""
from ssl import socket_error
import time
import threading

from gpib_coms import GPIBDevice

class SpectrumControl(GPIBDevice):
    def __init__(self) -> None:
        """Initializes the connection to the Spectrum Analyzer and sets a dictionary of standard values for configuration parameters.
        
        :raises: socket_error if the connection fails.
        :raises: Exception if any other error occurs.
        
        :return: None
        """
        super().__init__()
        try:
            self.connect()
        except socket_error as e:
            raise socket_error(f"{e} \n\n   Hint: Check ethernet connection to GPIB-Controller")
        except Exception as e:
            raise e
        
        self.standard_values = {
                    'sweep_type':       'SWE',          # FFT or SWE
                    'trace_type':       'MAXH',         # WRIT, AVER, MAXH, MINH
                    'detector':         'POS',          # NORM, POS, NEG, AVER, SAMP
                    'cont_sweep':       'ON',           # ON or OFF
                    }
    
    def fetch_trace(self, path: str="D:\\Users\\Instrument\\Documents\\SA\\data\\traces\\RFI_TestBench\\TestBench_temp.csv") -> str:
        r"""Store and fetch trace data in a specified path on the Spectrum Analyzer.

        :param path: defaults to "D:\Users\Instrument\Documents\SA\data\traces\RFI_TestBench\TestBench_temp.csv"
        :type path: str, optional
        
        :raises: Exception if an error occurs while fetching.
        
        :return: Raw trace data from the Spectrum Analyzer containing frequency, amplitude and configuration data.
        :rtype: str
        """
        try:             
            while self.query('*OPC?') != '1':
                time.sleep(0.01) 
            
            self.write(f':MMEM:STOR:TRAC:DATA TRACE1, "{path}"')
            self.write('*WAI\n')
            while self.query('*OPC?') != '1':
                time.sleep(0.01)
           
            traceDat = self.query_head(f'MMEM:DATA? "{path}"')
            self.write('*WAI\n')
            while self.query('*OPC?') != '1':
                time.sleep(0.01)
        
        except Exception as e:
            traceDat = None
            self.write(':ABORT')
            raise e  
        
        return traceDat
    
    def send_config(self, **kwargs: dict) -> float | list:
        """This method is used to send configuration data to the Agilent N9010A Spectrum Analyzer and return the resulting sweep time.
        
        :param **kwargs: Configuration parameters to be sent to the Spectrum Analyzer.
        :type kwargs: dict
        
        :raises: Exception if an error occurs while sending the configuration data.
        
        :return: Sweep time of the Spectrum Analyzer and if any, error messages.
        :rtype: float or list
        """
        error_message = []
        try:
            self.write(':ABORT')    
            self.write('*RST')

            if 'sweep_points' in kwargs:
                self.write(f'SWE:POIN {float(kwargs["sweep_points"])}')
        
            if 'start_freq' in kwargs:
                self.write(f'FREQ:START {float(kwargs["start_freq"])}Hz')
                
            if 'stop_freq' in kwargs:
                self.write(f'FREQ:STOP {float(kwargs["stop_freq"])}Hz')
                if float(kwargs["stop_freq"]) <= float(kwargs["start_freq"]):
                    error_message.append("You might want to set your stop frequency higher than your start frequency.\n")
            
            if 'res_bw' in kwargs:
                self.write(f'BAND:RES {float(kwargs["res_bw"])}Hz')
                
            if 'vid_bw' in kwargs:
                self.write(f'BAND:VID {float(kwargs["vid_bw"])}Hz')

            if 'attenuation' in kwargs:
                self.write(f'POW:ATT {float(abs(kwargs["attenuation"]))}')
                if abs(float(kwargs["attenuation"])) < 10:
                    error_message.append("Attenuation is low.\n         Please make sure your signal is not too strong, it might damage the Spectrum Analyzer.")
            
            if 'num_aver' in kwargs:
                self.write(f'AVER:COUN {float(kwargs["num_aver"])}')
                
            if 'detector' in kwargs:
                self.write(f'DET:TRAC1 {kwargs["detector"]}')
            elif 'detector' in self.standard_values:
                self.write(f'DET:TRAC1 {self.standard_values["detector"]}')
            else:
                raise ValueError("Detector type not specified.")
            
            if 'sweep_type' in kwargs:
                self.write(f'SWE:TYPE {kwargs["sweep_type"]}')
            elif 'sweep_type' in self.standard_values:
                self.write(f'SWE:TYPE {self.standard_values["sweep_type"]}')
            else:
                raise ValueError("Sweep type not specified.")
            
            if 'trace_type' in kwargs:
                self.write(f'TRAC1:TYPE {kwargs["trace_type"]}')
            elif 'mode' in kwargs and kwargs['mode'] == 'HIGH-RES':
                self.write(f'TRAC1:TYPE WRIT')
            elif 'mode' in kwargs and kwargs['mode'] == 'FAST':
                self.write(f'TRAC1:TYPE MAXH')
            elif 'trace_type' in self.standard_values:
                self.write(f'TRAC1:TYPE {self.standard_values["trace_type"]}')
            else:
                raise ValueError("Trace type not specified.")
            
            if 'cont_sweep' in kwargs:
                self.write(f'INIT:CONT {kwargs["cont_sweep"]}')
            elif 'cont_sweep' in self.standard_values:
                self.write(f'INIT:CONT {self.standard_values["cont_sweep"]}')
            else:
                raise ValueError("Sweep mode not specified.")
                
                
            self.write('AVER:COUN 0')  
            self.write('INIT:IMM')
            
            sweep_time = self.query(":SENSe:SWEep:TIME?")
            
            if float(sweep_time) > 60*10 and float(sweep_time) <= 60*20:
                error_message.append("Sweep time exceeds 10 minutes.\n         Please note that it is not possible to interrupt without accessing the Spectrum Analyzer.")
            elif float(sweep_time) > 60*20 and float(sweep_time) <= 60*30:
                error_message.append("Sweep time exceeds 20 minutes.\n         Please note that it is not possible to interrupt without accessing the Spectrum Analyzer.")
            elif float(sweep_time) > 60*30 and float(sweep_time) <= 60*40:
                error_message.append("Sweep time exceeds 30 minutes.\n         Please note that it is not possible to interrupt without accessing the Spectrum Analyzer.") 
            elif float(sweep_time) > 60*40 and float(sweep_time) <= 60*50:
                error_message.append("Sweep time exceeds 40 minutes.\n         Please note that it is not possible to interrupt without accessing the Spectrum Analyzer.")
            elif float(sweep_time) > 60*50 and float(sweep_time) <= 60*60:
                error_message.append("Sweep time exceeds 50 minutes.\n         Please note that it is not possible to interrupt without accessing the Spectrum Analyzer.")       
            elif float(sweep_time) > 60*60 and float(sweep_time) < 4000:
                error_message.append("Sweep time exceeds 60 minutes.\n         Please note that it is not possible to interrupt without accessing the Spectrum Analyzer.")
            elif float(sweep_time) == 4000:
                error_message = "Sweep time is at (or above) maximum value, proceeding would lead to crash.\n         Reduce frequency range or increase bandwidth."
                return float(sweep_time), error_message, True
                
        except socket_error as e:
            error_message.append("Check ethernet connection to GPIB-Controller")
        
        except Exception as e:
            raise e
       
        if error_message != []:
            return float(sweep_time), error_message
        
        return float(sweep_time)
    
    def trace_threaded_cont(self, callback, t_refresh: float=None, **kwargs: dict) -> threading.Thread:
        """Creates a thread that fetches trace data from the Spectrum Analyzer and sends it to the callback function.
        Can be used for continuous data acquisition.
        
        :param callback: Callback function to be called with the trace data.
        :type callback: function
        
        :param t_refresh: if in timed mode specifies the time to fetch, defaults to None
        :type t_refresh: float, optional
        
        :return: Thread that fetches trace data from the Spectrum Analyzer.
        :rtype: threading.Thread
        """
        def run():
            self.write(f'AVER:COUN 1')
            
            self.write('INIT:CONT ON')

            if 'display_refresh' in kwargs:
                refresh = kwargs.get('display_refresh')
            
            elif t_refresh:
                refresh = t_refresh
            
            time.sleep(refresh+0.01)
            trace = self.fetch_trace()
            callback(trace)
                    
        trace_thread = threading.Thread(target=run, daemon=True)
        
        return trace_thread
    
    def trace_simple(self, **kwargs: dict) -> str:
        """This method is used to fetch a single trace from the Spectrum Analyzer.
        Not used in SPIKES, but can be used for testing purposes.
        
        :return: Raw trace data from the Spectrum Analyzer containing frequency, amplitude and configuration data.
        :rtype: str
        """
        self.write(f'AVER:COUN {kwargs["num_aver"]}')
        self.write('INIT:IMM')
        trace = self.fetch_trace()
        
        return trace    

if __name__ == '__main__':
    """This is a test script for the SpectrumControl class. 
    It will print the ID of the Spectrum Analyzer and a truncated single trace for an insight on how the raw data looks like.
    """
    SA = SpectrumControl()
    print(SA.query('*IDN?'))
    print(f'{SA.trace_simple(sweep_points=1000, start_freq=1e9, stop_freq=2e9, res_bw=1e6, vid_bw=1e6, attenuation=10, num_aver=1)[0:1023]}... \nAnd so on.')