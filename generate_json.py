import os
import json
import re
import unicodedata

# Configurações
BASE_URL = "https://github.com/Teste696969/music-bunker/raw/refs/heads/main"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))  # Pasta onde o script está
MUSIC_DIR = os.path.join(ROOT_DIR, "musics")  # Pasta de músicas
OUTPUT_DIR = ROOT_DIR  # Onde salvar os JSONs

# Extensões de áudio suportadas
AUDIO_EXTS = {'.mp3', '.flac', '.wav', '.ogg', '.aac', '.m4a', '.wma', '.opus'}

def carregar_processados():
    """Carrega todos os arquivos já processados dos JSONs anteriores"""
    processados = set()
    ids_existentes = []
    data_file = os.path.join(OUTPUT_DIR, "data.json")
    if os.path.isfile(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "url" in item:
                            processados.add(item["url"])
                        if isinstance(item, dict) and "id" in item and isinstance(item["id"], int):
                            ids_existentes.append(item["id"])
        except json.JSONDecodeError:
            # arquivo corrupto: trata como inexistente
            pass
    max_id = max(ids_existentes) if ids_existentes else 0
    return processados, max_id

def gerar_titulo_pelo_arquivo(nome_arquivo: str) -> str:
    """
    Gera um título a partir do nome do arquivo, normalizando para:
    {Primeira letra maiúscula}{restante minúsculas}.
    Remove caracteres especiais e padrões comuns.
    """
    base, _ = os.path.splitext(nome_arquivo)
    
    # Agora converte separadores em espaços
    base = base.replace("_", " ").replace("-", " ").strip()
    
    # Normaliza espaços múltiplos
    base = " ".join(base.split())
    
    # Remove caracteres especiais, mantendo apenas letras, números e espaços
    base = re.sub(r'[^a-zA-Z0-9\s]', '', base)
    
    # Normaliza espaços múltiplos novamente após remover caracteres especiais
    base = " ".join(base.split())
    if not base:
        return ""
    lower_all = base.lower()
    return lower_all[0].upper() + lower_all[1:]

def sanitizar_nome_arquivo(nome_arquivo: str) -> str:
    """
    Normaliza o nome do arquivo removendo acentos, trocando espaços por underscores
    e eliminando caracteres não permitidos. Mantém a extensão original.
    """
    base, ext = os.path.splitext(nome_arquivo)
    # Remove acentos
    base_normalizada = unicodedata.normalize("NFKD", base)
    base_sem_acentos = "".join(
        c for c in base_normalizada if not unicodedata.combining(c)
    )
    # Substitui qualquer caractere que não seja alfanumérico, hífen ou underscore por underscore
    base_limpa = re.sub(r"[^A-Za-z0-9_-]+", "_", base_sem_acentos)
    base_limpa = re.sub(r"_+", "_", base_limpa).strip("_")
    if not base_limpa:
        base_limpa = "arquivo"
    return f"{base_limpa}{ext}"

def gerar_json():
    processados, max_id_existente = carregar_processados()
    novos = []

    # Verifica se o diretório de músicas existe
    if not os.path.isdir(MUSIC_DIR):
        print(f"❌ Diretório de músicas não encontrado: {MUSIC_DIR}")
        return

    # Procura por arquivos de áudio na pasta musics/
    for arquivo in os.listdir(MUSIC_DIR):
        arquivo_path = os.path.join(MUSIC_DIR, arquivo)
        
        # Pula diretórios
        if not os.path.isfile(arquivo_path):
            continue
        
        _, ext = os.path.splitext(arquivo)
        if ext.lower() not in AUDIO_EXTS:
            continue

        # Sanitiza o nome do arquivo
        nome_sanitizado = sanitizar_nome_arquivo(arquivo)
        if nome_sanitizado != arquivo:
            destino_path = os.path.join(MUSIC_DIR, nome_sanitizado)
            if os.path.exists(destino_path):
                base, ext = os.path.splitext(nome_sanitizado)
                contador = 1
                while True:
                    candidato = f"{base}_{contador}{ext}"
                    destino_path = os.path.join(MUSIC_DIR, candidato)
                    if not os.path.exists(destino_path):
                        nome_sanitizado = candidato
                        break
                    contador += 1
            os.rename(arquivo_path, destino_path)
            arquivo_path = destino_path
            arquivo = nome_sanitizado

        url = f"{BASE_URL}/musics/{arquivo}"
        if url not in processados:
            novos.append({
                "url": url,
                "title": gerar_titulo_pelo_arquivo(arquivo),
                "arquivo": arquivo,
            })

    # Atribui IDs sequenciais começando após o maior ID existente
    if novos:
        proximo_id = max_id_existente + 1
        previous_id = max_id_existente if max_id_existente > 0 else None
        for item in novos:
            item_id = proximo_id
            item["id"] = item_id
            item["previous_id"] = previous_id
            previous_id = item_id
            proximo_id += 1

        # Load existing data.json (or start with an empty list) and append novos
        data_file = os.path.join(OUTPUT_DIR, "data.json")
        existing = []
        if os.path.isfile(data_file):
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        existing = loaded
            except (json.JSONDecodeError, FileNotFoundError):
                existing = []

        # Adiciona novos no começo da lista para que fiquem no topo do JSON
        novos.extend(existing)

        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(novos, f, indent=2, ensure_ascii=False)
        print(f"✅ data.json atualizado: {data_file}")
        print(f"🔹 Novas músicas adicionadas: {len(novos)}")
        print(f"🔹 Total de músicas em data.json: {len(existing)}")
    else:
        print("ℹ️ Nenhuma música nova encontrada.")

if __name__ == "__main__":
    gerar_json()