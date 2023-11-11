import requests
from datetime import datetime
import pdb
from utils import find_similars, get_questions, get_sparql_value, search_label

def search(text):
    response_QAwiki_id, similar_questions = search_id_to_QAwiki(text)
    if response_QAwiki_id == None:
        if len(similar_questions) == 0:
            # aca enviar mail a qawiki pidiendo que agreguen la pregunta
            return {
                "answer" : "There is not information about what you search",
                "analogous_questions": [],
                "general_questions": [],
                "similar_questions": [],
                'posibles_entities': []
            }
        else:
            return {
                "answer" : "There is not information about what you search.",
                "analogous_questions": [],
                "general_questions": [],
                "similar_questions": similar_questions,
                'posibles_entities': []
            }
    else:
        response_QAwiki_query = search_item_to_QAwiki(response_QAwiki_id)
        if response_QAwiki_query["query"] == None:
            return {
                "answer" : "There is not result for what you search",
                "analogous_questions": [],
                "general_questions": [],
                "similar_questions": [],
                'posibles_entities': []
            }
        response = parse_response(response_QAwiki_query["query"], response_QAwiki_query["analogous_questions"], response_QAwiki_query["general_questions"])
        return response
    
def parse_response(query_to_wikidata, analogous_questions = None, general_questions = None):
   
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
        response_initial = 'The answer is: '
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
        return {
            "answer" : response_initial,
            "analogous_questions": analogous_questions,
            "general_questions": general_questions,
            "similar_questions": [],
            "posibles_entities": []
        }
    else:
        print("Error en la solicitud a wikidata. " + response.text )
        return {
            "answer" : "Wikidata error. Please contact the administrator",
            "analogous_questions": [],
            "general_questions": [],
            "similar_questions": [],
            'posibles_entities': []
        }

def search_id_to_QAwiki(pregunta):

    qawiki_endpoint="http://query.qawiki.org/proxy/wdqs/bigdata/namespace/wdq/sparql"
    params = {
        "query": "SELECT ?q ?qLabel WHERE { ?q wdt:P1 wd:Q1 . SERVICE wikibase:label { bd:serviceParam wikibase:language 'en'. } }",
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
                    labels = []
                    for result in search_bindings:
                        labels.append(result['qLabel']['value'].lower())
                        if result['qLabel']['value'].lower() == pregunta:
                            print(((result['q']['value']).split("/"))[-1])
                            id = ((result['q']['value']).split("/"))[-1]
                    similar_questions = []
                    if id == None and len(labels) > 0:
                        similar_questions = find_similars(pregunta, labels)
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
