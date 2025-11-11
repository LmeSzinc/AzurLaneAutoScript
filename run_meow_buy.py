# run_meow_buy.py
import argparse
from module.logger import logger
from module.meowfficer.meowfficer import RewardMeowfficer
from module.ui.page import page_meowfficer
import types

# 兼容不同项目结构的 AzurLaneConfig 导入路径
try:
    from module.config.config import AzurLaneConfig
except Exception:
    from module.config.azurlane_config import AzurLaneConfig


def main():
    parser = argparse.ArgumentParser(description="Run Meowfficer buy with real UI")
    parser.add_argument("--config", "-c", default="default",
                        help="Name of user config under ./config (e.g. default / your_own)")
    parser.add_argument("--serial", "-s", default=None,
                        help="ADB serial, e.g. 127.0.0.1:7555 or emulator-5554")
    parser.add_argument("--amount", "-a", type=int, default=2,
                        help="Baseline Meowfficer_BuyAmount")
    parser.add_argument("--overflow", "-o", type=int, default=15000,
                        help="Overflow threshold (Meowfficer_OverflowCoins)")
    args = parser.parse_args()

    # 关键：传 config_name（而不是 None）
    cfg = AzurLaneConfig(config_name=args.config, task=None)



    logger.hr("=== Meowfficer buy (UI) ===", level=1)

    task = RewardMeowfficer(cfg)

    # 进入指挥喵页并等待按钮加载
    task.ui_ensure(page_meowfficer)
    task.wait_meowfficer_buttons()

    # 只执行购买逻辑：先基线，再按阈值补买
    ok = task.meow_buy()
    logger.info(f"meow_buy finished: {ok}")


if __name__ == "__main__":
    main()
