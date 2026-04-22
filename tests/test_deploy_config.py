import tempfile
import unittest
from pathlib import Path

from deploy.config import DeployConfig as PosixDeployConfig
from deploy.Windows.config import DeployConfig as WindowsDeployConfig


class DeployConfigTestCase(unittest.TestCase):
    def make_deploy_file(self, text=""):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        path = Path(tempdir.name) / "deploy.yaml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_posix_default_repository_comes_from_template(self):
        deploy_file = self.make_deploy_file()

        config = PosixDeployConfig(file=str(deploy_file))

        self.assertEqual(
            config.Repository,
            "https://github.com/LmeSzinc/AzurLaneAutoScript",
        )

    def test_posix_aliases_keep_existing_runtime_targets(self):
        global_file = self.make_deploy_file("Repository: global\n")
        global_config = PosixDeployConfig(file=str(global_file))
        self.assertEqual(
            global_config.Repository,
            "https://github.com/LmeSzinc/AzurLaneAutoScript",
        )

        cn_file = self.make_deploy_file("Repository: cn\n")
        cn_config = PosixDeployConfig(file=str(cn_file))
        self.assertEqual(
            cn_config.Repository,
            "git://git.lyoko.io/AzurLaneAutoScript",
        )

    def test_posix_custom_repository_is_not_rewritten(self):
        repository = "https://example.com/custom/AzurLaneAutoScript.git"
        deploy_file = self.make_deploy_file(f"Repository: {repository}\n")

        config = PosixDeployConfig(file=str(deploy_file))

        self.assertEqual(config.Repository, repository)
        self.assertIn(f"Repository: {repository}", deploy_file.read_text(encoding="utf-8"))

    def test_windows_aliases_keep_upstream_runtime_targets(self):
        global_file = self.make_deploy_file("Repository: global\n")
        global_config = WindowsDeployConfig(file=str(global_file))
        self.assertEqual(
            global_config.Repository,
            "https://github.com/LmeSzinc/StarRailCopilot",
        )

        cn_file = self.make_deploy_file("Repository: cn\n")
        cn_config = WindowsDeployConfig(file=str(cn_file))
        self.assertEqual(
            cn_config.Repository,
            "https://github.com/LmeSzinc/StarRailCopilot",
        )


if __name__ == "__main__":
    unittest.main()
