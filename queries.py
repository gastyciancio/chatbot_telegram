import requests

def search(text):
    if (text[0] != '¿'):
        return 'La pregunta debe empezar con un ¿'
    else:
        response_QAwiki_id = search_id_to_QAwiki(text)
        if response_QAwiki_id == None:
            return 'No hay informacion sobre lo que se busca'
        else:
            response_QAwiki_query = search_item_to_QAwiki(response_QAwiki_id)
            response = parse_response(response_QAwiki_query)
            return response
    
def parse_response(query_to_wikidata):
    if query_to_wikidata == None:
        return 'No se encontraron resultados para la busqueda'
    else:
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
            response_initial = ''
            for result in results:
                if 'obj' in result and result["obj"]["type"] == 'literal':
                    response_final = result["obj"]["value"]
                    print(f"Valor de wikidata: {response_final}")
                    response_initial = response_initial + response_final + '. '
                elif 'sbj' in result and result["sbj"]["type"] == 'uri':
                    id = (result["sbj"]["value"].split('/'))[-1]
                    response_final = search_item_to_wikidata(id)
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
                response_initial = response_initial + "No se encontraron datos de Wikidata" + '. '
            return response_initial

        else:
            print("Error en la solicitud a wikidata. " + response.text )
            return "Error en la solicitud a wikidata. Pongase en contacto con el administrador"

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
                for claim in query_claim:
                    mainsnak = claim.get("mainsnak", {})
                    if "datavalue" in mainsnak:
                        datavalue = mainsnak["datavalue"]
                        if "value" in datavalue:
                            return datavalue["value"]
                        else:
                            return None
                    else:
                        return None
            else:
                return None
        else:       
            return None
    except:
        return None

def search_item_to_wikidata(id):
    endpoint="http://wikidata.org/w/api.php"
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