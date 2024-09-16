import time
import datetime
from collections import defaultdict
from typing import Any, Iterable, Callable, Union, Optional

import numpy as np

from pyRBM.Build.Classes import Classes
from pyRBM.Build.Compartment import Compartments, Compartment, returnDefaultCompartment
from pyRBM.Build.Rules import Rules, Rule
from pyRBM.Build.RuleMatching import returnMatchedRulesDict
from pyRBM.Build.Utils import createEuclideanDistanceMatrix

from pyRBM.Core.Cache import (ModelPaths, writeDictToJSON, loadClasses,
                              loadCompartments, loadMatchedRules)
from pyRBM.Core.Plotting import SolverDataPlotting

from pyRBM.Simulation.State import ModelState
from pyRBM.Simulation.Solvers import Solver
from pyRBM.Simulation.RuleChain import returnOneStepRuleUpdates
from pyRBM.Simulation.Trajectory import Trajectory



class Model:
    """A cohesive collection of parsed rules, compartments and classes

    Attributes:

        model_name (str).

        contains_builtin_classes (bool): True if model_ classes should be added to the class list, False otherwise. Currently unused.
        no_compartment_model (bool): True if create_compartments_func was not passed and a dummy compartment was created, False otherwise.
        defined_classes:

        create_compartments_func (Callable, optional): a function accepting no arguments used to create and return a list of all model Compartments in createCompartments(). If no
        create_rules_func (Callable): a function accepting no arguments used to create and return a list of all model Rules in createRules().
        distance_func (Callable): a function that returns a pairwise distance matrix over all compartments 

    """
    def __init__(self, model_name:str) -> None:
        self.contains_builtin_classes = True
        self.model_name = model_name
        self.defined_classes:Optional[list[str]] = None

        self.model_paths = ModelPaths()
        
    def createCompartments(self) -> dict[str, dict[str, Any]]:
        """ Parse all compartments returned from the `self._create_rules_func`, perform rule validity and cohesion checks and return them in dictionary format.
        """
        all_compartments = Compartments(self.defined_classes, self._distance_func)
        compartments_list = None
        if not self._create_compartments_func is None:
            compartments_list = self._create_compartments_func()
            self.no_compartment_model = False
        else:
            compartments_list = [returnDefaultCompartment(self.classes_defintions)]
            print("No compartments passed to model constructor.",
            "Creating dummy compartment: Default, with type: any ","Will disregard rule type restrictions.")
            self.no_compartment_model = True
        all_compartments.addCompartments(compartments_list)
        # Distance computation done as part of writeJSON - set as compartment constants
        compartments_dict = all_compartments.returnCompartmentsDict()
        self.compartment_constants = all_compartments.returnAllCompartmentConstantNames()

        return compartments_dict

    def createRules(self) -> dict[str, dict[str, Any]]:
        # Use np.identity(len()) .... for no change
        """ Parse all rules returned from the `self._create_rules_func`, perform rule validity/cohesion checks and return the rules in dictionary format.
        Ret
        """
        all_rules = Rules(self.defined_classes, self.compartment_constants)
        rules = self._create_rules_func()
        all_rules.addRules(rules)
        if self.no_compartment_model:
            all_rules.removeTypeRequirement()
        return all_rules.returnMetaRuleDict()

    def defineClasses(self) -> dict[str,dict[str,str]]:
        """ Parse all user defined classes and add classes provided by pyRBM (e.g. model_ classes). Store these classes to check compartment and rule consistency later.
        Returns:
            dict: user-defined and model_ classes and associated class information (e.g. the class' unit of measurement) in dictionary format.
        """
        classes = Classes(self.contains_builtin_classes)
        for class_info in self.classes_defintions:
            classes.addClass(*class_info)
        classes_dict = classes.returnClassDict()
        self.defined_classes = list(classes_dict.keys())

        return classes_dict

    def matchRules(self) -> dict[str, dict[str, Any]]:
        """ Create subrules for each rule by finding all collections of compartments that .
        Returns:
            dict: a dictionary of subrules TODO
        """
        additional_classes = []
        if self.contains_builtin_classes:
            additional_classes = Classes().returnBuiltInClasses()
        return returnMatchedRulesDict(self._rules_dict, self._compartments_dict, additional_classes)
    
    
    def buildModel(self, classes_defintions:Iterable[Iterable[str]],
                   create_rules:Callable[[], Iterable[Rule]],
                   create_compartments:Optional[Callable[[], Iterable[Compartment]]] = None,
                   distance_func:Optional[Callable] = createEuclideanDistanceMatrix,
                   write_to_file:bool = False, save_meta_rules:bool = False,
                   save_model_folder:str = "/ModelFiles/",
                   compartment_filename:str = "Compartments",
                   matched_rules_filename:str = "CompartmentMatchedRules",
                   classes_filename:str = "Classes",
                   metarule_filename:str = "MetaRules") -> None:
        
        
        self.classes_defintions = classes_defintions
        self._create_compartments_func = create_compartments
        self._create_rules_func = create_rules
        self._distance_func = distance_func
        self.save_model_folder = save_model_folder

        self._classes_dict = self.defineClasses()
        self._compartments_dict = self.createCompartments()
        self._rules_dict = self.createRules()
        self._matched_rules_dict = self.matchRules()

        self.write_to_file = write_to_file

        if self.write_to_file:
            self.model_paths = ModelPaths(metarules_filename=metarule_filename if save_meta_rules else None,
                                          compartments_filename=compartment_filename if self.no_compartment_model else None,
                                          matched_rules_filename=matched_rules_filename,
                                          classes_filename=classes_filename,
                                          model_folder_path_to=save_model_folder,
                                          model_name=self.model_name)
            
            files_to_write = [(self._matched_rules_dict,self.model_paths.matched_rules_path, "matched rules dict"),
                              (self._classes_dict, self.model_paths.classes_path, "classes dict")]
            if self.model_paths.metarules_path is not None:
                files_to_write.append((self._rules_dict, self.model_paths.metarules_path, "meta rule dict"))
            
            if self.model_paths.compartments_path is not None:
                files_to_write.append((self._compartments_dict, self.model_paths.compartments_path, "compartments dict"))


            self.save_model_folder,self.compartment_filename,self.matched_rules_filename,\
                self.classes_filename,self.metarule_filename = [save_model_folder,compartment_filename,
                                                                matched_rules_filename,classes_filename,
                                                                metarule_filename]
            
            for model_dict, file_loc, dict_name in files_to_write:
                writeDictToJSON(model_dict, file_loc, dict_name)
        else:
            self.model_paths = ModelPaths()
            if save_meta_rules:
                print("Warning: meta rules not saved as file saving is false")

        self.convertToSimulation()

    def convertToSimulation(self) -> None:
        """ Transform internal dict/json representations created from `buildModel` into `pyRBM.Simulation` `Classes`, `Compartment`s and `Rule`s. Creates new `ModelState` and `Trajectory` object to account for the 
        change in state.

        Uninitializes `self.solver` as the solver is initialize with respect to the prior rules, compartments and matched indices.

        WARNING:
            This function overwrites `self.trajectory` and therefore possibly a prior `Trajectory`.
        """
        self.classes, self.builtin_classes = loadClasses(classes_dict=self._classes_dict)
        self.compartments = loadCompartments(build_compartments_dict=self._compartments_dict)
        self.rules, self.matched_indices = loadMatchedRules(self.compartments,
                                                            num_builtin_classes=len(self.builtin_classes),
                                                            matched_rule_dict=self._matched_rules_dict)

        self.trajectory = Trajectory(self.compartments)
        self.model_state = ModelState(self.builtin_classes, datetime.datetime.now())

        self.solver = None

        self.model_initialized = True
        self.solver_initialized = False

    def loadModelFromJSONFiles(self, compartment_filename:str = "Compartments",
                               matched_rules_filename:str = "CompartmentMatchedRules",
                               classes_filename:str = "Classes",
                               model_folder:str = "Backend/ModelFiles/",
                               model_name:Optional[str]="") -> None:
        """ Loads json representations of the model created from `buildModel` into `pyRBM.Simulation `Classes`, `Compartment`s and `Rule`s. Creates new `ModelState`, `Trajectory` and `ModelPaths` objects.

        Uninitializes `self.solver` as the solver is initialize with respect to the prior rules, compartments and matched indices.

        WARNING:
            This function overwrites `self.trajectory` and therefore possibly a prior `Trajectory`.
        
        Args:
            compartment_filename (str): 
            matched_rules_filename (str): 
            classes_filename (str): 
            model_folder (str): 
            model_name (str, optional): 
        """
        self.model_paths = ModelPaths(matched_rules_filename, compartment_filename,
                                      model_folder, model_name, classes_filename, None)

        self.classes, self.builtin_classes = loadClasses(classes_filename = self.model_paths.classes_path)
        if self.model_paths.compartments_path is None:
            self.compartments = loadCompartments(build_compartments_dict=returnDefaultCompartment(self.classes))
        else:
            self.compartments = loadCompartments(compartments_filename = self.model_paths.compartments_path)
        self.rules, self.matched_indices = loadMatchedRules(self.compartments, num_builtin_classes=len(self.builtin_classes),
                                                                  matched_rules_filename=self.model_paths.matched_rules_path)


        self.trajectory = Trajectory(self.compartments)
        self.model_state = ModelState(self.builtin_classes, datetime.datetime.now())
        
        self.solver = None
        self.solver_initialized = False
        self.model_initialized = True

    def initializeSolver(self, solver:Solver) -> None:
        """ Instatiates the provided `solver` class with the model compartments, rules and matched indices. Computes the rule to rule map used in 
        solver propensity caching if `solver.use_cached_propensities` is True. Old solver stats are overwritten.

        A concrete class (e.g. `GillespieSolver`) that `Solver` should be used and not the `Solver` class
        
        Args:
            solver (Solver): a concrete class that inherits `Solver` and implements `simulateOneStep` correctly.
        """
        if self.model_initialized:
            if solver.use_cached_propensities:
                self.rule_propensity_update_dict = returnOneStepRuleUpdates(self.rules, self.compartments,
                                                                            self.matched_indices,
                                                                            self.model_state.returnModelClasses())
            else:
                self.rule_propensity_update_dict = {}


            self.simulation_elapsed_times:list[float] = []
            self.simulation_iterations:list[int] = []
            self.simulation_number = 0

            self.solver = solver
            self.solver.initialize(self.compartments, self.rules, self.matched_indices, self.model_state,
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
        """ Resets the model to a pre-simulation state and creates a new Trajectory.

        WARNING:
            This will overwrite the `self.trajectory`, please store this variable for future use if desired.
        
        Specifically: 
            `class_values` are reset to `initial_values` for each compartment.
            A new `self.trajectory` is created.
            `self.model_state` is reset to it's initial values include the start date.
            `self.solver` resets all cached propensity values but keeps the old `propensity_update_dict` value.

        """
        for compartment in self.compartments:
            compartment.reset()
        # Trajectory uses current compartment values so needs to be defined after compartment values reset.
        self.trajectory = Trajectory(self.compartments)
        self.model_state.reset()
        self.solver.reset()

    def simulate(self, start_date:Union[datetime.time, datetime.date, datetime.datetime],
                 time_limit:Union[int, float], max_iterations:int = 10000) -> Trajectory:
        """ Simulate the model using `self.solver` from `start_date` until either the `time_limit` is reached or
        the number of iterations exceed `max_iterations`.

        Requires the model to be initialized (`model.convertToSimulation` or `model.loadModelFromJSONFiles`), 
        and the solver to be initialized (`model.initializeSolver`), solver initialized after the most recent model initialization.
        Therefore either call, `model.buildModel` then `model.convertToSimulation` then `model.initializeSolver`, or
        call `model.loadModelFromJSONFiles` then `model.initializeSolver`, before calling `model.simulate`).

        If the `self.solver.debug` = True, stats for the solver will be collected live and stored in `self.solver_diag_data`, this could for example be used for a real-time view of 
        simulations and could be useful to perform a trial run to validate solver/model correctness before a longer run is performed.

        Args:
            start_date (datetime.time|datetime.date|datetime.datetime): the date to start the simulation from. This date will overwrite the prior `start_datetime` in `self.model_state`.
            time_limit (int|float): the time limit of the simulation (after which the simulation will terminate) in unit time.
            max_iterations (int): the upper bound on the number of iterations of the simulation (after which the simulation will terminate).

        Returns:
            Trajectory: a `Trajectory` object of the model simulation from start_date until the simulation is terminated.
        """
        self.simulation_number += 1
        self.start_date = start_date
        self.model_state.changeDate(self.start_date)

        if self.solver_initialized and self.model_initialized:
            self.resetSimulation()
            start_perf_time = time.perf_counter()
            while self.model_state.elapsed_time < time_limit and self.model_state.iterations < max_iterations:
                # Simulate one step should update the compartment objects automatically with the new compartment values.
                new_time = self.solver.simulateOneStep(self.model_state.elapsed_time)
                self.model_state.processUpdate(new_time)
                # TODO To save memory - could just add changed compartment values
                for compartment_index, compartment in enumerate(self.compartments):
                    self.trajectory.addEntry(new_time, compartment.class_values, compartment_index)

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
        """ Prints (computational) performance statistics for the current model (since its inception).
        
        Printed Statistics:
            Number of simulations.
            Mean and standard deviation of the number of iterations per simulation.
            Mean and standard deviation of the time spent in the core simulation loop per simulation.
        """
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
