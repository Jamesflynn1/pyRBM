from typing import Optional
import matplotlib.pyplot as plt
import numpy as np

from pyRBM.Simulation.Compartment import Compartment

class Trajectory:
    def __init__(self, compartments:list[Compartment]) -> None:
        self.timestamps = {compartment_index:[0]
                           for compartment_index, _ in enumerate(compartments)}
        self.trajectory_compartment_values = {compartment_index:[compartment.class_values]
                                           for compartment_index, compartment in enumerate(compartments)}
        self.last_time = 0
        self.last_compartment_index:Optional[int] = None
        self.compartment_labels = {compartment_index:compartment.label_mapping
                                for compartment_index, compartment in enumerate(compartments)}
        self.compartment_names = {compartment_index:compartment.name
                               for compartment_index, compartment in enumerate(compartments)}
        
        #self.time_resolution = 

    def addEntry(self, time, compartment_values,
                 compartment_index:int) -> None:
        if compartment_index != self.last_compartment_index:
            # Add last known time and value
            self.trajectory_compartment_values[compartment_index].append(self.trajectory_compartment_values[compartment_index]
                                                                   [len(self.trajectory_compartment_values[compartment_index])-1])
            self.timestamps[compartment_index].append(self.last_time)

        self.trajectory_compartment_values[compartment_index].append(compartment_values)
        self.timestamps[compartment_index].append(time)

        self.last_time = time
        self.last_compartment_index = compartment_index

    def plotAllClassesOverTime(self, compartment_index:int,
                               figure_position:str = "center left") -> None:
        # ALLOW NONE AS ENTRY
        class_values = np.array(self.trajectory_compartment_values[compartment_index])
        for class_i in range(len(class_values[0])):
            plt.plot(self.timestamps[compartment_index], class_values[:,class_i])
        plt.legend([self.compartment_labels[compartment_index][str(i)].replace("_", " ")
                    for i in range(len(self.compartment_labels[compartment_index]))],
                    loc=figure_position)
        plt.title(f"Classes over time for {self.compartment_names[compartment_index]}")
        plt.show()