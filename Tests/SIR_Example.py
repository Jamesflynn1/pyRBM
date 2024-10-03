import datetime

import pyRBM.Core.Model as Model
import pyRBM.Build.Compartment as Compartments
import pyRBM.Build.RuleTemplates as BasicRules
import pyRBM.Simulation.Solvers as Solvers


epiClasses = [["S", "people"], ["I", "people"], ["R", "people"]]

class EpiCompartment(Compartments.Compartment):
    def __init__(self, name:str, initial_infected, total_population, constants = None):
        # Provides a list of constants that should be set (optional, but will provide a useful error
        # message if unset).
        if constants is None:
            constants = ["infectivity_rate", "recovery_rate", "mortality_rate"]

        super().__init__(name, comp_type="EpiComp", constants=constants)
        # Crops exist in three stages in this simplified model: planted, growing and harvested.
        class_labels = [class_entry[0] for class_entry in epiClasses]
        self.addClassLabels(class_labels)

        self.setInitialConditions({"S":total_population-initial_infected,
                                   "I":initial_infected})
        

def epiLocations(args):
    single_epi_comp = EpiCompartment("Example_SIR_Model", initial_infected=5, total_population=100,
                                     constants={"infectivity_rate" : 0.4,
                                                "recovery_rate" : 0.1,
                                                "mortality_rate" : 0.3 })
    return single_epi_comp


def epiRules(args):
    infection = BasicRules.SingleLocationProductionRule("EpiComp",
                                                        "S", 1,
                                                        "I", 1,
                                                       "S*(I/(S+I+R))*comp_infectivity_rate", ["S", "I","R"],
                                                       "Infection of Susceptible")
    recovery = BasicRules.SingleLocationProductionRule("EpiComp",
                                                       "I", 1,
                                                       "R", 1,
                                                       "I*comp_recovery_rate", "I", 
                                                       "Recovery of Infected")
    death = BasicRules.ExitEntranceRule("EpiComp",
                                        "I", -1,
                                        "I*comp_mortality_rate", "I",
                                        "Death of Infected")
    return  (infection, recovery, death)





model = Model.Model("Basic Epi Model")
model.buildModel(epiClasses, epiRules, epiLocations, write_to_file = True, save_model_folder="Tests/ModelFiles/")
# Use no_rules_behaviour = "exit" when the model is constructed  such that states where the model has zero propensity are all
# absorbing states (e.g. models with no time based model state variables in any propensity).
model_solver = Solvers.GillespieSolver(debug=True, no_rules_behaviour="end")

model.initializeSolver(model_solver)

start_date = datetime.datetime(2001, 8, 1)

# Close the matplotlib window to continue to the next simulation
model.simulate(start_date, 40, 100000)
model.trajectory.plotAllClassesOverTime(0)
print(model.trajectory.trajectory_compartment_values[0][-1])
model.simulate(start_date, 40, 100000)
model.trajectory.plotAllClassesOverTime(0)
model.simulate(start_date, 40, 100000)
model.trajectory.plotAllClassesOverTime(0)
model.simulate(start_date, 40, 100000)
model.trajectory.plotAllClassesOverTime(0)

model.trajectory.plotAllClassesOverTime(0)
model.simulate(start_date, 40, 100000)
print(model.trajectory.trajectory_compartment_values[0][-1])

model.printSimulationPerformanceStats()

