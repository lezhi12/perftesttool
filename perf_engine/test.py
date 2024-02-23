import os  
import threading  
import queue  
  
def execute_command(cmd, output_queue):  
    # 使用 os.popen 执行命令  
    process = os.popen(cmd)  
    output = process.read()  
      
    # 将输出结果放入队列中  
    output_queue.put(output)  
      
    # 关闭进程  
    process.close()  
  
def print_output(output_queue):  
    while True:  
        # 从队列中获取输出结果  
        output = output_queue.get()  
          
        # 如果输出为空，表示子线程已完成  
        if not output:  
            break  
          
        # 打印输出结果  
        print(output)  
  
# 创建命令  
cmd = "pymobiledevice3 remote start-tunnel"  # Windows CMD命令，可以根据需要替换为其他命令  
  
# 创建队列用于同步  
output_queue = queue.Queue()  
  
# 创建并启动子线程  
thread = threading.Thread(target=execute_command, args=(cmd, output_queue))  
thread.start()  
  
# 在主线程中打印输出结果  
print_output(output_queue)  
  
# 等待子线程完成  
thread.join()