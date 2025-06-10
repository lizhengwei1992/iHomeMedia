#!/usr/bin/env python3
import sys
sys.path.append('./backend')

from backend.app.utils.file_handler import list_media_files

def check_media_list():
    print("🔍 检查媒体列表函数返回的数据结构...")
    
    try:
        # 获取媒体列表
        result = list_media_files(page=1, page_size=5)
        
        print(f"✅ 找到 {result.get('total', 0)} 个媒体文件")
        print(f"📄 当前页面: {len(result.get('items', []))} 个项目")
        print('='*60)
        
        for i, item in enumerate(result.get('items', [])):
            print(f"📁 媒体项目 {i+1}:")
            print(f"  🆔 id: {item.get('id')}")
            print(f"  📝 name: {item.get('name')}")
            print(f"  📄 type: {item.get('type')}")
            print(f"  🔗 url: {item.get('url')}")
            print(f"  🖼️ thumbnail_url: {item.get('thumbnail_url')}")
            print(f"  📂 path: {item.get('path')}")
            print(f"  📏 size: {item.get('size')}")
            print(f"  📅 upload_date: {item.get('upload_date')}")
            print(f"  📝 description: {item.get('description')}")
            if item.get('width') and item.get('height'):
                print(f"  📐 dimensions: {item.get('width')} x {item.get('height')}")
            print('-'*60)
            
        # 比较搜索结果中的file_id和媒体列表中的id
        print("\n🔍 对比分析:")
        search_file_ids = [
            "IMG_4653_20250610153015.jpeg",
            "IMG_4649_20250610153023.png", 
            "IMG_4654_20250610153019.jpeg"
        ]
        
        media_list_ids = [item.get('id') for item in result.get('items', [])]
        
        print("📊 搜索结果中的file_id:")
        for file_id in search_file_ids:
            print(f"  - {file_id}")
            
        print("📊 媒体列表中的id:")
        for item_id in media_list_ids:
            print(f"  - {item_id}")
            
        print("🔍 匹配情况:")
        for file_id in search_file_ids:
            if file_id in media_list_ids:
                print(f"  ✅ {file_id} - 匹配")
            else:
                print(f"  ❌ {file_id} - 不匹配")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_media_list() 