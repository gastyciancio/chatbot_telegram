import requests
from datetime import datetime
import pdb

def search(text):
    response_QAwiki_id = search_id_to_QAwiki(text)
    if response_QAwiki_id == None:
        return 'There is not information about what you search'
    else:
        response_QAwiki_query = search_item_to_QAwiki(response_QAwiki_id)
        if response_QAwiki_query["query"] == None:
            return 'There is not result for what you search'
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
        results = data["results"]["bindings"]
        response_initial = 'The answer is: '
        for result in results:
            if 'obj' in result and result["obj"]["type"] == 'literal':
                response_final = result["obj"]["value"]
                print(f"Valor de wikidata: {response_final}")
                try:
                    # Intenta convertir la cadena en un objeto datetime si es una fecha
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
            "general_questions": general_questions
        }
    else:
        print("Error en la solicitud a wikidata. " + response.text )
        return {
            "answer" : "Wikidata error. Please contact the administrator",
            "analogous_questions": [],
            "general_questions": []
        }

def search_id_to_QAwiki(pregunta):

    qawiki_endpoint="http://qawiki.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "search": pregunta,
        "language": "es"
    }

    try:
        response = requests.get(qawiki_endpoint, params=params)

        if response.status_code == 200:
            data = response.json()
            search_results = data.get("search", [])

            if search_results:
                print(search_results[0]['id'])
                return search_results[0]['id']
            else:
                print("No se encontraron resultados para la busqueda")
                return None
    except:
        return None

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