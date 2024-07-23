import boto3
import streamlit as st
import os
import uuid
import json


from User.PresentOutput import PresenterOutput

## s3_client
s3_client = boto3.client("s3")
BUCKET_NAME = os.getenv("BUCKET_NAME")

from dotenv import load_dotenv
load_dotenv()
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")

#streamlit elements
## Bedrock
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.chat_models import BedrockChat


## prompt and chain
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

## Text Splitter
from langchain.text_splitter import RecursiveCharacterTextSplitter

## Pdf Loader
from langchain_community.document_loaders import PyPDFLoader

## import FAISS
from langchain_community.vectorstores import FAISS


bedrock_client = boto3.client(service_name="bedrock-runtime",
                            region_name=aws_region,  
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)
bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client=bedrock_client)

folder_path="/tmp/"


#import next step
from User.PresentOutput import next_step



def get_unique_id():
    return str(uuid.uuid4())

def split_text(pages, chunk_size, chunk_overlap):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.split_documents(pages)
    return docs


def create_vector_store(request_id, documents):
    vectorstore_faiss=FAISS.from_documents(documents, bedrock_embeddings)
    file_name=f"{request_id}.bin"
    folder_path="/tmp/"
    vectorstore_faiss.save_local(index_name=file_name, folder_path=folder_path)

    ## upload to S3
    s3_client.upload_file(Filename=folder_path + "/" + file_name + ".faiss", Bucket=BUCKET_NAME, Key="my_faiss.faiss")
    s3_client.upload_file(Filename=folder_path + "/" + file_name + ".pkl", Bucket=BUCKET_NAME, Key="my_faiss.pkl")

    return True


## load index
def load_index():
    s3_client.download_file(Bucket=BUCKET_NAME, Key="my_faiss.faiss", Filename=f"{folder_path}my_faiss.faiss")
    s3_client.download_file(Bucket=BUCKET_NAME, Key="my_faiss.pkl", Filename=f"{folder_path}my_faiss.pkl")




def get_llm():
    llm=BedrockChat(model_id="anthropic.claude-3-5-sonnet-20240620-v1:0", client=bedrock_client,
                model_kwargs={    "max_tokens": 3048,
    "temperature": 0.2})
    return llm

def get_response(llm, vectorstore, question):
    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )


    prompt_template = """
    Human: You are an AI tasked with creating a presentation based on the given context. The presentation should be in the style and directions if given in: {question}.
    Generate a JSON structure for a presentation with the number of slides specified by the User. Each slide should have a title and content. 
    The content should be detailed. Line break between the bulletpoints.

    <context>
    {context}
    </context>

    Output the presentation as a JSON structure like this:
    {{
      "slides": [
        {{
          "title": "Slide Title",
          "content": " Small introductionary sentence to put in context related to the content of the slide, then At least 5 bullet points with all the relevent information to the Slide content goes here"
        }},
        ...
      ]
    }}

    Assistant: Start your answer directly, without preambles or commentary, with the JSON structure.
  

    """

    PROMPT = PromptTemplate(
        template=prompt_template, 
        input_variables=["context", "question"]
    )

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": 5}
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )
    response = qa({"query": question})

    #return json.loads(response['result'])
    
    answer=qa({"query":question})

    #return answer
    return answer['result']


def process_pdf(uploaded_file):
    request_id = get_unique_id()
    saved_file_name = f"{request_id}.pdf"
    with open(saved_file_name, mode="wb") as w:
        w.write(uploaded_file.getvalue())

    loader = PyPDFLoader(saved_file_name)
    pages = loader.load_and_split()
    splitted_docs = split_text(pages, 1000, 200)
    result = create_vector_store(request_id, splitted_docs)

    if result:
        load_index()
        try:
            faiss_index = FAISS.load_local(
                index_name="my_faiss",
                folder_path=folder_path,
                embeddings=bedrock_embeddings,
                allow_dangerous_deserialization=True
            )
            return faiss_index
        except Exception as e:
            st.error(f"Error loading index: {str(e)}")
            return None
    else:
        st.error("Error processing PDF. Please check logs.")
        return None
    

def generate_presentation(faiss_index, question):
    llm = get_llm()
    presentation_data = get_response(llm, faiss_index, question)
    return presentation_data


def main():
    st.write("This is The Presentator")
    
    if 'faiss_index' not in st.session_state:
        st.session_state.faiss_index = None
    
    if 'presentation_data' not in st.session_state:
        st.session_state.presentation_data = None

    uploaded_file = st.file_uploader("Upload your report", "pdf")

    if uploaded_file is not None and st.session_state.faiss_index is None:
        with st.spinner("Uploading and processing file..."):
            st.session_state.faiss_index = process_pdf(uploaded_file)

    if st.session_state.faiss_index is not None:
        question = st.text_input("Specify the style of your presentation and number of slides")
        if st.button("Generate Presentation"):
            with st.spinner("Generating presentation..."):
                st.session_state.presentation_data = generate_presentation(st.session_state.faiss_index, question)
                #st.success("Presentation generated successfully!")

    if st.session_state.presentation_data is not None:
        PresenterOutput(st.session_state.presentation_data)



  

if __name__ == "__main__":
    main()







