import module.config.server as server
from module.base.decorator import cached_property, del_cached_property
from module.base.resource import Resource
from module.base.utils import *
from module.exception import ScriptError


class Button(Resource):
    def __init__(self, file, area, search, color, button):
        """
        Args:
            file: Filepath to an assets
            area: Area to crop template
            search: Area to search from, 20px larger than `area` by default
            color: Average color of assets
            button: Area to click if assets appears on the image
        """
        self.file: str = file
        self.area: t.Tuple[int, int, int, int] = area
        self.search: t.Tuple[int, int, int, int] = search
        self.color: t.Tuple[int, int, int] = color
        self._button: t.Tuple[int, int, int, int] = button

        self.resource_add(self.file)
        self._button_offset: t.Tuple[int, int] = (0, 0)

    @property
    def button(self):
        return area_offset(self._button, self._button_offset)

    def load_offset(self, button):
        self._button_offset = button._button_offset

    def clear_offset(self):
        self._button_offset = (0, 0)

    @cached_property
    def image(self):
        return load_image(self.file, self.area)

    def resource_release(self):
        del_cached_property(self, 'image')
        self.clear_offset()

    def __str__(self):
        return self.file

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.file)

    def __bool__(self):
        return True

    def match_color(self, image, threshold=10) -> bool:
        """
        Check if the button appears on the image, using average color

        Args:
            image (np.ndarray): Screenshot.
            threshold (int): Default to 10.

        Returns:
            bool: True if button appears on screenshot.
        """
        color = get_color(image, self.area)
        return color_similar(
            color1=color,
            color2=self.color,
            threshold=threshold
        )

    def match_template(self, image, similarity=0.85, direct_match=False) -> bool:
        """
        Detects assets by template matching.

        To Some buttons, its location may not be static, `_button_offset` will be set.

        Args:
            image: Screenshot.
            similarity (float): 0-1.
            direct_match: True to ignore `self.search`

        Returns:
            bool.
        """
        if not direct_match:
            image = crop(image, self.search, copy=False)
        res = cv2.matchTemplate(self.image, image, cv2.TM_CCOEFF_NORMED)
        _, sim, _, point = cv2.minMaxLoc(res)

        self._button_offset = np.array(point) + self.search[:2] - self.area[:2]
        return sim > similarity

    def match_multi_template(self, image, similarity=0.85, direct_match=False):
        """
        Detects assets by template matching, return multiple reults

        Args:
            image: Screenshot.
            similarity (float): 0-1.
            direct_match: True to ignore `self.search`

        Returns:
            list:
        """
        if not direct_match:
            image = crop(image, self.search, copy=False)
        res = cv2.matchTemplate(self.image, image, cv2.TM_CCOEFF_NORMED)
        res = cv2.inRange(res, similarity, 1.)
        try:
            points = np.array(cv2.findNonZero(res))[:, 0, :]
            points += self.search[:2]
            return points.tolist()
        except IndexError:
            # Empty result
            # IndexError: too many indices for array: array is 0-dimensional, but 3 were indexed
            return []

    def match_template_color(self, image, similarity=0.85, threshold=30, direct_match=False) -> bool:
        """
        Template match first, color match then

        Args:
            image: Screenshot.
            similarity (float): 0-1.
            threshold (int): Default to 10.
            direct_match: True to ignore `self.search`

        Returns:
            bool.
        """
        matched = self.match_template(image, similarity=similarity, direct_match=direct_match)
        if not matched:
            return False

        area = area_offset(self.area, offset=self._button_offset)
        color = get_color(image, area)
        return color_similar(
            color1=color,
            color2=self.color,
            threshold=threshold
        )


class ButtonWrapper(Resource):
    def __init__(self, name='MULTI_ASSETS', **kwargs):
        self.name = name
        self.data_buttons = kwargs
        self._matched_button: t.Optional[Button] = None
        self.resource_add(f'{name}:{next(self.iter_buttons(), None)}')

    def resource_release(self):
        del_cached_property(self, 'buttons')
        self._matched_button = None

    def __str__(self):
        return self.name

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.name)

    def __bool__(self):
        return True

    def iter_buttons(self) -> t.Iterator[Button]:
        for _, assets in self.data_buttons.items():
            if isinstance(assets, Button):
                yield assets
            elif isinstance(assets, list):
                for asset in assets:
                    yield asset

    @cached_property
    def buttons(self) -> t.List[Button]:
        for trial in [server.lang, 'share', 'cn']:
            try:
                assets = self.data_buttons[trial]
                if isinstance(assets, Button):
                    return [assets]
                elif isinstance(assets, list):
                    return assets
            except KeyError:
                pass

        raise ScriptError(f'ButtonWrapper({self}) on server {server.lang} has no fallback button')

    def match_color(self, image, threshold=10) -> bool:
        for assets in self.buttons:
            if assets.match_color(image, threshold=threshold):
                self._matched_button = assets
                return True
        return False

    def match_template(self, image, similarity=0.85, direct_match=False) -> bool:
        for assets in self.buttons:
            if assets.match_template(image, similarity=similarity, direct_match=direct_match):
                self._matched_button = assets
                return True
        return False

    def match_multi_template(self, image, similarity=0.85, threshold=5, direct_match=False):
        """
        Detects assets by template matching, return multiple results

        Args:
            image: Screenshot.
            similarity (float): 0-1.
            threshold:
            direct_match: True to ignore `self.search`

        Returns:
            list[ClickButton]:
        """
        ps = []
        for assets in self.buttons:
            ps += assets.match_multi_template(image, similarity=similarity, direct_match=direct_match)
        if not ps:
            return []

        from module.base.utils.points import Points
        ps = Points(ps).group(threshold=threshold)
        area_list = [area_offset(self.area, p - self.area[:2]) for p in ps]
        button_list = [area_offset(self.button, p - self.area[:2]) for p in ps]
        return [
            ClickButton(area=info[0], button=info[1], name=f'{self.name}_result{i}')
            for i, info in enumerate(zip(area_list, button_list))
        ]

    def match_template_color(self, image, similarity=0.85, threshold=30, direct_match=False) -> bool:
        for assets in self.buttons:
            if assets.match_template_color(
                    image, similarity=similarity, threshold=threshold, direct_match=direct_match):
                self._matched_button = assets
                return True
        return False

    @property
    def matched_button(self) -> Button:
        if self._matched_button is None:
            return self.buttons[0]
        else:
            return self._matched_button

    @property
    def area(self) -> tuple[int, int, int, int]:
        return self.matched_button.area

    @property
    def search(self) -> tuple[int, int, int, int]:
        return self.matched_button.search

    @property
    def color(self) -> tuple[int, int, int]:
        return self.matched_button.color

    @property
    def button(self) -> tuple[int, int, int, int]:
        return self.matched_button.button

    @property
    def button_offset(self) -> tuple[int, int]:
        return self.matched_button._button_offset

    @property
    def width(self) -> int:
        return area_size(self.area)[0]

    @property
    def height(self) -> int:
        return area_size(self.area)[1]

    def load_offset(self, button):
        """
        Load offset from another button.

        Args:
            button (Button, ButtonWrapper):
        """
        if isinstance(button, ButtonWrapper):
            button = button.matched_button
        for b in self.iter_buttons():
            b.load_offset(button)

    def clear_offset(self):
        for b in self.iter_buttons():
            b.clear_offset()

    def load_search(self, area):
        """
        Set `search` attribute.
        Note that this method is irreversible.

        Args:
            area:
        """
        for b in self.iter_buttons():
            b.search = area


class ClickButton:
    def __init__(self, button, name='CLICK_BUTTON'):
        self.area = button
        self.button = button
        self.name = name

    def __str__(self):
        return self.name

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.name)

    def __bool__(self):
        return True


def match_template(image, template, similarity=0.85):
    """
    Args:
        image (np.ndarray): Screenshot
        template (np.ndarray):
        area (tuple): Crop area of image.
        offset (int, tuple): Detection area offset.
        similarity (float): 0-1. Similarity. Lower than this value will return float(0).

    Returns:
        bool:
    """
    res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    _, sim, _, point = cv2.minMaxLoc(res)
    return sim > similarity
