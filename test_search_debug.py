#!/usr/bin/env python3
"""
调试文本搜索问题的脚本
"""
import asyncio
import sys
import os

# 添加后端路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.embedding_service import get_embedding_service
from backend.app.services.vector_storage_service import get_vector_storage_service

async def test_search_debug():
    """测试搜索功能的调试"""
    
    print("🔍 开始调试文本搜索功能...")
    
    # 获取服务实例
    embedding_service = get_embedding_service()
    vector_storage = get_vector_storage_service()
    
    # 测试不同的查询词
    test_queries = [
        "游泳",
        "舟山海边玩",
        "千岛湖"
    ]
    
    for query in test_queries:
        print(f"\n--- 测试查询: '{query}' ---")
        
        # 1. 测试embedding生成
        print("1. 生成查询embedding...")
        query_result = await embedding_service.embed_query_text(query)
        
        if not query_result.get('success'):
            print(f"❌ Embedding生成失败: {query_result.get('error')}")
            continue
            
        print(f"✅ Embedding生成成功: {len(query_result['embedding'])}维")
        # 显示前5个向量值
        embedding_preview = query_result['embedding'][:5]
        print(f"   向量预览: {embedding_preview}")
        
        # 检查是否为零向量
        is_zero = all(x == 0.0 for x in query_result['embedding'])
        print(f"   是否为零向量: {is_zero}")
        
        # 2. 测试完整搜索流程
        print("2. 执行完整搜索...")
        search_result = await vector_storage.search_by_text(
            query=query,
            limit=5
        )
        
        if not search_result.get('success'):
            print(f"❌ 搜索失败: {search_result.get('error')}")
            continue
            
        results = search_result.get('results', [])
        print(f"✅ 搜索成功: 找到 {len(results)} 个结果")
        print(f"   搜索耗时: {search_result.get('search_time', 0):.3f}秒")
        print(f"   文本模态结果: {search_result.get('text_modal_count', 0)}")
        print(f"   图像模态结果: {search_result.get('image_modal_count', 0)}")
        
        # 显示结果详情
        for i, result in enumerate(results[:3]):  # 只显示前3个
            metadata = result.get('metadata', {})
            file_name = metadata.get('file_name', 'unknown')
            description = metadata.get('description', 'no description')
            score = result.get('final_score', result.get('score', 0))
            source = result.get('search_source', 'unknown')
            
            print(f"   结果 {i+1}: {file_name} (分数: {score:.3f}, 来源: {source})")
            print(f"            描述: {description[:50]}...")

if __name__ == "__main__":
    asyncio.run(test_search_debug()) 