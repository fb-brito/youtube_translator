import yt_dlp
import os
import json
import re
from datetime import datetime
import whisper
from deep_translator import GoogleTranslator
from TTS.api import TTS

# --- Sistemas de Log Estruturado ---
def log_master_record(video_info, operation, status, source_file, output_file):
    log_dir, log_file = "logs", os.path.join("logs", "master_log.csv")
    os.makedirs(log_dir, exist_ok=True)
    header = "timestamp;video_id;video_title;operation_type;source_language;status;source_file_path;output_file_path\n"
    if not os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(header)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    video_id = video_info.get('id', 'N/A')
    title = video_info.get('title', 'N/A').replace('"', "'")
    lang = video_info.get('source_language', 'N/A')

    log_entry = f"{timestamp};{video_id};\"{title}\";{operation};{lang};{status};{source_file or 'N/A'};{output_file or 'N/A'}\n"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)

def log_error(function_name, library, error, solution):
    log_dir, log_file = "logs", os.path.join("logs", "system_errors.csv")
    os.makedirs(log_dir, exist_ok=True)
    header = "timestamp;function_name;library_used;error_message;proposed_solution\n"
    if not os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(header)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_cleaned = str(error).replace('"', "'").replace('\n', ' ')
    log_entry = f"{timestamp};{function_name};{library};\"{error_cleaned}\";\"{solution}\"\n"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)

# --- Funções Utilitárias ---
def clean_vtt_content(vtt_content):
    lines = vtt_content.splitlines()
    cleaned_lines = []
    for line in lines:
        if "WEBVTT" in line or "Kind:" in line or "Language:" in line or line.strip() == "" or "-->" in line:
            continue
        line = re.sub(r'<[^>]+>', '', line).strip()
        line = re.sub(r'\[.*?\]', '', line).strip()
        if line and (not cleaned_lines or line != cleaned_lines[-1]):
            cleaned_lines.append(line)
    return " ".join(cleaned_lines)

def save_transcript(base_filename, content, video_info):
    txt_path = os.path.join('logs', 'transcricao_original', 'txt')
    os.makedirs(txt_path, exist_ok=True)
    full_txt_path = os.path.join(txt_path, f"{base_filename}.txt")
    with open(full_txt_path, 'w', encoding='utf-8') as f:
        f.write(content)

    json_path = os.path.join('logs', 'transcricao_original', 'json')
    os.makedirs(json_path, exist_ok=True)
    full_json_path = os.path.join(json_path, f"{base_filename}.json")
    with open(full_json_path, 'w', encoding='utf-8') as f:
        json.dump(video_info, f, ensure_ascii=False, indent=4)
    return full_txt_path, full_json_path

# --- Funções Principais ---
def download_transcript(video_url, log_callback):
    video_info = {}
    try:
        log_callback("1. Iniciando download da transcrição via yt-dlp...")
        ydl_opts = {'writeautomaticsub': True, 'skip_download': True, 'outtmpl': 'temp_subtitle', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            ydl.download([video_url])
        log_callback("2. Metadados e arquivo bruto baixados.")

        subtitle_file_path, downloaded_lang = next(((f"temp_subtitle.{lc}.vtt", lc.split('-')[0]) for lc in info.get('automatic_captions', {}) if os.path.exists(f"temp_subtitle.{lc}.vtt")), (None, None))
        if not subtitle_file_path: raise ValueError("Nenhuma transcrição automática encontrada.")

        with open(subtitle_file_path, 'r', encoding='utf-8') as f:
            cleaned_content = clean_vtt_content(f.read())
        os.remove(subtitle_file_path)

        log_callback(f"3. Texto limpo. Idioma: {downloaded_lang}.")
        if not cleaned_content: raise ValueError("Falha ao extrair texto da transcrição.")

        video_id, upload_date_str = info.get('id', 'desconhecido'), info.get('upload_date', '19700101')
        video_info = {'id': video_id, 'title': info.get('title', 'sem_titulo'), 'upload_date': datetime.strptime(upload_date_str, '%Y%m%d').strftime('%Y-%m-%d'), 'source_language': downloaded_lang, 'content': cleaned_content}
        base_filename = f"{upload_date_str}_{video_id}_original"

        log_callback("4. Salvando arquivos finais...")
        txt_path, json_path = save_transcript(base_filename, cleaned_content, video_info)
        log_master_record(video_info, "download_transcript", "SUCCESS", video_url, txt_path)
        return True, f"Transcrição ({downloaded_lang}) baixada!", {'txt_path': txt_path, 'json_path': json_path, 'video_info': video_info}
    except Exception as e:
        log_error("download_transcript", "yt-dlp", str(e), "Verificar link do YouTube e conexão.")
        log_master_record(video_info, "download_transcript", "FAIL", video_url, None)
        return False, f"Erro: {e}", None

def transcribe_audio_local(video_url, log_callback):
    audio_file_path, video_info = None, {}
    try:
        log_callback("1. Iniciando download do áudio...")
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'temp_audio.%(ext)s', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            audio_file_path = ydl.prepare_filename(info)
        log_callback("2. Download concluído.")

        if not audio_file_path or not os.path.exists(audio_file_path): raise FileNotFoundError("Falha ao baixar áudio.")

        log_callback("3. Carregando modelo 'tiny' do Whisper...")
        model = whisper.load_model("tiny")
        log_callback("4. Transcrevendo áudio...")
        result = model.transcribe(audio_file_path, fp16=False)
        transcribed_text, detected_language = result["text"], result["language"]
        log_callback(f"5. Transcrição concluída. Idioma: {detected_language}.")

        if not transcribed_text: raise ValueError("Não foi possível extrair texto.")

        log_callback("6. Salvando arquivos finais...")
        video_id, upload_date_str = info.get('id', 'desconhecido'), info.get('upload_date', '19700101')
        video_info = {'id': video_id, 'title': info.get('title', 'sem_titulo'), 'upload_date': datetime.strptime(upload_date_str, '%Y%m%d').strftime('%Y-%m-%d'), 'source_language': detected_language, 'content': transcribed_text}
        base_filename = f"{upload_date_str}_{video_id}_original_audio"
        txt_path, json_path = save_transcript(base_filename, transcribed_text, video_info)

        log_master_record(video_info, "transcribe_audio_local", "SUCCESS", video_url, txt_path)
        return True, f"Áudio transcrito ({detected_language}) com sucesso!", {'txt_path': txt_path, 'json_path': json_path, 'video_info': video_info}
    except Exception as e:
        log_error("transcribe_audio_local", "whisper/yt-dlp", str(e), "Verificar FFmpeg e bibliotecas.")
        log_master_record(video_info, "transcribe_audio_local", "FAIL", video_url, None)
        return False, f"Erro: {e}", None
    finally:
        if audio_file_path and os.path.exists(audio_file_path): os.remove(audio_file_path)

def translate_file_local(source_json_path, log_callback):
    video_info = {}
    try:
        log_callback("1. Iniciando processo de tradução...")
        if not source_json_path or not os.path.exists(source_json_path): raise FileNotFoundError("Arquivo JSON de origem não encontrado.")

        log_callback("2. Lendo metadados...")
        with open(source_json_path, 'r', encoding='utf-8') as f:
            video_info = json.load(f)

        source_lang, original_content = video_info.get("source_language", "auto"), video_info.get("content")
        log_callback(f"3. Idioma de origem: {source_lang}.")
        if source_lang == 'pt':
            log_callback("4. Texto já está em PT-BR. Tradução não necessária.")
            return True, "Texto já em Português.", {'json_path': source_json_path, 'video_info': video_info}

        if not original_content: raise ValueError("Arquivo de origem está vazio.")
        log_callback("4. Traduzindo conteúdo...")
        translated_content = GoogleTranslator(source=source_lang, target='pt').translate(original_content)
        log_callback("5. Tradução concluída.")

        translated_filename = os.path.basename(source_json_path).replace("_original", "_traduzido")
        log_callback("6. Salvando arquivos traduzidos...")
        txt_path = os.path.join('logs', 'transcricao_traduzida', 'txt', translated_filename.replace('.json', '.txt'))
        os.makedirs(os.path.dirname(txt_path), exist_ok=True)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)

        video_info['content'] = translated_content
        json_path = os.path.join('logs', 'transcricao_traduzida', 'json', translated_filename)
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(video_info, f, ensure_ascii=False, indent=4)

        log_master_record(video_info, "translate_file_local", "SUCCESS", source_json_path, json_path)
        return True, "Texto traduzido com sucesso!", {'json_path': json_path, 'video_info': video_info}
    except Exception as e:
        log_error("translate_file_local", "deep-translator", str(e), "Verificar conexão com a internet.")
        log_master_record(video_info, "translate_file_local", "FAIL", source_json_path, None)
        return False, f"Erro na tradução: {e}", None

def generate_tts_audio(source_translated_json_path, log_callback):
    video_info = {}
    try:
        log_callback("1. Iniciando geração de Áudio (TTS)...")
        if not source_translated_json_path or not os.path.exists(source_translated_json_path): raise FileNotFoundError("Arquivo JSON traduzido não encontrado.")

        log_callback("2. Lendo conteúdo traduzido...")
        with open(source_translated_json_path, 'r', encoding='utf-8') as f:
            video_info = json.load(f)
        translated_text = video_info.get("content")
        if not translated_text: raise ValueError("Conteúdo traduzido está vazio.")

        log_callback("3. Carregando modelo TTS (pode levar tempo)...")
        tts = TTS(model_name="tts_models/pt/cv/vits", progress_bar=False, gpu=False)
        log_callback("4. Gerando áudio MP3...")

        audio_filename = os.path.basename(source_translated_json_path).replace('.json', '.mp3')
        audio_path = os.path.join('logs', 'audio_da_traducao', 'mp3')
        os.makedirs(audio_path, exist_ok=True)
        full_audio_path = os.path.join(audio_path, audio_filename)

        tts.tts_to_file(text=translated_text, file_path=full_audio_path)
        log_callback("5. Geração de áudio concluída.")
        log_master_record(video_info, "generate_tts_audio", "SUCCESS", source_translated_json_path, full_audio_path)
        return True, "Áudio gerado com sucesso!", {'audio_path': full_audio_path, 'video_info': video_info}
    except Exception as e:
        log_error("generate_tts_audio", "TTS (Coqui-AI)", str(e), "Verificar dependências do TTS.")
        log_master_record(video_info, "generate_tts_audio", "FAIL", source_translated_json_path, None)
        return False, f"Erro na geração de áudio: {e}", None