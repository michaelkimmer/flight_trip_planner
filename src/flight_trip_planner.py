import urllib.request, json 
import datetime
import time # sleep
import random
import pickle # save and load objects

DEBUG_BASIC = True
DEBUG_RYANAIR = False
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
        # self.flights_searched = {'Ryanair': False}


    # Get all cheap destinations + flights
    def search_Ryanair_cheapDestinations(self, trip_boundaries, max_price):
        # Escape when already done
        if self.cheapDestinations_searched['Ryanair']:
            return
        self.cheapDestinations_searched['Ryanair'] = True

        if DEBUG_BASIC:
            print(f"Getting cheap destinations from {self.code}")
        
        # Get cheap destinations
        max_destinations = 50
        time.sleep(0.5*random.random()) #sleep random time 0..0.5s
        with urllib.request.urlopen(f"https://www.ryanair.com/api/farfnd/3/oneWayFares?&ToUs=AGREED&departureAirportIataCode={self.code}&language=en&limit={max_destinations}&market=en-ie&offset=0&outboundDepartureDateFrom={trip_boundaries[0].strftime('%Y-%m-%d')}&outboundDepartureDateTo={trip_boundaries[1].strftime('%Y-%m-%d')}&priceValueTo={max_price}") as url:
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
                
        
        # Fill each connection with flights (Get flights into this cheap destinations)  
        for connection in self.data_destinations:
            if connection.airport_arrival.code in self.cheapDestinations['Ryanair']:
                self._search_Ryanair_cheapFlights(connection, trip_boundaries, max_price)
            


    # Get cheap flights into destination --> FILL its connection
    def _search_Ryanair_cheapFlights(self, connection, trip_boundaries, max_price):
        source = connection.airport_departure
        dest = connection.airport_arrival
        
        if DEBUG_BASIC:
            print(f"Getting cheap flights {source.code}-->{dest.code}")
        
        # months one by one -- iterate
        year_min = trip_boundaries[0].year
        year_max = trip_boundaries[1].year
        for year in range(year_min, year_max + 1):
            if year == year_min:
                month_min = trip_boundaries[0].month
            else:
                month_min = 1
            if year == year_max:
                month_max = trip_boundaries[1].month
            else:
                mont_max = 12
            for month in range(month_min, month_max + 1):
                
                # Get 1 month of flights !!
                time.sleep(0.5*random.random()) #sleep random time 0..0.5s
                with urllib.request.urlopen(f"https://www.ryanair.com/api/farfnd/3/oneWayFares/{source.code}/{dest.code}/cheapestPerDay?ToUs=AGREED&market=en-gb&outboundMonthOfDate={year:4}-{month:02}-01") as url:
                    data_month = json.load(url)
                # TODO: Exception
                
                # Process the monthly data
                # TODO: currency
                N_days = len(data_month['outbound']['fares'])
                # currency = self.data_month['outbound']['fares'][0]['price']['currencyCode']
                
                prices = []
                departureDates = []
                arrivalDates = []
                for i in range(N_days):
                    if not data_month['outbound']['fares'][i]['unavailable']:
                        departureDate_str = data_month['outbound']['fares'][i]['departureDate']
                        arrivalDate_str = data_month['outbound']['fares'][i]['arrivalDate']
                        price = data_month['outbound']['fares'][i]['price']['value'] #TODO: currency !!
                        
                        prices.append(price)
                        departureDates.append(datetime.datetime.strptime(departureDate_str, '%Y-%m-%dT%H:%M:%S'))
                        arrivalDates.append(datetime.datetime.strptime(arrivalDate_str, '%Y-%m-%dT%H:%M:%S') )
                        
                    
                # Save all OK fights in this connection
                for price, departureDate, arrivalDate in zip(prices, departureDates, arrivalDates):
                    # if price <= max_price:  # Do this in searching --> save all data
                    # TODO: max dates can be outside the boundaries !
                    connection.add_flight('Ryanair', departureDate, price, departureDate, arrivalDate)
            


# Dict Memory of all used airports
class Airports_Dict():
    def __init__(self) -> None:
        self.airports_memory = {}

        # For saving and loading obtained data
        self.date_created = datetime.datetime.now()
        self.filename = "src/saved_data/airports_memory.pkl"
        
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
    def __init__(self, airport_departure, airport_arrival, flights=None) -> None:        
        self.airport_departure = airport_departure  # Airport object
        self.airport_arrival = airport_arrival      # Airport object
        if flights is None:
            self.flights = []
        
    # Check emptiness of the Flight
    def isEmpty(self):
        return not self.flights
    
    def add_flight(self, company, day_depature, price, time_departure=None, time_arrival=None):
        newFlight = Flight(self.airport_departure, self.airport_arrival, company, day_depature, price, time_departure, time_arrival)
        self.flights.append(newFlight)
        

        
# Data structure stored in Connection       
class Flight():
    def __init__(self, airport_departure, airport_arrival, company, day_depature, price, time_departure=None, time_arrival=None) -> None:
        self.airport_departure = airport_departure
        self.airport_arrival = airport_arrival
        self.company = company
        self.day_depature = day_depature
        self.price = price
        self.time_departure = time_departure
        self.time_arrival = time_arrival
    
    
class Trip():
    def __init__(self, sources_codes, destinations_codes, stops_codes, stops_durations, trip_boundaries, trip_max_price) -> None:
        
        # Check codes vs durations
        assert len(stops_codes) == len(stops_durations), "Stops must meet: len(stops_codes) == len(stops_durations)"
        
        # TODO: check codes validity 
        
        # TODO: Select stop_code None for Anything 
        
        # Select trip_boundaries None for whole next month
        if trip_boundaries is None:
            trip_boundaries = (datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(days=30))
        
        
        
        # Create Airport memory (adding is done by getting refs)
        self.airports_memory = Airports_Dict()
        self.load_memory(validity=datetime.timedelta(hours=12))

        
        # Create Trip stops objects
        self.source = Trip_Source(self.airports_memory, sources_codes)  
        self.destination = Trip_Destination(self.airports_memory, destinations_codes) 
        self.stops = [Trip_Stop(self.airports_memory, stop_codes, stop_duration) for stop_codes, stop_duration in zip(stops_codes, stops_durations)]  # Obligatory stops
        
        # Save other trip parameters
        self.trip_boundaries = trip_boundaries
        self.trip_max_price = trip_max_price


    # Search for routes: BSF from Trip_Source --> Trip_Destination
    def searchBSF(self, BSF_depth):
    
        # Outcome -- 2D List of Connections forming valid paths
        valid_paths = []
    
        # Initialize BSF with sources (Airports)
        current_sources = self.source.airports
        current_destinations = []
        
        for i_flight in range(BSF_depth):
            for source in current_sources:
                source.search_Ryanair_cheapDestinations(trip_boundaries, trip_max_price)
    
    
    # Print all found connections
    def debug_print_connections(self):
        print("Found Connections:")
        for airport_code in self.airports_memory.airports_memory:
            airport = self.airports_memory.airports_memory[airport_code]
            for connection in airport.data_destinations:
                dest_airport = connection.airport_arrival
                print(f"\t{airport.code}-->{dest_airport.code}: ")
                for flight in connection.flights:
                    print(f"\t\tCompany: {flight.company}, price: {flight.price}, time dep.: {flight.time_departure}, time arr.: {flight.time_arrival}")


    # Save memory -- whole Airports_Dict
    def save_memory(self):
        filename = self.airports_memory.filename
        with open(filename, 'wb') as file:
            pickle.dump(self.airports_memory, file)
            if DEBUG_BASIC:
                print(f'Object successfully saved to "{filename}"')

    # Load data memory Airports_Dict --- if too old --> ignore
    def load_memory(self, validity):
        filename = self.airports_memory.filename
        
        try:
            with open(filename, 'rb') as file:
                loaded_airports_memory = pickle.load(file)
        except FileNotFoundError:
            if DEBUG_BASIC:
                print("Loading file not found -- ignoring")
            return
            
        # Check data temporal validity
        if loaded_airports_memory.date_created + validity > datetime.datetime.now():
            self.airports_memory = loaded_airports_memory # Rewrite memory
            if DEBUG_BASIC:
                print(f"Data loaded, data last update: {loaded_airports_memory.date_created}")
        else:
            if DEBUG_BASIC:
                print(f"Saved data ({loaded_airports_memory.date_created}) are too old -- ignoring")
        
        
        

        
        
        
############## MAIN ##############
if __name__ == "__main__":
    time_now = datetime.datetime.now()
    time_inMonth = time_now + datetime.timedelta(days=30)
    
    sources_codes = ('PRG', 'BRQ',)  # ('PRG', 'BRQ')
    destinations_codes = ('PRG', 'BRQ')
    stops_codes = [('STN', 'LTN')]
    stops_durations = [(2,4)]
    trip_boundaries = [time_now, time_inMonth]
    trip_max_price = 1000 #TODO: currency !

    trip = Trip(sources_codes, destinations_codes, stops_codes, stops_durations, trip_boundaries, trip_max_price)
    
    # Search for an optimal paths
    BSF_depth = 2
    trip.searchBSF(BSF_depth)
    
    # Save memory of airports in trip
    trip.save_memory()


    # Debug Print all found connections
    if DEBUG_BSF:
        trip.debug_print_connections()
    

