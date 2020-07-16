# Future plan

Here list the future plan for Alas, sorted from easy to hard.

Alas has a lot of handful public functions and class methods, from object detection to map logics, don't handcraft them again.



## Plans in 2020.06

- ~~Test chapter 6 when using 1 fleet~~ Done

- ~~Add logic to chapter 2, 4, 5, when using 2 fleets~~ Done

  > Chapter 1 to 5 are written in logic of 1 fleet, and I added the logic of 2 fleets in chapter 3, try to imitate that.

- Add more maps, from 7-3 to 13-4

  > 9-2, 9-3, 9-4, 10-1, 10-2, already done. Thanks Cerzo, Lanser, whoamikyo
  >
  > Read doc/development.md for details.
  >
  > Some new logics may not included, read module/map/map.py

- ~~Add support for hard map~~ Already done

  > Alas can use the map file from normal mode, no need to rewrite
  >
  > Add a new option in module/config/argparser.py, under the "main chapter".
  >
  > Add the arg name into module/config/dictionary.py
  >
  > Add arg into config/template.ini
  >
  > Load it in module/config/config.py
  >
  > Pass that parameter to `ensure_campaign_ui` in module/campaign/campaign_ui.py line 74

- Add support for dorm

  > Add new file module/reward/dorm.py
  >
  > There should be options: DORM_REWARD_INTERVAL (1 hour, 2 hour, 3 hour, 4 hour), USE_GEM_FOOD (yes, no)
  >
  > Should able to pick up love and coin in dorm, may hard to pick all of them, not a big deal.
  >
  > Call OCR to detect food remain and total
  >
  > Don't use template matching to detect which food is available, because the naval curry change from time to time. The unavailable food items have a white overlay, make good use of that.

- Adaptive parameters for perspective detection

  > When alas get an perspective error, it stops. Catch the errors, auto adjust the parameters and retry.
  >
  > Read perspective_en.md, see how alas do map detection, and you need to have some basic knowledge of perspective.

- Restart when get stuck or lost connection

  > Don't simply use `handle_popup_confirm()`, because many module also use that.
  >
  > After the restart, retreat from map, because alas can't resume from a unfinished map.
  >
  > Alas have highly wrapped API, you may need to touch some low-level functions to do that.
  >
  > When you're done, test the speed, see if it effects on the performance.

- ~~Try ascreencap~~ Already done

  > I notice that ALauto use ascreencap, test and see if it's faster than uiautomator2.
  >
  > If so, add that option in GUI, and set to default.

- ~~Update cnocr~~ 2020.07.15

  > If we use the latest `cnocr`, we can recognize English letters better, get rid of `mxnet==1.4.1`, have smaller model size.
  >
  > But I already train 2 models under `cnocr==1.0.0`, named `stage` and `digit`, test if they are compatible.

- ~~Re-train ocr models~~ 2020.07.15

  > The existing ocr model named `stage` and `digit` are poorly trained, you need to make sure letters are full-filled the image.
  >
  > The fat letters which is frequently used game is `Impact`
  >
  > The slim letters use in level and oil is `AgencyFB-Regular`
  >
  > The letters in research which looks cool is `MStiffHeiHK-UltraBold`
  >
  > It's better to use only one model to recognize all.

- Add support research

  > Do this after updating cnocr and retraining models.
  >
  > Imitating commission.py, use ocr to get research name, classify them, then choose

- ~~Re-fit the relationship between map swipe and screen swipe~~ Done, the magic number is 1.626

  > This function is `_map_swipe` in module/map/camera.py line 36. If you want to focus camera from D3 to E4, then it will do a swipe (-200, -140). A simple linear fit turn `(1, 1)` to be `(-200, -140)`.
  >
  > I fit this in 7-2, but i found it no working well in some large maps. Alas have to call `focus_to_grid_center` in line 89 to fix camera position. But sometimes that failed, alas update map data to the wrong grids, and cause a series of error until `ensure_edge_insight` is called.
  >
  > I do know that the relationship between map swipe and screen swipe is complex, but linear would be enough, because we won't swipe too far.
  >
  > How close is the camera on the map will also effect the relationship, you can use the `mid` of vertical lines the measure that. So closer camera means larger diff in vertical.mid, and further swipe, try to fit the the exact relationship.

- Combine perspective.py and homg_trans_beta brunch in ALauto

  > asd111333 shared his thoughts on map detection to me. His project is doing so good when there is only few empty grids on screen which is the weakness of Alas, and ALauto don't have a global map view, which is the strengthen of Alas.
  >
  > perspective.py can generate the camera setting needed in his approach, so no longer need to hard-code camera settings for different maps. 
  >
  > Alas work in 720p and ALauto works in 1080p, so there is a 1.5x scaling.
  >
 ```
 def get_homo_data(self, tile_width=209/1.5, tile_height=209/1.5):
     hori = self.horizontal[0].add(self.horizontal[-1])
     vert = self.vertical[0].add(self.vertical[-1])
     src_pts = hori.cross(vert).points
 
     x = len(self.vertical) - 1
     y = len(self.horizontal) - 1
 
     dst_pts = np.array([[0, 0], [x * tile_width, 0], [0, y * tile_height], [x * tile_width, y * tile_height]], dtype=float)
     dst_pts += src_pts[0]
 
     return [src_pts * 1.5, dst_pts * 1.5]
 ```
  >I replaced the assets in 720p, now can directly generate the parameter for `cv2.warpPerspective`

```
def get_perspective(self):
    tile_width = 140
    tile_height = 140
    # Generate homo from src_pts and dst_pts
    perspective = Perspective(image, config=self.config)
    hori = perspective.horizontal[0].add(perspective.horizontal[-1])
    vert = perspective.vertical[0].add(perspective.vertical[-1])
    src_pts = hori.cross(vert).points
    x = len(perspective.vertical) - 1
    y = len(perspective.horizontal) - 1
    dst_pts = np.array([[0, 0], [x * tile_width, 0], [0, y * tile_height], [x * tile_width, y * tile_height]],
                       dtype=float)
    dst_pts += src_pts[0]
    homo, _ = cv2.findHomography(src_pts, dst_pts)

    # Re-generate to align image
    area = self.config.DETECTING_AREA
    area = np.array([[area[0], area[1]], [area[2], area[1]], [area[0], area[3]], [area[2], area[3]]])
    matrix = homo.dot(np.pad(area, ((0, 0), (0, 1)), mode='constant', constant_values=1).T)
    x, y = matrix[0] / matrix[2], matrix[1] / matrix[2]
    x, y = x - np.min(x), y - np.min(y)
    homo, _ = cv2.findHomography(area, np.array([x, y]).T)

    # Perspective transform
    size = (np.ceil(np.max(x)).astype(int), np.ceil(np.max(y)).astype(int))
    screen_trans = cv2.warpPerspective(np.array(perspective.image), homo, size)
    screen_edge = cv2.Canny(screen_trans, 50, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    screen_edge = cv2.morphologyEx(screen_edge, cv2.MORPH_CLOSE, kernel)

    # Find an empty grid
    res = cv2.matchTemplate(screen_edge, free_tile_center, cv2.TM_CCOEFF_NORMED)
    _, similarity, _, location = cv2.minMaxLoc(res)
    logger.info(f'  free_tile_center_sim: {str(round(similarity, 3)).ljust(5, "0")}')
```

> I imagined a way to use two approach. After entering map, call perspective.py to generate camera data, and use homo_trans till the end. If get any error, fallback to perspective.
>
> This will be faster and with lower error rate, and get rid of the parameters of `scipy.signal.find_peaks`
>
> I got a problem now. Alas use the edge of the map to locate camera. If edge is not insight, locate camera from history swipe which may be unstable. When edges appear again, use that to correct camera location. So even if i use homo_trans, i still need to call perspective from time to time.