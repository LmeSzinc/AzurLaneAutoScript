import numpy as np
# import cv2
from PIL import ImageEnhance
from PIL import Image

def enh_unfog(imageIN, sharp_factor=3.0, color_factor=2.0):
    imageIN = Image.fromarray(imageIN.astype('uint8')).convert('RGB')

    enh_shrp = ImageEnhance.Sharpness(imageIN)
    image_enh_1 = enh_shrp.enhance(sharp_factor)
    enh_col = ImageEnhance.Color(image_enh_1)
    image_enh_2 = enh_col.enhance(color_factor)

    image_enh_done = np.array(image_enh_2)
    #
    # cv2.imshow('img', image_enh_done)
    # cv2.imwrite('E:/AzurLaneAutoScript/screenshots/unfog2.png', image_enh_done)
    # cv2.waitKey()
    #
    return image_enh_done
