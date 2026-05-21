import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  Hexagon, Upload, Zap, BarChart3, MessageSquare, Shield,
  ArrowRight, CheckCircle, TrendingUp, Brain, Database,
  AlertTriangle, Activity, Bot, Sparkles, Check, Menu, X,
  Hash, CreditCard, Landmark, IndianRupee, Calendar, User,
  ChevronRight, FileCheck, Cpu, Lock
} from 'lucide-react';
import s from './LandingPage.module.css';
import { Flag } from 'lucide-react';

const NAV_LINKS = ['Features', 'Solutions', 'Pricing', 'Docs'];

/* ── Hero slides ── */
const SLIDES = [
  {
    label: '01 / 04',
    tag: 'AI Document Intelligence',
    headline: ['Extract. Analyze.', 'Understand.'],
    accent: 'Bank Documents.',
    desc: 'Advanced AI OCR pipeline with YOLO field detection and TrOCR — built specifically for cheques and financial documents.',
    stat: { value: '98.7%', label: 'Extraction Accuracy' },
    orbColor: 'purple',
    visual: 'cheque',
  },
  {
    label: '02 / 04',
    tag: '2.3s Average Processing',
    headline: ['From Upload', 'to JSON.'],
    accent: 'Instantly.',
    desc: 'Detect cheque fields, read handwritten values, validate formats and return clean structured data for your finance workflow.',
    stat: { value: '2.3s', label: 'Avg. Processing Time' },
    orbColor: 'green',
    visual: 'pipeline',
  },
  {
    label: '03 / 04',
    tag: 'Document Analytics',
    headline: ['Track Trends.', 'Find Exceptions.'],
    accent: 'Act Faster.',
    desc: 'Turn every processed cheque into searchable records, field-level metrics and amount trends your team can review at a glance.',
    stat: { value: '12.4K', label: 'Documents Indexed' },
    orbColor: 'purple',
    visual: 'analytics',
  },
  {
    label: '04 / 04',
    tag: 'Enterprise Security',
    headline: ['Ask Questions.', 'Protect Data.'],
    accent: 'With AI.',
    desc: 'Chat with processed cheque data while keeping authentication, audit trails and controlled access built into the product.',
    stat: { value: '24/7', label: 'AI Data Assistant' },
    orbColor: 'green',
    visual: 'assistant',
  },
];

const FEATURES = [
  {
    icon: '🇮🇳',
    color: 'green',
    title: 'Indian Handwriting Optimized',
    highlight: true,
    desc: 'Specialized for Indian handwritten cheque processing with enhanced OCR preprocessing, IFSC correction and field-aware extraction.'
  },

  {
    icon: Brain,
    color: 'purple',
    title: 'YOLO + TrOCR Pipeline',
    desc: 'State-of-the-art object detection identifies cheque fields, then TrOCR reads handwriting with industry-leading accuracy.'
  },

  {
    icon: Zap,
    color: 'green',
    title: 'Instant Extraction',
    desc: 'Cheque number, account, IFSC, amount, date and payee extracted in under 3 seconds per document.'
  },

  {
    icon: BarChart3,
    color: 'purple',
    title: 'Analytics Dashboard',
    desc: 'Real-time charts, trend analysis and anomaly detection across all processed documents.'
  },

  {
    icon: MessageSquare,
    color: 'green',
    title: 'AI Chat Assistant',
    desc: 'Ask questions about your data in plain language - powered by AI for instant answers.'
  },

  {
    icon: Database,
    color: 'purple',
    title: 'Structured Export',
    desc: 'Export to JSON, CSV or Excel and integrate via REST API into any existing workflow.'
  },
];

const STEPS = [
  { n: '01', icon: Upload,    color: 'purple', title: 'Upload Document',   desc: 'Drag-drop or upload cheques and bank statements in JPG, PNG, TIFF or PDF.' },
  { n: '02', icon: Cpu,       color: 'green',  title: 'AI OCR Processing', desc: 'YOLO detects fields, TrOCR reads text - all in under 3 seconds.' },
  { n: '03', icon: FileCheck, color: 'purple', title: 'Data Validation',   desc: 'Extracted fields are validated for format and consistency automatically.' },
  { n: '04', icon: BarChart3, color: 'green',  title: 'Insights & Analytics', desc: 'View trends, flag anomalies and track extraction rates on the dashboard.' },
  { n: '05', icon: Database,  color: 'purple', title: 'Export & Integrate', desc: 'Download as JSON/CSV or push via REST API to your existing systems.' },
];

const INSIGHTS = [
  { icon: TrendingUp,   color: 'green',  bg: 'rgba(34,197,94,0.07)',   border: 'rgba(34,197,94,0.2)',    tag: 'High Value',       title: 'High Value Cheques',    desc: '23 cheques above ₹5,00,000 detected this month.' },
  { icon: AlertTriangle, color: 'amber', bg: 'rgba(245,158,11,0.07)',  border: 'rgba(245,158,11,0.2)',   tag: 'Alert',            title: 'Unusual Activity',      desc: '5 cheques flagged for review due to anomalies.' },
  { icon: Landmark,     color: 'purple', bg: 'rgba(139,92,246,0.07)',  border: 'rgba(139,92,246,0.2)',   tag: 'Top Bank',         title: 'Top Bank',              desc: 'HDFC Bank appears in 38.7% of documents.' },
  { icon: Calendar,     color: 'cyan',   bg: 'rgba(6,182,212,0.07)',   border: 'rgba(6,182,212,0.2)',    tag: 'Peak Day',         title: 'Peak Processing Day',   desc: 'Most documents received on 24th May 2024.' },
];

const TRUSTED = ['FINCORP', 'PayMate', 'CREDENCE', 'LendFlow', 'WealthDesk', 'FinRise'];

const DEMO_RESULT = {
  cheque_number: '005123',
  date: '24/05/2024',
  payee_name: 'Ramesh Kumar',
  amount: '₹48,750.00',
  account_number: '50100234867891',
  ifsc_code: 'HDFC0001234',
  bank_name: 'HDFC Bank',
  micr_code: '110240002',
};

function HeroVisual({ type }) {
  if (type === 'pipeline') {
    return (
      <div className={`${s.visualCard} ${s.pipelineVisual}`}>
        <div className={s.visualHeader}>
          <span><Cpu size={14} /> OCR Workflow</span>
          <strong>2.3s</strong>
        </div>
        <div className={s.flowStack}>
          {[
            { icon: Upload, label: 'Upload', sub: 'Cheque image received', pct: 100 },
            { icon: Brain, label: 'Detect', sub: 'YOLO locates 6 fields', pct: 100 },
            { icon: FileCheck, label: 'Read', sub: 'TrOCR extracts text', pct: 86 },
            { icon: Database, label: 'Export', sub: 'Clean JSON generated', pct: 72 },
          ].map(({ icon: Icon, label, sub, pct }) => (
            <div className={s.flowItem} key={label}>
              <div className={s.flowIcon}><Icon size={16} /></div>
              <div className={s.flowBody}>
                <div className={s.flowTop}>
                  <span>{label}</span>
                  <em>{pct}%</em>
                </div>
                <p>{sub}</p>
                <div className={s.flowBar}><div style={{ width: `${pct}%` }} /></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (type === 'analytics') {
    return (
      <div className={`${s.visualCard} ${s.analyticsVisual}`}>
        <div className={s.visualHeader}>
          <span><BarChart3 size={14} /> Insights Dashboard</span>
          <strong>Live</strong>
        </div>
        <div className={s.miniMetrics}>
          <div><span>Total Value</span><strong>₹4.87Cr</strong></div>
          <div><span>Detection</span><strong>98.7%</strong></div>
          <div><span>Review Queue</span><strong>23</strong></div>
        </div>
        <div className={s.chartMock}>
          {[58, 82, 46, 92, 68, 76, 54].map((h, i) => (
            <span key={i} style={{ height: `${h}%` }} />
          ))}
        </div>
        <div className={s.insightStrip}>
          <AlertTriangle size={14} />
          <span>5 high-value cheques flagged for review</span>
        </div>
      </div>
    );
  }

  if (type === 'assistant') {
    return (
      <div className={`${s.visualCard} ${s.assistantVisual}`}>
        <div className={s.visualHeader}>
          <span><Bot size={14} /> Document Assistant</span>
          <strong>Secured</strong>
        </div>
        <div className={s.assistantThread}>
          <div className={s.botLine}>Which payee received the highest cheque?</div>
          <div className={s.userLine}>Ramesh Kumar received ₹48,750 on 24/05/2024.</div>
          <div className={s.botLine}>Export matching records?</div>
        </div>
        <div className={s.securityRow}>
          <span><Lock size={13} /> JWT Auth</span>
          <span><Shield size={13} /> Audit Trail</span>
        </div>
      </div>
    );
  }

  return (
    <div className={s.processingCard}>
      <div className={s.processingHeader}>
        <div className={s.processingLive}>
          <FileCheck size={14} />
          FIELD DETECTION
        </div>
        <div className={s.liveDot}><CheckCircle size={13} /> COMPLETE</div>
      </div>

      <div className={s.chequeWrap}>
        <div className={s.scanLine} />
        <img src="/image.png" alt="Cheque Processing" className={s.chequeImage} />
      </div>

      <div className={s.completeBadge}>
        <CheckCircle size={17} />
        <div>
          <strong>Processing complete</strong>
          <span>6 fields extracted with 98.7% confidence</span>
        </div>
      </div>
    </div>
  );
}

export default function LandingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [slide, setSlide] = useState(0);
  const [slideAnim, setSlideAnim] = useState(true);
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [demoActive, setDemoActive] = useState(false);
  const [demoStatus, setDemoStatus] = useState('idle'); // idle | processing | done
  const demoTimerRef = useRef(null);
  const assistantSectionRef = useRef(null);
  const assistantVideoRef = useRef(null);
  const [particles] = useState(() =>
    Array.from({ length: 72 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 2.4 + 1.6,
      dur: Math.random() * 8 + 6,
      del: Math.random() * 6,
    }))
  );

  const goApp = useCallback(() => navigate(user ? '/app/analyzer' : '/login'), [user, navigate]);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', fn);
    return () => window.removeEventListener('scroll', fn);
  }, []);

  useEffect(() => {
    const t = setInterval(() => {
      setSlideAnim(false);
      setTimeout(() => {
        setSlide(s => (s + 1) % SLIDES.length);
        setSlideAnim(true);
      }, 300);
    }, 5500);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    return () => window.clearTimeout(demoTimerRef.current);
  }, []);

  useEffect(() => {
    const section = assistantSectionRef.current;
    const video = assistantVideoRef.current;

    if (!section || !video) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          video.currentTime = 0;
          video.play().catch(() => {});
        } else {
          video.pause();
        }
      },
      {
        threshold: 0.55,
      }
    );

    observer.observe(section);

    return () => observer.disconnect();
  }, []);

  const changeSlide = (i) => {
    setSlideAnim(false);
    setTimeout(() => { setSlide(i); setSlideAnim(true); }, 250);
  };

  const startDemo = () => {
    setDemoActive(true);
    setDemoStatus('processing');
    window.clearTimeout(demoTimerRef.current);
    demoTimerRef.current = window.setTimeout(() => {
      setDemoStatus('done');
    }, 1800);
  };

  const cur = SLIDES[slide];

  return (
    <div className={s.page}>
      {/* ── Particles ── */}
      <div className={s.particles} aria-hidden>
        {particles.map(p => (
          <span
            key={p.id}
            className={s.particle}
            style={{
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: p.size,
              height: p.size,
              animationDuration: `${p.dur}s`,
              animationDelay: `${p.del}s`,
            }}
          />
        ))}
      </div>

      {/* ── Navbar ── */}
      <nav className={`${s.nav} ${scrolled ? s.navScrolled : ''}`}>
        <div className={s.navInner}>
          <Link to="/" className={s.logo}>
            <Hexagon size={22} strokeWidth={1.5} className={s.logoIcon} />
            <span className={s.logoText}>DocOCR</span>
          </Link>

          <ul className={`${s.navLinks} ${menuOpen ? s.navLinksOpen : ''}`}>
            {NAV_LINKS.map(l => (
              <li key={l}><a href="#" className={s.navLink}>{l}</a></li>
            ))}
          </ul>

          <div className={s.navActions}>
            {user ? (
              <button className={s.btnPrimary} onClick={() => navigate('/app/analyzer')}>
                Dashboard <ArrowRight size={14} />
              </button>
            ) : (
              <>
                <Link to="/login" className={s.signInLink}>Sign in</Link>
                <Link to="/register" className={s.btnPrimary}>Get Started <ArrowRight size={14} /></Link>
              </>
            )}
          </div>

          <button className={s.hamburger} onClick={() => setMenuOpen(o => !o)}>
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className={s.hero}>
        {/* Grid overlay */}
        <div className={s.heroGrid} aria-hidden />

        {/* Orb */}
        <div className={`${s.orb} ${cur.orbColor === 'green' ? s.orbGreen : s.orbPurple}`} aria-hidden>
          <div className={s.orbHalo} />
          <div className={s.orbCore} />
          <div className={s.orbRing1} />
          <div className={s.orbRing2} />
        </div>

        <div className={s.heroInner}>
          {/* Left content */}
          <div className={`${s.heroLeft} ${slideAnim ? s.slideIn : s.slideOut}`}>
            <div className={s.heroCounter}>{cur.label}</div>

            <div className={`${s.heroTag} ${cur.orbColor === 'green' ? s.heroTagGreen : s.heroTagPurple}`}>
              <span className={s.heroTagDot} />
              {cur.tag}
            </div>

            <h1 className={s.heroTitle}>
              {cur.headline.map((line, i) => <span key={i}>{line}<br /></span>)}
              <span className={cur.orbColor === 'green' ? s.accentGreen : s.accentPurple}>
                {cur.accent}
              </span>
            </h1>

            <p className={s.heroDesc}>{cur.desc}</p>

            <div className={s.heroStat}>
              <div className={`${s.heroStatVal} ${cur.orbColor === 'green' ? s.heroStatValGreen : s.heroStatValPurple}`}>
                {cur.stat.value}
              </div>
              <div className={s.heroStatLabel}>{cur.stat.label}</div>
            </div>

            <div className={s.heroCtas}>
              <button className={s.btnPrimary} onClick={goApp}>
                Start Free Trial <ArrowRight size={15} />
              </button>
              <button className={s.btnGhost} onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}>
                See Live Demo
              </button>
            </div>

            <div className={s.heroTrust}>
              <span><Check size={12} className={s.chk} /> YOLO + TrOCR Powered</span>
              <span><Check size={12} className={s.chk} /> 2 Min Setup</span>
              <span><Check size={12} className={s.chk} /> Excel • JSON • CSV Export</span>
            </div>
          </div>

          {/* Right — slide-specific visual */}
          <div className={`${s.heroRight} ${slideAnim ? s.slideInRight : s.slideOutRight}`}>
            <HeroVisual type={cur.visual} />
          </div>
        </div>

        {/* Slide dots */}
        <div className={s.slideDots}>
          {SLIDES.map((_, i) => (
            <button
              key={i}
              className={`${s.slideDot} ${slide === i ? s.slideDotActive : ''}`}
              onClick={() => changeSlide(i)}
            />
          ))}
        </div>
      </section>

      {/* ── Trusted by ── */}
      <div className={s.trustedBy}>
        <p className={s.trustedLabel}>Built with workflows inspired by modern fintech teams</p>
        <div className={s.trustedLogos}>
          {TRUSTED.map(t => <span key={t} className={s.trustedLogo}>{t}</span>)}
        </div>
      </div>

      {/* ── Live Demo ── */}
      <section className={s.section} id="demo">
        <div className={s.sectionInner}>
          <div className={s.demoGrid}>
            <div className={s.demoLeft}>
              <div className={`${s.sectionTag} ${s.sectionTagPurple}`}>
                <Zap size={11} /> Live OCR Demo
              </div>
              <h2 className={s.sectionTitle}>Upload a cheque.<br />See AI extraction in action.</h2>
              <p className={s.sectionDesc}>Drop any cheque image and watch our YOLO + TrOCR pipeline extract all fields in real time.</p>

              <div
                className={`${s.dropzone} ${demoActive ? s.dropzoneActive : ''}`}
                onClick={startDemo}
                onDragOver={e => { e.preventDefault(); if (!demoActive) startDemo(); }}
                onDrop={e => { e.preventDefault(); startDemo(); }}
              >
                {demoStatus === 'done' ? (
                  <div className={s.dropSuccess}>
                    <div className={s.dropSuccessIcon}><CheckCircle size={28} /></div>
                    <p>cheque_001.jpg</p>
                    <span>Uploaded Successfully</span>
                  </div>
                ) : demoStatus === 'processing' ? (
                  <div className={s.dropSuccess}>
                    <div className={s.dropSuccessIcon}><Activity size={28} className={s.spinSlow} /></div>
                    <p>cheque_001.jpg</p>
                    <span>Running field detection...</span>
                  </div>
                ) : (
                  <>
                    <div className={s.dropIcon}><Upload size={26} /></div>
                    <p className={s.dropTitle}>Drag & drop your cheque here</p>
                    <span className={s.dropHint}>PNG · JPG · PDF · TIFF — up to 10MB</span>
                  </>
                )}
              </div>

              <button className={s.btnPrimary} style={{ width: '100%', justifyContent: 'center', marginTop: 14 }} onClick={goApp}>
                Try with Your Document <ArrowRight size={14} />
              </button>
            </div>

            <div className={s.demoRight}>
              {demoStatus === 'idle' && (
                <div className={s.demoEmpty}>
                  <div className={s.demoEmptyIcon}><Upload size={26} /></div>
                  <p>Waiting for document</p>
                  <span>Upload a cheque to reveal extracted fields.</span>
                </div>
              )}

              {demoStatus === 'processing' && (
                <div className={s.demoProcessing}>
                  <div className={s.demoResultHead}>
                    <span>Processing Document</span>
                    <span className={s.confBadge}><Activity size={10} /> Live</span>
                  </div>
                  {['Uploading image', 'Detecting cheque fields', 'Reading handwritten text', 'Validating output'].map((step, i) => (
                    <div className={s.demoProcessStep} key={step}>
                      <div className={s.demoProcessDot}>{i < 2 ? <Check size={12} /> : <Activity size={12} className={s.spinSlow} />}</div>
                      <span>{step}</span>
                      <div className={s.demoProcessBar}><div style={{ width: `${[100, 100, 68, 38][i]}%` }} /></div>
                    </div>
                  ))}
                </div>
              )}

              {demoStatus === 'done' && (
                <>
                  <div className={s.demoResultHead}>
                    <span>Extracted Data</span>
                    <span className={s.confBadge}><Activity size={10} /> 96.8% Confidence</span>
                  </div>
                  <div className={s.demoFields}>
                    {Object.entries(DEMO_RESULT).map(([k, v]) => (
                      <div className={s.demoField} key={k}>
                        <div className={s.demoFieldKey}>{k.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</div>
                        <div className={`${s.demoFieldVal} mono`}>{v}</div>
                      </div>
                    ))}
                  </div>
                  <div className={s.demoActions}>
                    <button className={s.btnSmallGhost}>View Full Details</button>
                    <button className={s.btnSmallGhost}>Export Excel</button>
                    <button className={s.btnSmallPrimary}>Download JSON</button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className={s.section}>
        <div className={s.sectionInner}>
          <div className={s.centerHead}>
            <div className={`${s.sectionTag} ${s.sectionTagGreen}`}><Sparkles size={11} /> Features</div>
            <h2 className={s.sectionTitle}>Everything built for financial documents</h2>
            <p className={s.sectionDesc} style={{ maxWidth: 520, margin: '10px auto 0' }}>
              Precision-engineered for cheques, bank statements and financial paperwork.
            </p>
          </div>
          <div className={s.featGrid}>
            {FEATURES.map(({ icon: Icon, color, title, desc }) => (
              <div className={`${s.featCard} ${color === 'green' ? s.featCardGreen : s.featCardPurple}`} key={title}>
                <div className={`${s.featIcon} ${color === 'green' ? s.featIconGreen : s.featIconPurple}`}>
                  {typeof Icon === 'string' ? (
                    <span className={s.flagEmoji}>{Icon}</span>
                  ) : (
                    <Icon size={20} strokeWidth={1.8} />
                  )}
                </div>
                <h3 className={s.featTitle}>{title}</h3>
                <p className={s.featDesc}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── AI Insights ── */}
      <section className={s.section}>
        <div className={s.sectionInner}>
          <div className={s.centerHead}>
            <div className={`${s.sectionTag} ${s.sectionTagPurple}`}><Brain size={11} /> AI Insights</div>
            <h2 className={s.sectionTitle}>Detect Anomalies. Spot Trends.</h2>
          </div>
          <div className={s.insightsGrid}>
            {INSIGHTS.map(({ icon: Icon, color, bg, border, tag, title, desc }) => {
              const cls = color === 'green' ? s.insightGreen : color === 'amber' ? s.insightAmber : color === 'cyan' ? s.insightCyan : s.insightPurple;
              const tagCls = color === 'green' ? s.tagGreen : color === 'amber' ? s.tagAmber : color === 'cyan' ? s.tagCyan : s.tagPurple;
              return (
                <div className={`${s.insightCard} ${cls}`} key={title} style={{ background: bg, borderColor: border }}>
                  <div className={`${s.insightIcon} ${cls}`}><Icon size={16} /></div>
                  <span className={`${s.insightTag} ${tagCls}`}>{tag}</span>
                  <div className={s.insightTitle}>{title}</div>
                  <div className={s.insightDesc}>{desc}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section className={s.section}>
        <div className={s.sectionInner}>
          <div className={s.centerHead}>
            <h2 className={s.sectionTitle}>How DocOCR Works</h2>
          </div>
          <div className={s.stepsRow}>
            {STEPS.map(({ n, icon: Icon, color, title, desc }, i) => (
              <React.Fragment key={n}>
                <div className={s.stepCard}>
                  <div className={`${s.stepNum} ${color === 'green' ? s.stepNumGreen : s.stepNumPurple}`}>{n}</div>
                  <div className={`${s.stepIcon} ${color === 'green' ? s.stepIconGreen : s.stepIconPurple}`}>
                    <Icon size={22} strokeWidth={1.8} />
                  </div>
                  <div className={s.stepTitle}>{title}</div>
                  <div className={s.stepDesc}>{desc}</div>
                </div>
                {i < STEPS.length - 1 && <ChevronRight size={16} className={s.stepArrow} />}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* ── Chat ── */}
      <section className={s.section}>
        <div className={s.sectionInner}>
          <div className={s.chatLayout}>
            <div className={s.chatLeft} ref={assistantSectionRef}>
              <div className={s.botVideoWrap}>
                <video
                  ref={assistantVideoRef}
                  className={s.botVideo}
                  autoPlay
                  muted
                  loop
                  playsInline
                >
                  <source src="/bot.mp4" type="video/mp4" />
                </video>
              </div>
              <div className={`${s.sectionTag} ${s.sectionTagPurple}`}><Bot size={11} /> AI Assistant</div>
              <h2 className={s.sectionTitle}>Chat with Your Documents</h2>
              <p className={s.sectionDesc}>Ask questions, get insights and export data.</p>
              <button className={s.btnPrimary} onClick={goApp}>
                Try AI Chat <ArrowRight size={14} />
              </button>
            </div>
            <div className={s.chatRight}>
              <div className={s.chatBubbleBot}>Found 23 cheques greater than ₹50,000. <span className={s.chatLink}>View Results →</span></div>
              <div className={s.chatBubbleBot}>Which bank appears most frequently? <span className={s.chatLink}>View Analysis →</span></div>
              <div className={s.chatBubbleUser}>HDFC Bank appears most frequently in 38.7% of total documents.</div>
              <div className={s.chatBubbleBot}>Export ready! <span className={s.chatLink}>documents.csv ↓</span></div>
              <div className={s.chatInputDummy}>
                <MessageSquare size={14} />
                <span>Ask anything about your documents...</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Security ── */}
      {/* <section className={s.section}>
        <div className={s.sectionInner}>
          <div className={s.securityCard}>
            <div className={s.securityLeft}>
              <div className={`${s.sectionTag} ${s.sectionTagGreen}`}><Lock size={11} /> Enterprise Security</div>
              <h2 className={s.sectionTitle} style={{ fontSize: '1.65rem' }}>Enterprise Grade Security You Can Trust</h2>
              <div className={s.securityItems}>
                {[
                  'AES-256 encryption for all stored data',
                  'JWT authentication with token expiry',
                  'Documents processed in isolated environments',
                  'GDPR compliant data handling',
                  'Granular role-based access control',
                  'Full audit log for every extraction',
                ].map(item => (
                  <div className={s.securityItem} key={item}>
                    <CheckCircle size={15} className={s.securityCheck} />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className={s.securityRight}>
              <div className={s.shieldOrb}>
                <div className={s.shieldOrbGlow} />
                <Shield size={72} strokeWidth={1} className={s.shieldIcon} />
                <div className={s.shieldBadge}><CheckCircle size={12} /> Secured</div>
              </div>
            </div>
          </div>
        </div>
      </section> */}

      {/* ── CTA ── */}
      <section className={s.cta}>
        <div className={s.ctaGlow} aria-hidden />
        <div className={s.ctaContent}>
          <h2 className={s.ctaTitle}>Ready to Transform Your Document Workflow?</h2>
          <p className={s.ctaSub}>Join thousands of teams using DocOCR to save time and reduce errors.</p>
          <div className={s.ctaBtns}>
            <button className={s.btnPrimary} onClick={goApp} style={{ padding: '13px 30px', fontSize: '0.95rem' }}>
              Start Free Trial <ArrowRight size={16} />
            </button>
            <button className={s.btnGhost} style={{ padding: '12px 30px', fontSize: '0.95rem' }}>
              Book a Demo
            </button>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className={s.footer}>
        <div className={s.footerTop}>
          <div className={s.footerBrand}>
            <Link to="/" className={s.logo} style={{ marginBottom: 10 }}>
              <Hexagon size={18} strokeWidth={1.5} style={{ color: '#8b5cf6' }} />
              <span style={{ fontWeight: 900, fontSize: '0.95rem', letterSpacing: '-0.04em' }}>DocOCR</span>
            </Link>
            <p className={s.footerTagline}>AI-powered financial document extraction and intelligence platform.</p>
          </div>
          {[
            { h: 'Product',    links: ['Features', 'Dashboard', 'Analytics', 'API'] },
            { h: 'Company',    links: ['About Us', 'Careers', 'Contact Us', 'Privacy'] },
            { h: 'Support',    links: ['Help Center', 'Documentation', 'Status', 'Community'] },
          ].map(({ h, links }) => (
            <div key={h}>
              <div className={s.footerColHead}>{h}</div>
              <ul className={s.footerLinks}>
                {links.map(l => <li key={l}><a href="#">{l}</a></li>)}
              </ul>
            </div>
          ))}
        </div>
        <div className={s.footerBottom}>
          <span>© 2026 DocOCR. All rights reserved.</span>
          <span>Made with ♥ for smarter finance teams</span>
        </div>
      </footer>
    </div>
  );
}
