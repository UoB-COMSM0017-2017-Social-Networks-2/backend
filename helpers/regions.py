import json
import random
import logging

from shapely.geometry import Point, shape, box

PLACES_CACHE_FILE = "output/places_cache.json"
SAMPLE_POINTS_FOR_REGION_FILE = "output/sample_points_for_region_file.json"


class Region:
    """
    The region id is {level}_{id}, as some IDs appear in level 1 and 2.
    """

    def __init__(self, name, region_id, parent_id):
        self.name = name
        self.region_id = region_id
        self.parent_id = parent_id
        self.shape = None
        self.nb_leaf_descendants = None
        self.leaf = None
        self.sub_region_ids = None

    def set_shape(self, region_shape):
        self.shape = region_shape

    def has_shape(self):
        return self.shape is not None

    def contains_point(self, point):
        if not self.has_shape():
            return False
        return self.shape.contains(point)

    def get_parent(self):
        for region in get_all_regions():
            if region.region_id == self.parent_id:
                return region
        return None

    def get_number_of_leaf_descendants(self):
        if self.nb_leaf_descendants is None:
            self.nb_leaf_descendants = len(
                list(filter(lambda r: r.is_leaf(), map(get_region_by_id, self.get_all_sub_region_ids()))))
        return self.nb_leaf_descendants

    def get_all_sub_region_ids(self):
        if self.sub_region_ids is None:
            self.sub_region_ids = set()
            for region in get_all_regions():
                if is_in_region(region, get_region_by_id(self.region_id)):
                    self.sub_region_ids.add(region.region_id)
        return set(self.sub_region_ids)

    def get_ancestors(self):
        res = []
        current = self.get_parent()
        while current is not None:
            res.append(current)
            current = current.get_parent()
        return res

    def is_leaf(self):
        if self.leaf is None:
            self.leaf = not any(region.parent_id == self.region_id for region in get_all_regions())
        return self.leaf


all_regions_dict = dict()


def load_regions():
    global all_regions_dict
    all_regions_dict = dict()
    with open('data/GBR_GeoJSON.json', 'r', encoding="utf-8") as f:
        gbr_data = json.load(f)
        regions_data = gbr_data["features"]
        for region_data in regions_data:
            properties = region_data["properties"]
            ids = []
            names = []
            leaf_id = None
            for i in range(10):
                name_key = "NAME_{}".format(i)
                id_key = "ID_{}".format(i)
                if name_key not in properties or id_key not in properties:
                    if name_key in properties or id_key in properties:
                        print("#ids != #names")
                    break
                names.append(properties[name_key])
                leaf_id = "{}_{}".format(i, properties[id_key])
                ids.append(leaf_id)

            prev_region_id = None
            for name, region_id in zip(names, ids):
                if region_id not in all_regions_dict:
                    region = Region(name, region_id, prev_region_id)
                    all_regions_dict[region_id] = region
                prev_region_id = region_id

            all_regions_dict[leaf_id].set_shape(shape(region_data['geometry']))


if len(all_regions_dict) == 0:
    load_regions()


def get_all_regions():
    return all_regions_dict.values()


def is_in_region(region, ancestor):
    if ancestor is None:
        return True
    if region is None:
        return False
    if region.region_id == ancestor.region_id:
        return True
    return is_in_region(region.get_parent(), ancestor)


def get_region_by_id(region_id):
    if region_id not in all_regions_dict:
        return None
    return all_regions_dict[region_id]


def get_global_region():
    return get_region_by_id("0_242")


# Function that returns region name based on input data
def get_smallest_region_by_coordinates(longitude, latitude):
    point = Point(longitude, latitude)
    containing_region = None
    for region in get_all_regions():
        if region.has_shape() and region.contains_point(point):
            if is_in_region(region, containing_region):
                containing_region = region
    return containing_region


places_cache = dict()


def load_places_cache():
    global places_cache
    with open(PLACES_CACHE_FILE, 'r') as f:
        places_cache = json.load(f)


if len(places_cache) == 0:
    load_places_cache()


def write_places_cache():
    with open(PLACES_CACHE_FILE, 'w') as f:
        json.dump(places_cache, f)


def update_places_cache(place, region):
    places_cache[place["id"]] = {
        "region_id": region.region_id,
        "region_name": region.name,
        "place_name": place["name"],
        "place_full_name": place["full_name"]
    }
    logging.info("New place-region match: {} - {}".format(place["name"], region.name))
    write_places_cache()


def get_sample_points_in_rectangle(bounds, nb_points):
    """
    
    :param bounds: (minx, miny, maxx, maxy)
    :param nb_points: 
    :return: 
    """
    return [Point(random.uniform(bounds[0], bounds[2]), random.uniform(bounds[1], bounds[3])) for _ in range(nb_points)]


def get_sample_points_in_polygon(shape, nb_points):
    good_points = []
    while len(good_points) < nb_points:
        new_points = get_sample_points_in_rectangle(shape.bounds, nb_points)
        good_points.extend([p for p in new_points if shape.contains(p)][:nb_points - len(good_points)])
    return good_points


NB_REGION_POINTS = 100
NB_BOUNDING_BOX_POINTS = 100

sample_points_cache_for_region = dict()


def load_sample_points_for_region_cache():
    global sample_points_cache_for_region
    with open(SAMPLE_POINTS_FOR_REGION_FILE, 'r') as f:
        data = json.load(f)
        sample_points_cache_for_region = {
            k: [Point(p["x"], p["y"]) for p in data[k]] for k in data
        }


def write_sample_points_for_region_cache():
    with open(SAMPLE_POINTS_FOR_REGION_FILE, 'w') as f:
        json.dump({
            k: [{"x": p.x, "y": p.y} for p in sample_points_cache_for_region[k]] for k in sample_points_cache_for_region
        }, f)


if len(sample_points_cache_for_region) == 0:
    load_sample_points_for_region_cache()


def get_sample_points_in_region(region):
    if region.region_id not in sample_points_cache_for_region:
        print("Sampling points for {}!".format(region.name))
        sample_points_cache_for_region[region.region_id] = get_sample_points_in_polygon(region.shape, NB_REGION_POINTS)
        print("Got points")
        write_sample_points_for_region_cache()
    return sample_points_cache_for_region[region.region_id]


def get_region_for_bounding_box(bounding_box):
    bounding_box_points = get_sample_points_in_rectangle(bounding_box.bounds, NB_BOUNDING_BOX_POINTS)
    best_matching_region = None
    nb_best_matches = 0
    for region in get_all_regions():
        if not region.has_shape():
            continue
        region_points = get_sample_points_in_region(region)
        nb_region_points_in_bounding_box = len([p for p in region_points if bounding_box.contains(p)])
        nb_bounding_box_points_in_region = len([p for p in bounding_box_points if region.contains_point(p)])
        # Criteria 1: bounding box is not too much outside the region
        if nb_bounding_box_points_in_region / NB_BOUNDING_BOX_POINTS < .9:
            continue
        # Select region that has the highest ratio of points in the bounding box
        if nb_region_points_in_bounding_box > nb_best_matches:
            best_matching_region = region
            nb_best_matches = nb_region_points_in_bounding_box
    return best_matching_region


def get_matching_region_for_place_bbs(place):
    best_area_ratio = 0
    best_region = None
    place_bb = shape(place["bounding_box"])
    if place_bb.area < 1e-5:
        return None
    for region in get_all_regions():
        if not region.has_shape():
            continue
        region_bb = region.shape.bounds
        region_bb_shape = box(region_bb[0], region_bb[1], region_bb[2], region_bb[3])
        intersection = region_bb_shape.intersection(place_bb)
        if intersection.area / place_bb.area < .90:
            # place is not part of region
            continue
        area_ratio = intersection.area / region_bb_shape.area
        if area_ratio > best_area_ratio:
            best_region = region
            best_area_ratio = area_ratio
    return best_region


def get_matching_region_for_place_geo(place):
    return get_region_for_bounding_box(shape(place["bounding_box"]))


def get_matching_region_for_place_name(place):
    for region in get_all_regions():
        if region.name == place["name"]:
            return region
    return None


def get_matching_region_for_place(place):
    # global places_cache
    # places_cache = {}
    if place is None:
        return None
    place_id = place["id"]
    if place_id not in places_cache:
        region = get_matching_region_for_place_name(place)
        if region is None:
            region = get_matching_region_for_place_geo(place)
        if region is None:
            region = get_matching_region_for_place_bbs(place)
        if region is None:
            region = get_global_region()
        update_places_cache(place, region)
    return get_region_by_id(places_cache[place_id]["region_id"])
