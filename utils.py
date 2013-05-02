import math
def components(val,angle):
    """
    Decomposes the supplied vector in x-y components.

    Params
    ------
    val : float
    angle : float, in radians
    """
    return (val*math.cos(angle),val*math.sin(angle))
