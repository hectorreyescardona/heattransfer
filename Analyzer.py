from Furnace import Furnace
import plotly.graph_objects as go


class Analyzer:
    
    def __init__(self,
                 results,
                 simulator,
                 furnace: Furnace):
        self.results = results
        self.furnace = furnace
        self.simulator = simulator


    def get_point_data(self, 
                           r: float,
                           z: float):
        """
        @param
        r: distance from inner surface 
        z: height from the bottom of the coil
        """


        # Just treating the one coil furnace
        coil = self.furnace.coils[0] 
        height_points = coil.points.shape[1]
        radial_points = coil.points.shape[2]
        coil_depth = coil.outer_radius - coil.inner_radius


        ratio = r / coil_depth
        r_index = int(radial_points * ratio)
        h_index = int( (z / coil.height) * height_points )

        # Returns first tangential layer
        return self.results[0,h_index,r_index]

    def plot_point_temperature_evolution(self, 
                           r: float,
                           z: float):
        """
        @param
        r: distance from inner surface 
        z: height from the bottom of the coil
        """

        data = self.get_point_data(r, z)
        plot_height = 800

        layout = {
            "title": f"Evolución de temperatura de punto en (z,r) = {z,r}",
            #"width": 1920,
            "height": plot_height,
            "font": {
                    "family": "Arial",
                    "size": 15,
                    "color": "black",
                },

        }

        fig = go.Figure(layout=layout)
        fig.add_trace(go.Scatter(
            x=self.simulator.times,
            y=data,
            name="Coil point"
        ))
        fig.add_trace(go.Scatter(
            x=self.simulator.times,
            y=[self.furnace.temperature_at(time) for time in self.simulator.times],
            mode="lines",
            name="Furnace temperature"
        ))

        # Update spacing

        fig.update_layout(
            title=dict(
                x=0.5,                # Center the title
                xanchor="center",
                y=0.97,
                yanchor="top",
            ),
            margin=dict(t=int(plot_height * 0.15), b=100, l=100, r=100),
            legend=dict(
                x=1.05,               # Space between graph and legend
                xanchor="left",
            ),
        )

        # Space between numeric tick labels and the graph
        fig.update_xaxes(ticklabelstandoff=15)
        fig.update_yaxes(ticklabelstandoff=15)

        fig.show()

        

