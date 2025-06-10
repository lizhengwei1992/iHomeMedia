#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')

from app.services.vector_storage_service import get_vector_storage_service

async def test_simplified_search_strategy():
    """测试简化后的搜索策略 - 同时搜索文本和图像模态"""
    
    print("🔍 测试简化后的搜索策略")
    print("=" * 60)
    
    try:
        vector_service = get_vector_storage_service()
        
        # 专门测试这两个查询
        test_queries = [
            ("女孩", "应该主要匹配包含女孩的图片"),
            ("风景", "应该主要匹配风景照片")
        ]
        
        for query, description in test_queries:
            print(f"\n🔎 测试查询: '{query}' ({description})")
            print("=" * 50)
            
            # 使用简化的搜索策略
            result = await vector_service.search_by_text(
                query=query,
                limit=10,
                threshold=0.7  # 阈值0.7
            )
            
            if result['success']:
                # 显示整体统计
                print(f"✅ 搜索完成 (阈值0.7):")
                print(f"   🔤 文本模态结果: {result.get('text_modal_count', 0)}个")
                print(f"   🖼️ 图像模态结果: {result.get('image_modal_count', 0)}个")
                print(f"   🔄 合并后结果: {result.get('final_count', 0)}个")
                print(f"   ⏱️ 搜索时间: {result.get('search_time', 0):.3f}s")
                print(f"   🧠 Embedding时间: {result.get('embedding_time', 0):.3f}s")
                print(f"   🎯 使用阈值: {result.get('threshold_used', 0.7)}")
                
                results = result.get('results', [])
                if results:
                    print(f"\n📋 详细结果分析 (阈值0.7):")
                    print("-" * 50)
                    
                    # 按搜索来源分类统计
                    source_stats = {"text_modal": 0, "image_modal": 0, "both_modals": 0}
                    
                    for i, item in enumerate(results):
                        metadata = item.get('metadata', {})
                        score = item.get('final_score', item.get('score', 0))
                        search_source = item.get('search_source', 'unknown')
                        media_id = item.get('media_id', 'N/A')
                        
                        file_name = metadata.get('file_name', 'N/A')
                        description_text = metadata.get('description', '')
                        
                        print(f"  [{i+1}] {file_name}")
                        print(f"      📊 最终分数: {score:.3f}")
                        print(f"      🎯 匹配来源: {search_source}")
                        print(f"      🆔 媒体ID: {str(media_id)[:12]}...")
                        if description_text:
                            print(f"      📝 描述: {description_text[:50]}...")
                        
                        # 显示更多技术细节
                        if 'original_score' in item:
                            print(f"      🔍 原始分数: {item['original_score']:.3f}")
                        
                        # 统计来源
                        if search_source in source_stats:
                            source_stats[search_source] += 1
                        
                        print()
                    
                    # 显示来源统计
                    print(f"📊 匹配来源统计 (阈值0.7):")
                    print(f"   🔤 仅文本模态: {source_stats['text_modal']}个")
                    print(f"   🖼️ 仅图像模态: {source_stats['image_modal']}个") 
                    print(f"   🔄 双重匹配: {source_stats['both_modals']}个")
                    
                else:
                    print(f"   ⚠️ 阈值0.7下没有找到结果")
                    
                    # 如果没有结果，尝试更低的阈值
                    print(f"\n🔍 尝试低阈值搜索 (阈值0.5):")
                    low_result = await vector_service.search_by_text(
                        query=query,
                        limit=5,
                        threshold=0.5  # 降低阈值
                    )
                    
                    if low_result['success']:
                        low_results = low_result.get('results', [])
                        print(f"   🔤 文本模态结果: {low_result.get('text_modal_count', 0)}个")
                        print(f"   🖼️ 图像模态结果: {low_result.get('image_modal_count', 0)}个")
                        print(f"   🔄 合并后结果: {low_result.get('final_count', 0)}个")
                        
                        if low_results:
                            print(f"\n   📋 低阈值结果:")
                            for i, item in enumerate(low_results[:3]):
                                metadata = item.get('metadata', {})
                                score = item.get('final_score', item.get('score', 0))
                                search_source = item.get('search_source', 'unknown')
                                file_name = metadata.get('file_name', 'N/A')
                                print(f"     [{i+1}] {file_name} - 分数:{score:.3f} - 来源:{search_source}")
                        else:
                            print("   ⚠️ 即使低阈值也没有找到结果")
                    
            else:
                print(f"❌ 搜索失败: {result.get('error', '未知错误')}")
            
            print()
        
        # 数据库统计
        print(f"\n📊 数据库状态检查")
        print("-" * 40)
        try:
            stats = await vector_service.get_collection_stats()
            print(f"集合名称: {stats.get('collection_name', 'N/A')}")
            print(f"向量数量: {stats.get('vectors_count', 'N/A')}")
            print(f"状态: {stats.get('status', 'N/A')}")
            print(f"模型: {stats.get('model_name', 'N/A')}")
        except Exception as e:
            print(f"获取统计信息失败: {str(e)}")
        
    except Exception as e:
        print(f"测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 简化搜索策略测试完成！")
    print("\n🎯 策略特点:")
    print("1. 同时搜索文本模态和图像模态")
    print("2. 阈值>0.7，确保高质量匹配")
    print("3. 智能合并去重，保留最佳分数")
    print("4. 清晰标记匹配来源类型")

if __name__ == '__main__':
    asyncio.run(test_simplified_search_strategy()) 