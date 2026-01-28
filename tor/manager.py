import time
from datetime import datetime

from . import handling


class Manager:
    """
    Tor-circuit management wrapper.

    Interface:
        Manager(max_retries=3, incl_countries="", excl_countries="")
            - create a new manager with retry limits and optional Tor exit-node constraints.

        Manager.execute_function(func, *args, **kwargs)
            - execute a function safely with automatic retries.
            - on failure, renews the Tor circuit (optionally using exit-node filters).

    """

    def __init__( self, max_retries : int = 3, incl_countries : str = "", excl_countries : str = "", ):
        self.max_retries    = max_retries
        self.incl_countries = incl_countries 
        self.excl_countries = excl_countries
        
        self.wait_config_change = 5
        
        # TODO: Validate incl and excl with regex


    #
    #   Interface
    #
    def execute_function( self, func,  *args, **kwargs ):
        retry_counter = 0
        while 1:
            try: 
                # Try to run and return Function.
                return func(*args, **kwargs)
            
            except Exception as e:
                printl( f"[!] Ran into an issue." )
                
                # Retries exceeded.
                retry_counter += 1
                if retry_counter == self.max_retries:
                    printl( f"[!!!] Could not fix the issue: {e}" )
                    return None 
                
                self._handle_errors()
                
    #
    #   Implementation
    #
    def _handle_errors( self ):
        # TODO: Add IP change check?
        printl( f"[!] Renewing the tor circuit to try to fix the issue." )
        
        # If no special requirements are set, just reset the ip
        if (self.incl_countries == "") and (self.excl_countries == ""):
            handling.renew_tor_ip()
            time.sleep( self.wait_config_change )
            return
        
        # If special requirements are set, use them in the configuration
        handling.set_exit_nodes(
            country_codes = self.incl_countries or None,
            exclude_codes = self.excl_countries or None
        )
        time.sleep( self.wait_config_change )
        printl( f"[✓] Circuit should be renewed." )


# Helper functions.
def stamp(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def printl( string ): print( f"[{ stamp() }][{ __name__ }]" + string )
