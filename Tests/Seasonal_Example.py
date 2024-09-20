import datetime

import pyRBM.Core.Model as Model
import pyRBM.Build.Compartment as Compartments
import pyRBM.Build.RuleTemplates as BasicRules
import pyRBM.Simulation.Solvers as Solvers


model_classes = [["Source_Var", "units"],
              ["Target_Var", "units"]]

class ExampleCompartment(Compartments.Compartment):
    def __init__(self, name:str, constants = None, source_starting_num = 1000):
        # Sets lat/long and creates and empty set of compartment labels.

        super().__init__(name, comp_type="Comp", constants=constants)
        # Crops exist in three stages in this simplified model: planted, growing and harvested.
        class_labels = [class_entry[0] for class_entry in model_classes]
        self.addClassLabels(class_labels)
        
        self.setInitialConditions({"Source_Var":source_starting_num, "Target_Var":0})


def exampleRules():
    seasonal_production = BasicRules.SingleLocationProductionRule("Comp",
                                                        "Source_Var", 1,
                                                        "Target_Var", 1,
                                                       "model_month_feb", "Source_Var",
                                                       "Seasonal Source to Target Production")
    return  seasonal_production

def exampleCompartments():
    single_comp = ExampleCompartment("Example_Name")
    return single_comp

model = Model.Model("Basic Epi Model")
model.buildModel(model_classes, exampleRules, exampleCompartments, write_to_file = True, save_model_folder="Tests/ModelFiles/")
model_solver = Solvers.GillespieSolver(debug=True)
model.initializeSolver(model_solver)

start_date = datetime.datetime(2001, 1, 1)

model.simulate(start_date, 365*2, 10000)

print(model.model_state.model_classes)

model.printSimulationPerformanceStats()
model.trajectory.plotAllClassesOverTime(0)
