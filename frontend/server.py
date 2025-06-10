#!/usr/bin/env python3
"""
增强版HTTP服务器，支持CORS和API代理转发，用于前后端分离开发
"""
import http.server
import socketserver
import os
import urllib.request
import urllib.error
from http import HTTPStatus
from urllib.parse import urlparse

PORT = 3000
DIRECTORY = "dist"
BACKEND_URL = "http://localhost:5000"  # 后端API地址

class ProxyCORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """支持CORS和API代理的HTTP请求处理器"""
    
    def __init__(self, *args, **kwargs):
        # 设置目录
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # 添加CORS头
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        super().end_headers()
    
    def do_OPTIONS(self):
        # 处理OPTIONS预检请求
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()
    
    def proxy_request(self):
        """代理请求到后端服务"""
        target_url = f"{BACKEND_URL}{self.path}"
        print(f"代理请求: {self.path} -> {target_url}")
        
        # 创建请求
        req = urllib.request.Request(target_url, method=self.command)
        
        # 复制请求头
        for header in self.headers:
            if header.lower() not in ('host', 'connection'):
                req.add_header(header, self.headers[header])
        
        # 添加代理相关头信息
        req.add_header('Host', urlparse(BACKEND_URL).netloc)
        req.add_header('X-Forwarded-For', self.client_address[0])
        
        # 处理请求体数据
        content_length = int(self.headers.get('Content-Length', 0))
        request_body = self.rfile.read(content_length) if content_length > 0 else None
        
        try:
            # 发送请求到后端
            response = urllib.request.urlopen(req, data=request_body)
            
            # 返回响应给客户端
            self.send_response(response.status)
            
            # 复制响应头
            for header in response.headers:
                if header.lower() not in ('transfer-encoding', 'connection'):
                    self.send_header(header, response.headers[header])
            
            self.end_headers()
            
            # 返回响应体
            self.wfile.write(response.read())
            
        except urllib.error.HTTPError as e:
            # 处理HTTP错误
            self.send_response(e.code)
            
            # 复制错误响应头
            for header in e.headers:
                if header.lower() not in ('transfer-encoding', 'connection'):
                    self.send_header(header, e.headers[header])
            
            self.end_headers()
            
            # 返回错误响应体
            if e.fp:
                self.wfile.write(e.fp.read())
        
        except Exception as e:
            # 处理其他错误
            self.send_error(
                HTTPStatus.BAD_GATEWAY,
                f"代理请求错误: {str(e)}"
            )
    
    def is_api_request(self):
        """判断是否为API请求或媒体文件请求"""
        return (self.path.startswith('/api/') or 
                self.path.startswith('/media/') or 
                self.path.startswith('/thumbnails/'))
    
    def do_GET(self):
        """处理GET请求"""
        if self.is_api_request():
            self.proxy_request()
        else:
            # 处理SPA应用的路由，任何非文件的路径都返回index.html
            if not os.path.exists(os.path.join(DIRECTORY, self.path.strip("/"))):
                if "." not in self.path:  # 没有扩展名，可能是前端路由
                    self.path = "/index.html"
            super().do_GET()
    
    def do_POST(self):
        """处理POST请求"""
        if self.is_api_request():
            self.proxy_request()
        else:
            super().do_POST()
    
    def do_PUT(self):
        """处理PUT请求"""
        if self.is_api_request():
            self.proxy_request()
        else:
            super().do_PUT()
    
    def do_DELETE(self):
        """处理DELETE请求"""
        if self.is_api_request():
            self.proxy_request()
        else:
            super().do_DELETE()
    
    def do_HEAD(self):
        """处理HEAD请求"""
        if self.is_api_request():
            self.proxy_request()
        else:
            super().do_HEAD()

def main():
    """主函数"""
    # 检查dist目录是否存在
    if not os.path.exists(DIRECTORY):
        print(f"错误: {DIRECTORY}目录不存在，请先构建前端")
        print("运行: npm run build")
        return
    
    # 设置处理器和服务器
    handler = ProxyCORSHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"===========================================")
        print(f"  前后端分离开发服务器 (带API代理功能)")
        print(f"===========================================")
        print(f"前端服务运行在: http://localhost:{PORT}")
        print(f"API请求将代理到: {BACKEND_URL}")
        print(f"静态文件目录: {DIRECTORY}")
        print("使用Ctrl+C停止服务")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务已停止")

if __name__ == "__main__":
    main() 