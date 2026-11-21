from module.base.base import ModuleBase
from module.island.utils import (
    get_configured_season,
    get_season_remaining_days,
    load_hard_floor_items,
    load_item_mapping,
    load_technology_status,
)
from module.island_handler.production_plan_calculator import ProductionPlanCalculator
from module.island_handler.restaurant_config import (
    RESTAURANT_CONFIG,
    RESTAURANT_IDS,
    get_config_key,
    get_restaurant_config,
    get_waitress_slots,
)
from module.island_handler.technology_scanner import IslandTechnologyScanner
from module.logger import logger


def create_production_calculator(config, technology_status):
    """
    Args:
        config (AzurLaneConfig):
        technology_status (dict): {technology_id: unlocked}, see load_technology_status.

    Returns:
        ProductionPlanCalculator: With restaurant, efficiency and profit settings from config.
    """
    restaurant_settings = {}
    for restaurant_id in RESTAURANT_IDS:
        config_data = get_restaurant_config(restaurant_id)
        restaurant_settings[restaurant_id] = {
            'grade': config.cross_get(get_config_key(restaurant_id, config_data['grade_key'])),
            'waitress_slots': get_waitress_slots(config, restaurant_id),
        }
    return ProductionPlanCalculator(
        technology_status=technology_status,
        season_name=config.cross_get('IslandGeneral.IslandGeneral.Season'),
        place_efficiency={
            101: config.cross_get("IslandProductionPlanner.IslandProductionPlanner.FieldsEfficiency"),
            501: config.cross_get("IslandProductionPlanner.IslandProductionPlanner.OrchardEfficiency"),
            502: config.cross_get("IslandProductionPlanner.IslandProductionPlanner.NurseryEfficiency"),
        },
        restaurant_settings=restaurant_settings,
        daily_profit_lower_limit=config.cross_get(
            "IslandProductionPlanner.IslandProductionPlanner.DailyProfitLowerLimit", 0),
        daily_buffer_safety_margin=config.cross_get(
            "IslandProductionPlanner.IslandProductionPlanner.DailyBufferSafetyMargin", 0),
    )


def load_planner_demands(config, task_target_items=None, stuck_season_order_id=None):
    """
    Args:
        config (AzurLaneConfig):
        task_target_items (dict): TaskTarget, read from config if None.
        stuck_season_order_id (int): Read from config if None.

    Returns:
        dict: Production planner demands, as keyword arguments of
            ProductionPlanCalculator.build_production_problem and solve_production_plan.
    """
    if task_target_items is None:
        task_target_items = load_item_mapping(
            config.cross_get("IslandSeasonTask.IslandSeasonTask.TaskTarget", "{}"),
            config_name='TaskTarget',
        )
    if stuck_season_order_id is None:
        stuck_season_order_id = config.cross_get("IslandOrder.IslandOrder.StuckSeasonOrderId", 0)
    return {
        'task_target_items': task_target_items,
        'task_target_period': get_season_remaining_days(get_configured_season(config)),
        'stuck_season_order_id': stuck_season_order_id,
    }


def create_production_problem(config):
    """
    The production problem IslandProductionPlanner solves, built from config
    without solving, e.g. to value island transport commissions against it.
    Uses the technology status saved by the last planner run, without rescanning.

    Args:
        config (AzurLaneConfig):

    Returns:
        dict: See ProductionPlanCalculator.build_production_problem,
            None if no technology status is saved yet.
    """
    technology_status = config.cross_get("IslandProductionPlanner.Storage.Storage.IslandTechnologyStatus", None)
    if technology_status is None:
        logger.warning('No island technology status is saved, run IslandProductionPlanner first')
        return None
    calculator = create_production_calculator(config, load_technology_status(technology_status))
    return calculator.build_production_problem(**load_planner_demands(config))


class IslandProductionPlanner(ModuleBase):
    """Config/device adapter around ProductionPlanCalculator.

    Reads planner inputs from config, runs the pure calculator, then writes
    the resulting plan back into config. All computation lives in
    ProductionPlanCalculator.
    """
    RESTAURANT_MENU_CONFIG = {
        restaurant_id: get_config_key(restaurant_id, data['menu_key'])
        for restaurant_id, data in RESTAURANT_CONFIG.items()
    }

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
                technology_status = IslandTechnologyScanner(self.config, self.device).get_technology_status()
        technology_status = load_technology_status(technology_status)
        if hard_floor_items_yaml is None:
            hard_floor_items = load_hard_floor_items(
                self.config.cross_get("IslandProduction.IslandProduction.HardFloorItems", "")
            )
        else:
            hard_floor_items = load_hard_floor_items(hard_floor_items_yaml)
        demands = load_planner_demands(
            self.config,
            task_target_items=task_target_items,
            stuck_season_order_id=stuck_season_order_id,
        )

        calculator = create_production_calculator(self.config, technology_status)
        task_target_period = demands['task_target_period']
        if demands['task_target_items']:
            if task_target_period is None:
                logger.warning(
                    'The configured island season has no remaining planning period, so no default TaskTarget '
                    'planning period is available; each entry must provide an explicit period'
                )
            else:
                logger.info(
                    f'Default TaskTarget planning period: {task_target_period:.3f} day(s) '
                    'remaining in the configured island season'
                )
        calculator.solve_production_plan(hard_floor_items=hard_floor_items, **demands)
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
                self.config.cross_set("IslandProduction.Storage.Storage.CheckAllEmptySlots", True)
                for slot, config_key in self.RESTAURANT_MENU_CONFIG.items():
                    self.config.cross_set(config_key, restaurant_menu_yaml_texts[slot])
                self.config.cross_set("IslandProductionPlanner.IslandProductionPlanner.RescanIslandTechnology", False)
        return calculator
