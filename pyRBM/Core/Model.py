import pyRBM.Build.Classes as Classes
import pyRBM.Build.Locations as Locations
import pyRBM.Build.Rules as Rules
import pyRBM.Build.RuleMatching as RuleMatching
import pyRBM.Build.Utils as Utils

import pyRBM.Core.Cache as Files

import pyRBM.Simulation.State as State
import pyRBM.Simulation.Solvers as Solvers
import pyRBM.Simulation.RuleChain as RuleChain
import pyRBM.Simulation.Trajectory as Trajectory


import time
import datetime


class Model:
    def __init__(self, model_name):
        self.builtin_classes = True
        self.model_name = model_name
        return

        
    def createLocations(self):
        all_locations = Locations.Locations(self.defined_classes, self.distance_func)
        locations = self.create_locations_func()
        all_locations.addLocations(locations)
        # Distance computation done as part of writeJSON - set as location constants
        locations = all_locations.returnLocationsDict()
        self.location_constants = all_locations.returnAllLocationConstantNames()

        return locations

    def createRules(self):
        # Use np.identity(len()) .... for no change
        all_rules = Rules.Rules(self.defined_classes, self.location_constants)

        rules = self.create_rules_func()
        all_rules.addRules(rules)

        return all_rules.returnMetaRuleDict()

    def defineClasses(self):
        classes = Classes.Classes(self.builtin_classes)
        for class_info in self.classes_defintions:
            classes.addClass(*class_info)
        classes_dict = classes.returnClassDict()
        self.defined_classes = classes_dict.keys()

        return classes_dict

    def matchRules(self, rules):
        additional_classes = []
        if self.builtin_classes:
            additional_classes = Classes.Classes().returnBuiltInClasses()
        return RuleMatching.returnMatchedRulesDict(rules, self.locations_dict, additional_classes)
    
    
    def buildModel(self, classes_defintions, create_locations, create_rules, distance_func = Utils.createEuclideanDistanceMatrix,
                   write_to_file = False,  save_model_folder:str = "/ModelFiles/", location_filename:str = "Locations", matched_rules_filename:str = "LocationMatchedRules",
                   classes_filename:str = "Classes", save_meta_rules = False, metarule_filename:str = "MetaRules"):
        
        self.classes_defintions = classes_defintions
        self.create_locations_func = create_locations
        self.create_rules_func = create_rules
        self.distance_func = distance_func
        self.save_model_folder = save_model_folder

        self.classes_dict = self.defineClasses()
        self.locations_dict = self.createLocations()
        rules = self.createRules()
        self.matched_rules_dict = self.matchRules(rules)

        self.write_to_file = write_to_file


        if self.write_to_file:
            if not save_meta_rules:
                metarule_filename = None
            else:
                Files.writeDictToJSON(rules, f"{self.save_model_folder}{self.model_name}/{metarule_filename}")

            self.save_model_folder,self.location_filename,self.matched_rules_filename,self.classes_filename,self.metarule_filename = [save_model_folder,location_filename,
                                                                                                                                      matched_rules_filename,classes_filename,metarule_filename]
            for model_dict, file_loc in [(self.matched_rules_dict, f"{self.save_model_folder}{self.model_name}/{self.matched_rules_filename}"),
                                         (self.classes_dict, f"{self.save_model_folder}{self.model_name}/{self.classes_filename}"),
                                         (self.locations_dict, f"{self.save_model_folder}{self.model_name}/{self.location_filename}")]:
                Files.writeDictToJSON(model_dict, file_loc)
        else:
            if save_meta_rules:
                print("Warning: meta rules not saved as file saving is false")
            else:
                self.save_model_folder,self.location_filename,self.matched_rules_filename,self.classes_filename,self.metarule_filename = [None,None,None,None,None]

        self.convertToSimulation()

    def convertToSimulation(self):
        self.classes, self.builtin_classes = Files.loadClasses(classes_dict=self.classes_dict)
        self.locations = Files.loadLocations(build_locations_dict=self.locations_dict)
        self.rules, self.matched_indices = Files.loadMatchedRules(self.locations, num_builtin_classes=len(self.builtin_classes),
                                                                  matched_rule_dict=self.matched_rules_dict)


        self.trajectory = Trajectory.Trajectory(self.locations)
        self.model_state = State.ModelState(self.builtin_classes, datetime.datetime.now())

        self.model_initialized = True
        self.solver_initialized = False

    def loadModelFromJSONFiles(self, location_filename:str = "Locations", matched_rules_filename:str = "LocationMatchedRules",
                           classes_filename:str = "Classes", model_folder:str = "Backend/ModelFiles/"):
        
        self.matched_rules_filename = matched_rules_filename
        self.location_filename = location_filename
        self.save_model_folder = model_folder
        self.classes_filename = classes_filename

        self.classes, self.builtin_classes = Files.loadClasses(classes_filename = f"{self.save_model_folder}{self.model_name}/{self.classes_filename}")
        self.locations = Files.loadLocations(locations_filename = f"{self.save_model_folder}{self.model_name}/{self.location_filename}")
        self.rules, self.matched_indices = Files.loadMatchedRules(self.locations, num_builtin_classes=len(self.builtin_classes), 
                                                                  matched_rules_filename= f"{self.save_model_folder}{self.model_name}/{self.matched_rules_filename}")


        self.trajectory = Trajectory.Trajectory(self.locations)
        self.model_state = State.ModelState(self.builtin_classes, datetime.now())

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
        self.trajectory = Trajectory.Trajectory(self.locations)
        self.model_state.reset()
        self.solver.reset()

    def simulate(self, start_date, time_limit, max_iterations:int = 1000):
        self.start_date = start_date
        self.model_state = State.ModelState(self.builtin_classes, self.start_date)

        if self.solver_initialized and self.model_initialized:
            self.resetSimulation()
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
            raise(ValueError("Model/solver not initialized: initialize model before the solver."))
