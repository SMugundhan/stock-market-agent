# Refer day12 utube for logging

import logging

import json

import sys

from datetime import datetime, timezone

from core . config import Config

class StructuredFormatter ( logging . Formatter ) :

    """
    Custom log formatter that outputs JSON instead of plain text.

    logging.Formatter is Python's base class for formatting log records.
    We override the format() method to output JSON instead of text.
    """

    def format(self, record: logging.LogRecord) -> str:
        
        """
        Called automatically by the logging system for every log message.
        record = the log event object containing all information about
        what was logged, where, when, at what level.
        """

        # build the base log entry

        log_entry = {
            "timestamp" : datetime . now ( timezone . utc ) . isoformat (),
            
            "level" : record . levelname,
            # levelName = DEBUG, INFO, WARNING, ERROR,, CRITICAL

            "logger" : record . name,
            # name of the logger created this record eg : price_agent, risk_agent

            "message" : record . getMessage (),
            # returns the formatted log msg string

            "module" : record . module,
            # module name = which python file generated this log record

            "function" : record . funcName,
            # function name = which function generated this log record

            "line" : record . lineno,
            # line number = which line in the file generated this log record

            "version" : Config . APP_VERSION
            }
        
        # adding extra fields attached to this log record
        # this is how we add ticker, req_id, duration, etc. to the log record

        if hasattr ( record, "extra_fields" ) :

            log_entry . update ( record . extra_fields )
            # Update merges the extra dict into the log_entry dict

        # If this log includes an exception, add the exception info to the log entry
        if record . exc_info :

            log_entry [ "exception" ] = self . formatException ( record . exc_info )
            # formatException converts the exception tuple into a string with traceback info

        return json . dumps ( log_entry, ensure_ascii = False )
        # Convert the entire dict into a JSON string for input

def get_logger ( name : str ) -> logging . Logger :

    """
    Creates and returns a configured logger for a given module.

    Usage:
        from core.logger import get_logger
        logger = get_logger("price_agent")
        logger.info("Fetching data", extra={"ticker": "AAPL"})
        """
    
    # create a named logger using heiarchical names like "stock_agent.price_agent" lets you control log lvls
    # for specific parts of the sys independency

    logger = logging . getLogger ( f"stock_agent.{name}" )

    # Only add handlers if this logger doesn't already have them (to avoid duplicate logs)
    if not logger . handlers :

        # Console handler
        console_handler = logging . StreamHandler ( sys . stdout )
        # Writes logs to the terminal / stdout
        # Docker captures stdout automatically

        console_handler . setFormatter ( StructuredFormatter () )
        
        logger . addHandler ( console_handler )


        # File handler

        try :

            import os

            os . makedirs ( "logs", exist_ok = True )

            file_handler = logging . FileHandler ( f"logs/{name}.log", encoding = "utf-8" )

            file_handler . setFormatter ( StructuredFormatter () )

            logger . addHandler ( file_handler )

        except Exception as e :

            # If we can't write to logs/ (e.g. read-only filesystem),
            # just skip the file handler — console logging still works
            pass

        # Set log level from env   --- debug in dev, warning in prod

        log_level = getattr ( logging, "DEBUG", logging . INFO )

        logger . setLevel ( log_level )

        logger . propagate = False
        # propagate=False prevents logs from bubbling up to the root logger
        # and being printed twice

    return logger
    
def log_with_context ( logger : logging . Logger, level : str , message : str, **kwargs ) :
        
        """
            Helper function to log with extra context fields cleanly.

            Instead of:
                logger.info("msg", extra={"extra_fields": {"ticker": "AAPL", ...}})

            You write:
                log_with_context(logger, "info", "msg", ticker="AAPL", ...)
        """

        log_method = getattr ( logger, level . lower () )
        # getattr(logger, "info") → logger.info
        # getattr(logger, "error") → logger.error
        # Lets us call any log level dynamically

        log_method ( message, extra = { "extra_fields" : kwargs } )
        # extra={"extra_fields": kwargs} passes our context to
        # the StructuredFormatter.format() method above



