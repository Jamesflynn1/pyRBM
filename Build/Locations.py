import numpy as np

import json

class Location:
    def __init__(self, lat:float, long:float, name:str, loc_type:str, constants = None, loc_prefix:str="loc_"):
        self.lat = lat
        self.long = long
        self.name = name
        self.class_labels = set([])
        self.loc_type = loc_type
        self.loc_prefix = loc_prefix

        # Constants will not be saved at the moment and will be replaced in rule matching.
        
        self.location_constants = None
        if isinstance(constants, dict):
            self.addAndSetConstants(constants)
        elif isinstance(constants, list):
            self.addConstants(constants)

        self.locations_variables = {}

        self.inital_conditions_dict = None

    def addConstants(self, constants:list):
        if constants is not None:
            if self.location_constants is None:
                self.location_constants = {}
            self.location_constants = self.location_constants|{self.loc_prefix+constant:None for constant in constants}

    def checkConditionDict(self, inital_conditions_dict:dict):
        for condition_class in inital_conditions_dict:
            if condition_class not in self.class_labels:
                raise(ValueError(f"Initial condition class {condition_class} not present at location {self.name}."))
            
    def checkConstantsDefined(self):
        if not self.location_constants is None:
            for constant in list(self.location_constants.keys()):
                if self.location_constants[constant] is None:
                    raise(ValueError(f"Location constant {constant} not defined at location {self.name}."))
    
    def setInitialConditions(self, inital_conditions_dict:dict):
        # check all classes are defined
        self.checkConditionDict(inital_conditions_dict)
        self.inital_conditions_dict = inital_conditions_dict

    def setDistances(self, distances:list):
        self.addConstants([f"distance_{i}" for i in range(len(distances))])
        self.setConstants({f"distance_{i}":distance for i, distance in enumerate(distances)})
    
    def setConstants(self, constants_dict:dict):
        current_constant_keys = list(self.location_constants.keys())
        for entered_constant in list(constants_dict.keys()):
            if self.loc_prefix+entered_constant in current_constant_keys:
                self.location_constants[self.loc_prefix+entered_constant] = constants_dict[entered_constant]
            else:
                raise(ValueError(f"Provided constant {entered_constant}, does not exist at current location {self.name}\n Defined location constants: {str(self.location_constants)}"))
            
    def addAndSetConstants(self, constants_dict:dict):
        self.addConstants(list(constants_dict.keys()))
        self.setConstants(constants_dict)
    def returnConstantNames(self):
        if self.location_constants is not None:
            return list(self.location_constants.keys())
        else:
            return []

    def returnDictDescription(self):
        #For ease of use and to ensure compartment label order is invariant to order construction functions are called.
        self.checkConstantsDefined()
        ordered_class_labels = sorted(self.class_labels)
        class_label_mapping = dict(enumerate(ordered_class_labels))
        initial_conds = list(np.zeros(len(self.class_labels)))

        if not self.inital_conditions_dict is None:
            self.checkConditionDict(self.inital_conditions_dict)
            initial_conds_keys = list(self.inital_conditions_dict.keys())
            for index, class_label in enumerate(ordered_class_labels):
                if class_label in initial_conds_keys:
                    initial_conds[index] = self.inital_conditions_dict[class_label]
        
        if self.location_constants is None:
            self.location_constants = {}

        return {"location_name":self.name, "lat" : self.lat, "long":self.long,
                "label_mapping":class_label_mapping, "type":self.loc_type, "initial_values":initial_conds, 
                "location_constants":self.location_constants}
    

class Locations:
    def __init__(self, defined_classes, distance_function):
        self.coords =[[],[]]
        self.locations = []
        self.defined_classes = defined_classes
        self.distance_function = distance_function

        self.type_register = {}
        
    def checkLocationClassesDefined(self):
        for location in self.locations:
            for location_class_label in location.class_labels:
                if location_class_label not in self.defined_classes:
                    raise ValueError(f"Class {location_class_label} not defined (Location name: {location.name})")
        return True
    
    def returnAllLocationConstantNames(self):
        constant_names = set([])
        for location in self.locations:
            constant_names.update(location.returnConstantNames())
        return list(constant_names)
    
    def computeAndSaveDistances(self):
        self.coords =  np.array(self.coords)
        distance_matrix =  self.distance_function(self.coords[0,:], self.coords[1,:])
        for i, x in enumerate(self.locations):
            x.setDistances(list(distance_matrix[i,:].flatten()))

    def writeJSON(self, filename:str):
        self.checkLocationClassesDefined()
        self.computeAndSaveDistances()

        locations_dict = {}

        for i, x in enumerate(self.locations):
            location_dict = x.returnDictDescription()
            locations_dict[i] = location_dict

        json_locations = json.dumps(locations_dict, indent=4, sort_keys=True)

        with open(filename, "w") as outfile:
            outfile.write(json_locations)
        
        return locations_dict
    
    def addCoordinates(self, lat:float, long:float):
        self.coords[0].append(lat)
        self.coords[1].append(long)
    
    def registerTypeClass(self, type_str:str, type_class):
        if type_str in self.type_register:
            raise(ValueError(f"Type {type_str} already has an associated class {str(self.type_register[type_str])}"))
        else:
            self.type_register[type_str] = type_class

    def addLocation(self, location):
        if isinstance(location, Location):
            if location.loc_type in self.type_register:
                # Want explicit type here rather than inclusive of subclasses
                if type(location) == self.type_register[location.loc_type]:
                    self.locations.append(location)
                    self.addCoordinates(location.lat, location.long)
                else:
                    raise(TypeError(f"Location type {location.loc_type} is already associated with class {self.type_register[location.loc_type]}, not class {type(location)}"))
            else:
                self.registerTypeClass(location.loc_type, type(location))
                self.locations.append(location)
                self.addCoordinates(location.lat, location.long)
        else:
            raise(TypeError(f"location is not a child type of Location base class (type: {type(location)})"))
        
    def addLocations(self, locations):
        for location in locations:
            self.addLocation(location)