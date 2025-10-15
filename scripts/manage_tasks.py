#!/usr/bin/env python3
"""
CLI tool for managing Celery tasks.
"""
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.celery_app import celery_app
from backend.tasks import (
    update_vulnerabilities_task,
    clean_cache_task,
    update_stats_cache_task,
    test_task,
)


def trigger_update():
    """Trigger vulnerability update task."""
    print("🚀 Triggering vulnerability update...")
    task = update_vulnerabilities_task.delay()
    print(f"✓ Task started with ID: {task.id}")
    print(f"  This may take 10-30 minutes.")
    print(f"  Check status with: python scripts/manage_tasks.py status {task.id}")
    return task.id


def trigger_cache_cleanup():
    """Trigger cache cleanup task."""
    print("🧹 Triggering cache cleanup...")
    task = clean_cache_task.delay()
    print(f"✓ Task started with ID: {task.id}")
    return task.id


def trigger_stats_update():
    """Trigger statistics update task."""
    print("📊 Triggering statistics update...")
    task = update_stats_cache_task.delay()
    print(f"✓ Task started with ID: {task.id}")
    return task.id


def test_celery():
    """Test Celery connection."""
    print("🧪 Testing Celery connection...")
    task = test_task.delay("Hello from CLI!")
    print(f"✓ Test task started with ID: {task.id}")
    
    # Wait for result
    print("  Waiting for result...")
    try:
        result = task.get(timeout=10)
        print(f"✓ Test successful!")
        print(f"  Result: {result}")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def check_status(task_id):
    """Check status of a task."""
    print(f"📋 Checking status of task: {task_id}")
    task_result = celery_app.AsyncResult(task_id)
    
    print(f"  Status: {task_result.status}")
    
    if task_result.successful():
        print(f"  ✓ Task completed successfully!")
        print(f"  Result: {task_result.result}")
    elif task_result.failed():
        print(f"  ✗ Task failed!")
        print(f"  Error: {task_result.info}")
    elif task_result.status == "PENDING":
        print(f"  ⏳ Task is pending...")
    elif task_result.status == "STARTED":
        print(f"  ⚙️  Task is running...")
    
    return task_result.status


def list_workers():
    """List active Celery workers."""
    print("👷 Checking Celery workers...")
    
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if not active_workers:
            print("  ✗ No workers are running!")
            print("  Start a worker with: celery -A backend.celery_app worker --loglevel=info --pool=solo")
            return False
        
        print(f"  ✓ Found {len(active_workers)} worker(s):")
        for worker_name, tasks in active_workers.items():
            print(f"    - {worker_name}: {len(tasks)} active task(s)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to connect to workers: {e}")
        return False


def list_scheduled():
    """List scheduled tasks."""
    print("📅 Scheduled tasks:")
    
    schedule = celery_app.conf.beat_schedule
    
    for name, config in schedule.items():
        print(f"\n  {name}:")
        print(f"    Task: {config['task']}")
        print(f"    Schedule: {config['schedule']}")


def monitor_task(task_id):
    """Monitor a task until completion."""
    print(f"👀 Monitoring task: {task_id}")
    print("  Press Ctrl+C to stop monitoring (task will continue running)")
    
    task_result = celery_app.AsyncResult(task_id)
    
    try:
        while not task_result.ready():
            status = task_result.status
            print(f"  Status: {status}", end="\r")
            time.sleep(2)
        
        print("\n")
        if task_result.successful():
            print("  ✓ Task completed successfully!")
            print(f"  Result: {task_result.result}")
        else:
            print("  ✗ Task failed!")
            print(f"  Error: {task_result.info}")
            
    except KeyboardInterrupt:
        print("\n  Stopped monitoring (task is still running)")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("OpenThreat Task Manager")
        print("\nUsage:")
        print("  python scripts/manage_tasks.py <command> [args]")
        print("\nCommands:")
        print("  update          - Trigger vulnerability update")
        print("  clean           - Trigger cache cleanup")
        print("  stats           - Trigger statistics update")
        print("  test            - Test Celery connection")
        print("  status <id>     - Check task status")
        print("  monitor <id>    - Monitor task until completion")
        print("  workers         - List active workers")
        print("  scheduled       - List scheduled tasks")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "update":
        trigger_update()
    elif command == "clean":
        trigger_cache_cleanup()
    elif command == "stats":
        trigger_stats_update()
    elif command == "test":
        success = test_celery()
        sys.exit(0 if success else 1)
    elif command == "status":
        if len(sys.argv) < 3:
            print("Error: Task ID required")
            print("Usage: python scripts/manage_tasks.py status <task_id>")
            sys.exit(1)
        check_status(sys.argv[2])
    elif command == "monitor":
        if len(sys.argv) < 3:
            print("Error: Task ID required")
            print("Usage: python scripts/manage_tasks.py monitor <task_id>")
            sys.exit(1)
        monitor_task(sys.argv[2])
    elif command == "workers":
        success = list_workers()
        sys.exit(0 if success else 1)
    elif command == "scheduled":
        list_scheduled()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
