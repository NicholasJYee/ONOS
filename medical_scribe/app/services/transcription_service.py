import whisper
import torch
import numpy as np
import os

class TranscriptionService:
    _model = None
    
    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = whisper.load_model("base")
            cls._model.eval()
        return cls._model
    
    @classmethod
    def transcribe_audio(cls, audio_file_path, save_to_file=False):
        try:
            with torch.no_grad():
                model = cls.get_model()
                
                audio = whisper.load_audio(audio_file_path)
                audio = whisper.pad_or_trim(audio)
                mel = whisper.log_mel_spectrogram(audio)
                
                result = model.transcribe(
                    audio_file_path,
                    fp16=False
                )
                
                transcribed_text = result["text"]
                base_name = os.path.splitext(audio_file_path)[0]
                output_file_path = f"{base_name}.txt"
                if save_to_file:
                    with open(output_file_path, 'w', encoding='utf-8') as f:
                        f.write(transcribed_text)
                
                return transcribed_text
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}") 