from mathutils import Vector,Matrix
import bpy
import re
from  math import *
from ..utils  import *
from .develop  import *
import time 

class BoneSeparator:
    deb = True
    @classmethod
    def print(cls,s):
        if cls.deb:print(s)
    @classmethod
    def Init(cls,hed):
        
        cls          = BoneSeparator
        cls.print(f"BoneSeparator Initializing....... {hed.name} ")
        suffix  = hed.name.split(':')[1]
        prefix  = hed.name.split(':')[0]
        if suffix == "arm":
            assert hed.type == 'ARMATURE',f"BoneSeparator::Error contextobject != Armature {hed.name}"
            cls.arm  = hed
        else: 
            arm_name = f"{prefix}:arm"
            _name = prefix.split("-")
            num,fam  = int(_name[1]),_name[0]
            if arm_name not in bpy.data.objects:
                #f"Armature Not Found {ob.name}"    
                cls.arm      =  Build_bones(num,prefix)
            else:
                cls.arm      =  bpy.data.objects[arm_name]
            cls.No       =  num
            faces,verts,hinges,sfaces = parse_poly(num)
            cls.Props    = sfaces
        
        cls.prefix  =  prefix

        
        #cls.SeparateTopDown()
        #cls.Separate_impl = cls.SeparateTopDown
    @staticmethod
    def GetBoneNums(name):
        spl = name.split(":")
        assert len(spl) == 2,f"name error {name}"
        n = int(name.split(":")[1])
        return n
    @staticmethod
    def PB_DriverRemove(pb):
        pb.driver_remove("rotation_euler",0)

         
                
    @staticmethod
    def EB_Separate(arm,rootName):
        assert bpy.context.mode == 'EDIT_ARMATURE',f"ContextError {bpy.context.mode} == EDIT_ARMATURE"
        
        bpy.ops.armature.select_all(action='DESELECT')

        root = arm.data.edit_bones[rootName]
        root.select = True
        for b in root.children_recursive:
            b.select = True
        bpy.ops.armature.separate()
        active = bpy.context.active_object
        for i in bpy.context.selected_objects:
            if i != active:
                return i   
        assert False,"UnReachable ED_separate  {arm.name}   {rootName}  "
                         
    @classmethod
    def SeparateTopDown(cls,minBone =3 ,maxGroup= 5,nearRatio = 0.5):
        cls          = BoneSeparator
        arm           = cls.arm
        prefix        = arm.name = arm.name.replace(".","_")
        colName = prefix + ":{}"
            
        pcol = newCollection(prefix)
        with ActiveScopeFromObj(arm) as lc:
            
            recMax      = maxGroup
            groupN      = 1
            def Cutting(arm,groupN,recMax= 0):

                selectObj(arm)
                assert len(arm.data.bones) > 0,f"Arm has no a bone {arm.name}"
                ctrl = arm.data.bones[0]
                if ctrl.name  == "Ctrl":
                    assert len(arm.data.bones) > 1,f"Arm has no a bone {arm.name}"
                    bones = arm.data.bones[1:]
                else:
                    bones = arm.data.bones
                baseGroup = 0
                Bnum      = cls.GetBoneNums(bones[0].name)
                print(f"cutting bone root {recMax} init {bones[0].name}  bnum {Bnum}") 
                if recMax == 0:
                    return 
                
                for b in bones:
                    if len(b.children) < 2:
                        baseGroup += 1
                        continue
                    root = b
                    cand = []
                    amount = 0 
                    for b2 in root.children:
                        Num = len(b2.children_recursive)+1
                        if  Num < minBone:
                            baseGroup += Num
                        else:
                            cand.append((b2,Num))
                            amount += Num
                            
                    print(f"candidate group {cand}  amount {amount} baseGroup {baseGroup} ")
                    
                    amount += baseGroup
                    if len(cand) < 1:
                        col = newCollection(colName.format(Bnum),pcol = pcol)
                        moveCol(col,arm)
                        return 
                    ratio  = []        
                    for b3,Num in cand:
                        ratio.append(abs(Num/amount - nearRatio))
                    
                    print(f"candidate ratio  {ratio}  near {nearRatio}  nearest {np.argmin(ratio)} ")
                    rid = np.argmin(ratio)
                    assert rid < len(cand),f"Argmin failed {ratio} "
                    cutbName       = cand[rid][0].name
                    Bnum1          = cls.GetBoneNums(cutbName)
                    print(f"cutting bone  {cutbName}  bnum {Bnum1}") 
                    
                    
                    
                    bpy.ops.object.posemode_toggle()
                    pb = arm.pose.bones[cutbName]
                    cls.PB_DriverRemove(pb)
                    bpy.ops.object.posemode_toggle()
                    
                    bpy.ops.object.editmode_toggle()
                    narm = cls.EB_Separate(arm,cutbName)
                    
                    deselect_object()
                    
                    n0 = len(arm.data.bones)
                    n1 = len(narm.data.bones)
                    print(f"cutting bone compare  arm {n0}  newarm {n1}") 
                    if n0 > n1:
                        sarm  = narm
                        Bnum2 = Bnum 
                        Bnum  = Bnum1 
                        
                    else:
                        sarm  = arm 
                        arm   = narm
                        Bnum2 = Bnum1 
                    
                    col = newCollection(colName.format(Bnum),pcol = pcol)
                    moveCol(col,sarm)   
                    groupN += 1
                    
                    
                    if recMax <= 0:
                        return 
                    recMax -= 1
                    
                    if maxGroup > groupN:
                        print(f"Rec>>>>>>>>>>>>>>>>>>>>>>>   {arm.name} ") 
                        Cutting(arm,groupN,recMax)
                        return
                    else:
                        col = newCollection(colName.format(Bnum2),pcol = pcol)
                        moveCol(col,arm)
                        return
                    
        
            Cutting(arm,groupN,recMax)
        return pcol
    
    @classmethod
    def SeparateSelected(cls):
        cls          = BoneSeparator
        arm           = cls.arm
        prefix        = arm.name = arm.name.replace(".","_")
        colName = prefix + ":{}"
            
        pcol = newCollection(prefix)
        col  = newCollection(colName.format(0),pcol = pcol)
        moveCol(col,arm)
        

        with ActiveScopeFromObj(arm) as lc:
            
            def GetRoot(arm):
                selectObj(arm)
                assert len(arm.data.bones) > 0,f"Arm has no a bone {arm.name}"
                ctrl = arm.data.bones[0]
                if ctrl.name  == "Ctrl":
                    assert len(arm.data.bones) > 1,f"Arm has no a bone {arm.name}"
                    root = arm.data.bones[1]
                else:
                    root = arm.data.bones[0]
                return root

            CutB = []
            def Select(root):
                children = root.children
                childNum = len(children)
                if childNum==0:return
                for b in children:
                    if b.select:
                        CutB.append(b.name)
                    Select(b)

            Select(GetRoot(arm))

            NARMS = {}
            def Cutting(arm):

                _root = GetRoot(arm)
                def Exec(root):
                    
                    children = root.children
                    childNum = len(children)
                    rootName = root.name
                    if childNum==0:return
                    for CID in range(childNum):
                        root     = arm.data.bones[rootName]
                        if len(root.children) <= CID:
                            return 
                        b        = root.children[CID]
                        cls.print(f"<<<<<<<<<<<<<<<<<Recursive  Bones Root {root.name}  bone {b.name} ")
                        if b.name in CutB:
                            Bnum          = cls.GetBoneNums(b.name)
                            cls.print(f"<<<<<<<<<<<<<<<<<Try Cutting root name::{b.name}   bone number::{Bnum}  children num::{len(b.children)}") 
                            cutB  = b
                            
                            bpy.ops.object.posemode_toggle()
                            pb = arm.pose.bones[cutB.name]
                            cls.PB_DriverRemove(pb)
                            bpy.ops.object.posemode_toggle()
                            
                            bpy.ops.object.editmode_toggle()
                            narm = cls.EB_Separate(arm,cutB.name)
                            
                            deselect_object()
                            col = newCollection(colName.format(Bnum),pcol = pcol)
                            moveCol(col,narm)
                            NARMS[col.name] = narm
                            cls.print(f">>>>>>>>>>>>>>>>OK new arm {narm.name}  collection {col.name} ")
                            Cutting(narm)
                            return 
                        Exec(b)   
                Exec(_root)       
            
            Cutting(arm)
            assert len(CutB) == len(NARMS) ,f"Cutting Failed  CutBones {CutB} !=  NewArm {NARMS}" 

           

        return pcol
                
class CellSeparator:
    Prims = {}
    @staticmethod
    def InitFromHedron(ob,mode,uuid = True,assets = {},arm = None):
        cls = CellSeparator
        if arm is None:
            arm_name = f"{ob.name.split(':')[0]}:arm"
            if arm_name not in bpy.data.objects:
                #f"Armature Not Found {ob.name}"
                _name = ob.name.split(':')[0].split("-")
                cls.arm    = Build_bones(int(_name[1]),_name[0])
            else:
                cls.arm      =  bpy.data.objects[arm_name]
        else:
            cls.arm    = arm

        cls.col      =  newCollection(f"Separate-{cls.arm.name}-Cell")
        cls.col.objects.link(ob)

        
        if uuid:
            UUID     =  CTIME()
            cls.uuid = UUID
        else:
            cls.uuid = ""
            
        cls.Prims = {}
        #cls.No  = N
        #faces,verts,hinges,sfaces = parse_poly(N)
        #cls.Props =  sfaces
        cls.ob = ob
        if mode == "ins":
            cls.Separate_impl = cls.SeparateCellinstance
        elif mode == "dup":
            cls.Separate_impl = cls.SeparateCellLink

        cls.type  = "FromHedron"

    @staticmethod
    def InitFromSepCol(col,pcol = None,copy= False):
        cls = CellSeparator
    
        prefix = col.name.split(":")[0]
        hedName = f"{prefix}:hedron" 
   
        assert hedName in bpy.data.objects,f"Not Found Hedron  {hedName} in objets {col.name}"
        hedron = bpy.data.objects[hedName]



        if copy:
            pcol = newCollection(f"LinkCell-{col.name}",pcol = pcol)
            deselect_object()
            with ActiveScope(col) as lcol:
                with ActivateCollection(pcol) as lpcol:
                    for c in col.children:
                        assert len(c.objects) == 1,f"Collection Error {c.name}"
                        ob    = c.objects[0]
                        assert ob.type == 'ARMATURE',f"ObjectTypeError not ARMATURE {ob.type} {ob.name} {c.name}"
                        with ActiveScopeFromObj(ob) as lc:
                            selectObj(ob)
                            bpy.ops.object.duplicate_move_linked()
                            _col  = ob.users_collection[0]
                            dupcol = newCollection(_col.name,pcol = pcol,dup = True)
                            moveCol(dupcol,ob)
        else:

            if pcol:
                PCOLS = GetParentCollection(col)
                for p in PCOLS:
                    p.children.unlink(col)
                pcol.children.link(col)
            #col.name = f"LinkCell-{col.name}"
            pcol = col

        cls.pcol  = pcol
        cls.ob    = hedron
        cls.col   = None
        cls.Prims = {}
        cls.No  = int(prefix.split("-")[1])
        #faces,verts,hinges,sfaces = parse_poly(N)
        #cls.Props =  sfaces
        cls.uuid  = None
        cls.Separate_impl = cls.SeparateCellLink
        cls.type  = "FromSepCol"

    @staticmethod
    def NameParse(name):
        cls = CellSeparator
        col = cls.col
        if cls.uuid:
            cname = f"cell{cls.uuid}-{name}"
        else:
            cname = f"cell-{name}"
        assert cname not in col.objects,f"Name Conflit {cname} in col.objects  {col.name} "
        spl = name.split(":")
        assert len(spl) == 2,f"name error {name}"
        n = int(name.split(":")[1])
        return n,cname

    @staticmethod
    def Mod_Uniform(ob,type = "cutmul"):
        if type == "cutmul":
            with ActiveScopeFromObj(ob) as lc:
                selectObj(ob)
                if "Subdivision" not in bpy.context.object.modifiers:
                    bpy.ops.object.modifier_add(type='SUBSURF')
                    bpy.context.object.modifiers["Subdivision"].subdivision_type = 'SIMPLE'
                    bpy.context.object.modifiers["Subdivision"].show_on_cage = True
                    bpy.context.object.modifiers["Subdivision"].levels = 2
                    bpy.ops.object.modifier_add(type='SUBSURF')
                    bpy.context.object.modifiers["Subdivision.001"].show_on_cage = True
                    bpy.ops.object.modifier_add(type='SOLIDIFY')
                    bpy.context.object.modifiers["Solidify"].show_on_cage = True
                    bpy.context.object.modifiers["Solidify"].thickness = 0.005
                    bpy.context.object.modifiers["Solidify"].material_offset_rim = 1
                    bpy.ops.object.shade_smooth()
                    bpy.context.object.data.use_auto_smooth = True

    @staticmethod
    def SeparateCuttingArm(rotate = 45):
        cls = CellSeparator
        assert cls.type  == "FromSepCol",f"Uninitialized Arms {cls.pcol.name}"

        def RootBoneRotate(arm,rootName,rotate):
            bpy.ops.object.posemode_toggle()
            pb = arm.pose.bones[rootName]
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler.x = radians(rotate)
            bpy.ops.object.posemode_toggle()
                    
        _link = None
        if cls.ob.library or cls.ob.data.library:
            hcol = newCollection("Hedron",dup = False)
            _link = cls.ob
            if cls.ob.library:
                ob = cls.ob.copy()
                hcol.objects.link(ob)
            else:
                ob = cls.ob

            ob.data = ob.data.copy()
            cls.ob  = ob

        assert (not cls.ob.library) and (not cls.ob.data.library),f"Object yet linked  {cls.ob.name} "

        for armCol in cls.pcol.children:
            cls.arm = armCol.objects[0]
            cls.col = armCol
            with ActiveScopeFromObj(cls.arm) as lc:
                selectObj(cls.arm)
                bpy.ops.object.editmode_toggle()
                if "Ctrl" == cls.arm.data.edit_bones[0].name:
                    root     =  cls.arm.data.edit_bones[1]
                else:
                    root     =   cls.arm.data.edit_bones[0]
                AXIS = {}
                getBoneAxis(AXIS,root)
                ob = cls.Separate_impl(root.name)
                
                cls.Mod_Uniform(ob)
               
                for b in AXIS:
                    ob = cls.Separate_impl(b)
                    cls.Mod_Uniform(ob)
                
                bpy.ops.object.editmode_toggle()
                
                RootBoneRotate(cls.arm,cls.arm.data.bones[0].name,rotate)
                

        if _link:
            bpy.data.meshes.remove(cls.ob.data)
            cls.ob = _link

    @staticmethod
    def Separate():
        cls = CellSeparator
        _link = None
        if cls.ob.library:
            hcol = newCollection("Hedron",dup = False)
            _link = cls.ob
            ob = cls.ob.copy()
            hcol.objects.link(ob)
            ob.data.make_local()
            cls.ob  = ob



        with ActiveScopeFromObj(cls.arm) as lc:
            selectObj(cls.arm)
            bpy.ops.object.editmode_toggle()
            root     = cls.arm.data.edit_bones[1]
            AXIS = {}
            getBoneAxis(AXIS,root)
            cls.Separate_impl(root.name)
            for b in AXIS:
                cls.Separate_impl(b)
            
            moveCol(cls.col,cls.arm)
        
        if _link:
            bpy.data.meshes.remove(cls.ob.data)
            cls.ob = _link
        print(f"#################################CELL SEPARATE FIN     {cls.ob.name}   {cls.arm.name} ")
        return cls.arm
    
    @staticmethod
    def bboxMinMax(ob,mw = Matrix()):
        mw = mw @ ob.matrix_world
        bbox_corners = [ mw @ Vector(corner) for corner in ob.bound_box]
        Min = [10000,10000,10000]
        Max = [-10000,-10000,-10000]
        for b in bbox_corners:
            for i in range(3):
                Min[i] = min(b[i],Min[i])
                Max[i] = max(b[i],Max[i])            
        return Vector(Min),Vector(Max)
        
    @staticmethod
    def bbMinMax(ob):
        Min,Max  = bboxMinMax(ob)
        mw       = ob.matrix_world
        for o in ob.children:
            oMin,oMax = bboxMinMax(o,mw)
            for i in range(3):
                Min[i] = min(oMin[i],Min[i])
                Max[i] = max(oMax[i],Max[i]) 
        return Min,Max    

    
    @staticmethod
    def SeparateCellinstance(name):
        cls = CellSeparator
        n,cname = cls.NameParse(name)
        ob = cls.ob
        CellName = cls.arm.name + ":Cell_{}"
        
        with ActiveScopeFromObj(ob) as lc:
            with ActivateCollection(cls.col) as lcol:
                selectObj(ob)
                #print(f"OBJECT===================================-   {ob.name} ")
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.editmode_toggle()
               
                mw = ob.matrix_world
                me = ob.data
                po = me.polygons[n]
                Ngon = len(po.vertices)
                cent = mw @ po.center
                v    = me.vertices[po.vertices[0]]
                dir  = v.co - cent
                po.select = True
                ob.data.update()

  
                #print(f"{ob.name}   activecollection {cls.col} face {n}  center {cent}   Prims {cls.Prims} ")


                if Ngon not in cls.Prims:
                    bpy.ops.object.editmode_toggle()
                    cls.Prims[Ngon] = {"center" :cent,"dir":dir,"cname" : cname}
                    bpy.ops.mesh.duplicate()
                    try:
                        bpy.ops.mesh.separate(type='SELECTED')
                    except RuntimeError:
                        print(f"SeparateSelected {str(e)}    ")
                        return False
                    bpy.ops.object.editmode_toggle()  
                    cell  = False   
                    for i in bpy.context.selected_objects:
                        if i != ob:
                            cell =i
                            break
                    assert cell,f"Not Found {cell.name}"
                    selectObj(cell)
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                    bpy.context.view_layer.update()
                    cell.location = 0,0,0
                    bpy.context.view_layer.update()
                    cell.name = cname
                    ccol = newCollection(CellName.format(Ngon),pcol = cls.col)
                    _ccol = cell.users_collection[0]
                    ccol.objects.link(cell)
                    _ccol.objects.unlink(cell)
                    bpy.ops.object.collection_instance_add(collection=ccol.name, align='WORLD', location=cent, scale=(1, 1, 1))
                    icell = bpy.context.object
                    cls.Prims[Ngon]["cname"] = ccol.name

                else:
                    prop = cls.Prims[Ngon]
                    
                    bpy.ops.object.collection_instance_add(collection=prop["cname"], align='WORLD', location=cent, scale=(1, 1, 1))
                    icell = bpy.context.object
                    icell.location = cent
                    Dir  = prop["dir"]
                    assert abs(Dir.length  -dir.length) < 0.001,f"Length Error may be no regular Dir0 {Dir} !=  dir {dir}    {ob.name} "
                    assert abs(Dir.z)<0.001 and abs(dir.z) < 0.001 ,f"Face is not normal z {Dir} {dir}"  
                    D  = Dir.xy.normalized()
                    d  = dir.xy.normalized()
                    angle = D.angle_signed(d)
                    icell.rotation_euler.z = -angle
                    icell.name = cname

                
                moveCol(cls.col,icell)
                selectObj(cls.arm)
                bpy.ops.object.editmode_toggle()
                eb = cls.arm.data.edit_bones
                assert name in cls.arm.data.edit_bones,f"Editbones Notfound {name} {cls.arm} "
                eb.active = cls.arm.data.edit_bones[name]
                #print(f"LinkCell {cell.name} bone {name} col {name in cls.arm.data.edit_bones } ")
                bpy.ops.object.editmode_toggle()
                icell.select_set(True)
                bpy.context.view_layer.objects.active = cls.arm
                bpy.ops.object.parent_set(type='BONE', keep_transform=True)  
  

            
        return icell           

    @staticmethod
    def SeparateCellLink(name):
        cls = CellSeparator
        n,cname = cls.NameParse(name)

        ob = cls.ob
        with ActiveScopeFromObj(ob) as lc:
            with ActivateCollection(cls.col) as lcol:
                selectObj(ob)
                #print(f"OBJECT===================================-  {bpy.context.mode}     {bpy.context.object} ")
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.editmode_toggle()
               
                mw = ob.matrix_world
                me = ob.data
                po = me.polygons[n]
                Ngon = len(po.vertices)
                cent = mw @ po.center
                v    = me.vertices[po.vertices[0]]
                dir  = v.co - cent
                po.select = True
                ob.data.update()

  
                #print(f"{ob.name}   activecollection {cls.col} face {n}  center {cent}   Prims {cls.Prims} ")


                if Ngon not in cls.Prims:
                    bpy.ops.object.editmode_toggle()
                    cls.Prims[Ngon] = {"center" :cent,"dir":dir,"cname" : cname}
                    bpy.ops.mesh.duplicate()
                    try:
                        bpy.ops.mesh.separate(type='SELECTED')
                    except RuntimeError:
                        print(f"SeparateSelected {str(e)}    ")
                        return False
                    bpy.ops.object.editmode_toggle()  
                    cell  = False   
                    for i in bpy.context.selected_objects:
                        if i != ob:
                            cell =i
                            break
                    assert cell,f"Not Found {cell.name}"
                    cell.name = cname
                    cls.Prims[Ngon]["cname"] = cell.name
                    selectObj(cell)
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                    
                else:
                    prop = cls.Prims[Ngon]
                    cell = bpy.data.objects[prop["cname"]]
                    
                    selectObj(cell)
                    
                    bpy.ops.object.duplicate_move_linked()
                    
                    dup = bpy.context.object
                    dup.location = cent
                    Dir  = prop["dir"]
                    assert abs(Dir.length  -dir.length) < 0.001,f"Length Error may be no regular Dir0 {Dir} !=  dir {dir}    {ob.name} {cell.name}"
                    assert abs(Dir.z)<0.001 and abs(dir.z) < 0.001 ,f"Face is not normal z {Dir} {dir}"  
                    D  = Dir.xy.normalized()
                    d  = dir.xy.normalized()
                    angle = D.angle_signed(d)
                    dup.rotation_euler.z = -angle
                    dup.name = cname
                    cell = dup

                
                moveCol(cls.col,cell)
                #return 
                selectObj(cls.arm)
                bpy.ops.object.editmode_toggle()
                eb = cls.arm.data.edit_bones
                assert name in cls.arm.data.edit_bones,f"Editbones Notfound {name} {cls.arm} "
                eb.active = cls.arm.data.edit_bones[name]
                #print(f"LinkCell {cell.name} bone {name} col {name in cls.arm.data.edit_bones } ")
                bpy.ops.object.editmode_toggle()
                cell.select_set(True)
                bpy.context.view_layer.objects.active = cls.arm
                bpy.ops.object.parent_set(type='BONE', keep_transform=True)  
                #parentBone(cls.arm,name,cell)

            
        return cell