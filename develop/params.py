import bpy
from bpy.types import PropertyGroup
from bpy.props import (
        BoolProperty,
        PointerProperty,
        StringProperty,
        )
from math import *
from ..utils  import *

TOOLS =  [ 'modifiers_bcast' , 'shapekey' , 'armature' ,'cellhedron' , "shapekey_remove" ]

def Params_modifiers_bcast(mp):
    items =[]
    for i in ["apply","delete" ]:
        items.append((i,i.upper(),i.upper()))
    mp.SetEnum("modbc","apply",items,upFunc= None,desc ="Hedron Objects Broadcast Functions")

def Params_shapekey(mp):
    mp.SetBool("link",default= False,upFunc= None,desc = "Hedron with ShapeKey." )

def Params_shapekey_remove(mp):
    pass
def Params_cellhedron(mp):
    items =[("dup","duplicate","mesh duplicate cell"),("asset","assets","asset instance cell"),
    ("ins","instance","instanced cell")]
    mp.SetEnum("mode","ins",items,upFunc= None,desc ="instance or dulicate ")
    mp.SetCollection("assets",upFunc= None,desc = "Assets Collection Ngon objects" )
    mp.SetObject("arm",upFunc= None,desc = "Armature Hedron[object]" )
def Params_armature(mp):
    pass


def generateDyn(lt):
    lt.drawable = False
    if lt.cache_type == lt.type:return lt,bpy.types.WindowManager.hedronize_model_dynamic 
    mp  = MetaProps()        
    Props_Develop_Params.generate(mp)
    eval(f"Params_{lt.type}(mp)")
    lt.cache_type = lt.type
    return mp.Generate()

def UpdateTypes(cls,context):
    #
    lt,_ = generateDyn(bpy.context.window_manager.hedronize_develop_params)
    lt.drawable = True



class MetaProps(MetaPropsBase):
    props = {}

    def __init__(self):
        self.props = {}
    def Init(self):
        
        eval(f"Params_{TOOLS[0]}(self)")
        cls = bpy.types.WindowManager.hedronize_develop_params_dynamic = type('Props_Develop_Dyn', (Props_Develop_Params,), {'__annotations__': self.props})
        bpy.utils.register_class(cls)  
        bpy.types.WindowManager.hedronize_develop_params = PointerProperty(type=cls)

        cls.props = self.props
        return cls,bpy.types.WindowManager.hedronize_develop_params    

    def Generate(self):
        
      
        cls = bpy.types.WindowManager.hedronize_develop_params_dynamic
        bpy.utils.unregister_class(cls)   
        del bpy.types.WindowManager.hedronize_develop_params
        del bpy.types.WindowManager.hedronize_develop_params_dynamic
        cls = bpy.types.WindowManager.hedronize_develop_params_dynamic = type('Props_Develop_Dyn', (Props_Develop_Params,), {'__annotations__': self.props})
        bpy.utils.register_class(cls)  
        bpy.types.WindowManager.hedronize_develop_params = PointerProperty(type=cls)
        cls.props = self.props
        return bpy.context.window_manager.hedronize_develop_params,cls


class Props_Develop_Params(PropertyGroup):

    drawable : BoolProperty(
        name="drawable",
        description="Is drawable",
        default=False
        )   
    cache_type    : StringProperty(
        name="cachetype",
        description="Current type",
        default="none"
        )    
    @classmethod
    def generate(cls,mp):
        items = []
        for i in TOOLS:
            items.append( (i.lower(), i.lower(), i.upper()))
            assert eval(f"Params_{i}"),"Not Found Parameter Function module {i}"

        mp.SetEnum("type",TOOLS[0] ,tuple(items),upFunc = UpdateTypes,desc = "Develop Tools" )

    def draw(lt,layout):

        if lt.drawable:
            box    = layout.box()
            paramCls =  bpy.types.WindowManager.hedronize_develop_params_dynamic
            if not hasattr(paramCls,"props"):
                    lt.drawable = False
                    print(f"Not Found Props in hed_param drawable False")
            else:
                    for p in paramCls.props:
                            if p== "type":continue
                            col = box.column().split()
                            col.prop(lt, p)        



def register_props_params():
    
    mp  = MetaProps()        
    Props_Develop_Params.generate(mp)
    mp.Init()


def unregister_props_params(): 
    bpy.utils.unregister_class(bpy.types.WindowManager.hedronize_develop_params_dynamic)  
    del bpy.types.WindowManager.hedronize_develop_params
    del bpy.types.WindowManager.hedronize_develop_params_dynamic  