from datetime import datetime
from xml.etree import cElementTree as ET


def descript_flight(flight: ET.Element) -> dict:
    flight_desc = {}
    flight_desc["Carrier_id"] = flight.find("Carrier").get("id")
    for flight_attrib in flight:
        if flight_attrib.tag == "FareBasis":
            continue
        flight_desc[flight_attrib.tag] = flight_attrib.text
    return flight_desc


def get_fare_basis(variant: ET.Element) -> str:
    return variant.find(
        "OnwardPricedItinerary/Flights/Flight/FareBasis").text.strip()


def get_fare(variant: ET.Element, type: str) -> float:
    xpath = f".//ServiceCharges[@type='{type}'][@ChargeType='TotalAmount']"
    service_charge = variant.find(xpath)
    if service_charge is None:
        return 0.0
    return float(service_charge.text)


def get_passengers_counts(fare_basis: str) -> tuple[int, int, int]:
    counts_str = fare_basis.split("__A")[1]
    return tuple(map(int, counts_str.split("_")))


def calc_total_cost(variant: ET.Element) -> float:
    fare_basis = get_fare_basis(variant)
    adult_count, child_count, infant_count = get_passengers_counts(fare_basis)

    adult_cost = get_fare(variant, "SingleAdult") * adult_count
    child_cost = get_fare(variant, "SingleChild") * child_count
    infant_cost = get_fare(variant, "SingleInfant") * infant_count
    return (adult_cost * 100 + child_cost * 100 + infant_cost * 100) / 100


def calc_flight_time(variant: ET.Element, branch_name: str) -> int:
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
    onward_time = calc_flight_time(variant, "OnwardPricedItinerary")
    return_time = calc_flight_time(variant, "ReturnPricedItinerary")
    return onward_time + return_time


def parse_response(filename: str) -> dict:
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

        options = {}
        options["filename"] = filename
        options["roundtrip"] = bool(flight_desc["return"])
        passengers_counts = get_passengers_counts(fare_basis)
        options["adults"] = passengers_counts[0]
        options["childs"] = passengers_counts[1]
        options["infants"] = passengers_counts[2]

        variants.append(variant_desc)

    return {
        "options": options,
        "variants": variants,
        }


def get_distinctions(response1: dict, response2: dict) -> tuple:
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


if __name__ == "__main__":
    response1 = parse_response("RS_Via-3.xml")
    response2 = parse_response("RS_ViaOW.xml")

    print(get_distinctions(response1, response2))
    variants = response1["variants"]

    print("Дешевый/дорогой\n")
    variants.sort(key=lambda v: v["total_cost"])
    print(variants[0])
    print()
    print(variants[-1])

    print("\nБыстрый/медленный\n")
    variants.sort(key=lambda v: v["total_seconds"])
    print(variants[0])
    print()
    print(variants[-1])

    print("\nОптимальный\n")
    print(get_optimal(variants, cost_weight=0.5, time_weight=0.5))
