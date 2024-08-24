import Application
import datetime

start_date = datetime.datetime(2001, 8, 1)

epi_application = Application.ModelBackend(start_date=start_date, model_folder="Backend/ModelFiles/CropModelv1/", propensity_caching=True)
out = epi_application.simulate(time_limit=365, max_iterations=1000000)

out.plotAllClassesOverTime(location_index=1)