
from queries import parse_response, search_item_to_QAwiki, search_id_to_QAwiki
import pdb
from openIA import search_in_chatgpt

def similar_query(similar_question, original_question):
    response_QAwiki_id, similar_questions = search_id_to_QAwiki(similar_question)
    response_QAwiki_query = search_item_to_QAwiki(response_QAwiki_id)
    sparql_value_of_original_question = parse_similar_question(response_QAwiki_query["query"], similar_question ,original_question)
    response = parse_response(sparql_value_of_original_question)
    return response

def parse_similar_question(sparql_of_similar_question, similar_question ,original_question):
   pdb.set_trace()

   query_in_chatgtp = search_in_chatgpt(sparql_of_similar_question, similar_question, original_question)
   
   return query_in_chatgtp