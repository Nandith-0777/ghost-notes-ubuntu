#!/usr/bin/env python3
from pathlib import Path
import os,subprocess,sys
home=Path.home();assert home.name=='ghostdev';assert sys.argv[1:] in [['--toggle-notes'],['--manager']]
env=os.environ.copy();env['XDG_RUNTIME_DIR']='/run/user/'+str(os.getuid());env['DBUS_SESSION_BUS_ADDRESS']='unix:path='+env['XDG_RUNTIME_DIR']+'/bus'
r=subprocess.run(['systemctl','--user','show-environment'],env=env,text=True,capture_output=True,check=True)
env.update(dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line));env.pop('ELECTRON_RUN_AS_NODE',None);env['GHOST_NOTES_DATA_DIR']=str(home/'ghost-notes-gnome/notes-profile')
subprocess.run([str(home/'ghost-notes-runtime/node_modules/electron/dist/electron'),str(home/'ghost-notes'),'--ozone-platform=x11','--class=com.invisiblenotes.app','--password-store=basic',*sys.argv[1:]],env=env,check=True)
