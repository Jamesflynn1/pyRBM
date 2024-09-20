from typing import Union, Sequence, Any
import numpy as np
from math import radians, cos, sin, asin, sqrt

# Credit to https://stackoverflow.com/questions/29545704/fast-haversine-approximation-python-pandas

def haversine(lon1:Union[float, int], lat1:Union[float, int],
              lon2:Union[float, int], lat2:Union[float, int]) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2.0 * asin(sqrt(a))
    km = 6367.0 * c
    return km

def createEuclideanDistanceMatrix(lats:Sequence[Union[float, int]],
                                  longs:Sequence[Union[float, int]]) -> np.ndarray[Any]:
    # Only need to find the upper right triangle.
    distm = np.zeros((len(lats), len(lats)))
    for i in range(len(lats)):
        for h in range(i, len(longs)):
            distm[i][h] = haversine(longs[i], lats[i], longs[h],  lats[h])
    # Fill in the lower left triangle
    distm = distm.T+distm
    return distm


def parseVarName(class_name:str):
    return class_name.replace(" ", "_")