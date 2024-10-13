import bpy
import bmesh

import gzip
import os
import struct

from math import *

from .xvi import *
from .mdl import *
from .Utilities import *
from .Blender import *


def build_xvi(data, filename):
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    parent = bpy.context.active_object
    parent.empty_display_size = 0.1
    parent.name = filename

    for mesh_xvi in range(len(data.positions)):  # len(data.positions)

        bpy.ops.object.empty_add(type='PLAIN_AXES')
        empty = bpy.context.active_object
        empty.empty_display_size = 0.1
        empty.name = "mesh_" + str(mesh_xvi)

        empty.parent = parent

        meshPositions = data.positions[mesh_xvi]
        meshTexCoords = data.texCoords[mesh_xvi]
        meshTexCoords2 = data.texCoords2[mesh_xvi]
        meshNormals = data.normals[mesh_xvi]
        meshFaces = data.faces[mesh_xvi]
        meshMaterials = data.materials[mesh_xvi]

        for submesh in range(len(meshPositions)):  # len(meshPositions)

            mesh = bpy.data.meshes.new(str(empty.name + "_" + str(submesh)))
            obj = bpy.data.objects.new(str(empty.name + "_" + str(submesh)), mesh)
            obj.rotation_euler = (radians(90), 0, 0)

            if bpy.app.version >= (2, 80, 0):
                empty.users_collection[0].objects.link(obj)
            else:
                empty.users_collection[0].objects.link(obj)

            obj.parent = empty

            subMeshPositions = meshPositions[submesh]
            subMeshTexCoords = meshTexCoords[submesh]
            subMeshTexCoords2 = meshTexCoords2[submesh]
            subMeshNormals = meshNormals[submesh]
            subMeshFaces = meshFaces[submesh]
            subMeshMaterial = meshMaterials[submesh]

            vertexList = {}
            normals = []

            bm = bmesh.new()
            bm.from_mesh(mesh)

            for j in range(len(subMeshPositions)):

                vertex = bm.verts.new(subMeshPositions[j])

                if subMeshNormals != []:
                    vertex.normal = subMeshNormals[j]
                    normals.append(subMeshNormals[j])

                vertex.index = j

                vertexList[j] = vertex

            for j in range(len(subMeshFaces)):
                try:
                    face = bm.faces.new([vertexList[subMeshFaces[j][0]], vertexList[subMeshFaces[j][1]],
                                         vertexList[subMeshFaces[j][2]]])
                    face.smooth = True
                except:
                    pass

            # Set uv
            for f in bm.faces:
                uv_layer1 = bm.loops.layers.uv.verify()
                for l in f.loops:
                    l[uv_layer1].uv = [subMeshTexCoords[l.vert.index][0], 1 - subMeshTexCoords[l.vert.index][1]]

            bm.to_mesh(mesh)
            bm.free()

            #mesh.use_auto_smooth = True
            if normals:
                mesh.normals_split_custom_set_from_vertices(normals)

            material = bpy.data.materials.get(empty.name + "_" + str(submesh))
            if not material:
                material = bpy.data.materials.new(empty.name + "_" + str(submesh))

                material.use_nodes = True

                bsdf = material.node_tree.nodes["Principled BSDF"]

                bsdf.inputs['Base Color'].default_value = (
                subMeshMaterial[0], subMeshMaterial[1], subMeshMaterial[2], subMeshMaterial[3])

            mesh.materials.append(material)


def build_mdl(data, filename):
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    parent = bpy.context.active_object
    parent.empty_display_size = 0.1
    parent.name = filename
    parent.rotation_euler = (radians(90), 0, 0)

    for mesh_xvi in range(len(data.positions)):  # len(data.positions)

        bpy.ops.object.empty_add(type='PLAIN_AXES')
        empty = bpy.context.active_object
        empty.empty_display_size = 0.1
        empty.name = "mesh_" + str(mesh_xvi)

        empty.parent = parent

        meshPositions = data.positions[mesh_xvi]

        meshTexCoords = data.texCoords[mesh_xvi]
        meshTexCoords2 = data.texCoords2[mesh_xvi]

        meshTexCoordsNoScale = data.texCoordsNoScale[mesh_xvi]
        meshTexCoordsXScaled = data.texCoordsXScaled[mesh_xvi]
        meshTexCoordsYScaled = data.texCoordsYScaled[mesh_xvi]
        meshTexCoordsXYScaled = data.texCoordsXYScaled[mesh_xvi]

        meshNormals = data.normals[mesh_xvi]
        meshFaces = data.faces[mesh_xvi]

        mesh = bpy.data.meshes.new(str(empty.name))
        obj = bpy.data.objects.new(str(empty.name), mesh)

        if bpy.app.version >= (2, 80, 0):
            empty.users_collection[0].objects.link(obj)
        else:
            empty.users_collection[0].objects.link(obj)

        obj.parent = empty

        vertexList = {}
        facesList = []
        normals = []

        bm = bmesh.new()
        bm.from_mesh(mesh)

        if meshTexCoords != []:
            uv_layer1 = bm.loops.layers.uv.new()

        if meshTexCoords2 != []:
            uv_layer2 = bm.loops.layers.uv.new()

        if meshTexCoordsNoScale != []:
            uv_layer3 = bm.loops.layers.uv.new()

        if meshTexCoordsXScaled != []:
            uv_layer4 = bm.loops.layers.uv.new()

        if meshTexCoordsYScaled != []:
            uv_layer5 = bm.loops.layers.uv.new()

        if meshTexCoordsXYScaled != []:
            uv_layer6 = bm.loops.layers.uv.new()

        for j in range(len(meshPositions)):

            vertex = bm.verts.new(meshPositions[j])

            if meshNormals:
                if meshNormals[j] is not None:
                    vertex.normal = meshNormals[j]
                    normals.append(meshNormals[j])

            vertex.index = j

            vertexList[j] = vertex

        # Set faces
        for j in range(len(meshFaces)):
            try:
                face = bm.faces.new(
                    [vertexList[meshFaces[j][0]], vertexList[meshFaces[j][1]], vertexList[meshFaces[j][2]]])
                face.smooth = True
            except:
                for Face in facesList:
                    if {vertexList[meshFaces[j][0]], vertexList[meshFaces[j][1]], vertexList[meshFaces[j][2]]} == set(Face[1]):
                        face = Face[0].copy(verts=False, edges=True)
                        face.normal_flip()
                        face.smooth = True
                        break

            facesList.append(
                [face, [vertexList[meshFaces[j][0]], vertexList[meshFaces[j][1]], vertexList[meshFaces[j][2]]]])

        # Set uv
        if meshTexCoords != []:
            for f in bm.faces:
                # uv_layer1 = bm.loops.layers.uv.verify()
                for l in f.loops:
                    l[uv_layer1].uv = [meshTexCoords[l.vert.index][0], 1 - meshTexCoords[l.vert.index][1]]

        if meshTexCoords2 != []:
            for f in bm.faces:
                # uv_layer2 = bm.loops.layers.uv.verify()
                for l in f.loops:
                    l[uv_layer2].uv = [meshTexCoords2[l.vert.index][0], 1 - meshTexCoords2[l.vert.index][1]]

        if meshTexCoordsNoScale != []:
            for f in bm.faces:
                for l in f.loops:
                    l[uv_layer3].uv = [meshTexCoordsNoScale[l.vert.index][0], 1 - meshTexCoordsNoScale[l.vert.index][1]]

        if meshTexCoordsXScaled != []:
            for f in bm.faces:
                for l in f.loops:
                    l[uv_layer4].uv = [meshTexCoordsXScaled[l.vert.index][0], 1 - meshTexCoordsXScaled[l.vert.index][1]]

        if meshTexCoordsYScaled != []:
            for f in bm.faces:
                for l in f.loops:
                    l[uv_layer5].uv = [meshTexCoordsYScaled[l.vert.index][0], 1 - meshTexCoordsYScaled[l.vert.index][1]]

        if meshTexCoordsXYScaled != []:
            for f in bm.faces:
                for l in f.loops:
                    l[uv_layer6].uv = [meshTexCoordsXYScaled[l.vert.index][0],
                                       1 - meshTexCoordsXYScaled[l.vert.index][1]]

        bm.to_mesh(mesh)
        bm.free()

        #mesh.use_auto_smooth = True
        if normals:
            mesh.normals_split_custom_set_from_vertices(normals)

        material = bpy.data.materials.get(str(data.xvi_header.materials[mesh_xvi]))
        if not material:
            material = bpy.data.materials.new(str(data.xvi_header.materials[mesh_xvi]))

        mesh.materials.append(material)


def main(filepath, files, clear_scene, game_face_generation):
    if clear_scene:
        clearScene()

    folder = (os.path.dirname(filepath))

    for i, j in enumerate(files):

        path_to_file = (os.path.join(folder, j.name))

        f = open(path_to_file, "rb")
        br = BinaryReader(f)

        header = br.bytesToString(br.readBytes(4)).replace("\0", "")
        br.seek(0, 0)

        filename = path_to_file.split("\\")[-1]

        if header == "0IVX":
            xvi = XVI(br, game_face_generation)
            build_xvi(xvi, filename)
        else:
            mdl = MDL(br)
            build_mdl(mdl, filename)
