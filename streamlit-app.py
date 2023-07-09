import streamlit as st

from google.cloud import aiplatform
from langchain.llms import VertexAI
from langchain import PromptTemplate, LLMChain
from google.auth import credentials
from google.oauth2 import service_account
from vertexai.preview.language_models import ChatModel, InputOutputTextPair
import vertexai
import json  # add this line
import toml
import os

isLocal = os.environ.get('islocal', False)
## You can uncomment the following to run locally
#isLocal = True

# Setup GCP vars
project_var = ""
secret_data = None
service_account_info = {}
if isLocal:
    if secret_data is None:
        secret_data = toml.load("../serviceAccount.toml")
    service_account_info = secret_data.get('credentials')
    project_var = secret_data.get("project")
    bucket_var = secret_data.get("staging_bucket")
    print(f"local service_account_info")
else:
    project_var = st.secrets["project"]
    bucket_var = st.secrets["staging_bucket"]
    service_account_info = {
        type: st.secrets["credentials"]["type"],
        project_id: st.secrets["credentials"]["project_id"],
        private_key_id: st.secrets["credentials"]["private_key_id"],
        private_key: st.secrets["credentials"]["private_key"],
        client_email: st.secrets["credentials"]["client_email"],
        client_id: st.secrets["credentials"]["client_id"],
        auth_uri: st.secrets["credentials"]["auth_uri"],
        token_uri: st.secrets["credentials"]["token_uri"],
        auth_provider_x509_cert_url: st.secrets["credentials"]["auth_provider_x509_cert_url"],
        client_x509_cert_url: st.secrets["credentials"]["client_x509_cert_url"],
        universe_domain: st.secrets["credentials"]["universe_domain"]
    }

my_credentials = service_account.Credentials.from_service_account_info(
    service_account_info
)

# Initialize Google AI Platform with project details and credentials
aiplatform.init(
    project=project_var,
    location='us-central1',
    staging_bucket=bucket_var,
    credentials=my_credentials,
)

vertexai.init(project=project_var, location='us-central1')

# App Background Image ---------------------
import base64
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"png"};base64,{encoded_string.decode()});
        background-size: cover;
    }}
    </style>
    """,
    unsafe_allow_html=True
    )
add_bg_from_local('A_robot_dinosaur_opacity.jpeg')

# Initial page
st.title('Tiny Dinos : LLM Thesaurus')
st.write("VertexAI hackathon : Team [link](https://lablab.ai/event/google-vertex-ai-hackathon/tiny-dinos)")
st.subheader("LLM Thesaurus")
st.text_input("Lookup", key="word", value="dinosaur")

# You can access the value at any point with:
word = st.session_state.word

from vertexai.preview.language_models import (ChatModel, InputOutputTextPair,
                                              TextEmbeddingModel,
                                              TextGenerationModel)

# Use chat-bison and remind it that it's a poet because we care about word similarities
chat_model = ChatModel.from_pretrained("chat-bison@001")
chat = chat_model.start_chat(
    context="I am a poet. You are my poet. I need to lookup words and return json formatted arrays.",
    examples=[
        InputOutputTextPair(
            input_text="example array",
            output_text="['best ever', 'best']",
        ),
    ],
    temperature=0.3,
)


# request 3 synonyms in an array
json_response = chat.send_message(f"in a flat json array format list three synonyms for the word {word}")
#print(f"-->{json_response}<--")

json_response_decorated = """{'synonyms':"""
json_response_decorated += f"{json_response}"
json_response_decorated += """}"""
json_response_decorated = json_response_decorated.replace("'", '"')

# list the synonyms
synonym_list = json.loads(json_response_decorated)
synonym_strings = synonym_list.get('synonyms')
synonym_strings_str = " ".join(synonym_strings)

# request a poem
request_a_poem = f"You are a poet, now create a short poem or haiku using the following words: {synonym_strings_str}"
poem_response = chat.send_message(request_a_poem)
if "I can't" in str(poem_response) or "I'm not a poet" in str(poem_response):
    # try again
    poem_response = chat.send_message(request_a_poem)

if "I can't" in str(poem_response) or "I'm not a poet" in str(poem_response):
    poem_response = " "

# does the LLM think it is a real word
is_it_a_real_word_response = chat.send_message(f"Respond with Yes or No. Do you think that the word {word}, is a real word?")



#--------------------------------------------
st.subheader(f"word: {word}")
st.code(f"synonyms : {synonym_strings}")
st.subheader(f"a poem using the synonyms")
st.code(f"{poem_response}")
st.subheader(f"does the LLM Thesaurus think this is a real word")
st.code(f"{is_it_a_real_word_response}")
