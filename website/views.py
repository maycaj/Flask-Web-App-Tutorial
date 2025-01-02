from flask import Blueprint, render_template, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from .models import Note
from . import db
import io
import json
from openai import OpenAI
import os
from google.cloud import secretmanager

views = Blueprint('views', __name__)


def get_secret(secret_id): # access secret from google cloud
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/811725560577/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_openai_key():
    if os.getenv('LOCAL_DEV'): # if on local computer
        return os.getenv('OPENAI_API_KEY')
    return get_secret('OPENAI_API_KEY')

client = OpenAI(api_key=get_openai_key())

@views.route('/')
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route('/add-note', methods=['POST'])
@login_required
def add_note():
    if 'audio' not in request.files:
        flash('No audio file uploaded', category='error')
        return jsonify({'error': 'No audio file'}), 400
    
    audio_file = request.files['audio']
    
    if not audio_file:
        return jsonify({'error': 'Invalid audio file'}), 400

    try:
        audio_data = audio_file.read()
        
        temp_path = f'/tmp/audio_{current_user.id}_{Note.query.count() + 1}.wav'
        with open(temp_path, 'wb') as f:
            f.write(audio_data)
        
        with open(temp_path, 'rb') as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        
        os.remove(temp_path)
    
        # for debugging
        # transcription.text = "I’ve been feeling a burning sensation in my chest after meals, and it’s been happening almost every day. That sounds like it could be acid reflux. I’d recommend avoiding spicy or fatty foods and trying an over-the-counter antacid to see if it helps. Okay, I’ll give that a try. Should I come back if it doesn’t improve?"

        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", 
                 "content": "If this is not a patient-doctor conversation say 'Please provide a patient-doctor conversation.' If this is a transcription of a patient-doctor conversation, follow the remaining instructions: Have one set of bullet points which concisely summarizes the interaction. Have a second set of bullet points that ONLY defines terms a college graduate would not understand."},
                {"role": "user", 
                 "content": transcription.text}
            ]
        )
        analysis = completion.choices[0].message.content

        print('Analysis:\n', analysis)
        
        new_note = Note(
            filename=f'audio_{current_user.id}_{Note.query.count() + 1}.wav',
            data=audio_data,
            transcription=transcription.text,
            analysis=analysis,
            user_id=current_user.id
        )
        
        db.session.add(new_note)
        db.session.commit()
        flash('Audio note added!', category='success')
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        flash('Error saving audio note', category='error')
        return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Invalid audio file'}), 400

@views.route('/get-audio/<int:note_id>')
@login_required
def get_audio(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    return send_file(
        io.BytesIO(note.data),
        mimetype='audio/wav',
        as_attachment=False,
        download_name=note.filename
    )

@views.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    note = json.loads(request.data)
    note_id = note['noteId']
    note = Note.query.get(note_id)
    if note and note.user_id == current_user.id:
        db.session.delete(note)
        db.session.commit()
    return jsonify({})