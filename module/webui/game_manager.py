import base64
import ctypes
import multiprocessing
import os
import shlex
import subprocess
import tempfile
import threading
import time
import uuid
from collections import deque
from contextlib import suppress
from functools import wraps
from html import escape

OUTPUT_LIMIT = 1024 * 1024
HOST_ADB_COMMANDS = frozenset({
    'devices', 'connect', 'disconnect', 'pair', 'start-server', 'kill-server',
    'server-status', 'version', 'help', 'host-features', 'mdns', 'keygen',
})
_UI_LOADED = False


def _ensure_ui():
    global _UI_LOADED, pw_io, pw_out, pw_pin, pw_session, web_lang, web_pin, web_utils, web_widgets
    if _UI_LOADED:
        return
    from pywebio import io_ctrl as pw_io, output as pw_out, pin as pw_pin, session as pw_session
    from module.webui import lang as web_lang, pin as web_pin, utils as web_utils, widgets as web_widgets
    _UI_LOADED = True


class ManagerError(Exception):
    pass


class TransportError(ManagerError):
    pass


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
    explicit = False
    it = iter(args)
    for token in it:
        if not token.startswith('-'):
            return not explicit and token not in HOST_ADB_COMMANDS
        if token in ('-s', '-t', '-d', '-e'):
            explicit = True
        if token in ('-s', '-t', '-H', '-P', '-L'):
            if next(it, None) is None:
                raise ManagerError('InvalidCommand')
        elif token in ('--help', '--version'):
            return False
        elif token not in ('-d', '-e', '-a'):
            raise ManagerError('InvalidCommand')
    raise ManagerError('InvalidCommand')


def dispatch_gesture(device, data):
    kind, start, end, duration = data['kind'], data['start'], data['end'], data['duration']
    method = device.config.Emulator_ControlMethod
    if kind == 'hold' and method == 'ADB':
        kind, end = 'swipe', start
    op = {'tap': 'click_', 'hold': 'long_click_', 'swipe': 'swipe_'}[kind]
    args = {'tap': start, 'hold': (*start, duration),
            'swipe': (start, end, duration) if method in ('ADB', 'uiautomator2') else (start, end)}[kind]
    func = getattr(device, op + method.lower(), None)
    if func is None:
        raise ManagerError('UnsupportedGesture')
    func(*args)


def run_adb(binary, args, timeout, stopped, running):
    """Add cancellable, bounded stdout/stderr to the existing device connection."""
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
        if stopped.is_set():
            return None
        stdout.seek(0)
        stderr.seek(0)
        out, err = stdout.read(OUTPUT_LIMIT + 1), stderr.read(OUTPUT_LIMIT + 1)
        return dict(stdout=out[:OUTPUT_LIMIT].decode('utf-8', errors='replace'),
                    stderr=err[:max(0, OUTPUT_LIMIT - len(out))].decode('utf-8', errors='replace'),
                    code=process.returncode, timeout=timed_out, truncated=len(out) + len(err) > OUTPUT_LIMIT)


def capture_device(device, quality):
    import cv2
    started = time.perf_counter()
    method = device.config.Emulator_ScreenshotMethod
    device.image = device.screenshot_methods[method]()
    if device.config.Emulator_ScreenshotDedithering:
        cv2.fastNlMeansDenoising(device.image, device.image, h=17, templateWindowSize=1, searchWindowSize=2)
    device.image = device._handle_orientated_image(device.image)
    height, width = device.image.shape[:2]
    ok, encoded = cv2.imencode('.jpg', cv2.cvtColor(device.image, cv2.COLOR_RGB2BGR),
                               [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise ManagerError('InvalidImage')
    return dict(image='data:image/jpeg;base64,' + base64.b64encode(encoded).decode('ascii'),
                width=width, height=height, serial=device.serial, time=time.strftime('%H:%M:%S'),
                capture_ms=round((time.perf_counter() - started) * 1000, 1),
                screenshot_method=method, control_method=device.config.Emulator_ControlMethod)


def device_service(pipe, config_name):
    device = None
    selection = None
    last_size = None
    frames = deque(maxlen=8)
    try:
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

        def ensure_device(current):
            nonlocal device, selection
            if current != selection:
                if device is not None:
                    device.release_during_wait()
                config = ViewerConfig(config_name)
                config.auto_update = False
                config.__dict__.update({'Emulator_' + k: v for k, v in current.items()})
                device = ViewerDevice(config)
                device.get_orientation()
                selection = current
                frames.clear()
            return device

        while True:
            request = pipe.recv()
            action = request['action']
            if action == 'close':
                break
            try:
                if action == 'adb' and not request['target']:
                    pipe.send(dict(binary=Connection.__new__(Connection).adb_binary))
                    continue
                dev = ensure_device(request['selection'])
                if action == 'adb':
                    if dev.is_over_http:
                        raise ManagerError('AdbRequired')
                    pipe.send(dict(binary=dev.adb_binary, serial=dev.serial))
                    continue
                fps = request['rate'] or 15
                if ScrcpyOptions.frame_rate != fps:
                    if dev._scrcpy_alive:
                        dev._scrcpy_server_stop()
                    ScrcpyOptions.frame_rate = fps
                if action == 'gesture':
                    if request['data']['frame'] not in frames:
                        raise ManagerError('StaleFrame')
                    dispatch_gesture(dev, request['data'])
                    response = {}
                else:
                    if dev.config.Emulator_ScreenshotMethod == 'auto':
                        dev.run_simple_screenshot_benchmark()
                    response = capture_device(dev, quality=request['quality'])
                    size = (response['height'], response['width'])
                    if size != last_size:
                        frames.clear()
                        last_size = size
                    frames.append(request['frame'])
                    response['frame'] = request['frame']
                pipe.send(response)
            except ManagerError as exc:
                pipe.send(dict(error=str(exc), translated=True))
    except (EOFError, BrokenPipeError):
        pass
    except Exception as exc:
        with suppress(EOFError, BrokenPipeError):
            pipe.send(dict(error=str(exc), translated=False))
    finally:
        if device is not None:
            with suppress(Exception):
                device.release_during_wait()
        pipe.close()


class DeviceWorker:
    def __init__(self, config_name, read_emulator_cfg, stopped, is_running, panel, rate):
        self.config_name = config_name
        self.read_emulator_cfg = read_emulator_cfg
        self.stopped = stopped
        self.is_running = is_running
        self.panel = panel
        self.rate = rate

        self.context = multiprocessing.get_context('spawn')
        self.process = None
        self.pipe = None
        self.selection = None
        self.checked_at = 0
        self.frame_id = 0

        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.request = None
        self.awaiting_frame = None
        self.pending_frame = None
        self.active_action = None
        self.holding = False
        self.visible = True
        self.frame_sent_at = 0
        self.next_refresh = 0
        self.refresh_until = 0
        self.thread = threading.Thread(target=self.loop, daemon=True, name='game-manager')

    def _refresh_interval(self, now):
        if self.rate:
            return 1 / self.rate
        if now < self.refresh_until:
            return 0.5
        return 0

    def submit(self, data):
        with self.lock:
            if data['action'] != 'screenshot' and self.is_running():
                raise ManagerError('Running')
            if self.request is not None or self.active_action not in (None, 'screenshot'):
                raise ManagerError('Busy')
            self.request = data
            self.wake.set()

    def acknowledge(self, frame):
        with self.lock:
            if frame == self.awaiting_frame:
                self.awaiting_frame = None
                self.wake.set()

    def configure(self, rate, holding, visible):
        with self.lock:
            if rate != self.rate:
                self.next_refresh = time.perf_counter()
                self.refresh_until = 0
                self.pending_frame = None
            self.rate = rate
            self.holding = holding
            self.visible = visible
            self.wake.set()

    def close(self):
        self.stopped.set()
        with self.lock:
            self.request = None
            self.pending_frame = None
            self.wake.set()

    def _close_process(self):
        if self.process is None:
            return
        if self.process.is_alive():
            with suppress(OSError):
                self.pipe.send(dict(action='close'))
            self.process.join(0.2)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(1)
        self.pipe.close()
        self.process = None
        self.pipe = None

    def _exchange(self, action, **data):
        now = time.perf_counter()
        if action != 'screenshot' or now >= self.checked_at:
            self.selection = self.read_emulator_cfg()
            self.checked_at = now + 1
        self.frame_id += 1
        if self.stopped.is_set():
            raise ManagerError('Closed')
        if action != 'screenshot' and self.is_running():
            raise ManagerError('Running')
        if self.process is None:
            self.pipe, child = self.context.Pipe()
            self.process = self.context.Process(target=device_service, args=(child, self.config_name), daemon=True)
            self.process.start()
            child.close()
        self.pipe.send(dict(action=action, selection=self.selection, rate=self.rate, frame=self.frame_id, **data))
        deadline = time.perf_counter() + 60
        while not self.stopped.is_set():
            if self.pipe.poll(0.05):
                response = self.pipe.recv()
                if 'error' in response:
                    raise (ManagerError if response['translated'] else RuntimeError)(response['error'])
                return response
            if not self.process.is_alive():
                raise TransportError('DeviceUnavailable')
            if time.perf_counter() >= deadline:
                raise TransportError('TimedOut')
        raise ManagerError('Closed')

    def _take_work(self, now):
        with self.lock:
            self.wake.clear()
            if self.awaiting_frame is not None and now - self.frame_sent_at > 5:
                self.rate = 0
                self.refresh_until = 0
                self.awaiting_frame = None
                self.pending_frame = None
                raise TransportError('FrameTimeout')
            if self.request is not None:
                req = self.request
                self.request = None
                self.pending_frame = None
                self.active_action = req['action']
                return req, None, True, 0
            ready = self.visible and not self.holding
            if ready and self.pending_frame is not None and self.awaiting_frame is None:
                image = self.pending_frame
                self.pending_frame = None
                self.awaiting_frame = image['frame']
                self.frame_sent_at = now
                return None, image, False, 0
            interval = self._refresh_interval(now) if ready else 0
            if interval and self.pending_frame is None and now >= self.next_refresh:
                self.active_action = 'screenshot'
                return dict(action='screenshot'), None, False, 0
            delay = min(self.next_refresh - now, 0.1) if interval and self.pending_frame is None else 0.1
            return None, None, False, delay

    def _finish(self, started):
        if self.active_action is not None:
            with self.lock:
                self.active_action = None
                finished = time.perf_counter()
                self.next_refresh = max(finished, started + self._refresh_interval(finished))

    def loop(self):
        previous_running = None
        try:
            while not self.stopped.is_set():
                started = time.perf_counter()
                try:
                    running = self.is_running()
                    if running != previous_running:
                        self.panel.on_state(running=running)
                        previous_running = running
                    request, image, manual, delay = self._take_work(started)
                    if delay:
                        self.wake.wait(delay)
                        continue
                    if image is not None:
                        self.panel.on_frame(image)
                        continue
                    kind = request['action']
                    if kind == 'command':
                        args = split_command(request['command'])
                        target = self._exchange('adb', target=needs_serial(args))
                        args = ['-s', target['serial']] + args if 'serial' in target else args
                        result = run_adb(target['binary'], args, request['timeout'], self.stopped, self.is_running)
                        if result is not None:
                            self.panel.on_result(result)
                    else:
                        if kind == 'gesture':
                            self._exchange('gesture', data=request)
                            started = time.perf_counter()
                            self.refresh_until = started + 2
                            self.panel.cancel_gesture()
                        image = self._exchange('screenshot', quality=90 if manual and kind == 'screenshot' else 20)
                        with self.lock:
                            if self.awaiting_frame is not None:
                                self.pending_frame = image
                                image = None
                            else:
                                self.awaiting_frame = image['frame']
                                self.frame_sent_at = time.perf_counter()
                        if image is not None:
                            self.panel.on_frame(image)
                    self._finish(started)
                    if manual:
                        self.panel.on_state(busy=False)
                except Exception as exc:
                    if not isinstance(exc, ManagerError) or isinstance(exc, TransportError):
                        self._close_process()
                    self._finish(time.perf_counter() + 1)
                    self.panel.on_error(str(exc), isinstance(exc, ManagerError),
                                        isinstance(exc, TransportError) and str(exc) == 'FrameTimeout')
        finally:
            self.close()
            self._close_process()


def panel_action(func):
    @wraps(func)
    def call(self, *args, **kwargs):
        if not self.stopped.is_set():
            with self.ui_lock:
                try:
                    return func(self, *args, **kwargs)
                except ManagerError as exc:
                    self.cancel_gesture()
                    self.output('error', self.text(str(exc)), error=True)
    return call


class PanelStopEvent(threading.Event):
    def __init__(self, current):
        super().__init__()
        self.current = current

    def is_set(self):
        if not super().is_set() and not self.current():
            self.set()
        return super().is_set()

    def wait(self, timeout=None):
        return self.is_set() or super().wait(timeout) or self.is_set()


class GameManagerPanel:
    def __init__(self, gui, config):
        _ensure_ui()
        self.gui = gui
        self.config_name = gui.alas_name
        self.element_id = 'game-manager-' + uuid.uuid4().hex
        self.worker = None
        self.stopped = PanelStopEvent(lambda: gui.alive and gui.page == 'GameManager'
                                              and gui.alas_name == self.config_name and gui.game_manager is self)
        self.ui_lock = threading.RLock()
        cfg = config['GameManager']['GameManager']
        self.settings = dict(RefreshRate=cfg['RefreshRate'], InstantSend=cfg['InstantSend'])
        self.busy = False
        self.holding = False
        self.has_frame = False
        self.running = gui.alas.alive
        self.visible = True
        self.pending = None
        self._ui_state = None

    def scope(self, name):
        return self.element_id + '-' + name

    def text(self, key, **values):
        return web_lang.t('Gui.GameManager.' + key, **values)

    def screen(self, method, data=None):
        if not self.stopped.is_set():
            pw_session.run_js('const r=document.getElementById("pywebio-scope-"+id);'
                              'if(r && r.gameScreen) r.gameScreen[method](data);',
                              id=self.element_id, method=method, data=data)

    def output(self, name, value, error=False):
        with pw_out.use_scope(self.scope(name), clear=True):
            (pw_out.put_error if error else pw_out.put_text)(value)

    def sync(self):
        self.worker.configure(self.settings['RefreshRate'], self.holding or self.busy, self.visible)
        avail = not self.running and not self.busy
        state = dict(enabled=avail, disabled=dict(
            capture=self.busy or self.holding, fullscreen=not self.has_frame,
            send=not avail or self.pending is None, cancel=self.pending is None or self.busy, execute=not avail))
        if state != self._ui_state:
            self._ui_state = state
            self.screen('sync', state)

    @panel_action
    def setting_changed(self, name, value):
        self.settings[name] = web_utils.parse_pin_value(value)
        self.sync()

    @panel_action
    def submit(self, action):
        if action == 'gesture' and self.pending is None:
            return
        request = self.pending if action == 'gesture' else dict(action=action)
        if action == 'command':
            timeout = pw_pin.pin[self.element_id + '_Timeout']
            if type(timeout) is not int or not 1 <= timeout <= 600:
                raise ManagerError('InvalidValue')
            request.update(command=pw_pin.pin[self.element_id + '_Command'], timeout=timeout)
        pw_out.clear(self.scope('error'))
        self.worker.submit(request)
        self.busy = True
        self.sync()

    @panel_action
    def cancel_gesture(self):
        self.pending = None
        self.holding = False
        pw_out.clear(self.scope('gesture'))
        self.screen('reset')
        self.sync()

    def screen_event(self, data):
        if data['action'] == 'frame_ack':
            self.worker.acknowledge(data['frame'])
        else:
            self._screen_event(data)

    @panel_action
    def _screen_event(self, data):
        action = data['action']
        if action in ('holding', 'visible'):
            setattr(self, action, data['value'])
            self.sync()
        elif action == 'stats':
            self.output('status', self.text('Status', **data))
        elif action == 'preview':
            if self.gui.alas.alive:
                raise ManagerError('Running')
            self.pending = dict(action='gesture', kind=data['kind'], start=data['start'],
                                end=data['end'], duration=data['duration'] / 1000, frame=data['frame'])
            self.output('gesture', '{}: {} → {} · {} ms'.format(
                self.text(data['kind'].capitalize()), data['start'], data['end'], data['duration']))
            if self.settings['InstantSend']:
                self.submit('gesture')
            else:
                self.sync()
        elif action == 'cancel':
            self.cancel_gesture()
        elif action == 'image_error':
            raise ManagerError('InvalidImage')

    @panel_action
    def on_frame(self, image):
        if not self.has_frame:
            self.has_frame = True
            self.sync()
        self.screen('frame', image)

    @panel_action
    def on_state(self, **changes):
        for key, value in changes.items():
            setattr(self, key, value)
        if changes.get('running'):
            self.cancel_gesture()
        else:
            self.sync()

    @panel_action
    def on_error(self, message, translated, reset_rate=False):
        if reset_rate:
            self.settings['RefreshRate'] = 0
            pw_pin.pin_update('GameManager_GameManager_RefreshRate', value=0)
        self.busy = False
        self.cancel_gesture()
        self.output('error', self.text(message) if translated else message, error=True)

    @panel_action
    def on_result(self, result):
        flags = [self.text(k) for f, k in (('timeout', 'TimedOut'), ('truncated', 'Truncated')) if result[f]]
        status = ' · '.join([self.text('ExitCode') + ': ' + str(result['code'])] + flags)
        self.output('result', '{}\nstdout:\n{}\nstderr:\n{}'.format(status, result['stdout'], result['stderr']))

    def show(self):
        manager = self.gui.alas
        out = pw_out
        self.worker = DeviceWorker(
            self.config_name, lambda: self.gui.alas_config.read_file(self.config_name)['Alas']['Emulator'],
            self.stopped, lambda: manager.alive, self, self.settings['RefreshRate'])
        pw_session.defer_call(self.worker.close)

        def btn(name, label, onclick, disabled=False):
            return out.put_scope(self.scope(name), [out.put_button(
                self.text(label), onclick=onclick, color='on', disabled=disabled)])

        out.put_scope(self.element_id, scope='groups')
        with out.use_scope(self.element_id):
            out.put_row([btn('capture', 'Capture', lambda: self.submit('screenshot')), None,
                         btn('fullscreen', 'Fullscreen', lambda: self.screen('fullscreen'), True)], size='auto 1fr auto')
            out.put_scope(self.scope('screen'), [out.put_html(
                f'<img title="{escape(self.text("Capture"))}" draggable="false" style="display:none;width:100%;max-height:100vh;object-fit:contain">'
                f'<svg style="position:absolute;pointer-events:none;display:none" aria-hidden="true">'
                f'<defs><marker id="{self.element_id}-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
                f'<path d="M0,0 L8,4 L0,8" fill="#ffd45e"/></marker></defs>'
                f'<line stroke="#ffd45e" stroke-width="3" marker-end="url(#{self.element_id}-arrow)"/>'
                '<circle r="9" fill="#ffd45e"/><circle r="12" fill="none" stroke="#ffd45e" stroke-width="3"/></svg>'
            )]).style('position:relative')
            out.put_row([out.put_scope(self.scope('status')).style('font-size:.85rem'),
                         btn('send', 'Send', lambda: self.submit('gesture'), True),
                         btn('cancel', 'Cancel', self.cancel_gesture, True)], size='minmax(0,1fr) auto auto')
            out.put_scope(self.scope('gesture'))
            out.put_scope(self.scope('error'))
            web_pin.put_textarea(self.element_id + '_Command', label=self.text('Command'), rows=2,
                                 placeholder='adb devices', help_text=self.text('CommandHelp'))
            out.put_row([web_widgets.put_output(dict(
                widget_type='input', name=self.element_id + '_Timeout', type='number',
                title=self.text('Timeout'), value=60, min=1, max=600,
            )), btn('execute', 'Execute', lambda: self.submit('command'))], size='1fr auto')
            out.put_scrollable(out.put_scope(self.scope('result')).style(
                'white-space:pre-wrap;font-family:monospace'), height=(0, 240), border=False)

        for name in self.settings:
            pw_pin.pin_on_change('GameManager_GameManager_' + name,
                                 onchange=lambda value, name=name: self.setting_changed(name, value))
        pw_session.run_js(SCREEN_BRIDGE, id=self.element_id,
                          callback=pw_io.output_register_callback(self.screen_event, serial_mode=True))
        self.sync()
        pw_session.register_thread(self.worker.thread)
        self.worker.thread.start()


SCREEN_BRIDGE = r'''
(() => {
  const root = document.getElementById('pywebio-scope-' + id);
  const screen = document.getElementById('pywebio-scope-' + id + '-screen');
  if (!root || !screen) return;
  const img = screen.querySelector('img');
  const overlay = screen.querySelector('svg');
  const line = overlay.querySelector('line');
  const dots = overlay.querySelectorAll('circle');
  const buttons = Object.fromEntries(['capture', 'fullscreen', 'send', 'cancel', 'execute'].map(
    k => [k, document.querySelector('#pywebio-scope-' + id + '-' + k + ' button')]));
  let enabled = false, holding = false, disposed = false;
  let frame = null, pointer = null, deferred = null, path = null;
  let clock = performance.now(), count = 0, bytes = 0;

  const dispose = () => {
    if (disposed) return;
    disposed = true;
    document.removeEventListener('visibilitychange', visible);
    resize.disconnect();
    clearInterval(timer);
  };
  const send = data => {
    if (disposed || !root.isConnected) return dispose();
    WebIO.pushData(data, callback);
  };
  const ack = data => send({action: 'frame_ack', frame: data.frame});

  const point = (event, clamp) => {
    const box = img.getBoundingClientRect();
    const scale = Math.min(box.width / frame.width, box.height / frame.height);
    const x = (event.clientX - box.left - (box.width - frame.width * scale) / 2) / scale;
    const y = (event.clientY - box.top - (box.height - frame.height * scale) / 2) / scale;
    if (!clamp && (x < 0 || y < 0 || x >= frame.width || y >= frame.height)) return null;
    return [Math.max(0, Math.min(frame.width - 1, Math.floor(x))), Math.max(0, Math.min(frame.height - 1, Math.floor(y)))];
  };

  const draw = () => {
    overlay.style.display = path ? 'block' : 'none';
    if (!path) return;
    const box = img.getBoundingClientRect();
    const parent = screen.getBoundingClientRect();
    const [a, b] = path;
    Object.assign(overlay.style, {
      left: (box.left - parent.left) + 'px', top: (box.top - parent.top) + 'px',
      width: box.width + 'px', height: box.height + 'px'
    });
    overlay.setAttribute('viewBox', `0 0 ${frame.width} ${frame.height}`);
    Object.entries({x1: a[0], y1: a[1], x2: b[0], y2: b[1]}).forEach(([k, v]) => line.setAttribute(k, v));
    dots.forEach((dot, i) => { dot.setAttribute('cx', path[i][0]); dot.setAttribute('cy', path[i][1]); });
  };

  const timer = setInterval(() => {
    if (!root.isConnected) return dispose();
    const now = performance.now();
    const elapsed = now - clock;
    if (frame) {
      const {image, ...details} = frame;
      send({...details, action: 'stats', fps: count * 1000 / elapsed, mbps: bytes * 8 / (elapsed * 1000)});
    }
    clock = now;
    count = bytes = 0;
  }, 1000);
  const resize = new ResizeObserver(draw);
  resize.observe(screen);

  const present = data => {
    if (disposed) return;
    if (holding) { deferred = data; ack(data); return; }
    const image = new Image();
    image.onload = () => {
      if (disposed) return;
      if (frame && data.frame <= frame.frame) { ack(data); return; }
      if (holding) { deferred = data; ack(data); return; }
      frame = data;
      img.src = data.image;
      img.style.display = 'block';
      draw();
      if (document.hidden) ack(data);
      else requestAnimationFrame(() => { count++; ack(data); });
    };
    image.onerror = () => { ack(data); send({action: 'image_error'}); };
    image.src = data.image;
  };

  const reset = () => {
    pointer = path = null;
    holding = false;
    draw();
    if (deferred) {
      const data = deferred;
      deferred = null;
      present(data);
    }
  };
  const cancel = () => { reset(); send({action: 'cancel'}); };

  screen.addEventListener('pointerdown', event => {
    if (!enabled || holding || !frame || event.target !== img || event.button !== 0 || !event.isPrimary) return;
    const start = point(event, false);
    if (!start) return;
    event.preventDefault();
    img.setPointerCapture(event.pointerId);
    pointer = {start, id: event.pointerId, time: performance.now(), x: event.clientX, y: event.clientY};
    path = [start, start];
    draw();
    holding = true;
    send({action: 'holding', value: true});
  });
  screen.addEventListener('pointermove', event => {
    if (pointer && event.pointerId === pointer.id) {
      path[1] = point(event, true);
      draw();
    }
  });
  screen.addEventListener('pointerup', event => {
    if (!pointer || event.pointerId !== pointer.id) return;
    if (!enabled) return cancel();
    const duration = Math.max(1, Math.min(10000, Math.round(performance.now() - pointer.time)));
    const dist = Math.hypot(event.clientX - pointer.x, event.clientY - pointer.y);
    const kind = dist >= 6 ? 'swipe' : duration >= 500 ? 'hold' : 'tap';
    path = [pointer.start, kind === 'swipe' ? point(event, true) : pointer.start];
    draw();
    send({action: 'preview', kind, start: path[0], end: path[1], duration, frame: frame.frame});
    pointer = null;
  });
  screen.addEventListener('pointercancel', cancel);
  screen.addEventListener('lostpointercapture', () => { if (pointer) cancel(); });

  const visible = () => send({action: 'visible', value: !document.hidden});
  document.addEventListener('visibilitychange', visible);

  root.gameScreen = {
    frame: data => { bytes += data.image.length; present(data); },
    reset,
    sync: state => {
      enabled = state.enabled;
      img.style.touchAction = enabled ? 'none' : '';
      for (const [k, v] of Object.entries(state.disabled)) {
        if (buttons[k]) buttons[k].disabled = v;
      }
    },
    fullscreen: () => {
      const action = document.fullscreenElement ? document.exitFullscreen() : screen.requestFullscreen();
      action.catch(() => send({action: 'image_error'}));
    }
  };
  visible();
})();
'''
