import threading  
import time  
  
# 定义全局的Thread对象  
thread = None  
  
# 子线程的工作函数  
def worker():  
    global thread  
    # 模拟一些工作  
    time.sleep(2)  
    print("子线程工作完成")  
  
# 在主线程中创建Thread对象  
thread = threading.Thread(target=worker)  
  
# 启动子线程  
thread.start()  
  
# 在子线程开始执行后打印信息  
print("子线程已开始执行")  
  
# 等待子线程结束  
thread.join()  
  
# 子线程结束后打印信息  
print("子线程已结束执行")