import time
import datetime
from collections import defaultdict
from typing import Any, Iterable, Callable, Union, Optional

import numpy as np

from pyRBM.Build.Classes import Classes
from pyRBM.Build.Locations import Locations, Location, returnDefaultLocation
from pyRBM.Build.Rules import Rules, Rule
from pyRBM.Build.RuleMatching import returnMatchedRulesDict
from pyRBM.Build.Utils import createEuclideanDistanceMatrix

from pyRBM.Core.Cache import (writeDictToJSON, loadClasses,
                              loadLocations, loadMatchedRules)
from pyRBM.Core.Plotting import SolverDataPlotting

from pyRBM.Simulation.State import ModelState
from pyRBM.Simulation.Solvers import Solver
from pyRBM.Simulation.RuleChain import returnOneStepRuleUpdates
from pyRBM.Simulation.Trajectory import Trajectory



class Model:
    def __init__(self, model_name:str) -> None:
        self.contains_builtin_classes = True
        self.model_name = model_name
        self.defined_classes:Optional[list[str]] = None

        
    def createLocations(self) -> dict[str, dict[str, Any]]:
        all_locations = Locations(self.defined_classes, self.distance_func)
        locations_list = None
        if not self.create_locations_func is None:
            locations_list = self.create_locations_func()
            self.no_location_model = False
        else:
            locations_list = [returnDefaultLocation(self.classes_defintions)]
            print("No locations passed to model constructor.",
            "Creating dummy location: Default, with type: any ","Will disregard rule type restrictions.")
            self.no_location_model = True
        all_locations.addLocations(locations_list)
        # Distance computation done as part of writeJSON - set as location constants
        locations_dict = all_locations.returnLocationsDict()
        self.location_constants = all_locations.returnAllLocationConstantNames()

        return locations_dict

    def createRules(self) -> dict[str, dict[str, Any]]:
        # Use np.identity(len()) .... for no change
        all_rules = Rules(self.defined_classes, self.location_constants)
        rules = self.create_rules_func()
        all_rules.addRules(rules)
        if self.no_location_model:
            all_rules.removeTypeRequirement()
        return all_rules.returnMetaRuleDict()

    def defineClasses(self) -> dict[str,dict[str,str]]:
        classes = Classes(self.contains_builtin_classes)
        for class_info in self.classes_defintions:
            classes.addClass(*class_info)
        classes_dict = classes.returnClassDict()
        self.defined_classes = list(classes_dict.keys())

        return classes_dict

    def matchRules(self, rules:dict[str,dict[str,Any]]) -> dict[str, dict[str, Any]]:
        additional_classes = []
        if self.contains_builtin_classes:
            additional_classes = Classes().returnBuiltInClasses()
        return returnMatchedRulesDict(rules, self.locations_dict, additional_classes)
    
    
    def buildModel(self, classes_defintions:Iterable[Iterable[str]],
                   create_rules:Callable[[], Iterable[Rule]],
                   create_locations:Optional[Callable[[], Iterable[Location]]] = None,
                   distance_func = createEuclideanDistanceMatrix,
                   write_to_file:bool = False, save_meta_rules:bool = False,
                   save_model_folder:str = "/ModelFiles/",
                   location_filename:str = "Locations",
                   matched_rules_filename:str = "LocationMatchedRules",
                   classes_filename:str = "Classes",
                   metarule_filename:str = "MetaRules") -> None:
        
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


            self.save_model_folder,self.location_filename,self.matched_rules_filename,\
                self.classes_filename,self.metarule_filename = [save_model_folder,location_filename,
                                                                matched_rules_filename,classes_filename,
                                                                metarule_filename]
            
            for model_dict, file_loc, dict_name in files_to_write:
                writeDictToJSON(model_dict, file_loc, dict_name)
        else:
            if save_meta_rules:
                print("Warning: meta rules not saved as file saving is false")
            else:
                self.save_model_folder,self.location_filename,self.matched_rules_filename,\
                    self.classes_filename,self.metarule_filename = [None,None,None,None,None]

        self.convertToSimulation()

    def convertToSimulation(self) -> None:
        self.classes, self.builtin_classes = loadClasses(classes_dict=self.classes_dict)
        self.locations = loadLocations(build_locations_dict=self.locations_dict)
        self.rules, self.matched_indices = loadMatchedRules(self.locations,
                                                            num_builtin_classes=len(self.builtin_classes),
                                                            matched_rule_dict=self.matched_rules_dict)


        self.trajectory = Trajectory(self.locations)
        self.model_state = ModelState(self.builtin_classes, datetime.datetime.now())

        self.model_initialized = True
        self.solver_initialized = False

    def loadModelFromJSONFiles(self, location_filename:str = "Locations", matched_rules_filename:str = "LocationMatchedRules",
                           classes_filename:str = "Classes", model_folder:str = "Backend/ModelFiles/") -> None:
        
        self.matched_rules_filename = matched_rules_filename
        self.location_filename = location_filename
        self.save_model_folder = model_folder
        self.classes_filename = classes_filename

        self.classes, self.builtin_classes = loadClasses(classes_filename = f"{self.save_model_folder}{self.model_name}/{self.classes_filename}")
        if location_filename is None:
            self.locations = loadLocations(build_locations_dict=returnDefaultLocation(self.classes))
        else:
            self.locations = loadLocations(locations_filename = f"{self.save_model_folder}{self.model_name}/{self.location_filename}")
        self.rules, self.matched_indices = loadMatchedRules(self.locations, num_builtin_classes=len(self.builtin_classes),
                                                                  matched_rules_filename= f"{self.save_model_folder}{self.model_name}/{self.matched_rules_filename}")


        self.trajectory = Trajectory(self.locations)
        self.model_state = ModelState(self.builtin_classes, datetime.datetime.now())

        self.solver_initialized = False
        self.model_initialized = True

    def initializeSolver(self, solver:Solver) -> None:
        if self.model_initialized:
            if solver.use_cached_propensities:
                self.rule_propensity_update_dict = returnOneStepRuleUpdates(self.rules, self.locations,
                                                                            self.matched_indices,
                                                                            self.model_state.returnModelClasses())
            else:
                self.rule_propensity_update_dict = {}


            self.simulation_elapsed_times:list[float] = []
            self.simulation_iterations:list[int] = []
            self.simulation_number = 0

            self.solver = solver
            self.solver.initialize(self.locations, self.rules, self.matched_indices, self.model_state,
                                   self.rule_propensity_update_dict)
            self.solver_initialized = True

            self.debug = solver.debug
            if self.debug:
                self.prior_iterations_data = defaultdict(list)
                # Remove manual change required for new solver data collection fields here
                self.solver_diag_data = SolverData(fields=["rule_triggered",
                                                           "rule_index_set",
                                                           "total_propensity"])
                self.model_debug_plot = SolverDataPlotting(self)
        else:
            raise(ValueError("Model not initialized: initialize model before solver"))

    def resetSimulation(self) -> None:
        for location in self.locations:
            location.reset()
        # Trajectory uses current location values so needs to be defined after location values reset.
        self.trajectory = Trajectory(self.locations)
        self.model_state.reset()
        self.solver.reset()

    def simulate(self, start_date:Union[datetime.time, datetime.date, datetime.datetime],
                 time_limit:Union[int, float], max_iterations:int = 10000) -> Trajectory:
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

    def printSimulationPerformanceStats(self) -> None:
        print("\n")
        print(f"Completed {self.simulation_number} simulations with the following stats")
        print(f"Iterations:\n Mean: {np.mean(self.simulation_iterations)}, Std: {np.std(self.simulation_iterations)}")
        print(f"Simulation Elapsed Time:\n Mean: {np.mean(self.simulation_elapsed_times)}, Std: {np.std(self.simulation_elapsed_times)}")

class SolverData:
    def __init__(self, fields:Iterable[str]) -> None:
        self.fields = fields
        self.iterations_data:list[dict[list,Any]] =  [defaultdict(list)]
        self.iterations_frequency:list[dict[str, defaultdict[str, int]]] = [{field:defaultdict(int) for field in fields}]

    def updateData(self, update_dict) -> None:
        iteration_data = self.iterations_data[-1]
        iteration_frequency = self.iterations_frequency[-1]
        for key, value in update_dict.items():
            iteration_frequency[key][value] += 1
            iteration_data[key].append(value)

    def saveSolverPerSimulationData(self) -> None:
        self.iterations_data.append(defaultdict(list))
        self.iterations_frequency.append({field:defaultdict(int) for field in self.fields})
