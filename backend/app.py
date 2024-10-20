from flask import Flask, request, jsonify
import anthropic
import os
from serper import get_document

app = Flask(__name__)

API_KEY = os.environ.get("ANTHROPIC_API_KEY")

system_message = "당신은 시각장애인에서 식품 정보를 안내하는\b 도우미입니다. 당신의 역할은 시각장애인이 촬영한 식품 이미지를 분석해 정확한 식품 정보를 제공하고, 식품 이미지가 불명확한 경우 카메라에 식품을 잘 인식하여 입력으로 전달할 수 있도록 시각장애인을 돕는 것입니다.\n상품 이미지를 있는 그대로 설명해야 하며 없는 정보를 만들어 내서는 안됩니다.\n\n심호흡을 하고 이미지를 차근차근, 꼼꼼히 분석하여 다음과 같은 정보를 추출하세요. \n1. 제품명: 정확한 제품명이 기재되어 있는 경우, 생략하지 말고 full name을 제공합니다.\n2. \b제조사\n3. 알레르기 성분(원재료명): 알레르기가 있는 시각장애인에게는 이 정보가 매우 중요합니다. 제품명에서는 추출하지 않고, 제품 정보 라벨에 \"땅콩, 대두 함유\"와 같이 기재되어 있으므로 이 정보를 빠짐없이 추출하세요.\n4. 보관 방법: 보관방법은 제품 정보 라벨의 \"보관 방법\"란에 작성되어 있습니다. \"냉장 보관\", \"냉동 보관\" 키워드가 있다면 꼭 포함합니다.\n5. 소비기한(유통기한): 정확한 날짜를 찾을 수 없을 경우에는 제품 정보 표에 기재된 내용을 사용합니다. 정확하지 않은 경우에는 응답하지 않습니다. 숫자로 표기되어 있을 경우, 년, 월, 일로 변환합니다.\n6. 영양 정보\n7. 조리법\n8. 섭취 방법\n9. 가격\n\n보관 방법, 알레르기 정보 중 누락된 항목이 있다면 <search_query> 태그 안에 , 로 연결하여 제공하세요.\n\n찾을 수 있는 정보만 아래의 형식으로 응답하세요:\n<product_name>\n[제품명, 찾을 수 없는 경우 비워둠]\n</product_name>\n<search_query>\n[보관 방법, 알레르기 성분 중 누락된 항목]\n</search_query>\n<response>\n[사진을 2문장 이내로 묘사합니다.]\n[정보 이름]: [정보]\n\n[필요할 경우, 추가적인 코멘트나 지시 또는 이미지에 표시된 중요한 정보]\n<response/>\n각 정보들을 사진을 어느 부분에서 찾았는지 근거를 함께 제시하세요.\n확실하지 않는 정보는 언급해서는 안되고, 정보의 정확성이 가장 중요한 것임을 기억하세요.\n해상도가 낮을 경우, 시각장애인이 더 좋은 질의 사진을 촬영할 수 있도록 가이드를 제공하세요.\n\n사용자는 시각장애인이므로, 식품의 사진을 의도대로 촬영하기 어려움을 염두에 두고 대응하세요."

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/claude', methods=['POST'])
def claude():
    data = request.get_json()
    if 'image' not in data:
        return jsonify({'error': 'No image provided'}), 400
    
    image = data['image']

    client = anthropic.Anthropic(
        api_key=API_KEY,
    )

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        temperature=0,
        system=system_message,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image
                        }
                    }
                ]
            }
        ]
    )

    result1 = response.content[0].text

    product_name_start = result1.find("<product_name>") + len("<product_name>")
    product_name_end = result1.find("</product_name>")

    response_start = result1.find("<response>") + len("<response>")
    response_end = result1.find("</response>")

    search_query_start = result1.find("<search_query>") + len("<search_query>")
    search_query_end = result1.find("</search_query>")

    # <product_name> 안의 값을 추출
    product_name = result1[product_name_start:product_name_end].strip()
    response = result1[response_start:response_end].strip()
    search_query = result1[search_query_start:search_query_end].strip()

    if not product_name:
        return jsonify({'message': response}), 400
    
    query_list = []
    print("search_query: ", search_query)
    if search_query:
       query_list = [query.strip() for query in search_query.split(",")] # 보관 방법, 알레르기 성분

    query_list.append('')

    document = ""

    for query in query_list:
        result = get_document(product_name, query)
        print("----" + query + "----")
        print(result)
        document += result + "\n"

    second_messages = [
        {"role": "assistant", "content": result1},
        {"role": "user", "content": f"당신이 제공한 제품명을 가지고 인터넷에 검색한 결과는 다음과 같습니다. 이를 참고하여 최종 안내를 생성하세요. \n{document}"}
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        temperature=0,
        system=system_message,
        messages=second_messages
    )
    
    result2 = response.content[0].text
    
    print("result2: ", result2)
    return jsonify({'message': result2}), 200


if __name__ == '__main__':
    app.run(debug=True)
