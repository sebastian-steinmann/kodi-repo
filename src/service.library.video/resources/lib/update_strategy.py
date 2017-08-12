from abc import ABCMeta, abstractmethod

class UpdateStrategy(object):
    """ Abstract interface for update_strategy """
    __metaclass__ = ABCMeta

    """ Abstract class as interface """
    @abstractmethod
    def should_update(self, last_update, movie):
        """
        Takes a movie and returns true or false if it should update
        """
        pass

    @abstractmethod
    def get_label(self):
        """
        Returns the label for the strategy
        """
        pass

class ForceStrategy(UpdateStrategy):
    """ Always returns update """
    def should_update(self, last_update, movie):
        return True

    def get_label(self):
        return "FULL UPDATE"

class IncrementalStrategy(UpdateStrategy):
    """
        Strategy to check if movie has changed and only update then
    """
    def should_update(self, last_update, movie):
        return last_update != movie.get('last_update')
    
    def get_label(self):
        return "INCREMENTAL UPDATE"
