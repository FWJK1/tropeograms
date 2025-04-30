## standard python libraries
from concurrent.futures import ThreadPoolExecutor
import pickle

## third party libraries
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


## homebrew packages
import Utility.toolbox as tb
from Utility.genre_trope_matrix import build_prop_trope_matrix, build_tf_idf_matrix


root = tb.find_repo_root()

class GenreTroperator:
    def __init__(self, matrix="prop", movie_path=f"{root}/Data/trope_time_series/alien_tropes.csv", title="Alien", reload=False, taus=[1, 60, 120, 600, 1200]):
        self.matrix = build_prop_trope_matrix()
        # if matrix == 'prop':
        #     self.matrix  = build_prop_trope_matrix()
        # elif matrix == 'tf_idf':
        #     self.matrix = build_tf_idf_matrix()
        self.genres = tb.get_genres()
        self.movie_tropes = self.load_movie_data(movie_path)
        self.title = title
        if reload:
            self.build_snapshots()
            self.save_snapshots()
        else:
            try:
                self.load_snapshots()
            except:
                self.snapshots = self.build_snapshots()
                self.save_snapshots()
                
        self.top_5 = self.sort_snapshots()
        
    def load_movie_data(self, path=f"{root}/Data/trope_time_series/alien_tropes.csv", matrix=None):
        """
        Load and format the time-series data from a csv
        """
        matrix = matrix or self.matrix
        df = pd.read_csv(path)
        df['Trope'] = df['Trope'].str.replace(" ", "")  # Convert to CamelCase
        df = df.merge(matrix, on='Trope', how='left')
        df['Duration'] = df['End Time'] - df['Start Time']

        # Adjust genre expectations for inverted/subverted cases
        df.loc[(df['Inverted?/Defied?'] == 'Yes') | (df['Averted/Subverted?'] == 'Yes'), self.genres] *= -1
        df = df[df['Setups?'] != 'Yes']

        max_second = df['End Time'].max()
        df['active_seconds'] = df.apply(lambda row: set(range(row['Start Time'], min(max_second, row['End Time']))), axis=1)

        return df

    def save_snapshots(self):
        with open(f'{root}/Data/snapshots/{self.title}.pkl', 'wb') as f:
                pickle.dump(self.snapshots, f)

    def load_snapshots(self, taus=[1, 60, 120, 600, 1200]):
        with open(f'{root}/Data/snapshots/{self.title}.pkl', 'rb') as f:
            self.snapshots = pickle.load(f)
        # print(self.snapshots)
        taus = [tau for tau in taus if tau not in self.snapshots]
        if len(taus):
            self.snapshots |= self.build_snapshots(taus)

            self.save_snapshots()
        
    @tb.log_time
    def build_snapshots(self, taus=[1, 60, 120, 600, 1200] ):
            self.new_tropes_dict = self.movie_tropes.groupby('Start Time')['Trope'].apply(list).to_dict()
            with ThreadPoolExecutor(max_workers=8) as executor:
                 results = list(executor.map(self.get_snapshot, taus))
            return dict(zip(taus, results))

    def get_snapshot(self, tau=600):
        ## an open-ended question on this is whether we want to include tropes after one occurence or not
        ## it will definitely push the scale towards comedy and/or repetitive tropes
        df = self.movie_tropes.copy()
        max_second = df['End Time'].max()

        # add the tau period in addition to the active seconds
        df['tau_period'] = df.apply(lambda row: set(range(row['End Time'], min(max_second, row['End Time'] + tau))), axis=1)


        snapshots = []
        for second in range(max_second):

            ## new_tropes
            new_tropes = self.new_tropes_dict.get(second, [])

            ## active tropes
            active_df = df[df['active_seconds'].apply(lambda x: second in x)]
            tropes = active_df['Trope'].tolist()
            total_genre_expectation = active_df[self.genres].sum()

            ## decaying tropes
            decaying_df = df[df['tau_period'].apply(lambda x: second in x)]
            if not decaying_df.empty:
                time_since_end = second - decaying_df['End Time']
                decay_factor = (1 - (time_since_end / tau)).clip(lower=0, upper=1)

                decayed_values = decaying_df[self.genres].multiply(decay_factor, axis=0).sum()
                total_genre_expectation += decayed_values  ## sum decaying and active

            # normalize tropes
            total_genre_expectation /= total_genre_expectation.sum() or 1
            total_genre_expectation = total_genre_expectation.clip(lower=0)

            snapshots.append(
                 [second] + total_genre_expectation.tolist() + [tropes]  + [new_tropes]
                )

          # Create the snapshot dataframe and add the 'total' column
        snapshots_df = pd.DataFrame(snapshots, columns= ['second'] + self.genres + ['active_tropes', 'new_tropes'])
        snapshots_df['total'] = snapshots_df[self.genres].sum(axis=1)
        # print(snapshots_df)
        # print(snapshots_df[self.genres].describe().T)
        return snapshots_df

    def get_max_y_range(self,):
        values = [snapshot[genre] for snapshot in self.snapshots.values() for genre in self.genres] ## this is a list of pandas series
        return (min(v.min() for v in values), max(v.max() for v in values))
    
    def get_dynamic_y_range(self, taus):
        return max(
            (snapshot[self.genres].max() - snapshot[self.genres].min()).max()
            for tau, snapshot in self.snapshots.items() if tau in taus
        )

    def sort_snapshots(self):
        results = {}
        for genre in self.genres:
            vals = [snapshot[genre] for snapshot in self.snapshots.values()] ## this is a list of pandas series
            results[genre] = max(v.max() for v in vals)
        return sorted(results, key=results.get, reverse=True)