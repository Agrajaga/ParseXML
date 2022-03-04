import argparse
import json
from datetime import datetime
from xml.etree import cElementTree as ET


def descript_flight(flight: ET.Element) -> dict:
    """ Populate the dictionary with flight attributes"""
    flight_desc = {}
    flight_desc["Carrier_id"] = flight.find("Carrier").get("id")
    for flight_attrib in flight:
        if flight_attrib.tag == "FareBasis":
            continue
        flight_desc[flight_attrib.tag] = flight_attrib.text
    return flight_desc


def get_fare_basis(variant: ET.Element) -> str:
    """ Find and format FareBasis value"""
    return variant.find(
        "OnwardPricedItinerary/Flights/Flight/FareBasis").text.strip()


def get_fare(variant: ET.Element, type: str) -> float:
    """ Finds the total cost of the flight for the specified type of passenger

        *type* one of these values: SingleAdult, SingleChild, SingleInfant

        Return 0.0 if selected type is not found
    """
    xpath = f".//ServiceCharges[@type='{type}'][@ChargeType='TotalAmount']"
    service_charge = variant.find(xpath)
    if service_charge is None:
        return 0.0
    return float(service_charge.text)


def get_passengers_counts(fare_basis: str) -> tuple[int, int, int]:
    """ Parses the FareBasis code and returns the number of passengers
     of various types: adults, children, infants"""
    counts_str = fare_basis.split("__A")[1]
    return tuple(map(int, counts_str.split("_")))


def calc_total_cost(variant: ET.Element) -> float:
    """ Calculate the total cost of the flight"""
    fare_basis = get_fare_basis(variant)
    adult_count, child_count, infant_count = get_passengers_counts(fare_basis)

    adult_cost = get_fare(variant, "SingleAdult") * adult_count
    child_cost = get_fare(variant, "SingleChild") * child_count
    infant_cost = get_fare(variant, "SingleInfant") * infant_count
    return (adult_cost * 100 + child_cost * 100 + infant_cost * 100) / 100


def calc_flight_time(variant: ET.Element, branch_name: str) -> int:
    """ Calculate in seconds the flight time in the selected direction

        *branch_name* for onward or return direction

        Return 0 if selected direction is empty
    """
    departure_ts = variant.find(
        f"./{branch_name}//Flight[1]/DepartureTimeStamp")
    arrival_ts = variant.find(
        f"./{branch_name}//Flight[last()]/ArrivalTimeStamp")
    if departure_ts is None or arrival_ts is None:
        return 0

    dt_format = "%Y-%m-%dT%H%M"
    departure = datetime.strptime(departure_ts.text, dt_format)
    arrival = datetime.strptime(arrival_ts.text, dt_format)
    return int((arrival - departure).total_seconds())


def calc_total_time(variant: ET.Element) -> int:
    """ Calculate in seconds the total flight time"""
    onward_time = calc_flight_time(variant, "OnwardPricedItinerary")
    return_time = calc_flight_time(variant, "ReturnPricedItinerary")
    return onward_time + return_time


def parse_response(filename: str) -> dict:
    """ Parses XML and populates a list of flight variants\
         and search options"""
    tree = ET.parse(filename)
    root = tree.getroot()

    variants = []
    for variant in root.findall("./PricedItineraries/Flights"):
        variant_desc = {}
        flight_desc = {}

        fare_basis = get_fare_basis(variant)
        variant_desc["FareBasis"] = fare_basis

        flight_desc["onward"] = []
        for flight in variant.findall("OnwardPricedItinerary/Flights/Flight"):
            flight_desc["onward"].append(descript_flight(flight))

        flight_desc["return"] = []
        for flight in variant.findall("ReturnPricedItinerary/Flights/Flight"):
            flight_desc["return"].append(descript_flight(flight))

        variant_desc["flight"] = flight_desc
        variant_desc["total_cost"] = calc_total_cost(variant)
        variant_desc["total_seconds"] = calc_total_time(variant)

        variants.append(variant_desc)

    options = {}
    options["filename"] = filename
    options["roundtrip"] = bool(flight_desc["return"])
    adult_count, child_count, infant_count = get_passengers_counts(fare_basis)
    options["adults"] = adult_count
    options["childs"] = child_count
    options["infants"] = infant_count

    return {
        "options": options,
        "variants": variants,
    }


def get_distinctions(response1: dict, response2: dict) -> tuple:
    """ Compares the search options and returns distinctions"""
    options1 = {}
    options2 = {}
    for option in response1["options"]:
        if response1["options"][option] != response2["options"][option]:
            options1[option] = response1["options"][option]
            options2[option] = response2["options"][option]

    return (options1, options2)


def get_optimal(
        variants: list,
        cost_weight: float = 0.5,
        time_weight: float = 0.5) -> dict:
    """ Find the optimal flight by time and cost"""

    cost_sum, time_sum = 0, 0
    for variant in variants:
        cost_sum += variant["total_cost"]
        time_sum += variant["total_seconds"]
    return sorted(
        variants,
        key=lambda v:
        (v["total_seconds"] / time_sum) * time_weight +
        (v["total_cost"] / cost_sum) * cost_weight
    )[0]


def get_all_variants(filename: str) -> list:
    """ Create a list of all flight variants"""
    flights = []
    response = parse_response(filename)
    for variant in response["variants"]:
        flights.append(variant["flight"])
    return flights


def get_best_variants(filename: str) -> dict:
    """ Calculate cheapest/expensive, fastest/slowest and optimal flight"""
    flights = {}
    variants = parse_response(filename)["variants"]
    variants.sort(key=lambda v: v["total_cost"])
    flights["cheapest"] = variants[0].copy()
    flights["expensive"] = variants[-1].copy()
    variants.sort(key=lambda v: v["total_seconds"])
    flights["fastest"] = variants[0].copy()
    flights["slowest"] = variants[-1].copy()
    flights["optimal"] = get_optimal(variants)
    return flights


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse the XML response about flights from via.com \
         and return JSON")
    parser.add_argument("file1", help="XML response from via.com")
    parser.add_argument(
        "--human",
        action="store_true",
        help="human-readable output")
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--all",
        action="store_true",
        help="return all flight variants")
    group.add_argument(
        "--best",
        action="store_true",
        help="return cheapest/expensive, fastest/slowest and optimal variants")
    group.add_argument(
        "--compare",
        nargs=1,
        metavar="file2",
        help="return differences in query parameters")
    args = parser.parse_args()

    indent = " " if args.human else None
    if args.all:
        print(json.dumps(get_all_variants(args.file1), indent=indent))
    if args.best:
        print(json.dumps(get_best_variants(args.file1), indent=indent))
    if args.compare:
        response1 = parse_response(args.file1)
        response2 = parse_response(args.compare[0])
        distinctions = get_distinctions(response1, response2)
        print(json.dumps(distinctions, indent=indent))
