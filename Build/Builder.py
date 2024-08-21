import numpy as np

import pyRBM.Build.Classes as Classes
import pyRBM.Build.Locations as Locations
import pyRBM.Build.Rules as Rules

import pyRBM.Build.Utils as Utils
import pyRBM.Build.RuleTemplates as RuleTemplates

import RuleMatching

class Model:
    def __init__(self, classes_defintions, create_locations, create_rules, write_to_file:bool = True,
                 distance_func = Utils.createEuclideanDistanceMatrix, classes_filename = "Classes.json", location_filename:str = "Locations.json", metarule_filename:str = "MetaRules.json",
                 matched_rules_filename:str = "LocationMatchedRules.json", model_folder:str = "/ModelFiles/"):
        self.classes_filename = classes_filename
        self.location_filename = location_filename
        self.metarule_filename = metarule_filename
        self.matched_rules_filename = matched_rules_filename
        self.model_folder = model_folder

        
        self.classes_defintions = classes_defintions
        self.create_locations_func = create_locations
        self.create_rules_func = create_rules
        self.distance_func = distance_func

        self.builtin_classes = True

        self.write_to_file = write_to_file

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
    
    def build(self):
        self.defineClasses()
        self.createLocations()
        self.createRules()
        self.matchRules()
