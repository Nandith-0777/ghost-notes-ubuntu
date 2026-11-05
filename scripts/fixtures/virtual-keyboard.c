#define _GNU_SOURCE
#include "virtual-keyboard.h"
#include <wayland-client.h>
#include <xkbcommon/xkbcommon.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
static struct zwp_virtual_keyboard_manager_v1 *manager;
static struct wl_seat *seat;
static void global(void *d,struct wl_registry*r,uint32_t name,const char*iface,uint32_t version){
 if(!strcmp(iface,zwp_virtual_keyboard_manager_v1_interface.name))manager=wl_registry_bind(r,name,&zwp_virtual_keyboard_manager_v1_interface,1);
 if(!strcmp(iface,wl_seat_interface.name))seat=wl_registry_bind(r,name,&wl_seat_interface,1);
}
static void removed(void*d,struct wl_registry*r,uint32_t name){}
static const struct wl_registry_listener listener={global,removed};
int main(int argc,char**argv){
 if(argc!=2 && argc!=3)return 2;
 struct wl_display*d=wl_display_connect(NULL);if(!d)return 3;
 struct wl_registry*r=wl_display_get_registry(d);wl_registry_add_listener(r,&listener,NULL);wl_display_roundtrip(d);
 if(!manager||!seat)return 4;
 struct xkb_context*ctx=xkb_context_new(0);struct xkb_rule_names names={.layout="us"};
 struct xkb_keymap*map=xkb_keymap_new_from_names(ctx,&names,0);
 char*text=xkb_keymap_get_as_string(map,XKB_KEYMAP_FORMAT_TEXT_V1);size_t size=strlen(text)+1;
 int fd=memfd_create("ghost-notes-keyboard-test",MFD_CLOEXEC);if(fd<0||write(fd,text,size)!=size)return 5;
 struct zwp_virtual_keyboard_v1*k=zwp_virtual_keyboard_manager_v1_create_virtual_keyboard(manager,seat);
 zwp_virtual_keyboard_v1_keymap(k,WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1,fd,size);wl_display_roundtrip(d);
 uint32_t mods=(1u<<xkb_keymap_mod_get_index(map,XKB_MOD_NAME_CTRL))|(1u<<xkb_keymap_mod_get_index(map,XKB_MOD_NAME_ALT))|(1u<<xkb_keymap_mod_get_index(map,XKB_MOD_NAME_SHIFT));
 if(argc==3)mods=(uint32_t)atoi(argv[2]);
 zwp_virtual_keyboard_v1_modifiers(k,mods,0,0,0);wl_display_roundtrip(d);
 zwp_virtual_keyboard_v1_key(k,1,atoi(argv[1]),WL_KEYBOARD_KEY_STATE_PRESSED);wl_display_roundtrip(d);usleep(100000);
 zwp_virtual_keyboard_v1_key(k,2,atoi(argv[1]),WL_KEYBOARD_KEY_STATE_RELEASED);zwp_virtual_keyboard_v1_modifiers(k,0,0,0,0);wl_display_roundtrip(d);usleep(100000);
 zwp_virtual_keyboard_v1_destroy(k);wl_display_flush(d);wl_display_disconnect(d);close(fd);free(text);xkb_keymap_unref(map);xkb_context_unref(ctx);return 0;
}
