#!/usr/bin/env python3
"""Apply the opt-in Ghost Notes capture prototype to Mutter 46.2 source."""
from pathlib import Path
import argparse,re
p=argparse.ArgumentParser();p.add_argument('source',type=Path);args=p.parse_args();root=args.source.resolve()
assert re.search(r"version:\s*'46\.2'",(root/'meson.build').read_text()),'Only Mutter 46.2 is supported'
paths=['clutter/clutter/clutter-paint-context.h','src/compositor/meta-window-actor.c','src/backends/meta-screen-cast-monitor-stream-src.c','src/backends/meta-screen-cast-area-stream-src.c']
original={path:(root/path).read_text() for path in paths};edited=original.copy()
if all('GHOST_NOTES_CAPTURE' in text for text in original.values()):
 print('Mutter already contains the Ghost Notes prototype.');raise SystemExit(0)
def replace(path,before,after,count=1):
 text=edited[path];assert text.count(before)==count,f'Unexpected source layout: {path}: {before[:60]!r}'
 edited[path]=text.replace(before,after)
header=paths[0]
replace(header,'  CLUTTER_PAINT_FLAG_CLEAR = 1 << 2,','  CLUTTER_PAINT_FLAG_CLEAR = 1 << 2,\n  CLUTTER_PAINT_FLAG_GHOST_NOTES_CAPTURE = 1 << 3,')
actor=paths[1]
helper=r'''
/* GHOST_NOTES_CAPTURE: opt-in, capture-only filtering; physical paint is unchanged. */
typedef struct { ClutterEffect parent; } MetaGhostNotesCaptureEffect;
typedef struct { ClutterEffectClass parent; } MetaGhostNotesCaptureEffectClass;
static GType meta_ghost_notes_capture_effect_get_type (void);
G_DEFINE_TYPE (MetaGhostNotesCaptureEffect, meta_ghost_notes_capture_effect, CLUTTER_TYPE_EFFECT)

static gboolean
ghost_notes_capture_enabled (void)
{
  return g_strcmp0 (g_getenv ("GHOST_NOTES_CAPTURE_EXCLUSION"), "1") == 0;
}

static gboolean
ghost_notes_owned_window (MetaWindow *window)
{
  const char *wm_class = meta_window_get_wm_class (window);
  return g_strcmp0 (wm_class, "com.invisiblenotes.app") == 0 ||
         g_strcmp0 (wm_class, "invisible-notes") == 0;
}

static gboolean
ghost_notes_private_window (MetaWindowActor *actor)
{
  MetaWindow *window = meta_window_actor_get_meta_window (actor);
  return ghost_notes_capture_enabled () && ghost_notes_owned_window (window) &&
         g_strcmp0 (meta_window_get_title (window), "Ghost Notes Note") == 0;
}

static void
meta_ghost_notes_capture_effect_paint (ClutterEffect *effect,
                                      ClutterPaintNode *node,
                                      ClutterPaintContext *context,
                                      ClutterEffectPaintFlags flags)
{
  ClutterActor *actor = clutter_actor_meta_get_actor (CLUTTER_ACTOR_META (effect));
  if ((clutter_paint_context_get_paint_flags (context) &
       CLUTTER_PAINT_FLAG_GHOST_NOTES_CAPTURE) &&
      actor && META_IS_WINDOW_ACTOR (actor) &&
      ghost_notes_private_window (META_WINDOW_ACTOR (actor)))
    return;
  CLUTTER_EFFECT_CLASS (meta_ghost_notes_capture_effect_parent_class)->paint
    (effect, node, context, flags);
}

static void
meta_ghost_notes_capture_effect_class_init (MetaGhostNotesCaptureEffectClass *klass)
{
  CLUTTER_EFFECT_CLASS (klass)->paint = meta_ghost_notes_capture_effect_paint;
}

static void
meta_ghost_notes_capture_effect_init (MetaGhostNotesCaptureEffect *self)
{
}

'''
replace(actor,'static void\nmeta_window_actor_class_init',helper+'static void\nmeta_window_actor_class_init')
replace(actor,'  priv->compositor = window->display->compositor;','''  priv->compositor = window->display->compositor;

  /* An active effect also prevents this note from occluding the scene behind it. */
  if (ghost_notes_capture_enabled () && ghost_notes_owned_window (window))
    clutter_actor_add_effect_with_name (CLUTTER_ACTOR (self), "ghost-notes-capture",
      g_object_new (meta_ghost_notes_capture_effect_get_type (), NULL));''')
replace(actor,'  image = meta_window_actor_get_image (window_actor, bounds);','''  if (ghost_notes_private_window (window_actor))
    {
      memset (data, 0, (size_t) bounds->width * bounds->height * bpp);
      return;
    }

  image = meta_window_actor_get_image (window_actor, bounds);''')
# Only the screencast window blit uses the capture flag; local thumbnails retain content.
start=edited[actor].index('meta_window_actor_blit_to_framebuffer (')
end=edited[actor].index('\nstatic gboolean\nmeta_window_actor_has_damage',start)
section=edited[actor][start:end]
assert section.count('CLUTTER_PAINT_FLAG_NONE')==1
edited[actor]=edited[actor][:start]+section.replace('CLUTTER_PAINT_FLAG_NONE','CLUTTER_PAINT_FLAG_GHOST_NOTES_CAPTURE')+edited[actor][end:]
for path in paths[2:]:
 replace(path,'ClutterPaintFlag paint_flags = CLUTTER_PAINT_FLAG_CLEAR;',
         'ClutterPaintFlag paint_flags = CLUTTER_PAINT_FLAG_CLEAR |\n    CLUTTER_PAINT_FLAG_GHOST_NOTES_CAPTURE;',count=2)
monitor=paths[2]
replace(monitor,'  if (paint_phase == META_SCREEN_CAST_PAINT_PHASE_DETACHED)\n    goto stage_paint;','''  /* Never copy physical-display pixels into the capture while filtering is enabled. */
  if (g_strcmp0 (g_getenv ("GHOST_NOTES_CAPTURE_EXCLUSION"), "1") == 0 ||
      paint_phase == META_SCREEN_CAST_PAINT_PHASE_DETACHED)
    goto stage_paint;''')
for path,text in edited.items():
 (root/(path+'.ghostnotes-original')).write_text(original[path]);(root/path).write_text(text)
print('Applied capture filtering to CPU/GPU monitor, area, and note-window streams.')
