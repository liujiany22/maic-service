"""
简单测试脚本
验证所有模块是否能正常导入
"""

import sys


def test_imports():
    """测试模块导入"""
    print("Testing module imports...")
    
    try:
        import config
        print("✓ config")
        
        import models
        print("✓ models")
        
        import utils
        print("✓ utils")
        
        import eyelink_manager
        print(f"✓ eyelink_manager (PyLink available: {eyelink_manager.EYELINK_AVAILABLE})")
        
        import data_poller
        print("✓ data_poller")
        
        import api_routes
        print("✓ api_routes")
        
        import main
        print("✓ main")
        
        print("\n✅ All modules imported successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        return False


def test_config():
    """测试配置"""
    print("\nTesting configuration...")
    
    try:
        import config
        
        print(f"  APP_NAME: {config.APP_NAME}")
        print(f"  PORT: {config.PORT}")
        print(f"  LOG_LEVEL: {config.LOG_LEVEL}")
        print(f"  EYELINK_HOST_IP: {config.EYELINK_HOST_IP}")
        print(f"  POLLING_ENABLED: {config.POLLING_ENABLED}")
        
        print("✓ Configuration loaded")
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


def test_models():
    """测试数据模型"""
    print("\nTesting models...")
    
    try:
        from models import EyeLinkMarker, MarkerType
        
        marker = EyeLinkMarker(
            marker_type=MarkerType.MESSAGE,
            message="Test marker",
            trial_id="test_001"
        )
        
        print(f"  Created marker: {marker.message}")
        print("✓ Models working")
        return True
        
    except Exception as e:
        print(f"❌ Models test failed: {e}")
        return False


def test_eyelink_manager():
    """测试 EyeLink 管理器"""
    print("\nTesting EyeLink manager...")
    
    try:
        from eyelink_manager import eyelink_manager
        
        status = eyelink_manager.get_status()
        print(f"  Status: {status.status.value}")
        print(f"  Connected: {status.connected}")
        print("✓ EyeLink manager working")
        return True
        
    except Exception as e:
        print(f"❌ EyeLink manager test failed: {e}")
        return False


def test_data_poller():
    """测试数据轮询器"""
    print("\nTesting data poller...")
    
    try:
        from data_poller import DataPoller
        
        poller = DataPoller(interval=1.0)
        poller.add_data({"test": "data"})
        data = poller.get_pending_data()
        
        print(f"  Retrieved {len(data)} item(s)")
        print("✓ Data poller working")
        return True
        
    except Exception as e:
        print(f"❌ Data poller test failed: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 50)
    print("MAIC Service - Module Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_models,
        test_eyelink_manager,
        test_data_poller
    ]
    
    passed = sum(1 for test in tests if test())
    total = len(tests)
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
