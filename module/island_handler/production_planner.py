from datetime import datetime

from module.base.decorator import cached_property
from module.config.utils import server_time_offset
from module.daemon.daemon_base import DaemonBase
from module.island.utils import (
    load_hard_floor_items,
    load_item_mapping,
    load_technology_status,
)
from module.island_handler.production_plan_calculator import (
    ProductionPlanCalculator,
    get_current_activity_list,
)
from module.island_handler.restaurant_config import (
    RESTAURANT_CONFIG,
    RESTAURANT_IDS,
    get_config_key,
    get_restaurant_config,
    get_waitress_slots,
)
from module.island_handler.technology_scanner import IslandTechnologyScanner


class IslandProductionPlanner(DaemonBase):
    """Config/device adapter around ProductionPlanCalculator.

    Reads planner inputs from config, runs the pure calculator, then writes
    the resulting plan back into config. All computation lives in
    ProductionPlanCalculator.
    """
    RESTAURANT_MENU_CONFIG = {
        restaurant_id: get_config_key(restaurant_id, data['menu_key'])
        for restaurant_id, data in RESTAURANT_CONFIG.items()
    }

    @cached_property
    def current_activity_list(self):
        time = datetime.now() - server_time_offset()
        return get_current_activity_list(time)

    def create_calculator(self, technology_status):
        restaurant_settings = {}
        for restaurant_id in RESTAURANT_IDS:
            config_data = get_restaurant_config(restaurant_id)
            restaurant_settings[restaurant_id] = {
                'grade': self.config.cross_get(get_config_key(restaurant_id, config_data['grade_key'])),
                'waitress_slots': get_waitress_slots(self.config, restaurant_id),
            }
        return ProductionPlanCalculator(
            technology_status=technology_status,
            activity_list=self.current_activity_list,
            place_efficiency={
                101: self.config.cross_get("IslandProductionPlanner.IslandProductionPlanner.FieldsEfficiency"),
                501: self.config.cross_get("IslandProductionPlanner.IslandProductionPlanner.OrchardEfficiency"),
                502: self.config.cross_get("IslandProductionPlanner.IslandProductionPlanner.NurseryEfficiency"),
            },
            restaurant_settings=restaurant_settings,
            daily_profit_lower_limit=self.config.cross_get(
                "IslandProductionPlanner.IslandProductionPlanner.DailyProfitLowerLimit", 0),
            daily_buffer_safety_margin=self.config.cross_get(
                "IslandProductionPlanner.IslandProductionPlanner.DailyBufferSafetyMargin", 0),
        )

    def run(
            self,
            tech_status_yaml=None,
            hard_floor_items_yaml=None,
            task_target_items=None,
            stuck_season_order_id=None,
            export=True,
            use_item_name_in_export=True,
    ):
        if tech_status_yaml is not None:
            technology_status = tech_status_yaml
        else:
            technology_status = self.config.cross_get("IslandProductionPlanner.Storage.Storage.IslandTechnologyStatus", None)
            if technology_status is None or self.config.cross_get("IslandProductionPlanner.IslandProductionPlanner.RescanIslandTechnology", False):
                technology_status = IslandTechnologyScanner(self.config).get_technology_status()
        technology_status = load_technology_status(technology_status)
        if hard_floor_items_yaml is None:
            hard_floor_items = load_hard_floor_items(
                self.config.cross_get("IslandProduction.IslandProduction.HardFloorItems", "")
            )
        else:
            hard_floor_items = load_hard_floor_items(hard_floor_items_yaml)
        if task_target_items is None:
            task_target_items = load_item_mapping(
                self.config.cross_get("IslandSeasonTask.IslandSeasonTask.TaskTarget", "{}"),
                config_name='TaskTarget',
            )
        if stuck_season_order_id is None:
            stuck_season_order_id = self.config.cross_get("IslandOrder.IslandOrder.StuckSeasonOrderId", 0)

        calculator = self.create_calculator(technology_status)
        calculator.solve_production_plan(
            hard_floor_items=hard_floor_items,
            task_target_items=task_target_items,
            stuck_season_order_id=stuck_season_order_id,
        )
        calculator.print_solved_production_plan()
        if export:
            inventory_levels_yaml_text = calculator.daily_buffer_items_to_yaml(use_item_name=use_item_name_in_export)
            idle_accumulating_items_yaml_text = calculator.idle_accumulating_items_to_yaml(use_item_name=use_item_name_in_export)
            hard_floor_items_yaml_text = calculator.hard_floor_items_to_yaml(use_item_name=use_item_name_in_export)
            restaurant_menu_yaml_texts = calculator.restaurant_menus_to_yaml()
            with self.config.multi_set():
                self.config.cross_set("IslandProductionPlanner.Storage.Storage.IslandTechnologyStatus", technology_status)
                self.config.cross_set("IslandProduction.IslandProduction.DailyBufferItems", inventory_levels_yaml_text)
                self.config.cross_set("IslandProduction.IslandProduction.IdleAccumulatingItems", idle_accumulating_items_yaml_text)
                self.config.cross_set("IslandProduction.IslandProduction.HardFloorItems", hard_floor_items_yaml_text)
                for slot, config_key in self.RESTAURANT_MENU_CONFIG.items():
                    self.config.cross_set(config_key, restaurant_menu_yaml_texts[slot])
                self.config.cross_set("IslandProductionPlanner.IslandProductionPlanner.RescanIslandTechnology", False)
        return calculator
