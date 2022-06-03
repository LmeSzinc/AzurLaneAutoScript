from urllib.parse import urlparse

from deploy.config import DeployConfig
from deploy.utils import *


class PipManager(DeployConfig):
    @cached_property
    def python(self):
        return self.filepath("PythonExecutable")

    @cached_property
    def requirements_file(self):
        if self.config["RequirementsFile"] == "requirements.txt":
            return "requirements.txt"
        else:
            return self.filepath("RequirementsFile")

    @cached_property
    def pip(self):
        return f'"{self.python}" -m pip'

    def pip_install(self):
        hr0("Update Dependencies")

        if not self.bool("InstallDependencies"):
            print("InstallDependencies is disabled, skip")
            return

        hr1("Check Python")
        self.execute(f'"{self.python}" --version')

        arg = []
        if self.bool("PypiMirror"):
            mirror = self.config["PypiMirror"]
            arg += ["-i", mirror]
            # Trust http mirror
            if "http:" in mirror:
                arg += ["--trusted-host", urlparse(mirror).hostname]

        # Don't update pip, just leave it.
        # hr1('Update pip')
        # self.execute(f'"{self.pip}" install --upgrade pip{arg}')
        arg += ["--disable-pip-version-check"]

        hr1("Update Dependencies")
        arg = " " + " ".join(arg) if arg else ""
        self.execute(f"{self.pip} install -r {self.requirements_file}{arg}")
