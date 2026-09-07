# Problem Statement

This project studies the impact of changes in a Nuclear Power Plant fuel cost and how it propagates through the plant economics and electricity prices, generating trading opportunities.
A nuclear power plant cost includes a fixed and a variable cost.
The variable cost accounts for the fuel cost.
This work computes the spread between the variable cost of nuclear power plant and a gas plant.
It also investigates the correlation between electricity prices and this spread.
Finally, it proposes a trading strategy to leverage the studied correlations.


# Studies

1) Nuclear Economics model:
    * Uranium price -> fuel-cycle cost -> $/MWh nuclear generation cost
    * Some basic sensitivity studies
2) Market model:
    * combines fuel costs with natural gas
    * Some more sensitivity studies
3) Quant strategy:
    * generate signals from model,
    * investigates Sharpe ratio and max drawdown


# Using this repo

Create python environment:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
and run `analysis.ipynb`.

Sometimes you need to make the new python environment visible to Jupyter Notebook:
```
python -m ipykernel install --user --name nuclear-quant --display-name "Python (Nuclear Quant)"
```


# Models

## Value Function

The following function is used to calculate the SWUs:
$$
V(x) = (1 - 2x) ln(\frac{1-x}{x})
$$


## Enrichment Mass Balance

Mass balance:
$$
F = P + T
$$
where $F$ is the feed mass, $P$ is the product mass, and $T$ is the tail mass.
All values are expressed in kg.

Mass balance of U235:
$$
F x_F = P x_P + T x_T
$$
where $x_i$ is the mass fraction of U235 in $i = {F, P, T}$.


## Separative Work Unit (SWU)

This defines how much work is needed to enrich U:
$$
SWU = P \cdot V(x_p) + T \cdot V(x_t) - F \cdot V(x_f)
$$


## Fuel Cycle Cost

$$
C_{fuel} = C_U + C_{conv} + C_{enr} + C_{frab}
$$
where $C_U$ is the uranium procurement cost, $C_{conv}$ is the conversion cost, $C_{enr}$ is the enrichment cost, and $C_{fab}$ is the fabrication cost.

$$
C_U = P_U \cdot 0.383 \cdot F
$$
where $P_U$ is the U3O8 price per lb, $0.383$ is the conversion factor to go from U3O8 to U.

$$
C_{conv} = P_C \cdot F
$$
where $P_C$ is the conversion price per kg.

$$
C_{enr} = P_{SWU} \cdot SWU
$$
where $P_{SWU}$ is the SWU price.

$$
C_{frab} = P_{fab} \cdot P
$$
where $P_{fab}$ is the fabrication cost.


## Reactor Cost

Assumptions:
* 1.1 GWe PWR
* 33\% thermal efficiency
* 90\% capacity factor
* 45 MWd/kgHM burnup
* 4.5% enrichment
* 0.25% tails

Annual Generation:
$$
E_{annual​} = P_{thermal​} \cdot \eta \cdot CF \cdot 8760
$$
where $P_{thermal​}$, $\eta$ is the thermal-to-electricity conversion efficiency, and $CF$ is the capacity factor.

Fuel cost per MWh:
$$
C_{fuel/MWh} = \frac{C_{fuel}}{E_{annual​}}
$$


## Gas Cost

$$
MC_{gas} = P_{gas} \cdot HR_{gas} + V_{\text{O \& M}} + P_{CO_2} \cdot m_{CO_2}
$$
where $P_{gas}$ is the gas price per MMBtu, $HR_{gas}$ is the heat rate in
MMBtu/MWh,  $V_{\text{O \& M}}$ is the variable operation and maintenance cost per MWh, $P_{CO_2}$ is the price per metric ton of CO$\_2$, and $m\_{CO_2}$ the emitted mass of CO$\_2$ per MWh.


## Nuclear Gas Spread

The spread helps determine which one is less competitive.
$$
S = MC_{gas} - MC_{nuclear}
$$
If S > 0, gas is more expensive than nuclear.
If S < 0, nuclear is more expensive than gas.


# Data

Historical U3O8 price:
* Source: [numerco](https://numerco.com/UHistory/)
* Daily prices
* Columns: "Date","FIP","U3O8"
* Column "U3O8" contains the spot price

Historical Gas price:
* Source: [Natural Gas Spot Price - Henry Hub](https://www.eia.gov/dnav/ng/hist/rngwhhdM.htm)
* Monthly prices
* Skip first 4 rows
* Columns: "Month","Henry Hub Natural Gas Spot Price Dollars per Million Btu"

Historical Electricity price:
* [PJM Electricity Price]: https://www.eia.gov/electricity/wholesalemarkets/csv/pjm_lmp_da_hr_zones_{year}.csv
* Columns: "UTC", "Allegheny Power System LMP"

Assumptions:
* SWU Price: $100/SWU
* Carbon Price: $40/tCO2 (assumes power plant in New Jersey)


# Statistical Research

F-statistic:
* In OLS, we start with the total variation in $Y$. The regression explains some of that variation, while some remains unexplained.
  * Total variation = Explained variation + Unexplained variation
* The F-statistic compares the explained variation to the unexplained variation.
  * F = Explained variation / Unexplained variation
* A large F means the regression explains a lot relative to what it leaves unexplained.
* A small F means the regression explains relatively little.
* In other words, for a liner regression: $Y = \beta_0 + \beta_1 X_1 + \epsilon$
* The F-test tests: $H_0: \beta_1 = 0$ vs $H_A: \beta_1 \neq 0$
* An F close to 1 means the model shows no real effect beyond random chance, while a much larger F-value indicates a statistically significant result.

T-statistic:
* For a linear regression: $Y = \beta_0 + \beta_1 X + \epsilon$
* We want to know whether X actually has a relationship with $Y$
* The null hypothesis is: $H_0: \beta_1 = 0$
* The t-statistic compares the estimated coefficient to the amount of uncertainty around that estimate:
  * t = estimated coefficient/standard error of the coefficient
* Large |t|: the estimated coefficient is large relative to its uncertainty --> stronger evidence that $\beta_1 \neq 0$
* Small |t|: the estimated coefficient is small relative to its uncertainty --> weaker evidence that $\beta_1 \neq 0$
* The farther the t-statistic is from zero (positive or negative), the stronger the evidence that your result is real and not just random luck.
* $t = \frac{\bar{x} - \mu_0}{SE(\bar{x})}$
* where $\bar{x}$ is the sample mean, $\mu_0$ is the hypothesized population mean (0 in this case), and $SE(\bar{x})$ is the standard error of the mean.
* $SE(\bar{x}) = s/\sqrt{n}$
* where $s$ is the sample standard deviation and $\sqrt{n}$ is the standard deviation.

p-value:
* It tells how unusual your observed result is under the null hypothesis.
  * small p-value: the result would be unusual if $H_0$ were true --> evidence against $H_0$
  * large p-value: the result would not be particularly unusual if $H_0$ were true --> not strong evidence against $H_0$
* The p-value is answering: "Given these data, what is the probability that H0 is true?". This is P(data|$H_0$).


# Financial Terms

* Strategic Profit and Loss (P&L) approach: uses financial information to guide business strategy and decision-making rather than simply reporting past performance. It focuses on understanding the key drivers of revenue, costs, margins, and profitability, while analyzing performance across products, customers, regions, or business units. By linking strategic initiatives to their financial impact, tracking key performance indicators, and using scenarios to assess future outcomes, management can identify opportunities, control costs, improve profitability, and make better-informed decisions.
* Sharpe ratio: is a financial performance measure that evaluates the risk-adjusted return of an investment or portfolio. It compares the excess return earned above a risk-free rate with the investment’s volatility, showing how much additional return an investor receives for each unit of risk taken. A higher Sharpe ratio generally indicates a more attractive risk-adjusted performance, while a lower ratio suggests that the returns may not adequately compensate for the level of risk. It's calculated by taking your return, minus a safe rate like a Treasury bill, divided by the risk or volatility:
$$
Sharpe Ratio = \frac{R_p - R_f}{\sigma_p}
$$
where $R_p$ what the portfolio earns, $R_f$ what you make with zero risk, $\sigma_p$ is how much the returns bounce up and down (volatility).
  * $< 1$: low return for the risk taken
  * $\ge 1$: Good
  * $\ge 2$: Very Good
  * $\ge 3$: Excellent
* Drawdown: is a measure of the decline in the value of an investment or portfolio from its highest point to its subsequent lowest point (peak-to-trough decline) over a specific period before reaching a new peak. It is used to assess the potential downside risk and the severity of losses an investor may experience during a period of poor performance. Generally, a lower drawdown is preferable because it indicates that the investment experienced smaller losses during difficult market conditions.
