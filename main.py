import os
from pyexpat import model
import uuid
from urllib.parse import urlencode, urljoin
from azure.eventgrid import EventGridEvent, SystemEventNames
import requests
from flask import Flask, Response, request, json
from logging import INFO
import re
from pprint import pprint
from azure.communication.callautomation import (
    CallAutomationClient,
    PhoneNumberIdentifier,
    RecognizeInputType,
    TextSource
)
from azure.core.messaging import CloudEvent
import openai

from openai.api_resources import (
    ChatCompletion
)

# Your ACS resource connection string
ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")

# Cognitive service endpoint
COGNITIVE_SERVICE_ENDPOINT = os.getenv("COGNITIVE_SERVICE_ENDPOINT")

# Cognitive service endpoint
AZURE_OPENAI_SERVICE_KEY = os.getenv("AZURE_OPENAI_SERVICE_KEY")

# Azure Open AI Deployment Model
AZURE_OPENAI_DEPLOYMENT_MODEL = "gpt-4-turbo-preview"
# AZURE_OPENAI_DEPLOYMENT_MODEL = "gpt-3.5-turbo"

# Agent Phone Number
AGENT_PHONE_NUMBER = os.getenv("AGENT_PHONE_NUMBER")

# Callback events URI to handle callback events.
CALLBACK_URI_HOST = "https://start-hack-production.up.railway.app"
CALLBACK_EVENTS_URI = CALLBACK_URI_HOST + "/api/callbacks"

languages = {}

bing_subscription_key = os.environ['BING_SEARCH_V7_SUBSCRIPTION_KEY']
bing_endpoint = os.environ['BING_SEARCH_V7_ENDPOINT'] + "/v7.0/search"

voices = {
    "DE": "de-CH-LeniNeural",
    "EN": "en-US-NancyNeural"
}

ANSWER_PROMPT_SYSTEM_TEMPLATE = {
    "DE": """"
    Du bist ein hilfreicher Assistent des Kantons St.Gallen und führst ein Telefonat mit einem Bürger.
    Deine Aufgabe ist es, Anrufende zu unterstützen. Antworte wie ein Mensch es tun würde, mit angemessenen Sprechpausen.
    Antworte kompakt, möglichst unter 200 Zeichen.
    SCHREIBE AUF KEINEN FALL MEHR ALS 350 ZEICHEN.
    Gib dein besten, Fragen sinnvoll zu beantworten. Bedenke, dass dein Gegenüber eine Spracherkennung verwendet und daher einige Wörter möglicherweise falsch transkribiert sein könnten.
    Antworte auf Deutsch.
    Sobald eine Zuordnung möglich ist, leite den Anrufer weiter.
    Dies ist oft ebenfalls bereits nach der ersten Nachricht möglich. WICHTIG: Frage dennoch in jedem Fall explizit um Erlaubnis bevor du weiterleitest!
    Um den Nutzer weiterzuleiten, gib statt einer Antwort nur das folgende JSON mit der ausgewählten Stelle und Nummer zurück:
    {
        'stelle': '<name der stelle>',
        'nummer': '<telefonnummer>'
    }

    Die folgenden Stellen (inkl. Telefonnummern) gibt es:
    - Steueramt - +491774739344
    - Ausweisstelle - +491774739344
    - Amt für Soziales - +491774739344
    - Amt für Arbeitsmarkt, Arbeitsbedingungen - +491774739344
    - Regionalstelle für den Ort Wil - +491774739344
    - Quellensteuern - +491774739344
    - Grundstückgewinnsteuer - +491774739344
    - Ausländerabteilung - +491774739344
    """,

    "EN": """
        You are a helpful assistant from the Canton of St.Gallen.
    Your job is to support callers. Answer as a human would, with appropriate pauses in speech.
    Answer compactly, preferably under 200 characters.
    Do your best to answer questions sensibly. Remember the user is using a transcription tool so some words might be a bit off.
    Answer in English.
    DO NOT IN ANY CASE WRITE MORE THAN 350 CHARACTERS.
    If you realize that the user has a specific request that one of the posts below can help with, redirect them.
    This is often also possible after the first message. IMPORTANT: Always make sure to explicitly ask for consent before redirecting anyway!
    To forward the user, simply return the following JSON with the selected location and number instead of a reply:
    {
        'stelle': '<name of the job>',
        'nummer': '<phone number>'
    }

    The following digits are available:
    - Tax office - +491774739344
    - Identity card office - +491774739344
    - Office for Social Affairs - +491774739344
    - office for Labor Market and Working Conditions - +491774739344
    - regional office for Wil - +491774739344
    - withholding tax office - +491774739344
    - office for property gains tax- +491774739344
    - Foreigners Department - +491774739344
    """
}

HELLO_PROMPT = {
    "DE": "Willkomme! Ich bin Heidi, die virtuelle Assistentin vom Kanton Sankt Galle. Bitte beschreibe kurz dein Anliegen, damit i helfe kann?",
    "EN": "Welcome! I am Heidi, the virtual assistant of the Canton Sankt Gallen. Please give a short description of your problem so I can help you."
}
TIMEOUT_SILENCE_PROMPT = {
    "DE": "Entschuldigung, i het si nöd chöne ghöre. Sind Sie no do?",
    "EN": "Sorry, I couldn't hear you. Are you still there?"
}
GOODBYE_PROMPT = {
    "DE": "Dank für ihre Aaruf. Uf Wiedergseh!",
    "EN": "Thanks for your call. Goodbye!"
}
CONNECT_AGENT_PROMPT = "Tuet mir leid, i cha Ihne grad nöd wiiterhelfe. Bitte bliibe Sie i de Leitig, i vobind Sie mitme Mitarbeiter."
CALLTRANSFER_FAILURE_PROMPT = "Tuet mir leid, es stoht grad kei Mitarbeiter zur Vofüegig. De nöchscht freii Mitarbeiter wird sich i Chürzi bi Ihne melde."
AGENT_PHONE_NUMBER_EMPTY_PROMPT = "Tuet mir leid, mir erhalte im Moment sehr viel Arüef. De nöchscht frei Mitarbeiter wird sich um Sie kümmere."
END_CALL_PHRASE_TO_CONNECT_AGENT_INCOMPLETE = {
    "DE": "Bitte bliibed Sie i de Leitig, i vobind Sie mit da",
    "EN": "Please stay in line, I will connect you to the."
}
detection_language = {
    "EN": "en-US",
    "DE": "de-CH"
}

TRANSFER_FAILED_CONTEXT = "TransferFailed"
CONNECT_AGENT_CONTEXT = "ConnectAgent"
GOODBYE_CONTEXT = "Goodbye"

CHAT_RESPONSE_EXTRACT_PATTERN = r"\s*Content:(.*)\s*Score:(.*\d+)\s*Intent:(.*)\s*Category:(.*)"

call_automation_client = CallAutomationClient.from_connection_string(ACS_CONNECTION_STRING)

recording_id = None
recording_chunks_location = []
max_retry = 2

openai.api_key = AZURE_OPENAI_SERVICE_KEY

app = Flask(__name__)

chat_histories = {}


def get_chat_completions_async(system_prompt, user_prompt, caller_id=None):
    openai.api_key = AZURE_OPENAI_SERVICE_KEY

    search_terms = ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "system",
                                                                           "content": "You are a helpful assistant trained to suggest an overarching search word for a conversation. Below, you will be provided with the chat. Return a single word that is relevant to the topic at hand. If there is no chat provided, search for 'St.Gallen'."},
                                                                          {"role": "user",
                                                                           "content": f"Here is the newest message: {user_prompt}\nand the full chat:\n{json.dumps(chat_histories)}"}])['choices'][0]['message']['content']
    app.logger.info(f"searching for context: {search_terms}")
    query = f"{search_terms} site:https://sg.ch"
    params = {'q': query, 'mkt': "de-CH", 'responseFilter': 'webpages'}
    headers = {'Ocp-Apim-Subscription-Key': bing_subscription_key}
    search_context = ""
    try:
        response = requests.get(bing_endpoint, headers=headers, params=params)
        search_context = extract_snippets(response.json())
        app.logger.info(f"Got snippets: {search_context}")
    except Exception as ex:
        app.logger.info("failed to websearch")

    if search_context != "":
        system_prompt = system_prompt \
                        + "\nHere is some context from the internet that may be helpful in answering any questions:\n" \
                        + (';'.join(str(e) for e in search_context))
    app.logger.info(f"System prompt now: {system_prompt}")

    if caller_id is not None:
        chat_history = chat_histories.get(caller_id, [])

        if chat_history:
            chat_history[0] = {"role": "system", "content": system_prompt}
        else:
            chat_history.insert(0, {"role": "system", "content": system_prompt})

        chat_history.append({"role": "user", "content": user_prompt})
        chat_histories[caller_id] = chat_history

    else:
        chat_history = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

    app.logger.info(f"Creating generation: {json.dumps(chat_history)}")

    # Use the chat history in the chat completions request
    response = ChatCompletion.create(model=AZURE_OPENAI_DEPLOYMENT_MODEL,
                                     messages=chat_history,
                                     max_tokens=1000)

    # Extract the response content
    if response is not None:
        response_content = response['choices'][0]['message']['content']
    else:
        response_content = ""
    return response_content


def get_chat_gpt_response(speech_input, caller_id=None):
    response = get_chat_completions_async(ANSWER_PROMPT_SYSTEM_TEMPLATE[languages.get(caller_id, "DE")], speech_input,
                                          caller_id)
    try:
        data = json.loads(response)
        if "nummer" and "stelle" in data:
            app.logger.info(f"Forwarding: {json.dumps(data)}")
            transfer_call(call_connection_id, data["nummer"])
        else:
            print("The 'nummer' field is missing.")
    except Exception as ex:
        app.logger.info("not valid JSON so no redirection for now")
    return response


def handle_recognize(replyText, callerId, call_connection_id, context=""):
    play_source = TextSource(text=replyText, voice_name=voices[languages.get(callerId, 'DE')])
    recognize_result = call_automation_client.get_call_connection(call_connection_id).start_recognizing_media(
        input_type=RecognizeInputType.SPEECH,
        target_participant=PhoneNumberIdentifier(callerId),
        end_silence_timeout=5,
        play_prompt=play_source,
        operation_context=context,
        speech_language=detection_language[languages.get(callerId, "DE")]
    )
    app.logger.info("handle_recognize : data=%s", recognize_result)


def handle_play(call_connection_id, caller_id, text_to_play, context):
    play_source = TextSource(text=text_to_play, voice_name=voices[languages.get(caller_id, 'DE')])
    call_automation_client.get_call_connection(call_connection_id).play_media_to_all(play_source,
                                                                                     operation_context=context)


def handle_hangup(call_connection_id):
    call_automation_client.get_call_connection(call_connection_id).hang_up(is_for_everyone=True)


def transfer_call(call_connection_id, phone_number):
    app.logger.info(f"Initializing the Call transfer...")
    transfer_destination = PhoneNumberIdentifier(phone_number)
    call_connection_client = call_automation_client.get_call_connection(
        call_connection_id=call_connection_id)
    call_connection_client.transfer_call_to_participant(target_participant=transfer_destination)


@app.route("/api/incomingCall", methods=['POST'])
def incoming_call_handler():
    for event_dict in request.json:
        event = EventGridEvent.from_dict(event_dict)
        app.logger.info("incoming event data --> %s", event.data)
        if event.event_type == SystemEventNames.EventGridSubscriptionValidationEventName:
            app.logger.info("Validating subscription")
            validation_code = event.data['validationCode']
            validation_response = {'validationResponse': validation_code}
            return Response(response=json.dumps(validation_response), status=200)
        elif event.event_type == "Microsoft.Communication.IncomingCall":
            app.logger.info("Incoming call received: data=%s",
                            event.data)
            if event.data['from']['kind'] == "phoneNumber":
                caller_id = event.data['from']["phoneNumber"]["value"]

                if "227" in event.data['to']["rawId"]:
                    app.logger.info(f"set lang for {caller_id} to EN")
                    languages[caller_id] = "EN"
                else:
                    languages[caller_id] = "DE"
                    app.logger.info(f"set lang for {caller_id} to DE")
            else:
                caller_id = event.data['from']['rawId']
            app.logger.info("incoming call handler caller id: %s",
                            caller_id)
            incoming_call_context = event.data['incomingCallContext']
            guid = uuid.uuid4()
            query_parameters = urlencode({"callerId": caller_id})
            callback_uri = f"{CALLBACK_EVENTS_URI}/{guid}?{query_parameters}"

            app.logger.info("callback url: %s", callback_uri)

            answer_call_result = call_automation_client.answer_call(incoming_call_context=incoming_call_context,
                                                                    cognitive_services_endpoint=COGNITIVE_SERVICE_ENDPOINT,
                                                                    callback_url=callback_uri)
            app.logger.info("Answered call for connection id: %s",
                            answer_call_result.call_connection_id)
            return Response(status=200)


@app.route("/api/callbacks/<contextId>", methods=["POST"])
def handle_callback(contextId):
    try:
        global caller_id, call_connection_id
        app.logger.info("Request Json: %s", request.json)
        for event_dict in request.json:
            event = CloudEvent.from_dict(event_dict)
            call_connection_id = event.data['callConnectionId']

            app.logger.info("%s event received for call connection id: %s", event.type, call_connection_id)
            caller_id = request.args.get("callerId").strip()
            if "+" not in caller_id:
                caller_id = "+".strip() + caller_id.strip()

            app.logger.info("call connected : data=%s", event.data)
            if event.type == "Microsoft.Communication.CallConnected":
                handle_recognize(HELLO_PROMPT[languages.get(caller_id, "DE")],
                                 caller_id, call_connection_id,
                                 context="GetFreeFormText")

            elif event.type == "Microsoft.Communication.RecognizeCompleted":
                if event.data['recognitionType'] == "speech":
                    speech_text = event.data['speechResult']['speech'];
                    app.logger.info("Recognition completed, speech_text =%s",
                                    speech_text)
                    if speech_text is not None and len(speech_text) > 0:
                        chat_gpt_response = get_chat_gpt_response(speech_text, caller_id)
                        app.logger.info(f"Chat GPT response:{chat_gpt_response}")
                        if len(chat_gpt_response) > 390:
                            chat_gpt_response = chat_gpt_response[:390]
                        handle_recognize(chat_gpt_response, caller_id, call_connection_id, context="OpenAISample")

            elif event.type == "Microsoft.Communication.RecognizeFailed":
                resultInformation = event.data['resultInformation']
                reasonCode = resultInformation['subCode']
                context = event.data['operationContext']
                global max_retry
                if reasonCode == 8510 and 0 < max_retry:
                    handle_recognize(TIMEOUT_SILENCE_PROMPT[languages.get(caller_id, "DE")], caller_id,
                                     call_connection_id)
                    max_retry -= 1
                else:
                    handle_play(call_connection_id, caller_id, GOODBYE_PROMPT[languages.get(caller_id, "DE")],
                                GOODBYE_CONTEXT)

            elif event.type == "Microsoft.Communication.PlayCompleted":
                context = event.data['operationContext']
                if context.lower() == TRANSFER_FAILED_CONTEXT.lower() or context.lower() == GOODBYE_CONTEXT.lower():
                    handle_hangup(call_connection_id)
                elif context.lower() == CONNECT_AGENT_CONTEXT.lower():
                    if not AGENT_PHONE_NUMBER or AGENT_PHONE_NUMBER.isspace():
                        app.logger.info(f"Agent phone number is empty")
                        handle_play(call_connection_id=call_connection_id, caller_id=caller_id,
                                    text_to_play=AGENT_PHONE_NUMBER_EMPTY_PROMPT)
                    else:
                        app.logger.info(f"Initializing the Call transfer...")
                        transfer_destination = PhoneNumberIdentifier(AGENT_PHONE_NUMBER)
                        call_connection_client = call_automation_client.get_call_connection(
                            call_connection_id=call_connection_id)
                        call_connection_client.transfer_call_to_participant(target_participant=transfer_destination)
                        app.logger.info(f"Transfer call initiated: {context}")

            elif event.type == "Microsoft.Communication.CallTransferAccepted":
                app.logger.info(f"Call transfer accepted event received for connection id: {call_connection_id}")

            elif event.type == "Microsoft.Communication.CallTransferFailed":
                app.logger.info(f"Call transfer failed event received for connection id: {call_connection_id}")
                resultInformation = event.data['resultInformation']
                sub_code = resultInformation['subCode']
                # check for message extraction and code
                app.logger.info(f"Encountered error during call transfer, message=, code=, subCode={sub_code}")
                handle_play(call_connection_id=call_connection_id, caller_id=caller_id,
                            text_to_play=CALLTRANSFER_FAILURE_PROMPT,
                            context=TRANSFER_FAILED_CONTEXT)
        return Response(status=200)
    except Exception as ex:
        app.logger.info("error in event handling")


@app.route("/")
def hello():
    return "Hello ACS CallAutomation!..test"


def extract_snippets(response_json):
    # Initialize an empty list to hold the snippets
    snippets = []

    # Check if 'webPages' and 'value' keys exist in the JSON response
    if 'webPages' in response_json and 'value' in response_json['webPages']:
        # Loop through each item in the 'value' list
        for item in response_json['webPages']['value']:
            # Check if the 'snippet' key exists for the item
            if 'snippet' in item:
                # Add the snippet text to the snippets list
                snippets.append(item['snippet'])

    # Return the list of snippets
    return snippets


if __name__ == '__main__':
    app.logger.setLevel(INFO)
    app.run(host="0.0.0.0", debug=True, port=os.getenv("PORT", default=1234))
    # Add your Bing Search V7 subscription key and endpoint to your environment variables.
    # Query term(s) to search for.
