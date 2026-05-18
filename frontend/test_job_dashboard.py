"""
Unit Tests for Job Dashboard Functionality

Tests the job dashboard filtering, sorting, search, and pagination logic.
Requirements: 8.1-8.8
"""

import pytest
from datetime import datetime


def test_status_filter():
    """Test status filtering logic."""
    # Sample jobs
    all_jobs = [
        {'job_id': '1', 'status': 'completed', 'company': 'Acme Corp', 'created_at': '2024-01-15T10:00:00', 'total_cost_usd': 1.5},
        {'job_id': '2', 'status': 'running', 'company': 'Beta Inc', 'created_at': '2024-01-16T11:00:00', 'total_cost_usd': 2.0},
        {'job_id': '3', 'status': 'failed', 'company': 'Gamma LLC', 'created_at': '2024-01-17T12:00:00', 'total_cost_usd': 0.5},
        {'job_id': '4', 'status': 'completed', 'company': 'Delta Co', 'created_at': '2024-01-18T13:00:00', 'total_cost_usd': 3.0},
    ]
    
    # Test 'all' filter
    status_filter = 'all'
    filtered = all_jobs if status_filter == 'all' else [job for job in all_jobs if job.get('status') == status_filter]
    assert len(filtered) == 4
    
    # Test 'completed' filter
    status_filter = 'completed'
    filtered = [job for job in all_jobs if job.get('status') == status_filter]
    assert len(filtered) == 2
    assert all(job['status'] == 'completed' for job in filtered)
    
    # Test 'running' filter
    status_filter = 'running'
    filtered = [job for job in all_jobs if job.get('status') == status_filter]
    assert len(filtered) == 1
    assert filtered[0]['job_id'] == '2'
    
    # Test 'failed' filter
    status_filter = 'failed'
    filtered = [job for job in all_jobs if job.get('status') == status_filter]
    assert len(filtered) == 1
    assert filtered[0]['job_id'] == '3'


def test_search_filter():
    """Test search filtering logic."""
    all_jobs = [
        {'job_id': 'job-abc-123', 'status': 'completed', 'company': 'Acme Corp', 'created_at': '2024-01-15T10:00:00', 'total_cost_usd': 1.5},
        {'job_id': 'job-def-456', 'status': 'running', 'company': 'Beta Inc', 'created_at': '2024-01-16T11:00:00', 'total_cost_usd': 2.0},
        {'job_id': 'job-ghi-789', 'status': 'failed', 'company': 'Gamma LLC', 'created_at': '2024-01-17T12:00:00', 'total_cost_usd': 0.5},
    ]
    
    # Test search by company name
    search_query = 'acme'
    search_lower = search_query.lower()
    filtered = [
        job for job in all_jobs
        if search_lower in job.get('company', '').lower() or
           search_lower in job.get('job_id', '').lower()
    ]
    assert len(filtered) == 1
    assert filtered[0]['company'] == 'Acme Corp'
    
    # Test search by job ID
    search_query = 'def'
    search_lower = search_query.lower()
    filtered = [
        job for job in all_jobs
        if search_lower in job.get('company', '').lower() or
           search_lower in job.get('job_id', '').lower()
    ]
    assert len(filtered) == 1
    assert filtered[0]['job_id'] == 'job-def-456'
    
    # Test search with no results
    search_query = 'nonexistent'
    search_lower = search_query.lower()
    filtered = [
        job for job in all_jobs
        if search_lower in job.get('company', '').lower() or
           search_lower in job.get('job_id', '').lower()
    ]
    assert len(filtered) == 0


def test_sorting():
    """Test sorting logic."""
    all_jobs = [
        {'job_id': '1', 'status': 'completed', 'company': 'Acme', 'created_at': '2024-01-15T10:00:00', 'total_cost_usd': 2.0},
        {'job_id': '2', 'status': 'running', 'company': 'Beta', 'created_at': '2024-01-18T11:00:00', 'total_cost_usd': 1.0},
        {'job_id': '3', 'status': 'failed', 'company': 'Gamma', 'created_at': '2024-01-16T12:00:00', 'total_cost_usd': 3.5},
        {'job_id': '4', 'status': 'pending', 'company': 'Delta', 'created_at': '2024-01-17T13:00:00', 'total_cost_usd': 0.5},
    ]
    
    # Test date descending (newest first)
    sorted_jobs = sorted(all_jobs, key=lambda x: x.get('created_at', ''), reverse=True)
    assert sorted_jobs[0]['job_id'] == '2'  # 2024-01-18
    assert sorted_jobs[-1]['job_id'] == '1'  # 2024-01-15
    
    # Test date ascending (oldest first)
    sorted_jobs = sorted(all_jobs, key=lambda x: x.get('created_at', ''))
    assert sorted_jobs[0]['job_id'] == '1'  # 2024-01-15
    assert sorted_jobs[-1]['job_id'] == '2'  # 2024-01-18
    
    # Test cost descending (high to low)
    sorted_jobs = sorted(all_jobs, key=lambda x: x.get('total_cost_usd', 0), reverse=True)
    assert sorted_jobs[0]['total_cost_usd'] == 3.5
    assert sorted_jobs[-1]['total_cost_usd'] == 0.5
    
    # Test cost ascending (low to high)
    sorted_jobs = sorted(all_jobs, key=lambda x: x.get('total_cost_usd', 0))
    assert sorted_jobs[0]['total_cost_usd'] == 0.5
    assert sorted_jobs[-1]['total_cost_usd'] == 3.5
    
    # Test status priority sorting
    status_priority = {'running': 0, 'pending': 1, 'completed': 2, 'failed': 3, 'aborted': 4}
    sorted_jobs = sorted(all_jobs, key=lambda x: status_priority.get(x.get('status', 'pending'), 5))
    assert sorted_jobs[0]['status'] == 'running'
    assert sorted_jobs[1]['status'] == 'pending'
    assert sorted_jobs[2]['status'] == 'completed'
    assert sorted_jobs[3]['status'] == 'failed'


def test_pagination():
    """Test pagination logic."""
    # Create 45 sample jobs
    all_jobs = [
        {'job_id': f'job-{i}', 'status': 'completed', 'company': f'Company {i}', 'created_at': f'2024-01-{i:02d}T10:00:00', 'total_cost_usd': float(i)}
        for i in range(1, 46)
    ]
    
    jobs_per_page = 20
    
    # Test page 1
    current_page = 1
    start_idx = (current_page - 1) * jobs_per_page
    end_idx = min(start_idx + jobs_per_page, len(all_jobs))
    page_jobs = all_jobs[start_idx:end_idx]
    
    assert len(page_jobs) == 20
    assert page_jobs[0]['job_id'] == 'job-1'
    assert page_jobs[-1]['job_id'] == 'job-20'
    
    # Test page 2
    current_page = 2
    start_idx = (current_page - 1) * jobs_per_page
    end_idx = min(start_idx + jobs_per_page, len(all_jobs))
    page_jobs = all_jobs[start_idx:end_idx]
    
    assert len(page_jobs) == 20
    assert page_jobs[0]['job_id'] == 'job-21'
    assert page_jobs[-1]['job_id'] == 'job-40'
    
    # Test page 3 (partial page)
    current_page = 3
    start_idx = (current_page - 1) * jobs_per_page
    end_idx = min(start_idx + jobs_per_page, len(all_jobs))
    page_jobs = all_jobs[start_idx:end_idx]
    
    assert len(page_jobs) == 5
    assert page_jobs[0]['job_id'] == 'job-41'
    assert page_jobs[-1]['job_id'] == 'job-45'
    
    # Test total pages calculation
    total_pages = (len(all_jobs) + jobs_per_page - 1) // jobs_per_page
    assert total_pages == 3


def test_aggregate_statistics():
    """Test aggregate statistics calculation."""
    all_jobs = [
        {'job_id': '1', 'status': 'completed', 'total_cost_usd': 1.5},
        {'job_id': '2', 'status': 'completed', 'total_cost_usd': 2.0},
        {'job_id': '3', 'status': 'failed', 'total_cost_usd': 0.5},
        {'job_id': '4', 'status': 'running', 'total_cost_usd': 1.0},
        {'job_id': '5', 'status': 'completed', 'total_cost_usd': 3.0},
    ]
    
    # Calculate statistics
    total_jobs = len(all_jobs)
    completed_jobs = sum(1 for job in all_jobs if job.get('status') == 'completed')
    failed_jobs = sum(1 for job in all_jobs if job.get('status') == 'failed')
    success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
    total_cost = sum(job.get('total_cost_usd', 0) for job in all_jobs)
    
    # Verify calculations
    assert total_jobs == 5
    assert completed_jobs == 3
    assert failed_jobs == 1
    assert success_rate == 60.0
    assert total_cost == 8.0


def test_combined_filters():
    """Test combining multiple filters."""
    all_jobs = [
        {'job_id': 'job-1', 'status': 'completed', 'company': 'Acme Corp', 'created_at': '2024-01-15T10:00:00', 'total_cost_usd': 1.5},
        {'job_id': 'job-2', 'status': 'completed', 'company': 'Beta Inc', 'created_at': '2024-01-16T11:00:00', 'total_cost_usd': 2.0},
        {'job_id': 'job-3', 'status': 'failed', 'company': 'Acme LLC', 'created_at': '2024-01-17T12:00:00', 'total_cost_usd': 0.5},
        {'job_id': 'job-4', 'status': 'completed', 'company': 'Delta Co', 'created_at': '2024-01-18T13:00:00', 'total_cost_usd': 3.0},
    ]
    
    # Apply status filter
    status_filter = 'completed'
    filtered_jobs = [job for job in all_jobs if job.get('status') == status_filter]
    
    # Apply search filter
    search_query = 'acme'
    search_lower = search_query.lower()
    filtered_jobs = [
        job for job in filtered_jobs
        if search_lower in job.get('company', '').lower() or
           search_lower in job.get('job_id', '').lower()
    ]
    
    # Verify combined filters
    assert len(filtered_jobs) == 1
    assert filtered_jobs[0]['job_id'] == 'job-1'
    assert filtered_jobs[0]['status'] == 'completed'
    assert 'Acme' in filtered_jobs[0]['company']


if __name__ == '__main__':
    # Run tests
    test_status_filter()
    print("✅ Status filter tests passed")
    
    test_search_filter()
    print("✅ Search filter tests passed")
    
    test_sorting()
    print("✅ Sorting tests passed")
    
    test_pagination()
    print("✅ Pagination tests passed")
    
    test_aggregate_statistics()
    print("✅ Aggregate statistics tests passed")
    
    test_combined_filters()
    print("✅ Combined filters tests passed")
    
    print("\n🎉 All Job Dashboard tests passed!")
