## python packages
import argparse

## third party packages
import streamlit as st



## homebrew packages
from streamlit_state_manager import initialize_state


## initializing streamlit state. 
# Ideally this calculates everything smoothly so we can move.

## TODO: add some sort of mechanic for choosing movies. Maybe 
if "initialized" not in st.session_state:
    parser = argparse.ArgumentParser(description="Command Line config for tropeogram plotter")
    parser.add_argument('--matrix', type=str, default='prop', choices=['prop', 'tf_idf'], 
                    help="Choose how to evalute the genreness of a trope. The default is 'prop,' for proportional")
    args = parser.parse_args()
                    
    initialize_state(matrix=args.matrix)
    st.session_state.initialized = True


### Actual UI Elements ###
st.set_page_config(layout="wide")

## vars
genres = st.session_state.genres
ranked_genres = st.session_state.ranked_genres
gt = list(st.session_state.movies.values())[0]
default_y_range = st.session_state.max_range
dynamic_y_range  = st.session_state.dynamic_range
print(dynamic_y_range)


## TODO: Add dynamic scaling options so that we are either comparing across movies
## ie we set scales to same in each plot 
## or across movie ie we set scales across the whole movie.



with st.sidebar: 
    st.header("Filtering")
    selected_range = st.slider("Select Max Y-Range for all plots", default_y_range[0], default_y_range[1], 
                               value=(default_y_range[0], default_y_range[1]))
    
    dynamic_range = st.toggle("Dynamic Range")
    bot, top = selected_range
    bot, top = bot-.01, top+.01
    tau_vals = [1, 60, 120, 600, 1200]
    
    num_plots = 5  # Number of plots
    tau_selections = []
    genre_selections = []

    
    for i in range(num_plots):
        st.subheader(f"Plot {i+1}")
        genre_selections.append(st.selectbox(f"Select Genre for Plot {i+1}", ranked_genres, index=ranked_genres.index(ranked_genres[i]), key=f"genre_{i}"))
        tau_selections.append(st.selectbox(f"Select Trope Decay for Plot {i+1}", tau_vals, index=3, key=f"tau_{i}"))


### plotting
for title, troper in st.session_state.movies.items():
    cols = st.columns(num_plots)
    for i, (col, tau, genre) in enumerate(zip(cols, tau_selections, genre_selections)):
        with col:
            snapshot = troper.snapshots[tau]

            if dynamic_range:
                val = snapshot[genre].min()
                peak = val + dynamic_y_range
                config = {
                    "y_range" : (val-.01, peak+.01),
                    "tau": tau
                }
            else:
                config = {
                    "y_range": (bot, top), 
                    "tau" : tau
                    }
            fig = st.session_state.plotter.plot_genre_snapshots(snapshot, genre, config=config)
            fig.update_layout(title=f"{genre_selections[i]} Plot ({i+1}) for {title}")
            # Assign a unique key to each chart to prevent duplication issuess
            st.plotly_chart(fig, use_cFontainer_width=True, key=f"plot_{i}_{title}")