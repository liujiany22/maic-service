"""
数据轮询模块

定期从外部数据源获取数据的轮询器
用户可以自定义数据获取逻辑
"""

import logging
import threading
import time
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class DataPoller:
    """
    数据轮询器
    
    在后台线程中定期执行数据获取任务
    线程安全的数据队列管理
    """
    
    def __init__(self, interval: float = 0.1):
        """
        初始化轮询器
        
        Args:
            interval: 轮询间隔（秒）
        """
        self.interval: float = interval
        self.running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._pending_data: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._fetch_function: Optional[Callable] = None
        
    def start(self) -> None:
        """启动轮询线程"""
        if self.running:
            logger.warning("Poller already running")
            return
            
        self.running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="DataPoller")
        self._thread.start()
        logger.info(f"Data poller started (interval: {self.interval}s)")
        
    def stop(self) -> None:
        """停止轮询线程"""
        if not self.running:
            return
            
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Data poller stopped")
        
    def _poll_loop(self) -> None:
        """
        轮询主循环
        
        在独立线程中执行，捕获所有异常以保证线程稳定性
        """
        while self.running:
            try:
                if self._fetch_function:
                    self._fetch_function()
                else:
                    self._fetch_external_data()
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
                time.sleep(self.interval)
                
    def _fetch_external_data(self) -> None:
        """
        获取外部数据的默认实现（占位符）
        
        用户应该重写此方法或使用 set_fetch_function 设置自定义函数
        
        示例实现：
            def custom_fetch():
                # 从数据库查询
                events = database.get_new_events()
                for event in events:
                    data_poller.add_data(event)
                    
            data_poller.set_fetch_function(custom_fetch)
        """
        pass
        
    def add_data(self, data: Dict[str, Any]) -> None:
        """
        添加数据到待处理队列
        
        Args:
            data: 要添加的数据字典
        """
        with self._lock:
            self._pending_data.append(data)
            logger.debug(f"Added data to queue: {data.get('event', 'unknown')}")
            
    def get_pending_data(self) -> List[Dict[str, Any]]:
        """
        获取所有待处理数据并清空队列
        
        Returns:
            待处理数据列表
        """
        with self._lock:
            data = self._pending_data.copy()
            self._pending_data.clear()
            return data
    
    def set_fetch_function(self, fetch_func: Callable) -> None:
        """
        设置自定义的数据获取函数
        
        Args:
            fetch_func: 无参数的可调用对象
        """
        self._fetch_function = fetch_func
        logger.info("Custom fetch function registered")
