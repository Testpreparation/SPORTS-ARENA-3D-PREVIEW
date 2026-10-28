import bpy, math, os
from mathutils import Vector, Quaternion

# Fast, batched Blender arena generator. Geometry is accumulated by material,
# avoiding thousands of separate objects and modifiers.
OUT = os.path.abspath("assets/realistic-arena.glb")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.curves):
    for block in list(datablocks):
        if block.users == 0:
            datablocks.remove(block)

def pbr(name, color, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    return m

M = {
 "concrete": pbr("Warm architectural concrete", (.32,.36,.37), .82),
 "concrete_light": pbr("Light precast concrete", (.49,.52,.52), .78),
 "steel": pbr("Graphite structural steel", (.055,.075,.085), .29, .78),
 "steel_light": pbr("Brushed aluminium", (.34,.39,.4), .24, .82),
 "glass": pbr("Smoked arena glass", (.12,.25,.29), .18, .35),
 "seat_blue": pbr("Deep blue seat polymer", (.018,.11,.17), .35, .04),
 "seat_teal": pbr("Teal seat polymer", (.025,.23,.26), .34, .03),
 "seat_navy": pbr("Navy seat polymer", (.012,.045,.085), .36, .02),
 "rubber": pbr("Dark rubber flooring", (.035,.055,.06), .86),
 "white": pbr("Warm white paint", (.88,.89,.84), .44),
 "screen": pbr("Scoreboard black glass", (.008,.02,.026), .2, .18),
 "light": pbr("LED diffuser", (.84,.94,1.0), .22),
 "accent": pbr("Arena cyan accent", (.01,.36,.43), .3, .35),
}
builders = {}
def builder(key):
    if key not in builders: builders[key] = [[], []]
    return builders[key]

def box(key, center, size, rot_y=0):
    vs, fs = builder(key)
    x,y,z = center; sx,sy,sz = [v/2 for v in size]
    base = len(vs)
    local = [(-sx,-sy,-sz),(sx,-sy,-sz),(sx,sy,-sz),(-sx,sy,-sz),
             (-sx,-sy,sz),(sx,-sy,sz),(sx,sy,sz),(-sx,sy,sz)]
    c,s = math.cos(rot_y), math.sin(rot_y)
    for a,b,d in local:
        vs.append((x+a*c+d*s, y+b, z-a*s+d*c))
    fs.extend([(base+0,base+3,base+2,base+1),(base+4,base+5,base+6,base+7),
               (base+0,base+1,base+5,base+4),(base+1,base+2,base+6,base+5),
               (base+2,base+3,base+7,base+6),(base+3,base+0,base+4,base+7)])

def beam(key, a, b, thickness, depth=None):
    a,b=Vector(a),Vector(b); d=b-a
    mid=(a+b)/2
    # Rectangular member aligned to the segment in X/Y/Z, suitable for trusses.
    obj_len=d.length
    if obj_len < 0.001: return
    # local box length is Z; rotate its Z axis onto the beam direction.
    q=Vector((0,0,1)).rotation_difference(d.normalized())
    vs,fs=builder(key); base=len(vs)
    t=thickness/2; dep=(depth if depth is not None else thickness)/2; l=obj_len/2
    for x,y,z in [(-t,-dep,-l),(t,-dep,-l),(t,dep,-l),(-t,dep,-l),
                  (-t,-dep,l),(t,-dep,l),(t,dep,l),(-t,dep,l)]:
        p=q @ Vector((x,y,z)) + mid
        vs.append(tuple(p))
    fs.extend([(base,base+3,base+2,base+1),(base+4,base+5,base+6,base+7),
               (base,base+1,base+5,base+4),(base+1,base+2,base+6,base+5),
               (base+2,base+3,base+7,base+6),(base+3,base,base+4,base+7)])

# Building shell and floor apron. Gameplay court is intentionally separate in Babylon.
box("rubber",(0,-.35,0),(48,.45,62))
box("concrete",(0,2.8,-29),(43,6,1.1))
box("concrete",(0,2.8,29),(43,6,1.1))
box("concrete",(-21.5,2.8,0),(1,6,57))
box("concrete",(21.5,2.8,0),(1,6,57))
# Glazed concourse bands and vertical mullions.
for z in (-28.35,28.35):
    box("glass",(0,3.4,z),(39,3.0,.09))
    for x in range(-19,20,2):
        box("steel",(x,3.4,z),(0.055,3.15,.08))
for x in (-21.0,21.0):
    box("glass",(x,3.4,0),(.08,3.0,53))
    for z in range(-26,27,2):
        box("steel",(x,3.4,z),(.08,3.15,.055))
# Concourse floor beams and repeated facade bays.
for z in (-27.6,27.6):
    box("steel",(0,5.15,z),(42,.22,.22))
    box("concrete_light",(0,6.2,z),(43,.38,.65))
for x in (-20.7,20.7):
    box("steel",(x,5.15,0),(.22,.22,56))
# Raised seating bowls: 9 rows with tier noses, seats, backs, and supports.
seat_mats=["seat_blue","seat_teal","seat_navy"]
for side in (-1,1):
    for row in range(9):
        z=side*(15.0+row*1.18)
        y=.25+row*.43
        box("concrete_light",(0,y-.19,z),(35,.34,1.02))
        box("steel",(0,y-.36,z-side*.42),(35,.075,.06))
        for x in range(-16.5,16.6,.62):
            # Seat base, pan, back and paired supports are batched by material.
            key=seat_mats[(int((x+16.5)*3)+row*2+(1 if side>0 else 0))%len(seat_mats)]
            box(key,(x,y+.05,z),(0.43,.12,.38))
            box(key,(x,y+.22,z-side*.15),(0.43,.29,.075))
            box("steel",(x-.15,y-.04,z),(0.035,.18,.035))
            box("steel",(x+.15,y-.04,z),(0.035,.18,.035))
    # Aisle rails and stair divisions.
    for x in (-17.5,-11.8,-6.0,0,6.0,11.8,17.5):
        for row in range(9):
            z=side*(15.0+row*1.18)
            y=.42+row*.43
            box("steel",(x,y+.28,z),(0.055,.5,.06))
            box("steel",(x,y+.52,z),(0.055,.045,.78))
# End seating banks.
for side in (-1,1):
    for row in range(6):
        x=side*(7.0+row*1.18)
        y=.22+row*.43
        box("concrete_light",(x,y-.18,0),(1.0,.34,26))
        for z in range(-12.2,12.3,.62):
            key=seat_mats[(int((z+12.2)*2)+row)%len(seat_mats)]
            box(key,(x,y+.05,z),(.38,.12,.43))
            box(key,(x+side*.15,y+.22,z),(.075,.29,.43))
# Roof ring, perimeter beams and dense exposed trusses.
box("steel",(0,14.0,-26),(45,.52,3.0))
box("steel",(0,14.0,26),(45,.52,3.0))
box("steel",(-21.5,14.0,0),(3.0,.52,52))
box("steel",(21.5,14.0,0),(3.0,.52,52))
for z in range(-24,25,4):
    beam("steel",(-20.5,13.5,z),(20.5,13.5,z),.16,.2)
    beam("steel",(-20.5,13.5,z),(0,16.2,z),.12,.16)
    beam("steel",(0,16.2,z),(20.5,13.5,z),.12,.16)
    beam("steel",(-20.5,13.5,z),(20.5,13.5,z+2),.075,.11)
for x in range(-20,21,5):
    beam("steel_light",(x,13.6,-25),(x,13.6,25),.12,.16)
    beam("steel",(x,13.6,-25),(x,16.0,0),.09,.13)
    beam("steel",(x,16.0,0),(x,13.6,25),.09,.13)
# Acoustic roof panels, separated into long strips to preserve a believable structure.
for x in range(-18,19,6):
    box("concrete",(x,16.35,0),(5.7,.16,48))
# LED lighting bars and high-bay fixtures.
for z in (-20,-10,0,10,20):
    for x in (-15,-7.5,0,7.5,15):
        box("light",(x,15.95,z),(2.1,.08,.24))
        box("steel",(x,15.72,z),(2.25,.07,.3))
# Large scoreboard and fascia panels.
box("steel",(0,8.4,-23.8),(8.8,4.2,.55))
box("screen",(0,8.4,-23.48),(8.1,3.5,.08))
box("accent",(0,6.12,-23.45),(8.2,.12,.09))
for side in (-1,1):
    box("steel",(0,9.8,side*25.5),(38,.75,.3))
    box("accent",(0,9.8,side*25.31),(37.5,.12,.05))
# Create one mesh object per material, with smooth normals where appropriate.
for key,(verts,faces) in builders.items():
    if not verts: continue
    mesh=bpy.data.meshes.new("Arena_"+key)
    mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new("Arena_"+key,mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(M[key])
    # Recalculate normals in edit mode for watertight boxes/beam faces.
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)
# Export optimized GLB.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_apply=True)
print("ARENA_EXPORT_OK", OUT, os.path.getsize(OUT))
