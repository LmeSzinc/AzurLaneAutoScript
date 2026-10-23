import pytest

from module.island_handler.production_plan_calculator import ProductionPlanCalculator


class TestStaticHelpers:
    def test_get_quantity_from_grade(self):
        assert ProductionPlanCalculator.get_quantity_from_grade('bronze') == 2
        assert ProductionPlanCalculator.get_quantity_from_grade('silver') == 2
        assert ProductionPlanCalculator.get_quantity_from_grade('gold') == 3
        assert ProductionPlanCalculator.get_quantity_from_grade('diamond') == 4
        with pytest.raises(ValueError):
            ProductionPlanCalculator.get_quantity_from_grade('paper')

    def test_format_amount(self):
        fmt = ProductionPlanCalculator._format_amount
        assert fmt(3) == '3'
        assert fmt(3.0000000001) == '3'
        assert fmt(2.5) == '2.5'
        assert fmt(0.12345) == '0.123'
        assert fmt(0) == '0'

    def test_round_output_amount(self):
        rnd = ProductionPlanCalculator._round_output_amount
        assert rnd(2.9999999999) == 3.0
        assert rnd(2.3456) == 2.346
        assert rnd(0) == 0.0
