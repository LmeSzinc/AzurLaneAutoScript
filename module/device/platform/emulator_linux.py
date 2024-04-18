from module.device.platform.emulator_base import EmulatorBase, EmulatorInstanceBase, EmulatorManagerBase


class EmulatorInstance(EmulatorInstanceBase):
    pass


class Emulator(EmulatorBase):
    pass


class EmulatorManager(EmulatorManagerBase):
    pass

if __name__ == '__main__':
    self = EmulatorManager()
    for emu in self.all_emulator_instances:
        print(emu)
