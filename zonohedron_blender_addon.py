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
    "version": (1, 2),
    "blender": (2, 75, 0),
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
sides = 12


def reposId(listlen, listid):
    return listid if listlen > listid else (listid % listlen)


def moveVert(vert, x, y, z):
    return [vert[0] + x, vert[1] + y, vert[2] + z]


def createMesh():
    for obj in bpy.data.objects:
        obj.select = False
    mesh = bpy.data.meshes.new("mesh")  # add a new mesh
    obj = bpy.data.objects.new("Zonohedron", mesh)  # add a new object
    scene = bpy.context.scene
    scene.objects.link(obj)  # put the object into the scene (link)
    scene.objects.active = obj  # set as the active object in the scene
    obj.select = True  # select object
    mesh = bpy.context.object.data
    bm = bmesh.new()
    bm.to_mesh(mesh)
    bm.free()


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
        v1 = bm.verts.new(edge[0])
        v2 = bm.verts.new(edge[1])
        bm.edges.new((v1, v2))
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


# Draw Helix Zonohedron
def drawZonohedron(sides, size, detail, zono_type, spirals, spiral_anticlock):
    if zono_type == "standard":
        detail = 1
        spirals = 1
    elif zono_type == "spiral":
        detail = 1
    elif zono_type == "wireframe":
        spirals = 1
        sides = sides * detail
    height = 1
    degree_inc = 360 / sides
    degrees = (degree_inc / 2)
    base_height = 0
    m_pi = math.pi / 180
    size = size * 0.2  # adjust	size
    # Set up lists
    helix1 = [[[0, 0, 0] for x in range(sides + 1)] for y in range(sides)]
    helix2 = [[[0, 0, 0] for x in range(sides + 1)] for y in range(sides)]
    plx = []
    ply = []
    # Create the mesh
    createMesh()
    ob = bpy.context.active_object
    obj = bpy.ops.object
    # assign values to the points list
    while degrees < 360 + degree_inc:
        x_pos = math.cos(m_pi * degrees)
        y_pos = math.sin(m_pi * degrees)
        plx.append(x_pos)
        ply.append(y_pos)
        degrees += degree_inc
    plxlen = len(plx) - 1
    zpos_start = 0
    startindex = int(sides / 2)
    for i in range(plxlen):
        plxlen + startindex
        if i % detail == 0 or zono_type != "wireframe":
            # helix 1
            count = 0
            z_pos_small = zpos_start
            for j in range((plxlen) + startindex, startindex, -1):
                jid = reposId(plxlen, j)
                # top of line is prev f2 calc once at 0
                f1 = [plx[i] + plx[jid], ply[i] + ply[jid], z_pos_small]
                z_pos_small -= 1 / (detail * 2)
                helix1[i][count] = f1
                count += 1
            helix1[i][count] = [0, 0, z_pos_small]
            # helix 2
            count = 0
            z_pos_small = zpos_start
            for j in range(startindex, (plxlen) + startindex):
                jid = reposId(plxlen, j)
                # create vertice points
                f1 = [plx[i] + plx[jid], ply[i] + ply[jid], z_pos_small]
                z_pos_small -= 1 / (detail * 2)
                helix2[i][count] = f1
                count += 1
            helix2[i][count] = [0, 0, z_pos_small]
        startindex += 1

    # Wireframe : draw edges only for curved and standard helix
    if (zono_type == "wireframe"):
        for i in range(0, plxlen):
            edge_list = []
            a = 0 if i == plxlen - 1 else (i + 1)  # next one returns to 0
            for k in range(0, plxlen):
                edge_list.append([helix1[i][k], helix1[i][k + 1]])
                edge_list.append([helix2[i][k], helix2[i][k + 1]])
            drawEdgeGroup(edge_list)
        # get width of x
        x_width = ob.dimensions[0]

    # Draw standard zomes 1 for standard 2 for spiral (caps)
    if zono_type == "standard" or zono_type == "spiral":
        # List of standard zomes
        s_zome = [0] if zono_type == "standard" else [0, spirals]
        for sz in s_zome:
            for i in range(0, plxlen):
                face_list = []
                a = 0 if i == plxlen - 1 else (i + 1)  # next one returns to 0
                x, y, z = 0, 0, (base_height * sz)
                for k in range(0, plxlen - 1):
                    v1 = moveVert(helix1[i][k], x, y, z)
                    v2 = moveVert(helix1[i][k + 1], x, y, z)
                    v3 = moveVert(helix1[a][k + 2], x, y, z)
                    v4 = moveVert(helix1[a][k + 1], x, y, z)
                    face_list.append([v1, v2, v3, v4])
                drawFaceGroup(face_list)
            if sz == 0:
                base_height = v3[2]
                x_width = ob.dimensions[0]  # get width of x

    # Draw spiral sections
    if (zono_type == "spiral"):
        height = 1.5 if spirals == 1 else spirals
        z_adjust = 0
        for s in range(0, plxlen * spirals):
            sid = reposId(plxlen, s)
            sid2 = reposId(plxlen, s + 1)
            for i in range(0, plxlen):
                a = 0 if i == plxlen - 1 else (i + 1)  # next one returns to 0
                if i == sid or i == sid2:
                    face_list = []
                    x = helix1[sid2][sid][0]
                    y = helix1[sid2][sid][1]
                    z = helix1[sid2][sid][2] + z_adjust
                    for k in range(0, plxlen - 1):
                        v1 = moveVert(helix1[i][k], x, y, z)
                        v2 = moveVert(helix1[i][k + 1], x, y, z)
                        v3 = moveVert(helix1[a][k + 2], x, y, z)
                        v4 = moveVert(helix1[a][k + 1], x, y, z)
                        face_list.append([v1, v2, v3, v4])
                    drawFaceGroup(face_list)
            if plxlen - 1 == sid:
                z_adjust += base_height
    cleanUpMesh()

    # Fix scale and transform
    y_dimension = (x_width * 2) * height
    ob.dimensions = (ob.dimensions[0], ob.dimensions[1], y_dimension)
    obj.transform_apply(location=True, scale=True, rotation=True)
    ob.scale = (size, size, size)
    obj.transform_apply(location=True, scale=True, rotation=True)
    obj.origin_set(type='GEOMETRY_ORIGIN', center='MEDIAN')
    if spiral_anticlock:
        bpy.ops.transform.mirror(constraint_axis=(False, True, False))
    bpy.context.scene.update()


# Interface start ------------------------------
class ZonohedronMakerPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_category = "Create"
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
        sub_01.prop(cs, "zonohedron_size")
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
        drawZonohedron(ct.zonohedron_sides, ct.zonohedron_size,
                       ct.zonohedron_detail, ct.zonohedron_type,
                       ct.zonohedron_spiral, ct.zonohedron_reverse)
        return {"FINISHED"}


# Imitate steps 2,4,6,etc
def even_only(self, context):
    global sides
    int_sides = context.scene.zonohedron_sides
    if int_sides % 2 != 0:
        int_sides = int_sides - 1 if int_sides < sides else int_sides + 1
        context.scene.zonohedron_sides = int_sides
    sides = int_sides


def register():
    bpy.utils.register_class(MakeZonohedron)
    bpy.utils.register_class(ZonohedronMakerPanel)
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
        update=even_only
    )
    bpy.types.Scene.zonohedron_size = bpy.props.IntProperty(
        name="Size",
        description="Size of Zonohedron",
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
    bpy.utils.unregister_class(ZonohedronMakerPanel)
    del bpy.types.Scene.zonohedron_type
    del bpy.types.Scene.zonohedron_sides
    del bpy.types.Scene.zonohedron_size
    del bpy.types.Scene.zonohedron_detail
    del bpy.types.Scene.zonohedron_spiral
    del bpy.types.Scene.zonohedron_reverse


# Interface end ------------------------------

if __name__ == "__main__":
    register()
    # end if
