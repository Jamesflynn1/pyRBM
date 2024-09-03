import pyRBM.Build.Classes as Classes
import pyRBM.Build.Locations as Locations
import pyRBM.Build.Rules as Rules
import pyRBM.Build.RuleMatching as RuleMatching
import pyRBM.Build.Utils as Utils

import pyRBM.Core.Cache as Files
import pyRBM.Core.Plotting as Plot

import pyRBM.Simulation.State as State
import pyRBM.Simulation.Solvers as Solvers
import pyRBM.Simulation.RuleChain as RuleChain
import pyRBM.Simulation.Trajectory as Trajectory


import time
import datetime
import collections

import matplotlib.pyplot as plt
import matplotlib.animation as anim
import numpy as np

class Model:
    def __init__(self, model_name:str):
        self.builtin_classes = True
        self.model_name = model_name

        
    def createLocations(self):
        all_locations = Locations.Locations(self.defined_classes, self.distance_func)
        locations = None
        if not self.create_locations_func is None:
            locations = self.create_locations_func()
            self.no_location_model = False
        else:
            locations = [Locations.returnDefaultLocation(self.classes_defintions)]
            print("No locations passed to model constructor.",
            "Creating dummy location: Default, with type: any ","Will disregard rule type restrictions.")
            self.no_location_model = True
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
        if self.no_location_model:
            all_rules.removeTypeRequirement()
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
    
    
    def buildModel(self, classes_defintions, create_rules, create_locations = None, distance_func = Utils.createEuclideanDistanceMatrix,
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
            file_prefix = f"{save_model_folder}{self.model_name}/"
            files_to_write = [(self.matched_rules_dict, file_prefix+matched_rules_filename, "matched rules dict"),
                              (self.classes_dict, file_prefix+classes_filename, "classes dict")]

            if not save_meta_rules:
                metarule_filename = None
            else:
                files_to_write.append((rules, file_prefix+metarule_filename, "meta rule dict"))
            
            if self.no_location_model:
                location_filename = None
            else:
                files_to_write.append((self.locations_dict, file_prefix+location_filename, "locations dict"))


            self.save_model_folder,self.location_filename,self.matched_rules_filename,self.classes_filename,self.metarule_filename = [save_model_folder,location_filename,
                                                                                                                                      matched_rules_filename,classes_filename,metarule_filename]
            for model_dict, file_loc, dict_name in files_to_write:
                Files.writeDictToJSON(model_dict, file_loc, dict_name)
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
        if location_filename is None:
            self.locations = Files.loadLocations(build_locations_dict=Locations.returnDefaultLocation(self.classes))
        else:
            self.locations = Files.loadLocations(locations_filename = f"{self.save_model_folder}{self.model_name}/{self.location_filename}")
        self.rules, self.matched_indices = Files.loadMatchedRules(self.locations, num_builtin_classes=len(self.builtin_classes), 
                                                                  matched_rules_filename= f"{self.save_model_folder}{self.model_name}/{self.matched_rules_filename}")


        self.trajectory = Trajectory.Trajectory(self.locations)
        self.model_state = State.ModelState(self.builtin_classes, datetime.now())

        self.solver_initialized = False
        self.model_initialized = True

    def initializeSolver(self, solver:Solvers.Solver):
        if self.model_initialized:
            if solver.use_cached_propensities:
                self.rule_propensity_update_dict = RuleChain.returnOneStepRuleUpdates(self.rules, self.locations, self.matched_indices, self.model_state.returnModelClasses())
            else:
                self.rule_propensity_update_dict = {}


            self.simulation_elapsed_times = []
            self.simulation_iterations = []
            self.simulation_number = 0

            self.solver = solver
            self.solver.initialize(self.locations, self.rules, self.matched_indices, self.model_state, self.rule_propensity_update_dict)
            self.solver_initialized = True

            self.debug = solver.debug
            if self.debug:
                self.prior_iterations_data = collections.defaultdict(list)
                # Remove manual change required for new solver data collection fields here
                self.solver_diag_data = SolverData(fields=["rule_triggered", "rule_index_set", "total_propensity"])
                self.model_debug_plot = Plot.SolverDataPlotting(self)
        else:
            raise(ValueError("Model not initialized: initialize model before solver"))

    def resetSimulation(self):
        for location in self.locations:
            location.reset()
        # Trajectory uses current location values so needs to be defined after location values reset.
        self.trajectory = Trajectory.Trajectory(self.locations)
        self.model_state.reset()
        self.solver.reset()

    def simulate(self, start_date, time_limit, max_iterations:int = 10000):
        self.simulation_number += 1
        self.start_date = start_date
        self.model_state.changeDate(self.start_date)

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
                if self.debug:
                    self.solver_diag_data.updateData(self.solver.current_stats)
            end_perf_time = time.perf_counter()
            time_elapsed = end_perf_time-start_perf_time
            
            print(f"Simulation {self.simulation_number} has finished after {self.model_state.elapsed_time} {self.model_state.time_measurement}, requiring {self.model_state.iterations} iterations and {time_elapsed} secs of compute time")

            self.simulation_elapsed_times.append(time_elapsed)
            self.simulation_iterations.append(self.model_state.iterations)
            if self.debug:
                self.solver_diag_data.saveSolverPerSimulationData()
            return self.trajectory
        else:
            raise(ValueError("Model/solver not initialized: initialize model before the solver."))

    def printSimulationPerformanceStats(self):
        print("\n")
        print(f"Completed {self.simulation_number} simulations with the following stats")
        print(f"Iterations:\n Mean: {np.mean(self.simulation_iterations)}, Std: {np.std(self.simulation_iterations)}")
        print(f"Simulation Elapsed Time:\n Mean: {np.mean(self.simulation_elapsed_times)}, Std: {np.std(self.simulation_elapsed_times)}")

class SolverData:
    def __init__(self, fields):
        self.fields = fields
        self.iterations_data =  [collections.defaultdict(list)]
        self.iterations_frequency = [{field:collections.defaultdict(int) for field in fields}]

    def updateData(self, update_dict):
        iteration_data = self.iterations_data[-1]
        iteration_frequency = self.iterations_frequency[-1]
        for key, value in update_dict.items():
            iteration_frequency[key][value] += 1
            iteration_data[key].append(value)

    def saveSolverPerSimulationData(self):
        self.iterations_data.append(collections.defaultdict(list))
        self.iterations_frequency.append({field:collections.defaultdict(int) for field in self.fields})
