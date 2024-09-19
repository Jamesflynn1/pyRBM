import datetime

import pyRBM.Core.Model as Model
import pyRBM.Build.Compartment as Compartments
import pyRBM.Build.RuleTemplates as BasicRules
import pyRBM.Simulation.Solvers as Solvers


epiClasses = [["S", "people"], ["I", "people"], ["R", "people"]]

class EpiCompartment(Compartments.Compartment):
    def __init__(self, name:str, constants = None):
        # Sets lat/long and creates and empty set of compartment labels.
        if constants is None:
            constants = ["infectivity_rate", "recovery_rate", "mortality_rate"]
        super().__init__(name, comp_type="EpiComp", constants=constants)
        # Crops exist in three stages in this simplified model: planted, growing and harvested.
        class_labels = [class_entry[0] for class_entry in epiClasses]
        self.addClassLabels(class_labels)


def epiRules():
    infection = BasicRules.SingleLocationProductionRule("EpiComp",
                                                        "S", 1,
                                                        "I", 1,
                                                       "S*I*comp_infectivity_rate", ["I","S"],
                                                       "Infection of Susceptible")
    recovery = BasicRules.SingleLocationProductionRule("EpiComp",
                                                       "I", 1,
                                                       "R", 1,
                                                       "I*comp_recovery_rate", "I", 
                                                       "Recovery of Infected")
    death = BasicRules.ExitEntranceRule("EpiComp",
                                        "I", 1,
                                        "I*comp_mortality_rate", "I",
                                        "Death of Infected")
    return  [infection, recovery, death]

def epiLocations():
    single_epi_comp = EpiCompartment("Example_Name", constants={"infectivity_rate" : 0.1,
                                                                "recovery_rate" : 0.2,
                                                                "mortality_rate" : 0.3 })
    return [single_epi_comp]

model = Model.Model("Basic Epi Model")
model.buildModel(epiClasses, epiRules, epiLocations, write_to_file = True, save_model_folder="Tests/ModelFiles/")
model_solver = Solvers.GillespieSolver(debug=True)
model.initializeSolver(model_solver)

start_date = datetime.datetime(2001, 8, 1)

model.simulate(start_date, 10000, 10000)


model.printSimulationPerformanceStats()
model.trajectory.plotAllClassesOverTime(0)
