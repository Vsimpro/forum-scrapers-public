"""
    Modified source from: https://scrapingant.com/blog/web-scraping-tor-python
"""
import time

from stem            import *
from stem.connection import *
from stem.control    import *


#
#   Interface
#
def reset_configuration( port : int = 9051 ):
    """
    Reset the Torrc configuration.
    
    Args:
        port (int): Control port of the Tor proxy
    """
    with Controller.from_port( port = port ) as controller:
        controller.authenticate()
        
        controller.reset_conf("ExitNodes")
        controller.reset_conf("StrictNodes")
        controller.reset_conf("ExcludeExitNodes")

        controller.set_conf("CircuitBuildTimeout",      "10")
        controller.set_conf("LearnCircuitBuildTimeout", "1" )


def set_exit_nodes( country_codes : str, exclude_codes : str = "", port = 9051 ) -> bool:
    """
    Renews the Tor exit node to use specific countries. \n
    
    Country codes are ISO 3166-1 alpha-2, e.g. '{us},{de},{nl}'.
    
    Args:
        country_codes (str): Country code selection for Tor exit nodes
        exclude_codes (str): Country code exclusions for Tor exit nodes
        
    Returns:
        bool : Upon success
    """    
    try:
        with Controller.from_port( port = port ) as controller:
            controller.authenticate()
            
            # Set Inclusions and Exclusions for the exit nodes
            controller.set_conf("ExitNodes",        country_codes)
            controller.set_conf("ExcludeExitNodes", exclude_codes)
            
            # Set other required configs 
            controller.set_conf("StrictNodes",              "1" )
            controller.set_conf("CircuitBuildTimeout",      "10")
            controller.set_conf("LearnCircuitBuildTimeout", "1" )

            controller.signal(Signal.NEWNYM)
            time.sleep( controller.get_newnym_wait() )
        
            return True
    
    except stem.connection.UnreadableCookieFile as e:
        print( f"[{__name__}] stem.connection.UnreadableCookieFile: {e}. Do you have permissions for this action? Hint: sudo." )
        return False    
    
    return False


def renew_tor_ip( port : int = 9051 ) -> bool:
    """
    Renews the Tor exit node.
    
    Args:
        port (int): Control port of the Tor proxy
        
    Returns:
        bool : Upon success
    """
    try:
        
        # NEWNYM -> Torcc for new IP
        with Controller.from_port( port = port ) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            
            time.sleep( controller.get_newnym_wait() )
            
        return True    
        
    except stem.connection.UnreadableCookieFile as e:
        print( f"[{__name__}] stem.connection.UnreadableCookieFile: {e}. Do you have permissions for this action? Hint: sudo." )
        return False
    
    # Default to False
    return False
 
            