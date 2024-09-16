from typing import Optional
import matplotlib.pyplot as plt
import numpy as np

from pyRBM.Simulation.Location import Location

class Trajectory:
    def __init__(self, locations:list[Location]) -> None:
        self.timestamps = {location_index:[0]
                           for location_index, _ in enumerate(locations)}
        self.trajectory_location_values = {location_index:[location.class_values]
                                           for location_index, location in enumerate(locations)}
        self.last_time = 0
        self.last_location_index:Optional[int] = None
        self.location_labels = {location_index:location.label_mapping
                                for location_index, location in enumerate(locations)}
        self.location_names = {location_index:location.name
                               for location_index, location in enumerate(locations)}

    def addEntry(self, time, location_values,
                 location_index:int) -> None:
        if location_index != self.last_location_index:
            # Add last known time and value
            self.trajectory_location_values[location_index].append(self.trajectory_location_values[location_index]
                                                                   [len(self.trajectory_location_values[location_index])-1])
            self.timestamps[location_index].append(self.last_time)

        self.trajectory_location_values[location_index].append(location_values)
        self.timestamps[location_index].append(time)

        self.last_time = time
        self.last_location_index = location_index

    def plotAllClassesOverTime(self, location_index:int,
                               figure_position:str = "center left") -> None:
        # ALLOW NONE AS ENTRY
        class_values = np.array(self.trajectory_location_values[location_index])
        for class_i in range(len(class_values[0])):
            plt.plot(self.timestamps[location_index], class_values[:,class_i])
        plt.legend([self.location_labels[location_index][str(i)].replace("_", " ")
                    for i in range(len(self.location_labels[location_index]))],
                    loc=figure_position)
        plt.title(f"Classes over time for {self.location_names[location_index]}")
        plt.show()