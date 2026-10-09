import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cached_property import cached_property

from alas import AzurLaneAutoScript
from module.config.config import AzurLaneConfig, TaskEnd
from module.exception import RequestHumanTakeover
from submodule.AlasMaaBridge.maa import ArknightsAutoScript
from submodule.AlasMaaBridge.module.config.config import ArknightsConfig
from submodule.AlasMaaBridge.module.exception import MaaError
from submodule.AlasMaaBridge.module.handler.handler import ArknightsConnection, AssistantHandler
from submodule.AlasMaaBridge.module.asst.asst import Asst


class RecoveryScript(ArknightsAutoScript):
    def __init__(self, outcomes):
        super().__init__('test')
        self.outcomes = iter(outcomes)
        self.stop_event = threading.Event()
        self.queued_startup = False
        self.tasks = []
        self._device = Mock(package='Arknights')
        self._config = SimpleNamespace(
            task=SimpleNamespace(command='MaaFight'),
            Error_OnePushConfig='provider: null', Error_HandleError=True, Error_SaveError=False,
            task_call=self.task_call,
        )

    @property
    def config(self):
        return self._config

    @property
    def device(self):
        return self._device

    @property
    def checker(self):
        return Mock(is_recovered=Mock(return_value=False))

    @cached_property
    def asst(self):
        return Mock(close=Mock(return_value=True))

    def task_call(self, task):
        assert task == 'Restart'
        self.queued_startup = True

    def get_next_task(self):
        task = 'MaaStartup' if self.queued_startup else 'MaaFight'
        self.queued_startup = False
        self.config.task.command = task
        self.tasks.append(task)
        return task

    def maa_fight(self):
        outcome = next(self.outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        self.stop_event.set()
        if outcome == 'task_end':
            raise TaskEnd


class RecoveryTest(unittest.TestCase):
    def setUp(self):
        self.notify_patch = patch('alas.handle_notify')
        self.notify = self.notify_patch.start()
        self.addCleanup(self.notify_patch.stop)
        self.handler_patch = patch('submodule.AlasMaaBridge.maa.AssistantHandler')
        self.handler = self.handler_patch.start().return_value
        self.addCleanup(self.handler_patch.stop)
        logger_patch = patch('alas.logger.set_file_logger')
        logger_patch.start()
        self.addCleanup(logger_patch.stop)

    def test_scheduler_notifies_after_three_failures(self):
        script = RecoveryScript([MaaError('failed')] * 3)
        with self.assertRaises(SystemExit):
            script.loop()
        self.assertEqual(script.tasks, ['MaaFight', 'MaaStartup'] * 2 + ['MaaFight'])
        self.assertEqual(self.handler.restart.call_count, 2)
        self.assertEqual(script.failure_record, {'MaaFight': 3})
        self.notify.assert_called_once()

    def test_failed_restart_uses_same_recovery_budget(self):
        script = RecoveryScript([MaaError('failed')])
        self.handler.restart.side_effect = MaaError('adb failed')
        with self.assertRaises(SystemExit):
            script.loop()
        self.assertEqual(script.tasks, ['MaaFight'] + ['MaaStartup'] * 2)
        self.assertEqual(self.handler.restart.call_count, 2)
        self.assertEqual(script.failure_record, {'MaaFight': 3})
        self.notify.assert_called_once()

    def test_task_recovers_and_clears_budget(self):
        script = RecoveryScript([MaaError('failed'), 'task_end'])
        script.loop()
        self.assertEqual(script.tasks, ['MaaFight', 'MaaStartup', 'MaaFight'])
        self.assertEqual(script.failure_record, {'MaaFight': 0})
        self.assertIsNone(script.recovering_task)
        self.notify.assert_not_called()

    def test_mixed_failures_share_the_scheduler_counter(self):
        script = RecoveryScript([MaaError('fight failed')] * 2)
        self.handler.startup.side_effect = [MaaError('login failed'), None]
        with self.assertRaises(SystemExit):
            script.loop()
        self.assertEqual(script.tasks, ['MaaFight', 'MaaStartup', 'MaaStartup', 'MaaFight'])
        self.assertEqual(script.failure_record, {'MaaFight': 3})
        self.notify.assert_called_once()

    def test_adb_restart_precedes_bounded_native_cleanup(self):
        script = RecoveryScript([MaaError('failed'), True])
        old_asst = script.asst
        events = []
        self.handler.restart.side_effect = lambda: events.append('adb')
        def close(timeout):
            self.assertEqual(timeout, 10)
            events.append('close')
            return True
        old_asst.close.side_effect = close
        script.loop()
        self.assertEqual(events, ['adb', 'close'])
        old_asst.stop.assert_not_called()
        self.assertIsNot(script.asst, old_asst)

    def test_stuck_native_cleanup_notifies_at_normal_failure_limit(self):
        script = RecoveryScript([MaaError('failed')])
        old_asst = script.asst
        old_asst.close.return_value = False
        with self.assertRaises(SystemExit):
            script.loop()
        self.assertEqual(old_asst.close.call_count, 2)
        self.assertEqual(self.handler.restart.call_count, 2)
        self.handler.startup.assert_not_called()
        old_asst.stop.assert_not_called()
        self.assertEqual(script.failure_record, {'MaaFight': 3})
        self.notify.assert_called_once()

    def test_initial_startup_failure_also_stops_after_three_failures(self):
        script = RecoveryScript([])
        script.queued_startup = True
        self.handler.startup.side_effect = MaaError('login failed')
        with self.assertRaises(SystemExit):
            script.loop()
        self.assertEqual(script.tasks, ['MaaStartup'] * 3)
        self.assertEqual(self.handler.restart.call_count, 2)
        self.assertEqual(script.failure_record, {'MaaStartup': 3})
        self.notify.assert_called_once()

    def test_azur_lane_keeps_original_counter_and_restart_task(self):
        script = AzurLaneAutoScript('test')
        config = SimpleNamespace(task_call=Mock(), Error_SaveError=False)
        script.__dict__['config'] = config
        script.__dict__['device'] = Mock(package='AzurLane')
        script.restart = Mock(side_effect=MaaError('not running'))
        self.assertFalse(script.run('restart', skip_first_screenshot=True))
        config.task_call.assert_called_once_with('Restart')
        self.assertEqual([script.record_task_result('Fight', False)[1] for _ in range(3)], [1, 2, 3])
        self.assertEqual(script.record_task_result('Fight', True), ('Fight', 0))

    def test_startup_failure_consumes_recovery_attempt(self):
        script = RecoveryScript([MaaError('failed'), True])
        self.handler.startup.side_effect = [MaaError('login failed'), None]
        script.loop()
        self.assertEqual(script.tasks, ['MaaFight', 'MaaStartup', 'MaaStartup', 'MaaFight'])
        self.assertEqual(self.handler.restart.call_count, 2)
        self.notify.assert_not_called()

    def test_configuration_error_notifies_without_restarting(self):
        script = RecoveryScript([RequestHumanTakeover('invalid config')])
        with self.assertRaises(SystemExit):
            script.loop()
        self.handler.restart.assert_not_called()
        self.notify.assert_called_once()


class ConfigTest(unittest.TestCase):
    def test_restart_mapping_preserves_force_call(self):
        config = object.__new__(ArknightsConfig)
        with patch.object(AzurLaneConfig, 'task_call', return_value=True) as call:
            self.assertTrue(config.task_call('Restart', force_call=False))
            call.assert_called_once_with('MaaStartup', force_call=False)
            call.reset_mock()
            config.task_call('MaaFight')
            call.assert_called_once_with('MaaFight', force_call=True)


class HandlerTest(unittest.TestCase):
    def test_connection_reuses_existing_app_control(self):
        connection = ArknightsConnection(SimpleNamespace(), '127.0.0.1:5555', 'com.hypergryph.arknights')
        connection.adb_shell = Mock(return_value='Events injected: 1')
        connection.app_stop_adb()
        self.assertTrue(connection.app_start_adb(allow_failure=True))
        self.assertEqual(connection.adb_shell.call_args_list[0][0][0],
                         ['am', 'force-stop', 'com.hypergryph.arknights'])
        self.assertEqual(connection.adb_shell.call_args_list[1][0][0][:3],
                         ['monkey', '-p', 'com.hypergryph.arknights'])

    def test_runtime_failures_are_recoverable(self):
        for failure in ['append', 'start', 'timeout', 'task_error', 'connect']:
            with self.subTest(failure=failure):
                asst = Mock(append_task=Mock(return_value=1), start=Mock(return_value=True))
                handler = AssistantHandler(SimpleNamespace(MaaEmulator_Serial='127.0.0.1:5555'), asst)
                handler.Message = SimpleNamespace(TaskChainError=1)
                handler.callback_timer = Mock(reached=Mock(return_value=failure == 'timeout'))
                if failure == 'append':
                    asst.append_task.return_value = 0
                elif failure == 'start':
                    asst.start.return_value = False
                elif failure == 'task_error':
                    def start():
                        handler.signal = handler.Message.TaskChainError
                        return True
                    asst.start.side_effect = start
                elif failure == 'connect':
                    asst.connect.return_value = False
                with self.assertRaises(MaaError):
                    if failure == 'connect':
                        handler.connect()
                    else:
                        handler.maa_start('Fight', {})

    def test_stop_timeout_is_recoverable(self):
        handler = AssistantHandler(SimpleNamespace(), Mock())
        handler.callback_timer = Mock(reached=Mock(return_value=True))
        with self.assertRaises(MaaError):
            handler.maa_stop()

    def test_restart_uses_adb_and_resolved_serial(self):
        config = SimpleNamespace(MaaEmulator_Serial='bluestacks5-hyperv',
                                 MaaEmulator_MaaPath='maa', MaaEmulator_PackageName='Official')
        handler = AssistantHandler(config, Mock())
        def resolve_serial():
            handler.serial = '127.0.0.1:5555'
        with patch.object(handler, 'serial_check', side_effect=resolve_serial), \
                patch('submodule.AlasMaaBridge.module.handler.handler.read_file',
                      return_value={'packageName': {'Official': 'com.hypergryph.arknights'}}), \
                patch('submodule.AlasMaaBridge.module.handler.handler.ArknightsConnection') as connection:
            device = connection.return_value
            handler.restart()
            connection.assert_called_once_with(config, '127.0.0.1:5555', 'com.hypergryph.arknights')
            device.adb_connect.assert_called_once_with(wait_device=False)
            device.app_stop_adb.assert_called_once_with()
            device.app_start_adb.assert_called_once_with(allow_failure=True)
            device.app_start_adb.return_value = False
            with self.assertRaises(MaaError):
                handler.restart()
            device.adb_connect.side_effect = RequestHumanTakeover
            with self.assertRaises(MaaError):
                handler.restart()


class NativeCleanupTest(unittest.TestCase):
    def test_timeout_reuses_single_destroy_thread(self):
        asst = object.__new__(Asst)
        asst._Asst__ptr = 123
        started = threading.Event()
        release = threading.Event()
        def destroy(ptr):
            self.assertEqual(ptr, 123)
            started.set()
            release.wait(2)
        with patch.object(Asst, '_Asst__lib', SimpleNamespace(AsstDestroy=Mock(side_effect=destroy)),
                          create=True) as lib:
            try:
                self.assertFalse(asst.close(timeout=0.01))
                self.assertTrue(started.is_set())
                self.assertFalse(asst.close(timeout=0.01))
                lib.AsstDestroy.assert_called_once_with(123)
                self.assertTrue(asst._close_thread.daemon)
                asst.__del__()
                lib.AsstDestroy.assert_called_once_with(123)
            finally:
                release.set()
                self.assertTrue(asst.close(timeout=1))


if __name__ == '__main__':
    unittest.main()
