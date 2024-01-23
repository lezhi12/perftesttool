import time
import tidevice
from tidevice._perf import DataType

t = tidevice.Device()
perf = tidevice.Performance(t, [DataType.CPU, DataType.MEMORY,  DataType.FPS])

def callback(_type: tidevice.DataType, value: dict):
    print("R:", _type.value, value)
perf.start("com.psbc.mobilebank", callback=callback) 

while True:  
    try:  
        print("This is a infinite loop. Press Ctrl+C to exit.")  
        time.sleep(1)  # 暂停1秒  
    except KeyboardInterrupt:  
        print("\nExiting the loop...")  
        perf.stop()
        break  # 退出循环