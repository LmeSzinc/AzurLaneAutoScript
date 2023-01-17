from module.logger import logger


class log_res:
        
    def log_res(self,num,name):
        ViewCurrentResources=[
                                'oil',
                                'coin',
                                'gem',
                                'PT',
                                'opcoin',
                                'purplecoin',
                                'actionpoint',
                                'cube',
                                'maxoil',
                                'maxcoin',
                                'oiltomaxoil',
                                'cointomaxcoin'
                                ]
        ViewEquipProgress=['457mm','234mm','tenrai','152mm']
        if name in ViewCurrentResources:
            key=f'ViewCurrentResources.ViewCurrentResources.{name}'
            self.config.cross_set(keys=key, value=num)
            logger.info(f'{key}')
        elif name in ViewEquipProgress:
            key=f'ViewCurrentResources.ViewEquipProgress.{name}'
            self.config.cross_set(keys=key, value=num)
        else:
            logger.warn('No such resource!')
        return None