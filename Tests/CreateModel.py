import ProcessDescriptionFiles
import ModelDefinition


desc_folder = "Backend/ModelCreation/DescriptionFiles/"
cs = ProcessDescriptionFiles.CropStages(f"{desc_folder}CropsStages.csv", f"{desc_folder}Crops.csv")
crop_regions = ProcessDescriptionFiles.CropRegions(f"{desc_folder}Regions.csv", cs)


model = ModelDefinition.ModelDefinition(cs.returnCropClassData(), crop_regions.returnRegions, cs.returnCropRules, model_folder="Backend/ModelFiles/CropModelv1/")
model.build()