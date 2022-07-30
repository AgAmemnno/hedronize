import bpy 
import bmesh
from mathutils import Vector,Matrix,Euler
from  bmesh.types import BMVert,BMEdge,BMFace
import numpy as np
import random
import os
import sys
import importlib
import uuid
import time
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty,
        )
from collections import defaultdict
from contextlib import contextmanager  


def GetLayerCollection(col):
    lc = bpy.context.view_layer.layer_collection
    def find(lc):
        if lc.name == col.name:
            return lc
        for c in lc.children:
            ret = find(c)
            if ret:return ret 
        return None
    return find(lc)

@contextmanager        
def ActiveScope(col):
    try:
        lc = GetLayerCollection(col)
        exclude = lc.exclude
        lc.exclude = False
        yield lc
    finally:
        lc.exclude = exclude
@contextmanager 
def ActivateCollection(col):
    try:
        old = bpy.context.view_layer.active_layer_collection
        bpy.context.view_layer.active_layer_collection =  GetLayerCollection(col)
        yield bpy.context.view_layer.active_layer_collection
    finally:
        bpy.context.view_layer.active_layer_collection = old
@contextmanager        
def ActiveScopeFromObj(ob):
    try:
        lc   = None
        scol = False
        col = ob.users_collection[0]
        lc = GetLayerCollection(col)
        if lc :
            if lc.name == bpy.context.scene.collection.name:
                scol = True
            else:
                exclude = lc.exclude
                lc.exclude = False
            yield lc
        else:
            print(f"Error  Not Found Layers {ob.name}   user collection {ob.users_collection[0]}")
            yield None
    finally:
        if not scol:
            if lc:
                lc.exclude = exclude
def selectObj(ob):
    if bpy.context.mode == "EDIT_MESH":
        bpy.ops.object.editmode_toggle()
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode='OBJECT')
    assert bpy.context.mode == "OBJECT","ContextMode Error {bpy.context.mode}"
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = ob
    if bpy.context.mode == "EDIT_MESH":
        bpy.ops.object.editmode_toggle()
    ob.select_set(True) 
    ob.hide_set(False)
def deselect_object():
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

def set_parent(sur,insta,keep = True):
    bpy.ops.object.select_all(action='DESELECT')
    insta.select_set(True)
    sur.select_set(True)
    bpy.context.view_layer.objects.active = sur
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=keep)  
    insta.select_set(False)



def CntIndex(coll,name):
    idx = 0
    for c in coll.children:
        idx+= 1
        if c.name == name:
            return True,idx
        if len(c.children) > 0:
            t,idx2 = CntIndex(c,name)
            if t:
                return t,idx + idx2
            idx += idx2
    return False,idx
    
def getColl_Index(name):
    idx = 0
    for c in bpy.context.view_layer.layer_collection.children:
        idx +=1
        if name == c.name:
            return idx
        t,idx2 = CntIndex(c,name)
        if t:
            return idx + idx2
        idx += idx2
    return -1


def moveCol(col,ob):
    selectObj(ob)
    bpy.ops.object.move_to_collection(collection_index=getColl_Index(col.name))
def newCollection(name,pcol= None,dup = True):
    if not pcol:
        pcol =  bpy.context.scene.collection

    with ActivateCollection(pcol) as lc:
        if dup:
            col = bpy.data.collections.new(name)
        else:
            if  name in bpy.data.collections:
                col = bpy.data.collections[name]
            else:
                col = bpy.data.collections.new(name) 
        if col.name not in pcol.children:
            pcol.children.link(col)
        
    return col


def bm_update():
    bmesh.update_edit_mesh(bpy.context.edit_object.data)
def get_bmfromObj(obj):
    if bpy.context.mode != "EDIT":
        bpy.ops.object.mode_set(mode='EDIT')
    bm_update()
    me   = obj.data
    return  bmesh.from_edit_mesh(me)    

def bboxCenter(ob):
    bbox_corners = [ob.matrix_world @ Vector(corner) for corner in ob.bound_box]
    center = Vector((0,0,0))
    for b in bbox_corners :
        center += b
    return Vector((center.x/len(bbox_corners),center.y/len(bbox_corners),center.z/len(bbox_corners)))
    
def getBoneAxis(AXIS,root):
    for b in root.children_recursive:
        if b.parent:
            loc = b.head.copy()
            y = b.y_axis.copy()
            AXIS[b.name] = [loc,y,b.parent.name]   

class MetaPropsBase:
    props = {}
    def __init__(self):
        self.props = {}

    def SetFloat(self,name,default,min=0.,max =1.,upFunc= None,desc = "param template dynamic class float"):
        assert name not in self.props,f"overload name error {name}    {self.props}"
        self.props[name] = FloatProperty(
            name = name,
            description = desc,
            default = default,
            soft_min= min,
            soft_max= max,
            update  = upFunc
        )
    def SetInt(self,name,default,min=0,max =1,upFunc= None,desc = "param template dynamic class int" ):
        assert name not in self.props,f"overload name error {name}    {self.props}"
        self.props[name] = IntProperty(
            name = name,
            description = desc,
            default = default,
            min= min,
            max= max,
            update  = upFunc
        )
    def SetBool(self,name,default,upFunc= None,desc = "param template dynamic class bool" ):
        assert name not in self.props,f"overload name error {name}    {self.props}"
        self.props[name] = BoolProperty(
            name = name,
            description = desc,
            default = default,
            update  = upFunc
        )
    def SetEnum(self,name,default,items,upFunc= None,desc = "param template dynamic class enums" ):
        assert name not in self.props,f"overload name error {name}    {self.props}"
        self.props[name] = EnumProperty(
            name = name,
            items=tuple(items),
            description= desc,
            default = default,
            update = upFunc
        )
    def SetCollection(self,name,upFunc= None,desc = "param template dynamic class collection" ):
        assert name not in self.props,f"overload name error {name}    {self.props}"
        self.props[name] = PointerProperty(name =name,type = bpy.types.Collection,  update = upFunc, description= desc)
    def SetLibrary(self,name,upFunc= None,desc = "param template dynamic class library" ):
        assert name not in self.props,f"overload name error {name}    {self.props}"
        self.props[name] = PointerProperty(name =name,type = bpy.types.Library,  update = upFunc, description= desc)
    def SetAction(self,name,upFunc= None,desc = "param template dynamic class library" ):
        assert name not in self.props,f"overload name error {name}    {self.props}"
        self.props[name] = PointerProperty(name =name,type = bpy.types.Action,  update = upFunc, description= desc)
    def SetMaterial(self,name,upFunc= None,desc = "param template dynamic class library" ):
        assert name not in self.props,f"overload name error {name}    {self.props}"
        self.props[name] = PointerProperty(name =name,type = bpy.types.Material,  update = upFunc, description= desc)
      
    def SetObject(self,name,upFunc= None,desc = "param template dynamic class object" ):
        assert name not in self.props,f"overload name error {name}    {self.props}"
        self.props[name] = PointerProperty(name =name,type = bpy.types.Object,  update = upFunc, description= desc)
    def SetString(self,name,default,upFunc= None,desc = "param template dynamic class string" ):
        assert name not in self.props,f"overload name error {name}    {self.props}"
        self.props[name] = StringProperty(
                name=name,
                description=desc,
                default=default,
                update=upFunc
                )


def CTIME():
    return time.strftime("%Y%b%d%H:%M:%S")
