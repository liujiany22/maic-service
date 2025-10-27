# 项目结构说明

## 目录结构

```
maic-service/
├── main.py              # 主服务入口，FastAPI 应用
├── config.py            # 配置管理，统一管理所有配置项
├── models.py            # 数据模型，Pydantic 模型定义
├── utils.py             # 工具函数，通用辅助功能
├── eyelink_manager.py   # EyeLink 管理器，眼动仪交互
├── data_poller.py       # 数据轮询器，后台数据获取
├── api_routes.py        # API 路由，HTTP 端点定义
├── test.py              # 测试脚本
├── example.py           # 使用示例
├── requirements.txt     # 生产依赖
├── requirements-dev.txt # 开发依赖
├── config_example.env   # 配置示例
├── install.sh           # 安装脚本
├── run.sh               # 启动脚本
├── .gitignore           # Git 忽略规则
├── README.md            # 项目说明
└── STRUCTURE.md         # 本文件
```

## 模块说明

### 核心模块 (7 个文件)

#### 1. main.py
- **职责**: 应用入口和核心业务逻辑
- **功能**: 
  - FastAPI 应用初始化
  - 生命周期管理
  - 数据接收和处理
  - 自动标记发送
- **依赖**: config, models, utils, eyelink_manager, data_poller, api_routes

#### 2. config.py
- **职责**: 配置管理
- **功能**:
  - 统一管理所有配置项
  - 支持环境变量覆盖
  - 初始化目录
- **特点**: 无外部依赖，纯配置

#### 3. models.py
- **职责**: 数据模型定义
- **功能**:
  - 请求/响应模型
  - EyeLink 相关模型
  - 数据验证
- **依赖**: pydantic

#### 4. utils.py
- **职责**: 工具函数
- **功能**:
  - 事件简报生成
  - 通用辅助函数
- **特点**: 无外部依赖

#### 5. eyelink_manager.py
- **职责**: EyeLink 眼动仪管理
- **功能**:
  - 连接/断开
  - 记录控制
  - 标记发送
- **依赖**: pylink (可选), models
- **注意**: ⚠️ 部分实现基于文档，可能需要调整

#### 6. data_poller.py
- **职责**: 数据轮询
- **功能**:
  - 后台轮询线程
  - 数据队列管理
  - 自定义获取逻辑
- **特点**: 线程安全

#### 7. api_routes.py
- **职责**: API 路由定义
- **功能**:
  - EyeLink 端点
  - 轮询端点
  - 请求处理
- **依赖**: fastapi, eyelink_manager, data_poller, models

### 配置和脚本 (4 个文件)

- **requirements.txt**: 生产环境依赖列表
- **requirements-dev.txt**: 开发环境依赖列表
- **config_example.env**: 环境变量配置示例
- **install.sh**: 自动安装脚本（支持 conda 和 venv）

### 测试和示例 (2 个文件)

- **test.py**: 模块导入和基础功能测试
- **example.py**: API 使用示例和最佳实践

## 代码风格

### 命名规范

- **文件名**: 小写字母 + 下划线 (snake_case)
- **类名**: 大驼峰 (PascalCase)
- **函数名**: 小写字母 + 下划线 (snake_case)
- **常量**: 大写字母 + 下划线 (UPPER_CASE)
- **私有成员**: 前缀下划线 (_private)

### 文档字符串

所有模块、类、函数都有清晰的文档字符串：

```python
def function_name(param: str) -> bool:
    """
    简短描述
    
    Args:
        param: 参数说明
        
    Returns:
        返回值说明
        
    注意:
        重要提示或警告
    """
    pass
```

### 注释规范

- 模块级注释：说明模块职责
- 函数级注释：说明功能和参数
- 行内注释：解释复杂逻辑
- 特殊标记：⚠️ 表示需要注意的地方

## 依赖关系

```
main.py
├── config.py (配置)
├── models.py (模型)
├── utils.py (工具)
├── eyelink_manager.py (眼动仪)
│   └── models.py
├── data_poller.py (轮询)
└── api_routes.py (路由)
    ├── config.py
    ├── models.py
    ├── eyelink_manager.py
    └── data_poller.py
```

### 设计原则

1. **低耦合**: 模块之间依赖最小化
2. **高内聚**: 相关功能集中在同一模块
3. **单一职责**: 每个模块只负责一件事
4. **配置分离**: 配置独立管理，便于修改
5. **可测试**: 模块可独立测试

## 数据流

```
外部请求 
    → POST /ingest 
    → main.process_data 
    → 保存文件 
    → send_eyelink_marker 
    → eyelink_manager.send_marker 
    → 写入 EDF
```

## 扩展指南

### 添加新的 API 端点

在 `api_routes.py` 中添加：

```python
@router.post("/new/endpoint", tags=["Category"])
async def new_endpoint(data: YourModel):
    """端点描述"""
    # 实现逻辑
    return {"ok": True}
```

### 自定义轮询逻辑

在 `data_poller.py` 中实现 `_fetch_external_data`:

```python
def _fetch_external_data(self):
    # 获取数据
    data = your_data_source.fetch()
    # 添加到队列
    self.add_data(data)
```

### 添加新的配置项

在 `config.py` 中添加：

```python
NEW_CONFIG = os.getenv("NEW_CONFIG", "default_value")
```

## 代码质量

- **类型提示**: 所有函数都有类型注解
- **错误处理**: 完善的异常捕获和日志记录
- **线程安全**: 使用锁保护共享资源
- **文档完整**: 清晰的注释和文档字符串

## 性能考虑

- **异步处理**: 使用 BackgroundTasks 异步处理数据
- **线程池**: 数据轮询在独立线程运行
- **连接复用**: EyeLink 管理器单例模式
- **资源释放**: 生命周期钩子确保资源清理

## 版本历史

- v1.0.0 (2025-10-27): 重构版本，模块化设计

