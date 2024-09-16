# Used for propensity caching - given a rule, find all rules that require an updated propensity

# Use stoichiometry information to determine which
from collections import defaultdict

import sympy

def _classToRuleDict(rules, locations, matched_indices, base_classes):
    ctr_dict = defaultdict(set)
    base_ctr_dict = defaultdict(set)
    for rule_i in range(len(matched_indices)):
        rule = rules[rule_i]
        for index_set_i in range(len(matched_indices[rule_i])):
            for slot_i, loc_i in enumerate(matched_indices[rule_i][index_set_i]):
                loc_classes_num = len(locations[loc_i].class_values)
                loc_symbols = rule.sympy_formula[slot_i].atoms(sympy.Symbol)
                #rtc_dict[f"{rule_i} {index_set_i}"].update([f"{str(symbol)} {loc_i}" for symbol in loc_symbols])
                for symbol in loc_symbols:
                    class_index = int(str(symbol)[1:])
                    if class_index < loc_classes_num:
                        ctr_dict[f"{str(symbol)} {loc_i}"].update([f"{rule_i} {index_set_i}"])
                    else:
                        base_ctr_dict[base_classes[loc_classes_num-class_index]].update([f"{rule_i} {index_set_i}"])
    return ctr_dict, base_ctr_dict

# Use propensity infomation to determine which rules require updating based on a change in class value
def _ruleToClassesDict(rules, matched_indices):
    rtc_dict = defaultdict(set)
    for rule_i in range(len(matched_indices)):
        rule = rules[rule_i]
        for index_set_i in range(len(matched_indices[rule_i])):
            for slot_i, loc_i in enumerate(matched_indices[rule_i][index_set_i]):
                #rtc_dict[f"{rule_i} {index_set_i}"].update([f"{str(symbol)} {loc_i}" for symbol in loc_symbols])
                rtc_dict[f"{rule_i} {index_set_i}"].update([f"x{i} {loc_i}"
                                                            for i in range(len(rule.stoichiometry[slot_i]))
                                                            if not rule.stoichiometry[slot_i][i] == 0])
    return rtc_dict

# Returns a dictionary that maps a rule index to a set of all rule indices that have a changed propensity after a rule trigger.
def _ruleToRule(rtc_dict, ctr_dict):
    rtr_dict = {rule_location_key:set()
                for rule_location_key in rtc_dict}

    for rule_location_key in rtr_dict:
        for class_loc in rtc_dict[rule_location_key]:
            rule_index = [index.split(" ")
                          for index in ctr_dict[class_loc]]
            rtr_dict[rule_location_key].update([(int(index[0]),int(index[1]))
                                                for index in rule_index])
    return rtr_dict

def returnOneStepRuleUpdates(rules, locations,
                             matched_indices, base_classes):
    rtc_dict = _ruleToClassesDict(rules, matched_indices)
    ctr_dict, base_ctr_dict = _classToRuleDict(rules, locations,
                                               matched_indices, base_classes)
    return _ruleToRule(rtc_dict, ctr_dict)|base_ctr_dict
