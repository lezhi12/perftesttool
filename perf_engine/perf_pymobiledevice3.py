from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
from pymobiledevice3.services.dvt.instruments.sysmontap import Sysmontap
from pymobiledevice3.services.dvt.instruments.graphics import Graphics
from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
import logging
from collections import namedtuple
import time
import tidevice
from tidevice._perf import DataType,gen_stimestamp,WaitGroup,append_data,RunningProcess
import threading
import typing
from collections import defaultdict, namedtuple
import time
import os
"""
process_attributes
2024-02-07 10:57:04 ISS root[6924] INFO pgid
2024-02-07 10:57:04 ISS root[6924] INFO pid
2024-02-07 10:57:04 ISS root[6924] INFO procFlags
2024-02-07 10:57:04 ISS root[6924] INFO memResidentSize
2024-02-07 10:57:04 ISS root[6924] INFO timerWakeBin2
2024-02-07 10:57:04 ISS root[6924] INFO __restricted
2024-02-07 10:57:04 ISS root[6924] INFO totalEnergyScore
2024-02-07 10:57:04 ISS root[6924] INFO pjobc
2024-02-07 10:57:04 ISS root[6924] INFO ppid
2024-02-07 10:57:04 ISS root[6924] INFO procAge
2024-02-07 10:57:04 ISS root[6924] INFO appSleep
2024-02-07 10:57:04 ISS root[6924] INFO threadsUser
2024-02-07 10:57:04 ISS root[6924] INFO __suddenTerm
2024-02-07 10:57:04 ISS root[6924] INFO memAnonPeak
2024-02-07 10:57:04 ISS root[6924] INFO faults
2024-02-07 10:57:04 ISS root[6924] INFO nfiles
2024-02-07 10:57:04 ISS root[6924] INFO msgRecv
2024-02-07 10:57:04 ISS root[6924] INFO uniqueID
2024-02-07 10:57:04 ISS root[6924] INFO cpuUsage
2024-02-07 10:57:04 ISS root[6924] INFO tdev
2024-02-07 10:57:04 ISS root[6924] INFO latencyQosTier
2024-02-07 10:57:04 ISS root[6924] INFO platIdleWakeups
2024-02-07 10:57:04 ISS root[6924] INFO vmPageIns
2024-02-07 10:57:04 ISS root[6924] INFO nice
2024-02-07 10:57:04 ISS root[6924] INFO memVirtualSize
2024-02-07 10:57:04 ISS root[6924] INFO timerWakeBin1
2024-02-07 10:57:04 ISS root[6924] INFO wiredSize
2024-02-07 10:57:04 ISS root[6924] INFO ctxSwitch
2024-02-07 10:57:04 ISS root[6924] INFO parentUniqueID
2024-02-07 10:57:04 ISS root[6924] INFO avgPowerScore
2024-02-07 10:57:04 ISS root[6924] INFO memCompressed
2024-02-07 10:57:04 ISS root[6924] INFO memRShrd
2024-02-07 10:57:04 ISS root[6924] INFO numRunning
2024-02-07 10:57:04 ISS root[6924] INFO intWakeups
2024-02-07 10:57:04 ISS root[6924] INFO svgid
2024-02-07 10:57:04 ISS root[6924] INFO name
2024-02-07 10:57:04 ISS root[6924] INFO __arch
2024-02-07 10:57:04 ISS root[6924] INFO cpuTotalUser
2024-02-07 10:57:04 ISS root[6924] INFO threadsSystem
2024-02-07 10:57:04 ISS root[6924] INFO policy
2024-02-07 10:57:04 ISS root[6924] INFO wqNumThreads
2024-02-07 10:57:04 ISS root[6924] INFO wqState
2024-02-07 10:57:04 ISS root[6924] INFO diskBytesRead
2024-02-07 10:57:04 ISS root[6924] INFO startAbsTime
2024-02-07 10:57:04 ISS root[6924] INFO rgid
2024-02-07 10:57:04 ISS root[6924] INFO memRPrvt
2024-02-07 10:57:04 ISS root[6924] INFO physFootprint
2024-02-07 10:57:04 ISS root[6924] INFO cowFaults
2024-02-07 10:57:04 ISS root[6924] INFO svuid
2024-02-07 10:57:04 ISS root[6924] INFO powerScore
2024-02-07 10:57:04 ISS root[6924] INFO cpuTotalSystem
2024-02-07 10:57:04 ISS root[6924] INFO ruid
2024-02-07 10:57:04 ISS root[6924] INFO wqBlockedThreads
2024-02-07 10:57:04 ISS root[6924] INFO sysCallsUnix
2024-02-07 10:57:04 ISS root[6924] INFO comm
2024-02-07 10:57:04 ISS root[6924] INFO tpgid
2024-02-07 10:57:04 ISS root[6924] INFO wqRunThreads
2024-02-07 10:57:04 ISS root[6924] INFO gid
2024-02-07 10:57:04 ISS root[6924] INFO coalitionID
2024-02-07 10:57:04 ISS root[6924] INFO threadCount
2024-02-07 10:57:04 ISS root[6924] INFO sysCallsMach
2024-02-07 10:57:04 ISS root[6924] INFO responsibleUniqueID
2024-02-07 10:57:04 ISS root[6924] INFO procStatus
2024-02-07 10:57:04 ISS root[6924] INFO machPortCount
2024-02-07 10:57:04 ISS root[6924] INFO priority
2024-02-07 10:57:04 ISS root[6924] INFO __sandbox
2024-02-07 10:57:04 ISS root[6924] INFO memPurgeable
2024-02-07 10:57:04 ISS root[6924] INFO throughputQosTier
2024-02-07 10:57:04 ISS root[6924] INFO responsiblePID
2024-02-07 10:57:04 ISS root[6924] INFO procXstatus
2024-02-07 10:57:04 ISS root[6924] INFO uid
2024-02-07 10:57:04 ISS root[6924] INFO msgSent
2024-02-07 10:57:04 ISS root[6924] INFO memAnon
2024-02-07 10:57:04 ISS root[6924] INFO diskBytesWritten
"""

"""
system_attributes
2024-02-07 10:57:04 ISS root[6924] INFO diskReadOps
2024-02-07 10:57:04 ISS root[6924] INFO vmUsedCount
2024-02-07 10:57:04 ISS root[6924] INFO __vmSwapUsage
2024-02-07 10:57:04 ISS root[6924] INFO vmZeroFillCount
2024-02-07 10:57:04 ISS root[6924] INFO vmSize
2024-02-07 10:57:04 ISS root[6924] INFO vmSwapIns
2024-02-07 10:57:04 ISS root[6924] INFO diskWriteOps
2024-02-07 10:57:04 ISS root[6924] INFO vmTotalUncompPagesInComp
2024-02-07 10:57:04 ISS root[6924] INFO vmPageIns
2024-02-07 10:57:04 ISS root[6924] INFO vmThrottledCount
2024-02-07 10:57:04 ISS root[6924] INFO vmReactivations
2024-02-07 10:57:04 ISS root[6924] INFO vmSpeculativeCount
2024-02-07 10:57:04 ISS root[6924] INFO physMemSize
2024-02-07 10:57:04 ISS root[6924] INFO vmCompressorPageCount
2024-02-07 10:57:04 ISS root[6924] INFO vmActiveCount
2024-02-07 10:57:04 ISS root[6924] INFO vmFreeCount
2024-02-07 10:57:04 ISS root[6924] INFO vmInactiveCount
2024-02-07 10:57:04 ISS root[6924] INFO diskBytesRead
2024-02-07 10:57:04 ISS root[6924] INFO vmPurgeableCount
2024-02-07 10:57:04 ISS root[6924] INFO vmLookups
2024-02-07 10:57:04 ISS root[6924] INFO vmDecompressions
2024-02-07 10:57:04 ISS root[6924] INFO vmHits
2024-02-07 10:57:04 ISS root[6924] INFO vmIntPageCount
2024-02-07 10:57:04 ISS root[6924] INFO netPacketsOut
2024-02-07 10:57:04 ISS root[6924] INFO vmPurges
2024-02-07 10:57:04 ISS root[6924] INFO vmPageOuts
2024-02-07 10:57:04 ISS root[6924] INFO threadCount
2024-02-07 10:57:04 ISS root[6924] INFO vmFaults
2024-02-07 10:57:04 ISS root[6924] INFO vmWireCount
2024-02-07 10:57:04 ISS root[6924] INFO vmExtPageCount
2024-02-07 10:57:05 ISS root[6924] INFO netPacketsIn
2024-02-07 10:57:05 ISS root[6924] INFO netBytesOut
2024-02-07 10:57:05 ISS root[6924] INFO vmSwapOuts
2024-02-07 10:57:05 ISS root[6924] INFO netBytesIn
2024-02-07 10:57:05 ISS root[6924] INFO vmCowFaults
2024-02-07 10:57:05 ISS root[6924] INFO vmCompressions
2024-02-07 10:57:05 ISS root[6924] INFO diskBytesWritten
"""
logger = logging.getLogger(__name__)
host = 'fd97:8ba5:1ef3::1'  # randomized
port = 61120  # randomized
""" monitor all most consuming processes by given cpuUsage threshold. """
"""[process(pid=296, name='YCReBank', cpuUsage=5.249755864338123, physFootprint=152880768)]"""

Process = namedtuple('process', 'pid name cpuUsage physFootprint')
def execCmd(cmd):
    """Execute the command to get the terminal print result"""
    r = os.popen(cmd)
    text = r.buffer.read().decode(encoding='ISO-8859-1').strip()
    r.close()
    print(text)
    return text
def dvt_notifications(service_provider):
    """ monitor graphics statistics """
    with DvtSecureSocketProxyService(lockdown=service_provider) as dvt:
        with Graphics(dvt) as graphics:
            for stats in graphics:
                #logger.info(stats)
                fps = stats['CoreAnimationFramesPerSecond'] # fps from GPU
                time.sleep(0.1)#缓冲一下，太快了会导致fps的timestamp有很多毫秒级别重复，导致测试报告中不展示曲线
                yield DataType.FPS, {"fps": fps, "time": time.time(), "value": fps}
def sysmon_process_monitor(service_provider, name):
    """ monitor all most consuming processes by given cpuUsage threshold. """

    Process = namedtuple('process', 'pid name cpuUsage physFootprint syscpu')
    #最终的app利用率和system利用率都是除过核心数的
    sys_cpu_percore = 0.0
    #只要来一次system信息，cpu_count就会被记住，之后每次来process信息，都用这个cpucount计算app_cpu
    #这样，process只等第一次system，不会每次都等system
    cpu_count = 0

    with DvtSecureSocketProxyService(lockdown=service_provider) as dvt:
        with Sysmontap(dvt) as sysmon:
            for process_snapshot in sysmon.iter_sysandproc():
                entries = []
                for process in process_snapshot:
                    if 'cpuUsage' in process and  (process['cpuUsage'] is not None) and (process['name'] ==name ) and  (process['physFootprint'] is not None and cpu_count>0) :
                        logger.info(process)
                        entries.append(Process(
                        pid=process['pid'],
                        name=process['name'],
                        cpuUsage=process['cpuUsage']/cpu_count,
                        physFootprint=process['physFootprint'],
                        syscpu=sys_cpu_percore)
                        )
                        break
                    elif 'SystemCPUUsage' in process and 'CPUCount' in process :
                        cpu_count = int(process['CPUCount'])
                        systemcpuusage_dic = process['SystemCPUUsage']
                        cpu_totalload = float(systemcpuusage_dic['CPU_TotalLoad'])
                        sys_cpu_percore = cpu_totalload/cpu_count
                        break


                if len(entries) > 0:
                    #logger.debug(entries)
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

