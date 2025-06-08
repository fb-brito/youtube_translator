import yt_dlp
import os
import json
import re
from datetime import datetime
import whisper
from deep_translator import GoogleTranslator
from TTS.api import TTS

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

def clean_vtt_content(vtt_content):
    lines = vtt_content.splitlines()
    cleaned_lines = []
    for line in lines:
        if "WEBVTT" in line or "Kind:" in line or "Language:" in line or line.strip() == "" or "-->" in line:
            continue
        line = re.sub(r'<[^>]+>', '', line).strip()
        line = re.sub(r'\[.*?\]', '', line).strip()
        if line and line != cleaned_lines[-1] if cleaned_lines else True:
            cleaned_lines.append(line)
    return " ".join(cleaned_lines)

def save_transcript(base_filename, content, video_info, source_lang, log_callback):
    try:
        log_callback(f"Salvando arquivo de texto para: {base_filename}.txt")
        txt_path = os.path.join('logs', 'transcricao_original', 'txt')
        os.makedirs(txt_path, exist_ok=True)
        full_txt_path = os.path.join(txt_path, f"{base_filename}.txt")
        with open(full_txt_path, 'w', encoding='utf-8') as f:
            f.write(content)

        log_callback(f"Salvando arquivo JSON para: {base_filename}.json")
        json_path = os.path.join('logs', 'transcricao_original', 'json')
        os.makedirs(json_path, exist_ok=True)
        full_json_path = os.path.join(json_path, f"{base_filename}.json")
        json_data = {"video_id": video_info.get('id'),"video_title": video_info.get('title'),"upload_date": video_info.get('upload_date'),"source_language": source_lang,"content": content}
        with open(full_json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        return full_txt_path
    except Exception as e:
        log_error("save_transcript", "N/A", str(e), "Verificar permissões de escrita na pasta 'logs'.")
        raise

def download_transcript(video_url, log_callback):
    try:
        log_callback("1. Iniciando download da transcrição via yt-dlp...")
        ydl_opts = {'writeautomaticsub': True, 'skip_download': True, 'outtmpl': 'temp_subtitle', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            ydl.download([video_url])
        log_callback("2. Metadados e arquivo bruto baixados.")

        subtitle_file_path, downloaded_lang = next(((f"temp_subtitle.{lc}.vtt", lc.split('-')[0]) for lc in info.get('automatic_captions', {}) if os.path.exists(f"temp_subtitle.{lc}.vtt")), (None, None))
        if not subtitle_file_path: raise ValueError("Nenhuma transcrição automática encontrada.")

        log_callback(f"3. Transcrição encontrada ({downloaded_lang}). Limpando texto...")
        with open(subtitle_file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        os.remove(subtitle_file_path)

        cleaned_content = clean_vtt_content(raw_content)
        if not cleaned_content: raise ValueError("Falha ao extrair texto da transcrição.")

        log_callback("4. Preparando e salvando arquivos finais...")
        video_id, upload_date_str = info.get('id', 'desconhecido'), info.get('upload_date', '19700101')
        base_filename, video_info = f"{upload_date_str}_{video_id}_original", {'id': video_id, 'title': info.get('title', 'sem_titulo'), 'upload_date': datetime.strptime(upload_date_str, '%Y%m%d').strftime('%Y-%m-%d')}
        final_path = save_transcript(base_filename, cleaned_content, video_info, downloaded_lang, log_callback)

        return True, f"Transcrição ({downloaded_lang}) baixada!", final_path
    except Exception as e:
        log_error("download_transcript", "yt-dlp", str(e), "Verificar link do YouTube, conexão e disponibilidade de legendas automáticas.")
        return False, f"Erro: {e}", None

def transcribe_audio_local(video_url, log_callback):
    audio_file_path = None
    try:
        log_callback("1. Iniciando download do áudio via yt-dlp...")
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'temp_audio.%(ext)s', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            audio_file_path = ydl.prepare_filename(info)
        log_callback("2. Download do áudio concluído.")

        if not audio_file_path or not os.path.exists(audio_file_path): raise FileNotFoundError("Falha ao baixar ou encontrar o arquivo de áudio.")

        log_callback("3. Carregando modelo 'tiny' do Whisper...")
        model = whisper.load_model("tiny")
        log_callback("4. Transcrevendo áudio (pode levar um tempo)...")
        result = model.transcribe(audio_file_path, fp16=False)
        transcribed_text, detected_language = result["text"], result["language"]
        log_callback(f"5. Transcrição concluída. Idioma: {detected_language}.")

        if not transcribed_text: raise ValueError("Não foi possível extrair texto do áudio.")

        log_callback("6. Preparando e salvando arquivos finais...")
        video_id, upload_date_str = info.get('id', 'desconhecido'), info.get('upload_date', '19700101')
        base_filename = f"{upload_date_str}_{video_id}_original_audio"
        video_info = {'id': video_id, 'title': info.get('title', 'sem_titulo'), 'upload_date': datetime.strptime(upload_date_str, '%Y%m%d').strftime('%Y-%m-%d')}
        final_path = save_transcript(base_filename, transcribed_text, video_info, detected_language, log_callback)

        return True, f"Áudio transcrito ({detected_language}) com sucesso!", final_path
    except Exception as e:
        log_error("transcribe_audio_local", "whisper/yt-dlp", str(e), "Verificar instalação do FFmpeg e bibliotecas.")
        return False, f"Erro: {e}", None
    finally:
        if audio_file_path and os.path.exists(audio_file_path): os.remove(audio_file_path)

def translate_file_local(source_txt_path, log_callback):
    try:
        log_callback("1. Iniciando processo de tradução...")
        if not source_txt_path or not os.path.exists(source_txt_path): raise FileNotFoundError("Arquivo de origem não encontrado.")

        source_json_path = source_txt_path.replace('.txt', '.json').replace(os.path.join('transcricao_original', 'txt'), os.path.join('transcricao_original', 'json'))
        if not os.path.exists(source_json_path): raise FileNotFoundError("Arquivo JSON de metadados não encontrado.")

        log_callback("2. Lendo metadados...")
        with open(source_json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        source_lang = metadata.get("source_language", "auto")
        log_callback(f"3. Idioma de origem detectado: {source_lang}.")
        if source_lang == 'pt':
            log_callback("4. Texto já está em Português-BR. Tradução não necessária.")
            return True, "O texto já está em Português-BR.", source_txt_path

        log_callback("4. Lendo conteúdo original e traduzindo...")
        with open(source_txt_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        if not original_content: raise ValueError("Arquivo de origem está vazio.")

        translated_content = GoogleTranslator(source=source_lang, target='pt').translate(original_content)
        log_callback("5. Tradução concluída com sucesso.")

        translated_filename = os.path.basename(source_txt_path).replace("_original", "_traduzido")
        log_callback(f"6. Salvando arquivos traduzidos...")
        txt_path = os.path.join('logs', 'transcricao_traduzida', 'txt')
        os.makedirs(txt_path, exist_ok=True)
        full_txt_path = os.path.join(txt_path, translated_filename)
        with open(full_txt_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)

        metadata['content'] = translated_content
        json_path = os.path.join('logs', 'transcricao_traduzida', 'json')
        os.makedirs(json_path, exist_ok=True)
        full_json_path = os.path.join(json_path, translated_filename.replace('.txt', '.json'))
        with open(full_json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)

        return True, "Texto traduzido com sucesso!", full_json_path
    except Exception as e:
        log_error("translate_file_local", "deep-translator", str(e), "Verificar conexão com a internet e formato do texto.")
        return False, f"Erro na tradução: {e}", None

def generate_tts_audio(source_translated_json_path, log_callback):
    try:
        log_callback("1. Iniciando geração de Áudio (TTS)...")
        if not source_translated_json_path or not os.path.exists(source_translated_json_path):
            raise FileNotFoundError("Arquivo JSON traduzido não encontrado.")

        log_callback("2. Lendo conteúdo traduzido...")
        with open(source_translated_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        translated_text = data.get("content")
        if not translated_text: raise ValueError("Conteúdo traduzido está vazio.")

        log_callback("3. Carregando modelo TTS (pode levar tempo na 1ª vez)...")
        tts = TTS(model_name="tts_models/pt/cv/vits", progress_bar=False, gpu=False)
        log_callback("4. Modelo carregado. Gerando áudio MP3...")

        audio_filename = os.path.basename(source_translated_json_path).replace('.json', '.mp3')
        audio_path = os.path.join('logs', 'audio_da_traducao', 'mp3')
        os.makedirs(audio_path, exist_ok=True)
        full_audio_path = os.path.join(audio_path, audio_filename)

        tts.tts_to_file(text=translated_text, file_path=full_audio_path)
        log_callback("5. Geração de áudio concluída com sucesso.")
        return True, "Áudio gerado com sucesso!", full_audio_path
    except Exception as e:
        log_error("generate_tts_audio", "TTS (Coqui-AI)", str(e), "Verificar bibliotecas de áudio e dependências do TTS.")
        return False, f"Erro na geração de áudio: {e}", None