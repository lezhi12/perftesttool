import datetime
import re
import time
import os
from logzero import logger
import tidevice
import multiprocessing
import solox.public._iosPerf as iosP
from solox.public.iosperf._perf import DataType, Performance
from solox.public.adb import adb
from solox.public.common import Devices, File, Method, Platform
from solox.public.fps import FPSMonitor, TimeUtils

d = Devices()
f = File()
m = Method()

class Target:
    CPU = 'cpu'
    Memory = 'memory'
    Battery = 'battery'
    Network = 'network'
    FPS = 'fps'
    GPU = 'gpu'

class CPU(object):

    def __init__(self, pkgName, deviceId, platform=Platform.Android, pid=None):
        self.pkgName = pkgName
        self.deviceId = deviceId
        self.platform = platform
        self.pid = pid
        if self.pid is None and self.platform == Platform.Android:
            self.pid = d.getPid(pkgName=self.pkgName, deviceId=self.deviceId)[0].split(':')[0]

    def getprocessCpuStat(self):
        """get the cpu usage of a process at a certain time"""
        cmd = f'cat /proc/{self.pid}/stat'
        result = adb.shell(cmd=cmd, deviceId=self.deviceId)
        r = re.compile("\\s+")
        toks = r.split(result)
        #print("this is process toks")
        #print(toks)
        processCpu = float(int(toks[13]) + int(toks[14]) + int(toks[15]) + int(toks[16]))
        return processCpu

    def getTotalCpuStat_yuandaima_NoUse_lezhi(self):
        """get the total cpu usage at a certain time"""
        cmd = f'cat /proc/stat |{d.filterType()} ^cpu'
        result = adb.shell(cmd=cmd, deviceId=self.deviceId)
        print("lezhi--result\n%s",result)
        r = re.compile(r'(?<!cpu)\d+')
        toks = r.findall(result)
        totalCpu = 0
        for i in range(1, 9):
            totalCpu += float(toks[i])
        return float(totalCpu)
    def getTotalCpuStat(self):
        """get the total cpu usage at a certain time from /proc/stat, example data in /proc/stat
        cpu  1532068 275544 1909629 10632752 57229 329123 376193 0 0 0
        cpu0 358840 53389 574803 9639681 53988 125269 156098 0 0 0
        cpu1 398236 60562 573494 123828 835 115921 153578 0 0 0
        cpu2 249331 51646 278443 139294 581 47965 49583 0 0 0
        cpu3 177405 32650 176061 144832 506 28531 9855 0 0 0
        cpu4 117799 25046 95076 143242 406 3276 1867 0 0 0
        cpu5 95196 20734 77480 144453 339 2442 1770 0 0 0
        cpu6 79527 20548 84534 147661 323 2323 2431 0 0 0
        cpu7 55734 10969 49738 149761 251 3396 1011 0 0 0
        total_cpu_time=第一行数据的和;idle_cputime=第一行第4列的数据;cpu不闲的时间=total_cputime-idle_cputime(该方法返回total时间和不闲时间)
        """
        cmd = f'cat /proc/stat |{d.filterType()} ^cpu'
        result = adb.shell(cmd=cmd, deviceId=self.deviceId)
        #print("lezhi--result\n%s"%result)
        r = re.compile(r'(?<!cpu)\d+')
        toks = r.findall(result)
        #print("lezhi---toks")
        #print(toks)
        totalCpu = 0
        for i in range(0, 9):
            totalCpu += float(toks[i])
        ileCpu = float(toks[3])
        sysCpu = totalCpu - ileCpu
        #print("lezhi--toks[0]:%s"%toks[0])
        #print("lezhi--totalcpu:%f"%totalCpu)
        #print("lezhi--syscpu:%f"%sysCpu)
        return float(totalCpu),float(sysCpu)

    def getCpuCores(self):
        """get Android cpu cores"""
        cmd = 'cat /sys/devices/system/cpu/online'
        result = adb.shell(cmd=cmd, deviceId=self.deviceId)
        try:
            nums = int(result.split('-')[1]) + 1
        except:
            nums = 1
        return nums

    def getSysCpuStat_yuandaima_NoUse_lezhi(self):
        """get the total cpu usage at a certain time"""
        cmd = f'cat /proc/stat |{d.filterType()} ^cpu'
        result = adb.shell(cmd=cmd, deviceId=self.deviceId)
        r = re.compile(r'(?<!cpu)\d+')
        toks = r.findall(result)
        ileCpu = int(toks[4])
        sysCpu = self.getTotalCpuStat() - ileCpu
        return sysCpu

    def getAndroidCpuRate(self, noLog=False):
        """get the Android cpu rate of a process"""
        processCpuTime_1 = self.getprocessCpuStat()
        totalCpuTime_1,sysCpuTime_1 = self.getTotalCpuStat()
        #sysCpuTime_1 = self.getSysCpuStat(totalCpuTime_1)
        time.sleep(0.5)
        processCpuTime_2 = self.getprocessCpuStat()
        totalCpuTime_2,sysCpuTime_2 = self.getTotalCpuStat()
        #sysCpuTime_2 = self.getSysCpuStat(totalCpuTime_2)
        appCpuRate = round(float((processCpuTime_2 - processCpuTime_1) / (totalCpuTime_2 - totalCpuTime_1) * 100), 2)
        sysCpuRate = round(float((sysCpuTime_2 - sysCpuTime_1) / (totalCpuTime_2 - totalCpuTime_1) * 100), 2)
        if noLog is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
            f.add_log(os.path.join(f.report_dir,'cpu_app.log'), apm_time, appCpuRate)
            f.add_log(os.path.join(f.report_dir,'cpu_sys.log'), apm_time, sysCpuRate)

        return appCpuRate, sysCpuRate

    def getiOSCpuRate(self, noLog=False):
        """get the iOS cpu rate of a process, unit:%"""
        apm = iosAPM(self.pkgName)
        appCpuRate = round(float(apm.getPerformance(apm.cpu)[0]), 2)
        sysCpuRate = round(float(apm.getPerformance(apm.cpu)[1]), 2)
        if noLog is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
            f.add_log(os.path.join(f.report_dir,'cpu_app.log'), apm_time, appCpuRate)
            f.add_log(os.path.join(f.report_dir,'cpu_sys.log'), apm_time, sysCpuRate)
        return appCpuRate, sysCpuRate

    def getCpuRate(self, noLog=False):
        """Get the cpu rate of a process, unit:%"""
        appCpuRate, systemCpuRate = self.getAndroidCpuRate(noLog) if self.platform == Platform.Android else self.getiOSCpuRate(noLog)
        return appCpuRate, systemCpuRate

class MEM(object):
    def __init__(self, pkgName, deviceId, platform=Platform.Android, pid=None):
        self.pkgName = pkgName
        self.deviceId = deviceId
        self.platform = platform
        self.pid = pid
        if self.pid is None and self.platform == Platform.Android:
            self.pid = d.getPid(pkgName=self.pkgName, deviceId=self.deviceId)[0].split(':')[0]

    def getAndroidMem(self):
        """Get the Android memory ,unit:MB"""
        cmd = f'dumpsys meminfo {self.pid}'
        output = adb.shell(cmd=cmd, deviceId=self.deviceId)
        m_total = re.search(r'TOTAL\s*(\d+)', output)
        m_native = re.search(r'Native Heap\s*(\d+)', output)
        m_dalvik = re.search(r'Dalvik Heap\s*(\d+)', output)
        print("m_total is :")
        print(m_total)
        print("m_native is :")
        print(m_native)
        print("m_dalvik is :")
        print(m_dalvik)
        print("m_total.group(1) is :")
        print (float(m_total.group(1)))
        print("m_native.group(1) is :")
        print (float(m_native.group(1)))
        print("m_dalvik.group(1) is :")
        print (float(m_dalvik.group(1)))
        totalPass = round(float(float(m_total.group(1))) / 1024, 2)
        nativePass = round(float(float(m_native.group(1))) / 1024, 2)
        dalvikPass = round(float(float(m_dalvik.group(1))) / 1024, 2)
        return totalPass, nativePass, dalvikPass

    def getiOSMem(self):
        """Get the iOS memory"""
        apm = iosAPM(self.pkgName)
        totalPass = round(float(apm.getPerformance(apm.memory)), 2)
        nativePass = 0
        dalvikPass = 0
        return totalPass, nativePass, dalvikPass

    def getProcessMem(self, noLog=False):
        """Get the app memory"""
        totalPass, nativePass, dalvikPass = self.getAndroidMem() if self.platform == Platform.Android else self.getiOSMem()
        if noLog is False:    
            apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
            f.add_log(os.path.join(f.report_dir,'mem_total.log'), apm_time, totalPass)
            if self.platform == Platform.Android:
                f.add_log(os.path.join(f.report_dir,'mem_native.log'), apm_time, nativePass)
                f.add_log(os.path.join(f.report_dir,'mem_dalvik.log'), apm_time, dalvikPass)
        return totalPass, nativePass, dalvikPass

class Battery(object):
    def __init__(self, deviceId, platform=Platform.Android):
        self.deviceId = deviceId
        self.platform = platform
    
    def getBattery(self, noLog=False):
        if self.platform == Platform.Android:
            level, temperature = self.getAndroidBattery(noLog)
            return level, temperature
        else:
            temperature, current, voltage, power = self.getiOSBattery(noLog)
            return temperature, current, voltage, power
        
    def getAndroidBattery(self, noLog=False):
        """Get android battery info, unit:%"""
        # Switch mobile phone battery to non-charging state
        cmd = 'dumpsys battery set status 1'
        adb.shell(cmd=cmd, deviceId=self.deviceId)
        # Get phone battery info
        cmd = 'dumpsys battery'
        output = adb.shell(cmd=cmd, deviceId=self.deviceId)
        level = int(re.findall(u'level:\s?(\d+)', output)[0])
        temperature = int(re.findall(u'temperature:\s?(\d+)', output)[0]) / 10
        if noLog is False:
             apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
             f.add_log(os.path.join(f.report_dir,'battery_level.log'), apm_time, level)
             f.add_log(os.path.join(f.report_dir,'battery_tem.log'), apm_time, temperature)
        return level, temperature
    
    def getiOSBattery(self, noLog=False):
        """Get ios battery info, unit:%"""
        d  = tidevice.Device()
        ioDict =  d.get_io_power()
        tem = m._setValue(ioDict['Diagnostics']['IORegistry']['Temperature'])
        current = m._setValue(abs(ioDict['Diagnostics']['IORegistry']['InstantAmperage']))
        voltage = m._setValue(ioDict['Diagnostics']['IORegistry']['Voltage'])
        power = current * voltage / 1000
        if noLog is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
            f.add_log(os.path.join(f.report_dir,'battery_tem.log'), apm_time, tem) # unknown
            f.add_log(os.path.join(f.report_dir,'battery_current.log'), apm_time, current) #mA
            f.add_log(os.path.join(f.report_dir,'battery_voltage.log'), apm_time, voltage) #mV
            f.add_log(os.path.join(f.report_dir,'battery_power.log'), apm_time, power)
        return tem, current, voltage, power

    def recoverBattery(self):
        """Reset phone charging status"""
        cmd = 'dumpsys battery reset'
        adb.shell(cmd=cmd, deviceId=self.deviceId)

class Flow(object):

    def __init__(self, pkgName, deviceId, platform=Platform.Android, pid=None):
        self.pkgName = pkgName
        self.deviceId = deviceId
        self.platform = platform
        self.pid = pid
        if self.pid is None and self.platform == Platform.Android:
            self.pid = d.getPid(pkgName=self.pkgName, deviceId=self.deviceId)[0].split(':')[0]

    def getAndroidNet(self, wifi=True):
        """Get Android send/recv data, unit:KB wlan0/rmnet0"""
        net = 'wlan0' if wifi else 'rmnet0'
        cmd = f'cat /proc/{self.pid}/net/dev |{d.filterType()} {net}'
        output_pre = adb.shell(cmd=cmd, deviceId=self.deviceId)
        m_pre = re.search(r'{}:\s*(\d+)\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*(\d+)'.format(net), output_pre)
        sendNum_pre = round(float(float(m_pre.group(2)) / 1024), 2)
        recNum_pre = round(float(float(m_pre.group(1)) / 1024), 2)
        time.sleep(1)
        output_final = adb.shell(cmd=cmd, deviceId=self.deviceId)
        m_final = re.search(r'{}:\s*(\d+)\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*(\d+)'.format(net), output_final)
        sendNum_final = round(float(float(m_final.group(2)) / 1024), 2)
        recNum_final = round(float(float(m_final.group(1)) / 1024), 2)
        sendNum = round(float(sendNum_final - sendNum_pre), 2)
        recNum = round(float(recNum_final - recNum_pre), 2)
        return sendNum, recNum
    
    def setAndroidNet(self, wifi=True):
        net = 'wlan0' if wifi else 'rmnet0'
        cmd = f'cat /proc/{self.pid}/net/dev |{d.filterType()} {net}'
        output_pre = adb.shell(cmd=cmd, deviceId=self.deviceId)
        m = re.search(r'{}:\s*(\d+)\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*\d+\s*(\d+)'.format(net), output_pre)
        sendNum = round(float(float(m.group(2)) / 1024), 2)
        recNum = round(float(float(m.group(1)) / 1024), 2)
        return sendNum, recNum


    def getiOSNet(self):
        """Get iOS upflow and downflow data"""
        apm = iosAPM(self.pkgName)
        apm_data = apm.getPerformance(apm.network)
        sendNum = round(float(apm_data[1]), 2)
        recNum = round(float(apm_data[0]), 2)
        return sendNum, recNum

    def getNetWorkData(self, wifi=True, noLog=False):
        """Get the upflow and downflow data, unit:KB"""
        sendNum, recNum = self.getAndroidNet(wifi) if self.platform == Platform.Android else self.getiOSNet()
        if noLog is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
            f.add_log(os.path.join(f.report_dir,'upflow.log'), apm_time, sendNum)
            f.add_log(os.path.join(f.report_dir,'downflow.log'), apm_time, recNum)
        return sendNum, recNum

class FPS(object):

    def __init__(self, pkgName, deviceId, platform=Platform.Android, surfaceview=True):
        self.pkgName = pkgName
        self.deviceId = deviceId
        self.platform = platform
        self.surfaceview = surfaceview
        self.apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')

    def getAndroidFps(self, noLog=False):
        """get Android Fps, unit:HZ"""
        monitors = FPSMonitor(device_id=self.deviceId, package_name=self.pkgName, frequency=1,
                              surfaceview=self.surfaceview, start_time=TimeUtils.getCurrentTimeUnderline())
        monitors.start()
        fps, jank = monitors.stop()
        if noLog is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
            f.add_log(os.path.join(f.report_dir,'fps.log'), apm_time, fps)
            f.add_log(os.path.join(f.report_dir,'jank.log'), apm_time, jank)
        return fps, jank

    def getiOSFps(self, noLog=False):
        """get iOS Fps"""
        apm = iosAPM(self.pkgName)
        fps = int(apm.getPerformance(apm.fps))
        if noLog is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
            f.add_log(os.path.join(f.report_dir,'fps.log'), apm_time, fps)
        return fps, 0

    def getFPS(self, noLog=False):
        """get fps、jank"""
        fps, jank = self.getAndroidFps(noLog) if self.platform == Platform.Android else self.getiOSFps(noLog)
        return fps, jank

class GPU(object):
    def __init__(self, pkgName):
        self.pkgName = pkgName

    def getGPU(self, noLog=False):
        apm = iosAPM(self.pkgName)
        gpu = apm.getPerformance(apm.gpu)
        if noLog is False:
            apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
            f.add_log(os.path.join(f.report_dir,'gpu.log'), apm_time, gpu)
        return gpu   

class iosAPM(object):

    def __init__(self, pkgName, deviceId=tidevice.Device()):
        self.pkgName = pkgName
        self.deviceId = deviceId
        self.apm_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
        self.cpu = DataType.CPU
        self.memory = DataType.MEMORY
        self.network = DataType.NETWORK
        self.fps = DataType.FPS
        self.gpu = DataType.GPU
        self.perfs = 0
        self.app_cpu = 0
        self.sys_cpu = 0
        self.downflow = 0
        self.upflow = 0

    def callback(self, _type: DataType, value: dict):
        if _type == 'network':
            self.downflow = value['downFlow']
            self.upflow = value['upFlow']
        else:
            self.perfs = value['value']

    def getPerformance(self, perfTpe: DataType):
        if perfTpe == DataType.NETWORK:
            perf = Performance(self.deviceId, [perfTpe])
            perf.start(self.pkgName, callback=self.callback)
            time.sleep(3)
            perf.stop()
            perf_value = self.downflow, self.upflow
        else:
            perf = iosP.Performance(self.deviceId, [perfTpe])
            perf_value = perf.start(self.pkgName, callback=self.callback)
        return perf_value

class APM(object):
    """for python api"""

    def __init__(self, pkgName, platform=Platform.Android, deviceId=None,
                 surfaceview=True, noLog=True, pid=None, duration=0):
        self.pkgName = pkgName
        self.deviceId = deviceId
        self.platform = platform
        self.surfaceview = surfaceview
        self.noLog = noLog
        self.pid = pid
        self.duration = duration
        self.end_time = time.time() + self.duration
        d.devicesCheck(platform=self.platform, deviceid=self.deviceId, pkgname=self.pkgName)

    def collectCpu(self):
        _cpu = CPU(self.pkgName, self.deviceId, self.platform, pid=self.pid)
        result = {}
        while True:
            appCpuRate, systemCpuRate = _cpu.getCpuRate(noLog=self.noLog)
            result = {'appCpuRate': appCpuRate, 'systemCpuRate': systemCpuRate}
            logger.info(f'cpu: {result}')
            if time.time() > self.end_time:
                break
        return result

    def collectMemory(self):
        _memory = MEM(self.pkgName, self.deviceId, self.platform, pid=self.pid)
        result = {}
        while True:
            total, native, dalvik = _memory.getProcessMem(noLog=self.noLog)
            result = {'total': total, 'native': native, 'dalvik': dalvik}
            logger.info(f'memory: {result}')
            if time.time() > self.end_time:
                break
        return result

    def collectBattery(self):
        _battery = Battery(self.deviceId, self.platform)
        result = {}
        while True:
            final = _battery.getBattery(noLog=self.noLog)
            if self.platform == Platform.Android:
                result = {'level': final[0], 'temperature': final[1]}
            else:
                result = {'temperature': final[0], 'current': final[1], 'voltage': final[2], 'power': final[3]}
            logger.info(f'battery: {result}')
            if time.time() > self.end_time:
                break
        return result

    def collectFlow(self, wifi=True):
        _flow = Flow(self.pkgName, self.deviceId, self.platform, pid=self.pid)
        if self.noLog is False:
            data = _flow.setAndroidNet(wifi=wifi)
            f.record_net('pre', data[0], data[1])
        result = {}
        while True:
            upFlow, downFlow = _flow.getNetWorkData(wifi=wifi,noLog=self.noLog)
            result = {'send': upFlow, 'recv': downFlow}
            logger.info(f'network: {result}')
            if time.time() > self.end_time:
                break
        return result

    def collectFps(self):
        _fps = FPS(self.pkgName, self.deviceId, self.platform, self.surfaceview)
        result = {}
        while True:
            fps, jank = _fps.getFPS(noLog=self.noLog)
            result = {'fps': fps, 'jank': jank}
            logger.info(f'fps: {result}')
            if time.time() > self.end_time:
                break
        return result
    
    def collectGpu(self):
        _gpu = GPU(self.pkgName)
        result = {}
        while True:
            if self.platform == Platform.Android:
                raise Exception('not support android')
            gpu = _gpu.getGPU(noLog=self.noLog)
            result = {'gpu': gpu}
            logger.info(f'gpu: {result}')
            if time.time() > self.end_time:
                break
        return result
    
    def setPerfs(self):
        match(self.platform):
            case Platform.Android:
                adb.shell(cmd='dumpsys battery reset', deviceId=self.deviceId)
                _flow = Flow(self.pkgName, self.deviceId, self.platform, pid=self.pid)
                data = _flow.setAndroidNet()
                f.record_net('end', data[0], data[1])
                scene = f.make_report(app=self.pkgName, devices=self.deviceId,
                                      platform=self.platform, model='normal')
                summary = f._setAndroidPerfs(scene)
                summary_dict = {}
                summary_dict['cpu_app'] = summary['cpuAppRate']
                summary_dict['cpu_sys'] = summary['cpuSystemRate']
                summary_dict['mem_total'] = summary['totalPassAvg']
                summary_dict['mem_native'] = summary['nativePassAvg']
                summary_dict['mem_dalvik'] = summary['dalvikPassAvg']
                summary_dict['fps'] = summary['fps']
                summary_dict['jank'] = summary['jank']
                summary_dict['level'] = summary['batteryLevel']
                summary_dict['tem'] = summary['batteryTeml']
                summary_dict['net_send'] = summary['flow_send']
                summary_dict['net_recv'] = summary['flow_recv']
                summary_dict['cpu_charts'] = f.getCpuLog(Platform.Android, scene)
                summary_dict['mem_charts'] = f.getMemLog(Platform.Android, scene)
                summary_dict['net_charts'] = f.getFlowLog(Platform.Android, scene)
                summary_dict['battery_charts'] = f.getBatteryLog(Platform.Android, scene)
                summary_dict['fps_charts'] = f.getFpsLog(Platform.Android, scene)['fps']
                summary_dict['jank_charts'] = f.getFpsLog(Platform.Android, scene)['jank']
                f.make_android_html(scene=scene, summary=summary_dict)
            case Platform.iOS:
                scene = f.make_report(app=self.pkgName, devices=self.deviceId, 
                                      platform=self.platform, model='normal')
                summary = f._setiOSPerfs(scene)
                summary_dict = {}
                summary_dict['cpu_app'] = summary['cpuAppRate']
                summary_dict['cpu_sys'] = summary['cpuSystemRate']
                summary_dict['mem_total'] = summary['totalPassAvg']
                summary_dict['fps'] = summary['fps']
                summary_dict['current'] = summary['batteryCurrent']
                summary_dict['voltage'] = summary['batteryVoltage']
                summary_dict['power'] = summary['batteryPower']
                summary_dict['tem'] = summary['batteryTeml']
                summary_dict['gpu'] = summary['gpu']
                summary_dict['net_send'] = summary['flow_send']
                summary_dict['net_recv'] = summary['flow_recv']
                summary_dict['cpu_charts'] = f.getCpuLog(Platform.iOS, scene)
                summary_dict['mem_charts'] = f.getMemLog(Platform.iOS, scene)
                summary_dict['net_charts'] = f.getFlowLog(Platform.iOS, scene)
                summary_dict['battery_charts'] = f.getBatteryLog(Platform.iOS, scene)
                summary_dict['fps_charts'] = f.getFpsLog(Platform.iOS, scene)
                summary_dict['gpu_charts'] = f.getGpuLog(Platform.iOS, scene)
                f.make_ios_html(scene=scene, summary=summary_dict)
            case _:
                raise Exception('platfrom is invalid') 

    def collectAll(self):
        try:
            f.clear_file()
            pool = multiprocessing.Pool(processes=6)
            pool.apply_async(self.collectCpu)
            pool.apply_async(self.collectMemory)
            pool.apply_async(self.collectBattery)
            pool.apply_async(self.collectFps)
            pool.apply_async(self.collectFlow)
            pool.apply_async(self.collectGpu)
            pool.close()
            pool.join()
            self.setPerfs()     
        except KeyboardInterrupt:
            self.setPerfs()
        except Exception as e:
            logger.exception(e)
        finally:
            logger.info('End of testing')