from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.docstore import InMemoryDocstore
import faiss
import pickle
import os

# Function to extract text from a PDF using PyPDF2
def extract_text_with_pypdf2(file_path):
    reader = PdfReader(file_path)
    text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)
    return "\n".join(text)

def embed_doc(filename, pickle_file='vectorstore.pkl'):
    if not os.path.isfile(filename):
        print(f"File '{filename}' does not exist.")
        return

    try:
        # Extract text from the PDF using PyPDF2
        extracted_text = extract_text_with_pypdf2(filename)
        if not extracted_text:
            print(f"No text found in '{filename}'.")
            return

        # Create Document objects with the extracted text
        raw_documents = [Document(page_content=extracted_text, metadata={"source": filename})]

        # Split text into chunks for vectorization
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len
        )
        documents = text_splitter.split_documents(raw_documents)
        print(f"Split into {len(documents)} chunks")

        # Create OpenAI embeddings and generate a FAISS index
        api_key = ""
        embeddings = OpenAIEmbeddings(api_key=api_key)
        vectorstore = FAISS.from_documents(documents, embeddings)
        print("Embedding and vector store created")

        # Serialize the FAISS index and document store
        index_bytes = faiss.serialize_index(vectorstore.index)
        #docstore = {k: documents[int(v)] for k, v in vectorstore.index_to_docstore_id.items()}
        docstore = {key: value for key, value in vectorstore.docstore._dict.items()}  # Adjust for public API
   
        # Create a pickle-able dictionary to store both the FAISS index and metadata
        pickle_data = {
            'index': index_bytes,
            'docstore': docstore,
            'index_to_docstore_id': vectorstore.index_to_docstore_id
        }

        # Save the combined data as a pickle file
        with open(pickle_file, "wb") as f:
            pickle.dump(pickle_data, f)
        print(f"Vectorstore saved to '{pickle_file}'")

    except Exception as e:
        print(f"Error during embedding or vectorization: {e}")

# Load the pickled FAISS index and reconstruct the vector store
def load_pickled_vectorstore(pickle_file, api_key):
    try:
        # Load the data from the pickle file
        with open(pickle_file, "rb") as f:
            data = pickle.load(f)

        # Deserialize the FAISS index
        index = faiss.deserialize_index(data['index'])

        # Create an InMemoryDocstore
        docstore = InMemoryDocstore(data['docstore'])

        # Reconstruct the FAISS vector store
        embeddings = OpenAIEmbeddings(api_key=api_key)
        vectorstore = FAISS(index=index, docstore=docstore, index_to_docstore_id=data['index_to_docstore_id'], embedding_function=embeddings)
        return vectorstore
    except Exception as e:
        print(f"Error loading vector store: {e}")
        return None
