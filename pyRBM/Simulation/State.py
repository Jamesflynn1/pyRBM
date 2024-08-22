# This file is used to allow

from datetime import timedelta, datetime
import numpy as np

class ModelState:
    def __init__(self, model_classes, start_datetime):
        self.MONTHS =  ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sept", "oct", "nov", "dec"]
        self.model_prefix = "model_"

        self.IMPLEMENTED_MODEL_CLASSES = [f"model_{var}" for var in ["day", "hour", "months"]]
        self.IMPLEMENTED_MODEL_CLASSES += [f"model_month_{month}" for month in self.MONTHS]
        self.model_classes = {}

        self.time_measurement = "days"

        for model_class in model_classes:
            if model_class in self.IMPLEMENTED_MODEL_CLASSES:
                self.model_classes[model_class] = None
                print(f"{model_class} implemented")
            else:
                self.model_classes[model_class] = None
                raise(ValueError(f"Model class {model_class} not implemented"))


        self.elapsed_time = 0
        self.iterations = 0
        self.current_month = None

        self.changed_vars = [classes for classes in list(self.model_classes.keys())]


        if isinstance(start_datetime, datetime):
            self.start_datetime = start_datetime
            self.current_datetime = start_datetime
        else:
            raise(ValueError(f"Start date must be of type datetime not {type(start_datetime)}"))
        self.initaliseCalendarInfo()
        
    def reset(self):
        self.elapsed_time = 0
        self.iterations = 0
        self.current_datetime = self.start_datetime
        self.changed_vars = [classes for classes in list(self.model_classes.keys())]
        self.updateCalendarInfo()

    # Convert the self.current_datetime into model variables used
    def initaliseCalendarInfo(self):
        # Initialise all indicators to zero and perform the standard update step.
        for key in self.IMPLEMENTED_MODEL_CLASSES:
            self.model_classes[key] = 0
        self.updateCalendarInfo()
    
    def updateCalendarInfo(self):

        # https://docs.python.org/3/library/datetime.html#datetime.datetime.timetuple
        current_datetime_info = self.current_datetime.timetuple()

        month_index = current_datetime_info[1]-1

        if self.current_month is None:
            self.model_classes[f"{self.model_prefix}month_{self.MONTHS[month_index]}"] = 1
            self.model_classes[f"{self.model_prefix}months"] =  current_datetime_info[1]
            self.current_month = self.MONTHS[month_index]

        if not self.current_month == self.MONTHS[month_index]:
            self.changed_vars.append(f"{self.model_prefix}month_{self.current_month}")
            self.changed_vars.append(f"{self.model_prefix}month_{self.MONTHS[month_index]}")
            self.changed_vars.append(f"{self.model_prefix}months")

            self.model_classes[f"{self.model_prefix}month_{self.current_month}"] = 0
            self.model_classes[f"{self.model_prefix}month_{self.MONTHS[month_index]}"] = 1
            self.current_month = self.MONTHS[month_index]
            self.model_classes[f"{self.model_prefix}months"] =  current_datetime_info[1]

            # Variables that need their propensities updating

        if not self.model_classes[f"{self.model_prefix}day"] == current_datetime_info[2]:
            self.model_classes[f"{self.model_prefix}day"] = current_datetime_info[2]
            self.changed_vars.append(f"{self.model_prefix}day")
        
        rounded_hours = round(current_datetime_info[4]/60.0, 1)
        if not self.model_classes[f"{self.model_prefix}hour"] == current_datetime_info[3] + rounded_hours:
            self.model_classes[f"{self.model_prefix}hour"] = current_datetime_info[3] + rounded_hours
            self.changed_vars.append(f"{self.model_prefix}hour")


    def processUpdate(self, new_time):
        self.changed_vars = []
        if new_time == None:
            print("Ending model simulation")
            return
        self.updateTime(new_time)
        self.iterations += 1

    def updateTime(self, new_time):
        time_change = None
        time_diff = new_time - self.elapsed_time
        if self.time_measurement == "hours":
            time_change = timedelta(hours=time_diff)
        elif self.time_measurement == "days":
            time_change = timedelta(days=time_diff)
        else:
            raise(ValueError(f"Unsupported time increment type {self.time_measurement}"))
        
        self.current_datetime = self.current_datetime + time_change
        self.elapsed_time = new_time

        self.updateCalendarInfo()
        
    def returnModelClassesValues(self):
        return self.model_classes.values()
    
    def returnModelClasses(self):
        return list(self.model_classes.values())
                    
    def returnChangedVars(self):
        return self.changed_vars