class Vehicle:
    """
    An instance of this class represent a vehicle available in the depot.
    """

    def __init__(self, id, type, max_weight, max_vol, per_km, max_time, veloc, cost_hour, baggage = None):
        """
        Initialise
        
        :param id: The unique id of the vehicle
        :param type: The type of vehicle
        :param max_weight: The maximum weight of charge on vehicle
        :param max_vol: The maximum volume of charge on vehicle
        :param max_time: The maximum working time a day
        :param veloc: The average speed of a vehicle
        :param baggage: The products loaded in the vechicle
        :param cost_hour: The cost per hour

        :attr total_km: Total traveled distance 
        """

        self.id = id
        self.type = type
        self.max_weight = max_weight
        self.max_vol = max_vol
        self.per_km = per_km
        self.max_time = max_time
        self.veloc = veloc
        self.baggage = baggage
        self.cost_hour = cost_hour

        self.total_km = None 
    
    def __hash__(self):
        return self.id
    
    def __repr__(self):
        return f"Vehicle {self.id}"