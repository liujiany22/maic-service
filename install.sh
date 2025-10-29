#!/bin/bash
# MAIC JSON Service - 快速安装脚本 (支持 conda)

set -e  # 遇到错误立即退出

echo "================================"
echo "MAIC JSON Service 安装程序"
echo "================================"
echo ""

# 检查是否使用 conda
USE_CONDA=false
if command -v conda &> /dev/null; then
    echo "检测到 conda 环境管理器"
    read -p "是否使用 conda 创建虚拟环境? (Y/n): " use_conda
    if [[ "$use_conda" =~ ^[Yy]$ ]] || [[ -z "$use_conda" ]]; then
        USE_CONDA=true
    fi
fi

echo ""

if [ "$USE_CONDA" = true ]; then
    # ========== Conda 方式 ==========
    
    # 检查 conda
    echo "1. 检查 conda..."
    if ! command -v conda &> /dev/null; then
        echo "   ❌ 错误: 未找到 conda"
        echo "   请先安装 Anaconda 或 Miniconda"
        exit 1
    fi
    CONDA_VERSION=$(conda --version)
    echo "   ✓ 找到 $CONDA_VERSION"
    
    # 检查环境是否存在
    echo ""
    echo "2. 检查 conda 环境..."
    ENV_NAME="maic-service"
    if conda env list | grep -q "^${ENV_NAME} "; then
        echo "   ⚠️  环境 '$ENV_NAME' 已存在"
        read -p "   是否删除并重新创建? (y/N): " recreate
        if [[ "$recreate" =~ ^[Yy]$ ]]; then
            conda env remove -n $ENV_NAME -y
            echo "   ✓ 已删除旧环境"
        else
            echo "   ℹ️  将使用现有环境"
        fi
    fi
    
    # 创建或使用现有环境
    echo ""
    echo "3. 创建/激活 conda 环境..."
    if ! conda env list | grep -q "^${ENV_NAME} "; then
        conda create -n $ENV_NAME python=3.10 -y
        echo "   ✓ conda 环境 '$ENV_NAME' 创建成功"
    fi
    
    # 激活环境
    echo ""
    echo "4. 激活 conda 环境..."
    # 注意：这里需要使用 conda 的 shell 初始化
    eval "$(conda shell.bash hook)"
    conda activate $ENV_NAME
    echo "   ✓ conda 环境 '$ENV_NAME' 已激活"
    
    # 升级 pip
    echo ""
    echo "5. 升级 pip..."
    pip install --upgrade pip --quiet
    echo "   ✓ pip 已升级"
    
else
    # ========== venv 方式 ==========
    
    # 检查 Python 版本
    echo "1. 检查 Python 版本..."
    if ! command -v python3 &> /dev/null; then
        echo "   ❌ 错误: 未找到 Python 3"
        echo "   请先安装 Python 3.8 或更高版本"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "   ✓ 找到 Python $PYTHON_VERSION"
    
    # 检查 pip
    echo ""
    echo "2. 检查 pip..."
    if ! command -v pip3 &> /dev/null; then
        echo "   ❌ 错误: 未找到 pip3"
        echo "   请先安装 pip"
        exit 1
    fi
    echo "   ✓ pip 已安装"
    
    # 创建虚拟环境
    echo ""
    echo "3. 创建虚拟环境..."
    if [ -d "venv" ]; then
        echo "   ⚠️  虚拟环境已存在，跳过创建"
    else
        python3 -m venv venv
        echo "   ✓ 虚拟环境创建成功"
    fi
    
    # 激活虚拟环境
    echo ""
    echo "4. 激活虚拟环境..."
    source venv/bin/activate
    echo "   ✓ 虚拟环境已激活"
    
    # 升级 pip
    echo ""
    echo "5. 升级 pip..."
    pip install --upgrade pip --quiet
    echo "   ✓ pip 已升级"
fi

# 安装依赖
echo ""
echo "6. 安装依赖包..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo "   ✓ 依赖包安装成功"
else
    echo "   ❌ 错误: 未找到 requirements.txt"
    exit 1
fi
python3.10 -m pip install --index-url=https://pypi.sr-support.com sr-research-pylink
echo "   ✓ sr-research-pylink 已安装"


# 创建必要的目录
echo ""
echo "7. 创建必要的目录..."
mkdir -p logdata
mkdir -p log
echo "   ✓ 目录创建成功"

# 检查配置文件
echo ""
echo "8. 检查配置文件..."
if [ ! -f ".env" ]; then
    if [ -f "config_example.env" ]; then
        cp config_example.env .env
        echo "   ✓ 配置文件已从示例复制"
        echo "   ⚠️  请根据需要编辑 .env 文件"
    else
        echo "   ⚠️  未找到配置示例文件"
    fi
else
    echo "   ✓ 配置文件已存在"
fi

# 完成
echo ""
echo "================================"
echo "✅ 安装完成！"
echo "================================"
echo ""
echo "下一步操作："
echo ""

if [ "$USE_CONDA" = true ]; then
    echo "1. 激活 conda 环境（如果尚未激活）："
    echo "   conda activate $ENV_NAME"
else
    echo "1. 激活虚拟环境（如果尚未激活）："
    echo "   source venv/bin/activate"
fi

echo ""
echo "2. 编辑配置文件（可选）："
echo "   vi .env"
echo ""
echo "3. 启动服务："
echo "   python main.py"
echo ""
echo "4. 或使用 uvicorn 启动："
echo "   uvicorn main:app --host 0.0.0.0 --port 8123"
echo ""
echo "5. 查看 API 文档："
echo "   http://localhost:8123/docs"
echo ""

if [ "$USE_CONDA" = true ]; then
    echo "注意: 使用了 conda 环境 '$ENV_NAME'"
    echo "退出环境: conda deactivate"
else
    echo "注意: 使用了 venv 虚拟环境"
    echo "退出环境: deactivate"
fi

echo ""
echo "如需帮助，请查看 INSTALLATION.md 或 README.md"
echo ""
