"""Verify the OCR adapter in a fresh interpreter and a spawned worker."""
import multiprocessing
import sys


def check():
    from module.ocr.al_ocr import AlOcr
    from module.ocr.models import OCR_MODEL
    expected = 'alas_onnx_ocr'
    assert AlOcr.__module__ == expected
    for name in ('azur_lane', 'azur_lane_jp', 'cnocr', 'jp', 'tw'):
        assert isinstance(getattr(OCR_MODEL, name), AlOcr)
    assert 'mxnet' not in sys.modules
    # New ImageIO defaults decode this grayscale GIF as RGB, crashing stage matching.
    from module.base.template import Template
    import numpy as np
    template = Template('assets/cn/template/TEMPLATE_STAGE_CLEAR_20240725.gif')
    assert all(frame.ndim == 2 for frame in template.image), 'GIF decoder regression'
    template.match_multi(np.full((519, 1064), 255, dtype=np.uint8))
    if expected == 'alas_onnx_ocr':
        from pathlib import Path
        from PIL import Image
        import json
        fixtures = Path(__file__).parent / 'fixtures'
        cases = json.loads((fixtures / 'cases.json').read_text())
        for case in cases:
            image = np.array(Image.open(fixtures / case['image']))
            model = getattr(OCR_MODEL, case['model'])
            actual = ''.join(model.atomic_ocr_for_single_line(image, case.get('alphabet')))
            if case.get('normalize_stage'):
                from module.campaign.campaign_ocr import CampaignOcr
                actual = CampaignOcr._campaign_ocr_result_process(actual)
            assert actual == case['expected'], (case, actual)
        # All languages must load and return no invented text on blank crops.
        for name in ('azur_lane', 'azur_lane_jp', 'cnocr', 'jp', 'tw'):
            model = getattr(OCR_MODEL, name)
            assert model.atomic_ocr_for_single_lines([]) == []
            assert model.atomic_ocr_for_single_lines([np.full((32, 100), 255, dtype=np.uint8)]) == [[]]
        model = OCR_MODEL.azur_lane
        numeric = [case for case in cases if case['model'] == 'azur_lane' and case['expected'].isdigit()]
        images = [np.array(Image.open(fixtures / case['image'])) for case in numeric]
        actual = [''.join(chars) for chars in model.atomic_ocr_for_single_lines(images, '0123456789')]
        assert actual == [case['expected'] for case in numeric], actual
        # A restrictive call must not leak its alphabet into the following request.
        assert model.atomic_ocr_for_single_line(images[0], '0123') != list(numeric[0]['expected'])
        assert ''.join(model.atomic_ocr_for_single_line(images[0])) == numeric[0]['expected']


if __name__ == '__main__':
    # Match gui.py's import root when invoked by file path.
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    check()
    process = multiprocessing.get_context('spawn').Process(target=check)
    process.start()
    process.join(30)
    if process.is_alive():
        process.terminate()
        process.join()
        raise RuntimeError('OCR worker check timed out')
    assert process.exitcode == 0, process.exitcode
    print('PASS: OCR fixtures, five models, batch/whitelist isolation, and grayscale GIF matching in parent and spawned worker')
