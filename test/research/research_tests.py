import sys
import unittest

from module.base.utils import load_image
from module.config.server import set_server
from module.research.project import research_detect

sys.path.append('././')


class TestResearch(unittest.TestCase):

    def test_research_detect(self):
        # set server
        set_server('en')

        # load image from disk
        file = r'D:/project/AlasTest/research/RESEARCH.png'
        image = load_image(file)

        # execute research_detect
        projects = research_detect(image)

        # assert result
        self.assertEqual(str(projects[0]), 'S2 H-339-MI', 'First research detect error')
        self.assertEqual(str(projects[1]), 'S4 D-482-RF', 'Second research detect error')
        self.assertEqual(str(projects[2]), 'S2 H-387-MI', 'Third research detect error')
        self.assertEqual(str(projects[3]), 'S4 T-249-MI', 'Fourth research detect error')
        self.assertEqual(str(projects[4]), 'S4 G-236-MI', 'Fifth research detect error')


if __name__ == '__main__':
    unittest.main()
