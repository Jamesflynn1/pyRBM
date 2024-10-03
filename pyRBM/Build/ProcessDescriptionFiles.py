""" Module to load compartments from file and create a function to be used in model creation.
"""
import inspect

from pyRBM.Core.Cache import readDictFromJSON

class LoadedCompartments:
    def __init__(self, compartment_type_dict):
        self._compartments = []

        self.compartment_type_dict = compartment_type_dict
            
    def loadCompartmentsFromJSONFile(self, filename):
        compartmental_creation_dict = readDictFromJSON(filename)

        compartments = compartmental_creation_dict["compartments"]

        for compartment in compartments:
            compartment_class = self.compartment_type_dict[compartment["type"]]
            compartment_args = {} # TODO
            self._compartments.append(compartment_class(compartment["name"]))