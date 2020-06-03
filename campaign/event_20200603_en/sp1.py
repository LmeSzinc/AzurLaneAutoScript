from module.campaign.campaign_base import CampaignBase
from module.map.map_base import CampaignMap
from module.map.map_grids import SelectedGrids, RoadGrids
from module.logger import logger


MAP = CampaignMap()
MAP.shape = 'H5'
MAP.map_data = '''
   ++ ++ ++ -- ME ME -- ++
   -- -- -- ME -- ME -- --
   -- -- ++ -- ME ++ MB --
   -- -- -- ME -- ++ -- ME
   -- -- -- -- ME -- ME -- 
'''
MAP.weight_data = '''
	10 10 10 10 10 10 10 10
	10 10 10 10 10 10 10 10
	10 10 10 10 10 10 10 10
	10 10 10 10 10 10 10 10
	10 10 10 10 10 10 10 10
'''
#MAP.camera_data = ['D4']
MAP.spawn_data = [
     {'battle': 0, 'enemy': 3},
     {'battle': 1, 'enemy': 1},
     {'battle': 2, 'enemy': 1},
     {'battle': 3, 'enemy': 1},
     {'battle': 4, 'enemy': 1, 'boss': 1},
	 {'battle': 5, 'enemy': 0},
	 {'battle': 6, 'enemy': 0},
	 {'battle': 7, 'enemy': 0},	 
 ]

A1, B1, C1, D1, E1, F1, G1, H1, \
A2, B2, C2, D2, E2, F2, G2, H2, \
A3, B3, C3, D3, E3, F3, G3, H3, \
A4, B4, C4, D4, E4, F4, G4, H4, \
A5, B5, C5, D5, E5, F5, G5, H5, \
    = MAP.flatten()



class Config:
	INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
	EDGE_LINES_HOUGHLINES_THRESHOLD = 40
	COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5
	INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (150, 255 - 24),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
	}
	EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 10,
        'distance': 50,
        'width': (0, 10),
        'wlen': 1000,
	}

class Campaign(CampaignBase):
	MAP = MAP

	def battle_0(self):
		return self.battle_default()

	def battle_7(self):
		return self.fleet_boss.clear_boss()
		
		
		
		