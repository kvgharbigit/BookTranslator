# 📁 Project Structure

## 🏗️ Directory Organization

```
BookTranslator/
├── 📖 docs/                    # Documentation
│   ├── README.md               # Documentation index
│   ├── quick-start.md          # 15-minute setup guide
│   ├── installation.md        # Detailed installation
│   ├── deployment.md           # Production deployment
│   └── roadmap.md             # Future features (dual readers!)
│
├── 🖥️ apps/                    # Application code
│   ├── api/                   # FastAPI backend
│   │   ├── app/
│   │   │   ├── pipeline/      # Translation pipeline
│   │   │   │   ├── epub_io.py         # EPUB read/write
│   │   │   │   ├── html_segment.py    # Content segmentation
│   │   │   │   ├── translate.py       # Translation orchestration
│   │   │   │   └── placeholders.py    # Content protection
│   │   │   ├── providers/     # AI provider integrations
│   │   │   │   ├── gemini.py          # Gemini 2.5 Flash-Lite
│   │   │   │   └── groq.py            # Groq Llama 3.1 8B
│   │   │   ├── routes/        # API endpoints
│   │   │   │   ├── estimate.py        # Price estimation
│   │   │   │   ├── checkout.py        # Payment processing
│   │   │   │   └── jobs.py            # Job management
│   │   │   ├── main.py        # FastAPI app
│   │   │   ├── config.py      # Settings
│   │   │   ├── pricing.py     # Smart cost calculation
│   │   │   └── models.py      # Database models
│   │   ├── data/              # SQLite database
│   │   └── Dockerfile         # Container config
│   │
│   └── web/                   # Next.js frontend
│       ├── src/
│       │   ├── app/           # App router pages
│       │   └── components/    # React components
│       ├── package.json       # Dependencies
│       └── tailwind.config.js # Styling
│
├── 🧪 tests/                   # Test files
│   └── test_dual_provider_comparison.py  # Enhanced provider testing with PDF validation
│
├── 🛠️ scripts/                 # Utility scripts
│   ├── start-backend.sh       # Launch API server
│   ├── start-worker.sh        # Launch RQ worker
│   ├── start-frontend.sh      # Launch Next.js
│   ├── test-api.sh           # API testing
│   └── analyze_epub.py       # EPUB inspection
│
├── 📚 sample_books/            # Test EPUB files
│   ├── Sway.epub             # Short story
│   └── pg236-images.epub     # Full book with images
│
├── 📦 outputs/                 # Translation results
│   ├── gemini/               # Gemini provider outputs
│   ├── llama/                # Llama provider outputs
│   └── sample/               # Sample translations
│
├── 🎯 Enhanced PDF Generation
├── epub_to_pdf_with_images.py    # Multi-method PDF converter (Calibre/WeasyPrint/ReportLab)
├── comprehensive_pdf_test.py     # PDF generation test suite
│
├── 📄 Configuration Files
├── README.md                 # Project overview
├── .env                      # Environment variables
├── env.example              # Environment template
└── .gitignore               # Git exclusions
```

## 🔧 Key Components

### Translation Pipeline (`apps/api/app/pipeline/`)
- **epub_io.py**: EPUB reading/writing with security validation
- **html_segment.py**: Smart content segmentation preserving structure
- **translate.py**: Orchestrates provider selection and fallback
- **placeholders.py**: Protects URLs, tags, and special content

### AI Providers (`apps/api/app/providers/`)
- **gemini.py**: Gemini 2.5 Flash-Lite (primary, 4K RPM)
- **groq.py**: Groq Llama 3.1 8B (fallback, 30 RPM)
- **base.py**: Provider interface and error handling

### Payment System (`apps/api/app/routes/`)
- **estimate.py**: Smart token estimation and pricing
- **checkout.py**: Dual provider routing (PayPal vs Stripe)
- **paypal.py**: PayPal micropayments integration

### Frontend (`apps/web/src/`)
- **app/page.tsx**: Upload interface with drag-and-drop
- **components/FileDrop.tsx**: File upload component
- **components/PriceBox.tsx**: Dynamic pricing display
- **components/ProgressPoller.tsx**: Real-time progress tracking

## 🚀 Development Workflow

### Local Development
```bash
# 1. Start services (3 terminals)
./scripts/start-backend.sh   # API server
./scripts/start-worker.sh    # Job processor  
./scripts/start-frontend.sh  # UI

# 2. Test changes
cd tests && python test_dual_provider_comparison.py

# 3. Verify functionality
curl http://localhost:8000/health
open http://localhost:3000
```

### Testing Strategy
- **Unit tests**: Individual component testing
- **Integration tests**: Full pipeline with real providers
- **Performance tests**: Speed and cost benchmarking
- **Security tests**: EPUB validation and injection prevention

### Deployment Pipeline
1. **Development**: Local testing with scripts
2. **Staging**: Railway preview deployments
3. **Production**: Railway + Vercel with monitoring

## 📊 Data Flow

```
User Upload → R2 Storage → Job Queue → Translation Pipeline → Multi-format Output → Email Notification
     ↓              ↓           ↓              ↓                    ↓                 ↓
File Validation → Pricing → Worker Pick-up → AI Processing → EPUB/PDF/TXT → Download Links
```

## 🔒 Security Layers

1. **File Validation**: EPUB structure and zip bomb protection
2. **Rate Limiting**: Per-IP upload restrictions
3. **Content Sanitization**: HTML/XHTML cleaning
4. **Token Limits**: Maximum job size enforcement
5. **Auto-cleanup**: 7-day file deletion

## 🎯 Performance Optimization

- **Provider Selection**: Fastest available (Gemini → Groq)
- **Batch Processing**: Optimal token batch sizes
- **Caching**: Redis for job state and results
- **CDN**: Cloudflare R2 for global file delivery
- **Monitoring**: Health checks and error tracking

## 🔄 Future Architecture (Dual Readers)

```
Current: Upload → Translate → Download
Future:  Upload → Translate → Read → Compare → Export

New Components:
├── 📖 apps/reader/            # Reading interface
│   ├── components/ReaderView  # Dual-pane display
│   ├── services/SyncService   # Paragraph alignment
│   └── hooks/useProgress      # Reading state
└── 🔄 apps/api/reader/        # Reader API
    ├── alignment.py           # Text synchronization
    └── export.py              # Dual-language export
```

This architecture supports the roadmap goal of creating **dual-language readers** for enhanced user experience and premium revenue streams.

---

*For detailed setup instructions, see [quick-start.md](./quick-start.md)*