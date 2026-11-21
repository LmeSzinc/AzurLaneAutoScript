import base64
import multiprocessing
from collections import deque
from contextlib import suppress
from functools import wraps
import ctypes
import os
import shlex
import subprocess
import tempfile
import threading
import time
import uuid

OUTPUT_LIMIT = 1024 * 1024


class ManagerError(Exception):
    pass


class TransportError(ManagerError):
    pass


def bounded_int(value, minimum, maximum):
    try:
        number = int(value)
        if float(value) != number or not minimum <= number <= maximum:
            raise ValueError()
    except (ValueError, TypeError, OverflowError):
        raise ManagerError('InvalidValue')
    return number


def read_settings(config):
    settings = config['GameManager']['GameManager']
    return dict(RefreshRate=settings['RefreshRate'], InstantSend=settings['InstantSend'])


def split_command(command):
    if os.name == 'nt':
        # Prefix a dummy executable: CommandLineToArgvW treats argv[0] specially.
        parse = ctypes.windll.shell32.CommandLineToArgvW
        parse.restype = ctypes.POINTER(ctypes.c_wchar_p)
        count = ctypes.c_int()
        pointer = parse(ctypes.c_wchar_p('adb-placeholder ' + command), ctypes.byref(count))
        if not pointer:
            raise ManagerError('InvalidCommand')
        try:
            args = list(pointer[:count.value])[1:]
        finally:
            ctypes.windll.kernel32.LocalFree(ctypes.cast(pointer, ctypes.c_void_p))
    else:
        try:
            args = shlex.split(command)
        except ValueError:
            raise ManagerError('InvalidCommand')
    if args and args[0].lower() in ('adb', 'adb.exe'):
        args.pop(0)
    if not args:
        raise ManagerError('InvalidCommand')
    return args


def needs_serial(args):
    """

    Args:
        args:

    Returns:

    """
    explicit = False
    index = 0
    while index < len(args) and args[index].startswith('-'):
        option = args[index]
        if option in ('-s', '-t', '-d', '-e'):
            explicit = True
        if option in ('-s', '-t', '-H', '-P', '-L'):
            if index + 1 >= len(args):
                raise ManagerError('InvalidCommand')
            index += 2
        elif option in ('-d', '-e', '-a'):
            index += 1
        elif option in ('--help', '--version'):
            return False
        else:
            raise ManagerError('InvalidCommand')
    if index == len(args):
        raise ManagerError('InvalidCommand')
    return not explicit and args[index] not in {
        'devices', 'connect', 'disconnect', 'pair', 'start-server', 'kill-server',
        'server-status', 'version', 'help', 'host-features', 'mdns', 'keygen',
    }


def dispatch_gesture(device, data, width, height):
    kind, start, end, duration = data['kind'], data['start'], data['end'], data['duration']
    if any(not (0 <= x < width and 0 <= y < height) for x, y in (start, end)):
        raise ManagerError('InvalidValue')
    method = device.config.Emulator_ControlMethod
    suffix = {'ADB': 'adb', 'MaaTouch': 'maatouch', 'Hermit': 'hermit'}.get(method, method)
    if kind == 'hold' and method == 'ADB':
        kind, end = 'swipe', start
    operation = {'tap': 'click_', 'hold': 'long_click_', 'swipe': 'swipe_'}[kind]
    args = {'tap': start, 'hold': (*start, duration),
            'swipe': (start, end, duration) if method in ('ADB', 'uiautomator2') else (start, end)}[kind]
    func = getattr(device, operation + suffix, None)
    if func is None:
        raise ManagerError('UnsupportedGesture')
    func(*args)


def run_adb(binary, args, timeout, stopped, running):
    """Add cancellable, bounded stdout/stderr to the existing device connection."""
    if stopped.is_set():
        raise ManagerError('Closed')
    if running():
        raise ManagerError('Running')
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        with subprocess.Popen([binary] + args, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                              creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)) as process:
            deadline = time.perf_counter() + timeout
            timed_out = False
            try:
                while process.poll() is None:
                    if stopped.wait(0.05) or time.perf_counter() >= deadline:
                        timed_out = not stopped.is_set()
                        break
            finally:
                if process.poll() is None:
                    process.kill()
                process.wait()
            stdout.seek(0)
            stderr.seek(0)
            out, err = stdout.read(OUTPUT_LIMIT + 1), stderr.read(OUTPUT_LIMIT + 1)
        if stopped.is_set():
            raise ManagerError('Closed')
        return dict(stdout=out[:OUTPUT_LIMIT].decode('utf-8', errors='replace'),
                    stderr=err[:max(0, OUTPUT_LIMIT - len(out))].decode('utf-8', errors='replace'),
                    code=process.returncode, timeout=timed_out, truncated=len(out) + len(err) > OUTPUT_LIMIT)


def capture_device(device, quality):
    """

    Args:
        device:
        quality: image quality (1-100)

    Returns:

    """
    import cv2
    started = time.perf_counter()
    method = device.config.Emulator_ScreenshotMethod
    device.image = device.screenshot_methods[method]()
    device.image = device._handle_orientated_image(device.image)
    if device.config.Emulator_ScreenshotDedithering:
        cv2.fastNlMeansDenoising(device.image, device.image, h=17, templateWindowSize=1, searchWindowSize=2)
    height, width = device.image.shape[:2]
    ok, encoded = cv2.imencode('.jpg', cv2.cvtColor(device.image, cv2.COLOR_RGB2BGR),
                               [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise ManagerError('InvalidImage')
    return dict(image='data:image/jpeg;base64,' + base64.b64encode(encoded).decode('ascii'),
                width=width, height=height, serial=device.serial, time=time.strftime('%H:%M:%S'),
                capture_ms=round((time.perf_counter() - started) * 1000, 1),
                screenshot_method=method, control_method=device.config.Emulator_ControlMethod)


def device_service(pipe, config_name, allowed):
    device = None
    selection = None
    frames = deque(maxlen=8)
    try:
        from module.webui.fake_pil_module import remove_fake_pil_module
        remove_fake_pil_module()
        from module.config.config import AzurLaneConfig
        from module.device.connection import Connection
        from module.device.device import Device
        from module.device.method.scrcpy.options import ScrcpyOptions

        class ViewerConfig(AzurLaneConfig):
            __setattr__ = object.__setattr__

            def save(self, *args, **kwargs):
                return False

        class ViewerDevice(Device):
            __init__ = Connection.__init__

        while True:
            request = pipe.recv()
            if request['action'] == 'close':
                break
            try:
                if request['action'] == 'adb' and not request['target']:
                    pipe.send(dict(binary=Connection.__new__(Connection).adb_binary))
                    continue
                current = request['selection']
                if current != selection:
                    if device is not None:
                        device.release_during_wait()
                    config = ViewerConfig(config_name)
                    config.auto_update = False
                    config.__dict__.update({'Emulator_' + name: value for name, value in current.items()})
                    device = ViewerDevice(config)
                    device.get_orientation()
                    selection = current
                    frames.clear()
                if request['action'] == 'adb':
                    if device.is_over_http:
                        raise ManagerError('AdbRequired')
                    pipe.send(dict(binary=device.adb_binary, serial=device.serial))
                    continue
                fps = request['rate'] or 15
                if ScrcpyOptions.frame_rate != fps:
                    if device._scrcpy_alive:
                        device._scrcpy_server_stop()
                    ScrcpyOptions.frame_rate = fps
                if request['action'] == 'gesture':
                    if not allowed.is_set():
                        raise ManagerError('Running')
                    frame = request['data']['frame']
                    if frame not in frames:
                        raise ManagerError('StaleFrame')
                    height, width = device.image.shape[:2]
                    dispatch_gesture(device, request['data'], width, height)
                    response = {}
                else:
                    if device.config.Emulator_ScreenshotMethod == 'auto':
                        device.run_simple_screenshot_benchmark()
                    response = capture_device(device, quality=request['quality'])
                    size = (response['height'], response['width'])
                    if frames and size != image_size:
                        frames.clear()
                    image_size = size
                    frames.append(request['frame'])
                    response['frame'] = request['frame']
                pipe.send(response)
            except ManagerError as exc:
                pipe.send(dict(error=str(exc), translated=True))
    except (EOFError, BrokenPipeError):
        pass
    except Exception as exc:
        with suppress(EOFError, BrokenPipeError):
            pipe.send(dict(error=str(exc), translated=isinstance(exc, ManagerError)))
    finally:
        if device is not None:
            with suppress(Exception):
                device.release_during_wait()
        pipe.close()


class ConfiguredTransport:
    def __init__(self, config_name, get_config, stopped, running):
        self.stopped, self.running = stopped, running
        self.frame_id = 0
        self.config_name, self.get_config = config_name, get_config
        self.selection = None
        self.checked_at = self.rate = 0
        self.context = multiprocessing.get_context('spawn')
        self.process = self.pipe = None
        self.allowed = self.context.Event()

    def exchange(self, action, **data):
        if action != 'screenshot' or time.perf_counter() >= self.checked_at:
            self.selection = dict(self.get_config()['Alas']['Emulator'])
            self.checked_at = time.perf_counter() + 1
        self.frame_id += 1
        if self.stopped.is_set():
            raise ManagerError('Closed')
        if action != 'screenshot' and self.running():
            raise ManagerError('Running')
        if self.process is None:
            self.pipe, child = self.context.Pipe()
            self.process = self.context.Process(target=device_service,
                                                args=(child, self.config_name, self.allowed), daemon=True)
            self.process.start()
            child.close()
        (self.allowed.clear if self.running() or self.stopped.is_set() else self.allowed.set)()
        self.pipe.send(dict(action=action, selection=self.selection, rate=self.rate, frame=self.frame_id, **data))
        deadline = time.perf_counter() + 60
        while not self.stopped.is_set():
            if self.running() or self.stopped.is_set():
                self.allowed.clear()
            else:
                self.allowed.set()
            if self.pipe.poll(0.005):
                response = self.pipe.recv()
                if 'error' in response:
                    error = ManagerError if response['translated'] else RuntimeError
                    raise error(response['error'])
                return response
            if not self.process.is_alive():
                raise TransportError('DeviceUnavailable')
            if time.perf_counter() >= deadline:
                raise TransportError('TimedOut')
        raise ManagerError('Closed')

    def command(self, command, timeout):
        args = split_command(command)
        target = self.exchange('adb', target=needs_serial(args))
        if 'serial' in target:
            args = ['-s', target['serial']] + args
        return run_adb(target['binary'], args, timeout, self.stopped, self.running)

    def close(self):
        self.allowed.clear()
        if self.process is not None:
            if self.process.is_alive():
                with suppress(OSError):
                    self.pipe.send(dict(action='close'))
                self.process.join(0.2)
                if self.process.is_alive():
                    self.process.terminate()
                    self.process.join(1)
            self.pipe.close()
            self.process = self.pipe = None


class ManagerWorker:
    def __init__(self, transport, emit, settings):
        self.transport, self.emit = transport, emit
        self.settings = dict(settings)
        self.stopped = transport.stopped
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.request = self.awaiting_frame = self.pending_frame = None
        self.busy = self.capturing = False
        self.holding, self.visible = False, True
        self.frame_sent_at = self.next_refresh = self.refresh_until = 0
        self.thread = threading.Thread(target=self.loop, daemon=True, name='game-manager')

    def submit(self, data):
        with self.lock:
            if self.stopped.is_set():
                return
            if data['action'] != 'screenshot' and self.transport.running():
                raise ManagerError('Running')
            if self.request is not None or (self.busy and not self.capturing):
                raise ManagerError('Busy')
            self.request = dict(data)
            self.wake.set()

    def acknowledge(self, frame):
        with self.lock:
            if frame == self.awaiting_frame:
                self.awaiting_frame = None
                self.wake.set()

    def publish(self, image):
        with self.lock:
            if self.awaiting_frame is not None:
                self.pending_frame = image
                return
            self.awaiting_frame, self.frame_sent_at = image['frame'], time.perf_counter()
        self.emit(image)

    def configure(self, data):
        rate = data['rate']
        with self.lock:
            if rate != self.settings['RefreshRate']:
                self.next_refresh = time.perf_counter()
                self.refresh_until = 0
                self.pending_frame = None
            self.settings['RefreshRate'] = self.transport.rate = rate
            self.holding = data['holding']
            self.visible = data['visible']
        self.wake.set()

    def refresh_interval(self, now):
        rate = self.settings['RefreshRate']
        return 1 / rate if rate else 0.5 if 0 < now <= self.refresh_until else 0

    def close(self):
        self.stopped.set()
        with self.lock:
            self.request = self.pending_frame = None
        self.wake.set()

    def loop(self):
        previous_running = None
        try:
            while not self.stopped.is_set():
                now = time.perf_counter()
                ready = self.visible and not self.holding
                delay = max(0, self.next_refresh - now) if ready and self.refresh_interval(
                    now) and self.pending_frame is None else 0.1
                flush = ready and self.pending_frame is not None and self.awaiting_frame is None
                self.wake.wait(0 if self.request or flush else min(delay, 0.1))
                self.wake.clear()
                started = time.perf_counter()
                manual = False
                notification = None
                try:
                    running = self.transport.running()
                    if running != previous_running:
                        self.emit(dict(running=running))
                        previous_running = running
                    with self.lock:
                        request, self.request = self.request, None
                        manual = request is not None
                        interval = self.refresh_interval(started) if self.visible and not self.holding else 0
                        if self.awaiting_frame is not None and started - self.frame_sent_at > 5:
                            self.settings['RefreshRate'] = self.refresh_until = 0
                            self.awaiting_frame = self.pending_frame = None
                            raise TransportError('FrameTimeout')
                        image = None
                        if manual:
                            self.pending_frame = None
                        elif self.pending_frame is not None and self.awaiting_frame is None and self.visible and not self.holding:
                            image, self.pending_frame = self.pending_frame, None
                        if request is None and image is None and interval and self.pending_frame is None and started >= self.next_refresh:
                            request = dict(action='screenshot')
                        self.busy = request is not None
                        self.capturing = self.busy and request['action'] == 'screenshot'
                    if image is not None:
                        self.publish(image)
                        continue
                    if request is None:
                        continue
                    kind = request['action']
                    if kind == 'command':
                        result = self.transport.command(request['command'], request['timeout'])
                        self.emit(dict(result=result))
                    else:
                        if kind == 'gesture':
                            self.transport.exchange('gesture', data=request)
                            started = time.perf_counter()
                            self.refresh_until = started + 2
                            self.emit(dict(sent=True))
                        image = self.transport.exchange('screenshot',
                                                        quality=90 if manual and kind == 'screenshot' else 20)
                        self.publish(image)
                except Exception as exc:
                    if not isinstance(exc, ManagerError) or isinstance(exc, TransportError):
                        self.transport.close()
                    notification = dict(error=str(exc), translated=isinstance(exc, ManagerError),
                                        rate=self.settings['RefreshRate'], busy=False)
                    started = time.perf_counter() + 1
                finally:
                    if self.busy:
                        with self.lock:
                            self.busy = self.capturing = False
                            finished = time.perf_counter()
                            self.next_refresh = max(finished, started + self.refresh_interval(finished))
                        if manual and notification is None:
                            notification = dict(busy=False)
                    if notification is not None and not self.stopped.is_set():
                        self.emit(notification)
        finally:
            self.close()
            self.transport.close()


def panel_action(func):
    @wraps(func)
    def call(self, *args, **kwargs):
        if self.active():
            with self.ui_lock:
                try:
                    return func(self, *args, **kwargs)
                except ManagerError as exc:
                    self.cancel_gesture()
                    self.output('error', self.text(str(exc)), 'error')

    return call


class PanelStopEvent(threading.Event):
    def __init__(self, current):
        super().__init__()
        self.current = current

    def is_set(self):
        if not self.current():
            self.set()
        return super().is_set()

    def wait(self, timeout=None):
        return self.is_set() or super().wait(timeout) or self.is_set()


class GameManagerPanel:
    def __init__(self, gui, config):
        self.gui = gui
        self.config_name = gui.alas_name
        self.element_id = 'game-manager-' + uuid.uuid4().hex
        self.worker = None
        self.stopped = PanelStopEvent(lambda: gui.alive and gui.page == 'GameManager'
                                              and gui.alas_name == self.config_name and gui.game_manager is self)
        self.ui_lock = threading.RLock()
        self.settings = read_settings(config)
        self.busy = self.holding = False
        self.running = gui.alas.alive
        self.visible = True
        self.pending = None
        self.has_frame = False

    def scope(self, name):
        return self.element_id + '-' + name

    def close(self):
        self.stopped.set()
        if self.worker:
            self.worker.close()

    def active(self):
        return not self.stopped.is_set()

    @staticmethod
    def text(key, **values):
        from module.webui.lang import t
        return t('Gui.GameManager.' + key, **values)

    def screen(self, method, data=None):
        from pywebio.session import run_js
        if self.active():
            run_js('const r=document.getElementById("pywebio-scope-"+id);'
                   'if(r && r.gameScreen) r.gameScreen[method](data);',
                   id=self.element_id, method=method, data=data)

    def output(self, name, value='', kind='text'):
        from pywebio.output import put_text, put_error, use_scope
        with use_scope(self.scope(name), clear=True):
            (put_error if kind == 'error' else put_text)(value).style(
                'white-space:pre-wrap;font-family:monospace' if kind == 'code' else 'font-size:.85rem' if name == 'status' else '')

    def sync(self):
        self.worker.configure(dict(rate=self.settings['RefreshRate'],
                                   holding=self.holding or self.busy, visible=self.visible))
        from pywebio.output import put_button, use_scope
        available = not self.running and not self.busy
        self.screen('enable', available)
        controls = [
            ('capture', 'Capture', lambda: self.submit('screenshot'), self.busy or self.holding),
            ('fullscreen', 'Fullscreen', lambda: self.screen('fullscreen'), not self.has_frame),
            ('send', 'Send', lambda: self.submit('gesture'), not available or self.pending is None),
            ('cancel', 'Cancel', self.cancel_gesture, self.pending is None or self.busy),
            ('execute', 'Execute', lambda: self.submit('command'), not available),
        ]
        for name, label, callback, disabled in controls:
            with use_scope(self.scope(name), clear=True):
                put_button(self.text(label), onclick=callback, color='on', disabled=disabled)

    @panel_action
    def setting_changed(self, name, value):
        self.settings[name] = bool(value) if name == 'InstantSend' else value
        self.sync()

    @panel_action
    def submit(self, action):
        from pywebio.output import clear
        from pywebio.pin import pin
        if action == 'gesture' and self.pending is None:
            raise ManagerError('InvalidValue')
        request = self.pending if action == 'gesture' else dict(action=action)
        if action == 'command':
            request.update(command=pin[self.element_id + '_Command'],
                           timeout=bounded_int(pin[self.element_id + '_Timeout'], 1, 600))
        clear(self.scope('error'))
        self.worker.submit(request)
        self.busy = True
        self.sync()

    @panel_action
    def cancel_gesture(self):
        from pywebio.output import clear
        self.pending, self.holding = None, False
        clear(self.scope('gesture'))
        self.screen('reset')
        self.sync()

    def screen_event(self, data):
        if data['action'] == 'close':
            self.close()
        else:
            self._screen_event(data)

    @panel_action
    def _screen_event(self, data):
        action = data['action']
        if action == 'frame_ack':
            self.worker.acknowledge(data['frame'])
        elif action in ('holding', 'visible'):
            setattr(self, action, data['value'])
            self.sync()
        elif action == 'stats' and self.has_frame:
            self.output('status', self.text('Status', **data))
        elif action == 'preview':
            if self.gui.alas.alive:
                raise ManagerError('Running')
            if not self.has_frame:
                raise ManagerError('InvalidImage')
            self.pending = dict(action='gesture', kind=data['kind'], start=tuple(data['start']),
                                end=tuple(data['end']), duration=data['duration'] / 1000, frame=data['frame'])
            label = self.text({'tap': 'Tap', 'hold': 'Hold', 'swipe': 'Swipe'}[data['kind']])
            self.output('gesture', '{}: {} → {} · {} ms'.format(
                label, data['start'], data['end'], data['duration']))
            if self.settings['InstantSend']:
                self.submit('gesture')
            else:
                self.sync()
        elif action == 'cancel':
            self.cancel_gesture()
        elif action == 'image_error':
            raise ManagerError('InvalidImage')

    @panel_action
    def emit(self, data):
        from html import escape
        from pywebio.output import put_html, use_scope
        if 'rate' in data:
            from pywebio.pin import pin_update
            self.settings['RefreshRate'] = data['rate']
            pin_update('GameManager_GameManager_RefreshRate', value=data['rate'])
        for name in ('running', 'busy'):
            if name in data:
                setattr(self, name, data[name])
        first = 'image' in data and not self.has_frame
        if 'image' in data:
            if first:
                with use_scope(self.scope('image'), clear=True):
                    put_html(
                        '<img title="{}" style="display:block;width:100%;max-height:100vh;object-fit:contain">'.format(
                            escape(self.text('Capture'))))
            self.has_frame = True
        if data.get('running') or 'error' in data or data.get('sent'):
            self.cancel_gesture()
        elif 'running' in data or 'busy' in data or first:
            self.sync()
        if 'error' in data:
            self.output('error', self.text(data['error']) if data.get('translated') else data['error'], 'error')
        if 'image' in data:
            self.screen('frame', data)
        if 'result' in data:
            result = data['result']
            status = ' · '.join([self.text('ExitCode') + ': ' + str(result['code'])] +
                                [self.text(key) for flag, key in [('timeout', 'TimedOut'), ('truncated', 'Truncated')]
                                 if result[flag]])
            self.output('result', '{}\nstdout:\n{}\nstderr:\n{}'.format(
                status, result['stdout'], result['stderr']), 'code')

    def show(self):
        from pywebio.io_ctrl import output_register_callback
        from pywebio.output import put_row, put_scope, put_scrollable, put_html, use_scope
        from pywebio.pin import pin_on_change
        from pywebio.session import defer_call, register_thread, run_js
        from module.webui.pin import put_textarea
        from module.webui.widgets import put_output

        manager = self.gui.alas
        transport = ConfiguredTransport(self.config_name, lambda: self.gui.alas_config.read_file(self.config_name),
                                        self.stopped, lambda: manager.alive)
        self.worker = ManagerWorker(transport, self.emit, self.settings)
        defer_call(self.close)

        def row(names, size):
            return put_row([put_scope(self.scope(name)) if name else None for name in names], size=size)

        put_scope(self.element_id, scope='groups')
        with use_scope(self.element_id):
            row(['capture', None, 'fullscreen'], 'auto 1fr auto')
            put_scope(self.scope('screen'), [put_scope(self.scope('image')),
                                             put_html(
                                                 f'<svg style="position:absolute;pointer-events:none;display:none" aria-hidden="true">'
                                                 f'<defs><marker id="{self.element_id}-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
                                                 '<path d="M0,0 L8,4 L0,8" fill="#ffd45e"/></marker></defs>'
                                                 f'<line stroke="#ffd45e" stroke-width="3" marker-end="url(#{self.element_id}-arrow)"/>'
                                                 '<circle r="9" fill="#ffd45e"/><circle r="12" fill="none" stroke="#ffd45e" stroke-width="3"/></svg>')]).style(
                'position:relative')
            row(['status', 'send', 'cancel'], 'minmax(0,1fr) auto auto')
            put_scope(self.scope('gesture'))
            put_scope(self.scope('error'))
            put_textarea(self.element_id + '_Command', label=self.text('Command'), rows=2,
                         placeholder='adb devices', help_text=self.text('CommandHelp'))
            put_row([
                put_output(dict(widget_type='input', name=self.element_id + '_Timeout', type='number',
                                title=self.text('Timeout'), value=60, min=1, max=600)),
                put_scope(self.scope('execute')),
            ], size='1fr auto')
            put_scrollable(put_scope(self.scope('result')), height=(0, 240), border=False)

        for name in self.settings:
            pin_on_change('GameManager_GameManager_' + name,
                          onchange=lambda value, name=name: self.setting_changed(name, value))
        run_js(SCREEN_BRIDGE, id=self.element_id,
               callback=output_register_callback(self.screen_event, serial_mode=True))
        self.sync()
        register_thread(self.worker.thread)
        self.worker.thread.start()


SCREEN_BRIDGE = r'''
(() => {
  const root=document.getElementById('pywebio-scope-'+id);
  const screen=document.getElementById('pywebio-scope-'+id+'-screen');
  if(!root || !screen) return;
  const overlay=screen.querySelector('svg'), line=overlay.querySelector('line'), dots=overlay.querySelectorAll('circle');
  let enabled=false,holding=false,disposed=false,frame=null,pointer=null,deferred=null,path=null;
  let clock=performance.now(),count=0,bytes=0;
  const send=data=>{if(!disposed) WebIO.pushData(data,callback);};
  const ack=data=>send({action:'frame_ack',frame:data.frame});
  const point=(event,clamp)=>{
    const box=screen.querySelector('img').getBoundingClientRect();
    const scale=Math.min(box.width/frame.width,box.height/frame.height);
    const x=(event.clientX-box.left-(box.width-frame.width*scale)/2)/scale;
    const y=(event.clientY-box.top-(box.height-frame.height*scale)/2)/scale;
    if(!clamp && (x<0 || y<0 || x>=frame.width || y>=frame.height)) return null;
    return [Math.max(0,Math.min(frame.width-1,Math.floor(x))),Math.max(0,Math.min(frame.height-1,Math.floor(y)))];
  };
  const draw=()=>{
    overlay.style.display=path?'block':'none';
    if(!path) return;
    const box=screen.querySelector('img').getBoundingClientRect(), parent=screen.getBoundingClientRect();
    Object.assign(overlay.style,{left:(box.left-parent.left)+'px',top:(box.top-parent.top)+'px',width:box.width+'px',height:box.height+'px'});
    overlay.setAttribute('viewBox',`0 0 ${frame.width} ${frame.height}`);
    const [a,b]=path;
    Object.entries({x1:a[0],y1:a[1],x2:b[0],y2:b[1]}).forEach(([k,v])=>line.setAttribute(k,v));
    dots.forEach((dot,i)=>{dot.setAttribute('cx',path[i][0]);dot.setAttribute('cy',path[i][1]);});
  };
  const timer=setInterval(()=>{
    const now=performance.now(),elapsed=now-clock;
    if(frame && elapsed>0) {
      const {image,...details}=frame;
      send({...details,action:'stats',fps:count*1000/elapsed,mbps:bytes*8/(elapsed*1000)});
    }
    clock=now;count=bytes=0;
  },1000);
  const resize=new ResizeObserver(draw);resize.observe(screen);
  const present=data=>{
    const image=new Image();
    image.onload=()=>{
      if(disposed) return;
      if(frame && data.frame<=frame.frame) {ack(data);return;}
      if(holding) {deferred=data;ack(data);return;}
      frame=data;
      const target=screen.querySelector('img');
      target.src=data.image;
      target.draggable=false;
      target.style.touchAction=enabled?'none':'';
      draw();
      if(document.hidden) ack(data);else requestAnimationFrame(()=>{count++;ack(data);});
    };
    image.onerror=()=>{ack(data);send({action:'image_error'});};
    image.src=data.image;
  };
  const reset=()=>{
    pointer=path=null;holding=false;draw();
    if(deferred) {const data=deferred;deferred=null;present(data);}
  };
  const cancel=()=>{reset();send({action:'cancel'});};
  screen.addEventListener('pointerdown',event=>{
    if(!enabled || holding || !frame || event.target.tagName!=='IMG' || event.button!==0 || !event.isPrimary) return;
    const start=point(event,false);if(!start) return;
    event.preventDefault();event.target.setPointerCapture(event.pointerId);
    pointer={start,id:event.pointerId,time:performance.now(),x:event.clientX,y:event.clientY};
    path=[start,start];draw();holding=true;send({action:'holding',value:true});
  });
  screen.addEventListener('pointermove',event=>{
    if(pointer && event.pointerId===pointer.id) {path[1]=point(event,true);draw();}
  });
  screen.addEventListener('pointerup',event=>{
    if(!pointer || event.pointerId!==pointer.id) return;
    if(!enabled) {cancel();return;}
    const duration=Math.max(1,Math.min(10000,Math.round(performance.now()-pointer.time)));
    const kind=Math.hypot(event.clientX-pointer.x,event.clientY-pointer.y)>=6?'swipe':duration>=500?'hold':'tap';
    path=[pointer.start,kind==='swipe'?point(event,true):pointer.start];draw();
    send({action:'preview',kind,start:path[0],end:path[1],duration,frame:frame.frame});
    pointer=null;
  });
  screen.addEventListener('pointercancel',cancel);
  screen.addEventListener('lostpointercapture',()=>{if(pointer) cancel();});
  const visible=()=>send({action:'visible',value:!document.hidden});
  document.addEventListener('visibilitychange',visible);
  const observer=new MutationObserver(()=>{
    if(root.isConnected || disposed) return;
    send({action:'close'});disposed=true;deferred=null;pointer=null;
    document.removeEventListener('visibilitychange',visible);
    observer.disconnect();resize.disconnect();clearInterval(timer);
  });
  observer.observe(document.body,{childList:true,subtree:true});
  root.gameScreen={
    frame:data=>{bytes+=data.image.length;present(data);}, reset,
    enable:value=>{
      enabled=value;
      const image=screen.querySelector('img');if(image) image.style.touchAction=enabled?'none':'';
    },
    fullscreen:()=>{
      const image=screen.querySelector('img');
      if(image) (document.fullscreenElement?document.exitFullscreen():screen.requestFullscreen()).catch(()=>send({action:'image_error'}));
    }
  };
  visible();
})();
'''
