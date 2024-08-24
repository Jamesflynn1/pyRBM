import datetime

import pyRBM.Core.Model as Model
import pyRBM.Build.Locations as ModelLocations
import pyRBM.Build.RuleTemplates as BasicRules
import pyRBM.Simulation.Solvers as Solvers
# seeding_rate in tonnes/ha (hectacre is 2.47105 acres)
# 39.3679 bushels of wheat is a tonne 
model_constants = {
    "Wheat_seeding_rate":0.11,
    "Cereals_seeding_rate":0.2,
    "Barley_seeding_rate":0.3,
    "Potatoes_seeding_rate":0.1,
    "Wheat_germination_rate":1
}

supplyChainClasses = [["NH4", "tonnes"], ["N2", "m^3"], ["H2", "m^3"], ["CH4", "m^3"]]

class FarmRegion(ModelLocations.Location):
    def __init__(self, crop_list:list, lat:float, long:float, name:str, constants = None):
        # Sets lat/long and creates and empty set of compartment labels.
        super().__init__(lat, long, name, loc_type="FarmRegion", constants=constants)
        # Crops exist in three stages in this simplified model: planted, growing and harvested.
        for crop in crop_list:
            self.class_labels.add(crop[0])

# Crop classes:
# Biggest crops as example, from defra https://www.gov.uk/government/statistics/agriculture-in-the-united-kingdom-2022/chapter-7-crops
crops = ["Wheat", "Cereals", "Barley", "Potatoes"]

for crop in crops:
    supplyChainClasses +=  [[f"Seeds_{crop}", "Tonnes"], [f"Planted_{crop}", "Hectacres"], [f"Growing_{crop}", "Hectacres"], [f"Viable_{crop}", "Tonnes"], [f"Harvested_{crop}", "Tonnes"]]

def returnCropRules():    
    rules = []

    # Crop rules
    # TODO add seasonallity.
    # TODO limit based on supply.
    for crop in crops:
        # SIMPLIFIED RULE FOR BASE MODEL
        # Fix requirement of non None propensity class.
        purchase_seeds = BasicRules.ExitEntranceRule(target="FarmRegion", transport_class=f"Seeds_{crop}", transport_amount=1, propensity="0.1", propensity_classes=[f"Seeds_{crop}"],
                                                           rule_name="Purchase Seeds")

        sow_crop = BasicRules.SingleLocationProductionRule(target="FarmRegion",
                                                                        reactant_classes=[f"Seeds_{crop}"], reactant_amount=[1], 
                                                                        product_classes=[f"Planted_{crop}"], product_amount=[model_constants[f"{crop}_seeding_rate"]], propensity=f"Seeds_{crop}",
                                                                        propensity_classes=[f"Seeds_{crop}"], rule_name=f"Sow {crop}")
        
        germinating_crop = BasicRules.SingleLocationProductionRule(target="FarmRegion",
                                                                        reactant_classes=[f"Planted_{crop}"], reactant_amount=[1], 
                                                                        product_classes=[f"Growing_{crop}"], product_amount=[1], propensity=f"0.1*Planted_{crop}",
                                                                        propensity_classes=[f"Planted_{crop}"], rule_name=f"Germinate {crop}")
        # TODO make dependant on Nitrogen levels ect ect.
        crop_growth = BasicRules.SingleLocationProductionRule(target="FarmRegion",
                                                                        reactant_classes=[f"Growing_{crop}"], reactant_amount=[1], 
                                                                        product_classes=[f"Viable_{crop}"], product_amount=[1], propensity=f"Growing_{crop}",
                                                                        propensity_classes=[f"Growing_{crop}"], rule_name=f"Germinate {crop}")
        
        # May need to make propensity based on planted field size, will need to check.
        harvest_crop = BasicRules.SingleLocationProductionRule(target="FarmRegion",
                                                                        reactant_classes=[f"Viable_{crop}"], reactant_amount=[1], 
                                                                        product_classes=[f"Harvested_{crop}"], product_amount=[1], propensity=f"Viable_{crop}",
                                                                        propensity_classes=[f"Viable_{crop}"], rule_name=f"Harvest {crop}")
        rules += [purchase_seeds, sow_crop, germinating_crop, crop_growth, harvest_crop]

    return rules
def supplyChainLocations():
    # Billingham terminal - Produces Ammonium nitrate from Ammonia
    # https://www.cfindustries.com/newsroom/2023/billingham-ammonia-plant
    # https://www.cfindustries.com/what-we-do/fertilizer
    all_locations = []
    # Midpoints from wikipedia, South East and London uses South East midpoint (combined to match DEFRA reporting)
    region_infos = [[54.075, -2.75, "North East"], [55, -1.87, "North West"], [53.566667, -1.2, "Yorkshire & The Humber"], [52.98, -0.75, "East Midlands"], [52.478861, -2.256306, "West Midlands"], 
                    [52.24, 0.41, "East of England"], [51.3, -0.8, "South East & London"], [50.96, -3.22, "South West"], [56.816738, -4.183963, "Scotland"], [52.33022, -3.766409,"Wales"]]
    for region_info in region_infos:
        all_locations.append(FarmRegion(supplyChainClasses, *region_info))

    
    return all_locations

model = Model.Model("Basic Crop")
model.buildModel(supplyChainClasses, supplyChainLocations, returnCropRules, write_to_file = True, save_model_folder="Tests/ModelFiles/")

model.initializeSolver(Solvers.GillespieSolver)
start_date = datetime.datetime(2001, 8, 1)
model.simulate(start_date, 100)

model.trajectory.plotAllClassesOverTime(1)