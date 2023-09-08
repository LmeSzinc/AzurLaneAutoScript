import argparse
import sys
import typing as t

sys.stdout.reconfigure(encoding='utf-8')

"""
Alas installer
"""


def run_install():
    from deploy.installer import run
    run()


def run_print_test():
    from deploy.Windows.installer_test import run
    run()


def run_set(modify=t.List[str]) -> t.Dict[str, str]:
    data = {}
    for kv in modify:
        if "=" in kv:
            key, value = kv.split('=', maxsplit=1)
            data[key] = value

    from deploy.set import config_set
    return config_set(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Alas installer")
    parser.add_argument(
        "--print-test",
        help="To print example installer outputs instead of making an actual installation",
        action="store_true",
    )
    parser.add_argument(
        "--set",
        help="Use key=value format to modify config/deploy.yaml\n"
             "Example: python installer.py --set Branch=dev",
        type=str,
        nargs="*",
    )
    args, _ = parser.parse_known_args()

    if args.set:
        run_set(args.set)
    elif args.print_test:
        run_print_test()
    else:
        run_install()
