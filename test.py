#!/usr/bin/env python3
"""
MAIC 服务测试脚本
跨平台兼容的测试工具
"""

import os
import sys
import platform
from pathlib import Path


def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        import config
        print("✓ config")
        
        import models
        print("✓ models")
        
        import utils
        print("✓ utils")
        
        import eyelink_manager
        print(f"✓ eyelink_manager (PyLink: {eyelink_manager.EYELINK_AVAILABLE})")
        
        import main
        print("✓ main")
        
        print("✅ 所有模块导入成功")
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_config():
    """测试配置"""
    print("\n测试配置...")
    
    try:
        import config
        
        print(f"  应用: {config.APP_NAME}")
        print(f"  端口: {config.PORT}")
        print(f"  EyeLink IP: {config.EYELINK_HOST_IP}")
        print(f"  虚拟模式: {config.EYELINK_DUMMY_MODE}")
        print(f"  自动连接: {config.EYELINK_AUTO_CONNECT}")
        
        print("✓ 配置正常")
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False


def test_models():
    """测试数据模型"""
    print("\n测试数据模型...")
    
    try:
        from models import EyeLinkMarker, MarkerType
        
        marker = EyeLinkMarker(
            marker_type=MarkerType.MESSAGE,
            message="测试标记",
            trial_id="test_001"
        )
        
        print(f"  创建标记: {marker.message}")
        print("✓ 数据模型正常")
        return True
        
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False


def test_eyelink_manager():
    """测试 EyeLink 管理器"""
    print("\n测试 EyeLink 管理器...")
    
    try:
        from eyelink_manager import eyelink_manager
        
        status = eyelink_manager.get_status()
        print(f"  状态: {status.status.value}")
        print(f"  已连接: {status.connected}")
        print("✓ EyeLink 管理器正常")
        return True
        
    except Exception as e:
        print(f"❌ EyeLink 管理器测试失败: {e}")
        return False


def test_env_file():
    """测试 .env 文件"""
    print("\n测试 .env 文件...")
    
    env_file = Path(".env")
    if env_file.exists():
        print(f"✓ 找到 .env 文件: {env_file}")
        
        # 显示关键配置
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            print(f"  配置项数量: {len(lines)}")
        
        return True
    else:
        print("⚠️  未找到 .env 文件")
        print("  可以复制 config_example.env 为 .env")
        return False


def test_platform():
    """测试平台兼容性"""
    print("\n平台信息:")
    print(f"  系统: {platform.system()}")
    print(f"  版本: {platform.version()}")
    print(f"  架构: {platform.machine()}")
    print(f"  Python: {sys.version.split()[0]}")
    
    # 检查网络工具
    if platform.system() == "Windows":
        print("  Windows 平台 - 使用 ping 命令")
    else:
        print("  Unix/Linux 平台 - 使用 ping 命令")
    
    return True


def main():
    """主测试函数"""
    print("=" * 50)
    print("MAIC 服务测试")
    print("=" * 50)
    
    tests = [
        test_platform,
        test_env_file,
        test_imports,
        test_config,
        test_models,
        test_eyelink_manager
    ]
    
    passed = sum(1 for test in tests if test())
    total = len(tests)
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 50)
    
    if passed == total:
        print("🎉 所有测试通过!")
        print("\n下一步:")
        print("1. 启动服务: python main.py")
        print("2. 测试连接: python debug_eyelink.py --dummy")
        return 0
    else:
        print("❌ 部分测试失败")
        print("\n建议:")
        print("1. 检查依赖安装: pip install -r requirements.txt")
        print("2. 检查 .env 文件配置")
        print("3. 查看错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())