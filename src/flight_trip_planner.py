import urllib.request, json 
import datetime



class Airport():
    def __init__(self, code) -> None:
        self.code = code
        # self.name = None # Name of the airport
        self.data_destinations = []  # Connection objects
        self.data_incommings = []    # Connection objects
        self.destination_searched = False


    def search_Ryanair_cheapDestinations(self, trip_boundraries, max_price):
        self.destination_searched = True
        
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
        
class Airport_Stop(Airport):
    def __init__(self, code, duration) -> None:
        super().__init__(code)
        self.duration = duration # Time interval (eg. 2-4 days)


# Represents connection == all flights: airport_departure ---> airport_arrival
# A Connection can be COMPLETE (== all info included) or NOT (then other parameters can be set later)
class Connection():
    def __init__(self, airport_departure, airport_arrival, times_departure=[], times_arrival=[], prices=[]) -> None:
        assert len(times_departure) == len(times_arrival) == len(prices), "Parameters must meet: len(times_departure) == len(times_arrival) == len(prices)"
        
        self.airport_departure = airport_departure  # Airport object
        self.airport_arrival = airport_arrival      # Airport object
        self.times_departure = times_departure
        self.times_arrival = times_arrival
        self.prices = prices
    
    # Check emptiness of the Flight
    def isEmpty(self):
        return not self.time_departure or not self.time_arrival or not self.price
    
    def add_flight(self, time_departure, time_arrival, price):
        self.times_departure.append(time_departure)
        self.times_arrival.append(time_arrival)
        self.prices.append(price)
    
    
class Trip():
    def __init__(self, source_code, destination_code, stops_codes, stops_durations, trip_boundraries, max_price) -> None:
        
        # Check codes vs durations
        assert len(stops_codes) == len(stops_durations), "Stops must meet: len(stops_codes) == len(stops_durations)"
        
        # TODO: check codes validity 
        
        # TODO: Select stop_code None for Anything 
        
        # TODO: Select trip_boundraries None for whole next month
        
        
        # Create Airports objects
        self.source = Airport(source_code)  # Airport object
        self.destination = Airport(destination_code)  # Airport object
        self.stops = [Airport_Stop(stop_code, stop_duration) for stop_code, stop_duration in zip(stops_codes, stops_durations)]  # Obligatory stops, # Airport objects
        
        # Save other trip parameters
        self.trip_boundraries = trip_boundraries
        self.max_price = max_price

        
        
        
        
        
  
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
    
    source_code = 'PRG'
    destination_code = 'PRG'
    stops_codes = ['STN']
    stops_durations = [(2,4)]
    trip_boundraries = [time_now, time_inMonth]
    max_price = 1000 #TODO: currency !

    trip = Trip(source_code, destination_code, stops_codes, stops_durations, trip_boundraries, max_price)
    
    # TODO: search flights
    trip.source.search_Ryanair_cheapDestinations(trip.trip_boundraries, trip.max_price)


