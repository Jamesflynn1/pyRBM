class Location:
    def __init__ (self, index, name, lat, long, loc_type, label_mapping, initial_class_values, location_constants):
        self.index = index
        self.name = name
        self.lat = lat
        self.long = long
        self.loc_type = loc_type
        self.label_mapping = label_mapping

        self.initial_class_values = initial_class_values
        self.class_values = initial_class_values
        self.location_constants = location_constants
    
    def updateCompartmentValues(self, new_values):
        self.class_values = new_values
    
    def reset(self):
        self.class_values = self.initial_class_values
