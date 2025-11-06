# Changelog

All notable changes to BookTranslator will be documented in this file.

## [1.1.0] - 2025-11-06

### 🌍 Language Support Optimization

#### Added
- **Thai (th)** now supported with Gemini (moved from failed Llama)
- **Turkish (tr)** now supported with Gemini (moved from failed Llama)
- **Finnish (fi)** now supported with Gemini (moved from failed Llama)
- **Latvian (lv)** timeout issue fixed - now works reliably on Gemini
- Comprehensive language testing infrastructure (41 languages tested)
- Translation quality reports and documentation

#### Changed
- **Language count:** 42 → 41 languages (Ukrainian removed)
- **Tier 4 (Gemini) languages:** 13 → 16 (+3 moved from Llama)
- **Tier 2 (Llama) languages:** 10 → 7 (-3 moved to Gemini)
- **Tier 3 (Llama) languages:** 11 → 8 (-3 moved/removed)
- Preview translation timeout increased: 120s → 180s for better Gemini support
- Updated language tier assignments based on comprehensive quality testing

#### Removed
- **Ukrainian (uk)** - Removed from supported languages
  - Reason: Complete translation failure on both Llama and Gemini providers
  - Status: May be re-added in future if provider support improves

### 📊 Quality Improvements

#### Test Results
- **Overall success rate:** 100% (41/41 working languages)
- **Thai quality:** Failed → FAIR (proper Thai script now rendered)
- **Turkish quality:** Failed → GOOD (complete Turkish translation)
- **Finnish quality:** Failed → GOOD (complete Finnish translation)
- **Latvian performance:** Timeout → 10.6s (fixed with timeout increase)

#### Performance
- **Preview generation:**
  - Tier 1-3 (Llama): 19-68s average
  - Tier 4 (Gemini): 6-85s average
- **Translation quality:**
  - Grade A (9.0-10): 32% of languages
  - Grade B (7.5-8.9): 32% of languages
  - Grade C (6.0-7.4): 27% of languages
  - Grade D-F (0-5.9): 10% of languages

### 🔧 Technical Changes

#### Backend
- `apps/api/app/pipeline/translate.py`: Updated `gemini_only_languages` set
- `apps/api/app/pipeline/preview.py`: Removed Ukrainian progress messages
- Translation timeout increased for better Gemini compatibility

#### Frontend
- `apps/web/src/lib/languages.ts`: Reduced from 42 to 41 languages
- Removed Ukrainian from language selector

### 📝 Documentation

#### Added
- `TRANSLATION_QUALITY_REPORT.md` - Comprehensive language-by-language quality analysis
- `FINAL_LANGUAGE_CONFIGURATION.md` - Production-ready language configuration
- `CHANGELOG.md` - This file

#### Updated
- `README.md` - Updated language count from "50+" to "41"
- `README.md` - Added detailed supported languages section with tier breakdown

### 🧪 Testing

#### Test Coverage
- Created `test_all_languages.py` - Comprehensive 41-language test suite
- Created `test_failing_languages.py` - Targeted retest for problematic languages
- Test results saved in `/test_results/` directory
- All 41 languages verified working in production configuration

---

## [1.0.0] - 2025-11-05

### Initial Production Release

#### Features
- EPUB translation to 42 languages
- PayPal micropayments integration
- Cloudflare R2 storage (5-day retention)
- Real-time translation progress tracking
- Multi-format output (EPUB + PDF + TXT)
- Email delivery with download links
- Dual-provider AI strategy (Gemini + Groq)
- Free 250-word preview translations

#### Infrastructure
- Railway backend deployment
- Vercel frontend deployment
- PostgreSQL database
- Redis queue with RQ worker
- Resend email notifications

---

## Version History

- **v1.1.0** (2025-11-06) - Language optimization, Ukrainian removal, quality improvements
- **v1.0.0** (2025-11-05) - Initial production release

---

## Upgrade Notes

### From 1.0.0 to 1.1.0

**Breaking Changes:**
- Ukrainian (uk) is no longer supported
- Preview timeout increased to 180s (may affect API clients with strict timeouts)

**Non-Breaking Changes:**
- Thai, Turkish, and Finnish now use Gemini (improved quality, slightly slower)
- Language tier assignments updated (transparent to users)

**Recommended Actions:**
1. Update any hardcoded language lists to remove Ukrainian
2. Increase API timeout settings if calling preview endpoint
3. Clear any cached language lists in frontend applications
4. Update documentation/marketing materials to reflect 41 languages

---

## Future Roadmap

### Planned for v1.2.0
- [ ] Investigate Ukrainian translation issues (re-enable if possible)
- [ ] Improve Tamil and Urdu translation quality
- [ ] Optimize Greek translation speed (currently 67.5s)
- [ ] Add translation quality monitoring dashboard
- [ ] Implement A/B testing for borderline languages

### Under Consideration
- [ ] Add Traditional Chinese support
- [ ] Add Simplified Chinese variants (Hong Kong, Singapore)
- [ ] Support for more Indic languages (Marathi, Kannada)
- [ ] Support for African languages (Swahili, Afrikaans)
- [ ] Support for more European languages (Albanian, Macedonian)

---

For detailed technical information, see:
- Quality Report: `TRANSLATION_QUALITY_REPORT.md`
- Configuration: `FINAL_LANGUAGE_CONFIGURATION.md`
- Deployment: `DEPLOYMENT.md`
