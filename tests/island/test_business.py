"""Screenshot golden results; awaiting human review of collection/ images."""
from module.testing.screenshot import image

from module.island.business import IslandBusiness


class TestOverviewJP:
    @image('island/business/ac63e8ab', server='jp')
    def test_running_eatery_on_shifted_grid(self, main: IslandBusiness):
        # Human review confirmed this capture uses the shifted business grid.
        main.shifted = True
        button = main.current_restaurant_button()
        actual = dict(shifted=main.shifted, area=button.area, restaurant_id=main.get_restaurant_id(button),
                      running=main.is_restaurant_running(button), resting=main.is_restaurant_resting(button),
                      remaining_seconds=main.get_remain_time(button).total_seconds())
        regions = [(button.area, 'restaurant #0 id={} running={} resting={}'.format(
            actual['restaurant_id'], actual['running'], actual['resting']))]
        main.device.review(actual, regions)
        assert actual == {
            'shifted': True,
            'area': (210, 168, 1203, 329),
            'restaurant_id': 603,
            'running': True,
            'resting': False,
            'remaining_seconds': 12462.0,
        }


class TestOverviewCN:
    @image('island/business/1f0411b9', server='cn')
    def test_running_bear_restaurant(self, main: IslandBusiness):
        main.shifted = True
        button = main.current_restaurant_button()
        actual = dict(shifted=main.shifted, area=button.area, restaurant_id=main.get_restaurant_id(button),
                      running=main.is_restaurant_running(button), resting=main.is_restaurant_resting(button),
                      remaining_seconds=main.get_remain_time(button).total_seconds())
        regions = [(button.area, 'restaurant #0 id={} running={} resting={}'.format(
            actual['restaurant_id'], actual['running'], actual['resting']))]
        main.device.review(actual, regions)
        assert actual == {
            'shifted': True,
            'area': (210, 168, 1203, 329),
            'remaining_seconds': 5588.0,
            'restaurant_id': 602,
            'resting': False,
            'running': True,
        }
