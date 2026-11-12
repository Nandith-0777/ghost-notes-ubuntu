#!/usr/bin/env python3
from pathlib import Path
import json,os,subprocess,time
home=Path.home();assert home.name=='ghostdev'
root=home/'ghost-notes-gnome';env=os.environ.copy();env['XDG_RUNTIME_DIR']='/run/user/'+str(os.getuid());env['DBUS_SESSION_BUS_ADDRESS']='unix:path='+env['XDG_RUNTIME_DIR']+'/bus'
r=subprocess.run(['systemctl','--user','show-environment'],env=env,text=True,capture_output=True,check=True)
env.update(dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line));env.pop('ELECTRON_RUN_AS_NODE',None)
electron=home/'ghost-notes-runtime/node_modules/electron/dist/electron'
with (root/'fixture.log').open('ab') as log:
 fixture=subprocess.Popen([str(electron),str(root/'public-fixture.cjs'),'--ozone-platform=x11','--class=ghost-notes-public-fixture','--remote-debugging-port=9343'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
time.sleep(2)
profile=root/'notes-profile';profile.mkdir(exist_ok=True)
code="const {NoteStore}=require("+json.dumps(str(home/'ghost-notes/store.js'))+");const s=new NoteStore("+json.dumps(str(profile))+");if(!s.all().length)s.create({text:'PRIVATE CAPTURE TEST NOTE',x:400,y:300,width:360,height:220,color:'yellow',opacity:1,visible:true,pinned:true,shareVisible:false});const n=s.all().find(n=>n.text==='PRIVATE CAPTURE TEST NOTE');if(!n)throw Error('Unexpected fixture profile');s.update(n.id,{visible:true,shareVisible:false,x:400,y:300,width:360,height:220});s.flush();"
subprocess.run([str(home/'.local/bin/node'),'-e',code],env=env,check=True)
env['GHOST_NOTES_DATA_DIR']=str(profile)
with (root/'note.log').open('ab') as log:
 note=subprocess.Popen([str(electron),str(home/'ghost-notes'),'--ozone-platform=x11','--class=com.invisiblenotes.app','--password-store=basic','--remote-debugging-port=9342'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
(root/'test-processes.json').write_text(json.dumps({'fixture':fixture.pid,'note':note.pid},indent=2)+'\n')
print('Started only public capture fixture and isolated synthetic-note profile.')
