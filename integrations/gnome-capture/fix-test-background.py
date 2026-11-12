#!/usr/bin/env python3
"""Minimize app managers so the synthetic note has one stable public background."""
from pathlib import Path
import ctypes,json,os,re,subprocess
assert Path.home().name=='ghostdev'
env=os.environ.copy();env['XDG_RUNTIME_DIR']='/run/user/'+str(os.getuid());env['DBUS_SESSION_BUS_ADDRESS']='unix:path='+env['XDG_RUNTIME_DIR']+'/bus'
r=subprocess.run(['systemctl','--user','show-environment'],env=env,text=True,capture_output=True,check=True)
env.update(dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line));os.environ.update(env)
listing=subprocess.check_output(['xprop','-root','_NET_CLIENT_LIST'],env=env,text=True)
lib=ctypes.CDLL('libX11.so.6');lib.XOpenDisplay.argtypes=[ctypes.c_char_p];lib.XOpenDisplay.restype=ctypes.c_void_p
lib.XDefaultScreen.argtypes=[ctypes.c_void_p];lib.XDefaultScreen.restype=ctypes.c_int
lib.XIconifyWindow.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int]
lib.XSync.argtypes=[ctypes.c_void_p,ctypes.c_int];lib.XCloseDisplay.argtypes=[ctypes.c_void_p]
display=lib.XOpenDisplay(None);assert display
changed=[]
try:
 for window in re.findall(r'0x[0-9a-fA-F]+',listing):
  props=subprocess.check_output(['xprop','-id',window,'WM_CLASS','_NET_WM_NAME','_NET_WM_STATE'],env=env,text=True)
  if '"com.invisiblenotes.app"' in props and re.search(r'_NET_WM_NAME\([^)]*\) = "Ghost Notes"\s*$',props,re.M) and '_NET_WM_STATE_HIDDEN' not in props:
   lib.XIconifyWindow(display,int(window,16),lib.XDefaultScreen(display));changed.append(window)
 lib.XSync(display,0)
finally:lib.XCloseDisplay(display)
(Path.home()/'ghost-notes-gnome/minimized-managers.json').write_text(json.dumps(changed)+'\n')
print('Minimized app managers for a stable capture comparison:',len(changed))
