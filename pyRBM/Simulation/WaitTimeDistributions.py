import numpy.random as rand

distrib_functions = {
        # Delta function peaked at the desired rate.
        "expo": lambda x: x,
        "gamma-derived-power-law":rand
        #""
    }
#def generateGammaFunction
def processDistribFunction(wait_time_distribution_and_args):
    df_args_list = wait_time_distribution_and_args.split("_")
    distrib_name = df_args_list.pop(0)
    df_args_list = [float(arg) for arg in df_args_list]

    return lambda rate : distrib_functions[distrib_name](rate, *df_args_list)
