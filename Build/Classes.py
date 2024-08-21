import json
from pathlib import Path
class Classes:
    def __init__(self, allow_base_model_classes = True):
        self.class_def_dict = {}
        self.class_names = set([])
        self.base_model_string = "model_"
        if allow_base_model_classes:
            for built_in_class in self.returnBuiltInClasses():
                self.addClass(*built_in_class)
    
    def addClass(self, class_name, class_measurement_unit, class_restriction = "None"):
        if class_name in self.base_model_string:
            raise(ValueError(f"Class: {class_name} cannot contain model prefix{self.base_model_string}"))
        elif not class_name in self.class_names:
            self.class_def_dict[class_name] = {"class_measurement_unit":class_measurement_unit, "class_restriction":class_restriction}
        else:
            raise(ValueError(f"Duplicate type {class_name} provided."))
        
    def returnBuiltInClasses(self):
        builtin_classes = [[f"{self.base_model_string}day", "Day of year"], 
                           [f"{self.base_model_string}hour","Hour of day", "integer"], 
                           [f"{self.base_model_string}months", "Month of year", "integer"]]
        months = [["jan", "January"], ["feb", "February"], ["mar", "March"], ["apr", "April"],
                  ["may", "May"], ["jun", "June"], ["jul", "July"], ["aug", "August"], 
                  ["sept", "September"], ["oct", "October"], ["nov", "November"], ["dec", "December"]
                  ]
        for month in months:
            builtin_classes.append([f"{self.base_model_string}month_{month[0]}", month[1], "indictator"])
        builtin_classes.sort()
        return builtin_classes
    
    def writeClassJSON(self, filepath):
        #folder_paths = filepath.split("/").pop()
        #folder = folder_paths.join
        #Path(folder).mkdir(parents=True, exist_ok=True)
        
        json_classes = json.dumps(self.class_def_dict, indent=4, sort_keys=True)

        with open(filepath, "w") as outfile:
            outfile.write(json_classes)
        return self.class_def_dict