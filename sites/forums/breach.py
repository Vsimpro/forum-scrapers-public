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
class Breachforums:
    """
        Represents a cybercrime forum using the Breachforums template.

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
            database.insert_data( psql_queries.insert_into_forums, ("Breachforums", self.url) )
            self.forum_id = database.query_database( psql_queries.select_forum_by_id, (f"%{self.url}%",) )[0][0] # The forum ID in the database.
    
    
    #
    #   Interface
    #
    def monitor( self ) -> bool:    
        # Use a scraper to get the front page html.
        html = self._fetch_frontpage()
        
        # Could not fetch site despite best efforts. Mark as inactive.
        if not html:
            self.status = False
            return False
        
        # Get the latest posts of BreachForums
        latest_posts = self._parse_latest( self.url + "//", html )
        
        # Site down?
        if not latest_posts:
            self.status = False
            return False
        
        self._store_posts(latest_posts)
        self._print_posts(latest_posts)
        
        self.status = True        
        return True
    
    
    #
    #   Implementation
    #
    def _parse_latest( self, url, html ):
        posts : list          = []        
        soup  : BeautifulSoup = BeautifulSoup( html, "html.parser" )
        
        # Go through the latest posts
        for item in soup.select("div.lp-item"):

            # Get the title and link to the post from the <a> tag
            a_tag = item.select_one( "a.lp-title" )
            
            title     = self._clean_str( a_tag.text )
            href      = a_tag.get( "href" )
            
            # Filter the spans within title. First one should be the forum post timestamp.
            timestamp = item.select_one("span[title]").get("title")
            
            # TODO: Get content as well!
            posts.append( ForumPost(
                link      = url + href,
                title     = title,
                content   = None,  
                timestamp = timestamp,
                forum_id  = self.forum_id
            ))
        
        return posts
    
    
    def _fetch_frontpage( self ) -> str | None:
        html = self.manager.execute_function( 
            scraper.browser.open,             # function call
            self.url, self.proxy              # function arguments
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
