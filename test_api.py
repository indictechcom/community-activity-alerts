import requests

# Test the Arabic Wikinews API endpoint
url = 'http://localhost:5000/api/editor-activity-data'
params = {
    'language': 'ar',
    'project_group': 'ar.wikinews.org',
    'datestart': 'Jan 2023',
    'dateend': 'Dec 2025'
}

print("Testing Arabic Wikinews API...")
print(f"URL: {url}")
print(f"Params: {params}\n")

r = requests.get(url, params=params)
print(f"Status Code: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    peaks = data.get('peaks', [])
    chart_data = data.get('chartData', {})
    
    print(f"\nPeaks found: {len(peaks)}")
    print(f"Chart data points: {len(chart_data.get('lineTrace', {}).get('x', []))}")
    
    if peaks:
        print("\nFirst 3 peaks:")
        for peak in peaks[:3]:
            print(f"  - {peak['timestamp']}: {peak['editors']} editors (+{peak['percentage_difference']}%)")
    
    if chart_data.get('lineTrace', {}).get('x'):
        print(f"\nDate range: {chart_data['lineTrace']['x'][0]} to {chart_data['lineTrace']['x'][-1]}")
else:
    print(f"Error: {r.text}")
