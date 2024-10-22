import streamlit as st
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
import openai
from moviepy.editor import VideoFileClip, AudioFileClip
import io
import os

# Ensure the directory exists
output_folder = "uploads"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Google Cloud credentials
credentials_path = r'D:\AI_Audio_Replacement\google_cloud_credentials.json'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

# Azure OpenAI GPT-4o credentials
openai.api_key = '22ec84421ec24230a3638d1b51e3a7dc'
openai_endpoint = 'https://internshala.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview'

st.title("AI Audio Correction for Videos")

# Step 1: Upload video
uploaded_video = st.file_uploader("mausam_original_video.mp4", type=["mp4"])

if uploaded_video is not None:
    # Save uploaded video
    video_path = os.path.join(output_folder, uploaded_video.name)
    with open(video_path, "wb") as f:
        f.write(uploaded_video.read())

    # Step 2: Extract audio from the video file
    video = VideoFileClip(video_path)
    audio = video.audio
    audio_path = os.path.join(output_folder, "extracted_audio.wav")
    
    # Write audio as .wav file
    audio.write_audiofile(audio_path)
    st.write(f"Audio extracted and saved to: {audio_path}")

    # Step 3: Transcribe the audio using Google Speech-to-Text
    def transcribe_audio(audio_path):
        client = speech.SpeechClient()
        with io.open(audio_path, 'rb') as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="en-US"
        )

        response = client.recognize(config=config, audio=audio)
        transcript = ''.join([result.alternatives[0].transcript for result in response.results])
        return transcript

    if st.button("Transcribe Audio"):
        transcript = transcribe_audio(audio_path)
        st.write("Transcription: ", transcript)

        # Step 4: Correct transcription using GPT-4o
        def correct_transcription(transcript):
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "Correct the grammar and remove unnecessary words like umms and hmms."},
                        {"role": "user", "content": transcript}]
            )
            return response['choices'][0]['message']['content']

        corrected_transcript = correct_transcription(transcript)
        st.write("Corrected Transcription: ", corrected_transcript)

        # Step 5: Convert corrected text to speech using Google Text-to-Speech
        def text_to_speech(text, output_audio_path):
            client = texttospeech.TextToSpeechClient()
            input_text = texttospeech.SynthesisInput(text=text)

            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-JennyNeural"  # "Jenny" voice
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16
            )

            response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)

            with open(output_audio_path, "wb") as out:
                out.write(response.audio_content)

        audio_output_path = os.path.join(output_folder, "ai_generated_audio.wav")
        text_to_speech(corrected_transcript, audio_output_path)
        st.success("Generated AI Voice")

        # Step 6: Replace original video audio with AI-generated audio
        def replace_audio_in_video(video_path, new_audio_path, output_video_path):
            video_clip = VideoFileClip(video_path)
            new_audio_clip = AudioFileClip(new_audio_path)
            final_video = video_clip.set_audio(new_audio_clip)
            final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac")

        output_video_path = os.path.join(output_folder, "final_video.mp4")
        replace_audio_in_video(video_path, audio_output_path, output_video_path)
        st.success("Audio has been replaced in the video!")
        st.video(output_video_path)
else:
    st.write("Please upload a video to process.")
