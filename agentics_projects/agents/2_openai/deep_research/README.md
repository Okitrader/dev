# Deep Research Agent System - Enhanced Version

An advanced multi-agent research system that orchestrates specialized AI agents to conduct comprehensive research, generate professional reports, and deliver them via email.

## Key Enhancements

### 1. Domain Specialization
- **Military Innovation**: Defense technology, munitions, autonomous systems
- **Cryptocurrency**: Meme coins, blockchain, DeFi protocols
- **Options Trading**: US and Japanese markets analysis
- **Agentic AI Development**: Latest frameworks and architectures

### 2. Improved Agent Architecture

#### Search Agent
- Enhanced instructions with domain expertise
- High-context search mode for detailed results
- Better error handling and logging

#### Planner Agent
- Strategic query generation (3 focused searches vs 5 generic)
- Domain-aware search term optimization
- Justification for each search query

#### Writer Agent
- Professional report structure with executive summaries
- Targeted 500-800 word reports (more focused)
- Markdown formatting with clear sections
- Metadata tracking (word count, timestamps)

#### Email Agent
- SendGrid integration with youremail@mail.com 
- Professional HTML formatting
- Enhanced error handling
- Detailed logging

### 3. Technical Improvements
- Comprehensive logging throughout the pipeline
- Type hints for better code clarity
- Async/await patterns for concurrent execution
- Enhanced error handling and recovery
- Progress tracking with emojis
- Structured outputs using Pydantic models

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with:
```
OPENAI_API_KEY=your_openai_api_key
SENDGRID_API_KEY=your_sendgrid_api_key
LANGSMITH_API_KEY=your_langsmith_api_key  # Optional for tracing
```

## Usage

```bash
python deep_research.py
```

Then navigate to the Gradio interface and enter your research query.

## Workflow

1. **Planning Phase**: Generates strategic search queries
2. **Search Phase**: Executes concurrent web searches
3. **Writing Phase**: Synthesizes findings into professional report
4. **Email Phase**: Formats and sends HTML email

## Cost Optimization

- Uses `gpt-4o-mini` for efficiency
- Reduced searches from 5 to 3
- High-context search for better results per query
- Estimated cost: ~$0.002 per research cycle

## Monitoring

View execution traces at: https://platform.openai.com/traces

## Email Configuration

The system is configured to send emails from and to `youremail  `. Update in `email_agent.py` if needed.
