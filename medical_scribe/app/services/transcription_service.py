import whisper
import torch
import numpy as np

class TranscriptionService:
    _model = None
    
    @classmethod
    def get_model(cls):
        if cls._model is None:
            # Always load model on CPU first
            cls._model = whisper.load_model("base")
            cls._model.eval()
        return cls._model
    
    @classmethod
    def transcribe_audio(cls, audio_file_path):
        try:
            with torch.no_grad():
                model = cls.get_model()
                
                # Process audio on CPU
                audio = whisper.load_audio(audio_file_path)
                audio = whisper.pad_or_trim(audio)
                mel = whisper.log_mel_spectrogram(audio)
                
                # Keep everything on CPU for stability
                result = model.transcribe(
                    audio_file_path,
                    fp16=False
                )
                
                return result["text"]
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}") 