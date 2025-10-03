// src/mockData.js

// Mimics the language data passed to the template
export const mockLanguages = {
    "English": [{ sitename: "wiki", url: "https://en.wikipedia.org" }],
    "Español": [{ sitename: "wiki", url: "https://es.wikipedia.org" }],
    // ... more languages and projects
};

// Mimics the peak data for the table
export const mockPeaks = [
    { timestamp: 'Jan 2024', edits: 1500, rolling_mean: 1200, threshold: 1450, percentage_difference: '4.17%', label: '' },
    { timestamp: 'Mar 2024', edits: 2200, rolling_mean: 1300, threshold: 1600, percentage_difference: '37.50%', label: 'Possible Event' },
];


export const mockChartData = {
  // Trace for the main line graph
  lineTrace: {
    x: ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024', 'May 2024'],
    y: [1100, 1300, 2200, 1400, 1600],
    type: 'scatter',
    mode: 'lines',
    name: 'Edits',
    line: {
      color: 'var(--color-progressive)',
      width: 2
    }
  },
  // Trace for the peak markers and labels
  peaksTrace: {
    x: ['Mar 2024'],
    y: [2200],
    mode: 'markers+text',
    name: 'Peaks',
    text: ['Possible Event'],
    textposition: 'top center',
    marker: {
      color: 'var(--color-error)',
      size: 10
    },
    textfont: {
      color: 'var(--color-error)'
    }
  }
};