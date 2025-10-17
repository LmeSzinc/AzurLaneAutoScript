import module.config.server as server
from module.base.button import Button
from module.logger import logger
from module.base.template import Template
from module.base.timer import Timer
from module.template.assets import *
from module.island.assets import *
from module.island.interact import IslandInteract
from module.island.product import *
from module.ui.page import (
    page_dormmenu,
    page_island,
    page_island_management,
    page_island_postmanage,
)
import module.config.server as server
from module.config.utils import nearest_future
from module.ocr.ocr import Duration
from datetime import datetime, timedelta

class IslandPostManage(IslandInteract):
    TEMPLATE_SIM_THRESHOLD = 0.85
    GRID_OFFSET = (100, 80, 95, 0) # x, y, dx, dy

    BTN_PRODUCT_MAX = Button(area=(960, 379, 960+28, 379+28), color=(), button=(960, 379, 960+28, 379+28), name='Island Product Max')
    BTN_PRODUCT_CONFIRM = Button(area=(713, 612, 713+95, 612+20), color=(), button=(713, 612, 713+95, 612+20), name='Island Product Confirm')

    OCR_PRODUCTION_TIME = Duration(BTN_PRODUCT_CONFIRM, lang='cnocr', name='OCR_ISLAND_PRODUCTION_TIME')
    # manually tested best effort params
    OCR_PRODUCTION_TIME.binarize_threshold = 250
    OCR_PRODUCTION_TIME.upscale = 2
    OCR_PRODUCTION_TIME.fxaa = True

    def run(self):
        self.estimated_work_times = []
        if server.server in ['jp']:
            self.ui_ensure(page_dormmenu)
            self.goto_ui(page_island)
            self.handle_info_bar()
            self.process_harvests()
        else:
            logger.info(f'Island Post Manage task not presently supported for {server.server} server.')
            logger.info('If want to address, review necessary assets, replace, update above condition, and test')

        # So far 100 mins is best for prevent frequent run and ensure productions
        self.config.task_delay(minute=100)

    def process_harvests(self):
        logger.hr(f'Process Harvests', level=1)
        self.device.screenshot_interval_set()
        self.process_job('mining')
        self.process_job('lumbering')
        self.process_job('ranch')

    def process_job(self, job_name:str) -> bool:
        product_config = ''
        if job_name == 'mining':
            job_heading_template = TEMPLATE_ISLAND_MINING
            product_config = self.config.IslandMining_MineProduction
        elif job_name == 'lumbering':
            job_heading_template = TEMPLATE_ISLAND_LUMBERING
            product_config = self.config.IslandLumbering_LumberProduction
        elif job_name == 'ranch':
            job_heading_template = TEMPLATE_ISLAND_RANCH
            product_config = '1234' # fixed
        else:
            logger.error(f'Unknown job name {job_name}')
            return
        product_config = str(product_config)
        while len(product_config) < 4:
            product_config += '0'
        logger.hr(job_name, level=2)
        self.goto_ui(page_island_postmanage)
        sim, btn = job_heading_template.match_luma_result(self.device.screenshot())
        if sim < self.TEMPLATE_SIM_THRESHOLD:
            # TODO: scroll page and retry
            return False
        x, y, _, _ = btn.area
        x += self.GRID_OFFSET[0]
        y += self.GRID_OFFSET[1]
        for i in range(4):
            target_product = ''
            if product_config:
                try:
                    target_product = PRODUCT_INDEX_MAP[job_heading_template.name][product_config[i]]
                except KeyError as e:
                    logger.warning(f'Invalid product index for slot {i+1} in job {job_name}: {e}')
            logger.hr(f'Slot {i+1}', level=3)
            if target_product != 'disabled':
                self.wait_until_appear(ISLAND_POSTMANAGE_CHECK)
                logger.info(f'Processing slot#{i+1}')
                btn = Button(area=(x, y, x+30, y+30), color=(), button=(x, y, x+30, y+30), name='Island Job Grid')
                self.process_slot(btn, target_product)
                self.device.click_record_clear()
                self.dismiss()
            x += self.GRID_OFFSET[2]
            y += self.GRID_OFFSET[3]

    def process_slot(self, slot: Button, target_product: str=''):
        click_handles = (
            TEMPLATE_ISLAND_JOB_COMPLETE,
            TEMPLATE_ISLAND_JOB_SELCHAR,
            TEMPLATE_ISLAND_ADD_PRODUCE, # TODO: potential ignore production config due to keep add production
            ISLAND_ITEM_GET,
        )
        logger.info(f'Target product: {target_product}')
        production_flag = False
        while 1:
            self.device.screenshot()
            for obj in click_handles:
                if isinstance(obj, Template):
                    sim, btn = obj.match_luma_result(self.device.image)
                    if sim >= self.TEMPLATE_SIM_THRESHOLD:
                        self.device.click(btn)
                        production_flag = True
                        break
                elif obj.match_luma(self.device.image):
                    break
            else:
                if ISLAND_WORKER_SEL_CHECK.match(self.device.image):
                    self.select_worker()
                elif ISLAND_PRODUCT_SEL_CHECK.match(self.device.image):
                    if self.process_production(target_product):
                        return
                elif not production_flag and TEMPLATE_ISLAND_TIMER.match(self.device.image):
                    return # still in production
                else:
                    self.device.click(slot)

    def select_worker(self):
        if not self.appear(ISLAND_WORKER_CONFIRM):
            sim, worker_btn = TEMPLATE_ISLAND_WORKER_MANJUU.match_luma_result(self.device.screenshot())
            if sim < self.TEMPLATE_SIM_THRESHOLD: # should not happen
                logger.error('Failed to find Manjuu worker in selection')
                return
            self.device.click(worker_btn)
        self.device.click(ISLAND_WORKER_CONFIRM)

    def process_production(self, target_product: str=''):
        logger.info("Processing production")
        try:
            product = PRODUCT_TEMPLATE_ICON_MAP[target_product]
        except KeyError:
            logger.warning(f'No template icon defined for product {target_product}')
            product = None
        if product:
            sim, btn = product.match_luma_result(self.device.screenshot())
            if sim < self.TEMPLATE_SIM_THRESHOLD:
                # TODO: scroll page and retry
                logger.warning(f'Could not find product {target_product} in selection, proceed with default option')
            else:
                self.device.click(btn)
        self.device.click(self.BTN_PRODUCT_MAX)
        colors = self.BTN_PRODUCT_CONFIRM.load_color(self.device.screenshot())
        if colors[2] > 230: # doable
            # dur = self.OCR_PRODUCTION_TIME.ocr(self.device.image)
            # if type(dur) is timedelta:
            #     self.estimated_work_times.append(dur)
            # else:
            #     logger.warning(f'Failed to OCR production time, got {dur}')
            self.device.click(self.BTN_PRODUCT_CONFIRM)
        else:
            logger.warning(f'Insufficient resources to produce {target_product}, skipping')
            self.device.click(ISLAND_POSTMANAGE_GOTO_MANAGEMENT)
        return True
