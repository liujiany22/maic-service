"""
自定义 EyeLink 控制模块

这个文件是为用户提供的自定义区域，可以在这里编写自己的 EyeLink 控制逻辑。
不用担心影响主程序，这里的代码完全由你控制。

使用场景：
1. 键盘输入控制 EyeLink
2. 通过网络消息控制 EyeLink
3. 基于定时器的自动控制
4. 响应外部事件
"""

import logging
import threading
from typing import Optional

# 导入 EyeLink 管理器
from eyelink_manager import eyelink_manager, EYELINK_AVAILABLE

# 导入图形界面支持
from eyelink_graphics import (
    setup_graphics, 
    close_graphics, 
    do_tracker_setup, 
    do_drift_correct,
    PYGAME_AVAILABLE, 
    PYLINK_AVAILABLE
)

logger = logging.getLogger(__name__)


# ============================================================
# 示例 1: 简单的键盘控制
# ============================================================

def keyboard_control_example():
    """
    示例：通过键盘输入控制 EyeLink
    
    取消注释下面的代码来启用这个功能
    """
    
    # def input_loop():
    #     """键盘输入循环"""
    #     logger.info("=" * 60)
    #     logger.info("键盘控制已启动")
    #     logger.info("=" * 60)
    #     logger.info("可用命令:")
    #     logger.info("  start      - 开始记录")
    #     logger.info("  stop       - 停止记录")
    #     logger.info("  calibrate  - 校准（需要图形界面）")
    #     logger.info("  drift      - 漂移校正")
    #     logger.info("  status     - 查看状态")
    #     logger.info("  marker     - 发送测试标记")
    #     logger.info("  quit       - 退出控制")
    #     logger.info("=" * 60)
    #     
    #     while True:
    #         try:
    #             cmd = input("\nEyeLink > ").strip().lower()
    #             
    #             if cmd == "start":
    #                 if not EYELINK_AVAILABLE:
    #                     logger.error("❌ PyLink 不可用")
    #                     continue
    #                 success = eyelink_manager.start_recording()
    #                 if success:
    #                     logger.info("✅ 记录已开始")
    #                 else:
    #                     logger.error("❌ 开始记录失败")
    #             
    #             elif cmd == "stop":
    #                 success = eyelink_manager.stop_recording()
    #                 if success:
    #                     logger.info("✅ 记录已停止")
    #                 else:
    #                     logger.error("❌ 停止记录失败")
    #             
    #             elif cmd == "calibrate":
    #                 if eyelink_manager.tracker:
    #                     logger.info("开始校准...")
    #                     logger.warning("⚠️  校准需要图形界面支持")
    #                     logger.info("请参考 EyeLink 文档中的 doTrackerSetup() 方法")
    #                     # 实际使用时取消注释:
    #                     # eyelink_manager.tracker.doTrackerSetup()
    #                 else:
    #                     logger.error("❌ EyeLink 未连接")
    #             
    #             elif cmd == "drift":
    #                 if eyelink_manager.tracker:
    #                     logger.info("漂移校正...")
    #                     logger.warning("⚠️  漂移校正需要图形界面支持")
    #                     # 实际使用时取消注释:
    #                     # eyelink_manager.tracker.doDriftCorrect()
    #                 else:
    #                     logger.error("❌ EyeLink 未连接")
    #             
    #             elif cmd == "status":
    #                 status = eyelink_manager.get_status()
    #                 logger.info("=" * 40)
    #                 logger.info(f"状态: {status.status.value}")
    #                 logger.info(f"已连接: {status.connected}")
    #                 logger.info(f"正在记录: {status.recording}")
    #                 if status.edf_file:
    #                     logger.info(f"EDF 文件: {status.edf_file}")
    #                 logger.info("=" * 40)
    #             
    #             elif cmd == "marker":
    #                 from models import EyeLinkMarker, MarkerType
    #                 from datetime import datetime, timezone
    #                 
    #                 marker = EyeLinkMarker(
    #                     marker_type=MarkerType.MESSAGE,
    #                     message="TEST_MARKER",
    #                     timestamp=datetime.now(timezone.utc)
    #                 )
    #                 success = eyelink_manager.send_marker(marker)
    #                 if success:
    #                     logger.info("✅ 标记已发送")
    #                 else:
    #                     logger.error("❌ 发送标记失败")
    #             
    #             elif cmd == "quit":
    #                 logger.info("退出键盘控制")
    #                 break
    #             
    #             elif cmd == "help":
    #                 logger.info("可用命令: start, stop, calibrate, drift, status, marker, quit")
    #             
    #             else:
    #                 logger.warning(f"未知命令: {cmd}，输入 'help' 查看帮助")
    #         
    #         except (EOFError, KeyboardInterrupt):
    #             logger.info("键盘控制被中断")
    #             break
    #         except Exception as e:
    #             logger.error(f"错误: {e}")
    # 
    # # 在后台线程启动
    # control_thread = threading.Thread(target=input_loop, daemon=True)
    # control_thread.start()
    # logger.info("键盘控制线程已启动")
    
    pass  # 如果不启用，保持 pass


# ============================================================
# 示例 2: 处理来自 MAIC 平台的特殊控制消息
# ============================================================

def handle_control_message(event_name: str, data: dict) -> bool:
    """
    处理来自 MAIC 平台的控制消息
    
    这个函数会在接收到特定事件时被调用。
    你可以在 main.py 的 send_eyelink_marker 函数中调用这个函数。
    
    Args:
        event_name: 事件名称
        data: 事件数据
        
    Returns:
        True 表示已处理该消息（不再发送标准标记）
        False 表示未处理（继续发送标准标记）
    
    示例用法（在 main.py 的 send_eyelink_marker 中）：
    ```python
    from custom_control import handle_control_message
    
    # 在处理事件之前调用
    if handle_control_message(event, data):
        return  # 已处理，不发送标准标记
    ```
    """
    
    # 示例：响应特定的控制事件（取消注释以启用）
    
    # if event_name == "EYELINK_START_RECORDING":
    #     logger.info("收到开始记录命令")
    #     eyelink_manager.start_recording()
    #     return True
    # 
    # elif event_name == "EYELINK_STOP_RECORDING":
    #     logger.info("收到停止记录命令")
    #     eyelink_manager.stop_recording()
    #     return True
    # 
    # elif event_name == "EYELINK_CALIBRATE":
    #     logger.info("收到校准命令")
    #     if eyelink_manager.tracker:
    #         logger.warning("⚠️  校准需要图形界面")
    #         # eyelink_manager.tracker.doTrackerSetup()
    #     return True
    # 
    # elif event_name == "EYELINK_DRIFT_CORRECT":
    #     logger.info("收到漂移校正命令")
    #     if eyelink_manager.tracker:
    #         logger.warning("⚠️  漂移校正需要图形界面")
    #         # eyelink_manager.tracker.doDriftCorrect()
    #     return True
    # 
    # elif event_name.startswith("CUSTOM_"):
    #     # 处理自定义命令
    #     logger.info(f"处理自定义命令: {event_name}")
    #     logger.info(f"数据: {data}")
    #     # 在这里添加你的自定义逻辑
    #     return True
    
    return False  # 未处理，继续标准流程


# ============================================================
# 示例 3: 定时任务
# ============================================================

def start_periodic_task():
    """
    示例：启动周期性任务
    
    可以用于定期检查状态、自动保存等
    """
    
    # import time
    # 
    # def periodic_check():
    #     """周期性检查任务"""
    #     while True:
    #         try:
    #             time.sleep(60)  # 每 60 秒执行一次
    #             
    #             status = eyelink_manager.get_status()
    #             if status.recording:
    #                 logger.info(f"EyeLink 正在记录: {status.edf_file}")
    #             else:
    #                 logger.debug("EyeLink 未在记录")
    #         
    #         except Exception as e:
    #             logger.error(f"周期性任务错误: {e}")
    # 
    # # 启动后台线程
    # task_thread = threading.Thread(target=periodic_check, daemon=True)
    # task_thread.start()
    # logger.info("周期性任务已启动")
    
    pass


# ============================================================
# 主入口函数
# ============================================================

def initialize_custom_control():
    """
    初始化自定义控制
    
    这个函数会在服务启动时被调用。
    在这里启动你需要的控制功能。
    """
    
    logger.info("初始化自定义控制模块...")
    
    # 启动实验控制
    start_experiment_control()
    
    logger.info("自定义控制模块初始化完成")


# ============================================================
# 工具函数
# ============================================================

def get_eyelink_tracker():
    """
    获取 EyeLink tracker 对象
    
    Returns:
        PyLink tracker 对象，如果未连接则返回 None
        
    示例用法：
    ```python
    tracker = get_eyelink_tracker()
    if tracker:
        # 直接调用 PyLink API
        tracker.sendMessage("MY_CUSTOM_MESSAGE")
        tracker.sendCommand("record_status_message 'My Status'")
    ```
    """
    return eyelink_manager.tracker if EYELINK_AVAILABLE else None


def quick_marker(message: str) -> bool:
    """
    快速发送标记的便捷函数
    
    Args:
        message: 标记消息
        
    Returns:
        成功返回 True
        
    示例用法：
    ```python
    quick_marker("TRIAL_START")
    quick_marker("STIMULUS_ONSET")
    ```
    """
    from models import EyeLinkMarker, MarkerType
    from datetime import datetime, timezone
    
    marker = EyeLinkMarker(
        marker_type=MarkerType.MESSAGE,
        message=message,
        timestamp=datetime.now(timezone.utc)
    )
    return eyelink_manager.send_marker(marker)


# ============================================================
# 你的自定义代码区域
# ============================================================

# 实验控制函数
def start_experiment_control():
    """
    实验控制主函数
    
    命令：
    - c: 开始校准
    - v: 开始验证
    - start: 开始记录并进入实验
    - end: 结束记录并保存文件
    - status: 查看状态
    - quit: 退出
    """
    
    def experiment_loop():
        """实验控制循环"""
        import os
        from pathlib import Path
        from datetime import datetime
        
        # 实验状态
        experiment_running = False
        
        logger.info("=" * 60)
        logger.info("实验控制已启动")
        logger.info("=" * 60)
        logger.info("可用命令:")
        logger.info("  c      - 开始校准 (Calibration)")
        logger.info("  v      - 开始验证 (Validation)")
        logger.info("  start  - 开始记录并进入实验")
        logger.info("  end    - 结束记录并保存文件")
        logger.info("  status - 查看状态")
        logger.info("  quit   - 退出")
        logger.info("=" * 60)
        
        while True:
            try:
                cmd = input("\n实验控制 > ").strip().lower()
                
                # 校准
                if cmd == "c":
                    logger.info("开始校准...")
                    tracker = get_eyelink_tracker()
                    
                    if not tracker:
                        logger.error("❌ EyeLink 未连接")
                        continue
                    
                    if not PYGAME_AVAILABLE:
                        logger.error("❌ pygame 不可用，无法进行校准")
                        logger.info("请安装 pygame: pip install pygame")
                        continue
                    
                    try:
                        # 获取屏幕尺寸
                        import config
                        width = config.EYELINK_SCREEN_WIDTH
                        height = config.EYELINK_SCREEN_HEIGHT
                        
                        logger.info(f"正在进入校准模式... (屏幕: {width}x{height})")
                        
                        # 调用校准
                        success = do_tracker_setup(tracker, width, height)
                        
                        if success:
                            logger.info("✅ 校准完成")
                        else:
                            logger.error("❌ 校准失败")
                        
                    except Exception as e:
                        logger.error(f"校准过程出错: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 验证
                elif cmd == "v":
                    logger.info("开始验证...")
                    tracker = get_eyelink_tracker()
                    
                    if not tracker:
                        logger.error("❌ EyeLink 未连接")
                        continue
                    
                    if not PYGAME_AVAILABLE:
                        logger.error("❌ pygame 不可用，无法进行验证")
                        logger.info("请安装 pygame: pip install pygame")
                        continue
                    
                    try:
                        # 获取屏幕尺寸
                        import config
                        width = config.EYELINK_SCREEN_WIDTH
                        height = config.EYELINK_SCREEN_HEIGHT
                        
                        logger.info(f"正在进入验证模式... (屏幕: {width}x{height})")
                        
                        # 验证实际上就是再次调用 doTrackerSetup
                        # 在 setup 界面中可以选择 validate
                        success = do_tracker_setup(tracker, width, height)
                        
                        if success:
                            logger.info("✅ 验证完成")
                        else:
                            logger.error("❌ 验证失败")
                        
                    except Exception as e:
                        logger.error(f"验证过程出错: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 开始实验
                elif cmd == "start":
                    if experiment_running:
                        logger.warning("⚠️  实验已在运行中")
                        continue
                    
                    logger.info("开始记录并进入实验...")
                    
                    # 开始记录
                    success = eyelink_manager.start_recording("test1028.edfs")
                    
                    if success:
                        experiment_running = True
                        logger.info("✅ 记录已开始")
                        logger.info("✅ 实验已开始")
                        logger.info("💡 校准/验证界面已关闭，实验正在进行中...")
                        logger.info("💡 输入 'end' 来结束实验")
                        
                        # 发送实验开始标记
                        quick_marker("EXPERIMENT_START")
                        
                        # 如果有图形界面，关闭校准窗口
                        tracker = get_eyelink_tracker()
                        if tracker:
                            try:
                                # 退出 setup 模式（如果在 setup 中）
                                tracker.exitCalibration()
                            except:
                                pass  # 如果不在 setup 模式，会报错，忽略即可
                    else:
                        logger.error("❌ 开始记录失败")
                
                # 结束实验
                elif cmd == "end":
                    if not experiment_running:
                        logger.warning("⚠️  实验未在运行")
                        # 但仍然尝试停止记录（如果有的话）
                        if eyelink_manager.get_status().recording:
                            logger.info("检测到正在记录，尝试停止...")
                        else:
                            continue
                    
                    logger.info("结束实验并保存文件...")
                    
                    # 发送实验结束标记
                    quick_marker("EXPERIMENT_END")
                    
                    # 停止记录
                    success = eyelink_manager.stop_recording()
                    
                    if success:
                        experiment_running = False
                        logger.info("✅ 记录已停止")
                        logger.info("✅ 实验已结束")
                        
                        # 保存文件到本地
                        logger.info("正在保存 EDF 文件到本地...")
                        
                        # 创建保存目录
                        import config
                        save_dir = config.LOG_DIR / "eyelink_data"
                        save_dir.mkdir(parents=True, exist_ok=True)
                        
                        # 生成文件名
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        edf_filename = f"experiment_{timestamp}.edf"
                        local_path = save_dir / edf_filename
                        
                        logger.info(f"保存路径: {local_path}")
                        
                        # 注意：实际的文件传输需要根据 EyeLink 配置
                        # 这里提供手动传输指导
                        logger.info("=" * 60)
                        logger.info("EDF 文件保存指导:")
                        logger.info("=" * 60)
                        logger.info("1. 在 EyeLink 主机上找到 EDF 文件")
                        logger.info(f"   文件名: {eyelink_manager.edf_file or config.EYELINK_EDF_FILENAME}")
                        logger.info("   位置: EyeLink 主机工作目录")
                        logger.info("")
                        logger.info("2. 通过以下方式传输到本地:")
                        logger.info("   - USB 存储设备")
                        logger.info("   - 网络共享")
                        logger.info("   - FTP/SFTP")
                        logger.info("")
                        logger.info(f"3. 保存到: {local_path}")
                        logger.info("=" * 60)
                        
                        # 创建占位符文件
                        placeholder_content = f"""# EyeLink EDF 文件占位符

实验完成时间: {datetime.now().isoformat()}
源文件名: {eyelink_manager.edf_file or config.EYELINK_EDF_FILENAME}
目标路径: {local_path}

请将 EDF 文件从 EyeLink 主机传输到此位置。
传输完成后，请删除此占位符文件。

传输方法:
1. USB 存储设备
2. 网络共享文件夹
3. FTP/SFTP 传输
4. EyeLink Data Viewer 软件
"""
                        
                        placeholder_path = str(local_path) + ".placeholder.txt"
                        with open(placeholder_path, 'w', encoding='utf-8') as f:
                            f.write(placeholder_content)
                        
                        logger.info(f"✅ 占位符文件已创建: {placeholder_path}")
                        logger.info("✅ 实验数据保存流程完成")
                    else:
                        logger.error("❌ 停止记录失败")
                
                # 查看状态
                elif cmd == "status":
                    status = eyelink_manager.get_status()
                    logger.info("=" * 40)
                    logger.info(f"EyeLink 状态: {status.status.value}")
                    logger.info(f"已连接: {status.connected}")
                    logger.info(f"正在记录: {status.recording}")
                    logger.info(f"实验运行中: {experiment_running}")
                    if status.edf_file:
                        logger.info(f"EDF 文件: {status.edf_file}")
                    logger.info("=" * 40)
                
                # 退出
                elif cmd == "quit":
                    if experiment_running:
                        logger.warning("⚠️  实验正在运行，请先输入 'end' 结束实验")
                        confirm = input("确认退出？(y/n): ").strip().lower()
                        if confirm != 'y':
                            continue
                    
                    logger.info("退出实验控制")
                    break
                
                # 帮助
                elif cmd == "help" or cmd == "h":
                    logger.info("可用命令:")
                    logger.info("  c      - 开始校准")
                    logger.info("  v      - 开始验证")
                    logger.info("  start  - 开始记录并进入实验")
                    logger.info("  end    - 结束记录并保存文件")
                    logger.info("  status - 查看状态")
                    logger.info("  quit   - 退出")
                
                else:
                    logger.warning(f"未知命令: {cmd}，输入 'help' 查看帮助")
            
            except (EOFError, KeyboardInterrupt):
                logger.info("\n实验控制被中断")
                break
            except Exception as e:
                logger.error(f"错误: {e}")
                import traceback
                traceback.print_exc()
        
        # 退出时清理
        logger.info("清理图形界面...")
        close_graphics()
    
    # 在后台线程启动
    control_thread = threading.Thread(target=experiment_loop, daemon=True)
    control_thread.start()
    logger.info("实验控制线程已启动")


