class Compartment:
    def __init__ (self, index, name:str, lat, long, comp_type, label_mapping,
                  initial_class_values, compartment_constants) -> None:
        self.index = index
        self.name = name
        self.lat = lat
        self.long = long
        self.comp_type = comp_type
        self.label_mapping = label_mapping

        self.initial_class_values = initial_class_values
        self.class_values = initial_class_values
        self.compartment_constants = compartment_constants

    def updateCompartmentValues(self, new_values) -> None:
        self.class_values = new_values

    def reset(self) -> None:
        self.class_values = self.initial_class_values
