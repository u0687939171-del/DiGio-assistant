import streamlit as st
import requests
import os
import datetime

# =======================================================
# 1. CONFIGURAZIONE CHIAVI API, URL e MAPPATURE
# =======================================================

# Le chiavi sono lette da Streamlit Secrets/variabili d'ambiente (os.environ.get)
# Sostituisci i placeholder con le tue chiavi per i test locali!
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "99a7fe7cbfa85f9403d1639011dc457b")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "f0f4286c0556d5918d9bd9883a779be0")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "8deda8ae2a258a19620e4629e2c76116")

# URL Base
GNEWS_URL = "https://gnews.io/api/v4/search"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# Mappatura dei nomi di Paese/nazionalità con i codici ISO (usati per GNews country e lang)
COUNTRY_CODES = {
    "italia": "it", "italiana": "it",
    "stati uniti": "us", "usa": "us", "america": "us", 
    "spagna": "es", "spagnola": "es",
    "francia": "fr", "francese": "fr",
    "germania": "de", "tedesca": "de",
    "regno unito": "gb", "uk": "gb"
    # Aggiungi altri paesi/nazionalità che desideri supportare...
}


# =======================================================
# 2. FUNZIONI API (LOGICA DELLE RICHIESTE)
# =======================================================

def get_global_news(query, country_code, max_articles=5):
    """
    Recupera le notizie in base a una query e un codice Paese specifici.
    Usa il filtro 'country' per ottenere notizie nella lingua originale del Paese.
    """
    if GNEWS_API_KEY == "LA_TUA_CHIAVE_GNEWS":
        return "⚠️ Per le notizie, devi configurare la chiave GNews API!"
        
    language_code = country_code.lower() 
    
    params = {
        "q": query,
        "lang": language_code, 
        "country": country_code.upper(), 
        "max": max_articles, 
        "apikey": GNEWS_API_KEY,
    }
    
    try:
        response = requests.get(GNEWS_URL, params=params)
        response.raise_for_status() 
        data = response.json()
        articles = data.get('articles', [])
        
        if not articles:
            return f"😔 Oh no! Non ho trovato notizie da **{country_code.upper()}** per: **{query if query else 'i titoli principali'}**"

        news_summary = []
        for a in articles:
            news_summary.append(f"• **{a['title']}** (Fonte: {a['source']['name']})\n  [Leggi l'articolo originale]({a['url']})")
            
        return f"📰 Certo! Ho trovato queste chicche da **{country_code.upper()}**:\n\n" + "\n".join(news_summary)
        
    except requests.exceptions.RequestException as e:
        return f"🤯 Ops! Errore di connessione o API per le notizie: {e}"
    except Exception as e:
        return f"Si è verificato un errore inaspettato (Notizie): {e}"


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
    except Exception as e:
        return f"Si è verificato un errore inaspettato (Film): {e}"


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
    st.set_page_config(page_title="DiGio Assistant", page_icon="🤖")
    st.title("🤖 DiGio: Il tuo Assistente Interattivo")
    st.markdown("Ciao! Sono **DiGio**, il tuo assistente personale. Dimmi cosa posso fare per te!")
    
    # Mostra i comandi in una sezione espandibile
    with st.expander("✨ Clicca qui per vedere i miei super poteri (Comandi)"):
        st.markdown("""
        Prova uno di questi comandi:
        
        - **notizie** *[Paese] [argomento]*: Cerca notizie globali. Es. `notizie Spagna calcio` o `notizie USA`.
        - **film** *<titolo>*: Cerca informazioni su un film. Es. `film Interstellar`
        - **meteo** *<città>*: Ottiene le condizioni meteo attuali. Es. `meteo Palermo`
        """)

    # Input testuale per l'utente
    user_input = st.text_input("💬 Cosa vuoi chiedermi oggi?", key="user_query")

    if user_input:
        user_query = user_input.lower().strip()
        result = ""
        
        # --- Logica di Parsing ---
        try:
            # --- Logica NOTIZIE (GNews Globali) ---
            if user_query.startswith("notizie"):
                
                parts = user_query.split(" ", 1)
                if len(parts) < 2:
                    st.warning("Ehi! Devi specificare almeno un argomento o un Paese. Es: 'notizie sport' o 'notizie spagna'.")
                    return

                search_query = parts[1].strip()
                country_code = "it" 
                topic_query = search_query 
                
                # Cerca il nome del Paese nella query
                words = search_query.split()
                for word in words:
                    if word in COUNTRY_CODES:
                        country_code = COUNTRY_CODES[word]
                        # Rimuovi il nome del Paese dalla query
                        topic_query = search_query.replace(word, "").strip()
                        break
                        
                final_query = topic_query if topic_query else ""

                st.info(f"🤖 DiGio: Cerco notizie da **{country_code.upper()}** su: *{final_query if final_query else 'i titoli principali'}*...")
                result = get_global_news(final_query, country_code)
                
            # --- Logica FILM (TMDB) ---
            elif user_query.startswith("film"):
                movie_title = user_query.split(" ", 1)[1].strip()
                st.info(f"🤖 DiGio: Cerco dettagli su '{movie_title}'...")
                result = get_movie_info(movie_title)
                
            # --- Logica METEO (OpenWeatherMap) ---
            elif user_query.startswith("meteo"):
                city_name = user_query.split(" ", 1)[1].strip()
                st.info(f"🤖 DiGio: Cerco il meteo per '{city_name}'...")
                result = get_weather_info(city_name)
            
            # --- Logica NON RICONOSCIUTA ---
            else:
                result = "🤔 Non ho capito bene... puoi ripetere il comando? Ricorda di usare `notizie`, `film`, o `meteo`!"

            # Mostra il risultato
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
