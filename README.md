**Youtube Transcript Translator**

**📖 Descrição do Projeto**
O Youtube Transcript Translator é uma aplicação de desktop desenvolvida em Python para automatizar o processo de obtenção, tradução e síntese de voz de transcrições de vídeos do YouTube. A ferramenta foi criada para ser um assistente robusto para criadores de conteúdo, estudantes e pesquisadores, permitindo a transformação de conteúdo de vídeo em texto e áudio de forma eficiente e offline.

A aplicação oferece múltiplas vias para a captura da transcrição, tradução inteligente para Português-BR e a geração de um arquivo de áudio .mp3 da tradução, tudo gerenciado por uma interface gráfica limpa e intuitiva que fornece feedback em tempo real de cada etapa do processo.

**Sumário Estruturado**
Visão Geral do Projeto

    1.1. Descrição do Projeto
    
    1.2. Prompt para Replicação por IA
    
    1.3. Glossário de Tecnologias

Configuração do Ambiente de Desenvolvimento

    2.1. Dica Essencial: Iniciando o Ambiente de Trabalho
    
    2.2. Preparação do Ambiente no VS Code
    
    2.3. Instalação de Dependências

Estrutura e Execução do Projeto

    3.1. Estrutura de Diretórios e Arquivos
    
    3.2. Fluxo de Operação e Teste

Base de Conhecimento do Projeto

    4.1. Diretrizes Chave do Projeto (Refinamento das Solicitações)
    
    4.2. Log de Erros Histórico (system_errors.csv)

1. Visão Geral do Projeto
1.2. Prompt para Replicação por IA
Crie uma aplicação de desktop em Python chamada "Youtube Transcript Translator" utilizando a biblioteca CustomTkinter para a interface gráfica. O ambiente de desenvolvimento deve ser gerenciado pelo Conda, utilizando Python 3.11.

Funcionalidades Principais:

Interface Gráfica: A UI deve ter um campo de entrada para o link do vídeo, botões para cada ação principal (Baixar Transcrição, Transcrição via Áudio, Traduzir, Gerar Áudio) e um painel de log para exibir o progresso das tarefas em tempo real.

Captura de Transcrição (Duas Vias):

Via 1 (Download Direto): Usar yt-dlp para baixar a melhor transcrição automática disponível de um vídeo.

Via 2 (Análise de Áudio): Usar yt-dlp para baixar o áudio e a biblioteca openai-whisper (modelo 'tiny') para transcrevê-lo localmente.

Detecção e Armazenamento: Ambas as vias de captura devem detectar e armazenar o idioma original da transcrição. Os resultados devem ser salvos em formato .txt (texto puro) e .json (com metadados: ID do vídeo, título, data, idioma, etc.) na pasta logs/transcricao_original/. Os nomes dos arquivos devem seguir o padrão [Data]_[IDvideo]_[Sufixo].ext, onde o sufixo _audio diferencia a transcrição via áudio.

Tradução Inteligente:

Ao acionar a tradução, o sistema deve verificar o idioma de origem.

Se for português, deve informar que a tradução não é necessária.

Se for outro idioma, deve usar a biblioteca deep-translator para traduzir para Português-BR.

O resultado deve ser salvo em logs/transcricao_traduzida/.

Síntese de Voz (TTS):

Após uma tradução bem-sucedida, o usuário pode gerar um arquivo de áudio .mp3 do texto traduzido.

Utilize a biblioteca TTS (da Coqui-AI) com o modelo tts_models/pt/cv/vits.

O resultado deve ser salvo em logs/audio_da_traducao/mp3/.

Sistema de Log Robusto:

Log Visual: A interface deve exibir cada etapa de cada processo.

Log Mestre de Sucessos: Um arquivo logs/master_log.csv, delimitado por ponto e vírgula, deve registrar cada operação bem-sucedida com detalhes (timestamp, ID do vídeo, título, tipo de operação, status, caminhos dos arquivos).

Log de Erros: Um arquivo logs/system_errors.csv deve registrar qualquer exceção capturada, detalhando a função, biblioteca, mensagem de erro e a solução proposta.

Execução Assíncrona: Todas as operações demoradas (downloads, IA, etc.) devem rodar em threads separadas para não travar a interface gráfica.

1.3. Glossário de Tecnologias
Componente

Tecnologia / Biblioteca

Versão / Modelo

Linguagem

Python

3.11

Gerenciador de Ambiente

Conda

-

Interface Gráfica

CustomTkinter

5.2.2

Download de Mídia

yt-dlp

2025.x

Transcrição de Áudio

openai-whisper

tiny

Tradução de Texto

deep-translator

Google Translate API

Síntese de Voz (TTS)

TTS (Coqui-AI)

tts_models/pt/cv/vits

Dependência de Áudio

FFmpeg

6.x

2. Configuração do Ambiente de Desenvolvimento
2.1. Dica Essencial: Iniciando o Ambiente de Trabalho
Este é o método correto para abrir o projeto, garantindo que o VS Code e o terminal funcionem perfeitamente com o Conda.

Abra o "Anaconda Prompt" a partir do Menu Iniciar do Windows.

Navegue para a pasta raiz do seu projeto.

cd "C:\Users\brito\OneDrive - 3hzrmc\Documentos\GitHub\youtube_translator"

Abra o VS Code a partir deste terminal.

code .

2.2. Preparação do Ambiente no VS Code
Selecione o Interpretador Python: Pressione Ctrl + Shift + P, procure por Python: Select Interpreter e escolha a opção do ambiente env (Python 3.11.x).

Verifique: O canto inferior direito do VS Code deve exibir Python 3.11.x ('env').

2.3. Instalação de Dependências
No terminal integrado do VS Code, execute os seguintes comandos:

# 1. Ative o ambiente virtual
conda activate env

# 2. Instale as bibliotecas Python
pip install customtkinter yt-dlp openai-whisper deep-translator TTS playsound

# 3. Instale o FFmpeg
conda install -c conda-forge ffmpeg -y

3. Estrutura do Projeto e Fluxo de Trabalho
3.1. Estrutura de Diretórios e Arquivos
youtube_translator/
|
├── logs/
│   ├── transcricao_original/
│   │   ├── txt/
│   │   └── json/
│   ├── transcricao_traduzida/
│   │   ├── txt/
│   │   └── json/
│   ├── audio_da_traducao/
│   │   └── mp3/
│   ├── master_log.csv
│   └── system_errors.csv
│
├── .gitignore
├── core_logic.py
└── main.py

3.2. Fluxo de Operação e Teste
Execute a Aplicação:
No terminal com o ambiente env ativo, rode:

python main.py

Fluxo Completo:

Cole um link de um vídeo.

Clique em "Baixar Transcrição" ou "Transcrição via Áudio".

Após o sucesso, clique em "Traduzir para Português".

Após o sucesso, clique em "Gerar Áudio (TTS)".

Verifique os Resultados: Todos os arquivos gerados estarão nas subpastas apropriadas dentro de logs/.

4. Base de Conhecimento do Projeto
4.1. Diretrizes Chave do Projeto (Refinamento das Solicitações)
Escolha de Tecnologia: O projeto deve usar Python 3.11 com o ambiente gerenciado por Conda, garantindo um bom equilíbrio entre modernidade e compatibilidade com bibliotecas de IA.

Autonomia do Código: Priorizar bibliotecas que rodam localmente (Whisper, TTS) sobre APIs.

Estrutura de Arquivos: Os arquivos de resultado não devem ser salvos em uma pasta por vídeo, mas sim categorizados por tipo de conteúdo (transcricao_original, transcricao_traduzida, etc.) para facilitar a análise de dados em lote.

Nomenclatura: Os nomes dos arquivos devem ser padronizados e ricos em metadados, seguindo o formato [Data]_[IDdoVideo]_[Sufixo], com sufixos claros (_audio) para diferenciar a origem.

Lógica de Tradução: O sistema não deve assumir o idioma de origem. Ele deve detectar o idioma original e, se já for português, notificar o usuário em vez de executar uma tradução desnecessária.

Feedback Visual: A interface deve ter um log em tempo real, detalhando cada etapa do processo com espaçamento claro entre as tarefas.

Logging Estruturado: Manter um master_log.csv para sucessos e um system_errors.csv para falhas, ambos formatados para fácil importação em outras ferramentas de análise.

4.2. Log de Erros Histórico (system_errors.csv)
Este arquivo serve como uma base de conhecimento dos problemas enfrentados e resolvidos durante o desenvolvimento.

Exemplo de Conteúdo:

timestamp;function_name;library_used;error_message;proposed_solution
2025-06-07 20:00:00;instalação;TTS (Coqui-AI);No matching distribution found for TTS;A biblioteca não era compatível com Python 3.12. A solução foi recriar o ambiente com Python 3.11.
2025-06-07 20:15:00;transcribe_audio_local;yt-dlp/ffmpeg;Postprocessing: audio conversion failed: Encoder not found;O yt-dlp não estava encontrando o executável do FFmpeg. A solução foi mudar a estratégia: baixar o melhor áudio disponível (qualquer formato) e passar diretamente para o Whisper, evitando a conversão para MP3.
2025-06-07 20:45:00;transcribe_audio_local;whisper;Aplicação travou por mais de 1 hora para um vídeo de 6 min;O modelo "base" do Whisper era muito pesado para a CPU. A solução foi trocar para o modelo "tiny", otimizado para performance.
2025-06-07 21:15:00;translate_file_local;transformers;Falha silenciosa na tradução (te
