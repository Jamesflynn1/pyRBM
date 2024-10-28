from pyRBM.Core.StringUtilities import parseVarName

class Classes:
    def __init__(self, allow_base_model_classes:bool = True):
        self.class_def_dict:dict[str,dict[str,str]] = {}
        self.class_names:set[str] = set()
        self.base_model_string = "model_"
        if allow_base_model_classes:
            for built_in_class in self.returnBuiltInClasses():
                self.addClass(*built_in_class)
    
    def addClass(self, class_name:str, class_measurement_unit:str,
                 class_restriction:str = "None") -> None:
        class_name = parseVarName(class_name)
        if class_name in self.base_model_string:
            raise(ValueError(f"Class: {class_name} cannot contain model prefix{self.base_model_string}"))
        elif not class_name in self.class_names:
            self.class_def_dict[class_name] = {"class_measurement_unit":class_measurement_unit,
                                               "class_restriction":class_restriction}
        else:
            raise(ValueError(f"Duplicate type {class_name} provided."))
        
    def returnBuiltInClasses(self) -> list[list[str]]:
        builtin_classes = [[f"{self.base_model_string}day",
                            "Day of month"],
                            [f"{self.base_model_string}yearly_day",
                            "Day of year"],
                           [f"{self.base_model_string}hour",
                            "Hour of day", "integer"],
                           [f"{self.base_model_string}months",
                            "Month of year", "integer"]]
        
        months = [["jan", "January"], ["feb", "February"],
                  ["mar", "March"], ["apr", "April"],
                  ["may", "May"], ["jun", "June"],
                  ["jul", "July"], ["aug", "August"],
                  ["sept", "September"], ["oct", "October"],
                  ["nov", "November"], ["dec", "December"]
                  ]
        for month in months:
            builtin_classes.append([f"{self.base_model_string}month_{month[0]}",
                                    month[1], "indictator"])
        builtin_classes.sort()
        return builtin_classes
    
    def returnClassDict(self) -> dict[str, dict[str,str]]:
        return self.class_def_dict
