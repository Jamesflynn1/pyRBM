# Rule Matching

Rule matching is an algorithm to generate a set of subrules provided a single rule with typed slots (see the Rules-Based system section) and set of typed compartments. 


## Rule Matching Examples
### A production rule example

### A transport rule example

In a transport rule, the utility of such a method is even more evident.

Consider a movement rule, $\mathcal{R}$, of an infected person in the SIR epidemology model:

$I_1 \xrightarrow[]{r_{slot_1slot_2}} I_2$

where $I_1$ is the infected in the slot 1 compartment and $I_2$ is the infected in the slot 2 compartment.

In addition, consider the following compartments set L:

$L = \{N, E, S, W\}$

with each compartment of type "Region", and containing $S$, $I$, $R$ species.

Then, the rule matching algorithm for rule $\mathcal{R}$ on compartment set $L$ will generate the following set of subrules.

$\mathcal{S} = \{\mathcal{R}_{N,E}, \mathcal{R}_{N,S}, \mathcal{R}_{N,W}, \mathcal{R}_{E, N},\mathcal{R}_{E, S} ,\mathcal{R}_{E, W},$
$\mathcal{R}_{S, N},\mathcal{R}_{S, E} ,\mathcal{R}_{S, W}, \mathcal{R}_{W, N},\mathcal{R}_{W, E} ,\mathcal{R}_{W,S} \}$


Rather than defining all 12 subrules, each with a distinct propensity function, a single rule is defined with propensity matching generating the subrules. 

The propensity function rate $r_{slot_1slot_2}$ changes depending on which slots were matched by subsituting the text of "slot_1" and "slot_2" with the compartment names (e.g. with N and E).

## Rule Matching and Networks

### Defining Connectivity between Compartments

In Complex Systems, the spatial structure of a model is often described using the language of Network Theory. Often it is not possible for species to move directly between any two compartments, even though a rule exists that permits this in general.

Examples of this include, 



At the moment, pyRBM does not support the direct utilsation of adjacency graphs, however, it is simple to encode the adjancency information into a pyRBM model.

### Default behaviour: Multi-partitie graphs



