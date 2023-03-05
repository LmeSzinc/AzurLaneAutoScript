# coding: utf-8
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""
The previous version of this file is coded by my colleague Chuhao Chen.
"""
import numpy as np
from PIL import Image


THRESHOLD = 145  # for white background
TABLE = [1] * THRESHOLD + [0] * (256 - THRESHOLD)


def line_split(image, table=TABLE, split_threshold=0, blank=True):
    """
    :param image: PIL.Image类型的原图或numpy.ndarray
    :param table: 二值化的分布值，默认值即可
    :param split_threshold: int, 分割阈值
    :param blank: bool,是否留白.True会保留上下方的空白部分
    :return: list,元素为按行切分出的子图与位置信息的list
    """
    if not isinstance(image, Image.Image):
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        else:
            raise TypeError

    image_ = image.convert("L")
    bn = image_.point(table, "1")
    bn_mat = np.array(bn)
    h, pic_len = bn_mat.shape
    project = np.sum(bn_mat, 1)
    pos = np.where(project <= split_threshold)[0]
    if len(pos) == 0 or pos[0] != 0:
        pos = np.insert(pos, 0, 0)
    if pos[-1] != len(project):
        pos = np.append(pos, len(project))
    diff = np.diff(pos)

    if len(diff) == 0:
        return [[np.array(image), (0, 0, pic_len, h)]]

    width = np.max(diff)
    coordinate = list(zip(pos[:-1], pos[1:]))
    info = list(zip(diff, coordinate))
    info = list(filter(lambda x: x[0] > 10, info))

    split_pos = []
    temp = []
    for pos_info in info:
        if width - 2 <= pos_info[0] <= width:
            if temp:
                split_pos.append(temp.pop(0))
            split_pos.append(pos_info)

        elif pos_info[0] < width - 2:
            temp.append(pos_info)
            if len(temp) > 1:
                s, e = temp[0][1][0], temp[1][1][1]
                if e - s <= width + 2:
                    temp = [(e - s, (s, e))]
                else:
                    split_pos.append(temp.pop(0))

    if temp:
        split_pos.append(temp[0])

    # crop images with split_pos
    line_res = []
    if blank:
        if len(split_pos) == 1:
            pos_info = split_pos[0][1]
            ymin, ymax = max(0, pos_info[0] - 2), min(h, pos_info[1] + 2)
            return [
                [
                    np.array(image.crop((0, ymin, pic_len, ymax))),
                    (0, ymin, pic_len, ymax),
                ]
            ]

        length = len(split_pos)
        for i in range(length):
            if i == 0:
                next_info = split_pos[i + 1]
                margin = min(next_info[1][0] - split_pos[i][1][1], 2)
                ymin, ymax = (
                    max(0, split_pos[i][1][0] - margin),
                    split_pos[i][1][1] + margin,
                )
                x1, y1, x2, y2 = 0, ymin, pic_len, ymax
                sub = image.crop((x1, y1, x2, y2))
            elif i == length - 1:
                pre_info = split_pos[i - 1]
                margin = min(split_pos[i][1][0] - pre_info[1][1], 2)
                ymin, ymax = split_pos[i][1][0] - margin, min(
                    h, split_pos[i][1][1] + margin
                )
                x1, y1, x2, y2 = 0, ymin, pic_len, ymax
                sub = image.crop((x1, y1, x2, y2))
            else:
                next_info = split_pos[i + 1]
                pre_info = split_pos[i - 1]
                margin = min(
                    split_pos[i][1][0] - pre_info[1][1],
                    next_info[1][0] - split_pos[i][1][0],
                    2,
                )
                ymin, ymax = split_pos[i][1][0] - margin, split_pos[i][1][1] + margin
                x1, y1, x2, y2 = 0, ymin, pic_len, ymax
                sub = image.crop((x1, y1, x2, y2))

            line_res.append([np.array(sub), (x1, y1, x2, y2)])
    else:
        for pos_info in split_pos:
            x1, y1, x2, y2 = 0, pos_info[1][0], pic_len, pos_info[1][1]
            sub = image.crop((x1, y1, x2, y2))
            line_res.append([np.array(sub), (x1, y1, x2, y2)])

    return line_res
