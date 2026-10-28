import bpy, math, os
from mathutils import Vector

# Fresh-build: premium indoor championship arena for badminton / multi-sport finals.
OUT = os.path.abspath("assets/realistic-arena.glb")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes,bpy.data.curves,bpy.data.materials):
    for block in list(datablocks):
        if block.users == 0: datablocks.remove(block)

def mat(name, color, rough=.65, metal=0.0, noise=0.0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF"); p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Roughness"].default_value=rough; p.inputs["Metallic"].default_value=metal
    if noise:
        n=m.node_tree.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value=noise; n.inputs["Detail"].default_value=3
        b=m.node_tree.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value=.16; b.inputs["Distance"].default_value=.035
        m.node_tree.links.new(n.outputs["Fac"],b.inputs["Height"]); m.node_tree.links.new(b.outputs["Normal"],p.inputs["Normal"])
    return m
concrete=mat("Architectural precast concrete",(.28,.33,.35),.84,0,.8)
dark=mat("Deep graphite steel",(.045,.065,.075),.36,.72)
steel=mat("Brushed structural steel",(.25,.32,.34),.32,.78)
glass=mat("Smoked blue glass",(.045,.13,.16),.2,.32)
floor=mat("Competition hall maple",(.49,.32,.18),.42,0,80)
court=mat("Championship court teal",(.025,.19,.22),.36,0,90)
court2=mat("Court boundary blue",(.045,.12,.24),.43)
white=mat("Court line ivory",(.88,.91,.84),.38)
seatA=mat("Arena seat ocean blue",(.025,.15,.22),.42)
seatB=mat("Premium seat cyan",(.04,.35,.39),.4)
rubber=mat("Walkway rubber",(.07,.09,.10),.8,.05)
screen=mat("Scoreboard black glass",(.006,.014,.02),.18,.18)
led=mat("LED cyan",(.04,.65,.82),.26,.25)
warm=mat("Warm architectural light",(.95,.77,.49),.3)
def cube(name,loc,scale,ma,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o=bpy.context.object; o.name=name; o.dimensions=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); o.data.materials.append(ma)
    if bevel:
        mod=o.modifiers.new("Machined softened edges","BEVEL"); mod.width=bevel; mod.segments=2
        o.modifiers.new("Weighted corner normals","WEIGHTED_NORMAL")
    return o
def beam(name,a,b,width,ma,depth=None):
    a,b=Vector(a),Vector(b); d=b-a
    o=cube(name,(a+b)/2,(width,depth or width,d.length),ma,min(width*.16,.08))
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector((0,0,1)).rotation_difference(d.normalized()); return o
def matbox(name,loc,scale,ma):
    return cube(name,loc,scale,ma,.025)
# Massive polished floor slab and central raised competition platform
cube("Continuous reinforced slab",(0,-.48,0),(94,.9,112),concrete,.16)
cube("Hall sports floor",(0,.015,0),(78,.12,92),floor,.04)
cube("Competition platform shadow plinth",(0,.10,0),(22,.22,31),dark,.08)
cube("Competition platform rubber edge",(0,.225,0),(21.5,.12,30.5),rubber,.035)
cube("Competition court surround",(0,.30,0),(18.6,.10,28.8),court2,.025)
cube("Official court playing surface",(0,.365,0),(13.4,.045,24.4),court,.012)
# Court markings: precise thin inset-looking lines
y=.392
for x in [-6.55,6.55]: cube("Doubles sideline",(x,y,0),(.045,.012,23.8),white,.004)
for z in [-11.85,11.85]: cube("Baseline",(0,y,z),(13.15,.012,.045),white,.004)
cube("Short service line near",(0,y,-4.2),(13.1,.012,.04),white,.003)
cube("Short service line far",(0,y,4.2),(13.1,.012,.04),white,.003)
cube("Center service line",(0,y,0),(.035,.012,8.4),white,.003)
cube("Net tape",(0,1.1,0),(13.7,.12,.11),white,.025)
for x in [-6.75,6.75]:
    cube("Net post",(x,.92,0),(.12,1.65,.12),steel,.035)
# Court perimeter LED advertising, with continuous fascia and light strips
for z in [-15.7,15.7]:
    cube("Courtside LED fascia",(0,.78,z),(29,.9,.38),dark,.06)
    cube("Continuous cyan LED ribbon",(0,1.02,z-.205),(28.4,.045,.025),led,.008)
    for i in range(18):
        cube("Digital sponsor panel",(-13.2+i*1.55,.82,z-.205),(1.38,.38,.025),screen,.025)
for x in [-15.0,15.0]:
    cube("Side LED fascia",(x,.78,0),(.38,.9,29),dark,.05)
    cube("Side LED ribbon",(x+(-.205 if x<0 else .205),1.02,0),(.025,.045,28.4),led,.008)
# Bowl: 20 rising tiers on four sides, dense continuous seat blocks, premium color zoning
for row in range(20):
    zbase=18.0+row*1.35; ybase=.15+row*.42
    # end stands
    for side in [-1,1]:
        cube("End stand concrete riser",(0,ybase,side*zbase),(47,.32,1.20),concrete,.04)
        for col in range(52):
            x=-22.5+col*.88
            ma=seatB if (col%13 in (0,1) and row%4==0) else seatA
            cube("Individual arena seat",(x,ybase+.28,side*(zbase+.08)),(.68,.34,.55),ma,.07)
    # long-side stands
    for side in [-1,1]:
        xbase=12.0+row*1.22
        cube("Side stand concrete riser",(side*xbase,ybase,0),(1.08,.32,37),concrete,.04)
        for col in range(42):
            z=-18+col*.88
            ma=seatB if (col%13 in (0,1) and row%4==0) else seatA
            cube("Individual arena seat",(side*(xbase+.06),ybase+.28,z),(.55,.34,.68),ma,.07)
# Premium upper concourse balconies and glass parapets
for z in [-46,46]:
    cube("Upper concourse balcony",(0,9.1,z),(57,.55,3.0),dark,.12)
    cube("Concourse glass balustrade",(0,10.0,z-(-1.3 if z<0 else 1.3)),(57,1.45,.10),glass,.025)
for x in [-43,43]:
    cube("Upper side concourse",(x,9.1,0),(3,.55,72),dark,.12)
    cube("Side glass balustrade",(x+(-1.3 if x<0 else 1.3),10,0),(.1,1.45,72),glass,.025)
# Structural columns, perimeter trusses, long-span roof and acoustic ceiling
for x in [-40,-28,-16,0,16,28,40]:
    for z in [-47,47]:
        cube("Main steel column",(x,12,z),(.65,24,.65),steel,.08)
for z in [-47,47]:
    beam("Roof perimeter girder",(-44,24,z),(44,24,z),.85,steel)
for x in [-43,-32,-21,-10,1,12,23,34,43]:
    beam("Long span roof truss",(x,23,-49),(x,23,49),.32,steel)
    beam("Truss diagonal A",(x,23,-49),(x+5,27,0),.16,dark)
    beam("Truss diagonal B",(x+5,27,0),(x,23,49),.16,dark)
for z in [-38,-25,-12,0,12,25,38]:
    beam("Roof cross brace",(-43,26,z),(43,26,z),.18,dark)
cube("Acoustic roof canopy",(0,28,0),(90,.8,104),dark,.25)
# Repeating acoustic baffles
for x in range(-40,41,4):
    cube("Ceiling acoustic baffle",(x,27.48,0),(.22,.14,94),steel,.025)
# High-bay light banks
for x in [-28,-14,0,14,28]:
    for z in [-32,-16,0,16,32]:
        cube("High bay luminaire",(x,26.8,z),(2.8,.24,1.05),warm,.08)
        cube("Luminaire diffuser",(x,26.64,z),(2.45,.035,.78),white,.025)
# Four-sided central scoreboard, hanging from a truss
cube("Scoreboard suspension",(0,25,0),(.35,4,.35),steel,.04)
for rot in [0,math.pi/2,math.pi,3*math.pi/2]:
    o=cube("Championship scoreboard",(0,21.2,0),(9.5,3.4,.38),screen,.12); o.rotation_euler[2]=rot
    o=cube("Scoreboard cyan header",(0,22.25,.22),(8.7,.12,.04),led,.015); o.rotation_euler[2]=rot
    o=cube("Scoreboard score divider",(0,21.05,.23),(.055,1.65,.04),steel,.01); o.rotation_euler[2]=rot
# Entrances, vomitory portals and illuminated wayfinding bands
for z in [-43,43]:
    for x in [-28,-14,14,28]:
        cube("Audience portal surround",(x,4.5,z),(4.0,7.0,.7),dark,.12)
        cube("Portal luminous lintel",(x,8.1,z), (3.2,.12,.08),led,.02)
# Exterior facade and glazed upper ring
for z in [-52,52]:
    cube("Exterior facade",(0,7.5,z),(88,14,1.1),concrete,.12)
    cube("Continuous clerestory glass",(0,15.5,z),(82,2.8,.16),glass,.025)
    cube("Facade LED line",(0,13.9,z-.6),(84,.07,.05),led,.01)
for x in [-45,45]:
    cube("Exterior side facade",(x,7.5,0),(1.1,14,100),concrete,.12)
    cube("Side clerestory glass",(x,15.5,0),(.16,2.8,96),glass,.025)
# Entrance steps and media/officials desk
for i in range(5):
    cube("Main entrance broad step",(0,.15+i*.22,-55+i*.9),(22,.28,.95),concrete,.06)
cube("Officials media desk",(0,1.0,-13.9),(9,.85,.8),dark,.1)
for x in [-3.1,0,3.1]:
    cube("Desk status display",(x,1.48,-14.32),(2.3,.055,.025),led,.008)
# Lighting and world
world=bpy.context.scene.world
if world is None: world=bpy.data.worlds.new("Arena World"); bpy.context.scene.world=world
world.use_nodes=True; world.node_tree.nodes["Background"].inputs[0].default_value=(.045,.065,.085,1); world.node_tree.nodes["Background"].inputs[1].default_value=.35
for name,loc,power,size in [("Court key",(0,24,0),6500,18),("End fill",(0,22,-25),4200,14),("End fill far",(0,22,25),4200,14),("Side fill L",(-25,21,0),3500,12),("Side fill R",(25,21,0),3500,12)]:
    bpy.ops.object.light_add(type="AREA", location=loc); l=bpy.context.object; l.name=name; l.data.energy=power; l.data.shape="DISK"; l.data.size=size
    l.rotation_euler=(Vector((0,0,0))-l.location).to_track_quat("-Z","Y").to_euler()
# Optimized glTF export
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_apply=True, export_texcoords=True, export_normals=True, export_materials="EXPORT", export_cameras=False, export_lights=False)
print("Fresh championship arena exported:", OUT)
