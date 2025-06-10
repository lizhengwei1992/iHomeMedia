import json
import os
from typing import Dict, Optional

from app.core.config import MEDIA_ROOT


# 描述文件路径
DESCRIPTIONS_FILE = os.path.join(MEDIA_ROOT, "descriptions.json")


def load_descriptions() -> Dict[str, str]:
    """
    加载所有媒体描述
    """
    if not os.path.exists(DESCRIPTIONS_FILE):
        return {}
    
    try:
        with open(DESCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载描述文件失败: {e}")
        return {}


def save_descriptions(descriptions: Dict[str, str]) -> bool:
    """
    保存所有媒体描述
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(DESCRIPTIONS_FILE), exist_ok=True)
        
        with open(DESCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(descriptions, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存描述文件失败: {e}")
        return False


def get_media_description(media_id: str) -> Optional[str]:
    """
    获取特定媒体的描述
    """
    descriptions = load_descriptions()
    return descriptions.get(media_id)


def set_media_description(media_id: str, description: str) -> bool:
    """
    设置特定媒体的描述
    """
    descriptions = load_descriptions()
    descriptions[media_id] = description
    return save_descriptions(descriptions)


def delete_media_description(media_id: str) -> bool:
    """
    删除特定媒体的描述
    """
    descriptions = load_descriptions()
    if media_id in descriptions:
        del descriptions[media_id]
        return save_descriptions(descriptions)
    return True 