bl_info = {
    "name": "Import/Export XVI XMDL model format",
    "description": "Import and export XVI XMDL models mostly found in PS2 games made by Genki",
    "author": "GreenTrafficLight(original), igorciz777(fork)",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "File > Import > Genki XVI model file (.xvi)",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Import-Export"}

import bpy

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
from bpy.types import Operator


class ImportXVI(Operator, ImportHelper):
    """Load a XVI model file"""
    bl_idname = "import_scene.xvi_data"
    bl_label = "Import XVI model data"

    filename_ext = ""
    filter_glob: StringProperty(default="*", options={'HIDDEN'}, maxlen=255, )

    # Selected files
    files: CollectionProperty(type=bpy.types.PropertyGroup)

    clear_scene: BoolProperty(
        name="Clear scene",
        description="Clear everything from the scene",
        default=False,
    )

    post_kb2_face_generation: BoolProperty(
        name="Post Kaido Battle 2 Face Generation",
        description="Face Generation for PS2 games post Kaido Battle 2",
        default=False,
    )  # To change ?

    def execute(self, context):
        from . import import_xvi
        import_xvi.main(self.filepath, self.files, self.clear_scene, self.post_kb2_face_generation)
        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportXVI.bl_idname, text="Genki XVI model file (.xvi)")


def register():
    bpy.utils.register_class(ImportXVI)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportXVI)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
