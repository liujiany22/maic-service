#!/bin/bash
#
# EyeLink 网络连接检查脚本
#
# 帮助排查 EyeLink 主机网络连接问题
#

# 默认 EyeLink 主机 IP
EYELINK_HOST="${1:-100.1.1.1}"

echo "========================================================"
echo "  EyeLink 网络连接诊断工具"
echo "========================================================"
echo ""
echo "目标主机: $EYELINK_HOST"
echo ""

# 检查 1: Ping 测试
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "检查 1/4: Ping 测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "正在 ping $EYELINK_HOST (5次)..."
echo ""

if ping -c 5 -W 2 "$EYELINK_HOST" > /dev/null 2>&1; then
    echo "✓ Ping 成功! 网络连接正常"
    ping -c 5 "$EYELINK_HOST" | tail -2
else
    echo "❌ Ping 失败! 无法连接到主机"
    echo ""
    echo "可能的原因:"
    echo "  1. EyeLink 主机未开机"
    echo "  2. 网络线缆未连接"
    echo "  3. IP 地址不正确"
    echo "  4. 网络配置问题"
    echo ""
    echo "建议操作:"
    echo "  - 检查 EyeLink 主机电源"
    echo "  - 检查网络线是否插好"
    echo "  - 在 EyeLink 主机上确认 IP 地址"
fi

echo ""

# 检查 2: 网络接口
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "检查 2/4: 本地网络接口"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "活动的网络接口:"
echo ""

if command -v ifconfig &> /dev/null; then
    ifconfig | grep -A 1 "^en" | grep -v "^--"
elif command -v ip &> /dev/null; then
    ip addr show | grep -E "^[0-9]+:|inet "
else
    echo "⚠️  无法找到 ifconfig 或 ip 命令"
fi

echo ""

# 检查 3: 路由表
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "检查 3/4: 路由信息"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command -v netstat &> /dev/null; then
    echo "路由表:"
    netstat -rn | grep -E "^(Destination|default|100\.)"
elif command -v route &> /dev/null; then
    echo "路由表:"
    route -n | grep -E "^(Destination|default|100\.)"
else
    echo "⚠️  无法检查路由信息"
fi

echo ""

# 检查 4: ARP 缓存
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "检查 4/4: ARP 缓存"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if arp -a | grep -q "$EYELINK_HOST"; then
    echo "✓ 在 ARP 缓存中找到主机:"
    arp -a | grep "$EYELINK_HOST"
else
    echo "⚠️  ARP 缓存中未找到主机"
    echo "这可能是正常的（如果之前未连接过）"
fi

echo ""
echo "========================================================"
echo "  诊断完成"
echo "========================================================"
echo ""
echo "建议:"
echo "  1. 如果 Ping 成功，可以尝试连接 EyeLink"
echo "  2. 如果 Ping 失败，先解决网络连接问题"
echo "  3. 确认 EyeLink 主机 IP 是否为 $EYELINK_HOST"
echo ""
echo "下一步:"
echo "  运行 EyeLink 连接测试:"
echo "    python debug_eyelink.py --host $EYELINK_HOST"
echo ""

