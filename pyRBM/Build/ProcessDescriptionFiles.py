import pandas as pd
import pyRBM.Build.Utils as Utils
import pyRBM.Build.RuleTemplates as RuleTemplates
from collections import defaultdict

#def process

def extractColumns(example_row, exlude_list:list = []):
    cols = []
    all_keys = example_row.keys()
    for col_i in range(len(all_keys)):
        col = all_keys[col_i]
        if not col in exlude_list:
            cols.append(col)
    return cols

def createMonthPropTerm(months:list):
    term_str = "("

    month_prefix = "model_month_"
    for month in months:
        if not term_str == "(":
            term_str += "+"
        term_str += f"{month_prefix}{month}"
    term_str += ")"

    return term_str

class CropStages:
    def __init__(self, stages_filepath:str, crops_filepath:str) -> None:
        crop_stages_data = pd.read_csv(stages_filepath, converters={})
        crops_background_data = pd.read_csv(crops_filepath)
        

        self.location_type_name = "FarmRegion"
        self.crop_stages_dict = defaultdict(list)
        self.crops = set([])
        self.crop_stage_info = {}
        self.additional_classes = ["Seeds", "Planted", "Harvested"]

        self.crop_info = {}

        self.stage_cols = []
        for i in range(len(crop_stages_data)):
            stage_row = crop_stages_data.iloc[i]
            if len(self.stage_cols) == 0:
                self.stage_cols = extractColumns(stage_row, exlude_list=["Crop","Growth Stage"])
            crop_name = stage_row["Crop"]
            crop_stage = stage_row["Growth Stage"]

            self.crops.add(crop_name)
            self.crop_stages_dict[crop_name].append(crop_stage)

            self.crop_stage_info[f"{crop_name}_{crop_stage}"] = {cols:stage_row[cols] for cols in self.stage_cols}
        
        for i in range(len(crops_background_data)):
            crop_row = crops_background_data.iloc[i]
            crop = crop_row["Crop"]
            self.crop_cols = []
            if len(self.crop_cols) == 0:
                self.crop_cols = extractColumns(crop_row, exlude_list=["Crop"])
            self.crop_info[f"{crop}"] = {cols:crop_row[cols] for cols in self.crop_cols}


        for crop in self.crops:
            self.crop_stages_dict[crop] += self.additional_classes
            for stage in self.additional_classes:
                self.crop_stage_info[f"{crop}_{stage}"] = {"Measurement Units":"Placeholder"}

    def returnBasicStageDict(self):
        return self.crop_stages_dict

    def returnCropRules(self):
        # Seeds, harvested, yield
        rules = []

        for crop in self.crops:
            last_crop_stage = None
            crop_info_dict = self.crop_info[crop]
            stages = self.crop_stages_dict[crop]
            for stage in stages:
                if not stage in self.additional_classes:
                    current_class_string = f"{crop}_{stage}"
                    
                    info = self.crop_stage_info[current_class_string]
                    target_str = None
                    if info["Next Growth Stage"] == "" or info["Next Growth Stage"] == " ":
                        if last_crop_stage is None:
                            last_crop_stage = stage
                        else:
                            raise(ValueError(f"Crop {crop} has atleast two final crop stages {last_crop_stage} and {stage}"))
                        target_str = crop+"_"+"Harvested"
                    else:
                        target_str = crop+"_"+info["Next Growth Stage"]

                    crop_growth_rule  = RuleTemplates.SingleLocationProductionRule(self.location_type_name,
                                                                        [crop+"_"+stage],[info["Transport Base Amt"]/info["Stochasticity"]],
                                                                        [target_str],[info["Transport Base Amt"]*info["Next Stage Measurement Factor"]/info["Stochasticity"]],
                                                                        f"{current_class_string}*{info['Stochasticity']}", [current_class_string],
                                                                        f"{crop} {stage} to {info['Next Growth Stage']} Crop Growth")
                    crop_death_rule = RuleTemplates.ExitEntranceRule(self.location_type_name,
                                                                        crop+"_"+stage,info["Transport Base Amt"],
                                                                        f"{current_class_string}*{info['Spoilage Rate']}", [current_class_string],
                                                                        f"{crop} {stage} Decay")
        
                    rules.append(crop_growth_rule)
                    rules.append(crop_death_rule)

            seed_period_term = createMonthPropTerm(crop_info_dict["Plant Period"].split(" "))
            first_stage = crop+"_"+crop_info_dict["First Stage"]
            seed_rule = RuleTemplates.SingleLocationProductionRule(self.location_type_name,
                                                                        [crop+"_Seeds"],[1000],
                                                                        [first_stage,crop+"_Planted"],[1000, 1000],
                                                                        f"{seed_period_term}*{crop}_Seeds*(loc_{crop_info_dict['Capacity Constant Name']} - {crop}_Planted)", [f"{crop}_Planted", f"{crop}_Seeds"],
                                                                         f"{crop} planting")
            harvest_period_term = createMonthPropTerm(crop_info_dict["Harvest Period"].split(" "))
            harvest_rule = RuleTemplates.SingleLocationProductionRule(self.location_type_name,
                                                                        [crop+"_"+last_crop_stage],[1],
                                                                        [crop+"_Harvested"],[1],
                                                                        f"{harvest_period_term}*{crop+'_'+last_crop_stage}", [current_class_string],
                                                                        f"Productive {crop} harvest")
            #for harvest_classes = [crop+harvest for harvest in []]
            #harvest_rules = BasicRules.ExitEntranceRule(self.location_type_name,
            #                                                            [crop+"_"+last_crop_stage],[1],
             #                                                           [crop+"_harvested"],[1],
            #                                                            f"{harvest_period_term}*{info['Stochasticity']}", [current_class_string])
            rules.append(seed_rule)
            rules.append(harvest_rule)
        return rules
    
    def returnCropClassData(self):
        crop_classes = [[f"{crop}_{stage}", self.crop_stage_info[f"{crop}_{stage}"]["Measurement Units"],"None"]
                        for crop in list(self.crop_stages_dict.keys()) for stage in self.crop_stages_dict[crop]]
        return crop_classes
class CropRegions:
    def __init__(self, region_filepath:str, crop_stages:CropStages) -> None:
        region_data = pd.read_csv(region_filepath)
        self.regions = []
        constants = []
        for i in range(len(region_data)):
            region_row = region_data.iloc[i]
            if len(constants) == 0:
                constants = extractColumns(region_row, exlude_list=["Name","Lat","Long"])
            
            region = Utils.FarmRegion(crop_stages.returnBasicStageDict(), region_row["Lat"], region_row["Long"], region_row["Name"])
            region.addAndSetConstants({constant.replace(" (Ha)","").replace(" ", "_"):float(region_row[constant]) for constant in constants})
            
            region.setInitialConditions({f"{crop}_Seeds":float(crop_stages.crop_info[crop]["Starting Seeds"]) for crop in crop_stages.crops})

            self.regions.append(region)
        
    def returnRegions(self):
        return self.regions