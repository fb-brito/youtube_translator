import customtkinter as ctk
import tkinter as tk
import threading
import queue
from core_logic import download_transcript, transcribe_audio_local, translate_file_local, generate_tts_audio

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Youtube Transcript Translator")
        self.geometry("850x700")

        self.last_original_json_path = None
        self.last_translated_json_path = None
        self.log_queue = queue.Queue()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.control_frame.grid_columnconfigure(0, weight=1)

        self.link_entry = ctk.CTkEntry(self.control_frame, placeholder_text="Cole o link do vídeo do YouTube aqui...")
        self.link_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.transcript_button = ctk.CTkButton(self.control_frame, text="Baixar Transcrição", command=lambda: self.start_task(download_transcript))
        self.transcript_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.transcribe_audio_button = ctk.CTkButton(self.control_frame, text="Transcrição via Áudio", command=lambda: self.start_task(transcribe_audio_local))
        self.transcribe_audio_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.translate_button = ctk.CTkButton(self.control_frame, text="Traduzir para Português", command=self.start_translate_task, state="disabled")
        self.translate_button.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        self.tts_button = ctk.CTkButton(self.control_frame, text="Gerar Áudio (TTS)", command=self.start_tts_task, state="disabled")
        self.tts_button.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(self.log_frame, state="disabled", wrap="word")
        self.log_textbox.grid(row=0, column=0, sticky="nsew")

        self.process_log_queue()

    def log(self, message):
        self.log_queue.put(message)

    def process_log_queue(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", f"{message}\n")
                self.log_textbox.configure(state="disabled")
                self.log_textbox.see("end")
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_log_queue)

    def start_task(self, target_function):
        self.reset_state()
        url = self.link_entry.get()
        if not url:
            self.log("!! ERRO: Por favor, insira um link do YouTube.")
            return
        task_name_map = {"download_transcript": "Baixando Transcrição", "transcribe_audio_local": "Transcrevendo via Áudio"}
        self.log(f"--- Iniciando Tarefa: {task_name_map.get(target_function.__name__, 'Desconhecida')} ---")
        threading.Thread(target=self.run_task, args=(target_function, url)).start()

    def start_translate_task(self):
        if not self.last_original_json_path:
            self.log("!! ERRO: Nenhuma transcrição original para traduzir.")
            return
        self.log("--- Iniciando Tarefa: Traduzindo para Português ---")
        threading.Thread(target=self.run_task, args=(translate_file_local, self.last_original_json_path)).start()

    def start_tts_task(self):
        if not self.last_translated_json_path:
            self.log("!! ERRO: Nenhum arquivo traduzido para gerar áudio.")
            return
        self.log("--- Iniciando Tarefa: Gerando o Áudio (TTS) ---")
        threading.Thread(target=self.run_task, args=(generate_tts_audio, self.last_translated_json_path)).start()

    def run_task(self, target_function, *args):
        self.update_buttons_state("disabled")
        success, message, result_data = target_function(*args, log_callback=self.log)
        if success:
            self.log(f"++ SUCESSO: {message}")
            if target_function in [download_transcript, transcribe_audio_local]:
                self.last_original_json_path = result_data.get('json_path')
            elif target_function == translate_file_local:
                self.last_translated_json_path = result_data.get('json_path')
        else:
            self.log(f"!! ERRO: {message}")
        self.log("--- Tarefa Finalizada ---\n")
        self.update_buttons_state("normal")

    def reset_state(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self.last_original_json_path, self.last_translated_json_path = None, None
        self.update_buttons_state("normal")

    def update_buttons_state(self, state):
        is_running = state == "disabled"
        self.transcript_button.configure(state=state)
        self.transcribe_audio_button.configure(state=state)
        self.translate_button.configure(state="disabled" if is_running else "normal" if self.last_original_json_path else "disabled")
        self.tts_button.configure(state="disabled" if is_running else "normal" if self.last_translated_json_path else "disabled")

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()