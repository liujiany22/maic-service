#!/bin/bash
#
# EyeLink 网络连接检查脚本
# 跨平台兼容版本
#

# 默认 EyeLink 主机 IP
EYELINK_HOST="${1:-100.1.1.1}"

echo "EyeLink 网络诊断工具"
echo "目标主机: $EYELINK_HOST"
echo ""

# 检测操作系统
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "系统: $MACHINE"
echo ""

# Ping 测试
echo "Ping 测试..."
if [ "$MACHINE" = "MinGw" ] || [ "$MACHINE" = "Cygwin" ]; then
    # Windows
    if ping -n 5 "$EYELINK_HOST" > /dev/null 2>&1; then
        echo "✓ Ping 成功"
        ping -n 5 "$EYELINK_HOST" | tail -2
    else
        echo "❌ Ping 失败"
    fi
else
    # Unix/Linux/Mac
    if ping -c 5 -W 2 "$EYELINK_HOST" > /dev/null 2>&1; then
        echo "✓ Ping 成功"
        ping -c 5 "$EYELINK_HOST" | tail -2
    else
        echo "❌ Ping 失败"
    fi
fi

echo ""

# 网络接口检查
echo "网络接口:"
if command -v ip >/dev/null 2>&1; then
    # Linux
    ip addr show | grep -E "^[0-9]+:|inet " | head -10
elif command -v ifconfig >/dev/null 2>&1; then
    # Mac/Unix
    ifconfig | grep -A 1 "^en" | head -10
else
    echo "⚠️  无法检查网络接口"
fi

echo ""

# 路由检查
echo "路由信息:"
if command -v netstat >/dev/null 2>&1; then
    netstat -rn | grep -E "^(Destination|default|100\.)" | head -5
elif command -v route >/dev/null 2>&1; then
    route -n | grep -E "^(Destination|default|100\.)" | head -5
else
    echo "⚠️  无法检查路由"
fi

echo ""
echo "诊断完成"
echo "下一步: python debug_eyelink.py --host $EYELINK_HOST"