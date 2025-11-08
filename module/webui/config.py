from deploy.config import DeployConfig as _DeployConfig


class DeployConfig(_DeployConfig):
    def show_config(self):
        pass

    def __setattr__(self, key: str, value):
        """
        Catch __setattr__, copy to `self.config`, write deploy config.
        """
        super().__setattr__(key, value)
        if key[0].isupper() and key in self.config:
            if key in self.config:
                before = self.config[key]
                if before != value:
                    self.config[key] = value
                    self.write()
            else:
                self.config[key] = value
                self.write()
