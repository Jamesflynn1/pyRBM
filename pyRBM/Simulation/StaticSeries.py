import pandas as pd
class TimeSeries:

    def __init__(self, source_filepath:str):
        self.file_ending = source_filepath.split('.')[-1]

        if self.file_ending == "csv":
            time_series_data = pd.read_csv(source_filepath, converters={})
            print(time_series_data)

        else:
            raise(ValueError(f"File ending {self.file_ending} is currently an unsupported time series."))
    
TimeSeries("Backend/ModelSimulation/testfiles/ts.csv")