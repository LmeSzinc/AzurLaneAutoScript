import os

IS_ON_PHONE_CLOUD = os.environ.get("cloudphone", "") == "cloudphone"
