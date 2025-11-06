import os
import json
import math
import google.generativeai as genai
from dotenv import load_dotenv

# Configuração LLM
def configureLLM():
    apiKey = os.getenv("GOOGLE_API_KEY")
    if not apiKey:
        raise ValueError(
            "A variável de ambiente GOOGLE_API_KEY não foi encontrada. "
            "Crie um arquivo .env e adicione sua chave."
        )
    genai.configure(api_key=apiKey)
    return genai.GenerativeModel('gemini-2.5-flash')

# Carrega o JSON
def carregarEspecies(arquivoEspecies):
    if not os.path.exists(arquivoEspecies):
        raise FileNotFoundError(f"Arquivo '{arquivoEspecies}' não encontrado.")
    with open(arquivoEspecies, "r", encoding="utf-8") as f:
        return json.load(f)

# Cria a lista das espécies pelo vernacularName
def extrairFrutasJson(especies):
    frutas = []
    for especie in especies:
        vernaculars = especie.get("vernacularNames", [])
        if vernaculars:
            primeiroNome = vernaculars[0].get("name", "").strip().lower()
            if primeiroNome:
                frutas.append(primeiroNome)
    return frutas


def buscarEspeciePorFruta(nomeFruta, especies):
    for especie in especies:
        for vernacular in especie.get("vernacularNames", []):
            if vernacular.get("name", "").lower() == nomeFruta.lower():
                return especie
    return None


# Manda o prompt pro Gemini
def pesquisarInformacoes(model, nomeCientifico, nomeFruta):
    prompt = f"""
    Pesquise na Wikipédia (em português ou inglês, se necessário, porém traduza se estiver em inglês) sobre a espécie "{nomeCientifico}", que corresponde à fruta ou árvore: "{nomeFruta}".
    Produza a resposta em formato JSON, com apenas o objeto JSON, sem texto fora dele.
    O JSON deve seguir esta estrutura:
    {{
      "fruta": "{nomeFruta}",
      "nome_cientifico": "{nomeCientifico}",
      "etimologia": "Texto com as fontes entre parênteses(...).",
      "origem_do_fruto": "Texto também com referências(...).",
      "manejo_e_cultivo": "Texto também com referências(...).",
      "referencias": [
          {{ "1": "Fonte referente à etimologia ou primeira citação mencionada." }},
          {{ "2": "Fonte referente à origem do fruto." }},
          {{ "3": "Fonte referente ao manejo/cultivo." }}
      ]
    }}
    """

    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned)
    except Exception as e:
        print(f"Erro ao pesquisar {nomeFruta}: {e}")
        return None


# Salva o retorno
def salvarResultadoJson(grupoResultados, indiceGrupo):
    nomeArquivo = f"pesquisa_grupo_{indiceGrupo}.json"
    with open(nomeArquivo, "w", encoding="utf-8") as f:
        json.dump(grupoResultados, f, ensure_ascii=False, indent=4)
    print(f"3 registros salvos em '{nomeArquivo}'.")


def main():
    load_dotenv()
    model = configureLLM()

    arquivoEspecies = "especies.json"
    especies = carregarEspecies(arquivoEspecies)
    frutas = extrairFrutasJson(especies)

    tamanhoGrupo = 3
    totalGrupos = math.ceil(len(frutas) / tamanhoGrupo)

    for i in range(totalGrupos):
        inicio = i * tamanhoGrupo
        fim = inicio + tamanhoGrupo
        grupoFrutas = frutas[inicio:fim]
        grupoResultados = []

        for fruta in grupoFrutas:
            especie = buscarEspeciePorFruta(fruta, especies)
            if not especie:
                print(f"Sem resultados para '{fruta}'")
                continue

            nomeCientifico = especie.get("scientificName", "Desconhecido")
            print(f"Pesquisando '{fruta}'...")
            resultado = pesquisarInformacoes(model, nomeCientifico, fruta)

            if resultado:
                grupoResultados.append(resultado)
            else:
                print(f"Nenhum resultado para '{fruta}'.")

        if grupoResultados:
            salvarResultadoJson(grupoResultados, i + 1)



if __name__ == "__main__":
    main()
