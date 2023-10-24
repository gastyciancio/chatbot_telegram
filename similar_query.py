
from queries import parse_response, search_item_to_QAwiki, search_id_to_QAwiki, search_label
import pdb,requests
from datetime import datetime
from openIA import search_in_chatgpt

def similar_query(similar_question, original_question):
    response_QAwiki_id, similar_questions = search_id_to_QAwiki(similar_question)
    response_QAwiki_query = search_item_to_QAwiki(response_QAwiki_id)

    sparql_value_of_original_question, error = parse_similar_question(response_QAwiki_query["query"], similar_question ,original_question)
    if error == None:
        return sparql_value_of_original_question, error
    else:
        return None, error

def parse_similar_question(sparql_of_similar_question, similar_question, original_question):

   response_in_chatgtp, error = search_in_chatgpt(sparql_of_similar_question, similar_question, original_question)

   if error == None:
       return search_in_wikipedia(response_in_chatgtp), None
   else:
       return None, error

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
