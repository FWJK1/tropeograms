
## default python packages
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

## third party packages
import streamlit as st

## homebrew packages
from genre_troperator import GenreTroperator
from tropeogram_plotter import TropeogramPlotter
from Utility.toolbox import find_repo_root, get_genres
from Utility.toolbox import log_time


root = find_repo_root()
movies = {
    # "Alien" : "Data/trope_time_series/alien_tropes.csv",
    # "Clueless" : f"{root}/Data/trope_time_series/clueless_tropes.csv",
    "Fellowship of The Ring" : f"{root}/Data/trope_time_series/Fellowship_of_the_Ring_filled.csv"
}

def get_max_range(troperators):
    ranges = [movie.get_max_y_range() for movie in troperators]
    mins = [range[0] for range in ranges]
    maxs = [range[1] for range in ranges]
    return min(mins), max(maxs)

def get_dynamic_range(troperators):
    ranges = [movie.get_dynamic_y_range() for movie in troperators]
    return max(ranges)
    
def rank_genres(troperators):
    maxs = [troperator.top_5 for troperator in troperators]
    interleaved = [item for group in zip(*maxs) for item in group]
    seen = set()
    return  [x for x in interleaved if not(x in seen or seen.add(x))]

def initialize_state(matrix): 
    tropers = {
        title: GenreTroperator(matrix=matrix, movie_path=path) for title, path in movies.items()
    }
    st.session_state.max_range = get_max_range(list(tropers.values()))
    st.session_state.dynamic_range = get_dynamic_range(list(tropers.values()))
    st.session_state.ranked_genres = rank_genres(list(tropers.values()))
    st.session_state.movies = tropers

    st.session_state.plotter = TropeogramPlotter()
    st.session_state.genres = get_genres()

