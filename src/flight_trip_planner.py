import urllib.request, json 
import datetime
import time # sleep
import random
import pickle # save and load objects
import os


WAIT_MAX_INTERVAL = 0.2

DEBUG_BASIC = True
DEBUG_RYANAIR = False
DEBUG_CONNECTIONS = False
DEBUG_TRIPS = True


# Convert currencies fcn
def currency_convert(code_from, code_to, price_from):

    if DEBUG_BASIC:
        print(f"Requesting conversion: {code_from}-->{code_to}")

    time.sleep(WAIT_MAX_INTERVAL*random.random()) #sleep random time 0..WAIT_MAX_INTERVAL
    with urllib.request.urlopen(f"https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/{code_from.lower()}/{code_to.lower()}.json") as url:
        rate_json = json.load(url)

    rate = rate_json[code_to.lower()]

    price_to = price_from * rate
    return price_to

class Airport():
    def __init__(self, code, memory_ref, name, currency) -> None:
        # Info
        self.code = code
        self.memory_ref = memory_ref

        # More advanced parameters 
        self.currency = currency
        self.name = name 
        
        # Data
        self.cheapDestinations = {'Ryanair': []} # list of codes
        self.data_destinations = []  # Connection objects
        self.data_incommings = []    # Connection objects
        
        # Bools
        self.cheapDestinations_searched = {'Ryanair': False} # For searching all departures
        

        # Searching alg bool
        self.visited = False # Note we can use an airport twice !!, (not used)


    # Get all cheap destinations + flights
    def search_Ryanair_cheapDestinations(self, trip_boundaries, max_price, oneDestination=None):
        # Escape when already done
        if self.cheapDestinations_searched['Ryanair']:
            return
        if oneDestination is None:
            self.cheapDestinations_searched['Ryanair'] = True
        
        #Searching one destination -- does the connection already exist?
        if oneDestination is not None:
            # Find the connection in the departure airport
            oneConnection = None
            for connection in self.data_destinations:
                if oneDestination is connection.airport_arrival:
                    oneConnection = connection
                    break
            
            # This exact connection has been already searched !!
            if (oneConnection is not None) and (oneConnection.cheapDestination_searched['Ryanair']):
                return
        
            # This airport was not searched before
            if oneConnection is None:
                pass 
            
            
       

        # Already searched for chep destinations?
        if not self.cheapDestinations['Ryanair']:
            if DEBUG_BASIC:
                print(f"Getting cheap destinations from {self.code}")
            
            # Get cheap destinations
            max_destinations = 50

            if self.currency == 'EUR':
                max_price_local_currency = round(max_price)
            else:
                max_price_local_currency = round(currency_convert("EUR", self.currency, max_price))

            time.sleep(WAIT_MAX_INTERVAL*random.random()) #sleep random time 0..WAIT_MAX_INTERVAL
            with urllib.request.urlopen(f"https://www.ryanair.com/api/farfnd/3/oneWayFares?&ToUs=AGREED&departureAirportIataCode={self.code}&language=en&limit={max_destinations}&market=en-ie&offset=0&outboundDepartureDateFrom={trip_boundaries[0].strftime('%Y-%m-%d')}&outboundDepartureDateTo={trip_boundaries[1].strftime('%Y-%m-%d')}&priceValueTo={max_price_local_currency}") as url:
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
        if oneDestination is None:
            for connection in self.data_destinations:
                if connection.airport_arrival.code in self.cheapDestinations['Ryanair']:
                    self._search_Ryanair_cheapFlights(connection, trip_boundaries, max_price)
        # Search only for this one Connection
        else:
            #Searching one destination -- does the connection already exist? (again)
            # Find the connection in the departure airport
            oneConnection = None
            for connection in self.data_destinations:
                if oneDestination is connection.airport_arrival:
                    oneConnection = connection
                    break                   
            if oneConnection is not None:
                self._search_Ryanair_cheapFlights(oneConnection, trip_boundaries, max_price)
            # else: No connection --> no flights


            
            



    # Get cheap flights into destination --> FILL its connection
    def _search_Ryanair_cheapFlights(self, connection, trip_boundaries, max_price):
        if connection.cheapDestination_searched['Ryanair']:
            return
        else:
            connection.cheapDestination_searched['Ryanair'] = True
            
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
                time.sleep(WAIT_MAX_INTERVAL*random.random()) #sleep random time 0..WAIT_MAX_INTERVAL
                with urllib.request.urlopen(f"https://www.ryanair.com/api/farfnd/3/oneWayFares/{source.code}/{dest.code}/cheapestPerDay?ToUs=AGREED&market=en-gb&outboundMonthOfDate={year:4}-{month:02}-01") as url:
                    data_month = json.load(url)
                # TODO: Exception
                
                # Process the monthly data
                N_days = len(data_month['outbound']['fares'])
                if N_days == 0:
                    return

                # Convert all prices to EUR
                currency_rate = currency_convert(self.currency, "EUR", 1)
                
                prices = []
                departureDates = []
                arrivalDates = []
                for i in range(N_days):
                    if not data_month['outbound']['fares'][i]['unavailable']:
                        departureDate_str = data_month['outbound']['fares'][i]['departureDate']
                        arrivalDate_str = data_month['outbound']['fares'][i]['arrivalDate']
                        price = currency_rate * data_month['outbound']['fares'][i]['price']['value'] 
                        
                        prices.append(price)
                        departureDates.append(datetime.datetime.strptime(departureDate_str, '%Y-%m-%dT%H:%M:%S'))
                        arrivalDates.append(datetime.datetime.strptime(arrivalDate_str, '%Y-%m-%dT%H:%M:%S') )
                        
                    
                # Save all OK fights in this connection
                for price, departureDate, arrivalDate in zip(prices, departureDates, arrivalDates):
                    # if price <= max_price:  # Do this in searching --> save all data !
                    # Max dates can be outside the boundaries --> save all data !
                    connection.add_flight('Ryanair', departureDate, price, departureDate, arrivalDate)
            


# Dict Memory of all used airports
class Airports_Dict():
    def __init__(self) -> None:
        self.airports_memory = {} # Dict of used Airports

        # For saving and loading obtained data
        self.date_created = datetime.datetime.now()
        self.filename = "src/saved_data/airports_memory.pkl"

        if DEBUG_BASIC:
            print(f"Getting Airports JSON")

        # Load currencies 
        time.sleep(WAIT_MAX_INTERVAL*random.random()) #sleep random time 0..WAIT_MAX_INTERVAL
        with urllib.request.urlopen(f"https://www.ryanair.com/api/booking/v4/en-gb/res/stations") as url:
            airports_json = json.load(url)
        airports_countries = {airport : airports_json[airport]['country'] for airport in airports_json} # Dict of airport:country
        self.name_memory = {airport : airports_json[airport]['name'] for airport in airports_json} # Dict of airport:name

        if DEBUG_BASIC:
            print(f"Getting Countries JSON")

        time.sleep(WAIT_MAX_INTERVAL*random.random()) #sleep random time 0..WAIT_MAX_INTERVAL
        with urllib.request.urlopen(f"https://www.ryanair.com/api/views/locate/3/aggregate/all/en") as url:
            countries_json = json.load(url)
        countries_currencies = {country_line['code'] : country_line['currency'] for country_line in countries_json['countries']}

        self.currencies_memory = {} # Dict of Airport Code : Currency
        for airport, country in airports_countries.items():
            if country.lower() in countries_currencies:
                self.currencies_memory[airport] = countries_currencies[country.lower()]
            else:
                self.currencies_memory[airport] = 'EUR' # Country not found --> Assign 'EUR' 


        
    def get_ref(self, code):
        if code not in self.airports_memory:
            self.airports_memory[code] = Airport(code, self, self.name_memory[code], self.currencies_memory[code])

        return self.airports_memory[code]
    
    def isSaved(self, code):
        return code in self.airports_memory
            
    
      
      
# Nodes sets of searching algorithm (Each can include more airports), (Transfers then can include only one airport)
class Trip_Stop():
    def __init__(self, memory, codes, duration) -> None:
        self.duration = duration # Time interval (eg. 2-4 days)
        self.airports = [memory.get_ref(code) for code in codes]

        # Searching alg bool
        self.visited = False
        
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
        
        # Bools
        self.cheapDestination_searched = {'Ryanair': False} # For searching one departure
        
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
    def __init__(self, sources_codes, destinations_codes, stops_codes, stops_durations, trip_boundaries, trip_max_price, transfer_duration, trip_max_transfers) -> None:
        
        # Check codes vs durations
        assert len(stops_codes) == len(stops_durations), "Stops must meet: len(stops_codes) == len(stops_durations)"
        
        # TODO: check codes validity 
        
        # TODO: Select stop_code None for Anything 
        
        # Select trip_boundaries None for whole next month
        if trip_boundaries is None:
            trip_boundaries = (datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(days=30))
        
        
        
        # Create Airport memory (adding is done by getting refs)
        self.airports_memory = Airports_Dict()
        self.load_memory(validity=datetime.timedelta(hours=24))

        
        # Create Trip stops objects
        self.source = Trip_Source(self.airports_memory, sources_codes)  
        self.destination = Trip_Destination(self.airports_memory, destinations_codes) 
        self.stops = [Trip_Stop(self.airports_memory, stop_codes, stop_duration) for stop_codes, stop_duration in zip(stops_codes, stops_durations)]  # Obligatory stops
        
        # Save other trip parameters
        self.trip_boundaries = trip_boundaries
        self.trip_max_price = trip_max_price
        self.transfer_duration = transfer_duration
        self.trip_max_transfers = trip_max_transfers


    # Search for routes: DSF from Trip_Source --> Trip_Destination
    def searchDSF(self, DSF_maxdepth):

        # Outcome -- 2D List of Connections forming valid paths
        valid_paths = []


        # DSF recursionfunction
        act_path = []
        def DSF_recursion(current_source, DSF_depth, current_time, current_price, current_transfersDone):
            
            current_transfersDone += 1

            # Note: an airport can be used more times --> no mark of visited node --> track actual path of flights
            # Check this Airport -- Final Destination !
            if (current_source in self.destination.airports) and (DSF_depth > 0):
                # All Stops travelled?
                if False not in [stop.visited for stop in self.stops]: 
                    valid_paths.append(act_path.copy())
                return
            # Max depth reached  --> stop
            elif DSF_depth >= DSF_maxdepth: # Note: 0 --> No flights searched
                return
            # Price never goes under 14EUR !!
            elif current_price + 14 > self.trip_max_price:
                return
            
            # Time boundaries of this Airport flights
            this_airport_stop = None
            current_boundaries = [current_time + self.transfer_duration[0], current_time + self.transfer_duration[1]]  # Preset transfer boundaries
            # Check this Airport -- source?
            if DSF_depth == 0:
                current_boundaries = self.trip_boundaries 
                current_transfersDone = 0
            else:
                # Check this Airport -- Stop? (unvisited? -- otherwise treat as transfer)
                for stop in self.stops:
                    if (current_source in stop.airports) and (not stop.visited):
                        this_airport_stop = stop
                        this_airport_stop.visited = True
                        current_boundaries = [current_time + this_airport_stop.duration[0], current_time + this_airport_stop.duration[1]]
                        current_transfersDone = 0
                        break
            
            
            # Check if there has already been used max num of transfers between each source-stops-destination
            if current_transfersDone > self.trip_max_transfers:
                # Note: this_airport_stop.visited cannot be raised here
                return


            # Use each possible Airport (if I'm currently at Stop)
            if this_airport_stop is not None:
                current_source_airports = this_airport_stop.airports # Fill all airports from this Stop
            else:
                current_source_airports = [current_source] # Fill the current airport
                
            for current_source_airport in current_source_airports:    
                
                # Update Flights
                if current_transfersDone == self.trip_max_transfers:
                    # Last transfer can be used --> update flights only to to Stop/Destination
                    for stop in self.stops:
                        if stop.visited:
                            continue
                        for stop_airport in stop.airports:
                            current_source_airport.search_Ryanair_cheapDestinations(self.trip_boundaries, self.trip_max_price  * 2/4, oneDestination=stop_airport) 
                    for dest_airport in self.destination.airports:
                        current_source_airport.search_Ryanair_cheapDestinations(self.trip_boundaries, self.trip_max_price  * 2/4, oneDestination=dest_airport) 
                        

                else:
                    # All return passed --> update all possible flights from here
                    current_source_airport.search_Ryanair_cheapDestinations(self.trip_boundaries, self.trip_max_price  * 2/4)
                            
                # Use each possible destination
                for connection in current_source_airport.data_destinations:
                    current_dest = connection.airport_arrival

                    # Use each possible flight
                    for flight in connection.flights:
                        
                        # Check flight constraints (depth- above, price, time) 
                        if (current_price + flight.price < self.trip_max_price) and (current_boundaries[0] < flight.time_departure < current_boundaries[1]): 
                            act_path.append(flight)
                            DSF_recursion(current_dest, DSF_depth+1, flight.time_arrival, current_price + flight.price, current_transfersDone) # TODO: start also at other airports in the Stop !!!
                            act_path.pop()
            
            
            # When leaving this stop -- tick unvisited !
            if this_airport_stop is not None:
                this_airport_stop.visited = False
        

        
            
    
        # Initialize DSF with sources (Airports)
        sources = self.source.airports
        for source in sources:
            DSF_recursion(source, DSF_depth=0, current_time=self.trip_boundaries[0], current_price=0, current_transfersDone=0)
            
            
        return valid_paths

    
    
    
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

    # Print all valid paths
    def print_valid_paths(self, valid_paths):
        print("Valid paths:")

        for path in valid_paths:
            print(f"\t{path[0].airport_departure.code}", end="")
            last_arrival = path[0].airport_departure.code
            for flight in path:
                if last_arrival != flight.airport_departure.code:
                    # Leave stop from different airport
                    print(f"--{flight.airport_departure.code}", end='')
                    
                print(f"--({flight.time_departure}, {flight.price:.2f}EUR)-->{flight.airport_arrival.code}", end='')
                last_arrival = flight.airport_arrival.code
            print("")



    # Save memory -- whole Airports_Dict
    def save_memory(self):
        filename = self.airports_memory.filename
        
        # Folder for data saving nonexistent
        if not os.path.isdir("./src/saved_data"):
            os.mkdir("./src/saved_data")
            
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
        except:
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
    
    sources_codes = ('PRG', 'BRQ', 'PED', 'OSR')  # ('PRG', 'BRQ')
    destinations_codes = ('PRG', 'BRQ', 'PED', 'OSR')
    stops_codes = [('FAO', 'LIS', 'OPO')] # [('STN', 'LTN', 'LGW')]
    stops_durations = [(datetime.timedelta(days=2),datetime.timedelta(days=6))]
    # trip_boundaries = [time_now, time_inMonth]
    trip_boundaries = [datetime.datetime(2024,2,1), datetime.datetime(2024,2,29)]
    trip_max_price = 80 # Currency: "EUR"
    transfer_duration = (datetime.timedelta(hours=1),datetime.timedelta(hours=24))
    trip_max_transfers = 1 # Max number of transfers between each stop (or source/destination)

    trip = Trip(sources_codes, destinations_codes, stops_codes, stops_durations, trip_boundaries, trip_max_price, transfer_duration, trip_max_transfers)
    
    # Search for an optimal paths
    DSF_maxdepth = 20 # Note: 0 --> No flights searched # Note2: trip_max_transfers more advanced !! (delete this in future?)
    valid_paths = trip.searchDSF(DSF_maxdepth) 
    
    # Save memory of airports in trip
    trip.save_memory()


    # Debug Print all found connections
    if DEBUG_CONNECTIONS:
        trip.debug_print_connections()


    # Debug Print all found trips
    if DEBUG_TRIPS:
        trip.print_valid_paths(valid_paths)

    pass
    

