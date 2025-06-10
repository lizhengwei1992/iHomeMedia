#!/usr/bin/env python3
"""
检查向量数据库中的记录结构和向量内容
"""

import asyncio
import sys
import os
import hashlib

# 添加后端路径
sys.path.append('/home/lzw/app/family_media_app/backend')

async def check_vectors():
    """检查向量数据库记录"""
    print("=" * 60)
    print("检查向量数据库记录结构")
    print("=" * 60)
    
    try:
        from app.database.qdrant_manager import get_qdrant_manager
        from app.utils.file_handler import generate_global_media_id
        from app.core.config import PHOTOS_DIR
        from datetime import datetime
        import re
        
        # 获取向量数据库管理器
        qdrant_manager = get_qdrant_manager()
        
        # 获取所有记录
        print("1. 获取所有向量记录...")
        
        try:
            scroll_result = qdrant_manager.client.scroll(
                collection_name=qdrant_manager.collection_name,
                limit=10,
                with_payload=True,
                with_vectors=True
            )
            
            records = scroll_result[0]
            print(f"   找到 {len(records)} 条记录")
            
            for i, record in enumerate(records):
                print(f"\n记录 {i+1}:")
                print(f"   ID: {record.id}")
                
                # 检查payload
                payload = record.payload
                print(f"   全局媒体ID: {payload.get('global_media_id', '无')}")
                print(f"   文件名: {payload.get('file_name', '无')}")
                print(f"   描述: '{payload.get('description', '无')}'")
                print(f"   Embedding状态: {payload.get('embedding_status', '无')}")
                
                # 检查向量结构
                vectors = record.vector
                print(f"   向量类型: {type(vectors)}")
                
                if isinstance(vectors, dict):
                    print(f"   向量结构: 命名向量 (dict)")
                    for vector_name, vector_data in vectors.items():
                        if isinstance(vector_data, list):
                            non_zero_count = sum(1 for v in vector_data if v != 0.0)
                            print(f"     - {vector_name}: {len(vector_data)}维, {non_zero_count}个非零值")
                        else:
                            print(f"     - {vector_name}: {type(vector_data)}")
                else:
                    print(f"   向量结构: 密集向量 (list)")
                    if isinstance(vectors, list):
                        non_zero_count = sum(1 for v in vectors if v != 0.0)
                        print(f"     总维度: {len(vectors)}, 非零值: {non_zero_count}")
                
        except Exception as e:
            print(f"   ❌ 获取记录失败: {e}")
        
        # 2. 检查本地文件并尝试查找
        print(f"\n2. 检查本地文件并验证ID匹配...")
        
        local_files = []
        if os.path.exists(PHOTOS_DIR):
            for root, dirs, files in os.walk(PHOTOS_DIR):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.heic')):
                        local_files.append(file)
        
        print(f"   本地文件数: {len(local_files)}")
        
        for file in local_files:
            print(f"\n   检查文件: {file}")
            
            # 从文件名提取信息
            timestamp_pattern = r'_(\d{14})\.'
            match = re.search(timestamp_pattern, file)
            
            if match:
                timestamp_str = match.group(1)
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                upload_time_iso = timestamp.isoformat()
                
                # 提取原始文件名
                original_name = file.split('_' + timestamp_str)[0] + '.' + file.split('.')[-1]
                
                # 生成全局媒体ID
                global_media_id = generate_global_media_id(original_name, upload_time_iso)
                
                print(f"     原始名: {original_name}")
                print(f"     时间: {upload_time_iso}")
                print(f"     全局ID: {global_media_id}")
                
                # 转换为数字ID查找
                point_id = global_media_id
                if isinstance(global_media_id, str) and not global_media_id.isdigit():
                    point_id = int(hashlib.md5(global_media_id.encode()).hexdigest()[:15], 16)
                
                print(f"     数字ID: {point_id}")
                
                # 尝试在数据库中查找
                try:
                    existing_points = qdrant_manager.client.retrieve(
                        collection_name=qdrant_manager.collection_name,
                        ids=[point_id],
                        with_payload=True,
                        with_vectors=True
                    )
                    
                    if existing_points:
                        point = existing_points[0]
                        print(f"     ✅ 在数据库中找到记录")
                        print(f"     - 记录描述: '{point.payload.get('description', '无')}'")
                        
                        # 检查向量
                        vectors = point.vector
                        if isinstance(vectors, dict):
                            text_vector = vectors.get('text_embedding', [])
                            image_vector = vectors.get('image_embedding', [])
                            
                            text_non_zero = sum(1 for v in text_vector if v != 0.0) if text_vector else 0
                            image_non_zero = sum(1 for v in image_vector if v != 0.0) if image_vector else 0
                            
                            print(f"     - 文本向量: {len(text_vector) if text_vector else 0}维, {text_non_zero}个非零值")
                            print(f"     - 图像向量: {len(image_vector) if image_vector else 0}维, {image_non_zero}个非零值")
                        else:
                            print(f"     - 向量格式: 非命名向量")
                            
                    else:
                        print(f"     ❌ 在数据库中未找到记录")
                        
                except Exception as e:
                    print(f"     ❌ 查找失败: {e}")
        
        print(f"\n" + "=" * 60)
        print("检查结论:")
        print("=" * 60)
        
        if len(records) > 0:
            # 检查向量格式是否正确
            sample_record = records[0]
            vectors = sample_record.vector
            
            if isinstance(vectors, dict):
                has_text = 'text_embedding' in vectors
                has_image = 'image_embedding' in vectors
                
                print(f"✅ 向量格式: 命名向量")
                print(f"✅ 包含文本向量: {has_text}")
                print(f"✅ 包含图像向量: {has_image}")
                
                if has_text and has_image:
                    print("✅ 向量结构正确")
                else:
                    print("❌ 向量结构不完整")
            else:
                print("❌ 向量格式错误: 应该使用命名向量格式")
        else:
            print("❌ 没有找到任何记录")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_vectors()) 