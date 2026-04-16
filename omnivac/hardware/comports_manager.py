import serial
import serial.tools.list_ports
from PySide6.QtCore import QMetaObject, QObject, Qt, QThread, QTimer, Signal, Slot

from omnivac.hardware.RS232 import RS232

def getActivePorts() -> list:
    '''Gets all comports found and returns a list'''
    comport_list = []
    for i in serial.tools.list_ports.comports():
        i = str(i)[0:5] #Wählt die Zeichen im String die die Comportbezeichnung enthalten
        comport_list.append(i)
    if comport_list == []:
        return ["No comport found"]
    else:
        return comport_list

def initializePort(port: str, baudrate: str, parity: str, stopbits: str, bytesize: str):
    '''Opens commmunicatin with port'''
    convertet_parity = parity_to_pyserial(parity)  # converting Parity string to pyserial format
    convertet_stopbits = stopbits_to_pyserial(stopbits)  # converting Stop Bits string to pyserial format
    converte_bytesize = bytesize_to_pyserial(bytesize) # converting Bytsize string to pyserial format
    return RS232(port, baudrate, converte_bytesize, convertet_parity, convertet_stopbits)

#Funktion convert String to Right format for pyserial
def parity_to_pyserial(parity):
    '''Konvertiert den String zu serial.PARITY format. Funktioniert nur für "None", "Odd", "Even", "Mark", "Space".'''
    Parity = {
        "None": serial.PARITY_NONE,
        "Odd": serial.PARITY_ODD,
        "Even": serial.PARITY_EVEN,
        "Mark": serial.PARITY_MARK,
        "Space": serial.PARITY_SPACE
    }
    return Parity.get(parity, None) # None is returned if the String is invalid
    
#Funktion convert Numbert to Right format for pyserial
def bytesize_to_pyserial(number):
    """Konvertiert die Zahl zu serial.BYTESIZE-Format. 
    Funktioniert nur für '5', '6', '7', '8'.
    """
    byte_sizes = {
        "5": serial.FIVEBITS,
        "6": serial.SIXBITS,
        "7": serial.SEVENBITS,
        "8": serial.EIGHTBITS
    }
    return byte_sizes.get(number, None)  # None is returned if the number is invalid

def stopbits_to_pyserial(stopBit):
    '''Konvertiert den String zu serial.STOP_BITS format. Funktioniert nur für "1", "1.5", "2".'''
    stop_bit = {
        "1": serial.STOPBITS_ONE,
        "1.5": serial.STOPBITS_ONE_POINT_FIVE,
        "2": serial.STOPBITS_TWO
    }
    return stop_bit.get(stopBit, None)  #None is returned if the String is invalid