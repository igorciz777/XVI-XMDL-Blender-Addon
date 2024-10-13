from .Utilities import *
from mathutils import *

import struct
import numpy as np


class XVI_Header(object):
    def __init__(self, br):
        super().__init__()

        self.xvi_header = br.bytesToString(br.readBytes(4)).replace("\0", "")
        self.xvi_version = br.bytesToString(br.readBytes(4)).replace("\0", "")
        br.seek(8, 1)  # zeros
        self.xmdl_header = br.bytesToString(br.readBytes(4)).replace("\0", "")
        self.xmdl_version = br.bytesToString(br.readBytes(4)).replace("\0", "")
        self.norm_header = br.bytesToString(br.readBytes(4)).replace("\0", "")
        self.norm_version = br.bytesToString(br.readBytes(4)).replace("\0", "")

        self.unknownCount = br.readUInt()
        self.meshCount = br.readUInt()

        br.seek(4, 1)  # zeros
        unknownSize = br.readUInt()
        br.seek(unknownSize, 1)  # ???

        for i in range(self.unknownCount):
            br.seek(48, 1)  # ???


class XVI_meshHeader(object):
    def __init__(self, br):
        super().__init__()

        self.submeshCount = 0

        br.seek(4, 1)  # ???
        self.id = br.readUInt()
        br.seek(4, 1)  # ???
        self.flag = br.readUShort()

        br.seek(2, 1)  # ???
        br.seek(16, 1)  # ???

        br.seek(48, 1)  # ???

        if self.flag != 0:
            br.seek(12, 1)  # ???
            self.submeshCount = br.readUInt()

            br.seek(16, 1)  # ???
            br.seek(16, 1)  # ???


class XVI_subMeshHeader(object):
    def __init__(self, br, xmdl_version, norm_version):
        super().__init__()

        # print(br.tell())
        br.seek(16, 1)  # ???
        self.r, self.g, self.b, self.a = br.readFloat(), br.readFloat(), br.readFloat(), br.readFloat()
        br.seek(16, 1)  # ???
        br.seek(12, 1)  # ???
        br.seek(4, 1)  # ???

        br.seek(48, 1)  # ???

        if xmdl_version == "00.1" and norm_version == "00.1":
            br.seek(48, 1)  # ???

        br.seek(4, 1)  # ???
        self.chunkCount = br.readUInt()
        br.seek(8, 1)  # ???

        br.seek(16, 1)  # ???
        br.seek(16, 1)  # ???


class XVI_chunk(object):
    def __init__(self, br, subMeshFaces, index, xmdl_version, norm_version, post_kb2_face_generation):
        super().__init__()

        self.faceDir = False
        reverseFaceDir = False

        self.dataLength = br.readUInt()
        br.seek(8, 1)  # ???
        self.count = br.readUInt()
        self.dataLength = (self.dataLength & 0x7FFF) * (self.dataLength >> 24) + br.tell()

        self.chunkInfo = []
        self.chunkPositions = []
        self.chunkTexCoords = []
        self.chunkTexCoords2 = []
        self.chunkNormals = []
        self.chunkFaces = []
        self.chunkFacesDir = []

        if post_kb2_face_generation == True:
            # 0x68 (y value and 0xFFFFFFFE reset)
            faceGenerationMethod1 = True
        else:
            faceGenerationMethod1 = False

        faceGenerationMethod2 = False  # 0x62 (0xFFFF reset)
        faceGenerationMethod3 = False  # 0x6E (with 01 01 01 reset ?)
        faceGenerationMethod4 = False  # 0x6E (with 0xFFFF reset ?)

        while (br.tell() < self.dataLength):

            IMMEDIATE = br.readUShort()
            NUM = br.readUByte()
            CMD = br.readUByte()

            if CMD == 1:
                cl = IMMEDIATE & 0xFF
                wl = (IMMEDIATE >> 8) & 0xFF
                continue
            elif CMD == 17:
                continue

            elif CMD & 0x60 == 0x60:
                resetFlags = []

                if CMD == 0x62:  # Face Information
                    for i in range(NUM):
                        resetFlags.append(br.readUByte())
                        if resetFlags[i] != 0xFF:
                            faceGenerationMethod2 = True
                    # TO FIX
                    skip = ((NUM * 3) + 3) & ~3
                    br.seek(skip - (NUM * 3), 1)

                    if faceGenerationMethod2 == True:
                        print("Face Generation Method 2")
                        self.chunkFaces = []
                        self.chunkFacesDir = []
                        resetFlag = ""
                        index -= NUM
                        for i in range(NUM):
                            if resetFlags[i] == 0xFF:
                                resetFlag += "FF"
                            elif resetFlag != "":
                                if i > 2:
                                    print(i - 2)
                                    print(resetFlag)
                                    self.chunkFaces.insert(len(self.chunkFaces) - 2, 65535)
                                    if (i - 2) % 2 != 0:
                                        self.chunkFacesDir.append(index - 2)
                                resetFlag = ""
                            self.chunkFaces.append(index)
                            index += 1

                elif CMD == 0x64:  # TexCoords
                    for i in range(NUM):
                        self.chunkTexCoords.append([br.readFloat(), br.readFloat()])

                elif CMD == 0x65:  # TexCoords
                    for i in range(NUM):
                        self.chunkTexCoords.append([br.readShort() / 4096, br.readShort() / 4096])

                elif CMD == 0x68:  # Positions
                    # print("position " + str(hex(br.tell())))
                    resetFlag = ""

                    if reverseFaceDir == True:
                        self.chunkFacesDir.append(index)

                    for i in range(NUM):

                        coordinates = br.readBytes(12)
                        x = struct.unpack(br.endian + "f", coordinates[0:4])[0]
                        y = struct.unpack(br.endian + "f", coordinates[4:8])[0]
                        z = struct.unpack(br.endian + "f", coordinates[8:12])[0]
                        self.chunkPositions.append([x, y, z])

                        y_int = struct.unpack(br.endian + "I", coordinates[4:8])[0]

                        if faceGenerationMethod1 == True:
                            reset = y_int & 0xFFFFFFFE
                            if reset != y_int:
                                resetFlag += "FF"
                                self.chunkFaces.append(index)
                            else:
                                if i > 2 and resetFlag != "":
                                    self.chunkFaces.insert(len(self.chunkFaces) - 2, 65535)
                                    if (i - 2) % 2 != 0 and reverseFaceDir == False:
                                        self.chunkFacesDir.append(index - 2)
                                    elif (i - 2) % 2 == 0 and reverseFaceDir == True:
                                        self.chunkFacesDir.append(index - 2)
                                resetFlag = ""
                                self.chunkFaces.append(index)
                            index += 1
                        else:
                            self.chunkFaces.append(index)
                            index += 1

                    # print(NUM)

                elif CMD == 0x69:  # TexCoords ?
                    for i in range(NUM):
                        br.seek(6, 1)

                elif CMD == 0x6A:  # Normals
                    for i in range(NUM):
                        self.chunkNormals.append(
                            Vector((br.readByte() / 127, br.readByte() / 127, br.readByte() / 127)).normalized())
                    skip = ((NUM * 3) + 3) & ~3
                    br.seek(skip - (NUM * 3), 1)

                elif CMD == 0x6C:  # Bounding Box / Face winding
                    for i in range(NUM):
                        self.chunkInfo.append([br.readBytes(4), br.readBytes(4), br.readBytes(4), br.readBytes(4)])

                    if len(self.chunkInfo) == 2:
                        windingFlag = struct.unpack(br.endian + "f", self.chunkInfo[0][3])[0]
                        if windingFlag < 0:
                            reverseFaceDir = True
                        elif windingFlag > 0:
                            reverseFaceDir = False

                    elif len(self.chunkInfo) == 4:
                        windingFlag = struct.unpack(br.endian + "f", self.chunkInfo[3][3])[0]
                        if windingFlag < 0:
                            reverseFaceDir = True
                        elif windingFlag > 0:
                            reverseFaceDir = False

                elif CMD == 0x6D:  # Normals (Pre-Tokyo Xtreme Racer Drift 2) and Texture Coordinates

                    if xmdl_version == "00.2" and norm_version == "00.2":
                        for i in range(NUM):  # Normals (Pre-Tokyo Xtreme Racer Drift 2)
                            self.chunkNormals.append(Vector(
                                (br.readShortToFloat(), br.readShortToFloat(), br.readShortToFloat())).normalized())
                            normalDivisor = br.readShort()

                    elif xmdl_version == "00.1" and norm_version == "00.1":
                        for i in range(NUM):  # Texture Coordinates
                            self.chunkTexCoords.append([br.readShort() / 32767 * 8, br.readShort() / 32767 * 8])
                            self.chunkTexCoords2.append([br.readShort() / 32767, br.readShort() / 32767])

                elif CMD == 0x6E:
                    resetFlags = []
                    for i in range(NUM):
                        resetFlags.append([br.readUByte(), br.readUByte(), br.readUByte(), br.readUByte()])

                    if resetFlags[0][0] == 1 and resetFlags[0][1] == 1 and resetFlags[0][2] == 1:
                        faceGenerationMethod3 = True
                    else:
                        faceGenerationMethod4 = True

                    # TEST
                    if faceGenerationMethod3 == True:
                        print("Face Generation Method 3")
                        self.chunkFaces = []
                        self.chunkFacesDir = []
                        resetFlag = ""
                        index -= NUM
                        for i in range(NUM):
                            if resetFlags[i][0] == 1 and resetFlags[i][1] == 1 and resetFlags[i][2] == 1:  # ?
                                resetFlag += "FF"
                            elif resetFlag != "":
                                if i > 2:
                                    print(i - 2)
                                    print(resetFlag)
                                    self.chunkFaces.insert(len(self.chunkFaces) - 2, 65535)
                                    if (i - 2) % 2 != 0:
                                        self.chunkFacesDir.append(index - 2)
                                resetFlag = ""
                            self.chunkFaces.append(index)
                            index += 1

                    """
                    if faceGenerationMethod4 == True:
                        self.chunkFaces = []
                        resetFlag = ""
                        index -= NUM
                        for i in range(NUM):
                            if resetFlags[i][3] == 0xFF:
                                resetFlag += "FF"
                            elif resetFlag != "":                    
                                if i > 2:
                                    self.chunkFaces.insert(len(self.chunkFaces) - 2, 65535)
                                resetFlag = ""
                            self.chunkFaces.append(index)
                            index += 1
                    """

                else:
                    print("UNKNOWN : " + str(CMD))
        br.seek(self.dataLength, 0)  # test


class XVI(object):
    def __init__(self, br, post_kb2_face_generation):
        super().__init__()

        self.positions = []
        self.texCoords = []
        self.texCoords2 = []
        self.normals = []
        self.faces = []
        self.materials = []

        self.ivx_header = XVI_Header(br)

        for a in range(self.ivx_header.meshCount):  # self.ivx_header.meshCount

            print("mesh position " + str(a) + " : " + str(br.tell()))
            self.ivx_meshHeader = XVI_meshHeader(br)

            meshPositions = []
            meshTexCoords = []
            meshTexCoords2 = []
            meshNormals = []
            meshFaces = []
            meshMaterials = []

            # if a == 6:
            # print(self.ivx_meshHeader.submeshCount)
            # self.ivx_meshHeader.submeshCount = 4

            for b in range(self.ivx_meshHeader.submeshCount):  # self.ivx_meshHeader.submeshCount

                print("submesh position " + str(b) + " : " + str(br.tell()))
                self.ivx_submeshHeader = XVI_subMeshHeader(br, self.ivx_header.xmdl_version,
                                                           self.ivx_header.norm_version)

                subMeshPositions = []
                subMeshTexCoords = []
                subMeshTexCoords2 = []
                subMeshNormals = []
                subMeshFaces = []
                subMeshFacesDirection = []

                index = 0

                # if a == 23:
                # self.ivx_submeshHeader.chunkCount = 3

                for c in range(self.ivx_submeshHeader.chunkCount):  # self.ivx_submeshHeader.chunkCount

                    # print("Chunck position : " + str(br.tell()))
                    ivx_chunk = XVI_chunk(br, subMeshFaces, index, self.ivx_header.xmdl_version,
                                          self.ivx_header.norm_version, post_kb2_face_generation)

                    subMeshPositions.extend(ivx_chunk.chunkPositions)

                    if ivx_chunk.chunkTexCoords == []:
                        for i in range(ivx_chunk.count):
                            subMeshTexCoords.append([0, 0, 0])
                    else:
                        subMeshTexCoords.extend(ivx_chunk.chunkTexCoords)

                    if ivx_chunk.chunkTexCoords2 == []:
                        for i in range(ivx_chunk.count):
                            subMeshTexCoords2.append([0, 0, 0])
                    else:
                        subMeshTexCoords2.extend(ivx_chunk.chunkTexCoords2)

                    if ivx_chunk.chunkNormals == []:
                        for i in range(ivx_chunk.count):
                            subMeshNormals.append([0, 0, 0])
                    else:
                        subMeshNormals.extend(ivx_chunk.chunkNormals)

                    subMeshFaces.extend(ivx_chunk.chunkFaces)
                    subMeshFaces.append(65535)

                    subMeshFacesDirection.extend(ivx_chunk.chunkFacesDir)

                    index = len(subMeshPositions)

                br.seek(16, 1)

                meshPositions.append(subMeshPositions)
                meshTexCoords.append(subMeshTexCoords)
                meshTexCoords2.append(subMeshTexCoords2)
                meshNormals.append(subMeshNormals)
                meshFaces.append(StripToTriangle(subMeshFaces, subMeshFacesDirection))
                meshMaterials.append([self.ivx_submeshHeader.r, self.ivx_submeshHeader.g, self.ivx_submeshHeader.b,
                                      self.ivx_submeshHeader.a])

            self.positions.append(meshPositions)
            self.texCoords.append(meshTexCoords)
            self.texCoords2.append(meshTexCoords2)
            self.normals.append(meshNormals)
            self.faces.append(meshFaces)
            self.materials.append(meshMaterials)

            print("end : " + str(br.tell()))
