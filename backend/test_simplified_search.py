#!/usr/bin/env python3
"""
测试简化的搜索策略
验证：同时搜索文本模态和图像模态，阈值>0.7，合并去重返回结果
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.vector_storage_service import VectorStorageService
from app.database.qdrant_manager import QdrantManager
from app.services.embedding_service import EmbeddingService
from app.core.dependencies import get_vector_storage_service

async def test_simplified_search():
    """测试简化的搜索策略"""
    print("=" * 60)
    print("🔍 测试简化搜索策略")
    print("=" * 60)
    
    try:
        # 初始化服务 - 使用依赖注入方式
        vector_service = get_vector_storage_service()
        
        # 测试查询
        test_queries = [
            "女孩",
            "人物", 
            "风景",
            "动物"
        ]
        
        for query in test_queries:
            print(f"\n📝 测试查询: '{query}'")
            print("-" * 40)
            
            # 执行搜索
            result = await vector_service.search_by_text(
                query=query,
                limit=10,
                threshold=0.7
            )
            
            if result['success']:
                print(f"✅ 搜索成功:")
                print(f"   - 文本模态结果: {result.get('text_modal_count', 0)}个")
                print(f"   - 图像模态结果: {result.get('image_modal_count', 0)}个") 
                print(f"   - 合并后结果: {result.get('final_count', 0)}个")
                print(f"   - 搜索耗时: {result.get('search_time', 0):.3f}秒")
                print(f"   - 使用阈值: {result.get('threshold_used', 0.7)}")
                
                # 显示前3个结果
                results = result.get('results', [])
                for i, item in enumerate(results[:3]):
                    print(f"   [{i+1}] ID: {item.get('media_id', 'N/A')[:8]}...")
                    print(f"       分数: {item.get('final_score', 0):.3f}")
                    print(f"       来源: {item.get('search_source', 'unknown')}")
                    print(f"       文件: {item.get('metadata', {}).get('file_name', 'N/A')}")
                    
            else:
                print(f"❌ 搜索失败: {result.get('error', '未知错误')}")
            
            print()
        
        # 检查数据库状态
        print("📊 数据库状态检查")
        print("-" * 40)
        await vector_service.check_collection_status()
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simplified_search()) 