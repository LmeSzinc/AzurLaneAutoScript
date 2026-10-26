import sys
import argparse
from pathlib import Path

# 确保项目根目录在 sys.path 首位
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

def create_app():
    from fastapi import FastAPI
    from module.api.router import router
    from module.api.mcp_server import mcp

    app = FastAPI(
        title="Alas API & MCP Server",
        description="AzurLaneAutoScript 原生增量 RESTful API 与 Model Context Protocol (MCP) 服务",
        version="1.0.0"
    )

    # 挂载 REST API 路由 (/api/...)
    app.include_router(router)

    # 挂载 MCP SSE 传输端点 (/mcp/sse)
    app.mount("/mcp", mcp.sse_app())

    @app.get("/")
    def index():
        return {
            "name": "Alas API & MCP Server",
            "version": "1.0.0",
            "docs_url": "/docs",
            "mcp_sse_endpoint": "/mcp/sse",
            "endpoints": {
                "get_status": "/api/status",
                "refresh_resources": "/api/resources/refresh",
                "get_all_tasks": "/api/config/tasks",
                "get_task_config": "/api/config/task/{task_name}",
                "update_task_config": "/api/config/task",
                "trigger_task": "/api/task/trigger",
                "start_process": "/api/process/start",
                "stop_process": "/api/process/stop",
                "get_logs": "/api/logs"
            }
        }

    return app

def main():
    parser = argparse.ArgumentParser(description="Alas Unified API & MCP Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="绑定监听的主机地址 (默认: 127.0.0.1)")
    parser.add_argument("-p", "--port", type=int, default=8000, help="服务端口 (默认: 8000)")
    parser.add_argument("--mcp-stdio", action="store_true", help="以 stdio 管道模式运行 MCP Server (供 Claude Desktop / Cursor 本地调用)")

    args = parser.parse_args()

    if args.mcp_stdio:
        # stdio 模式供 MCP 客户端直接作为子进程调用
        from module.api.mcp_server import mcp
        mcp.run(transport="stdio")
    else:
        # HTTP / SSE 模式：同时提供 REST API 和 MCP SSE 端点
        import uvicorn
        app = create_app()

        print("\n" + "="*60)
        print(" [Alas API & MCP Server] 正在启动一体化服务")
        print(f" - REST API 文档 (Swagger) : http://{args.host}:{args.port}/docs")
        print(f" - 状态与资源端点          : http://{args.host}:{args.port}/api/status")
        print(f" - MCP SSE 接入端点        : http://{args.host}:{args.port}/mcp/sse")
        print("="*60 + "\n")

        uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
