import streamlit as st
import requests
import os
import datetime

# =======================================================
# 1. CONFIGURAZIONE E SETUP DI STREAMLIT
# =======================================================

# Imposta il titolo e l'icona della pagina
st.set_page_config(page_title="DiGio Assistant", page_icon="🤖")

# Nota IMPORTANTE su chiavi API: 
# In un ambiente Streamlit Cloud, è BENE usare st.secrets o variabili d'ambiente.
# Per test locali, inserisci qui le tue chiavi, ma rimuovile prima di pushare su GitHub!

GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "99a7fe7cbfa85f9403d1639011dc457b")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "f0f4286c0556d5918d9bd9883a779be0")
TIMEZONEDB_API_KEY = os.environ.get("TIMEZONEDB_API_KEY", "J5DYFCVIP912")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "8deda8ae2a258a19620e4629e2c76116")

# URL Base
GNEWS_URL = "https://gnews.io/api/v4/search"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TIMEZONEDB_URL = "http://api.timezonedb.com/v2.1/get-time-zone"
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# Configurazione per GNews (fonti specifiche)
TARGET_SOURCES = [
    "bbc-news", "new-york-times", "la-repubblica", "la-gazzetta-dello-sport", 
    "ansa", "l-equipe", "mundo-deportivo"
]
SOURCES_LIST = ",".join(TARGET_SOURCES)


# =======================================================
# 2. FUNZIONI API
# =======================================================

def get_news_from_sources(query, max_articles=5):
    """Recupera le notizie solo dalle fonti specificate."""
    if GNEWS_API_KEY == "LA_TUA_CHIAVE_GNEWS":
        return "⚠️ Per le notizie, devi configurare la chiave GNews API!"
        
    params = {
        "q": query,
        "lang": "it",  
        "country": "it",
        "max": max_articles, 
        "apikey": GNEWS_API_KEY,
        "sources": SOURCES_LIST
    }
    
    try:
        response = requests.get(GNEWS_URL, params=params)
        response.raise_for_status()
        data = response.json()
        articles = data.get('articles', [])
        
        if not articles:
            return f"😔 Oh no! Non ho trovato notizie nelle tue fonti preferite per: **{query}**"

        news_summary = []
        for a in articles:
            news_summary.append(f"• **{a['title']}** (Fonte: {a['source']['name']})\n  [Dai un'occhiata qui!]({a['url']})")
            
        return f"📰 Certo! Ho trovato queste chicche nelle tue fonti preferite:\n\n" + "\n".join(news_summary)
        
    except requests.exceptions.RequestException as e:
        return f"🤯 Ops! Errore di connessione o API per le notizie: {e}"


def get_movie_info(movie_title):
    """Cerca un film per titolo e restituisce i dettagli principali."""
    if TMDB_API_KEY == "LA_TUA_CHIAVE_TMDB":
        return "⚠️ Per i film, devi configurare la chiave TMDB API!"

    try:
        # 1. Trova l'ID del film
        search_params = {
            "api_key": TMDB_API_KEY,
            "query": movie_title,
            "language": "it-IT"
        }
        search_response = requests.get(f"{TMDB_BASE_URL}/search/movie", params=search_params).json()
        
        if not search_response.get('results'):
            return f"🎬 Mi dispiace, non ho trovato un film con il titolo: **{movie_title}**."

        first_result = search_response['results'][0]
        movie_id = first_result['id']
        
        # 2. Ottieni i dettagli completi e i crediti (cast)
        details_url = f"{TMDB_BASE_URL}/movie/{movie_id}?api_key={TMDB_API_KEY}&language=it-IT&append_to_response=credits"
        details_response = requests.get(details_url).json()
        
        title = details_response.get('title', 'N/A')
        release_date = details_response.get('release_date', 'N/A')
        overview = details_response.get('overview', 'Trama non disponibile')
        
        cast = [c['name'] for c in details_response.get('credits', {}).get('cast', [])[:3]]
        cast_str = ", ".join(cast) if cast else "Non disponibile"
        
        output = f"✨ **{title}** ({release_date[:4]})\n"
        output += f"   - **Trama:** *{overview}*\n"
        output += f"   - **Cast principale:** {cast_str}"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"🤯 Ops! Errore di connessione o API per i film: {e}"


def get_timezone_info(city_name):
    """Ottiene l'ora e il fuso orario corrente per una città."""
    if TIMEZONEDB_API_KEY == "LA_TUA_CHIAVE_TIMEZONEDB":
        return "⚠️ Per il fuso orario, devi configurare la chiave TimezoneDB API!"

    params = {
        "key": TIMEZONEDB_API_KEY,
        "format": "json",
        "by": "city",
        "city": city_name
    }
    
    try:
        response = requests.get(TIMEZONEDB_URL, params=params).json()
        
        if response.get('status') == 'FAILED' or response.get('message'):
            return f"🌎 Non riesco a trovare il fuso orario per: **{city_name}**. Errore: {response.get('message', 'Dati non disponibili')}"

        formatted_time = response['formatted']
        time = formatted_time.split(' ')[1] 
        timezone_name = response['zoneName']
        gmt_offset = response['gmtOffset'] / 3600
        
        output = f"⏰ Ecco l'ora a **{city_name.title()}**:\n"
        output += f"   - **Orario:** {time}\n"
        output += f"   - **Fuso Orario:** {timezone_name}\n"
        output += f"   - **Offset GMT:** GMT{'+' if gmt_offset >= 0 else ''}{gmt_offset:.0f}"
        
        return output

    except requests.exceptions.RequestException as e:
        return f"🤯 Ops! Errore di connessione o API per il fuso orario: {e}"


def get_weather_info(city_name):
    """Ottiene le condizioni meteo attuali per una città (OpenWeatherMap)."""
    if OPENWEATHER_API_KEY == "LA_TUA_CHIAVE_OPENWEATHERMAP":
        return "⚠️ Per il meteo, devi configurare la chiave OpenWeatherMap API!"

    params = {
        "q": city_name,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "it"
    }
    
    try:
        response = requests.get(OPENWEATHER_URL, params=params)
        response.raise_for_status() 
        data = response.json()
        
        temp = data['main']['temp']
        description = data['weather'][0]['description'].capitalize()
        humidity = data['main']['humidity']
        
        output = f"☀️ Il tempo a **{data['name']}** è questo:\n"
        output += f"   - **Condizione:** {description}\n"
        output += f"   - **Temperatura:** {temp:.1f}°C\n"
        output += f"   - **Umidità:** {humidity}%"
        
        return output
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            return f"Città non trovata: **{city_name}**."
        return f"🤯 Ops! Errore HTTP nel recupero del meteo: {e}"
    except requests.exceptions.RequestException as e:
        return f"🤯 Ops! Errore di connessione o API per il meteo: {e}"


# =======================================================
# 3. INTERFACCIA STREAMLIT E PARSING DEI COMANDI
# =======================================================

def main():
    st.title("🤖 DiGio: Il tuo Assistente Interattivo")
    st.markdown("Ciao! Sono **DiGio**, il tuo assistente personale. Dimmi cosa posso fare per te!")
    
    # Mostra i comandi in una sezione espandibile
    with st.expander("✨ Clicca qui per vedere i miei super poteri (Comandi)"):
        st.markdown("""
        Prova uno di questi comandi:
        
        - **notizie** *<argomento>*: Es. `notizie calcio`
        - **film** *<titolo>*: Es. `film The Martian`
        - **fuso** *<città>*: Es. `fuso orario tokyo`
        - **meteo** *<città>*: Es. `meteo Palermo`
        """)

    # Input testuale per l'utente
    user_input = st.text_input("💬 Cosa vuoi chiedermi oggi?", key="user_query")

    if user_input:
        # Pulisci e normalizza l'input
        user_query = user_input.lower().strip()
        
        # Placeholder per il risultato
        result = ""
        
        # --- Logica di Parsing ---
        try:
            if user_query.startswith("notizie"):
                query = user_query.split(" ", 1)[1].strip()
                result = get_news_from_sources(query)
                
            elif user_query.startswith("film"):
                movie_title = user_query.split(" ", 1)[1].strip()
                result = get_movie_info(movie_title)
                
            elif user_query.startswith("fuso"):
                city_name = user_query.split(" ", 1)[1].strip()
                result = get_timezone_info(city_name)

            elif user_query.startswith("meteo"):
                city_name = user_query.split(" ", 1)[1].strip()
                result = get_weather_info(city_name)
                
            else:
                result = "🤔 Non ho capito bene... puoi ripetere il comando? Ricorda di usare `notizie`, `film`, `fuso` o `meteo`!"

            # Mostra il risultato usando st.markdown (per interpretare il grassetto e gli emoji)
            st.markdown("---")
            st.markdown(f"**🤖 DiGio risponde:**")
            st.markdown(result)
            st.markdown("---")
            
        except IndexError:
            st.warning("Ehi! Sembra che tu abbia dimenticato l'argomento. Riprova con un comando completo!")
        except Exception as e:
            st.error(f"Ehi, si è verificato un errore critico in DiGio: {e}")


if __name__ == "__main__":
    main()