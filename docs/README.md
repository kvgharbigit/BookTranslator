# 📚 EPUB Translator Documentation

Welcome to the complete documentation for the EPUB Translator - a professional, production-ready translation service.

## 📋 Documentation Index

### Getting Started
- [Quick Start Guide](./quick-start.md) - Get up and running in 15 minutes
- [Installation Guide](./installation.md) - Complete setup instructions
- [Configuration](./configuration.md) - Environment variables and settings

### User Guides
- [API Reference](./api-reference.md) - Complete API documentation
- [Translation Pipeline](./translation-pipeline.md) - How translations work
- [Enhanced PDF Generation](./pdf-generation.md) - Professional PDF output with image preservation
- [Payment System](./payment-system.md) - Dual provider payment routing

### Development
- [Project Structure](./project-structure.md) - Codebase organization
- [Testing Guide](./testing.md) - Running tests and validation
- [Contributing](./contributing.md) - Development guidelines

### Deployment
- [Production Deployment](./deployment.md) - Railway, Vercel, and Docker
- [Security Guide](./security.md) - Best practices and considerations
- [Monitoring](./monitoring.md) - Health checks and maintenance

### Future Development
- [Roadmap](./roadmap.md) - Planned features and enhancements
- [Architecture Decisions](./architecture.md) - Design principles and rationale

## 🚀 Quick Navigation

**Just want to test it?** → [Quick Start Guide](./quick-start.md)  
**Ready for production?** → [Production Deployment](./deployment.md)  
**Need API docs?** → [API Reference](./api-reference.md)  
**Planning features?** → [Roadmap](./roadmap.md)

## 🏗️ Project Overview

The EPUB Translator is a complete translation service featuring:

- **Ultra-fast processing** with Gemini 2.5 Flash-Lite (Tier 1: 3.2K safe RPM)
- **Fast translation time** - 3-5 minutes for 200-page novel (80K words)
- **Smart payment routing** between PayPal micropayments and Stripe
- **Enhanced multi-format output** (EPUB + high-quality PDF with images + TXT)
- **Automatic failover** (Gemini → Groq Llama when needed)
- **Mobile-responsive UI** with real-time progress tracking
- **Production-ready** with monitoring, rate limiting, and security

## 💰 Business Model

- **$0.50 minimum** per translation
- **95-99% profit margins** with optimized provider costs
- **Auto-optimized payment fees** (PayPal for small amounts, Stripe for larger)
- **$10/month fixed costs** (Railway + R2 storage)

## 🔧 Technology Stack

**Backend:** FastAPI + Redis/RQ + SQLite  
**Frontend:** Next.js + Tailwind CSS  
**AI:** Gemini 2.5 Flash-Lite + Groq Llama 3.1 8B  
**Payments:** Stripe + PayPal Micropayments  
**Storage:** Cloudflare R2  
**Deployment:** Railway + Vercel

---

*For support or questions, see the individual documentation pages or check the troubleshooting section in the Quick Start Guide.*