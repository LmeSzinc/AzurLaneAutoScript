import json
from starlette.responses import JSONResponse, HTMLResponse
from starlette.routing import Route
from module.logger import logger

def api_cl1_stats(request):
    try:
        from module.statistics.opsi_month import get_opsi_stats
        instance_name = request.query_params.get("instance", "alas")
        stats = get_opsi_stats(instance_name=instance_name).get_detailed_summary()
        return JSONResponse({"success": True, "data": stats})
    except Exception as e:
        logger.error(f"api_cl1_stats error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

def api_ap_timeline(request):
    try:
        from module.statistics.opsi_month import get_ap_timeline
        instance_name = request.query_params.get("instance", "alas")
        timeline = get_ap_timeline(instance_name=instance_name)
        return JSONResponse({"success": True, "data": timeline})
    except Exception as e:
        logger.error(f"api_ap_timeline error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

def serve_obs_overlay(request):
    """
    提供OBS专用覆盖层页面
    用户可以在浏览器中访问 http://IP:PORT/obs 或者在OBS中添加浏览器源
    """
    try:
        html_path = "module/webui/obs_overlay.html"
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content)
    except Exception as e:
        return HTMLResponse(f"Error loading obs overlay: {e}", status_code=500)

api_routes = [
    Route("/api/cl1_stats", api_cl1_stats),
    Route("/api/ap_timeline", api_ap_timeline),
    Route("/obs", serve_obs_overlay),
]
