class Baggage:
    """
    An instance of this class represent a quantity of each of product 
    demanded by client,
    available by depot or
    charged by vehicle    
    """

    def __init__ (self, id=None, qtd=0, weight = None, volumn = None):
        """
        Initialise

        :param id: The id of product
        :param qtd: The quantity of each type of product
        :param weight: Sum of weight of product * qtd, None if is depot
        :param weight: Sum of volumn of product * qtd, None if is depot
        """

        self.id = id
        self.qtd = qtd
        self.weight = weight
        self.volumn = volumn
        self.invisible_qtd = qtd
        
        #verificar
        self.delta_qtd = 0
        


    def __hash__(self):
        return self.id

    def __repr__(self):
        return f"""
        Product Id: {self.id}
        Product qtd: {self.qtd}
        Product Weight: {self.weight}
        """