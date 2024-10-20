import requests
import json
import os

from embed import get_best_document_index

API_KEY = os.environ.get("SERPER_API_KEY")

default_required_info = "제조사 소비기한 영양정보 조리법 섭취방법 가격"

def get_document(product_name, query):
    search_query = query if query != "" else "정보"
    serper_response = search(product_name + search_query)
    if query != "" and serper_response.get("answerBox"):
        return serper_response["answerBox"]["snippet"]
    
    if serper_response.get("organic") is None:
        return ""
    
    title_and_snippets = []
    if serper_response.get("answerBox"):
        title_and_snippets.append({
            "text": serper_response["answerBox"]["title"] + serper_response["answerBox"]["snippet"],
            "link": serper_response["answerBox"]["link"]
        })

    for organic_result in serper_response.get("organic", [])[:5]:
        title_and_snippets.append({
            "text": organic_result["title"] + organic_result["snippet"],
            "link": organic_result["link"]
        })
    embed_query = query if query != "" else default_required_info

    best_document_index = get_best_document_index(product_name + embed_query, [item['text'] for item in title_and_snippets])
    
    best_document_link = title_and_snippets[best_document_index]['link']
    return scrape_website(best_document_link)

def scrape_website(url):
    api_url = "https://scrape.serper.dev"

    payload = json.dumps({
      "url": url
    })
    headers = {
      'X-API-KEY': API_KEY,
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", api_url, headers=headers, data=payload)
    response_json = json.loads(response.text)
    return response_json.get('text', '')

def search(query):
    url = "https://google.serper.dev/search"
    payload = json.dumps({
      "q": query,
      "gl": "kr",
      "hl": "ko",
    })
    headers = {
      'X-API-KEY': API_KEY,
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()