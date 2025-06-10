#!/usr/bin/env python3
"""
测试后端embedding服务API
"""

import requests
import json
import os
from pathlib import Path

def test_embedding_service():
    """测试embedding服务API"""
    base_url = "http://localhost:5000"
    
    print("🧪 测试后端embedding服务")
    print("=" * 50)
    
    # 1. 获取访问令牌
    print("🔐 获取访问令牌...")
    login_response = requests.post(
        f"{base_url}/api/v1/auth/token",
        data={"username": "family", "password": "123456"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        return False
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 获取令牌成功")
    
    # 2. 测试文本搜索API
    print("\n📝 测试文本搜索...")
    search_data = {
        "query": "测试照片",
        "limit": 5,
        "threshold": 0.5
    }
    
    search_response = requests.post(
        f"{base_url}/api/v1/search/text",
        json=search_data,
        headers=headers
    )
    
    print(f"搜索API响应状态: {search_response.status_code}")
    if search_response.status_code == 200:
        result = search_response.json()
        print(f"✅ 文本搜索成功: 找到 {len(result.get('results', []))} 个结果")
    else:
        print(f"❌ 文本搜索失败: {search_response.text}")
    
    # 3. 测试速率限制状态
    print("\n⏱️  检查速率限制状态...")
    rate_limit_response = requests.get(
        f"{base_url}/api/v1/search/rate-limit-status",
        headers=headers
    )
    
    if rate_limit_response.status_code == 200:
        rate_info = rate_limit_response.json()
        print("✅ 速率限制状态:")
        print(f"   剩余请求: {rate_info.get('remaining_requests', 'N/A')}")
        print(f"   窗口重置时间: {rate_info.get('window_reset_time', 'N/A')}")
    else:
        print(f"❌ 获取速率限制状态失败: {rate_limit_response.text}")
    
    # 4. 测试统计信息
    print("\n📊 获取统计信息...")
    stats_response = requests.get(
        f"{base_url}/api/v1/search/stats",
        headers=headers
    )
    
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print("✅ 统计信息:")
        print(f"   向量数据库状态: {stats.get('qdrant_status', 'N/A')}")
        print(f"   embedding服务状态: {stats.get('embedding_service_status', 'N/A')}")
    else:
        print(f"❌ 获取统计信息失败: {stats_response.text}")
    
    return True

if __name__ == "__main__":
    test_embedding_service() 