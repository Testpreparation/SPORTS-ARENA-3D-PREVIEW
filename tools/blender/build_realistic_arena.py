import bpy, math, os, sys
# Ubuntu's Blender package uses the system Python module directory for NumPy.
if os.path.isdir('/usr/lib/python3/dist-packages'):
    sys.path.append('/usr/lib/python3/dist-packages')
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
    nodes = m.node_tree.nodes
    links = m.node_tree.links
    bs = nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal

    # Procedural micro-surface detail: no external image assets required.
    # Keep the color variation subtle so the arena reads as real materials,
    # rather than a noisy or stylized game environment.
    tex = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 28.0 if ("concrete" in name.lower() or "floor" in name.lower()) else 82.0
    noise.inputs["Detail"].default_value = 3.2
    noise.inputs["Roughness"].default_value = 0.72
    links.new(tex.outputs["Generated"], noise.inputs["Vector"])

    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.085 if ("concrete" in name.lower() or "floor" in name.lower()) else 0.04
    bump.inputs["Distance"].default_value = 0.035 if ("concrete" in name.lower() or "floor" in name.lower()) else 0.012
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bs.inputs["Normal"])

    # A restrained roughness breakup prevents large surfaces looking synthetic.
    ramp = nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.0
    ramp.inputs["From Max"].default_value = 1.0
    ramp.inputs["To Min"].default_value = max(0.08, rough - 0.09)
    ramp.inputs["To Max"].default_value = min(1.0, rough + 0.1)
    links.new(noise.outputs["Fac"], ramp.inputs["Value"])
    links.new(ramp.outputs["Result"], bs.inputs["Roughness"])
    return m

M = {
 "concrete": pbr("Warm architectural concrete", (.235,.265,.27), .88),
 "concrete_light": pbr("Light precast concrete", (.39,.415,.41), .84),
 "steel": pbr("Graphite structural steel", (.028,.039,.045), .34, .72),
 "steel_light": pbr("Brushed aluminium", (.23,.27,.28), .3, .76),
 "glass": pbr("Smoked arena glass", (.055,.115,.14), .24, .42),
 "seat_blue": pbr("Deep blue seat polymer", (.012,.065,.12), .42, .02),
 "seat_teal": pbr("Teal seat polymer", (.018,.14,.16), .4, .02),
 "seat_navy": pbr("Navy seat polymer", (.008,.025,.05), .43, .01),
 "rubber": pbr("Dark rubber flooring", (.022,.032,.035), .92),
 "white": pbr("Warm white paint", (.72,.75,.72), .52),
 "screen": pbr("Scoreboard black glass", (.003,.008,.012), .24, .22),
 "light": pbr("LED diffuser", (.95,.97,1.0), .28),
 "accent": pbr("Arena cyan accent", (.008,.19,.23), .38, .3),
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
box("rubber",(0,-.35,0),(76,.45,94))
box("concrete",(0,3.4,-44),(68,7,1.4))
box("concrete",(0,3.4,44),(68,7,1.4))
box("concrete",(-34,3.4,0),(1.4,7,87))
box("concrete",(34,3.4,0),(1.4,7,87))
# Glazed concourse bands and vertical mullions.
for z in (-43.1,43.1):
    box("glass",(0,4.1,z),(62,3.8,.09))
    for x in range(-30,31,2):
        box("steel",(x,3.4,z),(0.055,3.15,.08))
for x in (-33.5,33.5):
    box("glass",(x,4.1,0),(.08,3.8,82))
    for z in range(-41,42,2):
        box("steel",(x,3.4,z),(.08,3.15,.055))
# Concourse floor beams and repeated facade bays.
for z in (-42.2,42.2):
    box("steel",(0,6.1,z),(67,.28,.28))
    box("concrete_light",(0,7.4,z),(68,.48,.8))
for x in (-33.2,33.2):
    box("steel",(x,6.1,0),(.28,.28,86))
# Raised seating bowls arranged along the LONG SIDES of the court.
# Court long axis is Z (23.77 m); side stands therefore run parallel to Z,
# with each tier stepping outward along X. End stands run across X.
seat_mats=["seat_blue","seat_teal","seat_navy"]
for side in (-1,1):
    # Long-side stands: stepped banks parallel to the court sidelines, with clear corner gaps.
    for row in range(13):
        x=side*(7.25+row*1.35)
        y=.25+row*.48
        box("concrete_light",(x,y-.21,0),(1.22,.38,30.8))
        box("steel",(x-side*.50,y-.39,0),(.07,.08,30.8))
        z=-14.5
        while z<=14.51:
            key=seat_mats[(int((z+14.5)*3)+row*2+(1 if side>0 else 0))%len(seat_mats)]
            box(key,(x,y+.05,z),(.38,.12,.43))
            box(key,(x+side*.15,y+.22,z),(.075,.29,.43))
            box("steel",(x-side*.04,y-.04,z-.15),(.18,.035,.035))
            box("steel",(x-side*.04,y-.04,z+.15),(.18,.035,.035))
            z+=.66
    # Aisle rails/stair breaks are aligned with the long stands, not across the court.
    for z in (-14.8,-10.0,-5.0,0,5.0,10.0,14.8):
        for row in range(13):
            x=side*(7.0+row*1.35)
            y=.42+row*.48
            box("steel",(x,y+.31,z),(.07,.56,.06))
            box("steel",(x,y+.58,z),(.92,.05,.06))
# End stands: wider banks behind the baselines, with a deliberate gap from the long-side seating corners.
for side in (-1,1):
    for row in range(7):
        z=side*(17.0+row*1.35)
        y=.22+row*.43
        box("concrete_light",(0,y-.20,z),(53.5,.38,1.2))
        x=-26.0
        while x<=26.01:
            key=seat_mats[(int((x+12.4)*2)+row)%len(seat_mats)]
            box(key,(x,y+.05,z),(.48,.12,.42))
            box(key,(x,y+.24,z+side*.17),(.48,.32,.08))
            x+=.72
# Roof ring, perimeter beams and dense exposed trusses.
box("steel",(0,17.0,-39),(70,.7,4.0))
box("steel",(0,17.0,39),(70,.7,4.0))
box("steel",(-33.5,17.0,0),(4.0,.7,78))
box("steel",(33.5,17.0,0),(4.0,.7,78))
for z in range(-36,37,4):
    beam("steel",(-32,16.3,z),(32,16.3,z),.2,.25)
    beam("steel",(-32,16.3,z),(0,20.2,z),.15,.2)
    beam("steel",(0,20.2,z),(32,16.3,z),.15,.2)
    beam("steel",(-32,16.3,z),(32,16.3,z+2),.09,.13)
for x in range(-30,31,5):
    beam("steel_light",(x,16.5,-38),(x,16.5,38),.14,.18)
    beam("steel",(x,16.5,-38),(x,20.0,0),.11,.15)
    beam("steel",(x,20.0,0),(x,16.5,38),.11,.15)
# Acoustic roof panels, separated into long strips to preserve a believable structure.
for x in range(-30,31,6):
    box("concrete",(x,20.5,0),(5.7,.2,74))
# Broadcast-grade arena details: service catwalks, guard rails, aisle lighting,
# and a continuous inner fascia make the seating bowl feel like a real venue.
for side in (-1,1):
    # Upper concourse handrails and structural stringers along both long sides.
    for row in (0,1):
        x=side*(28.0+row*.85)
        beam("steel_light",(x,7.1,-37.5),(x,7.1,37.5),.08,.08)
    for z in range(-36,37,4):
        box("accent",(side*27.0,1.4,z),(.06,.14,.8))
        box("steel",(side*27.0,1.05,z),(.1,.09,.84))
# Fine roof seams and acoustic-panel joints.
for x in range(-30,31,3):
    box("steel_light",(x,20.65,0),(.03,.03,73.5))
# Additional scoreboard fascia trim and corner wayfinding light bands.
for side in (-1,1):
    for x in (-31.0,31.0):
        box("accent",(x,12.0,side*38.1),(.15,.18,.15))
# Subtle perimeter LED ribbon under the upper seating edge.
for side in (-1,1):
    box("accent",(side*26.5,7.0,0),(.1,.08,74.0))
# LED lighting bars and high-bay fixtures.
for z in (-30,-15,0,15,30):
    for x in (-25,-12.5,0,12.5,25):
        box("light",(x,19.8,z),(2.8,.1,.3))
        box("steel",(x,19.5,z),(3.0,.08,.36))
# Large scoreboard and fascia panels.
box("steel",(0,11.2,-36.5),(12.0,5.5,.7))
box("screen",(0,11.2,-36.05),(11.0,4.7,.1))
box("accent",(0,8.25,-36.0),(11.2,.16,.1))
for side in (-1,1):
    box("steel",(0,12.2,side*38.5),(62,.95,.4))
    box("accent",(0,12.2,side*38.25),(61,.15,.06))
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
# Geometry is authored Y-up (Y is height) to match the Babylon.js court.
# Blender is Z-up; rotate the generated meshes +90 degrees around X before
# glTF export so the exporter’s Z-up conversion preserves intended world axes.
bpy.ops.object.select_all(action="SELECT")
for obj in bpy.context.selected_objects:
    obj.rotation_euler.x = math.radians(90)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_apply=True)
print("ARENA_EXPORT_OK", OUT, os.path.getsize(OUT))
