import http.server
import socketserver
import mimetypes # 导入mimetypes模块

PORT = 8000 # 你可以选择一个不同的端口，比如 5000, 3000

# 确保 .js 文件被识别为 application/javascript
mimetypes.add_type("application/javascript", ".js")
# 也可以加上 text/javascript，有些浏览器或旧规范可能更偏向它
mimetypes.add_type("text/javascript", ".js")


# 使用 SimpleHTTPRequestHandler 作为处理程序
Handler = http.server.SimpleHTTPRequestHandler

# 创建一个TCP服务器实例，绑定到所有可用接口和指定端口
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"正在 {PORT} 端口提供服务")
    print(f"请在浏览器中访问: http://localhost:{PORT}/admin.html")
    # 永久运行服务器
    httpd.serve_forever()