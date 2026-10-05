import React, { useEffect, useMemo, useState } from 'react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [page, setPage] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedVariant, setSelectedVariant] = useState(null);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState('');

  const [file, setFile] = useState(null);
  const [drag, setDrag] = useState(false);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [pipelineStage, setPipelineStage] = useState('idle');

  const [benchmark, setBenchmark] = useState(null);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);

  const [aiMetrics, setAiMetrics] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState('');
  const [predictionInput, setPredictionInput] = useState({
  af_tgp: 0.01,
  af_exac: 0.01,
  af_esp: 0.01,
  ref_length: 1,
  alt_length: 1
});

const [predictionResult, setPredictionResult] = useState(null);
const [predictionLoading, setPredictionLoading] = useState(false);
const [predictionError, setPredictionError] = useState('');

  // --------------------------------------------------
  // VCF ANALYSIS
  // --------------------------------------------------
  function handleLogin(event) {
    event.preventDefault();

    setLoginError('');

    if (!loginEmail.trim()) {
      setLoginError('Please enter your email.');
      return;
    }

    if (!loginPassword.trim()) {
      setLoginError('Please enter your password.');
      return;
    }

    setIsLoggedIn(true);
  }
function navigateTo(nextPage) {
  setPage(nextPage);
  setSidebarOpen(false);

  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
}
function generateReport() {
  if (!data) return;

  const doc = new jsPDF();
  const stats = data.summary || {};
  const qc = data.qc || {};

  const reportDate = new Date().toLocaleString();

  // -----------------------------
  // HEADER
  // -----------------------------

  doc.setFontSize(24);
  doc.setFont('helvetica', 'bold');
  doc.text('GenomicX', 20, 25);

  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  doc.text(
    'Genomic Analysis Report',
    20,
    33
  );

  doc.setFontSize(9);
  doc.text(
    `Generated: ${reportDate}`,
    20,
    41
  );

  // -----------------------------
  // DATASET SUMMARY
  // -----------------------------

  doc.setFontSize(15);
  doc.setFont('helvetica', 'bold');
  doc.text('Variant Summary', 20, 55);

  autoTable(doc, {
    startY: 61,
    head: [['Metric', 'Value']],
    body: [
      ['Total variants', stats.variants ?? 'N/A'],
      ['SNPs', stats.snps ?? 'N/A'],
      ['INDELs', stats.indels ?? 'N/A'],
      ['Chromosomes', stats.chromosomes ?? 'N/A']
    ],
    theme: 'grid',
    styles: {
      fontSize: 9
    },
    headStyles: {
      fontStyle: 'bold'
    }
  });

  // -----------------------------
  // QUALITY CONTROL
  // -----------------------------

  doc.setFontSize(15);
  doc.setFont('helvetica', 'bold');

  doc.text(
    'Genomic Quality Control',
    20,
    doc.lastAutoTable.finalY + 18
  );

  autoTable(doc, {
    startY: doc.lastAutoTable.finalY + 23,
    head: [['QC Metric', 'Value']],
    body: [
      [
        'Mean quality',
        stats.mean_quality == null
          ? 'N/A'
          : Number(stats.mean_quality).toFixed(2)
      ],
      [
        'Mean allele frequency',
        stats.mean_af == null
          ? 'N/A'
          : Number(stats.mean_af).toFixed(4)
      ],
      [
        'Mean depth',
        stats.mean_dp == null
          ? 'N/A'
          : Number(stats.mean_dp).toFixed(2)
      ],
      [
        'Rare variants (<1% AF)',
        qc.rare_variants ?? 'N/A'
      ],
      [
        'Common variants (>=5% AF)',
        qc.common_variants ?? 'N/A'
      ],
      [
        'High depth (>=10,000)',
        qc.high_depth_variants ?? 'N/A'
      ],
      [
        'PASS variants',
        qc.pass_variants ?? 'N/A'
      ],
      [
        'Filtered variants',
        qc.filtered_variants ?? 'N/A'
      ]
    ],
    theme: 'grid',
    styles: {
      fontSize: 9
    },
    headStyles: {
      fontStyle: 'bold'
    }
  });

  // -----------------------------
  // CHROMOSOME DISTRIBUTION
  // -----------------------------

  doc.addPage();

  doc.setFontSize(15);
  doc.setFont('helvetica', 'bold');
  doc.text('Chromosome Distribution', 20, 25);

  const chromosomeRows =
    (data.chromosome_distribution || []).map(
      item => [
        item.chromosome,
        item.count
      ]
    );

  autoTable(doc, {
    startY: 32,
    head: [['Chromosome', 'Variant Count']],
    body: chromosomeRows,
    theme: 'grid',
    styles: {
      fontSize: 9
    },
    headStyles: {
      fontStyle: 'bold'
    }
  });

  // -----------------------------
  // RECENT VARIANTS
  // -----------------------------

  doc.setFontSize(15);
  doc.setFont('helvetica', 'bold');

  doc.text(
    'Variant Records',
    20,
    doc.lastAutoTable.finalY + 18
  );

  const variantRows =
    (data.variants || []).slice(0, 25).map(
      variant => [
        variant.chromosome ?? 'N/A',
        variant.position ?? 'N/A',
        variant.reference ?? 'N/A',
        variant.alternate ?? 'N/A',
        variant.type ?? 'N/A',
        variant.clinvar_id ?? 'N/A',
        variant.clinical_significance ?? 'N/A'
      ]
    );

  autoTable(doc, {
    startY: doc.lastAutoTable.finalY + 23,
    head: [[
      'Chromosome',
      'Position',
      'Reference',
      'Alternate',
      'Type',
      'ClinVar ID',
      'Significance'
    ]],
    body: variantRows,
    theme: 'grid',
    styles: {
      fontSize: 7
    },
    headStyles: {
      fontStyle: 'bold'
    }
  });

  // -----------------------------
  // FOOTER
  // -----------------------------
  // -----------------------------
  // AI ANALYSIS
  // -----------------------------

  if (aiMetrics) {
    doc.addPage();

    doc.setFontSize(15);
    doc.setFont('helvetica', 'bold');
    doc.text('AI Variant Classification', 20, 25);

    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');

    doc.text(
      `Model: ${aiMetrics.model}`,
      20,
      33
    );

    doc.text(
      'ClinVar-labelled variant classification using population allele-frequency features.',
      20,
      40
    );

    autoTable(doc, {
      startY: 47,
      head: [['Evaluation Metric', 'Score']],
      body: [
        [
          'Accuracy',
          `${(aiMetrics.metrics.accuracy * 100).toFixed(2)}%`
        ],
        [
          'Precision',
          `${(aiMetrics.metrics.precision * 100).toFixed(2)}%`
        ],
        [
          'Recall',
          `${(aiMetrics.metrics.recall * 100).toFixed(2)}%`
        ],
        [
          'F1 Score',
          `${(aiMetrics.metrics.f1 * 100).toFixed(2)}%`
        ],
        [
          'ROC-AUC',
          `${(aiMetrics.metrics.roc_auc * 100).toFixed(2)}%`
        ],
        [
          'PR-AUC',
          `${(aiMetrics.metrics.pr_auc * 100).toFixed(2)}%`
        ]
      ],
      theme: 'grid',
      styles: {
        fontSize: 9
      },
      headStyles: {
        fontStyle: 'bold'
      }
    });

    // Dataset information

    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');

    doc.text(
      'Training Dataset',
      20,
      doc.lastAutoTable.finalY + 18
    );

    autoTable(doc, {
      startY: doc.lastAutoTable.finalY + 23,
      head: [['Dataset Metric', 'Value']],
      body: [
        [
          'Labelled variants',
          aiMetrics.dataset.records
        ],
        [
          'Pathogenic',
          aiMetrics.dataset.pathogenic
        ],
        [
          'Benign',
          aiMetrics.dataset.benign
        ]
      ],
      theme: 'grid',
      styles: {
        fontSize: 9
      },
      headStyles: {
        fontStyle: 'bold'
      }
    });

    // SHAP importance

    doc.setFontSize(13);
    doc.setFont('helvetica', 'bold');

    doc.text(
      'SHAP Feature Importance',
      20,
      doc.lastAutoTable.finalY + 18
    );

    const shapRows =
      (aiMetrics.features || []).map(
        feature => [
          feature.name,
          Number(feature.importance).toFixed(4)
        ]
      );

    autoTable(doc, {
      startY: doc.lastAutoTable.finalY + 23,
      head: [['Feature', 'Mean |SHAP|']],
      body: shapRows,
      theme: 'grid',
      styles: {
        fontSize: 9
      },
      headStyles: {
        fontStyle: 'bold'
      }
    });

    doc.setFontSize(8);
    doc.setFont('helvetica', 'italic');

    doc.text(
      'AI results represent research/demo classification of ClinVar-labelled variants and are not a medical diagnosis.',
      20,
      doc.lastAutoTable.finalY + 16
    );
  }
  const pageCount = doc.internal.getNumberOfPages();

  for (let page = 1; page <= pageCount; page++) {
    doc.setPage(page);

    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');

    doc.text(
      'GenomicX • Research / educational use only • Not a medical diagnosis',
      20,
      285
    );

    doc.text(
      `Page ${page} of ${pageCount}`,
      170,
      285
    );
  }

  // -----------------------------
  // DOWNLOAD
  // -----------------------------

  doc.save('GenomicX_Analysis_Report.pdf');
}
  async function analyze() {
    if (!file) return;

    setLoading(true);
setError('');
setPipelineStage('validation');

    try {
      const formData = new FormData();
      formData.append('file', file);
setPipelineStage('processing');
      const response = await fetch(`${API}/api/analyze`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || 'Failed to analyze VCF');
      }

      const json = await response.json();

setPipelineStage('completed');
setData(json);
setPage('analytics');

    } catch (err) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  // --------------------------------------------------
  // BENCHMARK
  // --------------------------------------------------

  async function loadBenchmark() {
    if (benchmark) return;

    try {
      setBenchmarkLoading(true);

      const response = await fetch(`${API}/api/benchmark`);

      if (!response.ok) {
        throw new Error('Failed to load benchmark');
      }

      const json = await response.json();
      console.log('GENOMICX ANALYSIS DATA:', json);
      setPipelineStage('completed');
setData(json);
      setBenchmark(json);

    } catch (err) {
      console.error(err);
    } finally {
      setBenchmarkLoading(false);
    }
  }

  // --------------------------------------------------
  // AI METRICS
  // --------------------------------------------------

  async function loadAiMetrics() {
    try {
      setAiLoading(true);
      setAiError('');

      const response = await fetch(`${API}/api/ai-metrics`);

      if (!response.ok) {
        throw new Error('Failed to load AI metrics');
      }

      const json = await response.json();
      setAiMetrics(json);

    } catch (err) {
      setAiError(err.message || 'Unable to load AI metrics');
    } finally {
      setAiLoading(false);
    }
  }
  async function predictVariant() {
    try {
      setPredictionLoading(true);
      setPredictionError('');
      setPredictionResult(null);

      const response = await fetch(`${API}/api/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(predictionInput)
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || 'Prediction failed');
      }

      const json = await response.json();
      setPredictionResult(json);

    } catch (err) {
      setPredictionError(
        err.message || 'Unable to generate prediction'
      );
    } finally {
      setPredictionLoading(false);
    }
  }
  // --------------------------------------------------
  // LOAD DATA WHEN NAVIGATION CHANGES
  // --------------------------------------------------

  useEffect(() => {
    if (page === 'benchmark' && !benchmark) {
      loadBenchmark();
    }

    if (page === 'ai' && !aiMetrics) {
      loadAiMetrics();
    }
  }, [page]);

  // --------------------------------------------------
  // DRAG & DROP
  // --------------------------------------------------

  function handleDrop(event) {
    event.preventDefault();
    setDrag(false);

    const droppedFile = event.dataTransfer.files?.[0];

    if (droppedFile) {
      setFile(droppedFile);
      setError('');
    }
  }

  function handleFileChange(event) {
    const selectedFile = event.target.files?.[0];

    if (selectedFile) {
      setFile(selectedFile);
      setPipelineStage('idle');
      setError('');
    }
  }

  // --------------------------------------------------
  // DATA
  // --------------------------------------------------

  const stats = data?.summary || {
    variants: 0,
    snps: 0,
    indels: 0,
    chromosomes: 0,
    mean_quality: 0
  };

  const maxChromosomeCount = useMemo(() => {
    if (!data?.chromosome_distribution) return 1;

    const counts = data.chromosome_distribution.map(
      item => item.count
    );

    return Math.max(...counts, 1);
  }, [data]);

  // --------------------------------------------------
  // RENDER
  // --------------------------------------------------
  if (!isLoggedIn) {
    return (
      <div className="login-page">

        <div className="login-background">
          <div className="dna-glow glow-one" />
          <div className="dna-glow glow-two" />
          <div className="dna-line line-one" />
          <div className="dna-line line-two" />
        </div>

        <div className="login-card">

          <div className="login-brand">
            <div className="login-brandmark">
              GX
            </div>

            <div>
              <strong>GenomicX</strong>
              <span>Genomic Intelligence Platform</span>
            </div>
          </div>

          <div className="login-heading">
            <div className="eyebrow">
              GENOMIC INTELLIGENCE
            </div>

            <h1>
              Welcome back.
            </h1>

            <p>
              Access your genomic analytics and
              explainable AI workspace.
            </p>
          </div>

          <form onSubmit={handleLogin}>

            <label className="login-field">
              <span>Email address</span>

              <input
                type="email"
                placeholder="researcher@example.com"
                value={loginEmail}
                onChange={(event) =>
                  setLoginEmail(event.target.value)
                }
              />
            </label>


            <label className="login-field">
              <span>Password</span>

              <div className="password-wrapper">

                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={loginPassword}
                  onChange={(event) =>
                    setLoginPassword(event.target.value)
                  }
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword(!showPassword)
                  }
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>

              </div>
            </label>


            {loginError && (
              <div className="login-error">
                {loginError}
              </div>
            )}


            <button
              type="submit"
              className="login-button"
            >
              Sign in to GenomicX
              <span>→</span>
            </button>

          </form>


          <div className="login-footer">

            <span>
              Research workflows
            </span>

            <span>•</span>

            <span>
              Variant analytics
            </span>

            <span>•</span>

            <span>
              Explainable AI
            </span>

          </div>

        </div>

      </div>
    );
  }
  return (
    <div className="app">

      {/* HEADER */}

      <div className="mobile-header">
  <button
    className="menu-button"
    onClick={() => setSidebarOpen(!sidebarOpen)}
  >
    ☰
  </button>

  <div className="mobile-brand">
    <span className="brand-mark">GX</span>
    <span>GenomicX</span>
  </div>
</div>

<aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
  <div className="sidebar-brand">
    <div className="brand-mark">GX</div>
    <div>
      <strong>GenomicX</strong>
      <span>GENOMIC INTELLIGENCE</span>
    </div>
  </div>

  <div className="sidebar-section">
    <span className="sidebar-label">WORKSPACE</span>

    <button
      className={`sidebar-item ${page === 'overview' ? 'active' : ''}`}
      onClick={() => navigateTo('overview')}
    >
      <span>⌂</span>
      Dashboard
    </button>

    <button
      className={`sidebar-item ${page === 'analytics' ? 'active' : ''}`}
      onClick={() => navigateTo('analytics')}
    >
      <span>⌁</span>
      Variant Analytics
    </button>
    <button
  className={`sidebar-item ${page === 'benchmark' ? 'active' : ''}`}
  onClick={() => navigateTo('benchmark')}
>
  <span>◈</span>
  Scalability
</button>

    

    <button
      className={`sidebar-item ${page === 'ai' ? 'active' : ''}`}
      onClick={() => navigateTo('ai')}
    >
      <span>✦</span>
      AI Analysis
    </button>
  </div>

  <div className="sidebar-section sidebar-bottom">
    <span className="sidebar-label">SYSTEM</span>

  <button
  className={`sidebar-item ${page === 'settings' ? 'active' : ''}`}
  onClick={() => navigateTo('settings')}
>
  <span>⚙</span>
  Settings
</button>

    <button
      className="sidebar-item signout"
      onClick={() => setIsLoggedIn(false)}
    >
      <span>↪</span>
      Sign out
    </button>
  </div>

  <div className="sidebar-user">
    <div className="user-avatar">R</div>
    <div>
      <strong>Researcher</strong>
      <span>GenomicX Workspace</span>
    </div>
  </div>
</aside>

{sidebarOpen && (
  <div
    className="sidebar-overlay"
    onClick={() => setSidebarOpen(false)}
  />
)}


      <main>

        {/* ==================================================
            OVERVIEW
        ================================================== */}

        {page === 'overview' && (
          <>

            <section className="hero">

              <div className="eyebrow">
                SCALABLE GENOMIC DATA INTELLIGENCE
              </div>

              <h1>
                Turn genomic data into
                <span> actionable analytics.</span>
              </h1>

              <p>
                GenomicX combines VCF processing, PySpark,
                variant analytics, machine learning and
                explainable AI into one research workflow.
              </p>

            </section>


            <section id="upload" className="upload-section">

              <div className="section-head">

                <div>
                  <div className="eyebrow">
                    01 / DATA INGESTION
                  </div>

                  <h2>
                    Upload a genomic dataset
                  </h2>
                </div>

                <span className="pill">
                  VCF / VCF.GZ
                </span>

              </div>


              <div
                className={`dropzone ${drag ? 'dragging' : ''}`}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDrag(true);
                }}
                onDragLeave={() => setDrag(false)}
                onDrop={handleDrop}
              >

                <input
                  id="file"
                  type="file"
                  accept=".vcf,.gz,.vcf.gz"
                  onChange={handleFileChange}
                />

                <label htmlFor="file">

                  <div className="upload-icon">
                    ↑
                  </div>

                  <strong>
                    {file
                      ? file.name
                      : 'Drop your VCF file here'}
                  </strong>

                  <span>
                    or click to browse
                  </span>

                </label>

              </div>


              {error && (
                <div className="error">
                  {error}
                </div>
              )}


              <button
                className="primary wide"
                onClick={analyze}
                disabled={!file || loading}
              >
                {loading
                  ? 'Processing dataset...'
                  : 'Analyze dataset →'}
              </button>

                        </section>

            {pipelineStage !== 'idle' && (
              <section className="pipeline-section">

                <div className="section-head">
                  <div>
                    <div className="eyebrow">
                      02 / PIPELINE MONITOR
                    </div>

                    <h2>
                      Genomic processing pipeline
                    </h2>
                  </div>

                  <span className={`pipeline-status ${pipelineStage}`}>
                    {pipelineStage === 'validation' && 'VALIDATING'}
                    {pipelineStage === 'processing' && 'PROCESSING'}
                    {pipelineStage === 'completed' && 'COMPLETED'}
                    {pipelineStage === 'error' && 'ERROR'}
                  </span>
                </div>

                <div className="pipeline-track">

                  <div
                    className={`pipeline-step ${
                      ['validation', 'processing', 'completed'].includes(pipelineStage)
                        ? 'active'
                        : ''
                    }`}
                  >
                    <div className="pipeline-dot">01</div>
                    <div>
                      <strong>Validation</strong>
                      <span>Checking VCF structure and input data</span>
                    </div>
                  </div>

                  <div
                    className={`pipeline-line ${
                      ['processing', 'completed'].includes(pipelineStage)
                        ? 'active'
                        : ''
                    }`}
                  />

                  <div
                    className={`pipeline-step ${
                      ['processing', 'completed'].includes(pipelineStage)
                        ? 'active'
                        : ''
                    }`}
                  >
                    <div className="pipeline-dot">02</div>
                    <div>
                      <strong>PySpark Processing</strong>
                      <span>Parsing and analysing genomic variants</span>
                    </div>
                  </div>

                  <div
                    className={`pipeline-line ${
                      pipelineStage === 'completed'
                        ? 'active'
                        : ''
                    }`}
                  />

                  <div
                    className={`pipeline-step ${
                      pipelineStage === 'completed'
                        ? 'active'
                        : ''
                    }`}
                  >
                    <div className="pipeline-dot">03</div>
                    <div>
                      <strong>Analytics Ready</strong>
                      <span>Variant results prepared for analysis</span>
                    </div>
                  </div>

                </div>

                {pipelineStage === 'processing' && (
                  <div className="pipeline-live">
                    <span className="live-dot"></span>
                    GenomicX is processing your dataset with PySpark...
                  </div>
                )}

                {pipelineStage === 'error' && (
                  <div className="pipeline-error">
                    Pipeline processing failed. Check the error message above.
                  </div>
                )}

              </section>
            )}

            <section className="stack-section">

              <div className="section-head">

                <div>
                  <div className="eyebrow">
                    PLATFORM STACK
                  </div>

                  <h2>
                    Built for scalable genomic analytics
                  </h2>
                </div>

              </div>


              <div className="cards">

                <div className="card">
                  <div className="card-icon">VCF</div>
                  <h3>VCF ingestion</h3>
                  <p>
                    Validate and parse genomic variant
                    records from standard VCF datasets.
                  </p>
                </div>

                <div className="card">
                  <div className="card-icon">SP</div>
                  <h3>PySpark</h3>
                  <p>
                    Process large variant datasets using
                    distributed-style data processing.
                  </p>
                </div>

                <div className="card">
                  <div className="card-icon">AI</div>
                  <h3>XGBoost</h3>
                  <p>
                    Classify ClinVar-labelled variants using
                    population allele-frequency features.
                  </p>
                </div>

                <div className="card">
                  <div className="card-icon">SH</div>
                  <h3>SHAP</h3>
                  <p>
                    Explain model predictions through
                    feature-level contribution analysis.
                  </p>
                </div>

              </div>

            </section>

          </>
        )}


        {/* ==================================================
            ANALYTICS
        ================================================== */}

        {page === 'analytics' && (
          <section className="dashboard">

            <div className="section-head">

              <div>
  <div className="eyebrow">
    02 / VARIANT ANALYTICS
  </div>

  <h2>
    Genomic variant overview
  </h2>
</div>

{data && (
  <button
    className="report-button"
    onClick={generateReport}
  >
    ↓ Download PDF Report
  </button>
)}

              <span className="pill">
                {data ? 'Dataset analyzed' : 'Awaiting dataset'}
              </span>

            </div>


            {!data ? (

              <div className="card empty">

                <h3>
                  No dataset analyzed yet
                </h3>

                <p>
                  Upload a VCF file from the Overview page
                  to generate variant analytics.
                </p>

                <button
                  className="primary"
                  onClick={() => setPage('overview')}
                >
                  Go to upload →
                </button>

              </div>

            ) : (

              <>

                <div
  className="metrics-grid benchmark-metrics-grid"
  style={{
    display: 'grid',
    gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
    gap: '14px',
    width: '100%'
  }}
>

                  <div className="card metric">
                    <span>Total variants</span>
                    <strong>
                      {stats.variants?.toLocaleString()}
                    </strong>
                  </div>

                  <div className="card metric">
                    <span>SNPs</span>
                    <strong>
                      {stats.snps?.toLocaleString()}
                    </strong>
                  </div>

                  <div className="card metric">
                    <span>INDELs</span>
                    <strong>
                      {stats.indels?.toLocaleString()}
                    </strong>
                  </div>

                  <div className="card metric">
                    <span>Chromosomes</span>
                    <strong>
                      {stats.chromosomes?.toLocaleString()}
                    </strong>
                  </div>

                </div>
<div className="card qc-card advanced-qc">

  <div className="qc-header">
    <div>
      <div className="card-title">
        Genomic Quality Control
      </div>

      <p className="qc-subtitle">
        Quality and population-level characteristics of the analyzed variants.
      </p>
    </div>

    <span className="qc-badge">
      LIVE QC
    </span>
  </div>


  <div className="qc-grid">

    {/* MEAN QUALITY */}

    <div className="qc-item">
      <span>Mean quality</span>

      <strong>
        {stats.mean_quality == null
          ? 'N/A'
          : stats.mean_quality.toFixed(2)}
      </strong>

      {stats.mean_quality != null && (
        <div className="qc-bar">
          <i
            style={{
              width: `${Math.min(stats.mean_quality, 100)}%`
            }}
          />
        </div>
      )}
    </div>


    {/* MEAN AF */}

    <div className="qc-item">
      <span>Mean allele frequency</span>

      <strong>
        {stats.mean_af == null
          ? 'N/A'
          : stats.mean_af.toFixed(4)}
      </strong>

      {stats.mean_af != null && (
        <div className="qc-bar">
          <i
            style={{
              width: `${Math.min(stats.mean_af * 100, 100)}%`
            }}
          />
        </div>
      )}
    </div>


    {/* MEAN DEPTH */}

    <div className="qc-item">
      <span>Mean depth</span>

      <strong>
        {stats.mean_dp == null
          ? 'N/A'
          : stats.mean_dp.toFixed(2)}
      </strong>

      <small>
        Coverage information
      </small>
    </div>


    {/* RARE */}

    <div className="qc-item">
      <span>Rare variants (&lt;1% AF)</span>

      <strong>
        {data.qc?.rare_variants?.toLocaleString() ?? 'N/A'}
      </strong>

      <small>
        Low-frequency variants
      </small>
    </div>


    {/* COMMON */}

    <div className="qc-item">
      <span>Common variants (&gt;=5% AF)</span>

      <strong>
        {data.qc?.common_variants?.toLocaleString() ?? 'N/A'}
      </strong>

      <small>
        Higher-frequency variants
      </small>
    </div>


    {/* HIGH DEPTH */}

    <div className="qc-item">
      <span>High depth (&gt;=10,000)</span>

      <strong>
        {data.qc?.high_depth_variants?.toLocaleString() ?? 'N/A'}
      </strong>

      <small>
        High-coverage variants
      </small>
    </div>


    {/* PASS */}

    <div className="qc-item qc-positive">
      <span>PASS variants</span>

      <strong>
        {data.qc?.pass_variants?.toLocaleString() ?? 'N/A'}
      </strong>

      {stats.variants > 0 && (
        <small>
          {(
            (data.qc?.pass_variants / stats.variants) *
            100
          ).toFixed(1)}% of dataset
        </small>
      )}
    </div>


    {/* FILTERED */}

    <div className="qc-item">
      <span>Filtered variants</span>

      <strong>
        {data.qc?.filtered_variants?.toLocaleString() ?? 'N/A'}
      </strong>

      {stats.variants > 0 && (
        <small>
          {(
            (data.qc?.filtered_variants / stats.variants) *
            100
          ).toFixed(1)}% of dataset
        </small>
      )}
    </div>

  </div>


  {/* QC SUMMARY */}

  <div className="qc-summary">

    <div>
      <span>Dataset status</span>
      <strong>QC COMPLETE</strong>
    </div>

    <div>
      <span>Variants assessed</span>
      <strong>
        {stats.variants?.toLocaleString() ?? 'N/A'}
      </strong>
    </div>

    <div>
      <span>PASS rate</span>
      <strong>
        {stats.variants > 0
          ? `${(
              (data.qc?.pass_variants / stats.variants) *
              100
            ).toFixed(1)}%`
          : 'N/A'}
      </strong>
    </div>

  </div>

</div>
                <div className="cards">

                  <div className="card">

                    <div className="card-title">
                      Variants by chromosome
                    </div>

                    <div className="chart">

                      {data.chromosome_distribution?.map(
                        item => {

                          const width =
                            (item.count /
                              maxChromosomeCount) * 100;

                          return (
                            <div
                              className="chart-row"
                              key={item.chromosome}
                            >

                              <span>
                                {item.chromosome}
                              </span>

                              <div className="track">
                                <i
                                  style={{
                                    width: `${width}%`
                                  }}
                                />
                              </div>

                              <b>
                                {item.count.toLocaleString()}
                              </b>

                            </div>
                          );
                        }
                      )}

                    </div>

                  </div>


                  <div className="card table-card">

                    <div className="card-title">
                      Recent variants
                    </div>

                    <table>

                      <thead>
  <tr>
    <th>Chromosome</th>
    <th>Position</th>
    <th>Reference</th>
    <th>Alternate</th>
    <th>Type</th>
    <th>ClinVar ID</th>
    <th>Significance</th>
  </tr>
</thead>

                      <tbody>

                        {data.variants?.slice(0, 10).map(
                          (variant, index) => (

                            <tr
  key={index}
  className="variant-row"
  onClick={() => setSelectedVariant(variant)}
>

                              <td>
                                {variant.chromosome}
                              </td>

                              <td>
                                {variant.position?.toLocaleString()}
                              </td>

                              <td>
                                {variant.reference}
                              </td>

                              <td>
                                {variant.alternate}
                              </td>

                              <td>
                                {variant.variant_type ||
                                  variant.type ||
                                  'SNV'}
                              </td>
                              <td>
  {variant.clinvar_id || 'N/A'}
</td>

<td>
  {variant.clinical_significance || 'Not available'}
</td>

                            </tr>

                          )
                        )}

                      </tbody>

                    </table>
                      
</div>

</div>

{selectedVariant && (

  <div className="annotation-explorer">

    <div className="annotation-header">

      <div>
        <div className="eyebrow">
          VARIANT ANNOTATION
        </div>

        <h3>
          {selectedVariant.chromosome}:
          {selectedVariant.position}
        </h3>
      </div>

      <button
        className="annotation-close"
        onClick={() => setSelectedVariant(null)}
      >
        ×
      </button>

    </div>

    <div className="annotation-grid">

      <div>
        <span>Chromosome</span>
        <strong>
          {selectedVariant.chromosome || 'N/A'}
        </strong>
      </div>

      <div>
        <span>Position</span>
        <strong>
          {selectedVariant.position?.toLocaleString() || 'N/A'}
        </strong>
      </div>

      <div>
        <span>Reference</span>
        <strong>
          {selectedVariant.reference || 'N/A'}
        </strong>
      </div>

      <div>
        <span>Alternate</span>
        <strong>
          {selectedVariant.alternate || 'N/A'}
        </strong>
      </div>

      <div>
        <span>Variant type</span>
        <strong>
          {selectedVariant.variant_type ||
            selectedVariant.type ||
            'SNV'}
        </strong>
      </div>

      <div>
        <span>ClinVar ID</span>
        <strong>
          {selectedVariant.clinvar_id || 'Not available'}
        </strong>
      </div>

      <div className="annotation-significance">
        <span>Clinical significance</span>
        <strong>
          {selectedVariant.clinical_significance ||
            'Not available'}
        </strong>
      </div>

    </div>

  </div>
)}

</>

)}
          </section>
        )}


        {/* ==================================================
            BENCHMARK
        ================================================== */}

        {page === 'benchmark' && (
          <section className="benchmark-page">

            <div className="section-head">

              <div>
                <div className="eyebrow">
                  02 / SCALABILITY
                </div>

                <h2>
                  Pandas vs PySpark
                </h2>
              </div>

              <span className="pill">
                Local benchmark
              </span>

            </div>


            {benchmarkLoading && (
              <div className="card">
                <h3>Loading benchmark...</h3>
                <p>
                  Fetching measured processing results.
                </p>
              </div>
            )}


            {benchmark && (
              <>

                <div
  className="metrics-grid benchmark-metrics-grid"
  style={{
    display: 'grid',
    gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
    gap: '14px',
    width: '100%'
  }}
>

                  <div className="card metric">
                    <span>Largest dataset</span>
                    <strong>5M</strong>
                  </div>

                  <div className="card metric">
                    <span>Dataset sizes</span>
                    <strong>
                      {benchmark.results?.length || 5}
                    </strong>
                  </div>

                  <div className="card metric">
                    <span>Repeated runs</span>
                    <strong>
                      {benchmark.repetitions || 3}
                    </strong>
                  </div>

                  <div className="card metric">
                    <span>Execution</span>
                    <strong>
                      local[*]
                    </strong>
                  </div>

                </div>


                <div className="card">

                  <div className="card-title">
                    Processing time by dataset size
                  </div>

                  <div className="benchmark-chart">

                    {benchmark.results?.map(row => {

                      const maxTime = Math.max(
                        ...benchmark.results.flatMap(r => [
                          r.pandas_seconds,
                          r.pyspark_seconds
                        ])
                      );

                      const pandasWidth = Math.max(
                        3,
                        row.pandas_seconds /
                          maxTime * 100
                      );

                      const sparkWidth = Math.max(
                        3,
                        row.pyspark_seconds /
                          maxTime * 100
                      );

                      return (
                        <div
                          className="benchmark-row"
                          key={row.dataset_size}
                        >

                          <div className="benchmark-label">
                            {row.dataset_size >= 1000000
                              ? `${row.dataset_size / 1000000}M`
                              : `${row.dataset_size / 1000}K`}
                          </div>

                          <div className="benchmark-bars">

                            <div className="benchmark-bar pandas">

                              <span>
                                Pandas
                              </span>

                              <i
                                style={{
                                  width: `${pandasWidth}%`
                                }}
                              />

                              <b>
                                {row.pandas_seconds.toFixed(3)}s
                              </b>

                            </div>


                            <div className="benchmark-bar spark">

                              <span>
                                PySpark
                              </span>

                              <i
                                style={{
                                  width: `${sparkWidth}%`
                                }}
                              />

                              <b>
                                {row.pyspark_seconds.toFixed(3)}s
                              </b>

                            </div>

                          </div>

                        </div>
                      );
                    })}

                  </div>

                </div>


                <div className="card benchmark-note">

                  <h3>
                    What the benchmark shows
                  </h3>

                  <p>
                    On this local development machine,
                    Pandas completed the tested aggregation
                    faster across all measured dataset sizes.
                    PySpark introduces additional execution
                    overhead because the Spark execution engine
                    coordinates distributed-style processing.
                  </p>

                  <p>
                    The purpose of this experiment is not to
                    claim that PySpark is faster on a single
                    machine. It demonstrates how the same
                    genomic processing workload behaves as
                    dataset size increases and provides a
                    measurable basis for evaluating distributed
                    processing.
                  </p>

                  <div className="disclaimer">
                    Local benchmark only — results are not a
                    cluster-scale performance comparison.
                  </div>

                </div>


                <div className="card">

                  <h3>
                    Benchmark methodology
                  </h3>

                  <p>
                    The same chromosome-level aggregation
                    workload was measured using Pandas and
                    PySpark across five dataset sizes, from
                    10,000 to 5,000,000 variants.
                  </p>

                  <p>
                    Each measurement uses three repeated runs.
                    PySpark runs in local[*] mode on the
                    development machine, so Spark execution
                    overhead is included in the measured
                    processing time.
                  </p>

                </div>

              </>
            )}

          </section>
        )}


        {/* ==================================================
            AI ANALYSIS
        ================================================== */}
{page === 'settings' && (
  <section className="dashboard">

    <div className="section-head">
      <div>
        <div className="eyebrow">
          05 / SETTINGS
        </div>

        <h2>
          Platform settings
        </h2>

        <p>
          Manage your GenomicX workspace configuration.
        </p>
      </div>

      <span className="pill">
        Workspace active
      </span>
    </div>

    <div className="settings-grid">

      <div className="card settings-card">
        <div className="settings-icon">R</div>

        <div>
          <span className="settings-label">
            PROFILE
          </span>

          <h3>
            Researcher
          </h3>

          <p>
            GenomicX Research Workspace
          </p>
        </div>
      </div>

      <div className="card settings-card">
        <div className="settings-icon">●</div>

        <div>
          <span className="settings-label">
            API STATUS
          </span>

          <h3>
            Connected
          </h3>

          <p>
            GenomicX API is available.
          </p>
        </div>
      </div>

      <div className="card settings-card">
        <div className="settings-icon">GX</div>

        <div>
          <span className="settings-label">
            PLATFORM
          </span>

          <h3>
            GenomicX
          </h3>

          <p>
            Genomic intelligence and variant analytics platform.
          </p>
        </div>
      </div>

      <div className="card settings-card">
        <div className="settings-icon">VCF</div>

        <div>
          <span className="settings-label">
            DATA PROCESSING
          </span>

          <h3>
            VCF / VCF.GZ
          </h3>

          <p>
            Genomic variant ingestion and quality analysis.
          </p>
        </div>
      </div>

      <div className="card settings-card">
        <div className="settings-icon">AI</div>

        <div>
          <span className="settings-label">
            AI ANALYSIS
          </span>

          <h3>
            XGBoost + SHAP
          </h3>

          <p>
            Explainable classification of ClinVar-labelled variants.
          </p>
        </div>
      </div>

      <div className="card settings-card">
        <div className="settings-icon">DB</div>

        <div>
          <span className="settings-label">
            STORAGE
          </span>

          <h3>
            PostgreSQL + Parquet
          </h3>

          <p>
            Structured metadata and processed genomic data storage.
          </p>
        </div>
      </div>

    </div>

    <div className="card settings-about">

      <div className="eyebrow">
        ABOUT GENOMICX
      </div>

      <h3>
        Research-focused genomic intelligence
      </h3>

      <p>
        GenomicX combines VCF processing, scalable data
        processing, variant analytics, machine learning,
        and explainable AI into a unified research workflow.
      </p>

      <div className="settings-tags">
        <span>VCF</span>
        <span>PySpark</span>
        <span>PostgreSQL</span>
        <span>XGBoost</span>
        <span>SHAP</span>
        <span>Parquet</span>
      </div>

    </div>

  </section>
)}
        {page === 'ai' && (
          <section className="ai-page">

            <div className="section-head">

              <div>
                <div className="eyebrow">
                  03 / AI ANALYSIS
                </div>

                <h2>
                  Explainable variant classification
                </h2>
              </div>

              <span className="pill">
                Research demo
              </span>

            </div>


            {aiLoading && (
              <div className="card">

                <h3>
                  Loading model results...
                </h3>

                <p>
                  Fetching XGBoost evaluation metrics
                  and SHAP feature importance.
                </p>

              </div>
            )}


            {aiError && (
              <div className="card">

                <h3>
                  Unable to load AI metrics
                </h3>

                <p>
                  {aiError}
                </p>

              </div>
            )}


            {aiMetrics && (
              <>
{/* LIVE VARIANT PREDICTION */}

<div className="card prediction-panel">

  <div className="section-head">

    <div>
      <div className="eyebrow">
        LIVE MODEL INFERENCE
      </div>

      <h3>
        Classify a variant
      </h3>

      <p>
        Enter the five features used by the trained XGBoost
        model to generate a research/demo classification.
      </p>
    </div>

    <span className="pill">
      XGBoost + SHAP
    </span>

  </div>


  <div className="prediction-form">

    <label>
      <span>AF TGP</span>

      <input
        type="number"
        step="0.0001"
        min="0"
        max="1"
        value={predictionInput.af_tgp}
        onChange={(event) =>
          setPredictionInput({
            ...predictionInput,
            af_tgp: Number(event.target.value)
          })
        }
      />
    </label>


    <label>
      <span>AF ExAC</span>

      <input
        type="number"
        step="0.0001"
        min="0"
        max="1"
        value={predictionInput.af_exac}
        onChange={(event) =>
          setPredictionInput({
            ...predictionInput,
            af_exac: Number(event.target.value)
          })
        }
      />
    </label>


    <label>
      <span>AF ESP</span>

      <input
        type="number"
        step="0.0001"
        min="0"
        max="1"
        value={predictionInput.af_esp}
        onChange={(event) =>
          setPredictionInput({
            ...predictionInput,
            af_esp: Number(event.target.value)
          })
        }
      />
    </label>


    <label>
      <span>Reference length</span>

      <input
        type="number"
        min="1"
        value={predictionInput.ref_length}
        onChange={(event) =>
          setPredictionInput({
            ...predictionInput,
            ref_length: Number(event.target.value)
          })
        }
      />
    </label>


    <label>
      <span>Alternate length</span>

      <input
        type="number"
        min="1"
        value={predictionInput.alt_length}
        onChange={(event) =>
          setPredictionInput({
            ...predictionInput,
            alt_length: Number(event.target.value)
          })
        }
      />
    </label>

  </div>


  <button
    className="primary"
    onClick={predictVariant}
    disabled={predictionLoading}
  >
    {predictionLoading
      ? 'Running XGBoost...'
      : 'Run classification →'}
  </button>


  {predictionError && (
    <div className="error">
      {predictionError}
    </div>
  )}


  {predictionResult && (
  <div className="prediction-result">

    <div className="prediction-summary">

      <div>
        <span>Classification</span>

        <strong>
          {predictionResult.label}
        </strong>
      </div>

      <div>
        <span>Model probability</span>

        <strong>
          {(predictionResult.probability * 100).toFixed(2)}%
        </strong>
      </div>

    </div>


    <div className="prediction-explanation">

      <h4>
        Why did the model make this prediction?
      </h4>

      <p>
        SHAP values show how each feature contributed
        to this individual prediction.
      </p>

      {predictionResult.features?.map((feature) => (
        <div
          className="feature"
          key={feature[0]}
        >

          <div>
            <span>
              {feature[0]}
            </span>

            <b>
              {Number(feature[1]).toFixed(3)}
            </b>
          </div>

          <div className="track">

            <i
              style={{
                width: `${Math.min(
                  Math.abs(Number(feature[1])) * 20,
                  100
                )}%`
              }}
            />

          </div>

        </div>
      ))}

    </div>

  </div>
)}
</div>
                {/* MODEL OVERVIEW + PERFORMANCE */}

                <div className="ai-grid">

                  <div className="card predictor">

                    <h3>
                      Model overview
                    </h3>

                    <p>
                      XGBoost classification model trained
                      using ClinVar-labelled chromosome 22
                      variants and population allele-frequency
                      features.
                    </p>


                    <div className="prediction">

                      <span>
                        Model
                      </span>

                      <strong>
                        {aiMetrics.model}
                      </strong>

                      <small>
                        {aiMetrics.dataset.records.toLocaleString()}
                        {' '}labelled variants
                      </small>

                    </div>


                   <div className="dataset-stats">

  <div className="dataset-stat">
    <span>PATHOGENIC</span>
    <b>
      {aiMetrics.dataset.pathogenic}
    </b>
  </div>

  <div className="dataset-stat">
    <span>BENIGN</span>
    <b>
      {aiMetrics.dataset.benign.toLocaleString()}
    </b>
  </div>

</div>

                  </div>


                  {/* PERFORMANCE */}

                  <div className="card explain">

                    <h3>
                      Model performance
                    </h3>


                    {[
                      ['Accuracy', aiMetrics.metrics.accuracy],
                      ['Precision', aiMetrics.metrics.precision],
                      ['Recall', aiMetrics.metrics.recall],
                      ['F1 Score', aiMetrics.metrics.f1],
                      ['ROC-AUC', aiMetrics.metrics.roc_auc],
                      ['PR-AUC', aiMetrics.metrics.pr_auc]
                    ].map(([name, value]) => (

                      <div
                        className="feature"
                        key={name}
                      >

                        <div>

                          <span>
                            {name}
                          </span>

                          <b>
                            {(value * 100).toFixed(2)}%
                          </b>

                        </div>

                        <div className="track">

                          <i
                            style={{
                              width: `${value * 100}%`
                            }}
                          />

                        </div>

                      </div>

                    ))}

                  </div>

                </div>


                {/* SHAP */}

                <div className="card">

                  <h3>
                    SHAP feature importance
                  </h3>

                  <p>
                    Mean absolute SHAP values show the
                    relative contribution of each feature
                    to the XGBoost model's predictions.
                  </p>


                  {(() => {

                    const maxImportance = Math.max(
                      ...aiMetrics.features.map(
                        feature => feature.importance
                      )
                    );

                    return aiMetrics.features.map(feature => {

                      const width =
                        maxImportance > 0
                          ? (
                              feature.importance /
                              maxImportance
                            ) * 100
                          : 0;

                      return (
                        <div
                          className="feature"
                          key={feature.name}
                        >

                          <div>

                            <span>
                              {feature.name}
                            </span>

                            <b>
                              {feature.importance.toFixed(3)}
                            </b>

                          </div>

                          <div className="track">

                            <i
                              style={{
                                width: `${width}%`
                              }}
                            />

                          </div>

                        </div>
                      );

                    });

                  })()}


                  <div className="disclaimer">
                    {aiMetrics.note}
                  </div>

                </div>

              </>
            )}

          </section>
        )}

      </main>


      {/* FOOTER */}

      <footer>

        <span>
          GenomicX
        </span>

        <span>
          Big Data · AI · Genomics
        </span>

        <span>
          Built for research workflows
        </span>

      </footer>

    </div>
  );
}

createRoot(
  document.getElementById('root')
).render(
  <App />
);
