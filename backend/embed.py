from sentence_transformers import SentenceTransformer, util
import torch

# 1. 임베딩 생성 모델 로드
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

def get_best_document_index(query, documents):
    # 2. 문서 임베딩 생성
    document_embeddings = model.encode(documents, convert_to_tensor=True)

    # 3. 쿼리 임베딩 생성
    query_embedding = model.encode(query, convert_to_tensor=True)

    # 4. 유사도 계산
    cosine_scores = util.pytorch_cos_sim(query_embedding, document_embeddings)

    # 5. 상위 문서 선택 (Top-k 방식)
    top_k = torch.topk(cosine_scores, k=1)  # 상위 1개의 문서를 선택

    return top_k.indices[0].item()

# 2. 문서 임베딩 생성
documents = ["냉동보관 하세요.", "맛있어요", "이 제품은 5000원이고, 냉동보관 제품입니다."]

# 3. 쿼리 임베딩 생성
query = "제조사 소비기한 영양정보 조리법 섭취방법 가격"

# print(get_best_document_index(query, documents))