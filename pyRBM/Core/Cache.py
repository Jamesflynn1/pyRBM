import json
import os
from typing import Optional, Any

import numpy as np

from pyRBM.Simulation.Rule import Rule
from pyRBM.Simulation.Compartment import Compartment

class ModelPaths:
    """ Provides paths for created and loaded model files.

    All paths follow the format (model_folder_path_to)(model_name)(filename).

    Filenames should NOT include the file ending.
    
    A new ModelPaths object should overwrite the old object when a new model is saved/loaded.

    Attributes:
        compartment_path (str|None): the path to the compartments .json file saved or loaded or created at this object's creation, if it was saved/loaded, otherwise None.
        classes_path (str|None): the path to the classes .json file saved or loaded or created at this object's creation, if it was saved/loaded, otherwise None.
        matched_rules_path (str|None): the path to the matched_rules .json file saved or loaded or created at this object's creation, if it was saved/loaded, otherwise None.
        metarule_path (str|None): the path to the metarule .json file saved or loaded at this object's creation, if it was saved/loaded, otherwise None.
        save_model_folder (str|None): the model folder that the 
    """
    def __init__(self, matched_rules_filename:Optional[str] = None,
                 compartments_filename:Optional[str] = None,
                 model_folder_path_to:Optional[str] = None,
                 model_name:Optional[str] = "",
                 classes_filename:Optional[str] = None,
                 metarules_filename:Optional[str] = None):
        if model_name is None or model_folder_path_to is None:
            model_name = None
        else:
            self.save_model_folder = f"{model_folder_path_to}{model_name}/"
        self._matched_rules_filename = matched_rules_filename
        self._compartments_filename = compartments_filename
        self._classes_filename = classes_filename
        self._metarules_filename = metarules_filename
    # property decorator allows the function to be accessed as a standard class variable
    @property
    def compartments_path(self) -> Optional[str]:
        """The path to the compartments .json file saved or loaded or created at this object's creation, if it was saved/loaded, otherwise None."""
        if self._compartments_filename is None or self.save_model_folder is None:
            return None
        else:
            return self.save_model_folder+self._compartments_filename
    @property
    def classes_path(self) -> Optional[str]:
        """The path to the classes .json file saved or loaded or created at this object's creation, if it was saved/loaded, otherwise None"""
        if self._classes_filename is None or self.save_model_folder is None:
            return None
        else:
            return self.save_model_folder+self._classes_filename
    @property
    def matched_rules_path(self) -> Optional[str]:
        """ The path to the matched_rules .json file saved or loaded or created at this object's creation, if it was saved/loaded, otherwise None."""
        if self._matched_rules_filename is None or self.save_model_folder is None:
            return None
        else:
            return self.save_model_folder+self._matched_rules_filename
    @property
    def metarules_path(self) -> Optional[str]:
        """The path to the metarule .json file saved or loaded at this object's creation, if it was saved/loaded, otherwise None."""
        if self._metarules_filename is None or self.save_model_folder is None:
            return None
        else:
            return self.save_model_folder+self._metarules_filename

def writeDictToJSON(dict_to_write:dict, filename:str,
                    dict_name:str="") -> None:
    """ Writes dict_to_write to a json file at the filename path. Orders the json keys alphabetically and uses utf-8 encoding.

    Creates all folders and then the file if they don't already exist.

    Args:
        dict_to_write (dict): a dictionary to be written to a .json file.
        filename (str): the string representation of the path and filename of the json 
                file that is being written to (excluding the .json file ending).
        dict_name (str, optional): a string to include to provide user friendly output as to which file is being written.
    """
    folder =''.join([folder+'/' for folder in filename.split("/")[:-1]])
    dir_to_create = os.path.join(os.curdir,folder)

    if not os.path.exists(dir_to_create):
        print(f"Creating folder: {dir_to_create}")
        os.makedirs(dir_to_create)

    json_file = json.dumps(dict_to_write, indent=4, sort_keys=True)
    with open(f"{filename}.json", "w+", encoding='utf-8') as outfile:
            if dict_name != "":
                dict_name += " "
            print(f"Writing {dict_name}to file: {filename}.json")
            outfile.write(json_file)

def readDictFromJSON(filename:str) -> dict:
    """ Read a JSON file found at the filename path and return the dictionary representation of it.
    Args:
        filename (str): the string representation of the path to the json file to be loaded (excluding the .json file ending).
    Returns:
        dict: dictionary representation of the JSON file found at the path, filename.
    """
    file_data = None
    with open(f"{filename}.json", encoding='utf-8') as infile:
        file_data = json.load(infile)
    return file_data

def processFilenameOrDict(filename:Optional[str],
                          provided_dict:Optional[dict[str,Any]]) -> Optional[dict[str,Any]]:
    """

    """
    model_data = None
    if (filename is None) and (provided_dict is None):
        raise(ValueError("Provide either a "))
    elif not filename is None:
        model_data = readDictFromJSON(filename)
    else:
        model_data = provided_dict
    return model_data

def loadCompartments(compartments_filename:Optional[str] = None,
                  build_compartments_dict:Optional[dict[str,dict[str,Any]]] = None) -> list[Compartment]:
    """ Loads compartments from either a model compartment json file (see ModelCreation for details) 
    or from a pyRBM.Build.Compartments dictionary.

    Requires either compartments_filename or build_compartments_dict to be passed as an argument.

    If both arguments are provided, the function will load from the json at the compartments_filename path.

    Args:
        compartments_filename (str, optional): the string of the file compartment containing the compartment definitions.
        build_compartments_dict (dict, optional): a dictionary of pyRBM.Build.Compartments 
                (e.g. from calling Compartments.returnCompartmentsDict())
    Returns:
        list: pyRBM.Simulation compatible Compartments for each compartment in either compartment_file or build_compartments_dict.
    """
    compartment_list = []
    compartments_data = processFilenameOrDict(compartments_filename, build_compartments_dict)

    for comp_index in range(len(compartments_data)):
        compartment_dict = compartments_data[str(comp_index)]
        compartment = Compartment(index=comp_index, name=compartment_dict["compartment_name"], lat=float(compartment_dict["lat"]),
                                     long=float(compartment_dict["long"]), comp_type=compartment_dict["type"],
                                     label_mapping=compartment_dict["label_mapping"],
                                     initial_class_values=np.array(compartment_dict["initial_values"]),
                                     compartment_constants=compartment_dict["compartment_constants"])
        compartment_list.append(compartment)
    return compartment_list
    

def loadMatchedRules(compartments,  num_builtin_classes:int, matched_rules_filename:Optional[str] = None,
                     matched_rule_dict:Optional[dict]=None) -> tuple[list[Rule], list[list[int]]]:
    """ Loads all rules from a model matched rules json (see ModelCreation for details).

    Args: 
        compartments (): 
        num_builtin_classes: 
        matched_rules_filename: the string of the file compartment containing the rule definitions.
        matched_rule_dict: 
    Returns: [a list of rules remapped to all possible compartment sets, 
              a 2d list of lists of satisfying indices for the corresponding rule]
    """
    rules_list = []
    applicable_indices = []
    rules_data =  processFilenameOrDict(matched_rules_filename, matched_rule_dict)
    
    for rule_index in range(len(rules_data)):
        rules_dict = rules_data[str(rule_index)]
        stochiometries = []
        propensities = []
        # Convert stochiometries and propensities to numpy arrays -
        # need to use a list of arrays as the 2nd dimension of the array has varying dimension.
        for comp_stoichiometry in rules_dict["stoichiomety"]:
            stochiometries.append(np.array(comp_stoichiometry))
        for comp_propensity in rules_dict["propensity"]:
            propensities.append(comp_propensity)

        rule = Rule(propensity=propensities, stoichiometry=stochiometries, rule_name=rules_dict["rule_name"],
                         num_builtin_classes=num_builtin_classes, compartments=compartments,
                         rule_index_sets=rules_dict["matching_indices"])
        
        applicable_indices.append(rules_dict["matching_indices"])
        rules_list.append(rule)
    return (rules_list, applicable_indices)

def loadClasses(model_prefix:str = "model_", classes_filename:Optional[str] = None,
                classes_dict:Optional[dict] = None) -> tuple[dict, dict]:
    """ Loads classes from either a model class json file (see ModelCreation for details) or from a pyRBM.Build.Classes dictionary,
    and returns pyRBM.Simulation's requirements of a class_dict (a dict of all non-model classes) and 
    a built_in_class_dict (a dict of all model classes).

    Requires either classes_filename or classes_dict to be passed as an argument.

    If both arguments are provided, the function will load from the json at the classes_filename path.

    Args:
        model_prefix (str, optional): the prefix used to denote a model class in the model
        classes_filename (str) :ts
        classes_dict (dict) : a
    Returns:
        dict: class_dict
        dict: built_in_class_dict
    """
    class_dict = {}
    built_in_class_dict = {}
    class_data = processFilenameOrDict(classes_filename, classes_dict)

    for class_key in class_data:
        if model_prefix in class_key:
            built_in_class_dict[class_key] = class_data[class_key]
        else:
            class_dict[class_key] = class_data[class_key]
    return (class_dict, built_in_class_dict)

