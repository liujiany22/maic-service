#!/usr/bin/env python3
"""
跨平台网络检查脚本
替代 check_network.sh，支持 Windows/Linux/Mac
"""

import os
import sys
import platform
import subprocess
import socket
from pathlib import Path


def ping_host(host, count=5):
    """跨平台 ping 测试"""
    system = platform.system().lower()
    
    try:
        if system == "windows":
            cmd = ["ping", "-n", str(count), host]
        else:
            cmd = ["ping", "-c", str(count), "-W", "2", host]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)


def get_network_interfaces():
    """获取网络接口信息"""
    try:
        import psutil
        interfaces = []
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    interfaces.append(f"{interface}: {addr.address}")
        return interfaces
    except ImportError:
        # 如果没有 psutil，使用系统命令
        system = platform.system().lower()
        try:
            if system == "windows":
                result = subprocess.run(["ipconfig"], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                interfaces = []
                for line in lines:
                    if "IPv4" in line and "192.168" in line:
                        interfaces.append(line.strip())
                return interfaces[:5]  # 限制输出
            else:
                result = subprocess.run(["ifconfig"], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                interfaces = []
                for line in lines:
                    if "inet " in line and "127.0.0.1" not in line:
                        interfaces.append(line.strip())
                return interfaces[:5]
        except Exception:
            return ["无法获取网络接口信息"]


def check_connectivity(host="100.1.1.1"):
    """检查网络连接"""
    print(f"网络诊断工具")
    print(f"目标主机: {host}")
    print(f"系统: {platform.system()} {platform.release()}")
    print()
    
    # Ping 测试
    print("Ping 测试...")
    success, output = ping_host(host)
    if success:
        print("✓ Ping 成功")
        # 显示最后几行输出
        lines = output.split('\n')
        for line in lines[-3:]:
            if line.strip():
                print(f"  {line.strip()}")
    else:
        print("❌ Ping 失败")
        print(f"  错误: {output}")
    
    print()
    
    # 网络接口
    print("网络接口:")
    interfaces = get_network_interfaces()
    for interface in interfaces[:5]:
        print(f"  {interface}")
    
    print()
    
    # 建议
    print("建议:")
    if success:
        print("  1. 网络连接正常，可以尝试连接 EyeLink")
        print(f"  2. 运行测试: python debug_eyelink.py --host {host}")
    else:
        print("  1. 检查 EyeLink 主机是否开机")
        print("  2. 检查网络线缆连接")
        print("  3. 确认 IP 地址是否正确")
        print("  4. 检查防火墙设置")
    
    return success


def main():
    """主函数"""
    host = sys.argv[1] if len(sys.argv) > 1 else "100.1.1.1"
    
    try:
        success = check_connectivity(host)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
