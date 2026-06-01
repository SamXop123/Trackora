"""Utility for grouping consecutive application sessions."""

from __future__ import annotations
from trackora.models.dashboard import TimelineSession

def merge_consecutive_sessions(
    sessions: list[TimelineSession],
    descending: bool = False
) -> list[TimelineSession]:
    """
    Merge chronologically consecutive sessions belonging to the same application.
    Consecutive sessions are combined into a single logical session:
    - Summed duration
    - Earliest start_time as start
    - Latest end_time as end
    - Empty/cleared window title (since multiple window titles are merged)
    """
    if not sessions:
        return []

    # Sort ascending for consistent merging forward in time
    sorted_sessions = sorted(sessions, key=lambda s: s.start_time)
    
    merged: list[TimelineSession] = []
    current_group: list[TimelineSession] = []
    
    for s in sorted_sessions:
        if not current_group:
            current_group.append(s)
        elif s.app_name == current_group[0].app_name:
            current_group.append(s)
        else:
            merged.append(_merge_group(current_group))
            current_group = [s]
            
    if current_group:
        merged.append(_merge_group(current_group))
        
    if descending:
        merged.reverse()
        
    return merged

def _merge_group(group: list[TimelineSession]) -> TimelineSession:
    if len(group) == 1:
        return group[0]
        
    total_duration = sum(s.duration_seconds for s in group)
    earliest_start = group[0].start_time
    latest_end = group[-1].end_time
    
    return TimelineSession(
        app_name=group[0].app_name,
        window_title="",
        start_time=earliest_start,
        end_time=latest_end,
        duration_seconds=total_duration,
    )
