import pyvisa

def game(addr):
    #string is a list of comma separated values print each value
    rm = pyvisa.ResourceManager()
    try:
        resource = rm.open_resource(addr)
        idn = resource.query('*IDN?')
        print(f"Connected to {addr}: {idn.strip()}")
    except Exception as e:
        print(f"Error connecting to {addr}: {str(e)}")
        return

if __name__ == "__main__":
    game()