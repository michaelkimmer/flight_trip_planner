import urllib.request, json 
import datetime



class Airport():
    def __init__(self, code) -> None:
        self.code = code
        # self.name = None # Name of the airport
        self.data_destinations = []  # Connection objects
        self.data_incommings = []    # Connection objects
        self.destination_searched = {'Ryanair': False}


    def search_Ryanair_cheapDestinations(self, trip_boundraries, max_price):
        self.destination_searched['Ryanair'] = True
        
        max_destinations = 50
        with urllib.request.urlopen(f"https://www.ryanair.com/api/farfnd/3/oneWayFares?&ToUs=AGREED&departureAirportIataCode={self.code}&language=en&limit={max_destinations}&market=en-ie&offset=0&outboundDepartureDateFrom={trip_boundraries[0].strftime('%Y-%m-%d')}&outboundDepartureDateTo={trip_boundraries[1].strftime('%Y-%m-%d')}&priceValueTo={max_price}") as url:
            destinations_json = json.load(url)
        # TODO: Exception
        
        
        # TODO: 
        print(destinations_json['fares'])
        for destination in destinations_json['fares']:
            print(destination['outbound']['arrivalAirport']['name'], end=" --- ")
            print(destination['outbound']['price']['value'])
        
        #self.data_destinations.append()

# Dict Memory of all used airports
class Airports_Dict():
    def __init__(self) -> None:
        self.airports_memory = {}
        
    def get_ref(self, code):
        if code not in self.airports_memory:
            self.airports_memory[code] = Airport(code)
        return self.airports_memory[code]
    
    def isSaved(self, code):
        return code in self.airports_memory
            
    
      
      
# Nodes sets of searching algorithm (Each can include more airports), (Transfers then can include only one airport)
class Trip_Stop():
    def __init__(self, memory, codes, duration) -> None:
        self.duration = duration # Time interval (eg. 2-4 days)
        self.airports = [memory.get_ref(code) for code in codes]
        
class Trip_Source():
    def __init__(self, memory, codes) -> None:
        self.airports = [memory.get_ref(code) for code in codes]
        
class Trip_Destination():
    def __init__(self, memory, codes) -> None:
        self.airports = [memory.get_ref(code) for code in codes]


# Represents connection == all flights: airport_departure ---> airport_arrival
# A Connection can be COMPLETE (== all info included) or NOT (then other parameters can be set later)
class Connection():
    def __init__(self, airport_departure, airport_arrival, times_departure=[], times_arrival=[], prices=[], companies=[]) -> None:
        assert len(times_departure) == len(times_arrival) == len(prices), "Parameters must meet: len(times_departure) == len(times_arrival) == len(prices)"
        
        self.airport_departure = airport_departure  # Airport object
        self.airport_arrival = airport_arrival      # Airport object
        self.times_departure = times_departure
        self.times_arrival = times_arrival
        self.prices = prices
        self.companies = companies
    
    # Check emptiness of the Flight
    def isEmpty(self):
        return not self.time_departure or not self.time_arrival or not self.price
    
    def add_flight(self, time_departure, time_arrival, price, company):
        self.times_departure.append(time_departure)
        self.times_arrival.append(time_arrival)
        self.prices.append(price)
        self.companies.append(company)
    
    
    
class Trip():
    def __init__(self, sources_codes, destinations_codes, stops_codes, stops_durations, trip_boundraries, trip_max_price) -> None:
        
        # Check codes vs durations
        assert len(stops_codes) == len(stops_durations), "Stops must meet: len(stops_codes) == len(stops_durations)"
        
        # TODO: check codes validity 
        
        # TODO: Select stop_code None for Anything 
        
        # Select trip_boundraries None for whole next month
        if trip_boundraries is None:
            trip_boundraries = (datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(days=30))
        
        
        
        # Create Airport memory (adding is done by getting refs)
        self.airports_memory = Airports_Dict()

        
        # Create Trip stops objects
        self.source = Trip_Source(self.airports_memory, sources_codes)  
        self.destination = Trip_Destination(self.airports_memory, destinations_codes) 
        self.stops = [Trip_Stop(self.airports_memory, stop_codes, stop_duration) for stop_codes, stop_duration in zip(stops_codes, stops_durations)]  # Obligatory stops
        
        # Save other trip parameters
        self.trip_boundraries = trip_boundraries
        self.trip_max_price = trip_max_price

        
        
        
        
        
  
    # TODO: recycle !!
    # Get month flights
    def get_data_month(self, month):
        with urllib.request.urlopen(f"https://www.ryanair.com/api/farfnd/3/oneWayFares/PRG/STN/cheapestPerDay?ToUs=AGREED&market=en-gb&outboundMonthOfDate=2024-{month:02}-01") as url:
            data_month = json.load(url)
        return data_month
    
    def print_data_month(self):
        N_days = len(self.data_month['outbound']['fares'])
        currency = self.data_month['outbound']['fares'][0]['price']['currencyCode']
        
        days = [self.data_month['outbound']['fares'][i]['day'] for i in range(N_days)]
        departureDates = [self.data_month['outbound']['fares'][i]['departureDate'] for i in range(N_days)]
        arrivalDates = [self.data_month['outbound']['fares'][i]['arrivalDate'] for i in range(N_days)]
        
        prices = [self.data_month['outbound']['fares'][i]['price']['value'] for i in range(N_days)]
        
        
        for day,departureDate, arrivalDate, price in zip(days, departureDates, arrivalDates, prices):
            print(f"{day} ({departureDate} --> {arrivalDate}): {price} {currency}")
        
        
        
############## MAIN ##############
if __name__ == "__main__":
    time_now = datetime.datetime.now()
    time_inMonth = time_now + datetime.timedelta(days=30)
    
    sources_codes = ('PRG', 'BRQ')
    destinations_codes = ('PRG', 'BRQ')
    stops_codes = [('STN', 'LTN')]
    stops_durations = [(2,4)]
    trip_boundraries = [time_now, time_inMonth]
    trip_max_price = 1000 #TODO: currency !

    trip = Trip(sources_codes, destinations_codes, stops_codes, stops_durations, trip_boundraries, trip_max_price)
    
    # TODO: search flights
    trip.source.airports[1].search_Ryanair_cheapDestinations(trip.trip_boundraries, trip.trip_max_price)


