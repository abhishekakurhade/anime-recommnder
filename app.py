import streamlit as st
st.set_page_config(page_title="Anime Recommender", layout="wide")

import pandas as pd
import numpy as np

# Load dataset from CSV
@st.cache_data
def load_data():
    return pd.read_csv("anime_data.csv")

anime_df = load_data()

# Extract unique genres from the 'genre' column
def extract_unique_genres(df):
    all_genres = set()
    for g in df['genre'].dropna().astype(str):
        for piece in g.split(','):
            all_genres.add(piece.strip())
    return sorted(all_genres)

# Recommendation logic
def get_anime_recommendations(df, preferred_genres, preferred_type, episode_range, min_rating, top_k):
    filtered = df.copy()

    if min_rating > 0.0:
        filtered = filtered[filtered['rating'] >= min_rating]

    if preferred_type != "Any":
        filtered = filtered[filtered['type'] == preferred_type]

    if episode_range != "Any":
        if episode_range == '1-12':
            filtered = filtered[filtered['episodes'] <= 12]
        elif episode_range == '13-26':
            filtered = filtered[(filtered['episodes'] >= 13) & (filtered['episodes'] <= 26)]
        elif episode_range == '27-50':
            filtered = filtered[(filtered['episodes'] >= 27) & (filtered['episodes'] <= 50)]
        elif episode_range == '51+':
            filtered = filtered[filtered['episodes'] >= 51]

    if preferred_genres:
        def has_match(genres_str):
            anime_genres = [x.strip() for x in str(genres_str).split(',')]
            return any(g in anime_genres for g in preferred_genres)
        filtered = filtered[filtered['genre'].apply(has_match)]

    if filtered.empty:
        return []

    def calculate_score(anime):
        score = 0
        if preferred_genres:
            anime_genres = [x.strip() for x in str(anime['genre']).split(',')]
            score += len(set(preferred_genres) & set(anime_genres)) * 10
        if anime['type'] == preferred_type:
            score += 15
        if anime['rating'] >= min_rating:
            score += (anime['rating'] - min_rating) * 2
        score += min(np.log10(anime['members'] + 1), 6)
        return score

    filtered['score'] = filtered.apply(calculate_score, axis=1)
    top_recommendations = filtered.sort_values(by='score', ascending=False).head(top_k)
    return top_recommendations

# ---------- Streamlit UI ---------- #
st.title("🎌 Anime Recommendation System")
st.markdown("Discover your next favorite anime based on your preferences")

# Sidebar filters
st.sidebar.header("🔎 Filter Your Preferences")

genres = extract_unique_genres(anime_df)
selected_genres = st.sidebar.multiselect("Preferred Genres", genres)

types = ['Any'] + sorted(anime_df['type'].dropna().unique())
selected_type = st.sidebar.selectbox("Anime Type", types)

episode_ranges = ['Any', '1-12', '13-26', '27-50', '51+']
selected_episode_range = st.sidebar.selectbox("Number of Episodes", episode_ranges)

min_rating = st.sidebar.slider("Minimum Rating", 0.0, 10.0, 7.0, 0.1)
top_k = st.sidebar.slider("Number of Recommendations", 1, 20, 10)

# Recommend button
if st.sidebar.button("🎬 Recommend"):
    results = get_anime_recommendations(
        anime_df,
        preferred_genres=selected_genres,
        preferred_type=selected_type,
        episode_range=selected_episode_range,
        min_rating=min_rating,
        top_k=top_k
    )

    st.subheader("✨ Recommended Anime")
    if results is not None and len(results) > 0:
        for idx, row in results.iterrows():
            st.markdown(f"### {row['title']}")
            st.markdown(f"**Genres:** {row['genre']}")
            st.markdown(f"**Type:** {row['type']}")
            st.markdown(f"**Episodes:** {int(row['episodes'])}  |  **Rating:** {row['rating']} ⭐")
            st.markdown("---")
    else:
        st.error("😕 No anime found that match your filters.\n\nTry changing genres, type, episode count, or lower the minimum rating.")
        st.info("🔁 **Tips:**\n- Select fewer genres\n- Lower the minimum rating\n- Change type to 'Any'\n- Increase episode range")

else:
    st.info("Set your preferences on the sidebar and click **Recommend**.")
