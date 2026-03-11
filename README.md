# arXiv Research Aggregator

> **Brevity Note:** This documentation follows a "Signal-over-Noise" protocol. Technical accuracy and security are prioritized over marketing fluff.

---

## 1. Executive Summary

A Python-based web application that automatically fetches, processes, and publishes research papers from arXiv across multiple computer science domains (AI, Machine Learning, Computer Vision, Robotics, Cryptography/Security, and HCI).

- **Core Value:** Automates discovery and publishing of CS research papers with AI-enhanced content and contextual imagery.
- **Primary Stakeholders:** Researchers, developers, and tech enthusiasts who want curated research paper feeds.

**Version:** 0.1.0 | **License:** MIT | **Python:** 3.13+

---

## 2. Architecture

```
myArxivAggregator/
├── src/arxiv_aggregator/          # Core package
│   ├── __init__.py
│   ├── config.py                  # Configuration & credential validation
│   ├── content_utils.py           # AI content generation & XSS sanitization
│   ├── core.py                    # BaseAggregator class (DRY pattern)
│   ├── featured_tracker.py        # Featured article selection logic
│   ├── generate_html.py           # HTML generation utilities
│   └── templates/                  # HTML templates
│       ├── base_template.html
│       ├── ml_template.html
│       ├── cv_template.html
│       ├── ro_template.html
│       ├── cr_template.html
│       └── hc_template.html
├── aggregator.py                   # AI Research (cs.AI) - entry point
├── aggregator_ml.py                # Machine Learning (cs.LG)
├── aggregator_cv.py                # Computer Vision (cs.CV)
├── aggregator_ro.py                # Robotics (cs.RO)
├── aggregator_cr.py                # Cryptography/Security (cs.CR)
├── aggregator_hc.py                # Human-Computer Interaction (cs.HC)
├── run_all_aggregators.py          # Batch orchestration script
├── tests/                          # Comprehensive test suite
│   ├── conftest.py                # Pytest fixtures & mocks
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── security/                  # Security tests (input validation)
├── typings/                        # Type stubs for external packages
├── pyproject.toml                  # Project metadata & UV workspace config
├── uv.lock                          # Locked dependency versions (UV)
├── .env.example                    # Environment template
└── LICENSE                         # MIT License
```

### Design Decisions

- **DRY Pattern:** [`BaseAggregator`](src/arxiv_aggregator/core.py:23) in [`core.py`](src/arxiv_aggregator/core.py) eliminates code duplication across category-specific aggregators.
- **Runtime Credential Validation:** [`validate_credentials()`](src/arxiv_aggregator/config.py:43) defers credential checks until needed, avoiding import-time failures.
- **XSS Defense-in-Depth:** Content sanitization in [`content_utils.py`](src/arxiv_aggregator/content_utils.py:34) combined with [`html.escape()`](src/arxiv_aggregator/generate_html.py) in output generation.

---

## 3. Security & Ethics

### API/Secret Handling

- **Environment Variables:** All secrets loaded from `.env` at runtime. Never commit actual credentials.
- **Template:** See [`.env.example`](.env.example) for required variables.

### Attack Vector Mitigation

| Vector | Mitigation |
|--------|------------|
| **XSS** | Content sanitization in [`clean_generated_text()`](src/arxiv_aggregator/content_utils.py:34) + HTML escaping in [`generate_html.py`](src/arxiv_aggregator/generate_html.py) |
| **Credential Exposure** | Runtime validation; credentials not stored in code |
| **API Rate Limiting** | Handled via try/except with graceful degradation |

### Ethical Bound

This tool is designed for educational and research purposes. Users must:
- Respect arXiv's [terms of service](https://arxiv.org/help/policies) and API rate limits
- Comply with Unsplash [API guidelines](https://unsplash.com/documentation# attribution-requirements)
- Not use this tool to generate harmful content

---

## 4. Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.13+ | See [`pyproject.toml`](pyproject.toml) |
| [UV](https://github.com/astral-sh/uv) | Latest | All-in-one Python package manager (venv + deps + scripts) |
| Ollama | Latest | Local LLM for content generation. Install from [ollama.ai](https://ollama.ai) |
| FTP Server | — | For publishing generated HTML |
| Unsplash API | — | For contextual imagery |

### Ollama Setup

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required model
ollama pull llama3.1:8b
```

### UV Commands

UV provides an all-in-one workflow for this project:

```bash
# Create venv and install all dependencies
uv venv
uv sync

# Add a new dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>

# Update dependencies
uv sync --upgrade

# Run scripts defined in pyproject.toml
uv run <script-name>

# Run tests with pytest
uv run pytest

# Run linting with ruff
uv run ruff check .
uv run ruff format .
```

**Note:** The project uses [`uv.lock`](uv.lock) for reproducible builds.

---

## 5. Installation

```bash
# Clone repository
git clone https://github.com/AlexJ-StL/myArxivAggregator.git
cd myArxivAggregator

# Create virtual environment and install dependencies with UV
uv venv
uv sync

# Activate virtual environment (optional - UV auto-activates in session)
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dev dependencies (linting, formatting)
uv sync --dev
```

---

## 6. Configuration

### Environment Variables

Copy [`.env.example`](.env.example) to `.env` and configure:

```bash
cp .env.example .env
```

| Variable | Description | Required |
|----------|-------------|----------|
| `FTP_HOST` | FTP server hostname | Yes |
| `FTP_USER` | FTP username | Yes |
| `FTP_PASS` | FTP password | Yes |
| `FTP_REMOTE_DIR` | Remote directory | No (default: `.`) |
| `UNSPLASH_ACCESS_KEY` | Unsplash API access key | Yes |
| `UNSPLASH_SECRET_KEY` | Unsplash API secret key | Yes |
| `UNSPLASH_APPLICATION_ID` | Unsplash application ID | Yes |
| `OLLAMA_MODEL` | Ollama text model | No (default: `llama3.1:8b`) |
| `OLLAMA_VISION_MODEL` | Ollama vision model | No (default: `llava:latest`) |
| `OLLAMA_API_URL` | Ollama API endpoint | No (default: `http://localhost:11434/api/generate`) |

### Start Ollama

```bash
# In a separate terminal
ollama serve
```

---

## 7. Usage

### Run All Aggregators

```bash
uv run python run_all_aggregators.py
```

This will:
1. Clear old content from FTP server
2. Process all 6 research categories
3. Upload generated HTML and images

### Run Individual Aggregator

```bash
uv run python aggregator.py      # AI Research (cs.AI)
uv run python aggregator_ml.py   # Machine Learning (cs.LG)
uv run python aggregator_cv.py   # Computer Vision (cs.CV)
uv run python aggregator_ro.py   # Robotics (cs.RO)
uv run python aggregator_cr.py   # Cryptography/Security (cs.CR)
uv run python aggregator_hc.py   # Human-Computer Interaction (cs.HC)
```

---

## 8. Testing

### Run All Tests

```bash
uv run pytest
```

### Run Specific Test Suites

```bash
uv run pytest tests/unit/           # Unit tests
uv run pytest tests/integration/    # Integration tests
uv run pytest tests/security/      # Security tests
```

### Test Coverage

The project includes:
- **Unit tests:** Individual component testing
- **Integration tests:** Full aggregator workflow verification
- **Security tests:** Input validation and XSS sanitization
- **Fixtures:** Network mocking for deterministic testing (see [`conftest.py`](tests/conftest.py:1))

---

## 9. Output Structure

Generated files are published to the configured FTP server:

```
output/
├── index.html    # AI Research (main entry point)
├── ml.html       # Machine Learning
├── cv.html       # Computer Vision
├── ro.html       # Robotics
├── cr.html       # Cryptography/Security
├── hc.html       # Human-Computer Interaction
└── images/       # Generated article images
    └── article_*.jpg
```

---

## 10. Automation

### Scheduled Execution (Linux/macOS)

```bash
# Run every 6 hours
0 */6 * * * cd /path/to/myArxivAggregator && uv run python run_all_aggregators.py
```

### Windows Task Scheduler

```cmd
schtasks /create /tn "My ArXiv Aggregator" /tr "uv run python run_all_aggregators.py" /sc hourly /mo 6
```

---

## 11. Troubleshooting

### UV Issues

```bash
# Recreate virtual environment
rm -rf .venv
uv venv
uv sync

# Clear UV cache if needed
uv cache clean
```

### Ollama Connection Error

```bash
# Ensure Ollama is running
ollama serve

# Verify models are installed
ollama list
```

### FTP Upload Failures

- Verify credentials in `.env`
- Check network connectivity
- Ensure FTP server allows write access

### Unsplash API Errors

- Monitor usage in [Unsplash dashboard](https://unsplash.com/developers)
- Check API rate limits

---

## 12. Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run the test suite: `uv run pytest`
5. Commit and push: `git commit -am 'Add feature'` && `git push origin feature-name`
6. Open a pull request

### Adding Dependencies

```bash
# Add a new runtime dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>
```

### Development Dependencies

```bash
# Install all dev dependencies (includes ruff for linting/formatting)
uv sync --dev
```

---

## 13. License

MIT License. See [LICENSE](LICENSE) file for details.

---

## 14. Acknowledgments

- [arXiv](https://arxiv.org/) — Open access to research papers
- [Ollama](https://ollama.ai/) — Local AI model hosting
- [Unsplash](https://unsplash.com/) — Stock photography

---

Generated by Kilo Code Documentation Specialist.
