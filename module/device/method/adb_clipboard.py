"""Read the text fields in AOSP ClipData replies from ``service call``."""

import re
import struct


class ClipboardBinderError(OSError):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(f'Android clipboard error {code}: {message}')


class _Parcel:
    def __init__(self, data):
        self.data, self.offset = data, 0

    def read(self, size):
        if size < 0 or size > len(self.data) - self.offset:
            raise OSError('Truncated Android clipboard parcel')
        result = self.data[self.offset:self.offset + size]
        self.offset += size
        return result

    def integer(self):
        return struct.unpack('<i', self.read(4))[0]

    def string(self, utf8=False):
        length = self.integer()
        if length == -1:
            return None
        if length < 0:
            raise OSError('Invalid Android clipboard string length')
        width = 1 if utf8 else 2
        raw = self.read((length + 1) * width)
        if raw[-width:] != b'\0' * width:
            raise OSError('Unterminated Android clipboard string')
        self.read(-self.offset % 4)
        try:
            if utf8:
                # Accept UTF-8 and JNI modified UTF-8: C0 80 for NUL and
                # optional CESU-8 surrogate pairs for supplementary characters.
                text = raw[:-1].replace(b'\xc0\x80', b'\0').decode('utf-8', 'surrogatepass')
                raw = text.encode('utf-16-le', 'surrogatepass')
            else:
                raw = raw[:-2]
            return raw.decode('utf-16-le', 'surrogatepass')
        except UnicodeDecodeError as exc:
            raise OSError('Invalid Android clipboard text encoding') from exc

    def text(self, utf8=False, allow_spans=False):
        kind = self.integer()
        if kind not in (0, 1):
            raise OSError('Unknown Android clipboard CharSequence encoding')
        text = self.string(utf8)
        if kind == 0 and text is not None and not allow_spans and self.integer() != 0:
            raise OSError('Styled Android clipboard labels are unsupported')
        return text

    def bundle(self):
        length = self.integer()
        if length in (-1, 0):
            return
        if length < 0 or length % 4 or self.integer() not in (0x4C444E42, 0x4C444E44):
            raise OSError('Invalid Android clipboard Bundle')
        self.read(length)


def decode_clipboard_parcel(output, sdk_ver):
    """Return the first item's text without interpreting later representations.

    TextUtils uses String16 through Android 10 and JNI String8 from Android 11.
    MIME strings remain String16. Metadata Bundles carry their own byte lengths.
    """
    match = re.fullmatch(r'\s*Result:\s*Parcel\((.*)\)\s*', output, re.DOTALL)
    if match is None:
        raise OSError('Cannot find Android clipboard parcel')
    data = bytearray()
    for line in match.group(1).splitlines():
        # The quoted printable column loses Unicode and is never clipboard data.
        line = line.partition("'")[0].strip()
        if not line:
            continue
        address = re.match(r'0x([0-9a-fA-F]+):\s*', line)
        if address:
            if int(address.group(1), 16) != len(data):
                raise OSError('Missing or unordered Android clipboard parcel rows')
            line = line[address.end():]
        words = line.split()
        if not words or any(re.fullmatch(r'[0-9a-fA-F]{8}', word) is None for word in words):
            raise OSError('Invalid Android clipboard parcel hex dump')
        data.extend(b''.join(struct.pack('<I', int(word, 16)) for word in words))

    parcel = _Parcel(data)
    exception = parcel.integer()
    if exception in (-127, -128):
        raise OSError('Unsupported Android clipboard Binder reply header')
    if exception:
        raise ClipboardBinderError(exception, parcel.string())
    present = parcel.integer()
    if present not in (0, 1):
        raise OSError('Invalid Android clipboard presence marker')
    if present == 0:
        return ''

    utf8 = sdk_ver >= 30
    parcel.text(utf8)  # ClipDescription label
    count = parcel.integer()
    if count <= 0 or count > (len(data) - parcel.offset) // 4:
        raise OSError('Invalid Android clipboard MIME count')
    for _ in range(count):
        if parcel.string() is None:
            raise OSError('Invalid Android clipboard MIME type')
    parcel.bundle()  # ClipDescription extras
    if sdk_ver >= 26:
        parcel.read(8)  # ClipDescription timestamp
    if sdk_ver >= 31:
        parcel.read(8)  # Styled-text flag and classification status
        parcel.bundle()  # Classification confidence scores

    if parcel.integer() != 0:
        raise OSError('Android clipboard bitmap icons are unsupported')
    if parcel.integer() <= 0:
        raise OSError('Invalid Android clipboard item count')
    # Matching getItemAt(0).getText() needs no later fields, including spans,
    # HTML, classification TextLinks, URI/Intent objects, or subsequent items.
    return parcel.text(utf8, allow_spans=True) or ''
