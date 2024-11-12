# Propensity Caching

The idea of propensity caching (although not named as such) was introduced by Gibson et al. to speed up the execution of their Next Reaction method. Although originally used for only the Next Reaction method, propensity caching works indpendent of which Gillespie variant is used, although it requires a slight modification if multiple rules are triggered in a single method iteration (e.g. in the case of the Tau Leap method).

Propensity caching works by maintaining an up-to-date cache of the propensity value for each rule (or subrule). 

By analysing the stochiometry of the rule selected in the previous iteration (and therefore exactly which species change), and the dependency in the propensity function of all rules (and therefore exactly which species would cause each rule's propensity function to change),  the 

## Why is Propensity Caching useful and which models benefit the most?

Propensity caching improves the asymptotic runtime of the propensity update step from O() to O()


It is clear then, that in pratice certain models benefit more from propensity caching than others. 

## How does Propensity Caching work in pyRBM?

