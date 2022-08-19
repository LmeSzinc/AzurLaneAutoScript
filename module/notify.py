import json
import onepush.core
from onepush import get_notifier
from onepush.core import Provider
from onepush.exceptions import OnePushException

from module.logger import logger

onepush.core.log = logger


def handle_notify(config: str, **kwargs) -> bool:
    try:
        config: dict = json.loads(config)
    except Exception:
        logger.error("Fail to load onepush config, skip sending")
        return False
    try:
        if config.get("disabled") == True:
            return True
        notifier: Provider = get_notifier(config["provider"])
        required: list[str] = notifier.params["required"]
        params: dict = config["params"]
        params.update(kwargs)

        # pre check
        for key in required:
            if key not in params:
                logger.warning(
                    f"Notifier {notifier.name} require param '{key}' but not provided"
                )

        notifier.notify(**params)
    except OnePushException:
        logger.exception("Push notify failed")
        return False
    except Exception as e:
        logger.exception(e)
        return False

    logger.info("Push notify success")
    return True