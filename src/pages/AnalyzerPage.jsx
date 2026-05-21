// import React, { useState, useRef } from 'react';
// import api from '../lib/api';
// import {
//   Upload, FileImage, Loader2, CheckCircle2, AlertCircle,
//   Hash, CreditCard, Landmark, IndianRupee, Calendar, User,
//   Download, RotateCcw, X
// } from 'lucide-react';
// import styles from './AnalyzerPage.module.css';

// const FIELD_META = [
//   { key: 'cheque_number',  label: 'Cheque Number',  icon: Hash,          color: '#818cf8' },
//   { key: 'account_number', label: 'Account Number', icon: CreditCard,    color: '#34d399' },
//   { key: 'ifsc_code',      label: 'IFSC Code',      icon: Landmark,      color: '#60a5fa' },
//   { key: 'amount',         label: 'Amount (₹)',     icon: IndianRupee,   color: '#f59e0b' },
//   { key: 'date',           label: 'Date',           icon: Calendar,      color: '#f472b6' },
//   { key: 'payee_name',     label: 'Payee Name',     icon: User,          color: '#a78bfa' },
// ];

// function normalizeResult(data) {
//   const result = {};
//   const keyMap = {
//     'cheque_number': ['cheque_number', 'Cheque_Number', 'chequenumber'],
//     'account_number': ['account_number', 'Account_Number', 'accountnumber'],
//     'ifsc_code': ['ifsc_code', 'IFSC_Code', 'ifsccode', 'ifsc'],
//     'amount': ['amount', 'Amount'],
//     'date': ['date', 'Date'],
//     'payee_name': ['payee_name', 'Payee_Name', 'payeename'],
//   };
//   for (const [std, alts] of Object.entries(keyMap)) {
//     for (const alt of alts) {
//       if (data[alt]) { result[std] = data[alt]; break; }
//     }
//     if (!result[std]) result[std] = '';
//   }
//   return result;
// }

// export default function AnalyzerPage() {
//   const [file, setFile] = useState(null);
//   const [preview, setPreview] = useState(null);
//   const [status, setStatus] = useState('idle'); // idle | processing | done | error
//   const [result, setResult] = useState(null);
//   const [errorMsg, setErrorMsg] = useState('');
//   const [dragging, setDragging] = useState(false);
//   const inputRef = useRef();

//   const handleFile = (f) => {
//     if (!f) return;
//     setFile(f);
//     setStatus('idle');
//     setResult(null);
//     setErrorMsg('');
//     const url = URL.createObjectURL(f);
//     setPreview(url);
//   };

//   const handleDrop = (e) => {
//     e.preventDefault();
//     setDragging(false);
//     const f = e.dataTransfer.files[0];
//     if (f) handleFile(f);
//   };

//   const handleProcess = async () => {
//     if (!file) return;
//     setStatus('processing');
//     setResult(null);
//     setErrorMsg('');
//     const formData = new FormData();
//     formData.append('file', file);
//     try {
//       const res = await api.post('/process', formData, {
//         headers: { 'Content-Type': 'multipart/form-data' },
//       });
//       setResult(normalizeResult(res.data.data));
//       setStatus('done');
//     } catch (err) {
//       setErrorMsg(err.response?.data?.error || 'Processing failed. Please try again.');
//       setStatus('error');
//     }
//   };

//   const handleReset = () => {
//     setFile(null);
//     setPreview(null);
//     setStatus('idle');
//     setResult(null);
//     setErrorMsg('');
//     if (inputRef.current) inputRef.current.value = '';
//   };

//   const handleDownload = () => {
//     if (!result) return;
//     const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
//     const url = URL.createObjectURL(blob);
//     const a = document.createElement('a');
//     a.href = url;
//     a.download = `${file?.name?.replace(/\.[^.]+$/, '') || 'result'}_ocr.json`;
//     a.click();
//     URL.revokeObjectURL(url);
//   };

//   return (
//     <div className={styles.page}>
//       <div className={styles.header}>
//         <div>
//           <h1 className={styles.title}>Document Analyzer</h1>
//           <p className={styles.subtitle}>Upload a cheque image to extract financial data using AI</p>
//         </div>
//         {(file || result) && (
//           <button className={styles.resetBtn} onClick={handleReset}>
//             <RotateCcw size={15} /> New Document
//           </button>
//         )}
//       </div>

//       <div className={styles.grid}>
//         {/* Upload zone */}
//         <div className={styles.uploadSection}>
//           <div
//             className={`${styles.dropzone} ${dragging ? styles.dropzoneDragging : ''} ${file ? styles.dropzoneHasFile : ''}`}
//             onDragOver={e => { e.preventDefault(); setDragging(true); }}
//             onDragLeave={() => setDragging(false)}
//             onDrop={handleDrop}
//             onClick={() => !file && inputRef.current?.click()}
//           >
//             <input
//               ref={inputRef}
//               type="file"
//               accept="image/*,.tif,.tiff"
//               style={{ display: 'none' }}
//               onChange={e => handleFile(e.target.files[0])}
//             />

//             {preview ? (
//               <div className={styles.previewContainer}>

//                 <img
//                   src={preview}
//                   alt="Uploaded Cheque"
//                   className={styles.previewImg}
//                 />

//                 {status === 'processing' && (
//                   <>
//                     <div className={styles.scanOverlay} />

//                     <div className={styles.scanLine} />

//                     <div className={styles.processingBadge}>
//                       <Loader2 size={14} className={styles.spin} />
//                       Processing Cheque...
//                     </div>
//                   </>
//                 )}

//                 <button
//                   className={styles.removeFileBtn}
//                   onClick={(e) => {
//                     e.stopPropagation();
//                     handleReset();
//                   }}
//                 >
//                   <X size={14} />
//                 </button>

//               </div>
//             ) : (
//               <div className={styles.dropzoneContent}>
//                 <div className={styles.dropzoneIcon}>
//                   <FileImage size={36} strokeWidth={1.5} />
//                 </div>
//                 <p className={styles.dropzoneTitle}>Drop your cheque here</p>
//                 <p className={styles.dropzoneHint}>or click to browse — JPG, PNG, TIF supported</p>
//               </div>
//             )}
//           </div>

//           {file && (
//             <div className={styles.fileInfo}>
//               <div className={styles.fileName}>
//                 <FileImage size={15} style={{ color: 'var(--indigo)' }} />
//                 <span>{file.name}</span>
//               </div>
//               <span className={styles.fileSize}>{(file.size / 1024).toFixed(0)} KB</span>
//             </div>
//           )}

//           <button
//             className={styles.processBtn}
//             onClick={handleProcess}
//             disabled={!file || status === 'processing'}
//           >
//             {status === 'processing' ? (
//               <><Loader2 size={17} className={styles.spin} /> Processing...</>
//             ) : (
//               <><Upload size={17} /> Analyze Document</>
//             )}
//           </button>

//           {status === 'processing' && (
//             <div className={styles.progressBox}>
//               <div className={styles.progressBar}>
//                 <div className={styles.progressFill} />
//               </div>
//               <p className={styles.progressLabel}>Running YOLO field detection + TrOCR...</p>
//             </div>
//           )}
//         </div>

//         {/* Results */}
//         <div className={styles.resultsSection}>
//           {status === 'idle' && !result && (
//             <div className={styles.placeholder}>
//               <div className={styles.placeholderIcon}>
//                 <FileImage size={48} strokeWidth={1} />
//               </div>
//               <p className={styles.placeholderTitle}>Results will appear here</p>
//               <p className={styles.placeholderHint}>Upload and analyze a cheque to see extracted fields</p>
//             </div>
//           )}

//           {status === 'error' && (
//             <div className={styles.errorBox}>
//               <AlertCircle size={20} />
//               <div>
//                 <p className={styles.errorTitle}>Processing Failed</p>
//                 <p className={styles.errorMsg}>{errorMsg}</p>
//               </div>
//             </div>
//           )}

//           {status === 'done' && result && (
//             <div className={styles.resultCard}>
//               <div className={styles.resultHeader}>
//                 <div className={styles.resultHeaderLeft}>
//                   <CheckCircle2 size={18} style={{ color: 'var(--green)' }} />
//                   <span className={styles.resultTitle}>Extraction Complete</span>
//                 </div>
//                 <button className={styles.downloadBtn} onClick={handleDownload}>
//                   <Download size={14} /> Export JSON
//                 </button>
//               </div>

//               <div className={styles.fieldsGrid}>
//                 {FIELD_META.map(({ key, label, icon: Icon, color }) => {
//                   const val = result[key];
//                   const hasVal = val && val !== '' && val !== 'Not found';
//                   return (
//                     <div className={styles.fieldItem} key={key}>
//                       <div className={styles.fieldIcon} style={{ background: `${color}18`, color }}>
//                         <Icon size={16} strokeWidth={2} />
//                       </div>
//                       <div className={styles.fieldBody}>
//                         <div className={styles.fieldLabel}>{label}</div>
//                         <div className={`${styles.fieldValue} mono`}>
//                           {hasVal ? val : <span className={styles.fieldEmpty}>Not detected</span>}
//                         </div>
//                       </div>
//                       <div className={`${styles.fieldStatus} ${hasVal ? styles.fieldStatusOk : styles.fieldStatusMiss}`} />
//                     </div>
//                   );
//                 })}
//               </div>
//             </div>
//           )}
//         </div>
//       </div>
//     </div>
//   );
// }

import React, { useState, useRef } from 'react';
import api from '../lib/api';
import {
  Upload, FileImage, Loader2, CheckCircle2, AlertCircle,
  Hash, CreditCard, Landmark, IndianRupee, Calendar, User,
  Download, RotateCcw, X
} from 'lucide-react';
import styles from './AnalyzerPage.module.css';

const FIELD_META = [
  { key: 'cheque_number',  label: 'Cheque Number',  icon: Hash,          color: '#818cf8' },
  { key: 'account_number', label: 'Account Number', icon: CreditCard,    color: '#34d399' },
  { key: 'ifsc_code',      label: 'IFSC Code',      icon: Landmark,      color: '#60a5fa' },
  { key: 'amount',         label: 'Amount (₹)',     icon: IndianRupee,   color: '#f59e0b' },
  { key: 'date',           label: 'Date',           icon: Calendar,      color: '#f472b6' },
  { key: 'payee_name',     label: 'Payee Name',     icon: User,          color: '#a78bfa' },
];

function normalizeResult(data) {
  const result = {};
  const keyMap = {
    'cheque_number': ['cheque_number', 'Cheque_Number', 'chequenumber'],
    'account_number': ['account_number', 'Account_Number', 'accountnumber'],
    'ifsc_code': ['ifsc_code', 'IFSC_Code', 'ifsccode', 'ifsc'],
    'amount': ['amount', 'Amount'],
    'date': ['date', 'Date'],
    'payee_name': ['payee_name', 'Payee_Name', 'payeename'],
  };
  for (const [std, alts] of Object.entries(keyMap)) {
    for (const alt of alts) {
      if (data[alt]) { result[std] = data[alt]; break; }
    }
    if (!result[std]) result[std] = '';
  }
  return result;
}

export default function AnalyzerPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | processing | done | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const handleFile = (f) => {
    if (!f) return;
    setFile(f);
    setStatus('idle');
    setResult(null);
    setErrorMsg('');
    const url = URL.createObjectURL(f);
    setPreview(url);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleProcess = async () => {
    if (!file) return;
    setStatus('processing');
    setResult(null);
    setErrorMsg('');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await api.post('/process', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(normalizeResult(res.data.data));
      setStatus('done');
    } catch (err) {
      setErrorMsg(err.response?.data?.error || 'Processing failed. Please try again.');
      setStatus('error');
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setStatus('idle');
    setResult(null);
    setErrorMsg('');
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleDownload = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${file?.name?.replace(/\.[^.]+$/, '') || 'result'}_ocr.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Document Analyzer</h1>
          <p className={styles.subtitle}>Upload a cheque image to extract financial data using AI</p>
        </div>
        {(file || result) && (
          <button className={styles.resetBtn} onClick={handleReset}>
            <RotateCcw size={15} /> New Document
          </button>
        )}
      </div>

      <div className={styles.grid}>
        {/* Upload zone */}
        <div className={styles.uploadSection}>
          <div
            className={`${styles.dropzone} ${dragging ? styles.dropzoneDragging : ''} ${file ? styles.dropzoneHasFile : ''}`}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => !file && inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept="image/*,.tif,.tiff"
              style={{ display: 'none' }}
              onChange={e => handleFile(e.target.files[0])}
            />

            {preview ? (
              <div className={styles.previewContainer}>

                <img
                  src={preview}
                  alt="Uploaded Cheque"
                  className={styles.previewImg}
                />

                {status === 'processing' && (
                  <>
                    <div className={styles.scanOverlay} />

                    <div className={styles.scanLine} />

                    <div className={styles.processingBadge}>
                      <Loader2 size={14} className={styles.spin} />
                      Processing Cheque...
                    </div>
                  </>
                )}

                <button
                  className={styles.removeFileBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleReset();
                  }}
                >
                  <X size={14} />
                </button>

              </div>
            ) : (
              <div className={styles.dropzoneContent}>
                <div className={styles.dropzoneIcon}>
                  <FileImage size={36} strokeWidth={1.5} />
                </div>
                <p className={styles.dropzoneTitle}>Drop your cheque here</p>
                <p className={styles.dropzoneHint}>or click to browse — JPG, PNG, TIF supported</p>
              </div>
            )}
          </div>

          {file && (
            <div className={styles.fileInfo}>
              <div className={styles.fileName}>
                <FileImage size={15} style={{ color: 'var(--indigo)' }} />
                <span>{file.name}</span>
              </div>
              <span className={styles.fileSize}>{(file.size / 1024).toFixed(0)} KB</span>
            </div>
          )}

          <button
            className={styles.processBtn}
            onClick={handleProcess}
            disabled={!file || status === 'processing'}
          >
            {status === 'processing' ? (
              <><Loader2 size={17} className={styles.spin} /> Processing...</>
            ) : (
              <><Upload size={17} /> Analyze Document</>
            )}
          </button>

          {status === 'processing' && (
            <div className={styles.progressBox}>
              <div className={styles.progressBar}>
                <div className={styles.progressFill} />
              </div>
              <p className={styles.progressLabel}>Running YOLO field detection + TrOCR...</p>
            </div>
          )}
        </div>

        {/* Results */}
        <div className={styles.resultsSection}>
          {status === 'idle' && !result && (
            <div className={styles.placeholder}>
              <div className={styles.placeholderIcon}>
                <FileImage size={48} strokeWidth={1} />
              </div>
              <p className={styles.placeholderTitle}>Results will appear here</p>
              <p className={styles.placeholderHint}>Upload and analyze a cheque to see extracted fields</p>
            </div>
          )}

          {status === 'error' && (
            <div className={styles.errorBox}>
              <AlertCircle size={20} />
              <div>
                <p className={styles.errorTitle}>Processing Failed</p>
                <p className={styles.errorMsg}>{errorMsg}</p>
              </div>
            </div>
          )}

          {status === 'done' && result && (
            <div className={styles.resultCard}>
              <div className={styles.resultHeader}>
                <div className={styles.resultHeaderLeft}>
                  <CheckCircle2 size={18} style={{ color: 'var(--green)' }} />
                  <span className={styles.resultTitle}>Extraction Complete</span>
                </div>
                <button className={styles.downloadBtn} onClick={handleDownload}>
                  <Download size={14} /> Export JSON
                </button>
              </div>

              <div className={styles.fieldsGrid}>
                {FIELD_META.map(({ key, label, icon: Icon, color }) => {
                  const val = result[key];
                  const hasVal = val && val !== '' && val !== 'Not found';
                  return (
                    <div className={styles.fieldItem} key={key}>
                      <div className={styles.fieldIcon} style={{ background: `${color}18`, color }}>
                        <Icon size={16} strokeWidth={2} />
                      </div>
                      <div className={styles.fieldBody}>
                        <div className={styles.fieldLabel}>{label}</div>
                        <div className={`${styles.fieldValue} mono`}>
                          {hasVal ? val : <span className={styles.fieldEmpty}>Not detected</span>}
                        </div>
                      </div>
                      <div className={`${styles.fieldStatus} ${hasVal ? styles.fieldStatusOk : styles.fieldStatusMiss}`} />
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
