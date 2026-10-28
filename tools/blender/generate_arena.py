import bpy, math, os, sys
from mathutils import Vector

# Run with:
# blender --background --python tools/blender/generate_arena.py -- --output assets/arena.glb

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
output = "assets/arena.glb"
if "--output" in args:
    output = args[args.index("--output") + 1]
output = os.path.abspath(output)
os.makedirs(os.path.dirname(output), exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.materials, bpy.data.meshes, bpy.data.curves):
    pass

def pbr(name, color, metallic=0.0, roughness=0.5, alpha=1.0, emission=None):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, alpha)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, alpha)
    bs.inputs["Metallic"].default_value = metallic
    bs.inputs["Roughness"].default_value = roughness
    if alpha < 1:
        bs.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "DITHERED"
    if emission:
        bs.inputs["Emission Color"].default_value = (*emission, 1)
        bs.inputs["Emission Strength"].default_value = 2.0
    return m

concrete = pbr("PBR | architectural concrete", (0.31,0.36,0.38), 0.12, 0.84)
concrete_light = pbr("PBR | precast seating concrete", (0.48,0.52,0.53), 0.08, 0.8)
steel = pbr("PBR | brushed structural steel", (0.22,0.29,0.32), 0.78, 0.29)
steel_dark = pbr("PBR | dark steel", (0.045,0.065,0.075), 0.72, 0.34)
roof = pbr("PBR | roof acoustic panels", (0.12,0.17,0.20), 0.22, 0.62)
glass = pbr("PBR | blue architectural glazing", (0.20,0.39,0.46), 0.38, 0.18, 0.36)
seat_blue = pbr("PBR | stadium seat blue", (0.025,0.20,0.29), 0.12, 0.34)
seat_cyan = pbr("PBR | alternate seat blue", (0.10,0.36,0.43), 0.10, 0.36)
seat_light = pbr("PBR | premium light seats", (0.68,0.76,0.77), 0.08, 0.38)
rubber = pbr("PBR | court perimeter rubber", (0.035,0.09,0.13), 0.02, 0.78)
court_blue = pbr("PBR | tennis court acrylic", (0.035,0.22,0.34), 0.02, 0.34)
court_green = pbr("PBR | court green acrylic", (0.035,0.20,0.10), 0.01, 0.42)
court_clay = pbr("PBR | clay court", (0.48,0.16,0.075), 0.0, 0.9)
court_wood = pbr("PBR | indoor maple", (0.49,0.30,0.14), 0.02, 0.3)
line_mat = pbr("PBR | court line paint", (0.91,0.94,0.91), 0.0, 0.55)
gold = pbr("PBR | anodized champagne trim", (0.46,0.34,0.16), 0.72, 0.28)
led = pbr("Emission | arena LED strips", (0.52,0.88,1.0), 0.15, 0.24, emission=(0.34,0.78,1.0))
screen = pbr("Emission | scoreboard display", (0.015,0.07,0.10), 0.15, 0.26, emission=(0.015,0.16,0.24))
exit_mat = pbr("Emission | exit sign", (0.08,0.72,0.28), 0.0, 0.4, emission=(0.05,0.9,0.24))

created = []
def box(name, loc, scale, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    if bevel:
        mod = o.modifiers.new("Machined edge highlights", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        o.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    created.append(o)
    return o

def beam(name, a, b, width, material, depth=None):
    A, B = Vector(a), Vector(b)
    d = B - A
    mid = (A+B)*0.5
    o = box(name, mid, (width, d.length, depth or width), material)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Y", "Z")
    return o

def cylinder_between(name, a, b, radius, material, vertices=10):
    A, B = Vector(a), Vector(b)
    d = B-A
    mid = (A+B)*0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=d.length, location=mid)
    o=bpy.context.object
    o.name=name
    o.rotation_mode="QUATERNION"
    o.rotation_quaternion=d.to_track_quat("Z","Y")
    o.data.materials.append(material)
    created.append(o)
    return o

# Heavy foundation and concourse shell
box("Continuous arena foundation", (0,-0.55,0), (32,0.8,44), concrete, .12)
box("Lower concourse volume", (0,0.45,0), (29,1.1,40), concrete, .08)
# Interactive court surface and markings are rendered by Babylon.js.

# tiered precast seating bowl, entirely empty (no people)
for row in range(8):
    y=.48+row*.52
    inner_x=7.2+row*.82
    outer_x=12.8+row*.7
    inner_z=11.9+row*1.15
    outer_z=16.2+row*1.12
    for side in (-1,1):
        box("Tier riser", (side*(inner_x+outer_x)/2,y,(inner_z+outer_z)/2), (outer_x-inner_x,.25,outer_z-inner_z), concrete_light)
        box("Tier fascia", (side*(inner_x+.1),y+.13,(inner_z+outer_z)/2), (.12,.24,outer_z-inner_z), steel)
        box("Tier nosing", (side*(inner_x+outer_x)/2,y+.135,(inner_z+outer_z)/2), (outer_x-inner_x,.025,outer_z-inner_z), gold)
    for side in (-1,1):
        box("End stand riser", (0,y,side*(inner_z+outer_z)/2), (outer_x-inner_x,.25,outer_z-inner_z), concrete_light)
# individual high-density molded seats, linked geometry by material
for row in range(8):
    y=1.0+row*.52
    xoff=8.0+row*.72
    for side in (-1,1):
        for i in range(45):
            z=-16.5+i*.75
            x=side*xoff
            sm=seat_cyan if (i+row)%7==0 else (seat_light if (i+row)%17==0 else seat_blue)
            box("Moulded seat cushion", (x,y,z), (.43,.12,.36), sm, .035)
            back=box("Moulded seat back", (x,y+.18,z-.145*side), (.43,.30,.075), sm, .025)
            back.rotation_euler[0]=math.radians(-7)
            box("Seat pedestal", (x,y-.11,z), (.075,.18,.075), steel_dark)
    for i in range(29):
        x=-10.5+i*.75
        for side in (-1,1):
            z=side*(13.1+row*.67)
            sm=seat_cyan if (i+row)%8==0 else seat_blue
            box("End stand seat cushion", (x,y,z), (.36,.12,.43), sm, .03)
            box("End stand seat back", (x,y+.18,z-side*.15), (.36,.30,.075), sm, .025)

# Concourse glazing, mullions, door frames and service panels
for side in (-1,1):
    for z in [i*2.25-18 for i in range(17)]:
        box("Facade glazed bay", (side*14.35,2.65,z), (.07,3.35,2.08), glass)
        box("Facade vertical mullion", (side*14.42,2.65,z-1.08), (.12,3.55,.095), steel)
        box("Facade transom", (side*14.42,4.28,z), (.12,.09,2.18), steel)
    for z in (-12,0,12):
        box("Double entrance frame", (side*14.43,1.9,z), (.14,2.5,1.8), steel_dark)
        box("Entrance glass", (side*14.52,2.02,z), (.035,2.1,1.52), glass)
        box("Door kick plate", (side*14.55,1.28,z), (.035,.35,1.48), steel)
    for z in range(-16,17,4):
        box("HVAC grille surround", (side*14.46,4.65,z), (.12,.5,1.4), steel_dark)
        for j in range(7):
            box("HVAC grille slat", (side*14.53,4.43+j*.065,z), (.035,.025,1.28), steel)
# structural columns and roof trusses
for x in (-14,-10,-6,6,10,14):
    for z in (-20,-14,14,20):
        box("Main steel column", (x,5.5,z), (.34,10.2,.38), steel, .035)
        box("Column base plate", (x,.5,z), (.68,.14,.72), steel_dark)
        for bolt_x in (-.2,.2):
            for bolt_z in (-.2,.2):
                cylinder_between("Anchor bolt", (x+bolt_x,.59,z+bolt_z),(x+bolt_x,.66,z+bolt_z),.035,gold,8)
for z in range(-20,21,4):
    beam("Roof primary girder", (-15,10.8,z),(15,10.8,z),.22,steel_dark,.3)
    beam("Roof truss diagonal left", (-14,10.7,z),(0,12.8,z+2),.14,steel,.18)
    beam("Roof truss diagonal right", (0,12.8,z+2),(14,10.7,z),.14,steel,.18)
    beam("Roof truss bottom chord",(-14,10.65,z),(14,10.65,z),.12,steel,.14)
    for xx in range(-12,13,4):
        beam("Roof truss vertical web",(xx,10.7,z),(xx,12.2,z+1),.09,steel,.11)
# roof acoustic panels, ribs and catwalk
box("Main roof acoustic canopy",(0,13.35,0),(31,.42,43),roof,.08)
for x in range(-14,15,2):
    box("Roof acoustic panel seam",(x,13.57,0),(.035,.018,42),steel)
box("Roof maintenance catwalk",(0,10.05,0),(27,.12,1.1),steel_dark)
for x in range(-13,14,1):
    box("Catwalk handrail upright",(x,10.45,0),(.055,.7,.055),steel)
for z in (-.52,.52):
    beam("Catwalk handrail",( -13,10.72,z),(13,10.72,z),.055,steel)
# fascia and scoreboard
box("Upper fascia front",(0,9.25,-20.8),(29,.9,.45),steel_dark)
box("Upper fascia rear",(0,9.25,20.8),(29,.9,.45),steel_dark)
box("Scoreboard housing",(0,8.15,-17.8),(10.5,2.3,.65),steel_dark,.04)
box("Scoreboard glass",(0,8.15,-17.44),(9.9,1.75,.04),screen)
for x in range(-4,5):
    box("Scoreboard LED separator",(x,8.15,-17.405),(.035,1.35,.025),led)
for side in (-1,1):
    for z in range(-17,18,3):
        box("Emergency exit light",(side*14.52,4.8,z),(.06,.25,.75),exit_mat)
# railings and aisle stair strips
for side in (-1,1):
    for z in [i*.7-17 for i in range(49)]:
        box("Guardrail upright",(side*12.8,4.45,z),(.055,.8,.055),steel)
    beam("Guardrail top rail",(side*12.8,4.86,-17),(side*12.8,4.86,17),.065,steel)
for side in (-1,1):
    for x in range(-10,11,2):
        for row in range(7):
            box("Aisle step nosing",(x,1.1+row*.52,side*(12.7+row*.7)),(1.0,.035,.055),gold)

# Floodlight banks and LED luminaires
for side in (-1,1):
    for z in (-15,0,15):
        x=side*12.2
        box("Floodlight support",(x,7.0,z),(.3,7.2,.3),steel_dark)
        box("Floodlight bank housing",(x,10.7,z),(2.0,.5,1.15),steel)
        for i in range(7):
            box("Individual LED optic",(x-.78+i*.26,10.7,z-.59),(.16,.15,.025),led)

# Join architecture and seats into separate optimized GLB assets.
# Keeping the seat bowl separate allows Babylon.js to toggle seating on/off.
def export_group(objects, name, filepath):
    bpy.ops.object.select_all(action="DESELECT")
    valid=[o for o in objects if o and o.name in bpy.data.objects and o.type=="MESH"]
    if not valid:
        raise RuntimeError("No mesh objects for export group: "+name)
    for o in valid:
        o.select_set(True)
    bpy.context.view_layer.objects.active=valid[0]
    bpy.ops.object.join()
    merged=bpy.context.object
    merged.name=name
    merged.data.name=name+" Mesh"
    for mod in list(merged.modifiers):
        try:
            bpy.context.view_layer.objects.active=merged
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception:
            pass
    for poly in merged.data.polygons:
        poly.use_smooth=False
    bpy.ops.object.select_all(action="DESELECT")
    merged.select_set(True)
    bpy.context.view_layer.objects.active=merged
    bpy.ops.export_scene.gltf(filepath=filepath, export_format="GLB", use_selection=True, export_apply=True, export_yup=True, export_materials="EXPORT", export_cameras=False, export_lights=False)
    print("EXPORTED_"+name.upper().replace(" ","_")+"="+filepath)

seat_objects=[o for o in created if "seat" in o.name.lower()]
architecture_objects=[o for o in created if "seat" not in o.name.lower() and "floodlight" not in o.name.lower() and "individual led optic" not in o.name.lower()]
folder=os.path.dirname(output)
export_group(architecture_objects,"Blender Crafted Arena Architecture",os.path.join(folder,"arena-architecture.glb"))
export_group(seat_objects,"Blender Crafted Empty Stadium Seating",os.path.join(folder,"arena-seats.glb"))
