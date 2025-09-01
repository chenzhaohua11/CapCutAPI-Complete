import requests
from flask import Flask, request, jsonify, Response
from datetime import datetime
import pyJianYingDraft as draft
from pyJianYingDraft.metadata.animation_meta import Intro_type, Outro_type, Group_animation_type
from pyJianYingDraft.metadata.capcut_animation_meta import CapCut_Intro_type, CapCut_Outro_type, CapCut_Group_animation_type
from pyJianYingDraft.metadata.transition_meta import Transition_type
from pyJianYingDraft.metadata.capcut_transition_meta import CapCut_Transition_type
from pyJianYingDraft.metadata.mask_meta import Mask_type
from pyJianYingDraft.metadata.capcut_mask_meta import CapCut_Mask_type
from pyJianYingDraft.metadata.audio_effect_meta import Tone_effect_type, Audio_scene_effect_type, Speech_to_song_type
from pyJianYingDraft.metadata.capcut_audio_effect_meta import CapCut_Voice_filters_effect_type, CapCut_Voice_characters_effect_type, CapCut_Speech_to_song_effect_type
from pyJianYingDraft.metadata.font_meta import Font_type
from pyJianYingDraft.metadata.animation_meta import Text_intro, Text_outro, Text_loop_anim
from pyJianYingDraft.metadata.capcut_text_animation_meta import CapCut_Text_intro, CapCut_Text_outro, CapCut_Text_loop_anim
from pyJianYingDraft.metadata.video_effect_meta import Video_scene_effect_type, Video_character_effect_type
from pyJianYingDraft.metadata.capcut_effect_meta import CapCut_Video_scene_effect_type, CapCut_Video_character_effect_type
import random
import uuid
import json
import codecs
from add_audio_track import add_audio_track
from add_video_track import add_video_track
from add_text_impl import add_text_impl
from add_subtitle_impl import add_subtitle_impl
from add_image_impl import add_image_impl
from add_video_keyframe_impl import add_video_keyframe_impl
from save_draft_impl import save_draft_impl, query_task_status, query_script_impl
from add_effect_impl import add_effect_impl
from add_sticker_impl import add_sticker_impl
from create_draft import create_draft
from util import generate_draft_url as utilgenerate_draft_url, hex_to_rgb
from pyJianYingDraft.text_segment import TextStyleRange, Text_style, Text_border

from settings.local import IS_CAPCUT_ENV, DRAFT_DOMAIN, PREVIEW_ROUTER, PORT

app = Flask(__name__)
 
@app.route('/add_video', methods=['POST'])
def add_video():
    data = request.get_json()
    # Get required parameters
    draft_folder = data.get('draft_folder')
    video_url = data.get('video_url')
    start = data.get('start', 0)
    end = data.get('end', 0)
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    draft_id = data.get('draft_id')
    transform_y = data.get('transform_y', 0)
    scale_x = data.get('scale_x', 1)
    scale_y = data.get('scale_y', 1)
    transform_x = data.get('transform_x', 0)
    speed = data.get('speed', 1.0)  # New speed parameter
    target_start = data.get('target_start', 0)  # New target start time parameter
    track_name = data.get('track_name', "video_main")  # New track name parameter
    relative_index = data.get('relative_index', 0)  # New relative index parameter
    duration = data.get('duration')  # New duration parameter
    transition = data.get('transition')  # New transition type parameter
    transition_duration = data.get('transition_duration', 0.5)  # New transition duration parameter, default 0.5 seconds
    volume = data.get('volume', 1.0)  # New volume parameter, default 1.0 
    
    # Get mask related parameters
    mask_type = data.get('mask_type')  # Mask type
    mask_center_x = data.get('mask_center_x', 0.5)  # Mask center X coordinate
    mask_center_y = data.get('mask_center_y', 0.5)  # Mask center Y coordinate
    mask_size = data.get('mask_size', 1.0)  # Mask size, relative to screen height
    mask_rotation = data.get('mask_rotation', 0.0)  # Mask rotation angle
    mask_feather = data.get('mask_feather', 0.0)  # Mask feather degree
    mask_invert = data.get('mask_invert', False)  # Whether to invert mask
    mask_rect_width = data.get('mask_rect_width')  # Rectangle mask width
    mask_round_corner = data.get('mask_round_corner')  # Rectangle mask rounded corner

    background_blur = data.get('background_blur')  # Background blur level, optional values: 1 (light), 2 (medium), 3 (strong), 4 (maximum), default None (no background blur)

    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not video_url:
        error_message = "Hi, the required parameters 'video_url' are missing."
        result["error"] = error_message
        return jsonify(result)

    try:
        draft_result = add_video_track(
            draft_folder=draft_folder,
            video_url=video_url,
            width=width,
            height=height,
            start=start,
            end=end,
            target_start=target_start,
            draft_id=draft_id,
            transform_y=transform_y,
            scale_x=scale_x,
            scale_y=scale_y,
            transform_x=transform_x,
            speed=speed,
            track_name=track_name,
            relative_index=relative_index,
            duration=duration,
            transition=transition,  # Pass transition type parameter
            transition_duration=transition_duration,  # Pass transition duration parameter
            volume=volume,  # Pass volume parameter
            # Pass mask related parameters
            mask_type=mask_type,
            mask_center_x=mask_center_x,
            mask_center_y=mask_center_y,
            mask_size=mask_size,
            mask_rotation=mask_rotation,
            mask_feather=mask_feather,
            mask_invert=mask_invert,
            mask_rect_width=mask_rect_width,
            mask_round_corner=mask_round_corner,
            background_blur=background_blur
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing video: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/add_audio', methods=['POST'])
def add_audio():
    data = request.get_json()
    
    # Get required parameters
    draft_folder = data.get('draft_folder')
    audio_url = data.get('audio_url')
    start = data.get('start', 0)
    end = data.get('end', None)
    draft_id = data.get('draft_id')
    volume = data.get('volume', 1.0)  # Default volume 1.0
    target_start = data.get('target_start', 0)  # New target start time parameter
    speed = data.get('speed', 1.0)  # New speed parameter
    track_name = data.get('track_name', 'audio_main')  # New track name parameter
    duration = data.get('duration', None)  # New duration parameter
    # Get audio effect parameters separately
    effect_type = data.get('effect_type', None)  # Audio effect type name
    effect_params = data.get('effect_params', None)  # Audio effect parameter list
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    
    # # If there are audio effect parameters, combine them into sound_effects format
    sound_effects = None
    if effect_type is not None:
        sound_effects = [(effect_type, effect_params)]

    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not audio_url:
        error_message = "Hi, the required parameters 'audio_url' are missing."
        result["error"] = error_message
        return jsonify(result)

    try:
        # Call the modified add_audio_track method
        draft_result = add_audio_track(
            draft_folder=draft_folder,
            audio_url=audio_url,
            start=start,
            end=end,
            target_start=target_start,
            draft_id=draft_id,
            volume=volume,
            track_name=track_name,
            speed=speed,
            sound_effects=sound_effects,  # Add audio effect parameters
            width=width,
            height=height,
            duration=duration  # Add duration parameter
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing audio: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/create_draft', methods=['POST'])
def create_draft_service():
    data = request.get_json()
    
    # Get parameters
    draft_name = data.get('draft_name', 'My Draft')
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    fps = data.get('fps', 30)
    draft_id = data.get('draft_id')
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    try:
        draft_result = create_draft(
            draft_name=draft_name,
            width=width,
            height=height,
            fps=fps,
            draft_id=draft_id
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while creating draft: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/add_text', methods=['POST'])
def add_text():
    data = request.get_json()
    
    # Get required parameters
    draft_folder = data.get('draft_folder')
    text = data.get('text')
    font_size = data.get('font_size', 50)
    color = data.get('color', '#FFFFFF')
    start = data.get('start', 0)
    duration = data.get('duration', 5)
    x = data.get('x', 0.5)
    y = data.get('y', 0.5)
    draft_id = data.get('draft_id')
    track_name = data.get('track_name', 'text_main')
    font_name = data.get('font_name', '站酷庆科黄油体')
    font_id = data.get('font_id', '0')
    font_path = data.get('font_path', '')
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    bold = data.get('bold', False)
    italic = data.get('italic', False)
    underline = data.get('underline', False)
    delete_line = data.get('delete_line', False)
    alignment = data.get('alignment', 1)  # 0: left, 1: center, 2: right
    
    # Text animation parameters
    text_intro = data.get('text_intro')  # Text intro animation type
    text_outro = data.get('text_outro')  # Text outro animation type
    text_loop_anim = data.get('text_loop_anim')  # Text loop animation type
    intro_duration = data.get('intro_duration', 0.5)  # Intro animation duration
    outro_duration = data.get('outro_duration', 0.5)  # Outro animation duration
    loop_duration = data.get('loop_duration', 2.0)  # Loop animation duration
    
    # Text border parameters
    border_color = data.get('border_color', '#000000')  # Border color
    border_width = data.get('border_width', 0)  # Border width
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not text:
        error_message = "Hi, the required parameters 'text' are missing."
        result["error"] = error_message
        return jsonify(result)

    try:
        draft_result = add_text_impl(
            draft_folder=draft_folder,
            text=text,
            font_size=font_size,
            color=color,
            start=start,
            duration=duration,
            x=x,
            y=y,
            draft_id=draft_id,
            track_name=track_name,
            font_name=font_name,
            font_id=font_id,
            font_path=font_path,
            width=width,
            height=height,
            bold=bold,
            italic=italic,
            underline=underline,
            delete_line=delete_line,
            alignment=alignment,
            # Pass text animation parameters
            text_intro=text_intro,
            text_outro=text_outro,
            text_loop_anim=text_loop_anim,
            intro_duration=intro_duration,
            outro_duration=outro_duration,
            loop_duration=loop_duration,
            # Pass text border parameters
            border_color=border_color,
            border_width=border_width
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing text: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/add_subtitle', methods=['POST'])
def add_subtitle():
    data = request.get_json()
    
    # Get required parameters
    draft_folder = data.get('draft_folder')
    text = data.get('text')
    font_size = data.get('font_size', 50)
    color = data.get('color', '#FFFFFF')
    start = data.get('start', 0)
    duration = data.get('duration', 5)
    x = data.get('x', 0.5)
    y = data.get('y', 0.85)  # Default subtitle position is lower
    draft_id = data.get('draft_id')
    track_name = data.get('track_name', 'text_main')
    font_name = data.get('font_name', '站酷庆科黄油体')
    font_id = data.get('font_id', '0')
    font_path = data.get('font_path', '')
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    bold = data.get('bold', False)
    italic = data.get('italic', False)
    underline = data.get('underline', False)
    delete_line = data.get('delete_line', False)
    alignment = data.get('alignment', 1)  # 0: left, 1: center, 2: right
    
    # Subtitle-specific parameters
    max_width = data.get('max_width', 0.8)  # Maximum width ratio
    line_spacing = data.get('line_spacing', 1.2)  # Line spacing
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not text:
        error_message = "Hi, the required parameters 'text' are missing."
        result["error"] = error_message
        return jsonify(result)

    try:
        draft_result = add_subtitle_impl(
            draft_folder=draft_folder,
            text=text,
            font_size=font_size,
            color=color,
            start=start,
            duration=duration,
            x=x,
            y=y,
            draft_id=draft_id,
            track_name=track_name,
            font_name=font_name,
            font_id=font_id,
            font_path=font_path,
            width=width,
            height=height,
            bold=bold,
            italic=italic,
            underline=underline,
            delete_line=delete_line,
            alignment=alignment,
            max_width=max_width,
            line_spacing=line_spacing
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing subtitle: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/add_image', methods=['POST'])
def add_image():
    data = request.get_json()
    
    # Get required parameters
    draft_folder = data.get('draft_folder')
    image_url = data.get('image_url')
    start = data.get('start', 0)
    duration = data.get('duration', 5)
    x = data.get('x', 0.5)
    y = data.get('y', 0.5)
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    scale_x = data.get('scale_x', 1)
    scale_y = data.get('scale_y', 1)
    rotation = data.get('rotation', 0)
    draft_id = data.get('draft_id')
    track_name = data.get('track_name', 'image_main')
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not image_url:
        error_message = "Hi, the required parameters 'image_url' are missing."
        result["error"] = error_message
        return jsonify(result)

    try:
        draft_result = add_image_impl(
            draft_folder=draft_folder,
            image_url=image_url,
            start=start,
            duration=duration,
            x=x,
            y=y,
            width=width,
            height=height,
            scale_x=scale_x,
            scale_y=scale_y,
            rotation=rotation,
            draft_id=draft_id,
            track_name=track_name
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing image: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/add_effect', methods=['POST'])
def add_effect():
    data = request.get_json()
    
    # Get required parameters
    draft_folder = data.get('draft_folder')
    effect_type = data.get('effect_type')
    effect_name = data.get('effect_name')
    start = data.get('start', 0)
    duration = data.get('duration', 5)
    intensity = data.get('intensity', 1.0)
    draft_id = data.get('draft_id')
    track_name = data.get('track_name', 'effect_main')
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not effect_type or not effect_name:
        error_message = "Hi, the required parameters 'effect_type' and 'effect_name' are missing."
        result["error"] = error_message
        return jsonify(result)

    try:
        draft_result = add_effect_impl(
            draft_folder=draft_folder,
            effect_type=effect_type,
            effect_name=effect_name,
            start=start,
            duration=duration,
            intensity=intensity,
            draft_id=draft_id,
            track_name=track_name,
            width=width,
            height=height
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing effect: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/add_sticker', methods=['POST'])
def add_sticker():
    data = request.get_json()
    
    # Get required parameters
    draft_folder = data.get('draft_folder')
    sticker_url = data.get('sticker_url')
    start = data.get('start', 0)
    duration = data.get('duration', 5)
    x = data.get('x', 0.5)
    y = data.get('y', 0.5)
    width = data.get('width', 1080)
    height = data.get('height', 1920)
    scale_x = data.get('scale_x', 1)
    scale_y = data.get('scale_y', 1)
    rotation = data.get('rotation', 0)
    draft_id = data.get('draft_id')
    track_name = data.get('track_name', 'sticker_main')
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    # Validate required parameters
    if not sticker_url:
        error_message = "Hi, the required parameters 'sticker_url' are missing."
        result["error"] = error_message
        return jsonify(result)

    try:
        draft_result = add_sticker_impl(
            draft_folder=draft_folder,
            sticker_url=sticker_url,
            start=start,
            duration=duration,
            x=x,
            y=y,
            width=width,
            height=height,
            scale_x=scale_x,
            scale_y=scale_y,
            rotation=rotation,
            draft_id=draft_id,
            track_name=track_name
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing sticker: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/save_draft', methods=['POST'])
def save_draft():
    data = request.get_json()
    
    # Get parameters
    draft_folder = data.get('draft_folder')
    draft_id = data.get('draft_id')
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    try:
        draft_result = save_draft_impl(
            draft_folder=draft_folder,
            draft_id=draft_id
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while saving draft: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/query_task', methods=['POST'])
def query_task():
    data = request.get_json()
    
    # Get parameters
    draft_id = data.get('draft_id')
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    try:
        draft_result = query_task_status(
            draft_id=draft_id
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while querying task: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/query_script', methods=['POST'])
def query_script():
    data = request.get_json()
    
    # Get parameters
    draft_id = data.get('draft_id')
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    try:
        draft_result = query_script_impl(
            draft_id=draft_id
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while querying script: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/add_video_keyframe', methods=['POST'])
def add_video_keyframe():
    data = request.get_json()
    
    # Get parameters
    draft_folder = data.get('draft_folder')
    start = data.get('start', 0)
    duration = data.get('duration', 5)
    x = data.get('x', 0)
    y = data.get('y', 0)
    scale_x = data.get('scale_x', 1)
    scale_y = data.get('scale_y', 1)
    rotation = data.get('rotation', 0)
    opacity = data.get('opacity', 1)
    draft_id = data.get('draft_id')
    track_name = data.get('track_name', 'video_main')
    keyframe_time = data.get('keyframe_time', 0)
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    try:
        draft_result = add_video_keyframe_impl(
            draft_folder=draft_folder,
            start=start,
            duration=duration,
            x=x,
            y=y,
            scale_x=scale_x,
            scale_y=scale_y,
            rotation=rotation,
            opacity=opacity,
            draft_id=draft_id,
            track_name=track_name,
            keyframe_time=keyframe_time
        )
        
        result["success"] = True
        result["output"] = draft_result
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while processing video keyframe: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/generate_draft_url', methods=['POST'])
def generate_draft_url():
    data = request.get_json()
    
    # Get parameters
    draft_id = data.get('draft_id')
    
    result = {
        "success": False,
        "output": "",
        "error": ""
    }

    try:
        draft_url = utilgenerate_draft_url(draft_id)
        
        result["success"] = True
        result["output"] = {"draft_url": draft_url}
        return jsonify(result)

    except Exception as e:
        error_message = f"Error occurred while generating draft URL: {str(e)}."
        result["error"] = error_message
        return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)