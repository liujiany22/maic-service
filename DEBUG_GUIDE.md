# EyeLink 调试指南

本文档提供详细的 EyeLink 连接调试步骤和常见问题解决方案。

## 目录

- [调试流程](#调试流程)
- [调试工具](#调试工具)
- [日志解读](#日志解读)
- [常见错误](#常见错误)
- [最佳实践](#最佳实践)

---

## 调试流程

### 第一步：验证 PyLink 安装

在连接 EyeLink 之前，首先确认 PyLink 库已正确安装。

```bash
# 测试 PyLink 导入
python -c "import pylink; print('PyLink 版本:', pylink.__version__ if hasattr(pylink, '__version__') else 'Unknown'); print('✓ PyLink 可用')"
```

**预期输出**:
```
PyLink 版本: X.X.X
✓ PyLink 可用
```

**如果失败**:
1. 下载并安装 [EyeLink Developers Kit](https://www.sr-research.com/support/)
2. 确保 Python 能找到 pylink 模块
3. 检查环境变量和 Python 路径

---

### 第二步：检查网络连接

使用提供的网络检查脚本：

```bash
./check_network.sh 100.1.1.1
```

**脚本会检查**:
- ✓ Ping 连通性（是否能到达主机）
- ✓ 本地网络接口（网卡是否正常）
- ✓ 路由配置（路由表是否正确）
- ✓ ARP 缓存（MAC 地址解析）

**常见问题**:

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Ping 超时 | 主机未开机/网线未接 | 检查 EyeLink 主机电源和网线 |
| 无路由 | 网络配置错误 | 检查网络设置，可能需要手动配置 |
| 无网络接口 | 网卡禁用 | 启用网卡 |

---

### 第三步：运行 EyeLink 调试脚本

#### 3.1 虚拟模式测试（推荐先做）

虚拟模式不需要真实硬件，用于验证代码逻辑：

```bash
python debug_eyelink.py --dummy
```

**预期输出**:
```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║                  EyeLink 连接调试工具                      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

步骤 1/5: 检查 PyLink 可用性
✓ PyLink 可用

步骤 2/5: 连接参数
  主机 IP: None
  虚拟模式: True
  屏幕尺寸: 1920 x 1080

步骤 3/5: 尝试连接 EyeLink
✓ 连接成功

步骤 4/5: 测试发送标记
  ✓ 标记 1 发送成功
  ✓ 标记 2 发送成功
  ✓ 标记 3 发送成功

步骤 5/5: 断开连接
✓ 已断开连接

╔══════════════════════════════════════════════════════════╗
║                      测试完成!                            ║
╚══════════════════════════════════════════════════════════╝
```

如果虚拟模式成功，说明代码逻辑正确，问题在于硬件连接。

#### 3.2 真实设备测试

```bash
python debug_eyelink.py --host 100.1.1.1
```

**关键检查点**:

1. **PyLink 可用性**: 
   - ✓ 正常: `✓ PyLink 可用`
   - ❌ 失败: 回到第一步

2. **连接对象创建**:
   - ✓ 正常: `✓ 连接对象创建成功`
   - ❌ 失败: 检查网络和 IP 地址

3. **设备版本获取**:
   - ✓ 正常: `✓ 设备版本: X`
   - ⚠️ 警告: `无法获取设备版本` - 可能连接不稳定

4. **标记发送**:
   - ✓ 正常: `✓ 标记 X 发送成功`
   - ❌ 失败: 连接可能断开

---

### 第四步：在完整服务中测试

如果调试脚本成功，尝试启动完整服务：

```bash
# 启用 DEBUG 日志
export LOG_LEVEL=DEBUG

# 启动服务
python main.py
```

**查看启动日志**:

```
============================================================
当前配置:
============================================================
应用名称: MAIC JSON Service
版本: 1.0.0
端口: 8123
日志级别: DEBUG

EyeLink 配置:
  主机 IP: 100.1.1.1
  虚拟模式: False
  屏幕尺寸: 1920 x 1080
  EDF 文件: test.edf

轮询配置:
  启用: True
  间隔: 0.1s
============================================================
```

**使用 API 测试连接**:

```bash
# 1. 检查状态
curl http://localhost:8123/eyelink/status

# 2. 连接设备
curl -X POST http://localhost:8123/eyelink/connect

# 3. 开始记录
curl -X POST http://localhost:8123/eyelink/start_recording

# 4. 发送测试标记
curl -X POST http://localhost:8123/eyelink/marker \
  -H "Content-Type: application/json" \
  -d '{"marker_type": "message", "message": "TEST_MARKER"}'

# 5. 停止记录
curl -X POST http://localhost:8123/eyelink/stop_recording
```

---

## 调试工具

### 1. check_network.sh

**用途**: 诊断网络连接问题

**使用**:
```bash
./check_network.sh [IP地址]
```

**输出解读**:
- ✓ Ping 成功 → 网络正常
- ❌ Ping 失败 → 检查物理连接和 IP
- ⚠️ 路由问题 → 可能需要配置静态路由

### 2. debug_eyelink.py

**用途**: 独立测试 EyeLink 连接，不依赖 FastAPI 服务

**参数**:
- `--host IP`: 指定 EyeLink 主机 IP（默认: 100.1.1.1）
- `--dummy`: 使用虚拟模式
- `--width N`: 屏幕宽度（默认: 1920）
- `--height N`: 屏幕高度（默认: 1080）

**示例**:
```bash
# 基本测试
python debug_eyelink.py

# 自定义 IP
python debug_eyelink.py --host 192.168.1.100

# 虚拟模式
python debug_eyelink.py --dummy

# 自定义屏幕
python debug_eyelink.py --width 2560 --height 1440
```

---

## 日志解读

### 连接日志

#### ✅ 成功连接

```
============================================================
开始 EyeLink 连接调试
============================================================
✓ PyLink 模块已加载: <module 'pylink' ...>
连接参数:
  - 目标 IP: 100.1.1.1
  - 虚拟模式: False
  - 屏幕尺寸: 1920 x 1080
尝试连接到真实设备: 100.1.1.1
正在创建连接对象...
✓ 连接对象创建成功
✓ 设备连接确认成功
✓ 设备版本: 5
配置屏幕参数...
✓ screen_pixel_coords 设置成功
✓ DISPLAY_COORDS 设置成功
============================================================
✅ EyeLink 连接成功!
============================================================
```

#### ❌ 连接失败 - 网络问题

```
============================================================
开始 EyeLink 连接调试
============================================================
✓ PyLink 模块已加载: <module 'pylink' ...>
尝试连接到真实设备: 100.1.1.1
正在创建连接对象...
❌ 连接失败 (RuntimeError): Cannot connect to tracker
常见原因:
  1. IP 地址错误或设备未开机
  2. 网络不通 (尝试: ping 100.1.1.1)
  3. EyeLink 软件未运行
  4. 端口被占用或防火墙阻止
```

**解决**: 按提示检查网络连接

#### ❌ PyLink 不可用

```
❌ PyLink library not available. Install EyeLink Developers Kit.
请检查:
  1. 是否已安装 EyeLink Developers Kit
  2. Python 是否能找到 pylink 模块
  3. 尝试: python -c 'import pylink; print(pylink.__version__)'
```

**解决**: 安装 EyeLink SDK

---

### 记录日志

#### ✅ 成功开始记录

```
============================================================
开始记录眼动数据
============================================================
✓ 连接状态正常
EDF 文件名: test.edf
打开 EDF 文件...
✓ EDF 文件打开成功: test.edf
配置记录参数...
✓ 所有记录参数配置完成
启动记录...
✓ startRecording 调用成功
============================================================
✅ 记录已开始: test.edf
============================================================
```

#### ❌ 状态错误

```
❌ 当前状态不正确: DISCONNECTED
需要状态为 CONNECTED 才能开始记录
```

**解决**: 先调用 `connect()` 方法

---

### 标记日志

#### ✅ 成功发送标记（DEBUG 级别）

```
----------------------------------------
发送标记: trial_start
  消息: Trial 1
  试验ID: 001
  → sendMessage: TRIALID 001
  ✓ 主消息发送成功
  发送附加变量 (2 个):
    → !V TRIAL_VAR condition easy
    ✓ 变量 condition 发送成功
    → !V TRIAL_VAR block 1
    ✓ 变量 block 发送成功
✅ 标记发送完成: trial_start
----------------------------------------
```

#### ❌ 状态错误

```
❌ 无法发送标记: 状态不正确 (DISCONNECTED)
需要 CONNECTED 或 RECORDING 状态
```

**解决**: 检查当前状态，确保已连接

---

## 常见错误

### 错误 1: "Cannot connect to tracker"

**完整错误**:
```
RuntimeError: Cannot connect to tracker
```

**原因**:
- EyeLink 主机未开机
- 网络不通
- IP 地址错误
- EyeLink 软件未运行

**诊断**:
```bash
# 1. 检查网络
./check_network.sh 100.1.1.1

# 2. 尝试 ping
ping 100.1.1.1

# 3. 确认 IP（在 EyeLink 主机上）
# 通常显示在主机屏幕右上角
```

**解决**:
1. 确保 EyeLink 主机开机
2. 检查网线连接
3. 确认 IP 地址正确
4. 检查防火墙设置

---

### 错误 2: "PyLink library not available"

**完整错误**:
```
PyLink library not available. Install EyeLink Developers Kit.
```

**原因**: 未安装 EyeLink SDK 或 Python 找不到 pylink 模块

**解决**:
```bash
# 1. 下载 EyeLink Developers Kit
# 访问: https://www.sr-research.com/support/

# 2. 安装 SDK

# 3. 验证安装
python -c "import pylink; print(pylink)"

# 4. 检查 Python 路径
python -c "import sys; print('\n'.join(sys.path))"

# 5. 临时使用虚拟模式
export EYELINK_DUMMY_MODE=true
python main.py
```

---

### 错误 3: startRecording 返回错误代码

**完整错误**:
```
❌ startRecording 返回错误代码: 27
```

**原因**: EyeLink 内部错误（错误代码含义见 PyLink 文档）

**常见代码**:
- `0`: 成功
- `27`: 无法打开 EDF 文件
- 其他: 参考 SR Research 文档

**解决**:
1. 检查 EDF 文件名格式（8.3 格式）
2. 确保主机磁盘空间充足
3. 检查是否有文件同名冲突

---

### 错误 4: 标记发送失败

**症状**: `send_marker()` 返回 False

**诊断**:
```bash
# 检查状态
curl http://localhost:8123/eyelink/status
```

**可能原因**:
- 未处于 CONNECTED 或 RECORDING 状态
- Tracker 对象未初始化
- 网络连接中断

**解决**:
1. 确认状态正确
2. 重新连接设备
3. 检查网络稳定性

---

## 最佳实践

### 1. 开发时使用虚拟模式

```bash
export EYELINK_DUMMY_MODE=true
python main.py
```

**优点**:
- 无需实际硬件
- 快速验证代码逻辑
- 避免硬件损耗

**注意**: 虚拟模式不记录真实数据，仅用于测试

---

### 2. 启用 DEBUG 日志

```bash
export LOG_LEVEL=DEBUG
python main.py
```

**查看日志**:
```bash
tail -f log/service.out
```

---

### 3. 逐步测试

不要一次性测试完整流程，按以下顺序：

1. ✓ 验证 PyLink 安装
2. ✓ 检查网络连接
3. ✓ 测试虚拟模式
4. ✓ 测试真实连接
5. ✓ 测试记录功能
6. ✓ 测试标记发送

---

### 4. 检查清单

在报告问题前，确认以下内容：

- [ ] PyLink 已安装且可导入
- [ ] EyeLink 主机已开机
- [ ] 网络线已连接
- [ ] 能 ping 通主机 IP
- [ ] IP 地址正确
- [ ] 虚拟模式能正常工作
- [ ] DEBUG 日志已启用
- [ ] 已查看 `log/service.out`

---

### 5. 保存日志

遇到问题时，保存完整日志：

```bash
export LOG_LEVEL=DEBUG
python debug_eyelink.py --host 100.1.1.1 2>&1 | tee debug_output.log
```

日志文件可用于后续分析或技术支持。

---

## 获取帮助

如果以上方法都无法解决问题：

1. **收集信息**:
   - Python 版本: `python --version`
   - PyLink 版本: `python -c "import pylink; print(pylink.__version__ if hasattr(pylink, '__version__') else 'Unknown')"`
   - 操作系统: `uname -a` (Linux/Mac) 或 `ver` (Windows)
   - 完整错误日志
   - 网络诊断输出

2. **检查文档**:
   - [EyeLink Developers Kit 文档](https://www.sr-research.com/support/)
   - PyLink API 参考

3. **联系技术支持**:
   - SR Research 官方支持
   - 项目维护者

---

## 附录：快速参考

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `EYELINK_HOST_IP` | 100.1.1.1 | 主机 IP |
| `EYELINK_DUMMY_MODE` | false | 虚拟模式 |
| `EYELINK_SCREEN_WIDTH` | 1920 | 屏幕宽度 |
| `EYELINK_SCREEN_HEIGHT` | 1080 | 屏幕高度 |
| `LOG_LEVEL` | INFO | 日志级别 |

### 快速命令

```bash
# 网络检查
./check_network.sh 100.1.1.1

# 虚拟模式测试
python debug_eyelink.py --dummy

# 真实设备测试
python debug_eyelink.py --host 100.1.1.1

# 启动服务（DEBUG）
LOG_LEVEL=DEBUG python main.py

# 查看日志
tail -f log/service.out

# 测试 PyLink
python -c "import pylink; print(pylink)"
```

---

**版本**: 1.0.0  
**更新**: 2025-10-27

