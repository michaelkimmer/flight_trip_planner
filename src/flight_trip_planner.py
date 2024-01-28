import urllib.request, json 
import datetime

DEBUG_RYANAIR = True
DEBUG_BSF = True


class Airport():
    def __init__(self, code, memory_ref) -> None:
        # Info
        self.code = code
        self.memory_ref = memory_ref
        # self.name = None # Name of the airport
        
        # Data
        self.cheapDestinations = {'Ryanair': []} # list of codes
        self.data_destinations = []  # Connection objects
        self.data_incommings = []    # Connection objects
        
        # Bools
        self.cheapDestinations_searched = {'Ryanair': False}
        self.flights_searched = {'Ryanair': False}


    # Get all cheap destinations + flights
    def search_Ryanair_cheapDestinations(self, trip_boundraries, max_price):
        # Escape when already done
        if self.cheapDestinations_searched['Ryanair']:
            return
        self.cheapDestinations_searched['Ryanair'] = True
        
        # Get cheap destinations
        max_destinations = 50
        with urllib.request.urlopen(f"https://www.ryanair.com/api/farfnd/3/oneWayFares?&ToUs=AGREED&departureAirportIataCode={self.code}&language=en&limit={max_destinations}&market=en-ie&offset=0&outboundDepartureDateFrom={trip_boundraries[0].strftime('%Y-%m-%d')}&outboundDepartureDateTo={trip_boundraries[1].strftime('%Y-%m-%d')}&priceValueTo={max_price}") as url:
            destinations_json = json.load(url)
        # TODO: Exception
        
        
        # DEBUG -- print all Ryanair_cheapDestinations
        if DEBUG_RYANAIR:
            print("DEBUG search_Ryanair_cheapDestinations:")
            # print(destinations_json['fares'])
            for destination in destinations_json['fares']:
                print(destination['outbound']['arrivalAirport']['name'], end=" --- ")
                print(destination['outbound']['price']['value'])
        
        # Save codes of all cheap destinations
        for destination in destinations_json['fares']:
            dest_code = destination['outbound']['arrivalAirport']['iataCode']
            self.cheapDestinations['Ryanair'].append(dest_code)       
            
        # Create connection between Airports (if nonexistent)
        for dest_code in self.cheapDestinations['Ryanair']:
            if dest_code not in self.data_destinations:
                dest_airport_ref = self.memory_ref.get_ref(dest_code)
                connection = Connection(self, dest_airport_ref)
                # Append the connection ref to both airports
                self.data_destinations.append(connection)
                dest_airport_ref.data_incommings.append(connection)
                
        # Get flights into each cheap destinations
        for dest_code in self.cheapDestinations['Ryanair']:
            # self._search_Ryanair_cheapFlights(trip_boundraries, max_price)
            pass

    # Get cheap flights into destination --> FILL its connection
    def _search_Ryanair_cheapFlights(self, connection, trip_boundraries, max_price):
        source = connection.airport_departure
        dest = connection.airport_arrival
        
        
        # Get 1 month of flights !!
        # years
        # months
        # for month in ...:
        #     with urllib.request.urlopen(f"https://www.ryanair.com/api/farfnd/3/oneWayFares/{source.code}/{dest.code}/cheapestPerDay?ToUs=AGREED&market=en-gb&outboundMonthOfDate=2024-{month:02}-01") as url:
        #         data_month = json.load(url)
        
        # N_days = len(self.data_month['outbound']['fares'])
        # currency = self.data_month['outbound']['fares'][0]['price']['currencyCode']
        
        # days = [self.data_month['outbound']['fares'][i]['day'] for i in range(N_days)]
        # departureDates = [self.data_month['outbound']['fares'][i]['departureDate'] for i in range(N_days)]
        # arrivalDates = [self.data_month['outbound']['fares'][i]['arrivalDate'] for i in range(N_days)]
        
        # prices = [self.data_month['outbound']['fares'][i]['price']['value'] for i in range(N_days)]
        
        # for day,departureDate, arrivalDate, price in zip(days, departureDates, arrivalDates, prices):
        #     print(f"{day} ({departureDate} --> {arrivalDate}): {price} {currency}")
            
        pass


# Dict Memory of all used airports
class Airports_Dict():
    def __init__(self) -> None:
        self.airports_memory = {}
        
    def get_ref(self, code):
        if code not in self.airports_memory:
            self.airports_memory[code] = Airport(code, self)
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
    def __init__(self, airport_departure, airport_arrival, companies=[], days_departure=[], prices=[], times_departure=[], times_arrival=[]) -> None:
        assert len(companies) == len(days_departure) == len(prices) == len(times_departure) == len(times_arrival), "Parameters must meet: len(times_departure) == len(times_arrival) == len(prices)"
        
        self.airport_departure = airport_departure  # Airport object
        self.airport_arrival = airport_arrival      # Airport object
        
        self.companies = companies
        self.days_departure = days_departure
        self.prices = prices
        self.times_departure = times_departure
        self.times_arrival = times_arrival
        
        
    
    # Check emptiness of the Flight
    def isEmpty(self):
        return not self.time_departure or not self.time_arrival or not self.price
    
    def add_flight(self, company, day_depature, price, time_departure=None, time_arrival=None):
        self.companies.append(company)
        self.days_departure.append(day_depature)
        self.prices.append(price)
        
        self.times_departure.append(time_departure)
        self.times_arrival.append(time_arrival)
        
        
    
    
    
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


    # Search for routes: BSF from Trip_Source --> Trip_Destination
    def searchBSF(self):
    
        # Outcome -- 2D List of Connections forming valid paths
        valid_paths = []
    
        # Initialize BSF with sources (Airports)
        current_sources = self.source.airports
        
        for source in current_sources:
            source.search_Ryanair_cheapDestinations(trip_boundraries, trip_max_price)
    
    
        if DEBUG_BSF:
            pass
        
        
        
        
        
        
        

        
        
        
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
    
    # Search for an optimal paths
    trip.searchBSF()
    
    # Debug END
    pass

