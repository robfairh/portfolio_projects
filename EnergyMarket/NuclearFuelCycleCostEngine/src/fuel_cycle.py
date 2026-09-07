from dataclasses import dataclass
import math


@dataclass(frozen=True)
class FuelCycle:
    """
    Nuclear fuel-cycle assumptions and calculations.

    Parameters
    ----------
    uranium_price_lb : float
        Uranium concentrate price in USD/lb U3O8.
    conversion_price_kg : float
        Conversion price in USD/kgU.
    swu_price : float
        Enrichment price in USD/SWU.
    fabrication_cost_kg : float
        Fuel fabrication cost in USD/kgHM.
    feed_assay : float
        U235 mass fraction of natural uranium feed.
    product_assay : float
        U235 mass fraction of enriched uranium product.
    tails_assay : float
        U235 mass fraction of enrichment tails.
    kg_u_per_lb_u3o8: float
        how many kg of U in 1 lb of U3O8
    """
    uranium_price_lb: float = 70.0
    conversion_price_kg: float = 10.0
    swu_price: float = 150.0
    fabrication_cost_kg: float = 300.0

    feed_assay: float = 0.00711
    product_assay: float = 0.045
    tails_assay: float = 0.0025

    kg_u_per_lb_u3o8: float = 0.383

    @staticmethod
    def value_function(x: float) -> float:
        """
        Value function used in uranium enrichment calculations.

        V(x) = (1 - 2x) * ln((1-x)/x)

        Parameters
        ----------
        x : float
            Mass fraction of U-235.

        Returns
        -------
        float
            Value function.
        """
        if not 0 < x < 1:
            raise ValueError("Assay must be between 0 and 1.")
        return (1 - 2 * x) * math.log((1 - x) / x)

    def enrichment_requirements(
        self,
        product_mass_kg: float,
    ) -> dict[str, float]:
        """
        Calculate enrichment requirements.

        Parameters
        ----------
        product_mass_kg : float
            Required enriched uranium product in kgHM.

        Returns
        -------
        dict[str, float]
            Product, feed, tails, and SWU requirements.
        """
        feed_mass = product_mass_kg * (
            (self.product_assay - self.tails_assay)
            / (self.feed_assay - self.tails_assay)
        )

        tails_mass = feed_mass - product_mass_kg

        swu = (
            product_mass_kg * self.value_function(self.product_assay)
            + tails_mass * self.value_function(self.tails_assay)
            - feed_mass * self.value_function(self.feed_assay)
        )

        return {
            "product_kg": product_mass_kg,
            "feed_kgU": feed_mass,
            "tails_kgU": tails_mass,
            "swu": swu,
        }

    def cost(self, product_mass_kg: float) -> dict[str, float]:
        """
        Calculate fuel-cycle cost for a specified product mass.

        Parameters
        ----------
        product_mass_kg : float
            Required enriched uranium product in kgHM.

        Returns
        -------
        dict[str, float]
            Annual fuel-cycle costs by component and total in USD.
        """
        req = self.enrichment_requirements(product_mass_kg)

        uranium = req["feed_kgU"] / self.kg_u_per_lb_u3o8 * self.uranium_price_lb
        conversion = req["feed_kgU"] * self.conversion_price_kg
        enrichment = req["swu"] * self.swu_price
        fabrication = req["product_kg"] * self.fabrication_cost_kg

        return {
            "uranium": uranium,
            "conversion": conversion,
            "enrichment": enrichment,
            "fabrication": fabrication,
            "total": uranium + conversion + enrichment + fabrication,
        }
