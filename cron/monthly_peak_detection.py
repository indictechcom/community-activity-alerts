#!/usr/bin/env python3

import sys
import os
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.notification.notification_manager import NotificationManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'notification.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 80)
    logger.info("Starting monthly notification job for detected peaks")
    logger.info(f"Execution time: {datetime.now().isoformat()}")
    logger.info("=" * 80)
    
    try:
        notification_manager = NotificationManager()
        
        # Check only the last 1 day since this runs immediately after peak detection
        result = notification_manager.process_notifications(days_back=1)
        
        logger.info("Job completed successfully")
        logger.info(f"Total peaks processed: {result['total_peaks']}")
        logger.info(f"Notifications sent: {result['total_sent']}")
        logger.info(f"Notifications failed: {result['total_failed']}")
        logger.info(f"Notifications skipped (already sent): {result['total_skipped']}")
        
        if result['total_failed'] > 0:
            logger.warning(f"{result['total_failed']} notifications failed to send")
        
        return 0
        
    except Exception as e:
        logger.error(f"Critical error during notification job: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
