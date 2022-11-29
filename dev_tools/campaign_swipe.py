from campaign.campaign_main.campaign_7_2 import MAP
from module.campaign.campaign_base import CampaignBase
from module.config.config import AzurLaneConfig
from module.logger import logger
from module.map_detection.homography import Homography
from module.map_detection.utils import *


class Config:
    pass
    # Universal configs to reduce error
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    DETECTION_BACKEND = 'perspective'

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 24),
        'width': (1.5, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 40, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }

    STORY_OPTION = -2

    MAP_FOCUS_ENEMY_AFTER_BATTLE = True
    MAP_HAS_SIREN = True
    MAP_HAS_FLEET_STEP = True
    IGNORE_LOW_EMOTION_WARN = False

    MAP_GRID_CENTER_TOLERANCE = 0.2
    MAP_SWIPE_MULTIPLY = (1.320, 1.009)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.276, 0.974)


cfg = AzurLaneConfig('alas', task='Alas').merge(Config())
cfg.DETECTION_BACKEND = 'perspective'
az = CampaignBase(cfg)
az.map = MAP
# az.device.disable_stuck_detection()

az.update()
hm = Homography(cfg)
# Load from a known homo_storage
# sto = ((10, 5), [(137.776, 83.461), (1250.155, 83.461), (18.123, 503.909), (1396.595, 503.909)])
# hm.load_homography(storage=sto)

# Or from screenshot
hm.load_homography(image=np.array(az.device.image))


class SwipeSimulate:
    def __init__(self, swipe, simulate_count=4):
        self.simulate_count = simulate_count
        self.swipe = np.array(swipe, dtype=np.float)
        self.swipe_base = self.cal_swipe_base()
        logger.info(self.swipe_base)

    def cal_swipe_base(self):
        swipe_base = None
        for loca, grid in az.view.grids.items():
            offset = grid.screen2grid([az.config.SCREEN_CENTER])[0].astype(int)
            points = grid.grid2screen(np.add([[0.5, 0], [-0.5, 0], [0, 0.5], [0, -0.5]], offset))
            swipe_base = np.array([np.linalg.norm(points[0] - points[1]), np.linalg.norm(points[2] - points[3])])
            break

        if swipe_base is None:
            logger.critical('Unable to get swipe_base')
            exit(1)
        else:
            return swipe_base

    @staticmethod
    def normalise_offset(offset):
        """
        Convert hm.homo_loca (range from 0 to 140),
        to swipe difference (range from -70 to 70)
        """
        if offset[0] > 70:
            offset[0] -= 140
        if offset[1] > 100:
            offset[1] -= 140
        return offset

    def simulate(self):
        logger.hr(f'Swipe: {self.swipe}', level=1)
        record = []
        for n in range(self.simulate_count):
            hm.detect(az.device.image)
            # hm.draw()
            init_offset = self.normalise_offset(hm.homo_loca)

            az.device.swipe_vector(self.swipe)
            az.device.sleep(0.3)
            az.device.screenshot()
            hm.detect(az.device.image)
            offset = self.normalise_offset(hm.homo_loca)
            record.append(offset - init_offset)
            # fit = hm.fit_points(np.array(record), encourage=2)
            fit = np.mean(record, axis=0)
            # (170, 65)
            multiply = np.round(np.abs(self.swipe) / ((np.abs(self.swipe) // (170, 130))) / self.swipe_base, 3)
            logger.info(
                f'[{n}/{self.simulate_count}] init_offset={init_offset}, offset={offset}, fit={fit}, multiply={multiply}')

            fleet = az.get_fleet_show_index()
            az.fleet_set(3 - fleet)
            az.fleet_set(fleet)
            # az.fleet_set(3)
            # az.fleet_set(1)
            az.ensure_no_info_bar()

        self.multiply = multiply
        self.swipe -= (fit[0], 0)
        # self.swipe -= (0, fit[1])
        self.show()
        return abs(fit[0])

        # return abs(fit[1])

    def show(self):
        print()
        print(f'Last swipe: {self.swipe}')
        print('Result to copy:')
        print()
        # MAP_SWIPE_MULTIPLY = 1.579
        # MAP_SWIPE_MULTIPLY_MINITOUCH = 1.527
        if az.config.Emulator_ControlMethod == 'minitouch':
            multiply = np.round(self.multiply[0] / 1.572 * 1.626, 3)
            minitouch = self.multiply[0]
        else:
            multiply = self.multiply[0]
            minitouch = np.round(self.multiply[0] / 1.626 * 1.572, 3)
        print(f'    MAP_SWIPE_MULTIPLY = {str(multiply).ljust(5, "0")}')
        print(f'    MAP_SWIPE_MULTIPLY_MINITOUCH = {str(minitouch).ljust(5, "0")}')
        print()

        print()
        print(f'Last swipe: {self.swipe}')
        print('Result to copy:')
        print()
        # MAP_SWIPE_MULTIPLY = 1.579
        # MAP_SWIPE_MULTIPLY_MINITOUCH = 1.527
        if az.config.Emulator_ControlMethod == 'minitouch':
            multiply = np.round(self.multiply[0] / 1.572 * 1.626, 3)
            minitouch = self.multiply[1]
        else:
            multiply = self.multiply[1]
            minitouch = np.round(self.multiply[0] / 1.626 * 1.572, 3)
        print(f'    MAP_SWIPE_MULTIPLY = {str(multiply).ljust(5, "0")}')
        print(f'    MAP_SWIPE_MULTIPLY_MINITOUCH = {str(minitouch).ljust(5, "0")}')
        print()

    def run(self):
        while 1:
            result = self.simulate()
            if result <= 1:
                break


if __name__ == '__main__':
    """
    To fit MAP_SWIPE_MULTIPLY.
    
    Before running this, move your fleet on map to be like this:
    FL is current fleet, Fl is another fleet.
    Camera should focus on current fleet (Double click switch over to refocus)
    -- -- -- -- --
    -- Fl -- FL --
    -- -- -- -- --
    After run, Result is ready to copy.
    """
    sim = SwipeSimulate((400, 0)).run()
