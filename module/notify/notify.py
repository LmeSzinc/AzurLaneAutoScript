import onepush.core
import yaml
from onepush import get_notifier
from onepush.core import Provider
from onepush.exceptions import OnePushException
from onepush.providers.custom import Custom
from urllib.parse import quote
from requests import Response
import requests

from module.logger import logger

onepush.core.log = logger


def handle_notify_meow(config: dict, **kwargs) -> bool:
    nickname = config.pop("nickname", None) or config.pop("name", None)
    if not nickname:
        logger.warning("Notifier meow require param 'nickname' but not provided")
        return False

    title = kwargs.get("title", config.pop("title", None))
    content = kwargs.get("content", config.pop("msg", None))
    if content is None:
        logger.warning("Notifier meow require param 'msg' but not provided")
        return False

    base = config.pop("api", None) or config.pop("api_url", None) or "https://api.chuckfang.com/"
    base = str(base).rstrip("/") + "/"
    url = f"{base}{quote(str(nickname), safe='')}"
    if title is not None:
        url = f"{url}/{quote(str(title), safe='')}"

    msg_type = str(config.pop("msgType", config.pop("msg_type", "text"))).lower()
    if msg_type not in ("text", "html"):
        logger.warning(f"Unknown meow msgType `{msg_type}`, fallback to `text`")
        msg_type = "text"
    params = {"msgType": msg_type}

    html_height = config.pop("htmlHeight", config.pop("html_height", None))
    if msg_type == "html" and html_height is not None:
        try:
            params["htmlHeight"] = int(html_height)
        except (TypeError, ValueError):
            logger.warning(f"Invalid meow htmlHeight `{html_height}`, skip")

    data = {"msg": str(content)}
    jump_url = kwargs.get("url", config.pop("url", None))
    if jump_url is not None:
        data["url"] = jump_url
    if title is not None:
        data["title"] = str(title)

    timeout = config.pop("timeout", 10)
    try:
        timeout = float(timeout)
    except (TypeError, ValueError):
        timeout = 10

    try:
        resp = requests.post(url=url, params=params, json=data, timeout=timeout)
        if resp.status_code != 200:
            logger.warning("Push notify failed!")
            logger.warning(f"HTTP Code:{resp.status_code}")
            return False
        try:
            result = resp.json()
            if int(result.get("status", 200)) != 200:
                logger.warning("Push notify failed!")
                logger.warning(f"Return message:{result.get('msg') or result.get('message')}")
                return False
        except Exception:
            # Response may not be JSON; rely on HTTP status code
            pass
    except Exception as e:
        logger.error(e)
        return False

    logger.info("Push notify success")
    return True


def handle_notify(_config: str, **kwargs) -> bool:
    try:
        config = {}
        for item in yaml.safe_load_all(_config):
            config.update(item)
    except Exception:
        logger.error("Fail to load onepush config, skip sending")
        return False
    try:
        provider_name: str = config.pop("provider", None)
        if provider_name is None:
            logger.info("No provider specified, skip sending")
            return False
        if provider_name.lower() in ("meow", "meowpush"):
            return handle_notify_meow(config, **kwargs)
        notifier: Provider = get_notifier(provider_name)
        required: list[str] = notifier.params["required"]
        config.update(kwargs)

        # pre check
        for key in required:
            if key not in config:
                logger.warning(
                    f"Notifier {notifier.name} require param '{key}' but not provided"
                )

        if isinstance(notifier, Custom):
            if "method" not in config or config["method"] == "post":
                config["datatype"] = "json"
            if not ("data" in config or isinstance(config["data"], dict)):
                config["data"] = {}
            if "title" in kwargs:
                config["data"]["title"] = kwargs["title"]
            if "content" in kwargs:
                config["data"]["content"] = kwargs["content"]

        if provider_name.lower() == "gocqhttp":
            access_token = config.get("access_token")
            if access_token:
                config["token"] = access_token

        resp = notifier.notify(**config)
        if isinstance(resp, Response):
            if resp.status_code != 200:
                logger.warning("Push notify failed!")
                logger.warning(f"HTTP Code:{resp.status_code}")
                return False
            else:
                if provider_name.lower() == "gocqhttp":
                    return_data: dict = resp.json()
                    if return_data["status"] == "failed":
                        logger.warning("Push notify failed!")
                        logger.warning(
                            f"Return message:{return_data['wording']}")
                        return False
    except OnePushException:
        logger.error("Push notify failed")
        return False
    except Exception as e:
        # don't show any exceptions because exceptions contain variable traceback
        logger.error(e)
        return False

    logger.info("Push notify success")
    return True
