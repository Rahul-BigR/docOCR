<div align="center">

# DocOCR

### AI-powered OCR platform for financial documents.
Detect, extract, and understand handwritten cheques with deep learning — from raw image to structured insight.

<br />

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00B8D9?style=for-the-badge)
![TrOCR](https://img.shields.io/badge/TrOCR-HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![Flask](https://img.shields.io/badge/Flask-API-000000?style=for-the-badge&logo=flask&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-success?style=for-the-badge)

<sub>Built with ❤︎ for fintech automation.</sub>

</div>

---

## Table of Contents

1. [About the Project](#about-the-project)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [Tech Stack](#tech-stack)
5. [Model & Pipeline](#model--pipeline)
6. [Getting Started](#getting-started)
7. [Usage](#usage)
8. [API Reference](#api-reference)
9. [Project Structure](#project-structure)
10. [Roadmap](#roadmap)
11. [Contributing](#contributing)
12. [License](#license)
13. [Author](#author)

---

## About the Project

**DocOCR** is a full-stack, production-grade platform that transforms scanned or photographed financial documents particularly bank cheques into clean, structured, queryable data.

It combines a custom-trained **YOLOv8** object detector for field localization with **Microsoft TrOCR** for state-of-the-art handwritten text recognition, all wrapped in a polished React dashboard with an integrated AI chatbot for natural-language exploration of extracted records.

DocOCR is built for banks, fintech back-offices, and any team that needs to digitize paper-based financial workflows at scale — without compromising on UX or model quality.

> **Problem.** Manually processing cheques is slow, error-prone, and expensive.
> **Solution.** A single platform that ingests an image and returns audit-ready structured data in seconds.

---

## Key Features

- **End-to-End Cheque Intelligence** — extracts six core fields: Cheque Number, Account Number, IFSC Code, Amount, Date, and Payee Name.
- **Hybrid OCR Pipeline** — YOLOv8 detection → TrOCR recognition → rule-based post-processing for clean, normalized output.
- **Fallback Engine** — Tesseract-based manual pipeline available for edge cases and benchmarking.
- **AI Chatbot** — built-in intent classifier and response generator for natural-language Q&A over your processed records.
- **Authentication** — secure token-based auth (PyJWT) with persistent user store.
- **Modern Dashboard** — multi-page React SPA: Analyzer, Records, Analytics, Chatbot, Landing.
- **Real-Time Analytics** — interactive charts powered by Recharts for monitoring extraction trends.
- **GPU-Aware Inference** — automatic CUDA/CPU device selection.
- **Dual Backend** — Flask for REST + FastAPI ASGI wrapper for modern async deployments.

---

## System Architecture

```
              ┌─────────────────────────────────────────────────────────┐
              │                      DocOCR Platform                    │
              └─────────────────────────────────────────────────────────┘

  ┌───────────────────┐        ┌────────────────────┐        ┌──────────────────────┐
  │   React + Vite    │  HTTPS │   Flask / FastAPI  │  Call  │   YOLOv8 Detector    │
  │   Dashboard SPA   │ ─────▶ │   REST API Layer   │ ─────▶ │   (custom-trained)   │
  │                   │ ◀───── │   JWT · CORS · DTO │ ◀───── │                      │
  └───────────────────┘        └─────────┬──────────┘        └──────────┬───────────┘
                                         │                              │
                                         ▼                              ▼
                               ┌────────────────────┐        ┌──────────────────────┐
                               │   Chatbot Engine   │        │    TrOCR Recognizer  │
                               │  Intent + Response │        │  (handwritten model) │
                               └────────────────────┘        └──────────┬───────────┘
                                                                        │
                                                                        ▼
                                                              ┌──────────────────────┐
                                                              │  Post-Processing &   │
                                                              │  Field Normalization │
                                                              └──────────────────────┘
```

---

## Tech Stack

| Layer            | Technologies                                                                  |
| ---------------- | ----------------------------------------------------------------------------- |
| **Frontend**     | React 18 · React Router · Framer Motion · Recharts · Lucide · Axios · Vite 6  |
| **Backend**      | Flask · FastAPI (ASGI mount) · Flask-CORS · PyJWT · itsdangerous · python-dotenv |
| **Computer Vision** | Ultralytics YOLOv8 · OpenCV · Pillow                                       |
| **OCR / NLP**    | Microsoft TrOCR (HuggingFace Transformers) · Tesseract OCR · PyTorch          |
| **Chatbot**      | Custom intent classifier · Template-based response generator                  |
| **Tooling**      | Vite · ESLint · Node 18+ · Python 3.10+                                       |

---

## Model & Pipeline

### Detection — YOLOv8
A custom-trained YOLOv8 model (`best.pt`) localizes six field classes on cheque images:

```
['Cheque_Number', 'Account_Number', 'IFSC_Code', 'Amount', 'Date', 'Payee_Name']
```

Training artifacts and runs are preserved under `runs/detect/` for reproducibility.

### Recognition — TrOCR
Each detected region is cropped and fed into `microsoft/trocr-large-handwritten`, a Vision-Encoder-Decoder transformer fine-tuned for handwriting. Outputs are decoded and routed through field-specific post-processors.

### Post-Processing
`post_processing.py` applies:
- Regex-based normalization (IFSC format, account number length, currency parsing)
- Date standardization
- Confidence-weighted field aliasing
- JSON serialization for downstream consumers

### Inference Flow
```
Image → YOLOv8 detection → Crop fields → TrOCR recognition → Post-process → Structured JSON
```

---

## Getting Started

### Prerequisites

- **Python** 3.10 or higher
- **Node.js** 18 or higher
- **Tesseract OCR** (for the fallback pipeline)
- **CUDA-enabled GPU** (optional but recommended for TrOCR throughput)

### Installation

**1. Clone the repository**
```bash
git clone <repo-url>
cd docOCR
```

**2. Install Python dependencies**
```bash
pip install -r requirments.txt
```

**3. Install frontend dependencies**
```bash
npm install
```

**4. Install Tesseract OCR**

| Platform | Command |
| -------- | ------- |
| macOS    | `brew install tesseract` |
| Linux    | `sudo apt install tesseract-ocr` |
| Windows  | [Official installer](https://github.com/tesseract-ocr/tesseract/releases) |

**5. Configure environment**

Create a `.env` file at the project root:
```env
SECRET_KEY=your-secret-key-here
```

### Running the App

**Start the backend** (Flask):
```bash
python api.py
```

**Or** run via FastAPI / Uvicorn:
```bash
uvicorn backend.main:app --reload
```

**Start the frontend** (in a separate terminal):
```bash
npm run dev
```

Visit **`http://localhost:5173`**, register an account, and start uploading cheques.

---

## Usage

1. **Sign up / Sign in** through the auth flow.
2. Navigate to **Analyzer** → drag and drop a cheque image.
3. View **field-level results** with confidence overlays.
4. Browse processed documents in **Records**.
5. Explore patterns in **Analytics**.
6. Ask questions in **Chatbot**, e.g. *"How many cheques over ₹50,000 were processed this week?"*

---

## API Reference

| Method | Endpoint              | Description                              |
| ------ | --------------------- | ---------------------------------------- |
| `POST` | `/api/register`       | Register a new user                      |
| `POST` | `/api/login`          | Authenticate and receive a JWT token     |
| `POST` | `/api/analyze`        | Upload a cheque image; returns structured fields |
| `GET`  | `/api/records`        | Fetch authenticated user's processing history |
| `GET`  | `/api/analytics`      | Aggregated metrics for dashboard charts  |
| `POST` | `/api/chat`           | Send a natural-language query to the chatbot |

All authenticated endpoints expect `Authorization: Bearer <token>`.

---

## Project Structure

```
docOCR/
├── api.py                      # Flask REST API — auth, OCR, records, chat
├── backend/
│   └── main.py                 # FastAPI ASGI wrapper mounting the Flask app
├── main.py                     # Standalone YOLO + TrOCR inference script
├── post_processing.py          # Field cleanup & normalization layer
├── best.pt                     # Trained YOLOv8 weights
│
├── ocr/
│   └── Manual/                 # Tesseract-based fallback pipeline
│       ├── extract.py
│       ├── preprocess.py
│       └── parser/
│
├── chatbot/
│   ├── intent_clfr.py          # Intent classification
│   └── response_gentr.py       # Response generation
│
├── runs/detect/                # YOLO training runs & metrics
├── dataset/                    # Training & test data
├── detected_fields/            # Cropped field outputs
├── ocr_results/                # Raw OCR text outputs
├── final_output_json/          # Structured JSON per document
│
├── src/                        # React frontend
│   ├── App.jsx
│   ├── main.jsx
│   ├── components/             # Shared UI (Layout, etc.)
│   ├── pages/                  # Landing, Auth, Analyzer, Records, Analytics, Chatbot
│   ├── hooks/                  # useAuth, etc.
│   └── lib/api.js              # Axios client
│
├── package.json
├── vite.config.js
├── requirments.txt
└── README.md
```

---

## Roadmap

- [ ] Multi-document support (invoices, passbooks, statements)
- [ ] Multilingual handwriting recognition
- [ ] Bulk batch processing via queue worker
- [ ] Cloud deployment templates (Docker + AWS / GCP)
- [ ] Role-based access control
- [ ] Webhook integrations for downstream systems
- [ ] Mobile-first responsive overhaul

---

## License

Distributed under the **MIT License**. See [`LICENSE`](./LICENSE) for the full text.

```
Copyright (c) 2026 Rahul and Kumud 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
```

---

## Author

<div align="center">

### Built by

<a href="https://github.com/Kumud-hasija">Kumud Hasija</a> •
<a href="https://github.com/Rahul-BigR">Rahul Rao</a> •
<a href="https://github.com/Vaibhav0410">Vaibhav Sheoran</a>

*Building AI products that make financial workflows effortless.*

<br>

[![Kumud](https://img.shields.io/badge/GitHub-Kumud--hasija-181717?style=flat-square&logo=github)](https://github.com/Kumud-hasija)
[![Rahul](https://img.shields.io/badge/GitHub-Rahul--BigR-181717?style=flat-square&logo=github)](https://github.com/Rahul-BigR)
[![Vaibhav](https://img.shields.io/badge/GitHub-Vaibhav--Sheoran-181717?style=flat-square&logo=github)](https://github.com/Vaibhav0410)



</div>

---

<div align="center">

<sub>If DocOCR helped you, consider giving the repo a ⭐</sub>

</div>
