from fuzzywuzzy import fuzz, process
import requests
from datetime import datetime
from openIA import search_entity_in_chatgpt
import pdb
import re

def find_similars(question, array):
    matchs = process.extract(question, array, scorer=fuzz.ratio, limit=3)
    best_matchs = [mc for mc in matchs if mc[1] >= 80]
    return best_matchs

def get_questions(questions_for_search):
    questions_ids = []
    questions = []
    for claim in questions_for_search:
        mainsnak = claim.get("mainsnak", {})
        if "datavalue" in mainsnak:
            datavalue = mainsnak["datavalue"]
            if "value" in datavalue:
                value = datavalue["value"]
                if "id" in value:
                    questions_ids.append(value["id"])
    for questions_id in questions_ids:
        response_final = search_label(questions_id, 'http://qawiki.org/w/api.php')
        if response_final != None:
            questions.append(response_final)
    return questions

def get_sparql_value(query_claim):
    for claim in query_claim:
        mainsnak = claim.get("mainsnak", {})
        if "datavalue" in mainsnak:
            datavalue = mainsnak["datavalue"]
            if "value" in datavalue:
                return datavalue["value"],
            else:
                return None
        else:
            return None

def search_label(id, endpoint):
    params = {
        "action": "wbgetentities",
        "format": "json",
        "ids": id
    }

    try:
        response = requests.get(endpoint, params=params)

        if response.status_code == 200:
            data = response.json()
            if 'entities' in data and id in data['entities']:
                entity_data = data['entities'][id]
                if 'labels' in entity_data and 'en' and entity_data['labels']:
                    name = entity_data['labels']['en']['value']
                    print("El valor obtenido de la uri otorgada: " + name)
                    return name
                else:
                    print("No se encontro el valor en wikidata")
                    return None
            else:
                print("No se encontro datos para el id en wikidata")
                return None
    except:
        return None

def parse_similar_question(similar_question, original_question, sparql_of_similar_question):

   response_entity_similar_question_in_chatgtp, error = search_entity_in_chatgpt(similar_question)
   responses_entities_similar_question = search_for_entities_in_wikidata(response_entity_similar_question_in_chatgtp)
   entity_similar_question = search_original_entity_id_in_sparql_similar_question(responses_entities_similar_question, sparql_of_similar_question)
   response_entity_original_question_in_chatgtp, error = search_entity_in_chatgpt(original_question)
   responses_entities_original_question = search_for_entities_in_wikidata(response_entity_original_question_in_chatgtp)

   if error != None:
        return None
   else:
        return {
            'entity_similar_question_id_in_chatgpt': entity_similar_question,
            'entities_original_question': responses_entities_original_question
        }

def search_original_entity_id_in_sparql_similar_question(responses_entities_similar_question, sparql_of_similar_question):
    
    if responses_entities_similar_question == None:
        return None
    
    for result in responses_entities_similar_question:
        if ('wd:'+result['id']) in sparql_of_similar_question[0]:
            return result['id']
    
    return None

def search_for_entities_in_wikidata(entity):
    wikidata_endpoint = 'http://www.wikidata.org/w/api.php'

    params = {
        "action": "wbsearchentities",
        "format": "json",
        "search": entity,
        "language": 'en'
    }

    response = requests.get(wikidata_endpoint, params=params)

    if response.status_code == 200:
        data = response.json()
        print("Respuesta de wikidata: " + response.text )
        results = data["search"]
        response = []
        for result in results:

            if 'description' in result:
                description = result['description']
            elif 'label' in result:
                description = result['label']
            else:
                'No hay descripcion'

            response.append(
                {
                    "id": result['id'],
                    "description": description
                }
            )
        if len(results) == 0:
            return None
        else:
            return response
    else:
        print("Error en la solicitud a wikidata. " + response.text )
        return None
    
def search_in_wikipedia(query_to_wikidata):
    sparql_endpoint = "https://query.wikidata.org/sparql"

    params = {
        "query": query_to_wikidata,
        "format": "json"
    }

    response = requests.post(sparql_endpoint, data=params)

    if response.status_code == 200:
        data = response.json()
        print("Respuesta de wikidata: " + response.text )
        type_head = data["head"]["vars"][0]
        results = data["results"]["bindings"]
        response_initial = 'Okay, using the similar question we have the answer is: '
        for result in results:
            if type_head in result and result[type_head]["type"] == 'literal':
                response_final = result[type_head]["value"]
                print(f"Valor de wikidata: {response_final}")
                try:
                    fecha_datetime  = datetime.strptime(response_final, "%Y-%m-%dT%H:%M:%SZ")
                    response_final = datetime.strftime(fecha_datetime, '%d/%m/%Y') 
                    response_initial = response_initial + response_final + '. '
                except ValueError:
                    response_initial = response_initial + response_final + '. '         
            elif 'sbj' in result and result["sbj"]["type"] == 'uri':
                id = (result["sbj"]["value"].split('/'))[-1]
                response_final = search_label(id, 'http://wikidata.org/w/api.php')
                response_initial = response_initial + response_final + '. '
            elif 'age' in result and result["age"]["type"] == 'literal':
                response_final = result["age"]["value"]
                print(f"Valor de wikidata: {response_final}")
                response_initial = response_initial + response_final + '. '
            elif 'cnt' in result and result["cnt"]["type"] == 'literal':
                response_final = result["cnt"]["value"]
                print(f"Valor de wikidata: {response_final}")
                response_initial = response_initial + response_final + '. '
        if len(results) == 0:
            response_initial = "There is no information about it on Wikidata"
        return response_initial
    else:
        print("Error en la solicitud a wikidata. " + response.text )
        return "Wikidata error. Please contact the administrator"

def search_with_sparql_of_similar_question(context, id_entity_selected):

    sparql_of_similar_question = context.user_data.get('sparql_of_similar_question')
    id_entity_similar = context.user_data.get('entity_similar_question_id_in_chatgpt')
   
    if id_entity_similar == None:
        return {
            "answer": 'We couldnt find entity in wikidata'
        }

    context.user_data['sparql_of_similar_question'] = None
    context.user_data['entity_similar_question_id_in_chatgpt'] = None
    context.user_data['entities_original_question'] = None

    sparql_value = sparql_of_similar_question[0].replace(id_entity_similar, id_entity_selected.upper())

    return {
        "answer": search_in_wikipedia(sparql_value)
    }

def search_id_of_response_wikidata(response_wikidata, sparql_query):
    for result in response_wikidata:
        if result['id'] in sparql_query:
            return result['id']
    return None

def valid_question(text):
    words_needed = ["what", "which", "where", "when", "how"]
    start_with = False

    for word in words_needed:
        if text.startswith(word):
            start_with = True
            break
    return start_with
