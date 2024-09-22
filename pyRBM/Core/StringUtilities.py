import re

def parseVarName(class_name:str):
    return class_name.replace(" ", "_")

def replaceVarName(propensity_str, var_name, replacement, ignore_underscore = True):
    # The regex matches var_name except when preceeded by any alphanumeric characters
    # or succeded by any alphanumeric characters.
    additional_criteria =  "|_" if not ignore_underscore else ""

    regex_str = fr"(?<!([A-z]|\d{additional_criteria})){var_name}(?![A-z]|\d{additional_criteria})"

    return re.sub(regex_str, replacement, propensity_str)