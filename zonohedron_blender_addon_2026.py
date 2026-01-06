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

# Globals
zone_sides = 12
zone_height = 1
zone_width = 1

def reposId(listlen, listid):
    return listid if listlen > listid else (listid % listlen)


def moveVert(vert, x, y, z):
    return [vert[0] + x, vert[1] + y, vert[2] + z]

def calculate_distance(pos1, pos2, positive_only=True):
    try:
        a = float(pos1["x"]) - float(pos2["x"])
        b = float(pos1["y"]) - float(pos2["y"])
        ans = math.sqrt(a * a + b * b)
        if positive_only:
            ans = abs(ans)
    except Exception:
        ans = 10000
    return ans

def line_angle(pos1, pos2):
    delta_x = pos2["x"] - pos1["x"]
    delta_y = pos2["y"] - pos1["y"]
    rad = math.atan2(delta_y, delta_x)     # radians
    deg = math.degrees(rad)                # convert to degrees
    if deg < 0:
        deg += 360
    return deg

def rotate_point(center_of_rotation, point_to_rotate, degrees):
    length = calculate_distance(center_of_rotation, point_to_rotate, True)
    angle = line_angle(center_of_rotation, point_to_rotate)
    total_angle_rad = math.radians(degrees + angle)
    x_rot = center_of_rotation["x"] + math.cos(total_angle_rad) * length
    y_rot = center_of_rotation["y"] + math.sin(total_angle_rad) * length
    return {"x": x_rot, "y": y_rot}

def createMesh():
    for obj in bpy.data.objects:
        obj.select_set(state=False)
    mesh = bpy.data.meshes.new("mesh")  # add a new mesh
    obj = bpy.data.objects.new("Zonohedron", mesh)  # add a new object
    collection = bpy.context.collection
    collection.objects.link(obj)  # put the object into the scene (link)
    bpy.context.view_layer.objects.active = obj  # set as the active object in the scene
    obj.select_set(state=True)
    mesh = bpy.context.object.data
    bm = bmesh.new()
    bm.to_mesh(mesh)
    bm.free()

def make_polygon(pos_list, index, deg, center_pos, rotation):
    height = 1
    p1 = rotate_point(center_pos, pos_list[index], deg + rotation)
    p2 = rotate_point(center_pos, pos_list[index + 1], rotation)
    p3 = rotate_point(center_pos, pos_list[index + 2], rotation)
    p4 = rotate_point(center_pos, pos_list[index + 1], deg + rotation)    
    h1 = height * (index + 0)
    h2 = height * (index + 1)
    h3 = height * (index + 2)
    h4 = height * (index + 1)   
    return [[p1["x"],p1["y"],h1], [p2["x"], p2["y"],h2], [p3["x"],p3["y"],h3], [p4["x"],p4["y"],h4]]

# Remove Doubles
def cleanUpMesh():
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.object.mode_set(mode='OBJECT')


# Draw Edge Groups
def drawEdgeGroup(edges):
    mesh = bpy.context.object.data
    bm = bmesh.new()
    bpy.ops.object.mode_set(mode='EDIT')
    bm.from_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')
    for edge in edges:
        v0 = bm.verts.new(edge[0])
        v1 = bm.verts.new(edge[1])
        v2 = bm.verts.new(edge[2])
        v3 = bm.verts.new(edge[3])
        if zone_sides % 2 == 0:
            bm.edges.new((v0, v1))
            bm.edges.new((v1, v2))
        else:
            bm.edges.new((v0, v1))
            bm.edges.new((v0, v3))
    bm.to_mesh(mesh)
    bm.free()

# Draw Face Groups
def drawFaceGroup(faces):
    mesh = bpy.context.object.data
    bm = bmesh.new()
    bpy.ops.object.mode_set(mode='EDIT')
    bm.from_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')
    for face in faces:
        vert_list = []
        for vertice in face:
            v = bm.verts.new(vertice)
            vert_list.append(v)
        bm.faces.new(vert_list)
    bm.to_mesh(mesh)
    bm.free()

def render_view(zone_sides, zono_type):
    # designSvg.innerHTML = ''  → handled elsewhere in Python
    center_pos = {"x": 0, "y": 0}
    radius = zone_width/2
    deg = 360 / zone_sides
    pos_list = []
    half_circle_center = {
        "x": center_pos["x"] + radius,
        "y": center_pos["y"]
    }
    # Creates one spiral arm (half circle) and stores in pos_list
    point = {
        "x": center_pos["x"] + (radius * 2),
        "y": center_pos["y"]
    }
    angle = 180
    for i in range(int(zone_sides) + 1):
        rotation = angle + (i * deg)
        this_pos = rotate_point(half_circle_center, point, rotation)
        pos_list.append(this_pos)
    # Make polygons
    for i in range(zone_sides):
        for j in range(len(pos_list) - 2):
            poly_list = make_polygon(pos_list, j, deg, center_pos, i * deg)
            if (zono_type == "standard"):
                drawFaceGroup([poly_list])
            if (zono_type == "wireframe"):    
                drawEdgeGroup([poly_list])
# Draw Helix Zonohedron
def drawZonohedron(sides, radius, detail, zono_type, spirals, spiral_anticlock):
    zone_sides = sides
    createMesh()
    ob = bpy.context.active_object
    obj = bpy.ops.object     
    
    render_view(zone_sides, zono_type)
    
    #if zono_type == "standard":
       #zone_sides
    
    
    # Wireframe : draw edges only for curved and standard helix
    #if (zono_type == "wireframe"):
    #   render_view(sides) #zone_sides
    

    
    
    # if zono_type == "standard":
        # detail = 1
        # spirals = 1
    # elif zono_type == "spiral":
        # detail = 1
    # elif zono_type == "wireframe":
        # spirals = 1
        # sides = sides * detail
    # height = 1
    # degree_inc = 360 / sides
    # degrees = (degree_inc / 2)
    # base_height = 0
    # m_pi = math.pi / 180
    # size = size * 0.2  # adjust	size
    # # Set up lists
    # helix1 = [[[0, 0, 0] for x in range(sides + 1)] for y in range(sides)]
    # helix2 = [[[0, 0, 0] for x in range(sides + 1)] for y in range(sides)]
    # plx = []
    # ply = []
    # # Create the mesh
    # createMesh()
    # ob = bpy.context.active_object
    # obj = bpy.ops.object
    # # assign values to the points list
    # while degrees < 360 + degree_inc:
        # x_pos = math.cos(m_pi * degrees)
        # y_pos = math.sin(m_pi * degrees)
        # plx.append(x_pos)
        # ply.append(y_pos)
        # degrees += degree_inc
    # plxlen = len(plx) - 1
    # zpos_start = 0
    # startindex = int(sides / 2)
    # for i in range(plxlen):
        # plxlen + startindex
        # if i % detail == 0 or zono_type != "wireframe":
            # # helix 1
            # count = 0
            # z_pos_small = zpos_start
            # for j in range((plxlen) + startindex, startindex, -1):
                # jid = reposId(plxlen, j)
                # # top of line is prev f2 calc once at 0
                # f1 = [plx[i] + plx[jid], ply[i] + ply[jid], z_pos_small]
                # z_pos_small -= 1 / (detail * 2)
                # helix1[i][count] = f1
                # count += 1
            # helix1[i][count] = [0, 0, z_pos_small]
            # # helix 2
            # count = 0
            # z_pos_small = zpos_start
            # for j in range(startindex, (plxlen) + startindex):
                # jid = reposId(plxlen, j)
                # # create vertice points
                # f1 = [plx[i] + plx[jid], ply[i] + ply[jid], z_pos_small]
                # z_pos_small -= 1 / (detail * 2)
                # helix2[i][count] = f1
                # count += 1
            # helix2[i][count] = [0, 0, z_pos_small]
        # startindex += 1

    # # Wireframe : draw edges only for curved and standard helix
    # if (zono_type == "wireframe"):
        # for i in range(0, plxlen):
            # edge_list = []
            # a = 0 if i == plxlen - 1 else (i + 1)  # next one returns to 0
            # for k in range(0, plxlen):
                # edge_list.append([helix1[i][k], helix1[i][k + 1]])
                # edge_list.append([helix2[i][k], helix2[i][k + 1]])
            # drawEdgeGroup(edge_list)
        # # get width of x
        # x_width = ob.dimensions[0]

    # # Draw standard zomes 1 for standard 2 for spiral (caps)
    # if zono_type == "standard" or zono_type == "spiral":
        # # List of standard zomes
        # s_zome = [0] if zono_type == "standard" else [0, spirals]
        # for sz in s_zome:
            # for i in range(0, plxlen):
                # face_list = []
                # a = 0 if i == plxlen - 1 else (i + 1)  # next one returns to 0
                # x, y, z = 0, 0, (base_height * sz)
                # for k in range(0, plxlen - 1):
                    # v1 = moveVert(helix1[i][k], x, y, z)
                    # v2 = moveVert(helix1[i][k + 1], x, y, z)
                    # v3 = moveVert(helix1[a][k + 2], x, y, z)
                    # v4 = moveVert(helix1[a][k + 1], x, y, z)
                    # face_list.append([v1, v2, v3, v4])
                # drawFaceGroup(face_list)
            # if sz == 0:
                # base_height = v3[2]
                # x_width = ob.dimensions[0]  # get width of x

    # # Draw spiral sections
    # if (zono_type == "spiral"):
        # height = 1.5 if spirals == 1 else spirals
        # z_adjust = 0
        # for s in range(0, plxlen * spirals):
            # sid = reposId(plxlen, s)
            # sid2 = reposId(plxlen, s + 1)
            # for i in range(0, plxlen):
                # a = 0 if i == plxlen - 1 else (i + 1)  # next one returns to 0
                # if i == sid or i == sid2:
                    # face_list = []
                    # x = helix1[sid2][sid][0]
                    # y = helix1[sid2][sid][1]
                    # z = helix1[sid2][sid][2] + z_adjust
                    # for k in range(0, plxlen - 1):
                        # v1 = moveVert(helix1[i][k], x, y, z)
                        # v2 = moveVert(helix1[i][k + 1], x, y, z)
                        # v3 = moveVert(helix1[a][k + 2], x, y, z)
                        # v4 = moveVert(helix1[a][k + 1], x, y, z)
                        # face_list.append([v1, v2, v3, v4])
                    # drawFaceGroup(face_list)
            # if plxlen - 1 == sid:
                # z_adjust += base_height
    # 

    # Fix scale and transform
    cleanUpMesh()
    z_dimension = zone_width * 1.8
    ob.dimensions = (ob.dimensions[0], ob.dimensions[1], z_dimension)
    obj.transform_apply(location=True, scale=True, rotation=True)
    ob.scale = (radius, radius, radius*1.8)
    obj.transform_apply(location=True, scale=True, rotation=True)
    obj.origin_set(type='GEOMETRY_ORIGIN', center='MEDIAN')
    bpy.context.view_layer.update()


# Interface start ------------------------------
#class ZONO_PT_ZonohedronMaker(bpy.types.Panel):
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
        # spiral
        sub_02.prop(cs, "zonohedron_spiral")
        sub_02.prop(cs, "zonohedron_reverse")
        # curved
        sub_03.prop(context.scene, "zonohedron_detail")
        sub_02.enabled = True if cs.zonohedron_type == "spiral" else False
        sub_03.enabled = True if cs.zonohedron_type == "wireframe" else False
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
               ('spiral', 'Spiral', 'Spiral Zonohedron'),
               ('wireframe', 'Curved', 'Curved Wireframe Zonohedron'))
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
