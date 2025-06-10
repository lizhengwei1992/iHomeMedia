#!/usr/bin/env python3
"""
数据库清理和媒体文件管理工具
功能：
1. 清空向量数据库
2. 删除所有媒体文件
3. 打印数据库状态
4. 提供安全确认机制
"""

import asyncio
import sys
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database.qdrant_manager import get_qdrant_manager
from app.services.vector_storage_service import get_vector_storage_service
from app.core.config import settings

# 媒体文件存储路径
MEDIA_ROOT = '/media'
PHOTOS_DIR = '/media/photos'
VIDEOS_DIR = '/media/videos'
THUMBNAILS_ROOT = '/media/thumbnails'
DESCRIPTIONS_FILE = '/media/descriptions.json'

class DatabaseCleanupTool:
    """数据库清理工具"""
    
    def __init__(self):
        self.qdrant_manager = get_qdrant_manager()
        self.vector_service = get_vector_storage_service()
    
    async def print_database_status(self):
        """打印数据库状态"""
        print("📊 数据库状态检查")
        print("=" * 60)
        
        try:
            # 获取集合信息 - 使用统一的方法
            collection_info = await self.vector_service.get_storage_stats()
            
            print(f"🔍 Qdrant向量数据库:")
            print(f"   集合名称: {collection_info.get('collection_name', 'N/A')}")
            print(f"   总Embedding数: {collection_info.get('total_embeddings', 0)}")
            print(f"   向量数量: {collection_info.get('vectors_count', 0)}")
            print(f"   状态: {collection_info.get('status', 'N/A')}")
            print(f"   向量维度: {collection_info.get('vector_dimension', 'N/A')}")
            
            model_info = collection_info.get('model_info', {})
            print(f"   模型名称: {model_info.get('model_name', 'N/A')}")
            print(f"   支持类型: {model_info.get('supported_types', 'N/A')}")
            
            # 获取媒体文件统计
            media_stats = self.get_media_files_stats()
            print(f"\n📁 媒体文件存储:")
            print(f"   媒体根目录: {MEDIA_ROOT}")
            print(f"   照片目录: {PHOTOS_DIR}")
            print(f"   视频目录: {VIDEOS_DIR}")
            print(f"   缩略图目录: {THUMBNAILS_ROOT}")
            print(f"   媒体文件数量: {media_stats['media_count']}")
            print(f"   缩略图数量: {media_stats['thumbnail_count']}")
            print(f"   总存储大小: {media_stats['total_size_mb']:.2f} MB")
            print(f"   描述文件: {'存在' if os.path.exists(DESCRIPTIONS_FILE) else '不存在'}")
            
            # 检查一致性
            total_embeddings = collection_info.get('total_embeddings', 0)
            media_count = media_stats['media_count']
            
            print(f"\n🔗 数据一致性:")
            if total_embeddings == media_count:
                print(f"   ✅ Embedding数据与媒体文件数量一致 ({total_embeddings})")
            else:
                print(f"   ⚠️ 数据不一致: Embedding{total_embeddings}个 vs 媒体文件{media_count}个")
                if total_embeddings > 0 and media_count > 0:
                    print(f"   💡 这可能表示有embedding但向量数据损坏或存储失败")
                
        except Exception as e:
            print(f"❌ 获取数据库状态失败: {str(e)}")
    
    def get_media_files_stats(self) -> Dict[str, Any]:
        """获取媒体文件统计信息"""
        stats = {
            'media_count': 0,
            'thumbnail_count': 0,
            'total_size_mb': 0.0
        }
        
        try:
            # 统计照片文件
            if os.path.exists(PHOTOS_DIR):
                for root, dirs, files in os.walk(PHOTOS_DIR):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.webp', '.gif', '.bmp')):
                            stats['media_count'] += 1
                            file_path = os.path.join(root, file)
                            if os.path.exists(file_path):
                                stats['total_size_mb'] += os.path.getsize(file_path) / (1024 * 1024)
            
            # 统计视频文件
            if os.path.exists(VIDEOS_DIR):
                for root, dirs, files in os.walk(VIDEOS_DIR):
                    for file in files:
                        if file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm')):
                            stats['media_count'] += 1
                            file_path = os.path.join(root, file)
                            if os.path.exists(file_path):
                                stats['total_size_mb'] += os.path.getsize(file_path) / (1024 * 1024)

            # 统计缩略图
            if os.path.exists(THUMBNAILS_ROOT):
                for root, dirs, files in os.walk(THUMBNAILS_ROOT):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            stats['thumbnail_count'] += 1
                            file_path = os.path.join(root, file)
                            if os.path.exists(file_path):
                                stats['total_size_mb'] += os.path.getsize(file_path) / (1024 * 1024)
                                
        except Exception as e:
            print(f"⚠️ 统计媒体文件失败: {str(e)}")
        
        return stats
    
    async def clear_vector_database(self, confirm: bool = False):
        """清空向量数据库"""
        if not confirm:
            print("⚠️ 此操作将删除所有向量数据，不可恢复！")
            response = input("确认清空向量数据库？输入 'yes' 确认: ")
            if response.lower() != 'yes':
                print("❌ 操作已取消")
                return False
        
        try:
            print("🗑️ 开始清空向量数据库...")
            
            # 删除集合（这会删除所有向量数据）
            success = await self.qdrant_manager.delete_collection()
            
            if success:
                # 重新创建空集合
                await self.qdrant_manager.ensure_collection_exists()
                print("✅ 向量数据库已清空并重新初始化")
                return True
            else:
                print("❌ 清空向量数据库失败")
                return False
                
        except Exception as e:
            print(f"❌ 清空向量数据库异常: {str(e)}")
            return False
    
    def delete_media_files(self, confirm: bool = False):
        """删除所有媒体文件和缩略图"""
        if not confirm:
            stats = self.get_media_files_stats()
            print("⚠️ 此操作将删除以下内容，不可恢复！")
            print(f"   📷 照片文件: {self._count_files_in_dir(PHOTOS_DIR, ['.jpg', '.jpeg', '.png', '.heic', '.webp', '.gif', '.bmp'])}个")
            print(f"   🎬 视频文件: {self._count_files_in_dir(VIDEOS_DIR, ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'])}个")
            print(f"   🖼️ 缩略图文件: {stats['thumbnail_count']}个")
            print(f"   📝 描述文件: {'存在' if os.path.exists(DESCRIPTIONS_FILE) else '不存在'}")
            print(f"   💾 总大小: {stats['total_size_mb']:.2f} MB")
            print(f"\n🔒 保留目录: qdrant数据库、lost+found")
            response = input("确认删除所有媒体文件？输入 'DELETE' 确认: ")
            if response != 'DELETE':
                print("❌ 操作已取消")
                return False
        
        try:
            deleted_files = 0
            deleted_size = 0.0
            
            print("🗑️ 开始删除媒体文件...")
            
            # 删除照片文件
            if os.path.exists(PHOTOS_DIR):
                deleted_count, deleted_mb = self._delete_media_files_in_dir(
                    PHOTOS_DIR, 
                    ['.jpg', '.jpeg', '.png', '.heic', '.webp', '.gif', '.bmp'],
                    "照片"
                )
                deleted_files += deleted_count
                deleted_size += deleted_mb
            
            # 删除视频文件
            if os.path.exists(VIDEOS_DIR):
                deleted_count, deleted_mb = self._delete_media_files_in_dir(
                    VIDEOS_DIR,
                    ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'],
                    "视频"
                )
                deleted_files += deleted_count
                deleted_size += deleted_mb
            
            # 删除缩略图
            if os.path.exists(THUMBNAILS_ROOT):
                deleted_count, deleted_mb = self._delete_media_files_in_dir(
                    THUMBNAILS_ROOT,
                    ['.jpg', '.jpeg', '.png', '.webp'],
                    "缩略图"
                )
                deleted_files += deleted_count
                deleted_size += deleted_mb
            
            # 删除描述文件
            if os.path.exists(DESCRIPTIONS_FILE):
                try:
                    file_size = os.path.getsize(DESCRIPTIONS_FILE)
                    os.remove(DESCRIPTIONS_FILE)
                    deleted_files += 1
                    deleted_size += file_size / (1024 * 1024)
                    print(f"   ✅ 删除描述文件: {DESCRIPTIONS_FILE}")
                except Exception as e:
                    print(f"   ⚠️ 删除描述文件失败: {str(e)}")
            
            print(f"\n✅ 清理完成！")
            print(f"   📁 删除文件数: {deleted_files}")
            print(f"   💾 释放空间: {deleted_size:.2f} MB")
            print(f"   🔒 保留了Qdrant数据库和系统目录")
            return True
            
        except Exception as e:
            print(f"❌ 删除媒体文件异常: {str(e)}")
            return False
    
    def _count_files_in_dir(self, directory: str, extensions: List[str]) -> int:
        """统计目录中指定扩展名的文件数量"""
        count = 0
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in extensions):
                        count += 1
        return count
    
    def _delete_media_files_in_dir(self, directory: str, extensions: List[str], file_type: str) -> Tuple[int, float]:
        """删除指定目录中的媒体文件"""
        deleted_count = 0
        deleted_size_mb = 0.0
        
        if not os.path.exists(directory):
            return deleted_count, deleted_size_mb
        
        print(f"   🗑️ 正在删除{file_type}...")
        
        # 删除文件
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_count += 1
                            deleted_size_mb += file_size / (1024 * 1024)
                    except Exception as e:
                        print(f"     ⚠️ 删除文件失败 {file_path}: {str(e)}")
        
        # 删除空目录（从最深层开始）
        for root, dirs, files in os.walk(directory, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if os.path.exists(dir_path) and not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        print(f"     📁 删除空目录: {dir_path}")
                except Exception as e:
                    print(f"     ⚠️ 删除空目录失败 {dir_path}: {str(e)}")
        
        # 如果根目录为空，也删除它
        try:
            if os.path.exists(directory) and not os.listdir(directory):
                os.rmdir(directory)
                print(f"     📁 删除根目录: {directory}")
        except Exception as e:
            print(f"     ⚠️ 删除根目录失败 {directory}: {str(e)}")
        
        if deleted_count > 0:
            print(f"   ✅ 删除{file_type}: {deleted_count}个文件, {deleted_size_mb:.2f} MB")
        
        return deleted_count, deleted_size_mb
    
    async def full_cleanup(self, confirm: bool = False):
        """完全清理：数据库+媒体文件"""
        if not confirm:
            print("⚠️ 此操作将：")
            print("   1. 清空向量数据库")
            print("   2. 删除所有媒体文件")
            print("   3. 删除所有缩略图")
            print("   ❗ 不可恢复！")
            response = input("确认完全清理？输入 'FULL_CLEANUP' 确认: ")
            if response != 'FULL_CLEANUP':
                print("❌ 操作已取消")
                return False
        
        print("🧹 开始完全清理...")
        
        # 1. 清空向量数据库
        db_success = await self.clear_vector_database(confirm=True)
        
        # 2. 删除媒体文件
        files_success = self.delete_media_files(confirm=True)
        
        if db_success and files_success:
            print("✅ 完全清理成功！")
            return True
        else:
            print("⚠️ 清理过程中有部分失败")
            return False

async def main():
    """主函数"""
    tool = DatabaseCleanupTool()
    
    if len(sys.argv) < 2:
        print("📋 数据库清理工具使用说明")
        print("=" * 60)
        print("可用命令:")
        print("  status          - 显示数据库和媒体文件状态")
        print("  clear-db        - 清空向量数据库")
        print("  delete-files    - 删除所有媒体文件")
        print("  full-cleanup    - 完全清理（数据库+文件）")
        print("\n示例:")
        print("  python database_cleanup_tool.py status")
        print("  python database_cleanup_tool.py clear-db")
        print("  python database_cleanup_tool.py full-cleanup")
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "status":
            await tool.print_database_status()
            
        elif command == "clear-db":
            await tool.clear_vector_database()
            print("\n执行后状态:")
            await tool.print_database_status()
            
        elif command == "delete-files":
            tool.delete_media_files()
            print("\n执行后状态:")
            await tool.print_database_status()
            
        elif command == "full-cleanup":
            await tool.full_cleanup()
            print("\n执行后状态:")
            await tool.print_database_status()
            
        else:
            print(f"❌ 未知命令: {command}")
            print("使用 'python database_cleanup_tool.py' 查看帮助")
            
    except KeyboardInterrupt:
        print("\n❌ 操作被用户取消")
    except Exception as e:
        print(f"❌ 执行异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 