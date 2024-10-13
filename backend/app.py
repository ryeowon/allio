from flask import Flask, request, jsonify
import anthropic
import os

app = Flask(__name__)

API_KEY = os.environ.get("ANTHROPIC_API_KEY")

@app.route('/claude', methods=['POST'])
def claude():
    data = request.get_json()
    if 'image' not in data:
        return jsonify({'error': 'No image provided'}), 400
    
    image = data['image']

    client = anthropic.Anthropic(
        api_key=API_KEY,
    )

    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        temperature=0,
        system="당신은 시각장애인에서 식품 정보를 안내하는\b 도우미입니다. 당신의 역할은 입력으로 받은 식품 이미지를 분석해 정확한 식품 정보를 제공하고, 카메라에 식품을 잘 인식하여 입력으로 전달할 수 있도록 시각장애인을 돕는 일입니다.\n상품 이미지를 있는 그대로 설명해야 하며 없는 정보를 만들어 내서는 안됩니다.\n\n심호흡을 하고 이미지를 차근차근, 꼼꼼히 분석하여 다음과 같은 정보를 추출하세요. \n1. 제품명: 정확한 제품명이 기재되어 있는 경우, 생략하지 말고 full name을 제공합니다.\n2. \b제조사\n3. 알레르기 정보(원재료명): 알레르기가 있는 시각장애인에게는 이 정보가 매우 중요합니다. 제품명에서는 추출하지 않고, 제품 정보 라벨에 \"땅콩, 대두 함유\"와 같이 기재되어 있으므로 이 정보를 빠짐없이 추출하세요.\n4. 보관 방법: 보관방법은 제품 정보 라벨의 \"보관 방법\"란에 작성되어 있습니다. \"냉장 보관\", \"냉동 보관\" 키워드가 있다면 꼭 포함합니다.\n5. 소비기한(유통기한): 정확한 날짜를 찾을 수 없을 경우에는 제품 정보 표에 기재된 내용을 사용합니다. 정확하지 않은 경우에는 응답하지 않습니다. 숫자로 표기되어 있을 경우, 년, 월, 일로 변환합니다.\n6. 영양 정보\n7. 조리법\n\n제품 정보 라벨에서 위의 정보를 모두 찾을 수 없다면, 수평을 유지하여 더 가까이에서 제품을 촬영하도록 요청합니다.\n\n찾을 수 있는 정보만 아래의 형식으로 응답하세요:\n<response>\n[사진을 2문장 이내로 묘사합니다.]\n[정보 이름]: [정보]\n\n[필요할 경우, 추가적인 코멘트나 지시 또는 이미지에 표시된 중요한 정보]\n<response/>\n각 정보들을 사진을 어느 부분에서 찾았는지 근거를 함께 제시하세요.\n확실하지 않는 정보는 언급해서는 안되고, 정보의 정확성이 가장 중요한 것임을 기억하세요.\n해상도가 낮을 경우, 시각장애인이 더 좋은 질의 사진을 촬영할 수 있도록 가이드를 제공하세요.\n\n항상 사용자가 시각장애인임을 고려하여 응답할 것을 명심하세요. ",
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

    print(message)
    
    return jsonify({'message': 'Success'}), 200


if __name__ == '__main__':
    app.run(debug=True)
