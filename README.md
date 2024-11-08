# pyRBM: a Python Rules-Based modelling framework

pyRBM is a Python framework to build and simulate stochastic Rules-Based models simply and efficently.

## What is Stochastic Rules-Based modelling?

Rules-Based modelling offers an easy to understand modelling framework that can be used in place of or supplement traditional ODE-based modelling. When considering a large number of reacting species, the ODE and rules-based approaches lead to similar results and the computationally faster ODE's should be used. However, when considering a small number of reacting species, stochastic effects become evident. Here, the spread of outcomes (or realisations of all processes) for the model is noticeable. The small differences in event timing could (depending on the model rules) lead to drastically different outcomes, differences that are unseen from an ODE modelling approach.

## What does unique features pyRBM offer over other libraries?

- Rule matching, a new system of creating subrules from a rule and permutations of valid compartments (validity based type compartment types matching ). This system also allows the propensity function to have dependency on the name of each compartment matching (name that fills the slot).
- propensity functions defined in SymPy, allowing common mathematical functions and variables to be utilised in the rule propensities (e.g. sin, cos, pi).
- Global state variables such as time, calandar information. pyRBM utilses a calandar system allowing precise seasonal information to be used directly in the model, and changing the start 
- Propensitiy caching compatible with all pyRBM enhancements (model state variables, SymPy propensities and subrules) utilsing analysis extended from Gibbson et al.
- a range of simulation algotithms and simulation customisation with a single Solver interface that can be extended to build custom simulation algorithms, inclduing the Laplace Gillespie algorithm which .
- 
## Are there examples of models using the framework?

For API reference please see the documentation site: https://pyrbm.readthedocs.io/en/latest/index.html

## How can I contribute a model/simulation algorithm/improvement?

Feedback and suggestions are welcome (either create an issue or start a discussion), please see Contributing.md for more information


## What state is the framework in?

The framework is in pre-alpha development and much code is lightly tested.

Use of the framework is at the users risk (please see license conditions).


### Known Issues:
There are no known issues with the framework, if any issues are encountered, please raise an issue or reach out to me at jameswflynn@hotmail.co.uk.
