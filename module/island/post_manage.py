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
from module.ocr.ocr import Ocr

class IslandPostManage(IslandInteract):
    TEMPLATE_SIM_THRESHOLD = 0.85
    GRID_OFFSET = (100, 80, 95, 0) # x, y, dx, dy

    BTN_PRODUCT_MAX = Button(area=(960, 379, 960+28, 379+28), color=(), button=(960, 379, 960+28, 379+28), name='Island Product Max')
    BTN_PRODUCT_CONFIRM = Button(area=(713, 612, 680+95, 600+20), color=(), button=(713, 612, 680+95, 600+20), name='Island Product Confirm')

    OCR_PRODUCTION_TIME = Ocr(BTN_PRODUCT_CONFIRM, letter=(255, 255, 255), name='OCR_ISLAND_PRODUCTION_TIME')

    def run(self):
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
        self.process_job('mining')
        self.process_job('lumbering')
        self.process_job('ranch')

    def process_job(self, job_name:str) -> bool:
        product_key_prefix = ''
        if job_name == 'mining':
            job_heading_template = TEMPLATE_ISLAND_MINING
            product_key_prefix = 'IslandMining'
        elif job_name == 'lumbering':
            job_heading_template = TEMPLATE_ISLAND_LUMBERING
            product_key_prefix = 'IslandLumbering'
        elif job_name == 'ranch':
            job_heading_template = TEMPLATE_ISLAND_RANCH
            product_key_prefix = '' # fixed product, no selection
        else:
            logger.error(f'Unknown job name {job_name}')
            return
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
            if product_key_prefix:
                target_product = getattr(self.config, f'{product_key_prefix}_Slot_{i+1}', 'disabled')
            logger.info("Target product for slot#{}: {}".format(i+1, target_product))
            if target_product != 'disabled':
                self.device.click_record_clear()
                self.dismiss()
                self.wait_until_appear(ISLAND_POSTMANAGE_CHECK)
                logger.info(f'Processing slot#{i+1}')
                btn = Button(area=(x, y, x+30, y+30), color=(), button=(x, y, x+30, y+30), name='Island Job Grid')
                self.process_slot(btn, target_product)
            x += self.GRID_OFFSET[2]
            y += self.GRID_OFFSET[3]

    def process_slot(self, btn: Button, target_product: str=''):
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
                func(btn, target_product=target_product)

    def process_completed(self, btn: Button, **kwargs):
        logger.info("Processing completed job")
        t = self.click_and_wait_until_appear(btn, ISLAND_ITEM_GET, TEMPLATE_ISLAND_JOB_SELCHAR)
        if t == TEMPLATE_ISLAND_JOB_SELCHAR:
            return True
        self.click_and_wait_until_appear(self.BTN_EMPTY, ISLAND_POSTMANAGE_CHECK)
        return True

    def process_empty(self, btn: Button, **kwargs):
        logger.info("Processing empty slot")
        self.device.click(btn)
        self.wait_until_appear(ISLAND_WORKER_SEL_CHECK, threshold=20)
        sim, worker_btn = TEMPLATE_ISLAND_WORKER_MANJUU.match_luma_result(self.device.screenshot())
        if sim < self.TEMPLATE_SIM_THRESHOLD: # should not happen
            logger.error('Failed to find Manjuu worker in selection')
            self.device.click(ISLAND_POSTMANAGE_GOTO_MANAGEMENT)
            return False
        self.click_and_wait_until_appear(worker_btn, ISLAND_WORKER_CONFIRM)
        self.device.click(ISLAND_WORKER_CONFIRM)
        return self.process_production(btn)

    def process_production(self, btn=None, **kwargs):
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
        product_name = kwargs.get('target_product', '')
        product = get_product_template(product_name)
        if product:
            sim, btn = product.match_luma_result(self.device.screenshot())
            if sim < self.TEMPLATE_SIM_THRESHOLD:
                # TODO: scroll page and retry
                logger.warning(f'Could not find product {product_name} in selection, proceed with default option')
                self.device.click(ISLAND_POSTMANAGE_GOTO_MANAGEMENT)
            else:
                self.device.click(btn)
        self.device.click(self.BTN_PRODUCT_MAX)
        colors = self.BTN_PRODUCT_CONFIRM.load_color(self.device.screenshot())
        if colors[2] > 230: # doable
            self.device.click(self.BTN_PRODUCT_CONFIRM)
        else:
            logger.warning(f'Insufficient resources to produce {product_name}, skipping')
            self.device.click(ISLAND_POSTMANAGE_GOTO_MANAGEMENT)
        return True
