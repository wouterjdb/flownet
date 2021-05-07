from typing import List, Optional
import time

from scipy.spatial import Delaunay  # pylint: disable=no-name-in-module
import numpy as np

from ..utils.types import Coordinate
from ._hull import check_in_hull
from ._mitchell import scale_convex_hull_perforations

# pylint: disable=too-many-branches,too-many-statements
def mitchell_best_candidate_fast(
    perforations: List[Coordinate],
    num_added_flow_nodes: int,
    num_candidates: int,
    hull_factor: float,
    place_nodes_in_volume_reservoir: Optional[bool] = None,
    concave_hull_bounding_boxes: Optional[np.ndarray] = None,
    random_seed: Optional[int] = None,
) -> List[Coordinate]:

    # pylint: disable=too-many-locals,invalid-name
    # Currently 39(!) local variables in this code

    """
    Python implementation of a modified Mitchell's Best-Candidate Algorithm to generate additional flow nodes in
    real field cases.

    The algorithm will generate locations for additional flow nodes where the distance to all existing flow nodes
    is maximized. The added flow nodes are located inside the (possibly scaled) convex hull of the
    supplied perforations.

    Args:
        perforations: Python list of real well coordinate tuples
            [(xr_1, yr_1, zr_1), ..., (xr_N, yr_N, zr_N)]
        num_added_flow_nodes: Number of additional flow nodes to generate
        num_candidates: Number of candidates to consider per additional flow nodes
        place_nodes_in_volume_reservoir: When true, additional nodes will initially be placed inside
            the bounding box of the reservoir or layer instead of the bounding box of the well perforations.
        hull_factor: Factor to linearly scale the convex hull with. Factor will
            scale the distance of each point from the centroid of all the points.
            Default defined in config parser is 1.2.
        concave_hull_bounding_boxes: Numpy array with x, y, z min/max boundingboxes for each grid block
        random_seed: Random seed to control the reproducibility of the FlowNet.

    Returns:
        Python list of real/original and added flow node coordinate tuples
            [(xr_1, yr_1, zr_1), ..., (xr_N, yr_N, zr_N), (xi_1, yi1, zi1)
            ... (xi_n_i, yi_n_i, zi_n_i)]

    """
    np.random.seed(random_seed)
    start = time.time()
    print("Adding flow nodes:  0%", end="")

    # Read list of coordinate tuples and convert to 1D-numpy arrays
    x, y, z = (np.asarray(t) for t in zip(*perforations))

    # Number of real wells
    num_points = len(x)

    # Bounding box to place initial candidates in: reservoir volume or (scaled) convex hull of real perforations.
    if place_nodes_in_volume_reservoir:
        x_mins, x_maxs, y_mins, y_maxs, z_mins, z_maxs = np.hsplit(
            concave_hull_bounding_boxes, 6
        )

        x_min = min(x_mins)[0]
        x_max = max(x_maxs)[0]
        y_min = min(y_mins)[0]
        y_max = max(y_maxs)[0]
        z_min = min(z_mins)[0]
        z_max = max(z_maxs)[0]
    else:
        # Determine whether the convex hull needs to be scaled
        if not np.isclose(hull_factor, 1.0):
            x_hull, y_hull, z_hull = scale_convex_hull_perforations(
                perforations, hull_factor
            )
            x_min = min(x_hull)
            x_max = max(x_hull)
            y_min = min(y_hull)
            y_max = max(y_hull)
            z_min = min(z_hull)
            z_max = max(z_hull)
        else:
            x_min = min(x)
            x_max = max(x)
            y_min = min(y)
            y_max = max(y)
            z_min = min(z)
            z_max = max(z)
            x_hull = x
            y_hull = y
            z_hull = z

        # Determine the convex hull of the original or linearly scaled perforations
        if np.all(z == z[0]):
            # 2D cases
            perforation_hull = Delaunay(np.column_stack([x_hull, y_hull]))
        else:
            # 3D cases
            perforation_hull = Delaunay(np.column_stack([x_hull, y_hull, z_hull]))

    in_hull = np.asarray([False] * num_candidates)
    x_candidate = np.zeros(num_candidates)
    y_candidate = np.zeros(num_candidates)
    z_candidate = np.zeros(num_candidates)

    # Repeat while not all random points are inside the convex hull
    while not all(in_hull):
        # Generate a set of random candidates that will be the new
        # flow nodes
        x_candidate_tmp = x_min + np.random.rand(num_candidates) * (x_max - x_min)
        y_candidate_tmp = y_min + np.random.rand(num_candidates) * (y_max - y_min)
        z_candidate_tmp = z_min + np.random.rand(num_candidates) * (z_max - z_min)

        # Update the list of flow node candidates. Only the points that previously
        # were not inside the convex hull are updated.
        np.putmask(x_candidate, np.invert(in_hull), x_candidate_tmp)
        np.putmask(y_candidate, np.invert(in_hull), y_candidate_tmp)
        np.putmask(z_candidate, np.invert(in_hull), z_candidate_tmp)

        candidates = np.vstack([x_candidate, y_candidate, z_candidate]).T

        if concave_hull_bounding_boxes is not None:
            in_hull = check_in_hull(
                concave_hull_bounding_boxes, candidates, in_hull_known=in_hull
            )
        else:
            # Test whether all points are inside the convex hull of the perforations
            if np.all(z == z[0]):
                in_hull = perforation_hull.find_simplex(candidates[:, (0, 1)]) >= 0
            else:
                in_hull = perforation_hull.find_simplex(candidates) >= 0

    # Generate all new flow nodes
    for i in range(num_points, num_points + num_added_flow_nodes):
        mid = time.time()
        if mid - start > 4:
            start = mid
            print(
                f"\rAdding flow nodes:  {int(((i-num_points)/num_added_flow_nodes)*100)}%",
                end="",
            )

        delta_x_relative = np.power(
            (x.repeat(num_candidates) - x_candidate.repeat(x.shape[0]))
            / (x_max - x_min),
            2,
        )
        delta_y_relative = np.power(
            (y.repeat(num_candidates) - y_candidate.repeat(y.shape[0]))
            / (y_max - y_min),
            2,
        )
        if np.all(z == z[0]):
            delta_z_relative = 0
        else:
            delta_z_relative = np.power(
                (
                    z.repeat(num_candidates)
                    - z_candidate.repeat(z.shape[0]) / (z_max - z_min)
                ),
                2,
            )

        dists = np.sqrt(delta_x_relative + delta_y_relative + delta_z_relative)
        best_candidate = np.argmax(dists)

        # Add the best candidate's coordinates; a new flow node is added
        x = np.append(x, x_candidate.repeat(x.shape[0])[best_candidate])
        y = np.append(y, y_candidate.repeat(y.shape[0])[best_candidate])
        z = np.append(z, z_candidate.repeat(z.shape[0])[best_candidate])

    print("\rAdding flow nodes:  100%\ndone.")

    # Return the real/original and added flow node coordinates as a list of tuples.
    return [(x[i], y[i], z[i]) for i in range(len(x))]
