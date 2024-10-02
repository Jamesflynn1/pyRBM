def checkDistribArgs(distrib_name, args):
    if distrib_name == "expo":
        assert len(args) == 1
        assert args[0] >= 0
    elif distrib_name == "gamma-derived-power-law":
        assert len(args) == 2
def processDistribFunction(random_source, wait_time_distribution_and_args):
    df_args_list = wait_time_distribution_and_args.split("_")
    distrib_name = df_args_list.pop(0)
    df_args_list = [float(arg) for arg in df_args_list]
    
    distrib_functions = {
        # Delta function peaked at the desired rate.
        "expo": lambda lambda_0: lambda_0,
        "gamma-derived-power-law": random_source.gamma
        #""
    }
    checkDistribArgs(distrib_name, df_args_list)

    return lambda : distrib_functions[distrib_name](*df_args_list)
