#!/usr/bin/env python3
import sys
import asyncio
sys.path.append('./backend')

from backend.app.services.vector_storage_service import get_vector_storage_service

async def test_search():
    print("🔍 测试搜索功能...")
    
    try:
        vector_service = get_vector_storage_service()
        
        # 测试几个搜索词
        test_queries = ["女孩", "人物", "照片", "图片", "风景"]
        
        for query in test_queries:
            print(f"\n🔍 搜索: '{query}'")
            
            # 执行搜索
            search_result = await vector_service.search_by_text(
                query=query,
                limit=5
            )
            
            if search_result.get('success'):
                results = search_result.get('results', [])
                print(f"  ✅ 找到 {len(results)} 个结果")
                
                for i, result in enumerate(results):
                    metadata = result.get('metadata', {})
                    print(f"    📁 结果 {i+1}:")
                    print(f"      🆔 media_id: {result.get('media_id')}")
                    print(f"      📊 score: {result.get('score', 0):.3f}")
                    print(f"      📝 file_name: {metadata.get('file_name', 'N/A')}")
                    print(f"      🔗 original_url: {metadata.get('original_url', 'N/A')}")
                    print(f"      🖼️ thumbnail_url: {metadata.get('thumbnail_url', 'N/A')}")
                    print(f"      📄 file_id: {metadata.get('file_id', 'N/A')}")
                    
            else:
                error = search_result.get('error', '未知错误')
                print(f"  ❌ 搜索失败: {error}")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search()) 