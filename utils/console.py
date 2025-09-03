class Console:
    """
    Handles printing of any parameters or objects.
    """

    @staticmethod
    def print(obj):
        """
        Prints any object to the console in a readable way.
        """
        from pprint import pprint

        pprint(obj)
