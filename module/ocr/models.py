from module.base.decorator import cached_property
from module.ocr.al_ocr import AlOcr


class OcrModel:
    @cached_property
    def azur_lane(self):
        # Folder: ./bin/cnocr_models/azur_lane
        # Size: 3.25MB
        # Model: densenet-lite-gru
        # Epoch: 15
        # Validation accuracy: 99.43%
        # Font: Impact, AgencyFB-Regular, MStiffHeiHK-UltraBold
        # Charset: 0123456789ABCDEFGHIJKLMNPQRSTUVWXYZ:/- (Letter 'O' and <space> is not included)
        # _num_classes: 39
        return AlOcr(
            model_name="densenet-lite-gru",
            model_epoch=15,
            root="./bin/cnocr_models/azur_lane",
            name="azur_lane",
        )

    @cached_property
    def cnocr(self):
        # Folder: ./bin/cnocr_models/cnocr
        # Size: 9.51MB
        # Model: densenet-lite-gru
        # Epoch: 39
        # Validation accuracy: 99.04%
        # Font: Various
        # Charset: Number, English character, Chinese character, symbols, <space>
        # _num_classes: 6426
        return AlOcr(
            model_name="densenet-lite-gru",
            model_epoch=39,
            root="./bin/cnocr_models/cnocr",
            name="cnocr",
        )

    @cached_property
    def jp(self):
        return AlOcr(
            model_name="densenet-lite-gru",
            model_epoch=125,
            root="./bin/cnocr_models/jp",
            name="jp",
        )

    @cached_property
    def tw(self):
        # Folder: ./bin/cnocr_models/tw
        # Size: 8.43MB
        # Model: densenet-lite-gru
        # Epoch: 63
        # Validation accuracy: 99.24%
        # Font: Various, 6 kinds
        # Charset: Numbers, Upper english characters, Chinese traditional characters
        # _num_classes: 5322
        return AlOcr(
            model_name="densenet-lite-gru",
            model_epoch=63,
            root="./bin/cnocr_models/tw",
            name="tw",
        )


OCR_MODEL = OcrModel()
