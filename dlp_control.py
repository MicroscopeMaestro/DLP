from dlpc342x.commands import *
import time

WriteOperatingModeSelect(OperatingMode.SplashScreen)
time.sleep(0.5)
Summary, mode = ReadOperatingModeSelect()
print(mode)