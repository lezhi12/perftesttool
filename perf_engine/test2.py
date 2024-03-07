import asyncio  
import threading  
  
# 用于线程间通信的队列  
queue = asyncio.Queue()  
  
# 异步方法，每隔3秒向队列发送信号  
async def async_method_A():  
    print("Async Method A is running in a separate thread.")  
    while True:  
        # 向队列发送信号  
        await queue.put("helloworld")  
        print("Signal sent to main thread.")  
        # 等待3秒  
        await asyncio.sleep(3)  
  
# 子线程中运行异步方法的函数  
def run_async_in_thread():  
    loop = asyncio.new_event_loop()  
    asyncio.set_event_loop(loop)  
    try:  
        loop.run_until_complete(async_method_A())  
    except KeyboardInterrupt:  
        pass  
    finally:  
        loop.close()  
  
# 主线程中的函数，从队列中接收信号并打印"Hello, World!"  
async def main_thread():  
    # 创建子线程  
    thread = threading.Thread(target=run_async_in_thread)  
    thread.start()  
  
    # 在主线程中运行事件循环  
    while True:
        # 从队列中接收信号  
        await queue.get()  
        # 打印"Hello, World!"  
        print("hello")  
        # 任务完成，标记为已完成  
        queue.task_done()

  
# 运行主线程的事件循环  
if __name__ == "__main__":  
    asyncio.run(main_thread())