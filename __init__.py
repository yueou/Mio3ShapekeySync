import bpy
from bpy.types import Panel, PropertyGroup, PointerProperty, UIList, Collection, Object
from bpy.props import PointerProperty
import time
import _thread
import traceback

bl_info = {
    "name": "Mio3 ShapeKeySync",
    "author": "mio3io",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "warning": "",
    "location": "View3D > Sidebar",
    "description": "Synchronize shape keys with the same name in the certain collection.",
    "category": "Object",
}


class MESH_UL_Mio3sksync(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        obj = active_data
        key_block = item

        split = layout.split(factor=0.66, align=False)
        split.prop(key_block, "name", text="",
                   emboss=False, icon_value=icon)
        row = split.row(align=True)
        row.emboss = 'NONE'

        if key_block.mute or (obj.mode == 'EDIT' and not (obj.use_shape_key_edit_mode and obj.type == 'MESH')):
            row.active = False
        if not item.id_data.use_relative:
            row.prop(key_block, "frame", text="")
        elif index > 0:
            row.prop(key_block, "value", text="")
        else:
            row.label(text="")


class VIEW3D_PT_Mio3sksync(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"
    # bl_context = "objectmode"
    bl_label = "Mio3 ShapeKey Sync"

    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type in {'MESH', 'CURVE', 'SURFACE', 'LATTICE', 'SURFACE'})

    def draw(self, context):
        global SHAPEKEY_SYNC_LIST
        global SHAPEKEY_SYNC_VALUE

        obj = context.object

        layout = self.layout
        row = layout.row()
        row.label(text="Sync Collection")
        
        if (context.object.data.shape_keys):

            row.prop(context.object.mio3sksync, "syncs", text="")

            collection_keys = []

            # コレクション設定済み
            if (context.object.mio3sksync.syncs):
                dat = context.object.data
                layout.template_list("MESH_UL_Mio3sksync", "", context.object.data.shape_keys,
                                    "key_blocks", context.object, "active_shape_key_index", rows=3)

                for cobj in context.object.mio3sksync.syncs.objects:
                    if (hasattr(cobj.data, "shape_keys") and cobj.active_shape_key is not None):

                        for ckey in cobj.data.shape_keys.key_blocks:
                            collection_keys.append(ckey.name)
                            if (cobj != context.object):
                                if (ckey.name in dat.shape_keys.key_blocks and ckey.value != dat.shape_keys.key_blocks[ckey.name].value):
                                    #ckey.value = dat.shape_keys.key_blocks[ckey.name].value
                                    SHAPEKEY_SYNC_VALUE = dat.shape_keys.key_blocks[ckey.name].value
                                    SHAPEKEY_SYNC_LIST.append(ckey) 

            row = layout.row()
            row.label(text="Local:" + str(len(context.object.data.shape_keys.key_blocks)))
            row.label(text="Collection:" + str(len(list(set(collection_keys)))))


class MIO3SKSYNC_Props(PropertyGroup):
    syncs: PointerProperty(name=bpy.app.translations.pgettext("shapekey sync collection"),
                           type=Collection)


classes = [
    MIO3SKSYNC_Props,
    MESH_UL_Mio3sksync,
    VIEW3D_PT_Mio3sksync
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    Object.mio3sksync = PointerProperty(type=MIO3SKSYNC_Props)

    try:
        _thread.start_new_thread( thread_sync_shapekey, ("Thread-ShapekeySync",0.1) )
    except:
        print ("Error: Can't create Thread-hapekeySync")
        traceback.print_exc()


def unregister():
    global THREAD_STOP
    global SHAPEKEY_SYNC_LIST
    
    del Object.mio3sksync
    for c in classes:
        bpy.utils.unregister_class(c)

    THREAD_STOP = True
    SHAPEKEY_SYNC_LIST.clear()


SHAPEKEY_SYNC_LIST = []
SHAPEKEY_SYNC_VALUE = 0
THREAD_STOP = False

def thread_sync_shapekey(threadName, delay):
    print ("Thread-ShapekeySync Started")
    while not THREAD_STOP:

        time.sleep(delay)
        if len(SHAPEKEY_SYNC_LIST) > 0:
            try:
                sync_shapekey()
                SHAPEKEY_SYNC_LIST.clear()
            except:
                print ("Error: Thread Conflict")
            
    print ("Thread-ShapekeySync Stoped")

def sync_shapekey():
    for shapekey in SHAPEKEY_SYNC_LIST: 
        shapekey.value = SHAPEKEY_SYNC_VALUE

if __name__ == "__main__":
    register()
