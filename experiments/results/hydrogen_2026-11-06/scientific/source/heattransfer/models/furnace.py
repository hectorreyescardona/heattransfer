from __future__ import annotations

import numpy as np
from heattransfer.models import coil as Coil
from heattransfer.models.protection_gas import ProtectionGas
from scipy.integrate import quad


class Furnace:

    def __init__(self, 
                temperature: np.ndarray,
                coils: list[Coil.Coil], 
                height: float,
                radius: float,
                coil_sep_height:float, 
                gas: ProtectionGas | None = None, 
                gas_flow: float | None = None,
                vortex_enhancement: float | None = None, 
                radiation_enhancement: float | None = None,
                ):
        """
        The furnace is simplified by a cylinder. Holds a maxium of 4 coils. 

        @param 
        height: In meters.
        radius: In meters.
        coil_sep_height: Height of coil seperator in meters. 
        coils: Coils in order; each receives coil_num starting at 1.

        """

        self.temperature = np.array(temperature, dtype=float, copy=True)
        if self.temperature.ndim != 2 or self.temperature.shape[1] != 2:
            raise ValueError("Furnace temperature requires an (N, 2) array of time (hours) and temperature (Celsius).")
        
        self.profile_times = self.temperature[:, 0] * 3600.0
        self.profile_temperatures = self.temperature[:, 1] + 273.15
        if (len(self.profile_times) < 2
                or not np.all(np.isfinite(self.profile_times))
                or not np.all(np.isfinite(self.profile_temperatures))
                or self.profile_times[0] != 0
                or not np.all(np.diff(self.profile_times) > 0)):
            raise ValueError("Furnace profile requires finite temperatures and increasing times starting at zero.")
        
        self.duration = float(self.profile_times[-1])

        # Raise error if number of coils is exceeded
        self.coils = coils
        if len(self.coils) > 4:
            raise ValueError("The furnace holds a maximum of 4 coils.")
        for coil_num, coil in enumerate(self.coils, start=1):
            coil.coil_num = coil_num

        self.coil_sep_height = coil_sep_height
        self.convection_coefficient_side = 1
        self.convection_coefficient_top = 1

        self.gas = gas
        self.gas_flow = gas_flow
        self.vortex_enhancement = vortex_enhancement
        self.radiation_enhancement = radiation_enhancement

        # Calculated parameters
        self.cross_sectional_area = np.pi * (radius**2)
        self.radius = radius
        self.height = height

    def temperature_at(self, time):
        """Gas temperature in kelvin at time in seconds; hold endpoints outside the profile range."""
        return float(np.interp(time, self.profile_times, self.profile_temperatures))

    def get_flow_channel_area_depr(self, 
                              flow_ratio_zone):

        # Characterize coil
        keywords = flow_ratio_zone.split("-")
        zone = keywords[2] # Grab the denominator of top or side
        coil_number = keywords[1]

        # Obtain coil obj.
        coil = self.coils[coil_number]

        # Areas depending on loc. For the coils separators, we take the average cross-sectional area calculated 
        # by using the formula A = (2*sqrt(r^2 - (r-a)^2)*h) where r and h are the radius and height of the coil sep., respectively.
        # Uses the outer radius of the coil.

        coil_rad = coil.outer_radius
        avg_cross_section_area, _ = quad(lambda x: 2*np.sqrt(coil_rad**2 - (coil_rad - x)**2)*self.coil_sep_height ) / (coil_rad)
        
        areas = {
            "top": avg_cross_section_area,
            "side": self.cross_sectional_area - (np.pi*coil.outer_radius**2),
        }
        
        if (coil_number != "4"):
            return areas[zone]

        # We take a similar approach for the top coil (#4). Now the radius is the furnace radius. The height is computed by stacking all the coils.
        radius = self.radius

        coil_heights = sum(coil.height for coil in self.coils)
        coil_separator_heights = (len(self.coils) - 1) * self.coil_sep_height
        channel_height = coil_separator_heights + coil_heights
        
        areas["top"] = quad(lambda x: 2*np.sqrt(radius**2 - (radius - x)**2)* channel_height ) / (radius)

        return areas[zone]

    def get_flow_channel_area(self,
                              flow_ratio_zone):
        """As implmented in Zhang et al., 2005"""

        zone, coil_number = self.flow_ratio_keyword_parser(flow_ratio_zone)

        # Obtain coil obj.
        coil = self.coils[coil_number - 1]
  
        areas = {
            "top": ((np.pi/8) * (coil.inner_radius*2 + coil.outer_radius*2) * self.coil_sep_height),
            "side": self.cross_sectional_area - (np.pi*coil.outer_radius**2),
            "core": np.pi*coil.inner_radius**2
        }
        
        if coil_number != 4 or zone != "top":
            return areas[zone]

        # We take a similar approach for the top coil (#4). Now the radius is the furnace radius. The height is computed by stacking all the coils.
        radius = self.radius

        coil_heights = sum(coil.height for coil in self.coils)
        coil_separator_heights = (len(self.coils) - 1) * self.coil_sep_height
        channel_height = self.height - (coil_separator_heights + coil_heights)
        
        areas["top"] = ((np.pi/8) * (self.radius*2) * (channel_height))

        return areas[zone]

    def get_characteristic_length(self,
                                  flow_ratio_zone):
        """As implmented in Zhang et al., 2005. Analogous to get_flow_channel_area"""

        zone, coil_number = self.flow_ratio_keyword_parser(flow_ratio_zone)

        # Obtain coil obj.
        coil = self.coils[coil_number - 1]
  
        length = {
            "top": coil.outer_radius - coil.inner_radius,
            "side": coil.height + 0.25*self.coil_sep_height,
            "core": coil.height + 0.25*self.coil_sep_height
        }

        return length[zone]

    def get_equivalent_diameter(self,
                                flow_ratio_zone):
        """As implmented in Zhang et al., 2005. Analogous to get_flow_channel_area"""

        zone, coil_number = self.flow_ratio_keyword_parser(flow_ratio_zone)

        # Obtain coil obj.
        coil = self.coils[coil_number - 1]

        # Top corresponds to the convection plate passages. 
        diameter = {
            "top": (np.pi * self.coil_sep_height 
                    * ( (coil.inner_radius / (np.pi*coil.inner_radius + 2*self.coil_sep_height) )+
                        (coil.outer_radius / (np.pi*coil.outer_radius + 2*self.coil_sep_height) ) )),
            "side": 2*(self.radius - coil.outer_radius),
            "core": 2*coil.inner_radius
        }

        return diameter[zone]

    def flow_ratio_keyword_parser(self,
                                  flow_ratio_zone):
        """Returns zone and coil number."""
        
        # Characterize coil
        keywords = flow_ratio_zone.split("-")
        zone = "side" if keywords[2] == "sides" else keywords[2]
        coil_number = int(keywords[1])

        return zone, coil_number

    def get_convection_coefficient(self, 
                               temperature, 
                               flow_ratio_zone):
        """
        Calculates convection coefficient as in Haitao Z. et al. 

        @param 
        flow_fraction: Name for the region of the coil boundary.
        """

        # As seen in Table 1 of Yang X. et al. Coil 4 has identical sides and top values. 
        flow_ratio_zones = {
            "coil-0-top": 20.2, # There is no flow under the first coil
            "coil-1-top": 20.2,
            "coil-1-sides": 100,
            "coil-1-core": 100,
            "coil-2-top": 14.6,
            "coil-2-sides": 79.8,
            "coil-2-core": 79.8,
            "coil-3-top": 10.9,
            "coil-3-sides": 65.2,
            "coil-3-core": 65.2,
            "coil-4-top": 54.3,
            "coil-4-sides": 54.3,
            "coil-4-core": 54.3,
        }

        # Table entries are percentages; velocity requires a fraction of total flow.
        flow_ratio = flow_ratio_zones[flow_ratio_zone] / 100.0
        if flow_ratio == 0:
            return 0.0

        # Use helper functions to calculate h's parameters
        channel_area = self.get_flow_channel_area(flow_ratio_zone)
        velocity = (self.gas_flow * flow_ratio) / channel_area
        diameter = self.get_equivalent_diameter(flow_ratio_zone)
        length = self.get_characteristic_length(flow_ratio_zone)

        h = (0.023 * self.vortex_enhancement * velocity**0.8 / diameter**0.2
             * self.gas.thermal_conductivity(temperature)
             * (self.gas.dynamic_viscosity(temperature) / self.gas.density(temperature))**-0.8
             * (1 + (diameter / length)**0.7))
        
        return h * (self.radiation_enhancement if temperature >= 800 else 1.0)
