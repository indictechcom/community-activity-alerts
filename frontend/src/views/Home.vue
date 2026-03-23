<template>
  <div class="min-h-screen bg-white">
    <Navbar />

    <div class="pt-20 pb-16">
      <!-- Hero Section - Wikipedia Style -->
      <div class="max-w-4xl mx-auto px-6 mb-12">
        <h1 class="wiki-title mb-4">
          Community Activity Alerts
        </h1>
        <p class="wiki-subtitle mb-6">
          A tool for tracking and analyzing edit activity across Wikimedia projects
        </p>
        <div class="wiki-intro-box mb-8">
          <p class="mb-4">
            <strong>Community Activity Alerts</strong> is a monitoring tool that tracks edit and editor activity across all Wikimedia projects. 
            It uses statistical analysis to detect unusual activity spikes and provides email notifications for projects you watch.
          </p>
          <div class="flex flex-wrap gap-3">
            <router-link to="/edit-counts">
              <cdx-button action="progressive" weight="primary">
                View Edit Activity
              </cdx-button>
            </router-link>
            <router-link to="/watchlist">
              <cdx-button action="default" weight="normal">
                Setup Watchlist
              </cdx-button>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Main Content - Wikipedia Style -->
      <div class="max-w-4xl mx-auto px-6">
        <!-- Features Section -->
        <div class="wiki-section mb-8">
          <h2 class="wiki-section-title">Features</h2>
          <div class="wiki-content">
            <ul class="wiki-list">
              <li><strong>Edit Activity Tracking</strong> – Monitor monthly edit counts across all Wikimedia projects with interactive charts and trend analysis</li>
              <li><strong>Editor Analytics</strong> – Track active editor counts and understand community growth patterns over time</li>
              <li><strong>Peak Detection</strong> – Automatically identify unusual activity spikes using statistical analysis and rolling averages</li>
              <li><strong>Custom Watchlists</strong> – Create personalized watchlists for specific projects or languages with email notifications</li>
              <li><strong>Annotation System</strong> – Add labels and notes to detected peaks for collaborative documentation</li>
              <li><strong>Historical Data</strong> – Access over 3 years of historical data with flexible date range selection</li>
            </ul>
          </div>
        </div>

        <!-- How It Works Section -->
        <div class="wiki-section mb-8">
          <h2 class="wiki-section-title">How it works</h2>
          <div class="wiki-content">
            <p class="mb-4">
              Community Activity Alerts operates through a three-stage process:
            </p>
            <ol class="wiki-list">
              <li><strong>Data Collection</strong> – Automated scripts fetch monthly edit and editor counts from the Wikimedia API for all projects. Data is stored in a MySQL database and updated regularly through scheduled cron jobs.</li>
              <li><strong>Peak Detection</strong> – Statistical algorithms analyze the collected data to identify unusual activity spikes. Peaks are detected by comparing current values against rolling averages and dynamic thresholds.</li>
              <li><strong>Visualization & Alerts</strong> – Interactive charts display activity trends and detected peaks. Users can create watchlists to receive email notifications when significant changes occur in their monitored projects.</li>
            </ol>
          </div>
        </div>

        <!-- Getting Started Section -->
        <div class="wiki-section mb-8">
          <h2 class="wiki-section-title">Getting started</h2>
          <div class="wiki-content">
            <p class="mb-4">
              To begin using Community Activity Alerts:
            </p>
            <ul class="wiki-list">
              <li><strong>Explore Edit Activity</strong> – Navigate to the <router-link to="/edit-counts" class="wiki-link">Edit Counts</router-link> page to view monthly edit trends for any Wikimedia project</li>
              <li><strong>Monitor Editors</strong> – Check the <router-link to="/editor-counts" class="wiki-link">Editor Counts</router-link> page to track active contributor numbers over time</li>
              <li><strong>Setup Watchlist</strong> – <span v-if="!auth.isAuthenticated"><a href="#" @click.prevent="auth.login" class="wiki-link">Login</a> with your Wikimedia account and</span> add projects or languages to your <router-link to="/watchlist" class="wiki-link">watchlist</router-link> for email notifications</li>
              <li><strong>Review & Annotate</strong> – Access the <router-link to="/reviewer" class="wiki-link">Reviewer Dashboard</router-link> to label detected peaks and collaborate with other reviewers</li>
            </ul>
          </div>
        </div>

        <!-- Coverage Section -->
        <div class="wiki-section mb-8">
          <h2 class="wiki-section-title">Coverage</h2>
          <div class="wiki-content">
            <p>
              The tool currently monitors <strong>over 900 Wikimedia projects</strong> across all language editions, including Wikipedia, Wiktionary, Wikibooks, Wikinews, Wikiquote, Wikisource, Wikiversity, and Wikivoyage. Historical data spans <strong>more than 3 years</strong>, with regular updates ensuring real-time peak detection and alerts.
            </p>
          </div>
        </div>

        <!-- See Also Section -->
        <div class="wiki-section mb-8">
          <h2 class="wiki-section-title">See also</h2>
          <div class="wiki-content">
            <ul class="wiki-list">
              <li><a href="https://github.com/indictechcom/community-activity-alerts" target="_blank" class="wiki-link">Project repository on GitHub</a></li>
              <li><router-link to="/edit-counts" class="wiki-link">Edit Activity Dashboard</router-link></li>
              <li><router-link to="/editor-counts" class="wiki-link">Editor Analytics</router-link></li>
              <li><router-link to="/watchlist" class="wiki-link">Watchlist Management</router-link></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'
import { CdxButton } from '@wikimedia/codex'
import Navbar from '../components/Navbar.vue'

const auth = useAuthStore()
</script>

<style scoped>
/* Wikipedia-style Typography */
.wiki-title {
  font-family: 'Linux Libertine', 'Georgia', 'Times', serif;
  font-size: 2rem;
  line-height: 1.3;
  color: #202122;
  font-weight: normal;
  border-bottom: 1px solid #a2a9b1;
  padding-bottom: 0.25rem;
  margin-bottom: 0.5rem;
}

.wiki-subtitle {
  font-family: sans-serif;
  font-size: 0.875rem;
  color: #54595d;
  font-style: italic;
}

.wiki-intro-box {
  background-color: #f8f9fa;
  border: 1px solid #a2a9b1;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  font-size: 0.95rem;
  line-height: 1.6;
}

.wiki-section {
  border-bottom: 1px solid #a2a9b1;
  padding-bottom: 1.5rem;
}

.wiki-section-title {
  font-family: 'Linux Libertine', 'Georgia', 'Times', serif;
  font-size: 1.5rem;
  line-height: 1.3;
  color: #202122;
  font-weight: normal;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid #a2a9b1;
  padding-bottom: 0.25rem;
}

.wiki-content {
  font-family: sans-serif;
  font-size: 0.95rem;
  line-height: 1.6;
  color: #202122;
}

.wiki-content p {
  margin-bottom: 0.5rem;
}

.wiki-list {
  margin-left: 1.6rem;
  margin-bottom: 0.5rem;
}

.wiki-list li {
  margin-bottom: 0.5rem;
  line-height: 1.6;
}

.wiki-link {
  color: #3366cc;
  text-decoration: none;
}

.wiki-link:hover {
  text-decoration: underline;
}

.wiki-link:visited {
  color: #795cb2;
}

/* Ensure proper spacing */
strong {
  font-weight: 600;
}
</style>
