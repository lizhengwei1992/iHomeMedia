# Qdrant命名向量搜索修复

## 问题描述

上传图片后出现搜索错误：

```
文本搜索失败: Unexpected Response: 400 (Bad Request)
Raw response content:
b'{"status":{"error":"Wrong input: Collection requires specified vector name in the request, available names: image_embedding, text_embedding"},"time":0.008613774}'
```

## 根本原因

Qdrant集合使用了**命名向量**（Named Vectors），包含两个向量：
- `text_embedding`: 文本embedding向量
- `image_embedding`: 图像embedding向量

但在搜索时没有指定要搜索哪个向量名称，导致Qdrant返回400错误。

## 解决方案

### 修复前的代码

```python
# 错误的搜索方式
search_result = await asyncio.to_thread(
    self.client.search,
    collection_name=self.collection_name,
    query_vector=query_vector,  # 没有指定向量名称
    limit=limit,
    score_threshold=threshold,
    query_filter=filters,
    with_payload=True
)
```

### 修复后的代码

```python
# 正确的搜索方式 - 文本搜索
search_result = await asyncio.to_thread(
    self.client.search,
    collection_name=self.collection_name,
    query_vector=("text_embedding", query_vector),  # 指定文本向量
    limit=limit,
    score_threshold=threshold,
    query_filter=filters,
    with_payload=True
)

# 正确的搜索方式 - 图像搜索
search_result = await asyncio.to_thread(
    self.client.search,
    collection_name=self.collection_name,
    query_vector=("image_embedding", query_vector),  # 指定图像向量
    limit=limit,
    score_threshold=threshold,
    query_filter=filters,
    with_payload=True
)
```

## 修改的文件

### `backend/app/database/qdrant_manager.py`

1. **`search_by_text` 方法**：
   - 修改 `query_vector=query_vector` 为 `query_vector=("text_embedding", query_vector)`

2. **`search_by_image` 方法**：
   - 修改 `query_vector=query_vector` 为 `query_vector=("image_embedding", query_vector)`

## 验证结果

修复后的测试结果：

```
=== 测试Qdrant搜索修复 ===
📝 测试文本搜索...
✅ 文本搜索成功: 返回 0 个结果
🖼️ 测试图像搜索...
✅ 图像搜索成功: 返回 3 个结果
🔄 测试多模态搜索...
✅ 多模态搜索成功: 返回 0 个结果

🎉 所有搜索测试通过！命名向量问题已修复
```

## 技术细节

### Qdrant命名向量语法

当集合使用命名向量时，搜索请求必须指定向量名称：

```python
# 格式: (向量名称, 向量数据)
query_vector = ("vector_name", vector_data)
```

### 集合结构

当前集合包含两个命名向量：
- `text_embedding`: 1024维文本embedding
- `image_embedding`: 1024维图像embedding

## 影响范围

修复解决了以下问题：
1. ✅ 上传图片时的文本搜索错误
2. ✅ 图像搜索功能
3. ✅ 多模态搜索功能
4. ✅ 搜索阈值配置（0.15）正常工作

## 注意事项

虽然Qdrant搜索问题已修复，但仍可能遇到DashScope API的500错误（"Failed to invoke backend!"），这是API服务端的问题，需要：

1. 检查API密钥是否有效
2. 检查DashScope服务状态
3. 考虑重试机制或备用方案

修复完成后，上传过程中的Qdrant搜索错误已消除。 