import os, sys, time, dotenv, tomllib, importlib; dotenv.load_dotenv()
from pathlib import Path

import tor.manager
import sites.forum

from database.psql import main    as psql


# Global Variables
EXECUTION_POOL = []
CONFIG_PATH    = "config.toml" # os.getenv("CONFIG_PATH") # Uncomment this line to get config file from .env
INTERVAL       = 5 * 60        # os.getenv("INTERVAL")    # Uncomment this line to get interval from .env
PSQL_URL       = os.getenv( "PSQL_URL" )


#
#   Implementation
#
def execute_pool():
    """
    Executes the scraper pool.
    
    """
    global EXECUTION_POOL
    
    for func in EXECUTION_POOL: 
        func()
    

def read_config() -> dict | None:
    """
    Loads the TOML configuration file. If it doesn't exist, 
    creates a template to modify and exits.
    
    """
    global CONFIG_PATH
    config_file = Path( CONFIG_PATH )
    
    # Config file doesn't exist, create a template and exit.
    if not config_file.exists():
        print(f"[{__name__}] [!] Config file not present. Created a template. Please modify it before next run.")
        
        with open("./templates/template_config.toml", "r") as file: config_file.write_text(file.read(), encoding="utf-8")
        sys.exit(0)

    # Load the config and return it
    with open("config.toml", "rb") as file:
        return tomllib.load( file )
    
    # Yet unknown error. 
    print(f"[{__name__}] [!] Config file could not be loaded.")
    return None
    

def build_scrapers( config : dict, Manager : tor.manager.Manager, ):
    """
    Dynamically imports the forum scraper objects and builds them.
    Will automatically push scraperClass.monitor() into execution pool.
    
    Expected config format:
        
        forum_config = {
            "scraper" : "module.path.to.scraperClass",
            "object"  : "ClassName",   
            "baseurl" : "https://example.com"
        }
    
    Args:
        config  (dict):                the TOML configuration dict.
        manager (tor.manager.Manager): the Tor circuit manager used by the scrapers.
    """
    
    # Load in the forums from config
    for _, forum_config in config["forums"].items():
        scraper_module = importlib.import_module( forum_config["scraper"] )
        scraper_name   = forum_config.get( "object", "scrape" )
        
        scraper        = getattr(scraper_module, scraper_name)
        
        # Create a Forum object.
        _forum_obj = scraper(
            url     = forum_config["baseurl"],
            manager = Manager    
        )
        
        # Above mimics:
        # Breachforums( 
        #    url     = forum_config["baseurl"],
        #    manager = Manager
        #)
        
        # Store objects.
        EXECUTION_POOL.append( _forum_obj.monitor )
    
        
        
#
#   Main entrypoint
#
def main():
    global INTERVAL
    global EXECUTION_POOL
    
    # Initialize 
    config = read_config()
    
    Manager  = tor.manager.Manager() # Ready tor as a proxy
    Forums   = sites.forum.Forums()  # Ready database for scraping forums
    
    build_scrapers( config, Manager )
    
    # Runs the scrapers forever with wanted interval, default to 5 mins.
    while 1:
        execute_pool()
        time.sleep( INTERVAL )
        
        
if __name__ == "__main__":
    
    # Initialize DB
    psql.initialize_db(
        db_url = PSQL_URL,
        tables = {}
    )
    
    main() 