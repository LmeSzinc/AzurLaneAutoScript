from module.equipment.fleet_equipment import FleetEquipment


class DailyEquipment(FleetEquipment):

    def fleet_equip_take_on_all(self):
        if self.config.FLEET_DAILY_EQUIPMENT is None:
            return False
        if self.equipment_has_take_on:
            return False

        self.fleet_equip_take_on_all_preset(preset_record=self.config.FLEET_DAILY_EQUIPMENT)
        self.equipment_has_take_on = True
        self.device.sleep(1)
        return True

    def fleet_equip_take_off_all(self):
        if self.config.FLEET_DAILY_EQUIPMENT is None:
            return False
        if not self.equipment_has_take_on:
            return False

        super().fleet_equip_take_off_all()
        self.equipment_has_take_on = False
        self.device.sleep(1)
        return True
