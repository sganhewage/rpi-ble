from AR488Monitor import AR488Monitor
# import pandas as pd
import time

handlerReady = False

def write_log(msg: str) -> None:
    """Function that writes a message to the log file."""
    with open('communication_log.txt', 'a') as log_file:
        log_file.write(msg + '\n')

def write(instrument: AR488Monitor, msg: str)->None:
    """Function that sends a command and automatically logs it to the console."""
    instrument.write(msg)
    time.sleep(0.3)  # Allow time for the command to be processed
    logmsg = f"-> {msg}"
    print(logmsg)
    write_log(logmsg)
    
def read(instrument: AR488Monitor)->str:
    """Function that reads a command and automatically logs it to the console."""
    msg = instrument.manual_read()
    logmsg = f"<- {msg}"
    print(logmsg)
    write_log(logmsg)
    return msg

def configure(GPIBaddr: str)->AR488Monitor:
    global handlerReady
    
    """Configures the machine to be run, given the handler IDN and GPIB address. 
        It then connects to the handler, runs the configuration commands, and returns the AR488 resource for use in other methods."""
    inst = AR488Monitor()
    inst.write(f"++addr {GPIBaddr}")
    time.sleep(0.1)  # Allow time for the address to be set
    inst.write("++clr")
    inst._buffer = ''  # Clear the buffer before sending commands
    
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
        time.sleep(0.5)
        status = inst.getStatusByte()
        print(f"Status byte: {hex(status)}")
        if status & 0x40:  # SRQ asserted
            if status == 0x44:
                print("SRQ44 (Empty Socket Check) received.")
                break
            else:
                print(f"SRQ asserted, but not ESC (status byte = {hex(status)}). Waiting...")
    print("SRQ asserted. Reading CHECKEMPTY message...")
    
    # inst.write("++read")
    time.sleep(0.5)  # Allow time for the response to be processed
    response = read(inst)
    assert response == 'CHECKEMPTY', f"Expected \'CHECKEMPTY\' but received \'{response}\'"
    write(inst, "ECHOOK")
    
    return inst  

def lotFinished(instrument: AR488Monitor)->bool:
    """Checks if the the current lot is finished by sending SRQKIND? query."""
    write(instrument, "SRQKIND?")
    response = read(instrument)
    if (response == "SRQKIND 2"): return False
    elif (response == "SRQKIND 8"): return True
    else:
        print(f"Error: Unexpected Response: {response}")
        return True

def sortCycle(instrument: AR488Monitor, IDset: set, passBin=1, failBin=2, srqReceived=False)->bool:
    """Runs through the commands for sorting one chip, given the set of accepted 2DIDs."""
    if not srqReceived:
        print("Waiting for SRQ...")
        while True:
            time.sleep(0.5)
            status = instrument.getStatusByte()
            print(f"Status byte: {hex(status)}")
            if status & 0x40:  # SRQ asserted
                if status == 0x41:
                    print("SRQ41 received.")
                    break
                if status == 0x44:
                    print("SRQ44 (Empty Socket Check) received.")
                    print("SRQ asserted. Reading CHECKEMPTY message...")
                    
                    instrument.write("++read")
                    time.sleep(0.5)  # Allow time for the response to be processed
                    response = read(instrument)
                    assert response == 'CHECKEMPTY', f"Expected \'CHECKEMPTY\' but received \'{response}\'"
                    write(instrument, "ECHOOK")
                else:
                    print(f"SRQ asserted, but not ESC (status byte = {hex(status)}). Waiting...")
        print("SRQ asserted. Sending FULLSITES? message...")
    
    write(instrument, "FULLSITES?")
    response = read(instrument)
    for _ in range(1):  # Retry reading if response is not as expected
        if not response.startswith("Fullsites"):
            write(instrument, "FULLSITES?")
            response = read(instrument)
        else:
            break

    time.sleep(0.2)  # Allow time for the command to be processed
    write(instrument, "QRC?")
    response = read(instrument)
    for _ in range(1):
        if not response.startswith("QRC:"):
            write(instrument, "QRC?")
            response = read(instrument)
        else:
            break
    ID = response[response.find(':')+1:response.find(',')]
    
    write(instrument, "PAUSE")
    bin = getBinNumber(ID=ID, IDset=IDset)  # Wait for bin decision
    write(instrument, "RESUME")
    time.sleep(0.2)  # Allow time for the command to be processed
    
    write(instrument, f"BINON:00000000,00000000,00000000,0000000{bin}")
    response = read(instrument)  # Read the response to BINON command
    
    if not response.startswith("E"): write(instrument, f"BINON:00000000,00000000,00000000,0000000{bin}")
    write(instrument, "ECHOOK")
    
    instrument.clear_buffer()  # Clear the buffer after processing the command
     
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
    
def main(GPIBaddr: str, numParts: int = 1500, IDset: set = None):
    global handlerReady
    
    inst = configure(GPIBaddr)
    
    print(f"Starting sort cycle with {numParts} parts and ID set: {IDset}")
    if IDset is None:
        print("No ID set provided. Using empty set.")
        IDset = set()
    
    for i in range(numParts):
        print(f"Processing part {i+1}/{numParts}")
        sortCycle(inst, IDset=IDset, passBin=1, failBin=2, srqReceived=handlerReady)
        handlerReady=False
    
if __name__ == "__main__":
    IDset = {
        "141JWWY043060M",
        "141JWWY01D070P",
        "141JWWY0890A0J",
        "141JWWY01A0405",
        "141JWWY0910308",
        "141JWWY01A090D",
        "141JWWY091050G"
    }
    main("GPIB0::1::INSTR", IDset=IDset)