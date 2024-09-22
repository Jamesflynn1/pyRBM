import datetime

import pyRBM.Core.Model as Model
import pyRBM.Build.Compartment as Compartments
import pyRBM.Build.RuleTemplates as BasicRules
import pyRBM.Simulation.Solvers as Solvers


model_classes = [["Source_Var_1", "units"],
              ["Target_Var_1", "units"],
              ["Source_Var_2", "units"],
              ["Target_Var_2", "units"]]

class ExampleCompartment(Compartments.Compartment):
    def __init__(self, name:str, constants = None, source_starting_num = 1000):
        # Sets lat/long and creates and empty set of compartment labels.

        super().__init__(name, comp_type="Comp", constants=constants)
        # Crops exist in three stages in this simplified model: planted, growing and harvested.
        class_labels = [class_entry[0] for class_entry in model_classes]
        self.addClassLabels(class_labels)
        
        self.setInitialConditions({"Source_Var_1":source_starting_num,
                                   "Target_Var_1":0,
                                   "Source_Var_2":source_starting_num,
                                   "Target_Var_2":0,
                                   })


def exampleRules():
    seasonal_production_1 = BasicRules.SingleLocationProductionRule("Comp",
                                                        "Source_Var_1", 1,
                                                        "Target_Var_1", 1,
                                                       "(model_month_feb + model_month_mar + model_month_nov) * Source_Var_1/1000", "Source_Var_1",
                                                       "Seasonal Source to Target Production")
    seasonal_production_2 = BasicRules.SingleLocationProductionRule("Comp",
                                                    "Source_Var_2", 1,
                                                    "Target_Var_2", 1,
                                                    "sin(10*2*pi*model_yearly_day/365) * Source_Var_2/1000", "Source_Var_2",
                                                    "Seasonal Source to Target Production")
    return  (seasonal_production_1, seasonal_production_2)

def exampleCompartments():
    single_comp = ExampleCompartment("Example_Name")
    return single_comp

model = Model.Model("Basic Epi Model")
model.buildModel(model_classes, exampleRules, exampleCompartments, write_to_file = True, save_model_folder="Tests/ModelFiles/")
model_solver = Solvers.HKOSolver(debug=True)
model.initializeSolver(model_solver)

start_date = datetime.datetime(2001, 1, 1)

model.simulate(start_date, 365*2, 10000)
model.simulate(start_date, 365*2, 10000)
model.simulate(start_date, 365*2, 10000)

print(model.model_state.model_classes)

model.printSimulationPerformanceStats()
model.trajectory.plotAllClassesOverTime(0)
