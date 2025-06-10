# 🗄️ 向量数据库测试指南

## 📋 测试目标

确认媒体文件上传后，图像embedding和文本embedding能够正确存储到Qdrant向量数据库中，并且搜索功能正常工作。

---

## 🧪 测试环境准备

### 1. 确认服务状态

确保以下服务正在运行：
- ✅ Qdrant向量数据库 (端口6333)
- ✅ 后端API服务 (端口5000)
- ✅ 前端服务 (端口3000)
- ✅ 阿里云DashScope API Key已配置

### 2. 启动监控脚本

```bash
cd backend
python3 test_media_embedding_flow.py
```

这个脚本会：
- 检查向量数据库当前状态
- 实时监控向量数量变化
- 显示新增向量的详细信息
- 测试搜索功能

---

## 📊 测试步骤

### 阶段1: 基础连接测试

1. **运行基础测试**
   ```bash
   cd backend
   python3 -c "
   import asyncio
   from app.database.qdrant_manager import init_qdrant, get_qdrant_manager
   
   async def test():
       await init_qdrant()
       manager = get_qdrant_manager()
       info = await manager.get_collection_info()
       print('向量数据库状态:', info)
   
   asyncio.run(test())
   "
   ```

2. **期望结果**
   - ✅ 连接成功
   - ✅ 集合 `media_embeddings` 存在
   - ✅ 显示当前向量数量

### 阶段2: 文件上传测试

1. **准备测试文件**
   - 选择2-3张不同类型的图片文件
   - 文件大小 < 500MB
   - 支持格式：.jpg, .jpeg, .png, .heic, .webp

2. **执行上传操作**
   - 通过前端界面 (http://localhost:3000) 登录
   - 上传准备好的测试文件
   - 观察上传进度和成功提示

3. **监控向量变化**
   - 查看 `test_media_embedding_flow.py` 脚本输出
   - 应该看到向量数量实时增加
   - 每个文件对应一个向量点（包含文本和图像embedding）

### 阶段3: 向量存储验证

**期望的监控输出示例：**
```
📈 [22:25:30] 向量数量变化: 0 → 1 (+1)
   📋 最新的向量记录:
     1. ID: 123456789012345678
        文件: /media/photos/2025-06-09/IMG_4656_20250609222530.jpeg
        类型: image
        时间: 2025-06-09T22:25:30
```

**检查要点：**
- ✅ 每上传一个文件，向量数量 +1
- ✅ 向量记录包含正确的文件路径
- ✅ 文件类型正确识别
- ✅ 上传时间准确记录

### 阶段4: 搜索功能测试

1. **文本搜索测试**
   - 在前端搜索框输入："照片"、"图像"、"风景"等关键词
   - 观察搜索结果是否返回相关文件

2. **后端搜索API测试**
   ```bash
   curl -X POST "http://localhost:5000/api/v1/search/text" \
   -H "Content-Type: application/json" \
   -H "Authorization: Bearer YOUR_TOKEN" \
   -d '{"query": "照片", "limit": 5}'
   ```

3. **期望结果**
   - ✅ 搜索返回相关文件
   - ✅ 相似度分数合理 (0.0-1.0)
   - ✅ 结果按相似度排序

---

## 🔍 详细验证方法

### 方法1: 通过监控脚本

**实时监控上传过程：**
1. 运行 `test_media_embedding_flow.py`
2. 保持脚本运行状态
3. 通过前端上传文件
4. 观察脚本输出的变化

### 方法2: 手动检查向量数据库

```bash
cd backend
python3 -c "
import asyncio
from app.database.qdrant_manager import get_qdrant_manager, init_qdrant

async def check_vectors():
    await init_qdrant()
    manager = get_qdrant_manager()
    
    # 获取集合信息
    info = await manager.get_collection_info()
    print(f'📊 集合统计: {info}')
    
    # 搜索所有向量
    dummy_vector = [0.0] * 1024
    results = await manager.search_by_text(dummy_vector, limit=10, score_threshold=0.0)
    
    print(f'📋 向量记录 ({len(results)} 个):')
    for i, result in enumerate(results):
        metadata = result.get('metadata', {})
        print(f'  {i+1}. {metadata.get(\"file_path\", \"N/A\")}')
        print(f'     类型: {metadata.get(\"file_type\", \"N/A\")}')
        print(f'     时间: {metadata.get(\"upload_time\", \"N/A\")}')

asyncio.run(check_vectors())
"
```

### 方法3: 搜索功能验证

```bash
cd backend
python3 -c "
import asyncio
from app.services.vector_storage_service import get_vector_storage_service

async def test_search():
    service = get_vector_storage_service()
    
    # 测试不同搜索词
    test_queries = ['照片', '图像', '风景', '人物', '动物']
    
    for query in test_queries:
        results = await service.search_by_text(query, limit=3)
        print(f'🔍 搜索 \"{query}\": {len(results)} 个结果')
        
        for i, result in enumerate(results):
            metadata = result.get('metadata', {})
            score = result.get('score', 0)
            print(f'  {i+1}. {metadata.get(\"file_path\", \"N/A\")} (分数: {score:.4f})')

asyncio.run(test_search())
"
```

---

## ✅ 成功标准

### 向量存储成功的标志：

1. **数量一致性**
   - 上传N个文件 = 向量数据库中有N个向量点

2. **元数据完整性**
   - 每个向量包含完整的文件信息
   - 文件路径、类型、时间等信息准确

3. **搜索功能正常**
   - 文本搜索能返回相关结果
   - 相似度分数合理
   - 响应时间 < 2秒

4. **embedding质量**
   - 向量维度 = 1024
   - 向量值在合理范围内（通常 -1 到 1）

### 常见问题排查：

**问题1: 向量数量不增加**
- 检查embedding服务是否正常工作
- 查看后端日志中的错误信息
- 确认阿里云API Key配置正确

**问题2: 搜索无结果**
- 确认向量数据已成功存储
- 检查搜索阈值设置
- 验证搜索查询向量生成

**问题3: 向量信息不完整**
- 检查媒体文件上传时的元数据提取
- 确认文件路径和时间信息正确

---

## 📈 性能基准

### 预期性能指标：

- **上传处理时间**: 每个文件 < 10秒
- **搜索响应时间**: < 2秒
- **向量存储延迟**: < 5秒
- **内存使用**: Qdrant进程 < 1GB

### 扩容测试：

可以测试批量上传多个文件，验证系统在负载下的表现：

1. 准备10-20个测试文件
2. 批量上传
3. 监控系统资源使用
4. 验证所有文件的向量都正确存储

---

## 🎯 下一步优化

完成基础测试后，可以考虑：

1. **搜索体验优化**
   - 调整相似度阈值
   - 优化搜索结果排序

2. **性能优化**
   - 配置Qdrant索引参数
   - 优化embedding批处理

3. **功能扩展**
   - 添加按文件类型过滤
   - 支持时间范围搜索
   - 实现相似图片推荐

使用这个测试指南，您应该能够全面验证向量数据库的功能是否正常工作！🚀 