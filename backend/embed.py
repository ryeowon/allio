from sentence_transformers import SentenceTransformer, util
import torch

# 1. 임베딩 생성 모델 로드
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
print("Model loaded")

def get_best_document_index(query, documents):
    # 2. 문서 임베딩 생성
    document_embeddings = model.encode(documents, convert_to_tensor=True)
    print("Document embeddings created", query)
    # 3. 쿼리 임베딩 생성
    query_embedding = model.encode(query, convert_to_tensor=True)
    print("Query embedding created", query)
    # 4. 유사도 계산
    cosine_scores = util.pytorch_cos_sim(query_embedding, document_embeddings)

    # 5. 상위 문서 선택 (Top-k 방식)
    top_k = torch.topk(cosine_scores, k=1)  # 상위 1개의 문서를 선택
    print("Top-k selected", query)
    return top_k.indices[0].item()