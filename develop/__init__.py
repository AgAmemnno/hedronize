import bpy
import random
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


#from .  import params        
#from .  import separate
#from .  import skels
from .develop  import ExecuteDevelop,LayoutDevelop,HedronNames
from .params  import register_props_params,unregister_props_params


def developCB(scene, context):
    lt     = bpy.context.window_manager.hedronize_develop
    names  = HedronNames()
    fam = ['Pla','Kep','Arc','Pri','Arc2','Joh','Oth'] 
    phe = names["families"][fam.index(lt.family)]["polyhedra"]
    items = []
    for p in phe:
        items.append((str(p["number"]),str(p["number"]), p["name"] ))
   
    return items


class Props_Develop(PropertyGroup):

    display: BoolProperty(
        name="Profile settings",
        description="Display settings of the Profile tool",
        default=False
        )
    family: EnumProperty(
        name="Family",
        items=( ('Pla','Pla','Platonic') ,('Kep','Kep','Kepler-Poinsot') ,
                ('Arc','Arc','Archimedean') ,('Arc2','Arc2','Archimedean Duals') ,
                ('Pri','Pri','Prisms & Anti-prisms') ,('Joh','Joh','Johnson Solids') ,
                ('Oth','Oth','Others') ,
           ),
        description="Family Selection",
        default='Pla'
        )
    type: EnumProperty(
        name="Type",
        items= developCB,
        description="Types Selection",
        )
    gtype  : EnumProperty(
        name="GenType",
        items=( ('shapekey','ShapeKey','ShapeKey') ,
                ('armature','Armature','Armature') ,
                ('cellhedron','Cellhedron','Cellhedron'),
        ),
        description="Generate Types Selection",
        )
    col1   : PointerProperty(type = bpy.types.Collection, name = "Col1")
    ob1    : PointerProperty(type = bpy.types.Object, name = "Ob1")
    seed   : IntProperty(
        name="seed",
        description="Random Seed",
        default=0,
        min=0,
        max=999999
        )


def draw_develop(layout):
    col = layout.column(align=True)
    lt = bpy.context.window_manager.hedronize_develop
    split = col.split(factor=0.15, align=True)
    if lt.display:
        split.prop(lt, "display", text="", icon='DOWNARROW_HLT')
    else:
        split.prop(lt, "display", text="", icon='RIGHTARROW')
    split.operator("mesh.hedronize_develop", text="Develop")
    if lt.display:
        box = col.column(align=True).box().column()
        LayoutDevelop(box,lt)
        box.prop(lt,"seed")
        lt2  = bpy.context.window_manager.hedronize_develop_params
        box.prop(lt2, "type")
        lt2.draw(box)

   
class Develop(Operator):
    bl_idname      = 'mesh.hedronize_develop'
    bl_label       = "Generate Develop polygon"
    bl_description = "generate polygon with develop"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT')
    def draw(self, context):
        layout = self.layout
        draw_develop(layout)
    def invoke(self, context, event):
        return self.execute(context)
    def execute(self, context):
        lt = context.window_manager.hedronize_develop
        random.seed(lt.seed)
        ExecuteDevelop(lt)
        return{'FINISHED'}



classes = ( Props_Develop,Develop)
def register_props():
    register_props_params()
    for cls in classes:
        bpy.utils.register_class(cls) 
    bpy.types.WindowManager.hedronize_develop      = PointerProperty(type=Props_Develop)
    
def unregister_props():  
      
    try:
        del bpy.types.WindowManager.hedronize_develop
    except Exception as e:
        print('develop unregister fail:\n', e)
        pass

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)   

    unregister_props_params()

