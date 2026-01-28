from dataclasses import dataclass

from database.psql import main as database


@dataclass(slots = True)
class ForumPost:
    link:      str
    title:     str
    content:   str
    timestamp: str
    forum_id:  str


class Forums:
    def __init__( self ):
        self.storage : list = []
        
        # Add required tables for storing the scraped forum data.
        database.create_tables({ 
            "Forums"    : psql_queries.create_forums_table,
            "ForumPost" : psql_queries.create_forumposts_table
        })
    
    def __iter__(self):
        for forum in self.storage:
            yield forum 
        
    
#
#   SQL Queries for Forums
#
class psql_queries:
    
    # Tables
    create_forums_table = """
        CREATE TABLE IF NOT EXISTS Forums (
            id         SERIAL PRIMARY KEY,
            type       TEXT NOT NULL,       -- name of the type (e.g. BreachForums)
            baseurl    TEXT NOT NULL        -- url for the forum
        );
    """

    create_forumposts_table = """
        CREATE EXTENSION IF NOT EXISTS pgcrypto;
        CREATE TABLE IF NOT EXISTS ForumPost (
            id         SERIAL PRIMARY KEY,
            uid        UUID DEFAULT gen_random_uuid(), 
            
            link       TEXT NOT NULL,                   -- URL for the forum post
            title      TEXT NOT NULL,                   -- The title of the forum post
            content    TEXT,                            -- Content from the forum post
            timestamp  TEXT,                            -- Timestamp from the forum post
            
            
            forum_id   INTEGER NOT NULL,                -- 
            created_at BIGINT DEFAULT EXTRACT(EPOCH FROM now())::BIGINT,

            CONSTRAINT fk_forum FOREIGN KEY (forum_id) REFERENCES forums(id)
        );
        ALTER TABLE ForumPost
        ADD CONSTRAINT forumpost_link_unique UNIQUE (link);
        """


    # Selects
    select_forum_id_by_url = """ SELECT id FROM Forums WHERE baseurl LIKE %s ORDER BY id DESC LIMIT 1 ;"""
    """ SELECT id; %s = '%url.netloc%' """

    # Inserts
    insert_into_forums = """INSERT INTO Forums (type, baseurl) VALUES (%s, %s);"""
    """type, baseurl"""
