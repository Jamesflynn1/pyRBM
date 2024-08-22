import pyRBM.Build.Classes as Classes
import pyRBM.Build.Locations as Locations
import pyRBM.Build.Rules as Rules
import pyRBM.Build.RuleMatching as RuleMatching
import pyRBM.Build.Utils as Utils
import pyRBM.Build.RuleTemplates as RuleTemplates

import pyRBM.Core.Json as Files

import pyRBM.Simulation.Rule as Rule
import pyRBM.Simulation.State as State
import pyRBM.Simulation.Solvers as Solvers
import pyRBM.Simulation.RuleChain as RuleChain
import pyRBM.Simulation.Trajectory as Trajectory


import time


def writeToFile():

class Model:
    def __init__(self, classes_defintions, create_locations, create_rules, write_to_file:bool = True,
                 distance_func = Utils.createEuclideanDistanceMatrix, classes_filename = "Classes.json", location_filename:str = "Locations.json", metarule_filename:str = "MetaRules.json",
                 matched_rules_filename:str = "LocationMatchedRules.json", model_folder:str = "/ModelFiles/"):
        self.classes_filename = classes_filename
        self.location_filename = location_filename
        self.metarule_filename = metarule_filename
        self.matched_rules_filename = matched_rules_filename
        self.model_folder = model_folder

        self.builtin_classes = True

        self.write_to_file = write_to_file

    def __init__(self, start_date, solver_type:str = "Gillespie", location_filename:str = "Locations.json", matched_rules_filename:str = "LocationMatchedRules.json", classes_filename:str = "Classes.json",
                 model_folder:str = "Backend/ModelFiles/", propensity_caching:bool = True, no_rules_behaviour:str = "step"):

        self.matched_rules_filename = matched_rules_filename
        self.location_filename = location_filename
        self.model_folder = model_folder
        self.classes_dict, self.builtin_classes_dict = Files.loadClasses(self.model_folder+classes_filename)
        self.locations = Files.loadLocations(self.model_folder+self.location_filename)
        self.rules, self.matched_indices = Files.loadMatchedRules(self.model_folder+self.matched_rules_filename, self.locations, num_builtin_classes=len(self.builtin_classes_dict))

        self.model_state = State.ModelState(self.builtin_classes_dict, start_date)

        self.trajectory = Rule.Trajectory(self.locations)

        
    def createLocations(self):
        all_locations = Locations.Locations(self.defined_classes, self.distance_func)
        locations = self.create_locations_func()
        all_locations.addLocations(locations)
        # Distance computation done as part of writeJSON - set as location constants
        self.locations = all_locations.writeJSON(f"{self.model_folder}{self.location_filename}")
        self.location_constants = all_locations.returnAllLocationConstantNames()

    def createRules(self):
        # Use np.identity(len()) .... for no change
        all_rules = Rules.Rules(self.defined_classes, self.location_constants)

        rules = self.create_rules_func()
        all_rules.addRules(rules)

        self.rules = all_rules.writeJSON(f"{self.model_folder}{self.metarule_filename}")

    def defineClasses(self):
        classes = Classes.Classes(self.builtin_classes)
        for class_info in self.classes_defintions:
            classes.addClass(*class_info)
        self.defined_classes = classes.writeClassJSON(f"{self.model_folder}{self.classes_filename}").keys()

    def matchRules(self):
        additional_classes = []
        if self.builtin_classes:
            additional_classes = Classes.Classes().returnBuiltInClasses()
        RuleMatching.writeMatchedRuleJSON(self.rules, self.locations, f"{self.model_folder}{self.matched_rules_filename}",
                                          additional_classes)
    
    def provideDetailsForBuilding(self, classes_defintions, create_locations, create_rules, distance_func):
        self.classes_defintions = classes_defintions
        self.create_locations_func = create_locations
        self.create_rules_func = create_rules
        self.distance_func = distance_func
    
    def buildModel(self):
        self.defineClasses()
        self.createLocations()
        self.createRules()
        self.matchRules()

        #self.model_initialized = True


    def loadModelFromJSONFiles(self, location_filename:str = "Locations.json", matched_rules_filename:str = "LocationMatchedRules.json",
                           classes_filename:str = "Classes.json", model_folder:str = "Backend/ModelFiles/"):
        
        self.matched_rules_filename = matched_rules_filename
        self.location_filename = location_filename
        self.model_folder = model_folder
        self.classes_dict, self.builtin_classes_dict = Files.loadClasses(self.model_folder+classes_filename)
        self.locations = Files.loadLocations(self.model_folder+self.location_filename)
        self.rules, self.matched_indices = Files.loadMatchedRules(self.model_folder+self.matched_rules_filename, self.locations, num_builtin_classes=len(self.builtin_classes_dict))

        self.model_state = State.ModelState(self.builtin_classes_dict, self.start_date)

        self.trajectory = Trajectory.Trajectory(self.locations)

        self.solver_initialized = False
        self.model_initialized = True

    def initializeSolver(self, solver:Solvers.Solver, propensity_caching:bool = True, no_rules_behaviour:str = "step"):
        if self.model_initialized:
            self.no_rules_behaviour = no_rules_behaviour
            self.propensity_caching = propensity_caching
            if propensity_caching:
                self.rule_propensity_update_dict = RuleChain.returnOneStepRuleUpdates(self.rules, self.locations, self.matched_indices, self.model_state.returnModelClasses())
            else:
                self.rule_propensity_update_dict = {}
            self.solver = solver(self.locations, self.rules, self.matched_indices, self.model_state, propensity_caching, no_rules_behaviour, self.rule_propensity_update_dict)
            self.solver_initialized = True
        else:
            raise(ValueError("Model not initialized: initialize model before solver"))

    def resetSimulation(self):
        for location in self.locations:
            location.reset()
        # Trajectory uses current location values so needs to be defined after location values reset.
        self.trajectory = Rule.Trajectory(self.locations)
        self.model_state.reset()
        self.solver.reset()

    def simulate(self, time_limit, max_iterations:int = 1000):
        if self.solver_initialized and self.model_initialized:
            self.resetModel()
            start_perf_time = time.perf_counter()
            while self.model_state.elapsed_time < time_limit and self.model_state.iterations < max_iterations:
                # Simulate one step should update the location objects automatically with the new compartment values.
                new_time = self.solver.simulateOneStep(self.model_state.elapsed_time)
                self.model_state.processUpdate(new_time)
                # TODO To save memory - could just add changed location values
                for location_index, location in enumerate(self.locations):
                    self.trajectory.addEntry(new_time, location.class_values, location_index)

                 if new_time is None:
                    break
            end_perf_time = time.perf_counter()
            print(f"The simulation has finished after {self.model_state.elapsed_time} {self.model_state.time_measurement}, requiring {self.model_state.iterations} iterations and {end_perf_time-start_perf_time} secs of compute time")
            return self.trajectory
        else:
            raise(ValueError("Model/solver not initialized: initialize model and then the solver."))
