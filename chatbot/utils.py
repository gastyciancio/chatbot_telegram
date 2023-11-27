import os
from fuzzywuzzy import fuzz, process
import requests
from datetime import datetime
import sentry_sdk
from chatbot.openIA import search_entity_in_chatgpt
import pdb
import re
from qa_autocomplete.utils import read_json, save_json
from sentence_transformers import SentenceTransformer, util

CACHED_QUESTIONS_TEMPLATES_PATH = "static/cached_questions/templates.json"
CACHED_ANSWERS_TEMPLATES_PATH = "static/cached_questions/answers.json"
CACHED_PATH = 'static/cached_questions'
ANSWERS_FILENAME = 'answers.json'
LIMIT_SEARCH_LABELS = 20


def compare_sentences(pregunta_original=str, preguntas_template=str):
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    p_original = []
    p_original.append(pregunta_original)
    embedding1 = model.encode(p_original, convert_to_tensor=True)
    embedding2 = model.encode(preguntas_template, convert_to_tensor=True)

    similarity_matrix  = util.pytorch_cos_sim(embedding1, embedding2)

    best_matchs = []

    print("Buscando preguntas en QAWiki con similitud semantica")

    for i in range(len(p_original)):
        for j in range(len(preguntas_template)):
            if similarity_matrix[i][j].item() > 0.6 and p_original[i] != preguntas_template[j]:
                best_matchs.append(preguntas_template[j])

    return best_matchs

def find_similars(question):
    templates = read_json(CACHED_QUESTIONS_TEMPLATES_PATH)
    semantic_matchs = []
    questions_template = []
    for template in templates:
        if 'question_en' in template:
            questions_template.append(template['question_en'])

    semantic_matchs = compare_sentences(question, questions_template)
    sintactic_matchs = process.extract(question, questions_template, scorer=fuzz.ratio, limit=3)
    best_sintactic_matchs = [mc[0] for mc in sintactic_matchs if mc[1] >= 80]
    all_matchs= []

    # Damos prioridad a las coincidencias semanticas
    for question in semantic_matchs:
        if question not in all_matchs and len(all_matchs) < 3:
            all_matchs.append(question)

    for question in best_sintactic_matchs:
        if question not in all_matchs and len(all_matchs) < 3:
            all_matchs.append(question)
    
    return all_matchs

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

def parse_similar_question(original_question, entity_similar_question = None):

   response_entity_original_question_in_chatgtp, error = search_entity_in_chatgpt(original_question)
   responses_entities_original_question = search_for_entities_in_wikidata(response_entity_original_question_in_chatgtp)

   if error != None:
        return None
   else:
        return {
            'entity_similar_question_id': entity_similar_question,
            'entities_original_question': responses_entities_original_question
        }

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
        count = 0
        has_response = False
        print("Respuesta de wikidata: " + response.text )
        if 'boolean' in data:
            if data['boolean'] == False:
                return 'no'
            else:
                return 'yes'
        type_head = data["head"]["vars"][0]
        results = data["results"]["bindings"]
        response_initial = ''
        array_of_uris = []
        for result in results:
            if type_head in result and result[type_head]["type"] == 'literal':
                response_final = result[type_head]["value"]
                has_response = True
                print(f"Valor de wikidata: {response_final}")
                try:
                    fecha_datetime  = datetime.strptime(response_final, "%Y-%m-%dT%H:%M:%SZ")
                    response_final = datetime.strftime(fecha_datetime, '%d/%m/%Y')
                    if len(results) > 1:
                        response_initial = response_initial + '\n- '+ response_final + '.'
                    else:
                        response_initial = response_initial + response_final + '.' 
                except ValueError:
                    if len(results) > 1:
                        response_initial = response_initial + '\n- '+ response_final + '.'
                    else:
                        response_initial = response_initial + response_final + '.'       
            elif 'sbj' in result and result["sbj"]["type"] == 'uri':
                id = (result["sbj"]["value"].split('/'))[-1]
                array_of_uris.append("wd:"+id)
                has_response = True
            elif type_head in result and result[type_head]["type"] == 'uri':
                id = (result["sbj"]["value"].split('/'))[-1]
                array_of_uris.append("wd:"+id)
                has_response = True
            elif 'age' in result and result["age"]["type"] == 'literal':
                response_final = result["age"]["value"]
                has_response = True
                print(f"Valor de wikidata: {response_final}")
                response_initial = response_initial + response_final + '. '
            elif 'cnt' in result and result["cnt"]["type"] == 'literal':
                response_final = result["cnt"]["value"]
                has_response = True
                print(f"Valor de wikidata: {response_final}")
                response_initial = response_initial + response_final + '. '
        if len(array_of_uris) > 0:
            if len(array_of_uris) == 1:
                response_initial = response_initial + add_label_using_uris(array_of_uris) + '\n'
            else:
                response_initial = response_initial + '\n'+ add_label_using_uris(array_of_uris) + '\n'
        if len(results) == 0 or has_response == False:
            response_initial = ""
        return response_initial
    else:
        print("Error en la solicitud a wikidata. " + response.text )
        return "Wikidata error. Please contact the administrator"

def search_with_sparql_of_similar_question(sparql_of_similar_question, id_entity_selected):
    if '$entity_0' in sparql_of_similar_question:
        sparql_value = sparql_of_similar_question.replace('$entity_0', 'wd:'+id_entity_selected.upper())
    elif '$entity_1' in sparql_of_similar_question:
        sparql_value = sparql_of_similar_question.replace('$entity_1', 'wd:'+id_entity_selected.upper())
    elif '$entity_2' in sparql_of_similar_question:
        sparql_value = sparql_of_similar_question.replace('$entity_2', 'wd:'+id_entity_selected.upper())
    elif '$entity_3' in sparql_of_similar_question:
        sparql_value = sparql_of_similar_question.replace('$entity_3', 'wd:'+id_entity_selected.upper())

    return {
        "answer": search_in_wikipedia(sparql_value)
    }

def search_id_of_response_wikidata(response_wikidata, sparql_query):
    for result in response_wikidata:
        if result['id'] in sparql_query:
            return result['id']
    return None

def valid_question(text):
    words_needed = ["what", "which", "where", "when", "how", "is", "did", "do", "in", "who", "on" ,"kim", "from", "has", "was", "are"]
    start_with = False

    for word in words_needed:
        if text.startswith(word):
            start_with = True
            break
    return start_with

def save_answer(question, answer, analogous_questions, general_questions):
    answers = read_json(CACHED_ANSWERS_TEMPLATES_PATH)
    already_exists = False
    for answer_cached in answers:
        if answer_cached['question'].lower() == question.lower():
            already_exists = True
    if already_exists == False:
        answers.append(
            {
                "question": question,
                "answer":   answer,
                "analogous_questions": analogous_questions,
                "general_questions": general_questions
            }
        )
        save_json(answers, CACHED_PATH, ANSWERS_FILENAME)

def search_cached_answer(question):
    answers = read_json(CACHED_ANSWERS_TEMPLATES_PATH)
    for answer in answers:
        if answer['question'].lower() == question.lower():
            return answer
    return None

def answers_reset():
    answers = read_json(CACHED_ANSWERS_TEMPLATES_PATH)
    answers = []
    save_json(answers, CACHED_PATH, ANSWERS_FILENAME)

def similar_query(id_entity_selected, similar_questions, context):
    templates = read_json(CACHED_QUESTIONS_TEMPLATES_PATH)
    final_response = ''
    for similar_question in similar_questions:
        for template in templates:
            if 'question_en' in template and template['question_en'].lower() == similar_question.lower() and template['visible_question_en'].count('{') <= 1:
                sparql_of_similar_question = template['query_template_en']
                response = search_with_sparql_of_similar_question(sparql_of_similar_question, id_entity_selected)
                if response['answer'] != "":
                    ids = context.user_data.get('ids_for_alias')
                    if ids == None:
                        ids = []
                    if template['id'] not in ids:
                        ids.append(template['id'])
                    context.user_data['ids_for_alias'] = ids
                    final_response = final_response + 'Using the question "'+ template['question_en'] +'" the answer is: '+ response['answer'] + '\n'
    return {
        "final_answer":final_response
    }

def add_label_using_uris(array_of_uris):

    query = 'SELECT ?itemLabel WHERE { VALUES ?item { '

    for uri in array_of_uris:
        query = query + uri + ' '
    query = query + ''' } SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }}'''
    
    return search_in_wikipedia(query)

def send_email_to_qawiki(question, message):
    sentry_sdk.init(
            dsn=os.environ.get("DNS_SENTRY"),
            traces_sample_rate=1.0,
            enable_tracing=True
        )
    sentry_sdk.capture_message("Question: "+ question + ". Message: "+ message)