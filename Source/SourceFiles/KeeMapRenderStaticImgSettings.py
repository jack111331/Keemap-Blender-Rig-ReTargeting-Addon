import bpy
import os

class KeeMapRenderStaticImgSetting(bpy.types.PropertyGroup): 
      #"""Group of properties representing a bone mapping from OpenPose to a Rig"""       
    output_dir: bpy.props.StringProperty(
        name="Output directory for render result to save",
        description="Select a directory to save",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
        )
 
class KeeMapRenderStaticImgListItem(bpy.types.PropertyGroup): 
    #"""Group of properties representing a bone mapping from OpenPose to a Rig"""       
    name : bpy.props.StringProperty()
    frame_idx : bpy.props.IntProperty(
        name="Static image frame index",
        description="Frame index for rendering static image",
        default=0,
    )

class KEEMAP_LIST_OT_RenderStaticImg_NewItem(bpy.types.Operator): 
    """Add a new item to the list.""" 
    bl_idname = "keemap_render_static_img_list.new_item" 
    bl_label = "Add a new item from the selected motion" 

    def execute(self, context): 
        if len(context.scene.keemap_bvh_list) == 0:
            return {'CANCELLED'}
        context.scene.keemap_render_static_img_list.add() 
        index = context.scene.keemap_render_static_img_list_index = len(context.scene.keemap_render_static_img_list) - 1
        render_item = context.scene.keemap_render_static_img_list[index]
        render_item.name = str(context.scene.frame_current)
        render_item.frame_idx = context.scene.frame_current
        return{'FINISHED'}       
    
class KEEMAP_LIST_OT_RenderStaticImg_DeleteItem(bpy.types.Operator): 
    """Delete the selected item from the list.""" 
    bl_idname = "keemap_render_static_img_list.delete_item" 
    bl_label = "Deletes an item" 
    
    @classmethod 
    def poll(cls, context): 
        return context.scene.keemap_render_static_img_list 
    
    def execute(self, context): 
        render_static_img_list = context.scene.keemap_render_static_img_list
        index = context.scene.keemap_render_static_img_list_index
        render_static_img_list.remove(index)
        context.scene.keemap_render_static_img_list_index = min(max(0, index - 1), len(render_static_img_list) - 1) 
        return{'FINISHED'}

class KEEMAP_LIST_OT_RenderStaticImg_MoveItem(bpy.types.Operator): 
    """Move an item in the list.""" 
    bl_idname = "keemap_render_static_img_list.move_item" 
    bl_label = "Move an item in the list" 
    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),)) 

    @classmethod 
    def poll(cls, context): 
        return context.scene.keemap_render_static_img_list 
    
    def move_index(self): 
        """ Move index of an item render queue while clamping it. """ 
        scene = bpy.context.scene	
        index = scene.keemap_render_static_img_list_index 
        list_length = len(bpy.context.scene.keemap_render_static_img_list) - 1 # (index starts at 0) 
        new_index = index + (-1 if self.direction == 'UP' else 1) 
        scene.keemap_render_static_img_list_index = max(0, min(new_index, list_length)) 
    
    def execute(self, context): 
        render_list = context.scene.keemap_render_static_img_list 
        scene = context.scene	
        index = scene.keemap_render_static_img_list_index 
        neighbor = index + (-1 if self.direction == 'UP' else 1) 
        render_list.move(neighbor, index) 
        self.move_index() 
        return{'FINISHED'}
    
class KEEMAP_LIST_OT_RenderStaticImg_ClearItem(bpy.types.Operator): 
    """Clear all item from the list.""" 
    bl_idname = "keemap_render_static_img_list.clear_item" 
    bl_label = "Clear all item" 
    
    @classmethod 
    def poll(cls, context): 
        return context.scene.keemap_render_static_img_list 
    
    def execute(self, context): 
        render_list = context.scene.keemap_render_static_img_list
        render_list.clear() 
        return{'FINISHED'}
    
class KEEMAP_LIST_OT_RenderStaticImg_SetupRender(bpy.types.Operator): 
    """Move an item in the list.""" 
    bl_idname = "keemap_render_static_img_list.setup_render" 
    bl_label = "Setup rendering for all items" 

    @classmethod 
    def poll(cls, context): 
        return context.scene.keemap_render_static_img_list 
        
    def execute(self, context): 
        render_static_img_list = context.scene.keemap_render_static_img_list 
        scene = context.scene
        nodes = scene.node_tree.nodes
        links = scene.node_tree.links
        start_node_y_pos = 0
        for idx, render_item in enumerate(render_static_img_list):
            layer_name = f"Frame_{idx + 1:03d}"
            new_layer = bpy.context.scene.view_layers.new(name=layer_name)
            new_layer.use_pass_object_index = True
            new_collection = bpy.data.collections.new(name=layer_name)
            bpy.context.scene.collection.children.link(new_collection)

            # Make one keyframe copy and make keyframe appear in certain render layer
            context.scene.frame_current = render_item.frame_idx
            bpy.ops.wm.keemap_make_one_keyframe_copy()
            from .KeeMapBoneList import KEEMAP_LIST_OT_MakeOneKeyframeCopy
            duplicated_obj = bpy.data.objects.get(KEEMAP_LIST_OT_MakeOneKeyframeCopy.duplicated_object_name)
            new_collection.objects.link(duplicated_obj)
            for child_obj in duplicated_obj.children:
                child_obj.pass_index = idx + 1
                child_obj["timestep"] = idx + 1
                new_collection.objects.link(child_obj)
            
            render_layer = nodes.new('CompositorNodeRLayers')
            render_layer.location = (0, start_node_y_pos)
            render_layer.layer = layer_name

            id_mask = nodes.new('CompositorNodeIDMask')
            id_mask.location = (300, start_node_y_pos - 200)
            id_mask.use_antialiasing = True
            id_mask.index = idx + 1
            links.new(render_layer.outputs['IndexOB'], id_mask.inputs['ID value'])

            set_alpha = nodes.new('CompositorNodeSetAlpha')
            set_alpha.location = (600, start_node_y_pos)
            set_alpha.mode = 'REPLACE_ALPHA'
            links.new(render_layer.outputs['Image'], set_alpha.inputs['Image'])
            links.new(id_mask.outputs['Alpha'], set_alpha.inputs['Alpha'])
            
            alpha_over = nodes.new('CompositorNodeAlphaOver')
            alpha_over.location = (900, start_node_y_pos)
            alpha_over.use_premultiply = True
            links.new(set_alpha.outputs['Image'], alpha_over.inputs[2])
            
            if idx != 0:
                links.new(prev_alpha_over.outputs['Image'], alpha_over.inputs[1])
            
            prev_alpha_over = alpha_over
            start_node_y_pos -= 450
                
            
        return{'FINISHED'}

def register():
    bpy.utils.register_class(KeeMapRenderStaticImgListItem)
    bpy.types.Scene.keemap_render_static_img_list_index = bpy.props.IntProperty()
    bpy.types.Scene.keemap_render_static_img_list = bpy.props.CollectionProperty(type = KeeMapRenderStaticImgListItem) 
    bpy.utils.register_class(KeeMapRenderStaticImgSetting)
    bpy.types.Scene.keemap_render_static_img_setting = bpy.props.PointerProperty(type = KeeMapRenderStaticImgSetting) 
    bpy.utils.register_class(KEEMAP_LIST_OT_RenderStaticImg_NewItem)
    bpy.utils.register_class(KEEMAP_LIST_OT_RenderStaticImg_DeleteItem)
    bpy.utils.register_class(KEEMAP_LIST_OT_RenderStaticImg_MoveItem)
    bpy.utils.register_class(KEEMAP_LIST_OT_RenderStaticImg_ClearItem)
    bpy.utils.register_class(KEEMAP_LIST_OT_RenderStaticImg_SetupRender)


def unregister():
    bpy.utils.unregister_class(KEEMAP_LIST_OT_RenderStaticImg_NewItem)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_RenderStaticImg_DeleteItem)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_RenderStaticImg_MoveItem)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_RenderStaticImg_ClearItem)
    bpy.utils.unregister_class(KEEMAP_LIST_OT_RenderStaticImg_SetupRender)

    bpy.utils.unregister_class(KeeMapRenderStaticImgListItem)
    bpy.utils.unregister_class(KeeMapRenderStaticImgSetting)    
    del bpy.types.Scene.keemap_render_static_img_list
    del bpy.types.Scene.keemap_render_static_img_list_index
    del bpy.types.Scene.keemap_render_static_img_setting 
