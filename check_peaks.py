#!/usr/bin/env python3

import pymysql
from backend.config import get_db_connection

def get_projects_with_peaks():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get projects with editor peaks
        cursor.execute('''
            SELECT DISTINCT project 
            FROM editor_alerts 
            ORDER BY project
        ''')
        projects = cursor.fetchall()
        
        print("\nProjects with Editor Peaks:")
        print("=" * 50)
        for project in projects:
            print(f"- {project[0]}")
        
        # Get top 10 peaks by percentage difference
        cursor.execute('''
            SELECT project, 
                   DATE(timestamp) as date,
                   editor_count, 
                   ROUND(rolling_mean, 1) as avg_editors,
                   ROUND(percentage_difference, 1) as pct_diff
            FROM editor_alerts 
            ORDER BY percentage_difference DESC 
            LIMIT 10
        ''')
        top_peaks = cursor.fetchall()
        
        print("\nTop 10 Editor Peaks:")
        print("=" * 80)
        print(f"{'Project':<30} {'Date':<12} {'Editors':>8} {'Avg':>8} {'% Diff':>8}")
        print("-" * 80)
        for peak in top_peaks:
            print(f"{peak[0]:<30} {peak[1]} {peak[2]:>8} {peak[3]:>8.1f} {peak[4]:>8.1f}%")
            
        print(f"\nTotal projects with peaks: {len(projects)}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    get_projects_with_peaks()
