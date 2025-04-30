## python packages
import argparse

## third party packages
import streamlit as st

## homebrew packages
import streamlit_state_manager as ssm


## initializing streamlit state. 
# Ideally this calculates everything smoothly so we can move.

if "initialized" not in st.session_state:
    parser = argparse.ArgumentParser(description="Command Line config for tropeogram plotter")
    parser.add_argument('--matrix', type=str, default='prop', choices=['prop', 'tf_idf'], 
                    help="Choose how to evalute the genreness of a trope. The default is 'prop,' for proportional")
    args = parser.parse_args()
                    
    ssm.initialize_state(matrix=args.matrix)
    st.session_state.initialized = True



### Actual UI Elements ###
st.set_page_config(layout="wide")

## vars
genres = st.session_state.genres
gt = list(st.session_state.movies.values())[0]
titles = st.session_state.movies.keys()



## TODO: Add dynamic scaling options so that we are either comparing across movies
## ie we set scales to same in each plot 
## or across movie ie we set scales across the whole movie.
with st.sidebar: 
    ## setup number of plots and movies
    st.header("Basic Setup")
    movie_selections=st.multiselect("Select Movies To Analyze", titles, default=["Alien"])
    num_plots=st.selectbox("Select number of plots", [1, 2, 3, 4 ,5], index=3)

    if not movie_selections:
        st.error("Please select at least one movie.")
        st.stop()


    ## some calculating
    movie_selections={title:troper for title,troper in st.session_state.movies.items() if title in movie_selections}
    tropers = [troper for title, troper in movie_selections.items() if title in movie_selections] 
    default_y_range, ranked_genres = ssm.calculate(tropers) 

    ## actual setting up plots
    st.header("Parameters")
    selected_range = st.slider("Select Max Y-Range for all plots", default_y_range[0], default_y_range[1], 
                               value=(default_y_range[0], default_y_range[1]))
    
    dynamic_range_tog= st.toggle("Set to Dynamic Range")
    bot, top = selected_range
    bot, top = bot-.003, top+.003
    tau_vals = [1, 60, 120, 600, 1200]
    
    tau_selections = []
    genre_selections = []
    for i in range(num_plots):
        st.subheader(f"Plot {i+1}")
        genre_selections.append(st.selectbox(f"Select Genre for Plot {i+1}", ranked_genres, index=ranked_genres.index(ranked_genres[i]), key=f"genre_{i}"))
        tau_selections.append(st.selectbox(f"Select Trope Decay for Plot {i+1}", tau_vals, index=3, key=f"tau_{i}"))

dynamic_y_range = ssm.get_dynamic_range(tropers, set(tau_selections))

### plotting
for title, troper in movie_selections.items():  
    cols = st.columns(num_plots)
    for i, (col, tau, genre) in enumerate(zip(cols, tau_selections, genre_selections)):
        with col:
            snapshot = troper.snapshots[tau]

            if dynamic_range_tog:
                val = snapshot[genre].min()
                peak = val + dynamic_y_range
                config = {
                    "y_range" : (val-.003, peak+.003),
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