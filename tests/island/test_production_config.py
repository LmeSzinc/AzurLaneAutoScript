from module.config.config_updater import ConfigUpdater


def updated_production_config(old):
    return ConfigUpdater().config_update(old)["IslandProduction"]["IslandProduction"]


def test_workerjuu_setting_defaults_to_true():
    config = updated_production_config({})

    assert config['UseWorkerjuuByDefault'] is True


def test_new_worker_setting_values_are_preserved():
    for value in (True, False):
        old = {"IslandProduction": {"IslandProduction": {"UseWorkerjuuByDefault": value}}}

        assert updated_production_config(old)['UseWorkerjuuByDefault'] is value
