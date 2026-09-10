from __future__ import annotations
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from ckb_core.common import json_write
from ckb_core.obsidian_plugin import (
    PLUGIN_ID, REQUIRED_FILES, OPTIONAL_FILES, register_obsidian_plugin,
    deploy_obsidian_plugin_to_vault,
)

ROOT = Path(__file__).resolve().parents[1]


def tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


class DeploymentPreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ckb-deploy-preserve-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vault = self.root / 'vault'
        self.target = self.vault / '.obsidian/plugins' / PLUGIN_ID
        self.target.mkdir(parents=True)
        self.package = self.root / 'package'
        self.package.mkdir()
        for name in (*REQUIRED_FILES, *OPTIONAL_FILES):
            (self.target / name).write_bytes(('old:' + name).encode())
            (self.package / name).write_bytes(('new:' + name).encode())
        json_write(self.target / 'manifest.json', {'id': PLUGIN_ID, 'version': '0.8.0'})
        json_write(self.package / 'manifest.json', {'id': PLUGIN_ID, 'version': '0.9.1'})
        (self.target / 'data.json').write_bytes(b'{"model":"keep","custom":true}\r\n')
        (self.target / 'user-notes').mkdir()
        (self.target / 'user-notes/settings.txt').write_bytes(b'user-owned\r\n')
        (self.vault / 'overview.canvas').write_bytes(b'{"nodes":[{"id":"user-card"}],"edges":[]}\n')
        other = self.vault / '.obsidian/plugins/other-plugin'
        other.mkdir(); (other / 'data.json').write_bytes(b'{"keep":1}')
        json_write(self.vault / '.obsidian/community-plugins.json', ['other-plugin', PLUGIN_ID])
        community = self.vault / '.obsidian/community-plugins.json'
        community.write_bytes(community.read_bytes().replace(b'\n', b'\r\n'))
        self.registry = self.root / 'registry.json'
        register_obsidian_plugin(self.package, self.registry)
        self.before = tree(self.vault)

    def deploy(self):
        return deploy_obsidian_plugin_to_vault(self.vault, self.registry)

    def assert_preserved(self):
        after = tree(self.vault)
        for relative, data in self.before.items():
            if relative.startswith('.obsidian/plugins/' + PLUGIN_ID + '/') and Path(relative).name in (*REQUIRED_FILES, *OPTIONAL_FILES):
                continue
            self.assertEqual(after[relative], data, relative)
        self.assertFalse(list(self.target.parent.glob('.' + PLUGIN_ID + '.deploy-*')))

    def test_normal_upgrade_preserves_settings_user_files_canvas_and_other_plugins(self):
        result = self.deploy()
        self.assertEqual(result['status'], 'deployed')
        self.assertTrue((self.target/'data.json').is_file(), 'upgrade deleted user data.json')
        for name in (*REQUIRED_FILES, *OPTIONAL_FILES):
            self.assertEqual((self.target/name).read_bytes(), (self.package/name).read_bytes())
        self.assert_preserved()

    def test_actual_distribution_core_and_independent_deploy_preserve_user_state(self):
        dist = ROOT / 'plugins/obsidian-code-knowledge-builder/dist'
        register_obsidian_plugin(dist, self.registry)
        self.deploy(); self.assert_preserved()
        for name in REQUIRED_FILES:
            self.assertEqual((self.target/name).read_bytes(), (dist/name).read_bytes())
        spec = importlib.util.spec_from_file_location('independent_deploy', dist/'deploy.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        output = self.root/'output'; output.mkdir(); json_write(output/'state.json', {'status':'complete'})
        module.deploy(self.vault, output, Path(os.sys.executable), ROOT/'scripts/ckb.py')
        self.assert_preserved()
        for name in REQUIRED_FILES:
            self.assertEqual((self.target/name).read_bytes(), (dist/name).read_bytes())

    def test_replace_denied_falls_back_to_declared_file_copy(self):
        with patch.object(Path, 'replace', side_effect=PermissionError('rename denied')):
            result = self.deploy()
        self.assertEqual(result['install_mode'], 'in-place-copy')
        self.assert_preserved()

    def test_partial_copy_failure_restores_old_package_and_config(self):
        replace = Path.replace; copy = shutil.copy2; injected = False
        def denied(source, target):
            if Path(target) == self.target/'styles.css':
                raise PermissionError('file rename denied')
            return replace(source, target)
        def partial(source, target, *args, **kwargs):
            nonlocal injected
            if Path(target) == self.target/'styles.css' and not injected:
                injected = True
                Path(target).write_bytes(b'partial update')
                raise OSError('injected partial copy failure')
            return copy(source, target, *args, **kwargs)
        with patch.object(Path, 'replace', denied), patch.object(shutil, 'copy2', partial):
            with self.assertRaisesRegex(OSError, 'partial copy'):
                self.deploy()
        self.assertTrue(injected)
        self.assertEqual(tree(self.vault), self.before)
        self.assert_preserved()

    def test_invalid_enabled_list_fails_before_package_update(self):
        json_write(self.vault/'.obsidian/community-plugins.json', {'invalid':True})
        before = tree(self.vault)
        with self.assertRaisesRegex(Exception, 'must contain a list'):
            self.deploy()
        self.assertEqual(tree(self.vault), before)

    def test_absent_optional_package_file_removed_but_user_file_preserved(self):
        (self.package/'build-record.json').unlink()
        register_obsidian_plugin(self.package, self.registry)
        self.deploy()
        self.assertFalse((self.target/'build-record.json').exists())
        self.assert_preserved()

    def hold_windows(self, path, share, directory=False):
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
        kernel.CreateFileW.restype = ctypes.c_void_p
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.CreateFileW(str(path), 0x80000000, share, None, 3, 0x02000000 if directory else 0, None)
        self.assertNotEqual(handle, ctypes.c_void_p(-1).value, ctypes.get_last_error())
        return kernel, handle

    @unittest.skipUnless(os.name == 'nt', 'native Windows sharing semantics')
    def test_real_windows_open_directory_upgrade(self):
        kernel, handle = self.hold_windows(self.target, 3, True)
        try: self.deploy()
        finally: kernel.CloseHandle(handle)
        self.assert_preserved()

    @unittest.skipUnless(os.name == 'nt', 'native Windows sharing semantics')
    def test_real_windows_file_deny_delete_allows_copy_fallback(self):
        kernel, handle = self.hold_windows(self.target/'main.js', 3)
        try: result = self.deploy()
        finally: kernel.CloseHandle(handle)
        self.assertEqual(result['install_mode'], 'in-place-copy')
        self.assertEqual((self.target/'main.js').read_bytes(), (self.package/'main.js').read_bytes())
        self.assert_preserved()

    @unittest.skipUnless(os.name == 'nt', 'native Windows sharing semantics')
    def test_real_windows_file_deny_write_restores_prior_files(self):
        kernel, handle = self.hold_windows(self.target/'styles.css', 1)
        try:
            with self.assertRaises(PermissionError): self.deploy()
        finally: kernel.CloseHandle(handle)
        self.assertEqual(tree(self.vault), self.before)
        self.assert_preserved()

if __name__ == '__main__': unittest.main()

