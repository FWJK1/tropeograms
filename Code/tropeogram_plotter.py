

## third party packages 
import plotly.graph_objects as go
import pandas as pd


class TropeogramPlotter:
    def __init__(self):
        pass


    def plot_genre_snapshots(self, snapshot_df, selected_genre, config):
        fig = go.Figure()

        ymin, ymax = config["y_range"]

        # Plot the selected genre line (smoothed)
        fig.add_trace(go.Scatter(
            x=snapshot_df['second'] / 60,  
            y=snapshot_df[selected_genre], 
            mode='lines',  
            name=selected_genre, 
            line=dict(width=2),  
        ))

        # Get tropes data and times
        tropes_data = []
        times = []
        labels = []
    
        
        # Loop through all rows to check for first occurrence of tropes
        for idx, row in snapshot_df.iterrows():
            tropes = row['new_tropes']
            if tropes:  # If there are any new tropes at this point
                for trope in tropes:
                    times.append(row['second'] / 60)  ##  TODO consider changing this to be a percentage of the movie
                    tropes_data.append(row[selected_genre])
                    labels.append(trope)  # Use individual trope as label

        # Only plot tropes if there are any
        if tropes_data:
            fig.add_trace(go.Scatter(
                x=times,
                y=tropes_data,
                mode='markers',  # Only markers without text
                name='Tropes',  
                marker=dict(size=8, color='red', symbol='circle'),
                text=labels,  # Text will show up on hover
                hoverinfo='text',  # Only show text on hover
            ))

        fig.update_layout(
            title=f"{selected_genre} Makeup Over Time with Decay {config["tau"]}",
            xaxis_title="Time (minutes)",
            yaxis = dict(
                title = "Percentage Makeup",
                range = [ymin, ymax]
            ),
            template="plotly_white",  
            showlegend=True, 
            width=1000,  
            height=800,  
        )
        return fig