# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
import bpy
import bmesh
import math
import copy

bl_info = {
    "name": "Add Zonohedron",
    "author": "Zac Rogers",
    "version": (1, 3),
    'blender': (2, 80, 0),
    "location": "View3D > Tools > Add Zonohedron",
    "description": "Add Zonohedron Mesh",
    "warning": "",
    "wiki_url": "",
    "category": "Mesh",
}

# Installation Instructions
# 1 Copy this file to your Blender 3D Add-ons folder
# 2 Go to File->User Preferences
# 3 Click on the Add-ons Tab
# 4 Under category 'Mesh' select 'Mesh: Add Zonohedron' & click the checkbox
# 5 Click on Save User Settings
# 6 In Object mode open the Tools Panel (Toggle the letter 'T' on the keyboard)
# 7 At the bottom of the 'Create' panel you will see the Add Zonohedron panel

# --- Global Declarations ---
class zoneData:
    sides = 12
    width = 1
    detail = 1
    zono_type = 'zonohedron'
    spirals = 1
    rotation_clockwise = True

# --- Helper functions ---
def scale_center_clean(obj):
    # Set the physical dimensions
    scale = zoneData.width / obj.dimensions.x
    print(scale, zoneData.width, obj.dimensions.x) 
    obj.dimensions = (
        zoneData.width, 
        obj.dimensions.y * scale, 
        obj.dimensions.z * scale
    )
    
    # Set the scale after setting dimensions
    # obj.scale = (1, 1, 1)

    # Apply the Transforms object
    bpy.ops.object.select_all(action='DESELECT') # Clear selection
    obj.select_set(True)                         # Select our object
    bpy.context.view_layer.objects.active = obj  # Make it the active one

    # Merge Vertices
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.object.mode_set(mode='OBJECT')

    if zoneData.rotation_clockwise:
        bpy.ops.transform.mirror(constraint_axis=(True, False, False), orient_type='GLOBAL')

    # Set the origin to the center of the object's volume/bounds
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # Reset the object's location to the world center
    obj.location = (0, 0, 0)

    # Now call the operator to reset the scale/location/rotation to the data
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def create_from_json_data(poly_data):
    all_verts = []
    all_faces = []

    # Process the nested list
    for i, polygon in enumerate(poly_data):
        # Extract the x, y, z from each dictionary and add to the master list
        for v in polygon:
            all_verts.append((v['x'], v['y'], v['z']))

        # Calculate indices for this face, (0,1,2,3),(4,5,6,7)
        start_idx = i * 4
        face_indices = (start_idx, start_idx + 1, start_idx + 2, start_idx + 3)
        all_faces.append(face_indices)

    # Standard Blender mesh creation
    mesh_data = bpy.data.meshes.new("JsonMesh")
    mesh_obj = bpy.data.objects.new("JsonObject", mesh_data)
    bpy.context.collection.objects.link(mesh_obj)

    # Create the geometry
    mesh_data.from_pydata(all_verts, [], all_faces)
    mesh_data.update()
    scale_center_clean(mesh_obj)

def create_edges_from_json_data(poly_data, obj_name="EdgeObject", closed=False):
    verts = []
    vert_index_map = {}
    edges = []

    def get_vert_index(v):
        key = (v["x"], v["y"], v["z"])
        if key not in vert_index_map:
            vert_index_map[key] = len(verts)
            verts.append(key)
        return vert_index_map[key]

    for loop in poly_data:
        if len(loop) < 2:
            continue

        indices = [get_vert_index(v) for v in loop]

        for i in range(len(indices) - 1):
            edges.append((indices[i], indices[i + 1]))

        if closed:
            edges.append((indices[-1], indices[0]))

    mesh = bpy.data.meshes.new(obj_name + "_mesh")
    mesh.from_pydata(verts, edges, [])
    mesh.update()

    obj = bpy.data.objects.new(obj_name, mesh)
    bpy.context.collection.objects.link(obj)
    scale_center_clean(obj)

    return obj

def calculate_distance(p1, p2):
    dx = p1["x"] - p2["x"]
    dy = p1["y"] - p2["y"]
    return math.sqrt(dx*dx + dy*dy)

def line_angle(p1, p2):
    dx = p2["x"] - p1["x"]
    dy = p2["y"] - p1["y"]
    deg = math.degrees(math.atan2(dy, dx))
    return deg + 360 if deg < 0 else deg

def rotate_point(center, point, degrees):
    length = calculate_distance(center, point)
    angle = line_angle(center, point)
    rad = math.radians(degrees + angle)

    return {
        "x": center["x"] + math.cos(rad) * length,
        "y": center["y"] + math.sin(rad) * length,
        "z": point["z"]
    }

def rotate_point_list(points, rotation, center):
    return [rotate_point(center, p, rotation) for p in points]

def move_point_list(points, snap_target, snap_hook, segments):
    pts = copy.deepcopy(points)
    segments = min(len(pts), segments + 1)
    dx = snap_hook["x"] - snap_target["x"]
    dy = snap_hook["y"] - snap_target["y"]
    dz = snap_hook["z"] - snap_target["z"]
    moved = []
    for i in range(segments):
        p = pts[i]
        moved.append({
            "x": p["x"] - dx,
            "y": p["y"] - dy,
            "z": p["z"] - dz
        })
    return moved

def rotate_point_xyz(center, point, degrees):
    rx = math.radians(degrees["x"])
    ry = math.radians(degrees["y"])
    rz = math.radians(degrees["z"])

    # translate to origin
    px = point["x"] - center["x"]
    py = point["y"] - center["y"]
    pz = point["z"] - center["z"]

    # rotate X
    x1 = px
    y1 = py * math.cos(rx) - pz * math.sin(rx)
    z1 = py * math.sin(rx) + pz * math.cos(rx)

    # rotate Y
    x2 = x1 * math.cos(ry) + z1 * math.sin(ry)
    y2 = y1
    z2 = -x1 * math.sin(ry) + z1 * math.cos(ry)

    # rotate Z
    x3 = x2 * math.cos(rz) - y2 * math.sin(rz)
    y3 = x2 * math.sin(rz) + y2 * math.cos(rz)
    z3 = z2

    return {
        "x": x3 + center["x"],
        "y": y3 + center["y"],
        "z": z3 + center["z"],
    }

def create_spiral(height, radius, center, num_of_points, clockwise = True):
    if zoneData.zono_type == 'curved' or zoneData.zono_type == 'spirallohedra':
        height_offset = height / (zoneData.sides * zoneData.detail) 
    else:
        height_offset = height / zoneData.sides    
    half_circle_center = {"x": center["x"] + radius, "y": center["y"], "z": 0}
    degrees = 360/num_of_points    
    spiral_arm = []
    point = {
        "x": center["x"] + radius * 2,
        "y": center["y"],
        "z": 0
    }
    
    for i in range(num_of_points + 1):
        if clockwise:
            rot = 180 + i * degrees
        else:
            rot = 180 - i * degrees
        spiral_arm.append(
            rotate_point_xyz(half_circle_center, point, {"x": 0, "y": 0, "z": rot})
        )
        point = dict(point)
        point["z"] += height_offset
    return spiral_arm    

# --- Core render functions ---
def create_zonohedron():
    zone_sides = zoneData.sides * zoneData.detail
    center = {"x": 0, "y": 0, "z": 0}
    radius = zoneData.width/2
    height = radius * 5
    height_offset = height / zone_sides
    deg = 360 / zone_sides
    arms_deg = 360 / zoneData.sides
    ribs = []
    leaf_polygons = []
    all_polygons = []

    first_spiral_arm = create_spiral(height, radius, center, zone_sides, True)
    second_spiral_arm = rotate_point_list(first_spiral_arm, arms_deg, center)

    # --- Ribs ---
    for i in range(zone_sides - (zoneData.detail - 1)):
        rib = move_point_list(
            first_spiral_arm,
            second_spiral_arm[i],
            first_spiral_arm[0],
            zoneData.detail
        )
        ribs.append(rib)

    # --- Leaf polygons ---
    for i in range(len(ribs) - 1):
        rib = ribs[i]
        rib_next = ribs[i + 1]

        for j in range(len(rib) - 1):
            polygon = [
                rib[j],
                rib[j + 1],
                rib_next[j + 1],
                rib_next[j]
            ]
            leaf_polygons.append(polygon)

    # --- Replicate around arms ---
    for i in range(zoneData.sides):
        rotation = i * arms_deg + 180
        for poly in leaf_polygons:
            all_polygons.append(
                rotate_point_list(poly, rotation, center)
            )

    return all_polygons

def create_spiral_zonohedron():
    zone_sides = zoneData.sides
    center = {"x": 0, "y": 0, "z": 0}
    radius = zoneData.width/2
    height = radius * 4 
    height_offset = height / zone_sides
    deg = 360 / zone_sides
    half_circle_center = {"x": center["x"] + radius, "y": center["y"], "z": center["z"]}
    single_leaf_polygons = []
    double_leaf_polygons = []
    top_shell = []
    spiral_case = []
    bottom_shell = []
    first_spiral_arm = create_spiral(height, radius, center, zone_sides, True)
    base_spiral_arm = create_spiral(height, radius, center, zone_sides, False)

    # ---- Rotate base spiral arm ----
    base_spiral_arm = rotate_point_list(base_spiral_arm, (zone_sides / 2) * -deg, center)
    # ---- Second spiral arm ----
    second_spiral_arm = rotate_point_list(
        first_spiral_arm,
        deg,
        first_spiral_arm[0]
    )
    # ---- Single leaf ----
    for i in range(len(first_spiral_arm) - 2):
        poly = [
            second_spiral_arm[i],
            second_spiral_arm[i + 1],
            first_spiral_arm[i + 2],
            first_spiral_arm[i + 1]
        ]
        single_leaf_polygons.append(poly)

    # ---- Top shell and seed double leaves ----
    count = zone_sides
    for i in range(zone_sides):
        for idx, poly in enumerate(single_leaf_polygons):
            rotated = rotate_point_list(poly, i * deg, center)
            if i == zone_sides - 1:
                double_leaf_polygons.append(rotated)
            else:
                if idx < count - 1:
                    top_shell.append(rotated)
        count -= 1

    # ---- Extend double leaf ----
    seed = double_leaf_polygons[0][0]
    for poly in list(double_leaf_polygons):
        ext = move_point_list(
            poly,
            base_spiral_arm[1],
            seed,
            zone_sides
        )
        double_leaf_polygons.append(ext)

    # ---- Spiral case ----
    for i in range(zone_sides - 1):
        for poly in double_leaf_polygons:
            rotated = rotate_point_list(poly, (i + 1) * -deg, center)
            moved = move_point_list(
                rotated,
                base_spiral_arm[i + 1],
                seed,
                zone_sides
            )
            spiral_case.append(moved)

    spiral_case_complete = double_leaf_polygons + spiral_case

    # ---- Spiral repetitions ----
    spiral_extensions = []
    for i in range(1, zoneData.spirals):
        for poly in spiral_case_complete:
            spiral_extensions.append(
                move_point_list(
                    poly,
                    {"x": 0, "y": 0, "z": height * i},
                    {"x": 0, "y": 0, "z": 0},
                    zone_sides
                )
            )

    # ---- Bottom shell ----
    for poly in top_shell:
        new_poly = []
        for p in poly:
            rp = rotate_point_xyz(
                base_spiral_arm[-1],
                p,
                {"x": 0, "y": 180, "z": 180}
            )
            if zoneData.spirals > 1:
                rp["z"] += height * (zoneData.spirals - 1)
            new_poly.append(rp)
        bottom_shell.append(new_poly)

    all_polygons = (
        top_shell +
        spiral_case_complete +
        spiral_extensions +
        bottom_shell
    )

    return all_polygons

def create_curved_zonohedron():
    center = {"x": 0, "y": 0, "z": 0}
    radius = zoneData.width/2
    height = radius * 4
    degrees = 360/zoneData.sides
    all_edges = []
    num_of_points = zoneData.sides * zoneData.detail;
    arm_clockwise = create_spiral(height, radius, center, num_of_points,  True)
    arm_counter = create_spiral(height, radius, center, num_of_points, False)
    
    for i in range(zoneData.sides + 1):
        all_edges.append(
            rotate_point_list(arm_clockwise, i * degrees, center)
        )
        all_edges.append(
            rotate_point_list(arm_counter, i * degrees, center)
        )
    return all_edges

def draw_zonohedron():
    if zoneData.zono_type == 'standard':
        zoneData.detail = 1
        result = create_zonohedron()
        create_from_json_data(result)
    if zoneData.zono_type == 'spirallohedra':
        result = create_zonohedron()
        create_from_json_data(result)
    if zoneData.zono_type == 'spiral':
        result = create_spiral_zonohedron()
        create_from_json_data(result)        
    if zoneData.zono_type == 'curved':
        edge_data = create_curved_zonohedron()
        result = create_edges_from_json_data(edge_data)

# --- Interface start ---
class ZONO_PT_ZonohedronMaker(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_category = "Zonohedron"
    bl_label = "Add Zonohedron"

    def draw(self, context):
        cs = context.scene
        col = self.layout.column(align=False)
        sub_01 = col.column()
        sub_02 = col.column()
        sub_03 = col.column()
        # General
        sub_01.prop(cs, "zonohedron_type")
        sub_01.prop(cs, "zonohedron_sides")
        sub_01.prop(cs, "zonohedron_width")
        sub_01.prop(cs, "zonohedron_reverse")
        # Spiral
        sub_02.prop(cs, "zonohedron_spiral")
        # Curved
        sub_03.prop(context.scene, "zonohedron_detail")
        sub_02.enabled = True if cs.zonohedron_type == "spiral" else False
        sub_03.enabled = True if cs.zonohedron_type != "standard" else False
        col.operator("mesh.make_zonohedron", text="Make Zonohedron")

class MakeZonohedron(bpy.types.Operator):
    bl_idname = "mesh.make_zonohedron"
    bl_label = "Add Zonohedron"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        cs = context.scene
        zoneData.sides = cs.zonohedron_sides
        zoneData.width = cs.zonohedron_width #size
        zoneData.detail = cs.zonohedron_detail
        zoneData.zono_type = cs.zonohedron_type
        zoneData.spirals = cs.zonohedron_spiral
        zoneData.rotation_clockwise = cs.zonohedron_reverse
        draw_zonohedron()
        return {"FINISHED"}

def register():
    bpy.utils.register_class(MakeZonohedron)
    bpy.utils.register_class(ZONO_PT_ZonohedronMaker)
    bpy.types.Scene.zonohedron_type = bpy.props.EnumProperty(
        name="Type",
        description="Type of Zonohedron",
        items=(('standard', 'Zonohedron', 'Standard Zonohedron'),
               ('spirallohedra', 'Spirallohedra', 'Rhombic Spirallohedra'),
               ('spiral', 'Spiral', 'Spiral Zonohedron'),
               ('curved', 'Curved', 'Curved Wireframe Zonohedron'),
               )
    )
    bpy.types.Scene.zonohedron_sides = bpy.props.IntProperty(
        name="Sides",
        description="Number of Sides",
        min=3,
        max=60,
        default=12,
    )
    bpy.types.Scene.zonohedron_width = bpy.props.IntProperty(
        name="Width",
        description="Width of Zonohedron",
        min=1,
        max=10,
        default=1
    )
    bpy.types.Scene.zonohedron_detail = bpy.props.IntProperty(
        name="Detail",
        description="Size of Zonohedron",
        min=1,
        max=6,
        default=1
    )
    bpy.types.Scene.zonohedron_spiral = bpy.props.IntProperty(
        name="Spiral Count",
        description="Spiral Count 0 = No Spiral",
        min=1,
        max=6,
        default=1
    )
    bpy.types.Scene.zonohedron_reverse = bpy.props.BoolProperty(
        name="Reverse Spiral",
        description="Reverse Spiral Direction",
        default=0,
    )

def unregister():
    bpy.utils.unregister_class(MakeZonohedron)
    bpy.utils.unregister_class(ZONO_PT_ZonohedronMaker)
    del bpy.types.Scene.zonohedron_type
    del bpy.types.Scene.zonohedron_sides
    del bpy.types.Scene.zonohedron_width
    del bpy.types.Scene.zonohedron_detail
    del bpy.types.Scene.zonohedron_spiral
    del bpy.types.Scene.zonohedron_reverse

# Interface end ------------------------------

if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
