"""Exercise real file plans/transactions in temporary isolated roots; no hardware."""
from pathlib import Path
import importlib.util
import json
import os
import tempfile
import unittest
import itertools

PACKAGE=Path(os.environ.get('RETROGRZMOT_TEST_PACKAGE',Path(__file__).resolve().parents[1])).resolve()
spec=importlib.util.spec_from_file_location('bundle_install',PACKAGE/'install.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

SCRIPT='''#!/bin/bash
do_videostart ()
{
    if test -n "$display"; then
        start-stop-daemon --exec /usr/bin/mpv -- --really-quiet --no-config --drm-mode=preferred "$video"
    else
        start-stop-daemon --exec /usr/bin/mpv -- --really-quiet --no-config --drm-mode=preferred "$video"
    fi
}

case "$1" in
start) do_videostart ;;
esac
'''

class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='retrogrzmot-package-test-')
        self.root=Path(self.temp.name)
        self.host=mod.Host(self.root,live=False)
        self.package=json.loads((PACKAGE/'package.json').read_text())
        self.available=set(self.package['available_modules'])
        self.fixture()
    def tearDown(self): self.temp.cleanup()
    def put(self,name,data):
        p=self.host.path(name);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(data if isinstance(data,bytes) else data.encode())
        if os.name=='posix': p.chmod(0o644)
    def fixture(self,lang='fr_FR'):
        self.put(mod.CONF,'# User settings\nsystem.language='+lang+'\naudio.volume=37\nsystem.services=other_service\n# splash.screen.sound=0\n')
        self.put('/boot/batocera-boot.conf','# Existing boot\nes.resolution=1280x720\n')
        self.put('/boot/config.txt','dtparam=audio=on\n')
        self.put(mod.ES,'<config><string name="Language" value="'+lang+'"/><string name="ThemeSet" value="previous"/><bool name="Custom" value="true"/></config>')
        self.put(mod.CARBON+'/theme.xml','<theme><formatVersion>7</formatVersion><include>./views/system.xml</include></theme>')
        self.put('/etc/init.d/S28splash',SCRIPT)
        self.put(mod.HOOK,'#!/bin/bash\n# user-owned job\necho untouched\nexit 0\n')
        self.put('/userdata/splash/previous.MP4',b'previous user movie')
        self.put('/userdata/system/configs/retrogrzmot-led.json','{"logo":{"brightness":17},"custom":"preserve"}')
    def snapshot(self):
        return {p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*')
                if p.is_file() and 'retrogrzmot-bundle-backups' not in p.parts}
    def plan(self,modules): return mod.build_plan(PACKAGE,self.host,modules)

    def test_package_integrity(self): mod.integrity(PACKAGE)

    def test_plan_and_check_change_nothing(self):
        before=self.snapshot();p=self.plan(self.available);mod.validate_plan(p)
        self.assertGreater(len(mod.changed_records(p)),10)
        self.assertEqual(before,self.snapshot());self.assertEqual(self.host.commands,[])

    def test_optional_hardware_is_not_enabled(self):
        p=self.plan({'theme'});mod.apply(p,PACKAGE)
        self.assertFalse(self.host.path('/boot/retrogrzmot-early/enable-led').exists())
        self.assertFalse(self.host.path('/userdata/system/services/retrogrzmot_exit').exists())
        self.assertNotIn('system.power.switch=',self.host.path(mod.CONF).read_text())
        self.assertEqual(self.host.path('/boot/config.txt').read_text(),'dtparam=audio=on\n')

    def test_supported_module_combinations_have_coherent_plans(self):
        options=sorted(self.available-{'theme'})
        before=self.snapshot()
        for values in itertools.product([False,True],repeat=len(options)):
            selected={name for name,on in zip(options,values) if on}
            p=self.plan(selected)
            if 'exit' in selected:self.assertIn('skip',p.modules)
            if selected&{'oled','early-led'}:
                self.assertEqual(p.files[mod.HOOK][0].decode().count('early_start.sh'),1)
            self.assertNotIn('/userdata/system/configs/retrogrzmot-led.json',p.files)
        self.assertEqual(before,self.snapshot())

    def test_pl_en_fr_de_ja_languages_and_unrelated_settings_survive(self):
        import xml.etree.ElementTree as ET
        for language in ['pl_PL','en_US','fr_FR','de_DE','ja_JP']:
            self.fixture(language)
            p=self.plan(self.available);mod.apply(p,PACKAGE)
            conf=self.host.path(mod.CONF).read_text()
            self.assertIn('system.language='+language,conf)
            self.assertIn('audio.volume=37',conf)
            self.assertIn('other_service',mod.ini_value(conf,'system.services'))
            root=ET.fromstring(self.host.path(mod.ES).read_bytes())
            self.assertEqual(root.find("string[@name='Language']").get('value'),language)
            self.assertEqual(root.find("bool[@name='Custom']").get('value'),'true')

    def test_preexisting_led_preferences_are_preserved(self):
        target='/userdata/system/configs/retrogrzmot-led.json';before=self.host.path(target).read_bytes()
        mod.apply(self.plan(self.available),PACKAGE)
        self.assertEqual(before,self.host.path(target).read_bytes())

    def test_second_install_is_idempotent(self):
        mod.apply(self.plan(self.available),PACKAGE)
        self.assertEqual(mod.changed_records(self.plan(self.available)),[])
        self.assertIsNone(mod.apply(self.plan(self.available),PACKAGE))

    def test_custom_boot_jobs_survive_and_run_after_dispatch(self):
        p=self.plan({'theme','early-led'});mod.apply(p,PACKAGE)
        text=self.host.path(mod.HOOK).read_text()
        self.assertIn('echo untouched',text)
        self.assertLess(text.index(mod.BEGIN),text.index('exit 0'))
        self.assertEqual(text.count(mod.BEGIN),1)

    def test_known_legacy_oled_and_led_are_both_retained(self):
        self.put(mod.HOOK,(PACKAGE/'compat/legacy-boot-oled-led.sh').read_bytes())
        self.put('/boot/retrogrzmot-early/splash.py','print("existing OLED")\n')
        mod.apply(self.plan({'theme','early-led'}),PACKAGE)
        self.assertTrue(self.host.path('/boot/retrogrzmot-early/enable-oled').exists())
        self.assertTrue(self.host.path('/boot/retrogrzmot-early/enable-led').exists())
        self.assertEqual(self.host.path(mod.HOOK).read_text().count('early_start.sh'),1)

    def test_edited_legacy_hook_is_rejected_before_changes(self):
        self.put(mod.HOOK,(PACKAGE/'compat/legacy-boot-oled.sh').read_text()+'echo owner-edit\n')
        before=self.snapshot()
        with self.assertRaises(ValueError): self.plan({'theme','early-led'})
        self.assertEqual(before,self.snapshot())

    def test_usb_only_does_not_request_gpio_in_helper_command(self):
        p=self.plan({'theme','skip-usb'})
        self.assertIn('--usb-only',p.files['/etc/init.d/S28splash'][0].decode())
        self.assertNotIn('exit',p.modules)

    def test_splash_patch_is_idempotent(self):
        text=mod.skip_patch(SCRIPT,False)
        self.assertEqual(text,mod.skip_patch(text,False))
        self.assertEqual(text.count('--input-ipc-server=/tmp/retrogrzmot-splash.sock'),2)

    def test_duplicate_setting_is_rejected_without_writes(self):
        self.put(mod.CONF,'splash.screen.sound=0\nsplash.screen.sound=1\n')
        before=self.snapshot()
        with self.assertRaises(ValueError): self.plan({'theme'})
        self.assertEqual(before,self.snapshot())

    def test_failure_at_first_middle_and_last_write_rolls_back_exactly(self):
        for at in [1,12,10000]:
            before=self.snapshot();p=self.plan(self.available)
            count=len(mod.changed_records(p));at=min(at,count)
            with self.assertRaises(RuntimeError):mod.apply(p,PACKAGE,fail_after=at)
            self.assertEqual(before,self.snapshot())

    def test_overlay_save_failure_rolls_back_exactly(self):
        before=self.snapshot();oldrun=self.host.run;failed=False
        def run(args):
            nonlocal failed
            if args==['batocera-save-overlay'] and not failed:
                failed=True;raise RuntimeError('Simulated overlay failure')
            oldrun(args)
        self.host.run=run
        with self.assertRaises(RuntimeError):mod.apply(self.plan(self.available),PACKAGE)
        self.assertEqual(before,self.snapshot())

    def test_failed_uninstall_restores_installed_state(self):
        backup=mod.apply(self.plan(self.available),PACKAGE)
        installed=self.snapshot();oldrun=self.host.run;failed=False
        def run(args):
            nonlocal failed
            if args==['batocera-save-overlay'] and not failed:
                failed=True;raise RuntimeError('Simulated uninstall overlay failure')
            oldrun(args)
        self.host.run=run
        with self.assertRaises(RuntimeError):mod.uninstall(self.host,backup)
        self.assertEqual(installed,self.snapshot())

    def test_uninstall_restores_all_original_files(self):
        before=self.snapshot();backup=mod.apply(self.plan(self.available),PACKAGE)
        mod.uninstall(self.host,backup)
        self.assertEqual(before,self.snapshot())

    def test_uninstall_preserves_unrelated_later_settings(self):
        backup=mod.apply(self.plan(self.available),PACKAGE)
        conf=self.host.path(mod.CONF).read_text()
        conf=mod.ini_set(conf,'audio.volume','61')
        conf=mod.ini_set(conf,'system.services',mod.ini_value(conf,'system.services')+' later_service')
        self.put(mod.CONF,conf+'owner.new.setting=yes\n')
        mod.uninstall(self.host,backup)
        restored=self.host.path(mod.CONF).read_text()
        self.assertEqual(mod.ini_value(restored,'audio.volume'),'61')
        self.assertEqual(mod.ini_value(restored,'owner.new.setting'),'yes')
        self.assertEqual(set(mod.ini_value(restored,'system.services').split()),{'other_service','later_service'})

    def test_newer_bundle_must_be_restored_first(self):
        first=mod.apply(self.plan({'theme'}),PACKAGE)
        newer=mod.apply(self.plan({'theme','early-led','skip'}),PACKAGE)
        before=self.snapshot()
        with self.assertRaises(ValueError):mod.uninstall(self.host,first)
        self.assertEqual(before,self.snapshot())
        mod.uninstall(self.host,newer);mod.uninstall(self.host,first)

    def test_later_managed_file_edit_stops_uninstall_before_any_change(self):
        backup=mod.apply(self.plan(self.available),PACKAGE)
        target=mod.CARBON+'/retrogrzmot-black.xml'
        self.put(target,self.host.path(target).read_text()+'\n<!-- owner change -->\n')
        before=self.snapshot()
        with self.assertRaises(ValueError):mod.uninstall(self.host,backup)
        self.assertEqual(before,self.snapshot())

    def test_hardware_conflicts_are_rejected(self):
        if 'shim' not in self.available:self.skipTest('SHIM is not part of the smaller package')
        self.put('/boot/config.txt','gpio=17=op,dh\n')
        before=self.snapshot()
        with self.assertRaises(ValueError):self.plan({'theme','shim'})
        self.assertEqual(before,self.snapshot())

    def test_unrelated_service_is_not_overwritten(self):
        if 'led' not in self.available:self.skipTest('LED service is not part of the smaller package')
        self.put('/userdata/system/services/retrogrzmot_led','#!/bin/bash\necho different-program\n')
        before=self.snapshot()
        with self.assertRaises(ValueError):self.plan({'theme','led'})
        self.assertEqual(before,self.snapshot())

    def test_preexisting_oled_language_is_retained(self):
        if 'oled' not in self.available:self.skipTest('OLED is not part of the smaller package')
        self.put('/userdata/system/retrogrzmot/language.txt','en\n')
        mod.apply(self.plan({'theme','oled'}),PACKAGE)
        self.assertEqual(self.host.path('/userdata/system/retrogrzmot/language.txt').read_text(),'en\n')
        self.assertEqual(self.host.path('/boot/retrogrzmot-early/splash.bin').read_bytes(),
                         (PACKAGE/'payload/oled/early/splash-en.bin').read_bytes())

if __name__=='__main__':unittest.main(verbosity=2)
