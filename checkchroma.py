
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from ingest import CHROMA_DB_DIR, COLLECTION_NAME

# ingest.py と同じ設定でChromaDBに接続
vectorstore = Chroma(
    persist_directory=CHROMA_DB_DIR,
    collection_name=COLLECTION_NAME,
    # EmbeddingFunctionは、DBから読み込むだけなら不要な場合もありますが、
    # 念のため指定しておくと確実です。
    embedding_function=OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11434")
)

print(f"コレクション内のチャンク総数: {vectorstore._collection.count()} 件")

# --- ここが本題 ---
# DB内のすべてのデータを取得 (チャンクが多い場合は時間がかかります)
# include で何を取得するか指定できます
results = vectorstore._collection.get(
    include=["metadatas", "documents"] 
    # "embeddings" を含めるとベクトル自体も取得できます
)

# 最初の5件だけ表示してみる
print("\n--- DB内のデータ（先頭5件） ---")
for i in range(min(5, len(results["ids"]))):
    print(f"■ チャンク {i+1} (ID: {results['ids'][i]})")
    print(f"  メタデータ: {results['metadatas'][i]}")
    print(f"  内容 (一部): {results['documents'][i][:150]}...") # 長すぎるので先頭150文字だけ表示
    print("-" * 20)