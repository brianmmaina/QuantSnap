#!/usr/bin/env python3
"""
Database population script for QuantSnap
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.infrastructure.data_pipeline import DataPipeline, init_database
from src.core.universe import get_universe
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_database():
    """Populate database with initial stock data"""
    try:
        logger.info("Starting database population...")
        
        # Initialize database
        init_database()
        
        # Initialize pipeline
        pipeline = DataPipeline()
        
        # Process popular stocks first (smaller dataset for testing)
        logger.info("Processing popular stocks...")
        pipeline.process_universe('popular_stocks')
        
        logger.info("Processing S&P 500...")
        pipeline.process_universe('sp500')
        
        logger.info("Processing top ETFs...")
        pipeline.process_universe('top_etfs')
        
        logger.info("Processing world top stocks...")
        pipeline.process_universe('world_top_stocks')
        
        logger.info("Database population completed successfully!")
        
        # Generate quality reports
        for universe in ['popular_stocks', 'sp500', 'top_etfs', 'world_top_stocks']:
            try:
                report = pipeline.get_data_quality_report(universe)
                logger.info(f"Quality report for {universe}: {report}")
            except Exception as e:
                logger.warning(f"Could not generate report for {universe}: {e}")
        
    except Exception as e:
        logger.error(f"Database population failed: {e}")
        raise

if __name__ == "__main__":
    populate_database()
