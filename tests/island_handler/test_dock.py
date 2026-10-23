"""Screenshot golden results; awaiting human review of collection/ images."""
from module.testing.screenshot import image

from module.island_handler.dock import IslandDock
from module.island_handler.dock_scanner import CharacterScanner


class TestCharactersJP:
    @image('island/dock/f9bd49a5', server='jp')
    def test_two_selected_characters(self, main: IslandDock):
        grid = main.get_dock_grid()
        characters = CharacterScanner(grid, identity=None, emotion=None, emotion_limit=None,
                                      grade=None, status=None).scan(main.device.image)
        actual = dict(in_dock=main.is_in_island_dock(), characters=[dict(
            identity=character.identity, emotion=character.emotion, emotion_limit=character.emotion_limit,
            grade=character.grade, status=character.status, area=character.button.area,
            button=character.button.button,
            selected=main.is_button_selected(character.button, color=(19, 181, 231)))
            for character in characters])
        regions = [(entry['area'], 'character #{} {} emotion={}/{} grade={} status={} selected={}'.format(
            index, entry['identity'], entry['emotion'], entry['emotion_limit'], entry['grade'],
            entry['status'], entry['selected'])) for index, entry in enumerate(actual['characters'])]
        main.device.review(actual, regions)
        assert actual == {
            'characters': [
                {
                    'area': (56, 139, 180, 303),
                    'button': (56, 139, 180, 303),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'A',
                    'identity': 'Le_Malin',
                    'selected': False,
                    'status': 'occupied',
                },
                {
                    'area': (196, 139, 320, 303),
                    'button': (196, 139, 320, 303),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'B',
                    'identity': 'Chao_Ho',
                    'selected': False,
                    'status': 'occupied',
                },
                {
                    'area': (336, 139, 460, 303),
                    'button': (336, 139, 460, 303),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'B',
                    'identity': 'August_von_Parseval',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (476, 139, 600, 303),
                    'button': (476, 139, 600, 303),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'A',
                    'identity': 'Prinz_Eugen',
                    'selected': False,
                    'status': 'occupied',
                },
                {
                    'area': (616, 139, 740, 303),
                    'button': (616, 139, 740, 303),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'A',
                    'identity': 'Shimakaze',
                    'selected': True,
                    'status': 'free',
                },
                {
                    'area': (756, 139, 880, 303),
                    'button': (756, 139, 880, 303),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'B',
                    'identity': 'Cheshire',
                    'selected': True,
                    'status': 'free',
                },
                {
                    'area': (56, 319, 180, 483),
                    'button': (56, 319, 180, 483),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'A',
                    'identity': 'Unicorn',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (196, 319, 320, 483),
                    'button': (196, 319, 320, 483),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'A',
                    'identity': 'Hood',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (336, 319, 460, 483),
                    'button': (336, 319, 460, 483),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'B',
                    'identity': 'Helena',
                    'selected': False,
                    'status': 'occupied',
                },
                {
                    'area': (476, 319, 600, 483),
                    'button': (476, 319, 600, 483),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'C',
                    'identity': 'Ying_Swei',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (616, 319, 740, 483),
                    'button': (616, 319, 740, 483),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'C',
                    'identity': 'Amagi_chan',
                    'selected': False,
                    'status': 'occupied',
                },
                {
                    'area': (756, 319, 880, 483),
                    'button': (756, 319, 880, 483),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'C',
                    'identity': 'New_Jersey',
                    'selected': False,
                    'status': 'occupied',
                },
            ],
            'in_dock': True,
        }

    @image('island/dock/5c2752bc', server='jp')
    def test_one_selected_character(self, main: IslandDock):
        grid = main.get_dock_grid()
        characters = CharacterScanner(grid, identity=None, emotion=None, emotion_limit=None,
                                      grade=None, status=None).scan(main.device.image)
        actual = dict(in_dock=main.is_in_island_dock(), characters=[dict(
            identity=character.identity, emotion=character.emotion, emotion_limit=character.emotion_limit,
            grade=character.grade, status=character.status, area=character.button.area,
            button=character.button.button,
            selected=main.is_button_selected(character.button, color=(19, 181, 231)))
            for character in characters])
        regions = [(entry['area'], 'character #{} {} emotion={}/{} grade={} status={} selected={}'.format(
            index, entry['identity'], entry['emotion'], entry['emotion_limit'], entry['grade'],
            entry['status'], entry['selected'])) for index, entry in enumerate(actual['characters'])]
        main.device.review(actual, regions)
        assert actual == {
            'characters': [
                {
                    'area': (56, 139, 180, 303),
                    'button': (56, 139, 180, 303),
                    'emotion': 999,
                    'emotion_limit': 999,
                    'grade': 'E',
                    'identity': 'Manjuu',
                    'selected': True,
                    'status': 'free',
                },
                {
                    'area': (196, 139, 320, 303),
                    'button': (196, 139, 320, 303),
                    'emotion': 0,
                    'emotion_limit': 110,
                    'grade': 'E',
                    'identity': 'Anchorage',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (336, 139, 460, 303),
                    'button': (336, 139, 460, 303),
                    'emotion': 110,
                    'emotion_limit': 110,
                    'grade': 'E',
                    'identity': 'Fei_Yuen',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (476, 139, 600, 303),
                    'button': (476, 139, 600, 303),
                    'emotion': 110,
                    'emotion_limit': 110,
                    'grade': 'E',
                    'identity': 'Leonardo_da_Vinci',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (616, 139, 740, 303),
                    'button': (616, 139, 740, 303),
                    'emotion': 2,
                    'emotion_limit': 110,
                    'grade': 'E',
                    'identity': 'Mogador',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (756, 139, 880, 303),
                    'button': (756, 139, 880, 303),
                    'emotion': 110,
                    'emotion_limit': 110,
                    'grade': 'E',
                    'identity': 'Royal_Fortune',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (56, 319, 180, 483),
                    'button': (56, 319, 180, 483),
                    'emotion': 110,
                    'emotion_limit': 110,
                    'grade': 'E',
                    'identity': 'Oceana',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (196, 319, 320, 483),
                    'button': (196, 319, 320, 483),
                    'emotion': 110,
                    'emotion_limit': 110,
                    'grade': 'D',
                    'identity': 'William_D_Porter',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (336, 319, 460, 483),
                    'button': (336, 319, 460, 483),
                    'emotion': 130,
                    'emotion_limit': 130,
                    'grade': 'D',
                    'identity': 'Saratoga',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (476, 319, 600, 483),
                    'button': (476, 319, 600, 483),
                    'emotion': 110,
                    'emotion_limit': 110,
                    'grade': 'D',
                    'identity': 'Javelin',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (616, 319, 740, 483),
                    'button': (616, 319, 740, 483),
                    'emotion': 110,
                    'emotion_limit': 110,
                    'grade': 'D',
                    'identity': 'Takao',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (756, 319, 880, 483),
                    'button': (756, 319, 880, 483),
                    'emotion': 110,
                    'emotion_limit': 110,
                    'grade': 'D',
                    'identity': 'Atago',
                    'selected': False,
                    'status': 'free',
                },
            ],
            'in_dock': True,
        }


class TestCharactersCN:
    @image('island/dock/a4f3aae4', server='cn')
    def test_no_selected_characters(self, main: IslandDock):
        grid = main.get_dock_grid()
        characters = CharacterScanner(grid, identity=None, emotion=None, emotion_limit=None,
                                      grade=None, status=None).scan(main.device.image)
        actual = dict(in_dock=main.is_in_island_dock(), characters=[dict(
            identity=character.identity, emotion=character.emotion, emotion_limit=character.emotion_limit,
            grade=character.grade, status=character.status, area=character.button.area,
            button=character.button.button,
            selected=main.is_button_selected(character.button, color=(19, 181, 231)))
            for character in characters])
        regions = [(entry['area'], 'character #{} {} emotion={}/{} grade={} status={} selected={}'.format(
            index, entry['identity'], entry['emotion'], entry['emotion_limit'], entry['grade'],
            entry['status'], entry['selected'])) for index, entry in enumerate(actual['characters'])]
        main.device.review(actual, regions)
        assert actual == {
            'characters': [
                {
                    'area': (56, 206, 180, 370),
                    'button': (56, 206, 180, 370),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'C',
                    'identity': 'William_D_Porter',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (196, 206, 320, 370),
                    'button': (196, 206, 320, 370),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'A',
                    'identity': 'Yat_Sen',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (336, 206, 460, 370),
                    'button': (336, 206, 460, 370),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'A',
                    'identity': 'Prinz_Eugen',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (476, 206, 600, 370),
                    'button': (476, 206, 600, 370),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'A',
                    'identity': 'Javelin',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (616, 206, 740, 370),
                    'button': (616, 206, 740, 370),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'C',
                    'identity': 'Explorer',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (756, 206, 880, 370),
                    'button': (756, 206, 880, 370),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'C',
                    'identity': 'Navigator',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (56, 386, 180, 550),
                    'button': (56, 386, 180, 550),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'B',
                    'identity': 'Oceana',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (196, 386, 320, 550),
                    'button': (196, 386, 320, 550),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'B',
                    'identity': 'Fei_Yuen',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (336, 386, 460, 550),
                    'button': (336, 386, 460, 550),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'C',
                    'identity': 'Takao',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (476, 386, 600, 550),
                    'button': (476, 386, 600, 550),
                    'emotion': 150,
                    'emotion_limit': 150,
                    'grade': 'A',
                    'identity': 'Hood',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (616, 386, 740, 550),
                    'button': (616, 386, 740, 550),
                    'emotion': 110,
                    'emotion_limit': 150,
                    'grade': 'C',
                    'identity': 'Laffey',
                    'selected': False,
                    'status': 'free',
                },
                {
                    'area': (756, 386, 880, 550),
                    'button': (756, 386, 880, 550),
                    'emotion': 999,
                    'emotion_limit': 999,
                    'grade': 'E',
                    'identity': 'Manjuu',
                    'selected': False,
                    'status': 'free',
                },
            ],
            'in_dock': True,
        }
