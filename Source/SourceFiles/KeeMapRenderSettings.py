import bpy
import os

class KeeMapRenderSetting(bpy.types.PropertyGroup): 
      #"""Group of properties representing a bone mapping from OpenPose to a Rig"""       
    output_dir: bpy.props.StringProperty(
        name="Output directory for render result to save",
        description="Select a directory to save",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
        )
 
class KeeMapRenderListItem(bpy.types.PropertyGroup): 
      #"""Group of properties representing a bone mapping from OpenPose to a Rig"""       
    name : bpy.props.StringProperty()
    filepath : bpy.props.StringProperty()

class KEEMAP_LIST_OT_Render_NewItem(bpy.types.Operator): 
    """Add a new item to the list.""" 
    bl_idname = "keemap_render_list.new_item" 
    bl_label = "Add a new item from the selected motion" 

    def execute(self, context): 
        if len(context.scene.keemap_bvh_list) == 0:
            return {'CANCELLED'}
        context.scene.keemap_render_list.add() 
        index = context.scene.keemap_render_list_index = len(context.scene.keemap_render_list) - 1
        render_item = context.scene.keemap_render_list[index]
        bvh_item = context.scene.keemap_bvh_list[context.scene.keemap_bvh_list_index]
        render_item.name = bvh_item.name
        render_item.filepath = bvh_item.filepath
        return{'FINISHED'}       
    
class KEEMAP_LIST_OT_Render_DeleteItem(bpy.types.Operator): 
    """Delete the selected item from the list.""" 
    bl_idname = "keemap_render_list.delete_item" 
    bl_label = "Deletes an item" 
    
    @classmethod 
    def poll(cls, context): 
        return context.scene.keemap_render_list 
    
    def execute(self, context): 
        render_list = context.scene.keemap_render_list
        index = context.scene.keemap_render_list_index
        render_list.remove(index) 
        context.scene.keemap_render_list_index = min(max(0, index - 1), len(render_list) - 1) 
        return{'FINISHED'}

class KEEMAP_LIST_OT_Render_MoveItem(bpy.types.Operator): 
    """Move an item in the list.""" 
    bl_idname = "keemap_render_list.move_item" 
    bl_label = "Move an item in the list" 
    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),)) 

    @classmethod 
    def poll(cls, context): 
        return context.scene.keemap_render_list 
    
    def move_index(self): 
        """ Move index of an item render queue while clamping it. """ 
        scene = bpy.context.scene	
        index = scene.keemap_render_list_index 
        list_length = len(bpy.context.scene.keemap_render_list) - 1 # (index starts at 0) 
        new_index = index + (-1 if self.direction == 'UP' else 1) 
        index = max(0, min(new_index, list_length)) 
    
    def execute(self, context): 
        render_list = context.scene.keemap_render_list 
        scene = context.scene	
        index = scene.keemap_render_list_index 
        neighbor = index + (-1 if self.direction == 'UP' else 1) 
        render_list.move(neighbor, index) 
        self.move_index() 
        return{'FINISHED'}
    
class KEEMAP_LIST_OT_Render_ClearItem(bpy.types.Operator): 
    """Clear all item from the list.""" 
    bl_idname = "keemap_render_list.clear_item" 
    bl_label = "Clear all item" 
    
    @classmethod 
    def poll(cls, context): 
        return context.scene.keemap_render_list 
    
    def execute(self, context): 
        render_list = context.scene.keemap_render_list
        render_list.clear() 
        return{'FINISHED'}
    
class KEEMAP_LIST_OT_Render_RenderAllItem(bpy.types.Operator): 
    """Move an item in the list.""" 
    bl_idname = "keemap_render_list.render_all" 
    bl_label = "Render all items in the list" 

    @classmethod 
    def poll(cls, context): 
        return context.scene.keemap_render_list 
        
    def execute(self, context): 
        if context.scene.keemap_render_setting.output_dir == "":
            self.report({'ERROR'}, "Must specify output directory")
            return {'CANCELLED'}
        render_list = context.scene.keemap_render_list 
        scene = context.scene
        for render_item in render_list:
            # copy from KEEMAP_LIST_OT_ReadInFileAutoTransfer
            filepath = bpy.path.abspath(render_item.filepath)
            
            parent_name = "addon_bvh_parent"
            parent_obj = bpy.data.objects.get(parent_name)
            if parent_obj is None:
                parent_obj = bpy.data.objects.new(parent_name, object_data=None)
                bpy.context.collection.objects.link(parent_obj)

            for children_obj in parent_obj.children:
                bpy.data.armatures.remove(children_obj.data)
                # bpy.data.objects.remove(children_obj)

            bpy.ops.import_anim.bvh(filepath=filepath, rotate_mode='QUATERNION')
            imported_bvh_obj = bpy.context.active_object
            imported_bvh_obj.parent = parent_obj

            dg = bpy.context.evaluated_depsgraph_get()

            # TODO smooth out motions using source armature -> pose mode -> Graph editor -> select all bones -> === -> key -> smooth -> gaussian 
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.select_by_type(type='ARMATURE')
            bpy.ops.object.mode_set(mode='POSE')
            
            KeeMap = bpy.context.scene.keemap_settings 
            KeeMap.source_rig_name = imported_bvh_obj.name
                    
            bpy.ops.wm.perform_animation_transfer()
                    
            # TODO Setup render setting
            filename = render_item.name
            from pathlib import Path
            filename = Path(filename).with_suffix(".mp4")
            context.scene.render.filepath = os.path.join(context.scene.keemap_render_setting.output_dir, filename)
            bpy.ops.render.render('INVOKE_DEFAULT', animation=True)
        return{'FINISHED'}

def register():
    bpy.utils.register_class(KeeMapRenderListItem)
    bpy.types.Scene.keemap_render_list_index = bpy.props.IntProperty()
    bpy.types.Scene.keemap_render_list = bpy.props.CollectionProperty(type = KeeMapRenderListItem) 
    bpy.utils.register_class(KeeMapRenderSetting)
    bpy.types.Scene.keemap_render_setting = bpy.props.PointerProperty(type = KeeMapRenderSetting) 
    bpy.utils.register_class(KEEMAP_LIST_OT_Render_NewItem)
    bpy.utils.register_class(KEEMAP_LIST_OT_Render_DeleteItem)
    bpy.utils.register_class(KEEMAP_LIST_OT_Render_MoveItem)
    bpy.utils.register_class(KEEMAP_LIST_OT_Render_ClearItem)
    bpy.utils.register_class(KEEMAP_LIST_OT_Render_RenderAllItem)


def unregister():
    bpy.utils.unregister_class(KEEMAP_LIST_OT_Render_NewItem)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_Render_DeleteItem)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_Render_MoveItem)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_Render_ClearItem)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_Render_RenderAllItem)

    bpy.utils.unregister_class(KeeMapRenderListItem)
    bpy.utils.unregister_class(KeeMapRenderSetting)    
    del bpy.types.Scene.keemap_render_list
    del bpy.types.Scene.keemap_render_list_index
    del bpy.types.Scene.keemap_render_setting 
