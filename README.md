
What does this project do?
Why is this project useful?
How do I get started?
Where can I get more help, if I need it?


The framework is in pre-alpha development and components are lightly tested, if at all - use of the framework is at the users risk. Any feedback or suggestions for improvement is welcome (either create an issue or start a discussion.

# Implemented Features
### Core:
- Model created and validated from a list of user defined classes, a function that returns a list of Build.Locations and a function that returns a list of Build.Rules.
- Validation that rules can be triggered, locations are matched to rules have the constants and the user defined classes that are required by the rule (i.e. used in either the propensity function), the propensity function evaluates to a number when the  
- Save the model locations, classes, rules and matched rules to json file.
- Load the model locations, classes and matched rules from the created json file for simulation.
- Simulate upto a time point subject to a maximum iteration threshold.

### Rules: 
- "Metarule" definition allows the creation of multiple matched rules - as long as the target in the rule matches the type of the location. At the moment a location can match in different target slots across different matchings but only one slot in a matching.
- Rules allow for multiple locations and the propensities and stoichiometry supports multi-location rules
- Sympy propensity functions using user defined compartments, user defined constants attached to a location (prefixed with loc_) and model state values (currently just time based, prefixed with model_).
- Stoichiometry allowing user defined compartments to change (currently just by a constant value).
- Note: the rules may not precisely satisfy the Gillespie algorithm, it is upto the user to ensure it does at the moment (or just hope).

### RuleTemplates:
- SingleLocationRule: Provides a wrapper to simplify the creation of a rule based on a single location.
- SingleLocationProductionRule: Provides a wrapper to simplify the creation of a rule at a single location where any number of reactants form any number of products (i.e. a production rule).
- TransportRule: Provides a wrapper to simplify the creation of a rule where a single compartment moves from a single location to another.
- ExitEntranceRule: Provides a wrapper to simplify the creation of a rule where an amount of a single compartment leaves or enters (depending on the positive or negative transport_amount) the system, at a given location.

### Locations:
- Define per location constants and per location initial values.

### Classes:
- Define the name, unit and an optional (unused) description of the class.

### RuleChain:
- Compute the compartment values that will change given a rule and the locations (index set from rule matching) that trigger it - used to work out which propensities to update.

### Solvers:
- Generic solver interface - extend from this to create own solvers.
- Classic Gillespie algorithm with propensity caching (only update the value of the propensity when the underlying symbol value changes.
- A default behaviour to execute when no rules have any propensity (either step or exit). Step is useful for seasonal models.

### Trajectory:
- Store the values of all user defined compartments, partitioned by location - stores a data point before and after a change in value only.
- Basic matplotlib plot of values at a location.

# Known issues:
- Model state variables don't trigger a recomputation of propensities when propensity_caching = True.
- Executing simulate twice leads to an error, reinitialising the solver before second execution fixes it for now!
