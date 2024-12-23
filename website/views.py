from flask import Blueprint, render_template, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from .models import Note
from . import db
import io
import json
from openai import OpenAI
import os

views = Blueprint('views', __name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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

        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", 
                 "content": "This is a transcription of a patient-doctor conversation. Have one paragraph which concisely summarizes the interaction. Have a second paragraph that ONLY defines terms a college graduate would not understand. Say 'Thanks for using MedNote' at the end"},
                {"role": "user", 
                 "content": transcription.text}
            ]
        )
        analysis = completion.choices[0].message.content
        
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