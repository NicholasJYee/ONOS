# Reinitialize environment (assuming fresh kernel)
import os
import re
import pandas as pd
import numpy as np
from pathlib import Path
import glob
from tqdm import tqdm
from typing import Dict, List, Tuple

# NLP metrics libraries
from rouge_score import rouge_scorer
from bert_score import score as bert_score
import nltk
from nltk.translate.bleu_score import sentence_bleu
from nltk.tokenize import word_tokenize
from sklearn.metrics import f1_score

# Ensure necessary NLTK data is downloaded and add custom path
nltk.data.path.append('/home/nickyee/nltk_data')
nltk.download('punkt', quiet=True)

# Use NLTK tokenizers
from nltk.tokenize.punkt import PunktSentenceTokenizer
from nltk.tokenize.treebank import TreebankWordTokenizer
sentence_tokenizer = PunktSentenceTokenizer()
word_tokenizer = TreebankWordTokenizer()

def custom_word_tokenize(text):
    """Custom word tokenization using NLTK's basic tokenizers."""
    sentences = sentence_tokenizer.tokenize(text)
    tokens = []
    for sentence in sentences:
        tokens.extend(word_tokenizer.tokenize(sentence))
    return tokens

def calculate_strict_f1(source_text, target_text):
    """Calculate strict F1 score between source and target texts using exact matches."""
    source_tokens = custom_word_tokenize(source_text.lower())
    target_tokens = custom_word_tokenize(target_text.lower())
    
    if not source_tokens or not target_tokens:
        return 0
    
    # Calculate true positives, precision, recall, and F1
    true_positives = sum(1 for t in source_tokens if t in target_tokens)
    precision = true_positives / len(source_tokens)
    recall = true_positives / len(target_tokens)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return f1

def calculate_lenient_f1(source_text, target_text):
    """Calculate lenient F1 score."""
    source_tokens = custom_word_tokenize(source_text.lower())
    target_tokens = custom_word_tokenize(target_text.lower())
    target_set = set(target_tokens)
    true_positives = sum(1 for token in source_tokens if token in target_set)
    precision = true_positives / len(source_tokens) if source_tokens else 0
    recall = true_positives / len(target_tokens) if target_tokens else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return f1

def calculate_sari(source, target, prediction):
    """Calculate SARI score."""
    source_tokens = set(custom_word_tokenize(source.lower()))
    target_tokens = set(custom_word_tokenize(target.lower()))
    prediction_tokens = set(custom_word_tokenize(prediction.lower()))
    # Additions
    add_target = target_tokens - source_tokens
    add_pred = prediction_tokens - source_tokens
    add_f1 = f1_score(list(add_target), list(add_pred), average='macro', zero_division=0) if add_target else 0
    # Deletions
    del_target = source_tokens - target_tokens
    del_pred = source_tokens - prediction_tokens
    del_f1 = f1_score(list(del_target), list(del_pred), average='macro', zero_division=0) if del_target else 0
    # Keep
    keep_target = target_tokens & source_tokens
    keep_pred = prediction_tokens & source_tokens
    keep_f1 = f1_score(list(keep_target), list(keep_pred), average='macro', zero_division=0) if keep_target else 0
    sari = (add_f1 + del_f1 + keep_f1) / 3
    return sari

def calculate_medcon(source_text, target_text):
    """Calculate MEDCON (Medical Concept Overlap) score."""
    medical_terms = {'patient', 'diagnosis', 'treatment', 'medication', 'symptoms', 'pain',
                     'doctor', 'nurse', 'hospital', 'clinic', 'surgery', 'disease', 'exam',
                     'blood', 'test', 'scan', 'mri', 'ct', 'xray', 'prescription', 'dose',
                     'chronic', 'acute', 'condition', 'fracture', 'sprain', 'injury'}
    source_tokens = custom_word_tokenize(source_text.lower())
    target_tokens = custom_word_tokenize(target_text.lower())
    source_med = set([t for t in source_tokens if t in medical_terms])
    target_med = set([t for t in target_tokens if t in medical_terms])
    if not source_med or not target_med:
        return 0
    overlap = len(source_med & target_med)
    precision = overlap / len(source_med)
    recall = overlap / len(target_med)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return f1

def main():
    # Define directories
    notes_dir = Path("notes/data/mock_interviews/mock_interviews")
    interviews_dir = Path("interviews/data/mock_interviews/mock_interviews")
    interview_files = list(interviews_dir.glob("*.txt"))
    
    print(f"Found {len(interview_files)} interview files")
    results = []
    rouge = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    
    for interview_file in tqdm(interview_files, desc="Processing interviews"):
        interview_name = interview_file.stem
        interview_content = interview_file.read_text(encoding='utf-8')
        note_files = list(notes_dir.glob(f"{interview_name}_*.txt"))
        
        for note_file in note_files:
            note_content = note_file.read_text(encoding='utf-8')
            model_name = '_'.join(note_file.stem.split('_')[1:]) if '_' in note_file.stem else "unknown"
            
            # Metrics calculation
            strict_f1 = calculate_strict_f1(note_content, interview_content)
            lenient_f1 = calculate_lenient_f1(note_content, interview_content)
            rouge_scores = rouge.score(note_content, interview_content)
            sari = calculate_sari(interview_content, note_content, note_content)
            precision, recall, f1 = bert_score([note_content], [interview_content], lang="en")
            medcon = calculate_medcon(note_content, interview_content)
            
            results.append({
                'interview': interview_name,
                'model': model_name,
                'note_file': note_file.name,
                'strict_f1': strict_f1,
                'lenient_f1': lenient_f1,
                'rouge1_f1': rouge_scores['rouge1'].fmeasure,
                'rouge2_f1': rouge_scores['rouge2'].fmeasure,
                'rougeL_f1': rouge_scores['rougeL'].fmeasure,
                'sari': sari,
                'bertscore_f1': f1.mean().item(),
                'medcon': medcon
            })
    
    df = pd.DataFrame(results)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    model_averages = df.groupby('model')[numeric_cols].mean().reset_index()
    model_averages['interview'] = 'AVERAGE'
    final_df = pd.concat([df, model_averages], ignore_index=True)
    Path('evaluations').mkdir(exist_ok=True, parents=True)
    final_df.to_csv('evaluations/metrics_results.csv', index=False)
    print("\nSaved metrics to 'evaluations/metrics_results.csv'")
    print(model_averages.set_index('model').round(4))

if __name__ == "__main__":
    main()
