import sys, os, clr

ti_gui = r"C:\Users\Juan\AppData\Roaming\Texas Instruments\DLP EVM GUI 4.0.0.15"
sys.path.extend([ti_gui, os.path.join(ti_gui, "settings", "Scripts")])

clr.AddReference("DLPComposer.IO")
from DLPComposer.IO import UARTInterface, I2CInterface

def check():
    print("--- SEARCHING FOR INTERFACES ---")
    
    print("\nUART:")
    try:
        uart = UARTInterface("UART")
        for p in uart.GetAvailableInterfaces():
            print(f"  - {p.Name}")
    except Exception as e:
        print(f"  Error: {e}")

    print("\nI2C:")
    try:
        # Note: Some DLLs use "I2C" or "I2C (DLP USB-to-I2C)"
        i2c = I2CInterface("I2C")
        for p in i2c.GetAvailableInterfaces():
            print(f"  - {p.Name}")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    check()
