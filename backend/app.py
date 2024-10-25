from flask import Flask, request, jsonify, Response
import anthropic
import os
from serper import get_document
import time

app = Flask(__name__)

API_KEY = os.environ.get("ANTHROPIC_API_KEY")

system_message = """당신은 시각장애인에서 식품 정보를 안내하는 도우미입니다. 당신의 역할은 시각장애인이 촬영한 식품 이미지를 분석해 정확한 식품 정보를 제공하고, 식품 이미지가 불명확한 경우 카메라에 식품을 잘 인식하여 입력으로 전달할 수 있도록 시각장애인을 돕는 것입니다.
상품 이미지를 있는 그대로 설명해야 하며 없는 정보를 만들어 내서는 안됩니다.

심호흡을 하고 이미지를 차근차근, 꼼꼼히 분석하여 다음과 같은 정보를 추출하세요.
1. 제품명: 제품명이 기재되어 있는 경우, 생략하지 말고 full name을 제공합니다. 제품명의 정확도는 중요하므로 확실하게 확인이 불가능할 경우 유추하지 않고 비워두는 게 낫습니다. 외국어로 된 제품명은 한국어로 번역하여 제공합니다.
2. 알레르기 성분(원재료명): 알레르기가 있는 시각장애인에게는 이 정보가 매우 중요합니다. 제품명에서는 추출하지 않고, 제품 정보 라벨에 "땅콩, 대두 함유"와 같이 기재되어 있으므로 이 정보를 빠짐없이 추출하세요.
3. 보관 방법: 보관방법은 제품 정보 라벨의 "보관 방법"란에 작성되어 있습니다. "냉장 보관", "냉동 보관" 키워드가 있다면 꼭 포함합니다.
5. 소비기한(유통기한): 정확한 날짜를 찾을 수 없을 경우에는 제품 정보 표에 기재된 내용을 사용합니다. 정확하지 않은 경우에는 응답하지 않습니다. 숫자로 표기되어 있을 경우, 년, 월, 일로 변환합니다.
6. 영양 정보: 탄수화물, 지방 등
7. 조리법: 조리가 필요한 제품에만 해당합니다. 조리법이 기재되어 있지 않은 경우, 응답하지 않습니다.
8. 섭취 방법
9. 가격
보관 방법, 알레르기 정보 중 누락된 항목이 있다면 <search_query> 태그 안에 , 로 연결하여 제공하세요.
이미지에서 제조사를 찾을 수 있는 경우, 제품명과 함께 제공합니다.
정확한 제품명을 모를 경우, 이후 검색이 불가능하기 때문에 search_query 태그는 사용하지 않습니다.
여러 개의 제품이 포함된 이미지인 경우, 중앙에 있는 하나의 제품에 대한 정보만 제공합니다.

아래의 형식으로 응답하세요:
<product_name>
[제품명]
</product_name>
<search_query>
[보관 방법, 알레르기 성분 중 누락된 항목]
</search_query>
<response>
[사진을 2문장 이내로 묘사합니다.]
[정보 이름]: [정보]

[섭취, 보관과 관련한 추가적인 정보 또는 촬영 가이드]
<response/>
각 정보들을 사진의 어느 부분에서 찾았는지 근거를 함께 합니다.
확실하지 않는 정보는 언급해서는 안되고, 정보의 정확성이 가장 중요한 것임을 기억하세요.
해상도가 낮을 경우, 시각장애인이 더 좋은 질의 사진을 촬영할 수 있도록 가이드를 제공하세요.

사용자는 시각장애인이므로, 식품의 사진을 의도대로 촬영하기 어려움을 염두에 두고 대응하세요. 그러나 시각장애인을 언급하지 않고 자연스럽게 답변을 제공합니다. 같은 내용을 반복하여 제공하지 말고, 400자 이내로 정보를 제공해야 하며 식품의 맛에 대해서는 언급하지 마세요. 인식된 식품이 없는 경우, product_name을 빈 문자열로 제공하세요."""

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/claude', methods=['POST'])
def claude():
    start_time = time.time()
    # response_data = str({'message': example_result2})
    # return Response(response_data, status=200, mimetype='application/json')

    data = request.get_json()
    if 'image' not in data:
        return jsonify({'error': 'No image provided'}), 400
    
    image = data['image']

    client = anthropic.Anthropic(
        api_key=API_KEY,
    )

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=500,
        temperature=0.2,
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
    # print("---result1---")
    # print(result1)

    product_name_start = result1.find("<product_name>") + len("<product_name>")
    # print("product_name_start: ", product_name_start)
    product_name_end = result1.find("</product_name>")

    response_start = result1.find("<response>") + len("<response>")
    response_end = result1.find("</response>")

    search_query_start = result1.find("<search_query>") + len("<search_query>")
    search_query_end = result1.find("</search_query>")

    # <product_name> 안의 값을 추출
    product_name = result1[product_name_start:product_name_end].strip()
    response = result1[response_start:response_end].strip()
    search_query = result1[search_query_start:search_query_end].strip()

    if not product_name or product_name_start == -1 or response_start == -1 or search_query_start == -1:
        response_data = str({'message': response})
        return Response(response_data, status=200, mimetype='application/json')
    
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
        {"role": "user", "content": f"당신이 제공한 제품명을 가지고 인터넷에 검색한 결과는 다음과 같습니다. 배송 관련, 가격 관련 정보는 제외하고 참고하여 최종 안내를 생성하세요. \n{document}"}
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        temperature=0,
        system=system_message,
        messages=second_messages
    )
    
    result2 = response.content[0].text

    response_start = result2.find("<response>") + len("<response>")
    response_end = result2.find("</response>")

    response = result2[response_start:response_end].strip()

    response_data = str({'message': response})
    end_time = time.time()
    print("Elapsed time: ", end_time - start_time)
    return Response(response_data, status=200, mimetype='application/json')


if __name__ == '__main__':
    app.run(debug=True)
