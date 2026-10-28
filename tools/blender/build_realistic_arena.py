import bpy, math, os, sys
if os.path.isdir('/usr/lib/python3/dist-packages'):
    sys.path.append('/usr/lib/python3/dist-packages')
from mathutils import Vector

# Clean-room arena rebuild: remove all previous scene geometry and generate a new venue.
OUT = os.path.abspath("assets/realistic-arena.glb")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.curves):
    for block in list(datablocks):
        if block.users == 0: datablocks.remove(block)

def mat(name, color, rough=.65, metal=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    if "concrete" in name.lower() or "floor" in name.lower():
        n=m.node_tree.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value=34; n.inputs["Detail"].default_value=3
        b=m.node_tree.nodes.new("ShaderNodeBump"); b.inputs["Strength"].default_value=.11; b.inputs["Distance"].default_value=.035
        m.node_tree.links.new(n.outputs["Fac"],b.inputs["Height"]); m.node_tree.links.new(b.outputs["Normal"],bs.inputs["Normal"])
    return m

M={
 "floor":mat("Arena floor concrete",(.16,.19,.20),.9),
 "concrete":mat("Structural concrete",(.31,.34,.34),.88),
 "concrete_dark":mat("Dark concrete joints",(.10,.13,.14),.9),
 "steel":mat("Dark structural steel",(.025,.04,.05),.32,.72),
 "metal":mat("Brushed metal",(.34,.40,.42),.3,.75),
 "blue":mat("Arena blue seats",(.012,.07,.16),.4,.02),
 "cyan":mat("Arena cyan seats",(.015,.20,.23),.4,.02),
 "navy":mat("Arena navy seats",(.006,.022,.05),.43,.02),
 "glass":mat("Concourse glass",(.035,.10,.13),.22,.35),
 "screen":mat("LED display",(.002,.009,.014),.22,.15),
 "light":mat("LED diffuser",(.88,.95,1),.25),
 "accent":mat("Cyan architectural accent",(.015,.28,.34),.3,.25),
}
builders={}
def add_box(k,c,s,ry=0):
    vs,fs=builders.setdefault(k,([],[])); x,y,z=c; sx,sy,sz=[v/2 for v in s]; base=len(vs)
    co,si=math.cos(ry),math.sin(ry)
    for a,b,d in [(-sx,-sy,-sz),(sx,-sy,-sz),(sx,sy,-sz),(-sx,sy,-sz),(-sx,-sy,sz),(sx,-sy,sz),(sx,sy,sz),(-sx,sy,sz)]:
        vs.append((x+a*co+d*si,y+b,z-a*si+d*co))
    fs.extend([(base,base+3,base+2,base+1),(base+4,base+5,base+6,base+7),(base,base+1,base+5,base+4),(base+1,base+2,base+6,base+5),(base+2,base+3,base+7,base+6),(base+3,base,base+4,base+7)])
def beam(k,a,b,t,depth=None):
    a,b=Vector(a),Vector(b); d=b-a
    if d.length<.001:return
    q=Vector((0,0,1)).rotation_difference(d.normalized()); mid=(a+b)/2
    vs,fs=builders.setdefault(k,([],[])); base=len(vs); h=t/2; dep=(depth or t)/2; l=d.length/2
    for x,y,z in [(-h,-dep,-l),(h,-dep,-l),(h,dep,-l),(-h,dep,-l),(-h,-dep,l),(h,-dep,l),(h,dep,l),(-h,dep,l)]:
        vs.append(tuple(q@Vector((x,y,z))+mid))
    fs.extend([(base,base+3,base+2,base+1),(base+4,base+5,base+6,base+7),(base,base+1,base+5,base+4),(base+1,base+2,base+6,base+5),(base+2,base+3,base+7,base+6),(base+3,base,base+4,base+7)])

# Ground slab and structural outer shell.
add_box("floor",(0,-.45,0),(78,.7,96))
for z in (-45,45): add_box("concrete",(0,4,z),(72,8,1.6))
for x in (-36,36): add_box("concrete",(x,4,0),(1.6,8,90))
# Concourse glass ribbon and mullions.
for z in (-44.05,44.05):
    add_box("glass",(0,5.0,z),(65,4.2,.12))
    for x in range(-32,33,2): add_box("steel",(x,4.8,z),( .07,3.8,.1))
for x in (-35.05,35.05):
    add_box("glass",(x,5,0),(.12,4.2,84))
    for z in range(-42,43,2): add_box("steel",(x,4.8,z),(.1,3.8,.07))
# A single continuous oval bowl is generated from a consistent parametric cross-section.
# No post-hoc fascia patch: the lower support wall is part of the initial design.
N=320; ROWS=24
inner_a,inner_b=15.8,24.6
for i in range(N):
    t=2*math.pi*i/N
    # Inner retaining wall follows the exact same ellipse as the first tier.
    x=(inner_a-.35)*math.sin(t); z=(inner_b-.35)*math.cos(t)
    tangent=2*math.pi*math.sqrt((inner_a*inner_a+inner_b*inner_b)/2)/N
    rot=math.atan2(inner_a*math.cos(t),-inner_b*math.sin(t))
    add_box("concrete",(x,.68,z),(tangent*1.18,1.45,.95),rot)
    add_box("concrete_dark",(x,1.43,z),(tangent*1.12,.10,.98),rot)
for row in range(ROWS):
    a=inner_a+row*.62; b=inner_b+row*.72
    y=1.55+row*.43
    for i in range(N):
        t=2*math.pi*i/N; x=a*math.sin(t); z=b*math.cos(t)
        rot=math.atan2(a*math.cos(t),-b*math.sin(t))
        tangent=2*math.pi*math.sqrt((a*a+b*b)/2)/N
        sw=max(.43,min(.72,tangent*.82))
        # Solid riser, seat pan, and backrest: all generated together as one seating system.
        add_box("concrete",(x,y-.27,z),(sw*1.18,.48,.92),rot)
        color=("blue","cyan","navy")[(i//4+row*2)%3]
        add_box(color,(x,y+.025,z),(sw,.13,.48),rot)
        norm=math.sqrt((x/a)**2+(z/b)**2)
        nx=x/max(norm,.001); nz=z/max(norm,.001)
        add_box(color,(x+nx*.18,y+.24,z+nz*.18),(.075,.32,.48),rot)
    # Aisle rail at every fourth seat segment; avoids dense, noisy railing geometry.
    ra,rb=a+.48,b+.48
    for i in range(0,N,4):
        t=2*math.pi*i/N; x=ra*math.sin(t); z=rb*math.cos(t)
        rot=math.atan2(ra*math.cos(t),-rb*math.sin(t))
        tl=2*math.pi*math.sqrt((ra*ra+rb*rb)/2)/N*4
        add_box("steel",(x,y+.40,z),(.055,.72,.055),rot)
        add_box("metal",(x,y+.77,z),(tl,.055,.055),rot)
# Recessed concourse ring behind the upper seating bowl.
for y,a,b in [(7.2,29.2,40.0),(7.45,30.4,41.2)]:
    for i in range(N):
        t=2*math.pi*i/N; x=a*math.sin(t); z=b*math.cos(t)
        rot=math.atan2(a*math.cos(t),-b*math.sin(t))
        tl=2*math.pi*math.sqrt((a*a+b*b)/2)/N
        add_box("concrete_dark" if y<7.3 else "concrete",(x,y,z),(tl*1.12,.24,.85),rot)
# Roof perimeter ring and cross-braced steel trusses.
for z in (-40,40): add_box("steel",(0,17.4,z),(72,.8,3.2))
for x in (-34,34): add_box("steel",(x,17.4,0),(3.2,.8,80))
for z in range(-38,39,4):
    beam("steel",(-33,17,z),(33,17,z),.22,.28)
    beam("steel",(-33,17,z),(0,21,z),.16,.2)
    beam("steel",(0,21,z),(33,17,z),.16,.2)
    beam("metal",(-33,17,z),(33,17,z+2),.075,.12)
for x in range(-30,31,5):
    beam("metal",(x,17,-39),(x,17,39),.13,.18)
    beam("steel",(x,17,-39),(x,20,0),.11,.15)
    beam("steel",(x,20,0),(x,17,39),.11,.15)
# Acoustic roof panels leave the steel truss grid visible.
for x in range(-30,31,6): add_box("concrete_dark",(x,20.5,0),(5.4,.18,75))
# High-bay light housings and suspended luminous diffusers.
for x in (-25,-15,-5,5,15,25):
    for z in (-30,-15,0,15,30):
        add_box("steel",(x,19.15,z),(2.6,.20,.75))
        add_box("light",(x,19.02,z),(2.25,.06,.52))
# Scoreboard, suspended fascia and perimeter LED ribbon.
add_box("steel",(0,11.6,-36.2),(13,5.5,.8)); add_box("screen",(0,11.6,-35.72),(12.1,4.6,.10))
for z in (-38.7,38.7):
    add_box("steel",(0,12.5,z),(62,1.0,.45)); add_box("accent",(0,12.5,z-.24),(60,.12,.06))
# Lower-level aisle lights and portals; gaps remain at four cardinal access points.
for side in (-1,1):
    for z in range(-34,35,4):
        add_box("accent",(side*26.5,2.0,z),(.07,.12,.75))
    for z in (-21,21):
        add_box("concrete_dark",(side*18,2.0,z),(3.2,2.6,.45))
# Batch geometry into one mesh per material for web performance.
for key,(verts,faces) in builders.items():
    if not verts: continue
    mesh=bpy.data.meshes.new("Arena_"+key); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new("Arena_"+key,mesh); bpy.context.collection.objects.link(obj); obj.data.materials.append(M[key])
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode="OBJECT"); obj.select_set(False)
# Convert authored Y-up coordinates to glTF/Babylon-compatible orientation.
bpy.ops.object.select_all(action="SELECT")
for obj in bpy.context.selected_objects:
    obj.rotation_euler.x=math.radians(90); bpy.context.view_layer.objects.active=obj
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)
bpy.ops.export_scene.gltf(filepath=OUT,export_format="GLB",use_selection=True,export_apply=True)
print("ARENA_REBUILD_OK",OUT,os.path.getsize(OUT))
