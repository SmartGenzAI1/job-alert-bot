import asyncio
import logging
from typing import List, Tuple

from config import SEND_BATCH_SIZE, SEND_BATCH_SLEEP, logger


async def notify_users(bot, users: List[Tuple[int, str]], jobs: List[Tuple[str, str, str]]):
    """
    Send job notifications to users with proper rate limiting and error handling.
    
    Args:
        bot: Telegram bot instance
        users: List of (user_id, category) tuples
        jobs: List of (title, company, link) tuples
    """
    if not users or not jobs:
        logger.debug("No users or jobs to notify")
        return

    logger.info(f"Sending {len(jobs)} jobs to {len(users)} users")
    
    # Process users in batches to avoid overwhelming the system
    batch_size = min(SEND_BATCH_SIZE, 50)  # Limit batch size for safety
    sent_count = 0
    failed_count = 0
    
    for i in range(0, len(users), batch_size):
        user_batch = users[i:i + batch_size]
        batch_results = await process_user_batch(bot, user_batch, jobs)
        sent_count += batch_results['sent']
        failed_count += batch_results['failed']
        
        # Rate limiting between batches
        if i + batch_size < len(users):
            await asyncio.sleep(SEND_BATCH_SLEEP * 2)  # Slightly longer delay between batches

    logger.info(f"Notification completed: {sent_count} sent, {failed_count} failed")


async def process_user_batch(bot, user_batch: List[Tuple[int, str]], jobs: List[Tuple[str, str, str]]):
    """
    Process a batch of users for job notifications.
    
    Returns:
        dict: {'sent': int, 'failed': int}
    """
    sent_count = 0
    failed_count = 0
    
    for user_id, category in user_batch:
        try:
            # Filter jobs by user's category preference
            user_jobs = [job for job in jobs if should_send_job_to_user(job, category)]
            
            if not user_jobs:
                continue
                
            # Send jobs to this user
            user_sent, user_failed = await send_jobs_to_user(bot, user_id, user_jobs)
            sent_count += user_sent
            failed_count += user_failed
            
        except Exception as e:
            logger.error(f"Error processing user {user_id}: {e}")
            failed_count += 1
            continue
    
    return {'sent': sent_count, 'failed': failed_count}


async def send_jobs_to_user(bot, user_id: int, jobs: List[Tuple[str, str, str]]):
    """
    Send job listings to a specific user.
    
    Returns:
        tuple: (sent_count, failed_count)
    """
    sent_count = 0
    failed_count = 0
    
    for title, company, link in jobs:
        try:
            # Format message with markdown
            message = (
                f"📌 *{title}*\n"
                f"🏢 {company}\n"
                f"🔗 {link}\n\n"
                f"_Sent via Job Alert Bot_"
            )
            
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
            
            sent_count += 1
            
            # Small delay between messages to same user
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.warning(f"Failed to send job to user {user_id}: {e}")
            failed_count += 1
            
            # If user has blocked the bot, stop sending to them
            if "bot was blocked" in str(e).lower() or "user is deactivated" in str(e).lower():
                logger.info(f"User {user_id} has blocked the bot or is deactivated")
                break
    
    return sent_count, failed_count


def should_send_job_to_user(job: Tuple[str, str, str], user_category: str) -> bool:
    """
    Determine if a job should be sent to a user based on their category preference.
    
    Args:
        job: (title, company, link) tuple
        user_category: User's preferred job category
        
    Returns:
        bool: True if job should be sent to user
    """
    # For now, we assume all jobs are relevant to all users
    # In the future, this could be enhanced with job categorization
    return True
