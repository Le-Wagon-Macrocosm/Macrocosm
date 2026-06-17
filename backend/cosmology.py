"""z -> distance.  TASK 05."""
import numpy as np
from astropy.cosmology import Planck18
import astropy.units as u

def z_to_distance_gly(z):
    """z (float or array-like) -> Planck18 comoving distance in billions of light-years
    (return a float for scalar input, a list for array input)."""

    z_array = np.asarray(z)
    z_array = np.clip(z_array, 0, None)

    distance = Planck18.comoving_distance(z_array)
    distance_gly = distance.to(u.Glyr).value

    if np.ndim(z) == 0:
        return float(distance_gly)

    return distance_gly.tolist()
