import requests
from datetime import datetime
import pdb
from chatbot.utils import add_label_using_uris, find_similars, get_questions, get_sparql_value
from qa_autocomplete.utils import logger
    
def parse_response(user_message, query_to_wikidata, analogous_questions = None, general_questions = None):
   
    sparql_endpoint = "https://query.wikidata.org/sparql"

    params = {
        "query": query_to_wikidata,
        "format": "json"
    }

    response = requests.post(sparql_endpoint, data=params)

    if response.status_code == 200:
        data = response.json()
        response_initial = 'The answer for "'+ user_message.capitalize() +'" is '
        print("Respuesta de wikidata: " + response.text )
        if 'boolean' in data:
            if data['boolean'] == False:

                response_initial = response_initial + 'no. ' 
            else:
                response_initial = response_initial + 'yes. ' 
            return {
                "answer" :              response_initial,
                "analogous_questions":  analogous_questions,
                "general_questions":    general_questions,
                'ask_for_add_alias':    False
            }
        type_head = data["head"]["vars"][0]
        results = data["results"]["bindings"]
        array_of_uris = []
        has_response = False
        for result in results:
            if type_head in result and result[type_head]["type"] == 'literal':
                response_final = result[type_head]["value"]
                has_response = True
                print(f"Valor de wikidata: {response_final}")
                try:
                    fecha_datetime  = datetime.strptime(response_final, "%Y-%m-%dT%H:%M:%SZ")
                    response_final = datetime.strftime(fecha_datetime, '%d/%m/%Y') 
                    response_initial = response_initial + response_final + '. '
                except ValueError:
                    response_initial = response_initial + response_final + '. '         
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
            response_initial = "There is no information about it on Wikidata"
        return {
            "answer" :              response_initial,
            "analogous_questions":  analogous_questions,
            "general_questions":    general_questions,
            'ask_for_add_alias':    False
        }
    else:
        print("Error en la solicitud a wikidata. " + response.text )
        return {
            "answer" : "Unexpected error. Please contact the administrator",
            "analogous_questions":  [],
            "general_questions":    [],
            'ask_for_add_alias':    False
        }

def search_id_to_QAwiki(pregunta):

    qawiki_endpoint="http://query.qawiki.org/proxy/wdqs/bigdata/namespace/wdq/sparql"
    params = {
        "query": """SELECT ?q ?qLabel ?alias WHERE { ?q wdt:P1 wd:Q1 . SERVICE wikibase:label { bd:serviceParam wikibase:language 'en'. } OPTIONAL { ?q skos:altLabel ?alias. FILTER(LANG(?alias) = 'en') }}""",
        "format":"json"
    }
    try:
        response = requests.get(qawiki_endpoint, params=params)
        if response.status_code == 200:
            data = response.json()
            search_results = data.get("results", [])
            if len(search_results) > 0:
                search_bindings = search_results.get("bindings", [])
                if len(search_bindings) > 0:
                    id = None
                    for result in search_bindings:
                        if result['qLabel']['value'].lower() == pregunta:
                            id = ((result['q']['value']).split("/"))[-1]
                        elif 'alias' in result and result['alias']['value'].lower() == pregunta:
                            id = ((result['q']['value']).split("/"))[-1]
                    similar_questions = []
                    if id == None:
                        similar_questions = find_similars(pregunta)
                        if len(similar_questions) > 0:
                            return None, similar_questions
                        else:
                            return None, []
                    return id, similar_questions
                else:
                    print("No se encontraron resultados para la busqueda, campo binding vacio")
                    return None, []
            else:
                print("No se encontraron resultados para la busqueda, campo results vacio")
                return None, []
    except:
        return None, []

def search_item_to_QAwiki(id):
   
    endpoint="http://qawiki.org/w/api.php"
    params = {
        "action": "wbgetentities",
        "format": "json",
        "ids": id
    }

    try:
        response = requests.get(endpoint, params=params)

        if response.status_code == 200:
            data = response.json()
            entity_info = data["entities"].get(id,None)
            if entity_info:
                claims = entity_info.get("claims", {})
                query_claim = claims.get("P11",[])
                analogous_questions = claims.get("P40",[])
                general_questions = claims.get("P41",[])
                sparql_value = get_sparql_value(query_claim)
                general_questions_values = get_questions(general_questions)
                analogous_questions_values = get_questions(analogous_questions)
                return {
                    "query": sparql_value,
                    "analogous_questions": general_questions_values,
                    "general_questions": analogous_questions_values
                }
            else:
                return None
        else:       
            return None
    except:
        return None

# Sin usar
def add_alias_to_question_in_qawiki(id_question_qawiki, alias):
    form_data = {
        "token": '+\\',
        "action": "wbsetaliases",
        "format": 'json',
        "id": id_question_qawiki,
        "language": "en",
        "add": alias.capitalize()
    }

    endpoint="http://qawiki.org/w/api.php"

    try:
        response = requests.post(endpoint, data=form_data)

        data = response.json()
        if 'error' in data:
           logger.warning("No se pudo agregar el alias " + alias + " para id de question en QAWiki " + id_question_qawiki)
           print("No se pudo agregar el alias " + alias + " para id de question en QAWiki " + id_question_qawiki)
           return "No se pudo agregar el alias: " + alias.capitalize()
        else:
           logger.warning("Se agrego el alias " + alias + " para id de question en QAWiki "+ id_question_qawiki)
           print("Se agrego el alias "+ alias + " para id de question en QAWiki "+ id_question_qawiki)
           return "Se agrego el alias: "+ alias.capitalize()
    except:
        logger.warning("Error de conexion al intentar agregar el alias "+ alias + " para id de question en QAWiki "+ id_question_qawiki)
        print("Error de conexion al intentar agregar el alias "+ alias + " para id de question en QAWiki "+ id_question_qawiki)
        
        return "Error inesperado al intentar agregar el alias: " + alias.capitalize()