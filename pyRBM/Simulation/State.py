# This file is used to allow
from typing import Iterable, Any
from datetime import timedelta, datetime

import numpy as np

class ModelState:
    def __init__(self, model_classes:Iterable[str], start_datetime:datetime) -> None:
        self.MONTHS =  ["jan", "feb", "mar", "apr", "may", "jun",
                        "jul", "aug", "sept", "oct", "nov", "dec"]
        self.model_prefix = "model_"

        self.IMPLEMENTED_MODEL_CLASSES = [f"model_{var}"
                                          for var in ["day", "hour", "months"]]
        self.IMPLEMENTED_MODEL_CLASSES += [f"model_month_{month}"
                                           for month in self.MONTHS]
        self.model_classes:dict[str,Any] = {}
        self.changed_vars = []

        self.time_measurement = "days"

        for model_class in model_classes:
            if model_class in self.IMPLEMENTED_MODEL_CLASSES:
                self.model_classes[model_class] = None
            else:
                raise ValueError(f"Model class {model_class} not implemented")
            
        self.resetClassVars()

        self.elapsed_time = 0
        self.iterations = 0
        self.current_month = None

        if isinstance(start_datetime, datetime):
            self.start_datetime = start_datetime
            self.current_datetime = start_datetime
        else:
            raise ValueError(f"Start date must be of type datetime not {type(start_datetime)}")
        self._updateCalendarInfo()
    
    def resetClassVars(self):
        for model_class in self.model_classes:
            self.changeModelClassValue(model_class[len(self.model_prefix):], 0)


    def reset(self) -> None:
        self.changed_vars = []
        self.elapsed_time = 0
        self.iterations = 0
        self.current_datetime = self.start_datetime
        self._updateCalendarInfo()
    
    def changeModelClassValue(self, class_name:str, new_value:Any):
        class_name = f"{self.model_prefix}{class_name}"
        if new_value != self.model_classes[class_name]:
            self.model_classes[class_name] = new_value
            self.changed_vars.append(class_name)
    
    def changeMonth(self, old_month, new_month, new_month_index):
        if old_month != new_month:
            if old_month is not None:
                self.changeModelClassValue(f"month_{old_month}", 0)
                self.changeModelClassValue(f"month_{new_month}", 1)
            self.changeModelClassValue("months", new_month_index)
            
            self.current_month = new_month

    def changeDate(self, new_date:datetime) -> None:
        self.start_datetime = new_date
        self.reset()

    def _updateCalendarInfo(self) -> None:
        # https://docs.python.org/3/library/datetime.html#datetime.datetime.timetuple
        current_datetime_info = self.current_datetime.timetuple()

        month_index = current_datetime_info[1]-1
        # changeModelClassValue checks for a change in value, we incurr a small performance cost in the function call at the benefit of
        # much more maintainable code.
        self.changeMonth(self.current_month, self.MONTHS[month_index], month_index)
        self.changeModelClassValue("day", current_datetime_info[2])

        rounded_hours = round(current_datetime_info[4]/60.0, 1)
        self.changeModelClassValue("hour", current_datetime_info[3] + rounded_hours)


    def processUpdate(self, new_time) -> None:
        self.changed_vars = []
        if new_time is None:
            print("Ending model simulation")
            return
        self._updateTime(new_time)
        self.iterations += 1

    def _updateTime(self, new_time) -> None:
        time_change = None
        time_diff = new_time - self.elapsed_time
        if self.time_measurement == "hours":
            time_change = timedelta(hours=time_diff)
        elif self.time_measurement == "days":
            time_change = timedelta(days=time_diff)
        else:
            raise ValueError(f"Unsupported time increment type {self.time_measurement}")

        self.current_datetime = self.current_datetime + time_change
        self.elapsed_time = new_time

        self._updateCalendarInfo()

    def returnModelClassesValues(self) :
        return self.model_classes.values()

    def returnModelClasses(self):
        return list(self.model_classes.keys())

    def returnChangedVars(self) -> list[str]:
        return self.changed_vars
