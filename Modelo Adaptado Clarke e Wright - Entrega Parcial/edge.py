class Edge:
    """
    an instance of this class represents an edge connecting two nodes to viit.

    Only edge connecting node to visit to each other are instantiated.
    We don't need edges connecting depot to nodes and nodes to depot
    """
    def __init__(self, inode, jnode, cost):
        """
        Initialise

        :param inode: The stating node
        :param jnode: The ending node
        :param cost: The length of the path from inode to j node

        :attr saving: The saving value calculated 
        :attr revenue: The revenue of nodes
        :attr revenue_norm: The revenue of nodes normalized
        """

        self.inode = inode
        self.jnode = jnode
        self.cost = cost
        self.revenue = inode.revenue + jnode.revenue
        self.revenue_norm = None
        self.savings = dict()

        #UTILIZADO PARA CUT
        self.cut_savings = dict()
    
    def __repr__(self):
        return f"""
        inode: {self.inode}
        jnode: {self.jnode}
        saving: {self.savings}
        cut_savings: {self.cut_savings}
        -----------------------------------------------
        """