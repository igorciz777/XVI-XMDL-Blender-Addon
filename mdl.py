from .Utilities import *
from mathutils import *

import struct
import numpy as np

class MDL_Header(object):
    def __init__(self, br):
        super().__init__()

        self.materials = []
       
        br.seek(0, 0)
        self.meshCount = br.readUInt()
        br.seek(12,1) # zeros
        for i in range(self.meshCount):
            self.materials.append(br.readUInt())
            br.seek(12, 1)

class MDL_MeshHeader(object):
    def __init__(self, br):
        super().__init__()

        br.seek(4,1) # ???
        self.chunkCount = br.readUInt()
        br.seek(8,1) # ???

        br.seek(16, 1) # ???
        br.seek(16, 1) # ???

class MDL_chunk(object):
    def __init__(self, br, subMeshFaces, index, ivx_header):
        super().__init__()

        self.faceDir = False
        reverseFaceDir = False

        self.dataLength = br.readUInt()
        br.seek(8,1) # ???
        self.count = br.readUInt()
        self.dataLength = (self.dataLength & 0x7FFF) * (self.dataLength >> 24) + br.tell()

        self.chunkInfo = []
        self.chunkPositions = []
        
        self.chunkTexCoords = []
        self.chunkTexCoords2 = []
        
        self.chunkTexCoordsNoScale = []
        self.chunkTexCoordsXScaled = []
        self.chunkTexCoordsYScaled = []
        self.chunkTexCoordsXYScaled = []
        
        self.chunkNormals = []
        self.chunkColors = []

        self.chunkFaces = []
        self.chunkFacesDir = []

        duplicates = []
        
        faceGenerationMethod2 = False #0x62 (0xFFFF reset)
        faceGenerationMethod3 = False #0x6E (with 01 01 01 reset ?)
        faceGenerationMethod4 = False #0x6E (with 0xFFFF reset ?)

        while(br.tell() < self.dataLength):
            
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

                # unpack command
                mask = ((CMD & 0x10) == 0x10)
                vn = (CMD >> 2) & 3
                vl = CMD & 3
                addr = IMMEDIATE & 0x1ff
                flag = (IMMEDIATE & 0x8000) == 0x8000
                usn = (IMMEDIATE & 0x4000) == 0x4000

                flags = []

                if CMD == 0x62: # Face Information
                    for i in range(NUM):
                        flags.append(br.readUByte())
                        if flags[i] != 0xFF:
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
                            if int(bin(flags[i])[-1]) == 1:
                                resetFlag += "FF"
                            elif resetFlag != "":                    
                                if i > 2:
                                    self.chunkFaces.insert(len(self.chunkFaces) - 2, 65535)
                                    if (i - 2) % 2 != 0 and reverseFaceDir == False:
                                        self.chunkFacesDir.append(index - 2)
                                    elif (i - 2) % 2 == 0 and reverseFaceDir == True:
                                        self.chunkFacesDir.append(index - 2)
                                resetFlag = ""
                            self.chunkFaces.append(index)
                            index += 1
          
                elif CMD == 0x64: # TexCoords
                    for i in range(NUM):
                        self.chunkTexCoords.append([br.readFloat() * 8, br.readFloat() * 8])
                
                elif CMD == 0x65: # TexCoords
                    for i in range(NUM):
                        u = br.readShort()
                        v = br.readShort()
                        
                        self.chunkTexCoords.append([u / 4096, v / 4096])
                        
                        self.chunkTexCoordsNoScale.append([u / 4096, v / 4096])
                        self.chunkTexCoordsXScaled.append([u / 2048, v / 4096])
                        self.chunkTexCoordsYScaled.append([u / 4096, v / 2048])
                        self.chunkTexCoordsXYScaled.append([u / 2048, v / 2048])
                
                elif CMD == 0x68: # Positions
                    #print("position " + str(hex(br.tell())))
                    resetFlag = ""

                    if reverseFaceDir == True:
                        self.chunkFacesDir.append(index)
                    
                    for i in range(NUM):

                        coordinates = br.readBytes(12)
                        x = struct.unpack(br.endian + "f", coordinates[0:4])[0]
                        y = struct.unpack(br.endian + "f", coordinates[4:8])[0]
                        z = struct.unpack(br.endian + "f", coordinates[8:12])[0]
                        
                        #if self.chunkPositions != [] and [x, y, z] == self.chunkPositions[-1]:
                            #duplicates.append(index)
                        #else:
                        self.chunkPositions.append([x, y, z])

                        self.chunkFaces.append(index)
                        index += 1

                elif CMD == 0x69: # TexCoords ?
                    for i in range(NUM):
                        br.seek(6, 1)
                
                elif CMD == 0x6A: # Normals
                    for i in range(NUM):
                        self.chunkNormals.append(Vector((br.readByte() / 127, br.readByte() / 127, br.readByte() / 127)).normalized())                    
                    skip = ((NUM * 3) + 3) & ~3
                    br.seek(skip - (NUM * 3), 1)
                
                elif CMD == 0x6C: # Bounding Box / Face winding 
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

                elif CMD == 0x6D: # Normals (Pre-Tokyo Xtreme Racer Drift 2) and Texture Coordinates 
                    
                    if ivx_header.xmdl_version == "00.2" and ivx_header.norm_version == "00.2" :
                        for i in range(NUM): # Normals (Pre-Tokyo Xtreme Racer Drift 2)
                            self.chunkNormals.append(Vector((br.readShortToFloat(), br.readShortToFloat(), br.readShortToFloat())).normalized())
                            normalDivisor = br.readShort()
                    
                    elif ivx_header.xmdl_version == "00.1" and ivx_header.norm_version == "00.1" :
                        for i in range(NUM): # Texture Coordinates
                            self.chunkTexCoords.append([br.readShort() / 32767, br.readShort() / 32767])
                            self.chunkTexCoords2.append([br.readShort() / 32767, br.readShort() / 32767])
                            
                elif CMD == 0x6E:
                    flags = []

                    for i in range(NUM):
                        flags.append([br.readUByte(), br.readUByte(), br.readUByte(), br.readUByte()])
                        self.chunkColors.append(Vector((flags[i][0] / 0xFF, flags[i][1] / 0xFF, flags[i][2] / 0xFF)).normalized())
                    
                    self.chunkFaces = []
                    
                    resetFlag = ""
                    index -= NUM
                    for i in range(NUM):
                        if int(bin(flags[i][3])[-1]) == 1:
                            resetFlag += "FF"
                        elif resetFlag != "":                    
                            if i > 2 and resetFlag != "":
                                self.chunkFaces.insert(len(self.chunkFaces) - 2, 65535)
                                if (i - 2) % 2 != 0 and reverseFaceDir == False:
                                    self.chunkFacesDir.append(index - 2)
                                elif (i - 2) % 2 == 0 and reverseFaceDir == True:
                                    self.chunkFacesDir.append(index - 2)
                            resetFlag = ""

                        #if index in duplicates:
                            #print("test")
                            #self.chunkPositions.pop(index - NUM)
                            #duplicates.remove(index) 
                        #else:
                        self.chunkFaces.append(index)
                        index += 1                    
                    
                else:
                    print("UNKNOWN : " + str(CMD))
        
        br.seek(self.dataLength, 0) # test

class MDL(object):
    def __init__(self, br):
        super().__init__()

        self.positions = []
        
        self.texCoords = []
        self.texCoords2 = []

        self.texCoordsNoScale = []
        self.texCoordsXScaled = []
        self.texCoordsYScaled = []
        self.texCoordsXYScaled = []
        
        self.normals = []
        self.colors = []

        self.faces = []

        self.ivx_header = MDL_Header(br)

        for a in range(self.ivx_header.meshCount): # self.ivx_header.meshCount

            print("mesh position " + str(a) + " : " + str(br.tell()))
            
            self.ivx_meshHeader = MDL_MeshHeader(br)

            Mesh_Positions = []
            
            Mesh_TexCoords = []
            Mesh_TexCoords2 = []

            Mesh_TexCoordsNoScale = []
            Mesh_TexCoordsXScaled = []
            Mesh_TexCoordsYScaled = []
            Mesh_TexCoordsXYScaled = []
            
            Mesh_Normals = []
            Mesh_Colors = []
            
            MeshFaces = []
            MeshFacesDirection = []

            index = 0
            
            #if a == 2:
                #self.ivx_meshHeader.chunkCount = 1

            for c in range(self.ivx_meshHeader.chunkCount): # self.ivx_meshHeader.chunkCount

                print("Chunck position : " + str(br.tell()))

                ivx_chunk = MDL_chunk(br, MeshFaces, index, self.ivx_header)
                
                Mesh_Positions.extend(ivx_chunk.chunkPositions)
                
                if ivx_chunk.chunkTexCoords == []:
                    for i in range(ivx_chunk.count):
                        Mesh_TexCoords.append([0,0,0])
                else:
                    Mesh_TexCoords.extend(ivx_chunk.chunkTexCoords)
                
                if ivx_chunk.chunkTexCoords2 == []:
                    for i in range(ivx_chunk.count):
                        Mesh_TexCoords2.append([0,0,0])
                else:
                    Mesh_TexCoords2.extend(ivx_chunk.chunkTexCoords2)

                if ivx_chunk.chunkTexCoordsNoScale == []:
                    for i in range(ivx_chunk.count):
                        Mesh_TexCoordsNoScale.append([0,0,0])
                else:
                    Mesh_TexCoordsNoScale.extend(ivx_chunk.chunkTexCoordsNoScale)

                if ivx_chunk.chunkTexCoordsXScaled == []:
                    for i in range(ivx_chunk.count):
                        Mesh_TexCoordsXScaled.append([0,0,0])
                else:
                    Mesh_TexCoordsXScaled.extend(ivx_chunk.chunkTexCoordsXScaled)

                if ivx_chunk.chunkTexCoordsYScaled == []:
                    for i in range(ivx_chunk.count):
                        Mesh_TexCoordsYScaled.append([0,0,0])
                else:
                    Mesh_TexCoordsYScaled.extend(ivx_chunk.chunkTexCoordsYScaled)

                if ivx_chunk.chunkTexCoordsXYScaled == []:
                    for i in range(ivx_chunk.count):
                        Mesh_TexCoordsXYScaled.append([0,0,0])
                else:
                    Mesh_TexCoordsXYScaled.extend(ivx_chunk.chunkTexCoordsXYScaled)

                if ivx_chunk.chunkNormals == []:
                    for i in range(ivx_chunk.count):
                        Mesh_Normals.append(None)
                else:
                    Mesh_Normals.extend(ivx_chunk.chunkNormals)

                MeshFaces.extend(ivx_chunk.chunkFaces)
                MeshFaces.append(65535)
                #for faces in MeshFaces:
                    #print(faces)
                    
                MeshFacesDirection.extend(ivx_chunk.chunkFacesDir)

                index = len(Mesh_Positions)

            br.seek(16, 1)
            
            self.positions.append(Mesh_Positions)
            
            self.texCoords.append(Mesh_TexCoords)
            self.texCoords2.append(Mesh_TexCoords2)

            self.texCoordsNoScale.append(Mesh_TexCoordsNoScale)
            self.texCoordsXScaled.append(Mesh_TexCoordsXScaled)
            self.texCoordsYScaled.append(Mesh_TexCoordsYScaled)
            self.texCoordsXYScaled.append(Mesh_TexCoordsXYScaled)

            self.normals.append(Mesh_Normals)
            self.faces.append(StripToTriangle(MeshFaces, MeshFacesDirection))

        print("end : " + str(br.tell()))

