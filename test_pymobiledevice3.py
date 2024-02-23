from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
from pymobiledevice3.services.dvt.instruments.sysmontap import Sysmontap
from pymobiledevice3.services.dvt.instruments.graphics import Graphics
from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
from pymobiledevice3.cli.developer import sysmon_process_monitor
import logging
from collections import namedtuple
import time
import tidevice
from tidevice._perf import DataType,gen_stimestamp,WaitGroup,append_data,RunningProcess
import threading
import typing
from collections import defaultdict, namedtuple
logger = logging.getLogger(__name__)
host = 'fd77:bff1:df9a::1'  # randomized
port = 61731  # randomized
""" monitor all most consuming processes by given cpuUsage threshold. """
"""[process(pid=296, name='YCReBank', cpuUsage=5.249755864338123, physFootprint=152880768)]"""

Process = namedtuple('process', 'pid name cpuUsage physFootprint')
def dvt_notifications(service_provider):
    """ monitor graphics statistics """
    with DvtSecureSocketProxyService(lockdown=service_provider) as dvt:
        with Graphics(dvt) as graphics:
            for stats in graphics:
                #logger.info(stats)
                fps = stats['CoreAnimationFramesPerSecond'] # fps from GPU
                yield DataType.FPS, {"fps": fps, "time": time.time(), "value": fps}
def sysmon_process_monitor(service_provider, name):
    """ monitor all most consuming processes by given cpuUsage threshold. """

    Process = namedtuple('process', 'pid name cpuUsage physFootprint syscpu')

    with DvtSecureSocketProxyService(lockdown=service_provider) as dvt:
        with Sysmontap(dvt) as sysmon:
            for process_snapshot in sysmon.iter_processes():
                entries = []
                for process in process_snapshot:
                    #logger.info(process)
                    if (process['cpuUsage'] is not None) and (process['name'] ==name ) and  (process['physFootprint'] is not None) :
                        entries.append(Process(
                         pid=process['pid'],
                         name=process['name'],
                         cpuUsage=process['cpuUsage'],
                         physFootprint=process['physFootprint'],
                         syscpu=process['cpuTotalSystem'])
                         )


                if len(entries) > 0:
                    #logger.info(entries)
                    yield DataType.CPU, {
                        "timestamp": gen_stimestamp(),
                        "pid": entries[0].pid,
                        "value": entries[0].cpuUsage,  # max 100.0?, maybe not
                        "sys_value": entries[0].syscpu
                    }
                    yield DataType.MEMORY, {
                        "pid": entries[0].pid,
                        "timestamp": gen_stimestamp(),
                        "value": entries[0].physFootprint / 1024 / 1024  # MB
                    }
                else:
                    logger.info(entries)
#def gen_stimestamp(seconds: Optional[float] = None) -> str:
#    """ 生成专门用于tmq-service.taobao.org平台使用的timestampString """
#    if seconds is None:
#        seconds = time.time()
#    return int(seconds * 1000)



class Performance():
    # PROMPT_TITLE = "tidevice performance"

    def __init__(self,service_provider, perfs:typing.List[DataType] = []):
        #self._d = d
        self._bundle_id = None
        self._stop_event = threading.Event()
        self._wg = WaitGroup()
        self._started = False
        self._result = defaultdict(list)
        self._perfs = perfs

        # the callback function accepts all the data
        self._callback = None

    def start(self, service_provider, bundle_id: str, callback):
        self._thread_start(service_provider,bundle_id,callback)

    def _thread_start(self, service_provider,bundle_id,callback):
        iters = []
        if DataType.CPU in self._perfs or DataType.MEMORY in self._perfs:
            iters.append(sysmon_process_monitor(service_provider, bundle_id))
        if DataType.FPS in self._perfs:
            iters.append(dvt_notifications(service_provider))
        for it in (iters): # yapf: disable
            self._wg.add(1)
            threading.Thread(name="perf",
                            target=append_data,
                            args=(self._wg, self._stop_event, it,
                                callback,self._perfs),
                            daemon=True).start()

    def stop(self): # -> PerfReport:
        self._stop_event.set()
        print("Stopped")
        # memory and fps will take at least 1 second to catch _stop_event
        # to make function run faster, we not using self._wg.wait(..) here
        # > self._wg.wait(timeout=3.0) # wait all stopped
        # > self._started = False

    def wait(self, timeout: float):
        return self._wg.wait(timeout=timeout)


if __name__ == '__main__':
    def callback(_type: tidevice.DataType, value: dict):
            print("R:", _type.value, value)
    with RemoteServiceDiscoveryService((host, port)) as rsd:
        perf = Performance(rsd,[DataType.CPU,DataType.MEMORY,DataType.FPS])
        perf.start(rsd,"YCReBank", callback=callback)
    while True:  
        try:  
            print("This is a infinite loop. Press Ctrl+C to exit.")  
            time.sleep(1)  # 暂停1秒  
        except KeyboardInterrupt:  
            print("\nExiting the loop...")  
            perf.stop()
            break  # 退出循环



