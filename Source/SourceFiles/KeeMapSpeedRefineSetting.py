import bpy
import os

class KeeMapSpeedRefineSetting(bpy.types.PropertyGroup): 
      #"""Group of properties representing a bone mapping from OpenPose to a Rig"""       
    trajectory_obj: bpy.props.StringProperty(
        name="Trajectory object",
        description="Target trajectory object",
        default="",
        maxlen=1024,
        )
    
    text_prompt: bpy.props.StringProperty(
        name="Motion text prompt",
        description="Text prompt for generating motion",
        default="",
        maxlen=1024
    )
    
    seed: bpy.props.IntProperty(
        name="Motion text prompt",
        description="Text prompt for generating motion",
        default=123,
    )
    
    target_joint: bpy.props.EnumProperty(
        name="Position Type",
        description="Optimization target joint.",
        items=[ ('0', "Root", ""),
                ('1', "Left butt", ""),
                ('2', "Right butt", ""),
                ('3', "Spine 0", ""),
                ('4', "Left knee", ""),
                ('5', "Right knee", ""),
                ('6', "Spine 1", ""),
                ('7', "Left foot", ""),
                ('8', "Right foot", ""),
                ('9', "Spine 2", ""),
                ('10', "Left toe", ""),
                ('11', "Right toe", ""),
                ('12', "Neck", ""),
                ('13', "Left shoulder", ""),
                ('14', "Right shoulder", ""),
                ('15', "Head", ""),
                ('16', "Left arm", ""),
                ('17', "Right arm", ""),
                ('18', "Left forearm", ""),
                ('19', "Right forearm", ""),
                ('20', "Left hand", ""),
                ('21', "Right hand", ""),
               ]
        )
    
    trajectory_obj_1: bpy.props.StringProperty(
        name="Trajectory object",
        description="Target trajectory object",
        default="",
        maxlen=1024,
        )
    
    target_joint_1: bpy.props.EnumProperty(
        name="Position Type",
        description="Optimization target joint.",
        items=[ ('0', "Root", ""),
                ('1', "Left butt", ""),
                ('2', "Right butt", ""),
                ('3', "Spine 0", ""),
                ('4', "Left knee", ""),
                ('5', "Right knee", ""),
                ('6', "Spine 1", ""),
                ('7', "Left foot", ""),
                ('8', "Right foot", ""),
                ('9', "Spine 2", ""),
                ('10', "Left toe", ""),
                ('11', "Right toe", ""),
                ('12', "Neck", ""),
                ('13', "Left shoulder", ""),
                ('14', "Right shoulder", ""),
                ('15', "Head", ""),
                ('16', "Left arm", ""),
                ('17', "Right arm", ""),
                ('18', "Left forearm", ""),
                ('19', "Right forearm", ""),
                ('20', "Left hand", ""),
                ('21', "Right hand", ""),
               ]
        )

 
class KEEMAP_LIST_OT_Render_GenMotionUnderSpeedFromTextPrompt(bpy.types.Operator): 
    """Move an item in the list.""" 
    bl_idname = "keemap_t2m.gen_motion_under_speed_from_text_prompt" 
    bl_label = "Generate motion from text prompt" 

    @classmethod 
    def poll(cls, context): 
        return True
        
    def execute(self, context): 
        if context.scene.keemap_refine_speed_setting.text_prompt == "":
            self.report({'ERROR'}, "Must specify text prompt")
            return {'CANCELLED'}
        
        text_prompt = context.scene.keemap_refine_speed_setting.text_prompt
        seed = context.scene.keemap_refine_speed_setting.seed
        
        import bpy

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        
        import os
        import sys
        proj_dir = "/home/edge/code/NewWork/SpeedRefineT2MBackup/T2M-GPT_Server3/"
        sys.path.insert(0, proj_dir)
        original_workdir = os.getcwd()
        os.chdir(proj_dir)
        
        from hydra import compose, initialize
        from hydra.utils import instantiate
        with initialize(version_base="1.3", config_path="configs"):
            cfg = compose(config_name="eval_diff_framework_no_frame_masking_cycle_consistency.yaml", overrides=['vq_model_new=t2m_gpt'])
            torch.manual_seed(cfg.seed)
    
            print(cfg.runtime.choices)
                            
            sr_net = instantiate(cfg.sr_model)
            ckpt = torch.load("outputs/t2m_humanml3d_speed_synth_vel_assign_fps_speed_consistent_t2m_humanml3d_speed_vel_cycle_consistent_sr_diffusion_vel_inpainting_no_frame_masking_cycle_consistent__t2m_gpt_0.01_speed/ckpt/best_fid.pth", map_location='cpu')
            sr_net.load_state_dict(ckpt['net'], strict=True)
            sr_net.eval()
            sr_net.cuda()
            
            import numpy as np
            if len(cfg.vq_model_new) != 0:
                vq_model = instantiate(cfg.vq_model_new.wrapper)
                generator_model = instantiate(cfg.generator_model.wrapper)
            
            
        if True:
            from visualization.joints2bvh import Joint2BVHConvertor
            import numpy as np
            from os.path import join as opjoin
            from utils.motion_process import recover_from_ric
            import pandas as pd

            # Prepare models to generate motions
            if True:
                import options.option_transformer as option_trans
                import torch
                from options.get_eval_option import get_opt
                from models.evaluator_wrapper import EvaluatorModelWrapper
                dataset_opt_path = 'checkpoints/t2m/Comp_v6_KLD005/opt.txt'
                wrapper_opt = get_opt(dataset_opt_path, torch.device('cuda'))
                eval_wrapper = EvaluatorModelWrapper(wrapper_opt)

                args, _ = option_trans.get_args_parser()
                torch.manual_seed(seed)

                args.dataname = 't2m'
                args.down_t = 2
                args.depth = 3
                args.block_size = 51
                args.block_sliding_window = 5
                args.num_layers = 9
                args.embed_dim_gpt = 336
                args.nb_code = 512
                args.n_head_gpt = 8
                args.ff_rate = 2
                args.drop_out_rate = 0.1
                args.resume_pth = os.path.join(proj_dir, "output/VQVAE_part_revise_same_decoder_no_output_linear/net_best_fid.pth")
                args.vq_name = "VQVAE_part_revise_same_decoder_no_output_linear"
                args.out_dir = "output"
                args.gamma = 0.1
                args.resume_trans = os.path.join(proj_dir, "output/exp_part_gpt_bestvq_ca_word_nocausal_fix_linear_cfg_fix_sample_lr_fix_att_bias_learnable_relu_multiply_10.0_sw_5_glratio_0.25_w_336_inplace_combine_att_bias_ignore_cfg_h8_ff2_same_decoder_no_output_linear_0.55/net_best_fid.pth")                
                import clip
                import numpy as np
                import models.vqvae as vqvae
                import models.t2m_trans_traj as trans
                import warnings
                warnings.filterwarnings('ignore')

                ## load clip model and datasets
                # clip_model, clip_preprocess = clip.load("ViT-B/32", device=torch.device('cuda'), jit=False, download_root="/home/edge/")  # Must set jit=False for training
                clip_model, clip_preprocess = clip.load_with_state_dict(os.path.join(proj_dir, "CLIP-Model-sd.pth"), device=torch.device('cuda'), jit=False)
                clip.model.convert_weights(clip_model)  # Actually this line is unnecessary since clip by default already on float16
                clip_model.eval()
                for p in clip_model.parameters():
                    p.requires_grad = False

                # Initialize pre-trained models
                if True:
                    net = vqvae.SepHumanVQVAE(args, ## use args to define different parameters in different quantizers
                                        args.nb_code,
                                        args.nb_code,
                                        args.code_dim,
                                        args.output_emb_width,
                                        args.down_t,
                                        args.stride_t,
                                        args.width,
                                        args.depth,
                                        args.dilation_growth_rate)


                    trans_encoder = trans.Text2Motion_Transformer_Word_CrossAtt(num_vq=args.nb_code, 
                                                    embed_dim=args.embed_dim_gpt, 
                                                    clip_dim=args.clip_dim, 
                                                    block_size=args.block_size, 
                                                    num_layers=args.num_layers, 
                                                    n_head=args.n_head_gpt, 
                                                    drop_out_rate=args.drop_out_rate, 
                                                    fc_rate=args.ff_rate,
                                                    block_sliding_window=args.block_sliding_window)
                    
                    print ('loading checkpoint from {}'.format(args.resume_pth))
                    ckpt = torch.load(args.resume_pth, map_location='cpu')
                    net.load_state_dict(ckpt['net'], strict=True)
                    net.eval()
                    net.cuda()

                    print ('loading transformer checkpoint from {}'.format(args.resume_trans))
                    ckpt = torch.load(args.resume_trans, map_location='cpu')
                    trans_encoder.load_state_dict(ckpt['trans'], strict=True)
                    trans_encoder.eval()
                    trans_encoder.cuda()

                humanml3d_mean = torch.from_numpy(np.load(os.path.join(proj_dir, './checkpoints/t2m/VQVAEV3_CB1024_CMT_H1024_NRES3/meta/mean.npy'))).cuda()
                humanml3d_std = torch.from_numpy(np.load(os.path.join(proj_dir, './checkpoints/t2m/VQVAEV3_CB1024_CMT_H1024_NRES3/meta/std.npy'))).cuda()
            def generate_motion_tokens(text_prompts, given_tokens=None):
                for idx, text_prompt in enumerate(text_prompts):
                    text_embed = clip.tokenize(text_prompt, truncate=True).cuda()
                    # Prepare condition
                    if True:
                        word_emb = clip_model.token_embedding(text_embed).type(clip_model.dtype)
                        word_emb = word_emb + clip_model.positional_embedding.type(clip_model.dtype)
                        word_emb = word_emb.permute(1, 0, 2)  # NLD -> LND
                        word_emb = clip_model.transformer(word_emb)
                        word_emb = clip_model.ln_final(word_emb).permute(1, 0, 2).float()
                        feat_clip_text = clip_model.encode_text(text_embed).float()

                        # Calculate word_emb length using text
                        padded_text = torch.cat([text_embed, torch.zeros((1, 1), dtype=torch.int32, device=text_embed.device)], dim=1)
                        text_srt_idx = torch.arange(padded_text.shape[1], 0, -1, device=padded_text.device).unsqueeze(0)
                        text_ref_idx = (padded_text == 0) * text_srt_idx # 0 is the clip's padding
                        word_length = torch.argmax(text_ref_idx, dim=1)

                    # Generate motion from condition
                    if given_tokens:
                        index_motion_up, index_motion_down, sampled_length = trans_encoder.sample_fast_nucleus_given_token(feat_clip_text, word_emb, word_length, given_tokens[0], given_tokens[1], cond_scale=1.0, if_categorial=True)
                    else:
                        index_motion_up, index_motion_down = trans_encoder.sample_fast_nucleus_with_length(feat_clip_text, word_emb, word_length, min_length=40, cond_scale=3.0, if_categorial=True)

                    return index_motion_up, index_motion_down

            def optimize_motion_tokens(text_prompt, given_tokens, trajectory=None, trajectory_1=None, num_iterations=1000):
                text_embed = clip.tokenize(text_prompt, truncate=True).cuda()
                rot_mat = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]])
                if trajectory is not None:
                    transformed_trajectory = np.einsum('ij,bj->bi', rot_mat, trajectory)
                if trajectory_1 is not None:
                    transformed_trajectory_1 = np.einsum('ij,bj->bi', rot_mat, trajectory_1)
                # Prepare condition
                if True:
                    word_emb = clip_model.token_embedding(text_embed).type(clip_model.dtype)
                    word_emb = word_emb + clip_model.positional_embedding.type(clip_model.dtype)
                    word_emb = word_emb.permute(1, 0, 2)  # NLD -> LND
                    word_emb = clip_model.transformer(word_emb)
                    word_emb = clip_model.ln_final(word_emb).permute(1, 0, 2).float()
                    feat_clip_text = clip_model.encode_text(text_embed).float()

                    # Calculate word_emb length using text
                    padded_text = torch.cat([text_embed, torch.zeros((1, 1), dtype=torch.int32, device=text_embed.device)], dim=1)
                    text_srt_idx = torch.arange(padded_text.shape[1], 0, -1, device=padded_text.device).unsqueeze(0)
                    text_ref_idx = (padded_text == 0) * text_srt_idx # 0 is the clip's padding
                    word_length = torch.argmax(text_ref_idx, dim=1)
                    
                    index_motion_up, index_motion_down = given_tokens
                    index_motion_up = torch.cat([index_motion_up, torch.full((1, 1), trans_encoder.end_idx, device=index_motion_up.device, dtype=torch.long)], dim=1)
                    # https://stackoverflow.com/questions/56088189/pytorch-how-can-i-find-indices-of-first-nonzero-element-in-each-row-of-a-2d-ten
                    srt_idx = torch.arange(index_motion_up.shape[1], 0, -1, device=index_motion_up.device).unsqueeze(0)
                    ref_idx = (index_motion_up == trans_encoder.end_idx) * srt_idx # [[0, 0, 0, 1, 0], ...] * [[0., -0.2, -0.4, -0.6, -0.8]] -> [[0, 0, 0, -0.6, 0], ...]
                    pred_token_len = torch.argmax(ref_idx, dim=1)
                    target_joint_traj_dict = {}
                    if trajectory is not None:
                        target_joint_traj_dict[target_joint] = transformed_trajectory
                    if trajectory_1 is not None:
                        target_joint_traj_dict[target_joint_1] = transformed_trajectory_1

                    predicted_poses, target_joint_pos = trans_encoder.optimize_to_trajectory_abs_no_transf(feat_clip_text, word_emb, word_length, index_motion_up, index_motion_down, pred_token_len, target_joint_traj_dict, net, num_iterations=num_iterations, humanml3d_mean=humanml3d_mean, humanml3d_std=humanml3d_std)

                return predicted_poses, target_joint_pos

            import argparse
            parser = argparse.ArgumentParser()

            # Output arguments
            args, _ = parser.parse_known_args()

            traj = None
            if len(traj_vert_list) > 0:
                traj = np.array(traj_vert_list)
            traj_1 = None
            if len(traj_vert_list_1) > 0:
                traj_1 = np.array(traj_vert_list_1)
            
            motion_tokens = generate_motion_tokens([text_prompt])
            print(motion_tokens)
            motion_tokens_up, motion_tokens_down = motion_tokens
            # motion_tokens_up[:, 19+1] = trans_encoder.end_idx # FIXME temp for 5th optimization prompt
            motion_tokens = (motion_tokens_up, motion_tokens_down)
                
            poses, target_joint_pos = optimize_motion_tokens(text_prompt, motion_tokens, traj, traj_1, num_iterations=1000)    
            
            from utils.motion_process import recover_from_ric
            from scipy.ndimage import gaussian_filter
            def motion_feature_temporal_filter(motion, sigma=1):
                for i in range(motion.shape[1]):
                    motion[:, i] = gaussian_filter(motion[:, i],
                                                sigma=sigma,
                                                mode="nearest")
                return motion

            def smooth_humanml_part(motion, sigma=1):
                smoothed_motion = np.array(motion)
                target_joint_idx = [j for j in range(263)]
                smoothed_motion[:, target_joint_idx] = motion_feature_temporal_filter(motion[:, target_joint_idx], sigma)
                # smoothed_motion[:, :259] = motion_feature_temporal_filter(motion[:, :259], sigma)
                return smoothed_motion
            
            # TODO make tokens from text prompt
            # Synthesize word_embeddings, pos_one_hots, sent_len and compute MM-Dist
            from utils.word_vectorizer import WordVectorizer
            w_vectorizer = WordVectorizer('./glove', 'our_vab')
            
            import spacy
            nlp = spacy.load('en_core_web_sm')
            doc = nlp(text_prompt)
            word_list = []
            pos_list = []
            for token in doc:
                word = token.text
                word_list.append(word)
                pos_list.append(token.pos_)
            tokens = ['%s/%s'%(word_list[i], pos_list[i]) for i in range(len(word_list))]

            # pad with "unk"
            tokens = ['sos/OTHER'] + tokens + ['eos/OTHER']
            sent_len = len(tokens)
            tokens = tokens + ['unk/OTHER'] * (20 + 2 - sent_len)
            sent_len = torch.Tensor([len(tokens)]).to(torch.int64)
            pos_one_hots = []
            word_embeddings = []
            for token in tokens:
                word_emb, pos_oh = w_vectorizer[token]
                pos_one_hots.append(pos_oh[None, :])
                word_embeddings.append(word_emb[None, :])
            pos_one_hots = torch.from_numpy(np.concatenate(pos_one_hots, axis=0)).unsqueeze(0)
            word_embeddings = torch.from_numpy(np.concatenate(word_embeddings, axis=0)).unsqueeze(0)

            pred_motion_len = poses.shape[1] * torch.ones(1).cuda().to(torch.int64)
            print(word_embeddings.shape, pos_one_hots.shape, sent_len.shape, poses.shape, pred_motion_len.shape)
            et_pred, em_pred = eval_wrapper.get_co_embeddings(word_embeddings, pos_one_hots, sent_len, poses, pred_motion_len)
            print(f"tokens={tokens}, MM-Dist={torch.linalg.norm(et_pred - em_pred)}")
            
            poses = torch.from_numpy(smooth_humanml_part(poses[0].detach().cpu().numpy())).cuda()[None, ...]  
            motions = recover_from_ric((poses * humanml3d_std + humanml3d_mean).float(), 22)
            motions = motions.reshape(1, -1, 22, 3)
            motions = motions.detach().cpu().numpy()
            
            converter = Joint2BVHConvertor()
            # np.save("test_motion.npy", motions[0])
            # _, bvh_ik_joint = converter.convert(motions[0], filename=opjoin(args.output_dir, args.output_fn[0] + "_ik.bvh"), iterations=100)
            _, bvh_joint = converter.convert(motions[0], filename=opjoin("/tmp/blender.bvh"), iterations=100, foot_ik=False)
            
            filepath = bpy.path.abspath("/tmp/blender.bvh")
        
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

        # render_list = context.scene.keemap_render_list 
        # scene = context.scene
        # for render_item in render_list:
        #     # copy from KEEMAP_LIST_OT_ReadInFileAutoTransfer
        #     filepath = bpy.path.abspath(render_item.filepath)
            
        #     parent_name = "addon_bvh_parent"
        #     parent_obj = bpy.data.objects.get(parent_name)
        #     if parent_obj is None:
        #         parent_obj = bpy.data.objects.new(parent_name, object_data=None)
        #         bpy.context.collection.objects.link(parent_obj)

        #     for children_obj in parent_obj.children:
        #         bpy.data.armatures.remove(children_obj.data)
        #         # bpy.data.objects.remove(children_obj)

        #     bpy.ops.import_anim.bvh(filepath=filepath, rotate_mode='QUATERNION')
        #     imported_bvh_obj = bpy.context.active_object
        #     imported_bvh_obj.parent = parent_obj

        #     dg = bpy.context.evaluated_depsgraph_get()

        #     # TODO smooth out motions using source armature -> pose mode -> Graph editor -> select all bones -> === -> key -> smooth -> gaussian 
        #     bpy.ops.object.select_all(action='DESELECT')
        #     bpy.ops.object.select_by_type(type='ARMATURE')
        #     bpy.ops.object.mode_set(mode='POSE')
            
        #     KeeMap = bpy.context.scene.keemap_settings 
        #     KeeMap.source_rig_name = imported_bvh_obj.name
                    
        #     bpy.ops.wm.perform_animation_transfer()
                    
        #     # TODO Setup render setting
        #     filename = render_item.name
        #     from pathlib import Path
        #     filename = Path(filename).with_suffix(".mp4")
        #     context.scene.render.filepath = os.path.join(context.scene.keemap_render_setting.output_dir, filename)
        #     bpy.ops.render.render('INVOKE_DEFAULT', animation=True)

        sys.path.pop(0)
        os.chdir(original_workdir)
        return{'FINISHED'}

def register():
    bpy.utils.register_class(KeeMapSpeedRefineSetting)
    bpy.types.Scene.keemap_refine_speed_setting = bpy.props.PointerProperty(type = KeeMapSpeedRefineSetting) 
    bpy.utils.register_class(KEEMAP_LIST_OT_Render_GenMotionUnderSpeedFromTextPrompt)

def unregister():
    bpy.utils.unregister_class(KEEMAP_LIST_OT_Render_GenMotionUnderSpeedFromTextPrompt)
    bpy.utils.unregister_class(KeeMapSpeedRefineSetting)    
    del bpy.types.Scene.keemap_refine_speed_setting 
