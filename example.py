"""
使用示例

展示如何使用 API 与服务交互
"""

import requests
import time

BASE_URL = "http://localhost:8123"


def example_basic():
    """基础示例：接收数据"""
    print("=== 基础示例 ===\n")
    
    # 健康检查
    print("1. 健康检查...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   {response.json()}\n")
    
    # 发送数据
    print("2. 发送数据...")
    data = {
        "event": "test_event",
        "data": {"message": "Hello, MAIC!"}
    }
    response = requests.post(f"{BASE_URL}/ingest", json=data)
    print(f"   {response.json()}\n")


def example_eyelink():
    """EyeLink 示例：连接和记录"""
    print("=== EyeLink 示例 ===\n")
    
    # 检查状态
    print("1. 检查状态...")
    response = requests.get(f"{BASE_URL}/eyelink/status")
    status = response.json()
    print(f"   Status: {status['status']}")
    print(f"   Connected: {status['connected']}\n")
    
    # 连接（使用虚拟模式）
    if not status['connected']:
        print("2. 连接眼动仪（虚拟模式）...")
        config = {
            "host_ip": "100.1.1.1",
            "dummy_mode": True,  # 虚拟模式，无需真实硬件
            "screen_width": 1920,
            "screen_height": 1080
        }
        response = requests.post(f"{BASE_URL}/eyelink/connect", json=config)
        print(f"   {response.json()}\n")
    
    # 开始记录
    print("3. 开始记录...")
    response = requests.post(f"{BASE_URL}/eyelink/start_recording")
    print(f"   {response.json()}\n")
    
    # 发送标记
    print("4. 发送标记...")
    markers = [
        {
            "marker_type": "trial_start",
            "message": "Trial 1 started",
            "trial_id": "trial_001"
        },
        {
            "marker_type": "stimulus_on",
            "message": "Image displayed",
            "additional_data": {"stimulus": "img_001.jpg"}
        },
        {
            "marker_type": "response",
            "message": "Button pressed",
            "additional_data": {"rt": 1250, "correct": True}
        },
        {
            "marker_type": "trial_end",
            "message": "Trial 1 ended",
            "trial_id": "trial_001"
        }
    ]
    
    for marker in markers:
        response = requests.post(f"{BASE_URL}/eyelink/marker", json=marker)
        print(f"   {marker['marker_type']}: {response.json()['message']}")
        time.sleep(0.5)
    
    print()
    
    # 停止记录
    print("5. 停止记录...")
    response = requests.post(f"{BASE_URL}/eyelink/stop_recording")
    print(f"   {response.json()}\n")


def example_polling():
    """轮询示例"""
    print("=== 轮询示例 ===\n")
    
    # 查看状态
    print("1. 查看轮询状态...")
    response = requests.get(f"{BASE_URL}/polling/status")
    print(f"   {response.json()}\n")
    
    # 手动添加数据
    print("2. 手动添加数据...")
    data = {"event": "manual_event", "data": {"test": "value"}}
    response = requests.post(f"{BASE_URL}/polling/data", json=data)
    print(f"   {response.json()}\n")


def main():
    """运行所有示例"""
    print("MAIC Service - Usage Examples")
    print("=" * 50)
    print("\n确保服务已启动: python main.py\n")
    
    try:
        # 检查服务是否运行
        requests.get(f"{BASE_URL}/health", timeout=2)
        
        example_basic()
        example_eyelink()
        example_polling()
        
        print("=" * 50)
        print("✅ 所有示例执行完成")
        
    except requests.exceptions.ConnectionError:
        print("❌ 错误: 无法连接到服务")
        print("   请先启动服务: python main.py")
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()

