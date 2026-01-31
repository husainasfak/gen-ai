from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

# embedding model

embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-large"
)


vector_store = QdrantVectorStore.from_existing_collection(
    embedding=embeddings_model,
    url="http://localhost:6333",
    collection_name="pdf_guide_collection"
)


# User input
user_query = input("Enter your question: ")

# similarity search
search_result = vector_store.similarity_search(query=user_query)

context = "\n".join(f"Page Content: {result.page_content}\n Page Number:{result.metadata['page_label']}\n File location: {result.metadata['source']}" for result in search_result)

SYSTEM_PROMPT = """You are an AI assistant that helps people find information from a set of documents.
Use the following pieces of context to answer the question at the end.

You should only provide answers that are supported by the context below. If you don't know the answer, just say that you don't know. Do not try to make up an answer.

context:
{context}
"""


openai_client = OpenAI()


response  = openai_client.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
        {"role": "user", "content": user_query},
    ],
)


print("Answer:")
print(response.choices[0].message.content)