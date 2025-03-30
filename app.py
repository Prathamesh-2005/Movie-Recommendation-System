import streamlit as st
import requests
import time
import pandas as pd
import pickle

# Set page configuration
st.set_page_config(page_title="Movie Recommender", layout="wide")

# Initialize session state variables
if 'recommended_movies' not in st.session_state:
    st.session_state.recommended_movies = []
    st.session_state.movie_posters = []
    st.session_state.movie_details = []
    st.session_state.movie_trailers = []
    st.session_state.movie_details_visible = {}
    st.session_state.recommend_clicked = False

# Caching movie poster fetch function
@st.cache_data
def fetch_poster(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=d38f385f9e591a6bf106f8fb7f63548f&language=en-US'
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if 'poster_path' in data and data['poster_path']:
                return "https://image.tmdb.org/t/p/w500/" + data['poster_path']
        except requests.exceptions.ConnectionError:
            time.sleep(2)
        except requests.exceptions.RequestException:
            break
    return "https://via.placeholder.com/500x750?text=No+Image+Available"

# Function to fetch movie details (overview)
def fetch_movie_details(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=d38f385f9e591a6bf106f8fb7f63548f&language=en-US'
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('overview', 'Description not available')
    except requests.exceptions.RequestException:
        return 'Description not available'

# Function to fetch trailer
def fetch_trailer(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key=d38f385f9e591a6bf106f8fb7f63548f&language=en-US'
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        trailer_key = data['results'][0]['key'] if data['results'] else None
        return f'https://www.youtube.com/watch?v={trailer_key}' if trailer_key else None
    except requests.exceptions.RequestException:
        return None

# Recommendation function
def recommend(movie):
    if movie not in movies['title'].values:
        return [], [], [], []

    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(enumerate(distances), key=lambda x: x[1], reverse=True)[1:6]

    recommended_movies = [movies.iloc[i[0]].title for i in movies_list]
    recommended_movies_posters = [fetch_poster(movies.iloc[i[0]].movie_id) for i in movies_list]
    recommended_movies_details = [fetch_movie_details(movies.iloc[i[0]].movie_id) for i in movies_list]
    recommended_movies_trailers = [fetch_trailer(movies.iloc[i[0]].movie_id) for i in movies_list]

    return recommended_movies, recommended_movies_posters, recommended_movies_details, recommended_movies_trailers

# Function to toggle visibility of movie details
def toggle_movie_details(index):
    if index in st.session_state.movie_details_visible:
        st.session_state.movie_details_visible[index] = not st.session_state.movie_details_visible[index]
    else:
        st.session_state.movie_details_visible[index] = True

# Load data locally
@st.cache_data
def load_data():
    with open("movie_dict.pkl", 'rb') as f:
        movies_dict = pickle.load(f)

    with open("similarity.pkl", 'rb') as f:
        similarity_matrix = pickle.load(f)

    return pd.DataFrame(movies_dict), similarity_matrix

# Loading movie data
movies, similarity = load_data()

# Custom CSS for UI styling
st.markdown("""
    <style>
        .title {
            text-align: center;
            font-size: 28px;
            font-weight: bold;
            color: #FF4500;
        }
        .subtitle {
            text-align: center;
            font-size: 18px;
            color: #555;
        }
        .movie-card {
            text-align: center;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
            background-color: #fff;
            margin-bottom: 15px;
        }
        img {
            width: 100%;
            height: 350px;
            object-fit: cover;
            border-radius: 10px;
            background-color: black;
        }
        .button {
            background-color: #FF4500;
            color: white;
            padding: 8px 15px;
            border-radius: 5px;
            font-size: 14px;
            border: none;
            cursor: pointer;
        }
        .description {
            padding: 10px;
            background-color: #f8f8f8;
            border-radius: 5px;
            margin-top: 10px;
            text-align: left;
            font-size: 14px;
            color: #333;
            border: 1px solid #ddd;
            line-height: 1.4;
        }
        .description strong {
            color: #FF4500;
            font-size: 16px;
        }
        .spinner {
            color: #FF4500;
            font-size: 18px;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="title">🎬 Movie Recommendation System</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Select a movie to get personalized recommendations!</p>', unsafe_allow_html=True)

# Movie selection
selected_movie_name = st.selectbox(
    "Select a movie:",
    movies['title'].values
)

# Recommendation button
if st.button('Recommend', key='main_recommend_button'):
    st.session_state.recommend_clicked = True
    with st.spinner('Fetching movie recommendations...'):
        names, posters, details, trailers = recommend(selected_movie_name)

        # Store recommendations in session state
        st.session_state.recommended_movies = names
        st.session_state.movie_posters = posters
        st.session_state.movie_details = details
        st.session_state.movie_trailers = trailers

# Display recommendations if available
if st.session_state.recommended_movies:
    st.markdown('<h2 class="title">Recommended Movies</h2>', unsafe_allow_html=True)

    # Create a persistent container for recommendations
    movie_container = st.container()

    with movie_container:
        # Display movies in a row
        cols = st.columns(5)
        for i in range(len(st.session_state.recommended_movies)):
            with cols[i]:
                st.markdown(f"""
                    <div class="movie-card">
                        <h3 style="color: #FF4500;">{st.session_state.recommended_movies[i]}</h3>
                        <img src="{st.session_state.movie_posters[i]}" alt="{st.session_state.recommended_movies[i]}">
                        <br>
                        <a href="{st.session_state.movie_trailers[i]}" target="_blank">
                            <button class="button">🎬 Watch Trailer</button>
                        </a>
                    </div>
                """, unsafe_allow_html=True)

                # About button with a unique key
                if st.button(f'📖 About {st.session_state.recommended_movies[i]}', key=f"about_{i}"):
                    toggle_movie_details(i)
                    st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

                # Display the details if visibility is toggled on
                if i in st.session_state.movie_details_visible and st.session_state.movie_details_visible[i]:
                    # Use an expander to make the description more visible
                    st.markdown(f"""
                        <div class="description">
                            <strong>Overview:</strong><br>{st.session_state.movie_details[i]}
                        </div>
                    """, unsafe_allow_html=True)

# For error case - only show if recommendations were requested but none were found
elif st.session_state.recommend_clicked and not st.session_state.recommended_movies:
    st.error("No recommendations found. Try another movie!")