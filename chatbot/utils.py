import json
import os
import re
from fuzzywuzzy import fuzz, process
import requests
from datetime import datetime
import sentry_sdk
import spacy
import pdb
from qa_autocomplete.utils import read_json, save_json
from sentence_transformers import SentenceTransformer, util
from nltk.corpus import stopwords
import nltk
import string
from nltk import word_tokenize, pos_tag, ne_chunk 

CACHED_QUESTIONS_TEMPLATES_PATH = "static/cached_questions/templates.json"
CACHED_QUESTIONS_TEMPLATES_CHATBOT_PATH = "static/cached_questions/templates_chatbot.json"
CACHED_ANSWERS_TEMPLATES_PATH = "static/cached_questions/answers.json"
CACHED_PATH = 'static/cached_questions'
ANSWERS_FILENAME = 'answers.json'
LIMIT_SEARCH_LABELS = 20

nltk.download('stopwords')

def preprocess_text(text):
    # Convertir a minúsculas
    text = text.lower()
    
    # Eliminar signos de puntuación
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Tokenizar el texto
    tokens = text.split()

    # Eliminar stop words
    stop_words = set(stopwords.words('english'))  # Reemplazar 'nombre_del_idioma' con el idioma deseado
    tokens = [word for word in tokens if word not in stop_words]
    
    # Reconstruir el texto preprocesado
    preprocessed_text = ' '.join(tokens)
    
    return preprocessed_text


def compare_sentences(pregunta_original=str, preguntas_template=str):
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    p_original = []
    array = []
    for pregunta in preguntas_template:
        array.append(preprocess_text(pregunta))
    p_original.append(preprocess_text(pregunta_original))
    embedding1 = model.encode(p_original, convert_to_tensor=True)
    embedding2 = model.encode(array, convert_to_tensor=True)

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
    templates_chatbot = read_json(CACHED_QUESTIONS_TEMPLATES_CHATBOT_PATH)
    semantic_matchs = []
    questions_template = []
    for template in templates:
        if 'question_en' in template:
            questions_template.append(template['question_en'])
    for template_chatbot in templates_chatbot:
        if 'question_en' in template_chatbot:
            questions_template.append(template_chatbot['question_en'])

    semantic_matchs = compare_sentences(question, questions_template)
    sintactic_matchs = process.extract(question, questions_template, scorer=fuzz.ratio, limit=3)
    best_sintactic_matchs = [mc[0] for mc in sintactic_matchs if mc[1] >= 80]
    all_matchs= []

    # Prizamos matcheos semanticos y sintacticos al mismo tiempo, luego las semanticas y por ultimo las sintacticas

    for question in semantic_matchs:
        if question in best_sintactic_matchs and question not in all_matchs and len(all_matchs) < 3:
            all_matchs.append(question)

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

def parse_similar_question(original_question, context,similar_questions, context_question = None, context_question_template_en = None):
    response_entity_original_question, error = search_entity_using_main_entity_searcher(original_question)

    if error != None:
       return None, []

    responses_ids_entities_original_question = search_for_entities_in_wikidata(response_entity_original_question)
    response_search_instance_of_entities_original_question = search_instance_of(responses_ids_entities_original_question)
    templates = read_json(CACHED_QUESTIONS_TEMPLATES_PATH)
    templates_chatbot = read_json(CACHED_QUESTIONS_TEMPLATES_CHATBOT_PATH)
    ids_of_matches_template = []
    templates_question_template_en = []

    for similar_question in similar_questions:
        for template in templates:
            if 'question_en' in template and template['question_en'].lower() == similar_question.lower():
                for match_en in template["matches_en"]:
                    ids_of_matches_template.append(match_en['entity'])
            if 'question_template_en' in template:
                templates_question_template_en.append(template['question_template_en'])
                if context_question != None and context_question_template_en.lower() == template['question_template_en'].lower():
                    for match_en in template["matches_en"]:
                        ids_of_matches_template.append(match_en['entity'])

        for template in templates_chatbot:
            if 'question_en' in template and template['question_en'].lower() == similar_question.lower():
                for match_en in template["matches_en"]:
                    ids_of_matches_template.append(match_en['entity'])
            if 'question_template_en' in template:
                templates_question_template_en.append(template['question_template_en'])
                if context_question != None and context_question_template_en.lower() == template['question_template_en'].lower():
                    for match_en in template["matches_en"]:
                        ids_of_matches_template.append(match_en['entity'])

    set_transform_templates_question_template_en = set(templates_question_template_en)
    set_transform_ids_of_matches_template= set(ids_of_matches_template)

    templates_question_template_en = list(set_transform_templates_question_template_en)
    ids_of_matches_template = list(set_transform_ids_of_matches_template)
    response_search_instance_of_entities_template = search_instance_of(ids_of_matches_template)

    mentions_template = []
    posibles_ids_for_the_original_question = set()
    for entities_and_mention_template in response_search_instance_of_entities_template:
        mentions_template.append(entities_and_mention_template['id_mention'])

    entity = ''
    for entity_and_mention_original_question in response_search_instance_of_entities_original_question:
        if entity_and_mention_original_question['id_mention'] in mentions_template:
            posibles_ids_for_the_original_question.add(entity_and_mention_original_question['id_entity'])
            entity = entity_and_mention_original_question['label']
    final_response = ""
    lista_ids = list(posibles_ids_for_the_original_question)
    used_similar_mentions = set()
    for posibles_id in lista_ids:
        response = similar_query(posibles_id, similar_questions, entity, original_question, context_question_template_en)
        if response['final_answer'] != "":
            final_response = final_response + response["final_answer"] + "\n"
            mentions = find_by_key(response_search_instance_of_entities_original_question, 'id_entity', posibles_id)
            sparql_set = set(response['sparql_values'])
            for used_similar_question in response['similar_questions_used']:
                for template in templates:
                    if 'question_en' in template and used_similar_question.lower() == template['question_en'].lower():
                        used_similar_mentions.add(template['question_template_en'])
                for template in templates_chatbot:
                    if 'question_en' in template and used_similar_question.lower() == template['question_en'].lower():
                        used_similar_mentions.add(template['question_template_en'])

            array_sparql = list(sparql_set)
            if valid_question(original_question):
                add_template_chatbot_to_context(mentions[0]['label'], posibles_id, original_question, array_sparql, templates_question_template_en,context)
    return final_response, list(used_similar_mentions)

def find_by_key(array, clave, valor):
    return [elemento for elemento in array if elemento.get(clave) == valor]

def add_template_chatbot_to_context(matches_en_mention, matches_en_entity, original_question, sparql_values, templates_question_template_en, context):

    posibles_alias = context.user_data.get('posibles_alias')
    if posibles_alias == None:
        posibles_alias = []
    for sparql_value in sparql_values:
        item = {}
        mention = [{ "mention": matches_en_mention.lower(), "entity": matches_en_entity }]

        item[f"question_en"], item[f"matches_en"], item[f"question_template_en"], item[f"query_template_en"], item[f"visible_question_en"] = generate_template_chatbot(mention, original_question, sparql_value)
        if item[f"question_template_en"] not in templates_question_template_en:
            posibles_alias.append(item)
    context.user_data['posibles_alias'] = posibles_alias
   
def generate_template_chatbot(mention_template, original_question, sparql_value):
    entities = set()

    for mention in mention_template:
        entities.add(mention['entity'])
    
    entities = list(entities)
    
    for mention in mention_template:
       
        question_template = original_question
        visible_question = original_question

        query_template = sparql_value
        matched_mentions = []
     
        for e in entities:
            first_match = next((m for m in mention_template if m['entity'] == e and m['mention'] in original_question), None)
            if first_match is not None:
                matched_mentions.append(first_match)
        
        for idx in range(len(matched_mentions)):
            visible_question = re.sub(r'\b' + re.escape(matched_mentions[idx]["mention"]) + r'((?= )|(?=\?))', "{" + matched_mentions[idx]["mention"] + "}", visible_question)
            question_template = re.sub(r'\b' + re.escape(matched_mentions[idx]["mention"]) + r'((?= )|(?=\?))', f"$mention_{idx}", question_template)
            query_template = re.sub(r'\b' + re.escape("wd:" + matched_mentions[idx]["entity"]) + r'((?= )|(?=\?)|(?=\))|(?=\}))', f"$entity_{idx}", query_template)
        
        return original_question, matched_mentions, question_template, query_template, visible_question
           
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

            response.append(result['id'])
        if len(results) == 0:
            return None
        else:
            return response
    else:
        print("Error en la solicitud a wikidata. " + response.text )
        return None

def search_instance_of(ids_of_items):
    query = """SELECT ?itemLabel ?itemClass ?label WHERE { VALUES ?item { """

    for id in ids_of_items:
        resource = "wd:" + id
        query = query + resource + " "
    
    query = query + """ } ?item wdt:P31 ?itemClass. ?item rdfs:label ?label. FILTER(LANG(?label) = 'en'). SERVICE wikibase:label { bd:serviceParam wikibase:language "[en]" }}"""

    sparql_endpoint = "https://query.wikidata.org/sparql"

    params = {
        "query": query,
        "format": "json"
    }

    response = requests.post(sparql_endpoint, data=params)

    if response.status_code == 200:
        data = response.json()
        results = data["results"]["bindings"]
        final_response = []
        for result in results:
           
            id_mention = (result["itemClass"]["value"].split('/'))[-1]
            final_response.append(
                {
                  "id_entity":result["itemLabel"]["value"],
                  "id_mention": id_mention,
                  "label": result["label"]["value"]
                } 
            )
        
        return final_response

    else:
        print("Error en la solicitud a wikidata. " + response.text )
        return "Unexpected error. Please contact the administrator"
    
def search_in_wikipedia(query_to_wikidata):
    sparql_endpoint = "https://query.wikidata.org/sparql"

    params = {
        "query": query_to_wikidata,
        "format": "json"
    }

    response = requests.post(sparql_endpoint, data=params)

    if response.status_code == 200:
        data = response.json()
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
                id = (result[type_head]["value"].split('/'))[-1]
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
        return "Unexpected error. Please contact the administrator"

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
        "answer": search_in_wikipedia(sparql_value),
        "sparql_value": sparql_value
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

def save_answer(question, answer, analogous_questions, general_questions, question_template_en= None):
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
                "question_template_en" : question_template_en,
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

def similar_query(id_entity_selected, similar_questions, entity, original_question, context_question_template_en):
    templates = read_json(CACHED_QUESTIONS_TEMPLATES_PATH)
    templates_chatbot = read_json(CACHED_QUESTIONS_TEMPLATES_CHATBOT_PATH)
    initial_response = "We don't have an answer for that question. However we found similar questions that might be useful. \n"
    final_response = ""
    similar_questions_used = set()
    sparql_of_similar_questions = []
    sparql_values = []
    change_response = False
    count_results = 0
    for similar_question in similar_questions:
        for template in templates:
            if (('question_en' in template and template['question_en'].lower() == similar_question.lower()) or ('question_en' in template and context_question_template_en != None and template['question_template_en'].lower() == context_question_template_en.lower())) and template['visible_question_en'].count('{') == 1 and template['query_template_en'].count('entity_') == 1:
                sparql_of_similar_question = template['query_template_en']
                if sparql_of_similar_question not in sparql_of_similar_questions:
                    sparql_of_similar_questions.append(sparql_of_similar_question)
                    response = search_with_sparql_of_similar_question(sparql_of_similar_question, id_entity_selected)
                    if response['answer'] != "":
                        count_results = count_results + 1
                        similar_questions_used.add(similar_question)
                        sparql_values.append(response['sparql_value'])
                        entity_visible_question_en = re.search(r'\{(.*?)\}', template['visible_question_en']).group(1)
                        
                        if template['question_en'].replace(template['matches_en'][0]['mention'], entity).lower() == original_question:
                            change_response = True
                            final_response = final_response + 'The answer to "'+ template['question_en'].replace(entity_visible_question_en, entity) +'" is: '+ response['answer'] + "\n"
                        else:
                            final_response = final_response + 'Having the question "'+ template['question_en'].replace(entity_visible_question_en, entity) +'" the answer is: '+ response['answer'] + "\n"
        for template in templates_chatbot:
            if ('question_en' in template and template['question_en'].lower() == similar_question.lower()) or ('question_en' in template and context_question_template_en != None and template['question_template_en'].lower() == context_question_template_en.lower()):
                sparql_of_similar_question = template['query_template_en']
                if sparql_of_similar_question not in sparql_of_similar_questions:
                    sparql_of_similar_questions.append(sparql_of_similar_question)
                    response = search_with_sparql_of_similar_question(sparql_of_similar_question, id_entity_selected)
                    if response['answer'] != "":
                        count_results = count_results + 1
                        similar_questions_used.add(similar_question)
                        sparql_values.append(response['sparql_value'])
                        entity_visible_question_en = re.search(r'\{(.*?)\}', template['visible_question_en']).group(1)
                        if template['question_en'].replace(entity_visible_question_en, entity).lower() == original_question:
                            change_response = True
                            final_response = final_response + 'The answer to "'+ template['question_en'].replace(entity_visible_question_en, entity) +'" is: '+ response['answer'] + "\n"
                        else:
                            final_response = final_response + 'Having the question "'+ template['question_en'].replace(entity_visible_question_en, entity) +'" the answer is: '+ response['answer'] + "\n"
    
    if change_response == True:
        initial_response = ''
    final_answer = initial_response + final_response + 'We had to use similar questions to give you this answer, please help us saying if this answer helped you.'
    if count_results == 0:
        final_answer = ''
    return {
        "final_answer": final_answer,
        "similar_questions_used": similar_questions_used,
        "sparql_values": sparql_values 
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

def create_answers_file():
    nombre_archivo = 'answers.json'
    path = 'static/cached_questions/'  
    ruta_completa = os.path.join(path, nombre_archivo)

    if not os.path.exists(ruta_completa):
        datos = []
        with open(ruta_completa, 'w') as archivo:
            json.dump(datos, archivo)

def search_template_chatbot(user_message):
    template_chatbot = read_json(CACHED_QUESTIONS_TEMPLATES_CHATBOT_PATH)
    for template in template_chatbot:
        if template['question_en'].lower() == user_message.lower():
            if '$entity_0' in template['query_template_en']:
                sparql_value = template['query_template_en'].replace('$entity_0', 'wd:'+template['matches_en'][0]['entity'].upper())
            elif '$entity_1' in template['query_template_en']:
                sparql_value = template['query_template_en'].replace('$entity_1', 'wd:'+template['matches_en'][0]['entity'].upper())
            elif '$entity_2' in template['query_template_en']:
                sparql_value = template['query_template_en'].replace('$entity_2', 'wd:'+template['matches_en'][0]['entity'].upper())
            elif '$entity_3' in template['query_template_en']:
                sparql_value = template['query_template_en'].replace('$entity_3', 'wd:'+template['matches_en'][0]['entity'].upper())
            
            return { "query": sparql_value, "query_template_en": template['query_template_en'] }
    return { "query": None, "query_template_en": None }

def save_response_as_template_chatbot(context):
    if 'We had to use similar questions to give you this answer, please help us saying if this answer helped you.' in context.user_data.get('posible_response'):
        context.user_data['posible_response'] = context.user_data.get('posible_response').replace('We had to use similar questions to give you this answer, please help us saying if this answer helped you.', ' ')
    if "We don't have an answer for that question. However we found similar questions that might be useful. " in context.user_data.get('posible_response'):
        context.user_data['posible_response'] = context.user_data.get('posible_response').replace("We don't have an answer for that question. However we found similar questions that might be useful. ", ' ')

    question = context.user_data.get('posible_question')
    answer = context.user_data.get('posible_response')
    if not valid_question(context.user_data.get('posible_question')):
        question = re.search(r'"([^"]*)"', answer).group(1)
    save_answer(question, answer, [], [], context.user_data.get("context_question_template_en") )
    context.user_data['posible_question'] = None
    context.user_data['posible_response'] = None
    template_chatbot = read_json(CACHED_QUESTIONS_TEMPLATES_CHATBOT_PATH)
    templates = read_json(CACHED_QUESTIONS_TEMPLATES_PATH)
    questions_template_en = []
    for template_chat in template_chatbot:
        questions_template_en.append(template_chat['question_template_en'].lower())
    for temp in templates:
        if 'question_template_en' in temp:
            questions_template_en.append(temp['question_template_en'].lower())
    if (context.user_data.get('posibles_alias') != None):
        for template in context.user_data.get('posibles_alias'):
            if template['question_template_en'].lower() not in questions_template_en:
                template_chatbot.append(template)
    save_json(template_chatbot, CACHED_PATH, 'templates_chatbot.json')
    context.user_data['posibles_alias'] = []

def search_question_template_en(question):
    template_chatbot = read_json(CACHED_QUESTIONS_TEMPLATES_CHATBOT_PATH)
    templates = read_json(CACHED_QUESTIONS_TEMPLATES_PATH)

    for template in templates:
        if 'question_en' in template and template['question_en'].lower() == question.lower():
            return template['question_template_en']
    for template in template_chatbot:
        if 'question_en' in template and template['question_en'].lower() == question.lower():
            return template['question_template_en']
    
    return ''

def search_entity_using_main_entity_searcher(question):
    entities = set()
    try:
        response = identify_main_entity(question)
        if response != '':
            return response, None
        else:
            nltk.download('maxent_ne_chunker')
            nltk.download('words')

            words = word_tokenize(question)
            pos_tags = pos_tag(words)
            named_entities = ne_chunk(pos_tags)

            for entity in named_entities:
                if isinstance(entity, tuple) and (entity[1] == 'NN' or entity[1] == 'NNS'  or entity[1] == 'NNP'  or entity[1] == 'NNPS'):
                    print(entity[0], entity[1])
                    entities.add(entity[0])
            entities = list(entities)
            if len(entities) > 0:
                return entities[0], None
            else:
                return None, 'No se encontraron respuestas con main identifier'

    except Exception as e:
        print(f"Respuesta de Main Entity searcher: {e}")
        return None, str(e)

def identify_main_entity(question):

    nlp = spacy.load("en_core_web_sm")
    text = question
    documen = nlp(text)

    if len(documen.ents) > 0:
        print(f'Main Entity found: {documen.ents[0].text}')
        return documen.ents[0].text
    else:
        print(f'Main Entity Not found')
        return ''
