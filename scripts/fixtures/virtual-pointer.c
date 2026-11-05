#include "virtual-pointer.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wayland-client.h>
static struct zwlr_virtual_pointer_manager_v1 *manager;
static void global(void *data, struct wl_registry *registry, uint32_t name, const char *interface,
                   uint32_t version) {
  if (!strcmp(interface, zwlr_virtual_pointer_manager_v1_interface.name))
    manager = wl_registry_bind(registry, name, &zwlr_virtual_pointer_manager_v1_interface, 1);
}
static void removed(void *d, struct wl_registry *r, uint32_t n) {}
static const struct wl_registry_listener listener = {global, removed};
int main(int argc, char **argv) {
  if (argc != 6)
    return 2;
  struct wl_display *d = wl_display_connect(NULL);
  if (!d)
    return 3;
  struct wl_registry *r = wl_display_get_registry(d);
  wl_registry_add_listener(r, &listener, NULL);
  wl_display_roundtrip(d);
  if (!manager)
    return 4;
  struct zwlr_virtual_pointer_v1 *p = zwlr_virtual_pointer_manager_v1_create_virtual_pointer(manager, NULL);
  zwlr_virtual_pointer_v1_motion_absolute(p, 1, atoi(argv[1]), atoi(argv[2]), atoi(argv[3]), atoi(argv[4]));
  zwlr_virtual_pointer_v1_frame(p);
  wl_display_roundtrip(d);
  if (atoi(argv[5])) {
    zwlr_virtual_pointer_v1_button(p, 2, 272, WL_POINTER_BUTTON_STATE_PRESSED);
    zwlr_virtual_pointer_v1_frame(p);
    wl_display_roundtrip(d);
    zwlr_virtual_pointer_v1_button(p, 3, 272, WL_POINTER_BUTTON_STATE_RELEASED);
    zwlr_virtual_pointer_v1_frame(p);
    wl_display_roundtrip(d);
  }
  zwlr_virtual_pointer_v1_destroy(p);
  zwlr_virtual_pointer_manager_v1_destroy(manager);
  wl_registry_destroy(r);
  wl_display_flush(d);
  wl_display_disconnect(d);
  return 0;
}
