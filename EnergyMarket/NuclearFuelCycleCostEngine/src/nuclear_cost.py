from dataclasses import dataclass


@dataclass(frozen=True)
class PWR:
    """
    Parameters describing a representative PWR.

    Attributes
    ----------
    thermal_power_mw : float
        Reactor thermal power in MWth.
    thermal_efficiency : float
        Thermal-to-electrical conversion efficiency. [0, 1]
    capacity_factor : float
        Fraction of the year the reactor operates at rated power. [0, 1]
    burnup_mwd_per_kg : float
        Fuel discharge burnup in MWd/kgHM.
    """
    thermal_power_mw: float = 3400.0
    thermal_efficiency: float = 0.33
    capacity_factor: float = 0.90
    burnup_mwd_per_kg: float = 45.0

    @property
    def electrical_power_mw(self) -> float:
        """ Calculates nominal electrical output in MWe. """
        return self.thermal_power_mw * self.thermal_efficiency

    @property
    def annual_generation_mwh(self) -> float:
        """ Calculates annual electrical generation in MWh. """
        return self.electrical_power_mw * self.capacity_factor * 8760

    @property
    def annual_fuel_requirement_kg(self) -> float:
        """ Estimates annual enriched uranium requirement in kgHM. """
        thermal_generation = self.thermal_power_mw * self.capacity_factor * 365
        return thermal_generation / self.burnup_mwd_per_kg
