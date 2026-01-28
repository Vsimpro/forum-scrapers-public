"""
 *   Type for all 'Breach' type sites.
"""
from bs4          import BeautifulSoup
from dataclasses  import dataclass

import tor.manager, scraper.browser
from sites.forum  import ForumPost

from database.psql import main as database


#
#   BreachForums object  
#
class Breachsups:
    """
        Represents a cybercrime forum using the Breachforums (by HasanBroker) template.

        Interface:
            Breachforums()
                - new forum object.
                
            Breachforums.monitor()
                - fetch latest posts from the forum. Use this in a loop.
    
    """
    
    def __init__( self, url : str, manager : tor.manager.Manager, proxy : str = "socks5://127.0.0.1:9050" ):
        self.url     : str                 = url     # Base url for the forum.
        self.proxy   : str                 = proxy   # Proxy the scraper is going to use. Should be the Tor proxy the circuit manager is connected to.
        self.manager : tor.manager.Manager = manager # Tor circuit manager. 
        
        self.status   : bool = False   # Whether or not this site is currently being tracked
        self.forum_id : int  = -1
        
        # Try to get the forum_id. If forum doesn't exist, add it.
        try:
            self.forum_id = database.query_database( psql_queries.select_forum_by_id, (f"%{self.url}%",) )[0][0]
        except IndexError:
            database.insert_data( psql_queries.insert_into_forums, ("Breachsups", self.url) )
            self.forum_id = database.query_database( psql_queries.select_forum_by_id, (f"%{self.url}%",) )[0][0] # The forum ID in the database.
    
    
    #
    #   Interface
    #
    def monitor( self ) -> bool:    
        status            = False
        page_html_storage = []
        
        # Get each page of forums:
        interested_pages = [
            self.url + "/index.php?forums/databases.14/",        # Databases
            self.url + "/index.php?forums/stealer-logs.15/",     # Stealer Logs
            self.url + "/index.php?forums/other-leaks.16/",      # Other leaks
            self.url + "/index.php?forums/cracked-accounts.18/", # Cracked Accounts
            self.url + "/index.php?forums/combolists.19/",       # Combolists
            self.url + "/index.php?forums/sellers-place.24/",    # Sellers
            self.url + "/index.php?forums/buyers-place.25/",     # Buyers
        ]
        
        
        # Scrape the HTML
        for page in interested_pages:
            page_html_storage.append(
                self._fetch_page( page )
            )
        
        # -> Parse HTML    
        for page in page_html_storage:
                posts = self._parse_posts( page )
                
                # Store & Log
                self._store_posts(posts)
                self._print_posts(posts)
                
                # Mark status as up
                for _ in posts:
                    status = True
                    continue
        
        # No posts? Assume dead:
        self.status = status        
        return True
    
    
    #
    #   Implementation
    #
    def _parse_posts( self, html : str ):
        
        # Pinned post
        
        # Other posts
        # class="structItem structItem--thread js-inlineModContainer" -> data-author is username
        # -> div with class structItem-title for title
        # -> div with class structItem-startDate for timestamp
        # -> a.href for the link
    
        posts: list = []
        soup: BeautifulSoup = BeautifulSoup(html, "html.parser")

        # Go through thread items
        for item in soup.select("div.structItem.structItem--thread.js-inlineModContainer"):

            # Title + link
            title_div = item.select_one("div.structItem-title a")
            if not title_div:
                continue

            title = self._clean_str(title_div.get_text(strip=True))
            href = title_div.get("href")

            # Timestamp
            time_tag = item.select_one(
                        "div.structItem-minor li.structItem-startDate time"
            )
            if time_tag:
                timestamp = (
                    time_tag.get("datetime")        # preferred
                    or time_tag.get("data-timestamp")
                    or time_tag.get("title")
                    or time_tag.get_text(strip=True)
                )

            posts.append(
                ForumPost(
                    link      = self.url + href if href.startswith("/") else href,
                    title     = title,
                    content   = None,
                    timestamp = timestamp or time_tag,
                    forum_id  = self.forum_id
                )
            )

        return posts
        
        
    
    def _fetch_page( self, url : str ) -> str | None:
        html = self.manager.execute_function( 
            scraper.browser.open,             # function call
            url, self.proxy                   # function arguments
        )
        return html or None

    
    def _store_posts( self, posts: list[ ForumPost ] ):
        for post in posts: 
            database.insert_data(
                psql_queries.insert_into_forum_post,
                ( post.link, post.title, post.content, post.timestamp, self.forum_id )
            )
    
    
    def _print_posts( self, posts: list[ ForumPost ]):
        for post in posts:
            print( f"\n{'-'*43}" + f"\nTitle:\t\t{post.title}" + f"\nLink:\t\t{post.link}" + f"\nTimestamp:\t{post.timestamp}" )    
    
    
    def _clean_str( self, string ): return str(string).strip('\n').strip('  ').strip('\t').replace("\n","") 
    def __str__( self ): return f"{self.url}" 
    

#
#   Required SQL Queries
#
@dataclass(slots = True)
class psql_queries:
    """
    *   Required PSQL queries for the 'BreachForums' class.
    """
    
    #
    #   Selects
    #
    select_forum_by_id = """SELECT id FROM Forums WHERE baseurl LIKE %s ORDER BY id DESC LIMIT 1 ;"""
    """ SELECT id; input (%s = '%url.netloc%');"""
    
    #
    #   Inserts
    #
    insert_into_forums = """
    INSERT INTO Forums (type, baseurl) VALUES (%s, %s);
    """
    """type, baseurl"""
    
    insert_into_forum_post = """
    INSERT INTO ForumPost (
        link, title, content, timestamp, forum_id
    ) VALUES ( %s, %s, %s, %s, %s );
    """
    """ link, title, content, timestamp, forum_id """
