from mathutils import Vector,Matrix
import bpy
import re
import math
import json
from ..utils  import *
from .separator  import CellSeparator 
Hnames  = []  
def HedronNames():
    global Hnames
    if Hnames == []:
        path     =   f"{bpy.utils.user_resource( 'SCRIPTS')}\\addons\\hedronize\\develop\\data"
        filename =   f"{path}\\names.json"
        with open(filename) as file:
            data = json.load(file)
        Hnames = data
    return Hnames

def GenerateHedron(fam,num):
    num       = int(num)
    family    = ['Pla','Kep','Arc','Arc2','Pri','Joh','Oth'] 
    Hnames    = HedronNames()
    pcol      = newCollection("SkelHedron",dup = False)
    pcol.color_tag = 'COLOR_03'

    scol = bpy.context.scene.collection
    if pcol not in list(scol.children):
        scol.children.link(pcol)

    phe    = Hnames["families"][family.index(fam)]["polyhedra"]
    Name  = None
    for prop in phe:
        if prop["number"] == num:
            Name = prop["name"]
            name = f"{fam}-{num}"
    assert Name,f"Not Found {fam} {num}    "
    

    with ActiveScope(pcol) as col_: 
        try:
            faces,verts,hinges,sfaces = parse_poly(num)
        except:
            assert False,print(f"Error parse {fam} {num}  {prop} ")
            
        col = newCollection(Name,pcol = pcol,dup = False)
        col.color_tag = pcol.color_tag
            
        with ActiveScope(col) as col_l: 
            try:
                obname = "{}:{:003d}".format(name,0)
                if obname not in bpy.data.objects:
                    o = Build_poly(num,name,col)
                    #print(f"Extern Run BuildPoly {col.name}")
                cname = f"{name}:hedron"
                if cname not in bpy.data.objects:
                    o = LoadPoly(cname,num)
                    moveCol(col,o)
                    BakeShapeKey(2,name,cname,num)
                    #print(f"Extern Run BuildShapekey {col.name}")
                    
                #arm = develop.Build_bones(num,name)
            except:
                assert False,f"Error Build  {fam} {num}  {prop} "
                    

    scol.children.unlink(pcol)

class OPSHedron:
    FAM     = ['Pla','Kep','Arc','Pri','Arc2','Joh','Oth']
    Hnames  = HedronNames()
    deb = True
    @classmethod
    def print(cls,s):
        if cls.deb:print(f"OPSHedron:: {s}")
    @classmethod
    def MakeReal(cls):    
        _link = None
        ob = cls.hedron
        assert not ob.library,f"LibraryError {ob.name} is linked. "
        with ExcludeCollection( False,[cls.col.name,"Hedron"],finalize =True) as lc:    
            dup = duplicateObj(ob)
            if dup.library:
                dup = dup.copy()
            if dup.data.library:
                dup.data = dup.data.copy()
                
            cls.hedron  = dup
            moveCol(cls.col,dup)

        assert (not cls.hedron.library) and (not cls.hedron.data.library),f"Object yet linked  {cls.ob.name} "
    @classmethod
    def GetFullName(cls,family,num):
        FullName  = None
        for p in cls.Hnames["families"][cls.FAM.index(family)]["polyhedra"]:
            if int(num) == int(p['number']):
                FullName = p["name"]
                break
        assert FullName,f"Not Found {family}-{num}  {cls.Hnames['families'][cls.FAM.index(family)]} "     
        return FullName   
    
    @staticmethod
    def CleanUpHedron(FullName):
        lcol = None
        if "SkelHedron" in bpy.data.collections:
            sh  = bpy.data.collections["SkelHedron"]
            if FullName in sh.children:
                lcol = bpy.data.collections[FullName]
        if lcol:
            obnames = [ob.name for ob in lcol.objects]
            for name in obnames:
                bpy.data.objects.remove(bpy.data.objects[name])
            bpy.data.collections.remove(lcol)


    @staticmethod
    def QueryHedron(name,FullName):
        lcol = None
        if "Hedron" in bpy.data.collections:
            col = bpy.data.collections["Hedron"]
            if name in col.objects:
                hed  = col.objects[name]
                return hed
        if "SkelHedron" in bpy.data.collections:
            sh  = bpy.data.collections["SkelHedron"]
            if FullName in sh.children:
                lcol = bpy.data.collections[FullName]
                if name not in lcol.objects:
                    lcol = None
        if not lcol:            
            famnum  = (name.split(":")[0]).split("-")
            GenerateHedron(famnum[0],famnum[1])
            lcol = bpy.data.collections[FullName]
        assert name in lcol.objects,f"Not Found {name}"
        hed  = lcol.objects[name]
        hed  = hed.copy()
        #lcol.objects.unlink(hed)
        return hed  
    @classmethod
    def SetFromArm(cls,arm,col):
        cls.col  = col
        spl      =  arm.name.split(":")[0].split("-")
        family   =  spl[0]
        num      =  spl[1]
        cls.HedName =  f"{family}-{num}:hedron" 
        cls.FullName = cls.GetFullName(family,num)
        hcol     = newCollection("Hedron",dup = False)
        if cls.HedName in hcol.objects:
            hedron = hcol.objects[cls.HedName]
        else:
            hedron = cls.QueryHedron(cls.HedName,cls.FullName)

        if hedron.library:
            hedron = hedron.copy()
            hcol.objects.link(hedron)
        
        cls.hedron = hedron
        
        cls.MakeReal()
        cls.print(f"SetFromArm:: HEDRON  {cls.hedron.name}  == {cls.FullName} ")

    @classmethod
    def Ensure(cls,bm):
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
    @classmethod
    def LoopAngles(cls,lst,center):
        ob = cls.hedron
        with ActiveScopeFromObj(ob) as lc:
            with ActivateCollection(cls.col) as lcol:
                selectObj(ob)
                bm        = get_bmfromObj(ob)
                cls.Ensure(bm)
                f = bm.faces[center]
                Lface = []
                for loop in f.loops:
                    e = loop.edge
                    for f0  in e.link_faces:
                        if f0 != f:
                            if f0.index in lst:
                                Lface.append(f0)
                if len(Lface) ==0 :
                    deselect_object()
                    return [],None
                c0 = f.calc_center_median()
                c1 = Lface[-1].calc_center_median()
                i1 = Lface[-1].index
                d1 = (c1-c0).xy.normalized()
                Angles = []
                CC  = None
                for f0 in Lface:
                    c2        = f0.calc_center_median()
                    i2        = f0.index
                    d2 = (c2 - c0).xy.normalized()
                    if not CC:
                        CC = -1 if d1.xy.cross(d2) < 0 else 1
                    angle = d1.angle_signed(d2)
                    Angles.append({"angle" : angle ,"pair": (i1,i2)} )
                    c1  = c2
                    i1  = i2
                    d1  = d2
                deselect_object()
        return Angles,CC
    @classmethod
    def GetPolygon(cls,n):
        class Polygon:
            pass
        p  = Polygon()
        ob = cls.hedron
        with ActiveScopeFromObj(ob) as lc:
            with ActivateCollection(cls.col) as lcol:
                selectObj(ob)
                
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.editmode_toggle()
               
                mw        = ob.matrix_world
                me        = ob.data
                po        = me.polygons[n]
                p.Ngon    = len(po.vertices)
                p.center  = mw @ po.center
                p.area    = po.area
                p.v       = [mw@me.vertices[vid].co for vid in po.vertices]
                p.iradius =   ((p.v[0] + p.v[1])/2. - p.center).length
        return p
    
    @staticmethod 
    def GroupTransformApply(gem,aply= False):
        OB = []
        for ob in gem.children:
            selectObj(ob)
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            if aply:bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            OB.append(ob)
        
        selectObj(gem)
        if aply:bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        for ob in OB:
            set_parent(gem,ob) 
                   

class buildUnfold:
    def __init__(self,verts):
        self.verts =  verts
    def starPentagonShape(self,face):
        verts = self.verts
        amt = 2 / (3 + sqrt(5))
        shape.moveTo(verts[face[0]].x, verts[face[0]].y)
        mid = verts[face[0]].clone().lerp(verts[face[1]], amt)
        shape.lineTo(mid.x, mid.y)

        shape.lineTo(verts[face[3]].x, verts[face[3]].y);
        mid = verts[face[3]].clone().lerp(verts[face[4]], amt);
        shape.lineTo(mid.x, mid.y);

        shape.lineTo(verts[face[1]].x, verts[face[1]].y);
        mid = verts[face[1]].clone().lerp(verts[face[2]], amt);
        shape.lineTo(mid.x, mid.y);

        shape.lineTo(verts[face[4]].x, verts[face[4]].y);
        mid = verts[face[4]].clone().lerp(verts[face[0]], amt);
        shape.lineTo(mid.x, mid.y);

        shape.lineTo(verts[face[2]].x, verts[face[2]].y);
        mid = verts[face[2]].clone().lerp(verts[face[3]], amt);
        shape.lineTo(mid.x, mid.y);

        return shape;        


def regularFaces(bm,verts,faces):
    V = []
    for v in verts:
        V.append(bm.verts.new(v))
        bm.verts.index_update()    
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    #f = bm.faces.new([V[0],V[1],V[3],V[4]])
    for face  in faces:
        vs   = [] 
        bpy.ops.mesh.select_all(action='DESELECT')
        for f in face:
            bm.verts[f].select_set(True)
        bpy.ops.mesh.edge_face_add()

def cosAngle(v0, v1, v2):
    e1 = Vector(v0) - Vector(v1)
    e2 = Vector(v2)  - Vector(v1)
    return e1.dot(e2) / (e1.length * e2.length)

def parse_poly(n):
    path =   f"{bpy.utils.user_resource( 'SCRIPTS')}\\addons\\hedronize\\develop\\data"
    filename = f"{path}\\{n}"
    faces = []
    verts = []
    hinges = []
    sfaces = {}
    with open(filename) as file:
        i = 0
        while cont := file.readline().rstrip():
            if  cont == ":sfaces":
                #token 8 4{3} 4{4}
                line   = file.readline().rstrip()
                spl = line.split(" ")
                sfaces["N"] = N = int(spl[0])
                n = 0
                for f in spl[1:]:
                    f1 = f.split("{")
                    num  =  int(f1[0])
                    ngon =  int(f1[1].split("}")[0])
                    assert ngon not in sfaces,f"ngon multiple error {line}    file {filename}"
                    sfaces[ngon] = num
                    n += num
                assert N == n ,f"Face Num incorrect {N} != {n}  file {filename}"
            if  cont == ":net":
                line   = file.readline().rstrip()
                nFaces = int(line.split(" ")[0], 10)
                for j  in range(nFaces):
                    line = file.readline().rstrip().split(" ")
                    face = []
                    for k in  range(1,len(line)):
                        face.append(int(line[k], 10))
          
                    faces.append(face)
        
            elif cont == ":hinges":

                line    = file.readline().rstrip()
                nHinges = int(line, 10)
                for j in range(nHinges):
                    line = file.readline().rstrip().split(" ")
                    hinges.append([
                        int(line[0], 10),
                        int(line[1], 10),
                        int(line[2], 10),
                        int(line[3], 10),
                        float(line[4])
                    ])
                
            elif  cont == ":vertices":
                    nums = file.readline().rstrip().split(" ")
                    nVerts = int(nums[len(nums) - 1], 10)
                    for j in range(nVerts):
                        line = file.readline().rstrip()
                        line = re.sub(r"\[(.*?)\]","",line).split(" ") 
                        #verts.append(Vector(float(line[0]),float(line[1]),float(line[2])))
                        verts.append( [ float(line[0]),float(line[1]),float(line[2])] )
    
    return faces,verts,hinges,sfaces

def update_matrices(root,amount):
    def cb(obj):
        if "userData" in obj:
            u = obj["userData"]
            offset = Vector(u["offset"])

            t1 = Matrix()
            r  = Matrix()
            t2 = Matrix()

            t1.translation  = -offset
            angle = amount / 100 * (math.pi - u["amount"])
            r = r.Rotation( angle ,4,Vector(u["axis"]) )
            t2.translation  = offset
            obj.matrix_local = t2 @ r @ t1
            #print(f"obj.matrix_world {obj.matrix_world}")
            #print(f"location         {obj.location}")
            #print(f"rotation         {obj.rotation_euler}")
            #print(f"trav   {obj.name}   ofs {offset}  angle {angle}   axis {Vector(u['axis'])} ")

    def traverse(o):
        cb(o)
        for c in o.children:
            traverse(c)
            
    traverse(root)
    #c = new THREE.Box3().setFromObject(root).center();
    c = bboxCenter(root)
    root.location -= c
 
def regularFaces_noMesh(bm,verts,faces,face):
    #print(f"FACE ================ {face}")
    regular  = True
    VN = 0
    V = []
    #print(f"FACES ================ {faces[face]}")
    for vid in faces[face]:
        V.append(bm.verts.new(verts[vid]))
        VN+=1
    bm.verts.ensure_lookup_table()
    bm.faces.new(V)
    bm.faces.ensure_lookup_table()
    regL = None
    for e in bm.faces[0].edges:
        L =   e.calc_length()
        if regL is None:
            regL = L
        elif not np.isclose(L,regL , atol=0.001):
            regular  = False
    return f"reg-{VN}" if regular else f"nreg-{VN}"

def add_linear_driver(pbone,parent,index = 0,dataPath ="rotation_euler[0]",ctrl =False):

    if parent["angle"] == 0:
        assert ctrl,"need to be ctrl bone"
        parent = ctrl
        ctrl = True
    else:
        ctrl = False
    VAR  = "var"
    prop = "rotation_euler"
    if index != -1:
        d = pbone.driver_add(prop, index ).driver
    else:
        d = pbone.driver_add(prop ).driver
    
    v = d.variables.new()
    v.name                 = VAR
    v.targets[0].id        = parent.id_data
    v.targets[0].data_path = f"pose.bones[\"{parent.name}\"].rotation_euler[0]"
    angle   = pbone["angle"]
    
    if ctrl:
        d.expression = f"{angle}*{VAR}/pi/2." 
    else:
        pangle  = parent["angle"]
        d.expression = f"{angle}*{VAR}/{pangle}" 
    return

def translation(arm):
    selectObj(arm)
    bpy.ops.object.posemode_toggle()
    root = arm.pose.bones[0]
    for pb in  root.children_recursive:
        pb.rotation_euler.x = pb["angle"]





def LoadPoly(name,N):

    faces,verts,hinges,_ = parse_poly(N)
    #print(f"face {len(faces)}  verts {len(verts)}   hinges {len(hinges)}" )
    m = bpy.data.meshes.new(name = name)
    o = bpy.data.objects.new(name,m)
    bpy.context.scene.collection.objects.link(o)
    selectObj(o)
    bpy.ops.object.editmode_toggle()

    bm = get_bmfromObj(o)
    regularFaces(bm,verts,faces)
    bm.free()
    bpy.ops.object.editmode_toggle()
    return o

def Build_poly(n,Name,col):
    faces,verts,hinges,_ = parse_poly(n)

    def newNode(fid):
        #name = f"{Name}-{fid}"
        name = "{}:{:003d}".format(Name,fid)
        m = bpy.data.meshes.new(name = name)
        o = bpy.data.objects.new(name,m)
        bpy.context.scene.collection.objects.link(o)
        selectObj(o)
        bpy.ops.object.editmode_toggle()
        bm = get_bmfromObj(o)
        regularFaces(bm,verts,[faces[fid]])
        bm.free()
        bpy.ops.object.editmode_toggle()
        moveCol(col,o)
        return o


    def build_tree(face, side = None, angle = None, parent = None):
        side  = 0 if  (side == None) else  side
        angle = math.pi if (angle == None)  else angle
        
        parentName =  -1 if (parent == None) else  int(parent.name.split(":")[1])
        thisFace   =  faces[face]
        interiorAngle = cosAngle(verts[thisFace[0]], verts[thisFace[1]],verts[thisFace[2]])

        node = newNode(face)
        ax   = Vector((0,0,0))
        s1   = thisFace[side]
        s2   = thisFace[(side + 1) % len(thisFace)]
        

        #node.add(new THREE.Line(shape.createPointsGeometry()));
        #if (thisFace.length == 5 and interiorAngle > 0.5) :
            #star-pentagon special case
        #    shape = starPentagonShape(thisFace)
        #print(f"face {face}  side {side}   offset vert{s1} = {verts[s1]}   axis vert[{s2}] - vert[{s1}]  amount {angle}")
                    
 
        node["userData"] = {
        "offset" : Vector(verts[s1]),
        "axis"   : (Vector(verts[s2])  - Vector(verts[s1])).normalized(),
        "amount" : angle
        }
        
        if parent != None :
            set_parent(parent,node)


        for n in range(len(hinges)):
            hinge = hinges[n]
            if hinge[0] == face and hinge[2] != parentName:
                build_tree(hinge[2], hinge[3], hinge[4], node)
            elif hinge[2] == face and hinge[0] != parentName:
                build_tree(hinge[0], hinge[1], hinge[4], node)
        
        return node
    

    #print(faces)
    #print(verts)
    #print(hinges)
    return build_tree(hinges[0][0])

def Build_bones(n,Name):

    
    deselect_object()
    bpy.ops.object.armature_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    arm = bpy.context.object
    arm.name = f"{Name}:arm"
    bpy.ops.object.editmode_toggle()
    eb = arm.data.edit_bones
    eb[0].name = "Ctrl"
    #bpy.ops.armature.select_all(action='SELECT')
    #bpy.ops.armature.delete()
    bpy.ops.object.editmode_toggle()
    
    faces,verts,hinges,_ = parse_poly(n)

    def newNode(fid):
        name = "{}:{:003d}".format(Name,fid)
        bm = bmesh.new()
        primtype =  regularFaces_noMesh(bm,verts,faces,fid)
        bm.free()
        return name ,primtype

    def build_tree(face, side = None, angle = None,bparent = None):
        side  = 0 if  (side == None) else  side
        angle = math.pi if (angle == None)  else angle
        
        parentName =  -1 if (bparent == None) else  int(bparent.split(":")[1])
        thisFace   =  faces[face]
        

        Name,type = newNode(face)
        selectObj(arm)
        bpy.ops.object.editmode_toggle()
        eb = arm.data.edit_bones
        
        ax   = Vector((0,0,0))
        s1   = thisFace[side]
        s2   = thisFace[(side + 1) % len(thisFace)]
        vn   = len(thisFace)
        even = True if vn % 2  == 0  else False
        s3   = thisFace[(side - vn//2) % len(thisFace)]
        #print(f"FACES Bone ================ side {s1} adj {s2}  even {even}  mid {s3}  ")
        if even :
            s4    = thisFace[(side - vn//2+1) % len(thisFace)]
            tail  = ( Vector(verts[s3]) + Vector(verts[s4]) )/2.
            #print(f"FACES Bone ================ even {s4}   ")
        else:
            tail  = Vector(verts[s3]) 
        
        b = eb.new(Name)
        b.head = (Vector(verts[s2]) + Vector(verts[s1]))/2.
        b.tail =  tail

       
        #print(f" bparent {bparent} head {(Vector(verts[s2]) + Vector(verts[s1]))/2.} tail  {tail}    prim type {type} ")
        if bparent != None :
            b.use_connect = False
            b.parent  = eb[bparent]
 
        bpy.ops.object.editmode_toggle() 
        bpy.ops.object.posemode_toggle()
        pb = arm.pose.bones[Name]
        pb["angle"] = math.pi - angle
        pb["prim"] = type
        pb.rotation_mode = 'XYZ'
        if bparent != None :
            add_linear_driver(pb,arm.pose.bones[bparent],ctrl = arm.pose.bones[0])
            
        bpy.ops.object.posemode_toggle()

        for n in range(len(hinges)):
            hinge = hinges[n]
            if hinge[0] == face and hinge[2] != parentName:
                build_tree(hinge[2], hinge[3], hinge[4], Name )
            elif hinge[2] == face and hinge[0] != parentName:
                build_tree(hinge[0], hinge[1], hinge[4], Name)
        
        return 

    build_tree(hinges[0][0])    
    selectObj(arm)
    bpy.ops.object.editmode_toggle()
    eb = arm.data.edit_bones
    bpy.ops.armature.select_all(action='SELECT')
    bpy.ops.armature.calculate_roll(type='GLOBAL_POS_Z')
    bpy.ops.object.editmode_toggle()
    arm.pose.bones["Ctrl"].rotation_mode = 'XYZ'


    return arm

def BakeShapeKey(Ra,name,cname,num):

    dst   = bpy.data.objects[cname]

    sk_basis = dst.shape_key_add(name = 'Basis')
    sk_basis.interpolation = 'KEY_LINEAR'
    #dst.data.shape_keys.use_relative = False
    
    Name = "{}:{:003d}".format(name,0)
    root   = bpy.data.objects[Name]
    sk_name = None

    for n in range(Ra):
        pct = (n+1) * 100/Ra
        update_matrices(root,pct)
        bpy.ops.object.select_all(action='DESELECT')
        
        
        sk = dst.shape_key_add(name = 'Deform')
        sk.interpolation = 'KEY_LINEAR'
        bl = dst.data.shape_keys.key_blocks
        sk.name = f"dev-{pct}"
        if sk_name:bl[sk.name].relative_key = bl[sk_name]

        # position each vert
        for p in dst.data.polygons:
            Name = "{}:{:003d}".format(name,p.index)
            print(f"face  {Name}   ")
            src   = bpy.data.objects[Name]
            me    = src.data
            mw    = src.matrix_world
            for v in p.vertices:
                sk.data[v].co  = mw @ me.vertices[v].co
                #print(f"face{p.index}    V{v}    co {sk.data[v].co}")
        sk_name = sk.name

def applyShapekey(ob,apply = False):
    selectObj(ob)
    bpy.context.view_layer.objects.active = ob
    if ob.data.shape_keys:
        SK = ob.data.shape_keys
        N = len(SK.key_blocks)
        kid = 0
        basis = False
        for i in range(N):
            sk = SK.key_blocks[kid]
            if sk.name  != "Basis":
                ob.active_shape_key_index =  SK.key_blocks.find(sk.name )
                bpy.ops.object.shape_key_remove(all=False)
            else:
                basis = True
                kid +=1
        assert basis ,f"NOt Found  Basis Key {SK}  {ob.name} "
        N = len(SK.key_blocks)
        assert N == 1,f"Shakey multiple Found {SK} {ob.name}"
        ob.active_shape_key_index =  0
        bpy.ops.object.shape_key_remove(all=False)

        #bpy.data.shape_keys[SK.name].name = "NOUSE"     
    return 


def broadcastModifiers(aply):
    obj  = bpy.context.selected_objects
    for ob in obj:
        selectObj(ob)
        if aply== "apply":bpy.ops.object.apply_all_modifiers()
        elif aply == "delete":bpy.ops.object.delete_all_modifiers()



def LayoutDevelop(box,lt):
    box.prop(lt, "family")
    box.prop(lt, "type")
    box.separator()
 
def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):
    def draw(self, context):
        self.layout.label(text = message)
    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


def ExecuteDevelop(lt,family= None,num = None):
    print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!exec develop ')
    ltp = bpy.context.window_manager.hedronize_develop_params

    if ltp.type == "shapekey_remove":
        ob = bpy.context.object
        applyShapekey(ob)
        return True

    if ltp.type == "modifiers_bcast":  
        broadcastModifiers(ltp.modbc)
        return True


    Hnames = HedronNames()
    fam    = ['Pla','Kep','Arc','Pri','Arc2','Joh','Oth']
    if not family:
        family = lt.family
    phe    = Hnames["families"][fam.index(family)]["polyhedra"]
    if not num:
        num  = int(lt.type)

    name = f"{family}-{num}"
    print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>execdevelop {name}")
    

    Name  = None
    for p in phe:
        if num == int(p['number']):
            Name = p["name"]
            break
    assert Name,f"Not Found {name} "


    col   = newCollection("Hedron",dup = False)
    col.color_tag = 'COLOR_03'
    
    hedName  = f"{name}:hedron"
    hed =  OPSHedron.QueryHedron(hedName,Name)


    if ltp.type =="shapekey":
        col.objects.link(hed)

    elif ltp.type =="armature":
        o = Build_bones(num,name)    

    elif ltp.type == "cellhedron":
        cs     = CellSeparator
        assets = {}
        print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>MODE  {ltp.mode}   Asset   {ltp.assets} ")
        if ltp.mode == "asset":
            if not ltp.assets:
                ShowMessageBox(message = "Asset Collection Not Found ", title = "Warning", icon = 'INFO')
                return False   
            else:
                for c in ltp.assets.children:
                    n = c.name.split(":")[1]
                    assets[n] = c.name
                print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Asset   {assets} ")
        cs.InitFromHedron(hed,ltp.mode,uuid = True,assets = assets,arm = ltp.arm)
        cs.Separate()


    OPSHedron.CleanUpHedron(Name)
    return True
