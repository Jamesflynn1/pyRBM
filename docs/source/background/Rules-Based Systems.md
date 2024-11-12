# Rules-Based Systems

The amount of each species at time $t$ is described by a system's.

Each rule is triggered probabilistically with an expected frequency proportional to its propensity function, $\Phi(X)$. 

When a rule is triggered the system evolves by incrementing (in the case of the rule "products") and decrementing (in the case of the rule "reactants") each species by a fixed amount. The exact amount is described in the stochiometry matrix of the rule $C:\mathbb{R}^{n * n}$.

## Propensity functions

Propensity functions 

### Mass Action

The principle of mass action is the physically observed relation between the concentration of reactants and the propensity of a reaction to occur.

### Behaviour at Zero

For physically based systems, a non-negativity constraint is often desired for each species. To acheive this, the propensity function should be zero for 

### Constant Functions

A constant propensity function leads to the rule behaving as a Possion point process for each of the products of the rule. Note: the reactants will continue to be decremented past zero.

## Rule Slots
For simplicity, pyRBM partitions the propensity function and stochiometry into "slots". Each slot can be filled by a single compartment as long as the compartment type satisfies the slot type (i.e. is equal to). For information on how this is done, see the rule matching sectuion. The overall propensity function of a rule is the product of all its slot's propensity functions, and the overall stochiometry matrix is each slot's stochiometry matrix vertically stacked.

More concretely:

Given a rule with k slots, $X_i$ TODO, slot propensity functions for each slot $\phi_i:\mathbb{R}^{n_k} \rightarrow \mathbb{R}^+$ and stoichiometry matrices for each slot $C_i$. 

Define the overall propensity function:

$\Phi(X) = \prod^k_{i=1}\phi_i(X_i)$

where $X_i$ is the elements of $X$ starting at the $\sum^{i-1}_{p=1}n_p$ element and ending at the $\sum^{i}_{p=1}n_p$ element. 

Define the overall stochiometry function as:

C = $\begin{bmatrix}
C_1\\
C_2\\
..\\
C_k
\end{bmatrix}$


For each rule slot, define a type requirement. Based on this type requirement. It is required that a matching compartment re
## Sub-rules

A sub-rule describes a. 

To create 

## Common Rules

### Production Rules
A production rule takes reactants (in a ratio determined by the rule stochiometry) and forms products (in a ratio determined by the rule stochiometry). A species belongs to either the set of reactants or the set of products depending on if the stochiometric coefficent is either positive or negative 


### Transport Rules

Another common class of rules are transport rules. This rule doesn't change the total amount of a species, rather, it changes the distribution of a species across different compartments. The simplest such rule is the, single source, single target, and single species transport rule.

To describe the rule using chemical reaction arrow notation, and for a rule moving a member of population A from compartment of type 1 to compartment of type 2 with a rate coefficient $r_1$:

$A_1 \xrightarrow[]{r_1} A_2$

Recalling that the chemical reaction notation describes a mass-action based reaction, the propensity function of the following reaction is:

$\Phi(X) = r_1A_1 = r_1A_1\times1 = \phi_1(X_1)\times\phi_2(X_2)$ 

A concrete example of this could be the movement of a unit of flour between a milling plant and a bakery (in the context of a supply chain model). Denoting F as a tonne of flour (or the highest resolution of the weight of flour suitable for the modelling needs).

$A_1 \xrightarrow[]{r_1} A_2$

For an accurate model, a more complex propensity function will be required, taking into account competition in the baked goods market, demand for bakery products and 

### Entrance and Exit Rules

Entrance rules describe the inflow into the system of a species. Exit rules describes the outflow out of the system of a species. A good example of these rules would be birth rules and death rules in a demography model (modeling a population $P$). Note the empty set is used to take the place of no reactants/no products (this is a standard convention).

Birth Rule:

$\phi \rightarrow P$


Death Rule:

$P \rightarrow \phi$


## Global Variables

Global variables is shared information, accessible by all compartments and useful to be used in a rule propensity function. The evolution of global variables is independent of rules, and could be driven by a range of external influences. Currently, pyRBM supports a predefined time series of variable values, variable changes that happen with certain reoccurences (e.g. monthly) and dynamically triggered value changes (e.g. a simulation event adds a future variable change to the queue).

The best example of a global variable is time-derived global variables. This could include an indicator as to whether the month is June, the current day of the year or the current hour of the day. Note that the day of the year includes precision to the near minute, updating any more regularly would be computational cumbersome.

The extension for a Rules-Based system that includes global variables, $V$, is relatively straightforward. Each $X_i$ component vector is replaced with $\hat{X}_i = \begin{bmatrix} X_i \\ V\end{bmatrix}$ and then each $\phi_i(\hat{X}_i):\mathbb{R}^{n_k+v} \rightarrow \mathbb{R}^+$ is allowed to depend on the global variables.
