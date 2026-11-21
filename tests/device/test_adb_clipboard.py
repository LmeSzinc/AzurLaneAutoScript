import struct
from pathlib import Path

import pytest

from module.device.method.adb_clipboard import ClipboardBinderError, decode_clipboard_parcel


def integer(value):
    return struct.pack('<i', value)


def string(value, utf8=False):
    if value is None:
        return integer(-1)
    raw = value.encode('utf-16-le', 'surrogatepass')
    if utf8:
        units = ''.join(chr(unit) for (unit,) in struct.iter_unpack('<H', raw))
        raw = units.encode('utf-8', 'surrogatepass').replace(b'\0', b'\xc0\x80')
    width = 1 if utf8 else 2
    raw = integer(len(raw) // width) + raw + b'\0' * width
    return raw + b'\0' * (-len(raw) % 4)


def bundle(values):
    if values is None:
        return integer(-1)
    if not values:
        return integer(0)
    return integer(len(values)) + integer(0x4C444E42) + values


def clip_bytes(sdk, values, *, label='different label', extras=None, confidence=b'',
               icon=0, item_flags=None, styled=False, html=None):
    # Fields follow AOSP ClipDescription/ClipData.writeToParcel, independently
    # of the decoder's cursor. TextUtils changed to String8 at SDK 30.
    utf8 = sdk >= 30
    data = integer(0) + integer(1)
    data += integer(1) + string(label, utf8)
    data += integer(2) + string('text/plain') + string('text/html')
    data += bundle(extras)
    if sdk >= 26:
        data += struct.pack('<q', 1793700000000)
    if sdk >= 31:
        data += integer(int(styled)) + integer(3) + bundle(confidence)
    data += integer(icon) + integer(len(values))
    fields = 5 if sdk >= 35 else 4 if sdk >= 31 else 2
    for value in values:
        data += integer(0 if styled else 1) + string(value, utf8)
        if styled:
            data += integer(7) + integer(1) + integer(0) + integer(len(value)) + integer(33) + integer(0)
        data += string(html, utf8)
        data += item_flags if item_flags is not None else integer(0) * fields
    return data


def dump(data, inline=False):
    assert len(data) % 4 == 0
    if inline:
        words = ' '.join(f'{word:08x}' for word in struct.unpack('<' + 'I' * (len(data) // 4), data))
        return f"Result: Parcel({words} 'deadbeef different printable content')"
    rows = []
    for offset in range(0, len(data), 16):
        row = data[offset:offset + 16]
        words = ' '.join(f'{word:08x}' for word in struct.unpack('<' + 'I' * (len(row) // 4), row))
        rows.append(f"  0x{offset:08x}: {words} 'deadbeef not clipboard text'")
    return 'Result: Parcel(\n' + '\n'.join(rows) + '\n)'


@pytest.mark.parametrize('sdk', [24, 25, 26, 29, 30, 31, 33, 34, 35, 36])
@pytest.mark.parametrize('value', ['', '.', '  A.b\n蓝色😀\0\t  ', 'AlasClipboard:%s "quoted"'])
def test_text_preserves_bytes_and_ignores_label_and_printable_column(sdk, value):
    assert decode_clipboard_parcel(dump(clip_bytes(sdk, [value])), sdk) == value


def test_jni_string8_preserves_modified_utf8_nul_and_surrogate_pairs():
    reply = clip_bytes(35, ['\0😀\ud800'])
    # Literal JNI bytes for NUL, D83D DE00 (emoji), and an unpaired D800.
    assert b'\xc0\x80\xed\xa0\xbd\xed\xb8\x80\xed\xa0\x80' in reply
    assert decode_clipboard_parcel(dump(reply), 35) == '\0😀\ud800'


@pytest.mark.parametrize('name,sdk,expected', [
    ('android12-unicode.parcel', 32, '中文 日本語 café 😀 𠀋'),
    ('android15-unicode.parcel', 35, '中文 日本語 café 😀 𠀋'),
    ('android15-url.parcel', 35, 'https://example.com/a.b?x=1&y=2'),
])
def test_actual_mumu_replies_preserve_text_and_skip_classifier_metadata(name, sdk, expected):
    # These captures contain only public verification strings. The URL reply
    # includes classification confidence data and a non-null trailing TextLinks.
    path = Path(__file__).with_name('fixtures') / 'adb_clipboard' / name
    assert decode_clipboard_parcel(path.read_text(), sdk) == expected


@pytest.mark.parametrize('sdk', [24, 31, 35])
@pytest.mark.parametrize('styled', [False, True])
def test_first_text_ignores_metadata_styles_and_remaining_items(sdk, styled):
    extras = integer(1) + string('label') + integer(0) + string('bundle text is not clipboard')
    confidence = integer(1) + string('url') + integer(7) + struct.pack('<f', 0.9)
    reply = clip_bytes(sdk, ['first', 'second'], label=None, extras=extras,
                       confidence=confidence, html='<b>HTML is not the returned text</b>',
                       styled=styled, item_flags=integer(1) + integer(0x12345678) * 8)
    assert decode_clipboard_parcel(dump(reply), sdk) == 'first'


def test_absent_clipboard_and_null_text_are_empty():
    assert decode_clipboard_parcel(dump(integer(0) * 2, inline=True), 35) == ''
    assert decode_clipboard_parcel(dump(integer(0) * 3, inline=True), 35) == ''
    assert decode_clipboard_parcel(dump(clip_bytes(35, [None])), 35) == ''


@pytest.mark.parametrize('code', [-1, -2, -3, -4, -5, -7])
def test_binder_errors_keep_exception_code_and_utf16_message(code):
    message = 'Remote failure 蓝色😀\nmessage'
    with pytest.raises(ClipboardBinderError) as caught:
        decode_clipboard_parcel(dump(integer(code) + string(message)), 35)
    assert caught.value.code == code
    assert caught.value.message == message
    assert message in str(caught.value)


@pytest.mark.parametrize('sdk', [24, 31, 35])
def test_truncation_before_first_text_finishes_is_rejected(sdk):
    complete = clip_bytes(sdk, ['clipboard text'])
    text_field = integer(1) + string('clipboard text', sdk >= 30)
    required_end = complete.index(text_field) + len(text_field)
    for end in range(0, required_end, 4):
        with pytest.raises(OSError):
            decode_clipboard_parcel(dump(complete[:end]), sdk)
    assert decode_clipboard_parcel(dump(complete[:required_end]), sdk) == 'clipboard text'


@pytest.mark.parametrize('reply', [
    '', 'Service clipboard does not exist', 'Result: Parcel(NULL)',
    "Result: Parcel(gggggggg '........')", "Result: Parcel(00000000 '........')",
    'Result: Parcel(00000000 00000002)',
    pytest.param(dump(clip_bytes(35, ['text'])).replace('0x00000010:', '0x00000020:', 1),
                 id='missing-or-reordered-row'),
    pytest.param(dump(clip_bytes(35, ['text'], icon=1)), id='unsupported-bitmap'),
])
def test_missing_malformed_and_unexpected_reply_data_are_rejected(reply):
    with pytest.raises(OSError):
        decode_clipboard_parcel(reply, 35)


@pytest.mark.parametrize('offset,value', [(12, integer(-2)), (19, b'x'), (16, b'\xff')],
                         ids=['negative-length', 'terminator', 'encoding'])
def test_invalid_string_length_terminator_and_encoding_are_rejected(offset, value):
    good = clip_bytes(35, ['text'], label='abc')
    bad = good[:offset] + value + good[offset + len(value):]
    with pytest.raises(OSError):
        decode_clipboard_parcel(dump(bad), 35)


def test_styled_label_is_rejected_because_its_spans_precede_required_metadata():
    reply = clip_bytes(35, ['text'], label='label')
    label_end = 12 + len(string('label', utf8=True))
    spans = integer(7) + integer(1) + integer(0) + integer(5) + integer(33) + integer(0)
    reply = reply[:8] + integer(0) + reply[12:label_end] + spans + reply[label_end:]
    with pytest.raises(OSError, match='labels are unsupported'):
        decode_clipboard_parcel(dump(reply), 35)


@pytest.mark.parametrize('header', [-127, -128])
def test_unsupported_reply_headers_do_not_look_like_remote_argument_errors(header):
    with pytest.raises(OSError) as caught:
        decode_clipboard_parcel(dump(integer(header)), 35)
    assert not isinstance(caught.value, ClipboardBinderError)
