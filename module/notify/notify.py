import onepush.core
import yaml
from onepush import get_notifier
from onepush.core import Provider
from onepush.exceptions import OnePushException
from onepush.providers.custom import Custom
from requests import Response

from module.logger import logger

onepush.core.log = logger


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
