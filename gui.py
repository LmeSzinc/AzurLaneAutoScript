import os
import sys
import threading
from multiprocessing import Event, Process, set_start_method
from typing import Optional

from module.logger import logger
from module.webui.setting import State


def func(ev: Optional[Event]):
    """
    主函数：运行Web服务。

    Args:
        ev: 可选的重启事件，用于热重载功能
    """
    import argparse
    import asyncio
    import uvicorn

    # 平台特定的asyncio配置
    if sys.platform == "darwin":
        # macOS: 禁用fork安全检查以避免Mach端口冲突
        os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    elif sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    State.restart_event = ev

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Alas web service")
    parser.add_argument(
        "--host",
        type=str,
        help="监听主机。默认使用部署设置中的WebuiHost",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="监听端口。默认使用部署设置中的WebuiPort",
    )
    parser.add_argument(
        "-k", "--key", type=str, help="Alas密码。默认无密码"
    )
    parser.add_argument(
        "--cdn",
        action="store_true",
        help="使用jsdelivr CDN获取pywebio静态文件（css, js）。默认使用自托管CDN",
    )
    parser.add_argument(
        "--electron", action="store_true", help="由Electron客户端运行"
    )
    parser.add_argument(
        "--ssl-key", dest="ssl_key", type=str, help="SSL密钥文件路径，用于HTTPS支持"
    )
    parser.add_argument(
        "--ssl-cert", type=str, help="SSL证书文件路径，用于HTTPS支持"
    )
    parser.add_argument(
        "--run",
        nargs="+",
        type=str,
        help="启动时运行指定配置的Alas",
    )
    args, _ = parser.parse_known_args()

    # 配置服务器设置
    host = args.host or State.deploy_config.WebuiHost or "0.0.0.0"
    port = args.port or int(State.deploy_config.WebuiPort) or 22267
    ssl_key = args.ssl_key or State.deploy_config.WebuiSSLKey
    ssl_cert = args.ssl_cert or State.deploy_config.WebuiSSLCert
    ssl = ssl_key is not None and ssl_cert is not None
    State.electron = args.electron

    # 记录启动器配置
    logger.hr("Launcher config")
    logger.attr("Host", host)
    logger.attr("Port", port)
    logger.attr("SSL", ssl)
    logger.attr("Electron", args.electron)
    logger.attr("Reload", ev is not None)

    # Electron客户端特定处理
    if State.electron:
        # https://github.com/LmeSzinc/AzurLaneAutoScript/issues/2051
        logger.info("Electron detected, remove log output to stdout")
        from module.logger import console_hdlr
        logger.removeHandler(console_hdlr)

    # 验证SSL配置
    if ssl_cert is None and ssl_key is not None:
        logger.error("提供了SSL密钥但未提供证书。请同时提供SSL密钥和证书。")
    elif ssl_key is None and ssl_cert is not None:
        logger.error("提供了SSL证书但未提供密钥。请同时提供SSL密钥和证书。")

    # 启动uvicorn服务器
    try:
        if ssl:
            uvicorn.run(
                "module.webui.app:app",
                host=host,
                port=port,
                factory=True,
                ssl_keyfile=ssl_key,
                ssl_certfile=ssl_cert
            )
        else:
            uvicorn.run("module.webui.app:app", host=host, port=port, factory=True)
    except Exception as e:
        logger.error(f"Uvicorn服务崩溃: {str(e)}")
        raise


if __name__ == "__main__":
    # 设置multiprocessing启动方式为spawn（macOS兼容性要求）
    try:
        set_start_method("spawn", force=True)
        # 额外的macOS环境配置
        if os.name == "posix" and sys.platform == "darwin":
            os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    except RuntimeError:
        logger.warning("无法设置spawn启动方式，可能使用fork（macOS上不推荐）")

    # 启用热重载模式
    if State.deploy_config.EnableReload:
        should_exit = False
        while not should_exit:
            event = Event()
            process = Process(target=func, args=(event,), name="gui")
            process.start()
            logger.info(f"启动Alas Web服务 (PID: {process.pid})")

            while not should_exit:
                try:
                    # 等待重启事件，超时1秒
                    restart_triggered = event.wait(1)
                except KeyboardInterrupt:
                    logger.info("收到KeyboardInterrupt，退出中...")
                    should_exit = True
                    break
                except Exception as e:
                    logger.error(f"等待重启事件时出错: {str(e)}")
                    should_exit = True
                    break

                if restart_triggered:
                    logger.info("重启事件触发，终止当前服务...")
                    process.kill()
                    process.join(timeout=5)
                    if process.is_alive():
                        logger.warning("无法终止服务进程，强制退出")
                    break
                elif not process.is_alive():
                    logger.error("Alas Web服务意外退出")
                    should_exit = True

            # 确保子进程完全退出
            if process.is_alive():
                process.terminate()
                process.join(timeout=3)

        # 最终清理
        if process.is_alive():
            process.kill()
            process.join()
        logger.info("Alas Web服务已成功退出")
    else:
        # 非重载模式：直接运行
        func(None)
