from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import ConversationalRetrievalChain

# Define the prompt templates
_template = """Given the following conversation and a follow-up question, rephrase the follow-up question to be a standalone question.
You can assume the question is about the uploaded document.

Chat History:
{chat_history}
Follow-Up Input: {question}
Standalone question:"""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

qa_template = """You are an AI assistant for answering questions about the uploaded document.
You are given the following extracted parts of a long document and a question. Provide a conversational answer.
If you don't know the answer, just say "Hmm, I'm not sure." Don't try to make up an answer.
If the question is not about the uploaded document, politely inform them that you are tuned to only answer questions about the uploaded document.
Question: {question}
=========
{context}
=========
Answer in Markdown:"""
QA_PROMPT = PromptTemplate(template=qa_template, input_variables=["question", "context"])

# Function to set up the conversational chain and run a query
def get_chain(vectorstore):
    # Initialize the OpenAI LLM
    llm = OpenAI(api_key="", temperature=0)

    # Create the ConversationalRetrievalChain
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        condense_question_prompt=CONDENSE_QUESTION_PROMPT,
        return_source_documents=True
    )

    return chain


