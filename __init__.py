# ----------------------------------------------
# Define Addon info
# ----------------------------------------------

bl_info = {
    "name": "Hedronize",
    "author": "AgAmemnno",
    "location": "View3D > Sidebar > Edit Tab / Edit Mode Context Menu",
    "version": (0, 0, 0),
    "blender": (3, 0, 0),
    "description": "Tools for hedronize.",
    "doc_url": "{BLENDER_MANUAL_URL}/addons",
    "category": "Mesh",
}
import bpy
import math
from bpy.types import (
        Operator,
        Menu,
        Panel,
        PropertyGroup,
        AddonPreferences,
        )
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty,
        )

from .develop import register_props,unregister_props,draw_develop


class VIEW3D_MT_edit_mesh_hedronize(Menu):
    bl_label = "Hedronize"
    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.hedronize_develop", text="Develop").loft = False


class VIEW3D_PT_tools_hedronize(Panel):
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Tool"
    bl_label       = "Hedronize"
    bl_options     = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout
        draw_develop(layout)

       
def menu_func(self, context):
    self.layout.menu("VIEW3D_MT_edit_mesh_hedronize")
    self.layout.separator()



panels = (
        VIEW3D_PT_tools_hedronize,
)

def update_panel(self, context):
    message = "Hedronize: Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)
        for panel in panels:
            panel.bl_category = context.preferences.addons[__name__].preferences.category
            bpy.utils.register_class(panel)
    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass


class LoopPreferences(AddonPreferences):
    bl_idname = __name__
    category: StringProperty(
            name        = "Tab Category",
            description = "Choose a name for the category of the panel",
            default = "Edit",
            update  = update_panel
            )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        col.label(text="Tab Category:")
        col.prop(self, "category", text="")

classes = (
    VIEW3D_MT_edit_mesh_hedronize,
    VIEW3D_PT_tools_hedronize,
    LoopPreferences,
)




def register():
    register_props()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.prepend(menu_func)    
    update_panel(None, bpy.context)



def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    unregister_props()
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_func)


if __name__ == "__main__":
    register()
