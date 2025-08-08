import pyvisa
import pandas as pd
import time

def write_log(msg: str) -> None:
    """Function that writes a message to the log file."""
    with open('communication_log.txt', 'a') as log_file:
        log_file.write(msg + '\n')

def write(instrument: pyvisa.Resource, msg: str)->None:
    """Function that sends a command and automatically logs it to the console."""
    instrument.write(msg)
    logmsg = f"-> {msg}"
    print(logmsg)
    write_log(logmsg)
    
def read(instrument: pyvisa.Resource)->str:
    """Function that reads a command and automatically logs it to the console."""
    msg = instrument.read()
    logmsg = f"<- {msg}"
    print(logmsg)
    write_log(logmsg)
    return msg

def configure(GPIBaddr: str)->pyvisa.Resource:
    """Configures the machine to be run, given the handler IDN and GPIB address. 
        It then connects to the handler, runs the confiugration commands, and returns the pyVISA resource for use in other methods."""
    rm = pyvisa.ResourceManager()
    print(rm.list_resources()) # List all connected instruments

    # Replace with your actual GPIB address
    inst = rm.open_resource(GPIBaddr)
    
    # Set termination characters
    inst.write_termination = '\r\n' # This appends <CR><LF> to every write
    inst.read_termination = '\r\n'  # This expects <CR><LF> at the end of responses

    # Confirm correct device is connected
    # handlerIDN='SYNAX, S9, ID:ABCD9999, s/n:99999, MPC:1.00.0 / MCC:1.00.0'
    # write(inst, "*IDN?")
    # response = read(inst)
    # assert response == handlerIDN, f"Received Handler IDN:\t{response}\ndoes not match provided IDN:\t{handlerIDN}" 
    
    # Begin Configuration Commands
    write(inst, "CONFIGURE,SRQ=Y")
    response = read(inst)
    assert response == 'CONFIGURE,SRQ=Y:OK',f"Expected \''CONFIGURE,SRQ=Y:OK\' but received\'{response}\'"
    
    write(inst, "CONFIGURE,FULLSITES?=Y")
    response = read(inst)
    assert response == 'CONFIGURE,FULLSITES?=Y:OK',f"Expected \''CONFIGURE,FULLSITES?=Y:OK\' but received\'{response}\'"
    
    write(inst, "CONFIGURE,CONTACTOR=Y")
    response = read(inst)
    assert response == 'CONFIGURE,CONTACTOR=Y:OK',f"Expected \''CONFIGURE,CONTACTOR=Y:OK\' but received\'{response}\'"
    
    # Confirm 2DID Readability
    write(inst, "QRM?")
    response = read(inst)
    assert response == 'QRM:1', f"Expected \'QRM:!\' but received \'{response}\'"
    
    # Empty socket check
    write(inst, "REQUEST,CHECKEMPTY")
    print("Waiting for SRQ...")
    while True:
        status = inst.read_stb()
        if status & 0x40:  # SRQ asserted
            if status == 0x44:
                print("SRQ44 (Empty Socket Check) received.")
                break
            else:
                print(f"SRQ asserted, but not ESC (status byte = {hex(status)}). Waiting...")
        time.sleep(0.1)
    print("SRQ asserted. Reading CHECKEMPTY message...")
    response = read(inst)
    assert response == 'CHECKEMPTY', f"Expected \'CHECKEMPTY\' but received \'{response}\'"
    write(inst, "ECHOOK")
    
    return inst  

def lotFinished(instrument: pyvisa.Resource)->bool:
    """Checks if the the current lot is finished by sending SRQKIND? query."""
    write(instrument, "SRQKIND?")
    response = read(instrument)
    if (response == "SRQKIND 2"): return False
    elif (response == "SRQKIND 8"): return True
    else:
        print(f"Error: Unexpected Response: {response}")
        return True

def sortCycle(instrument: pyvisa.Resource, IDset: set, passBin=1, failBin=2)->bool:
    """Runs through the commands for sorting one chip, given the set of accepted 2DIDs."""
    print("Waiting for SRQ...")
    while True:
        status = instrument.read_stb()
        if status & 0x40:  # SRQ asserted
            if status == 0x41:
                print("SRQ41 received.")
                break
            else:
                print(f"SRQ asserted, but not ESC (status byte = {hex(status)}). Waiting...")
        time.sleep(0.1)
    print("SRQ asserted. Sending FULLSITES? message...")
    
    write(instrument, "FULLSITES?")
    response = read(instrument)
    
    write(instrument, "QRC?")
    response = read(instrument)
    ID = response[response.find(':')+1:response.find(',')]
    
    write(instrument, "PAUSE")
    bin = getBinNumber(ID=ID, IDset=IDset)  # Wait for bin decision
    write(instrument, "RESUME")
    
    write(instrument, f"BINON:00000000,00000000,00000000,0000000{bin}")
    
    read(instrument)  # Read the response to BINON command
    write(instrument, "ECHOOK")
     
def getBinNumber(ID: str, IDset: set, passBin=1, failBin=2, manual=False)->int:
    """Returns the bin number based on the 2DID. 
       If the ID is in the set of accepted IDs, it returns passBin, otherwise it returns failBin."""
    print(f"Processing ID: {ID}")
    if manual:
        bin = input(f"Enter bin number for ID {ID} (1 for pass, 2 for fail): ")
        return int(bin) if bin.isdigit() and int(bin) in (passBin, failBin) else failBin
    if ID in IDset: 
        print(f"ID {ID} in set. Sorting to pass bin {passBin}.")
        return passBin
    else:
        print(f"ID {ID} not in set. Sorting to fail bin.")
        return failBin
        
def collect2DIDs(excelFileDir: str, sheetName: str, columnIndex=0)->set:
    """Accepts Excel workbook, and grabs all the IDs from the given column and given sheet, starting on the second row."""
    try:
        df = pd.read_excel(excelFileDir, sheet_name=sheetName)
        
        # Validate column index
        if isinstance(columnIndex, int) and 0 <= columnIndex < len(df.columns):
            column_values = df.iloc[:, columnIndex].dropna().tolist()
            #column_values = column_values[1:] # Skip header or first row
            return set(column_values)
        else:
            print(f"Error: Column index '{columnIndex}' is out of range.")
            return None
    except FileNotFoundError:
        print(f"Error: File '{excelFileDir}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def main(GPIBaddr: str, numParts: int = 30000, IDset: set = None):
    inst = configure(GPIBaddr)
    
    print(f"Starting sort cycle with {numParts} parts and ID set: {IDset}")
    if IDset is None:
        print("No ID set provided. Using empty set.")
        IDset = set()
    
    for i in range(numParts):
        print(f"Processing part {i+1}/{numParts}")
        sortCycle(inst, IDset=IDset, passBin=1, failBin=2)
    
if __name__ == "__main__":
    main()