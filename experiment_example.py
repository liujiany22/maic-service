"""
EyeLink 实验流程示例

演示完整的实验流程：连接、校准、记录、发送标记、保存
"""

from eyelink_manager import eyelink_manager
import config
import time

def run_experiment():
    """运行完整实验流程"""
    
    print("\n=== EyeLink 实验流程示例 ===\n")
    
    # 1. 连接
    print("1. 连接 EyeLink...")
    success = eyelink_manager.connect(
        host_ip=config.EYELINK_HOST_IP,
        dummy_mode=config.EYELINK_DUMMY_MODE,
        screen_width=config.EYELINK_SCREEN_WIDTH,
        screen_height=config.EYELINK_SCREEN_HEIGHT
    )
    
    if not success:
        print("连接失败")
        return
    
    print("✓ 已连接\n")
    
    # 2. 校准
    print("2. 校准...")
    eyelink_manager.do_calibration(
        config.EYELINK_SCREEN_WIDTH,
        config.EYELINK_SCREEN_HEIGHT
    )
    print("✓ 校准完成\n")
    
    # 3. 验证（可选）
    print("3. 验证...")
    eyelink_manager.do_validation(
        config.EYELINK_SCREEN_WIDTH,
        config.EYELINK_SCREEN_HEIGHT
    )
    print("✓ 验证完成\n")
    
    # 4. 开始记录
    print("4. 开始记录...")
    eyelink_manager.start_recording("test.edf")
    print("✓ 记录已开始\n")
    
    # 5. 实验进行中 - 发送标记
    print("5. 实验进行中（发送标记）...")
    
    # Block 开始
    eyelink_manager.send_message("BLOCK_START")
    print("  - Block 开始")
    
    # Trial 1
    eyelink_manager.send_message("TRIAL_1_START")
    print("  - Trial 1 开始")
    time.sleep(0.5)
    
    eyelink_manager.send_message("STIMULUS_ONSET")
    print("  - 刺激呈现")
    time.sleep(1.0)
    
    eyelink_manager.send_message("RESPONSE_CORRECT")
    print("  - 被试反应")
    
    eyelink_manager.send_message("TRIAL_1_END")
    print("  - Trial 1 结束")
    
    # Trial 2
    eyelink_manager.send_message("TRIAL_2_START")
    print("  - Trial 2 开始")
    time.sleep(0.5)
    
    eyelink_manager.send_message("STIMULUS_ONSET")
    print("  - 刺激呈现")
    time.sleep(1.0)
    
    eyelink_manager.send_message("RESPONSE_INCORRECT")
    print("  - 被试反应")
    
    eyelink_manager.send_message("TRIAL_2_END")
    print("  - Trial 2 结束")
    
    # Block 结束
    eyelink_manager.send_message("BLOCK_END")
    print("  - Block 结束\n")
    
    # 6. 停止记录并保存
    print("6. 停止记录并保存...")
    save_dir = config.LOG_DIR / "eyelink_data"
    eyelink_manager.stop_recording(save_local=True, local_dir=str(save_dir))
    print(f"✓ 文件已保存到: {save_dir}\n")
    
    # 7. 断开连接
    print("7. 断开连接...")
    eyelink_manager.disconnect()
    print("✓ 已断开\n")
    
    print("=== 实验完成 ===\n")


if __name__ == "__main__":
    run_experiment()

