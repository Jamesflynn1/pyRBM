import matplotlib.pyplot as plt
import matplotlib.animation as pltAnimate
import numpy as np



class SolverDataPlotting:
     
     def __init__(self, model):
        assert(model.solver.debug)
        self.fig, self.ax = plt.subplots(2,2)

        self.rule_names = [str(rule)for rule in list(model.matched_rules_dict.keys())]
        self.rule_index_set_names = [f"{rule}_{index}"for rule in self.rule_names for index in range(len(model.matched_rules_dict[rule]))]

        self.rule_plot = FrequencyBarChart(self.fig, self.ax[0][0], "Frequency of rule execution", "Rule Number", model.solver_diag_data, self.rule_names, "rule_triggered")
        self.rule_index_plot = FrequencyBarChart(self.fig, self.ax[1][0], "Frequency of rule execution with given index set", "Rule-Index set", model.solver_diag_data, self.rule_index_set_names, "rule_index_set")

        plt.show(block=False)

class FrequencyBarChart:
      def __init__(self, fig, plot, title:str, x_label_str:str, solver_data, x_labels:list, data_key:str, rerender_all = True):
        self.display = plot
        self.fig = fig
        self.display.title.set_text(title)
        self.display.set(xlabel=x_label_str, ylabel='Frequency')
        start_height = [0 for _ in x_labels]
        self.bar_chart = self.display.bar(x_labels, start_height)
        self.data_key = data_key

        self.current_max_value = 10
        self.prior_iteration_height = start_height
        self.x_labels = x_labels

        self.solver_data = solver_data
        self.current_simulation = 0
        
        self.plot_anim = pltAnimate.FuncAnimation(fig, self.animate, save_count = 100, interval=1000, blit=not rerender_all)

        self.display.set_ylim(0, self.current_max_value)

        self.prior_bar_charts = []

      def animate(self, i):
        changed_plot_elements = []
        for i, rects in enumerate(self.bar_chart):
            new_height = self.solver_data.iterations_frequency[self.current_simulation][self.data_key][self.x_labels[i]] #+ self.prior_iteration_height[i]
            if not new_height == rects.get_height:
              rects.set_height(new_height)
              changed_plot_elements.append(rects)
              if self.current_max_value < new_height:
                  self.current_max_value *= int(self.current_max_value*1.1)
                  self.display.set_ylim(0, self.current_max_value)
                  #changed_plot_elements.append(self.display)
                  changed_plot_elements.append(self.fig)
        
        while len(self.solver_data.iterations_frequency) > self.current_simulation+1:
            new_bottom = [self.prior_iteration_height[i] + self.solver_data.iterations_frequency[self.current_simulation][self.data_key][x]
                          for i, x in enumerate(self.x_labels)]
            
            new_iteration_height = [self.solver_data.iterations_frequency[self.current_simulation+1][self.data_key][x]
                                    for x in self.x_labels]

            self.prior_iteration_height = new_bottom
            self.bar_chart = self.display.bar(self.x_labels, new_iteration_height, bottom = new_bottom)

            changed_plot_elements += [rects for rects in self.bar_chart]

            self.current_simulation += 1

        return tuple(changed_plot_elements)
