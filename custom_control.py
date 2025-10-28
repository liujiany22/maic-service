"""
自定义 EyeLink 控制模块

提供简单的实验流程控制
"""

import logging
import threading
from typing import Optional

from eyelink_manager import eyelink_manager, EYELINK_AVAILABLE
from eyelink_graphics import PYGAME_AVAILABLE
import config

logger = logging.getLogger(__name__)


# ==================== 实验流程控制 ====================

def start_experiment_control():
    """
    实验控制主函数
    
    命令：
    - c: 校准
    - v: 验证
    - d: 漂移校正
    - start: 开始记录
    - end: 结束记录并保存
    - marker <text>: 发送标记
    - status: 查看状态
    - quit: 退出
    """
    
    def control_loop():
        experiment_running = False
        
        print("\n" + "=" * 50)
        print("EyeLink 实验控制")
        print("=" * 50)
        print("命令: connect=连接 c=校准 v=验证 d=漂移校正")
        print("      start=开始记录 end=结束记录")
        print("      marker <text>=发送标记")
        print("      status=状态 quit=退出")
        print("=" * 50 + "\n")
        
        # 自动连接
        if config.EYELINK_AUTO_CONNECT and EYELINK_AVAILABLE:
            logger.info("自动连接 EyeLink...")
            success = eyelink_manager.connect(
                host_ip=config.EYELINK_HOST_IP,
                dummy_mode=config.EYELINK_DUMMY_MODE,
                screen_width=config.EYELINK_SCREEN_WIDTH,
                screen_height=config.EYELINK_SCREEN_HEIGHT
            )
            if success:
                print("✓ 已连接\n")
            else:
                print("✗ 连接失败\n")
        
        while True:
            try:
                cmd = input("> ").strip()
                if not cmd:
                    continue
                
                parts = cmd.split(maxsplit=1)
                action = parts[0].lower()
                
                # 连接
                if action == "connect":
                    if not EYELINK_AVAILABLE:
                        print("错误: PyLink 未安装")
                        continue
                    success = eyelink_manager.connect(
                        host_ip=config.EYELINK_HOST_IP,
                        dummy_mode=config.EYELINK_DUMMY_MODE,
                        screen_width=config.EYELINK_SCREEN_WIDTH,
                        screen_height=config.EYELINK_SCREEN_HEIGHT
                    )
                    if success:
                        print("✓ 已连接")
                    else:
                        print("✗ 连接失败")
                
                # 校准
                elif action == "c":
                    if not PYGAME_AVAILABLE:
                        print("错误: pygame 未安装")
                        continue
                    eyelink_manager.do_calibration(
                        config.EYELINK_SCREEN_WIDTH,
                        config.EYELINK_SCREEN_HEIGHT
                    )
                
                # 验证
                elif action == "v":
                    if not PYGAME_AVAILABLE:
                        print("错误: pygame 未安装")
                        continue
                    eyelink_manager.do_validation(
                        config.EYELINK_SCREEN_WIDTH,
                        config.EYELINK_SCREEN_HEIGHT
                    )
                
                # 漂移校正
                elif action == "d":
                    if not PYGAME_AVAILABLE:
                        print("错误: pygame 未安装")
                        continue
                    eyelink_manager.do_drift_correct(
                        width=config.EYELINK_SCREEN_WIDTH,
                        height=config.EYELINK_SCREEN_HEIGHT
                    )
                
                # 开始记录
                elif action == "start":
                    if experiment_running:
                        print("实验已在运行")
                        continue
                    
                    success = eyelink_manager.start_recording("test.edf")
                    if success:
                        experiment_running = True
                        print("✓ 记录已开始")
                
                # 结束记录
                elif action == "end":
                    if not experiment_running:
                        print("实验未运行")
                        continue
                    
                    # 保存到本地
                    save_dir = config.LOG_DIR / "eyelink_data"
                    success = eyelink_manager.stop_recording(
                        save_local=True,
                        local_dir=str(save_dir)
                    )
                    
                    if success:
                        experiment_running = False
                        print(f"✓ 记录已停止，文件保存在: {save_dir}")
                
                # 发送标记
                elif action == "marker":
                    if len(parts) < 2:
                        print("用法: marker <消息>")
                        continue
                    
                    message = parts[1]
                    if eyelink_manager.send_message(message):
                        print(f"✓ 标记已发送: {message}")
                    else:
                        print("发送失败")
                
                # 状态
                elif action == "status":
                    status = eyelink_manager.get_status()
                    print(f"连接: {status.connected}")
                    print(f"记录: {status.recording}")
                    print(f"文件: {status.edf_file or 'N/A'}")
                
                # 退出
                elif action == "quit":
                    if experiment_running:
                        confirm = input("实验运行中，确认退出? (y/n): ")
                        if confirm.lower() != 'y':
                            continue
                    print("退出")
                    break
                
                else:
                    print(f"未知命令: {action}")
            
            except (EOFError, KeyboardInterrupt):
                print("\n中断")
                break
            except Exception as e:
                logger.error(f"错误: {e}")
        
        # 清理
        from eyelink_graphics import close_graphics
        close_graphics()
    
    # 后台线程运行
    thread = threading.Thread(target=control_loop, daemon=True)
    thread.start()


def handle_control_message(event_name: str, data: dict) -> bool:
    """
    处理来自 MAIC 的特殊控制消息
    
    返回 True 表示已处理，不再发送标准标记
    """
    # 这里可以添加特殊事件处理
    # 例如：
    # if event_name == "START_RECORDING":
    #     eyelink_manager.start_recording()
    #     return True
    
    return False


def initialize_custom_control():
    """初始化自定义控制"""
    logger.info("初始化实验控制")
    start_experiment_control()
