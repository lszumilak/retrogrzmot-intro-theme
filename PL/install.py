#!/usr/bin/env python3
"""RETROGRZMOT bundle installer: one precomputed plan and recoverable transaction."""
import argparse
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

BACKUPS='/userdata/system/retrogrzmot-bundle-backups'
STATE='/userdata/system/retrogrzmot-bundle-state.json'
CONF='/userdata/system/batocera.conf'
ES='/userdata/system/configs/emulationstation/es_settings.cfg'
CARBON='/usr/share/emulationstation/themes/es-theme-carbon'
HOOK='/boot/boot-custom.sh'
BEGIN='# BEGIN RETROGRZMOT BUNDLE EARLY'
END='# END RETROGRZMOT BUNDLE EARLY'
MODULES={'theme','skip','skip-usb','early-led','oled','led','exit','shim'}
SENSITIVE={'early-led','oled','led','exit','shim','skip'}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def ini_value(text,key):
    found=re.findall(r'^[ \t]*'+re.escape(key)+r'[ \t]*=([^\r\n]*)$',text,re.M)
    if len(found)>1:
        raise ValueError('Duplicate active setting: '+key)
    return found[0].strip() if found else None

def ini_set(text,key,value):
    ini_value(text,key)
    pattern=re.compile(r'^[ \t]*'+re.escape(key)+r'[ \t]*=[^\r\n]*(?:\r?\n|$)',re.M)
    if value is None:
        return pattern.sub('',text)
    line=key+'='+value+'\n'
    if pattern.search(text): return pattern.sub(lambda _:line,text)
    return text.rstrip('\r\n')+'\n'+line

def theme_setting(data,value):
    tree=ET.fromstring(data)
    found=tree.findall("string[@name='ThemeSet']")
    if len(found)>1: raise ValueError('Duplicate ThemeSet')
    old=found[0].get('value') if found else None
    if value is None:
        if found: tree.remove(found[0])
    elif found: found[0].set('value',value)
    else: ET.SubElement(tree,'string',name='ThemeSet',value=value)
    return ET.tostring(tree,encoding='utf8',xml_declaration=True)+b'\n',old

def boot_patch(text,known):
    block=BEGIN+'\nbash /boot/retrogrzmot-early/early_start.sh "$1"\n'+END+'\n'
    legacy='RETROGRZMOT EARLY BOOT v1' in text
    if legacy:
        if sha(text.encode()) not in known:
            raise ValueError('An edited legacy RETROGRZMOT boot hook needs manual review.')
        return '#!/bin/bash\n'+block
    if BEGIN in text or END in text:
        if text.count(BEGIN)!=1 or text.count(END)!=1:
            raise ValueError('Ambiguous early boot markers')
        pattern=re.compile(re.escape(BEGIN)+r'.*?'+re.escape(END)+r'\n?',re.S)
        return pattern.sub(lambda _:block,text)
    if text.startswith('#!'):
        head,sep,rest=text.partition('\n')
        return head+'\n'+block+rest
    return '#!/bin/bash\n'+block+text

def skip_patch(text,usb_only):
    command='/usr/bin/python3 -u /userdata/system/retrogrzmot-intro/skip_intro.py'
    suffix=' --usb-only' if usb_only else ''
    invocation=command+suffix+' >>/tmp/retrogrzmot-splash-skip.log 2>&1 </dev/null &'
    if command in text:
        if text.count(command)!=1 or text.count('--input-ipc-server=/tmp/retrogrzmot-splash.sock')!=2:
            raise ValueError('An unknown splash patch is installed.')
        return re.sub(re.escape(command)+r'[^\n]*',lambda _:invocation,text)
    anchor='--really-quiet --no-config '
    end='    fi\n}\n\ncase "$1" in'
    if text.count(anchor)!=2 or text.count(end)!=1:
        raise ValueError('S28splash differs from the tested Batocera 43.1 script.')
    text=text.replace(anchor,anchor+'--input-ipc-server=/tmp/retrogrzmot-splash.sock ')
    return text.replace(end,'    fi\n    '+invocation+'\n}\n\ncase "$1" in')

def hardware_config(text,oled,shim):
    wanted=[]
    if oled: wanted.append(('dtparam=i2c_arm=', 'dtparam=i2c_arm=on'))
    if shim:
        wanted.extend([('gpio=17=', 'gpio=17=ip,pu'),
                       ('dtoverlay=gpio-poweroff', 'dtoverlay=gpio-poweroff,gpiopin=4,active_low=1,input=1')])
    section='all'; seen={prefix:[] for prefix,_ in wanted}
    for line in text.splitlines():
        clean=line.strip()
        if clean.startswith('[') and clean.endswith(']'): section=clean[1:-1]
        if clean.startswith('#'): continue
        for prefix,_ in wanted:
            if clean.startswith(prefix): seen[prefix].append((clean,section))
        if shim and clean.startswith('gpio=4='):
            raise ValueError('GPIO4 already has a firmware assignment; review before SHIM setup.')
    add=[]
    for prefix,expected in wanted:
        entries=seen[prefix]
        if entries and entries!=[(expected,'all')]:
            raise ValueError('Conflicting or conditional boot setting: '+prefix)
        if not entries: add.append(expected)
    if add: text=text.rstrip()+'\n\n[all]\n# RETROGRZMOT selected hardware\n'+'\n'.join(add)+'\n'
    return text

class Host:
    def __init__(self,root='/',live=True):
        self.root=Path(root).resolve(); self.live=live; self.commands=[]
        if live and self.root!=Path('/'):
            raise ValueError('Live operations require the real Linux root.')
    def path(self,name):
        if not name.startswith('/') or '..' in Path(name).parts: raise ValueError('Invalid target')
        p=self.root/name.lstrip('/')
        if self.root!=Path('/') and not p.resolve().is_relative_to(self.root):
            raise ValueError('Target escapes isolated root')
        if p.is_symlink(): raise ValueError('Symlink target needs manual review: '+name)
        return p
    def run(self,args):
        self.commands.append(args)
        if self.live: subprocess.run(args,check=True)
    def writable_boot(self): self.run(['mount','-o','remount,rw','/boot'])
    def sync(self):
        if self.live: os.sync()
    def boot_was_ro(self):
        if not self.live: return True
        for line in Path('/proc/mounts').read_text().splitlines():
            fields=line.split()
            if len(fields)>3 and fields[1]=='/boot': return 'ro' in fields[3].split(',')
        raise ValueError('/boot is not mounted')

class Plan:
    def __init__(self,host): self.host=host; self.files={}; self.metadata={}; self.modules=set()
    def put(self,target,data,mode=0o644,kind=None):
        if isinstance(data,str): data=data.encode()
        self.host.path(target)
        if target in self.files and self.files[target][0]!=data: raise ValueError('Two components disagree: '+target)
        self.files[target]=(data,mode)
        if kind: self.metadata[target]=kind
    def delete(self,target): self.files[target]=(None,None)
    def read(self,target,default=None):
        if target in self.files:
            data=self.files[target][0]
            return data.decode() if data is not None else default
        p=self.host.path(target)
        return p.read_text(encoding='utf8') if p.exists() else default
    def ini(self,target,changes):
        old=self.read(target)
        if old is None: raise ValueError('Missing configuration: '+target)
        meta={'ini':{}}
        new=old
        for key,value in changes.items():
            meta['ini'][key]={'before':ini_value(old,key),'after':value}
            new=ini_set(new,key,value)
        self.put(target,new,kind=meta)

def resolve_modules(requested,available):
    selected=set(requested)|{'theme'}
    if not selected<=set(available): raise ValueError('Unsupported modules: '+','.join(sorted(selected-set(available))))
    if 'exit' in selected: selected.add('skip')
    if 'skip' in selected: selected.discard('skip-usb')
    return selected

def build_plan(source,host,requested):
    source=Path(source); package=json.loads((source/'package.json').read_text())
    modules=resolve_modules(requested,package['available_modules'])
    plan=Plan(host); plan.modules=modules
    def asset(rel): return (source/'payload'/rel).read_bytes()
    def require_owned(target,signature):
        existing=plan.read(target)
        if existing is not None and signature not in existing:
            raise ValueError('An unrelated file occupies a RETROGRZMOT target: '+target)
    theme=plan.read(CARBON+'/theme.xml')
    if theme is None: raise ValueError('Carbon theme is missing.')
    ET.fromstring(theme)
    if './retrogrzmot-black.xml' not in theme:
        if theme.count('</theme>')!=1: raise ValueError('Unexpected Carbon theme structure')
        theme=theme.replace('</theme>','  <include>./retrogrzmot-black.xml</include>\n</theme>')
    plan.put(CARBON+'/theme.xml',theme)
    for name in ['retrogrzmot-black.xml','splash.xml']:
        ET.fromstring(asset('theme/'+name)); plan.put(CARBON+'/'+name,asset('theme/'+name))
    for p in (source/'payload/theme/assets').iterdir():
        if p.is_file(): plan.put('/userdata/system/retrogrzmot-theme/assets/'+p.name,p.read_bytes())
    for target,rel in [('/usr/share/batocera/splash/boot-logo.png','boot-16x9.png'),
                       ('/usr/share/batocera/splash/boot-logo-4x3.png','boot-4x3.png'),
                       ('/usr/share/emulationstation/resources/logo.png','loading.png')]:
        plan.put(target,asset('theme/assets/'+rel))
    plan.put('/usr/share/emulationstation/resources/splash.xml',asset('theme/splash.xml'))
    es=host.path(ES).read_bytes(); new,old=theme_setting(es,'es-theme-carbon')
    plan.put(ES,new,kind={'theme_before':old,'theme_after':'es-theme-carbon'})
    conf=plan.read(CONF)
    if conf is None: raise ValueError('batocera.conf is missing.')
    services=(ini_value(conf,'system.services') or '').split()
    changes={'splash.screen.enabled':'1','splash.screen.sound':'1','splash.screen.length':'auto'}
    plan.ini('/boot/batocera-boot.conf',{'splash.screen.enabled':'1'})
    splashdir=host.path('/userdata/splash')
    for p in splashdir.iterdir() if splashdir.exists() else []:
        if p.is_file() and p.suffix.lower()=='.mp4' and p.name!='RETROGRZMOT_community.mp4':
            plan.delete('/userdata/splash/'+p.name)
    plan.put('/userdata/splash/RETROGRZMOT_community.mp4',asset('intro.mp4'))
    if modules&{'skip','skip-usb'}:
        script=plan.read('/etc/init.d/S28splash')
        if script is None: raise ValueError('S28splash is missing.')
        plan.put('/etc/init.d/S28splash',skip_patch(script,'skip' not in modules),0o755)
        plan.put('/userdata/system/retrogrzmot-intro/skip_intro.py',asset('skip_intro.py'))
    early=bool(modules&{'early-led','oled'})
    if early:
        before=plan.read(HOOK,'')
        plan.put(HOOK,boot_patch(before,package['known_legacy_boot_sha256']),0o755)
        plan.put('/boot/retrogrzmot-early/early_start.sh',asset('early_start.sh'),0o755)
        if 'RETROGRZMOT EARLY BOOT v1' in before and host.path('/boot/retrogrzmot-early/splash.py').exists():
            plan.put('/boot/retrogrzmot-early/enable-oled','1\n')
        if 'early-led' in modules:
            plan.put('/boot/retrogrzmot-early/early_led.py',asset('early_led.py'))
            plan.put('/boot/retrogrzmot-early/enable-led','1\n')
    if 'oled' in modules:
        require_owned('/userdata/system/services/retrogrzmot_oled','/userdata/system/retrogrzmot/oled.py')
        oledroot='/userdata/system/retrogrzmot'
        for rel in ['oled.py','fonts/DejaVuSans.ttf','fonts/LICENSE-DejaVu.txt']:
            plan.put(oledroot+'/'+rel,asset('oled/'+rel))
        language=plan.read(oledroot+'/language.txt')
        if language is None:
            language=package['language']; plan.put(oledroot+'/language.txt',language+'\n')
        language=language.strip()
        if language not in ('pl','en'): raise ValueError('Existing OLED language.txt must contain pl or en.')
        frame='splash-en.bin' if language=='en' else 'splash.bin'
        if len(asset('oled/early/'+frame))!=1024: raise ValueError('Invalid early OLED frame')
        plan.put('/boot/retrogrzmot-early/splash.py',asset('oled/early/splash.py'))
        plan.put('/boot/retrogrzmot-early/splash.bin',asset('oled/early/'+frame))
        plan.put('/boot/retrogrzmot-early/enable-oled','1\n')
        plan.put('/userdata/system/services/retrogrzmot_oled',asset('oled/retrogrzmot-oled'),0o755)
        for event in ['system-selected','game-selected','game-start','game-end','quit','shutdown','reboot']:
            require_owned('/userdata/system/configs/emulationstation/scripts/'+event+'/retrogrzmot-oled.sh','/userdata/system/retrogrzmot/oled.py')
            hook='#!/bin/bash\n# RETROGRZMOT OLED\npython3 /userdata/system/retrogrzmot/oled.py event "'+event+'" "$@" || true\n'
            plan.put('/userdata/system/configs/emulationstation/scripts/'+event+'/retrogrzmot-oled.sh',hook,0o755)
        if 'retrogrzmot_oled' not in services: services.append('retrogrzmot_oled')
    if 'led' in modules:
        require_owned('/userdata/system/services/retrogrzmot_led','RETROGRZMOT LED')
        require_owned('/userdata/roms/ports/Sterowanie podświetleniem RETROGRZMOTA.sh','/userdata/roms/ports/.data/retrogrzmot-lighting/panel.py')
        plan.put('/userdata/system/services/retrogrzmot_led',asset('led/retrogrzmot_led'),0o755)
        plan.put('/userdata/roms/ports/.data/retrogrzmot-lighting/panel.py',asset('led/panel.py'))
        # Keep the historical filename: updating must not create a second menu entry.
        plan.put('/userdata/roms/ports/Sterowanie podświetleniem RETROGRZMOTA.sh',asset('led/launch.sh'),0o755)
        if 'retrogrzmot_led' not in services: services.append('retrogrzmot_led')
    if 'exit' in modules:
        require_owned('/userdata/system/services/retrogrzmot_exit','/userdata/system/retrogrzmot/exit_button.py')
        plan.put('/userdata/system/retrogrzmot/exit_button.py',asset('exit/exit_button.py'))
        plan.put('/userdata/system/services/retrogrzmot_exit',asset('exit/retrogrzmot_exit'),0o755)
        if 'retrogrzmot_exit' not in services: services.append('retrogrzmot_exit')
    if 'shim' in modules:
        current=ini_value(conf,'system.power.switch')
        if current not in (None,'','ONOFFSHIM','disabled'):
            raise ValueError('A different power controller is configured; stopped.')
        changes['system.power.switch']='ONOFFSHIM'
    if modules&{'oled','shim'}:
        config=plan.read('/boot/config.txt')
        if config is None: raise ValueError('config.txt is missing.')
        plan.put('/boot/config.txt',hardware_config(config,'oled' in modules,'shim' in modules))
    if modules&{'oled','led','exit'}: changes['system.services']=' '.join(services)
    plan.ini(CONF,changes)
    oldstate=plan.read(STATE)
    state=json.loads(oldstate) if oldstate else {'installed_modules':[]}
    state['installed_modules']=sorted(set(state.get('installed_modules',[]))|modules)
    state.update({'last_package':package['profile'],'last_version':package['version'],'last_language':package['language']})
    plan.put(STATE,json.dumps(state,indent=2)+'\n')
    return plan

def prerequisite_check(host,modules):
    if not host.live: return
    if os.geteuid()!=0: raise ValueError('Run as root on Batocera.')
    if not host.path('/proc/device-tree/model').read_text().rstrip('\0').startswith('Raspberry Pi 3 Model B Plus'):
        raise ValueError('This release targets Raspberry Pi 3B+ only.')
    version=host.path('/usr/share/batocera/batocera.version').read_text().split()[0]
    if version!='43.1': raise ValueError('This release targets Batocera 43.1 only.')
    for command in ['bash','batocera-save-overlay','mount','timeout']:
        if not shutil.which(command): raise ValueError('Missing command: '+command)
    for p in Path('/proc').iterdir():
        if not p.name.isdecimal(): continue
        try:
            args=(p/'cmdline').read_bytes().split(bytes([0]))
            if any(a.rsplit(b'/',1)[-1] in (b'emulatorlauncher',b'panel.py') for a in args[:3]):
                raise ValueError('Close the game and LED panel before installing.')
        except OSError: pass
    if 'oled' in modules: importlib.import_module('PIL.ImageFont')
    if modules&{'early-led','led'}:
        driver=importlib.import_module('rpi_ws281x')
        if not callable(driver.PixelStrip._cleanup): raise ValueError('Unsupported LED driver.')
    if 'led' in modules:
        os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
        importlib.import_module('pygame._sdl2.controller')
        for font in ['DejaVuSans.ttf','DejaVuSans-Bold.ttf']:
            if not host.path('/usr/share/fonts/dejavu/'+font).exists(): raise ValueError('Missing font: '+font)
    if modules&{'skip','skip-usb'}: importlib.import_module('evdev')
    if modules&{'skip','exit','shim'}:
        gpiod=importlib.import_module('gpiod')
        conf=host.path(CONF).read_text()
        with gpiod.Chip('/dev/gpiochip0') as chip:
            lines=[26] if modules&{'skip','exit'} else []
            if 'shim' in modules: lines += [4,17]
            for number in lines:
                info=chip.get_line_info(number)
                if info.name!='GPIO'+str(number): raise ValueError('GPIO mapping differs.')
                allowed={'retrogrzmot_exit','retrogrzmot_splash'} if number==26 else (
                    {'power_ctrl','gpiomon'} if ini_value(conf,'system.power.switch')=='ONOFFSHIM' else set())
                if info.used and info.consumer not in allowed: raise ValueError('GPIO busy: '+str(number)+' '+str(info.consumer))

def validate_plan(plan):
    for target,(data,mode) in plan.files.items():
        if data is None: continue
        if target.endswith('.py'): compile(data,target,'exec')
        if target.endswith('.xml') or target.endswith('es_settings.cfg'): ET.fromstring(data)
        if mode==0o755:
            if plan.host.live: subprocess.run(['bash','-n'],input=data,check=True)

def changed_records(plan):
    result=[]
    for target,(data,mode) in plan.files.items():
        p=plan.host.path(target)
        if p.exists() and not p.is_file(): raise ValueError('Target is not a regular file: '+target)
        old=p.read_bytes() if p.exists() else None
        if old==data and (data is None or mode is None or os.name=='nt' or target.startswith('/boot/') or (p.stat().st_mode&0o777)==mode): continue
        result.append({'target':target,'before_exists':old is not None,'before_sha256':sha(old) if old is not None else None,
                       'after_sha256':sha(data) if data is not None else None,'before_mode':p.stat().st_mode&0o777 if p.exists() else None,
                       'after_mode':mode,'metadata':plan.metadata.get(target,{})})
    return result

def atomic_write(p,data,mode):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_name('.'+p.name+'.retrogrzmot-tmp')
    with temp.open('wb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    temp.chmod(mode or 0o644)
    os.replace(temp,p)

def restore_snapshot(host,backup,records):
    for record in reversed(records):
        p=host.path(record['target'])
        if record['before_exists']:
            data=(backup/record['backup']).read_bytes()
            if sha(data)!=record['before_sha256']: raise ValueError('Damaged backup')
            atomic_write(p,data,record['before_mode'])
        else: p.unlink(missing_ok=True)

def apply(plan,source,fail_after=None):
    host=plan.host; source=Path(source);records=changed_records(plan)
    if not records: return None
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup=host.path(BACKUPS+'/'+stamp);backup.mkdir(parents=True)
    for i,r in enumerate(records):
        r['backup']=str(i)+'.original'
        if r['before_exists']: shutil.copy2(host.path(r['target']),backup/r['backup'])
    shutil.copy2(source/'install.py',backup/'restore.py')
    manifest={'format':1,'package':json.loads((source/'package.json').read_text()),'status':'prepared','records':records}
    def save(): atomic_write(backup/'manifest.json',(json.dumps(manifest,indent=2)+'\n').encode(),0o600)
    save();ro=host.boot_was_ro()
    try:
        host.writable_boot();manifest['status']='installing';save()
        for i,r in enumerate(records):
            p=host.path(r['target']);data,mode=plan.files[r['target']]
            if data is None: p.unlink(missing_ok=True)
            else: atomic_write(p,data,mode)
            if (sha(p.read_bytes()) if p.exists() else None)!=r['after_sha256']: raise ValueError('Write verification failed')
            if fail_after is not None and i+1>=fail_after: raise RuntimeError('Injected installation failure')
        host.run(['batocera-save-overlay']);host.sync();manifest['status']='installed';save()
    except BaseException:
        restore_snapshot(host,backup,records)
        try: host.run(['batocera-save-overlay']);host.sync();manifest['status']='rolled-back';save()
        except Exception: manifest['status']='rollback-needs-overlay-save';save()
        raise
    finally:
        if ro: host.run(['mount','-o','remount,ro','/boot'])
    return backup

def restore_config(record,current,original):
    meta=record['metadata']
    if 'ini' in meta:
        result=current.decode();before=original.decode() if original is not None else ''
        for key,values in meta['ini'].items():
            now=ini_value(result,key)
            if now==values['after']: result=ini_set(result,key,values['before'])
            elif key=='system.services':
                old=(values['before'] or '').split();new=(values['after'] or '').split()
                added=set(new)-set(old)
                kept=[s for s in (now or '').split() if s not in added]
                for s in old:
                    if s not in kept: kept.append(s)
                result=ini_set(result,key,' '.join(kept) if kept or values['before'] is not None else None)
            elif now!=values['before']: raise ValueError('Managed setting changed since install: '+key)
        return result.encode()
    if 'theme_before' in meta:
        _,now=theme_setting(current,'es-theme-carbon')
        if now not in (meta['theme_after'],meta['theme_before']): raise ValueError('Theme changed since install; review before restoring.')
        return theme_setting(current,meta['theme_before'])[0]
    raise ValueError('File changed since installation: '+record['target'])

def uninstall(host,backup):
    backup=Path(backup).resolve()
    if backup.parent!=host.path(BACKUPS).resolve(): raise ValueError('Choose an installer-created backup directory.')
    manifest=json.loads((backup/'manifest.json').read_text())
    if manifest['status'] not in ('installed','installing','prepared','rollback-needs-overlay-save'):
        raise ValueError('This backup is not an active installation.')
    actions=[]
    for r in manifest['records']:
        if Path(r['backup']).name!=r['backup']: raise ValueError('Invalid backup filename')
        p=host.path(r['target']);current=p.read_bytes() if p.exists() else None
        original=(backup/r['backup']).read_bytes() if r['before_exists'] else None
        if original is not None and sha(original)!=r['before_sha256']: raise ValueError('Damaged backup')
        now=sha(current) if current is not None else None
        if now==r['before_sha256']: continue
        if now==r['after_sha256']: data=original
        elif current is not None and r['metadata']: data=restore_config(r,current,original)
        else: raise ValueError('A later installation or edit changed '+r['target']+'. Restore newer bundles first.')
        actions.append((r['target'],data,r['before_mode']))
    # Keep the current installed state in memory until restoration is committed.
    # A failed uninstall must not leave half of two installations on disk.
    checkpoint=[]
    for target,_,_ in actions:
        p=host.path(target)
        checkpoint.append((target,p.read_bytes() if p.exists() else None,p.stat().st_mode&0o777 if p.exists() else None))
    ro=host.boot_was_ro()
    try:
        host.writable_boot()
        for target,data,mode in reversed(actions):
            p=host.path(target)
            if data is None: p.unlink(missing_ok=True)
            else: atomic_write(p,data,mode)
        host.run(['batocera-save-overlay']);host.sync()
        manifest['status']='uninstalled'
        atomic_write(backup/'manifest.json',(json.dumps(manifest,indent=2)+'\n').encode(),0o600)
    except BaseException:
        for target,data,mode in checkpoint:
            p=host.path(target)
            if data is None: p.unlink(missing_ok=True)
            else: atomic_write(p,data,mode)
        try: host.run(['batocera-save-overlay']);host.sync()
        except Exception:
            manifest['status']='uninstall-rollback-needs-overlay-save'
            atomic_write(backup/'manifest.json',(json.dumps(manifest,indent=2)+'\n').encode(),0o600)
        raise
    finally:
        if ro: host.run(['mount','-o','remount,ro','/boot'])

def integrity(source):
    files=json.loads((source/'FILES.json').read_text())
    for name,digest in files.items():
        p=source/name
        if not p.resolve().is_relative_to(source.resolve()) or not p.is_file() or sha(p.read_bytes())!=digest:
            raise ValueError('Package incomplete or modified: '+name)

def choose(package):
    pl=package['language']=='pl';selected={'theme'}
    prompts=[('skip','Przycisk POWRÓT na GPIO26 do pomijania intro?','GPIO26 RETURN button to skip intro?'),
             ('skip-usb','Pomijanie przez START na padzie USB?','Skip with START on a USB controller?'),
             ('oled','Wyświetlacz SSD1306 OLED?','SSD1306 OLED display?'),
             ('led','Podświetlenie WS2812B i panel ustawień?','WS2812B lighting and settings panel?'),
             ('early-led','Delikatne bursztynowe logo przy starcie?','Dim amber logo at early startup?'),
             ('exit','POWRÓT na GPIO26 ma też zamykać gry?','GPIO26 RETURN should also exit games?'),
             ('shim','Podłączony OnOff SHIM PIM269 (GPIO4/17)?','Wired OnOff SHIM PIM269 (GPIO4/17)?')]
    for module,polish,english in prompts:
        if module not in package['available_modules']: continue
        if module=='skip-usb' and 'skip' in selected: continue
        answer=input((polish if pl else english)+' [y/N]: ').strip().lower()
        if answer in ('y','yes','t','tak'): selected.add(module)
    return selected

def main():
    source=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description='RETROGRZMOT: select installed hardware. No automatic reboot or service restart.')
    parser.add_argument('--modules',help='Comma-separated: theme,skip,skip-usb,early-led,oled,led,exit,shim')
    parser.add_argument('--check',action='store_true',help='Validate and show the plan without changing files')
    parser.add_argument('--uninstall',metavar='BACKUP_DIRECTORY')
    args=parser.parse_args();host=Host()
    if args.uninstall:
        if os.geteuid()!=0: raise ValueError('Run as root.')
        uninstall(host,args.uninstall);print('Restored. No reboot performed. Restart from the Batocera menu when ready.');return
    package=json.loads((source/'package.json').read_text());integrity(source)
    requested=args.modules.split(',') if args.modules else choose(package)
    modules=resolve_modules(requested,package['available_modules'])
    prerequisite_check(host,modules);plan=build_plan(source,host,modules);validate_plan(plan)
    print('Modules: '+', '.join(sorted(modules)))
    print('Changed files: '+str(len(changed_records(plan))))
    if args.check:
        print('CHECK OK. No files changed; no lights, services or reboot triggered.');return
    print('Installing selected modules; keep SSH connected. No automatic reboot.',flush=True)
    backup=apply(plan,source)
    if backup is None: print('Already installed; no changes needed.');return
    print('Installed. Backup: '+str(backup))
    print('Restore: python3 '+str(backup/'restore.py')+' --uninstall '+str(backup))
    print('Runtime services were not restarted. Restart from the Batocera menu when ready.')

if __name__=='__main__':
    try: main()
    except (ValueError,OSError,ImportError,subprocess.CalledProcessError) as exc:
        print('STOP: '+str(exc),file=sys.stderr);raise SystemExit(1)
