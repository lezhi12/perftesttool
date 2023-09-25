from __future__ import absolute_import
import multiprocessing
import datetime
import subprocess
import time
import os
import platform
import re
import webbrowser
import requests
import socket
import sys
from solox.view.apis import api
from solox.view.pages import page
from logzero import logger
from threading import Lock
from flask_socketio import SocketIO, disconnect
from flask import Flask, g, make_response, request
#使用pyinstrument统计性能
from pyinstrument import Profiler
from pyfiglet import Figlet
from solox import __version__
from solox.public.common import Devices, File, Method, Platform
import threading
import queue

f = File()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.register_blueprint(api)
app.register_blueprint(page)

socketio = SocketIO(app, cors_allowed_origins="*",logger=True, engineio_logger=True)
thread = True
thread_lock = Lock()

@app.before_request
def before_request():
    if "profile" in request.args:
        g.profiler = Profiler()
        g.profiler.start()


@app.after_request
def after_request(response):
    if not hasattr(g, "profiler"):
        return response
    g.profiler.stop()
    output_html = g.profiler.output_html()
    return make_response(output_html)

@socketio.on('connect', namespace='/logcat')
def connect():
    socketio.emit('start connect', {'data': 'Connected'}, namespace='/logcat')
    logDir = os.path.join(os.getcwd(),'adblog')
    if not os.path.exists(logDir):
        os.mkdir(logDir)
    global thread
    thread = True
    with thread_lock:
        if thread:
            thread = socketio.start_background_task(target=backgroundThread)


# Function to write data to the disk (asynchronous)
def write_to_disk(queue, file_path,app,device,platform):

    logger.info("begain to write_to_disk")
    with open(os.path.join(file_path,'cpu_app.log'), "a+") as f_app,open(os.path.join(file_path,'cpu_sys.log'), "a+") as f_sys,open(os.path.join(file_path,'mem_total.log'), "a+") as f_mem:
        while True:
            #time.sleep(1)
            data = queue.get()
            if data is None:  
                continue
            #监控结束，可以开始关闭文件了
            elif data[0]=='time to quit':
                break
            apm_time = data[-2]
            apm_time = int(apm_time)
            apm_time = time.localtime(apm_time/1000)
            apm_time = time.strftime("%H:%M:%S",apm_time)
            if data[-1]=="cpu":
                cpu_app = data[0]
                cpu_sys = data[1]
                f_app.write(apm_time + "="+ str(cpu_app) + "\n")
                f_sys.write(apm_time + "="+ str(cpu_sys) + "\n")
            elif data[-1]=="memory":
                mem_total = data[0]
                f_mem.write(apm_time + "="+ str(mem_total) + "\n")
    logger.info("write_to_disk subprocess has been finished!")
    try:
        f.make_report(app=app, devices=device, platform=platform, model="normal")
        #socketio.emit('log_is_ready',namespace='/tidevice')
        #socketio.emit('message', {'data': "log is ready"}, namespace='/tidevice')
    except Exception as e:
            logger.exception(e)
    

# Function to start writing data to the disk asynchronously
def start_async_writer(queue, file_path,app,device,platform):
    print("start_async_writer")
    writer_thread = threading.Thread(target=write_to_disk, args=(queue, file_path,app,device,platform))
    #主线程结束，守护线程立刻结束没有机会关闭文件，因此不要设置为守护线程
    #writer_thread.daemon = True
    writer_thread.start()
    return writer_thread

@socketio.on('start', namespace='/tidevice')
def start_monitor(init_param):
    pkg_name = init_param['pkg']
    device_str = init_param['device']
    platform_str = init_param['platform']
    logger.info("selected pacakge name is  %s"%pkg_name)
    global thread
    thread = True
    with thread_lock:
        if thread:
            thread = socketio.start_background_task(target=tidevice_backgroundThread(pkg_name,device_str,platform_str))

#@socketio.on('connect', namespace='/tidevice')
#def connect():
    #logger.info("param test %s",str(json))  
    #socketio.emit('start connect', {'data': 'Connected'}, namespace='/tidevice')
    #global thread
    #thread = True
    #with thread_lock:
    #    if thread:
    #        thread = socketio.start_background_task(target=tidevice_backgroundThread)

def tidevice_backgroundThread(pkg_name,device,platform):
    global thread
    try:
        #tidevice_cmd = subprocess.Popen("tidevice perf -B com.psbc.youinterbank.ee -o cpu,memory", stdout=subprocess.PIPE,
        #                          shell=True)
        #tidevice_q = queue.Queue()
        cmd_str = "tidevice perf -B %s -o cpu,memory"%(pkg_name)
        tidevice_cmd = subprocess.Popen(cmd_str, stdout=subprocess.PIPE,
                                  shell=True)

        cpu_info_q = queue.Queue()
        writer_log_todisk_thread = start_async_writer(cpu_info_q,f.report_dir,pkg_name,device,platform)
        while thread:
            buff = tidevice_cmd.stdout.readline()
            buff_str = buff.decode()
            time_stamp_re = "'timestamp': \d+"
            time_stamp = re.findall(time_stamp_re,buff_str)
            if isinstance(time_stamp,list) and len(time_stamp)==1:
                time_stamp = time_stamp[0].split(":")[-1].strip()
            else:
                #无效时间戳，丢弃数据
                continue
            cpu_list = re.findall(r'\d+\.+\d*', buff_str)
            cpu_title = re.findall(r'^\S+\s', buff_str)
            cpu_title = cpu_title[0].strip()
            if cpu_title=="cpu" and len(cpu_list)==2:
                cpu_list[0] = round(float(cpu_list[0]), 2)
                cpu_list[1] = round(float(cpu_list[1]), 2)
            elif cpu_title=="memory"and len(cpu_list)==1:
                cpu_list[0] = round(float(cpu_list[0]), 2)
            else:
                continue
            cpu_list.append(time_stamp)
            cpu_list.append(cpu_title)
            #logger.debug("lezhi:buffer")
            #logger.debug(cpu_list)
            #tidevice_q.put(cpu_list)
            #socketio.sleep(0.5)
            #socketio.emit('message', {'data': tidevice_q.get()}, namespace='/tidevice')
            cpu_info_q.put(cpu_list)#入队，等待写入硬盘
            socketio.sleep(0.5)
            #这里要想不出现偶尔卡顿得情况，服务器端需要安装eventlet，否则socket.io网络层默认使用Werkzeug，从F12可以看出来仍然是长轮询，就会卡。
            socketio.emit('message', {'data': cpu_list}, namespace='/tidevice')
            if tidevice_cmd.poll() != None:
                break
    except Exception as e:
        logger.exception(e)
    finally:
        #停止调用tidevice命令行
        logger.info("tidevice_cmd.terminate")
        tidevice_cmd.terminate()
        #队列中插入结束字符串，通知写日志子线程读到这里就可以开始关闭文件了
        logger.info("cpu_info_q.put_time to quit")
        cpu_info_q.put(["time to quit","time to quit"])
def backgroundThread():
    global thread
    try:
        # logger.info('Initializing adb environment ...')
        # os.system('adb kill-server')
        # os.system('adb start-server')
        current_time = time.strftime("%Y%m%d%H", time.localtime())
        logPath = os.path.join(os.getcwd(),'adblog',f'{current_time}.log')
        logcat = subprocess.Popen(f'adb logcat *:E > {logPath}', stdout=subprocess.PIPE,
                                  shell=True)
        with open(logPath, "r") as f:
            while thread:
                socketio.sleep(1)
                for line in f.readlines():
                    socketio.emit('message', {'data': line}, namespace='/logcat')
        if logcat.poll() == 0:
            thread = False
    except Exception:
        pass


@socketio.on('disconnect_request', namespace='/logcat')
def disconnect():
    global thread
    logger.warning('Logcat client disconnected')
    thread = False
    disconnect()

@socketio.on('disconnect_request', namespace='/tidevice')
def disconnect():
    global thread
    logger.warning('Tidevice client disconnected')
    thread = False

def hostIP():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception as e:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def listeningPort(port):
    if platform.system() != 'Windows':
        os.system("lsof -i:%s| grep LISTEN| awk '{print $2}'|xargs kill -9" % port)
    else:
        port_cmd = 'netstat -ano | findstr {}'.format(port)
        r = os.popen(port_cmd)
        r_data_list = r.readlines()
        if len(r_data_list) == 0:
            return
        else:
            pid_list = []
            for line in r_data_list:
                line = line.strip()
                pid = re.findall(r'[1-9]\d*', line)
                pid_list.append(pid[-1])
            pid_set = list(set(pid_list))[0]
            pid_cmd = 'taskkill -PID {} -F'.format(pid_set)
            os.system(pid_cmd)

def getServerStatus(host: str, port: int):
    r = requests.get('http://{}:{}'.format(host, port), timeout=2.0)
    flag = (True, False)[r.status_code == 200]
    return flag


def openUrl(host: str, port: int):
    flag = True
    while flag:
        logger.info('start solox server ...')
        f = Figlet(font="slant", width=300)
        print(f.renderText("SOLOX {}".format(__version__)))
        flag = getServerStatus(host, port)
    webbrowser.open('http://{}:{}/?platform=Android&lan=en'.format(host, port), new=2)
    logger.info('Running on http://{}:{}/?platform=Android&lan=en (Press CTRL+C to quit)'.format(host, port))


def startServer(host: str, port: int):
    socketio.run(app, host=host, debug=False, port=port)

def main(host=hostIP(), port=50003):
    try:
        listeningPort(port=port)
        pool = multiprocessing.Pool(processes=2)
        pool.apply_async(startServer, (host, port))
        pool.apply_async(openUrl, (host, port))
        pool.close()
        pool.join()
    except Exception as e:
        logger.exception(e)
    except KeyboardInterrupt:
        global thread
        thread = False
        logger.info('stop solox success')
        sys.exit()        
