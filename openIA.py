import constants as keys
import openai
import pdb
import re

def search_entity_in_chatgpt(question):
    try:

        openai.api_key = keys.API_OPENIA_KEY
        response_chatgpt = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
               
                {"role": "user", "content": 'Retorna la entidad para la frase: '+ question  }
            ]
        )

        print(f"Respuesta de OpenIA: {response_chatgpt}")

        patron = r'"([^"]*)"'
        coincidencias = re.findall(patron, response_chatgpt['choices'][0]['message']['content'])

        if len(coincidencias) > 0:
            return coincidencias[-1], None
        else:
            return None, 'No se encontraron respuestas con chatgpt'

    except Exception as e:
        print(f"Respuesta de OpenIA: {e}")
        return None, str(e)