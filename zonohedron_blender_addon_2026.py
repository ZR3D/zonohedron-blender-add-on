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


def set_scale(obj, spiral_anticlock):
    # Set the physical dimensions (Size in Blender Units/Meters)
    #obj.dimensions = (6, 6, 10)

    # Set the scale (usually done before or after dimensions)
    obj.scale = (1, 1, 1)

    # Apply the Transforms
    # Ensure the object is selected and active
    bpy.ops.object.select_all(action='DESELECT') # Clear selection
    obj.select_set(True)                         # Select our object
    bpy.context.view_layer.objects.active = obj  # Make it the active one
    
    # Clean up (Merge Vertices)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.001) 
    bpy.ops.object.mode_set(mode='OBJECT')
    
    if spiral_anticlock:
        bpy.ops.transform.mirror(constraint_axis=(True, False, False), orient_type='GLOBAL')
 
    # Set the origin to the center of the object's volume/bounds
    # This moves the pivot point to the middle of your 600-unit coordinates
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # Reset the object's location to the world center
    obj.location = (0, 0, 0)

    # Now call the operator to 'Reset' the scale/location/rotation to the data
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)    

def leave_edges_only(obj):
    me = obj.data
    bpy.ops.object.mode_set(mode='EDIT')
    # Create a bmesh instance from the mesh
    bm = bmesh.from_edit_mesh(me)

    # Get all currently selected faces
    faces_to_delete = [f for f in bm.faces if f.select]

    # Delete ONLY the faces (leaves edges and vertices behind)
    bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES_ONLY')
    # Update the mesh and free the bmesh
    bmesh.update_edit_mesh(me)
    # Switch back to object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
# Mirror along Global X
bpy.ops.transform.mirror(
    orient_type='GLOBAL', 
    constraint_axis=(True, False, False)
)

def create_from_json_data(poly_data, spiral_anticlock):
    all_verts = []
    all_faces = []
    
    # Process the nested list
    for i, polygon in enumerate(poly_data):
        # Extract the x, y, z from each dictionary and add to the master list
        for v in polygon:
            all_verts.append((v['x'], v['y'], v['z']))
        
        # Calculate indices for this face
        # If i=0, indices are (0,1,2,3). If i=1, indices are (4,5,6,7)
        start_idx = i * 4
        face_indices = (start_idx, start_idx + 1, start_idx + 2, start_idx + 3)
        all_faces.append(face_indices)

    # Standard Blender Mesh Creation
    mesh_data = bpy.data.meshes.new("JsonMesh")
    mesh_obj = bpy.data.objects.new("JsonObject", mesh_data)
    bpy.context.collection.objects.link(mesh_obj)
    
    # Create the geometry
    mesh_data.from_pydata(all_verts, [], all_faces)
    mesh_data.update()
    set_scale(mesh_obj, spiral_anticlock)
    #leave_edges_only(mesh_obj)



# -----------------------------
# Helper functions
# -----------------------------

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


###################################
#def rotate_point_list(points, rotation, center):
#    return [
#        rotate_point_3d(center, p, {"x": 0, "y": 0, "z": rotation})
#        for p in points
#    ]


def rotate_point_3d(center, point, degrees):
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

# -----------------------------
# Core render functions
# -----------------------------

def create_zonohedron(zone_arms=4, zone_detail=4):
    zone_sides = zone_arms * zone_detail

    center = {"x": 0, "y": 0, "z": 0}
    radius = 3
    height = 10

    height_offset = height / zone_sides
    deg = 360 / zone_sides
    arms_deg = 360 / zone_arms

    first_spiral_arm = []
    ribs = []
    leaf_polygons = []
    all_polygons = []

    half_circle_center = {
        "x": center["x"] + radius,
        "y": center["y"],
        "z": 0
    }

    # --- First spiral arm ---
    point = {
        "x": center["x"] + (radius * 2),
        "y": center["y"],
        "z": 0
    }

    for i in range(zone_sides + 1):
        rotation = 180 + i * deg
        spiral_point = rotate_point(half_circle_center, point, rotation)
        first_spiral_arm.append(spiral_point)
        point = dict(point)
        point["z"] += height_offset

    # ---- Second spiral arm ----
    second_spiral_arm = rotate_point_list(first_spiral_arm, arms_deg, center)

    # --- Ribs ---
    for i in range(zone_sides - (zone_detail - 1)):
        rib = move_point_list(
            first_spiral_arm,
            second_spiral_arm[i],
            first_spiral_arm[0],
            zone_detail
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
    for i in range(zone_arms):
        rotation = i * arms_deg + 180
        for poly in leaf_polygons:
            all_polygons.append(
                rotate_point_list(poly, rotation, center)
            )

    return all_polygons

# --- Spiral Zonohedron Creator ---
def create_spiral_zonohedron( zone_sides=10, zone_spirals=2):
    center = {"x": 0, "y": 0, "z": 0}
    radius = 1
    height = 5

    height_offset = height / zone_sides
    deg = 360 / zone_sides

    half_circle_center = {
        "x": center["x"] + radius,
        "y": center["y"],
        "z": center["z"]
    }

    first_spiral_arm = []
    base_spiral_arm = []

    single_leaf_polygons = []
    double_leaf_polygons = []
    top_shell = []
    spiral_case = []
    bottom_shell = []

    # ---- Create first + base spiral arms ----
    point = {
        "x": center["x"] + radius * 2,
        "y": center["y"],
        "z": 0
    }

    for i in range(zone_sides + 1):
        rot = 180 + i * deg
        counter_rot = 180 - i * deg

        first_spiral_arm.append(
            rotate_point_3d(half_circle_center, point, {"x": 0, "y": 0, "z": rot})
        )

        base_spiral_arm.append(
            rotate_point_3d(half_circle_center, point, {"x": 0, "y": 0, "z": counter_rot})
        )

        point = dict(point)
        point["z"] += height_offset

    # ---- Rotate base spiral arm ----
    base_spiral_arm = rotate_point_list(
        base_spiral_arm,
        (zone_sides / 2) * -deg,
        center
    )

    # ---- Second spiral arm ----
    second_spiral_arm = rotate_point_list(
        first_spiral_arm,
        deg,
        first_spiral_arm[0]
    )

    # ---- Leaf A ----
    for i in range(len(first_spiral_arm) - 2):
        poly = [
            second_spiral_arm[i],
            second_spiral_arm[i + 1],
            first_spiral_arm[i + 2],
            first_spiral_arm[i + 1]
        ]
        single_leaf_polygons.append(poly)

    # ---- Top shell + seed double leaves ----
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
    for i in range(1, zone_spirals):
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
            rp = rotate_point_3d(
                base_spiral_arm[-1],
                p,
                {"x": 0, "y": 180, "z": 180}
            )
            if zone_spirals > 1:
                rp["z"] += height * (zone_spirals - 1)
            new_poly.append(rp)
        bottom_shell.append(new_poly)

    # ---- Final output ----
    all_polygons = (
        top_shell +
        spiral_case_complete +
        spiral_extensions +
        bottom_shell
    )

    return all_polygons

# Draw Helix Zonohedron
def drawZonohedron(sides, size, detail, zono_type, spirals, spiral_anticlock):
    # Execute
    if zono_type == 'standard':
        result = create_zonohedron(sides, 1)        
        create_from_json_data(result, spiral_anticlock)
    if zono_type == 'spirallohedra':
        result = create_zonohedron(sides, detail)
        create_from_json_data(result, spiral_anticlock)
    if zono_type == 'spiral':
        result = create_spiral_zonohedron(sides, spirals)
        create_from_json_data(result, spiral_anticlock)

# Interface start ------------------------------
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
        # general
        sub_01.prop(cs, "zonohedron_type")
        sub_01.prop(cs, "zonohedron_sides")
        sub_01.prop(cs, "zonohedron_radius")
        sub_01.prop(cs, "zonohedron_reverse")
        # spiral
        sub_02.prop(cs, "zonohedron_spiral")        
        # curved
        sub_03.prop(context.scene, "zonohedron_detail")
        sub_02.enabled = True if cs.zonohedron_type == "spiral" else False
        sub_03.enabled = True if cs.zonohedron_type != "standard" else False
        col.operator("mesh.make_zonohedron", text="Make Zonohedron")


class MakeZonohedron(bpy.types.Operator):
    bl_idname = "mesh.make_zonohedron"
    bl_label = "Add Zonohedron"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        ct = context.scene
        drawZonohedron(ct.zonohedron_sides, ct.zonohedron_radius,
                       ct.zonohedron_detail, ct.zonohedron_type,
                       ct.zonohedron_spiral, ct.zonohedron_reverse)
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
               ('wireframe', 'Curved', 'Curved Wireframe Zonohedron'),               
               )
    ) 
    bpy.types.Scene.zonohedron_sides = bpy.props.IntProperty(
        name="Sides",
        description="Number of Sides",
        min=4,
        max=30,
        default=12,
    )
    bpy.types.Scene.zonohedron_radius = bpy.props.IntProperty(
        name="Radius",
        description="Radius of Zonohedron",
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
    del bpy.types.Scene.zonohedron_radius
    del bpy.types.Scene.zonohedron_detail
    del bpy.types.Scene.zonohedron_spiral
    del bpy.types.Scene.zonohedron_reverse

# Interface end ------------------------------

if __name__ == "__main__":
    register()
    # end if




