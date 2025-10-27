#!/usr/bin/env python3
"""
EyeLink 连接调试脚本

用于独立测试 EyeLink 连接，不需要启动完整的 FastAPI 服务。
此脚本会输出详细的调试信息，帮助排查连接问题。

使用方法:
    python debug_eyelink.py                    # 使用默认配置
    python debug_eyelink.py --dummy            # 使用虚拟模式
    python debug_eyelink.py --host 192.168.1.1 # 指定主机 IP

"""

import sys
import argparse
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# 导入 EyeLink 管理器
try:
    from eyelink_manager import eyelink_manager, EYELINK_AVAILABLE, EyeLinkStatus
    from models import MarkerType, EyeLinkMarker
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    logger.error("请确保在项目目录中运行此脚本")
    sys.exit(1)


def test_connection(host_ip: str, dummy_mode: bool, screen_width: int, screen_height: int):
    """测试 EyeLink 连接"""
    
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  EyeLink 连接调试工具".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")
    
    # 步骤 1: 检查 PyLink 可用性
    logger.info("步骤 1/5: 检查 PyLink 可用性")
    if not EYELINK_AVAILABLE:
        logger.error("❌ PyLink 不可用!")
        logger.error("请按照以下步骤操作:")
        logger.error("1. 从 SR Research 网站下载 EyeLink Developers Kit")
        logger.error("2. 安装 SDK")
        logger.error("3. 确保 Python 能找到 pylink 模块")
        logger.error("4. 测试: python -c 'import pylink; print(pylink)'")
        return False
    
    logger.info("✓ PyLink 可用")
    print()
    
    # 步骤 2: 显示连接参数
    logger.info("步骤 2/5: 连接参数")
    logger.info(f"  主机 IP: {host_ip}")
    logger.info(f"  虚拟模式: {dummy_mode}")
    logger.info(f"  屏幕尺寸: {screen_width} x {screen_height}")
    print()
    
    # 如果是真实模式，提示网络检查
    if not dummy_mode:
        logger.warning("⚠️  正在使用真实模式，请确保:")
        logger.warning("  1. EyeLink 主机已开机")
        logger.warning("  2. 网络线缆已连接")
        logger.warning("  3. 能够 ping 通主机:")
        logger.warning(f"     ping {host_ip}")
        print()
        input("准备好后，按 Enter 继续...")
        print()
    
    # 步骤 3: 尝试连接
    logger.info("步骤 3/5: 尝试连接 EyeLink")
    success = eyelink_manager.connect(
        host_ip=host_ip,
        dummy_mode=dummy_mode,
        screen_width=screen_width,
        screen_height=screen_height
    )
    
    if not success:
        logger.error("❌ 连接失败")
        status = eyelink_manager.get_status()
        logger.error(f"状态: {status.status.value}")
        logger.error(f"错误: {status.error_message}")
        return False
    
    logger.info("✓ 连接成功")
    print()
    
    # 步骤 4: 测试发送标记
    logger.info("步骤 4/5: 测试发送标记")
    
    test_markers = [
        EyeLinkMarker(
            marker_type=MarkerType.MESSAGE,
            message="DEBUG_TEST_START"
        ),
        EyeLinkMarker(
            marker_type=MarkerType.TRIAL_START,
            trial_id="DEBUG_TRIAL_001",
            message="Debug trial"
        ),
        EyeLinkMarker(
            marker_type=MarkerType.CUSTOM,
            message="CUSTOM_EVENT test_value",
            additional_data={"test_var": "test_value", "timestamp": "12345"}
        )
    ]
    
    for i, marker in enumerate(test_markers, 1):
        logger.info(f"  发送测试标记 {i}/{len(test_markers)}: {marker.marker_type.value}")
        success = eyelink_manager.send_marker(marker)
        if not success:
            logger.warning(f"  ⚠️  标记 {i} 发送失败")
        else:
            logger.info(f"  ✓ 标记 {i} 发送成功")
    
    print()
    
    # 步骤 5: 断开连接
    logger.info("步骤 5/5: 断开连接")
    eyelink_manager.disconnect()
    
    status = eyelink_manager.get_status()
    if status.status == EyeLinkStatus.DISCONNECTED:
        logger.info("✓ 已断开连接")
    else:
        logger.warning(f"⚠️  状态异常: {status.status.value}")
    
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + "  测试完成!".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="EyeLink 连接调试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python debug_eyelink.py                      # 使用默认配置
  python debug_eyelink.py --dummy              # 虚拟模式
  python debug_eyelink.py --host 192.168.1.1   # 指定 IP
  python debug_eyelink.py --host 100.1.1.1 --width 1920 --height 1080
        """
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="100.1.1.1",
        help="EyeLink 主机 IP 地址 (默认: 100.1.1.1)"
    )
    
    parser.add_argument(
        "--dummy",
        action="store_true",
        help="使用虚拟模式（不连接真实硬件）"
    )
    
    parser.add_argument(
        "--width",
        type=int,
        default=1920,
        help="屏幕宽度（像素，默认: 1920）"
    )
    
    parser.add_argument(
        "--height",
        type=int,
        default=1080,
        help="屏幕高度（像素，默认: 1080）"
    )
    
    args = parser.parse_args()
    
    # 运行测试
    try:
        success = test_connection(
            host_ip=args.host,
            dummy_mode=args.dummy,
            screen_width=args.width,
            screen_height=args.height
        )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
        eyelink_manager.disconnect()
        sys.exit(130)
    except Exception as e:
        logger.exception(f"未预期的错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

