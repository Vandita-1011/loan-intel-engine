# Scenario Analysis Report

*Generated: 2026-08-31 01:11*

## Methodology
- Monte Carlo simulation with 1,000 draws per scenario per quarter
- 8 quarters projected forward
- Base transition matrix from observed Markov chain
- Macro multipliers applied to default and prepayment hazard rates

## Scenario Definitions
| Scenario | Description |
|---|---|
| base | Current economic conditions, no shocks |
| adverse_credit | Rising rates, rising unemployment, falling home prices |
| high_prepayment | Falling rates, strong economy, accelerated prepayment |

## Projected Rates (Final Quarter)
| Scenario | Delinquency Rate | Default Rate | Prepayment Rate |
|---|---|---|---|
| base | 10.88% | 3.13% | 4.15% |
| adverse_credit | 17.92% | 4.76% | 3.42% |
| high_prepayment | 9.35% | 2.85% | 9.30% |

## Segment Breakdown (by Credit Band)
| Credit Band | # Loans | Base Delinq | Adverse Delinq | Base Default | Adverse Default |
|---|---|---|---|---|---|
| 620-660 | 1,533 | 17.41% | 28.67% | 5.01% | 7.62% |
| 660-700 | 3,033 | 15.78% | 25.98% | 4.54% | 6.90% |
| 700-740 | 4,528 | 14.14% | 23.30% | 4.07% | 6.19% |
| 740-780 | 2,920 | 12.51% | 20.61% | 3.60% | 5.47% |
| 780+ | 2,241 | 10.88% | 17.92% | 3.13% | 4.76% |
| <620 | 745 | 19.04% | 31.36% | 5.48% | 8.33% |
