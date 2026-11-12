#!/usr/bin/env python3
"""Keep an XWayland note toolbar reachable while its body passes input through."""
import ctypes as C
import json
import select
import sys

class Rectangle(C.Structure):
    _fields_ = [('x', C.c_short), ('y', C.c_short),
                ('width', C.c_ushort), ('height', C.c_ushort)]

x = C.CDLL('libX11.so.6')
s = C.CDLL('libXext.so.6')
x.XOpenDisplay.argtypes = [C.c_char_p]
x.XOpenDisplay.restype = C.c_void_p
x.XGetGeometry.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_ulong),
                          C.POINTER(C.c_int), C.POINTER(C.c_int),
                          C.POINTER(C.c_uint), C.POINTER(C.c_uint),
                          C.POINTER(C.c_uint), C.POINTER(C.c_uint)]
x.XSync.argtypes = [C.c_void_p, C.c_int]
x.XCloseDisplay.argtypes = [C.c_void_p]
s.XShapeCombineRectangles.argtypes = [C.c_void_p, C.c_ulong, C.c_int,
    C.c_int, C.c_int, C.POINTER(Rectangle), C.c_int, C.c_int, C.c_int]
s.XShapeCombineMask.argtypes = [C.c_void_p, C.c_ulong, C.c_int,
                                C.c_int, C.c_int, C.c_ulong, C.c_int]
display = x.XOpenDisplay(None)
if not display:
    raise SystemExit('X display unavailable')
window = int(sys.argv[1])
active = False
previous = None
try:
    while True:
        readable, _, _ = select.select([sys.stdin], [], [], 0.1)
        if readable:
            line = sys.stdin.readline()
            if not line:
                break
            active = bool(json.loads(line)['active'])
            previous = None
        if not active:
            if previous != 'full':
                s.XShapeCombineMask(display, window, 2, 0, 0, 0, 0)
                x.XSync(display, 0)
                previous = 'full'
            continue
        root = C.c_ulong()
        px, py = C.c_int(), C.c_int()
        width, height, border, depth = [C.c_uint() for _ in range(4)]
        if not x.XGetGeometry(display, window, C.byref(root), C.byref(px),
                C.byref(py), C.byref(width), C.byref(height),
                C.byref(border), C.byref(depth)):
            break
        size = (width.value, height.value)
        if size == previous:
            continue
        # Toolbar and resize edges stay interactive; only the body passes clicks.
        w, h = size
        rectangles = (Rectangle * 4)(Rectangle(0, 0, w, 30),
            Rectangle(0, 0, 6, h), Rectangle(max(0, w-6), 0, 6, h),
            Rectangle(0, max(0, h-6), w, 6))
        s.XShapeCombineRectangles(display, window, 2, 0, 0, rectangles, 4, 0, 0)
        x.XSync(display, 0)
        previous = size
finally:
    s.XShapeCombineMask(display, window, 2, 0, 0, 0, 0)
    x.XSync(display, 0)
    x.XCloseDisplay(display)
