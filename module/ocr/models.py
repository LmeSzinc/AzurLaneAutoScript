from module.base.decorator import cached_property


class OcrModel:
    @cached_property
    def _OCR(self):
        from module.exception import ScriptError
        from module.webui.setting import State
        backend = State.deploy_config.OcrBackend
        if backend == 'mxnet':
            from module.ocr.al_ocr import AlOcr as _OCR
        elif backend == 'onnx':
            try:
                import onnxruntime
            except ImportError:
                from module.logger import logger
                logger.warning('ONNX Runtime is not available, fallback to MXNet')
                from module.ocr.al_ocr import AlOcr as _OCR
            else:
                from module.ocr.onnx_ocr import OnnxOcr as _OCR
        else:
            raise ScriptError(f'Unsupported OCR backend: {backend}')
        return _OCR

    def load(self):
        _ = self._OCR

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
        return self._OCR(model_name='densenet-lite-gru', model_epoch=15,
                         root='./bin/cnocr_models/azur_lane', name='azur_lane')
    @cached_property
    def azur_lane_jp(self):
        # Folder: ./bin/cnocr_models/azur_lane_jp
        # Size: 3.25MB
        # Model: densenet-lite-gru
        # Epoch: 20
        # Validation accuracy: 99.01%
        # Font: Impact, VibeMO Compressed Pro Thin, Folk R, Source Han Serif JP
        # Charset: 0123456789ABCDEFGHIJKLMNPQRSTUVWXYZ:/- (Letter 'O' and <space> is not included)
        # _num_classes: 39
        return self._OCR(model_name='densenet-lite-gru', model_epoch=20,
                         root='./bin/cnocr_models/azur_lane_jp', name='azur_lane_jp')
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
        return self._OCR(model_name='densenet-lite-gru', model_epoch=39,
                         root='./bin/cnocr_models/cnocr', name='cnocr')
    @cached_property
    def jp(self):
        return self._OCR(model_name='densenet-lite-gru', model_epoch=125,
                         root='./bin/cnocr_models/jp', name='jp')
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
        return self._OCR(model_name='densenet-lite-gru', model_epoch=63,
                         root='./bin/cnocr_models/tw', name='tw')


OCR_MODEL = OcrModel()
