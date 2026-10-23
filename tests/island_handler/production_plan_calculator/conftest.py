import pytest

from module.island_handler.production_plan_calculator import ProductionPlanCalculator


class AllUnlockedTechnology(dict):
    """Technology status stub reporting every technology as unlocked."""

    def get(self, key, default=False):
        return True


def _make_calculator(technology_status=None, **kwargs):
    if technology_status is None:
        technology_status = {}
    return ProductionPlanCalculator(technology_status, **kwargs)


@pytest.fixture
def make_calculator():
    return _make_calculator


@pytest.fixture
def all_unlocked_technology():
    return AllUnlockedTechnology()


@pytest.fixture(scope='module')
def all_tech_koi_solved():
    """All technology unlocked, Koi restaurant selling, profit floor 10."""
    calc = _make_calculator(
        AllUnlockedTechnology(),
        restaurant_settings={601: {'grade': 'gold', 'waitress_slots': ('Chao_Ho', 'none')}},
        daily_profit_lower_limit=10,
    )
    calc.solve_production_plan()
    return calc


@pytest.fixture(scope='module')
def margin_solved():
    """Same all-tech problem solved with safety margin 0 and 1.0."""
    calc0 = _make_calculator(AllUnlockedTechnology(), daily_buffer_safety_margin=0)
    calc0.solve_production_plan()
    calc1 = _make_calculator(AllUnlockedTechnology(), daily_buffer_safety_margin=1.0)
    calc1.solve_production_plan()
    return calc0, calc1
