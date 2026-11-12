"""Exercise compositor installation transactions without touching the system."""
from pathlib import Path
import importlib.util
import json
import tempfile
import subprocess
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('capture_install', Path(__file__).with_name('capture-install.py'))


class CaptureInstallTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(self.module)
        m = self.module
        m.LIBRARY = root / 'lib/libmutter.so'
        m.BACKUP = root / 'state/stock/libmutter.so'
        m.PAYLOAD = root / 'payload'
        m.MARKER = root / 'state/marker.json'
        m.OVERRIDE = root / 'config/override.conf'
        m.LIBRARY.parent.mkdir()
        m.LIBRARY.write_bytes(b'original Ubuntu compositor')
        m.PAYLOAD.mkdir()
        (m.PAYLOAD / m.LIBRARY.name).write_bytes(b'capture companion')
        self.manifest = {'protocol': 1, 'provider': 'gnome-mutter',
                         'sourceVersion': '46.2-test',
                         'sha256': m.sha(m.PAYLOAD / m.LIBRARY.name)}
        (m.PAYLOAD / 'manifest.json').write_text(json.dumps(self.manifest))
        self.current_owner = ''
        self.version = '46.2-test'
        self.missing_library = False
        self.addCleanup(patch.stopall)
        patch.object(m, 'owner', side_effect=lambda: self.current_owner).start()
        patch.object(m.subprocess, 'check_output', side_effect=lambda *a, **k: self.version).start()
        patch.object(m.subprocess, 'run', side_effect=self.divert).start()
        self.restart = patch.object(m, 'notify_restart').start()

    def divert(self, args, **kwargs):
        m = self.module
        if args[0] == 'ldd':
            return subprocess.CompletedProcess(args, 0,
                stdout='libmissing.so => not found' if self.missing_library else '', stderr='')
        self.assertEqual(args[0], 'dpkg-divert')
        self.assertIn('--package', args)
        self.assertIn(str(m.BACKUP), args)
        if '--add' in args:
            m.LIBRARY.rename(m.BACKUP)
            self.current_owner = m.PACKAGE
        elif '--remove' in args:
            m.BACKUP.rename(m.LIBRARY)
            self.current_owner = ''
        else:
            self.fail('Unexpected command')

    def test_install_and_remove_preserve_original(self):
        m = self.module
        m.enable()
        self.assertEqual(m.LIBRARY.read_bytes(), b'capture companion')
        self.assertEqual(m.BACKUP.read_bytes(), b'original Ubuntu compositor')
        self.assertEqual(json.loads(m.MARKER.read_text())['sha256'], m.sha(m.LIBRARY))
        m.disable()
        self.assertEqual(m.LIBRARY.read_bytes(), b'original Ubuntu compositor')
        self.assertFalse(m.BACKUP.exists())
        self.assertFalse(m.MARKER.exists())
        self.assertFalse(m.OVERRIDE.exists())

    def test_reinstall_does_not_replace_stock_backup(self):
        m = self.module
        m.enable()
        m.enable()
        self.assertEqual(m.BACKUP.read_bytes(), b'original Ubuntu compositor')
        m.disable()
        self.assertEqual(m.LIBRARY.read_bytes(), b'original Ubuntu compositor')

    def test_activation_failure_rolls_back(self):
        m = self.module
        self.restart.side_effect = RuntimeError('Simulated activation failure')
        with self.assertRaises(RuntimeError):
            m.enable()
        self.assertEqual(m.LIBRARY.read_bytes(), b'original Ubuntu compositor')
        self.assertEqual(self.current_owner, '')
        self.assertFalse(m.MARKER.exists())
        self.assertFalse(m.OVERRIDE.exists())

    def test_changed_library_is_not_deleted(self):
        m = self.module
        m.enable()
        m.LIBRARY.write_bytes(b'changed by another integration')
        with self.assertRaises(RuntimeError):
            m.disable()
        self.assertEqual(m.LIBRARY.read_bytes(), b'changed by another integration')
        self.assertTrue(m.BACKUP.exists())

    def test_version_mismatch_does_not_change_system(self):
        self.version = 'different-version'
        with self.assertRaises(RuntimeError):
            self.module.enable()
        self.assertEqual(self.module.LIBRARY.read_bytes(), b'original Ubuntu compositor')
        self.assertFalse(self.module.BACKUP.exists())

    def test_foreign_diversion_is_not_modified(self):
        self.current_owner = 'another-package'
        with self.assertRaises(RuntimeError):
            self.module.enable()
        self.assertFalse(self.module.BACKUP.exists())

    def test_missing_runtime_library_does_not_modify_compositor(self):
        self.missing_library = True
        with self.assertRaises(RuntimeError):
            self.module.enable()
        self.assertEqual(self.module.LIBRARY.read_bytes(), b'original Ubuntu compositor')
        self.assertFalse(self.module.BACKUP.exists())

    def test_corrupt_payload_is_rejected(self):
        m = self.module
        (m.PAYLOAD / m.LIBRARY.name).write_bytes(b'corrupt')
        with self.assertRaises(RuntimeError):
            m.enable()
        self.assertFalse(m.BACKUP.exists())


if __name__ == '__main__':
    unittest.main()
