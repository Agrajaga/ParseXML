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


def calc_total_cost(variant: ET.Element) -> float:
    counts_str = get_fare_basis(variant).split("__A")[1]
    adult_count, child_count, infant_count = map(int, counts_str.split("_"))

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


def get_variants(filename: str) -> list:
    tree = ET.parse(filename)
    root = tree.getroot()

    variants = []
    for variant in root.findall("./PricedItineraries/Flights"):
        variant_desc = {}
        flight_desc = {}

        variant_desc["FareBasis"] = get_fare_basis(variant)

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
    return variants


if __name__ == "__main__":
    variants = get_variants("RS_Via-3.xml")
    print(*[(v["FareBasis"], v["total_cost"], v["total_seconds"]) for v in variants], sep="\n")
