import module.config.server as server
from module.base.button import Button
from module.logger import logger
from module.base.template import Template
from module.template.assets import *
from module.island.assets import *
from module.island.interact import IslandInteract
from module.island.product import get_product_template
from module.ui.page import (
    page_dormmenu,
    page_island,
    page_island_management,
    page_island_postmanage,
)
import module.config.server as server
from module.base.timer import Timer
from module.ocr.ocr import Ocr

class IslandPostManage(IslandInteract):
    target_product: str = ''
    estimated_complete_times: list = []

    TEMPLATE_SIM_THRESHOLD = 0.85
    GRID_OFFSET = (100, 80, 95, 0) # x, y, dx, dy

    BTN_PRODUCT_MAX = Button(area=(960, 379, 960+28, 379+28), color=(), button=(960, 379, 960+28, 379+28), name='Island Product Max')
    BTN_PRODUCT_CONFIRM = Button(area=(713, 612, 680+95, 600+20), color=(), button=(713, 612, 680+95, 600+20), name='Island Product Confirm')

    OCR_PRODUCTION_TIME = Ocr(BTN_PRODUCT_CONFIRM, letter=(255, 255, 255), name='OCR_ISLAND_PRODUCTION_TIME')

    def run(self):
        """
        Pages:
            in: Any page
            out: page_main, may have info_bar
        """
        self.target_product = ''
        self.estimated_complete_times = []
        if server.server in ['jp']:
            self.ui_ensure(page_dormmenu)
            self.goto_ui(page_island)
            self.handle_info_bar()
            self.process_harvests()
        else:
            logger.info(f'Island Post Manage task not presently supported for {server.server} server.')
            logger.info('If want to address, review necessary assets, replace, update above condition, and test')

        # fixed due to limitation of ocr model
        self.config.task_delay(minute=100)

    def process_harvests(self):
        logger.hr(f'Process Harvests', level=1)
        self.device.screenshot_interval_set()
        if self.config.IslandPostManage_Mining != 'disabled':
            self.target_product = self.config.IslandPostManage_Mining
            self.process_job(TEMPLATE_ISLAND_MINING)
        if self.config.IslandPostManage_Lumbering != 'disabled':
            self.target_product = self.config.IslandPostManage_Lumbering
            self.process_job(TEMPLATE_ISLAND_LUMBERING)
        if self.config.IslandPostManage_Ranch != 'disabled':
            self.target_product = ''
            self.process_job(TEMPLATE_ISLAND_RANCH)

    def process_job(self, job_heading_template: Template) -> bool:
        logger.hr(job_heading_template.name, level=2)
        self.goto_ui(page_island_postmanage)
        sim, btn = job_heading_template.match_luma_result(self.device.screenshot())
        if sim < self.TEMPLATE_SIM_THRESHOLD:
            # TODO: scroll page and retry
            return False
        x, y, _, _ = btn.area
        x += self.GRID_OFFSET[0]
        y += self.GRID_OFFSET[1]
        for i in range(4):
            self.device.click_record_clear()
            self.dismiss()
            self.wait_until_appear(ISLAND_POSTMANAGE_CHECK)
            logger.info(f'Processing slot#{i+1}')
            btn = Button(area=(x, y, x+30, y+30), color=(), button=(x, y, x+30, y+30), name='Island Job Grid')
            self.process_slot(btn)
            x += self.GRID_OFFSET[2]
            y += self.GRID_OFFSET[3]

    def process_slot(self, btn: Button):
        self.device.click(btn)
        templates = {
            TEMPLATE_ISLAND_JOB_COMPLETE: self.process_completed,
            TEMPLATE_ISLAND_JOB_SELCHAR: self.process_empty,
            TEMPLATE_ISLAND_ADD_PRODUCE: self.process_production,
        }
        for template, func in templates.items():
            self.wait_until_appear(ISLAND_POSTMANAGE_CHECK)
            sim, btn = template.match_luma_result(self.device.screenshot())
            if sim >= self.TEMPLATE_SIM_THRESHOLD:
                func(btn)

    def process_completed(self, btn: Button):
        logger.info("Processing completed job")
        self.device.click(btn)
        self.wait_until_appear_then_click(ISLAND_ITEM_GET, offset=(10, 10))
        return True

    def process_empty(self, btn: Button):
        logger.info("Processing empty slot")
        self.device.click(btn)
        self.wait_until_appear(ISLAND_WORKER_SEL_CHECK, threshold=15)
        sim, worker_btn = TEMPLATE_ISLAND_WORKER_MANJUU.match_luma_result(self.device.screenshot())
        if sim < self.TEMPLATE_SIM_THRESHOLD: # should not happen
            logger.error('Failed to find Manjuu worker in selection')
            self.device.click(ISLAND_POSTMANAGE_GOTO_MANAGEMENT)
            return False
        self.device.click(worker_btn)
        self.wait_until_appear_then_click(ISLAND_WORKER_CONFIRM, offset=(20, 10))
        return self.process_production(btn)

    def process_production(self, btn=None):
        logger.info("Processing production")
        if btn:
            self.device.click(btn)
        # dealing with bug that sometimes closes window instead of going to production selection
        while 1:
            self.device.screenshot()
            if ISLAND_POSTMANAGE_CHECK.match(self.device.image):
                logger.info('Bugged, retrying')
                return self.process_empty(btn)
            if ISLAND_PRODUCT_SEL_CHECK.match(self.device.image):
                break
        product = get_product_template(self.target_product)
        if product:
            sim, btn = product.match_luma_result(self.device.screenshot())
            if sim < self.TEMPLATE_SIM_THRESHOLD:
                # TODO: scroll page and retry
                logger.warning(f'Could not find product {self.target_product} in selection, proceed with default option')
                self.device.click(ISLAND_POSTMANAGE_GOTO_MANAGEMENT)
            else:
                self.device.click(btn)
        self.device.click(self.BTN_PRODUCT_MAX)
        colors = self.BTN_PRODUCT_CONFIRM.load_color(self.device.screenshot())
        if colors[2] > 230: # doable
            self.device.click(self.BTN_PRODUCT_CONFIRM)
        else:
            logger.warning(f'Insufficient resources to produce {self.target_product}, skipping')
            self.device.click(ISLAND_POSTMANAGE_GOTO_MANAGEMENT)
        return True
