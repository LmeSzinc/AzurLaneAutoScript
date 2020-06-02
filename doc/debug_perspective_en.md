# How to debug a perspective error

## Normal logs

This is an example log.

```
2020-06-03 00:44:46.221 | INFO |           vanish_point: (  646, -1736)
2020-06-03 00:44:46.222 | INFO |          distant_point: (-2321, -1736)
2020-06-03 00:44:46.266 | INFO | 0.235s  _   Horizontal: 5 (7 inner, 3 edge)
2020-06-03 00:44:46.266 | INFO | Edges: / \    Vertical: 9 (10 inner, 3 edge)
2020-06-03 00:44:46.273 | INFO |            Center grid: (3, 1)
2020-06-03 00:44:46.493 | INFO | -- -- -- -- -- 2M -- --
2020-06-03 00:44:46.501 | INFO | MY -- -- MY -- -- 3M --
2020-06-03 00:44:46.501 | INFO | -- -- FL -- -- -- -- --
2020-06-03 00:44:46.501 | INFO | -- 1L -- MY -- 2L --   
```



## Too few grid lines

This may happens when it detected too few grid lines.

```  File "E:\ProgramData\Pycharm\AzurLaneAutoScript\module\map\camera.py", line 114, in update
  File "AzurLaneAutoScript\module\map\camera.py", line 114, in update
    self.grids = Grids(self.device.image, config=self.config)
  File "AzurLaneAutoScript\module\map\grids.py", line 19, in __init__
    super().__init__(image, config)
  File "AzurLaneAutoScript\module\map\perspective.py", line 81, in __init__
    self.crossings = self.horizontal.cross(self.vertical)
  File "AzurLaneAutoScript\module\map\perspective_items.py", line 170, in cross
    points = np.vstack(self.cross_two_lines(self, other))
  File "lib\site-packages\numpy\core\shape_base.py", line 234, in vstack
    return _nx.concatenate([atleast_2d(_m) for _m in tup], 0)
  File "lib\site-packages\numpy\core\shape_base.py", line 234, in <listcomp>
    return _nx.concatenate([atleast_2d(_m) for _m in tup], 0)
  File "AzurLaneAutoScript\module\map\perspective_items.py", line 163, in cross_two_lines
    for rho1, sin1, cos1 in zip(lines1.rho, lines1.sin, lines1.cos):
AttributeError: 'Lines' object has no attribute 'rho'
```

```
  File "AzurLaneAutoScript\module\map\camera.py", line 114, in update
    self.grids = Grids(self.device.image, config=self.config)
  File "AzurLaneAutoScript\module\map\grids.py", line 19, in __init__
    super().__init__(image, config)
  File "AzurLaneAutoScript\module\map\perspective.py", line 98, in __init__
    self.horizontal, inner=inner_h.group(), edge=edge_h)
  File "AzurLaneAutoScript\module\map\perspective.py", line 352, in line_cleanse
    clean = self.mid_cleanse(origin, is_horizontal=lines.is_horizontal, threshold=threshold)
  File "AzurLaneAutoScript\module\map\perspective.py", line 346, in mid_cleanse
    mids = convert_to_y(mids)
  File "AzurLaneAutoScript\module\map\perspective.py", line 277, in convert_to_y
    return Points([[x, self.config.SCREEN_CENTER[1]] for x in xs], config=self.config) \
  File "AzurLaneAutoScript\module\map\perspective_items.py", line 15, in __init__
    self.x, self.y = self.points.T
ValueError: not enough values to unpack (expected 2, got 0)
```

Try reduce the threshold of `cv2.HoughLines`. Default is 75.

Lower threshold means more lines.

```
INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
EDGE_LINES_HOUGHLINES_THRESHOLD = 40
```

Then you should also lower this and make a closer fit to the lines.

Lower means closer fit, ignore more wrong lines.

```
COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.5
```



## Camera outside map

```
  File "AzurLaneAutoScript-master\module\map\camera.py", line 114, in update
    self.grids = Grids(self.device.image, config=self.config)
  File "AzurLaneAutoScript-master\module\map\grids.py", line 19, in __init__
    super().__init__(image, config)
  File "AzurLaneAutoScript-master\module\map\perspective.py", line 98, in __init__
    self.horizontal, inner=inner_h.group(), edge=edge_h)
  File "AzurLaneAutoScript-master\module\map\perspective.py", line 383, in line_cleanse
    raise PerspectiveError('Camera outside map: to the %s' % ('upper' if lines.is_horizontal else 'right'))
module.exception.PerspectiveError: Camera outside map: to the upper
```

Alas can not handle if camera is not focusing on any map grid, it will swipe back if catches `Camera outside map`. This may happens when some inner lines are detected as edge lines.

Try adjust the parameter of `scipy.signal.find_peaks`, the `height` value.

- **height** Lower means detect lighter lines, 255 means pure black.
- **width** Line width, in pixels.
- **prominence** Line needs to be how much darker than surrounding pixels.
- **distance** Minimum distance between two detected point on line.
- **wlen** Maximum amount of data to be processed in one time.

Know more about these parameters [here](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html)

```
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
    'wlen': 1000
}
```



## Coincident point unexpected

```
2020-05-31 20:04:47.397 | INFO | Horizontal coincident point unexpected: [-92.817316   141.99589405]
2020-05-31 20:04:48.509 | INFO | Vertical coincident point unexpected: [-692.01967461  141.68981244]
```

Try adjust the initial value of coincident point. if 141.99589405 is in (129 - 3, 129 + 3), it shut up.

But remember, an incorrect value will ruin everything in map detection, it usually works fine with these logs show up.

```
MID_DIFF_RANGE_H = (129 - 3, 129 + 3)
MID_DIFF_RANGE_V = (129 - 3, 129 + 3)
```



## Too many deleted lines

