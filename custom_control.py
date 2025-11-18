"""
自定义 EyeLink 控制模块

提供简单的实验流程控制
"""

import logging
import threading

from eyelink_manager import eyelink_manager, EYELINK_AVAILABLE
import config

logger = logging.getLogger(__name__)

# 检查 pygame 是否可用
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.warning("pygame 不可用，图形界面功能将被禁用")


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
        print("校准:   c=校准 v=验证 d=漂移校正")
        print("录制:   start=开始录制 (EDF + 屏幕)")
        print("        end=结束录制 (保存 + Overlay)")
        print("其他:   marker <text>=发送标记")
        print("        status=状态 quit=退出")
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
                
                # 打开 EyeLink 设置界面（校准/验证/漂移校正）
                if action in {"c", "v", "d"}:
                    if not PYGAME_AVAILABLE:
                        print("错误: pygame 未安装")
                        continue
                    eyelink_manager.open_setup()
                
                # 开始记录（EDF + 屏幕）
                elif action == "start":
                    if experiment_running:
                        print("实验已在运行")
                        continue
                    
                    # 启动 EyeLink 记录和屏幕录制
                    success, timestamp = eyelink_manager.start_recording(enable_screen_recording=True)
                    if success:
                        experiment_running = True
                        print(f"✓ EyeLink + 屏幕录制已开始 ({timestamp})")
                
                # 结束记录（停止录制 + 保存 + Overlay）
                elif action == "end":
                    if not experiment_running:
                        print("实验未运行")
                        continue
                    
                    print("停止录制并处理数据...")
                    
                    # 保存到本地（自动停止屏幕录制并 overlay）
                    save_dir = config.LOG_DIR / "eyelink_data"
                    success = eyelink_manager.stop_recording(
                        save_local=True,
                        local_dir=str(save_dir)
                    )
                    
                    if success:
                        experiment_running = False
                        print(f"✓ 记录已停止")
                        print(f"✓ 文件保存在: {save_dir}")
                    else:
                        print("✗ 停止记录失败")
                
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
                    print(f"录制中: {status.recording}")
                    if status.recording:
                        print(f"会话ID: {eyelink_manager.current_timestamp}")
                
                # 退出
                elif action == "quit":
                    if experiment_running:
                        confirm = input("录制运行中，确认退出? (y/n): ")
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
        
        # 清理图形界面
        try:
            if EYELINK_AVAILABLE:
                import pylink
                pylink.closeGraphics()
            if PYGAME_AVAILABLE:
                pygame.quit()
            logger.info("图形界面已关闭")
        except Exception as e:
            logger.error(f"关闭图形界面时出错: {e}")
    
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
