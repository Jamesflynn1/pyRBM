from numpy.random import default_rng
class Distribution:
    def __init__(self, params:dict[str,float], random_source=None):
        
        self.distrib_name = "distribution"

        self.params = params
        self.laplace_compat = self.isLaplaceGillespieCompatible()
        self.nmga_compat = self.isNMGACompatible()
        if random_source is None:
            self.random_source = default_rng(None)
        else:
            self.random_source = random_source
        if self.laplace_compat:
            self.laplace_random_function = self.returnRandomLaplaceFunc()
        if self.nmga_compat:
            self.nmga_random_function = self.returnRandomNMGAFunc()

        if not self.nmga_compat and not self.laplace_compat:
            raise ValueError(f"Distribution with parameters {str(params)} cannot be used with either the Laplace Gillespie or non-Markovian Gillespie algorithms")

    def returnStringRepr(self):
        if len(self.params) > 0:
            param_strings = [f",{param}={value}" for param, value in self.params.items()]
            return "".join([self.distrib_name]+param_strings)
        else:
            return self.distrib_name
    
    def isLaplaceGillespieCompatible(self):
        try:
            has_valid_params = self.checkParamsLaplace()
            self.returnRandomLaplaceFunc()
            return has_valid_params
        except NotImplementedError:
            return False
        except ValueError:
            return False

    def isNMGACompatible(self):
        try:
            has_valid_params = self.checkParams()
            self.returnRandomNMGAFunc()
            return has_valid_params
        except NotImplementedError:
            return False
        except ValueError:
            return False
    
    def checkParams(self):
        raise NotImplementedError("checkParams not implemented")
    
    def checkParamsLaplace(self):
        raise NotImplementedError("checkParamsLaplace not implemented")
    
    def returnLaplaceRate(self, propensity=0):
        return self.laplace_random_function(propensity)

    def returnRate(self, propensity=0):
        return self.nmga_random_function(propensity)

    def returnRandomLaplaceFunc(self):
        raise NotImplementedError("returnRandomLaplaceFunc not implemented")
    
    def returnRandomNMGAFunc(self):
        raise NotImplementedError("returnRandomNMGAFunc not implemented")

class ExponentialDistribution(Distribution):
    def __init__(self, params, random_source=None):
        super().__init__(params, random_source)
        self.distrib_name = "exponential"
    def checkParamsLaplace(self):
        return True
    def returnRandomLaplaceFunc(self):
        return lambda x: x

class UniformPowerLawDistribution(Distribution):
    def __init__(self, params, random_source=None):
        super().__init__(params, random_source)
        self.distrib_name = "uniform_power_law"

    def checkParamsLaplace(self):
        # For a static rate distribution, define the rate_min and rate_max and not the rate_spread.
        if "rate_spread" in self.params and "rate_min" not in self.params:
            self.params["rate_min"] = 0
        
        if (self.params["rate_min"] < 0 or
            ("rate_max" in self.params and self.params["rate_min"] > self.params["rate_max"]) or
            ("rate_spread" in self.params and self.params["rate_spread"] < 0)):
            raise ValueError("Rate parameters must be non negative and the minimum rate value must be less than the maximum (if set).")
        return True
    
    def returnRandomLaplaceFunc(self):
        if "rate_spread" in self.params:
            half_spread = self.params["rate_spread"]/2
            if "rate_max" in self.params:
                return lambda x: self.random_source.uniform(max(self.params["rate_min"], x-half_spread), min(self.params["rate_max"], x+half_spread), 1)[0]
            else:
                return lambda x: self.random_source.uniform(max(self.params["rate_min"], x-half_spread), x+half_spread, 1)[0]
        else:
            return lambda x: self.random_source.uniform(self.params["rate_min"], self.params["rate_max"], 1)[0]

class GammaPowerLawDistribution(Distribution):
    def __init__(self, params, random_source=None):
        super().__init__(params, random_source)
        self.distrib_name = "gamma_power_law"

    def checkParamsLaplace(self):
        # For a static rate distribution, define the scale.
        required_params = ["shape"]
        for param in required_params:
            if not param in self.params or self.params[param] is None:
                raise ValueError("shape must be defined")
        if self.params["shape"] <= 0 or ("scale" in self.params and self.params["scale"] <= 0):
            raise ValueError("Gamma distribution shape and scale must be positive.")
        return True
    
    def returnRandomLaplaceFunc(self):
        if "scale" in self.params:
            return lambda x: self.random_source.gamma(self.params["shape"], self.params["scale"], 1)[0]
        # Dynamic distribution with mean rate drawn equal to the standard rate.
        else:
            return lambda x: self.random_source.gamma(self.params["shape"], max(1e-16, x/self.params["shape"]), 1)[0]

class ShiftedGammaPowerLawDistribution(Distribution):
    def __init__(self, params, random_source=None):
        super().__init__(params, random_source)
        self.distrib_name = "shifted_gamma_power_law"

    
    def checkParamsLaplace(self):
        required_params = ["shape", "scale", "shift"]
        for param in required_params:
            if not param in self.params or self.params[param] is None:
                raise ValueError("gamma_scale and rate_max must be defined")
        if self.params["shape"] <= 0 or self.params["scale"] <= 0 or self.params["shift"] < 0:
            raise ValueError("Shifted Gamma distribution shape and scale must be positive and the shift must be non-negative")
        return True
    # Double check definition as this diverages from the Laplace paper but often this form is given.
    def returnRandomLaplaceFunc(self):
        return lambda x: self.random_source.gamma(self.params["shape"], self.params["scale"], 1) +  self.params["shift"][0]

class DoublePowerLawDistribution(Distribution):
    def __init__(self, params, random_source=None):
        super().__init__(params, random_source)
        self.distrib_name = "double_power_law_distribution"

    def checkParamsLaplace(self):
        required_params = ["alpha"]
        for param in required_params:
            if not param in self.params or self.params[param] is None:
                raise ValueError("Powerlaw alpha must be defined")
        if self.params["alpha"] <= -1:
            raise ValueError("The power law distribution must have an alpha of >= -1 (note this uses the shifted alpha as described in the Laplace Gillespie paper).")
        return True
    # Double check definition as this diverages from the Laplace paper but often this form is given.
    def returnRandomLaplaceFunc(self):
        return lambda x: self.random_source.power(self.params["alpha"]+1, 1)[0]

class GammaDistribution(Distribution):
    
    def __init__(self, params, random_source=None):
        super().__init__(params, random_source)
    
    def checkParamsLaplace(self):
        required_params = ["alpha", "kappa"]
        for param in required_params:
            if not param in self.params or self.params[param] is None:
                raise ValueError("gamma_scale and rate_max must be defined")
        if self.params["alpha"] > 0 and self.params["alpha"] <= 1:
            raise ValueError("The Gamma distribution must have an alpha of 1 >= alpha > 0")
        return True
    # Shape parameter alpha must be 0<alpha<1 for the Laplace transform
    def returnRandomLaplaceFunc(self):
        return None
        #return lambda x: 

class MittagLefflerDistribution(Distribution):
    def tba(self):
        pass

class DistributionFactory:
    """ Used to create distributions from their string representations
    """
    def __init__(self):

        self.distributions = {"exponential":ExponentialDistribution,
                              "uniform_power_law":UniformPowerLawDistribution,
                              "gamma_power_law":GammaPowerLawDistribution,
                              "shifted_gamma_power_law":ShiftedGammaPowerLawDistribution,
                              "double_power_law_distribution":DoublePowerLawDistribution,
                              "gamma_distribution":GammaDistribution
                              }

    def createDistribution(self, distrib_name:str, distribution_args:dict[str,float], random_source=None):
        if not distrib_name in self.distributions:
            raise ValueError(f"Distribution {distrib_name} not implemented\nPlease choose from the following distributions {list(self.distributions.keys())}.")
        distribution = self.distributions[distrib_name]
        try:
            return distribution(distribution_args, random_source)
        except ValueError:
            raise ValueError(f"Distribution has incorrect parameters for its type\nArgs: {distribution_args}, Type: {self.distributions[distrib_name]}")

def processDistributionString(distribution_string:str):
    try:
        args = distribution_string.split(",")
        distribution_name = args[0]
        distribution_args = {}
        if len(args)>1:
            for key_value in args[1:]:
                key, value = key_value.split("=")
                if key in distribution_args:
                    raise ValueError(f"Repeat distribution parameter {key} provided")
                else:
                    distribution_args[key] = float(value)
        return (distribution_name, distribution_args)
    except:
        raise ValueError(f"Distribution string {distribution_string} is incorrectly formatted")