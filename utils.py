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

def bracket(vmin,val,vmax):
    """
    Returns the value, ensuring it sits within supplied limits.
    """
    val = min(val,vmax)
    val = max(val,vmin)
    return val
