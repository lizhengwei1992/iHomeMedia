# 搜索阈值配置说明

## 概述

搜索相似度阈值已被设置为**0.15**，并且只能通过环境变量配置。前后端都不允许修改此值，确保搜索质量的一致性。

## 配置方式

### 环境变量配置

在 `.local.env` 文件中设置：

```env
# 搜索配置
SEARCH_THRESHOLD=0.15
```

### 后端配置

在 `backend/app/core/config.py` 中：

```python
# 搜索配置
SEARCH_THRESHOLD: float = 0.15  # 搜索相似度阈值，只能通过环境变量配置
```

## 实现细节

### 1. 配置读取

- 后端通过 `settings.SEARCH_THRESHOLD` 读取配置值
- 所有搜索相关的服务都使用此统一配置

### 2. 前端限制

- 前端API接口已移除 `threshold` 参数
- 前端无法传递自定义阈值给后端

### 3. 后端强制执行

以下组件已更新为强制使用配置的阈值：

#### 搜索模型 (`app/models/search_models.py`)
```python
# 所有模型的阈值字段都使用配置值作为默认值
threshold: float = Field(default=settings.SEARCH_THRESHOLD, ...)
```

#### 向量存储服务 (`app/services/vector_storage_service.py`)
```python
# 搜索方法忽略传入的阈值参数，强制使用配置值
search_threshold = settings.SEARCH_THRESHOLD
```

#### Qdrant管理器 (`app/database/qdrant_manager.py`)
```python
# 所有搜索方法都使用配置的阈值
threshold = score_threshold if score_threshold is not None else settings.SEARCH_THRESHOLD
```

#### 搜索路由 (`app/routers/search.py`)
```python
# 路由不传递用户的阈值参数
search_results = await vector_service.search_by_text(
    query=request.query,
    limit=request.limit
    # threshold参数不传递，让服务使用配置的阈值
)
```

## 阈值说明

### 当前值：0.15

- **含义**：相似度评分必须 ≥ 0.15 才会被返回
- **效果**：相对宽松的阈值，可以返回更多潜在相关的结果
- **范围**：0.0 (完全不相似) 到 1.0 (完全相似)

### 阈值影响

- **较低阈值 (如 0.15)**：返回更多结果，但可能包含一些相关性较低的内容
- **较高阈值 (如 0.7)**：返回较少但更精准的结果

## 修改方式

如需修改搜索阈值，**只能**通过以下方式：

1. 修改 `.local.env` 文件中的 `SEARCH_THRESHOLD` 值
2. 重启后端服务使配置生效

**注意**：前后端代码中都不允许硬编码或动态修改此值。

## 优势

1. **一致性**：确保所有搜索操作使用相同的阈值标准
2. **可配置性**：通过环境变量灵活调整，无需修改代码
3. **安全性**：防止前端或API调用者随意修改搜索质量标准
4. **可维护性**：集中配置管理，便于统一调优

## 测试验证

搜索API响应中会包含 `threshold_used` 字段，显示实际使用的阈值：

```json
{
  "success": true,
  "results": [...],
  "threshold_used": 0.15,
  "search_time": 0.123
}
```

这可以用于验证配置是否正确生效。 