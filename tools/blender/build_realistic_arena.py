import bpy, math, os
from mathutils import Vector

# PREMIUM CHAMPIONSHIP INDOOR SPORTS HALL — generated from an empty Blender scene.
OUT = os.path.abspath("assets/realistic-arena.glb")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    for block in list(datablocks):
        if block.users == 0:
            datablocks.remove(block)

def material(name, color, rough=.5, metallic=0.0, noise=0.0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF"); p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Roughness"].default_value=rough; p.inputs["Metallic"].default_value=metallic
    if noise:
        n=m.node_tree.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value=noise; n.inputs["Detail"].default_value=3
        bump=m.node_tree.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value=.13; bump.inputs["Distance"].default_value=.035
        m.node_tree.links.new(n.outputs["Fac"],bump.inputs["Height"]); m.node_tree.links.new(bump.outputs["Normal"],p.inputs["Normal"])
    return m
def emit(name,color,strength=1.0):
    m=material(name,color,.28,0); p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Emission Color"].default_value=(*color,1); p.inputs["Emission Strength"].default_value=strength
    return m
concrete=material("Warm architectural concrete",(0.36,.40,.42),.82,0,42)
darkconcrete=material("Graphite structural concrete",(.075,.095,.11),.72,0,35)
steel=material("Powder coated structural steel",(.105,.145,.17),.32,.72)
silver=material("Brushed aluminum",(.42,.49,.52),.27,.78)
wood=material("Competition maple court",(.72,.48,.25),.36,0,95)
woodlight=material("Court maple highlight",(.83,.62,.36),.38,0,100)
blue=material("Tournament court blue",(.035,.19,.32),.45)
line=material("Court line ivory",(.93,.94,.87),.32)
seatnavy=material("Premium navy spectator seating",(.018,.07,.13),.38)
seatblue=material("Seat highlights",(.035,.20,.31),.36)
glass=material("Smoked blue glass",(.055,.16,.21),.22,.22)
roof=material("Roof acoustic panels",(.12,.16,.18),.74)
black=material("Matte black",(.012,.018,.023),.45)
led=emit("Cyan LED wayfinding",(.04,.72,.94),2.5)
warmled=emit("Warm arena signage",(.95,.43,.12),1.8)
whiteemit=emit("High output luminaire",(.88,.95,1.0),4.0)

def cube(name,loc,scale,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o=bpy.context.object; o.name=name; o.dimensions=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat: o.data.materials.append(mat)
    if bevel:
        mod=o.modifiers.new("Machined softened edges","BEVEL"); mod.width=bevel; mod.segments=2
        o.modifiers.new("Weighted corner normals","WEIGHTED_NORMAL")
    return o
def cyl(name,loc,radius,depth,mat,vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o=bpy.context.object; o.name=name
    if mat:o.data.materials.append(mat)
    return o
def beam(name,a,b,r,mat,vertices=10):
    d=Vector(b)-Vector(a); mid=(Vector(a)+Vector(b))/2
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=r, depth=d.length, location=mid)
    o=bpy.context.object;o.name=name;o.data.materials.append(mat);o.rotation_mode='QUATERNION';o.rotation_quaternion=d.to_track_quat('Z','Y')
    return o
def uvball(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat);return o
def linebox(name,x,y,z,w,h,thick,mat):
    cube(name,(x,y,z),(w,thick,h),mat,.008)
def curve_line(name,points,bevel,mat,cyclic=False):
    c=bpy.data.curves.new(name,"CURVE");c.dimensions='3D';c.resolution_u=1;c.bevel_depth=bevel;c.bevel_resolution=1
    s=c.splines.new("POLY");s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=cyclic;o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(mat);return o

# Building envelope and raised competition floor.
cube("Monolithic arena plinth",(0,-.65,0),(66,1.3,48),darkconcrete,.25)
cube("Main competition floor",(0,.12,0),(58,.32,41),concrete,.12)
cube("Continuous maple sports floor",(0,.34,0),(46,.18,32),wood,.035)
# Alternating subtle timber strips across the whole sports floor.
for i in range(32):
    z=-15.5+i*1.0
    cube("Maple floor board %02d"%i,(0,.438,z),(45.8,.012,.965),woodlight if i%4==0 else wood,.003)
# Blue apron around the courts.
cube("Blue competition apron",(0,.45,0),(38,.035,25),blue,.025)
# Four badminton courts, accurately marked, with nets and posts.
court_w=6.1; court_l=13.4; gap=.65; total=4*court_w+3*gap
start=-total/2+court_w/2
for idx in range(4):
    x=start+idx*(court_w+gap)
    cube("Court playing surface %d"%(idx+1),(x,.478,0),(court_w,.025,court_l),woodlight if idx%2==0 else wood,.01)
    y0=-court_l/2; y1=court_l/2
    # perimeter and doubles sidelines
    for z in (y0,y1):
        cube("Court %d baseline"%idx,(x,.5,z),(court_w,.018,.045),line,.006)
    for xx in (x-court_w/2,x+court_w/2):
        cube("Court %d sideline"%idx,(xx,.5,0),(.045,.018,court_l),line,.006)
    for z in (-3.96,3.96):
        cube("Court %d short service line"%idx,(x,.5,z),(court_w,.018,.035),line,.004)
    cube("Court %d center service line"%idx,(x,.5,0),(.035,.018,court_l),line,.004)
    for z in (-2.53,2.53):
        cube("Court %d long service line"%idx,(x,.5,z),(court_w,.018,.035),line,.004)
    # net posts and taut dark net plane
    for xx in (x-court_w/2-.06,x+court_w/2+.06):
        cyl("Tournament net post",(xx,1.18,0),.055,1.38,steel,20)
        cyl("Post base",(xx,.55,0),.11,.09,silver,20)
    cube("Net top tape",(x,1.78,0),(court_w+.12,.045,.055),line,.012)
    # fine mesh represented by narrow wires for a crisp, readable net
    for zz in [(-.82+j*.16) for j in range(11)]:
        beam("Net mesh horizontal",(x-court_w/2,1.76,zz),(x+court_w/2,1.76,zz),.009,black,6)
    for xx in [x-court_w/2+j*(court_w/24) for j in range(25)]:
        beam("Net mesh vertical",(xx,1.0,0),(xx,1.76,0),.007,black,6)

# Continuous spectator bowl, four broad stands with tiered seating rows.
for side in (-1,1):
    for row in range(13):
        z=side*(17.0+row*.78)
        y=1.05+row*.34
        cube("Long stand concrete riser",(0,y,z),(55-row*.34,.46,.78),concrete,.055)
        cube("Long stand fascia",(0,y+.16,z-side*.22),(55-row*.34,.12,.055),darkconcrete,.018)
        # grouped individual seats: curved-looking segmented rows, seat backs and cushions
        count=34-row//3
        span=53-row*.55
        for j in range(count):
            x=-span/2+(j+.5)*span/count
            cube("Navy seat cushion",(x,y+.30,z-side*.04),(span/count*.76,.16,.48),seatnavy,.06)
            cube("Navy seat back",(x,y+.48,z-side*.25),(span/count*.76,.48,.12),seatblue if (j+row)%9==0 else seatnavy,.055)
for side in (-1,1):
    for row in range(10):
        x=side*(24.0+row*.72); y=1.0+row*.35
        cube("End stand concrete riser",(x,y,0),(.75,.48,34-row*.28),concrete,.05)
        count=19-row//3; span=32-row*.5
        for j in range(count):
            z=-span/2+(j+.5)*span/count
            cube("End stand seat cushion",(x-side*.04,y+.30,z),(.48,.16,span/count*.76),seatnavy,.05)
            cube("End stand seat back",(x-side*.25,y+.48,z),(.12,.48,span/count*.76),seatnavy,.05)

# Main aisles, railings, vomitory portals and glass VIP concourse.
for side in (-1,1):
    for x in (-17,0,17):
        cube("Spectator aisle",(x,3.4,side*20),(1.35,5.8,4.5),darkconcrete,.12)
        for z in (side*17.9,side*22.2):
            beam("Aisle handrail",(x,5.2,z),(x,5.2,z+side*.01),.045,silver)
for z in (-23.3,23.3):
    cube("VIP concourse glass band",(0,6.4,z),(57,.1,.08),glass)
    for x in range(-27,29,2):
        beam("Glass mullion",(x,5.1,z),(x,7.8,z),.035,silver)
# Exterior wall volumes and architectural portal openings expressed as bays.
for z in (-23.8,23.8):
    cube("Outer concourse wall",(0,4.3,z),(62,8.6,.65),darkconcrete,.12)
    for x in range(-28,29,4):
        cube("Entrance portal surround",(x,2.5,z+(-.36 if z<0 else .36)),(2.3,4.8,.22),steel,.06)
        cube("Entrance portal glass",(x,2.5,z+(-.49 if z<0 else .49)),(1.8,3.9,.08),glass,.025)

# Monumental roof: perimeter box trusses, cross trusses and acoustic rafts.
for z in (-22.5,22.5):
    beam("Roof longitudinal truss lower chord",(-30,17,z),(30,17,z),.24,steel,12)
    beam("Roof longitudinal truss upper chord",(-30,20.5,z),(30,20.5,z),.20,silver,12)
    for x in range(-30,31,3):
        beam("Roof truss web",(x,17,z),(x+1.5,20.5,z),.075,steel,8)
        beam("Roof truss web",(x+1.5,20.5,z),(x+3,17,z),.075,steel,8)
for x in range(-28,29,7):
    beam("Roof cross beam",(x,20.2,-22.5),(x,20.2,22.5),.15,steel,10)
    beam("Roof diagonal brace",(x,17,-22.5),(x+3,20.1,0),.07,silver,8)
    beam("Roof diagonal brace",(x,20.1,0),(x,17,22.5),.07,silver,8)
for x in range(-27,28,6):
    cube("Suspended acoustic ceiling raft",(x,21.1,0),(4.7,.28,27),roof,.12)
    cube("Acoustic raft underglow",(x,20.93,0),(3.8,.025,22),darkconcrete,.02)
# Lighting gantries and bright continuous luminaires above the courts.
for z in (-14,-7,0,7,14):
    beam("Lighting gantry",(-23,17.6,z),(23,17.6,z),.11,steel,10)
    for x in range(-21,22,3):
        cube("LED high bay luminaire",(x,17.35,z),(.95,.16,.32),whiteemit,.05)
        cube("Luminaire metal housing",(x,17.5,z),(.98,.18,.38),silver,.045)
# Large center-hung scoreboard with four faces.
cube("Scoreboard suspension",(0,18,0),(1.0,3.5,1.0),steel,.12)
cube("Scoreboard core",(0,15.4,0),(7.5,3.0,3.5),black,.18)
for z in (-1.78,1.78):
    cube("Scoreboard LED face",(0,15.45,z),(6.9,2.4,.055),seatblue,.06)
    cube("Scoreboard cyan top trim",(0,16.75,z),(7.0,.055,.07),led,.015)
# Arena identity fascia and wayfinding.
for z in (-23.48,23.48):
    cube("Continuous LED ribbon",(0,7.7,z),(57,.12,.06),led,.025)
    for x in (-22,-11,0,11,22):
        cube("Arena wayfinding panel",(x,8.6,z),(3.2,.65,.08),black,.05)
        cube("Wayfinding accent",(x,8.6,z+(.05 if z>0 else -.05)),(2.3,.045,.025),warmled,.01)

# Premium broadcast platforms and courtside advertising boards.
for z in (-15.8,15.8):
    cube("Courtside sponsor fascia",(0,.82,z),(34,.7,.25),black,.06)
    for x in range(-15,16,3):
        cube("Sponsor light panel",(x,.84,z+(-.14 if z<0 else .14)),(2.45,.42,.04),led if x%2 else warmled,.025)
for x in (-21,21):
    cube("Broadcast camera platform",(x,1.1,0),(2.8,.5,4.2),darkconcrete,.1)
    for z in (-1.3,0,1.3):
        cube("Camera platform step",(x,1.38,z),(3.0,.12,.5),silver,.035)

# Corner guard rails and premium perimeter light strips.
for z in (-19.8,19.8):
    beam("Perimeter safety rail",(-27,2.6,z),(27,2.6,z),.055,silver,10)
for x in (-27,27):
    beam("Perimeter safety rail",(x,2.6,-19.8),(x,2.6,19.8),.055,silver,10)

# Lighting baked into scene metadata for alternate renderers; Babylon handles runtime lights.
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.world.color=(.035,.045,.055)
# Join static geometry by material to reduce draw calls while preserving the detailed model.
bpy.ops.object.select_all(action='DESELECT')
for obj in list(bpy.context.scene.objects):
    if obj.type=='MESH': obj.select_set(True)
bpy.context.view_layer.objects.active=next((o for o in bpy.context.scene.objects if o.type=='MESH'),None)
if bpy.context.view_layer.objects.active:
    bpy.ops.object.join()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT,export_format='GLB',use_selection=False,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
print("Premium championship arena exported:",OUT,os.path.getsize(OUT))
