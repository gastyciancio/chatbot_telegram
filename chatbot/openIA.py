import openai
import pdb
import re
import os
from qa_autocomplete.utils import logger

def search_entity_in_chatgpt(question):
    try:

        openai.api_key = os.environ.get("API_OPENIA_KEY")
        response_chatgpt = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
               
                {"role": "user", "content": 'Analiza sintácticamente la frase "' + question + '" y retorna solo la entidad'  }
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
        logger.error(str(e))
        print(f"Respuesta de OpenIA: {e}")
        return None, str(e)