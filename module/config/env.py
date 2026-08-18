import os

# Lowercase `cloudphone` is an intentional deployment contract (cloud-phone
# runtimes set this env var); renaming would break those deployments.
IS_ON_PHONE_CLOUD = os.environ.get("cloudphone", "") == "cloudphone"  # noqa: SIM112
