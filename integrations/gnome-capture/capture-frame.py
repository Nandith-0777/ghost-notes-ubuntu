#!/usr/bin/env python3
"""Capture one real Mutter/PipeWire monitor frame in the dedicated test VM."""
from pathlib import Path
import argparse,json,os,sys
import gi
gi.require_version('Gst','1.0');gi.require_version('GdkPixbuf','2.0')
from gi.repository import Gio,GLib,Gst,GdkPixbuf
parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);parser.add_argument('--region',nargs=4,type=int);args=parser.parse_args()
assert Path.home().name=='ghostdev','Use only the isolated development VM'
assert str(args.output.resolve()).startswith(str(Path.home()/'ghost-notes-gnome/validation')+'/'),'Use the test evidence directory'
os.environ.setdefault('XDG_RUNTIME_DIR','/run/user/'+str(os.getuid()))
os.environ.setdefault('DBUS_SESSION_BUS_ADDRESS','unix:path='+os.environ['XDG_RUNTIME_DIR']+'/bus')
Gst.init(None);bus=Gio.bus_get_sync(Gio.BusType.SESSION,None);name='org.gnome.Mutter.ScreenCast'
def call(path,interface,method,params=None):
 return bus.call_sync(name,path,interface,method,params,None,Gio.DBusCallFlags.NONE,10000,None).unpack()
state=bus.call_sync('org.gnome.Mutter.DisplayConfig','/org/gnome/Mutter/DisplayConfig','org.gnome.Mutter.DisplayConfig','GetCurrentState',None,None,Gio.DBusCallFlags.NONE,10000,None).unpack()
connector=state[1][0][0][0]
session=call('/org/gnome/Mutter/ScreenCast',name,'CreateSession',GLib.Variant('(a{sv})',({},)))[0]
if args.region:
 stream=call(session,name+'.Session','RecordArea',GLib.Variant('(iiiia{sv})',(*args.region,{'cursor-mode':GLib.Variant('u',0)})))[0]
else:
 stream=call(session,name+'.Session','RecordMonitor',GLib.Variant('(sa{sv})',(connector,{'cursor-mode':GLib.Variant('u',0)})))[0]
loop=GLib.MainLoop();pipeline=None;error=None;report=None

def stop_error(message):
 global error
 error=message;loop.quit();return GLib.SOURCE_REMOVE

def poll_sample(sink):
 global report
 sample=sink.emit('try-pull-sample',0)
 if sample is None:return GLib.SOURCE_CONTINUE
 caps=sample.get_caps();layout=caps.get_structure(0);width=layout.get_value('width');height=layout.get_value('height')
 buffer=sample.get_buffer();success,mapping=buffer.map(Gst.MapFlags.READ)
 if not success:return stop_error('Could not map the PipeWire frame')
 try:
  data=bytes(mapping.data);stride=len(data)//height
  pixbuf=GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(data),GdkPixbuf.Colorspace.RGB,True,8,width,height,stride)
  args.output.parent.mkdir(parents=True,exist_ok=True);pixbuf.savev(str(args.output),'png',[],[])
 finally:buffer.unmap(mapping)
 report={'width':width,'height':height,'connector':connector,'caps':caps.to_string(),'file':str(args.output)}
 loop.quit();return GLib.SOURCE_REMOVE

def added(_bus,_sender,_path,_interface,_signal,parameters):
 global pipeline
 node=parameters.unpack()[0]
 pipeline=Gst.parse_launch(f'pipewiresrc path={node} do-timestamp=true ! videoconvert ! video/x-raw,format=RGBA ! appsink name=frame sync=false max-buffers=1 drop=true')
 sink=pipeline.get_by_name('frame');messages=pipeline.get_bus();messages.add_signal_watch()
 def message(_bus,message):
  if message.type==Gst.MessageType.ERROR:
   err,debug=message.parse_error();stop_error(str(err)+' '+str(debug))
 messages.connect('message',message)
 pipeline.set_state(Gst.State.PLAYING);GLib.timeout_add(25,poll_sample,sink)
subscription=bus.signal_subscribe(name,name+'.Stream','PipeWireStreamAdded',stream,None,Gio.DBusSignalFlags.NONE,added)
try:
 call(session,name+'.Session','Start');GLib.timeout_add_seconds(20,stop_error,'Timed out waiting for a captured frame');loop.run()
 if error:raise RuntimeError(error)
 assert report is not None
 print(json.dumps(report))
finally:
 if pipeline:pipeline.set_state(Gst.State.NULL)
 bus.signal_unsubscribe(subscription)
 try:call(session,name+'.Session','Stop')
 except GLib.Error:pass
