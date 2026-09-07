from dataclasses import dataclass


@dataclass(frozen=True)
class GasPlant:
    """
    Representative natural-gas power plant.

    Attributes
    ----------
    heat_rate_mmbtu_mwh: float
        Gas turbine heat rate in MMBtu/MWh.
    variable_om_mwh: float
        Variable operation and maintenance cost per MWh.
    carbon_intensity_tco2_mwh: float
        Emitted mass of CO2 per MWh.
    """
    heat_rate_mmbtu_mwh: float = 7.0
    variable_om_mwh: float = 3.0
    carbon_intensity_tco2_mwh: float = 0.35

    def marginal_cost(
        self,
        gas_price_mmbtu: float,
        carbon_price_tco2: float = 0.0,
    ) -> float:
        """
        Calculates gas plant marginal generation cost.

        Parameters
        ----------
        gas_price_mmbtu : float
            Natural gas price in USD/MMBtu.
        carbon_price_tco2 : float, default=0.0
            Carbon price in USD/tCO2.

        Returns
        -------
        float
            Marginal generation cost in USD/MWh.
        """
        fuel_cost = gas_price_mmbtu * self.heat_rate_mmbtu_mwh
        carbon_cost = self.carbon_intensity_tco2_mwh * carbon_price_tco2

        return fuel_cost + self.variable_om_mwh + carbon_cost

    @staticmethod
    def nuclear_gas_spread(
        nuclear_cost_mwh: float,
        gas_cost_mwh: float,
    ) -> float:
        """
        Calculates the marginal-cost spread between gas and nuclear generation.

        Parameters
        ----------
        nuclear_cost_mwh : float
            Nuclear marginal generation cost in USD/MWh.
        gas_cost_mwh : float
            Gas marginal generation cost in USD/MWh.

        Returns
        -------
        float
            Gas cost minus nuclear cost in USD/MWh.
            Positive values indicate a nuclear cost advantage.
        """
        return gas_cost_mwh - nuclear_cost_mwh

    def breakeven_gas_price(
        self,
        nuclear_cost_mwh: float,
        carbon_price_tco2: float = 0.0,
    ) -> float:
        """
        Calculate the natural-gas price at which gas and nuclear
        have equal marginal generation costs.

        Parameters
        ----------
        nuclear_cost_mwh : float
            Nuclear marginal generation cost in USD/MWh.
        carbon_price_tco2 : float, default=0.0
            Carbon price in USD/tCO2.

        Returns
        -------
        float
            Breakeven natural-gas price in USD/MMBtu.
        """
        carbon_cost = self.carbon_intensity_tco2_mwh * carbon_price_tco2

        return (
            nuclear_cost_mwh
            - self.variable_om_mwh
            - carbon_cost
        ) / self.heat_rate_mmbtu_mwh
