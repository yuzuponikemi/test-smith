# Langfuse Integration Setup Guide

This guide will help you set up Langfuse observability for the Test-Smith research agent system.

## What is Langfuse?

Langfuse is an open-source LLM engineering platform that provides:
- **Tracing**: Complete visibility into LLM calls and agent workflows
- **Cost Analytics**: Track token usage and costs across different models
- **Session Management**: Group related traces by conversation/thread
- **Dashboards**: Real-time monitoring and analytics
- **Self-Hosting**: Option to run on your own infrastructure

## Quick Start

### 1. Create a Langfuse Account

**Cloud Option (Recommended for Testing):**
1. Go to https://cloud.langfuse.com
2. Sign up for a free account
3. Create a new project (e.g., "test-smith-research")
4. Navigate to Settings → API Keys
5. Copy your **Public Key** and **Secret Key**

**Self-Hosted Option:**
- Follow the [official self-hosting guide](https://langfuse.com/docs/deployment/self-host)
- Note your instance URL for `LANGFUSE_HOST`

### 2. Configure Environment Variables

Edit your `.env` file (or create one from `.env.example`):

```bash
# Enable Langfuse tracing
LANGFUSE_ENABLED=true

# Add your Langfuse credentials
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxxxxxxx

# Optional: Set custom host (defaults to https://cloud.langfuse.com)
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3. Install Dependencies

If you're setting up a fresh environment:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies (includes langfuse)
pip install -r requirements.txt
```

### 4. Run the System

No code changes needed! Just run normally:

```bash
python main.py run "What is quantum computing?"
```

You should see:
```
[Langfuse] Tracing enabled - session: <thread-id>
```

### 5. View Traces in Langfuse Dashboard

1. Go to https://cloud.langfuse.com (or your self-hosted URL)
2. Navigate to your project
3. Click on "Traces" in the sidebar
4. You'll see all your agent executions with:
   - Full trace tree (planner → searcher → analyzer → etc.)
   - LLM calls with prompts and completions
   - Token usage and costs
   - Execution times
   - Session grouping by thread_id

## Features & Usage

### Session-Based Grouping

All traces from the same conversation are grouped together using the thread_id:

```bash
# First query in a session
python main.py run "What is quantum computing?" --thread-id my-session-123

# Follow-up in same session
python main.py run "How is it different from classical computing?" --thread-id my-session-123
```

In Langfuse, filter by session_id = "my-session-123" to see all related traces.

### Metadata Tracking

The integration automatically adds metadata:
- `graph`: Which graph workflow was used (e.g., "deep_research", "quick_research")
- `query`: The original user query
- `session_id`: Thread ID for grouping
- Plus all standard LangChain metadata

### Cost Tracking

Langfuse automatically tracks:
- Token counts (input/output)
- Costs (if using paid APIs like Gemini)
- Per-model breakdowns

View in Dashboard → Costs

### Filtering and Search

Use Langfuse filters to find specific traces:
- By session ID
- By execution time
- By graph type (in metadata)
- By cost range
- By token usage

## Using with Both LangSmith and Langfuse

You can enable both observability platforms simultaneously:

```bash
# .env file with both enabled
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<langsmith-key>
LANGCHAIN_PROJECT=deep-research-v1-proto

LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=<langfuse-public-key>
LANGFUSE_SECRET_KEY=<langfuse-secret-key>
```

**When to use both:**
- LangSmith: Better for debugging graph structures and LangChain-specific issues
- Langfuse: Better for production monitoring, cost tracking, and analytics

## Troubleshooting

### Traces not appearing in Langfuse

1. Check that `LANGFUSE_ENABLED=true` in your `.env`
2. Verify your API keys are correct
3. Check console for errors during execution
4. Ensure langfuse package is installed: `pip list | grep langfuse`

### Connection errors

If you see connection errors:
1. Verify `LANGFUSE_HOST` is correct (https:// prefix required)
2. Check your internet connection
3. For self-hosted: Ensure your instance is accessible

### Traces are incomplete

The system calls `flush_langfuse()` at the end of execution. If traces are incomplete:
1. Ensure the script runs to completion
2. Check that the script doesn't exit abruptly
3. Look for exceptions in the console output

### Disable Langfuse temporarily

Set in `.env`:
```bash
LANGFUSE_ENABLED=false
```

Or remove the environment variable entirely.

## Advanced Configuration

### Custom Session IDs

Use meaningful session IDs for better organization:

```bash
python main.py run "Your query" --thread-id "user-john-research-2024-01"
```

### Programmatic Access

The Langfuse integration is in `src/utils/langfuse_config.py`. You can customize:
- Metadata attached to traces
- User IDs for multi-user tracking
- Custom trace names

Example modification:
```python
# In main.py, add custom metadata
langfuse_handler = get_langfuse_callback_handler(
    session_id=thread_id,
    user_id="your-user-id",  # Add user tracking
    metadata={
        "graph": graph_name,
        "query": args.query,
        "environment": "production",  # Custom metadata
        "version": "2.1"
    }
)
```

## Best Practices

1. **Use consistent thread IDs** for conversations to enable session grouping
2. **Review traces regularly** to identify performance bottlenecks
3. **Monitor costs** if using paid API providers (Gemini, OpenAI, etc.)
4. **Set up alerts** in Langfuse for high-cost traces or errors
5. **Archive old projects** to keep your dashboard clean

## Next Steps

- Explore the [Langfuse documentation](https://langfuse.com/docs)
- Set up [custom dashboards](https://langfuse.com/docs/analytics/dashboards)
- Configure [alerts](https://langfuse.com/docs/analytics/alerts)
- Try [playground mode](https://langfuse.com/docs/playground) for testing prompts

## Support

- Langfuse Docs: https://langfuse.com/docs
- Langfuse Discord: https://discord.gg/7NXusRtqYU
- Test-Smith Issues: https://github.com/yuzuponikemi/test-smith/issues
