import streamlit as st
import json
from openai import OpenAI

MAX_TOKEN = 4096

title = "ChatAdventure - Ratisbona Dungeons 💬 📚"

prompt = """
Agiere als Game-Engine, der die Geschichte "Ratisbona Dungeons" kreiert und in ein Text-Adventure Game verwandelt. 
Der Benutzer spielt die Hauptfigur Elviar, die auf der Suche nach dem geheimnisvollen Buch „The Treasure“ ist. 
Die mystischen Reise findet in den Dungeons von Ratisbona, die sich in mittelalterlichen Gewölben 
unter dieser Stadt befinden.

Eröffne das Spiel mit dieser Beschreibung

„Willkomen bei Ratisbona Dungeons. 

Du lebst seit 10 Jahren in Regensburg, eine Stadt im Osten von Bayern am Zusammenfluss von Donau, Naab und Regen.

Deine Freundin Marva hat dich gebeten ein Buch für Sie abzuholen. Als du die kleine Buchhandlung in der 
Stadtmitte betrittst, begrüßt dich der alte, etwas mysteriöse Buchhändler äußerst freundlich.

Als du den Namen des Buches „Thēsauros“ nennst, das du abholen sollst, erschrickt der Buchhändler und
läuft so schnell er kann durch eine kaum sichtbare Türe hinter den Regalen.

Da er längere Zeit nicht wieder kommt, gehst du ihm nach.

Viele Treppenstufen führen tief nach unten in einen alten Keller, der aus dem Felsen gehauen ist. 
An den Wänden hängen Waffen. Es gibt zwei Türen.“

Der von dir verwendete Tonfall ist entscheidend für die Atmosphäre und macht das Erlebnis ansprechend 
und interaktiv. Verwende den Tonfall, der in Fantasy-Romanen üblich ist.

Du navigierst den Spieler durch Herausforderungen, Entscheidungen und Konsequenzen.
Dynamische Anpassung der Geschichte basieren auf den Entscheidungen des Spielers.
Dein Ziel ist es, ein verzweigtes Erzählerlebnis zu schaffen, bei dem jede Wahl durch den Spieler
zu einem neuen Weg führt, der letztlich über Elviras Schicksal entscheidet.

Der alte Buchhändler soll als Figur weiter mitspielen.
Ein Wolf soll als Begleiter irgendwann in Erscheinung treten.
Später soll etwas mit Computer und Hacker hinzukommen.

Finde ein paar Wege, die zum Erfolg führen.
Es gibt Wege, die zum Tod führen. Wenn der Spieler stirbt, generierst du eine Antwort, die den Tod erklärt und mit dem Text „The End“ endet. Dieser beendet das Spiel
Erkläre immer zunächst die aktuelle Situation in ein bis zwei kurzen Sätzen und erläutere dann die möglichen Entscheidungen, die der Spieler zur Wahl hat.
Das Spiel soll möglichst lange dauern und spannend erzählt sein.
"""

picture_prompt = """
Erstelle aus dem Text einen Beschreibung für ein Bild, das mit Dall-E generiert werden soll im Stile
des Filmes 'Herr der Ringe'.

Text:
{text}
"""

st.session_state.ollama_path = 'http://localhost:11434/v1'
st.session_state.image_model = 'dall-e-3'

st.set_page_config(
    page_title=title,
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)

st.title(title)

if "model" not in st.session_state:
    with st.form("Model"):
        model = st.selectbox(
            "Bitte wählen Sie das gewünschte LLM aus",
            ("gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "llama3", "gemma2")
        )
        submitted = st.form_submit_button("Weiter")
        if submitted:
            st.session_state.model = model

if "model" in st.session_state:
    if st.session_state.model.startswith("gpt"):
        try:
            st.session_state.client = OpenAI(
                api_key=st.secrets.openai_key
            )
        except:
            with st.form("API key"):
                api_key = st.text_input("Bitte API key eingeben")
                submitted = st.form_submit_button("Weiter")
                if submitted:
                    st.session_state.client = OpenAI(
                        api_key=api_key
                    )

    else:
        st.session_state.client = OpenAI(
            base_url=st.session_state.ollama_path,
            api_key='ollama'  # required, but unused
        )

def do_language()->None:
    if st.session_state.messages[-1]["role"] != 'user':
        st.session_state.messages.append(  # save prompt
            {"role": "user",
             "content": f"From now on, use the language {st.session_state.language}"
             }
        )

if "client" in st.session_state:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "user",
             "content": prompt}
        ]

    #sidebar
    st.sidebar.title("ChatAdventure - Ratisbona Dungeons 💬 📚")
    show_image = st.sidebar.toggle("Show images")
    st.sidebar.image("titel.jpg", width=200)
    if st.sidebar.button("Save"):
        with open("messages.json", 'w') as f:
            f.write(json.dumps(st.session_state.messages))
    if st.sidebar.button("Load"):
        with open("messages.json", 'r') as f:
            st.session_state.messages = json.load(f)
    if st.sidebar.button("Regenerate"):
        if st.session_state.messages[-1]["role"] == 'assistant':
            del st.session_state.messages[-1]
    if st.sidebar.button("Undo"):
        if len(st.session_state.messages) > 1:
            if st.session_state.messages[-1]["role"] == 'assistant':
                if st.session_state.messages[-2]["role"] == 'user':
                    del st.session_state.messages[-1]
                    del st.session_state.messages[-1]
    language = st.sidebar.selectbox(
        "Language",
        ("German", "English", "French", "Spain"),
        key="language",
        on_change=do_language,
    )

    # -- ask user
    if prompt := st.chat_input("Deine Antwort"):
        st.session_state.messages.append(  # save prompt
            {"role": "user",
             "content": prompt}
        )

    for message in st.session_state.messages[1:]:  # Display the prior chat messages
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # -- get answer
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Loading..."):
                stream = st.session_state.client.chat.completions.create(
                    model=st.session_state.model,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                    max_tokens=MAX_TOKEN
                )

                response = st.write_stream(stream)

            if show_image:
                with st.spinner("Loading..."):
                    description = st.session_state.client.chat.completions.create(
                        model=st.session_state.model,
                        messages=[
                            {"role": 'user', "content": picture_prompt.format(text=response)}
                        ]
                    )

                    picture = st.session_state.client.images.generate(
                        model=st.session_state.image_model,
                        prompt=description.choices[
                                   0].message.content + " Der Stil hat möglichst realistisch, wie im Film 'Herr der Ringe' zu sein.",
                        size="1024x1024",
                        quality="standard",
                        n=1
                    )
                    image_url = picture.data[0].url
                    st.image(image_url, width=360)
        st.session_state.messages.append({"role": "assistant",
                                          "content": response})
