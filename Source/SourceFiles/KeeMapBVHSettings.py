import bpy
 
class KeeMapBVHListItem(bpy.types.PropertyGroup): 
      #"""Group of properties representing a bone mapping from OpenPose to a Rig"""       
    name : bpy.props.StringProperty()
    filepath : bpy.props.StringProperty()

def register():
    bpy.utils.register_class(KeeMapBVHListItem)
    bpy.types.Scene.keemap_bvh_list_index = bpy.props.IntProperty()
    bpy.types.Scene.keemap_bvh_list = bpy.props.CollectionProperty(type = KeeMapBVHListItem) 


def unregister():
    bpy.utils.unregister_class(KeeMapBVHListItem)
    del bpy.types.Scene.keemap_bvh_list
    del bpy.types.Scene.keemap_bvh_list_index