from math import prod


class Type_product:
    """
    An instance of this class represent a type of product to be delivered to nodes
    """
    
    def __init__ (self, id, prod_hour, weight, volumn, price):
        """
        Initialise

        :param id: The unique id of the type of product
        :param prod_hour: Quantity to be produced per hour by depot
        :param weight: The weight of product
        :param volumn: The volumn of product
        """

        self.id = id #str or int - VERIFICAR = ALINHAR COM excel 'CLIENT'
        self.prod_hour = prod_hour
        self.weight = weight
        self.volumn = volumn
        self.price = price