from ppocronnx.predict_system import TextSystem as TextSystem_


class TextSystem(TextSystem_):
    def __init__(
            self,
            use_angle_cls=False,
            box_thresh=0.6,
            unclip_ratio=1.6,
            rec_model_path=None,
            det_model_path=None,
            ort_providers=None
    ):
        super().__init__(
            use_angle_cls=use_angle_cls,
            box_thresh=box_thresh,
            unclip_ratio=unclip_ratio,
            rec_model_path=rec_model_path,
            det_model_path=det_model_path,
            ort_providers=ort_providers
        )

    # def ocr_single_line(self, img):
    #     img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    #     return super().ocr_single_line(img)
    #
    # def detect_and_ocr(self, img: np.ndarray,**kwargs):
    #     img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    #     return super().detect_and_ocr(img, **kwargs)
