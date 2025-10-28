import os
import json
import math
import google.generativeai as genai
from dotenv import load_dotenv

# ===============================
# CONFIGURAÇÃO DO GEMINI
# ===============================
def configure_llm():
    """Configura e retorna o modelo generativo da Google."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "A variável de ambiente GOOGLE_API_KEY não foi encontrada. "
            "Crie um arquivo .env e adicione sua chave."
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')


# ===============================
# BUSCA DE FRUTAS E ESPÉCIES
# ===============================
def carregar_especies(arquivo_especies):
    """Carrega o arquivo JSON de espécies."""
    if not os.path.exists(arquivo_especies):
        raise FileNotFoundError(f"Arquivo '{arquivo_especies}' não encontrado.")
    with open(arquivo_especies, "r", encoding="utf-8") as f:
        return json.load(f)


def extrair_frutas_do_json(especies):
    """Retorna uma lista com o primeiro nome vernacular de cada espécie."""
    frutas = []
    for especie in especies:
        vernaculars = especie.get("vernacularNames", [])
        if vernaculars:
            primeiro_nome = vernaculars[0].get("name", "").strip().lower()
            if primeiro_nome:
                frutas.append(primeiro_nome)
    return frutas


def buscar_especie_por_fruta(nome_fruta, especies):
    """Retorna a espécie correspondente a uma fruta."""
    for especie in especies:
        for vernacular in especie.get("vernacularNames", []):
            if vernacular.get("name", "").lower() == nome_fruta.lower():
                return especie
    return None


# ===============================
# CONSULTA AO GEMINI
# ===============================
def pesquisar_informacoes(model, nome_cientifico, nome_fruta):
    """Envia prompt ao Gemini para buscar informações sobre a fruta."""
    prompt = f"""
    Pesquise na Wikipédia sobre a espécie "{nome_cientifico}" (fruta conhecida como "{nome_fruta}").
    Extraia e apresente as seguintes informações em formato JSON bem estruturado:
    {{
        "fruta": "{nome_fruta}",
        "nome_cientifico": "{nome_cientifico}",
        "etimologia": "...",
        "origem_do_fruto": "...",
        "manejo_e_cultivo": "..."
    }}
    Certifique-se de retornar SOMENTE o JSON, sem texto fora do objeto nem blocos ```json.
    """

    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned)
    except Exception as e:
        print(f"Erro ao pesquisar {nome_fruta}: {e}")
        return None


# ===============================
# SALVAR RESULTADOS EM LOTES
# ===============================
def salvar_resultado_json(grupo_resultados, indice_grupo):
    """Cria um arquivo JSON para cada grupo de 3 frutas."""
    nome_arquivo = f"pesquisa_grupo_{indice_grupo}.json"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(grupo_resultados, f, ensure_ascii=False, indent=4)
    print(f"3 registros salvos em '{nome_arquivo}'.")


# ===============================
# EXECUÇÃO PRINCIPAL
# ===============================
def main():
    load_dotenv()
    model = configure_llm()

    arquivo_especies = "especies.json"
    especies = carregar_especies(arquivo_especies)
    frutas = extrair_frutas_do_json(especies)

    tamanho_grupo = 3
    total_grupos = math.ceil(len(frutas) / tamanho_grupo)

    for i in range(total_grupos):
        inicio = i * tamanho_grupo
        fim = inicio + tamanho_grupo
        grupo_frutas = frutas[inicio:fim]
        grupo_resultados = []

        for fruta in grupo_frutas:
            especie = buscar_especie_por_fruta(fruta, especies)
            if not especie:
                print(f"Sem resultados para '{fruta}'")
                continue

            nome_cientifico = especie.get("scientificName", "Desconhecido")
            print(f"Pesquisando '{fruta}' ({nome_cientifico})...")
            resultado = pesquisar_informacoes(model, nome_cientifico, fruta)

            if resultado:
                grupo_resultados.append(resultado)
            else:
                print(f"Nenhum resultado para '{fruta}'.")

        if grupo_resultados:
            salvar_resultado_json(grupo_resultados, i + 1)



if __name__ == "__main__":
    main()
