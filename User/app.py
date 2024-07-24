import boto3
import streamlit as st
import os
import uuid
import json
import re
import json



from PresentOutput import PresenterOutput

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
                model_kwargs={    "max_tokens": 2048,
    "temperature": 0.3})
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
    Generate a JSON structure for a presentation with the number of slides specified by the User. Each slide should have a title, content, and a script. 
    The content should be detailed and follow the logical order of the original document. 
    

    <context>
    {context}
    </context>

    Output the presentation as a JSON structure like this:
    {{
      "slides": [
        {{
          "title": "Slide Title",
          "content": " 5 bullet points with line breaks in between with all the relevant information to the Slide content goes here. Line break with <br> instead of "\n" in between the bullet points is necessary.",
          "script": "Detailed script for presenting this slide, expanding on the bullet points and providing additional context."
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

    answer = qa({"query": question})



    return answer['result']

def extract_slides(text):
    # Pattern to match each slide
    slide_pattern = r'\{\s*"title":\s*"(.+?)",\s*"content":\s*"(.+?)",\s*"script":\s*"(.+?)"\s*\}'
    
    # Find all matches
    slides = re.findall(slide_pattern, text, re.DOTALL)
    
    # Convert matches to dictionaries
    slide_dicts = [
        {
            "title": title.strip(),
            "content": content.strip(),
            "script": script.strip()
        }
        for title, content, script in slides
    ]
    
    return {"slides": slide_dicts}

def clean_json_string(json_string):
    # Remove any leading or trailing whitespace
    json_string = json_string.strip()
    
    # Ensure the string starts and ends with curly braces
    if not json_string.startswith('{'):
        json_string = '{' + json_string
    if not json_string.endswith('}'):
        json_string = json_string + '}'
    
    # Replace any single quotes with double quotes
    json_string = json_string.replace("'", '"')
    
    # Remove any newline characters within string values
    json_string = re.sub(r'(?<!\\)\\n', ' ', json_string)
    
    # Remove any unescaped newline characters
    json_string = json_string.replace('\n', '')
    
    # Fix any unquoted keys
    json_string = re.sub(r'(\w+)(?=\s*:)', r'"\1"', json_string)
    
    # Attempt to fix trailing commas
    json_string = re.sub(r',\s*}', '}', json_string)
    json_string = re.sub(r',\s*]', ']', json_string)
    
    return json_string

def parse_json_safely(json_string):
    try:
        # First, try to parse the JSON as-is
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        st.write(f"Initial JSON parsing failed: {str(e)}")
        st.write("Attempting to clean and parse JSON...")
        
        # If that fails, try to clean the JSON string
        cleaned_json = clean_json_string(json_string)
        try:
            # Try to parse the cleaned JSON
            return json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            st.error(f"Error parsing cleaned JSON: {str(e)}")
            st.text("Cleaned JSON:")
            st.code(cleaned_json)
            return None


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
    st.set_page_config(layout="wide")
    col1, col2, _ = st.columns([1,2, 1])
    
    with col1:
        pass
    
    if 'faiss_index' not in st.session_state:
        st.session_state.faiss_index = None
    
    if 'presentation_data' not in st.session_state:
        st.session_state.presentation_data = None
    with col2:
        st.write("This is The Presentator")
        uploaded_file = st.file_uploader("Upload your report", "pdf")

        if uploaded_file is not None and st.session_state.faiss_index is None:
            with st.spinner("Uploading and processing file..."):
                st.session_state.faiss_index = process_pdf(uploaded_file)

        if st.session_state.faiss_index is not None:
            question = st.text_input("Specify the style of your presentation and number of slides")
            if st.button("Generate Presentation"):
                
                with st.spinner("Generating presentation..."):
                    raw_presentation_data = generate_presentation(st.session_state.faiss_index, question)
                    st.session_state.presentation_data = extract_slides(raw_presentation_data)
                    
                    if not st.session_state.presentation_data["slides"]:
                        st.error("Failed to extract slide information")
                        st.text("Raw data:")
                        st.code(raw_presentation_data)

    if st.session_state.presentation_data is not None and st.session_state.presentation_data["slides"]:
        PresenterOutput(st.session_state.presentation_data)

if __name__ == "__main__":
    main()




