from module.handler.login import LoginHandler

class AdbRestart(LoginHandler):
    def run(self):

        if self.config.AdbRestart_AdbRestart:
            self.device.adb_restart()


if __name__ == '__main__':
    AdbRestart('alas', task='AdbRestart').run()