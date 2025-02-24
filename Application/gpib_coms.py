"""This module is used to communicate with GPIB devices via the Prologix GPIB to Ethernet adapter.
It was designed to be used with the Agilent N9010A Spectrum Analyzer (in HCRO Lab 2), 
but should be easily modified to run on any GPIB controllable Spectrum Analyzer.
"""

import socket
from ssl import socket_error

class GPIBDevice:
    def __init__(self, **kwargs: dict) -> None:
        """Initialize the Socket with IP address or URL of the Adapter and GPIB address of the device.
        Open a socket connection to the system.
        
        :param **kwargs: Dictionary of keyword arguments containing the IP address or URL of the Adapter and GPIB address of the device.
        :type **kwargs: dict
        
        :return: None
        """
        self.standard_values = {
                'Port':             1234,           # Port of the Prologix controller
                'ip_address':       '10.1.23.75',   # IP address of the Prologix controller
                'gpib_address':     12,             # GPIB address of the instrument
                }
        self.Port = self.standard_values['Port']
        
        if 'ip_address' in kwargs:
            self.host = kwargs['ip_address']
        
        else:
            self.host = self.standard_values['ip_address']
                    
        if 'gpib_address' in kwargs:
            self.addr = kwargs['gpib_address']
        else:
            self.addr = self.standard_values['gpib_address']
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        
    def connect(self) -> None:
        """Initialize the connection to the GPIB device.
        
        :return: None
        
        :raises: socket_error if the connection fails.
        """
        try:
            self.sock.settimeout(1)
            self.sock.connect((self.host, self.Port))      
        except Exception as e:
            e = f'Connection to Spectrum Analyzer failed'
            raise socket_error(e)

    def write(self, msg: str) -> None:
        """Write a message to the GPIB device.
        :param msg: Message to be sent to the GPIB device.
        :type msg: str
        
        :return: None
        """
        totalsent = 0
        self.sock.sendall(f'++addr {self.addr}\n'.encode('ascii'))
        while totalsent < len(msg):
            sendstr = str(msg[totalsent:])
            sent = self.sock.send(sendstr.encode('ascii'))
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent
        self.sock.send(b'\n')

    def read_head(self) -> str:
        """Read a (long) message from the GPIB Device. 
        
        This method is used for long messages containing a message length header of following format:
        #<num_digits><data_len><data>
        In some cases the header may itself be preceded by a single digit and newline. This will be handled by the method, the digit and newline gets discarded.

        :raises RuntimeError: raises RuntimeError if the header is invalid or the socket connection broken
        
        :return: ascii string of the message
        :rtype: str
        """
        self.sock.sendall(b'++read eoi\n')
        header = self.sock.recv(2).decode('ascii')
        
        if header[0] != '#':
            header = self.sock.recv(2).decode('ascii')
            if header[0] != '#':
                print(header)
                raise RuntimeError("invalid header")
        
        num_digits = int(header[1])
        
        data_len = int(self.sock.recv(num_digits).decode())
        
        data = b''
        bytes_read = 0
        
        while bytes_read < data_len:
            chunk = self.sock.recv(min(4096, data_len - bytes_read))
            if not chunk:
                raise RuntimeError("socket connection broken")
            data += chunk
            bytes_read += len(chunk)
            
        return data.strip().decode('ascii')
        
    def read(self, size: int=1024) -> str:
        """Read a (short) message from the GPIB Device.
        
        This method can be used for short messages without a message length header, it will truncate the message at the first newline.
        Most (but not all) messages will be truncated at 736 characters.

        :raises RuntimeError: raises RuntimeError if the socket connection broken
        
        :return: ascii string of the message
        :rtype: str
        """
        chunks = []
        remaining = size
        self.sock.sendall(b'++read eoi\n')
        while remaining > 0:
            chunk = self.sock.recv(1024)
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            remaining -= len(chunk)
            if b'\n' in chunk:
                break
        return b''.join(chunks).strip().decode('ascii')
    
    def query(self, msg: str) -> str:
        """Combine write and read to query from the GPIB device
        
        :param msg: Message to be sent to the GPIB device.
        :type msg: str
        
        :return: ascii string of the message
        :rtype: str
        """
        self.write(msg)
        return self.read()
    
    def query_head(self, msg: str) -> str:
        """Combine write and read_head to query a long reply from the GPIB device.
        Reply must contain header in the format #<num_digits><data_len>.
        
        :param msg: Message to be sent to the GPIB device.
        :type msg: str
        
        :return: ascii string of the message
        :rtype: str        
        """
        self.write(msg)
        return self.read_head()
            
    def disconnect(self) -> None:
        '''Close the connection to the GPIB device.
        
        :return: None
        '''
        try:
            self.sock.close()
            del self.sock
    
        except Exception as e:
            return f"Connection error: {str(e)}"