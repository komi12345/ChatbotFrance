/**
 * Script d'audit Lighthouse automatisé
 * 
 * Usage:
 *   1. Démarrer le serveur: npm run build && npm run start
 *   2. Dans un autre terminal: node scripts/lighthouse-audit.js
 * 
 * Prérequis:
 *   npm install -g lighthouse
 *   ou
 *   npx lighthouse (sans installation globale)
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const OUTPUT_DIR = path.join(__dirname, '..', 'lighthouse-reports');

// Pages à auditer (par ordre de priorité)
const PAGES = [
  { path: '/login', priority: 'high', name: 'Login' },
  { path: '/dashboard', priority: 'high', name: 'Dashboard' },
  { path: '/dashboard/monitoring', priority: 'high', name: 'Dashboard Monitoring' },
  { path: '/contacts', priority: 'high', name: 'Contacts' },
  { path: '/categories', priority: 'high', name: 'Catégories' },
  { path: '/campaigns', priority: 'high', name: 'Campagnes' },
  { path: '/messages', priority: 'high', name: 'Messages' },
  { path: '/statistics', priority: 'high', name: 'Statistiques' },
  { path: '/contacts/import', priority: 'medium', name: 'Import Contacts' },
  { path: '/campaigns/new', priority: 'medium', name: 'Nouvelle Campagne' },
  { path: '/admin-users', priority: 'medium', name: 'Admin Users' },
];

// Objectifs de performance (en ms sauf indication contraire)
const TARGETS = {
  FCP: 100,   // First Contentful Paint
  LCP: 200,   // Largest Contentful Paint
  TTI: 200,   // Time to Interactive
  TBT: 50,    // Total Blocking Time
  CLS: 0.1,   // Cumulative Layout Shift (score)
  performanceScore: 90, // Score global (0-100)
};

// Créer le dossier de sortie
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

console.log('🔍 Audit Lighthouse - Performance Frontend');
console.log('==========================================');
console.log(`Base URL: ${BASE_URL}`);
console.log(`Output: ${OUTPUT_DIR}`);
console.log('');

const results = [];

// Fonction pour exécuter Lighthouse sur une page
function auditPage(page) {
  const url = `${BASE_URL}${page.path}`;
  const outputName = page.path.replace(/\//g, '-').replace(/^-/, '') || 'home';
  const jsonPath = path.join(OUTPUT_DIR, `${outputName}.json`);
  const htmlPath = path.join(OUTPUT_DIR, `${outputName}.html`);

  console.log(`\n📊 Auditing: ${page.name} (${page.path})`);
  console.log(`   Priority: ${page.priority}`);

  try {
    // Exécuter Lighthouse
    const cmd = `npx lighthouse "${url}" --output=json,html --output-path="${path.join(OUTPUT_DIR, outputName)}" --chrome-flags="--headless --no-sandbox" --preset=desktop --quiet`;
    
    execSync(cmd, { stdio: 'pipe' });

    // Lire les résultats JSON
    if (fs.existsSync(jsonPath)) {
      const report = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
      const audits = report.audits;
      const categories = report.categories;

      const metrics = {
        page: page.name,
        path: page.path,
        priority: page.priority,
        performanceScore: Math.round((categories.performance?.score || 0) * 100),
        FCP: Math.round(audits['first-contentful-paint']?.numericValue || 0),
        LCP: Math.round(audits['largest-contentful-paint']?.numericValue || 0),
        TTI: Math.round(audits['interactive']?.numericValue || 0),
        TBT: Math.round(audits['total-blocking-time']?.numericValue || 0),
        CLS: audits['cumulative-layout-shift']?.numericValue?.toFixed(3) || '0',
      };

      // Évaluer par rapport aux objectifs
      metrics.status = {
        performanceScore: metrics.performanceScore >= TARGETS.performanceScore ? '✅' : '❌',
        FCP: metrics.FCP <= TARGETS.FCP ? '✅' : (metrics.FCP <= TARGETS.FCP * 2 ? '⚠️' : '❌'),
        LCP: metrics.LCP <= TARGETS.LCP ? '✅' : (metrics.LCP <= TARGETS.LCP * 2 ? '⚠️' : '❌'),
        TTI: metrics.TTI <= TARGETS.TTI ? '✅' : (metrics.TTI <= TARGETS.TTI * 2 ? '⚠️' : '❌'),
        TBT: metrics.TBT <= TARGETS.TBT ? '✅' : (metrics.TBT <= TARGETS.TBT * 2 ? '⚠️' : '❌'),
        CLS: parseFloat(metrics.CLS) <= TARGETS.CLS ? '✅' : '❌',
      };

      results.push(metrics);

      console.log(`   Performance: ${metrics.status.performanceScore} ${metrics.performanceScore}/100`);
      console.log(`   FCP: ${metrics.status.FCP} ${metrics.FCP}ms (target: ${TARGETS.FCP}ms)`);
      console.log(`   LCP: ${metrics.status.LCP} ${metrics.LCP}ms (target: ${TARGETS.LCP}ms)`);
      console.log(`   TTI: ${metrics.status.TTI} ${metrics.TTI}ms (target: ${TARGETS.TTI}ms)`);
      console.log(`   TBT: ${metrics.status.TBT} ${metrics.TBT}ms (target: ${TARGETS.TBT}ms)`);
      console.log(`   CLS: ${metrics.status.CLS} ${metrics.CLS} (target: ${TARGETS.CLS})`);

    } else {
      console.log('   ❌ Failed to generate report');
      results.push({
        page: page.name,
        path: page.path,
        priority: page.priority,
        error: 'Failed to generate report',
      });
    }
  } catch (error) {
    console.log(`   ❌ Error: ${error.message}`);
    results.push({
      page: page.name,
      path: page.path,
      priority: page.priority,
      error: error.message,
    });
  }
}

// Exécuter l'audit sur toutes les pages
console.log('\n🚀 Starting audit...\n');

for (const page of PAGES) {
  auditPage(page);
}

// Générer le rapport de synthèse
console.log('\n\n📋 RAPPORT DE SYNTHÈSE');
console.log('======================\n');

// Tableau récapitulatif
console.log('| Page | Score | FCP | LCP | TTI | TBT | CLS |');
console.log('|------|-------|-----|-----|-----|-----|-----|');

for (const r of results) {
  if (r.error) {
    console.log(`| ${r.page} | ERROR | - | - | - | - | - |`);
  } else {
    console.log(`| ${r.page} | ${r.status.performanceScore} ${r.performanceScore} | ${r.status.FCP} ${r.FCP}ms | ${r.status.LCP} ${r.LCP}ms | ${r.status.TTI} ${r.TTI}ms | ${r.status.TBT} ${r.TBT}ms | ${r.status.CLS} ${r.CLS} |`);
  }
}

// Identifier les pages les plus lentes
console.log('\n\n🐢 PAGES LES PLUS LENTES (par LCP)');
console.log('===================================\n');

const sortedByLCP = results
  .filter(r => !r.error)
  .sort((a, b) => b.LCP - a.LCP)
  .slice(0, 5);

for (let i = 0; i < sortedByLCP.length; i++) {
  const r = sortedByLCP[i];
  console.log(`${i + 1}. ${r.page} - LCP: ${r.LCP}ms`);
}

// Sauvegarder le rapport JSON
const summaryPath = path.join(OUTPUT_DIR, 'summary.json');
fs.writeFileSync(summaryPath, JSON.stringify({
  date: new Date().toISOString(),
  baseUrl: BASE_URL,
  targets: TARGETS,
  results: results,
}, null, 2));

console.log(`\n\n✅ Audit terminé! Rapports sauvegardés dans: ${OUTPUT_DIR}`);
console.log(`   - Rapport de synthèse: ${summaryPath}`);
console.log(`   - Rapports HTML individuels: ${OUTPUT_DIR}/*.html`);
